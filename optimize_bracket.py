"""Bracket optimizer for pool play.

Generates optimal bracket picks that maximize probability of winning
a pool of N people, not just maximizing expected score.

Key insight: in large pools, you need to be RIGHT and DIFFERENT.
A pick's value = P(correct) × points × (1 / public_ownership).

Usage:
    python optimize_bracket.py brackets/bracket_2026.json 10000
    python optimize_bracket.py brackets/bracket_2026.json 10000 --pool-sizes 10 50 200
"""

from __future__ import annotations

import json
import numpy as np
import pandas as pd
from pathlib import Path

from predict import GamePredictor, build_player_features, _TORVIK_COLS, _TEAM_DIFF_STATS
from bracket import BracketSimulator, ROUND_NAMES

DATA_DIR = Path(__file__).resolve().parent / "data"
RESULTS_DIR = Path(__file__).resolve().parent / "results"
RESULTS_DIR.mkdir(exist_ok=True)

# ESPN standard scoring
ROUND_POINTS = {
    "R32": 10,
    "S16": 20,
    "E8": 40,
    "F4": 80,
    "Championship": 160,
    "Champion": 320,
}

# Historical public pick rates by seed matchup (R64).
# Based on ESPN bracket data aggregates. Values = P(higher seed picked).
PUBLIC_R64_RATES = {
    (1, 16): 0.98,
    (2, 15): 0.95,
    (3, 14): 0.90,
    (4, 13): 0.85,
    (5, 12): 0.65,
    (6, 11): 0.72,
    (7, 10): 0.60,
    (8, 9): 0.52,
}

# Public champion pick rates by seed (approximate, across all 4 regions combined)
# Source: ESPN aggregate bracket data, averaged across recent years.
PUBLIC_CHAMPION_BY_SEED = {
    1: 0.20,  # each 1-seed gets ~20% → 80% total for all four 1-seeds
    2: 0.04,  # each 2-seed ~4% → 16% total
    3: 0.01,
    4: 0.005,
    5: 0.002,
    6: 0.001,
    7: 0.001,
    8: 0.0005,
}

# Standard NCAA matchup order
MATCHUP_ORDER = [(1, 16), (8, 9), (5, 12), (4, 13), (6, 11), (3, 14), (7, 10), (2, 15)]


# Team name normalization: external sources → Barttorvik convention
_NAME_MAP = {
    "Michigan State": "Michigan St.",
    "Iowa State": "Iowa St.",
    "Ohio State": "Ohio St.",
    "Utah State": "Utah St.",
    "McNeese State": "McNeese St.",
    "Kennesaw State": "Kennesaw St.",
    "Wright State": "Wright St.",
    "North Dakota State": "North Dakota St.",
    "Tennessee State": "Tennessee St.",
    "California Baptist": "Cal Baptist",
    "Cal Baptist": "Cal Baptist",
    "Miami (Fla.)": "Miami FL",
    "Miami (OH)": "Miami OH",
    "Miami OH": "Miami OH",
    "NC State": "N.C. State",
    "N.C. State": "N.C. State",
    "Long Island": "LIU",
    "LIU": "LIU",
    "McNeese": "McNeese St.",
    "Prairie View": "Prairie View A&M",
    "St. John's": "St. John's",
    "Saint Mary's": "Saint Mary's",
}

# Round name normalization across sources
_ROUND_COLS = ["R32", "S16", "E8", "F4", "Championship", "Champion"]


def _normalize_name(name: str) -> str:
    """Map external team name to Barttorvik convention."""
    return _NAME_MAP.get(name, name)


