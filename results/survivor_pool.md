# March Madness 2026 — Survivor Pool Strategy

Updated 2026-03-21 (after R64). Pick one team per day to win. Can't reuse a team. One loss = eliminated. Optimized purely for survival probability (consensus model + sentiment + injuries).

---

## Schedule Structure

| Day | Date | Round | Games | Regions |
|---|---|---|---|---|
| 1 | Thu Mar 19 | R64 | 16 | All (Thursday R64) |
| 2 | Fri Mar 20 | R64 | 16 | All (Friday R64) |
| 3 | Sat Mar 21 | R32 | 8 | All (Thursday winners) |
| 4 | Sun Mar 22 | R32 | 8 | All (Friday winners) |
| 5 | Thu Mar 27 | Sweet 16 | 4 | East + South |
| 6 | Fri Mar 28 | Sweet 16 | 4 | West + Midwest |
| 7 | Sat Mar 29 | Elite 8 | 2 | East + South |
| 8 | Sun Mar 30 | Elite 8 | 2 | West + Midwest |
| 9 | Sat Apr 5 | Final Four | 2 | Semi 1 (E vs S) + Semi 2 (W vs MW) |
| 10 | Mon Apr 7 | Championship | 1 | Final |

**Days 1–4** follow the Thursday/Friday track. **Days 5–8** are assigned by region based on semifinal pairings (East/South together, West/Midwest together).

---

## Results So Far

| Day | Pick | Result | Win% | Cumulative |
|---|---|---|---|---|
| 1 | Gonzaga | ✅ Won 73-64 vs Kennesaw St. | 96% | 96.0% |
| 2 | UConn | ✅ Won 82-71 vs Furman | 96% | 92.2% |

**Used teams:** Gonzaga, UConn (cannot pick again)

---

## The Critical Constraint

Our consensus Final Four is **Duke (E) vs Florida/Illinois (S)** and **Arizona (W) vs Michigan (MW)**. On Day 9, only these 4 teams are playing. On Day 10, only 2 teams play. **We MUST save Duke + Michigan + Arizona for Days 9–10.**

Saving 3 teams provides full Day 10 coverage: whichever of Michigan/Arizona wins their semifinal, we have a valid championship pick.

---

## Day 3 — TODAY Sat Mar 21 (R32, Thursday winners)

### Actual R32 matchups after R64 upsets:

| Game | FanMatch | Notes |
|---|---|---|
| Duke vs TCU | Duke 88% | TCU upset Ohio St. Duke still cruises. |
| Michigan vs Saint Louis | Michigan 88% | Saint Louis upset Georgia. Michigan still heavy favorite. |
| Arkansas vs High Point | Arkansas 87% | **High Point upset Wisconsin!** Arkansas got a gift. |
| Illinois vs VCU | Illinois 81% | VCU upset North Carolina. Illinois still strong. |
| Houston vs Texas A&M | Houston 80% | Texas A&M upset Saint Mary's. Houston solid. |
| Gonzaga vs Texas | Gonzaga 68% | Texas upset BYU. Tougher for Gonzaga. (USED) |
| MSU vs Louisville | MSU 59% | Louisville beat USF. Competitive game. |
| Vanderbilt vs Nebraska | Vanderbilt 52% | Toss-up. |

### **PICK: Arkansas (87% vs High Point)**

