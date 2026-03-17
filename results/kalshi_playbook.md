# Kalshi Trading Playbook — 2026 March Madness

Updated: 2026-03-16 (v4 model: 15 features, 7:8 player:team ratio + consensus blending)

**Key changes in v4:** Rebalanced feature ratio (added adjoe/adjde, pruned 3 weak player features), added 30% consensus blending in bracket simulation. This corrects the player-feature bias that was overvaluing star-driven teams and undervaluing system/efficiency teams.

---

## Model Probabilities (Gravity v4 vs Consensus avg of Torvik/Miya/KenPom)

| Team | v4 Champ % | v3 Champ % | Consensus % | v4 Edge | Notes |
|------|-----------|-----------|-------------|---------|-------|
| Duke | 31.2 | 19.4 | 20.2 | +11.0 | Model very bullish — adjoe/adjde features boosted Duke |
| Michigan | 28.7 | 27.5 | 20.9 | +7.8 | Still our biggest edge, Miya confirms |
| Arizona | 22.3 | 19.4 | 17.0 | +5.3 | Increased — strong on both team + player metrics |
| Florida | 4.5 | 3.7 | 9.4 | -4.9 | Improved from v3 but still below consensus |
| Purdue | 3.4 | 4.6 | 4.8 | -1.4 | Slight decrease |
| Houston | 3.2 | 3.5 | 6.5 | -3.3 | Still below consensus — system team |
| Illinois | 1.4 | 1.4 | 4.3 | -2.9 | Unchanged — consensus blending helps in sim but champ% similar |
| Iowa St. | 1.2 | 1.7 | 4.6 | -3.4 | Still below consensus |
| Connecticut | 0.9 | 1.4 | 2.0 | -1.1 | Decreased |
| Michigan St. | 0.8 | 3.6 | 1.5 | -0.7 | Down from 3.6% — player-bias correction working |
| Nebraska | 0.2 | 1.6 | 0.5 | -0.3 | Down from 1.6% — player-bias correction working |

**v3 → v4 impact:** The feature rebalancing did what we expected. Star-driven teams that were overvalued (Michigan St. 3.6→0.8%, Nebraska 1.6→0.2%) came down. System teams (Florida 3.7→4.5%) moved up slightly. However, Duke's increase to 31.2% is driven by their strong adjoe/adjde profile, not player-bias.

---

## Section A: Current Holdings

All positions are **Champion YES** contracts.

| Team | Shares | Cost Basis | v4 Model % | Consensus % | Action |
|------|--------|------------|-----------|-------------|--------|
| Louisville | 935 | $19.99 | 0.1% | 0.5% | HOLD (illiquid, can't sell) |
| Houston | 208 | $19.92 | 3.2% | 6.5% | **HOLD** — consensus says 6.5%, model still underweights system teams |
| Purdue | 468 | $19.98 | 3.4% | 4.8% | **HOLD** — model + consensus roughly aligned |
| Illinois | 268 | $19.99 | 1.4% | 4.3% | **HOLD if market <5%** — consensus says 4.3% |
| Florida | 234 | $19.93 | 4.5% | 9.4% | **HOLD** — improved in v4 but still below consensus |

---

## Section B: New Orders

### High-Conviction Buys (model + consensus aligned)

| Market | Side | v4 Model | Consensus | Notes |
|--------|------|---------|-----------|-------|
| Michigan champ YES | BUY | 28.7% | 20.9% | Best edge, confirmed by Miya |
| Arizona champ YES | BUY | 22.3% | 17.0% | Strong edge, Miya agrees |
| Duke champ YES | BUY if <25% | 31.2% | 20.2% | New top pick in v4 — but check if market already priced in |

### Medium-Conviction Buys

| Market | Side | v4 Model | Consensus | Notes |
|--------|------|---------|-----------|-------|
| Michigan F4 YES | BUY | 73.2% | 53.8% | Large edge |
| Duke F4 YES | BUY | 71.7% | ~55% | Large edge if market below model |

### Removed from buy list (v4 corrections)

| Market | v3 Model | v4 Model | Consensus | Why removed |
|--------|---------|---------|-----------|-------------|
| Michigan St. F4 YES | 17.8% | 9.3% | 11.2% | Player-bias correction — no longer an edge |
| Vanderbilt F4 YES | 14.3% | 8.2% | 7.2% | Closer to consensus now, small edge not worth it |
| Nebraska F4 YES | 13.7% | 5.8% | 5.3% | Corrected down dramatically |

---

## Section C: Sells / Positions to Exit

**No active sells.** Consensus analysis + v4 corrections show our holdings are fairly valued or undervalued relative to consensus.

---

## Section D: Rebalancing Rules

1. **Check after each round**, not each day — avoid overtrading on noise
2. If a team advances and F4 price spikes, consider selling F4 to lock profit and let champ bet ride
3. If a team is eliminated, position goes to zero — no action needed
4. Re-run model with updated Torvik data after R32 to check if remaining edges still hold
5. If model edge on a position flips negative AND consensus agrees, sell
6. Michigan and Duke are the highest-conviction positions — model significantly above consensus on both
7. **Trust consensus over model** for Florida, Illinois, Iowa St., Houston — model still underweights system teams even after v4 correction
8. **Trust model over consensus** for Michigan, Duke, Arizona — strong team + player fundamentals
