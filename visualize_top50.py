"""Visualize gravity profiles for the top 50 teams."""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
import numpy as np
import pandas as pd
from pathlib import Path

from torvik import fetch_game_stats, fetch_team_stats
from gravity import build_team_game_stats, compute_all_gravities, build_combined_table, PAIRED_STATS

OUT_DIR = Path(__file__).resolve().parent / "plots"
CSV_DIR = Path(__file__).resolve().parent / "data"
OUT_DIR.mkdir(exist_ok=True)
CSV_DIR.mkdir(exist_ok=True)

STAT_LABELS = {
    "efficiency": "Efficiency",
    "efg": "eFG%",
    "three_pt_rate": "3pt Rate",
    "ft_rate": "FT Rate",
    "to_rate": "TO Rate",
    "orb_rate": "ORB Rate",
}

# Stats where LOWER offensive value = better (inverted for impact score)
INVERT_OFF = {"to_rate"}
# Stats where LOWER defensive value = better (inverted for impact score)
# def_eff, opp_efg, opp_tp_rate, opp_ft_rate, opp_orb_rate = opponent's stat, so lower = better defense
# opp_to_rate = opponent TOs, higher = better defense
INVERT_DEF = {"efficiency", "efg", "three_pt_rate", "ft_rate", "orb_rate"}


def load_data():
    games = fetch_game_stats(2026)
    teams = fetch_team_stats(2026)
    tgs = build_team_game_stats(games)
    gravities = compute_all_gravities(tgs)
    combined = build_combined_table(gravities)

    # Get top 50 by Torvik rank
    top50 = teams.nsmallest(50, "rank")[["team", "rank", "conf", "record", "adjoe", "adjde", "adj_tempo"]].copy()
    top50 = top50.set_index("team")

    return gravities, combined, top50, tgs


def compute_impact_scores(gravities, top50):
    """Compute impact = gravity × quality_direction for each stat.

    Positive impact = reliably good at this stat.
    Negative impact = reliably bad at this stat.
    Near zero = either average, or no gravity, or both.
    """
    teams = top50.index
    impact = pd.DataFrame(index=teams)

    # Tempo: positive deviation from mean = fast, but fast/slow isn't inherently good/bad
    # Use absolute gravity instead — tempo gravity just means "imposes pace" regardless of direction
    tempo = gravities["tempo"]
    impact["tempo"] = tempo.reindex(teams)["tempo_gravity"]

    for stat_name, off_col, def_col in PAIRED_STATS:
        df = gravities[stat_name]
        label = STAT_LABELS.get(stat_name, stat_name)
        off_grav_col = f"{stat_name}_off_gravity"
        def_grav_col = f"{stat_name}_def_gravity"
        off_avg_col = f"{stat_name}_off_avg"
        def_avg_col = f"{stat_name}_def_avg"

        df_top = df.reindex(teams)

        # Offensive impact: gravity × z-score (direction-adjusted)
        off_avg = df[off_avg_col]
        off_z = (df_top[off_avg_col] - off_avg.mean()) / off_avg.std()
        if stat_name in INVERT_OFF:
            off_z = -off_z  # lower TO rate = better
        impact[f"{label} (Off)"] = df_top[off_grav_col] * off_z

        # Defensive impact: gravity × z-score (direction-adjusted)
        def_avg = df[def_avg_col]
        def_z = (df_top[def_avg_col] - def_avg.mean()) / def_avg.std()
        if stat_name in INVERT_DEF:
            def_z = -def_z  # lower opponent stats = better defense
        impact[f"{label} (Def)"] = df_top[def_grav_col] * def_z

    return impact


