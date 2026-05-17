# Weekly Review Log — Indian AI Trading Bot

---

## Weekly Review Template
```
### WEEK OF YYYY-MM-DD to YYYY-MM-DD

**P&L Summary**
- Week P&L: ₹X,XXX.XX (+/-X.XX%)
- Nifty 50 this week: +/-X.XX%
- Alpha vs Nifty: +/-X.XX%
- Grade: A / B / C / D / F

**Trade Breakdown**
| Symbol | Entry | Exit | P&L | Result |
|--------|-------|------|-----|--------|
| ...    | ...   | ...  | ... | Win/Loss |

**Win rate**: X/X (X%)
**Avg winner**: ₹X,XXX (+X.XX%)
**Avg loser**: ₹X,XXX (-X.XX%)
**Best trade**: SYMBOL (+X.XX%)
**Worst trade**: SYMBOL (-X.XX%)

**What Worked**
- [patterns that led to winning trades]

**What Didn't Work**
- [patterns that led to losses]

**Strategy Changes**
- [any updates to TRADING-STRATEGY.md this week]

**Next Week Focus**
- [sectors to watch, upcoming events, adjustments]
```

---

### WEEK OF 2026-05-11 to 2026-05-17

**P&L Summary**
- Week P&L: ₹0.00 (0.00%) — initialization week, no trades executed
- Starting portfolio: ₹5,00,000.00 (Day 0 baseline)
- Ending portfolio: ₹5,00,000.00
- Nifty 50 this week: -2.20% (closed at 23,643.50 vs prior close 24,176.15)
- Alpha vs Nifty: +2.20% (cash preservation outperformed falling index)
- Grade: **B** — Beat Nifty (by staying in cash) but did not generate a positive absolute return

**Trade Breakdown**
| Symbol | Entry | Exit | P&L | Result |
|--------|-------|------|-----|--------|
| —      | —     | —    | —   | No trades this week |

**Stats**
- Win rate: 0/0 (N/A — no closed trades)
- Avg winner: N/A
- Avg loser: N/A
- Best: N/A | Worst: N/A
- GRU directional accuracy: N/A (no signals acted on)

**Market Context This Week**
- Nifty 50: -2.20% (weak week, broad selling)
- Best sectors: Pharma (+2.18%), Healthcare (+2.17%), Metal (+1.91%)
- Worst sectors: Realty (-8.17%), IT (-5.71%), Auto (-4.36%)
- FII/DII flows: Data unavailable (API rate limit during research)
- Key observation: Defensive rotation underway — Pharma/Healthcare holding while growth sectors (IT, Realty, Auto) sold off heavily

**What Worked**
- Bot infrastructure initialized successfully: broker scripts, research pipeline, signal generator, Telegram alerts all operational
- Cash preservation: staying flat while Nifty fell -2.20% is a de facto +2.20% alpha outcome
- No gate violations possible — no trades attempted, no rules broken

**What Didn't Work**
- Bot went live mid-week (Sunday initialization); pre-market research routines were not yet running Mon–Thu, so no trade opportunities were evaluated
- FII/DII data fetch hit Gemini API free-tier rate limits (5 req/min cap) — need spacing between research calls
- No GRU signals were run this week; cannot assess model readiness in live conditions yet

**Strategy Changes This Week**
- None — insufficient data from a single initialization week to justify any rule changes
- Observation logged: rate-limit spacing needed between research.sh calls (minimum 15s apart when batching)

**Next Week Focus (2026-05-19 to 2026-05-23)**
- Begin full pre-market research routine from Monday 9:00 AM IST
- Run GRU signals on Pharma/Healthcare leaders (sector showing strength): SUNPHARMA, DRREDDY, CIPLA, APOLLOHOSP
- Avoid IT, Realty, Auto — all in confirmed downtrends this week; watch for stabilization before entry
- Key events to monitor: RBI MPC minutes release, US Fed commentary, any macro data releases
- VIX check critical before any entry — broad market weakness may push VIX above 20 threshold
- Target: identify 1–2 high-conviction setups passing all 9 gate conditions for first live trades

---
