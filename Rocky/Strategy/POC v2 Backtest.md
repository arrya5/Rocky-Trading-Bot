---
type: strategy
tags: [strategy, backtest, poc, in-sample]
created: 2026-07-13
updated: 2026-07-13
source: [backtest/results/poc_report.md, README.md]
---

# POC v2 Backtest

The in-sample proof-of-concept that made the strategy *look* like it worked. Ran the baseline ruleset over a 6-month window with the v2 engine (partial P&L aggregation, gap-down fills, regime tagging). Generated 2026-05-18.

## Rules snapshot
- **Window**: 2025-05-01 → 2025-10-31 (127 trading days), 112-symbol universe, ₹5,00,000 start
- **Rules**: score ≥ 40, ADV ≥ ₹50 Cr, vol ≤ 3.0%, −7% stop, +15% partial, VIX < 25, FII > −₹3,500 Cr
- **Gates enforced**: 1, 2, 4, 5, 6, 7, 9. **Skipped**: 3 (catalyst — LLM lookahead) and 8 (earnings — deferred)

## Results
| Metric | Value |
|---|---|
| Portfolio return | **+12.31%** (₹500,000 → ₹561,570) |
| Nifty 50 | +5.65% |
| **Alpha** | **+6.66%** |
| Closed trades | 15 |
| Win rate | 73.3% (11W / 4L) |
| Avg winner / loser | +11.02% / −4.34% |
| Max drawdown | −3.5% |
| Best / worst | MARUTI +22.75% / PAGEIND −7.18% |

Regime split: bull 91% win (10/11), sideways 0% (0/3), bear 100% (1/1). Score band: 60–79 won 86%, 80–100 won 62%.

## Verdict
**Impressive but not to be trusted.** Six months captures a single (mostly bull) regime; gates 3/7/8 were disabled; survivorship bias present. Its own parameters were then subjected to [[Phase B Walk-Forward]] — which flagged them as [[Overfitting|overfit]]. Live [[Swing v3]] later confirmed the walk-forward, not the POC. Canonical lesson: **trust the walk-forward, not the in-sample.**

Related: [[Phase B Walk-Forward]] · [[Walk-Forward Validation]] · [[Overfitting]] · [[Swing v3]]
