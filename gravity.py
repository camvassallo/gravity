"""Compute gravity scores using ridge regression.

Gravity measures how much a team "pulls" a game toward their own tendencies.
For each stat, we fit:

    S_actual = mu + gamma_i * (S_i_avg - mu) + gamma_j * (S_j_avg - mu) + eps

where gamma_t is team t's gravity coefficient:
    ~1.0  = team fully imposes their tendency
    ~0.5  = splits the difference with opponent
    ~0.0  = no pull, dragged toward league mean
    >1.0  = over-imposes beyond their own average
"""

import warnings

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge

warnings.filterwarnings("ignore", category=RuntimeWarning, module="sklearn")

from torvik import fetch_game_stats, fetch_team_stats


# ---------------------------------------------------------------------------
# Data prep
# ---------------------------------------------------------------------------

_BOX_COLS = [
    "pts", "orb", "drb", "ast", "tov", "stl", "blk",
    "two_pm", "two_pa", "tpm", "tpa", "ftm", "fta",
]

# Stats where each team has its own value per game (offense vs opponent defense).
# Format: (name, off_col, def_col)
PAIRED_STATS = [
    ("efficiency", "off_eff", "def_eff"),
    ("efg", "efg", "opp_efg"),
    ("three_pt_rate", "tp_rate", "opp_tp_rate"),
    ("ft_rate", "ft_rate", "opp_ft_rate"),
    ("to_rate", "to_rate", "opp_to_rate"),
    ("orb_rate", "orb_rate", "opp_orb_rate"),
]


def build_team_game_stats(games: pd.DataFrame) -> pd.DataFrame:
    """Aggregate player-game rows into one row per team per game.

    Computes per-team-per-game stats and pairs each team with its opponent.
    """
    g = games.copy()
    for col in _BOX_COLS:
        g[col] = pd.to_numeric(g[col], errors="coerce")

    agg = g.groupby(["muid", "tt"])[_BOX_COLS].sum().reset_index()

    agg["fga"] = agg["two_pa"] + agg["tpa"]
    # Standard possessions estimate: FGA - OREB + TOV + 0.44 * FTA
    agg["poss"] = agg["fga"] - agg["orb"] + agg["tov"] + 0.44 * agg["fta"]
    # Drop rows with unreasonable possessions (bad data)
    agg.loc[agg["poss"] < 20, "poss"] = np.nan

    # Derived per-team-per-game stats
    agg["off_eff"] = agg["pts"] / agg["poss"] * 100
    agg["efg"] = np.where(agg["fga"] > 0, (agg["two_pm"] + 1.5 * agg["tpm"]) / agg["fga"] * 100, np.nan)
    agg["tp_rate"] = np.where(agg["fga"] > 0, agg["tpa"] / agg["fga"] * 100, np.nan)
    agg["ft_rate"] = np.where(agg["fga"] > 0, agg["fta"] / agg["fga"] * 100, np.nan)
    agg["to_rate"] = np.where(agg["poss"] > 0, agg["tov"] / agg["poss"] * 100, np.nan)
    # ORB rate needs opponent DRB, so we compute it after the merge

    # Keep only games with exactly 2 teams
    team_counts = agg.groupby("muid")["tt"].transform("count")
    agg = agg[team_counts == 2].copy()

    # Join opponent stats via self-merge
    opp_cols = ["muid", "tt", "poss", "off_eff", "pts", "efg", "tp_rate", "ft_rate", "to_rate", "orb", "drb"]
    opp = agg[opp_cols].rename(columns={
        "tt": "opp", "poss": "opp_poss", "off_eff": "opp_off_eff", "pts": "opp_pts",
        "efg": "opp_efg", "tp_rate": "opp_tp_rate", "ft_rate": "opp_ft_rate",
        "to_rate": "opp_to_rate", "orb": "opp_orb", "drb": "opp_drb",
    })
    merged = agg.merge(opp, on="muid")
    merged = merged[merged["tt"] != merged["opp"]].copy()

    # Shared game-level stat
    merged["game_pace"] = (merged["poss"] + merged["opp_poss"]) / 2

    # Defensive counterparts (opponent's offensive stat = your defensive stat)
    merged["def_eff"] = merged["opp_off_eff"]

    # Offensive rebound rate: your ORBs / (your ORBs + opponent DRBs)
    orb_total = merged["orb"] + merged["opp_drb"]
    merged["orb_rate"] = np.where(orb_total > 0, merged["orb"] / orb_total * 100, np.nan)
    opp_orb_total = merged["opp_orb"] + merged["drb"]
    merged["opp_orb_rate"] = np.where(opp_orb_total > 0, merged["opp_orb"] / opp_orb_total * 100, np.nan)

    return merged


# ---------------------------------------------------------------------------
# Gravity models
# ---------------------------------------------------------------------------

