# POC — Smaller Position Tiers Experiment

_Generated: 2026-05-18T20:00:58_

## Setup

- Starting capital: **Rs 500,000** (same as baseline POC)
- Tier sizes: **Rs 55,000 / Rs 35,000 / Rs 20,000** (baseline used 70k/50k/30k)
- Window: 2025-05-01 -> 2025-10-31

## Hypothesis

In baseline POC, 836 candidates were rejected for 'insufficient cash' — meaning Rocky's rules said BUY but capacity was full. 
Smaller positions should free up capital sooner, allowing more concurrent trades. 

- If win rate stays similar -> cash constraint was artificial scarcity, smaller tiers are better
- If win rate drops significantly -> original tier sizes were doing useful quality filtering

## Headline comparison (smaller tiers vs baseline)

| Metric | Smaller tiers (this) | Baseline POC | Δ |
|---|---|---|---|
| Total trades | **25** | 15 | +10 |
| Win rate | 68.0% | 73.3% | -5.3pp |
| Avg winner | +10.47% | +11.02% | -0.55pp |
| Avg loser | -5.86% | -4.34% | — |
| Total Rs P&L | **Rs 54,363** | Rs 61,570 | -7,207 |
| Total Rs deployed | Rs 1,111,706 | (capacity-capped ~5L) | — |
| Return on deployed | +4.89% | ~12% | — |
| Return on starting | **+11.02%** | +12.31% | -1.29pp |
| Max concurrent positions | 14 | 11 | +3 |
| Avg concurrent positions | 12.7 | — | — |
| Partial exits fired | 9 | 5 | +4 |

## Skip-log breakdown

| Reason | This run | Baseline |
|---|---|---|
| gate6_insufficient_cash | 533 | 836 |
| gate9_sector_full | 370 | 171 |
| gate4_circuit_gap | 0 | 0 |
| macro_skip | 0 | 0 |

## Sector concentration that actually happened

Max simultaneous open positions per sector (Gate 9 cap = 2):

| Sector | Max simultaneous | At cap? |
|---|---|---|
| Auto | 2 | **YES** |
| Banking | 2 | **YES** |
| Energy | 2 | **YES** |
| Finance | 2 | **YES** |
| FMCG | 2 | **YES** |
| Infrastructure | 2 | **YES** |
| Pharma | 2 | **YES** |
| IT | 2 | **YES** |
| Telecom | 1 |  |
| Other | 1 |  |
| Consumer | 1 |  |

## Regime-at-entry breakdown

| Regime | Trades | Wins | Win % | Avg P&L |
|---|---|---|---|---|
| bull | 18 | 15 | 83% | +8.21% |
| sideways | 6 | 2 | 33% | -1.58% |
| bear | 1 | 0 | 0% | -7.18% |

## Score-band breakdown

| Score band | Trades | Wins | Win % | Avg P&L |
|---|---|---|---|---|
| 40-59 | 0 | - | - | - |
| 60-79 | 11 | 8 | 73% | +6.52% |
| 80-100 | 14 | 9 | 64% | +4.25% |

## Caveats

- **Fixed brokerage hurts smaller positions more**: Rs 20/order is 0.10% of a Rs 20k position vs 0.029% of a Rs 70k position. Real costs erode small-position returns more.
- **Same single regime (May-Oct 2025)**: can't generalize to other market conditions yet.
- **Same gates skipped**: 3 (catalyst), 8 (earnings).
