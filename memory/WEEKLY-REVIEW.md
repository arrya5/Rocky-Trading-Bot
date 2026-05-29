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

### WEEK OF 2026-05-18 to 2026-05-22

**P&L Summary**
- Week P&L: +₹2,052.80 (+0.41%)
- Nifty 50 this week: +0.32% (23,643.50 → 23,719.30)
- Alpha vs Nifty: +0.09%
- Grade: **A** — positive return AND beat Nifty

**Trade Breakdown**
| Symbol | Sector | Entry | EOD Fri | Unrealized P&L | Status |
|--------|--------|-------|---------|----------------|--------|
| JSWSTEEL | Metals | ₹1,266.50 | ₹1,287.50 | +₹819 (+1.66%) | Open |
| BHARTIARTL | Telecom | ₹1,902.10 | ₹1,872.70 | -₹1,058 (-1.55%) | Open |
| TECHM | IT | ₹1,462.40 | ₹1,424.20 | -₹764 (-2.61%) ⚠️ | Open |
| MANAPPURAM | Finance | ₹314.90 | ₹324.90 | +₹2,220 (+3.18%) | Open |
| TATACONSUM | FMCG | ₹1,196.70 | ₹1,192.00 | -₹193 (-0.39%) | Open |
| RADICO | FMCG | ₹3,615.00 | ₹3,540.00 | -₹975 (-2.07%) ⚠️ | Open |
| BAJAJ-AUTO | Auto | ₹10,148.50 | ₹10,550.00 | +₹803 (+3.96%) | Open |
| HINDALCO | Metals | ₹1,091.70 | ₹1,110.00 | +₹1,171 (+1.68%) | Open |
| ADANIPORTS | Infrastructure | ₹1,787.00 | ₹1,788.10 | +₹30 (+0.06%) | Open |

**Stats**
- Win rate: N/A — 0 closed trades this week (all 9 positions remain open)
- Positions in profit: 5/9 (JSWSTEEL, MANAPPURAM, BAJAJ-AUTO, HINDALCO, ADANIPORTS)
- Positions in loss: 4/9 (BHARTIARTL, TECHM, TATACONSUM, RADICO)
- Avg unrealized winner: +₹1,009 (+2.51%)
- Avg unrealized loser: -₹748 (-1.66%)
- Best: BAJAJ-AUTO (+₹803, +3.96%) | Worst: BHARTIARTL (-₹1,058, -1.55%)
- GRU directional accuracy (unrealized, open positions): 5/9 (55.6%) — too early to judge

**Sector Context (week ending 2026-05-22)**
- Nifty Metal: +1.91% ✅ — portfolio Metals positions aligned (JSWSTEEL +1.66%, HINDALCO +1.68%)
- Nifty Private Bank: +1.40% ✅ — Finance (MANAPPURAM +3.18%) benefited from broader NBFC tailwind
- Nifty IT: -5.71% ❌ — drag on TECHM (-2.61%); sector underperformed despite Nvidia Q1 FY27 beat
- Nifty FMCG: -1.13% ❌ — drag on RADICO (-2.07%) and TATACONSUM (-0.39%)
- Nifty Telecom: hit 52-week high this week — yet BHARTIARTL underperformed at -1.55% vs entry

**What Worked**
1. **Gate 8 prevented binary risk** — 6 stocks blocked (TORNTPHARM, NYKAA, GRASIM, APOLLOHOSP, DIVISLAB, CIPLA, ONGC all had earnings within 7 days). At least 3 of these reported volatile results. Gate 8 is working exactly as designed.
2. **Metals thesis was correct** — Nifty Metal +1.91% weekly. Both JSWSTEEL (HARD: earnings beat, Q4 revenue +14% YoY) and HINDALCO (HARD: Q4 FY26 strong standalone ops) delivered gains aligned with the sector. HARD catalyst + sector momentum = reliable combination.
3. **Low-score high-catalyst outperformed high-score low-catalyst** — BAJAJ-AUTO (score 40/100, ₹30k min-size) delivered +3.96%, beating every 80-score entry. The ₹5,633 Cr buyback was a concrete near-term price driver that quantitative momentum scores couldn't fully capture. Catalyst quality > GRU score for short-term performance.

