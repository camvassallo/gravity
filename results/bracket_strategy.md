# 2026 March Madness Bracket Strategy

Generated: 2026-03-17 | Model: Gravity v4 (15 features, consensus blending, sim_temp=1.3)

## Data Sources

- **Gravity v4 model**: 15-feature logistic regression + spread model, trained on 2018-2026 (42,560 games)
- **Consensus projections**: Average of Torvik, Miya, KenPom
- **Public ownership**: Yahoo bracket pick rates (Image: KenPom vs Yahoo)
- **Historical base rates**: NCAA tournament results by seed since 1985 (Stathead)

## Key Insights

### Public Ownership vs Model (Champion %)

| Team | KenPom | Public (Yahoo) | Gravity v4 | Edge vs Public |
|------|--------|---------------|------------|----------------|
| Duke | 21.1% | **30.2%** | 25.8% | Public overvalues by 9pp |
| Michigan | 18.6% | 14.5% | 24.5% | **Undervalued by 4pp — best contrarian champ** |
| Arizona | 18.2% | 19.4% | 20.7% | Fairly priced |
| Florida | 7.5% | 6.5% | 5.6% | Slight public undervalue |
| Houston | 6.0% | 5.2% | 4.3% | Slight public undervalue |
| Iowa St. | 5.5% | 1.8% | 2.2% | **Public severely undervalues (+3.7pp)** |
| Illinois | 4.7% | 1.1% | 2.3% | **Public severely undervalues (+3.6pp)** |
| Purdue | 4.4% | 3.2% | 4.8% | Slight public undervalue |
| UConn | 1.9% | 3.6% | 1.5% | Public overvalues |
| Kansas | 0.5% | 1.6% | 0.1% | Public overvalues |

### Historical R64 Upset Rates (Since 1985)

| Seed | Power Conf Win% | Non-Power Win% | Our Model Range |
|------|-----------------|----------------|-----------------|
| 10 | 40% | 35% | 33-45% |
| 11 | **45%** | 35% | 27-32% (too low) |
| 12 | **44%** | 31% | 8-12% (too low) |
| 13 | 33% | 19% | 4-11% |

Average tournament has ~8 upsets by seeds 10+ in R64. Our model underestimates 11 and 12 seed upset rates, especially for power conference teams.

### R64 Upsets Ranked by EV Cost

| # | EV Cost | Upset | Model % | Seed | Conference |
|---|---------|-------|---------|------|------------|
| 1 | **-1.20** | Iowa over Clemson | 56.0% | 9 | Big Ten |
| 2 | **-0.80** | Utah St. over Villanova | 54.0% | 9 | MWC |
| 3 | +1.02 | Santa Clara over Kentucky | 44.9% | 10 | WCC |
| 4 | +1.66 | Saint Louis over Georgia | 41.7% | 9 | A-10 |
| 5 | +2.29 | Missouri over Miami FL | 38.6% | 10 | **SEC** |
| 6 | +2.63 | TCU over Ohio St. | 36.8% | 9 | Big 12 |
| 7 | +3.07 | UCF over UCLA | 34.7% | 10 | AAC |
| 8 | +3.35 | Texas A&M over Saint Mary's | 33.3% | 10 | **SEC** |
| 9 | +3.61 | SMU over Tennessee | 31.9% | 11 | **ACC** |
| 10 | +3.74 | N.C. State over BYU | 31.3% | 11 | **ACC** |
| 11 | +4.58 | VCU over North Carolina | 27.1% | 11 | A-10 |
| 12 | +5.62 | South Florida over Louisville | 21.9% | 11 | AAC |

First 2 upsets are FREE (model favors the underdog). First 4 cost only +0.68 total.

---

## Bracket A: Conservative (Pool <= 25)

**Champion: Duke(1) | F4: Duke(1), Houston(2), Arizona(1), Michigan(1)**
**R64 upsets: 3 | R64 EV cost: -0.98 (net positive)**

### EAST (E8 winner: Duke)

