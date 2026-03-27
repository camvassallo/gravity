# March Madness 2026 — Survivor Pool Strategy

Updated 2026-03-27 (Sweet 16 Friday). Pick one team per day to win. Can't reuse a team. One loss = eliminated. Complete 5-pick path (Days 6-10) optimized via brute-force search over all valid assignments, maximizing joint survival probability across 4 consensus sources + sentiment + injuries.

---

## Schedule Structure

| Day | Date | Round | Regions |
|---|---|---|---|
| 1 | Thu Mar 19 | R64 | All |
| 2 | Fri Mar 20 | R64 | All |
| 3 | Sat Mar 21 | R32 | Thursday winners |
| 4 | Sun Mar 22 | R32 | Friday winners |
| 5 | Thu Mar 26 | S16 | South + West |
| **6** | **Fri Mar 27** | **S16** | **East + Midwest** |
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
| 5 | Purdue | Won 79-77 vs Texas | 73% | 44.2% |

**Used teams:** Gonzaga, UConn, Arkansas, Iowa St., Purdue

---

## S16 Day 5 Results & Key Bracket Changes

| Result | Impact |
|---|---|
| **Illinois 65**, Houston 55 | **Houston (2S) eliminated!** Illinois dominates, advances to E8 South |
| **Iowa 77**, Nebraska 71 | Iowa's Cinderella run continues. E8 South = Illinois vs Iowa |
| **Arizona 109**, Arkansas 88 | Arizona dominant as 1-seed. E8 West = Arizona vs Purdue |
| **Purdue 79**, Texas 77 | Purdue survives close call (our Day 5 pick). E8 West = Arizona vs Purdue |

**Impact on path:** Houston's elimination removes our old Day 7 pick. But Illinois (77% F4) replaces Houston (41% F4) — a massive upgrade. Path is significantly stronger.

---

## S16 Day 6 Matchups — TODAY Fri Mar 27 (East + Midwest)

| Game | Consensus | FanMatch |
|---|---|---|
| MSU (3E) vs UConn (2E) | MSU 47% / UConn 48% | MSU 70-69 (51%) |
| St. John's (5E) vs Duke (1E) | Duke 75% / St. John's 26% | Duke 75-68 (75%) |
| Alabama (4MW) vs Michigan (1MW) | Michigan 81% / Alabama 13% | Michigan 91-83 (76%) |
| Tennessee (6MW) vs Iowa St. (2MW) | Iowa St. 63% / Tennessee 36% | Iowa St. 71-67 (64%) |

---

## E8 Matchups (Known)

| Day | Game | Notes |
|---|---|---|
| 7 (Sat Mar 29) | **Illinois (3S) vs Iowa (9S)** | South E8 |
| 7 (Sat Mar 29) | **Arizona (1W) vs Purdue (2W)** | West E8 (Purdue used) |
| 8 (Sun Mar 30) | East E8: TBD | Winners of MSU/UConn vs Duke/St. John's |
| 8 (Sun Mar 30) | Midwest E8: TBD | Winners of Michigan/Alabama vs Iowa St./Tennessee |

---

## Consensus Model (4-source avg + sentiment + injuries)

| Team | Region | E8% | F4% | F2% | Champ% |
|---|---|---|---|---|---|
| Arizona | W | 100.0 | 68.2 | 38.2 | 22.6 |
| Duke | E | 74.5 | 54.2 | 37.2 | 21.2 |
| Michigan | MW | 81.3 | 57.6 | 33.8 | 20.6 |
| Illinois | S | 100.0 | 77.0 | 36.5 | 15.9 |
| Purdue | W | 100.0 | 33.4 | 13.7 | 6.0 |
| Iowa St. | MW | 63.4 | 25.5 | 11.2 | 5.4 |
| UConn | E | 47.9 | 16.5 | 7.5 | 2.7 |
| Michigan St. | E | 47.0 | 15.3 | 6.7 | 2.2 |
| Iowa | S | 100.0 | 27.3 | 6.9 | 1.6 |
| St. John's | E | 25.9 | 12.1 | 5.0 | 1.5 |
| Tennessee | MW | 35.5 | 9.8 | 2.9 | 1.0 |
| Alabama | MW | 13.0 | 5.0 | 1.5 | 0.5 |

*E8% = prob of reaching E8 (100% for teams already in E8). F4% = reaching F4. F2% = reaching Championship game. Champ% = winning it all.*

---

## THE OPTIMAL COMPLETE PATH

Brute-force searched all valid 5-team assignments across Days 6-10, maximizing the product of win probabilities. Each team that isn't our pick must independently advance to the round where we pick them.

### How the math works

| Day | Round | What our pick needs | Probability used |
|---|---|---|---|
| 6 | S16 | Just win the S16 game (our pick) | Team's **E8%** |
| 7 | E8 | Already in E8 + win E8 (our pick) | Team's **F4%** |
| 8 | E8 | Win S16 independently + win E8 (our pick) | Team's **F4%** |
| 9 | F4 | Reach F4 independently + win F4 semi (our pick) | Team's **F2%** |
| 10 | Championship | Reach Final independently + win final (our pick) | Team's **Champ%** |