def load_consensus_projections(bracket_teams: set) -> dict | None:
    """Load consensus projections (average of Torvik, Miya, KenPom).

    First tries the pre-built consensus CSV. Falls back to parsing
    the individual source files if consensus CSV doesn't exist.

    Returns dict: {team_name: {round: probability}} or None.
    """
    # Try pre-built consensus file first
    consensus_path = DATA_DIR / "consensus_projections.csv"
    if consensus_path.exists():
        df = pd.read_csv(consensus_path)
        consensus = {}
        for _, row in df.iterrows():
            team = row["Team"]
            consensus[team] = {}
            for rnd in _ROUND_COLS:
                col = f"{rnd}_Consensus"
                consensus[team][rnd] = row.get(col, 0) / 100 if col in df.columns else 0.0
        return consensus

    # Fall back to parsing individual source files
    sources = []

    tv_path = DATA_DIR / "torvik_proj.csv"
    if tv_path.exists():
        tv = pd.read_csv(tv_path)
        tv_data = {}
        for _, row in tv.iterrows():
            team = _normalize_name(row["Team"])
            tv_data[team] = {
                "R32": pd.to_numeric(row.get("R32", 0), errors="coerce") / 100,
                "S16": pd.to_numeric(row.get("S16", 0), errors="coerce") / 100,
                "E8": pd.to_numeric(row.get("E8", 0), errors="coerce") / 100,
                "F4": pd.to_numeric(row.get("F4", 0), errors="coerce") / 100,
                "Championship": pd.to_numeric(row.get("F2", 0), errors="coerce") / 100,
                "Champion": pd.to_numeric(row.get("Champ", 0), errors="coerce") / 100,
            }
        sources.append(("Torvik", tv_data))

    miya_path = DATA_DIR / "miya_proj.csv"
    if miya_path.exists():
        with open(miya_path) as f:
            lines = [l.strip() for l in f.readlines()]
        miya_data = {}
        data_lines = lines[8:]
        for i in range(0, len(data_lines), 8):
            chunk = data_lines[i:i + 8]
            if len(chunk) < 8:
                break
            team = _normalize_name(chunk[0])
            try:
                miya_data[team] = {
                    "R32": float(chunk[2].replace("%", "")) / 100,
                    "S16": float(chunk[3].replace("%", "")) / 100,
                    "E8": float(chunk[4].replace("%", "")) / 100,
                    "F4": float(chunk[5].replace("%", "")) / 100,
                    "Championship": float(chunk[6].replace("%", "")) / 100,
                    "Champion": float(chunk[7].replace("%", "")) / 100,
                }
            except (ValueError, IndexError):
                continue
        sources.append(("Miya", miya_data))

    kp_path = DATA_DIR / "kenpom_proj.csv"
    if kp_path.exists():
        kp = pd.read_csv(kp_path)
        total_sims = kp["Rd2"].max() / 0.998
        kp_data = {}
        for _, row in kp.iterrows():
            team = _normalize_name(row["Team"])
            kp_data[team] = {
                "R32": row.get("Rd2", 0) / total_sims,
                "S16": row.get("Swt16", 0) / total_sims,
                "E8": row.get("Elite8", 0) / total_sims,
                "F4": row.get("Final4", 0) / total_sims,
                "Championship": row.get("Final", 0) / total_sims,
                "Champion": row.get("Champ", 0) / total_sims,
            }
        sources.append(("KenPom", kp_data))

    if not sources:
        return None

    consensus = {}
    all_teams = set()
    for _, data in sources:
        all_teams.update(data.keys())

    for team in all_teams:
        consensus[team] = {}
        for rnd in _ROUND_COLS:
            values = [data[team][rnd] for _, data in sources
                      if team in data and not np.isnan(data[team].get(rnd, 0))]
            consensus[team][rnd] = np.mean(values) if values else 0.0

    return consensus


def estimate_public_picks(bracket: dict, sim_results: pd.DataFrame) -> dict:
    """Estimate public pick distributions for every bracket slot.

    First tries to load real consensus projections from Torvik/Miya/KenPom
    CSV files. Falls back to seed-based heuristics if no data available.

    Returns dict: {team_name: {round_name: unconditional_probability}}
    """
    # Try loading real consensus data
    bracket_teams = set()
    for seeds in bracket["regions"].values():
        bracket_teams.update(seeds.values())

    consensus = load_consensus_projections(bracket_teams)

    if consensus:
        # Use consensus projections directly as public picks
        public = {}
        for team in sim_results.index:
            if team in consensus:
                public[team] = dict(consensus[team])
            else:
                # Team not in projections — use tiny defaults
                public[team] = {rnd: 0.001 for rnd in _ROUND_COLS}
        return public

    # Fallback: seed-based heuristic estimates
    return _estimate_public_from_seeds(bracket, sim_results)


