"""Score a bracket simulation against actual tournament results.

Trains the model on pre-tournament data, simulates the bracket,
generates picks, and scores against actual results.

Usage:
    python score_bracket.py
"""

from __future__ import annotations

import json
import numpy as np
import pandas as pd
from pathlib import Path

from gravity import run_gravity_pipeline
from torvik import fetch_team_stats, fetch_player_stats
from predict import GamePredictor, build_player_features, _TORVIK_COLS, _TEAM_DIFF_STATS
from bracket import BracketSimulator, ROUND_NAMES

BRACKETS_DIR = Path(__file__).resolve().parent / "brackets"

# ESPN standard scoring
ROUND_POINTS = {
    "R32": 10,
    "S16": 20,
    "E8": 40,
    "F4": 80,
    "Championship": 160,
    "Champion": 320,
}

TOURNAMENT_CUTOFFS = {
    2024: 20240318,
    2025: 20250317,
}

# 2025 actual results: team -> furthest round reached
ACTUAL_RESULTS_2025 = {
    # Champion
    "Florida": "Champion",
    # Runner-up (lost in Championship)
    "Houston": "Championship",
    # Final Four (lost in F4)
    "Auburn": "F4",
    "Duke": "F4",
    # Elite Eight (lost in E8)
    "Michigan St.": "E8",
    "Tennessee": "E8",
    "Texas Tech": "E8",
    "Alabama": "E8",
    # Sweet 16 (lost in S16)
    "Michigan": "S16",
    "Mississippi": "S16",
    "Purdue": "S16",
    "Kentucky": "S16",
    "Maryland": "S16",
    "Arkansas": "S16",
    "Arizona": "S16",
    "BYU": "S16",
    # Round of 32 (lost in R32)
    "Creighton": "R32",
    "New Mexico": "R32",
    "Iowa St.": "R32",
    "Texas A&M": "R32",
    "Gonzaga": "R32",
    "McNeese St.": "R32",
    "Illinois": "R32",
    "UCLA": "R32",
    "Connecticut": "R32",
    "Colorado St.": "R32",
    "Drake": "R32",
    "St. John's": "R32",
    "Baylor": "R32",
    "Oregon": "R32",
    "Wisconsin": "R32",
    "Saint Mary's": "R32",
    # Round of 64 (lost in R64)
    "Alabama St.": "R64",
    "Louisville": "R64",
    "UC San Diego": "R64",
    "Yale": "R64",
    "North Carolina": "R64",
    "Lipscomb": "R64",
    "Bryant": "R64",
    "Marquette": "R64",
    "Mount St. Mary's": "R64",
    "Mississippi St.": "R64",
    "Liberty": "R64",
    "Akron": "R64",
    "VCU": "R64",
    "Montana": "R64",
    "Robert Morris": "R64",
    "Vanderbilt": "R64",
    "SIU Edwardsville": "R64",
    "Georgia": "R64",
    "Clemson": "R64",
    "High Point": "R64",
    "Xavier": "R64",
    "Troy": "R64",
    "Wofford": "R64",
    "Utah St.": "R64",
    "Norfolk St.": "R64",
    "Oklahoma": "R64",
    "Memphis": "R64",
    "Grand Canyon": "R64",
    "Missouri": "R64",
    "UNC Wilmington": "R64",
    "Nebraska Omaha": "R64",
    "Kansas": "R64",
}

# Round ordering for comparison
ROUND_ORDER = {"R64": 0, "R32": 1, "S16": 2, "E8": 3, "F4": 4, "Championship": 5, "Champion": 6}


def actual_winners_per_round(actual: dict, bracket: dict) -> dict[str, list[str]]:
    """Determine actual winners for each round based on furthest advancement."""
    winners = {}
    for round_name in ["R32", "S16", "E8", "F4", "Championship", "Champion"]:
        round_idx = ROUND_ORDER[round_name]
        winners[round_name] = [
            team for team, furthest in actual.items()
            if ROUND_ORDER.get(furthest, 0) >= round_idx
        ]
    return winners