### The Path

| Day | Date | Pick | Round | Opponent | Prob | Why |
|---|---|---|---|---|---|---|
| ~~5~~ | ~~Thu Mar 26~~ | ~~Purdue~~ | ~~S16~~ | ~~Texas (11W)~~ | ~~73.4%~~ | ~~Won 79-77~~ |
| **6** | **Fri Mar 27** | **Michigan St.** | S16 | UConn (2E) | **47.0%** | Toss-up, but frees Michigan for E8 AND Duke for F4 |
| **7** | **Sat Mar 29** | **Illinois** | E8 | Iowa (9S) | **77.0%** | Already in E8, heavy favorite vs 9-seed Iowa |
| **8** | **Sun Mar 30** | **Michigan** | E8 | Midwest E8 | **57.6%** | Michigan must win S16 today (81%) then win E8 (~71%) |
| **9** | **Sat Apr 5** | **Duke** | F4 Semi 1 | E vs S | **37.2%** | Duke must reach F4 (54%) then win semifinal (~69%) |
| **10** | **Mon Apr 7** | **Arizona** | Championship | Final | **22.6%** | Arizona must reach Final (38%) then win title (~59%) |

### Joint Survival Probability

```
  Day 6:  47.0%  (MSU S16)
× Day 7:  77.0%  (Illinois E8 — already in E8, wins vs Iowa)
× Day 8:  57.6%  (Michigan reaches E8 + wins)
× Day 9:  37.2%  (Duke reaches F4 + wins semi)
× Day 10: 22.6%  (Arizona reaches Final + wins title)
─────────────────────────────────
= 1.76% from today
= 0.78% overall (with 44.2% prior)
```

**~1 in 57 from today. ~1 in 129 overall.**

---

## Why This Path Is Optimal

### Houston's loss HELPS us

Illinois replacing Houston on Day 7 is a massive upgrade:
- **Illinois F4%: 77.0%** vs Houston's old F4%: 40.6%
- Illinois just proved they can beat Houston head-to-head (65-55)
- The path went from 0.55% to 1.76% — a **3.2x improvement**

### The key insight: MSU on Day 6 (still holds)

Picking **MSU (47%)** on Day 6 instead of Michigan (81%) loses ~34 points on Day 6, but:

- **Frees Michigan for Day 8 E8** (57.6%) instead of needing MSU/Tennessee (15.3%/9.8%)
- **Frees Duke for Day 9 F4** (37.2%) instead of needing Illinois/MSU (36.5%/6.7%)
- **Preserves Arizona for Day 10 Championship** (22.6%) instead of Michigan (20.6%)

The downstream gains (Michigan 57.6% × Duke 37.2% × Arizona 22.6%) massively outperform the alternative.

### Top 5 paths compared

| Rank | Path (D6→D7→D8→D9→D10) | Product |
|---|---|---|
| **1** | **MSU → Illinois → Michigan → Duke → Arizona** | **1.755%** |
| 2 | MSU → Illinois → Michigan → Arizona → Duke | 1.689% |
| 3 | Tennessee → Illinois → Michigan → Duke → Arizona | 1.324% |
| 4 | MSU → Arizona → Duke → Illinois → Michigan | 1.305% |
| 5 | Tennessee → Illinois → Michigan → Arizona → Duke | 1.274% |

The #1 and #2 paths differ only in Duke/Arizona ordering for Days 9/10. We pick **Duke D9 + Arizona D10** because Duke has the higher Day 9 probability (37.2% vs 38.2%... actually close). The real reason: Duke's F2% (37.2%) × Arizona's Champ% (22.6%) = 8.41%, vs Arizona's F2% (38.2%) × Duke's Champ% (21.2%) = 8.10%.

---

## Day-by-Day Detail

### Day 5 — Thu Mar 26: PURDUE vs Texas — WON 79-77

Purdue survived a scare against 11-seed Texas. Tramon Mark led with 29 points. FanMatch had it at 75% pre-game. Close game but our pick held.

### Day 6 — TODAY Fri Mar 27: MICHIGAN ST. vs UConn

**Consensus: 47.0%** | FanMatch: 51% (70-69)

MSU (3E) vs UConn (2E). True toss-up. MSU beat Louisville 77-69 in R32, UConn beat UCLA 73-57. UConn is the higher seed but has been faded all tournament (0.92 sentiment). MSU's Coen Carr (21p/10r/2b) has been excellent.

MSU injury: Glenn OUT (knee, season), Ugochukwu OUT (foot, season) — both out for season, team has adjusted.
UConn injury: None significant.

**This is the riskiest single-day pick.** But picking Michigan (81%) here and losing Michigan for Day 8 costs far more in expected value. The brute-force search confirms every alternative to MSU on Day 6 produces a worse overall product.

