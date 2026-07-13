---
type: strategy
tags: [strategy, sector-rotation, experiment, rejected]
created: 2026-07-13
updated: 2026-07-13
source: [backtest/results/sector_phase_b_report.md, README.md]
---

# Sector Rotation Experiment

A top-down alternative — hold the strongest NSE sectors and rotate on a fixed cadence — put through the same [[Walk-Forward Validation]] gauntlet. Generated 2026-05-19. Final decision: **REVERT_TO_BASELINE**.

## Rules snapshot
- Rank sectors, hold the top-N, rebalance periodically. Baseline: `top_n=3`, `rebalance_freq_days=21`, `lookback_days=21`
- Three training windows tuned `top_n`, `rebalance_freq`, and `lookback`; ruleset locked for holdout

## Results
| Metric | Value |
|---|---|
| Training avg (3 windows) | **+31.08%** |
| Holdout return | **−9.69%** |
| Holdout / training ratio | **−31.2%** |
| Holdout trades | 4 |
| Holdout win rate | **25.0%** |
| Holdout max drawdown | **−18.06%** |
| Holdout Nifty | +0.00% |
| Holdout alpha | **−9.69%** |

## Verdict
**Rejected — the most spectacular overfit of the set.** Training looked like a hedge-fund dream (+31%); the holdout gave −9.69% off just 4 trades at 25% win rate — the widest train-to-holdout gap Rocky measured. The tiny holdout trade count also makes the "edge" statistically hollow. Do not adopt; production stays on [[Swing v3]]. Third confirmation (with [[Position Trading v1]] and [[Mean Reversion Experiment]]) that mechanical edges here don't survive out-of-sample.

Related: [[Mean Reversion Experiment]] · [[Phase B Walk-Forward]] · [[Overfitting]] · [[Strategy Verdict]]