High Point pulling the 12-over-5 upset of Wisconsin is a gift for us. Arkansas was going to face Wisconsin (~55% win probability) — now they face a 12-seed and FanMatch has them at 87%. Arkansas is completely disposable (they'd face Arizona in S16, ~25% win chance). This is the best non-saved pick available today.

**Why not Houston (80%)?** Arkansas is 7% safer. Both are disposable. Arkansas is the clear call.

**Why not Duke (88%) or Michigan (88%)?** Both are saved for Days 9–10. The 1% gain over Arkansas isn't worth losing championship insurance.

**Why not Illinois (81%)?** Illinois is reserved for Day 7 (South E8). Using Illinois today would leave nobody for Day 7.

---

## Day 4 — Sun Mar 22 (R32, Friday winners)

### R32 matchups:

| Game | FanMatch | Notes |
|---|---|---|
| Arizona vs Utah St. | Arizona 85% | SAVED for Day 10 |
| Iowa St. vs Kentucky | Iowa St. 75% | Save for Day 6 (S16) |
| Florida vs Iowa | Florida 75% | Iowa upset Clemson. Florida still solid. |
| Purdue vs Miami FL | Purdue 73% | Save for Day 8 (E8) |
| UConn vs UCLA | UConn 63% | USED |
| St. John's vs Kansas | St. John's 56% | Coin flip |
| Tennessee vs Virginia | Tennessee 51% | Pure toss-up |
| Alabama vs Texas Tech | Alabama 51% | Pure toss-up |

### **PICK: Florida (75% vs Iowa)**

Florida is the best non-saved, non-essential pick. Iowa upset Clemson but Florida is a 1-seed and FanMatch still has them at 75%.

**Why not Iowa St. (75%)?** Same win% but Iowa St. is needed for Day 6. Using Iowa St. now forces Purdue onto Day 6 (~60%) and leaves Virginia (~45%) for Day 8 — a much worse downstream chain.

**Why not Purdue (73%)?** Purdue is needed for Day 8 (West E8). Using Purdue now leaves nobody for Day 8.

---

## Day 5 — Thu Mar 27 (S16: East + South)

### Expected S16 matchups (bracket-aware):

**East region:**
- East top S16: Duke vs St. John's/Kansas (~70% Duke) — Duke SAVED
- East bottom S16: MSU vs UConn/UCLA (~55-58% MSU) — UConn USED but still playing

**South region:**
- South top S16: Florida vs Nebraska/Vanderbilt (~65% Florida) — Florida USED Day 4
- South bottom S16: Illinois vs Houston (~60% Illinois) — save Illinois for Day 7

### **PICK: Michigan St. (~57%)**

MSU's S16 opponent is UConn or UCLA from the East bottom half — **not Duke** (they don't meet until the E8). MSU is a 3-seed with tournament pedigree. UConn is faded (0.85x sentiment, "weakest 2 seed"). If UCLA upsets UConn tomorrow (~37%), MSU's matchup gets even easier.

This is the toughest pick in the path. But with Duke/Michigan/Arizona saved and Illinois reserved for Day 7, MSU is the best available option.

---

## Day 6 — Fri Mar 28 (S16: West + Midwest)

### Expected S16 matchups:

**West region:**
- West top S16: Arizona vs Arkansas/High Point (~75% Arizona) — Arizona SAVED
- West bottom S16: Gonzaga/Texas vs Purdue (~60% Purdue) — Gonzaga USED, save Purdue for Day 8

**Midwest region:**
- Midwest top S16: Michigan vs Alabama/Texas Tech (~75% Michigan) — Michigan SAVED
- Midwest bottom S16: Iowa St. vs Virginia/Tennessee (~65% Iowa St.)

### **PICK: Iowa St. (~65%)**

Iowa St. has been surging (+3.7% bracket value, Big 12 tourney run). Their S16 matchup is favorable — Virginia and Tennessee are both mediocre (51% toss-up against each other in R32). Iowa St. should handle either.

---

## Day 7 — Sat Mar 29 (E8: East + South)

### Expected E8 matchups:

- **East E8:** Duke vs MSU/UConn — Duke SAVED, MSU USED Day 5
- **South E8:** Florida vs Illinois — Florida USED Day 4, Illinois available

### **PICK: Illinois (~60%)**

This is why we saved Illinois. The South E8 is Florida vs Illinois in our consensus. Illinois is our South region pick — "best kill-shot team" with massive model support. 60% in the E8 is strong. Florida was used Day 4 but is still playing; we just can't pick them.

---

## Day 8 — Sun Mar 30 (E8: West + Midwest)

### Expected E8 matchups:

- **West E8:** Arizona vs Purdue/Gonzaga — Arizona SAVED
- **Midwest E8:** Michigan vs Iowa St. — Michigan SAVED, Iowa St. USED Day 6

### **PICK: Purdue (~40-50%)**

The weakest link in our chain. Purdue faces Arizona (1-seed) in the West E8 — they're the underdog. ~40% if facing Arizona directly, ~50% if the path shakes out differently.

**Contingency:** If Purdue is eliminated in S16 (loses to Gonzaga/Texas on Day 6), we're forced to use Arizona on Day 8 (~60%), which drops our Day 10 from 48.9% to 28.6%. This is the biggest risk in the plan. Monitor Purdue's S16 matchup closely.

---

## Day 9 — Sat Apr 5 (Final Four)

### Semifinal matchups:

