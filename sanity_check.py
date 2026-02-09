"""Sanity checks and visualizations for gravity scores."""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pathlib import Path

from torvik import fetch_game_stats, fetch_team_stats
from gravity import build_team_game_stats, compute_all_gravities, build_combined_table

OUT_DIR = Path(__file__).resolve().parent / "plots"
CSV_DIR = Path(__file__).resolve().parent / "data"
OUT_DIR.mkdir(exist_ok=True)
CSV_DIR.mkdir(exist_ok=True)

SPOTLIGHT_TEAMS = [
    "Virginia", "Houston", "Duke", "Gonzaga", "Tennessee",
    "Arkansas", "Auburn", "Texas Tech", "Purdue", "Kansas",
    "Kentucky", "North Carolina", "Iowa St.", "Alabama", "Connecticut",
    "St. John's", "Florida", "Michigan St.", "Marquette", "Wisconsin",
    "Michigan", "Arizona", "Illinois", "Baylor", "Oregon",
]

STAT_LABELS = {
    "tempo": "Tempo",
    "efficiency": "Efficiency",
    "efg": "Effective FG%",
    "three_pt_rate": "3pt Attempt Rate",
    "ft_rate": "Free Throw Rate",
    "to_rate": "Turnover Rate",
    "orb_rate": "Off. Rebound Rate",
}


def load_gravity():
    """Load data and compute all gravity scores."""
    games = fetch_game_stats(2026)
    teams = fetch_team_stats(2026)
    tgs = build_team_game_stats(games)
    gravities = compute_all_gravities(tgs)
    combined = build_combined_table(gravities)
    teams_df = teams.set_index("team")
    return gravities, combined, tgs, teams_df


# ---------------------------------------------------------------------------
# Sanity checks
# ---------------------------------------------------------------------------

def check_known_teams(gravities, combined):
    """Spot-check gravity for well-known teams."""
    print("=" * 90)
    print("SANITY CHECK: Known Teams — All Gravity Scores")
    print("=" * 90)

    # Gravity columns to show (skip avg columns)
    grav_cols = [c for c in combined.columns if "gravity" in c]

    print(f"\n{'Team':<20}", end="")
    for col in grav_cols:
        short = col.replace("_gravity", "").replace("_off", "(O)").replace("_def", "(D)")
        print(f"{short:>12}", end="")
    print()
    print("-" * (20 + 12 * len(grav_cols)))

    for team in SPOTLIGHT_TEAMS:
        if team not in combined.index:
            print(f"{team:<20}  ** NOT FOUND **")
            continue
        print(f"{team:<20}", end="")
        for col in grav_cols:
            val = combined.loc[team, col]
            print(f"{val:>12.2f}", end="")
        print()


def check_correlations(gravities):
    """Check whether gravity is just a proxy for being extreme at a stat."""
    print("\n" + "=" * 90)
    print("CORRELATION CHECK: Is gravity independent of stat level?")
    print("=" * 90)

    # Tempo
    tempo = gravities["tempo"]
    r = tempo["tempo_gravity"].corr(tempo["avg_pace"])
    print(f"\n  {'tempo_gravity vs avg_pace':<45} r = {r:+.3f}")

    # Paired stats
    for key, df in gravities.items():
        if key == "tempo":
            continue
        name = df.attrs["stat_name"]
        off_grav = f"{name}_off_gravity"
        def_grav = f"{name}_def_gravity"
        off_avg = f"{name}_off_avg"
        def_avg = f"{name}_def_avg"

        r_off = df[off_grav].corr(df[off_avg])
        r_def = df[def_grav].corr(df[def_avg])
        print(f"  {f'{name} off_grav vs off_avg':<45} r = {r_off:+.3f}")
        print(f"  {f'{name} def_grav vs def_avg':<45} r = {r_def:+.3f}")

    print("\n  r near 0 = gravity is independent of stat level (good!)")
    print("  r near ±1 = gravity is redundant with the stat itself")


def check_model_fit(gravities):
    """Print R² for all models."""
    print("\n" + "=" * 90)
    print("MODEL FIT (R²)")
    print("=" * 90)
    for key, df in gravities.items():
        r2 = df.attrs["r2"]
        n = df.attrs["n_obs"]
        label = STAT_LABELS.get(key, key)
        print(f"  {label:<25} R² = {r2:.4f}  ({n:,} obs)")


# ---------------------------------------------------------------------------
# CSV output
# ---------------------------------------------------------------------------

