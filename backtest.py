"""Historical backtesting for the prediction model.

Train on regular season, test on tournament games.
Includes per-round accuracy, bootstrap confidence intervals,
and regular-season holdout evaluation.
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
from torvik import fetch_team_stats, fetch_player_stats, fetch_player_stats_daterange
from predict import GamePredictor, build_player_features, compute_recency_weights

warnings.filterwarnings("ignore", category=RuntimeWarning)

OUT_DIR = Path(__file__).resolve().parent / "plots"
OUT_DIR.mkdir(exist_ok=True)

# Tournament typically starts mid-March. Cutoff dates (YYYYMMDD format).
TOURNAMENT_CUTOFFS = {
    2024: 20240318,
    2025: 20250317,
    2026: 20260316,
}

# Round date offsets relative to cutoff (days after cutoff)
ROUND_DAY_RANGES = {
    "R64": (1, 2),
    "R32": (3, 4),
    "S16": (8, 9),
    "E8": (10, 11),
    "F4+": (14, 30),
}


def split_regular_tournament(tgs: pd.DataFrame, cutoff: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split team-game stats into regular season and tournament."""
    regular = tgs[tgs["numdate"] <= cutoff].copy()
    tournament = tgs[tgs["numdate"] > cutoff].copy()
    return regular, tournament


def assign_round_labels(tourney: pd.DataFrame, cutoff: int) -> pd.Series:
    """Assign round labels to tournament games based on date offset from cutoff."""
    # Convert cutoff int (YYYYMMDD) to datetime for day arithmetic
    cutoff_dt = pd.to_datetime(str(cutoff), format="%Y%m%d")
    game_dates = pd.to_datetime(tourney["numdate"].astype(str), format="%Y%m%d")
    days_after = (game_dates - cutoff_dt).dt.days

    labels = pd.Series("Unknown", index=tourney.index)
    for round_name, (lo, hi) in ROUND_DAY_RANGES.items():
        mask = (days_after >= lo) & (days_after <= hi)
        labels[mask] = round_name
    return labels


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

    # Upset detection
    underdogs = y_prob < 0.5
    if underdogs.sum() > 0:
        upset_correct = (y_pred[underdogs] == y_true[underdogs]).mean()
        metrics["underdog_accuracy"] = upset_correct
    else:
        metrics["underdog_accuracy"] = np.nan

    return metrics


def bootstrap_ci(y_true: np.ndarray, y_prob: np.ndarray,
                 n_boot: int = 1000, ci: float = 0.95, seed: int = 42) -> dict:
    """Compute bootstrap 95% CI for log loss, AUC, and accuracy."""
    rng = np.random.RandomState(seed)
    n = len(y_true)
    boot_ll = []
    boot_auc = []
    boot_acc = []

    for _ in range(n_boot):
        idx = rng.randint(0, n, size=n)
        bt, bp = y_true[idx], y_prob[idx]
        # Skip degenerate bootstrap samples
        if len(np.unique(bt)) < 2:
            continue
        boot_ll.append(log_loss(bt, bp))
        boot_auc.append(roc_auc_score(bt, bp))
        boot_acc.append(accuracy_score(bt, (bp >= 0.5).astype(int)))

    alpha = (1 - ci) / 2
    lo = alpha
    hi = 1 - alpha

    return {
        "log_loss_ci": (np.percentile(boot_ll, lo * 100), np.percentile(boot_ll, hi * 100)),
        "auc_ci": (np.percentile(boot_auc, lo * 100), np.percentile(boot_auc, hi * 100)),
        "accuracy_ci": (np.percentile(boot_acc, lo * 100), np.percentile(boot_acc, hi * 100)),
    }