| Round | Matchup | Pick | Prob |
|-------|---------|------|------|
| R64 | (1) Duke vs (16) Siena | Duke | 99.4% |
| R64 | (8) Ohio St. vs (9) TCU | Ohio St. | 63.2% |
| R64 | (5) St. John's vs (12) Northern Iowa | St. John's | 91.7% |
| R64 | (4) Kansas vs (13) Cal Baptist | Kansas | 89.2% |
| R64 | (6) Louisville vs (11) South Florida | Louisville | 78.1% |
| R64 | (3) Michigan St. vs (14) North Dakota St. | Michigan St. | 95.3% |
| R64 | (7) UCLA vs (10) UCF | UCLA | 65.3% |
| R64 | (2) Connecticut vs (15) Furman | Connecticut | 98.5% |
| R32 | Duke vs Ohio St. | Duke | |
| R32 | St. John's vs Kansas | St. John's | |
| R32 | Michigan St. vs Louisville | Michigan St. | |
| R32 | Connecticut vs UCLA | Connecticut | |
| S16 | Duke vs St. John's | Duke | |
| S16 | Michigan St. vs Connecticut | Connecticut | |
| E8 | Duke vs Connecticut | Duke | |

### WEST (E8 winner: Arizona)

| Round | Matchup | Pick | Prob |
|-------|---------|------|------|
| R64 | (1) Arizona vs (16) LIU | Arizona | 99.5% |
| R64 | (8) Villanova vs (9) Utah St. | **Utah St.** | 54.0% |
| R64 | (5) Wisconsin vs (12) High Point | Wisconsin | 92.3% |
| R64 | (4) Arkansas vs (13) Hawaii | Arkansas | 95.7% |
| R64 | (6) BYU vs (11) N.C. State | BYU | 68.7% |
| R64 | (3) Gonzaga vs (14) Kennesaw St. | Gonzaga | 96.7% |
| R64 | (7) Miami FL vs (10) Missouri | Miami FL | 61.4% |
| R64 | (2) Purdue vs (15) Queens | Purdue | 98.7% |
| R32 | Arizona vs Utah St. | Arizona | |
| R32 | Wisconsin vs Arkansas | Arkansas | |
| R32 | Gonzaga vs BYU | Gonzaga | |
| R32 | Purdue vs Miami FL | Purdue | |
| S16 | Arizona vs Arkansas | Arizona | |
| S16 | Gonzaga vs Purdue | Purdue | |
| E8 | Arizona vs Purdue | Arizona | |

### SOUTH (E8 winner: Houston)

| Round | Matchup | Pick | Prob |
|-------|---------|------|------|
| R64 | (1) Florida vs (16) Prairie View A&M | Florida | 99.4% |
| R64 | (8) Clemson vs (9) Iowa | **Iowa** | 56.0% |
| R64 | (5) Vanderbilt vs (12) McNeese St. | Vanderbilt | 89.0% |
| R64 | (4) Nebraska vs (13) Troy | Nebraska | 96.4% |
| R64 | (6) North Carolina vs (11) VCU | North Carolina | 72.9% |
| R64 | (3) Illinois vs (14) Penn | Illinois | 96.6% |
| R64 | (7) Saint Mary's vs (10) Texas A&M | Saint Mary's | 66.7% |
| R64 | (2) Houston vs (15) Idaho | Houston | 97.6% |
| R32 | Florida vs Iowa | Florida | |
| R32 | Vanderbilt vs Nebraska | Vanderbilt | |
| R32 | Illinois vs North Carolina | Illinois | |
| R32 | Houston vs Saint Mary's | Houston | |
| S16 | Florida vs Vanderbilt | Florida | |
| S16 | Illinois vs Houston | Houston | |
| E8 | Florida vs Houston | **Houston** | |

### MIDWEST (E8 winner: Michigan)

