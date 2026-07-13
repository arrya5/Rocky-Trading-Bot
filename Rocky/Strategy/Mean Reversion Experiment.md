---
type: strategy
tags: [strategy, mean-reversion, experiment, rejected]
created: 2026-07-13
updated: 2026-07-13
source: [backtest/results/meanrev_poc_summary.json, backtest/results/meanrev_holdout_summary.json]
---

# Mean Reversion Experiment

A counter-trend alternative to momentum — buy oversold, sell the bounce — tested as a candidate strategy class. Signal logic in `backtest/engine/mean_reversion_signal_generator.py`, run via `backtest/run_mean_reversion.py`. **Rejected.**

## Rules snapshot
- Counter-trend entries on the Nifty 50 + Midcap 150 universe (mean-reversion signal generator, distinct from the momentum [[Swing Score]])
- Same portfolio engine, ₹5,00,000 base, evaluated over the standard POC and holdout windows

## Results
| Window | Trades | Win rate | Return | Nifty | Alpha |
|---|---|---|---|---|---|
| POC (2025-05 → 10) | 120 | **60.83%** | **−3.94%** | +5.65% | **−9.59%** |
| Holdout (2024-11 → 2025-04) | 56 | **64.29%** | **−0.63%** | +0.12% | **−0.75%** |

## Verdict
**Rejected — the classic mean-reversion trap.** A *high* win rate (60–64%) paired with a *negative* return: many small wins wiped out by a few large losses, and negative alpha in both windows. Reverting-to-the-mean picked pennies but couldn't beat buy-and-hold. One of three strategy classes (with position trading and [[Sector Rotation Experiment]]) that all collapsed — evidence the *category* of mechanical NSE-midcap edge is the problem, not the specific rule.

Related: [[Sector Rotation Experiment]] · [[Swing v3]] · [[Walk-Forward Validation]] · [[Strategy Verdict]]
