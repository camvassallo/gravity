"""Phase 1: Gravity significance analysis and feature importance.

Evaluates which gravity dimensions matter for predicting game outcomes,
identifies redundancies, and produces a finalized feature list.
"""

from __future__ import annotations

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.linear_model import LogisticRegression, LassoCV
from sklearn.metrics import roc_auc_score
from sklearn.preprocessing import StandardScaler
from sklearn.inspection import permutation_importance
import warnings

from gravity import run_gravity_pipeline, build_combined_table, PAIRED_STATS
from torvik import fetch_team_stats

warnings.filterwarnings("ignore", category=RuntimeWarning)

OUT_DIR = Path(__file__).resolve().parent / "plots"
OUT_DIR.mkdir(exist_ok=True)


# ---------------------------------------------------------------------------
# Dataset construction
# ---------------------------------------------------------------------------

def build_game_outcome_dataset(tgs: pd.DataFrame, combined: pd.DataFrame,
                                teams_df: pd.DataFrame) -> pd.DataFrame:
    """Build one row per game with gravity features, Torvik ratings, and outcome.

    Each game appears once (team1 = home/first alphabetically at neutral).
    """
    # Get gravity columns
    grav_cols = [c for c in combined.columns if "gravity" in c]

    # Deduplicate: keep one row per game (the row where tt < opp alphabetically)
    games = tgs.copy()
    games = games[games["tt"] < games["opp"]].copy()

    # Target variables
    games["win"] = (games["pts"] > games["opp_pts"]).astype(int)
    games["point_diff"] = games["pts"] - games["opp_pts"]

    # Map location: 1=home, 0=neutral, -1=away
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

        row = {"muid": g["muid"], "win": g["win"], "point_diff": g["point_diff"],
               "location": g["location"]}

        if "numdate" in g.index:
            row["numdate"] = g["numdate"]

        # Gravity features for both teams
        for col in grav_cols:
            row[f"t1_{col}"] = combined.loc[t1, col]
            row[f"t2_{col}"] = combined.loc[t2, col]

        # Torvik ratings
        for stat in ["adjoe", "adjde", "barthag", "adj_tempo", "sos"]:
            if stat in teams_df.columns:
                row[f"t1_{stat}"] = teams_df.loc[t1, stat] if t1 in teams_df.index else np.nan
                row[f"t2_{stat}"] = teams_df.loc[t2, stat] if t2 in teams_df.index else np.nan

        rows.append(row)

    return pd.DataFrame(rows).dropna()


# ---------------------------------------------------------------------------
# Univariate AUC
# ---------------------------------------------------------------------------

def compute_univariate_auc(df: pd.DataFrame) -> pd.DataFrame:
    """Compute AUC for each gravity feature individually for win prediction."""
    grav_features = [c for c in df.columns if "gravity" in c]
    y = df["win"].values

    results = []
    for feat in grav_features:
        x = df[feat].values
        try:
            auc = roc_auc_score(y, x)
            # Flip if AUC < 0.5 (negative relationship)
            direction = "+" if auc >= 0.5 else "-"
            auc = max(auc, 1 - auc)
            results.append({"feature": feat, "auc": auc, "direction": direction})
        except ValueError:
            continue

    return pd.DataFrame(results).sort_values("auc", ascending=False)


# ---------------------------------------------------------------------------
# Correlation matrix
# ---------------------------------------------------------------------------

def compute_gravity_correlations(combined: pd.DataFrame) -> pd.DataFrame:
    """Correlation matrix of all gravity dimensions."""
    grav_cols = [c for c in combined.columns if "gravity" in c]
    return combined[grav_cols].corr()


# ---------------------------------------------------------------------------
# LASSO feature selection
# ---------------------------------------------------------------------------

def run_lasso_analysis(df: pd.DataFrame) -> pd.DataFrame:
    """LASSO logistic regression to identify expendable features."""
    feature_cols = [c for c in df.columns if c not in ["muid", "win", "point_diff", "numdate"]]
    X = df[feature_cols].values
    y = df["win"].values

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Use LassoCV on point_diff for feature selection (continuous target)
    lasso = LassoCV(cv=5, random_state=42, max_iter=10000)
    lasso.fit(X_scaled, df["point_diff"].values)

    results = pd.DataFrame({
        "feature": feature_cols,
        "lasso_coef": lasso.coef_,
        "abs_coef": np.abs(lasso.coef_),
    }).sort_values("abs_coef", ascending=False)

    results["kept"] = results["abs_coef"] > 0
    return results


# ---------------------------------------------------------------------------
# LightGBM permutation importance
# ---------------------------------------------------------------------------

