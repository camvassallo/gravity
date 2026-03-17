# Model Improvements

## Latest Results: v4 Model (15 features, 7:8 player:team ratio + consensus blending)

Rebalanced feature ratio from 10:6 (player:team) to 7:8. Added `adjoe_diff` and `adjde_diff` (raw offensive/defensive efficiency), pruned 3 weak player features (`top5_porpag_weighted` +0.033, `top_ast_tov` +0.022, `top5_ts_sum` -0.036). Also added consensus blending in bracket simulation (30% weight from Torvik/Miya/KenPom average).

### v3 → v4 Comparison

| Metric | v3 (16 feat) | v4 (15 feat) | Delta |
|--------|-------------|-------------|-------|
| Avg Log Loss | 0.5318 | 0.5216 | -0.0102 |
| Avg Cal Log Loss | 0.5271 | 0.5168 | -0.0103 |
| Avg Accuracy | 74.3% | 75.4% | +1.1pp |
| 2025 Accuracy | 82.1% | 82.9% | +0.8pp |

Significant improvement across all metrics. The adjoe/adjde features are now the two strongest coefficients, allowing the model to weight offense vs defense independently rather than collapsing them into barthag.

### Feature Coefficients (v4 final model)

| Feature | Coefficient | Notes |
|---------|-------------|-------|
| diff_adjoe | +1.022 | **NEW**: offensive efficiency (strongest feature) |
| diff_adjde | -0.930 | **NEW**: defensive efficiency (negative = lower is better) |
| diff_fun | +0.472 | Fun rating |
| barthag_diff | +0.418 | Overall efficiency (now complementary to adjoe/adjde) |
| diff_wab | +0.185 | Wins above bubble |
| diff_top5_bpm_sum | -0.173 | Raw BPM sum |
| diff_qual_games | +0.126 | Quality game count |
| sos_diff | +0.125 | Strength of schedule |
| diff_elite_sos | +0.099 | Elite SOS |
| diff_top_porpag_trend | +0.084 | Late-season porpag improvement |
| diff_bench_bpm_sum | -0.069 | Bench depth |
| diff_top_gbpm | +0.023 | Game BPM |
| diff_top5_stops_sum | +0.018 | Defensive stops |
| diff_top5_bpm_weighted | -0.017 | Minutes-weighted BPM |
| diff_top5_bpm_trend | +0.013 | Late-season BPM improvement |

### Consensus Blending (bracket simulation)

Bracket simulation now blends model win probability with consensus-derived pairwise probability:
- `win_prob = 0.7 * model_prob + 0.3 * consensus_prob`
- Consensus pairwise probability derived from log-ratio of champion probabilities via logistic function
- Defaults to model-only if either team has 0 consensus champion probability

### Per-Year Backtest (v4, half-life=30)

| Test Year | N Games | Log Loss | Cal LL | Accuracy | Temp | Blend |
|-----------|---------|----------|--------|----------|------|-------|
| 2018 | 130 | 0.535 | 0.530 | 73.1% | 0.80 | 1.00 |
| 2019 | 139 | 0.514 | 0.513 | 76.3% | 0.90 | 1.00 |
| 2021 | 89 | 0.541 | 0.541 | 71.9% | 1.05 | 1.00 |
| 2022 | 130 | 0.515 | 0.512 | 74.6% | 0.85 | 1.00 |
| 2023 | 113 | 0.584 | 0.581 | 74.3% | 1.20 | 1.00 |
| 2024 | 120 | 0.521 | 0.519 | 75.0% | 0.85 | 1.00 |
| 2025 | 123 | 0.443 | 0.422 | 82.9% | 0.80 | 1.00 |
| **Avg** | **844** | **0.522** | **0.517** | **75.4%** | | |

### Simulation Calibration: sim_temp + EV formula

Two additional fixes applied to bracket simulation (not to per-game prediction):