def compute_gravity_ranking(gravities, top50):
    """Compute gravity-adjusted efficiency ranking.

    Blends Torvik's SOS-adjusted efficiency margin with overall gravity
    to create a "trustworthiness-weighted" ranking.

    adj_margin = adjOE - adjDE  (Torvik, SOS-adjusted)
    avg_gravity = mean gravity across all stat categories
    blended = adj_margin * (1 + λ * gravity_z)

    λ = 0.15 means gravity can adjust the margin by ~±30% at the extremes.
    """
    teams = top50.index

    # --- Torvik efficiency margin (SOS-adjusted baseline) ---
    adj_margin = top50["adjoe"] - top50["adjde"]

    # --- Overall gravity: mean across all stat categories ---
    # Tempo gravity
    tempo_grav = gravities["tempo"].reindex(teams)["tempo_gravity"]

    # Paired stat gravities (average of off + def for each)
    all_gravs = [tempo_grav]
    for stat_name, _, _ in PAIRED_STATS:
        df = gravities[stat_name].reindex(teams)
        off_g = df[f"{stat_name}_off_gravity"]
        def_g = df[f"{stat_name}_def_gravity"]
        all_gravs.append((off_g + def_g) / 2)

    avg_gravity = pd.concat(all_gravs, axis=1).mean(axis=1)

    # Z-score of gravity (among these 50 teams)
    gravity_z = (avg_gravity - avg_gravity.mean()) / avg_gravity.std()

    # Blended score: quality × confidence
    lam = 0.15
    blended = adj_margin * (1 + lam * gravity_z)

    ranking = pd.DataFrame({
        "adj_margin": adj_margin,
        "avg_gravity": avg_gravity,
        "gravity_z": gravity_z,
        "blended_score": blended,
        "torvik_rank": top50["rank"],
    }, index=teams)

    ranking["gravity_rank"] = ranking["blended_score"].rank(ascending=False).astype(int)
    ranking = ranking.sort_values("blended_score", ascending=False)

    return ranking


def plot_bubble_scatter(gravities, combined, top50):
    """Off efficiency vs Def efficiency, sized by total gravity."""
    teams = top50.index

    # Get efficiency gravities
    eff = gravities["efficiency"].reindex(teams)

    # Total gravity magnitude across all paired stats
    grav_cols = [c for c in combined.columns if "gravity" in c]
    total_grav = combined.reindex(teams)[grav_cols].abs().mean(axis=1)

    # Use raw off/def efficiency from the gravity data
    off_eff = eff["efficiency_off_avg"]
    def_eff = eff["efficiency_def_avg"]

    fig, ax = plt.subplots(figsize=(14, 10))

    # Size proportional to total gravity, min size for visibility
    sizes = (total_grav - total_grav.min()) / (total_grav.max() - total_grav.min())
    sizes = 80 + sizes * 500

    # Color by offensive gravity specifically (how much they impose offensively)
    off_grav = eff["efficiency_off_gravity"]

    scatter = ax.scatter(
        off_eff, def_eff, s=sizes, c=off_grav,
        cmap="RdYlGn", alpha=0.75, edgecolors="black", linewidths=0.5,
        vmin=0, vmax=2.5,
    )

    # Label every team
    for team in teams:
        if team not in off_eff.index:
            continue
        x, y = off_eff[team], def_eff[team]
        ax.annotate(
            team, (x, y), fontsize=6.5, ha="center", va="bottom",
            xytext=(0, 6), textcoords="offset points",
            path_effects=[pe.withStroke(linewidth=2, foreground="white")],
        )

    # Axis labels and formatting
    ax.set_xlabel("Offensive Efficiency (pts/100 poss) →  better offense →", fontsize=11)
    ax.set_ylabel("← better defense  ←  Defensive Efficiency (opp pts/100 poss)", fontsize=11)
    ax.set_title("Top 50 Teams: Efficiency Profile\nSize = overall gravity magnitude, Color = offensive efficiency gravity", fontsize=13)
    ax.invert_yaxis()  # Lower defensive efficiency = better, so invert

    cbar = fig.colorbar(scatter, ax=ax, shrink=0.6, label="Off. Efficiency Gravity")

    # Add quadrant labels
    xmid = off_eff.median()
    ymid = def_eff.median()
    ax.axhline(ymid, color="gray", linewidth=0.5, linestyle="--", alpha=0.5)
    ax.axvline(xmid, color="gray", linewidth=0.5, linestyle="--", alpha=0.5)

    fig.tight_layout()
    fig.savefig(OUT_DIR / "top50_bubble_efficiency.png", dpi=150, bbox_inches="tight")
    print(f"  Saved {OUT_DIR / 'top50_bubble_efficiency.png'}")
    plt.close(fig)