def run_permutation_importance(df: pd.DataFrame) -> pd.DataFrame:
    """Permutation importance with LightGBM for non-linear interactions."""
    try:
        import lightgbm as lgb
        lgb.LGBMClassifier()  # verify native lib loads
    except (ImportError, OSError):
        print("  lightgbm not available, skipping permutation importance")
        return pd.DataFrame()

    feature_cols = [c for c in df.columns if c not in ["muid", "win", "point_diff", "numdate"]]
    X = df[feature_cols].values
    y = df["win"].values

    model = lgb.LGBMClassifier(
        n_estimators=200, max_depth=5, learning_rate=0.05,
        subsample=0.8, colsample_bytree=0.8, random_state=42, verbose=-1,
    )
    model.fit(X, y)

    perm = permutation_importance(model, X, y, n_repeats=10, random_state=42, scoring="roc_auc")

    results = pd.DataFrame({
        "feature": feature_cols,
        "importance_mean": perm.importances_mean,
        "importance_std": perm.importances_std,
    }).sort_values("importance_mean", ascending=False)
    return results


# ---------------------------------------------------------------------------
# Impact scores: gravity × z-score
# ---------------------------------------------------------------------------

def add_impact_features(df: pd.DataFrame, combined: pd.DataFrame) -> pd.DataFrame:
    """Add impact score features (gravity × z-score of the team's average stat)."""
    df = df.copy()

    # Get avg columns from combined
    avg_cols = [c for c in combined.columns if "avg" in c or "avg_pace" in c]

    for col in avg_cols:
        mu = combined[col].mean()
        std = combined[col].std()
        if std < 1e-9:
            continue
        # Find corresponding gravity column
        base = col.replace("_off_avg", "_off_gravity").replace("_def_avg", "_def_gravity").replace("avg_pace", "tempo_gravity")
        if base not in combined.columns:
            continue

        z_name = col.replace("avg", "zscore")
        impact_name = base.replace("gravity", "impact")

        for prefix in ["t1_", "t2_"]:
            grav_col = f"{prefix}{base}"
            if grav_col in df.columns:
                # z-score of the average stat
                avg_vals = df[grav_col]  # we don't have avg directly in df, skip
                # Instead compute impact from combined table directly
                pass

    return df


# ---------------------------------------------------------------------------
# Plotting
# ---------------------------------------------------------------------------

def plot_feature_importance(univariate_auc: pd.DataFrame, lasso: pd.DataFrame,
                            perm_imp: pd.DataFrame):
    """Summary plots of feature importance analysis."""
    fig, axes = plt.subplots(1, 3, figsize=(20, 8))

    # Univariate AUC
    top_uni = univariate_auc.head(20)
    axes[0].barh(range(len(top_uni)), top_uni["auc"].values, color="#2563eb")
    axes[0].set_yticks(range(len(top_uni)))
    axes[0].set_yticklabels([f.replace("_gravity", "").replace("t1_", "A:").replace("t2_", "B:")
                             for f in top_uni["feature"]], fontsize=7)
    axes[0].set_xlabel("AUC")
    axes[0].set_title("Univariate AUC (top 20)")
    axes[0].axvline(0.5, color="gray", linestyle="--", linewidth=0.5)
    axes[0].invert_yaxis()

    # LASSO
    top_lasso = lasso[lasso["kept"]].head(20)
    if len(top_lasso) > 0:
        axes[1].barh(range(len(top_lasso)), top_lasso["abs_coef"].values, color="#16a34a")
        axes[1].set_yticks(range(len(top_lasso)))
        axes[1].set_yticklabels([f.replace("_gravity", "").replace("t1_", "A:").replace("t2_", "B:")
                                 for f in top_lasso["feature"]], fontsize=7)
        axes[1].set_xlabel("|Coefficient|")
        axes[1].set_title("LASSO (non-zero, top 20)")
        axes[1].invert_yaxis()

    # Permutation importance
    if len(perm_imp) > 0:
        top_perm = perm_imp.head(20)
        axes[2].barh(range(len(top_perm)), top_perm["importance_mean"].values, color="#dc2626")
        axes[2].set_yticks(range(len(top_perm)))
        axes[2].set_yticklabels([f.replace("_gravity", "").replace("t1_", "A:").replace("t2_", "B:")
                                 for f in top_perm["feature"]], fontsize=7)
        axes[2].set_xlabel("Permutation Importance")
        axes[2].set_title("LightGBM Perm. Importance (top 20)")
        axes[2].invert_yaxis()

    fig.suptitle("Feature Importance Analysis", fontsize=14)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "feature_importance.png", dpi=150, bbox_inches="tight")
    print(f"  Saved {OUT_DIR / 'feature_importance.png'}")
    plt.close(fig)


