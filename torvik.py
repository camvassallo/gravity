"""Fetch and cache Barttorvik college basketball data."""

import gzip
import io
import json
from pathlib import Path

import pandas as pd
import requests

BASE_URL = "https://barttorvik.com"
CACHE_DIR = Path(__file__).resolve().parent / "data"

PLAYER_STATS_COLUMNS = [
    "player_name", "team", "conf", "gp", "min_per", "o_rtg", "usg", "e_fg",
    "ts_per", "orb_per", "drb_per", "ast_per", "to_per", "ftm", "fta",
    "ft_per", "two_pm", "two_pa", "two_p_per", "tpm", "tpa", "tp_per",
    "blk_per", "stl_per", "ftr", "yr", "ht", "num", "porpag", "adjoe",
    "pfr", "year", "pid", "hometown", "rec_rank", "ast_tov", "rim_made",
    "rim_attempted", "mid_made", "mid_attempted", "rim_pct", "mid_pct",
    "dunks_made", "dunks_attempted", "dunk_pct", "pick", "drtg", "adrtg",
    "dporpag", "stops", "bpm", "obpm", "dbpm", "gbpm", "mp", "ogbpm",
    "dgbpm", "oreb", "dreb", "treb", "ast", "stl", "blk", "pts",
    "player_type", "coag", "dob",
]

TEAM_STATS_COLUMNS = [
    "rank", "team", "conf", "record", "adjoe", "adjoe_rank", "adjde",
    "adjde_rank", "barthag", "barthag_rank", "proj_wins", "proj_losses",
    "proj_conf_wins", "proj_conf_losses", "conf_record", "sos", "nconf_sos",
    "conf_sos", "proj_sos", "proj_nconf_sos", "proj_conf_sos", "elite_sos",
    "elite_ncsos", "opp_adjoe", "opp_adjde", "opp_proj_adjoe", "opp_proj_adjde",
    "conf_adjoe", "conf_adjde", "qual_adjoe", "qual_adjde", "qual_barthag",
    "qual_games", "fun", "fun_rank", "conf_pf", "conf_pa", "conf_poss",
    "conf_adj_o", "conf_adj_d", "conf_sos_remain", "conf_win_perc", "wab",
    "wab_rank", "adj_tempo",
]

GAME_STATS_COLUMNS = [
    "numdate", "datetext", "opstyle", "quality", "win1", "opponent", "muid",
    "win2", "min_per", "o_rtg", "usage", "e_fg", "ts_per", "orb_per",
    "drb_per", "ast_per", "to_per", "dunks_made", "dunks_att", "rim_made",
    "rim_att", "mid_made", "mid_att", "two_pm", "two_pa", "tpm", "tpa",
    "ftm", "fta", "bpm_rd", "obpm", "dbpm", "bpm_net", "pts", "orb", "drb",
    "ast", "tov", "stl", "blk", "stl_per", "blk_per", "pf", "possessions",
    "bpm", "sbpm", "loc", "tt", "pp", "inches", "cls", "pid", "year",
]


def _cache_path(year: int, name: str) -> Path:
    return CACHE_DIR / f"{year}_{name}.csv"


def _ensure_cache_dir() -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)


def fetch_player_stats(year: int = 2026, force_refresh: bool = False) -> pd.DataFrame:
    """Fetch season-level player stats. Returns cached CSV if available."""
    path = _cache_path(year, "player_stats")
    if path.exists() and not force_refresh:
        return pd.read_csv(path)

    url = f"{BASE_URL}/getadvstats.php?year={year}&csv=1"
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()

    df = pd.read_csv(io.StringIO(resp.text), header=None, names=PLAYER_STATS_COLUMNS)

    _ensure_cache_dir()
    df.to_csv(path, index=False)
    print(f"Cached {len(df)} player rows -> {path}")
    return df


def fetch_team_stats(year: int = 2026, force_refresh: bool = False) -> pd.DataFrame:
    """Fetch team-level rankings and efficiency metrics. Returns cached CSV if available."""
    path = _cache_path(year, "team_stats")
    if path.exists() and not force_refresh:
        return pd.read_csv(path)

    url = f"{BASE_URL}/{year}_team_results.json"
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()

    rows = resp.json()
    n_cols = len(rows[0]) if rows else len(TEAM_STATS_COLUMNS)
    df = pd.DataFrame(rows, columns=TEAM_STATS_COLUMNS[:n_cols])

    _ensure_cache_dir()
    df.to_csv(path, index=False)
    print(f"Cached {len(df)} team rows -> {path}")
    return df


def fetch_game_stats(year: int = 2026, force_refresh: bool = False) -> pd.DataFrame:
    """Fetch per-game per-player box scores. Returns cached CSV if available."""
    path = _cache_path(year, "game_stats")
    if path.exists() and not force_refresh:
        return pd.read_csv(path, low_memory=False)

    url = f"{BASE_URL}/{year}_all_advgames.json.gz"
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()

    # Server or requests may auto-decompress; try raw first, fall back to gzip
    try:
        rows = json.loads(resp.content)
    except (json.JSONDecodeError, UnicodeDecodeError):
        raw = gzip.decompress(resp.content)
        rows = json.loads(raw)

    df = pd.DataFrame(rows, columns=GAME_STATS_COLUMNS[:len(rows[0])] if rows else GAME_STATS_COLUMNS)

    _ensure_cache_dir()
    df.to_csv(path, index=False)
    print(f"Cached {len(df)} game rows -> {path}")
    return df


def fetch_all_for_year(year: int = 2026, force_refresh: bool = False) -> dict:
    """Fetch all data types for a given year. Returns dict with keys: players, teams, games."""
    return {
        "players": fetch_player_stats(year, force_refresh),
        "teams": fetch_team_stats(year, force_refresh),
        "games": fetch_game_stats(year, force_refresh),
    }


if __name__ == "__main__":
    year = 2026

    print("Fetching player stats...")
    players = fetch_player_stats(year)
    print(f"  {players.shape[0]} players, {players.shape[1]} columns\n")

    print("Fetching team stats...")
    teams = fetch_team_stats(year)
    print(f"  {teams.shape[0]} teams, {teams.shape[1]} columns\n")

    print("Fetching game stats...")
    games = fetch_game_stats(year)
    print(f"  {games.shape[0]} game rows, {games.shape[1]} columns\n")

    print("Sample player stats:")
    print(players[["player_name", "team", "pts", "ast", "treb"]].head(10))