- **Semi 1 (E vs S):** Duke vs Florida/Illinois
- **Semi 2 (W vs MW):** Arizona vs Michigan

### **PICK: Duke (~65%)**

This is why we saved Duke all tournament. The East vs South semifinal features Duke against the South winner (Florida or Illinois). Duke is the East's 1-seed with Ngongba expected back. 65% is a premium F4 pick.

---

## Day 10 — Mon Apr 7 (Championship)

### **PICK: Michigan (~52%) or Arizona (~45%)**

The payoff of the triple save. After Duke wins Semi 1, the championship is Duke vs the winner of Arizona/Michigan:
- **Michigan wins semi (55%):** Pick Michigan, wins championship ~52%. Contributes 28.6%.
- **Arizona wins semi (45%):** Pick Arizona, wins championship ~45%. Contributes 20.3%.
- **Day 10 expected survival: 48.9%**

Without the triple save (Path B), 45% of the time Arizona wins the semi and we'd have no valid pick. The triple save eliminates that death scenario.

---

## Updated Survival Probability (Path A — Triple Save)

| Day | Pick | Opponent | Win% | Cumulative | Status |
|---|---|---|---|---|---|
| 1 | Gonzaga | Kennesaw St. | 96.0% | 96.0% | ✅ Won |
| 2 | UConn | Furman | 96.0% | 92.2% | ✅ Won |
| 3 | **Arkansas** | **High Point** | **87.0%** | **80.2%** | **TODAY** |
| 4 | Florida | Iowa | 75.0% | 60.2% | Tomorrow |
| 5 | Michigan St. | UConn/UCLA | 57.0% | 34.3% | Mar 27 |
| 6 | Iowa St. | Virginia/Tennessee | 65.0% | 22.3% | Mar 28 |
| 7 | Illinois | Florida | 60.0% | 13.4% | Mar 29 |
| 8 | Purdue | Arizona-side | 45.0% | 6.0% | Mar 30 |
| 9 | Duke | South winner | 65.0% | 3.9% | Apr 5 |
| 10 | Michigan/Arizona | vs Duke | 48.9% | **~1.9%** | Apr 7 |

**~1.9% overall survival.** Up from the original 1.86% estimate thanks to the Arkansas upgrade on Day 3 (87% vs original Houston at 75%).

---

## Comparison: What Changed from Pre-Tournament Plan

| Day | Original Pick (Win%) | Updated Pick (Win%) | Change |
|---|---|---|---|
| 1 | Gonzaga (96%) | Gonzaga (96%) ✅ | — |
| 2 | UConn (96%) | UConn (96%) ✅ | — |
| 3 | Houston (75%) | **Arkansas (87%)** | **+12%** High Point upset gift |
| 4 | Florida (75%) | Florida (75%) | Same (Iowa instead of Clemson) |
| 5 | MSU (58%) | MSU (57%) | ~Same |
| 6 | Iowa St. (65%) | Iowa St. (65%) | Same |
| 7 | Illinois (60%) | Illinois (60%) | Same |
| 8 | Purdue (50%) | Purdue (45%) | -5% (path may be tougher) |
| 9 | Duke (65%) | Duke (65%) | Same |
| 10 | Mich/AZ (49%) | Mich/AZ (49%) | Same |

The biggest gift from the R64 upsets: Arkansas's R32 opponent went from Wisconsin (would have been ~55%) to High Point (87%). Duke also benefited (TCU instead of Ohio St., 88% either way).

---

## Key Contingencies to Monitor

1. **MSU vs Louisville (TODAY):** If MSU loses, Day 5 gets harder. Backup Day 5 pick would be Houston (~55% in S16) — weaker but viable.
2. **UConn vs UCLA (Tomorrow):** If UCLA upsets UConn, MSU's Day 5 S16 matchup improves (UCLA easier than UConn).
3. **Purdue vs Miami FL (Tomorrow):** If Purdue loses, Day 8 collapses. We'd be forced into Arizona Day 8, converting to a 2-save and losing ~0.5% overall survival.
4. **Gonzaga vs Texas (TODAY):** If Texas upsets Gonzaga, Purdue's S16 path changes (faces Texas instead of Gonzaga — probably easier for Purdue).
5. **Iowa St. vs Kentucky (Tomorrow):** If Iowa St. loses, Day 6 falls to Purdue (~60%) and Day 8 to Virginia (~45%). Significant downgrade.