def plot_correlation_matrix(corr: pd.DataFrame):
    """Heatmap of gravity dimension correlations."""
    fig, ax = plt.subplots(figsize=(14, 12))
    labels = [c.replace("_gravity", "") for c in corr.columns]
    vmax = max(abs(corr.values[np.triu_indices_from(corr.values, k=1)].min()),
               abs(corr.values[np.triu_indices_from(corr.values, k=1)].max()))
    im = ax.imshow(corr.values, cmap="RdBu_r", vmin=-vmax, vmax=vmax)
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, fontsize=7, rotation=45, ha="right")
    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels(labels, fontsize=7)
    fig.colorbar(im, ax=ax, shrink=0.6)
    ax.set_title("Gravity Dimension Correlations")

    # Add correlation values
    for i in range(len(labels)):
        for j in range(len(labels)):
            val = corr.values[i, j]
            color = "white" if abs(val) > vmax * 0.6 else "black"
            ax.text(j, i, f"{val:.2f}", ha="center", va="center", fontsize=5, color=color)

    fig.tight_layout()
    fig.savefig(OUT_DIR / "gravity_correlations.png", dpi=150, bbox_inches="tight")
    print(f"  Saved {OUT_DIR / 'gravity_correlations.png'}")
    plt.close(fig)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 80)
    print("FEATURE ANALYSIS: Gravity Significance for Game Prediction")
    print("=" * 80)

    # Load data
    print("\nLoading 2026 data...")
    tgs, gravities, combined = run_gravity_pipeline(2026)
    teams_df = fetch_team_stats(2026).set_index("team")

    # Print R² for all gravity models (including new candidates)
    print("\n--- Gravity Model R² (including new candidates) ---")
    for key, df in gravities.items():
        r2 = df.attrs["r2"]
        n = df.attrs["n_obs"]
        print(f"  {key:<16} R² = {r2:.4f}  ({n:,} obs)")

    # Build outcome dataset
    print("\nBuilding game outcome dataset...")
    outcome_df = build_game_outcome_dataset(tgs, combined, teams_df)
    print(f"  {len(outcome_df)} games, {len(outcome_df.columns)} features")
    print(f"  Win rate: {outcome_df['win'].mean():.3f}")

    # Univariate AUC
    print("\n--- Univariate AUC per Gravity Feature ---")
    uni_auc = compute_univariate_auc(outcome_df)
    for _, row in uni_auc.iterrows():
        print(f"  {row['feature']:<45} AUC = {row['auc']:.4f} ({row['direction']})")

    # Correlation matrix
    print("\n--- Gravity Correlation Matrix ---")
    corr = compute_gravity_correlations(combined)
    # Show highly correlated pairs (|r| > 0.5)
    pairs = []
    for i in range(len(corr)):
        for j in range(i + 1, len(corr)):
            r = corr.iloc[i, j]
            if abs(r) > 0.5:
                pairs.append((corr.index[i], corr.columns[j], r))
    pairs.sort(key=lambda x: -abs(x[2]))
    if pairs:
        print("  Highly correlated pairs (|r| > 0.5):")
        for c1, c2, r in pairs:
            print(f"    {c1:<30} vs {c2:<30} r = {r:+.3f}")
    else:
        print("  No pairs with |r| > 0.5 — gravity dimensions are largely independent")

    # LASSO
    print("\n--- LASSO Feature Selection ---")
    lasso_results = run_lasso_analysis(outcome_df)
    kept = lasso_results[lasso_results["kept"]]
    dropped = lasso_results[~lasso_results["kept"]]
    print(f"  {len(kept)} features kept, {len(dropped)} zeroed out")
    print("  Top features:")
    for _, row in kept.head(15).iterrows():
        print(f"    {row['feature']:<45} coef = {row['lasso_coef']:+.4f}")
    if len(dropped) > 0:
        print("  Zeroed out (expendable):")
        for _, row in dropped.iterrows():
            feat = row["feature"]
            if "gravity" in feat:
                print(f"    {feat}")

    # Permutation importance
    print("\n--- LightGBM Permutation Importance ---")
    perm_results = run_permutation_importance(outcome_df)
    if len(perm_results) > 0:
        for _, row in perm_results.head(20).iterrows():
            print(f"  {row['feature']:<45} imp = {row['importance_mean']:.4f} ± {row['importance_std']:.4f}")

    # Generate plots
    print("\n--- Generating Plots ---")
    plot_feature_importance(uni_auc, lasso_results, perm_results)
    plot_correlation_matrix(corr)

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print("\nGravity dimensions ranked by combined importance:")
    # Aggregate importance across methods
    grav_dims = set()
    for c in combined.columns:
        if "gravity" in c:
            grav_dims.add(c)

    for dim in sorted(grav_dims):
        uni_score = uni_auc[uni_auc["feature"].str.contains(dim)]["auc"].max() if len(uni_auc) > 0 else 0
        lasso_score = lasso_results[lasso_results["feature"].str.contains(dim)]["abs_coef"].max() if len(lasso_results) > 0 else 0
        perm_score = perm_results[perm_results["feature"].str.contains(dim)]["importance_mean"].max() if len(perm_results) > 0 else 0
        print(f"  {dim:<35} AUC={uni_score:.3f}  LASSO={lasso_score:.3f}  Perm={perm_score:.4f}")
