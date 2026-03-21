"""Build a consensus bracket from multiple simulation sources + sentiment analysis.

Sources:
  1. Torvik (torvik_proj.csv)
  2. Evan Miya (miya_proj.csv)
  3. KenPom (kenpom_proj.csv)
  4. CBB Analytics (cbb_proj.csv)
  5. Sentiment adjustments from transcript analysis

Usage:
    python consensus_bracket.py
    python consensus_bracket.py --no-sentiment   # Skip sentiment adjustments
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

DATA = Path(__file__).resolve().parent / "data"
BRACKET_PATH = Path(__file__).resolve().parent / "brackets" / "bracket_2026.json"

# ── Name normalization ──────────────────────────────────────────────────────

ALIASES = {
    # Miya names
    "Connecticut": "UConn",
    "Iowa State": "Iowa St.",
    "Michigan State": "Michigan St.",
    "Ohio State": "Ohio St.",
    "Miami (Fla.)": "Miami FL",
    "Miami (OH)": "Miami OH",
    "McNeese State": "McNeese St.",
    "North Carolina State": "NC State",
    "N.C. State": "NC State",
    "Long Island": "LIU",
    "California Baptist": "Cal Baptist",
    "North Dakota State": "North Dakota St.",
    "Northern Iowa": "Northern Iowa",
    "Wright State": "Wright St.",
    "Tennessee State": "Tennessee St.",
    "Kennesaw State": "Kennesaw St.",
    "Prairie View": "Prairie View A&M",
    "Prairie View A&M": "Prairie View A&M",
    # CBB proj names
    "UConn": "UConn",
    "South Florida": "South Florida",
    # KenPom region codes
}


def normalize(name: str) -> str:
    name = name.strip()
    return ALIASES.get(name, name)


# ── Loaders ─────────────────────────────────────────────────────────────────

def load_torvik() -> dict[str, dict[str, float]]:
    """Returns {team: {R32, S16, E8, F4, F2, Champ}} in percentages."""
    teams = {}
    with open(DATA / "torvik_proj.csv") as f:
        reader = csv.DictReader(f)
        for row in reader:
            team = normalize(row["Team"])
            teams[team] = {
                "R32": float(row["R32"]) if row["R32"] != "✓" else 100.0,
                "S16": float(row["S16"]),
                "E8": float(row["E8"]),
                "F4": float(row["F4"]),
                "F2": float(row["F2"]),
                "Champ": float(row["Champ"]),
            }
    return teams


def load_miya() -> dict[str, dict[str, float]]:
    """Parse vertical format miya_proj.csv."""
    teams = {}
    with open(DATA / "miya_proj.csv") as f:
        lines = [l.strip() for l in f.readlines()]

    # Skip 8-line header
    i = 8
    while i + 5 < len(lines):
        team = normalize(lines[i])
        # skip seed line
        pcts = []
        for j in range(i + 2, i + 8):
            val = lines[j].replace("%", "").strip()
            pcts.append(float(val))
        teams[team] = {
            "R32": pcts[0],
            "S16": pcts[1],
            "E8": pcts[2],
            "F4": pcts[3],
            "F2": pcts[4],
            "Champ": pcts[5],
        }
        i += 8
    return teams


def load_kenpom() -> dict[str, dict[str, float]]:
    """KenPom uses raw counts out of ~1M simulations."""
    teams = {}
    with open(DATA / "kenpom_proj.csv") as f:
        reader = csv.DictReader(f)
        for row in reader:
            team = normalize(row["Team"])
            # Convert raw counts to percentages (out of 1M)
            teams[team] = {
                "R32": float(row["Rd2"]) / 10000,
                "S16": float(row["Swt16"]) / 10000,
                "E8": float(row["Elite8"]) / 10000,
                "F4": float(row["Final4"]) / 10000,
                "F2": float(row["Final"]) / 10000,
                "Champ": float(row["Champ"]) / 10000,
            }
    return teams


def load_cbb() -> dict[str, dict[str, float]]:
    teams = {}
    with open(DATA / "cbb_proj.csv") as f:
        reader = csv.DictReader(f)
        for row in reader:
            team = normalize(row["Team"])
            teams[team] = {
                "R32": float(row["R32"]),
                "S16": float(row["S16"]),
                "E8": float(row["E8"]),
                "F4": float(row["F4"]),
                "F2": float(row["F2"]),
                "Champ": float(row["Champ"]),
            }
    return teams


# ── Sentiment adjustments ───────────────────────────────────────────────────

# Multipliers on consensus probabilities derived from transcript analysis.
# >1.0 = analysts are more bullish than models, <1.0 = bearish.
# Applied to all rounds.

SENTIMENT_ADJUSTMENTS = {
    # === Strong consensus bullish (underseeded / bracket value) ===
    "St. John's": 1.20,       # "Most underseeded team" — universal, data-driven
    "Wisconsin": 1.18,         # Universal sleeper, wins at Michigan/Illinois/Purdue
    "Vanderbilt": 1.15,        # "Closer to a 3 than a 5", beat Florida by 17

    # === Moderate bullish ===
    "Michigan": 1.08,          # Bracket value darling (14% public vs 18-27% model)
    "Illinois": 1.08,          # "Least discussed threat", massive bracket value
    "Tennessee": 1.06,         # 46% OREB rate historically elite, bully ball floor
    "Texas Tech": 1.05,        # McCasland coaching, still 14th at Torvik post-Toppin
    "UCLA": 1.10,              # Dent elite since Feb 18, ranked 8th recent form
    "Arkansas": 1.05,          # SEC tourney champs, Akoff averaging 30+

    # === Upset-specific boosts (applied to underdogs) ===
    "VCU": 1.30,               # ~8/9 sources pick over UNC, model-favored by 1
    "Santa Clara": 1.30,       # ~8/9 sources pick over Kentucky, data-backed
    "South Florida": 1.25,     # ~7/9 sources pick over Louisville
    "Hofstra": 1.35,           # ~6/9 sources, top-5 2PT defense, Alabama weakened
    "Troy": 1.15,              # ~4/9 sources, #1 opponent strength adjustment
    "Texas A&M": 1.10,         # ~4/9 sources over St. Mary's

    # === Bearish (models too high) ===
    "Florida": 0.88,           # 6/9 sources fade, brutal draw, Vandy beat by 17
    "UConn": 0.85,             # Universal distrust, weakest 2 seed
    "Alabama": 0.80,           # Holloway out, 12pt efficiency drop, worst D on 1-6 lines
    "North Carolina": 0.75,    # Very bearish, 350th momentum, Wilson out
    "Kentucky": 0.80,          # "Hot garbage", 355th away from home
    "Louisville": 0.82,        # Paper tiger, multiple sources pick against
    "Kansas": 0.90,            # 138th rebound/TO differential, tough draw
    "Villanova": 0.85,         # "Most mid team", zero faith vs quality
    "BYU": 0.88,               # Saunders out, 363rd momentum
    "Saint Mary's": 0.90,      # 359th away from home, A&M pressure concern

    # === Polarizing (slight fade — bear case stronger) ===
    "Purdue": 0.95,            # Sharp split but "four days don't define a season"
}

# ── Injury adjustments ──────────────────────────────────────────────────────
# Multipliers for confirmed injuries NOT already in simulation models.
# These stack with sentiment adjustments.

INJURY_ADJUSTMENTS = {
    # === Confirmed OUT (not reflected in published simulations) ===
    "Alabama": 0.78,           # Holloway OUT (arrested): 61.6% Min, 16.8 PPG, BPM 6.10
    "Louisville": 0.82,        # Mikel Brown Jr OUT (back): 46.4% Min, 18.2 PPG (team 12-1 w/o him softens blow)
    "SMU": 0.60,               # B.J. Edwards OUT (ankle): 69.8% Min, BPM 8.07 — team's engine, devastating

    # === GTD / questionable — partial discount ===
    "Wisconsin": 0.88,         # Nolan Winter GTD (ankle): 67.6% Min, BPM 9.23 — best player + Janicki GTD
    "Duke": 0.96,              # Foster OUT for tournament; Ngongba GTD but expected to return. Deep enough to absorb
    "UCLA": 0.92,              # Bilodeau GTD (knee): 68% Min, leading scorer; already 0.5 weight in model
    "Arkansas": 0.95,          # Knox GTD (knee): 35% Min, rotation piece; deep team
}


# ── Consensus builder ───────────────────────────────────────────────────────

def build_consensus(
    sources: list[dict[str, dict[str, float]]],
    use_sentiment: bool = True,
    use_injuries: bool = True,
) -> dict[str, dict[str, float]]:
    """Average probabilities across sources, then apply sentiment + injury adjustments."""
    all_teams = set()
    for src in sources:
        all_teams.update(src.keys())

    consensus = {}
    for team in all_teams:
        rounds_data: dict[str, list[float]] = {}
        for src in sources:
            if team in src:
                for rd, val in src[team].items():
                    rounds_data.setdefault(rd, []).append(val)

        avg = {}
        for rd, vals in rounds_data.items():
            avg[rd] = sum(vals) / len(vals)

        # Apply sentiment multiplier
        if use_sentiment and team in SENTIMENT_ADJUSTMENTS:
            mult = SENTIMENT_ADJUSTMENTS[team]
            avg = {rd: min(v * mult, 99.9) for rd, v in avg.items()}

        # Apply injury multiplier (stacks with sentiment)
        if use_injuries and team in INJURY_ADJUSTMENTS:
            mult = INJURY_ADJUSTMENTS[team]
            avg = {rd: min(v * mult, 99.9) for rd, v in avg.items()}

        consensus[team] = avg

    return consensus


# ── Bracket filling ─────────────────────────────────────────────────────────

def load_bracket() -> dict:
    with open(BRACKET_PATH) as f:
        return json.load(f)


def pick_winner(team_a: str, team_b: str, round_key: str,
                consensus: dict[str, dict[str, float]]) -> tuple[str, float, float]:
    """Pick the team with higher consensus probability of reaching the next round."""
    prob_a = consensus.get(team_a, {}).get(round_key, 0.0)
    prob_b = consensus.get(team_b, {}).get(round_key, 0.0)
    if prob_a >= prob_b:
        return team_a, prob_a, prob_b
    return team_b, prob_b, prob_a


def fill_region(region_name: str, seeds: dict[str, str],
                consensus: dict[str, dict[str, float]]) -> dict:
    """Fill a region bracket. Returns round-by-round results."""
    # Normalize bracket team names to match consensus dict keys
    norm_seeds = {k: normalize(v) for k, v in seeds.items()}
    # Standard bracket matchups: 1v16, 8v9, 5v12, 4v13, 6v11, 3v14, 7v10, 2v15
    r64_matchups = [
        (norm_seeds["1"], norm_seeds["16"]),
        (norm_seeds["8"], norm_seeds["9"]),
        (norm_seeds["5"], norm_seeds["12"]),
        (norm_seeds["4"], norm_seeds["13"]),
        (norm_seeds["6"], norm_seeds["11"]),
        (norm_seeds["3"], norm_seeds["14"]),
        (norm_seeds["7"], norm_seeds["10"]),
        (norm_seeds["2"], norm_seeds["15"]),
    ]

    results = {"region": region_name, "R64": [], "R32": [], "S16": [], "E8_winner": None}

    # Round of 64 → Round of 32
    r32_teams = []
    for a, b in r64_matchups:
        winner, wp, lp = pick_winner(a, b, "R32", consensus)
        results["R64"].append({"matchup": f"{a} vs {b}", "winner": winner,
                               "winner_pct": round(wp, 1), "loser_pct": round(lp, 1)})
        r32_teams.append(winner)

    # Round of 32 → Sweet 16
    s16_teams = []
    for i in range(0, 8, 2):
        a, b = r32_teams[i], r32_teams[i + 1]
        winner, wp, lp = pick_winner(a, b, "S16", consensus)
        results["R32"].append({"matchup": f"{a} vs {b}", "winner": winner,
                               "winner_pct": round(wp, 1), "loser_pct": round(lp, 1)})
        s16_teams.append(winner)

    # Sweet 16 → Elite 8
    e8_teams = []
    for i in range(0, 4, 2):
        a, b = s16_teams[i], s16_teams[i + 1]
        winner, wp, lp = pick_winner(a, b, "E8", consensus)
        results["S16"].append({"matchup": f"{a} vs {b}", "winner": winner,
                               "winner_pct": round(wp, 1), "loser_pct": round(lp, 1)})
        e8_teams.append(winner)

    # Elite 8
    a, b = e8_teams[0], e8_teams[1]
    winner, wp, lp = pick_winner(a, b, "F4", consensus)
    results["E8"] = {"matchup": f"{a} vs {b}", "winner": winner,
                     "winner_pct": round(wp, 1), "loser_pct": round(lp, 1)}
    results["E8_winner"] = winner

    return results


def fill_bracket(consensus: dict[str, dict[str, float]], use_sentiment: bool = True):
    bracket = load_bracket()
    regions = bracket["regions"]
    ff_matchups = bracket["final_four_matchups"]

    print("=" * 72)
    label = "(models + sentiment + injuries)" if use_sentiment else "(models only)"
    print(f"  CONSENSUS BRACKET 2026  {label}")
    print("=" * 72)

    region_results = {}
    ff_teams = {}

    for region_name, seeds in regions.items():
        result = fill_region(region_name, seeds, consensus)
        region_results[region_name] = result
        ff_teams[region_name] = result["E8_winner"]

        print(f"\n{'─' * 72}")
        print(f"  {region_name.upper()} REGION")
        print(f"{'─' * 72}")

        print("\n  Round of 64:")
        for g in result["R64"]:
            marker = " ←UPSET" if g["loser_pct"] > g["winner_pct"] * 0.6 and g["winner_pct"] < 70 else ""
            print(f"    {g['matchup']:40s} → {g['winner']:20s} ({g['winner_pct']:5.1f}% vs {g['loser_pct']:5.1f}%){marker}")

        print("\n  Round of 32:")
        for g in result["R32"]:
            print(f"    {g['matchup']:40s} → {g['winner']:20s} ({g['winner_pct']:5.1f}% vs {g['loser_pct']:5.1f}%)")

        print("\n  Sweet 16:")
        for g in result["S16"]:
            print(f"    {g['matchup']:40s} → {g['winner']:20s} ({g['winner_pct']:5.1f}% vs {g['loser_pct']:5.1f}%)")

        print(f"\n  Elite 8:")
        g = result["E8"]
        print(f"    {g['matchup']:40s} → {g['winner']:20s} ({g['winner_pct']:5.1f}% vs {g['loser_pct']:5.1f}%)")
        print(f"\n  ★ {region_name} winner: {result['E8_winner']}")

    # Final Four
    print(f"\n{'=' * 72}")
    print("  FINAL FOUR")
    print(f"{'=' * 72}")

    champ_teams = []
    for pair in ff_matchups:
        a_region, b_region = pair
        a_team = ff_teams[a_region]
        b_team = ff_teams[b_region]
        winner, wp, lp = pick_winner(a_team, b_team, "F2", consensus)
        print(f"\n  {a_region} vs {b_region}:")
        print(f"    {a_team} vs {b_team} → {winner} ({wp:.1f}% vs {lp:.1f}%)")
        champ_teams.append(winner)

    # Championship
    print(f"\n{'=' * 72}")
    print("  NATIONAL CHAMPIONSHIP")
    print(f"{'=' * 72}")
    a, b = champ_teams[0], champ_teams[1]
    champion, wp, lp = pick_winner(a, b, "Champ", consensus)
    print(f"\n  {a} vs {b} → {champion} ({wp:.1f}% vs {lp:.1f}%)")
    print(f"\n  {'★' * 3} CHAMPION: {champion} {'★' * 3}")

    # Summary
    print(f"\n{'=' * 72}")
    print("  FINAL FOUR SUMMARY")
    print(f"{'=' * 72}")
    for region_name in regions:
        print(f"    {region_name:10s}: {ff_teams[region_name]}")
    print(f"    {'Champion':10s}: {champion}")

    # Write results to file
    output = {
        "method": "consensus_aggregate" + ("_with_sentiment" if use_sentiment else "_models_only"),
        "sources": ["torvik", "evan_miya", "kenpom", "cbb_analytics"],
        "sentiment_applied": use_sentiment,
        "regions": {},
        "final_four": {},
        "champion": champion,
    }
    for region_name, result in region_results.items():
        output["regions"][region_name] = {
            "winner": result["E8_winner"],
            "path": [g["winner"] for g in result["R64"]]
                   + [g["winner"] for g in result["R32"]]
                   + [g["winner"] for g in result["S16"]]
                   + [result["E8"]["winner"]],
        }

    out_path = Path(__file__).resolve().parent / "results" / "consensus_bracket.json"
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)
        f.write("\n")
    print(f"\n  Saved → {out_path}")

    return output


# ── Main ────────────────────────────────────────────────────────────────────

def main():
    use_sentiment = "--no-sentiment" not in sys.argv
    use_injuries = "--no-injuries" not in sys.argv

    print("Loading projection sources...")
    torvik = load_torvik()
    miya = load_miya()
    kenpom = load_kenpom()
    cbb = load_cbb()
    print(f"  Torvik:  {len(torvik)} teams")
    print(f"  Miya:    {len(miya)} teams")
    print(f"  KenPom:  {len(kenpom)} teams")
    print(f"  CBB:     {len(cbb)} teams")

    consensus = build_consensus([torvik, miya, kenpom, cbb],
                                use_sentiment=use_sentiment,
                                use_injuries=use_injuries)
    print(f"  Consensus: {len(consensus)} teams")

    if use_sentiment:
        print(f"\n  Sentiment adjustments applied to {len(SENTIMENT_ADJUSTMENTS)} teams")
        boosts = {k: v for k, v in SENTIMENT_ADJUSTMENTS.items() if v > 1.0}
        fades = {k: v for k, v in SENTIMENT_ADJUSTMENTS.items() if v < 1.0}
        print(f"    Boosted: {', '.join(f'{k} ({v:.0%})' for k, v in sorted(boosts.items(), key=lambda x: -x[1]))}")
        print(f"    Faded:   {', '.join(f'{k} ({v:.0%})' for k, v in sorted(fades.items(), key=lambda x: x[1]))}")

    if use_injuries:
        print(f"\n  Injury adjustments applied to {len(INJURY_ADJUSTMENTS)} teams")
        for team, mult in sorted(INJURY_ADJUSTMENTS.items(), key=lambda x: x[1]):
            print(f"    {team:20s}: {mult:.0%}")

    fill_bracket(consensus, use_sentiment=use_sentiment)


if __name__ == "__main__":
    main()
