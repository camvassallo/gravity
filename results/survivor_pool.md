# March Madness 2026 — Survivor Pool Strategy

Updated 2026-03-26 (Sweet 16 Thursday). Pick one team per day to win. Can't reuse a team. One loss = eliminated. Complete 6-pick path optimized via brute-force search over all valid assignments, maximizing joint survival probability across 4 consensus sources + sentiment + injuries.

---

## Schedule Structure

| Day | Date | Round | Regions |
|---|---|---|---|
| 1 | Thu Mar 19 | R64 | All |
| 2 | Fri Mar 20 | R64 | All |
| 3 | Sat Mar 21 | R32 | Thursday winners |
| 4 | Sun Mar 22 | R32 | Friday winners |
| **5** | **Thu Mar 26** | **S16** | **South + West** |
| 6 | Fri Mar 27 | S16 | East + Midwest |
| 7 | Sat Mar 29 | E8 | South + West |
| 8 | Sun Mar 30 | E8 | East + Midwest |
| 9 | Sat Apr 5 | Final Four | Semi 1 (E vs S) + Semi 2 (W vs MW) |
| 10 | Mon Apr 7 | Championship | Final |

---

## Results So Far

| Day | Pick | Result | Win% | Cumulative |
|---|---|---|---|---|
| 1 | Gonzaga | Won 73-64 vs Kennesaw St. | 96% | 96.0% |
| 2 | UConn | Won 82-71 vs Furman | 96% | 92.2% |
| 3 | Arkansas | Won 94-88 vs High Point | 87% | 80.2% |
| 4 | Iowa St. | Won 82-63 vs Kentucky | 75% | 60.2% |

**Used teams:** Gonzaga, UConn, Arkansas, Iowa St.

---

## R32 Results & Key Bracket Changes

| Result | Impact |
|---|---|
| Florida 72, **Iowa 73** | **Florida (1S) eliminated!** Iowa (9-seed) in S16 |
| **Texas 74**, Gonzaga 68 | Gonzaga eliminated. Purdue faces Texas (11) instead of Gonzaga (3) |
| Duke 81, TCU 58 | Duke dominant |
| Michigan 95, Saint Louis 72 | Michigan dominant |
| MSU 77, Louisville 69 | MSU advances |
| Illinois 76, VCU 55 | Illinois dominant |
| Houston 88, Texas A&M 57 | Houston cruises |
| Alabama 90, Texas Tech 65 | Alabama advances |
| Tennessee 79, Virginia 72 | Tennessee advances |
| St. John's 67, Kansas 65 | St. John's upset |

---

## Sweet 16 Matchups

**Day 5 — Thu Mar 26 (South + West):**

| Game | Consensus | FanMatch |
|---|---|---|
| Illinois (3S) vs Houston (2S) | Houston 55% / Illinois 46% | Houston 53% |
| Iowa (9S) vs Nebraska (4S) | Nebraska 56% / Iowa 40% | Nebraska 58% |
| Arkansas (4W) vs Arizona (1W) | Arizona 78% / Arkansas 22% | Arizona 79% |
| Texas (11W) vs Purdue (2W) | Purdue 73% / Texas 21% | Purdue 75% |

**Day 6 — Fri Mar 27 (East + Midwest):**

| Game | Consensus | FanMatch |
|---|---|---|
| MSU (3E) vs UConn (2E) | MSU 48% / UConn 47% | MSU 51% |
| Tennessee (6MW) vs Iowa St. (2MW) | Iowa St. 63% / Tennessee 39% | Iowa St. 64% |
| Alabama (4MW) vs Michigan (1MW) | Michigan 84% / Alabama 13% | Michigan 76% |
| St. John's (5E) vs Duke (1E) | Duke 75% / St. John's 26% | Duke 75% |

---

## Consensus Model (4-source avg + sentiment + injuries)

