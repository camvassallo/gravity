"""Analyze R64 upset EV to find optimal bracket configurations.

For each R64 matchup, compute:
- Model win probability for both teams (with sim_temp applied)
- ESPN scoring EV for picking favorite vs underdog
- The EV "cost" of picking the upset
- Cascade EV: how much later-round EV changes if this team advances

Then rank upsets by cost and generate bracket options.
"""

from __future__ import annotations

import json
import numpy as np
import pandas as pd
from pathlib import Path
from itertools import combinations

from predict import GamePredictor, build_player_features, _TORVIK_COLS, _TEAM_DIFF_STATS
from torvik import fetch_team_stats, fetch_player_stats, fetch_player_stats_daterange
from optimize_bracket import load_consensus_projections

# ESPN scoring
ROUND_POINTS = {"R64": 10, "R32": 20, "S16": 40, "E8": 80, "F4": 160, "Championship": 320}
MATCHUP_ORDER = [(1, 16), (8, 9), (5, 12), (4, 13), (6, 11), (3, 14), (7, 10), (2, 15)]

SIM_TEMP = 1.3


def apply_sim_temp(prob: float, temp: float) -> float:
    prob = np.clip(prob, 1e-7, 1 - 1e-7)
    logit = np.log(prob / (1 - prob))
    return float(1 / (1 + np.exp(-logit / temp)))


def get_pairwise_prob(predictor, teams_df, player_feats, t1, t2,
                      consensus, consensus_weight=0.3):
    """Get blended win probability for t1 vs t2."""
    torvik1 = {s: pd.to_numeric(teams_df.loc[t1, s], errors="coerce")
               for s in _TORVIK_COLS + _TEAM_DIFF_STATS if s in teams_df.columns}
    torvik2 = {s: pd.to_numeric(teams_df.loc[t2, s], errors="coerce")
               for s in _TORVIK_COLS + _TEAM_DIFF_STATS if s in teams_df.columns}
    p1 = player_feats.get(t1, {})
    p2 = player_feats.get(t2, {})

    features = predictor.build_features(torvik1, torvik2, p1, p2, 0.0)
    model_prob = predictor.ensemble_prob(features, tournament=True)

    # Consensus blend
    if consensus and consensus_weight > 0:
        c1 = consensus.get(t1, {}).get("Champion", 0)
        c2 = consensus.get(t2, {}).get("Champion", 0)
        if c1 > 0 and c2 > 0:
            log_ratio = np.log(c1 / c2)
            cons_prob = 1 / (1 + np.exp(-0.8 * log_ratio))
            model_prob = (1 - consensus_weight) * model_prob + consensus_weight * cons_prob

    # Apply sim_temp
    return apply_sim_temp(model_prob, SIM_TEMP)