| Round | Matchup | Pick | Prob |
|-------|---------|------|------|
| R64 | (1) Michigan vs (16) UMBC | Michigan | 99.5% |
| R64 | (8) Georgia vs (9) Saint Louis | Georgia | 58.3% |
| R64 | (5) Texas Tech vs (12) Akron | Texas Tech | 87.9% |
| R64 | (4) Alabama vs (13) Hofstra | Alabama | 93.1% |
| R64 | (6) Tennessee vs (11) SMU | Tennessee | 68.1% |
| R64 | (3) Virginia vs (14) Wright St. | Virginia | 96.3% |
| R64 | (7) Kentucky vs (10) Santa Clara | **Santa Clara** | 44.9% |
| R64 | (2) Iowa St. vs (15) Tennessee St. | Iowa St. | 98.3% |
| R32 | Michigan vs Georgia | Michigan | |
| R32 | Alabama vs Texas Tech | Alabama | |
| R32 | Virginia vs Tennessee | Virginia | |
| R32 | Iowa St. vs Santa Clara | Iowa St. | |
| S16 | Michigan vs Alabama | Michigan | |
| S16 | Virginia vs Iowa St. | Iowa St. | |
| E8 | Michigan vs Iowa St. | Michigan | |

### Final Four

| Semifinal | Pick |
|-----------|------|
| Duke vs Houston | Duke |
| Arizona vs Michigan | Michigan |
| **Championship** | **Duke** over Michigan |

### Rationale

Only deviates from chalk where the model actually favors the "upset" (Iowa 56%, Utah St. 54%) or it's nearly a coin flip (Santa Clara 45%). Houston over Florida in E8 is the cheapest way to avoid an all-1-seed F4 — only ~3 EV points less than Florida. Duke champion is correct for small pools where public ownership doesn't matter.

---

## Bracket B: Balanced (Pool 50-150)

**Champion: Michigan(1) | F4: Duke(1), Houston(2), Arizona(1), Michigan(1)**
**R64 upsets: 6 | R64 EV cost: +5.60**

Changes from Bracket A are marked with **>>**.

### EAST (E8 winner: Duke)

| Round | Matchup | Pick | Notes |
|-------|---------|------|-------|
| R64 | (1) Duke vs (16) Siena | Duke | |
| R64 | (8) Ohio St. vs (9) TCU | Ohio St. | |
| R64 | (5) St. John's vs (12) Northern Iowa | St. John's | |
| R64 | (4) Kansas vs (13) Cal Baptist | Kansas | |
| R64 | (6) Louisville vs (11) South Florida | Louisville | |
| R64 | (3) Michigan St. vs (14) North Dakota St. | Michigan St. | |
| R64 | (7) UCLA vs (10) UCF | **>> UCF** | 34.7%, historical 10-seed: 35-40% |
| R64 | (2) Connecticut vs (15) Furman | Connecticut | |
| R32 | Duke vs Ohio St. | Duke | |
| R32 | St. John's vs Kansas | St. John's | |
| R32 | Michigan St. vs Louisville | Michigan St. | |
| R32 | Connecticut vs UCF | Connecticut | |
| S16 | Duke vs St. John's | Duke | |
| S16 | Michigan St. vs Connecticut | Connecticut | |
| E8 | Duke vs Connecticut | Duke | |

### WEST (E8 winner: Arizona)

| Round | Matchup | Pick | Notes |
|-------|---------|------|-------|
| R64 | (1) Arizona vs (16) LIU | Arizona | |
| R64 | (8) Villanova vs (9) Utah St. | **Utah St.** | Model favors, 54% |
| R64 | (5) Wisconsin vs (12) High Point | Wisconsin | |
| R64 | (4) Arkansas vs (13) Hawaii | Arkansas | |
| R64 | (6) BYU vs (11) N.C. State | BYU | |
| R64 | (3) Gonzaga vs (14) Kennesaw St. | Gonzaga | |
| R64 | (7) Miami FL vs (10) Missouri | **>> Missouri** | 38.6%, SEC power conf, hist 40% |
| R64 | (2) Purdue vs (15) Queens | Purdue | |
| R32 | Arizona vs Utah St. | Arizona | |
| R32 | Wisconsin vs Arkansas | Arkansas | |
| R32 | Gonzaga vs BYU | Gonzaga | |
| R32 | Purdue vs Missouri | Purdue | |
| S16 | Arizona vs Arkansas | Arizona | |
| S16 | Gonzaga vs Purdue | Purdue | |
| E8 | Arizona vs Purdue | Arizona | |

