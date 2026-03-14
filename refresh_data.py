"""Refresh cached Barttorvik data for specified seasons.

Usage:
    python refresh_data.py                  # Refresh 2026 only
    python refresh_data.py 2024 2025 2026   # Refresh multiple years
"""

from __future__ import annotations

import sys

from torvik import fetch_player_stats, fetch_player_stats_daterange, fetch_team_stats, fetch_game_stats

TOURNAMENT_CUTOFFS = {
    2024: 20240318,
    2025: 20250317,
    2026: 20260316,
}


def refresh(years: list[int]):
    for year in years:
        print(f"\n{'=' * 40}")
        print(f"Refreshing {year}")
        print(f"{'=' * 40}")

        print("\n  Player stats (full season)...")
        fetch_player_stats(year, force_refresh=True)

        cutoff = TOURNAMENT_CUTOFFS.get(year)
        if cutoff:
            start = f"{year - 1}1101"
            end = str(cutoff)
            print(f"  Player stats (date range {start}-{end})...")
            fetch_player_stats_daterange(year, start, end, force_refresh=True)

        print("  Team stats...")
        fetch_team_stats(year, force_refresh=True)

        print("  Game stats...")
        fetch_game_stats(year, force_refresh=True)

    print("\nDone.")


if __name__ == "__main__":
    years = [int(y) for y in sys.argv[1:]] if len(sys.argv) > 1 else [2026]
    refresh(years)