**What Didn't Work**
1. **IT position despite sector headwind** — TECHM entered with HARD catalyst (Q4 PAT +21% QoQ) but Nifty IT fell 5.71% this week. The sector-wide selloff overrode the company-level earnings beat. TECHM now at -2.61% with only 4.51% buffer to stop. Risk: stop triggers Monday if IT weakness continues.
2. **FMCG sector concentration with crude headwind** — RADICO and TATACONSUM both entered when Brent crude was $110/bbl. FMCG sector -1.13% weekly; elevated crude (margins) and DXY at 6-week high (import costs) were consistent headwinds visible pre-entry. Gate should be more sensitive to crude levels for FMCG stocks.
3. **BHARTIARTL underperformed its sector** — Nifty Telecom hit a 52-week high this week, yet BHARTIARTL is -1.55% from entry. Company-specific weakness vs sector strength. Score had already declined 80→40 by May 22 research scan, suggesting momentum faded quickly post-entry.

**Strategy Changes This Week**
- No rule changes this week — 0 closed trades (need ≥ 20 for data-driven rule changes per performance_analyzer.py protocol)
- Observing: FMCG entries during elevated crude (>₹100/bbl Brent) may warrant additional Gate consideration — flag for review after 20+ closed trades
- Observing: Sector-level momentum score decline (BHARTIARTL 80→40 within 48h of entry) suggests exit trigger may be needed before stop loss — monitor

**Next Week**
- **Critical watches**: TECHM (stop ₹1,360.03, buffer 4.51%) and RADICO (stop ₹3,361.95, buffer 5.03%) — both at risk if sectoral weakness continues Monday
- **Upcoming earnings**: ONGC results May 26 (not held — just monitor); DIVISLAB May 23 (not held)
- **Sector to watch**: IT — Nifty IT -5.71% this week; if sector stabilizes, TECHM thesis may recover; if weakness extends, stop will trigger
- **Cash reserve**: ₹48,500 — can deploy one ₹30,000 score-40 position if a stop triggers and creates room for a score-60/80 re-entry
- **Target approach**: BAJAJ-AUTO at +3.96%, MANAPPURAM at +3.18% — both may approach +15% partial-exit trigger in coming weeks; prepare partial exit logic
- **Gemini API**: rate limiting (20 req/day free tier) and 503 errors constrained catalyst verification all week — consider upgrading tier or batching research queries to avoid quota exhaustion by midday
- **BHARTIARTL**: monitor for recovery — if Nifty Telecom sector strength continues and BHARTIARTL remains flat, consider exit before stop to redeploy capital into stronger names

---

### WEEK OF 2026-05-25 to 2026-05-29

**P&L Summary**
- Week P&L: ₹1,179.10 (+0.23%)
- Nifty 50 this week: +0.00%
- Alpha vs Nifty: +0.23%
- Grade: A

**Fitness score**: +0.000 (return +0.00%/trade, maxDD 0.0%, Sharpe 0.00)

**Closed trades (all time)**: 0
**Performance analyzer data sufficient**: False

**Hypothesis verification**
- No hypotheses verified this week (0 still under observation)

**Qualitative**
(no analysis - insufficient data)

**Strategy Changes This Week**
- None this week

---

### WEEK OF 2026-05-25 to 2026-05-29

**P&L Summary**
- Week P&L: ₹1,179.10 (+0.23%)
- Nifty 50 this week: +0.00%
- Alpha vs Nifty: +0.23%
- Grade: A

**Fitness score**: +0.000 (return +0.00%/trade, maxDD 0.0%, Sharpe 0.00)

**Closed trades (all time)**: 0
**Performance analyzer data sufficient**: False

**Hypothesis verification**
- No hypotheses verified this week (0 still under observation)

**Qualitative**
(no analysis - insufficient data)

**Strategy Changes This Week**
- None this week

---