### SOUTH (E8 winner: Houston)

| Round | Matchup | Pick | Notes |
|-------|---------|------|-------|
| R64 | (1) Florida vs (16) Prairie View A&M | Florida | |
| R64 | (8) Clemson vs (9) Iowa | **Iowa** | Model favors, 56% |
| R64 | (5) Vanderbilt vs (12) McNeese St. | Vanderbilt | |
| R64 | (4) Nebraska vs (13) Troy | Nebraska | |
| R64 | (6) North Carolina vs (11) VCU | North Carolina | |
| R64 | (3) Illinois vs (14) Penn | Illinois | |
| R64 | (7) Saint Mary's vs (10) Texas A&M | Saint Mary's | |
| R64 | (2) Houston vs (15) Idaho | Houston | |
| R32 | Florida vs Iowa | Florida | |
| R32 | Vanderbilt vs Nebraska | Vanderbilt | |
| R32 | Illinois vs North Carolina | Illinois | |
| R32 | Houston vs Saint Mary's | Houston | |
| S16 | Florida vs Vanderbilt | Florida | |
| S16 | Illinois vs Houston | Houston | |
| E8 | Florida vs Houston | **Houston** | |

### MIDWEST (E8 winner: Michigan)

| Round | Matchup | Pick | Notes |
|-------|---------|------|-------|
| R64 | (1) Michigan vs (16) UMBC | Michigan | |
| R64 | (8) Georgia vs (9) Saint Louis | Georgia | |
| R64 | (5) Texas Tech vs (12) Akron | Texas Tech | |
| R64 | (4) Alabama vs (13) Hofstra | Alabama | |
| R64 | (6) Tennessee vs (11) SMU | **>> SMU** | 31.9%, ACC power conf, hist 45% |
| R64 | (3) Virginia vs (14) Wright St. | Virginia | |
| R64 | (7) Kentucky vs (10) Santa Clara | **Santa Clara** | 44.9%, near coin flip |
| R64 | (2) Iowa St. vs (15) Tennessee St. | Iowa St. | |
| R32 | Michigan vs Georgia | Michigan | |
| R32 | Alabama vs Texas Tech | Alabama | |
| R32 | Virginia vs SMU | Virginia | |
| R32 | Iowa St. vs Santa Clara | Iowa St. | |
| S16 | Michigan vs Alabama | Michigan | |
| S16 | Virginia vs Iowa St. | Iowa St. | |
| E8 | Michigan vs Iowa St. | Michigan | |

### Final Four

| Semifinal | Pick |
|-----------|------|
| Duke vs Houston | Duke |
| Arizona vs Michigan | **>> Michigan** |
| **Championship** | **>> Michigan** over Duke |

### Rationale

Michigan champion is the key differentiator — 14.5% public ownership vs 24.5% model probability (1.7x leverage). Duke at 30.2% public is the most overvalued champion pick in the field. Houston over Florida in F4 is supported by consensus (KenPom 6.0% champ). Six R64 upsets include two power-conference 10/11 seeds (Missouri SEC, SMU ACC) where historical base rates (40-45%) suggest our model underestimates upset probability.

### Leverage Analysis

| Contrarian Pick | Model | Public | Leverage |
|-----------------|-------|--------|----------|
| Michigan champion | 24.5% | 14.5% | **1.7x** |
| Houston F4 | 27.4% | ~5.2% | **5.3x** |
| SMU over Tennessee | 31.9% | ~5% est. | **6.4x** |
| Missouri over Miami FL | 38.6% | ~10% est. | **3.9x** |

---

## Bracket C: Contrarian (Pool 150+)

**Champion: Michigan(1) | F4: Duke(1), Illinois(3), Arizona(1), Michigan(1)**
**R64 upsets: 8 | R64 EV cost: +12.02**

Changes from Bracket B are marked with **>>**.

