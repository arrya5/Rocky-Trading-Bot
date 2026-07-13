---
type: insight
tags: [insight, verdict, thesis, strategy, evaluation]
created: 2026-07-13
updated: 2026-07-13
source: [README.md, backtest/results/poc_report.md, backtest/results/phase_b_final_report.md, memory/trade-outcomes.json, memory/WEEKLY-REVIEW.md, memory/goal.yaml]
---

# Strategy Verdict

The central thesis of this vault, stated plainly:

> **The infrastructure is the asset. The strategy was the experiment — and it failed honestly.**

Rocky set out to prove a mechanical momentum edge on NSE mid/large caps. It did not find one. But it built the machine that could *tell* it there was no edge — and that machine, not the strategy, is what carries forward. A failed experiment reported honestly is a working measuring instrument.

## The evidence chain

The strategy's decline is fully traceable, in order, through four documented stages:

1. **In-sample looked great.** [[POC v2 Backtest]] over May–Oct 2025 returned +12.31% vs Nifty +5.65% → **+6.66% alpha**, 73.3% win rate across 15 trades. Enough to make the ruleset *look* validated.
2. **Walk-forward said no.** [[Phase B Walk-Forward]] locked those parameters and tested them once on an untouched Nov 2024–Apr 2025 holdout: **−6.57% return / −6.69% alpha**, win rate collapsing to 28.6%, drawdown blowing out to −16.61%. Holdout/training ratio −68.3%, tripping the −70% revert rule → `REVERT_TO_BASELINE`. Diagnosis: [[Overfitting|overfit]] to a mostly-bull training window.
3. **Live forward confirmed the walk-forward.** [[Swing v3]] ran live in paper mode from 2026-05-20. Nine closed trades: **44.4% win rate** (4W / 5L), **−2.96% all-time**, weekly self-grade **D**, [[Fitness Score]] **−0.768 / 1.0**, expected value **≈ −2.09%/trade**. Avg winner ~+2.15% against avg loser ~−5.27% — losers roughly 2.5× the size of winners. The [[Walk-Forward Validation]] warning was not a false alarm; live results landed exactly where it pointed.
4. **The category, not the rule, was wrong.** Two sibling strategy classes ran the same gauntlet and both reverted: [[Sector Rotation Experiment]] (train +31.08% → holdout −9.69%) and [[Mean Reversion Experiment]] (POC alpha −9.59% despite a 60%+ win rate). Three mechanical approaches, three collapses out-of-sample. The lesson is not "this strategy was miscalibrated" — it is "**mechanical momentum on NSE midcaps may have no durable edge.**"

## What is *not* proven

Every mechanical-edge hypothesis Rocky tested came back negative. The +5%/30d goal in `goal.yaml` was, in retrospect, mathematically unreachable under a delivery-only, long-only, no-F&O mandate — so it graded every honest result as failure.

## What *is* proven

The self-evaluating machinery worked — and that is the durable output:

- **Enforcement**: the [[9-Point Buy Gate]] and [[Regime Detection]] gate ran with zero discretion across all nine live entries.
- **Validation**: [[Walk-Forward Validation]] rejected three overfit strategies before they could reach production, and its verdict held up live.
- **Self-grading**: the [[Fitness Score]] against a fixed `goal.yaml` contract flagged the strategy's own failure (grade D) instead of rationalizing it.
- **Auditability**: every routine committed `memory/` to Git, so any trading day is replayable and every claim on these pages is traceable to a raw source.

Because the measuring instrument was built *before* betting on a strategy, the strategy is swappable without rebuilding anything. That portability — swap the runner and the ruleset, keep the instrument — is the design pattern the project actually proved. See [[Infrastructure Eras]].

## Bottom line

Rocky is a **success as an engineering artifact and a null result as a trading strategy**, and it is honest enough to say so itself. The next iteration should test an AI-reasoning-driven approach — where the edge is the reasoning, not the rule — against a realistic +1.5–2%/month bar, on the same instrument.

Related: [[Lessons Learned]] · [[Open Questions]] · [[Swing v3]] · [[POC v2 Backtest]] · [[Phase B Walk-Forward]] · [[Fitness Score]] · [[Timeline]]