**1. Simulation temperature (`sim_temp=1.3`):** The model's tournament temp (0.85) is calibrated for per-game log loss, but compounding over 6 rounds inflates top-team F4/champ probabilities (e.g., Duke 72% F4 was unrealistic). `sim_temp` applies a second temperature scaling to push probabilities back toward 50% during simulation only. At 1.3, Duke F4 drops to ~60%, which is more realistic for a historically great team.

**2. Pool EV formula:** The optimizer's `compute_pick_ev` now discounts high-ownership picks via `field_gain = 1 - alpha * ownership * 0.7`. Previously, when model and public agreed (edge≈1.0), the formula returned raw EV and always picked favorites. The ownership discount makes chalk picks less valuable in large pools because being correct on a pick that 90% of the field also made gains almost no ground over competitors.

### Bracket Simulation Results (v4 final: consensus + sim_temp=1.3)

| Team | Champ % | F4 % | vs Consensus |
|------|---------|------|--------------|
| Duke | 25.8 | 60.2 | +5.6pp |
| Michigan | 24.5 | 61.5 | +3.6pp |
| Arizona | 20.7 | 55.1 | +3.7pp |
| Florida | 5.6 | 31.1 | -3.8pp |
| Purdue | 4.8 | 23.8 | +0.0pp |
| Houston | 4.3 | 27.4 | -2.2pp |
| Illinois | 2.3 | 19.0 | -2.0pp |
| Iowa St. | 2.2 | 15.5 | -2.4pp |
| Michigan St. | 1.6 | 11.8 | +0.1pp |
| Connecticut | 1.5 | 12.4 | -0.5pp |

Distribution is less concentrated and closer to consensus than earlier v4 iterations. Florida/Houston/Illinois still below consensus but gap reduced. Feature rebalancing corrected Michigan St. (3.6→1.6%) and Nebraska (1.6→0.5%) overvaluation.

---

## Previous Results: v3 Model (16 features, pruned weak features)

Pruned 3 more weak features from v2: `avg_experience` (-0.023 coef), `avg_height` (-0.011 coef), `qual_barthag` (-0.046 coef). These were absorbed by existing features. Net: 19 → 16 features. Backtest shows strict improvement across all metrics.

### v2 → v3 Comparison

| Metric | v2 (19 feat) | v3 (16 feat) | Delta |
|--------|-------------|-------------|-------|
| Avg Log Loss | 0.5329 | 0.5318 | -0.0011 |
| Avg Cal Log Loss | 0.5272 | 0.5271 | -0.0001 |
| Avg Accuracy | 74.2% | 74.3% | +0.1pp |
| 2025 Accuracy | 81.3% | 82.1% | +0.8pp |

### Feature Coefficients (v3 final model)

| Feature | Coefficient | Notes |
|---------|-------------|-------|
| barthag_diff | +0.956 | Dominant feature |
| diff_fun | +0.389 | Fun rating |
| diff_top5_bpm_weighted | +0.307 | Minutes-weighted BPM |
| diff_qual_games | +0.172 | Quality game count |
| diff_top5_bpm_sum | +0.152 | Raw BPM sum |
| diff_bench_bpm_sum | +0.140 | Bench depth |
| sos_diff | +0.132 | Strength of schedule |
| diff_elite_sos | +0.104 | Elite SOS |
| diff_top5_bpm_trend | +0.094 | Late-season BPM improvement |
| diff_top5_stops_sum | +0.091 | Defensive stops |
| diff_top_porpag_trend | +0.081 | Late-season porpag improvement |
| diff_top_gbpm | +0.048 | Game BPM |
| diff_top5_ts_sum | -0.036 | True shooting |
| diff_top5_porpag_weighted | +0.033 | Usage-weighted porpag |
| diff_wab | -0.031 | Wins above bubble |
| diff_top_ast_tov | +0.022 | Assist/turnover ratio |

---

## Consensus Comparison: Gravity vs Torvik/Miya/KenPom

### Summary

