"""March Madness bracket simulator.

Monte Carlo simulation engine that uses the GamePredictor to simulate
tournament outcomes across N iterations.
"""

from __future__ import annotations

import json
import numpy as np
import pandas as pd
from pathlib import Path

from predict import GamePredictor, build_player_features, _TORVIK_COLS, _TEAM_DIFF_STATS

BRACKETS_DIR = Path(__file__).resolve().parent / "brackets"

ROUND_NAMES = ["R64", "R32", "S16", "E8", "F4", "Championship"]


class BracketSimulator:
    """Monte Carlo bracket simulator for March Madness."""

    def __init__(self, predictor: GamePredictor, teams_df: pd.DataFrame,
                 player_feats: dict):
        """
        Args:
            predictor: trained GamePredictor
            teams_df: Torvik team stats indexed by team name
            player_feats: dict from build_player_features()
        """
        self.predictor = predictor
        self.teams_df = teams_df
        self.player_feats = player_feats

    def _get_team_data(self, team: str) -> tuple[dict, dict]:
        """Get Torvik and player data for a team."""
        torvik = {}
        if team in self.teams_df.index:
            torvik = {s: pd.to_numeric(self.teams_df.loc[team, s], errors="coerce")
                      for s in _TORVIK_COLS + _TEAM_DIFF_STATS if s in self.teams_df.columns}

        players = self.player_feats.get(team, {})
        return torvik, players

    def simulate_game(self, team1: str, team2: str, location: float = 0.0) -> str:
        """Simulate a single game, return winner name."""
        t1_torvik, t1_players = self._get_team_data(team1)
        t2_torvik, t2_players = self._get_team_data(team2)

        features = self.predictor.build_features(t1_torvik, t2_torvik, t1_players, t2_players, location)
        win_prob = self.predictor.ensemble_prob(features, tournament=True)
        return team1 if np.random.random() < win_prob else team2

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
        """Simulate a region from first round matchups to Elite Eight winner."""
        current_teams = []

        for t1, t2 in teams:
            winner = self.simulate_game(t1, t2, location=0.0)
            current_teams.append(winner)
            tracker[winner]["R32"] += 1

        next_round = []
        for i in range(0, len(current_teams), 2):
            winner = self.simulate_game(current_teams[i], current_teams[i + 1], location=0.0)
            next_round.append(winner)
            tracker[winner]["S16"] += 1
        current_teams = next_round

        next_round = []
        for i in range(0, len(current_teams), 2):
            winner = self.simulate_game(current_teams[i], current_teams[i + 1], location=0.0)
            next_round.append(winner)
            tracker[winner]["E8"] += 1
        current_teams = next_round

        winner = self.simulate_game(current_teams[0], current_teams[1], location=0.0)
        tracker[winner]["F4"] += 1
        return winner

    def simulate_tournament(self, bracket: dict, n_sims: int = 1000,
                            seed: int | None = 42) -> pd.DataFrame:
        """Run Monte Carlo simulation of the full tournament."""
        if seed is not None:
            np.random.seed(seed)

        regions = bracket["regions"]
        ff_matchups = bracket.get("final_four_matchups", [["East", "West"], ["South", "Midwest"]])

        all_teams = set()
        for region_name, seeds in regions.items():
            for s, team in seeds.items():
                all_teams.add(team)

        round_cols = ["R64", "R32", "S16", "E8", "F4", "Championship", "Champion"]

        results = []
        for sim in range(n_sims):
            tracker = {t: {r: 0 for r in round_cols} for t in all_teams}
            for t in all_teams:
                tracker[t]["R64"] += 1

            region_winners = {}
            for region_name, seeds in regions.items():
                matchups = self._build_region_matchups(seeds)
                winner = self._simulate_region(matchups, tracker)
                region_winners[region_name] = winner

            ff_winners = []
            for r1, r2 in ff_matchups:
                t1 = region_winners[r1]
                t2 = region_winners[r2]
                winner = self.simulate_game(t1, t2, location=0.0)
                tracker[winner]["Championship"] += 1
                ff_winners.append(winner)

            champion = self.simulate_game(ff_winners[0], ff_winners[1], location=0.0)
            tracker[champion]["Champion"] += 1
            results.append(tracker)

        agg = {t: {r: 0 for r in round_cols} for t in all_teams}
        for sim_result in results:
            for team, rounds in sim_result.items():
                for r, count in rounds.items():
                    agg[team][r] += count

        df = pd.DataFrame(agg).T
        df = df / n_sims * 100
        df.index.name = "Team"
        df["E[Wins]"] = (
            df["R32"] / 100 + df["S16"] / 100 + df["E8"] / 100 +
            df["F4"] / 100 + df["Championship"] / 100 + df["Champion"] / 100
        )
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
            path = Path(__file__).resolve().parent / "results" / "bracket_simulation.csv"
            path.parent.mkdir(exist_ok=True)
        results.to_csv(path)
        print(f"\nSaved results -> {path}")

    def most_likely_bracket(self, bracket: dict, results: pd.DataFrame) -> dict:
        """Determine most likely bracket based on simulation probabilities."""
        regions = bracket["regions"]
        ff_matchups = bracket.get("final_four_matchups", [["East", "West"], ["South", "Midwest"]])
        most_likely = {"regions": {}, "champion": None}

        for region_name, seeds in regions.items():
            matchups = self._build_region_matchups(seeds)
            current_teams = []
            for t1, t2 in matchups:
                t1_r32 = results.loc[t1, "R32"] if t1 in results.index else 0
                t2_r32 = results.loc[t2, "R32"] if t2 in results.index else 0
                current_teams.append(t1 if t1_r32 >= t2_r32 else t2)

            next_round = []
            for i in range(0, len(current_teams), 2):
                t1, t2 = current_teams[i], current_teams[i + 1]
                t1_v = results.loc[t1, "S16"] if t1 in results.index else 0
                t2_v = results.loc[t2, "S16"] if t2 in results.index else 0
                next_round.append(t1 if t1_v >= t2_v else t2)
            current_teams = next_round

            next_round = []
            for i in range(0, len(current_teams), 2):
                t1, t2 = current_teams[i], current_teams[i + 1]
                t1_v = results.loc[t1, "E8"] if t1 in results.index else 0
                t2_v = results.loc[t2, "E8"] if t2 in results.index else 0
                next_round.append(t1 if t1_v >= t2_v else t2)
            current_teams = next_round

            t1, t2 = current_teams[0], current_teams[1]
            t1_v = results.loc[t1, "F4"] if t1 in results.index else 0
            t2_v = results.loc[t2, "F4"] if t2 in results.index else 0
            most_likely["regions"][region_name] = t1 if t1_v >= t2_v else t2

        ff_winners = []
        for r1, r2 in ff_matchups:
            t1 = most_likely["regions"][r1]
            t2 = most_likely["regions"][r2]
            t1_v = results.loc[t1, "Championship"] if t1 in results.index else 0
            t2_v = results.loc[t2, "Championship"] if t2 in results.index else 0
            ff_winners.append(t1 if t1_v >= t2_v else t2)

        t1, t2 = ff_winners[0], ff_winners[1]
        t1_v = results.loc[t1, "Champion"] if t1 in results.index else 0
        t2_v = results.loc[t2, "Champion"] if t2 in results.index else 0
        most_likely["champion"] = t1 if t1_v >= t2_v else t2

        return most_likely


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import json as _json
    import sys
    from torvik import fetch_team_stats, fetch_player_stats, fetch_player_stats_daterange

    bracket_path = sys.argv[1] if len(sys.argv) > 1 else BRACKETS_DIR / "bracket_2026.json"

    if not Path(bracket_path).exists():
        print(f"Bracket file not found: {bracket_path}")
        print(f"Create one at {BRACKETS_DIR / 'bracket_2026.json'}")
        sys.exit(1)

    print("Loading model...")
    predictor = GamePredictor.load()

    teams_df = fetch_team_stats(2026).set_index("team")
    players_df = fetch_player_stats(2026)

    # Recent 30-day window for form features
    cutoff_dt = pd.to_datetime("20260316", format="%Y%m%d")
    recent_start = (cutoff_dt - pd.Timedelta(days=30)).strftime("%Y%m%d")
    try:
        recent_players_df = fetch_player_stats_daterange(2026, recent_start, "20260316")
    except Exception:
        recent_players_df = None

    # Load injury exclusions and weights
    injuries_path = Path(__file__).resolve().parent / "config" / "injuries.json"
    exclusions = None
    weights = None
    if injuries_path.exists():
        with open(injuries_path) as _f:
            _injuries = _json.load(_f)
        exclusions = _injuries.get("2026", {}) or None
        weights = _injuries.get("_weights_2026", {}) or None

    player_feats = build_player_features(players_df, recent_players_df=recent_players_df,
                                         exclusions=exclusions, weights=weights)

    print("Loading bracket...")
    sim = BracketSimulator(predictor, teams_df, player_feats)
    bracket = sim.load_bracket(bracket_path)

    n_sims = int(sys.argv[2]) if len(sys.argv) > 2 else 1000
    print(f"Running {n_sims} simulations...")
    results = sim.simulate_tournament(bracket, n_sims=n_sims)

    sim.print_results(results)
    sim.export_csv(results)

    likely = sim.most_likely_bracket(bracket, results)
    print("\nMost Likely Bracket:")
    for region, winner in likely["regions"].items():
        print(f"  {region}: {winner}")
    print(f"  Champion: {likely['champion']}")

    # Save text report
    results_dir = Path(__file__).resolve().parent / "results"
    results_dir.mkdir(exist_ok=True)
    report_path = results_dir / "bracket_report.txt"
    with open(report_path, "w") as rpt:
        rpt.write(f"Bracket Simulation Report ({n_sims} simulations)\n")
        rpt.write(f"{'=' * 85}\n\n")
        if exclusions:
            rpt.write("Injuries/Exclusions:\n")
            for team, players in exclusions.items():
                rpt.write(f"  {team}: {', '.join(players)}\n")
            rpt.write("\n")
        header = (f"{'Team':<22} | {'R64':>5} | {'R32':>5} | {'S16':>5} | {'E8':>5} | "
                  f"{'F4':>5} | {'Champ':>5} | {'E[Wins]':>7}")
        rpt.write(header + "\n")
        rpt.write("-" * 85 + "\n")
        for team, row in results.iterrows():
            rpt.write(f"{team:<22} | {row['R64']:>5.1f} | {row['R32']:>5.1f} | {row['S16']:>5.1f} | "
                      f"{row['E8']:>5.1f} | {row['F4']:>5.1f} | {row['Champion']:>5.1f} | "
                      f"{row['E[Wins]']:>7.2f}\n")
        rpt.write(f"\nMost Likely Bracket:\n")
        for region, winner in likely["regions"].items():
            rpt.write(f"  {region}: {winner}\n")
        rpt.write(f"  Champion: {likely['champion']}\n")
    print(f"\nSaved report -> {report_path}")
