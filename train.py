"""Model training pipeline.

Fetches data, builds player features, trains the prediction models,
calibrates tournament temperature, and saves to disk.

Usage:
    python train.py                          # Train on 2026 data
    python train.py --years 2024 2025 2026   # Train on multiple years
"""

from __future__ import annotations

import argparse
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.metrics import log_loss, roc_auc_score, accuracy_score

from gravity import run_gravity_pipeline
from torvik import fetch_team_stats, fetch_game_stats, fetch_player_stats, fetch_player_stats_daterange
from predict import GamePredictor, build_player_features, compute_recency_weights, MODELS_DIR, _TORVIK_COLS, _TEAM_DIFF_STATS


TOURNAMENT_CUTOFFS = {
    2024: 20240318,
    2025: 20250317,
    2026: 20260316,
}


def train(years: list[int], cutoff_current_year: bool = True):
    """Train prediction models on specified years."""
    print("=" * 60)
    print("TRAINING PIPELINE")
    print("=" * 60)

    predictor = GamePredictor()
    all_X = []
    all_y_win = []
    all_y_spread = []
    all_weights = []

    for year in years:
        print(f"\n--- {year} ---")
        print(f"  Fetching data...")
        fetch_team_stats(year)
        fetch_game_stats(year)

        cutoff = TOURNAMENT_CUTOFFS.get(year) if cutoff_current_year else None
        print(f"  Building features (cutoff={cutoff})...")

        # Get team-game stats (for game outcomes)
        tgs, _, _ = run_gravity_pipeline(year, cutoff_date=cutoff)
        if cutoff is not None and "numdate" in tgs.columns:
            tgs = tgs[tgs["numdate"] <= cutoff].copy()

        teams_df = fetch_team_stats(year).set_index("team")
        if cutoff is not None:
            start = f"{year - 1}1101"
            end = str(cutoff)
            try:
                players_df = fetch_player_stats_daterange(year, start, end)
            except Exception as e:
                print(f"  Date-range fetch failed ({e.__class__.__name__}), falling back to full-season stats")
                players_df = fetch_player_stats(year)
        else:
            players_df = fetch_player_stats(year)
        player_feats = build_player_features(players_df)

        print(f"  {tgs['muid'].nunique()} games, {tgs['tt'].nunique()} teams")

        feat_df, y_win, y_spread, dates = predictor.build_training_data(tgs, teams_df, player_feats)
        print(f"  {len(feat_df)} training rows")

        # Compute recency weights for this year
        year_cutoff = cutoff if cutoff is not None else TOURNAMENT_CUTOFFS.get(year, year * 10000 + 316)
        weights = compute_recency_weights(dates, year_cutoff)

        all_X.append(feat_df)
        all_y_win.append(y_win)
        all_y_spread.append(y_spread)
        all_weights.append(weights)

    # Combine
    train_X = pd.concat(all_X, ignore_index=True)
    train_y_win = np.concatenate(all_y_win)
    train_y_spread = np.concatenate(all_y_spread)
    train_weights = np.concatenate(all_weights)

    print(f"\n{'=' * 60}")
    print(f"Total training: {len(train_X)} games, {len(train_X.columns)} features")
    print(f"Win rate: {train_y_win.mean():.3f}")
    print(f"Mean spread: {train_y_spread.mean():.1f}, std: {train_y_spread.std():.1f}")
    print(f"{'=' * 60}")

    # Train
    print("\nTraining models...")
    predictor.fit(train_X, train_y_win, train_y_spread, sample_weight=train_weights)

    # Training metrics
    print("\n--- Training Metrics ---")
    y_prob_train = []
    y_spread_train = []
    for _, row in train_X.iterrows():
        features = row.to_dict()
        y_prob_train.append(predictor.predict_proba(features))
        y_spread_train.append(predictor.predict_spread(features))
    y_prob_train = np.array(y_prob_train)
    y_spread_train = np.array(y_spread_train)

    print(f"  Log Loss:     {log_loss(train_y_win, y_prob_train):.4f}")
    print(f"  AUC:          {roc_auc_score(train_y_win, y_prob_train):.4f}")
    print(f"  Accuracy:     {accuracy_score(train_y_win, (y_prob_train >= 0.5).astype(int)):.1%}")
    print(f"  Spread RMSE:  {np.sqrt(np.mean((train_y_spread - y_spread_train) ** 2)):.1f} pts")
    print(f"  Spread Sigma: {predictor.spread_sigma:.1f} pts")

    # Feature importance
    print("\n--- Feature Coefficients (Logistic) ---")
    coefs = pd.Series(predictor.logistic.coef_[0], index=predictor.feature_names)
    coefs = coefs.reindex(coefs.abs().sort_values(ascending=False).index)
    for feat, coef in coefs.items():
        print(f"  {feat:<30} {coef:+.4f}")

    # Calibrate tournament temperature and blend weight on historical tournament data
    print("\n--- Tournament Calibration ---")
    tourney_logistic_probs = []
    tourney_spread_probs = []
    tourney_y = []
    for cal_year in years:
        cutoff = TOURNAMENT_CUTOFFS.get(cal_year)
        if cutoff is None:
            continue
        full_tgs, _, _ = run_gravity_pipeline(cal_year)
        if "numdate" not in full_tgs.columns:
            continue
        post_tgs = full_tgs[full_tgs["numdate"] > cutoff]
        if len(post_tgs) == 0:
            continue
        cal_teams = fetch_team_stats(cal_year).set_index("team")
        cal_start = f"{cal_year - 1}1101"
        cal_end = str(cutoff)
        cal_players = fetch_player_stats_daterange(cal_year, cal_start, cal_end)
        cal_pf = build_player_features(cal_players)
        cal_feat, cal_y_win, _, _ = predictor.build_training_data(post_tgs, cal_teams, cal_pf)
        if len(cal_feat) == 0:
            continue
        for _, row in cal_feat.iterrows():
            feat = row.to_dict()
            tourney_logistic_probs.append(predictor.predict_proba(feat))
            tourney_spread_probs.append(predictor.spread_win_prob(feat))
        tourney_y.extend(cal_y_win.tolist())

    if len(tourney_y) >= 20:
        tourney_logistic_probs = np.array(tourney_logistic_probs)
        tourney_spread_probs = np.array(tourney_spread_probs)
        tourney_y = np.array(tourney_y)
        predictor.calibrate_tournament_temp(tourney_y, tourney_logistic_probs)

        # Re-compute logistic probs with temperature for blend calibration
        # (temperature-scaled logistic probs are what the ensemble will use)
        tourney_logistic_cal = []
        for p in tourney_logistic_probs:
            logit = np.log(max(p, 1e-7) / max(1 - p, 1e-7))
            tourney_logistic_cal.append(float(1 / (1 + np.exp(-logit / predictor.tournament_temp))))
        tourney_logistic_cal = np.array(tourney_logistic_cal)

        predictor.calibrate_blend_weight(tourney_y, tourney_logistic_cal, tourney_spread_probs)
    else:
        print("  Not enough tournament data for calibration")

    # Save
    print(f"\nSaving models to {MODELS_DIR}...")
    predictor.save()
    print("Done!")

    return predictor


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train game prediction models")
    parser.add_argument("--years", "-y", nargs="+", type=int, default=[2026],
                        help="Season years to train on (default: 2026)")
    parser.add_argument("--no-cutoff", action="store_true",
                        help="Don't filter tournament games from training data")
    args = parser.parse_args()

    train(args.years, cutoff_current_year=not args.no_cutoff)
