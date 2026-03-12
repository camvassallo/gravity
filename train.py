"""Phase 5: Model training pipeline.

One-shot script that fetches data, computes gravities, trains the
prediction models, and saves them to disk.

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

from gravity import run_gravity_pipeline, PAIRED_STATS
from torvik import fetch_team_stats, fetch_all_for_year
from predict import GamePredictor, MODELS_DIR


TOURNAMENT_CUTOFFS = {
    2024: 20240318,
    2025: 20250317,
    2026: 20260316,
}


def train(years: list[int], cutoff_current_year: bool = True):
    """Train prediction models on specified years.

    Args:
        years: list of season years to include in training
        cutoff_current_year: if True, filter the latest year to exclude tournament games
    """
    print("=" * 60)
    print("TRAINING PIPELINE")
    print("=" * 60)

    predictor = GamePredictor()
    all_X = []
    all_y_win = []
    all_y_spread = []

    for year in years:
        print(f"\n--- {year} ---")

        # Fetch data
        print(f"  Fetching data...")
        fetch_all_for_year(year)

        # Compute gravity (with cutoff for current year to prevent leakage)
        cutoff = TOURNAMENT_CUTOFFS.get(year) if cutoff_current_year else None
        print(f"  Computing gravity (cutoff={cutoff})...")
        tgs, gravities, combined = run_gravity_pipeline(year, cutoff_date=cutoff)

        # Filter games if cutoff
        if cutoff is not None and "numdate" in tgs.columns:
            tgs = tgs[tgs["numdate"] <= cutoff].copy()

        teams_df = fetch_team_stats(year).set_index("team")

        print(f"  {tgs['muid'].nunique()} games, {tgs['tt'].nunique()} teams")

        # Print gravity model R²
        for key, df in gravities.items():
            r2 = df.attrs["r2"]
            print(f"    {key:<16} R² = {r2:.4f}")

        # Build training data
        feat_df, y_win, y_spread = predictor.build_training_data(tgs, combined, teams_df)
        print(f"  {len(feat_df)} training rows")

        all_X.append(feat_df)
        all_y_win.append(y_win)
        all_y_spread.append(y_spread)

    # Combine
    train_X = pd.concat(all_X, ignore_index=True)
    train_y_win = np.concatenate(all_y_win)
    train_y_spread = np.concatenate(all_y_spread)

    print(f"\n{'=' * 60}")
    print(f"Total training: {len(train_X)} games, {len(train_X.columns)} features")
    print(f"Win rate: {train_y_win.mean():.3f}")
    print(f"Mean spread: {train_y_spread.mean():.1f}, std: {train_y_spread.std():.1f}")
    print(f"{'=' * 60}")

    # Train
    print("\nTraining models...")
    predictor.fit(train_X, train_y_win, train_y_spread)

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
    print(f"  GBM Weight:   {predictor.gbm_weight:.3f}")

    # Feature importance (logistic coefficients)
    print("\n--- Top Feature Coefficients (Logistic) ---")
    coefs = pd.Series(predictor.logistic.coef_[0], index=predictor.feature_names)
    coefs = coefs.reindex(coefs.abs().sort_values(ascending=False).index)
    for feat, coef in coefs.head(20).items():
        print(f"  {feat:<45} {coef:+.4f}")

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
