"""Phase 3: March Madness bracket simulator.

Monte Carlo simulation engine that uses the GamePredictor to simulate
tournament outcomes across N iterations.
"""

from __future__ import annotations

import json
import numpy as np
import pandas as pd
from pathlib import Path

from predict import GamePredictor

BRACKETS_DIR = Path(__file__).resolve().parent / "brackets"

ROUND_NAMES = ["R64", "R32", "S16", "E8", "F4", "Championship"]


class BracketSimulator:
    """Monte Carlo bracket simulator for March Madness."""

    def __init__(self, predictor: GamePredictor, combined: pd.DataFrame,
                 teams_df: pd.DataFrame):
        """
        Args:
            predictor: trained GamePredictor
            combined: gravity combined table (team -> gravity coefficients)
            teams_df: Torvik team stats indexed by team name
        """
        self.predictor = predictor
        self.combined = combined
        self.teams_df = teams_df
        self.grav_cols = [c for c in combined.columns if "gravity" in c]

    def _get_team_data(self, team: str) -> tuple[dict, dict]:
        """Get gravity and Torvik data for a team."""
        grav = {}
        if team in self.combined.index:
            grav = {col: self.combined.loc[team, col] for col in self.grav_cols}

        torvik = {}
        if team in self.teams_df.index:
            for s in ["adjoe", "adjde", "barthag", "adj_tempo", "sos"]:
                if s in self.teams_df.columns:
                    torvik[s] = self.teams_df.loc[team, s]

        return grav, torvik

    def simulate_game(self, team1: str, team2: str, location: float = 0.0) -> str:
        """Simulate a single game, return winner name.

        Uses the spread model with Gaussian noise for stochastic outcomes.
        """
        t1_grav, t1_torvik = self._get_team_data(team1)
        t2_grav, t2_torvik = self._get_team_data(team2)

        features = self.predictor.build_features(t1_grav, t2_grav, t1_torvik, t2_torvik, location)

        # Use tournament-calibrated spread sigma for more accurate variance
        spread = self.predictor.predict_spread(features)
        margin = np.random.normal(spread, self.predictor.spread_sigma)
        return team1 if margin > 0 else team2

    def load_bracket(self, path: str | Path) -> dict:
        """Load bracket from JSON file."""
        with open(path) as f:
            return json.load(f)

    def _build_region_matchups(self, region_seeds: dict) -> list[tuple[str, str]]:
        """Build first-round matchups from seed dict.

        Standard NCAA bracket: 1v16, 8v9, 5v12, 4v13, 6v11, 3v14, 7v10, 2v15
        """
        matchup_order = [(1, 16), (8, 9), (5, 12), (4, 13), (6, 11), (3, 14), (7, 10), (2, 15)]
        matchups = []
        for s1, s2 in matchup_order:
            t1 = region_seeds.get(str(s1), f"Seed{s1}")
            t2 = region_seeds.get(str(s2), f"Seed{s2}")
            matchups.append((t1, t2))
        return matchups

    def _simulate_region(self, teams: list[tuple[str, str]], tracker: dict) -> str:
        """Simulate a region from first round matchups to Elite Eight winner.

        Returns the region champion.
        """
        current_teams = []

        # Round of 64
        for t1, t2 in teams:
            winner = self.simulate_game(t1, t2, location=0.0)
            current_teams.append(winner)
            tracker[winner]["R32"] += 1

        # Round of 32
        next_round = []
        for i in range(0, len(current_teams), 2):
            winner = self.simulate_game(current_teams[i], current_teams[i + 1], location=0.0)
            next_round.append(winner)
            tracker[winner]["S16"] += 1
        current_teams = next_round

        # Sweet 16
        next_round = []
        for i in range(0, len(current_teams), 2):
            winner = self.simulate_game(current_teams[i], current_teams[i + 1], location=0.0)
            next_round.append(winner)
            tracker[winner]["E8"] += 1
        current_teams = next_round

        # Elite Eight
        winner = self.simulate_game(current_teams[0], current_teams[1], location=0.0)
        tracker[winner]["F4"] += 1

        return winner

    def simulate_tournament(self, bracket: dict, n_sims: int = 1000,
                            seed: int | None = 42) -> pd.DataFrame:
        """Run Monte Carlo simulation of the full tournament.

        Args:
            bracket: bracket dict with regions and final_four_matchups
            n_sims: number of simulations
            seed: random seed (None for no seed)

        Returns:
            DataFrame with advancement probabilities per team per round
        """
        if seed is not None:
            np.random.seed(seed)

        regions = bracket["regions"]
        ff_matchups = bracket.get("final_four_matchups", [["East", "West"], ["South", "Midwest"]])

        # Collect all teams
        all_teams = set()
        for region_name, seeds in regions.items():
            for s, team in seeds.items():
                all_teams.add(team)

        # Initialize tracker
        round_cols = ["R64", "R32", "S16", "E8", "F4", "Championship", "Champion"]

        results = []
        for sim in range(n_sims):
            tracker = {t: {r: 0 for r in round_cols} for t in all_teams}

            # All teams make R64
            for t in all_teams:
                tracker[t]["R64"] += 1

            # Simulate each region
            region_winners = {}
            for region_name, seeds in regions.items():
                matchups = self._build_region_matchups(seeds)
                winner = self._simulate_region(matchups, tracker)
                region_winners[region_name] = winner

            # Final Four
            ff_winners = []
            for r1, r2 in ff_matchups:
                t1 = region_winners[r1]
                t2 = region_winners[r2]
                winner = self.simulate_game(t1, t2, location=0.0)
                tracker[winner]["Championship"] += 1
                ff_winners.append(winner)

            # Championship
            champion = self.simulate_game(ff_winners[0], ff_winners[1], location=0.0)
            tracker[champion]["Champion"] += 1

            results.append(tracker)

        # Aggregate
        agg = {t: {r: 0 for r in round_cols} for t in all_teams}
        for sim_result in results:
            for team, rounds in sim_result.items():
                for r, count in rounds.items():
                    agg[team][r] += count

        # Convert to probabilities
        df = pd.DataFrame(agg).T
        df = df / n_sims * 100  # as percentages
        df.index.name = "Team"

        # Expected wins
        df["E[Wins]"] = (
            df["R32"] / 100 + df["S16"] / 100 + df["E8"] / 100 +
            df["F4"] / 100 + df["Championship"] / 100 + df["Champion"] / 100
        )

        # Sort by championship probability
        df = df.sort_values("Champion", ascending=False)

        return df

    def print_results(self, results: pd.DataFrame, top_n: int = 30):
        """Print formatted results table."""
        print(f"\n{'Team':<22} | {'R64':>5} | {'R32':>5} | {'S16':>5} | {'E8':>5} | "
              f"{'F4':>5} | {'Champ':>5} | {'E[Wins]':>7}")
        print("-" * 85)
        for team, row in results.head(top_n).iterrows():
            print(f"{team:<22} | {row['R64']:>5.1f} | {row['R32']:>5.1f} | {row['S16']:>5.1f} | "
                  f"{row['E8']:>5.1f} | {row['F4']:>5.1f} | {row['Champion']:>5.1f} | "
                  f"{row['E[Wins]']:>7.2f}")

    def export_csv(self, results: pd.DataFrame, path: str | Path = None):
        """Export results to CSV."""
        if path is None:
            path = Path(__file__).resolve().parent / "data" / "bracket_simulation.csv"
        results.to_csv(path)
        print(f"\nSaved results -> {path}")

    def most_likely_bracket(self, bracket: dict, results: pd.DataFrame) -> dict:
        """Determine most likely bracket based on simulation probabilities."""
        regions = bracket["regions"]
        ff_matchups = bracket.get("final_four_matchups", [["East", "West"], ["South", "Midwest"]])

        most_likely = {"regions": {}, "final_four": {}, "champion": None}

        for region_name, seeds in regions.items():
            matchups = self._build_region_matchups(seeds)
            current_teams = []

            # R64: pick higher seed (more likely winner)
            for t1, t2 in matchups:
                # Use simulation results to pick more likely winner
                t1_r32 = results.loc[t1, "R32"] if t1 in results.index else 0
                t2_r32 = results.loc[t2, "R32"] if t2 in results.index else 0
                winner = t1 if t1_r32 >= t2_r32 else t2
                current_teams.append(winner)

            # R32
            next_round = []
            for i in range(0, len(current_teams), 2):
                t1, t2 = current_teams[i], current_teams[i + 1]
                t1_s16 = results.loc[t1, "S16"] if t1 in results.index else 0
                t2_s16 = results.loc[t2, "S16"] if t2 in results.index else 0
                winner = t1 if t1_s16 >= t2_s16 else t2
                next_round.append(winner)
            current_teams = next_round

            # S16
            next_round = []
            for i in range(0, len(current_teams), 2):
                t1, t2 = current_teams[i], current_teams[i + 1]
                t1_e8 = results.loc[t1, "E8"] if t1 in results.index else 0
                t2_e8 = results.loc[t2, "E8"] if t2 in results.index else 0
                winner = t1 if t1_e8 >= t2_e8 else t2
                next_round.append(winner)
            current_teams = next_round

            # E8
            t1, t2 = current_teams[0], current_teams[1]
            t1_f4 = results.loc[t1, "F4"] if t1 in results.index else 0
            t2_f4 = results.loc[t2, "F4"] if t2 in results.index else 0
            winner = t1 if t1_f4 >= t2_f4 else t2
            most_likely["regions"][region_name] = winner

        # Final Four
        ff_winners = []
        for r1, r2 in ff_matchups:
            t1 = most_likely["regions"][r1]
            t2 = most_likely["regions"][r2]
            t1_champ = results.loc[t1, "Championship"] if t1 in results.index else 0
            t2_champ = results.loc[t2, "Championship"] if t2 in results.index else 0
            winner = t1 if t1_champ >= t2_champ else t2
            ff_winners.append(winner)

        # Championship
        t1, t2 = ff_winners[0], ff_winners[1]
        t1_c = results.loc[t1, "Champion"] if t1 in results.index else 0
        t2_c = results.loc[t2, "Champion"] if t2 in results.index else 0
        most_likely["champion"] = t1 if t1_c >= t2_c else t2

        return most_likely


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    bracket_path = sys.argv[1] if len(sys.argv) > 1 else BRACKETS_DIR / "bracket_2026.json"

    if not Path(bracket_path).exists():
        print(f"Bracket file not found: {bracket_path}")
        print(f"Create one at {BRACKETS_DIR / 'bracket_2026.json'}")
        sys.exit(1)

    print("Loading model...")
    predictor = GamePredictor.load()

    from gravity import run_gravity_pipeline
    from torvik import fetch_team_stats
    tgs, gravities, combined = run_gravity_pipeline(2026)
    teams_df = fetch_team_stats(2026).set_index("team")

    print("Loading bracket...")
    sim = BracketSimulator(predictor, combined, teams_df)
    bracket = sim.load_bracket(bracket_path)

    n_sims = int(sys.argv[2]) if len(sys.argv) > 2 else 1000
    print(f"Running {n_sims} simulations...")
    results = sim.simulate_tournament(bracket, n_sims=n_sims)

    sim.print_results(results)
    sim.export_csv(results)

    # Most likely bracket
    likely = sim.most_likely_bracket(bracket, results)
    print("\nMost Likely Bracket:")
    for region, winner in likely["regions"].items():
        print(f"  {region}: {winner}")
    print(f"  Champion: {likely['champion']}")