### EAST (E8 winner: Duke)

| Round | Matchup | Pick | Notes |
|-------|---------|------|-------|
| R64 | (1) Duke vs (16) Siena | Duke | |
| R64 | (8) Ohio St. vs (9) TCU | **>> TCU** | 36.8%, hist 9-seed: 36-39% |
| R64 | (5) St. John's vs (12) Northern Iowa | St. John's | |
| R64 | (4) Kansas vs (13) Cal Baptist | Kansas | |
| R64 | (6) Louisville vs (11) South Florida | Louisville | |
| R64 | (3) Michigan St. vs (14) North Dakota St. | Michigan St. | |
| R64 | (7) UCLA vs (10) UCF | **UCF** | 34.7% |
| R64 | (2) Connecticut vs (15) Furman | Connecticut | |
| R32 | Duke vs TCU | Duke | |
| R32 | St. John's vs Kansas | St. John's | |
| R32 | Michigan St. vs Louisville | Michigan St. | |
| R32 | Connecticut vs UCF | Connecticut | |
| S16 | Duke vs St. John's | Duke | |
| S16 | Michigan St. vs Connecticut | Connecticut | |
| E8 | Duke vs Connecticut | Duke | |

### WEST (E8 winner: Arizona)

| Round | Matchup | Pick | Notes |
|-------|---------|------|-------|
| R64 | (1) Arizona vs (16) LIU | Arizona | |
| R64 | (8) Villanova vs (9) Utah St. | **Utah St.** | Model favors, 54% |
| R64 | (5) Wisconsin vs (12) High Point | Wisconsin | |
| R64 | (4) Arkansas vs (13) Hawaii | Arkansas | |
| R64 | (6) BYU vs (11) N.C. State | **>> N.C. State** | 31.3%, ACC power conf, hist 45% |
| R64 | (3) Gonzaga vs (14) Kennesaw St. | Gonzaga | |
| R64 | (7) Miami FL vs (10) Missouri | **Missouri** | 38.6%, SEC |
| R64 | (2) Purdue vs (15) Queens | Purdue | |
| R32 | Arizona vs Utah St. | Arizona | |
| R32 | Wisconsin vs Arkansas | Arkansas | |
| R32 | Gonzaga vs N.C. State | Gonzaga | |
| R32 | Purdue vs Missouri | Purdue | |
| S16 | Arizona vs Arkansas | Arizona | |
| S16 | Gonzaga vs Purdue | Purdue | |
| E8 | Arizona vs Purdue | Arizona | |

### SOUTH (E8 winner: Illinois)

| Round | Matchup | Pick | Notes |
|-------|---------|------|-------|
| R64 | (1) Florida vs (16) Prairie View A&M | Florida | |
| R64 | (8) Clemson vs (9) Iowa | **Iowa** | Model favors, 56% |
| R64 | (5) Vanderbilt vs (12) McNeese St. | Vanderbilt | |
| R64 | (4) Nebraska vs (13) Troy | Nebraska | |
| R64 | (6) North Carolina vs (11) VCU | North Carolina | |
| R64 | (3) Illinois vs (14) Penn | Illinois | |
| R64 | (7) Saint Mary's vs (10) Texas A&M | **>> Texas A&M** | 33.3%, SEC power conf, hist 40% |
| R64 | (2) Houston vs (15) Idaho | Houston | |
| R32 | Florida vs Iowa | Florida | |
| R32 | Vanderbilt vs Nebraska | Vanderbilt | |
| R32 | Illinois vs North Carolina | Illinois | |
| R32 | Houston vs Texas A&M | Houston | |
| S16 | Florida vs Vanderbilt | Florida | |
| S16 | **>> Illinois vs Houston** | **>> Illinois** | Big swing: 37.1% E8 prob |
| E8 | **>> Florida vs Illinois** | **>> Illinois** | Illinois to F4: 19.0% prob, 1.1% public |

### MIDWEST (E8 winner: Michigan)

