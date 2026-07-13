---
type: strategy
tags: [strategy, walk-forward, overfitting, case-study]
created: 2026-07-13
updated: 2026-07-13
source: [backtest/results/phase_b_final_report.md, README.md]
---

# Phase B Walk-Forward

The [[Overfitting]] case study that justifies the entire validation discipline. Tuned parameters on three sequential training windows, locked the ruleset, then tested once on an untouched holdout. Generated 2026-05-18. Final decision: **REVERT_TO_BASELINE**.

## Rules snapshot
- **Training windows** (2023–2024): W1 tuned `score_threshold` → keep baseline; W2 tuned `stop_tightness` → keep baseline (−7%); W3 tuned `position_sizing` → adopted `conservative_100_70_40`
- **Locked holdout**: Nov 2024 – Apr 2025, no tuning
- **Revert trigger**: holdout return < 70% of training average

## Results
| Metric | Value |
|---|---|
| Training avg (3 windows) | **+9.62%** |
| Holdout return | **−6.57%** |
| Holdout / training ratio | **−68.3%** (threshold −70% → revert) |
| Holdout trades | 21 |
| Holdout win rate | **28.6%** (vs 50–74% training) |
| Holdout max drawdown | **−16.61%** |
| Holdout Nifty | +0.12% |
| Holdout alpha | **−6.69%** |

The README frames it as: POC v2 showed **+6.66% alpha in-sample**; the holdout showed **−6.57% return / −6.69% alpha** → overfit, revert.

## Verdict
**A successful walk-forward — because it said no.** It correctly caught that the parameters were fit to a mostly-bull training period and prevented bad rules from reaching production. No rule changes recommended; no changes until 20+ forward trades are logged. Live [[Swing v3]] (win 44.4%, alpha ≈ −2.96%) then confirmed the warning. Compare its siblings: [[Sector Rotation Experiment]] and [[Mean Reversion Experiment]], both also reverted.

Related: [[POC v2 Backtest]] · [[Walk-Forward Validation]] · [[Overfitting]] · [[Strategy Verdict]]