def score_picks(picks: dict, actual: dict, bracket: dict) -> dict:
    """Score a set of bracket picks against actual results.

    picks: dict with regions (region -> list of winners per round) and champion
    actual: dict team -> furthest round
    """
    regions = bracket["regions"]
    ff_matchups = bracket["final_four_matchups"]
    actual_by_round = actual_winners_per_round(actual, bracket)

    total_score = 0
    round_scores = {}
    round_correct = {}
    round_total = {}

    # Build picks per round from the most_likely_bracket structure
    # We need to replay the bracket to get all picks, not just region winners
    sim_bracket = picks  # This is the full picks structure

    # For detailed scoring, we need to simulate the bracket pick-by-pick
    # Let's use a simpler approach: check if each actual winner was predicted
    # by comparing simulation probabilities

    return total_score, round_scores


def generate_deterministic_bracket(sim: BracketSimulator, bracket: dict,
                                    results: pd.DataFrame) -> dict:
    """Generate full bracket picks from simulation results.

    Returns dict mapping round -> list of (team, correct) tuples.
    """
    regions = bracket["regions"]
    ff_matchups = bracket["final_four_matchups"]

    all_picks = {}

    # Track picks per round
    r32_picks = []
    s16_picks = []
    e8_picks = []
    f4_picks = []
    champ_picks = []
    winner_pick = []

    region_winners = {}

    for region_name, seeds in regions.items():
        matchups = sim._build_region_matchups(seeds)

        # R64 -> R32 winners
        current_teams = []
        for t1, t2 in matchups:
            t1_prob = results.loc[t1, "R32"] if t1 in results.index else 0
            t2_prob = results.loc[t2, "R32"] if t2 in results.index else 0
            pick = t1 if t1_prob >= t2_prob else t2
            current_teams.append(pick)
            r32_picks.append(pick)

        # R32 -> S16 winners
        next_round = []
        for i in range(0, len(current_teams), 2):
            t1, t2 = current_teams[i], current_teams[i + 1]
            t1_prob = results.loc[t1, "S16"] if t1 in results.index else 0
            t2_prob = results.loc[t2, "S16"] if t2 in results.index else 0
            pick = t1 if t1_prob >= t2_prob else t2
            next_round.append(pick)
            s16_picks.append(pick)
        current_teams = next_round

        # S16 -> E8 winners
        next_round = []
        for i in range(0, len(current_teams), 2):
            t1, t2 = current_teams[i], current_teams[i + 1]
            t1_prob = results.loc[t1, "E8"] if t1 in results.index else 0
            t2_prob = results.loc[t2, "E8"] if t2 in results.index else 0
            pick = t1 if t1_prob >= t2_prob else t2
            next_round.append(pick)
            e8_picks.append(pick)
        current_teams = next_round

        # E8 -> F4 winner
        t1, t2 = current_teams[0], current_teams[1]
        t1_prob = results.loc[t1, "F4"] if t1 in results.index else 0
        t2_prob = results.loc[t2, "F4"] if t2 in results.index else 0
        pick = t1 if t1_prob >= t2_prob else t2
        f4_picks.append(pick)
        region_winners[region_name] = pick

    # Final Four
    for r1, r2 in ff_matchups:
        t1 = region_winners[r1]
        t2 = region_winners[r2]
        t1_prob = results.loc[t1, "Championship"] if t1 in results.index else 0
        t2_prob = results.loc[t2, "Championship"] if t2 in results.index else 0
        pick = t1 if t1_prob >= t2_prob else t2
        champ_picks.append(pick)

    # Championship
    t1, t2 = champ_picks[0], champ_picks[1]
    t1_prob = results.loc[t1, "Champion"] if t1 in results.index else 0
    t2_prob = results.loc[t2, "Champion"] if t2 in results.index else 0
    champion = t1 if t1_prob >= t2_prob else t2
    winner_pick.append(champion)

    return {
        "R32": r32_picks,
        "S16": s16_picks,
        "E8": e8_picks,
        "F4": f4_picks,
        "Championship": champ_picks,
        "Champion": winner_pick,
    }


def score_bracket_picks(picks: dict, actual: dict) -> tuple[int, dict]:
    """Score bracket picks against actual results.

    Returns (total_score, {round: {correct, total, points}}).
    """
    actual_by_round = actual_winners_per_round(actual, {})

    total = 0
    details = {}

    for round_name in ["R32", "S16", "E8", "F4", "Championship", "Champion"]:
        round_picks = picks.get(round_name, [])
        actual_winners = set(actual_by_round.get(round_name, []))
        pts_per = ROUND_POINTS.get(round_name, ROUND_POINTS.get("Championship", 320))

        correct = sum(1 for p in round_picks if p in actual_winners)
        points = correct * pts_per
        total += points

        details[round_name] = {
            "correct": correct,
            "total": len(round_picks),
            "points": points,
            "picks": [(p, p in actual_winners) for p in round_picks],
        }

    return total, details