def save_csvs(gravities, combined):
    """Save gravity results to CSV files."""
    print("\n" + "=" * 90)
    print("SAVING CSV FILES")
    print("=" * 90)

    # Combined table
    path = CSV_DIR / "gravity_scores.csv"
    combined.to_csv(path)
    print(f"  {path}  ({combined.shape[0]} teams, {combined.shape[1]} cols)")

    # Individual stat tables (with averages included)
    for key, df in gravities.items():
        path = CSV_DIR / f"gravity_{key}.csv"
        df.to_csv(path)
        print(f"  {path}  ({df.shape[0]} teams, {df.shape[1]} cols)")


# ---------------------------------------------------------------------------
# Visualizations
# ---------------------------------------------------------------------------

def _annotate_extremes(ax, x, y, n=5):
    """Label the n most extreme points on a scatter plot."""
    dist = np.sqrt((x - x.mean())**2 + (y - y.mean())**2)
    top_idx = dist.nlargest(n).index
    for idx in top_idx:
        ax.annotate(
            idx, (x.loc[idx], y.loc[idx]),
            fontsize=7, ha="left", va="bottom",
            xytext=(4, 4), textcoords="offset points",
        )


def plot_tempo(gravities):
    """Scatter: avg pace vs tempo gravity."""
    tempo = gravities["tempo"]
    fig, ax = plt.subplots(figsize=(10, 7))
    ax.scatter(tempo["avg_pace"], tempo["tempo_gravity"], alpha=0.5, s=30, c="#2563eb")
    _annotate_extremes(ax, tempo["avg_pace"], tempo["tempo_gravity"], n=12)

    ax.axhline(0, color="gray", linewidth=0.5, linestyle="--")
    ax.set_xlabel("Season Average Pace (possessions)")
    ax.set_ylabel("Tempo Gravity")
    ax.set_title("Tempo Gravity vs Average Pace\n(high gravity = imposes their pace on opponents)")
    fig.tight_layout()
    fig.savefig(OUT_DIR / "tempo_gravity_vs_pace.png", dpi=150)
    print(f"  Saved {OUT_DIR / 'tempo_gravity_vs_pace.png'}")
    plt.close(fig)


def plot_paired_stat(gravities, stat_key, off_color="#dc2626", def_color="#16a34a"):
    """Scatter plots for off/def gravity of a paired stat."""
    df = gravities[stat_key]
    name = df.attrs["stat_name"]
    label = STAT_LABELS.get(stat_key, name)

    off_grav = f"{name}_off_gravity"
    def_grav = f"{name}_def_gravity"
    off_avg = f"{name}_off_avg"
    def_avg = f"{name}_def_avg"

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 7))

    ax1.scatter(df[off_avg], df[off_grav], alpha=0.5, s=30, c=off_color)
    _annotate_extremes(ax1, df[off_avg], df[off_grav], n=8)
    ax1.axhline(0, color="gray", linewidth=0.5, linestyle="--")
    ax1.set_xlabel(f"Season Avg {label} (offense)")
    ax1.set_ylabel("Offensive Gravity")
    ax1.set_title(f"Off. Gravity vs Avg {label}")

    ax2.scatter(df[def_avg], df[def_grav], alpha=0.5, s=30, c=def_color)
    _annotate_extremes(ax2, df[def_avg], df[def_grav], n=8)
    ax2.axhline(0, color="gray", linewidth=0.5, linestyle="--")
    ax2.set_xlabel(f"Season Avg {label} (defense)")
    ax2.set_ylabel("Defensive Gravity")
    ax2.set_title(f"Def. Gravity vs Avg {label}")

    fig.suptitle(f"{label} Gravity", fontsize=13, y=1.02)
    fig.tight_layout()
    fig.savefig(OUT_DIR / f"gravity_{stat_key}.png", dpi=150, bbox_inches="tight")
    print(f"  Saved {OUT_DIR / f'gravity_{stat_key}.png'}")
    plt.close(fig)


def plot_distributions(gravities):
    """Histograms of all gravity distributions."""
    # Collect all gravity series
    grav_series = []
    grav_series.append(("Tempo", gravities["tempo"]["tempo_gravity"], "#2563eb"))
    colors_off = ["#dc2626", "#e11d48", "#f97316", "#ea580c", "#d97706", "#b91c1c"]
    colors_def = ["#16a34a", "#059669", "#0d9488", "#0891b2", "#2563eb", "#4f46e5"]

    for i, (key, df) in enumerate([(k, v) for k, v in gravities.items() if k != "tempo"]):
        name = df.attrs["stat_name"]
        label = STAT_LABELS.get(key, name)
        grav_series.append((f"{label} (Off)", df[f"{name}_off_gravity"], colors_off[i % len(colors_off)]))
        grav_series.append((f"{label} (Def)", df[f"{name}_def_gravity"], colors_def[i % len(colors_def)]))

    n = len(grav_series)
    cols = 4
    rows = (n + cols - 1) // cols
    fig, axes = plt.subplots(rows, cols, figsize=(4.5 * cols, 4 * rows))
    axes = axes.flatten()

    for i, (title, series, color) in enumerate(grav_series):
        ax = axes[i]
        ax.hist(series.dropna(), bins=25, color=color, alpha=0.7, edgecolor="white")
        ax.axvline(series.mean(), color="black", linewidth=1, linestyle="--")
        ax.axvline(0, color="gray", linewidth=0.5, linestyle=":")
        ax.set_title(title, fontsize=9)
        ax.set_ylabel("Teams")
        ax.tick_params(labelsize=8)

    # Hide unused axes
    for i in range(len(grav_series), len(axes)):
        axes[i].set_visible(False)

    fig.suptitle("Distribution of Gravity Scores (365 D1 teams)", fontsize=13)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "gravity_distributions.png", dpi=150)
    print(f"  Saved {OUT_DIR / 'gravity_distributions.png'}")
    plt.close(fig)