Compared our v3 model against three established projection systems for the 2026 tournament. Our model is most similar to **Miya** (r=0.969, avg champion diff 0.44pp) and furthest from Torvik (r=0.931, 0.70pp). This makes sense — Miya uses player-level data similar to our approach.

### Correlation with each source (Champion %)

| Source | Correlation | Avg |Diff| |
|--------|-------------|------------|
| Miya | 0.969 | 0.44pp |
| KenPom | 0.950 | 0.58pp |
| Torvik | 0.932 | 0.70pp |
| Consensus (avg) | 0.959 | — |

### Structural Bias: Player-Heavy Model

Our model has **10 player-derived features vs 6 team-level features**. This creates a systematic bias:

**We overvalue star-driven teams** (good individual BPM, visible player talent):
- Michigan St. F4: +6.5pp vs consensus (Izzo's star players inflate BPM)
- Nebraska F4: +8.4pp (individual stats outshine team)
- Arkansas F4: +6.0pp, Vanderbilt F4: +7.0pp

**We undervalue system/efficiency teams** (great team metrics, distributed talent):
- Florida F4: -9.8pp, E8: -15.7pp (strong barthag but no BPM-dominant stars)
- Iowa St. F4: -9.9pp (elite defense, system team)
- Illinois F4: -6.6pp (similar pattern)

All three consensus sources agree on these gaps — this isn't one model being wrong, it's us vs the field.

### By-Seed Bias (Gravity - Consensus, avg pp)

| Seed | R32 | S16 | E8 | F4 | Champ |
|------|-----|-----|----|----|-------|
| 1 | +0.5 | +0.4 | -6.0 | -2.1 | +0.6 |
| 2 | +1.8 | -3.7 | -4.8 | -4.3 | -1.7 |
| 3 | +3.4 | +1.4 | +3.1 | -0.2 | -0.2 |
| 4 | +7.5 | +6.1 | +6.5 | +5.3 | +1.1 |

We systematically undervalue 2-seeds (by -1.7pp champ) and overvalue 4-seeds (+1.1pp champ). The E8 gap for 1-seeds (-6.0pp) is driven almost entirely by Florida.

### Concentration

| Metric | Gravity | Consensus |
|--------|---------|-----------|
| Top 3 champion share | 66.2% | 58.0% |
| Top 5 champion share | 74.5% | 73.9% |

We're 8pp more concentrated in the top 3. This means we're more confident the best teams win — potentially overconfident given tournament variance.

### What This Means

**Edges we should trust:**
- **Michigan champion (27.5% vs 20.9%)**: Our biggest edge, and Miya independently agrees (26.5%). Michigan has strong team AND player metrics — our player features amplify a real advantage.
- **Michigan St. F4 (17.8% vs 11.2%)**: Player-driven edge, plausible for a Izzo team.
- **Arizona (19.4% vs 17.0%)**: Small edge, directionally consistent with Miya (18.0%).

**Edges we should NOT trust:**
- **Florida underweight (3.7% vs 9.4% champ)**: All three sources have Florida 7-11%. We're almost certainly too low — Florida's team efficiency is being under-captured by our player features.
- **Illinois underweight (1.4% vs 4.3%)**: Same structural issue.
- **Iowa St. underweight (1.7% vs 4.6%)**: Same structural issue.
- **Nebraska/Arkansas/Vanderbilt deep runs**: Our model projects these mid-seeds further than any consensus source. Likely player-feature bias inflating their chances.

### Actionable Takeaways

1. **Bracket optimizer**: Use consensus projections (already done) — don't use our model as the public proxy, because our model IS the outlier on some teams.
2. **Kalshi**: Don't sell Florida/Illinois/Houston champion contracts at prices below consensus — our model undervalues them. Don't buy Nebraska/Arkansas F4 at elevated prices — our model overvalues them.
3. **Model improvement**: The 10:6 player-to-team feature ratio needs rebalancing. Either add more team-level features (adjoe/adjde diff, tempo, 3PT profile) or reduce player features to top 5-6 most impactful ones.
4. **Consider consensus blending**: For bracket simulation, blend our model probabilities with consensus (e.g., 60% model / 40% consensus) to temper our structural biases while keeping genuine edges.

---

## Previous Results: v2 Model (19 features, pruned + new features)

Pruned 7 dead features, added 5 new ones: `qual_barthag` (quality-adjusted efficiency), `avg_experience` (minutes-weighted class year), `avg_height` (minutes-weighted height), `top5_bpm_trend` (last-30-day BPM vs season), `top_porpag_trend` (last-30-day porpag vs season). Net: 21 → 19 features.

### Per-Year Breakdown (v2, half-life=30, cumulative training)

| Test Year | Train Years | N Games | Log Loss | Cal LL | Accuracy | Temp | Blend |
|-----------|-------------|---------|----------|--------|----------|------|-------|
| 2018 | [2018] | 130 | 0.543 | 0.535 | 72.3% | 0.80 | 0.80 |
| 2019 | [2018,2019] | 139 | 0.530 | 0.530 | 74.8% | 0.90 | 0.80 |
| 2021 | [2018,2019,2021] | 89 | 0.551 | 0.550 | 76.4% | 1.05 | 0.80 |
| 2022 | [2018–2022] | 130 | 0.526 | 0.525 | 73.1% | 0.85 | 1.00 |
| 2023 | [2018–2023] | 113 | 0.599 | 0.595 | 72.6% | 1.25 | 1.00 |
| 2024 | [2018–2024] | 120 | 0.528 | 0.525 | 69.2% | 0.85 | 1.00 |
| 2025 | [2018–2025] | 123 | 0.453 | 0.431 | 81.3% | 0.80 | 1.00 |
| **Avg** | | **844** | **0.533** | **0.527** | **74.2%** | | |

### Comparison: v1 (21 features) vs v2 (19 features)

| Metric | v1 | v2 | Delta |
|--------|-----|-----|-------|
| Avg Log Loss | 0.5333 | 0.5329 | -0.0004 |
| Avg Cal Log Loss | 0.5272 | 0.5272 | +0.0000 |
| Avg Accuracy | 73.9% | 74.2% | +0.3pp |

Cal log loss is unchanged; accuracy improved slightly. The new features (trend, experience) offset the pruned features while reducing parameter count. Trend features have meaningful positive coefficients (BPM trend +0.094, porpag trend +0.081), confirming late-season form matters.

### Feature Coefficients (v2 final model)

| Feature | Coefficient | Notes |
|---------|-------------|-------|
| barthag_diff | +0.956 | Dominant feature |
| diff_fun | +0.389 | Fun rating |
| diff_top5_bpm_weighted | +0.307 | Minutes-weighted BPM |
| diff_qual_games | +0.172 | Quality game count |
| diff_top5_bpm_sum | +0.152 | Raw BPM sum |
| diff_bench_bpm_sum | +0.140 | Bench depth |
| sos_diff | +0.132 | Strength of schedule |
| diff_elite_sos | +0.104 | Elite SOS |
| **diff_top5_bpm_trend** | **+0.094** | **NEW: late-season BPM improvement** |
| diff_top5_stops_sum | +0.091 | Defensive stops |
| **diff_top_porpag_trend** | **+0.081** | **NEW: late-season porpag improvement** |
| diff_top_gbpm | +0.048 | Game BPM |
| diff_qual_barthag | -0.046 | **NEW: quality-adj efficiency (negative — absorbed by barthag)** |
| diff_top5_ts_sum | -0.036 | True shooting |
| diff_top5_porpag_weighted | +0.033 | Usage-weighted porpag |
| diff_wab | -0.031 | Wins above bubble |
| diff_avg_experience | -0.023 | **NEW: experience (weak, future prune candidate)** |
| diff_top_ast_tov | +0.022 | Assist/turnover ratio |
| diff_avg_height | -0.011 | **NEW: height (weak, future prune candidate)** |

### Final Model

Trained on 8 years (2018, 2019, 2021–2026) with half-life=30, 19 features. Tournament temp=0.85, blend=1.00.

---

## Previous Results: v1 Model (21 features, half-life=30)

### Half-Life Sweep Results (average across 7 tournament years)

| Half-Life | Avg Log Loss | Avg Cal Log Loss | Avg Accuracy |
|-----------|-------------|-----------------|-------------|
| 0 (none)  | 0.5385      | 0.5331          | 73.6%       |
| **30**    | **0.5333**  | **0.5272**      | **73.9%**   |
| 45        | 0.5343      | 0.5284          | 73.5%       |
| 60        | 0.5351      | 0.5293          | 73.7%       |
| 90        | 0.5360      | 0.5304          | 73.5%       |
| 120       | 0.5366      | 0.5310          | 73.6%       |

### Per-Year Breakdown (v1, half-life=30)

| Test Year | Train Years | N Games | Log Loss | Cal LL | Accuracy | Temp | Blend |
|-----------|-------------|---------|----------|--------|----------|------|-------|
| 2018 | [2018] | 130 | 0.540 | 0.532 | 70.8% | 0.80 | 1.00 |
| 2019 | [2018,2019] | 139 | 0.537 | 0.537 | 75.5% | 0.95 | 0.80 |
| 2021 | [2018,2019,2021] | 89 | 0.556 | 0.555 | 73.0% | 1.10 | 0.75 |
| 2022 | [2018–2022] | 130 | 0.529 | 0.528 | 73.1% | 0.85 | 1.00 |
| 2023 | [2018–2023] | 113 | 0.597 | 0.593 | 73.5% | 1.25 | 1.00 |
| 2024 | [2018–2024] | 120 | 0.523 | 0.517 | 70.0% | 0.80 | 1.00 |
| 2025 | [2018–2025] | 123 | 0.450 | 0.428 | 81.3% | 0.80 | 1.00 |

---

---

## Why This Model Configuration Is Best

### Model evolution

The prediction system has gone through four major iterations:

1. **PR #1 — Gravity features** (initial): Used gravity scores (how teams impose style) as predictive features alongside basic Torvik stats. Logistic regression + spread model.
2. **PR #2 — Temperature calibration**: Added tournament temperature scaling to push probabilities toward 50/50, reflecting tournament variance. Improved log loss.
3. **PR #3 — Torvik + player features**: Removed gravity features (didn't improve accuracy), replaced with 14-feature model using Torvik efficiency + team quality + player-derived stats (BPM, porpag, DBPM). This was the major architecture improvement.
4. **Current — Recency weighting + expanded dataset**: Added exponential recency weighting (half-life=30), expanded features to 21 (bench BPM, weighted stats, usage spread), expanded training/eval to 8 years.

### Why hl=30 over alternatives

We swept 6 half-life values across 7 tournament years (~844 games). The result is unambiguous on the proper scoring metric:

**hl=30 wins 7/7 years on calibrated log loss.**

| Year | N | hl=0 Cal LL | hl=30 Cal LL | Delta | hl=0 Acc | hl=30 Acc | Delta |
|------|---|------------|-------------|-------|---------|----------|-------|
| 2018 | 130 | 0.5385 | 0.5324 | -0.006 | 70.0% | 70.8% | +0.8% |
| 2019 | 139 | 0.5498 | 0.5366 | -0.013 | 71.2% | 75.5% | +4.3% |
| 2021 | 89 | 0.5611 | 0.5553 | -0.006 | 73.0% | 73.0% | +0.0% |
| 2022 | 130 | 0.5286 | 0.5278 | -0.001 | 73.8% | 73.1% | -0.7% |
| 2023 | 113 | 0.5990 | 0.5934 | -0.006 | 73.5% | 73.5% | +0.0% |
| 2024 | 120 | 0.5178 | 0.5170 | -0.001 | 73.3% | 70.0% | -3.3% |
| 2025 | 123 | 0.4370 | 0.4278 | -0.009 | 80.5% | 81.3% | +0.8% |
| **Avg** | | **0.5331** | **0.5272** | **-0.006** | **73.6%** | **73.9%** | **+0.3%** |

Accuracy is mixed (3/7 wins) because accuracy only measures whether you're on the right side of 50% — it doesn't reward better-calibrated probabilities. Log loss is the correct metric because our bracket simulator uses the full probability distribution, not just pick-the-favorite. A model that says 62% for a true 60% game outperforms one that says 55% for the same game, even though both "get it right."

### Why log loss > accuracy for this use case

1. **Bracket simulation uses probabilities**: The Monte Carlo simulator draws from win probabilities. Better-calibrated probabilities → more realistic simulations → better bracket recommendations.
2. **Spread predictions matter**: The spread model's sigma (10.9 pts) feeds into the normal CDF for spread-derived win probability. Better log loss means the probability surface is more truthful.
3. **Tournament games are high-variance**: With only ~120 games per tournament, accuracy fluctuates heavily (70-81% across years). Log loss is smoother and more reliable as an evaluation metric.
4. **Proper scoring rule**: Log loss is strictly proper — it's uniquely minimized when predicted probabilities match true outcome frequencies. Accuracy is not proper.

### Why the ensemble didn't help

The blend weight consistently calibrates to 1.0 (logistic-only) across 5 of 7 years. The two years where blending helped (2019: w=0.80, 2021: w=0.75) showed only marginal improvement (~0.002 log loss). This makes sense: the logistic and spread models use identical features, so the spread-derived probability is just a noisier version of the logistic probability. If they used different feature sets, blending might help.

### What we tried that didn't work

| Idea | Result | Why |
|------|--------|-----|
| Gravity features (PR #1→#3) | Removed — no lift | Gravity measures style imposition, not matchup advantage |
| Ensemble logistic+spread | Blend=1.0 | Same features → redundant signals |
| Long half-life (90-120 days) | Worse than hl=30 | November games add noise, not signal |
| No recency weighting | Worst config | Equal weighting dilutes late-season signal |

### Confidence in the current config

- **844 tournament games** across 7 years — enough to distinguish real effects from noise
- **Monotonic improvement** as half-life decreases from 120→30 (then diminishing returns)
- **7/7 years improved** on the proper scoring metric — not a fluke of one outlier year
- **Cumulative training** mirrors real usage (train on all prior years, predict next year)
- **2023 is the hardest year** for every config (log loss ~0.59) — likely a high-upset tournament, not a model failure

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
| 5 | Feature Pruning (21→14 core) | Low | Low | **Implemented** (v2) |
| 6 | Quality-Adjusted Efficiency (qual_barthag) | Low | Low | **Implemented** (v2) → **Pruned** (v3) |
| 7 | Late-Season Form Features (BPM/porpag trend) | Medium | Medium | **Implemented** (v2, +0.094/+0.081) |
| 8 | Experience & Height Features | Low | Low | **Implemented** (v2) → **Pruned** (v3) |
| 9 | Feature Pruning v3 (19→16) | Low | Low | **Implemented** (v3, all metrics improved) |
| 10 | Bracket Pool Optimizer | Medium | Medium | **Implemented** (leverage-based) |
| 11 | Consensus Comparison (Torvik/Miya/KenPom) | High | Low | **Implemented** (revealed player-feature bias) |
| 12 | Rebalance Feature Ratio (10:6 player:team) | High | Medium | **Next** — add adjoe/adjde diff, reduce player features |
| 13 | Consensus Blending (model + external) | Medium | Low | Next — blend our probs with consensus |
| 14 | Matchup Style Features | Medium | High | Future work |
| 15 | Seed-Specific Calibration | Low | Medium | Future work |

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

---

## What To Try Next

Based on v3 model (16 features) + consensus comparison revealing a 10:6 player-to-team feature imbalance.

### What we implemented

| Idea | Result | Notes |
|------|--------|-------|
| Feature pruning (21→16 features) | Positive | Improved all backtest metrics |
| Late-season form trends | **Positive** (+0.094, +0.081) | Late-season momentum matters |
| Experience/height/qual_barthag | Weak/negative | All pruned in v3 |
| Consensus comparison | **Revealed structural bias** | 10 player vs 6 team features → overvalue star teams, undervalue system teams |
| Bracket pool optimizer | **Working** | Leverage-based, pool-size-aware, uses consensus as public proxy |

### Priority 1: Rebalance Feature Ratio

**Problem (identified by consensus comparison):** Our model has 10 player-derived features and only 6 team-level features. This causes systematic overvaluation of star-driven teams (Michigan St., Nebraska, Arkansas) and undervaluation of system/efficiency teams (Florida, Illinois, Iowa St.).

**Approach:** Add team-level Torvik features that are currently unused:
- `adjoe_diff` + `adjde_diff` — raw offensive/defensive efficiency (currently only captured indirectly via barthag)
- `adj_tempo_diff` — pace difference (tempo mismatches affect outcomes)
- Alternatively: reduce player features to top 6 most impactful

**Projected impact:** Medium-High — consensus comparison suggests this is our biggest model weakness.

### Priority 2: Consensus Blending

**Problem:** Even after rebalancing features, we likely can't match 3 established systems' collective wisdom. Blending our model's probabilities with consensus averages would reduce structural bias while preserving genuine edges.

**Approach:** For bracket simulation, use `blended_prob = w * model_prob + (1-w) * consensus_prob` where w is calibrated on historical accuracy. Start with w=0.6 (trust model more on individual games, defer to consensus on cumulative tournament paths).

**Effort:** Low — already have consensus data loaded.

### Other ideas (lower priority)

### Idea 4: Shooting Profile Features

**Problem:** The model has `top5_ts_sum` (true shooting) but no breakdown of *how* teams score. A team that lives at the rim vs one that shoots 40% from three play very differently, and these matter in tournament matchups.

**Data available:** Player-level `rim_pct`, `mid_pct`, `tp_per`, `e_fg`, `ftr`, `orb_per`. All unused.

**Approach:** Add 2-3 features:
- `top5_3pt_rate` — three-point attempt share of top-5 (reliance on threes is high-variance)
- `top5_rim_pct` — rim finishing % (correlates with interior dominance)
- `top5_ft_rate` — free throw rate (ability to draw fouls, get to the line in close games)

**Projected impact:** Low-Medium — shooting profiles add texture but may be partially captured by existing efficiency features. Estimated -0.002 to -0.008 cal log loss.

**Effort:** Low — columns exist, just aggregate in `build_player_features()`.

### Idea 5: Gradient Boosted Trees

**Problem:** Logistic regression assumes linear feature relationships. In reality, a 10-point barthag_diff in a 1v16 matchup is less informative than a 0.02 barthag_diff in a 4v5 matchup. Non-linear models can learn these interactions.

**Approach:** Replace logistic regression with LightGBM or XGBoost. Keep the same feature set. Use the backtest framework to compare directly.

**Projected impact:** Medium-High potential, but **high risk of overfitting** on 844 tournament games. Tree models are hungry for data. Would need aggressive regularization (max_depth=3, min_child_samples=50+).

**Effort:** Medium — swap classifier, tune hyperparameters. ~50 lines of code plus sweep.

**Key risk:** With only ~42K training games and 844 test games, a boosted tree may overfit to regular-season patterns that don't transfer to tournaments. Logistic regression's simplicity is arguably a feature, not a bug.

### Idea 6: Pairwise Style Matchup Features

**Problem:** Some teams have stylistic advantages against specific opponents. The gravity analysis (PR #3) showed teams impose style differently, but raw gravity features didn't help. The issue was that gravity is a *team-level* stat, not a *matchup-level* one.

**Approach:** For each game, compute pairwise style gaps:
- `tempo_mismatch` = |team1_adj_tempo - team2_adj_tempo| (high mismatch → chaos → upsets)
- `turnover_vulnerability` = team1_gravity_to_rate × team2_to_rate_avg (teams that force TOs vs TO-prone teams)
- Could use gravity coefficients as interaction terms rather than standalone features

**Projected impact:** Low-Medium — style matchups are real but hard to quantify. Previous attempt (PR #3) failed. Estimated -0.001 to -0.010 cal log loss if done right.

**Effort:** High — requires rethinking the gravity → prediction pipeline.

### Idea 7: Round-Aware Temperature Calibration

**Problem:** Current temperature (0.85) is global. But the model may be differently calibrated for R64 (lots of blowouts) vs E8 (coin flips). R64 probably needs less temperature adjustment than E8.

**Approach:** Fit per-round temperatures using the 844-game backtest dataset. Group tournament games by round, find optimal temp for each.

**Projected impact:** Low — with only ~50-60 games per round in the dataset, per-round calibration will be noisy. Maybe -0.002 to -0.005 cal log loss.

**Effort:** Low — extend `calibrate_tournament_temp()` to accept round labels.

### Idea 8: Seed Differential as a Feature

**Problem:** The model doesn't know about seeds at all. It only sees team quality metrics. But seed assignments carry information (committee consensus) that isn't fully captured by Torvik ratings.

**Approach:** Add `seed_diff` or `avg_seed` as a feature during training. For regular-season games without seeds, use a pseudo-seed derived from Torvik rank.

**Projected impact:** Low — seed information is largely captured by barthag/SOS already. But it's free information. Estimated -0.001 to -0.003 cal log loss.

**Effort:** Low — need to map teams to seeds in the bracket JSON, add one feature.

### Prioritized Roadmap

| Priority | Idea | Projected cal LL improvement | Effort | Risk | Status |
|----------|------|------------------------------|--------|------|--------|
| ~~1~~ | ~~Feature pruning~~ | ~~-0.001 to -0.005~~ | ~~Low~~ | ~~Very low~~ | **Done** (v2) |
| ~~2~~ | ~~Quality-adjusted efficiency~~ | ~~-0.005 to -0.015~~ | ~~Low~~ | ~~Low~~ | **Done** (v2, weak) |
| ~~3~~ | ~~Late-season form features~~ | ~~-0.005 to -0.020~~ | ~~Medium~~ | ~~Low~~ | **Done** (v2, positive) |
| ~~4~~ | ~~Experience features~~ | ~~-0.002 to -0.008~~ | ~~Low~~ | ~~Low~~ | **Done** (v2, weak) |
| 5 | ~~Prune experience + height + qual_barthag~~ | ~~+0.001 (cleanup)~~ | ~~Low~~ | ~~Very low~~ | **Done** (v3) |
| 6 | ~~Bracket pool optimizer~~ | ~~N/A (strategy)~~ | ~~Medium~~ | ~~Low~~ | **Done** |
| 7 | ~~Consensus comparison~~ | ~~N/A (analysis)~~ | ~~Low~~ | ~~None~~ | **Done** (revealed bias) |
| ~~8~~ | ~~Rebalance features (add adjoe/adjde diff, prune 3 weak)~~ | ~~-0.005 to -0.015~~ | ~~Medium~~ | ~~Low~~ | **Done** (v4, -0.0103 cal LL) |
| ~~9~~ | ~~Consensus blending~~ | ~~N/A (strategy)~~ | ~~Low~~ | ~~Low~~ | **Done** (v4, 30% weight) |
| 10 | Shooting profiles | -0.002 to -0.008 | Low | Low | |
| 11 | Gradient boosted trees | -0.010 to -0.030 | Medium | High | |
| 12 | Style matchup features | -0.001 to -0.010 | High | Medium | |
| 13 | Round-aware temp | -0.002 to -0.005 | Low | Low | |

Items 1-9 done. v4 model (15 features, 7:8 player:team ratio) with consensus blending is the current production model.

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
