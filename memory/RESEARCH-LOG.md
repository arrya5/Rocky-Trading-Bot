# Research Log — Indian AI Trading Bot
*Pre-market research notes and trade ideas*

---

## Research Entry Template
```
### RESEARCH-YYYY-MM-DD

**Market Context**
- SGX Nifty premarket: +/- X pts (gap-up/gap-down signal)
- India VIX: XX.XX (< 15 calm | 15-20 elevated | > 20 avoid new positions)
- FII net flow yesterday: +/- ₹X,XXX Cr (buying/selling)
- DII net flow yesterday: +/- ₹X,XXX Cr
- Global cues: [US market direction, crude oil, dollar index]

**Sector Momentum**
- Strong today: [sectors]
- Weak today: [sectors]

**Trade Ideas**
1. SYMBOL — [catalyst] — GRU signal: BUY/SELL | confidence: XX%
   Entry: ₹XXXX | Target: ₹XXXX (+X%) | Stop: ₹XXXX (-7%)
   Risk: ₹X,XXX | Reward: ₹X,XXX | R:R = 1:X

**Rejected Ideas** (gate failed)
- SYMBOL — failed gate: [which rule failed]

**Key Events Today**
- [earnings, RBI, macro data, etc.]

**Sources**: [Gemini + Google Search]
```

---

### RESEARCH-2026-05-18

**Market Context**
- GIFT Nifty premarket: Partial data — session opened ~24,000 zone (data truncated by API)
- India VIX: 18.79 — elevated (15-25 range; investor nervousness, wider swings expected; BELOW 25 gate → PROCEED)
- FII net flow (May 15, last available): +₹1,329 Cr (net buyers) — POSITIVE; gate passes (>-₹3500 Cr threshold)
- DII net flow (May 15): -₹1,959 Cr (net sellers)
- Global cues: **NEGATIVE** — US-Iran tensions escalating | Brent crude >$110/barrel | INR at record low 96 vs USD | Wall St sharp sell-off Friday
- Regime: **BULL** (Nifty 20-day SMA slope: +3.13%, ADX: 20.9 — moderate trend strength)
- Nifty 50 close: ₹23,643.50 | SMA20: ₹24,046.73 | SMA50: ₹23,643 est. (price below SMA20 — pullback within bull trend)
- Nifty PCR: Unavailable (NSE API 403 Forbidden)

**Sector Momentum**
- Strong (CONFIRMED by both signal scan + Gemini): **Pharma** and **Metals** explicitly identified as outperforming sectors for week of May 18 — aligns with TATASTEEL(100), TORNTPHARM(100), HINDALCO(80), DRREDDY(80)
- Strong (signal scan): FMCG (TATACONSUM 100), Energy/Infrastructure (ONGC 80, ADANIENT 80, GRASIM 80)
- Weak (confirmed by Gemini): Banking — Nifty Bank closed -0.77% Friday, below key MAs, bearish bias today; Bank Nifty weekly expiry = elevated volatility; large private banks at "attractive valuations" per BofA but short-term bearish
- Weak (confirmed by Gemini): IT — Nifty IT -5.71% last week, "Strong Sell" across all MAs, 0 buy signals / 12 sell signals — avoid all IT names
- Weak (YTD context): Nifty Realty -24.4% YTD as of March 2026 — avoid
- Context: Nifty 50 was -22.80% YTD as of March 24, 2026 — current bull regime (+3.13% slope) is a recovery from a deep correction
- Macro headwinds: Crude at $110+ (negative for India overall, positive for ONGC/energy producers), INR at 96 record low (FII outflow pressure), US-Iran geopolitical risk-off

**Full Signal Scan Results** (Score ≥ 40, sorted by score)
Score 100:
- TATASTEEL — 100/100 | RSI: 55.4 | Mom10d: +2.59% | ADV: ₹533 Cr | Vol: 1.32%
- TATACONSUM — 100/100 | RSI: 64.8 | Mom10d: +7.81% | ADV: ₹322 Cr | Vol: 2.24%
- TORNTPHARM — 100/100 | RSI: 61.7 | Mom10d: +5.27% | ADV: ₹120 Cr | Vol: 1.62%

