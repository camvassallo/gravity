"""Single-game prediction CLI.

Usage:
    python game_predictor.py "Duke" "North Carolina" --location H
    python game_predictor.py "Houston" "Auburn" --location N
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd
from torvik import fetch_team_stats, fetch_player_stats, fetch_player_stats_daterange
from predict import GamePredictor, build_player_features, _TORVIK_COLS, _TEAM_DIFF_STATS

CONFIG_DIR = Path(__file__).resolve().parent / "config"


def load_injuries(year: int) -> dict | None:
    """Load player exclusions from config/injuries.json."""
    path = CONFIG_DIR / "injuries.json"
    if not path.exists():
        return None
    with open(path) as f:
        data = json.load(f)
    exclusions = data.get(str(year), {})
    return exclusions if exclusions else None


def load_injury_weights(year: int) -> dict | None:
    """Load partial-availability weights from config/injuries.json."""
    path = CONFIG_DIR / "injuries.json"
    if not path.exists():
        return None
    with open(path) as f:
        data = json.load(f)
    weights = data.get(f"_weights_{year}", {})
    return weights if weights else None


def predict_game(team1: str, team2: str, location: str = "N", year: int = 2026):
    """Predict a single game and display results."""
    predictor = GamePredictor.load()

    teams_df = fetch_team_stats(year).set_index("team")
    players_df = fetch_player_stats(year)
    exclusions = load_injuries(year)
    weights = load_injury_weights(year)

    # Recent 30-day window for form features
    cutoff_dt = pd.to_datetime("20260316", format="%Y%m%d")
    recent_start = (cutoff_dt - pd.Timedelta(days=30)).strftime("%Y%m%d")
    try:
        recent_players_df = fetch_player_stats_daterange(year, recent_start, "20260316")
    except Exception:
        recent_players_df = None

    player_feats = build_player_features(players_df, recent_players_df=recent_players_df,
                                         exclusions=exclusions, weights=weights)

    # Validate teams
    for team in [team1, team2]:
        if team not in teams_df.index:
            print(f"Error: '{team}' not found in Torvik data.")
            print(f"Available teams (first 20): {list(teams_df.index[:20])}")
            sys.exit(1)

    # Build team data dicts
    def get_torvik(team):
        return {s: pd.to_numeric(teams_df.loc[team, s], errors="coerce")
                for s in _TORVIK_COLS + _TEAM_DIFF_STATS if s in teams_df.columns}

    t1_torvik = get_torvik(team1)
    t2_torvik = get_torvik(team2)
    t1_players = player_feats.get(team1, {})
    t2_players = player_feats.get(team2, {})

    loc_val = {"H": 1, "A": -1, "N": 0}.get(location.upper(), 0)

    # Predict
    result = predictor.predict_game(t1_torvik, t2_torvik, t1_players, t2_players, loc_val)

    # Display
    loc_label = {"H": f"{team1} Home", "A": f"{team1} Away", "N": "Neutral"}.get(location.upper(), "Neutral")
    print(f"\n{'=' * 60}")
    print(f"  {team1}  vs  {team2}")
    print(f"  Location: {loc_label}")
    print(f"{'=' * 60}")

    print(f"\n  Win Probability:")
    print(f"    {team1:<25} {result['win_prob']:.1%}")
    print(f"    {team2:<25} {1 - result['win_prob']:.1%}")

    spread = result["spread"]
    favored = team1 if spread > 0 else team2
    print(f"\n  Predicted Spread: {favored} by {abs(spread):.1f}")
    print(f"  Spread Sigma:     {result['spread_sigma']:.1f} pts")

    print(f"\n  Predicted Score:")
    print(f"    {team1:<25} {result['t1_score']:.0f}")
    print(f"    {team2:<25} {result['t2_score']:.0f}")
    print(f"    Total:{'':>16} {result['predicted_total']:.0f}")

    # Torvik comparison
    print(f"\n  Torvik Ratings:")
    print(f"    {'':>25} {'AdjOE':>6} {'AdjDE':>6} {'Barthag':>8} {'Tempo':>6} {'SOS':>6}")
    for team, tv in [(team1, t1_torvik), (team2, t2_torvik)]:
        print(f"    {team:<25} {tv.get('adjoe', 0):>6.1f} {tv.get('adjde', 0):>6.1f} "
              f"{tv.get('barthag', 0):>8.4f} {tv.get('adj_tempo', 0):>6.1f} {tv.get('sos', 0):>6.3f}")

    # Team quality stats
    print(f"\n  Team Quality:")
    print(f"    {'':>25} {'Fun':>7} {'EliteSOS':>9} {'QualGames':>10} {'WAB':>5}")
    for team, tv in [(team1, t1_torvik), (team2, t2_torvik)]:
        print(f"    {team:<25} {tv.get('fun', 0):>7.4f} {tv.get('elite_sos', 0):>9.4f} "
              f"{tv.get('qual_games', 0):>10.0f} {tv.get('wab', 0):>5.1f}")

    # Player comparison
    print(f"\n  Top Player Stats:")
    print(f"    {'':>25} {'Top5 BPM':>9} {'Wt BPM':>7} {'BPM Trnd':>9} {'PPG Trnd':>9}")
    for team, pf in [(team1, t1_players), (team2, t2_players)]:
        print(f"    {team:<25} {pf.get('top5_bpm_sum', 0):>9.1f} {pf.get('top5_bpm_weighted', 0):>7.1f} "
              f"{pf.get('top5_bpm_trend', 0):>9.1f} {pf.get('top_porpag_trend', 0):>9.2f}")
    print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Predict a college basketball game")
    parser.add_argument("team1", help="First team name")
    parser.add_argument("team2", help="Second team name")
    parser.add_argument("--location", "-l", default="N", choices=["H", "A", "N"],
                        help="Location: H=team1 home, A=team1 away, N=neutral (default)")
    parser.add_argument("--year", "-y", type=int, default=2026, help="Season year (default: 2026)")
    args = parser.parse_args()

    predict_game(args.team1, args.team2, args.location, args.year)
