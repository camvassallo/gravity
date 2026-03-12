"""Phase 2: Game prediction engine.

GamePredictor uses gravity coefficients alongside Torvik efficiency ratings
to predict win probability and point spread.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression, LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.calibration import CalibratedClassifierCV
from scipy.stats import norm
import warnings
import joblib
from pathlib import Path

warnings.filterwarnings("ignore", category=RuntimeWarning)

MODELS_DIR = Path(__file__).resolve().parent / "models"


class GamePredictor:
    """Predicts game outcomes using gravity + Torvik features."""

    def __init__(self):
        self.logistic = None
        self.spread_model = None
        self.gbm = None
        self.scaler = StandardScaler()
        self.feature_names = []
        self.spread_sigma = 11.0  # empirical residual std, updated during training
        self.gbm_weight = 0.0  # ensemble weight for GBM (0 = logistic only)

    def build_features(self, t1_gravity: dict, t2_gravity: dict,
                       t1_torvik: dict, t2_torvik: dict,
                       location: float = 0.0) -> np.ndarray:
        """Build feature vector for a single game.

        Args:
            t1_gravity: gravity coefficients for team 1 (col_name -> value)
            t2_gravity: gravity coefficients for team 2
            t1_torvik: Torvik ratings for team 1 (adjoe, adjde, barthag, adj_tempo, sos)
            t2_torvik: Torvik ratings for team 2
            location: 1=t1 home, 0=neutral, -1=t1 away
        """
        features = {}

        # Efficiency gaps
        features["eff_gap_t1_off"] = t1_torvik.get("adjoe", 0) - t2_torvik.get("adjde", 0)
        features["eff_gap_t2_off"] = t2_torvik.get("adjoe", 0) - t1_torvik.get("adjde", 0)

        # Barthag diff
        features["barthag_diff"] = t1_torvik.get("barthag", 0) - t2_torvik.get("barthag", 0)

        # Expected tempo
        features["expected_tempo"] = (t1_torvik.get("adj_tempo", 67) + t2_torvik.get("adj_tempo", 67)) / 2

        # SOS diff
        features["sos_diff"] = t1_torvik.get("sos", 0) - t2_torvik.get("sos", 0)

        # Location
        features["location"] = location

        # All gravity coefficients for both teams
        for col, val in t1_gravity.items():
            features[f"t1_{col}"] = val
        for col, val in t2_gravity.items():
            features[f"t2_{col}"] = val

        # Gravity matchup features: t1_off × t2_def and vice versa
        for stat_base in ["efficiency", "efg", "three_pt_rate", "ft_rate", "to_rate",
                          "orb_rate", "ast_rate", "stl_rate", "two_pt_pct"]:
            t1_off = t1_gravity.get(f"{stat_base}_off_gravity", 0)
            t2_def = t2_gravity.get(f"{stat_base}_def_gravity", 0)
            t2_off = t2_gravity.get(f"{stat_base}_off_gravity", 0)
            t1_def = t1_gravity.get(f"{stat_base}_def_gravity", 0)
            features[f"matchup_{stat_base}_t1_off_t2_def"] = t1_off * t2_def
            features[f"matchup_{stat_base}_t2_off_t1_def"] = t2_off * t1_def

        return features

    def build_training_data(self, tgs: pd.DataFrame, combined: pd.DataFrame,
                            teams_df: pd.DataFrame) -> tuple[pd.DataFrame, np.ndarray, np.ndarray]:
        """Build training matrices from team-game stats.

        Returns (feature_df, y_win, y_spread).
        """
        grav_cols = [c for c in combined.columns if "gravity" in c]

        # One row per game: keep tt < opp
        games = tgs[tgs["tt"] < tgs["opp"]].copy()
        games["win"] = (games["pts"] > games["opp_pts"]).astype(int)
        games["point_diff"] = games["pts"] - games["opp_pts"]

        if "loc" in games.columns:
            loc_map = {"H": 1, "A": -1, "N": 0}
            games["location"] = games["loc"].map(loc_map).fillna(0)
        else:
            games["location"] = 0

        rows = []
        for _, g in games.iterrows():
            t1, t2 = g["tt"], g["opp"]
            if t1 not in combined.index or t2 not in combined.index:
                continue
            if t1 not in teams_df.index or t2 not in teams_df.index:
                continue

            t1_grav = {col: combined.loc[t1, col] for col in grav_cols}
            t2_grav = {col: combined.loc[t2, col] for col in grav_cols}
            t1_torvik = {s: teams_df.loc[t1, s] for s in ["adjoe", "adjde", "barthag", "adj_tempo", "sos"]
                         if s in teams_df.columns}
            t2_torvik = {s: teams_df.loc[t2, s] for s in ["adjoe", "adjde", "barthag", "adj_tempo", "sos"]
                         if s in teams_df.columns}

            feat = self.build_features(t1_grav, t2_grav, t1_torvik, t2_torvik, g["location"])
            feat["_win"] = g["win"]
            feat["_point_diff"] = g["point_diff"]
            rows.append(feat)

        df = pd.DataFrame(rows).dropna()
        y_win = df.pop("_win").values
        y_spread = df.pop("_point_diff").values

        return df, y_win, y_spread

    def fit(self, feature_df: pd.DataFrame, y_win: np.ndarray, y_spread: np.ndarray,
            use_gbm: bool = True):
        """Train logistic regression, spread model, and optionally LightGBM ensemble."""
        self.feature_names = list(feature_df.columns)
        X = feature_df.values
        X_scaled = self.scaler.fit_transform(X)

        # 1. Logistic regression for win probability
        self.logistic = LogisticRegression(C=1.0, max_iter=5000, random_state=42)
        self.logistic.fit(X_scaled, y_win)

        # 2. Linear regression for point spread
        self.spread_model = LinearRegression()
        self.spread_model.fit(X_scaled, y_spread)

        # Compute residual sigma for spread model
        spread_pred = self.spread_model.predict(X_scaled)
        residuals = y_spread - spread_pred
        self.spread_sigma = np.std(residuals)

        # 3. Optional LightGBM with Platt scaling
        if use_gbm:
            try:
                import lightgbm as lgb
                # Force a quick check that the native library is loadable
                lgb.LGBMClassifier()

                self.gbm = lgb.LGBMClassifier(
                    n_estimators=300, max_depth=5, learning_rate=0.05,
                    subsample=0.8, colsample_bytree=0.8, random_state=42, verbose=-1,
                    min_child_samples=20,
                )
                # Calibrate with Platt scaling
                self.gbm = CalibratedClassifierCV(self.gbm, cv=5, method="sigmoid")
                self.gbm.fit(X, y_win)

                # Determine ensemble weight via cross-validation log loss comparison
                from sklearn.model_selection import cross_val_predict
                logistic_probs = cross_val_predict(
                    LogisticRegression(C=1.0, max_iter=5000, random_state=42),
                    X_scaled, y_win, cv=5, method="predict_proba",
                )[:, 1]
                gbm_probs = cross_val_predict(self.gbm, X, y_win, cv=5, method="predict_proba")[:, 1]

                from sklearn.metrics import log_loss
                ll_logistic = log_loss(y_win, logistic_probs)
                ll_gbm = log_loss(y_win, gbm_probs)

                # Use GBM weight proportional to improvement
                if ll_gbm < ll_logistic:
                    self.gbm_weight = min(0.5, (ll_logistic - ll_gbm) / ll_logistic)
                else:
                    self.gbm_weight = 0.0

                print(f"  Logistic CV log loss: {ll_logistic:.4f}")
                print(f"  GBM CV log loss:      {ll_gbm:.4f}")
                print(f"  Ensemble weight:      {self.gbm_weight:.3f} (GBM)")
            except (ImportError, OSError):
                print("  lightgbm not available, using logistic only")
                self.gbm = None
                self.gbm_weight = 0.0

    def predict_proba(self, features: dict) -> float:
        """Predict win probability for team 1."""
        X = pd.DataFrame([features])[self.feature_names].values
        X_scaled = self.scaler.transform(X)

        logistic_prob = self.logistic.predict_proba(X_scaled)[0, 1]

        if self.gbm is not None and self.gbm_weight > 0:
            gbm_prob = self.gbm.predict_proba(X)[0, 1]
            prob = (1 - self.gbm_weight) * logistic_prob + self.gbm_weight * gbm_prob
        else:
            prob = logistic_prob

        return float(prob)

    def predict_spread(self, features: dict) -> float:
        """Predict point spread (positive = team 1 favored)."""
        X = pd.DataFrame([features])[self.feature_names].values
        X_scaled = self.scaler.transform(X)
        return float(self.spread_model.predict(X_scaled)[0])

    def spread_win_prob(self, features: dict) -> float:
        """Derive win probability from spread model: P(spread > 0)."""
        spread = self.predict_spread(features)
        return float(norm.cdf(spread / self.spread_sigma))

    def predict_game(self, t1_gravity: dict, t2_gravity: dict,
                     t1_torvik: dict, t2_torvik: dict,
                     location: float = 0.0) -> dict:
        """Full prediction for a single game.

        Returns dict with win_prob, spread, spread_win_prob, predicted scores.
        """
        features = self.build_features(t1_gravity, t2_gravity, t1_torvik, t2_torvik, location)

        win_prob = self.predict_proba(features)
        spread = self.predict_spread(features)
        spread_wp = self.spread_win_prob(features)

        # Predicted total from tempo-adjusted efficiency
        pace = features["expected_tempo"]
        t1_eff = t1_torvik.get("adjoe", 100)
        t2_eff = t2_torvik.get("adjoe", 100)
        predicted_total = (t1_eff * pace / 100) + (t2_eff * pace / 100)
        t1_score = (predicted_total + spread) / 2
        t2_score = (predicted_total - spread) / 2

        return {
            "win_prob": win_prob,
            "spread": spread,
            "spread_sigma": self.spread_sigma,
            "spread_win_prob": spread_wp,
            "predicted_total": predicted_total,
            "t1_score": t1_score,
            "t2_score": t2_score,
        }

    def save(self, path: Path = None):
        """Save model to disk."""
        if path is None:
            path = MODELS_DIR
        path.mkdir(parents=True, exist_ok=True)
        joblib.dump({
            "logistic": self.logistic,
            "spread_model": self.spread_model,
            "gbm": self.gbm,
            "scaler": self.scaler,
            "feature_names": self.feature_names,
            "spread_sigma": self.spread_sigma,
            "gbm_weight": self.gbm_weight,
        }, path / "game_predictor.joblib")

    @classmethod
    def load(cls, path: Path = None) -> "GamePredictor":
        """Load model from disk."""
        if path is None:
            path = MODELS_DIR
        data = joblib.load(path / "game_predictor.joblib")
        pred = cls()
        pred.logistic = data["logistic"]
        pred.spread_model = data["spread_model"]
        pred.gbm = data["gbm"]
        pred.scaler = data["scaler"]
        pred.feature_names = data["feature_names"]
        pred.spread_sigma = data["spread_sigma"]
        pred.gbm_weight = data["gbm_weight"]
        return pred
