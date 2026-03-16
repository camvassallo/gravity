# Model Improvements

## Latest Results: 7-Year Backtest + Half-Life Tuning

Expanded from 2 tournament years to 7 (2018–2025, skip 2020 COVID) — ~844 tournament games total. Swept recency weighting half-life values to find optimal config.

### Half-Life Sweep Results (average across 7 tournament years)

| Half-Life | Avg Log Loss | Avg Cal Log Loss | Avg Accuracy |
|-----------|-------------|-----------------|-------------|
| 0 (none)  | 0.5385      | 0.5331          | 73.6%       |
| **30**    | **0.5333**  | **0.5272**      | **73.9%**   |
| 45        | 0.5343      | 0.5284          | 73.5%       |
| 60        | 0.5351      | 0.5293          | 73.7%       |
| 90        | 0.5360      | 0.5304          | 73.5%       |
| 120       | 0.5366      | 0.5310          | 73.6%       |

**Selected: half-life=30.** Best on both primary metric (cal log loss) and tiebreaker (accuracy). Recency weighting helps vs no weighting; shorter half-life is better, suggesting late-season form is strongly predictive.

### Per-Year Breakdown (half-life=30, cumulative training)

| Test Year | Train Years | N Games | Log Loss | Cal LL | Accuracy | Temp | Blend |
|-----------|-------------|---------|----------|--------|----------|------|-------|
| 2018 | [2018] | 130 | 0.540 | 0.532 | 70.8% | 0.80 | 1.00 |
| 2019 | [2018,2019] | 139 | 0.537 | 0.537 | 75.5% | 0.95 | 0.80 |
| 2021 | [2018,2019,2021] | 89 | 0.556 | 0.555 | 73.0% | 1.10 | 0.75 |
| 2022 | [2018–2022] | 130 | 0.529 | 0.528 | 73.1% | 0.85 | 1.00 |
| 2023 | [2018–2023] | 113 | 0.597 | 0.593 | 73.5% | 1.25 | 1.00 |
| 2024 | [2018–2024] | 120 | 0.523 | 0.517 | 70.0% | 0.80 | 1.00 |
| 2025 | [2018–2025] | 123 | 0.450 | 0.428 | 81.3% | 0.80 | 1.00 |

### Final Model

Trained on 8 years (2018, 2019, 2021–2026) with half-life=30, tournament temp=0.85, blend=1.00.

---

## Previous Baseline (2-year backtest)

| Year | Log Loss | Accuracy | Cal Log Loss | Temp | Blend |
|------|----------|----------|--------------|------|-------|
| 2024 | 0.538 | 70.0% | 0.532 | 0.80 | 1.00 |
| 2025 | 0.452 | 82.9% | 0.430 | 0.80 | 1.00 |

---

## Summary

| # | Improvement | Impact | Effort | Status |
|---|-------------|--------|--------|--------|
| 1 | Recency Weighting (half-life=30) | High | Low | Implemented + tuned |
| 2 | Ensemble Logistic + Spread Probabilities | Medium | Low | Implemented |
| 3 | Consistent Daterange Player Stats | Low | Low | Implemented (cleanup) |
| 4 | Expanded Dataset (2018–2025, 7 years) | High | Low | Implemented |
| 5 | Matchup Style Features | Medium | High | Future work |
| 6 | Seed-Specific Calibration | Low | Medium | Future work |

---

## 1. Recency Weighting

**Rationale:** Late-season form is more predictive of tournament performance than November results. Teams improve, players get injured, and rotations solidify over the season. Weighting recent games more heavily should better capture a team's true tournament-time strength.

**Approach:** Exponential decay with configurable half-life (default 30 days). Games in March get weight ~0.84–1.0, while November games get ~0.21–0.30. Applied via sklearn's `sample_weight` parameter to both logistic and spread models.

**Implementation:** `compute_recency_weights()` in `predict.py`, wired through `train.py` and `backtest.py`.

**Tuning:** Swept half-life values {0, 30, 45, 60, 90, 120} across 7 tournament years. Half-life=30 wins on both calibrated log loss and accuracy. The improvement over no weighting is small but consistent (~0.006 cal log loss, +0.3% accuracy).

---

## 2. Ensemble Logistic + Spread Probabilities

**Rationale:** The logistic model and spread-derived probability capture different aspects of game prediction. The logistic model is directly optimized for classification, while the spread model captures margin information that translates to probability via the normal CDF. Blending them can reduce variance and improve calibration.

**Approach:** `ensemble_prob = w * logistic_prob + (1-w) * spread_prob`. The blend weight `w` is calibrated on tournament data via grid search minimizing log loss. If optimal weight is 0.0 or 1.0, the ensemble adds no value.

**Result:** Blend weight consistently calibrates to 1.0 (logistic-only) across most years. The ensemble infrastructure is in place but currently not providing lift — the logistic model is dominant.

**Implementation:** `ensemble_prob()` and `calibrate_blend_weight()` in `predict.py`. Bracket simulator uses ensemble probability for game simulation instead of spread sampling.

---

## 3. Consistent Daterange Player Stats (Cleanup)

**Rationale:** `train.py` called `fetch_all_for_year()` which fetches full-season player stats unnecessarily — the pipeline then re-fetches daterange-filtered player stats. This wasted bandwidth and was confusing. The fix replaces the broad fetch with targeted `fetch_team_stats()` + `fetch_game_stats()` calls.

**Implementation:** Changed import and call site in `train.py` line 20/45.

---

## 4. Expanded Dataset (2018–2025)

**Rationale:** With only 2 tournament years (~240 games), we couldn't confidently tune parameters or evaluate changes. Expanding to 7 tournament years (~844 games) provides enough data for proper parameter sweeps and more reliable evaluation.

**Approach:** Added tournament cutoff dates for 2018, 2019, 2021–2023. Backtest runs cumulative training (e.g., train on [2018] → test 2018, train on [2018,2019] → test 2019, etc.). Data auto-fetched from Barttorvik API.

**Implementation:** Updated `TOURNAMENT_CUTOFFS` in both `train.py` and `backtest.py`. Expanded main block in `backtest.py` to run 7 cumulative tests.

---

## 5. Matchup Style Features (Future Work)

**Rationale:** Some teams have stylistic advantages against certain opponents (e.g., a team that forces turnovers vs. a turnover-prone team). The gravity scores from `gravity.py` measure how much a team imposes its style, but they were removed from the model in PR #3 because raw gravity features didn't improve accuracy. A more targeted approach — computing pairwise style matchup advantages — could capture these dynamics.

**Possible approach:**
- For each game, compute the gap between Team A's offensive style and Team B's defensive vulnerability in specific dimensions (tempo, 3PT rate, TO rate, etc.)
- Use interaction terms rather than raw gravity scores
- Requires careful feature selection to avoid overfitting on small tournament samples

**Why deferred:** High effort relative to uncertain impact. Needs more research on which style dimensions actually matter in tournament play.

---

## 6. Seed-Specific Calibration (Future Work)

**Rationale:** Tournament upsets follow known seed-matchup patterns (e.g., 12-over-5 is historically ~35%). Current temperature scaling is global — it doesn't account for the fact that the model may be differently calibrated for top seeds vs. mid-majors.

**Possible approach:**
- Bin tournament games by seed differential
- Fit per-bin temperature or probability adjustments
- Requires enough historical data per bin to be reliable

**Why deferred:** Limited tournament sample size makes per-bin calibration noisy. The global temperature already helps. Could be revisited with more years of backtest data.
