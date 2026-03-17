# Kalshi Trading Playbook — 2026 March Madness

Updated: 2026-03-16 (v3 model: 16 features, half-life=30, 8-year training)

---

## Model Probabilities (v3 — pruned to 16 features)

| Team | Champ % | F4 % |
|------|---------|------|
| Michigan | 27.5 | 61.3 |
| Duke | 19.4 | 47.5 |
| Arizona | 19.4 | 48.9 |
| Purdue | 4.6 | 21.6 |
| Florida | 3.7 | 24.7 |
| Michigan St. | 3.6 | 17.8 |
| Houston | 3.5 | 24.9 |
| Arkansas | 2.7 | 12.7 |
| Iowa St. | 1.7 | 11.6 |
| Vanderbilt | 1.7 | 14.3 |
| St. John's | 1.6 | 9.0 |
| Nebraska | 1.6 | 13.7 |
| Virginia | 1.4 | 9.8 |
| Connecticut | 1.4 | 11.2 |
| Illinois | 1.4 | 14.2 |
| Alabama | 1.3 | 9.1 |

Changes from v2: Pruned 3 weak features (experience, height, qual_barthag) → 16 features. Michigan champ 26.0→27.5%, Arizona 19.1→19.4%, Purdue 5.0→4.6%, Michigan St. 3.3→3.6%.

---

## Section A: Current Holdings

All positions are **Champion YES** contracts.

| Team | Shares | Cost Basis | Model Champ % | Action |
|------|--------|------------|---------------|--------|
| Louisville | 935 | $19.99 | 0.3% | HOLD (illiquid, can't sell) |
| Houston | 208 | $19.92 | 3.5% | Check market — if >5%, SELL |
| Purdue | 468 | $19.98 | 4.6% | **HOLD** — still above cost basis edge |
| Illinois | 268 | $19.99 | 1.4% | **SELL** — model says 1.4%, no edge |
| Florida | 234 | $19.93 | 3.7% | **SELL if market >5%** |

**Key changes from v2:**
- Michigan champ up to 27.5% — strongest conviction buy
- Purdue dropped slightly 5.0→4.6% — still a hold but tighter
- Illinois dropped further to 1.4% — sell immediately
- Florida dropped 4.1→3.7% — lower sell trigger

---

## Section B: New Orders

Check live market prices before executing. Only buy where model edge > 3pp.

### High-Conviction Buys

| Market | Side | Model | Edge if market at... | Notes |
|--------|------|-------|---------------------|-------|
| Michigan champ YES | BUY | 27.5% | +7pp if 20% | Top model pick, strongest edge |
| Michigan F4 YES | BUY | 61.3% | Depends on market | Model has >61% — very strong |
| Duke champ YES | BUY | 19.4% | +4pp if 15% | If underpriced vs public |
| Arizona champ YES | BUY | 19.4% | +4pp if 15% | Tied 2nd with Duke |

### Situational Buys (if market is cheap)

| Market | Side | Model | Notes |
|--------|------|-------|-------|
| Purdue F4 YES | BUY | 21.6% | 2-seed, strong model support |
| Michigan St. F4 YES | BUY | 17.8% | 3-seed, up from 16.9%, public undervalues |
| Vanderbilt F4 YES | BUY | 14.3% | 5-seed dark horse, likely very cheap |
| Arkansas F4 YES | BUY | 12.7% | 4-seed, if market <8% |
| Iowa St. F4 YES | BUY | 11.6% | If market <8%, good value |

---

## Section C: Sells / Positions to Exit

| Market | Action | Reason |
|--------|--------|--------|
| Illinois champ YES | SELL NOW | Model says 1.4% — no edge at any realistic price |
| Florida champ YES | SELL if >5% | Model says 3.7%, tighter trigger than before |
| Houston champ YES | SELL if >5% | Model dropped to 3.5% |

---

## Section D: Rebalancing Rules

1. **Check after each round**, not each day — avoid overtrading on noise
2. If a team advances and F4 price spikes, consider selling F4 to lock profit and let champ bet ride
3. If a team is eliminated, position goes to zero — no action needed
4. Re-run model with updated Torvik data after R32 to check if remaining edges still hold
5. If model edge on a position flips negative (market corrects past model), sell
6. Illinois sell should happen ASAP — model confidence dropped to 1.4%
7. Michigan is the highest-conviction position across all markets
