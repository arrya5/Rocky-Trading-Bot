---
type: insight
tags: [insight, lessons, retrospective]
created: 2026-07-13
updated: 2026-07-13
source: [README.md, memory/trade-outcomes.json, memory/TRADE-LOG.md, backtest/results/phase_b_final_report.md, memory/goal.yaml]
---

# Lessons Learned

Distilled from the README retrospective and what the nine live trade pages actually show. Each lesson is one bold claim plus the evidence behind it. Losses are recorded as plainly as wins — see [[Strategy Verdict]].

**Trust the walk-forward, not the in-sample.**
[[POC v2 Backtest]] posted +12.31% / +6.66% alpha in-sample; [[Phase B Walk-Forward]] then showed −6.57% on a locked holdout, and live [[Swing v3]] confirmed the holdout, not the POC. In-sample backtests lie because they can be fit to a single (mostly bull) regime. See [[Overfitting]].

**The category was wrong, not just the parameters.**
Three mechanical strategy classes — [[Position Trading v1]], [[Swing v3]], [[Sector Rotation Experiment]], plus the [[Mean Reversion Experiment]] — all collapsed out-of-sample. When every variant of an approach fails the same way, the edge you're hunting probably isn't there. The next system should test AI-reasoning-driven decisions rather than another mechanical rule.

**Time-based exits dominated — and that's a warning.**
Six of the nine trades closed on the 15-trading-day **max_hold** limit, not on conviction or a profit target. Momentum that needs three weeks to *not* resolve was never really momentum. When your dominant exit reason is "the clock ran out," the entry signal isn't finding real thrust. See [[JSWSTEEL-2026-05-20]], [[BAJAJ-AUTO-2026-05-20]], [[HINDALCO-2026-05-21]].

**A hard stop can be gapped through — a time exit realizes more damage than the stop's floor.**
[[MANAPPURAM-2026-05-20]] force-closed at −7.0%, worse than the intended −5% [[Hard Stop]] floor, because the max_hold exit fired on a day price had already gapped below the stop level. A stop is a *ceiling on intended loss*, not a guarantee; overnight gaps and time-based force-closes both defeat it.

**A flawless catalyst is a reason to enter, not to override the stop.**
[[BHARTIARTL-2026-05-20]] carried the batch's best fundamental story (record revenue, 80 [[Swing Score]], analyst Overweight) and still bled to a −5.24% [[Hard Stop]] — the largest rupee loss of the cohort. The [[Catalyst Tiers|HARD catalyst]] justified the trade; discipline justified the exit. Both worked as designed.

**The score mis-ranked conviction.**
The cohort's best trade, [[BAJAJ-AUTO-2026-05-20]], came from a *minimum* 40 [[Swing Score]], while three 80-score entries ([[BHARTIARTL-2026-05-20]], [[MANAPPURAM-2026-05-20]], [[HINDALCO-2026-05-21]]) all lost. A 5-factor binary score that inverts conviction on this sample is not measuring what it claims to.

**The partial-exit rule helped the one time it fired — and near-misses were costly.**
[[BAJAJ-AUTO-2026-05-20]] was the only trade to reach the +6% [[Partial Exit]] trigger; banking half locked in gains before the fade. [[HINDALCO-2026-05-21]] topped at +5.65%, just short of the trigger, and that unrealized +5.65% became a realized −5.53%. A profit-lock that almost never engages barely protects the book.

**Build the measuring instrument before betting on the strategy.**
Because the gates, [[Regime Detection]], [[Walk-Forward Validation]], [[Fitness Score]] and the Git audit trail existed first, the failing strategy could be graded honestly (self-grade **D**) and swapped without a rebuild. The engineering is the asset; the strategy is the experiment.

**Never let an LLM failure silently change behavior — keep a deterministic floor.**
The Gemini catalyst classifier hit its quota and its failure path returned `SOFT` for everything, silently auto-rejecting every trade for days. Fixed with a keyword-based fallback. Any AI dependency needs a deterministic backstop so a quiet failure can't masquerade as a decision.

**Grade against a real bar, not an aspirational one.**
The `goal.yaml` +5%/30d target was unreachable under a delivery-only, long-only, no-F&O mandate, so the [[Fitness Score]] labelled every honest outcome a failure. A goal you can't mathematically hit corrupts the feedback loop. Next iteration: a realistic +1.5–2%/month target.

**One source of truth, or none.**
`memory/TRADE-LOG.md` and `trade-outcomes.json` disagree on real facts — TECHM's exit history (see [[TECHM-2026-05-20]]: log shows a June partial sale, JSON shows a 05-29 thesis_broken close with no partial) and BAJAJ-AUTO's quantity and partial attribution (see [[BAJAJ-AUTO-2026-05-20]]: log says 2 shares / 06-01 partial, JSON says 1 share / 05-28). When a human-readable journal and a machine record drift, the audit trail is only as trustworthy as its single designated source (`trade-outcomes.json` here). Reconciling them is itself a [[Open Questions|open question]].

Related: [[Strategy Verdict]] · [[Open Questions]] · [[Walk-Forward Validation]] · [[Timeline]]