def compute_tempo_gravity(tgs: pd.DataFrame, alpha: float = 1.0) -> pd.DataFrame:
    """Compute pace/tempo gravity per team.

    Pace is a shared game-level stat (both teams play the same number of
    possessions), so each game yields one observation.
    """
    pace_avg = tgs.groupby("tt")["game_pace"].mean()
    mu = pace_avg.mean()

    teams = sorted(pace_avg.index)
    team_idx = {t: i for i, t in enumerate(teams)}
    n_teams = len(teams)

    # Deduplicate to one row per game
    games = tgs.drop_duplicates(subset="muid").dropna(subset=["game_pace"])
    games = games[games["tt"].isin(teams) & games["opp"].isin(teams)]

    n_obs = len(games)
    X = np.zeros((n_obs, n_teams))
    y = games["game_pace"].values

    tt_idx = games["tt"].map(team_idx).values
    opp_idx = games["opp"].map(team_idx).values
    tt_dev = games["tt"].map(pace_avg).values - mu
    opp_dev = games["opp"].map(pace_avg).values - mu

    X[np.arange(n_obs), tt_idx] = tt_dev
    X[np.arange(n_obs), opp_idx] = opp_dev

    model = Ridge(alpha=alpha, fit_intercept=True)
    model.fit(X, y)
    r2 = model.score(X, y)

    result = pd.DataFrame({
        "team": teams,
        "tempo_gravity": model.coef_,
        "avg_pace": [pace_avg[t] for t in teams],
    }).set_index("team").sort_values("tempo_gravity", ascending=False)
    result.attrs["r2"] = r2
    result.attrs["n_obs"] = n_obs
    return result


def compute_paired_gravity(
    tgs: pd.DataFrame, stat_name: str, off_col: str, def_col: str, alpha: float = 10.0,
) -> pd.DataFrame:
    """Compute offensive and defensive gravity for any paired stat.

    A 'paired stat' is one where team A's offense faces team B's defense:

        stat_actual = mu + gamma_off_A * (off_avg_A - mu_off)
                         + gamma_def_B * (def_avg_B - mu_def) + eps

    Args:
        tgs: team-game stats from build_team_game_stats()
        stat_name: human-readable name for the stat
        off_col: column in tgs for the team's offensive version of the stat
        def_col: column in tgs for the opponent's version (team's defensive stat)
        alpha: ridge regularization strength
    """
    off_avg = tgs.groupby("tt")[off_col].mean()
    def_avg = tgs.groupby("tt")[def_col].mean()
    mu_off = off_avg.mean()
    mu_def = def_avg.mean()

    teams = sorted(set(off_avg.dropna().index) & set(def_avg.dropna().index))
    team_idx = {t: i for i, t in enumerate(teams)}
    n_teams = len(teams)

    valid = tgs.dropna(subset=[off_col, def_col])
    valid = valid[np.isfinite(valid[off_col]) & np.isfinite(valid[def_col])]
    valid = valid[valid["tt"].isin(teams) & valid["opp"].isin(teams)]

    n_obs = len(valid)
    X = np.zeros((n_obs, 2 * n_teams))
    y = valid[off_col].values

    off_idx = valid["tt"].map(team_idx).values
    def_idx = valid["opp"].map(team_idx).values
    off_dev = valid["tt"].map(off_avg).values - mu_off
    def_dev = valid["opp"].map(def_avg).values - mu_def

    X[np.arange(n_obs), off_idx] = off_dev
    X[np.arange(n_obs), n_teams + def_idx] = def_dev

    model = Ridge(alpha=alpha, fit_intercept=True)
    model.fit(X, y)
    r2 = model.score(X, y)

    result = pd.DataFrame({
        "team": teams,
        f"{stat_name}_off_gravity": model.coef_[:n_teams],
        f"{stat_name}_def_gravity": model.coef_[n_teams:],
        f"{stat_name}_off_avg": [off_avg[t] for t in teams],
        f"{stat_name}_def_avg": [def_avg[t] for t in teams],
    }).set_index("team")
    result.attrs["r2"] = r2
    result.attrs["n_obs"] = n_obs
    result.attrs["stat_name"] = stat_name
    return result


def compute_all_gravities(tgs: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Compute gravity for tempo + all paired stats. Returns dict of DataFrames."""
    results = {}

    results["tempo"] = compute_tempo_gravity(tgs)

    for stat_name, off_col, def_col in PAIRED_STATS:
        results[stat_name] = compute_paired_gravity(tgs, stat_name, off_col, def_col)

    return results


def build_combined_table(gravities: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Merge all gravity results into one wide table (one row per team)."""
    tempo = gravities["tempo"][["tempo_gravity", "avg_pace"]]
    combined = tempo.copy()

    for key, df in gravities.items():
        if key == "tempo":
            continue
        name = df.attrs["stat_name"]
        combined = combined.join(df[[f"{name}_off_gravity", f"{name}_def_gravity"]], how="outer")

    return combined


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    year = 2026

    print("Loading data...")
    games = fetch_game_stats(year)
    teams = fetch_team_stats(year)

    print("Building team-game stats...")
    tgs = build_team_game_stats(games)
    print(f"  {tgs['muid'].nunique()} games, {tgs['tt'].nunique()} teams\n")

    gravities = compute_all_gravities(tgs)

    for key, df in gravities.items():
        r2 = df.attrs["r2"]
        n = df.attrs["n_obs"]
        print(f"  {key:<16} R² = {r2:.4f}  ({n} obs)")

    # Combined table
    combined = build_combined_table(gravities)
    out_path = "data/gravity_scores.csv"
    combined.to_csv(out_path)
    print(f"\nSaved combined gravity table -> {out_path}")
    print(f"  {combined.shape[0]} teams, {combined.shape[1]} columns")
    print(f"\nColumns: {list(combined.columns)}")