| Team | Region | E8% | F4% | F2% | Champ% |
|---|---|---|---|---|---|
| Michigan | MW | 84.2 | 59.7 | 37.1 | 22.6 |
| Arizona | W | 77.5 | 54.6 | 30.3 | 17.5 |
| Duke | E | 74.5 | 54.2 | 36.6 | 21.1 |
| Purdue | W | 73.4 | 30.1 | 12.4 | 5.3 |
| Houston | S | 55.1 | 40.6 | 20.3 | 9.7 |
| Nebraska | S | 56.3 | 17.4 | 5.7 | 1.6 |
| MSU | E | 48.0 | 15.5 | 6.6 | 2.2 |
| Illinois | S | 46.0 | 32.1 | 15.1 | 6.7 |
| Iowa | S | 39.8 | 9.7 | 2.4 | 0.5 |
| Tennessee | MW | 39.1 | 10.7 | 3.8 | 1.2 |
| St. John's | E | 26.3 | 12.3 | 5.0 | 1.5 |
| Texas | W | 21.0 | 3.9 | 0.6 | 0.2 |
| Alabama | MW | 13.1 | 5.1 | 1.7 | 0.5 |

*E8% = prob of reaching E8 (= S16 win prob). F4% = reaching F4. F2% = reaching Championship game. Champ% = winning it all.*

---

## THE OPTIMAL COMPLETE PATH

Brute-force searched all valid 6-team assignments across Days 5-10, maximizing the product of win probabilities. Each team that isn't our S16 pick must independently advance to the round where we pick them.

### How the math works

| Day | Round | What our pick needs | Probability used |
|---|---|---|---|
| 5, 6 | S16 | Just win the S16 game (our pick) | Team's **E8%** |
| 7, 8 | E8 | Win S16 independently + win E8 (our pick) | Team's **F4%** |
| 9 | F4 | Win S16 + E8 independently + win F4 semi (our pick) | Team's **F2%** |
| 10 | Championship | Win S16 + E8 + F4 independently + win final (our pick) | Team's **Champ%** |

### The Path

| Day | Date | Pick | Round | Opponent | Prob | Why |
|---|---|---|---|---|---|---|
| **5** | **Thu Mar 26** | **Purdue** | S16 | Texas (11W) | **73.4%** | Strongest S+W pick while preserving Arizona for Championship |
| **6** | **Fri Mar 27** | **Michigan St.** | S16 | UConn (2E) | **48.0%** | Toss-up game, but frees Michigan for E8 AND Duke for F4 |
| **7** | **Sat Mar 29** | **Houston** | E8 | South E8 | **40.6%** | Houston must win S16 vs Illinois (55%) then win E8 (~74%) |
| **8** | **Sun Mar 30** | **Michigan** | E8 | Midwest E8 | **59.7%** | Michigan must win S16 vs Alabama (84%) then win E8 (~71%) |
| **9** | **Sat Apr 5** | **Duke** | F4 Semi 1 | E vs S | **36.6%** | Duke must reach F4 (54%) then win semifinal (~68%) |
| **10** | **Mon Apr 7** | **Arizona** | Championship | Final | **17.5%** | Arizona must reach Final (30%) then win title (~58%) |

### Joint Survival Probability

```
  Day 5:  73.4%  (Purdue S16)
× Day 6:  48.0%  (MSU S16)
× Day 7:  40.6%  (Houston reaches E8 + wins)
× Day 8:  59.7%  (Michigan reaches E8 + wins)
× Day 9:  36.6%  (Duke reaches F4 + wins semi)
× Day 10: 17.5%  (Arizona reaches Final + wins title)
─────────────────────────────────
= 0.55% from today
= 0.33% overall (with 60.2% prior)
```

**~1 in 180 from today. ~1 in 300 overall.**

---

## Why This Path Is Optimal

### The key insight: MSU on Day 6

The counterintuitive move is picking **MSU (48%)** on Day 6 instead of Michigan (84%). This loses 36 points on Day 6, but:

