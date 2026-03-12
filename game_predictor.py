"""Phase 4: Single-game prediction CLI.

Usage:
    python game_predictor.py "Duke" "North Carolina" --location H
    python game_predictor.py "Houston" "Auburn" --location N
"""

from __future__ import annotations

import argparse
import sys

from gravity import run_gravity_pipeline
from torvik import fetch_team_stats
from predict import GamePredictor


def predict_game(team1: str, team2: str, location: str = "N", year: int = 2026):
    """Predict a single game and display results."""
    # Load model
    predictor = GamePredictor.load()

    # Load gravity and Torvik data
    tgs, gravities, combined = run_gravity_pipeline(year)
    teams_df = fetch_team_stats(year).set_index("team")

    grav_cols = [c for c in combined.columns if "gravity" in c]

    # Validate teams
    for team in [team1, team2]:
        if team not in combined.index:
            print(f"Error: '{team}' not found in gravity data.")
            print(f"Available teams (first 20): {list(combined.index[:20])}")
            sys.exit(1)
        if team not in teams_df.index:
            print(f"Error: '{team}' not found in Torvik data.")
            sys.exit(1)

    # Get team data
    t1_grav = {col: combined.loc[team1, col] for col in grav_cols}
    t2_grav = {col: combined.loc[team2, col] for col in grav_cols}
    t1_torvik = {s: teams_df.loc[team1, s] for s in ["adjoe", "adjde", "barthag", "adj_tempo", "sos"]
                 if s in teams_df.columns}
    t2_torvik = {s: teams_df.loc[team2, s] for s in ["adjoe", "adjde", "barthag", "adj_tempo", "sos"]
                 if s in teams_df.columns}

    loc_val = {"H": 1, "A": -1, "N": 0}.get(location.upper(), 0)

    # Predict
    result = predictor.predict_game(t1_grav, t2_grav, t1_torvik, t2_torvik, loc_val)

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
    print(f"  Spread Win Prob:  {result['spread_win_prob']:.1%} ({team1})")

    print(f"\n  Predicted Score:")
    print(f"    {team1:<25} {result['t1_score']:.0f}")
    print(f"    {team2:<25} {result['t2_score']:.0f}")
    print(f"    Total:{'':>16} {result['predicted_total']:.0f}")

    # Key gravity matchup factors
    print(f"\n  Key Gravity Matchups:")
    stat_names = ["efficiency", "efg", "three_pt_rate", "to_rate", "orb_rate",
                  "ast_rate", "stl_rate", "two_pt_pct"]
    for stat in stat_names:
        t1_off = t1_grav.get(f"{stat}_off_gravity", 0)
        t2_def = t2_grav.get(f"{stat}_def_gravity", 0)
        t2_off = t2_grav.get(f"{stat}_off_gravity", 0)
        t1_def = t1_grav.get(f"{stat}_def_gravity", 0)

        # Show where there's a significant gravity mismatch
        matchup1 = t1_off - t2_def  # positive = t1 offense dominates
        matchup2 = t2_off - t1_def  # positive = t2 offense dominates
        if abs(matchup1) > 0.3 or abs(matchup2) > 0.3:
            edge1 = f"{team1} +{matchup1:.2f}" if matchup1 > 0 else f"{team2} +{-matchup1:.2f}"
            edge2 = f"{team2} +{matchup2:.2f}" if matchup2 > 0 else f"{team1} +{-matchup2:.2f}"
            print(f"    {stat:<15} Off edge: {edge1:<20} | {edge2}")

    # Torvik comparison
    print(f"\n  Torvik Ratings:")
    print(f"    {'':>25} {'AdjOE':>6} {'AdjDE':>6} {'Barthag':>8} {'Tempo':>6}")
    print(f"    {team1:<25} {t1_torvik.get('adjoe', 0):>6.1f} {t1_torvik.get('adjde', 0):>6.1f} "
          f"{t1_torvik.get('barthag', 0):>8.4f} {t1_torvik.get('adj_tempo', 0):>6.1f}")
    print(f"    {team2:<25} {t2_torvik.get('adjoe', 0):>6.1f} {t2_torvik.get('adjde', 0):>6.1f} "
          f"{t2_torvik.get('barthag', 0):>8.4f} {t2_torvik.get('adj_tempo', 0):>6.1f}")
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
