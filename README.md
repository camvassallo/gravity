# Gravity

A college basketball prediction system for March Madness. Combines Barttorvik efficiency ratings, team quality metrics, and player-derived features to predict game outcomes and simulate tournament brackets.

## How It Works

**Gravity scores** measure how much a team "imposes" its tendencies on opponents using ridge regression across seven statistical dimensions (efficiency, eFG%, 3PT rate, FT rate, TO rate, ORB rate, tempo). A gravity coefficient near 1.0 means the team fully dictates the stat; near 0.5 means it splits the difference with opponents.

The **prediction model** is a 14-feature logistic regression trained on Torvik data:
- 6 core Torvik features: efficiency gaps, barthag diff, tempo, SOS diff, location
- 4 team quality features: fun rating, elite SOS, quality games, WAB diffs
- 4 player-derived features: top-5 BPM sum, top porpag, top OBPM, top DBPM diffs

Gravity scores turned out to be descriptive (how a team plays) rather than predictive (whether they win), so they are not used in the prediction model. They remain useful for matchup analysis.

## Historical Performance

Bracket scoring uses ESPN standard points (10/20/40/80/160/320 per round).

| Year | Score | R32 | S16 | E8 | F4 | Champion |
|------|-------|-----|-----|----|----|----------|
| 2024 | 1,450 / 1,920 (75.5%) | 23/32 | 13/16 | 4/8 | 2/4 | Connecticut (correct) |
| 2025 | 1,160 / 1,920 (60.4%) | 26/32 | 13/16 | 8/8 | 4/4 | Auburn (wrong, Florida won) |

Backtest metrics on held-out tournament games:

| Test | Games | Calibrated Log Loss | AUC | Accuracy |
|------|-------|---------------------|-----|----------|
| 2024 tournament | 120 | 0.520 | 0.812 | 70.8% |
| 2025 tournament | 123 | 0.446 | 0.893 | 78.0% |

## Quick Start

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Train the model

```bash
python train.py --years 2024 2025 2026
```

### Predict a single game

```bash
python game_predictor.py "Duke" "North Carolina" --location H
python game_predictor.py "Houston" "Auburn" --location N
```

### Simulate a bracket

Edit `brackets/bracket_2026.json` with the actual bracket, then:

```bash
python bracket.py brackets/bracket_2026.json 10000
```

### Score against historical results

```bash
python score_bracket.py 2024 2025
```

### Run backtesting

```bash
python backtest.py
```

### Compute gravity scores

```bash
python gravity.py
```

## Project Structure

```
gravity.py            # Gravity score computation (ridge regression)
predict.py            # GamePredictor class (14-feature model)
train.py              # Model training pipeline
bracket.py            # Monte Carlo bracket simulator
score_bracket.py      # Score brackets against actual results
game_predictor.py     # Single-game prediction CLI
backtest.py           # Historical tournament backtesting
torvik.py             # Barttorvik data fetcher + cache
feature_analysis.py   # Feature importance analysis
sanity_check.py       # Gravity sanity checks + visualizations
visualize_top50.py    # Top 50 team gravity profiles

brackets/             # Tournament bracket JSON files (2024-2026)
models/               # Trained model artifacts (joblib)
data/                 # Cached Torvik data + gravity CSVs
plots/                # Generated visualizations
docs/                 # API documentation
```

## Data Sources

All data is sourced from [Barttorvik](https://barttorvik.com) (T-Rank college basketball ratings). Data is cached locally in `data/` after first fetch.

Team names must match Barttorvik conventions (e.g., "Michigan St." not "Michigan State", "Connecticut" not "UConn", "St. John's" not "Saint John's").
