"""Update config/injuries.json from a college basketball injury report CSV.

Usage:
    python update_injuries.py                          # Default CSV path
    python update_injuries.py --csv path/to/report.csv # Custom CSV path
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

DEFAULT_CSV = Path(__file__).resolve().parent / "data" / "college-basketball-injury-report.csv"
INJURIES_PATH = Path(__file__).resolve().parent / "config" / "injuries.json"

# CSV team name -> Barttorvik team name
TEAM_NAME_MAP = {
    # "State" -> "St." pattern
    "Appalachian State": "Appalachian St.",
    "Arizona State": "Arizona St.",
    "Arkansas State": "Arkansas St.",
    "Ball State": "Ball St.",
    "Boise State": "Boise St.",
    "Cleveland State": "Cleveland St.",
    "Colorado State": "Colorado St.",
    "Delaware State": "Delaware St.",
    "Eastern Washington": "Eastern Washington",
    "Florida State": "Florida St.",
    "Fresno State": "Fresno St.",
    "Georgia State": "Georgia St.",
    "Indiana State": "Indiana St.",
    "Iowa State": "Iowa St.",
    "Jackson State": "Jackson St.",
    "Jacksonville State": "Jacksonville St.",
    "Kansas State": "Kansas St.",
    "Kennesaw State": "Kennesaw St.",
    "Michigan State": "Michigan St.",
    "Mississippi State": "Mississippi St.",
    "Missouri State": "Missouri St.",
    "Montana State": "Montana St.",
    "Murray State": "Murray St.",
    "New Mexico State": "New Mexico St.",
    "Norfolk State": "Norfolk St.",
    "North Carolina State": "NC State",
    "North Dakota State": "North Dakota St.",
    "Ohio State": "Ohio St.",
    "Oklahoma State": "Oklahoma St.",
    "Oregon State": "Oregon St.",
    "Penn State": "Penn St.",
    "Portland State": "Portland St.",
    "Sacramento State": "Sacramento St.",
    "San Diego State": "San Diego St.",
    "San Jose State": "San Jose St.",
    "South Dakota State": "South Dakota St.",
    "Tennessee State": "Tennessee St.",
    "Texas Southern": "Texas Southern",
    "Utah State": "Utah St.",
    "Washington State": "Washington St.",
    "Wichita State": "Wichita St.",
    "Wright State": "Wright St.",

    # Special cases
    "Miami": "Miami FL",
    "Miami (OH)": "Miami OH",
    "Sam Houston": "Sam Houston St.",
    "UNC-Charlotte": "Charlotte",
    "UNC-Wilmington": "UNC Wilmington",
    "Middle Tennessee State": "Middle Tennessee",
    "Middle Tennessee St.": "Middle Tennessee",
    "Loyola-Chicago": "Loyola Chicago",
    "Detroit": "Detroit Mercy",
    "Bethune-Cookman": "Bethune Cookman",
    "College of Charleston": "Charleston",
    "Cal-Santa Barbara": "UC Santa Barbara",
    "Central Florida": "UCF",
    "Louisiana-Lafayette": "Louisiana",
    "St. Mary's (CAL)": "Saint Mary's",
    "St. Joseph's": "Saint Joseph's",
    "Florida International": "FIU",
    "Texas-San Antonio": "UTSA",
    "Pennsylvania": "Penn",
    "Arkansas-Pine Bluff": "Arkansas Pine Bluff",
    "Louisiana State": "LSU",
    "Connecticut": "UConn",
    "North Carolina A&T": "N.C. A&T",
}


def map_team_name(csv_name: str) -> str:
    """Map a CSV team name to its Barttorvik equivalent."""
    if csv_name in TEAM_NAME_MAP:
        return TEAM_NAME_MAP[csv_name]
    return csv_name


def read_injury_csv(csv_path: Path) -> list[dict]:
    """Read injury report CSV and return list of player records."""
    rows = []
    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def build_injuries(rows: list[dict], year: str = "2026") -> dict:
    """Build injuries dict from CSV rows, preserving existing manual entries."""
    # Load existing injuries
    existing = {}
    if INJURIES_PATH.exists():
        with open(INJURIES_PATH) as f:
            existing = json.load(f)

    # Separate existing manual entries for this year
    manual_entries = existing.get(year, {})

    out_for_season: dict[str, list[str]] = {}
    out_pending: dict[str, list[str]] = {}

    for row in rows:
        status = row.get("Status", "").strip()
        player = row.get("Player", "").strip()
        team = map_team_name(row.get("Team", "").strip())

        if not player or not team:
            continue

        if status == "Out For Season":
            out_for_season.setdefault(team, []).append(player)
        elif status == "Out":
            out_pending.setdefault(team, []).append(player)

    # Merge manual entries into out_for_season (preserve manually added players)
    for team, players in manual_entries.items():
        if team not in out_for_season:
            out_for_season[team] = []
        for p in players:
            if p not in out_for_season[team]:
                out_for_season[team].append(p)

    # Sort teams and players for readability
    out_for_season = {k: sorted(v) for k, v in sorted(out_for_season.items())}
    out_pending = {k: sorted(v) for k, v in sorted(out_pending.items())}

    result = {}
    result[year] = out_for_season
    pending_key = f"_out_pending_{year}"
    if out_pending:
        result[pending_key] = {
            "_note": "Players currently 'Out' - review and move to main section as needed",
            **out_pending,
        }

    # Preserve other years from existing file
    for key, value in existing.items():
        if key not in result:
            result[key] = value

    return result


def main():
    parser = argparse.ArgumentParser(description="Update injuries.json from CSV injury report")
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV, help="Path to injury CSV")
    parser.add_argument("--year", default="2026", help="Year key for injuries.json")
    args = parser.parse_args()

    if not args.csv.exists():
        print(f"Error: CSV not found at {args.csv}")
        return

    rows = read_injury_csv(args.csv)
    print(f"Read {len(rows)} injury records from {args.csv}")

    out_season = sum(1 for r in rows if r.get("Status", "").strip() == "Out For Season")
    out = sum(1 for r in rows if r.get("Status", "").strip() == "Out")
    gtd = sum(1 for r in rows if r.get("Status", "").strip() == "Game Time Decision")
    print(f"  Out For Season: {out_season}, Out: {out}, Game Time Decision: {gtd}")

    injuries = build_injuries(rows, year=args.year)
    year_entries = injuries.get(args.year, {})
    pending_entries = injuries.get(f"_out_pending_{args.year}", {})
    pending_count = sum(len(v) for k, v in pending_entries.items() if k != "_note")
    print(f"  -> {sum(len(v) for v in year_entries.values())} players in '{args.year}' (Out For Season + manual)")
    print(f"  -> {pending_count} players in '_out_pending_{args.year}' (Out, for review)")

    INJURIES_PATH.parent.mkdir(exist_ok=True)
    with open(INJURIES_PATH, "w") as f:
        json.dump(injuries, f, indent=2)
        f.write("\n")
    print(f"\nWritten to {INJURIES_PATH}")


if __name__ == "__main__":
    main()