- **Frees Michigan for Day 8 E8** (59.7%) instead of needing MSU/Tennessee (15.5%/10.7%)
- **Frees Duke for Day 9 F4** (36.6%) instead of needing Illinois/MSU (15.1%/6.6%)
- **Preserves Arizona for Day 10 Championship** (17.5%) instead of Purdue (5.3%)

The downstream gains (Michigan 59.7% × Duke 36.6% × Arizona 17.5%) massively outperform the alternative (MSU 15.5% × Illinois 15.1% × Purdue 5.3%).

### Top 5 paths compared

| Rank | Path | Product |
|---|---|---|
| **1** | **Purdue → MSU → Houston → Michigan → Duke → Arizona** | **0.546%** |
| **1t** | **Purdue → MSU → Houston → Michigan → Arizona → Duke** | **0.546%** |
| 3 | Purdue → MSU → Arizona → Duke → Houston → Michigan | 0.478% |
| 4 | Purdue → Tennessee → Houston → Michigan → Duke → Arizona | 0.445% |
| 5 | Purdue → MSU → Illinois → Michigan → Duke → Arizona | 0.432% |

The #1 and #1t paths are essentially identical (Duke D9 / Arizona D10 vs Arizona D9 / Duke D10). We pick **Duke D9 + Arizona D10** because Duke has the higher Day 9 probability (36.6% vs 30.3%), and surviving Day 9 is prerequisite for Day 10.

---

## Day-by-Day Detail

### Day 5 — TODAY Thu Mar 26: PURDUE vs Texas

**Consensus: 73.4%** | FanMatch: 75% (82-74)

Purdue (2W) vs Texas (11W). Purdue dominated through R64/R32 (104-71 over Queens, 79-69 over Miami FL). Texas is an 11-seed that upset Gonzaga and BYU but faces a significant step up.

Purdue injury: C.J. Cox GTD (knee) — rotation guard, minor impact.
Texas injury: Pope GTD, Traore OUT — role players.

**Why not Arizona (78%)?** Arizona's Champ% (17.5%) is irreplaceable on Day 10. No other Semi 2 team comes close — Purdue is 5.3%, Tennessee 1.2%. Using Arizona today wastes 12.2% of Championship equity for a 4.1% S16 improvement.

### Day 6 — Fri Mar 27: MICHIGAN ST. vs UConn

**Consensus: 48.0%** | FanMatch: 51% (70-69)

MSU (3E) vs UConn (2E). True toss-up. MSU beat Louisville 77-69, UConn beat UCLA 73-57. UConn is the higher seed but has been faded all tournament (0.90 sentiment adjustment). MSU's Coen Carr (21p/10r/2b) has been excellent.

**This is the riskiest pick in the path.** But picking Michigan (84%) here and losing Duke/Michigan for later rounds costs far more in expected value. The brute-force search proves every alternative to MSU Day 6 produces a worse overall product.

### Day 7 — Sat Mar 29: HOUSTON (E8 South)

**Requires: Houston wins S16 today (55.1%) + wins E8 Saturday (~74%)**
**Joint: 40.6%**

Houston (2S) must beat Illinois in today's S16 game, then beat Nebraska/Iowa in the South E8. Houston has been dominant (78-47 R64, 88-57 R32). If Houston reaches E8, they're a strong favorite against the weaker South lower bracket.

### Day 8 — Sun Mar 30: MICHIGAN (E8 Midwest)

**Requires: Michigan wins S16 Friday (84.2%) + wins E8 Sunday (~71%)**
**Joint: 59.7%**

Michigan (1MW) must beat Alabama Friday (heavily favored at 84%), then beat Iowa St./Tennessee in the Midwest E8. Michigan has been the most dominant team in the tournament (101-80, 95-72). Even without us picking them Friday, Michigan is overwhelmingly likely to advance.

