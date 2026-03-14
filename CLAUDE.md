# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Gravity is a college basketball prediction system for March Madness. It combines Barttorvik (T-Rank) efficiency ratings, team quality metrics, and player-derived features to predict game outcomes and simulate tournament brackets.

## Commands

```bash
# Setup
python -m venv venv && source venv/bin/activate && pip install -r requirements.txt

# Train model (saves to models/game_predictor.joblib)
python train.py --years 2024 2025 2026

# Predict a single game
python game_predictor.py "Duke" "North Carolina" --location H   # H=home, N=neutral, A=away

# Simulate bracket (Monte Carlo)
python bracket.py brackets/bracket_2026.json 10000

# Score brackets against historical actuals
python score_bracket.py 2024 2025

# Backtest model on tournament games
python backtest.py

# Compute gravity scores (descriptive analysis, not used in predictions)
python gravity.py
```

There is no formal test suite. Validation is done via backtesting on historical tournament data.

## Architecture

### Data Pipeline
All data comes from the Barttorvik API (`torvik.py`). Three data types are fetched and cached locally as CSV:
- **Player stats** (~5,000 players/season) → `data/{year}_player_stats.csv`
- **Team stats** (~365 teams/season) → `data/{year}_team_stats.csv`
- **Game stats** (per-player box scores, ~40MB uncompressed) → `data/{year}_game_stats.csv`

Team names must match Barttorvik conventions exactly (e.g., "Michigan St." not "Michigan State", "Connecticut" not "UConn").

### Prediction Model (`predict.py`: GamePredictor)
A 14-feature model using team-pair differences:

- **Torvik features (6)**: offensive/defensive efficiency gaps, barthag diff, expected tempo, SOS diff, location
- **Team quality (4)**: fun, elite SOS, quality games, wins above bubble (all diffs)
- **Player-derived (4)**: top-5 BPM sum, top porpag, top OBPM, top DBPM (all diffs)

Two models are trained together:
1. **Logistic regression** → win probability (with tournament temperature scaling 1.0–2.0)
2. **Linear regression** → point spread (spread sigma ~11 pts, win prob via normal CDF)

Saved as a single joblib bundle: `models/game_predictor.joblib`

### Gravity Scores (`gravity.py`)
Ridge regression measuring how much a team "imposes" its style on opponents across 7 dimensions (tempo, efficiency, eFG%, 3PT rate, FT rate, TO rate, ORB rate). This is **descriptive only** — gravity features were removed from the prediction model in PR #3 because they didn't improve accuracy.

### Bracket Simulation (`bracket.py`: BracketSimulator)
Monte Carlo engine that simulates the full 64-team tournament. Bracket definitions are JSON files in `brackets/` with 4 regions × 16 seeds and final four matchup pairings.

### Training (`train.py`)
Trains on regular-season games (pre-tournament cutoff ~mid-March), then calibrates tournament temperature on historical tournament games. Supports multi-year training for better generalization.

### Scoring (`score_bracket.py`)
Uses ESPN standard scoring: R32=10, S16=20, E8=40, F4=80, Championship=160, Champion=320 (max 1,920).
