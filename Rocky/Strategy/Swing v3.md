---
type: strategy
tags: [strategy, swing, active, momentum]
created: 2026-07-13
updated: 2026-07-13
source: [memory/TRADING-STRATEGY.md, README.md, memory/trade-outcomes.json]
---

# Swing v3

The **current** strategy, live in paper mode since 2026-05-20 (adopted 2026-05-27, migrated from [[Position Trading v1]]). Short-to-medium-term swing trading, holding 3–15 trading days on 5–15 day momentum bursts.

## Rules snapshot
- **Universe**: Nifty 50 + Midcap 150, equity delivery (CNC) only — no F&O, no intraday
- **Sizing**: flat **₹50,000 per trade**, only [[Swing Score]] ≥ 80 candidates; ~10 concurrent max, ≤ 2 per sector
- **Entry**: the full [[9-Point Buy Gate]] (+ regime gate 10)
- **Exits**: −5% [[Hard Stop]]; [[Partial Exit]] 50% at +6% then trail to −3%; [[Trailing Stop]] tighten at +12%; **max hold 15 trading days**
- **Regime**: block ALL entries in bear (Nifty 20d SMA slope < −1.5%)

## Results
**Live forward (9 closed trades, May–Jun 2026):**
- Win rate **44.4%** (4W / 5L)
- Portfolio **−2.96%** all-time; weekly self-grade **D**; [[Fitness Score]] −0.875 / 1.0
- Avg winner ~+2.15% vs avg loser ~−5.27% — losers ~2.5× the size of winners
- Exit mix: 2 hard stops ([[BHARTIARTL-2026-05-20]], [[TATACONSUM-2026-05-20]]), 1 thesis-broken ([[TECHM-2026-05-20]]), 1 partial ([[BAJAJ-AUTO-2026-05-20]] @ +6.43%), the rest max-hold
- Backtest lineage: swing-POC replay was −2.47% / −8.12% alpha; the [[Phase B Walk-Forward]] holdout was −6.57% and called overfit before live even started

## Verdict
**Honest failure so far.** The strategy is losing ~2% per trade with winners too small to pay for losers. The 30-day kill-switch criterion (win < 45% AND alpha < −3%) is knocking — win 44.4% is already through the first tripwire. The lesson isn't "this rule was wrong" but "mechanical momentum on NSE midcaps may have no durable edge." See [[Strategy Verdict]] and [[Lessons Learned]].

Related: [[Position Trading v1]] · [[POC v2 Backtest]] · [[Walk-Forward Validation]] · [[Timeline]]
