# Kalshi Trading Playbook — 2026 March Madness

Updated: 2026-03-16 (v2 model: 19 features, half-life=30, 8-year training)

---

## Model Probabilities (updated)

| Team | Champ % | F4 % |
|------|---------|------|
| Michigan | 26.0 | 59.1 |
| Duke | 19.7 | 47.6 |
| Arizona | 19.1 | 47.6 |
| Purdue | 5.0 | 22.4 |
| Florida | 4.1 | 25.2 |
| Houston | 3.7 | 25.2 |
| Michigan St. | 3.3 | 16.9 |
| Arkansas | 3.0 | 13.3 |
| Iowa St. | 2.0 | 12.5 |
| Vanderbilt | 1.8 | 14.0 |
| Illinois | 1.6 | 15.6 |
| St. John's | 1.5 | 8.5 |
| Connecticut | 1.5 | 11.3 |
| Alabama | 1.4 | 9.8 |
| Nebraska | 1.3 | 12.1 |
| Virginia | 1.3 | 9.4 |

Changes from prior model: Michigan champ up 23.3→26.0%, Purdue up 4.1→5.0%, Houston down 4.4→3.7%, Illinois down 1.7→1.6%. New features (experience, form trends) benefit Michigan and Arizona most.

---

## Section A: Current Holdings

All positions are **Champion YES** contracts.

| Team | Shares | Cost Basis | Model Champ % | Action |
|------|--------|------------|---------------|--------|
| Louisville | 935 | $19.99 | 0.4% | HOLD (illiquid, can't sell) |
| Houston | 208 | $19.92 | 3.7% | Check market — if >5%, SELL |
| Purdue | 468 | $19.98 | 5.0% | **HOLD** — model confirms edge, up from 4.1% |
| Illinois | 268 | $19.99 | 1.6% | **SELL** — model says 1.6%, no edge |
| Florida | 234 | $19.93 | 4.1% | **SELL if market >6%** |

**Key changes from prior model:**
- Purdue champ probability UP from 4.1% to 5.0% — stronger hold
- Illinois still at 1.6% — sell at any price above model
- Houston dropped from 4.4% to 3.7% — tighter sell trigger

---

## Section B: New Orders

Check live market prices before executing. Only buy where model edge > 3pp.

### High-Conviction Buys

| Market | Side | Model | Edge if market at... | Notes |
|--------|------|-------|---------------------|-------|
| Michigan champ YES | BUY | 26.0% | +6pp if 20% | Top model pick, strongest edge |
| Michigan F4 YES | BUY | 59.1% | Depends on market | Model has >59% — very strong |
| Duke champ YES | BUY | 19.7% | +5pp if 15% | If underpriced vs public |
| Arizona champ YES | BUY | 19.1% | +4pp if 15% | 3rd highest model probability |

### Situational Buys (if market is cheap)

| Market | Side | Model | Notes |
|--------|------|-------|-------|
| Purdue F4 YES | BUY | 22.4% | Up from 19.9%, strong 2-seed |
| Arkansas F4 YES | BUY | 13.3% | 4-seed dark horse, likely cheap |
| Michigan St. F4 YES | BUY | 16.9% | 3-seed, public undervalues |
| Vanderbilt F4 YES | BUY | 14.0% | New model favors them over Nebraska |
| Iowa St. F4 YES | BUY | 12.5% | If market <8%, good value |

---

## Section C: Sells / Positions to Exit

| Market | Action | Reason |
|--------|--------|--------|
| Illinois champ YES | SELL NOW | Model says 1.6% — no edge at any realistic price |
| Florida champ YES | SELL if >6% | Model says 4.1%, was overpriced last check |
| Houston champ YES | SELL if >5% | Model dropped to 3.7% |

---

## Section D: Rebalancing Rules

1. **Check after each round**, not each day — avoid overtrading on noise
2. If a team advances and F4 price spikes, consider selling F4 to lock profit and let champ bet ride
3. If a team is eliminated, position goes to zero — no action needed
4. Re-run model with updated Torvik data after R32 to check if remaining edges still hold
5. If model edge on a position flips negative (market corrects past model), sell
6. Illinois sell should happen ASAP — model confidence has dropped further
7. Purdue is now the strongest-conviction hold — model edge improved