### Day 7 — Sat Mar 29: ILLINOIS vs Iowa (E8 South)

**Illinois already in E8. Wins E8 = F4%: 77.0%**

Illinois (3S) just upset Houston 65-55 in a dominant defensive performance. Now faces Iowa (9S) who upset Florida and Nebraska. Illinois is heavily favored — 3 of 4 sources give them 70%+ to win this E8 game.

Illinois injury: Rodgers OUT (knee) — rotation wing, but team proved depth vs Houston.

This is a massive upgrade from the old path (Houston 40.6%).

### Day 8 — Sun Mar 30: MICHIGAN (E8 Midwest)

**Requires: Michigan wins S16 today (81.3%) + wins E8 Sunday (~71%)**
**Joint: 57.6%**

Michigan (1MW) must beat Alabama today (heavily favored at 81%, FanMatch 76%), then beat Iowa St./Tennessee in the Midwest E8. Michigan has been the most dominant team in the tournament (101-80 R64, 95-72 R32).

Michigan injury: Grady OUT (lower leg), L.J. Cason OUT (knee, season) — rotation depth hit but core intact.

### Day 9 — Sat Apr 5: DUKE (F4 Semi 1: East vs South)

**Requires: Duke wins S16 (74.5%) + wins E8 (~73%) + wins F4 semi (~69%)**
**Joint: 37.2%**

Duke must independently advance through the East bracket to reach the Final Four, then beat the South representative (likely Illinois, our Day 7 pick). Duke has been dominant (71-65 R64, 81-58 R32) and is the consensus co-favorite.

Duke injury: Foster GTD (foot, upgraded from OUT), Ngongba GTD (undisclosed).

### Day 10 — Mon Apr 7: ARIZONA (Championship)

**Requires: Arizona wins E8 (68.2%) + wins F4 semi (~56%) + wins final (~59%)**
**Joint: 22.6%**

Arizona must independently advance through the West bracket (beat Purdue in E8), win Semi 2 (vs Michigan most likely, our Day 8 pick), then beat the Semi 1 winner (Duke most likely, our Day 9 pick) in the Championship.

Arizona is the #1 overall seed. Their 22.6% Championship probability is the highest available for Day 10 from Semi 2 teams. Michigan (20.6%) is close but needed on Day 8.

---

## Survival Tracker

| Day | Pick | Win% | Cumulative | Status |
|---|---|---|---|---|
| 1 | Gonzaga | 96.0% | 96.0% | Won |
| 2 | UConn | 96.0% | 92.2% | Won |
| 3 | Arkansas | 87.0% | 80.2% | Won |
| 4 | Iowa St. | 75.0% | 60.2% | Won |
| 5 | Purdue | 73.4% | 44.2% | Won |
| **6** | **Michigan St.** | **47.0%** | **20.8%** | **TODAY** |
| 7 | Illinois | 77.0% | 16.0% | Sat Mar 29 |
| 8 | Michigan | 57.6% | 9.2% | Sun Mar 30 |
| 9 | Duke | 37.2% | 3.4% | Sat Apr 5 |
| 10 | Arizona | 22.6% | **0.78%** | Mon Apr 7 |

---

## What Kills This Path

| Event | Probability | Impact |
|---|---|---|
| MSU loses to UConn today | 53% | Eliminated Day 6 |
| Illinois loses to Iowa Saturday | 23% | Eliminated Day 7 |
| Michigan doesn't reach E8 | 19% | Eliminated Day 8 |
| Duke doesn't reach F4 | 46% | Eliminated Day 9 |
| Arizona doesn't win Championship | 77% | Eliminated Day 10 |

**The most likely failure point is Day 6 (MSU, 53% to fail).** If MSU wins today, the remaining path is strong — Days 7-8 are both above 50%.

---

## Data Sources (Updated 2026-03-27)

- **Torvik (T-Rank):** `data/torvik_proj.csv` (12 remaining teams, post-S16 S/W update)
- **KenPom:** `data/kenpom_proj.csv` (pre-S16, reconditioned for S/W teams already in E8)
- **Evan Miya:** `data/miya_proj.csv` (12 teams, updated post-S16)
- **CBB Analytics:** `data/cbb_proj.csv` (12 teams, updated post-S16)
- **FanMatch:** `schedule.txt` (game-day win probabilities)
- **Injuries:** `data/college-basketball-injury-report.csv`
  - Duke: Foster GTD (foot), Ngongba GTD (undisclosed)
  - Michigan: Grady OUT (lower leg), L.J. Cason OUT (knee, season)
  - Michigan St.: Glenn OUT (knee, season), Ugochukwu OUT (foot, season)
  - Alabama: Holloway GTD (susp) + Bristow/Hannah/Onyejiaka/Bediako OUT
  - Illinois: Rodgers OUT (knee)
  - Tennessee: Phillips OUT (shoulder, season)
  - Iowa: McCollum OUT (foot, season)