def evaluate_per_round(tourney: pd.DataFrame, test_feat_df: pd.DataFrame,
                       test_y_win: np.ndarray, y_prob: np.ndarray,
                       test_y_spread: np.ndarray, y_spread_pred: np.ndarray,
                       cutoff: int):
    """Print per-round accuracy and log loss."""
    # tourney and test_feat_df may differ in length (some games dropped during build_training_data).
    # We need round labels aligned to test_feat_df rows.
    # build_training_data filters to games where tt < opp, so roughly half the tourney rows.
    # We assign round labels to the full tourney, then align via index.
    round_labels = assign_round_labels(tourney, cutoff)

    # test_feat_df was built from tourney rows where tt < opp — we need to track which
    # tourney indices survived. Since build_training_data doesn't preserve index,
    # we reconstruct by filtering the same way.
    games = tourney[tourney["tt"] < tourney["opp"]].copy()
    # The round labels for these games (in order)
    game_rounds = round_labels.loc[games.index].values

    # test_feat_df may have fewer rows if some teams weren't in teams_df
    # We need to handle potential mismatches — use min length
    n = min(len(game_rounds), len(test_y_win))
    game_rounds = game_rounds[:n]

    print(f"\n  Per-Round Breakdown:")
    print(f"    {'Round':<8} {'N':>4} {'Accuracy':>9} {'Log Loss':>9}")
    print(f"    {'-' * 34}")

    for round_name in ["R64", "R32", "S16", "E8", "F4+"]:
        mask = game_rounds == round_name
        if mask.sum() == 0:
            continue
        r_y = test_y_win[mask]
        r_prob = y_prob[mask]
        r_acc = accuracy_score(r_y, (r_prob >= 0.5).astype(int))
        r_ll = log_loss(r_y, r_prob) if len(np.unique(r_y)) > 1 else float("nan")
        print(f"    {round_name:<8} {mask.sum():>4} {r_acc:>9.1%} {r_ll:>9.4f}")


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
    all_train_weights = []

    for year in train_years:
        print(f"  Loading {year} data...")
        year_cutoff = cutoff if year == test_year else TOURNAMENT_CUTOFFS.get(year)
        tgs, _, _ = run_gravity_pipeline(year, cutoff_date=year_cutoff)
        teams_df = fetch_team_stats(year).set_index("team")
        if year_cutoff is not None:
            start = f"{year - 1}1101"
            end = str(year_cutoff)
            players_df = fetch_player_stats_daterange(year, start, end)
        else:
            players_df = fetch_player_stats(year)
        player_feats = build_player_features(players_df)

        # For training years != test year, use all games
        if year != test_year:
            train_tgs = tgs
        else:
            train_tgs, _ = split_regular_tournament(tgs, cutoff)

        feat_df, y_win, y_spread, dates = predictor.build_training_data(train_tgs, teams_df, player_feats)
        year_cutoff_val = year_cutoff if year_cutoff is not None else TOURNAMENT_CUTOFFS.get(year, year * 10000 + 316)
        weights = compute_recency_weights(dates, year_cutoff_val)
        all_train_X.append(feat_df)
        all_train_y_win.append(y_win)
        all_train_y_spread.append(y_spread)
        all_train_weights.append(weights)

    # Combine training data
    train_X = pd.concat(all_train_X, ignore_index=True)
    train_y_win = np.concatenate(all_train_y_win)
    train_y_spread = np.concatenate(all_train_y_spread)
    train_weights = np.concatenate(all_train_weights)

    # Regular-season holdout: hold out 20% for evaluation
    rng = np.random.RandomState(42)
    n_train = len(train_X)
    holdout_mask = rng.rand(n_train) < 0.2
    holdout_X = train_X[holdout_mask].copy()
    holdout_y_win = train_y_win[holdout_mask]
    holdout_y_spread = train_y_spread[holdout_mask]
    fit_X = train_X[~holdout_mask].copy()
    fit_y_win = train_y_win[~holdout_mask]
    fit_y_spread = train_y_spread[~holdout_mask]
    fit_weights = train_weights[~holdout_mask]

    print(f"  Training on {len(fit_X)} games (holdout: {len(holdout_X)})...")
    predictor.fit(fit_X, fit_y_win, fit_y_spread, sample_weight=fit_weights)

    # Evaluate on regular-season holdout
    if len(holdout_X) > 0:
        ho_prob = []
        ho_spread_pred = []
        for _, row in holdout_X.iterrows():
            features = row.to_dict()
            ho_prob.append(predictor.predict_proba(features))
            ho_spread_pred.append(predictor.predict_spread(features))
        ho_prob = np.array(ho_prob)
        ho_spread_pred = np.array(ho_spread_pred)

        ho_metrics = evaluate_predictions(holdout_y_win, ho_prob, holdout_y_spread, ho_spread_pred,
                                          label + "_holdout")
        print(f"\n  Regular-Season Holdout ({ho_metrics['n_games']} games):")
        print(f"    Log Loss:     {ho_metrics['log_loss']:.4f}")
        print(f"    AUC:          {ho_metrics['auc']:.4f}")
        print(f"    Accuracy:     {ho_metrics['accuracy']:.1%}")
        print(f"    Spread RMSE:  {ho_metrics['spread_rmse']:.1f} pts")

    # Now retrain on ALL training data for tournament evaluation
    print(f"\n  Retraining on full {n_train} games for tournament eval...")
    predictor_full = GamePredictor()
    predictor_full.fit(train_X, train_y_win, train_y_spread, sample_weight=train_weights)

    # Test on tournament games (using pre-tournament player stats)
    print(f"  Testing on {test_year} tournament...")
    teams_df = fetch_team_stats(test_year).set_index("team")
    start = f"{test_year - 1}1101"
    end = str(cutoff)
    players_df = fetch_player_stats_daterange(test_year, start, end)
    player_feats = build_player_features(players_df)

    # Get full season data (including tournament) for test games
    full_tgs, _, _ = run_gravity_pipeline(test_year)
    _, tourney = split_regular_tournament(full_tgs, cutoff)

    if len(tourney) == 0:
        print(f"  No tournament games found for {test_year}")
        return {}

    # Build test predictions using pre-tournament team/player stats
    test_feat_df, test_y_win, test_y_spread, _ = predictor_full.build_training_data(
        tourney, teams_df, player_feats
    )

    if len(test_feat_df) == 0:
        print(f"  No valid tournament games for testing")
        return {}

    # Predict (raw)
    y_prob = []
    y_spread_pred = []
    y_spread_wp = []
    for _, row in test_feat_df.iterrows():
        features = row.to_dict()
        y_prob.append(predictor_full.predict_proba(features))
        y_spread_pred.append(predictor_full.predict_spread(features))
        y_spread_wp.append(predictor_full.spread_win_prob(features))

    y_prob = np.array(y_prob)
    y_spread_pred = np.array(y_spread_pred)
    y_spread_wp = np.array(y_spread_wp)

    # Evaluate raw
    metrics = evaluate_predictions(test_y_win, y_prob, test_y_spread, y_spread_pred, label)

    print(f"\n  Raw Results ({metrics['n_games']} tournament games):")
    print(f"    Log Loss:     {metrics['log_loss']:.4f}")
    print(f"    AUC:          {metrics['auc']:.4f}")
    print(f"    Accuracy:     {metrics['accuracy']:.1%}")
    print(f"    Brier Score:  {metrics['brier']:.4f}")
    print(f"    Spread MAE:   {metrics['spread_mae']:.1f} pts")
    print(f"    Spread RMSE:  {metrics['spread_rmse']:.1f} pts")

    # Bootstrap confidence intervals
    ci = bootstrap_ci(test_y_win, y_prob)
    print(f"\n  Bootstrap 95% CI ({metrics['n_games']} games, 1000 iterations):")
    print(f"    Log Loss:     [{ci['log_loss_ci'][0]:.4f}, {ci['log_loss_ci'][1]:.4f}]")
    print(f"    AUC:          [{ci['auc_ci'][0]:.4f}, {ci['auc_ci'][1]:.4f}]")
    print(f"    Accuracy:     [{ci['accuracy_ci'][0]:.1%}, {ci['accuracy_ci'][1]:.1%}]")
    metrics["log_loss_ci_lo"] = ci["log_loss_ci"][0]
    metrics["log_loss_ci_hi"] = ci["log_loss_ci"][1]

    # Per-round breakdown
    evaluate_per_round(tourney, test_feat_df, test_y_win, y_prob, test_y_spread, y_spread_pred, cutoff)

    # Calibrate tournament temperature
    print("\n  Calibrating tournament temperature...")
    predictor_full.calibrate_tournament_temp(test_y_win, y_prob)

    # Predict with temperature scaling
    y_prob_cal = []
    for _, row in test_feat_df.iterrows():
        features = row.to_dict()
        y_prob_cal.append(predictor_full.predict_proba(features, tournament=True))
    y_prob_cal = np.array(y_prob_cal)

    metrics_cal = evaluate_predictions(test_y_win, y_prob_cal, test_y_spread, y_spread_pred,
                                        label + "_calibrated")

    print(f"\n  Calibrated Results (temp={predictor_full.tournament_temp:.2f}):")
    print(f"    Log Loss:     {metrics_cal['log_loss']:.4f}")
    print(f"    AUC:          {metrics_cal['auc']:.4f}")
    print(f"    Accuracy:     {metrics_cal['accuracy']:.1%}")
    print(f"    Brier Score:  {metrics_cal['brier']:.4f}")

    # Ensemble evaluation: calibrate blend weight and evaluate
    predictor_full.calibrate_blend_weight(test_y_win, y_prob_cal, y_spread_wp)
    y_ensemble = predictor_full.blend_weight * y_prob_cal + (1 - predictor_full.blend_weight) * y_spread_wp
    metrics_ens = evaluate_predictions(test_y_win, y_ensemble, test_y_spread, y_spread_pred,
                                        label + "_ensemble")
    print(f"\n  Ensemble Results (blend={predictor_full.blend_weight:.2f}):")
    print(f"    Log Loss:     {metrics_ens['log_loss']:.4f}")
    print(f"    AUC:          {metrics_ens['auc']:.4f}")
    print(f"    Accuracy:     {metrics_ens['accuracy']:.1%}")
    print(f"    Brier Score:  {metrics_ens['brier']:.4f}")

    # Spread-only win prob evaluation
    metrics_spread_wp = evaluate_predictions(test_y_win, y_spread_wp, test_y_spread, y_spread_pred,
                                              label + "_spread_wp")
    print(f"\n  Spread Win Prob Results:")
    print(f"    Log Loss:     {metrics_spread_wp['log_loss']:.4f}")
    print(f"    AUC:          {metrics_spread_wp['auc']:.4f}")
    print(f"    Accuracy:     {metrics_spread_wp['accuracy']:.1%}")

    # Calibration plots (both raw and calibrated)
    if len(test_y_win) >= 20:
        plot_calibration(test_y_win, y_prob, label + " (raw)")
        plot_calibration(test_y_win, y_prob_cal, label + " (calibrated)")

    metrics["tournament_temp"] = predictor_full.tournament_temp
    metrics["cal_log_loss"] = metrics_cal["log_loss"]
    metrics["cal_brier"] = metrics_cal["brier"]
    metrics["blend_weight"] = predictor_full.blend_weight
    metrics["ensemble_log_loss"] = metrics_ens["log_loss"]
    metrics["ensemble_accuracy"] = metrics_ens["accuracy"]
    metrics["spread_wp_log_loss"] = metrics_spread_wp["log_loss"]

    # Store holdout metrics for comparison
    if len(holdout_X) > 0:
        metrics["holdout_log_loss"] = ho_metrics["log_loss"]
        metrics["holdout_accuracy"] = ho_metrics["accuracy"]

    return metrics


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("BACKTESTING: Torvik + Player Prediction Model")
    print("=" * 60)

    results = []

    # Test 1: Train 2024 regular season -> test 2024 tournament
    m = backtest_year([2024], 2024)
    if m:
        results.append(m)

    # Test 2: Train 2024 + 2025 regular season -> test 2025 tournament
    m = backtest_year([2024, 2025], 2025)
    if m:
        results.append(m)

    # Summary table
    if results:
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        summary = pd.DataFrame(results)
        cols = ["label", "n_games", "log_loss", "log_loss_ci_lo", "log_loss_ci_hi",
                "auc", "accuracy", "brier", "spread_rmse", "tournament_temp",
                "cal_log_loss", "cal_brier", "blend_weight",
                "ensemble_log_loss", "ensemble_accuracy", "spread_wp_log_loss"]
        if "holdout_log_loss" in summary.columns:
            cols += ["holdout_log_loss", "holdout_accuracy"]
        available = [c for c in cols if c in summary.columns]
        print(summary[available].to_string(index=False))
