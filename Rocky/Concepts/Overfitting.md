---
type: concept
tags: [concept, validation, methodology, lesson]
created: 2026-07-13
updated: 2026-07-13
source: [backtest/results/phase_b_final_report.md, README.md]
---

# Overfitting

## Definition
When a strategy's parameters are tuned so tightly to historical data that they capture noise instead of a durable edge — dazzling in-sample, worthless out-of-sample. The central failure mode Rocky's whole [[Walk-Forward Validation]] apparatus exists to catch.

## Exact rule
Operationalized as the holdout ratio test: if a tuned ruleset's holdout return is **< 70% of its training average**, declare it overfit and revert. No fuzzy judgement.

## Implementation
Detected by the walk-forward validator in `backtest/engine/`; the decision string (`REVERT_TO_BASELINE`) is written to `backtest/results/*_report.md`.

## In practice
The textbook case is [[Phase B Walk-Forward]]: POC v2 showed **+6.66% alpha** in-sample (May–Oct 2025), but the locked holdout (Nov 2024 – Apr 2025) delivered **−6.57% return / −6.69% alpha**, win rate collapsing from 50–74% to 28.6% and drawdown blowing out to −16.61%. Diagnosis: parameters were fit to a mostly-bull 2023–24 training window. README lesson #2: "Backtest results don't transfer unless walk-forward says so." Forward live trading confirmed it.

Related: [[Walk-Forward Validation]] · [[POC v2 Backtest]] · [[Phase B Walk-Forward]] · [[Strategy Verdict]]