def plot_impact_heatmap(impact, top50, gravities, ranking=None):
    """Heatmap: rows = teams (ranked), columns = stat categories.

    Tempo column uses a red/blue gradient (fast/slow, neither inherently better).
    Impact columns use green/red gradient (reliably good / reliably bad).
    Axis labels on both top and bottom.

    If ranking is provided, teams are ordered by gravity-adjusted rank and labels
    show both Torvik rank and gravity rank.
    """
    from matplotlib.gridspec import GridSpec
    from matplotlib.colors import Normalize
    import matplotlib.cm as cm

    if ranking is not None:
        ranked_teams = ranking.index  # already sorted by blended score
        labels = [
            f"{ranking.loc[t, 'gravity_rank']}. {t}  "
            f"(T{top50.loc[t, 'rank']:.0f}, {top50.loc[t, 'conf']}, {top50.loc[t, 'record']})"
            for t in ranked_teams
        ]
    else:
        ranked_teams = top50.sort_values("rank").index
        labels = [
            f"{top50.loc[t, 'rank']:.0f}. {t}  ({top50.loc[t, 'conf']}, {top50.loc[t, 'record']})"
            for t in ranked_teams
        ]

    impact_sorted = impact.reindex(ranked_teams)

    # --- Tempo column data ---
    tempo_df = gravities["tempo"]
    pace_avg = tempo_df["avg_pace"]
    pace_z = (pace_avg - pace_avg.mean()) / pace_avg.std()
    # Tempo impact: gravity × pace direction (positive = consistently fast, negative = consistently slow)
    tempo_impact = (tempo_df["tempo_gravity"] * pace_z).reindex(ranked_teams)

    # --- Paired stat impact data ---
    paired_cols = [c for c in impact_sorted.columns if c != "tempo"]
    paired_data = impact_sorted[paired_cols]

    # --- Column grouping headers ---
    # Map each column to its stat group
    group_spans = []  # (start_col, end_col, label)
    col_idx = 0
    for stat_name, _, _ in PAIRED_STATS:
        label = STAT_LABELS.get(stat_name, stat_name)
        group_spans.append((col_idx, col_idx + 1, label))
        col_idx += 2

    # Shorter column sub-labels
    short_cols = []
    for c in paired_cols:
        if "(Off)" in c:
            short_cols.append("Off")
        elif "(Def)" in c:
            short_cols.append("Def")
        else:
            short_cols.append(c)

    # --- Layout ---
    n_teams = len(ranked_teams)
    n_paired = len(paired_cols)

    fig = plt.figure(figsize=(18, 20))
    gs = GridSpec(1, 2, width_ratios=[1, n_paired], wspace=0.02, figure=fig)

    ax_tempo = fig.add_subplot(gs[0, 0])
    ax_impact = fig.add_subplot(gs[0, 1])

    # --- Draw tempo column (RdBu) ---
    tempo_vals = tempo_impact.values.reshape(-1, 1)
    tempo_vmax = max(abs(np.nanmin(tempo_vals)), abs(np.nanmax(tempo_vals)))
    im_tempo = ax_tempo.imshow(
        tempo_vals, cmap="coolwarm", aspect="auto",
        vmin=-tempo_vmax, vmax=tempo_vmax,
    )

    # Tempo labels and values
    ax_tempo.set_xticks([0])
    ax_tempo.set_xticklabels(["Tempo"], fontsize=9, fontweight="bold")
    ax_tempo.tick_params(top=True, bottom=True, labeltop=True, labelbottom=True)
    ax_tempo.xaxis.set_label_position("top")

    ax_tempo.set_yticks(range(n_teams))
    ax_tempo.set_yticklabels(labels, fontsize=7)

    for i in range(n_teams):
        val = tempo_vals[i, 0]
        if np.isfinite(val):
            color = "white" if abs(val) > tempo_vmax * 0.55 else "black"
            ax_tempo.text(0, i, f"{val:.1f}", ha="center", va="center", fontsize=6.5, color=color)

    # Horizontal grid lines for readability
    for i in range(n_teams):
        ax_tempo.axhline(i - 0.5, color="white", linewidth=0.3)

    # --- Draw impact columns (RdYlGn) ---
    data_vals = paired_data.values
    impact_vmax = np.nanpercentile(np.abs(data_vals), 95)

    im_impact = ax_impact.imshow(
        data_vals, cmap="RdYlGn", aspect="auto",
        vmin=-impact_vmax, vmax=impact_vmax,
    )

    # Bottom x-axis labels
    ax_impact.set_xticks(range(n_paired))
    ax_impact.set_xticklabels(short_cols, fontsize=8)
    ax_impact.tick_params(top=True, bottom=True, labeltop=True, labelbottom=True)

    # Top x-axis labels (same)
    ax_impact.xaxis.set_ticks_position("both")
    ax_top = ax_impact.secondary_xaxis("top")
    ax_top.set_xticks(range(n_paired))
    ax_top.set_xticklabels(short_cols, fontsize=8)

    # No y-axis labels on impact (shared with tempo)
    ax_impact.set_yticks(range(n_teams))
    ax_impact.set_yticklabels([])

    # Cell values
    for i in range(n_teams):
        for j in range(n_paired):
            val = data_vals[i, j]
            if np.isfinite(val):
                color = "white" if abs(val) > impact_vmax * 0.6 else "black"
                ax_impact.text(j, i, f"{val:.1f}", ha="center", va="center", fontsize=6.5, color=color)

    # Horizontal grid lines
    for i in range(n_teams):
        ax_impact.axhline(i - 0.5, color="white", linewidth=0.3)

    # Vertical separators between stat groups (every 2 columns)
    for col_start in range(2, n_paired, 2):
        ax_impact.axvline(col_start - 0.5, color="white", linewidth=1.5)

    # Stat group headers above top labels
    for start, end, label in group_spans:
        mid = (start + end) / 2
        ax_impact.text(
            mid, -2.0, label, ha="center", va="bottom",
            fontsize=9, fontweight="bold",
            transform=ax_impact.transData,
        )

    # --- Colorbars ---
    # Tempo colorbar (left)
    cbar_tempo = fig.colorbar(im_tempo, ax=ax_tempo, shrink=0.3, pad=0.02, location="bottom")
    cbar_tempo.set_label("← slow imposer      fast imposer →", fontsize=8)
    cbar_tempo.ax.tick_params(labelsize=7)

    # Impact colorbar (right)
    cbar_impact = fig.colorbar(im_impact, ax=ax_impact, shrink=0.3, pad=0.02, location="bottom")
    cbar_impact.set_label("← reliably bad      reliably good →", fontsize=8)
    cbar_impact.ax.tick_params(labelsize=7)

    if ranking is not None:
        title = (
            "Gravity Impact — Top 50 Teams (2025-26)\n"
            "Ordered by gravity-adjusted efficiency (T# = Torvik rank)  |  "
            "λ = 0.15\n"
            "Tempo: blue = consistently slow, red = consistently fast  |  "
            "Stats: green = reliably good, red = reliably bad"
        )
    else:
        title = (
            "Gravity Impact — Top 50 Teams (2025-26)\n"
            "Tempo: blue = consistently slow, red = consistently fast\n"
            "Stats: green = strong AND consistent, red = weak AND consistent"
        )
    fig.suptitle(title, fontsize=13, y=0.995, fontweight="bold")

    fig.savefig(OUT_DIR / "top50_impact_heatmap.png", dpi=150, bbox_inches="tight")
    print(f"  Saved {OUT_DIR / 'top50_impact_heatmap.png'}")
    plt.close(fig)


