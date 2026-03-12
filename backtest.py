"""Phase 2: Historical backtesting for the prediction model.

Train on regular season, test on tournament games.
"""

from __future__ import annotations

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.metrics import log_loss, roc_auc_score, brier_score_loss, accuracy_score
import warnings

from gravity import run_gravity_pipeline
from torvik import fetch_team_stats
from predict import GamePredictor

warnings.filterwarnings("ignore", category=RuntimeWarning)

OUT_DIR = Path(__file__).resolve().parent / "plots"
OUT_DIR.mkdir(exist_ok=True)

# Tournament typically starts mid-March. Cutoff dates (YYYYMMDD format).
TOURNAMENT_CUTOFFS = {
    2024: 20240318,
    2025: 20250317,
    2026: 20260316,
}


def split_regular_tournament(tgs: pd.DataFrame, cutoff: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split team-game stats into regular season and tournament."""
    regular = tgs[tgs["numdate"] <= cutoff].copy()
    tournament = tgs[tgs["numdate"] > cutoff].copy()
    return regular, tournament


def evaluate_predictions(y_true: np.ndarray, y_prob: np.ndarray, y_spread_true: np.ndarray,
                          y_spread_pred: np.ndarray, label: str = "") -> dict:
    """Compute all evaluation metrics."""
    y_pred = (y_prob >= 0.5).astype(int)

    metrics = {
        "label": label,
        "n_games": len(y_true),
        "log_loss": log_loss(y_true, y_prob),
        "auc": roc_auc_score(y_true, y_prob),
        "accuracy": accuracy_score(y_true, y_pred),
        "brier": brier_score_loss(y_true, y_prob),
        "spread_mae": np.mean(np.abs(y_spread_true - y_spread_pred)),
        "spread_rmse": np.sqrt(np.mean((y_spread_true - y_spread_pred) ** 2)),
    }

    # Upset detection: predicted underdog wins (prob < 0.5 and actually wins, or prob > 0.5 and actually loses)
    underdogs = y_prob < 0.5
    if underdogs.sum() > 0:
        upset_correct = (y_pred[underdogs] == y_true[underdogs]).mean()
        metrics["underdog_accuracy"] = upset_correct
    else:
        metrics["underdog_accuracy"] = np.nan

    return metrics


def plot_calibration(y_true: np.ndarray, y_prob: np.ndarray, label: str = ""):
    """Calibration plot: predicted probability vs actual win rate."""
    n_bins = 10
    bin_edges = np.linspace(0, 1, n_bins + 1)
    bin_centers = []
    bin_actuals = []
    bin_counts = []

    for i in range(n_bins):
        mask = (y_prob >= bin_edges[i]) & (y_prob < bin_edges[i + 1])
        if mask.sum() > 0:
            bin_centers.append((bin_edges[i] + bin_edges[i + 1]) / 2)
            bin_actuals.append(y_true[mask].mean())
            bin_counts.append(mask.sum())

    fig, ax = plt.subplots(figsize=(8, 8))
    ax.plot([0, 1], [0, 1], "k--", linewidth=1, label="Perfect calibration")
    ax.scatter(bin_centers, bin_actuals, s=[c * 5 for c in bin_counts], c="#2563eb", alpha=0.7, zorder=5)
    ax.plot(bin_centers, bin_actuals, c="#2563eb", alpha=0.5)

    for x, y, n in zip(bin_centers, bin_actuals, bin_counts):
        ax.annotate(f"n={n}", (x, y), fontsize=7, ha="center", va="bottom", xytext=(0, 8),
                    textcoords="offset points")

    ax.set_xlabel("Predicted Win Probability")
    ax.set_ylabel("Actual Win Rate")
    ax.set_title(f"Calibration Plot {label}")
    ax.set_xlim(-0.05, 1.05)
    ax.set_ylim(-0.05, 1.05)
    ax.legend()
    fig.tight_layout()
    fname = f"calibration_{label.replace(' ', '_').lower()}.png" if label else "calibration.png"
    fig.savefig(OUT_DIR / fname, dpi=150)
    print(f"  Saved {OUT_DIR / fname}")
    plt.close(fig)


def backtest_year(train_years: list[int], test_year: int) -> dict:
    """Train on regular season of train_years, test on tournament of test_year.

    Returns metrics dict.
    """
    label = f"train={'_'.join(map(str, train_years))}_test={test_year}"
    print(f"\n{'=' * 60}")
    print(f"Backtest: {label}")
    print(f"{'=' * 60}")

    cutoff = TOURNAMENT_CUTOFFS.get(test_year)
    if cutoff is None:
        print(f"  No tournament cutoff defined for {test_year}, skipping")
        return {}

    # Build training data from all training years
    predictor = GamePredictor()
    all_train_X = []
    all_train_y_win = []
    all_train_y_spread = []

    for year in train_years:
        print(f"  Loading {year} data...")
        tgs, gravities, combined = run_gravity_pipeline(year, cutoff_date=cutoff if year == test_year else None)
        teams_df = fetch_team_stats(year).set_index("team")

        # For training years != test year, use all games
        if year != test_year:
            train_tgs = tgs
        else:
            train_tgs, _ = split_regular_tournament(tgs, cutoff)

        feat_df, y_win, y_spread = predictor.build_training_data(train_tgs, combined, teams_df)
        all_train_X.append(feat_df)
        all_train_y_win.append(y_win)
        all_train_y_spread.append(y_spread)

    # Combine training data
    train_X = pd.concat(all_train_X, ignore_index=True)
    train_y_win = np.concatenate(all_train_y_win)
    train_y_spread = np.concatenate(all_train_y_spread)

    print(f"  Training on {len(train_X)} games...")
    predictor.fit(train_X, train_y_win, train_y_spread)

    # Test on tournament games
    print(f"  Testing on {test_year} tournament...")
    test_tgs, test_grav, test_combined = run_gravity_pipeline(test_year, cutoff_date=cutoff)
    test_teams_df = fetch_team_stats(test_year).set_index("team")

    # Get full season data (including tournament) for test games
    full_tgs, _, _ = run_gravity_pipeline(test_year)
    _, tourney = split_regular_tournament(full_tgs, cutoff)

    if len(tourney) == 0:
        print(f"  No tournament games found for {test_year}")
        return {}

    # Build test predictions using pre-tournament gravity
    test_feat_df, test_y_win, test_y_spread = predictor.build_training_data(
        tourney, test_combined, test_teams_df
    )

    if len(test_feat_df) == 0:
        print(f"  No valid tournament games for testing")
        return {}

    # Predict
    y_prob = []
    y_spread_pred = []
    for _, row in test_feat_df.iterrows():
        features = row.to_dict()
        y_prob.append(predictor.predict_proba(features))
        y_spread_pred.append(predictor.predict_spread(features))

    y_prob = np.array(y_prob)
    y_spread_pred = np.array(y_spread_pred)

    # Evaluate
    metrics = evaluate_predictions(test_y_win, y_prob, test_y_spread, y_spread_pred, label)

    print(f"\n  Results ({metrics['n_games']} tournament games):")
    print(f"    Log Loss:     {metrics['log_loss']:.4f}")
    print(f"    AUC:          {metrics['auc']:.4f}")
    print(f"    Accuracy:     {metrics['accuracy']:.1%}")
    print(f"    Brier Score:  {metrics['brier']:.4f}")
    print(f"    Spread MAE:   {metrics['spread_mae']:.1f} pts")
    print(f"    Spread RMSE:  {metrics['spread_rmse']:.1f} pts")

    # Calibration plot
    if len(test_y_win) >= 20:
        plot_calibration(test_y_win, y_prob, label)

    return metrics


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("BACKTESTING: Gravity + Torvik Prediction Model")
    print("=" * 60)

    results = []

    # Test 1: Train 2024 regular season → test 2024 tournament
    m = backtest_year([2024], 2024)
    if m:
        results.append(m)

    # Test 2: Train 2024 + 2025 regular season → test 2025 tournament
    m = backtest_year([2024, 2025], 2025)
    if m:
        results.append(m)

    # Summary table
    if results:
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        summary = pd.DataFrame(results)
        print(summary.to_string(index=False))
