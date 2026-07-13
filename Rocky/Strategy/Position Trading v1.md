---
type: strategy
tags: [strategy, position-trading, frozen, superseded]
created: 2026-07-13
updated: 2026-07-13
source: [trading-bot-india/memory/TRADING-STRATEGY.md, memory/TRADING-STRATEGY.md]
---

# Position Trading v1

The original, now-**frozen** strategy (last updated 2026-05-17, deployed 2026-05-18). Longer-horizon position trading, replaced by [[Swing v3]] on 2026-05-27. Preserved as the v1 snapshot in `trading-bot-india/`.

## Rules snapshot
- **Universe**: Nifty 50 + Midcap 150, delivery only (same as v3)
- **Sizing**: **max ₹1,00,000 per position** (20% of capital), tiered 70k/50k/30k; **5 simultaneous positions** max; **≤ 3 new positions/week**
- **Entry**: 9-point gate keyed to a **GRU BUY signal with confidence ≥ 60%**, catalyst merely *documented* in RESEARCH-LOG (no HARD/MEDIUM/SOFT tiering), **VIX < 20**, **FII > −₹2,000 Cr**
- **Exits**: **−7% [[Hard Stop]]**; **+15% partial** exit; trailing stop **10% below cost**, tightening to 7% at +15% and 5% at +20%; **no max-hold limit**; profit target +20–30%
- **Research LLM**: Perplexity (later the whole stack moved to Gemini)

## Results
No standalone forward track record survives — v1 ran only 2026-05-18 to 2026-05-27 before migration. Its parameter DNA lives in the [[POC v2 Backtest]] (score ≥ 40, −7% stop, +15% partial, 70/50/30k tiers), which posted +12.31% / +6.66% alpha in-sample but failed [[Phase B Walk-Forward]] on the holdout.

## Verdict
**Superseded, deliberately.** v3 tightened everything for a shorter horizon: −7%→−5% stop, +15%→+6% partial, added a hard 15-day max-hold and a bear-[[Regime Detection|regime]] block, single flat ₹50k sizing, and stricter catalyst tiering ([[Catalyst Tiers]]). Note: `memory/PROJECT-CONTEXT.md` still describes these v1 parameters and Perplexity — known upstream staleness, preserved as annotation not fixed.

Related: [[Swing v3]] · [[POC v2 Backtest]] · [[Signal Generator]]