if __name__ == "__main__":
    print("=" * 60)
    print("2025 BRACKET SCORING")
    print("=" * 60)

    # Train model on 2024 + 2025 regular season (pre-tournament)
    print("\nTraining model on pre-tournament data...")
    predictor = GamePredictor()
    all_X, all_y_win, all_y_spread = [], [], []

    for year in [2024, 2025]:
        cutoff = TOURNAMENT_CUTOFFS[year]
        tgs, _, _ = run_gravity_pipeline(year, cutoff_date=cutoff if year == 2025 else None)
        teams_df = fetch_team_stats(year).set_index("team")
        players_df = fetch_player_stats(year)
        player_feats = build_player_features(players_df)

        if year == 2025:
            tgs = tgs[tgs["numdate"] <= cutoff].copy()

        feat_df, y_win, y_spread = predictor.build_training_data(tgs, teams_df, player_feats)
        all_X.append(feat_df)
        all_y_win.append(y_win)
        all_y_spread.append(y_spread)
        print(f"  {year}: {len(feat_df)} games")

    train_X = pd.concat(all_X, ignore_index=True)
    train_y_win = np.concatenate(all_y_win)
    train_y_spread = np.concatenate(all_y_spread)

    print(f"  Total: {len(train_X)} training games")
    predictor.fit(train_X, train_y_win, train_y_spread)

    # Load 2025 bracket
    bracket_path = BRACKETS_DIR / "bracket_2025.json"
    with open(bracket_path) as f:
        bracket = json.load(f)

    # Set up simulator with 2025 pre-tournament data
    teams_df = fetch_team_stats(2025).set_index("team")
    players_df = fetch_player_stats(2025)
    player_feats = build_player_features(players_df)

    sim = BracketSimulator(predictor, teams_df, player_feats)

    # Run simulation
    n_sims = 10000
    print(f"\nRunning {n_sims} simulations...")
    results = sim.simulate_tournament(bracket, n_sims=n_sims)

    # Show top teams
    print("\nTop 20 Teams by Championship Probability:")
    sim.print_results(results, top_n=20)

    # Generate deterministic bracket (always pick higher probability)
    print("\n" + "=" * 60)
    print("BRACKET PICKS (chalk / most likely)")
    print("=" * 60)
    picks = generate_deterministic_bracket(sim, bracket, results)

    total_score, details = score_bracket_picks(picks, ACTUAL_RESULTS_2025)

    for round_name in ["R32", "S16", "E8", "F4", "Championship", "Champion"]:
        rd = details[round_name]
        print(f"\n  {round_name} ({rd['correct']}/{rd['total']} correct, {rd['points']} pts):")
        for team, correct in rd["picks"]:
            mark = "+" if correct else "X"
            print(f"    [{mark}] {team}")

    print(f"\n{'=' * 60}")
    print(f"TOTAL SCORE: {total_score} points")
    max_possible = sum(ROUND_POINTS[r] * details[r]["total"] for r in details)
    print(f"MAX POSSIBLE: {max_possible} points")
    print(f"PERCENTAGE: {total_score / max_possible * 100:.1f}%")

    # Also show what a perfect bracket would score
    perfect = sum(ROUND_POINTS.get(r, 320) * details[r]["total"] for r in details)

    # Compare to chalk (always pick higher seed)
    print(f"\n{'=' * 60}")
    print("CHAMPIONSHIP PICK ANALYSIS")
    print("=" * 60)
    champ_pick = picks["Champion"][0]
    actual_champ = [t for t, r in ACTUAL_RESULTS_2025.items() if r == "Champion"][0]
    print(f"  Our pick:      {champ_pick}")
    print(f"  Actual champ:  {actual_champ}")
    champ_prob = results.loc[champ_pick, "Champion"] if champ_pick in results.index else 0
    actual_prob = results.loc[actual_champ, "Champion"] if actual_champ in results.index else 0
    print(f"  Our pick prob: {champ_prob:.1f}%")
    print(f"  Actual prob:   {actual_prob:.1f}%")
