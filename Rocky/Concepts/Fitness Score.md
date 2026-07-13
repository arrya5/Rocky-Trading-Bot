---
type: concept
tags: [concept, evaluation, self-grading, goal]
created: 2026-07-13
updated: 2026-07-13
source: [memory/goal.yaml, README.md]
---

# Fitness Score

## Definition
The single machine-readable measure of whether the strategy is working, defined in `goal.yaml` and computed by `scripts/score.py`. It lets Rocky grade itself honestly against a fixed contract rather than a moving narrative.

## Exact rule
From `goal.yaml`:
- `target_return_30d: 0.05` — +5% absolute per 30 days
- `beat_nifty_by: 0.01` — +1pp/week alpha vs Nifty 50
- `max_drawdown: 0.10` — red-flag above 10% portfolio drawdown
- `failure_below: -0.04` — fitness floor; steeply negative below this realized return
- `min_sharpe: 1.0` — risk-adjusted quality bar
- `reflection_every: 20` closed trades before any rule change; `one_variable_only: true`
- `auto_revert_if_worse: true` — a change that worsens fitness is reverted

## Implementation
`scripts/score.py` (reads `goal.yaml`), surfaced weekly by `scripts/runners/weekly_review.py`.

## In practice
The live run self-graded **fitness −0.875 / 1.0** with a weekly grade of **D** — the system correctly flagged its own failure rather than rationalizing it. Retrospective lesson (README): the +5%/30d target was mathematically unreachable under a delivery-only, long-only, no-F&O mandate, so it made every honest result look like failure; the next iteration should set a realistic +1.5–2%/month bar.

Related: [[Fitness Score]] links → [[Swing v3]] · [[Walk-Forward Validation]] · [[Strategy Verdict]]