def _estimate_public_from_seeds(bracket: dict, sim_results: pd.DataFrame) -> dict:
    """Fallback: estimate public picks from seed position + model blend."""
    regions = bracket["regions"]
    public = {}

    seed_lookup = {}
    for region_name, seeds in regions.items():
        for seed_str, team in seeds.items():
            seed_lookup[team] = (region_name, int(seed_str))

    for team in sim_results.index:
        public[team] = {"R32": 0.0, "S16": 0.0, "E8": 0.0,
                        "F4": 0.0, "Championship": 0.0, "Champion": 0.0}

    for region_name, seeds in regions.items():
        matchups = [(seeds[str(s1)], seeds[str(s2)])
                    for s1, s2 in MATCHUP_ORDER]

        for (t1, t2), (s1, s2) in zip(matchups, MATCHUP_ORDER):
            rate = PUBLIC_R64_RATES.get((s1, s2), 0.55)
            public[t1]["R32"] = rate
            public[t2]["R32"] = 1 - rate

    # Champion: seed-based
    for team in sim_results.index:
        _, seed = seed_lookup.get(team, ("", 16))
        public[team]["Champion"] = PUBLIC_CHAMPION_BY_SEED.get(seed, 0.0005)
        public[team]["Championship"] = min(public[team]["Champion"] * 2, 0.5)

    return public


def compute_pick_ev(model_prob: float, points: int, public_prob: float,
                    pool_size: int) -> float:
    """Compute expected value of a bracket pick in a pool context.

    Core idea: in a pool of N people, you don't just need to be right —
    you need to be right AND different. The value of a correct pick is
    diminished when everyone else also picked it, because you don't gain
    ground on competitors.

    Uniqueness bonus: if you pick team X correctly and only K of N-1
    opponents also picked it, you gain points over (N-1-K) people.
    E[opponents who also picked X] = public_prob × (N-1).

    So: pick_value ∝ model_prob × points × (1 - public_prob)^(alpha)
    where alpha scales with pool size (no differentiation needed in small pools).
    """
    base_ev = model_prob * points

    if pool_size <= 5:
        return base_ev

    # Alpha: how much to weight differentiation (0 to 1)
    # Ramps from ~0.15 at pool_size=10 to ~1.0 at pool_size=500+
    alpha = min(np.log(pool_size / 5) / np.log(100), 1.0)

    # Differentiation factor: picks that fewer opponents make are more valuable
    # when correct. This models the fraction of the field you "beat" with this pick.
    # ownership = expected fraction of opponents who also picked this team
    ownership = min(public_prob, 0.95)  # cap to avoid degenerate cases

    # Edge ratio: how much better is our model than public on this pick?
    # If model says 30% and public says 20%, we're getting a 30% hit rate
    # on a pick only 20% of opponents have → good deal.
    # Conversely if model=20% and public=30%, we hit less often but so does everyone.
    edge = model_prob / max(public_prob, 0.005)

    # Differentiation-adjusted EV:
    # Base EV × (edge ^ alpha) gives more weight to contrarian picks in large pools
    return base_ev * (edge ** (alpha * 0.65))