Score 80:
- ASIANPAINT — 80/100 | RSI: 63.1 | Mom10d: +6.59% | ADV: ₹270 Cr
- ONGC — 80/100 | RSI: 60.0 | Mom10d: -0.07% | ADV: ₹519 Cr
- JSWSTEEL — 80/100 | RSI: 48.8 | Mom10d: +1.13% | ADV: ₹254 Cr
- ADANIENT — 80/100 | RSI: 76.4 (overbought) | Mom10d: +12.77% | ADV: ₹757 Cr
- DRREDDY — 80/100 | RSI: 50.4 | Mom10d: +1.04% | ADV: ₹429 Cr
- GRASIM — 80/100 | RSI: 71.7 | Mom10d: +4.98% | ADV: ₹256 Cr
- HINDALCO — 80/100 | RSI: 51.2 | Mom10d: +2.84% | ADV: ₹456 Cr
- APOLLOHOSP — 80/100 | RSI: 64.1 | Mom10d: +5.84% | ADV: ₹299 Cr
- MANAPPURAM — 80/100 | RSI: 63.3 | Mom10d: +4.62% | ADV: ₹135 Cr
- CONCOR — 80/100 | RSI: 53.3 | Mom10d: +1.96% | ADV: ₹61 Cr
- BIOCON — 80/100 | RSI: 93.6 (extremely overbought) | Mom10d: +19.59% | ADV: ₹189 Cr
- MCX — 80/100 | RSI: 86.9 (overbought) | Mom10d: +14.12% | ADV: ₹827 Cr
- ABCAPITAL — 80/100 | RSI: 58.6 | Mom10d: +3.37% | ADV: ₹178 Cr
- NYKAA — 80/100 | RSI: 53.6 | Mom10d: +2.89% | ADV: ₹93 Cr

Score 60: BHARTIARTL, SUNPHARMA, ADANIPORTS, DIVISLAB, CIPLA, BAJAJ-AUTO, PIDILITIND, COLPAL, MARICO, DABUR, MAXHEALTH, FORTIS, AUROPHARMA, RADICO, MFSL, ADANIGREEN, CAMS

Score 40: ITC, KOTAKBANK, NESTLEIND, POWERGRID, COALINDIA, SBILIFE, HDFCLIFE, LICHSGFIN, ALKEM

**Top 10 Candidates for Market-Open Gate Check**

1. TATASTEEL — Score: 100/100 — Catalyst: PENDING (Gemini rate-limited; Steel sector — India infra, anti-dumping duties context) [MEDIUM likely] — Chart: neutral (API error, low confidence)
   Sector: Metals | Size: ₹70,000 | Entry zone: ~₹217 | Stop: ₹202 (-7%) | Earnings guard: CLEAR

2. TATACONSUM — Score: 100/100 — Catalyst: PENDING (FMCG recovery, Tata brand premium) [MEDIUM likely] — Chart: neutral
   Sector: FMCG | Size: ₹70,000 | Entry zone: ~₹1,234 | Stop: ₹1,148 (-7%) | Earnings guard: CLEAR

3. TORNTPHARM — Score: 100/100 — Catalyst: PENDING (Pharma sector breakout, export momentum) [MEDIUM likely] — Chart: neutral
   Sector: Pharma | Size: ₹70,000 | Entry zone: ~₹4,406 | Stop: ₹4,097 (-7%) | Earnings guard: CLEAR

4. ASIANPAINT — Score: 80/100 — Catalyst: PENDING — Chart: neutral
   Sector: Consumer | Size: ₹70,000 | Entry zone: ~₹2,606 | Stop: ₹2,423 (-7%) | Earnings guard: CLEAR

5. DRREDDY — Score: 80/100 — Catalyst: PENDING — Chart: neutral
   Sector: Pharma | Size: ₹70,000 | Entry zone: ~₹1,337 | Stop: ₹1,243 (-7%) | Earnings guard: CLEAR

6. HINDALCO — Score: 80/100 — Catalyst: PENDING — Chart: neutral
   Sector: Metals | Size: ₹70,000 | Entry zone: ~₹1,068 | Stop: ₹993 (-7%) | Earnings guard: CLEAR

7. GRASIM — Score: 80/100 — Catalyst: PENDING — Chart: neutral
   Sector: Infrastructure | Size: ₹70,000 | Entry zone: ~₹2,934 | Stop: ₹2,729 (-7%) | Earnings guard: CLEAR

