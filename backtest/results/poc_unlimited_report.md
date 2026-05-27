# POC — Unlimited Capital Experiment

_Generated: 2026-05-18T19:49:36_

## Setup

- Starting capital: **Rs 100,000,000** (vs Rs 5,00,000 in baseline POC)
- Same rules, same window (2025-05-01 -> 2025-10-31)
- Gate 9 (sector cap = 2) STILL ENFORCED -> max ~28 concurrent positions
- Real-world caveat: market impact NOT modeled. Real returns at this scale would be 0.5-2% worse.

## Headline numbers

| Metric | Unlimited (this) | Baseline ₹5L POC | Multiplier |
|---|---|---|---|
| Total trades closed | **53** | 15 | 3.5x |
| Win rate | 50.9% | 73.3% | — |
| Total ₹ P&L | **Rs 91,899** | Rs 61,570 | 1.5x |
| Total ₹ deployed | Rs 3,332,987 | — | — |
| Return on deployed capital | **+2.76%** | ~12% | — |
| Total return on starting | +0.09% | +12.31% | — |
| Max concurrent positions | 26 | 11 | — |
| Avg concurrent positions | 22.4 | — | — |
| Partial exits fired | 17 | 5 | — |

## What this tells us

### 1. Cash constraint cost vs Gate 9 binding rate

| Skip reason | Unlimited run | Baseline ₹5L run |
|---|---|---|
| gate6_insufficient_cash | 0 | 836 |
| gate9_sector_full | 691 | 171 |
| gate4_circuit_gap | 0 | — |
| macro_skip_vix_or_fii | 0 | — |

If sector-full count exploded, Gate 9 is now the binding constraint — cash was just the most visible cap.

### 2. Win-rate / per-rupee return — did edge survive scaling?

- Baseline ₹5L POC: 73.3% win rate, ~12% return on deployed capital
- Unlimited: 50.9% win rate, +2.76% return on deployed

If per-rupee return is similar (~12%), the strategy edge is consistent — cash was just an artificial cap.
If per-rupee return dropped significantly, the additional trades are LOWER quality (marginal signals)
and the cash constraint was acting as a useful quality filter.

### 3. Sector concentration that actually happened

Max simultaneous open positions per sector (Gate 9 capped at 2):

| Sector | Max simultaneous | At cap? |
|---|---|---|
| Auto | 2 | **YES** |
| Banking | 2 | **YES** |
| Energy | 2 | **YES** |
| Finance | 2 | **YES** |
| FMCG | 2 | **YES** |
| Infrastructure | 2 | **YES** |
| Pharma | 2 | **YES** |
| Chemicals | 2 | **YES** |
| Consumer | 2 | **YES** |
| Metals | 2 | **YES** |
| Logistics | 2 | **YES** |
| IT | 2 | **YES** |
| Fin Services | 2 | **YES** |
| Telecom | 1 |  |
| Other | 1 |  |

### 4. Regime-at-entry — does the pattern hold with more trades?

| Regime | Trades | Wins | Win % | Avg P&L |
|---|---|---|---|---|
| bull | 33 | 20 | 61% | +4.55% |
| sideways | 19 | 7 | 37% | +1.14% |
| bear | 1 | 0 | 0% | -7.15% |

In the ₹5L POC, sideways regime trades were 0/3. With more samples, does that hold?

### 5. Score-band — does score 60-79 still beat 80-100?

| Score band | Trades | Wins | Win % | Avg P&L |
|---|---|---|---|---|
| 40-59 | 0 | - | - | - |
| 60-79 | 16 | 12 | 75% | +7.21% |
| 80-100 | 37 | 15 | 41% | +1.34% |

## Important caveat

This experiment is a **diagnostic**, not a strategy recommendation. The ₹91,899 P&L is mathematical not realistic:

- **Market impact ignored**: ₹100,000,000 deployed across 43 unique stocks would move prices on entry and exit. Real fills would be 0.5-2% worse, eroding 5-20% of the displayed P&L.
- **Liquidity ignored**: Some midcap stocks in this universe trade only ₹50 Cr/day — the ADV filter. A ₹3-5cr position in those stocks IS the daily volume.
- **Cost model is partial**: stamp duty, exchange fees, GST not included. These hurt more at scale due to ₹ amounts.

**Honest interpretation:** Use return ON DEPLOYED CAPITAL (+2.76%) — not total return (+0.09%) — when comparing to the ₹5L baseline. The fair scaling question is 'per rupee invested,' not 'per rupee started.'