def optimize_bracket(bracket: dict, sim_results: pd.DataFrame,
                     pool_size: int, public_picks: dict) -> dict:
    """Generate optimal bracket picks for a given pool size.

    Walks the bracket tree, selecting picks that maximize pool-adjusted EV
    at each slot. Path consistency is enforced (later picks must follow
    from earlier picks).

    Returns dict mapping round -> list of picked teams, plus metadata.
    """
    regions = bracket["regions"]
    ff_matchups = bracket["final_four_matchups"]

    picks = {"R32": [], "S16": [], "E8": [], "F4": [],
             "Championship": [], "Champion": []}
    annotations = {"R32": [], "S16": [], "E8": [], "F4": [],
                   "Championship": [], "Champion": []}

    region_winners = {}

    for region_name, seeds in regions.items():
        matchups = [(seeds[str(s1)], seeds[str(s2)], s1, s2)
                    for s1, s2 in MATCHUP_ORDER]

        # R64 → R32
        r32_teams = []
        for t1, t2, s1, s2 in matchups:
            t1_model = sim_results.loc[t1, "R32"] / 100 if t1 in sim_results.index else 0
            t2_model = sim_results.loc[t2, "R32"] / 100 if t2 in sim_results.index else 0
            t1_pub = public_picks.get(t1, {}).get("R32", 0.5)
            t2_pub = public_picks.get(t2, {}).get("R32", 0.5)

            t1_ev = compute_pick_ev(t1_model, ROUND_POINTS["R32"], t1_pub, pool_size)
            t2_ev = compute_pick_ev(t2_model, ROUND_POINTS["R32"], t2_pub, pool_size)

            if t1_ev >= t2_ev:
                pick, pick_model, pick_pub, loser = t1, t1_model, t1_pub, t2
                pick_seed, loser_seed = s1, s2
            else:
                pick, pick_model, pick_pub, loser = t2, t2_model, t2_pub, t1
                pick_seed, loser_seed = s2, s1

            r32_teams.append(pick)
            picks["R32"].append(pick)
            upset = pick_seed > loser_seed
            annotations["R32"].append({
                "team": pick, "seed": pick_seed, "opponent": loser,
                "opp_seed": loser_seed, "model": pick_model, "public": pick_pub,
                "upset": upset,
            })

        # R32 → S16
        s16_teams = []
        for i in range(0, len(r32_teams), 2):
            t1, t2 = r32_teams[i], r32_teams[i + 1]
            t1_model = sim_results.loc[t1, "S16"] / 100 if t1 in sim_results.index else 0
            t2_model = sim_results.loc[t2, "S16"] / 100 if t2 in sim_results.index else 0
            t1_pub = public_picks.get(t1, {}).get("S16", 0.5)
            t2_pub = public_picks.get(t2, {}).get("S16", 0.5)

            t1_ev = compute_pick_ev(t1_model, ROUND_POINTS["S16"], t1_pub, pool_size)
            t2_ev = compute_pick_ev(t2_model, ROUND_POINTS["S16"], t2_pub, pool_size)

            pick = t1 if t1_ev >= t2_ev else t2
            pick_model = t1_model if pick == t1 else t2_model
            pick_pub = t1_pub if pick == t1 else t2_pub
            s16_teams.append(pick)
            picks["S16"].append(pick)
            annotations["S16"].append({
                "team": pick, "model": pick_model, "public": pick_pub,
                "leverage": pick_model / max(pick_pub, 0.001),
            })

        # S16 → E8
        e8_teams = []
        for i in range(0, len(s16_teams), 2):
            t1, t2 = s16_teams[i], s16_teams[i + 1]
            t1_model = sim_results.loc[t1, "E8"] / 100 if t1 in sim_results.index else 0
            t2_model = sim_results.loc[t2, "E8"] / 100 if t2 in sim_results.index else 0
            t1_pub = public_picks.get(t1, {}).get("E8", 0.3)
            t2_pub = public_picks.get(t2, {}).get("E8", 0.3)

            t1_ev = compute_pick_ev(t1_model, ROUND_POINTS["E8"], t1_pub, pool_size)
            t2_ev = compute_pick_ev(t2_model, ROUND_POINTS["E8"], t2_pub, pool_size)

            pick = t1 if t1_ev >= t2_ev else t2
            pick_model = t1_model if pick == t1 else t2_model
            pick_pub = t1_pub if pick == t1 else t2_pub
            e8_teams.append(pick)
            picks["E8"].append(pick)
            annotations["E8"].append({
                "team": pick, "model": pick_model, "public": pick_pub,
                "leverage": pick_model / max(pick_pub, 0.001),
            })

        # E8 → F4
        t1, t2 = e8_teams[0], e8_teams[1]
        t1_model = sim_results.loc[t1, "F4"] / 100 if t1 in sim_results.index else 0
        t2_model = sim_results.loc[t2, "F4"] / 100 if t2 in sim_results.index else 0
        t1_pub = public_picks.get(t1, {}).get("F4", 0.3)
        t2_pub = public_picks.get(t2, {}).get("F4", 0.3)

        t1_ev = compute_pick_ev(t1_model, ROUND_POINTS["F4"], t1_pub, pool_size)
        t2_ev = compute_pick_ev(t2_model, ROUND_POINTS["F4"], t2_pub, pool_size)

        pick = t1 if t1_ev >= t2_ev else t2
        pick_model = t1_model if pick == t1 else t2_model
        pick_pub = t1_pub if pick == t1 else t2_pub
        picks["F4"].append(pick)
        region_winners[region_name] = pick
        annotations["F4"].append({
            "team": pick, "region": region_name,
            "model": pick_model, "public": pick_pub,
            "leverage": pick_model / max(pick_pub, 0.001),
        })

    # Final Four
    ff_winners = []
    for r1, r2 in ff_matchups:
        t1 = region_winners[r1]
        t2 = region_winners[r2]
        t1_model = sim_results.loc[t1, "Championship"] / 100 if t1 in sim_results.index else 0
        t2_model = sim_results.loc[t2, "Championship"] / 100 if t2 in sim_results.index else 0
        t1_pub = public_picks.get(t1, {}).get("Championship", 0.1)
        t2_pub = public_picks.get(t2, {}).get("Championship", 0.1)

        t1_ev = compute_pick_ev(t1_model, ROUND_POINTS["Championship"], t1_pub, pool_size)
        t2_ev = compute_pick_ev(t2_model, ROUND_POINTS["Championship"], t2_pub, pool_size)

        pick = t1 if t1_ev >= t2_ev else t2
        pick_model = t1_model if pick == t1 else t2_model
        pick_pub = t1_pub if pick == t1 else t2_pub
        ff_winners.append(pick)
        picks["Championship"].append(pick)
        annotations["Championship"].append({
            "team": pick, "matchup": f"{r1} vs {r2}",
            "model": pick_model, "public": pick_pub,
        })

    # Championship
    t1, t2 = ff_winners[0], ff_winners[1]
    t1_model = sim_results.loc[t1, "Champion"] / 100 if t1 in sim_results.index else 0
    t2_model = sim_results.loc[t2, "Champion"] / 100 if t2 in sim_results.index else 0
    t1_pub = public_picks.get(t1, {}).get("Champion", 0.05)
    t2_pub = public_picks.get(t2, {}).get("Champion", 0.05)

    t1_ev = compute_pick_ev(t1_model, ROUND_POINTS["Champion"], t1_pub, pool_size)
    t2_ev = compute_pick_ev(t2_model, ROUND_POINTS["Champion"], t2_pub, pool_size)

    pick = t1 if t1_ev >= t2_ev else t2
    pick_model = t1_model if pick == t1 else t2_model
    pick_pub = t1_pub if pick == t1 else t2_pub
    picks["Champion"] = [pick]
    annotations["Champion"] = [{
        "team": pick, "model": pick_model, "public": pick_pub,
        "leverage": pick_model / max(pick_pub, 0.001),
    }]

    return {"picks": picks, "annotations": annotations, "pool_size": pool_size}