8. ONGC — Score: 80/100 — Catalyst: PENDING (Oil sector, energy pricing) — Chart: neutral
   Sector: Energy | Size: ₹70,000 | Entry zone: ~₹299 | Stop: ₹278 (-7%) | Earnings guard: CLEAR

9. JSWSTEEL — Score: 80/100 — Catalyst: PENDING (Metals sector) — Chart: neutral
   Sector: Metals | Size: ₹70,000 | Entry zone: ~₹1,279 | Stop: ₹1,189 (-7%) | Earnings guard: CLEAR

10. ADANIENT — Score: 80/100 — RSI 76.4 (overbought caution) | Mom10d +12.77% — Catalyst: PENDING
    Sector: Energy | Size: ₹70,000 | Entry zone: ~₹2,716 | Stop: ₹2,526 (-7%) | Earnings guard: CLEAR

**Sector Concentration Notes** (Gate 9)
- Metals: TATASTEEL + HINDALCO + JSWSTEEL — max 2 positions; rank TATASTEEL > HINDALCO > JSWSTEEL; drop JSWSTEEL if both entered
- Energy: ONGC + ADANIENT — both can enter (2 max)
- Pharma: TORNTPHARM + DRREDDY — both can enter (2 max), but SUNPHARMA/DIVISLAB/CIPLA would be 3rd — skip

**Earnings Reporting Today** (NSE)
- NTPC (Q4), IOC, Indraprastha Gas, Astral, Triveni Turbine, Strides Pharma, Subros, Zydus Wellness, and 40+ smaller companies
- NONE of top 10 candidates have earnings today (per Gemini fallback check)

**Rejected**
- BIOCON — RSI 93.6 (extreme overbought, parabolic +19.59% in 10 days — momentum chase risk; catalyst verify needed)
- MCX — RSI 86.9, +14.12% in 10 days — overbought; watch for pullback entry
- ADANIENT — borderline; RSI 76.4 overbought; kept as #10 but needs HARD/MEDIUM catalyst confirmation at open
- NTPC — earnings TODAY (Q4 results) — would fail Gate 8; also no signal in top 10
- POWERGRID — Score 40, RSI 24 (oversold downtrend), negative momentum — weak setup
- All Banking/IT names — no BUY signal from signal_generator.py

**⚠️ API Limitations Today**
- Gemini API hit free-tier daily quota (20 req/day) during pre-market routine
- Catalyst classification (HARD/MEDIUM/SOFT) for ALL 10 candidates is PENDING
- Chart analysis (vision) returned neutral/API error for all 5 tested
- **CRITICAL**: At market open (9:20 AM), verify catalyst for each stock via manual research before placing ANY order
- Sector research (Steps 3) incomplete due to rate limit

**Key Events Today**
- NTPC Q4 results, IOC Q4 results, Indraprastha Gas Q4 results
- Astral results, Triveni Turbine results
- Zydus Wellness, Strides Pharma Science results
- ~50+ companies reporting results

**⚠️ Macro Risk Alert (Updated)**
- Brent crude >$110/barrel = inflationary pressure, negative for India overall
- INR at 96 record low = potential FII acceleration of selling; May 15 FII data (+1329 Cr) is PRE-WEEKEND and may not reflect latest geopolitical deterioration
- US-Iran tensions = global risk-off; Wall St sell-off Friday = negative gap-open likely
- Nifty Bank expiry day + bearish bias = avoid banking sector today
- VIX at 18.79 may rise intraday given geopolitical context — monitor closely
- If VIX crosses 25 intraday: CLOSE any new position opened today, halt further buying

**Candidate Revisions Given Macro Context**
- ONGC: Crude at $110 = direct revenue benefit (HARD catalyst candidate — oil producer)
- ADANIENT: Energy conglomerate, may benefit from energy cycle; but RSI 76.4 = overbought risk
- Banking candidates (KOTAKBANK score 40): Avoid — sector bearish today
- IT names: Avoid — sector in strong downtrend
- Defensive picks preferred in this environment: TORNTPHARM, TATACONSUM (FMCG defensive)

**Recommendation**: PROCEED WITH CAUTION (VIX 18.79 < 25, FII positive — gates pass) — but macro environment is RISK-OFF. Prioritize defensive/commodity candidates with confirmed HARD/MEDIUM catalyst. Verify catalyst (Gate 3) AND check if VIX has risen before any trade. Position sizing: use score-tiered sizes but consider entering fewer positions today given macro headwinds.

---