| Round | Matchup | Pick | Notes |
|-------|---------|------|-------|
| R64 | (1) Michigan vs (16) UMBC | Michigan | |
| R64 | (8) Georgia vs (9) Saint Louis | **>> Saint Louis** | 41.7%, nearly a coin flip |
| R64 | (5) Texas Tech vs (12) Akron | Texas Tech | |
| R64 | (4) Alabama vs (13) Hofstra | Alabama | |
| R64 | (6) Tennessee vs (11) SMU | **SMU** | 31.9%, ACC power conf |
| R64 | (3) Virginia vs (14) Wright St. | Virginia | |
| R64 | (7) Kentucky vs (10) Santa Clara | **Santa Clara** | 44.9% |
| R64 | (2) Iowa St. vs (15) Tennessee St. | Iowa St. | |
| R32 | Michigan vs Saint Louis | Michigan | |
| R32 | Alabama vs Texas Tech | Alabama | |
| R32 | Virginia vs SMU | Virginia | |
| R32 | Iowa St. vs Santa Clara | Iowa St. | |
| S16 | Michigan vs Alabama | Michigan | |
| S16 | Virginia vs Iowa St. | Iowa St. | |
| E8 | Michigan vs Iowa St. | Michigan | |

### Final Four

| Semifinal | Pick |
|-----------|------|
| Duke vs **Illinois** | Duke |
| Arizona vs Michigan | **Michigan** |
| **Championship** | **Michigan** over Duke |

### Rationale

This bracket targets maximum separation from the field. The Illinois F4 is the centerpiece — KenPom gives Illinois 4.7% champion probability but only 1.1% of the public picks them anywhere near the F4. If Illinois makes it, you gain 80 points over ~198 of 200 opponents. Eight R64 upsets matches the historical average, with upset picks concentrated on power-conference teams (Missouri SEC, N.C. State ACC, Texas A&M SEC, SMU ACC) in spots where historical base rates (40-45%) suggest the model and public both underestimate upset probability.

### Leverage Analysis

| Contrarian Pick | Model/KenPom | Public | Leverage |
|-----------------|-------------|--------|----------|
| Michigan champion | 24.5% / 18.6% | 14.5% | **1.7x** |
| Illinois F4 | 19.0% / ~20% | ~1.1% | **17x** |
| SMU over Tennessee | 31.9% | ~5% est. | **6.4x** |
| Iowa St. S16 | 75.3% | ~1.8% | **42x** |
| Texas A&M over St. Mary's | 33.3% | ~10% est. | **3.3x** |

---

## Summary

| | A: Conservative | B: Balanced | C: Contrarian |
|---|---|---|---|
| **Pool size** | <=25 | 50-150 | 150+ |
| **Champion** | Duke (1) | Michigan (1) | Michigan (1) |
| **F4 seeds** | 1, 2, 1, 1 | 1, 2, 1, 1 | 1, **3**, 1, 1 |
| **R64 upsets** | 3 | 6 | 8 |
| **R64 EV cost** | -0.98 | +5.60 | +12.02 |
| **Late-round EV** | ~668 | ~668 | ~560 |
| **Big swing** | None | Michigan champ | Illinois F4 |
| **Public overlap** | High | Medium | Low |
| **Best if...** | Maximizing expected score | Want to win a medium pool | Need to beat 150+ people |

### Key Principles

1. **Duke champion is a trap** in pools >25 — 30.2% of Yahoo brackets pick Duke, KenPom only gives 21.1%
2. **Michigan is the optimal contrarian champion** — 14.5% public, but KenPom (18.6%) and our model (24.5%) both agree they're undervalued
3. **Iowa St. and Illinois** are the most undervalued teams by the public — massive leverage plays for deep runs
4. **Power conference 10/11 seeds** win 40-45% historically — pick at least 2-3 of these upsets
5. **First 4 upsets are essentially free** — Iowa, Utah St., Santa Clara, and Saint Louis cost a combined +0.68 EV
6. **A->B costs almost nothing** — Michigan champ is nearly as likely as Duke but creates huge separation
7. **B->C costs ~108 late-round EV** — the Illinois F4 swing is expensive but necessary to win a large pool