def format_bracket(result: dict, bracket: dict, sim_results: pd.DataFrame) -> str:
    """Format optimized bracket as human-readable text."""
    picks = result["picks"]
    annotations = result["annotations"]
    pool_size = result["pool_size"]
    regions = bracket["regions"]

    lines = []
    lines.append(f"OPTIMIZED BRACKET (pool size: {pool_size})")
    lines.append("=" * 70)

    # Determine strategy label
    if pool_size <= 10:
        strategy = "Max Expected Score — pick the best team in every game"
    elif pool_size <= 50:
        strategy = "Moderate leverage — chalk core with selective contrarian picks"
    else:
        strategy = "High leverage — differentiate where model has edge over public"
    lines.append(f"Strategy: {strategy}")
    lines.append("")

    # Champion
    champ = annotations["Champion"][0]
    lines.append(f"CHAMPION: {champ['team']} "
                 f"(model: {champ['model']:.1%}, public: ~{champ['public']:.1%}, "
                 f"leverage: {champ['leverage']:.1f}x)")
    lines.append("")

    # Count upsets and contrarian picks (leverage > 1.3 in late rounds)
    upset_count = sum(1 for a in annotations["R32"] if a.get("upset"))
    contrarian_deep = sum(1 for rnd in ["S16", "E8", "F4"]
                         for a in annotations[rnd]
                         if a.get("leverage", 1.0) > 1.3)
    lines.append(f"R64 upsets: {upset_count}  |  Contrarian late-round picks: {contrarian_deep}")
    lines.append("")

    # Per-region breakdown
    region_order = list(regions.keys())
    r32_idx = 0
    s16_idx = 0
    e8_idx = 0
    f4_idx = 0

    for region_name in region_order:
        seeds = regions[region_name]
        lines.append(f"{region_name.upper()} REGION")
        lines.append("-" * 50)

        # R64 picks (8 per region)
        lines.append("  R64 (10 pts):")
        for j in range(8):
            a = annotations["R32"][r32_idx + j]
            marker = "*UPSET*" if a["upset"] else ""
            lev = a["model"] / max(a["public"], 0.001)
            contrarian = " *CONTRARIAN*" if lev > 1.5 and a["upset"] else ""
            lines.append(f"    ({a['seed']:>2}) {a['team']:<22} over "
                        f"({a['opp_seed']:>2}) {a['opponent']:<18} "
                        f"P={a['model']:.1%}{contrarian}")
        r32_idx += 8

        # R32 picks (4 per region)
        lines.append("  R32 (20 pts):")
        for j in range(4):
            a = annotations["S16"][s16_idx + j]
            lev = a.get("leverage", 1.0)
            lev_str = f"  [{lev:.1f}x]" if lev > 1.3 or lev < 0.8 else ""
            lines.append(f"    {a['team']:<26} P={a['model']:.1%}{lev_str}")
        s16_idx += 4

        # S16 picks (2 per region)
        lines.append("  S16 (40 pts):")
        for j in range(2):
            a = annotations["E8"][e8_idx + j]
            lev = a.get("leverage", 1.0)
            lev_str = f"  [{lev:.1f}x]" if lev > 1.3 or lev < 0.8 else ""
            lines.append(f"    {a['team']:<26} P={a['model']:.1%}{lev_str}")
        e8_idx += 2

        # E8 pick (1 per region = F4)
        a = annotations["F4"][f4_idx]
        lev = a.get("leverage", 1.0)
        lev_str = f"  [{lev:.1f}x]" if lev > 1.3 or lev < 0.8 else ""
        lines.append(f"  E8 (80 pts):")
        lines.append(f"    {a['team']:<26} P={a['model']:.1%}{lev_str}")
        f4_idx += 1

        lines.append("")

    # Final Four
    lines.append("FINAL FOUR (160 pts)")
    lines.append("-" * 50)
    for a in annotations["Championship"]:
        lines.append(f"  {a['team']:<26} ({a['matchup']})  P={a['model']:.1%}")

    # Championship
    lines.append("")
    lines.append("CHAMPIONSHIP (320 pts)")
    lines.append("-" * 50)
    a = annotations["Champion"][0]
    lines.append(f"  {a['team']:<26} P={a['model']:.1%} "
                f"(leverage: {a['leverage']:.1f}x)")

    # Expected score estimate
    total_ev = 0
    for rnd in ["R32", "S16", "E8", "F4", "Championship", "Champion"]:
        for a in annotations[rnd]:
            total_ev += a["model"] * ROUND_POINTS.get(rnd, 320)
    lines.append("")
    lines.append(f"Estimated Expected Score: {total_ev:.0f} / 1920")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    from torvik import fetch_team_stats, fetch_player_stats, fetch_player_stats_daterange

    bracket_path = sys.argv[1] if len(sys.argv) > 1 else "brackets/bracket_2026.json"
    n_sims = int(sys.argv[2]) if len(sys.argv) > 2 else 10000

    # Parse pool sizes from args
    pool_sizes = [10, 50, 200]
    if "--pool-sizes" in sys.argv:
        idx = sys.argv.index("--pool-sizes")
        pool_sizes = []
        for i in range(idx + 1, len(sys.argv)):
            try:
                pool_sizes.append(int(sys.argv[i]))
            except ValueError:
                break

    print("Loading model and data...")
    predictor = GamePredictor.load()

    teams_df = fetch_team_stats(2026).set_index("team")
    players_df = fetch_player_stats(2026)

    # Recent stats for form features
    cutoff_dt = pd.to_datetime("20260316", format="%Y%m%d")
    recent_start = (cutoff_dt - pd.Timedelta(days=30)).strftime("%Y%m%d")
    try:
        recent_players_df = fetch_player_stats_daterange(2026, recent_start, "20260316")
    except Exception:
        recent_players_df = None

    # Injuries
    injuries_path = Path(__file__).resolve().parent / "config" / "injuries.json"
    exclusions = None
    weights = None
    if injuries_path.exists():
        with open(injuries_path) as f:
            inj = json.load(f)
        exclusions = inj.get("2026", {}) or None
        weights = inj.get("_weights_2026", {}) or None

    player_feats = build_player_features(players_df, recent_players_df=recent_players_df,
                                         exclusions=exclusions, weights=weights)

    with open(bracket_path) as f:
        bracket = json.load(f)

    # Load consensus for simulation blending
    consensus = load_consensus_projections(set())
    if consensus:
        print("Loaded consensus projections for blending (weight=0.3)")
    else:
        print("No consensus projections found — using model only")

    print(f"Running {n_sims} simulations...")
    sim = BracketSimulator(predictor, teams_df, player_feats,
                           consensus=consensus, consensus_weight=0.3)
    sim_results = sim.simulate_tournament(bracket, n_sims=n_sims)

    # Load consensus projections
    consensus = load_consensus_projections(set())
    if consensus:
        print("Loaded consensus projections (Torvik + Miya + KenPom)")
    else:
        print("No projection CSVs found — using seed-based public estimates")

    print("Estimating public pick distributions...")
    public_picks = estimate_public_picks(bracket, sim_results)

    # Show leverage analysis for top teams
    print("\n" + "=" * 70)
    print("LEVERAGE ANALYSIS — Model vs Consensus")
    print(f"{'Team':<22} {'Model':>7} {'Consensus':>10} {'Leverage':>9}")
    print("-" * 50)
    top_teams = sim_results.nlargest(20, "Champion")
    for team in top_teams.index:
        model_p = sim_results.loc[team, "Champion"] / 100
        pub_p = public_picks.get(team, {}).get("Champion", 0.001)
        lev = model_p / max(pub_p, 0.001)
        print(f"{team:<22} {model_p:>7.1%} {pub_p:>10.1%} {lev:>8.1f}x")

    # Generate optimized brackets for each pool size
    for ps in pool_sizes:
        print(f"\n{'=' * 70}")
        result = optimize_bracket(bracket, sim_results, ps, public_picks)
        output = format_bracket(result, bracket, sim_results)
        print(output)

        # Save to file
        fname = f"bracket_pool_{ps}.txt"
        fpath = RESULTS_DIR / fname
        with open(fpath, "w") as f:
            f.write(output + "\n")
        print(f"\nSaved → {fpath}")