def plot_off_vs_def(gravities, stat_key="efficiency"):
    """Scatter: offensive gravity vs defensive gravity."""
    df = gravities[stat_key]
    name = df.attrs["stat_name"]
    label = STAT_LABELS.get(stat_key, name)
    off_grav = f"{name}_off_gravity"
    def_grav = f"{name}_def_gravity"

    fig, ax = plt.subplots(figsize=(10, 8))
    ax.scatter(df[off_grav], df[def_grav], alpha=0.5, s=30, c="#7c3aed")

    xmid, ymid = df[off_grav].median(), df[def_grav].median()
    ax.axhline(ymid, color="gray", linewidth=0.5, linestyle="--")
    ax.axvline(xmid, color="gray", linewidth=0.5, linestyle="--")

    _annotate_extremes(ax, df[off_grav], df[def_grav], n=15)

    ax.set_xlabel(f"Offensive {label} Gravity")
    ax.set_ylabel(f"Defensive {label} Gravity")
    ax.set_title(f"Off vs Def {label} Gravity\n(top-right = imposes both sides)")
    fig.tight_layout()
    fig.savefig(OUT_DIR / f"gravity_{stat_key}_off_vs_def.png", dpi=150)
    print(f"  Saved {OUT_DIR / f'gravity_{stat_key}_off_vs_def.png'}")
    plt.close(fig)


def plot_gravity_heatmap(combined):
    """Heatmap of all gravity scores for the spotlight teams."""
    grav_cols = [c for c in combined.columns if "gravity" in c]
    spotlight = [t for t in SPOTLIGHT_TEAMS if t in combined.index]
    data = combined.loc[spotlight, grav_cols]

    # Shorter column labels
    short_labels = []
    for col in grav_cols:
        s = col.replace("_gravity", "").replace("_off", "\n(off)").replace("_def", "\n(def)")
        short_labels.append(s)

    fig, ax = plt.subplots(figsize=(14, 10))
    vmax = max(abs(data.min().min()), abs(data.max().max()))
    im = ax.imshow(data.values, cmap="RdBu_r", aspect="auto", vmin=-vmax, vmax=vmax)

    ax.set_xticks(range(len(grav_cols)))
    ax.set_xticklabels(short_labels, fontsize=8, ha="center")
    ax.set_yticks(range(len(spotlight)))
    ax.set_yticklabels(spotlight, fontsize=9)

    # Add value text
    for i in range(len(spotlight)):
        for j in range(len(grav_cols)):
            val = data.values[i, j]
            if np.isfinite(val):
                color = "white" if abs(val) > vmax * 0.6 else "black"
                ax.text(j, i, f"{val:.1f}", ha="center", va="center", fontsize=7, color=color)

    fig.colorbar(im, ax=ax, shrink=0.6, label="Gravity Score")
    ax.set_title("Gravity Heatmap — Top 25 Programs", fontsize=13, pad=15)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "gravity_heatmap.png", dpi=150, bbox_inches="tight")
    print(f"  Saved {OUT_DIR / 'gravity_heatmap.png'}")
    plt.close(fig)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("Loading data and computing gravity...\n")
    gravities, combined, tgs, teams_df = load_gravity()

    # Sanity checks (printed)
    check_model_fit(gravities)
    check_known_teams(gravities, combined)
    check_correlations(gravities)

    # CSV output
    save_csvs(gravities, combined)

    # Visualizations
    print("\n" + "=" * 90)
    print("GENERATING PLOTS")
    print("=" * 90)
    plot_tempo(gravities)
    for stat_key in gravities:
        if stat_key != "tempo":
            plot_paired_stat(gravities, stat_key)
    plot_distributions(gravities)
    plot_off_vs_def(gravities, "efficiency")
    plot_gravity_heatmap(combined)

    print("\nDone! All plots saved to plots/, CSVs saved to data/")
