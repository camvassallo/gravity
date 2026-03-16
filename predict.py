"""Game prediction engine.

GamePredictor uses Torvik efficiency ratings, team quality metrics,
and player-derived features to predict win probability and point spread.

Feature set (16 features):
- 2 core Torvik: barthag diff, SOS diff
- 4 team quality: fun, elite SOS, quality games, WAB diffs
- 10 player-derived: BPM sum, weighted BPM, weighted porpag, ast/tov,
  stops, GBPM, TS% sum, bench BPM, BPM trend, porpag trend (all diffs)
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression, LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import cross_val_score
from scipy.stats import norm
import warnings
import joblib
from pathlib import Path

warnings.filterwarnings("ignore", category=RuntimeWarning)

MODELS_DIR = Path(__file__).resolve().parent / "models"


def compute_recency_weights(dates: np.ndarray, cutoff: int,
                            half_life_days: int = 60) -> np.ndarray:
    """Compute exponential recency weights for training games.

    Args:
        dates: array of numdate values (YYYYMMDD ints)
        cutoff: tournament cutoff date (YYYYMMDD int)
        half_life_days: half-life in days for exponential decay

    Returns:
        array of weights in (0, 1], where cutoff-day games get weight 1.0
    """
    cutoff_dt = pd.to_datetime(str(int(cutoff)), format="%Y%m%d")
    game_dts = pd.to_datetime(dates.astype(int).astype(str), format="%Y%m%d")
    days_before = (cutoff_dt - game_dts).days.values.astype(float)
    days_before = np.clip(days_before, 0, None)
    decay = np.log(2) / half_life_days
    return np.exp(-decay * days_before)

# Team-level stats used as diffs
_TEAM_DIFF_STATS = ["fun", "elite_sos", "qual_games", "wab"]

# Player-derived stats used as diffs
_PLAYER_DIFF_STATS = [
    "top5_bpm_sum", "top5_bpm_weighted", "top5_porpag_weighted",
    "top_ast_tov", "top5_stops_sum", "top_gbpm",
    "top5_ts_sum", "bench_bpm_sum",
    "top5_bpm_trend", "top_porpag_trend",
]

# Torvik columns needed per team
_TORVIK_COLS = ["adjoe", "adjde", "barthag", "adj_tempo", "sos"]


def build_player_features(players_df: pd.DataFrame,
                          recent_players_df: pd.DataFrame | None = None,
                          exclusions: dict | None = None,
                          weights: dict | None = None) -> dict[str, dict]:
    """Aggregate player stats into team-level features.

    Args:
        players_df: player stats DataFrame
        recent_players_df: optional player stats for recent window (last 30 days),
                           used to compute form/trend features
        exclusions: optional dict mapping team name -> list of player names
                    to exclude (e.g. injured players)
        weights: optional dict mapping team name -> {player_name: float}
                 where 0.0=out, 0.5=game-time decision, 1.0=healthy.
                 Weighted players have their stats scaled by the weight
                 instead of being fully excluded.

    Returns dict mapping team name -> {stat_name: value}.
    """
    players_df = players_df.copy()
    feats = {}
    for team in players_df["team"].unique():
        tp = players_df[players_df["team"] == team].copy()

        # Exclude injured/unavailable players
        if exclusions and team in exclusions:
            tp = tp[~tp["player_name"].isin(exclusions[team])]

        tp["min_total"] = pd.to_numeric(tp["mp"], errors="coerce")
        tp = tp.sort_values("min_total", ascending=False)

        # Apply partial weights (e.g. GTD players)
        team_weights = (weights or {}).get(team, {})
        if team_weights:
            _weight_cols = ["bpm", "porpag", "obpm", "dbpm", "stops", "gbpm", "ts_per"]
            for col in _weight_cols:
                if col in tp.columns:
                    tp[col] = pd.to_numeric(tp[col], errors="coerce")
            for player_name, w in team_weights.items():
                mask = tp["player_name"] == player_name
                if mask.any():
                    for col in _weight_cols:
                        if col in tp.columns:
                            tp.loc[mask, col] = tp.loc[mask, col] * w

        top5 = tp.head(5)
        top8 = tp.head(8)

        pf = {}
        # Core player stats
        bpm = pd.to_numeric(top5["bpm"], errors="coerce")
        porpag = pd.to_numeric(top5["porpag"], errors="coerce")
        min_per = pd.to_numeric(top5["min_per"], errors="coerce")
        usg = pd.to_numeric(top5["usg"], errors="coerce")

        pf["top5_bpm_sum"] = bpm.sum()

        # Weighted features
        min_sum = min_per.sum()
        pf["top5_bpm_weighted"] = (bpm * min_per).sum() / min_sum if min_sum > 0 else 0.0
        usg_sum = usg.sum()
        pf["top5_porpag_weighted"] = (porpag * usg).sum() / usg_sum if usg_sum > 0 else 0.0

        # Exploratory features
        pf["top_ast_tov"] = pd.to_numeric(top5["ast_tov"], errors="coerce").max()
        pf["top5_stops_sum"] = pd.to_numeric(top5["stops"], errors="coerce").sum()
        pf["top_gbpm"] = pd.to_numeric(top5["gbpm"], errors="coerce").max()

        # Shooting efficiency and bench depth
        ts = pd.to_numeric(top5["ts_per"], errors="coerce")
        pf["top5_ts_sum"] = ts.sum()

        bench = top8.iloc[5:8] if len(top8) > 5 else pd.DataFrame()
        if len(bench) > 0:
            pf["bench_bpm_sum"] = pd.to_numeric(bench["bpm"], errors="coerce").sum()
        else:
            pf["bench_bpm_sum"] = 0.0

        # Late-season form trends (default 0.0 if no recent data)
        pf["top5_bpm_trend"] = 0.0
        pf["top_porpag_trend"] = 0.0
        if recent_players_df is not None:
            rtp = recent_players_df[recent_players_df["team"] == team].copy()
            if exclusions and team in exclusions:
                rtp = rtp[~rtp["player_name"].isin(exclusions[team])]
            rtp["min_total"] = pd.to_numeric(rtp["mp"], errors="coerce")
            rtp = rtp.sort_values("min_total", ascending=False)
            rtop5 = rtp.head(5)
            if len(rtop5) > 0:
                recent_bpm = pd.to_numeric(rtop5["bpm"], errors="coerce")
                recent_porpag = pd.to_numeric(rtop5["porpag"], errors="coerce")
                pf["top5_bpm_trend"] = recent_bpm.sum() - bpm.sum()
                pf["top_porpag_trend"] = recent_porpag.max() - porpag.max()

        feats[team] = pf
    return feats


class GamePredictor:
    """Predicts game outcomes using Torvik + team quality + player features."""

    def __init__(self):
        self.logistic = None
        self.spread_model = None
        self.scaler = StandardScaler()
        self.feature_names = []
        self.spread_sigma = 11.0
        self.tournament_temp = 1.0
        self.best_C = 1.0
        self.blend_weight = 0.5

    def build_features(self, t1_torvik: dict, t2_torvik: dict,
                       t1_players: dict, t2_players: dict,
                       location: float = 0.0) -> dict:
        """Build feature vector for a single game.

        Args:
            t1_torvik: Torvik team stats for team 1 (must include adjoe, adjde,
                       barthag, adj_tempo, sos, fun, elite_sos, qual_games, wab)
            t2_torvik: Torvik team stats for team 2
            t1_players: player-derived features for team 1
            t2_players: player-derived features for team 2
            location: 1=t1 home, 0=neutral, -1=t1 away
        """
        features = {}

        # Core Torvik (2 features)
        features["barthag_diff"] = t1_torvik.get("barthag", 0) - t2_torvik.get("barthag", 0)
        features["sos_diff"] = t1_torvik.get("sos", 0) - t2_torvik.get("sos", 0)

        # Team quality diffs (4 features)
        for stat in _TEAM_DIFF_STATS:
            features[f"diff_{stat}"] = t1_torvik.get(stat, 0) - t2_torvik.get(stat, 0)

        # Player diffs (10 features)
        for stat in _PLAYER_DIFF_STATS:
            features[f"diff_{stat}"] = t1_players.get(stat, 0) - t2_players.get(stat, 0)

        return features

    def build_training_data(self, tgs: pd.DataFrame, teams_df: pd.DataFrame,
                            player_feats: dict) -> tuple[pd.DataFrame, np.ndarray, np.ndarray, np.ndarray]:
        """Build training matrices from team-game stats.

        Returns (feature_df, y_win, y_spread, dates).
        """
        games = tgs[tgs["tt"] < tgs["opp"]].copy()
        games["win"] = (games["pts"] > games["opp_pts"]).astype(int)
        games["point_diff"] = games["pts"] - games["opp_pts"]

        if "loc" in games.columns:
            games["location"] = games["loc"].map({"H": 1, "A": -1, "N": 0}).fillna(0)
        else:
            games["location"] = 0

        rows = []
        for _, g in games.iterrows():
            t1, t2 = g["tt"], g["opp"]
            if t1 not in teams_df.index or t2 not in teams_df.index:
                continue

            t1_torvik = {s: pd.to_numeric(teams_df.loc[t1, s], errors="coerce")
                         for s in _TORVIK_COLS + _TEAM_DIFF_STATS if s in teams_df.columns}
            t2_torvik = {s: pd.to_numeric(teams_df.loc[t2, s], errors="coerce")
                         for s in _TORVIK_COLS + _TEAM_DIFF_STATS if s in teams_df.columns}
            t1_players = player_feats.get(t1, {})
            t2_players = player_feats.get(t2, {})

            feat = self.build_features(t1_torvik, t2_torvik, t1_players, t2_players, g["location"])
            feat["_win"] = g["win"]
            feat["_point_diff"] = g["point_diff"]
            feat["_numdate"] = g.get("numdate", 0)
            rows.append(feat)

        df = pd.DataFrame(rows).dropna()
        y_win = df.pop("_win").values
        y_spread = df.pop("_point_diff").values
        dates = df.pop("_numdate").values
        return df, y_win, y_spread, dates

    def fit(self, feature_df: pd.DataFrame, y_win: np.ndarray, y_spread: np.ndarray,
            sample_weight: np.ndarray | None = None):
        """Train logistic regression and spread model with CV-tuned regularization."""
        self.feature_names = list(feature_df.columns)
        X = feature_df.values
        X_scaled = self.scaler.fit_transform(X)

        # Tune regularization via cross-validated log loss (unweighted for simplicity)
        best_C = 1.0
        best_score = -999
        for C in [0.01, 0.05, 0.1, 0.5, 1.0, 5.0, 10.0]:
            lr = LogisticRegression(C=C, max_iter=5000, random_state=42)
            scores = cross_val_score(lr, X_scaled, y_win, cv=5, scoring="neg_log_loss")
            mean_score = scores.mean()
            if mean_score > best_score:
                best_score = mean_score
                best_C = C

        self.best_C = best_C
        print(f"  Best C={best_C} (CV log loss: {-best_score:.4f})")

        # Logistic regression for win probability
        self.logistic = LogisticRegression(C=best_C, max_iter=5000, random_state=42)
        self.logistic.fit(X_scaled, y_win, sample_weight=sample_weight)

        # Linear regression for point spread
        self.spread_model = LinearRegression()
        self.spread_model.fit(X_scaled, y_spread, sample_weight=sample_weight)

        # Compute residual sigma
        spread_pred = self.spread_model.predict(X_scaled)
        self.spread_sigma = np.std(y_spread - spread_pred)

    def calibrate_tournament_temp(self, tourney_y: np.ndarray, tourney_probs: np.ndarray):
        """Find optimal temperature scaling for tournament predictions."""
        from sklearn.metrics import log_loss

        best_temp = 1.0
        best_ll = log_loss(tourney_y, tourney_probs)

        for temp in np.arange(0.8, 2.01, 0.05):
            logits = np.log(np.clip(tourney_probs, 1e-7, 1 - 1e-7) /
                           np.clip(1 - tourney_probs, 1e-7, 1 - 1e-7))
            scaled = 1 / (1 + np.exp(-logits / temp))
            ll = log_loss(tourney_y, scaled)
            if ll < best_ll:
                best_ll = ll
                best_temp = temp

        self.tournament_temp = best_temp
        print(f"  Tournament temperature: {best_temp:.2f} (log loss {best_ll:.4f})")

    def predict_proba(self, features: dict, tournament: bool = False) -> float:
        """Predict win probability for team 1."""
        X = pd.DataFrame([features])[self.feature_names].values
        X_scaled = self.scaler.transform(X)
        prob = float(self.logistic.predict_proba(X_scaled)[0, 1])

        if tournament and self.tournament_temp != 1.0:
            logit = np.log(max(prob, 1e-7) / max(1 - prob, 1e-7))
            prob = float(1 / (1 + np.exp(-logit / self.tournament_temp)))

        return prob

    def predict_spread(self, features: dict) -> float:
        """Predict point spread (positive = team 1 favored)."""
        X = pd.DataFrame([features])[self.feature_names].values
        X_scaled = self.scaler.transform(X)
        return float(self.spread_model.predict(X_scaled)[0])

    def spread_win_prob(self, features: dict) -> float:
        """Derive win probability from spread model: P(spread > 0)."""
        spread = self.predict_spread(features)
        return float(norm.cdf(spread / self.spread_sigma))

    def ensemble_prob(self, features: dict, tournament: bool = False) -> float:
        """Blended probability from logistic and spread models."""
        w = self.blend_weight
        logistic_p = self.predict_proba(features, tournament=tournament)
        spread_p = self.spread_win_prob(features)
        return w * logistic_p + (1 - w) * spread_p

    def calibrate_blend_weight(self, y_true: np.ndarray,
                               logistic_probs: np.ndarray,
                               spread_probs: np.ndarray):
        """Find optimal blend weight minimizing log loss on tournament data."""
        from sklearn.metrics import log_loss as _log_loss

        best_w = 0.5
        best_ll = float("inf")
        for w_int in range(0, 21):  # 0.0 to 1.0 in 0.05 steps
            w = w_int / 20.0
            blended = w * logistic_probs + (1 - w) * spread_probs
            ll = _log_loss(y_true, blended)
            if ll < best_ll:
                best_ll = ll
                best_w = w

        self.blend_weight = best_w
        print(f"  Blend weight: {best_w:.2f} (log loss {best_ll:.4f})")

    def predict_game(self, t1_torvik: dict, t2_torvik: dict,
                     t1_players: dict, t2_players: dict,
                     location: float = 0.0) -> dict:
        """Full prediction for a single game."""
        features = self.build_features(t1_torvik, t2_torvik, t1_players, t2_players, location)

        win_prob = self.predict_proba(features)
        spread = self.predict_spread(features)
        spread_wp = self.spread_win_prob(features)

        pace = (t1_torvik.get("adj_tempo", 67) + t2_torvik.get("adj_tempo", 67)) / 2
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
            "scaler": self.scaler,
            "feature_names": self.feature_names,
            "spread_sigma": self.spread_sigma,
            "tournament_temp": self.tournament_temp,
            "best_C": self.best_C,
            "blend_weight": self.blend_weight,
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
        pred.scaler = data["scaler"]
        pred.feature_names = data["feature_names"]
        pred.spread_sigma = data["spread_sigma"]
        pred.tournament_temp = data.get("tournament_temp", 1.0)
        pred.best_C = data.get("best_C", 1.0)
        pred.blend_weight = data.get("blend_weight", 0.5)
        return pred