def plot_gravity_consistency(gravities, top50):
    """For each stat: scatter of stat level vs gravity, only for top 50.

    Small multiples — one panel per paired stat showing off and def side by side.
    """
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    axes = axes.flatten()

    teams = top50.index

    for i, (stat_name, off_col, def_col) in enumerate(PAIRED_STATS):
        df = gravities[stat_name].reindex(teams)
        label = STAT_LABELS.get(stat_name, stat_name)
        off_grav = f"{stat_name}_off_gravity"
        def_grav = f"{stat_name}_def_gravity"
        off_avg = f"{stat_name}_off_avg"
        def_avg = f"{stat_name}_def_avg"

        ax = axes[i]

        # Offensive: circles
        ax.scatter(df[off_avg], df[off_grav], alpha=0.6, s=40, c="#dc2626", label="Offense", zorder=3)
        # Defensive: triangles
        ax.scatter(df[def_avg], df[def_grav], alpha=0.6, s=40, c="#2563eb", marker="^", label="Defense", zorder=3)

        ax.axhline(1.0, color="gray", linewidth=0.5, linestyle="--", alpha=0.5)
        ax.axhline(0, color="gray", linewidth=0.5, linestyle=":", alpha=0.3)

        # Label extremes
        for col_g, col_a, color in [(off_grav, off_avg, "#dc2626"), (def_grav, def_avg, "#2563eb")]:
            combined = np.sqrt((df[col_a] - df[col_a].mean())**2 + (df[col_g] - df[col_g].mean())**2)
            for idx in combined.nlargest(3).index:
                ax.annotate(
                    idx, (df.loc[idx, col_a], df.loc[idx, col_g]),
                    fontsize=6, ha="left", va="bottom", color=color,
                    xytext=(3, 3), textcoords="offset points",
                )

        ax.set_xlabel(f"{label} (season avg)")
        ax.set_ylabel("Gravity")
        ax.set_title(label, fontsize=11)
        ax.legend(fontsize=7, loc="upper left")

    fig.suptitle("Top 50 Teams: Stat Level vs Gravity\nAbove 1.0 = imposes their level, below 1.0 = gets pulled by opponents", fontsize=13)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "top50_stat_vs_gravity.png", dpi=150, bbox_inches="tight")
    print(f"  Saved {OUT_DIR / 'top50_stat_vs_gravity.png'}")
    plt.close(fig)


