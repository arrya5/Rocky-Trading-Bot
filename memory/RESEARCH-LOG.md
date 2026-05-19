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

*No research entries yet — Day 0 initialization*

---

### RESEARCH-2026-05-19

**Market Context**
- SGX Nifty: 23,669 — gap UP signal (+25.5 pts above prev close 23,643.50)
- India VIX: 19.63 (+4.47% from 18.79) — elevated (above normal 15-17 range, gate clears as <25)
- FII net flow (May 18): +₹2,813.69 Cr — strong buying (gate clears, well above -₹3,500 threshold)
- DII net flow (May 18): +₹2,682.12 Cr — buying
- Global cues: US futures slightly negative (S&P500 futures -0.21%), Brent crude ~$109/bbl (-1.91% on Iran de-escalation), DXY ~99 (stable), Asia mixed
- Regime: **bull** (Nifty 20d SMA slope: +2.77%, moderate trend strength, Nifty close: 23,649.95, SMA20: 24,011.55)
- Nifty PCR: unavailable (NSE API returned 403 Forbidden)

**Sector Momentum**
- Strong: IT (+2.43% on May 18, led by TCS/Infy/HCL on USD strength), Pharma (broad-based), Metals (JSWSTEEL momentum)
- Weak/Consolidating: Banking (Nifty Bank at 53,537 — volatile, gap-down then recovery, range-bound 52,700–54,000)
- Note: Crude oil falling (-1.91%, Iran tensions easing) — slightly negative for E&P (ONGC/BPCL) but positive for margins across manufacturing/FMCG

**Signal Scan Results** (all BUY signals ≥ 40, 36 total)
- Score 100: JSWSTEEL
- Score 80: BHARTIARTL, ONGC, ADANIENT, GRASIM, APOLLOHOSP, TORNTPHARM, BIOCON, RADICO, NYKAA, ADANIGREEN, MCX
- Score 60: KOTAKBANK, ASIANPAINT, SUNPHARMA, ADANIPORTS, DRREDDY, DIVISLAB, CIPLA, TATACONSUM, PIDILITIND, MARICO, MANAPPURAM, AUROPHARMA
- Score 40: ITC, TECHM, HINDALCO, BAJAJ-AUTO, HDFCLIFE, COLPAL, DABUR, PAGEIND, MAXHEALTH, FORTIS, ALKEM, ABCAPITAL, CAMS

**Earnings Guard Eliminations** (Gate 8 — earnings within 7 calendar days)
- ONGC — earnings on 2026-05-26 (7 days, binary event risk — skip)
- GRASIM — earnings on 2026-05-20 (1 day — skip)
- APOLLOHOSP — earnings on 2026-05-20 (1 day — skip)
- TORNTPHARM — earnings on 2026-05-22 (3 days — skip)
- NYKAA — earnings on 2026-05-21 (2 days — skip)

**Chart Pattern Analysis** (Step 4.7 — vision, all parse_error/neutral due to Gemini API quota limit)
- JSWSTEEL Chart: parse_error — neutral — neutral — treat as no contradiction
- BHARTIARTL Chart: parse_error — neutral — neutral
- ADANIENT Chart: parse_error — neutral — neutral
- RADICO Chart: api_error (quota) — neutral — neutral
- MCX Chart: parse_error — neutral — neutral

**Trade Candidates** (Score ≥ 40, post-earnings-guard, post-catalyst-gate, sorted by score)

1. **JSWSTEEL** — Score: 100/100 — Catalyst: Q4 FY26 earnings beat May 14 (consolidated net profit multifold via BPSL exceptional gain ₹17,888 Cr; revenue +14.19% YoY to ₹51,180 Cr; dividend ₹7.10/share declared) [HARD] — Chart: neutral (parse error)
   Sector: Metals | Size: ₹70,000 | Entry zone: ~₹1,293 | Stop: ₹1,202 (-7%) | ~54 shares
   RSI: 53.3 (neutral) | ADV: ₹243.7 Cr | Volatility: 1.13%/day

2. **ADANIENT** — Score: 80/100 — Catalyst: $275M OFAC settlement + US DoJ criminal charges dropped against Gautam Adani (major legal resolution enabling US capital market access) [HARD] — Chart: neutral (parse error)
   Sector: Energy | Size: ₹70,000 | Entry zone: ~₹2,690 | Stop: ₹2,502 (-7%) | ~26 shares
   RSI: 70.3 (overbought — caution) | ADV: ₹764.3 Cr | Volatility: 2.63%/day

3. **RADICO** — Score: 80/100 — Catalyst: Q4 FY26 record results May 7 (EBITDA margin 19% record, P&A volume +28%, FY26 revenue >₹6,000 Cr, guidance for 125bp EBITDA expansion + debt-free FY27) [HARD] — Chart: neutral (api error)
   Sector: FMCG | Size: ₹70,000 | Entry zone: ~₹3,471 | Stop: ₹3,228 (-7%) | ~20 shares
   RSI: 57.4 (neutral) | ADV: ₹156.1 Cr | Volatility: 1.63%/day

4. **MCX** — Score: 80/100 — Catalyst: Net profit surge 291% + positive analyst upgrades [HARD] — Chart: neutral (parse error)
   Sector: Fin Services | Size: ₹70,000 | Entry zone: ~₹3,348 | Stop: ₹3,114 (-7%) | ~20 shares
   RSI: 80.6 (very overbought — caution) | ADV: ₹845.3 Cr | Volatility: 1.8%/day

**Rejected**
- ONGC — Gate 8: earnings within 7 days (May 26, Financial Results/Dividend)
- GRASIM — Gate 8: earnings within 7 days (May 20, Financial Results/Dividend)
- APOLLOHOSP — Gate 8: earnings within 7 days (May 20)
- TORNTPHARM — Gate 8: earnings within 7 days (May 22)
- NYKAA — Gate 8: earnings within 7 days (May 21)
- BHARTIARTL — Gate 3: SOFT catalyst only (technical breakout + sector sentiment, no specific event)
- BIOCON — Gate 3: SOFT catalyst (no specific event today); RSI 89.1 extremely overbought — skip
- ADANIGREEN — Gate 3: SOFT catalyst (no specific event identified)
- All score-40 and score-60 stocks — lower priority, deprioritized vs. score-80+ candidates with HARD catalysts

**Key Events Today (2026-05-19)**
- Q4 FY26 results due: Bharat Electronics, Mankind Pharma, BPCL, Zydus Lifesciences, PI Industries, Zee Entertainment, Afcons Infrastructure
- RBI board meets May 22 to deliberate surplus transfer to government (~₹2.7-3L Cr for FY27)
- US-Iran military tension de-escalating → crude falling; rupee at 96.2 vs USD (weak)
- Elevated bond yields + inflation concerns cited as macro headwinds

**Recommendation**: PROCEED with 4 candidates. All pass the 9-point buy-side gate. Total deployment: 4 × ₹70,000 = ₹2,80,000 (56% of ₹5L portfolio). VIX elevated at 19.63 — monitor positions closely. Executing at market open 9:20 AM IST.

---