def main():
    print("Loading model and data...")
    predictor = GamePredictor.load()
    teams_df = fetch_team_stats(2026).set_index("team")
    players_df = fetch_player_stats(2026)

    cutoff_dt = pd.to_datetime("20260316", format="%Y%m%d")
    recent_start = (cutoff_dt - pd.Timedelta(days=30)).strftime("%Y%m%d")
    try:
        recent_players_df = fetch_player_stats_daterange(2026, recent_start, "20260316")
    except Exception:
        recent_players_df = None

    injuries_path = Path(__file__).resolve().parent / "config" / "injuries.json"
    exclusions = weights = None
    if injuries_path.exists():
        with open(injuries_path) as f:
            inj = json.load(f)
        exclusions = inj.get("2026", {}) or None
        weights = inj.get("_weights_2026", {}) or None

    player_feats = build_player_features(players_df, recent_players_df=recent_players_df,
                                         exclusions=exclusions, weights=weights)

    consensus = load_consensus_projections(set())

    with open("brackets/bracket_2026.json") as f:
        bracket = json.load(f)

    # Load simulation results for later-round probabilities
    sim_results = pd.read_csv("results/bracket_simulation.csv", index_col="Team")

    regions = bracket["regions"]

    print("\n" + "=" * 90)
    print("R64 UPSET ANALYSIS — EV Cost of Each Possible Upset")
    print("=" * 90)
    print(f"\n{'Region':<10} {'Matchup':<35} {'Fav%':>5} {'Dog%':>5} "
          f"{'Fav EV':>7} {'Dog EV':>7} {'Cost':>6} {'Dog R32%':>8} {'Dog S16%':>8}")
    print("-" * 95)

    all_upsets = []

    for region_name, seeds in regions.items():
        for s_hi, s_lo in MATCHUP_ORDER:
            fav = seeds[str(s_hi)]
            dog = seeds[str(s_lo)]

            # Only consider upsets where lower seed beats higher seed
            if s_lo <= s_hi:
                continue  # 8v9 handled separately

            prob_fav = get_pairwise_prob(predictor, teams_df, player_feats,
                                         fav, dog, consensus)
            prob_dog = 1 - prob_fav

            fav_ev = prob_fav * 10
            dog_ev = prob_dog * 10
            ev_cost = fav_ev - dog_ev  # how much EV you lose picking the upset

            # Later-round simulation probabilities for the underdog
            dog_r32 = sim_results.loc[dog, "R32"] if dog in sim_results.index else 0
            dog_s16 = sim_results.loc[dog, "S16"] if dog in sim_results.index else 0

            matchup_str = f"({s_hi}) {fav} vs ({s_lo}) {dog}"
            print(f"{region_name:<10} {matchup_str:<35} {prob_fav:>5.1%} {prob_dog:>5.1%} "
                  f"{fav_ev:>7.2f} {dog_ev:>7.2f} {ev_cost:>+6.2f} "
                  f"{dog_r32:>7.1f}% {dog_s16:>7.1f}%")

            all_upsets.append({
                "region": region_name,
                "fav": fav, "fav_seed": s_hi,
                "dog": dog, "dog_seed": s_lo,
                "fav_prob": prob_fav, "dog_prob": prob_dog,
                "ev_cost": ev_cost,
                "dog_r32": dog_r32, "dog_s16": dog_s16,
            })

    # Also include 8v9 games (where the 9-seed is actually favored by model)
    print("\n8v9 Games (model may favor either team):")
    for region_name, seeds in regions.items():
        t8 = seeds["8"]
        t9 = seeds["9"]
        prob_8 = get_pairwise_prob(predictor, teams_df, player_feats, t8, t9, consensus)
        prob_9 = 1 - prob_8
        print(f"  {region_name}: (8) {t8} {prob_8:.1%} vs (9) {t9} {prob_9:.1%}")

    # Sort upsets by EV cost (cheapest first)
    all_upsets.sort(key=lambda x: x["ev_cost"])

    print("\n" + "=" * 90)
    print("UPSETS RANKED BY EV COST (cheapest to most expensive)")
    print("=" * 90)
    print(f"\n{'#':>2} {'Cost':>6} {'Region':<10} {'Upset Pick':<25} {'Dog%':>5} {'Dog Seed':>8}")
    print("-" * 65)
    for i, u in enumerate(all_upsets):
        print(f"{i+1:>2} {u['ev_cost']:>+6.2f} {u['region']:<10} "
              f"{u['dog']:<25} {u['dog_prob']:>5.1%} {u['dog_seed']:>8}")

    # Compute cumulative EV cost for picking N upsets
    print("\n" + "=" * 90)
    print("CUMULATIVE R64 EV COST BY NUMBER OF UPSETS")
    print("=" * 90)
    print(f"\n{'N Upsets':>9} {'Cumul Cost':>11} {'Upsets Picked'}")
    print("-" * 80)
    cumul = 0
    for i, u in enumerate(all_upsets):
        cumul += u["ev_cost"]
        names = ", ".join(f"{all_upsets[j]['dog']}({all_upsets[j]['dog_seed']})"
                          for j in range(i + 1))
        print(f"{i+1:>9} {cumul:>+11.2f} {names}")

    # Now compute full bracket EV for different configurations
    print("\n" + "=" * 90)
    print("BRACKET OPTIONS")
    print("=" * 90)

    # For F4 analysis: compute pairwise probabilities for potential F4 matchups
    # F4 matchups: East vs South, West vs Midwest
    top_e8_teams = {
        "East": ["Duke", "Connecticut", "Michigan St."],
        "South": ["Florida", "Houston", "Illinois"],
        "West": ["Arizona", "Purdue", "Gonzaga"],
        "Midwest": ["Michigan", "Iowa St.", "Virginia"],
    }

    ff_matchups = bracket["final_four_matchups"]  # [["East", "South"], ["West", "Midwest"]]

    # Compute expected score for different F4 combos
    def compute_bracket_ev(f4_picks, champ_pick):
        """Estimate total bracket EV given F4 and champion picks."""
        ev = 0
        for team in f4_picks:
            # R64 through E8 cascade
            for rnd, pts in [("R32", 10), ("S16", 20), ("E8", 40), ("F4", 80)]:
                if team in sim_results.index:
                    ev += sim_results.loc[team, rnd] / 100 * pts
        # Championship game
        for team in f4_picks:
            if team in sim_results.index:
                ev += sim_results.loc[team, "Championship"] / 100 * 160
        # Champion
        if champ_pick in sim_results.index:
            ev += sim_results.loc[champ_pick, "Champion"] / 100 * 320

        return ev

    # Generate F4 combinations (not all 1-seeds)
    print("\nF4 Combinations (excluding all-1-seeds):")
    print(f"{'F4 Picks':<65} {'Champ':<20} {'Late EV':>8}")
    print("-" * 95)

    f4_options = []
    for e_team in top_e8_teams["East"]:
        for s_team in top_e8_teams["South"]:
            for w_team in top_e8_teams["West"]:
                for mw_team in top_e8_teams["Midwest"]:
                    picks = [e_team, s_team, w_team, mw_team]
                    # Skip all-1-seeds
                    one_seeds = {"Duke", "Florida", "Arizona", "Michigan"}
                    if set(picks) == one_seeds:
                        continue

                    # Champion = best team in F4 by champ%
                    champ = max(picks, key=lambda t: sim_results.loc[t, "Champion"]
                                if t in sim_results.index else 0)
                    ev = compute_bracket_ev(picks, champ)
                    f4_options.append((picks, champ, ev))

    f4_options.sort(key=lambda x: -x[2])
    for picks, champ, ev in f4_options[:15]:
        seeds = []
        seed_lookup = {}
        for rn, ss in regions.items():
            for s, t in ss.items():
                seed_lookup[t] = int(s)
        pick_str = ", ".join(f"{t}({seed_lookup.get(t, '?')})" for t in picks)
        print(f"{pick_str:<65} {champ:<20} {ev:>8.1f}")

    # Build 3 complete bracket options
    print("\n" + "=" * 90)
    print("THREE BRACKET OPTIONS")
    print("=" * 90)

    configs = [
        ("CHALK (pool ≤25)", 2, ["Duke", "Florida", "Arizona", "Michigan"], "Duke"),
        ("MODERATE (pool 25-100)", 4, ["Duke", "Houston", "Arizona", "Michigan"], "Michigan"),
        ("AGGRESSIVE (pool 100+)", 6, ["Duke", "Houston", "Purdue", "Iowa St."], "Duke"),
    ]

    for name, n_upsets, f4, champ in configs:
        print(f"\n--- {name} ---")
        print(f"F4: {', '.join(f4)}")
        print(f"Champion: {champ}")
        print(f"R64 upsets ({n_upsets}): ", end="")
        upset_picks = [all_upsets[i] for i in range(min(n_upsets, len(all_upsets)))]
        print(", ".join(f"{u['dog']}({u['dog_seed']}) over {u['fav']}({u['fav_seed']})"
              for u in upset_picks))
        total_cost = sum(u["ev_cost"] for u in upset_picks)
        print(f"Total R64 EV cost: {total_cost:+.2f} pts")

        # Estimate full bracket EV
        late_ev = compute_bracket_ev(f4, champ)
        r64_ev = 0
        for rn, ss in regions.items():
            for s_hi, s_lo in MATCHUP_ORDER:
                fav = ss[str(s_hi)]
                dog = ss[str(s_lo)]
                prob_fav = get_pairwise_prob(predictor, teams_df, player_feats,
                                             fav, dog, consensus)
                # Check if we picked this upset
                is_upset = any(u["dog"] == dog and u["region"] == rn for u in upset_picks)
                if is_upset:
                    r64_ev += (1 - prob_fav) * 10
                else:
                    r64_ev += prob_fav * 10
        print(f"R64 EV: {r64_ev:.1f}, Late-round EV: {late_ev:.1f}")


if __name__ == "__main__":
    main()