if __name__ == "__main__":
    print("Loading data...\n")
    gravities, combined, top50, tgs = load_data()
    print(f"Top 50 teams (by Torvik rank):\n")

    # Compute and save impact scores
    impact = compute_impact_scores(gravities, top50)
    impact.to_csv(CSV_DIR / "top50_impact_scores.csv")
    print(f"Saved impact scores -> {CSV_DIR / 'top50_impact_scores.csv'}")

    # Compute gravity-adjusted ranking
    ranking = compute_gravity_ranking(gravities, top50)
    ranking.to_csv(CSV_DIR / "top50_gravity_ranking.csv")
    print(f"Saved gravity ranking -> {CSV_DIR / 'top50_gravity_ranking.csv'}")

    # Show biggest movers
    ranking["delta"] = ranking["torvik_rank"] - ranking["gravity_rank"]
    risers = ranking.nlargest(5, "delta")[["torvik_rank", "gravity_rank", "delta", "avg_gravity", "blended_score"]]
    fallers = ranking.nsmallest(5, "delta")[["torvik_rank", "gravity_rank", "delta", "avg_gravity", "blended_score"]]
    print("\nBiggest risers (gravity-adjusted vs Torvik):")
    print(risers.to_string())
    print("\nBiggest fallers:")
    print(fallers.to_string())
    print()

    print("Generating plots...")
    plot_bubble_scatter(gravities, combined, top50)
    plot_impact_heatmap(impact, top50, gravities, ranking=ranking)
    plot_gravity_consistency(gravities, top50)

    print("\nDone!")
