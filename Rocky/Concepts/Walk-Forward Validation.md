---
type: concept
tags: [concept, validation, backtest, methodology]
created: 2026-07-13
updated: 2026-07-13
source: [backtest/results/phase_b_final_report.md, README.md]
---

# Walk-Forward Validation

## Definition
The anti-[[Overfitting]] discipline: tune parameters on historical training windows, then lock the ruleset and test it once on a completely untouched holdout period. If holdout performance collapses relative to training, the apparent edge was curve-fit and the rules are reverted.

## Exact rule
Rule of thumb applied in [[Phase B Walk-Forward]]: **revert to baseline if holdout return < 70% of the training average.** Three sequential training windows (2023–2024), one locked 6-month holdout (Nov 2024 – Apr 2025), zero tuning during holdout.

## Implementation
`backtest/engine/` walk-forward validator; configs in `backtest/config/phase_b_config.json`. Reports land in `backtest/results/*_report.md`.

## In practice
Run three times, it earned its keep every time by **rejecting** strategies:
- [[Phase B Walk-Forward]] (swing): training +9.62% → holdout −6.57%, ratio −68.3% → revert
- [[Sector Rotation Experiment]]: training +31.08% → holdout −9.69%, ratio −31.2% → revert
- [[Mean Reversion Experiment]]: POC alpha −9.59%, never even survived to production

Forward live results (win 44.4%, alpha ≈ −2.96%) later **confirmed** the walk-forward's warning — the headline README lesson is "trust the walk-forward, not the in-sample."

Related: [[Overfitting]] · [[POC v2 Backtest]] · [[Phase B Walk-Forward]]