### Day 9 — Sat Apr 5: DUKE (F4 Semi 1: East vs South)

**Requires: Duke wins S16 (74.5%) + wins E8 (~73%) + wins F4 semi (~68%)**
**Joint: 36.6%**

Duke must independently advance through the East bracket to reach the Final Four, then beat the South representative (likely Houston, our Day 7 pick — if Houston lost E8, it would be Nebraska/Iowa). Duke has the highest conditional F4 win rate (67.6%) of any team and is the consensus co-favorite for the title.

Duke injury update: Caleb Foster upgraded from OUT to GTD (foot) — positive sign. If Foster returns, Duke's F4 probability increases.

### Day 10 — Mon Apr 7: ARIZONA (Championship)

**Requires: Arizona wins S16 (77.5%) + wins E8 (~70%) + wins F4 semi (~56%) + wins final (~58%)**
**Joint: 17.5%**

Arizona must independently advance through the entire West bracket and Semi 2 (vs Michigan most likely), then beat the Semi 1 winner (Duke most likely, our Day 9 pick) in the Championship.

Arizona is the #1 overall seed and consensus title contender. Their 17.5% Championship probability is the highest available for any Semi 2 team — the next best is Michigan at 22.6%, but Michigan is needed on Day 8.

---

## Survival Tracker

| Day | Pick | Win% | Cumulative | Status |
|---|---|---|---|---|
| 1 | Gonzaga | 96.0% | 96.0% | Won |
| 2 | UConn | 96.0% | 92.2% | Won |
| 3 | Arkansas | 87.0% | 80.2% | Won |
| 4 | Iowa St. | 75.0% | 60.2% | Won |
| **5** | **Purdue** | **73.4%** | **44.2%** | **TODAY** |
| 6 | Michigan St. | 48.0% | 21.2% | Fri Mar 27 |
| 7 | Houston | 40.6% | 8.6% | Sat Mar 29 |
| 8 | Michigan | 59.7% | 5.1% | Sun Mar 30 |
| 9 | Duke | 36.6% | 1.9% | Sat Apr 5 |
| 10 | Arizona | 17.5% | **0.33%** | Mon Apr 7 |

---

## What Kills This Path

| Event | Probability | Impact |
|---|---|---|
| Purdue loses to Texas today | 27% | Eliminated Day 5 |
| MSU loses to UConn Friday | 52% | Eliminated Day 6 |
| Houston doesn't reach E8 (loses to Illinois) | 45% | Eliminated Day 7 |
| Michigan doesn't reach E8 (loses to Alabama) | 16% | Eliminated Day 8 |
| Duke doesn't reach F4 | 46% | Eliminated Day 9 |
| Arizona doesn't win Championship | 82% | Eliminated Day 10 |

**The most likely failure point is Day 6 (MSU, 52% to fail).** This is the cost of the optimal path — the Day 6 coin flip is what makes Days 8-10 possible.

---

## Data Sources (Updated 2026-03-26)

- **Torvik (T-Rank):** `data/torvik_proj.csv` (16 S16 teams)
- **KenPom:** `data/kenpom_proj.csv` (16 teams, E8/F4/Final/Champ)
- **Evan Miya:** `data/miya_proj.csv` (16 teams)
- **CBB Analytics:** `data/cbb_proj.csv` (16 teams, CBS projections)
- **FanMatch:** `schedule.txt` (game-day win probabilities)
- **Injuries:** `data/college-basketball-injury-report.csv`
  - Duke: Foster GTD (foot, upgraded from OUT)
  - Michigan: Grady GTD (lower leg)
  - Purdue: Cox GTD (knee)
  - Alabama: Holloway OUT + Bristow/Hannah/Onyejiaka GTD
  - Illinois: Rodgers OUT (knee)
  - Nebraska: Burt OUT (knee)
  - Arkansas: Knox OUT (knee)
  - Texas: Pope GTD, Traore OUT
