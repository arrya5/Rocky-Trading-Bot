---
type: insight
tags: [insight, open-questions, unresolved]
created: 2026-07-13
updated: 2026-07-13
source: [memory/goal.yaml, memory/trade-outcomes.json, memory/TRADE-LOG.md, README.md, memory/TRADING-STRATEGY.md]
---

# Open Questions

Genuine unknowns the record does not resolve. These are not rhetorical — each is a real decision the next era of Rocky has to make. Kept honest per [[Strategy Verdict]].

**Would Swing v3 perform in a sustained bull regime?**
All nine live entries were tagged `market_regime: bull` at entry (see [[Regime Detection]]), yet the forward record was −2.96%. But the entries clustered in one window (2026-05-20/21) and most exits landed as the tape rolled over through June — the cohort was effectively entered near a *regime top*. Was the failure the strategy, or the timing of a single entry batch into a fading bull? One cohort can't separate the two. The bear gate, meanwhile, never fired live and remains **unvalidated**.

**Is the 20-trade auto-tune threshold even reachable at this trade rate?**
`goal.yaml` sets `reflection_every: 20` — no rule change is permitted until 20 closed trades. Rocky reached 9 in a month and then went to **zero new entries** for the entire final week ([[2026-W25]]) because nothing cleared the [[9-Point Buy Gate]]. At that pace, the learning loop may never gather the sample size it requires to legitimately adjust a variable. Should the reflection threshold scale to the actual trade rate, or should the gate be loosened to generate a testable sample?

**Should max-hold be shorter than 15 days?**
Six of nine trades exited on **max_hold** (see [[Lessons Learned]]) — it was the dominant exit, not the stop or a target. Positions that need 15 trading days to resolve mostly faded rather than ran. Would a 7–10 day cap cut dead money and improve EV, or would it just truncate the occasional winner earlier? The [[BAJAJ-AUTO-2026-05-20]] partial suggests the real edge (if any) shows up inside the first week.

**Which record is trustworthy for TECHM and BAJAJ-AUTO partial-exit history?**
`memory/TRADE-LOG.md` and `trade-outcomes.json` disagree: for [[TECHM-2026-05-20]] the log shows a June hold with a partial sale while the JSON records a 05-29 thesis_broken close with none; for [[BAJAJ-AUTO-2026-05-20]] the log shows qty 2 / a 06-01 partial while the JSON shows qty 1 / a 05-28 partial. The wiki treats `trade-outcomes.json` as authoritative per [[Schema]], but the two were never reconciled at source. Until they are, any P&L attribution on these two trades carries an asterisk. (A smaller instance: [[Fitness Score]] is quoted as −0.875 in the README/[[Swing v3]] but −0.768 in the weekly journals — same drift, different file.)

**What should era-3 Claude routines do differently?**
The migration back to Claude ([[Infrastructure Eras]]) is a chance to change substance, not just the runner. Open design choices: set a realistic +1.5–2%/month [[Fitness Score]] target instead of the unreachable +5%/30d; move from a mechanical [[Swing Score]] to AI-reasoning-driven entries where the edge is the reasoning; add a deterministic backstop to every LLM dependency (the catalyst classifier already needed one). Does era 3 keep testing mechanical rules at all, or pivot the whole thesis?

**Does any mechanical edge survive here, or is the category closed?**
Four mechanical variants failed out-of-sample ([[Position Trading v1]], [[Swing v3]], [[Sector Rotation Experiment]], [[Mean Reversion Experiment]]). Is that conclusive evidence the category has no edge on NSE mid/large caps under a delivery-only mandate — or just evidence these four parameterizations don't? Distinguishing "the search was exhausted" from "the search was shallow" is the question that decides whether Rocky abandons mechanical strategies entirely.

Related: [[Strategy Verdict]] · [[Lessons Learned]] · [[Fitness Score]] · [[Regime Detection]] · [[Infrastructure Eras]]
