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

### RESEARCH-2026-05-20

**Market Context**
- SGX Nifty: 23,414 — gap DOWN signal (~-378 pts vs Nifty Futures close 23,792, ~-1.6%)
- India VIX: 18.68 (-4.84% from 19.63) — elevated but gate clears (<25)
- FII net flow (May 19): -₹2,457.49 Cr — net selling; gate clears (within -₹3,500 threshold)
- DII net flow (May 19): +₹3,801.68 Cr — net buying (cushioning FII outflows)
- Global cues: US S&P500 -0.67%, Nasdaq -0.84% (3rd consecutive down day); Brent crude $110.83/bbl (+elevated); DXY 99.4 (6-week high); Asia uniformly lower (Nikkei -0.8%, Hang Seng -0.34%, Kospi -0.5%); Nvidia earnings due tonight (key AI demand indicator)
- Regime: **bull** (Nifty 20d SMA slope: +2.44%, moderate trend; Nifty close: 23,618; SMA20: 23,974)
- Nifty PCR: unavailable (NSE API 403 Forbidden); use caution note — assume neutral

**Sector Momentum**
- Strong (May 19): IT (+3.23% — standout leader), Realty (+1.43%), PSU Bank (+0.81%), Consumer Durables (+0.44%), Pharma (+0.42%), Auto (+0.29%)
- Weak/Lagging (May 19): Metals, Financial Services
- Today's outlook: cautious, range-bound 23,350–23,800; IT sector resilience; Banking under pressure

**Trade Candidates** (Score ≥ 40, sorted by score — post earnings guard + catalyst gate)

1. **JSWSTEEL** — Score: 100/100 — Catalyst: Q4 FY26 earnings beat May 14 (consolidated net profit multifold via BPSL exceptional gain; revenue +14.19% YoY to ₹51,180 Cr; dividend ₹7.10/share declared) [HARD] — Chart: api_error/neutral (Gemini quota)
   Sector: Metals | Size: ₹70,000 | Entry zone: ~₹1,285 | Stop: ₹1,195 (-7%) | ~54 shares
   RSI: 51.5 (neutral) | ADV: ₹237.6Cr | Volatility: 1.14%/day

2. **BHARTIARTL** — Score: 80/100 — Catalyst: Q4 FY26 record revenue ₹211,000 Cr (lifetime high), ARPU ₹257 (+₹12 YoY), dividend ₹24/share (+50% YoY), Morgan Stanley Overweight TP ₹2,450 [HARD] — Chart: api_error/neutral
   Sector: Telecom | Size: ₹70,000 | Entry zone: ~₹1,913 | Stop: ₹1,779 (-7%) | ~36 shares
   RSI: 53.1 (neutral) | ADV: ₹1,779.6Cr | Volatility: 2.04%/day

3. **TECHM** — Score: 80/100 — Catalyst: Q4 FY26 PAT +21.26% QoQ to ₹1,356 Cr, FY26 revenue +7.2% YoY; IT sector momentum +3.23% yesterday [HARD] — Chart: api_error/neutral
   Sector: IT | Size: ₹70,000 | Entry zone: ~₹1,467 | Stop: ₹1,364 (-7%) | ~47 shares
   RSI: 51.1 (neutral) | ADV: ₹431.4Cr | Volatility: 2.5%/day

4. **MANAPPURAM** — Score: 80/100 — Catalyst: Q4 FY26 profit turnaround (loss -₹191 Cr → profit +₹404 Cr), Jefferies upgraded to BUY TP ₹360 (from ₹285 = +26% upside), dividend ₹0.50/share [HARD] — Chart: api_error/neutral
   Sector: Finance | Size: ₹70,000 | Entry zone: ~₹315 | Stop: ₹293 (-7%) | ~222 shares
   RSI: 63.2 (moderate) | ADV: ₹143.0Cr | Volatility: — (ADV slightly below peer avg, watch liquidity)

5. **TATACONSUM** — Score: 80/100 — Catalyst: Q4 FY26 net profit +20% YoY to ₹419 Cr, revenue +18% YoY to ₹5,434 Cr (May 8) [HARD] — Chart: api_error/neutral
   Sector: FMCG | Size: ₹70,000 | Entry zone: ~₹1,210 | Stop: ₹1,125 (-7%) | ~57 shares
   RSI: 59.0 (neutral) | ADV: ₹331.9Cr | Volatility: —

6. **RADICO** — Score: 80/100 — Catalyst: FY26 highest-ever revenue +22.7% YoY to ₹20,988 Cr, profit +74.9%; consensus Strong Buy, TP ~₹3,560–₹3,847 [HARD] — Chart: api_error/neutral
   Sector: FMCG | Size: ₹70,000 | Entry zone: ~₹3,600 | Stop: ₹3,348 (-7%) | ~19 shares
   RSI: 62.7 (moderate) | ADV: ₹152.0Cr | Volatility: 1.63%/day

7. **BAJAJ-AUTO** — Score: 80/100 — Catalyst: Q4 FY26 net profit +34% YoY to ₹2,746 Cr, revenue +32% YoY, ₹150 dividend + ₹5,633 Cr buyback approved (May 6) [HARD] — Chart: api_error/neutral
   Note: PL Capital/Prabhudas downgraded to Hold post-run; ICICI/HDFC maintaining Buy
   Sector: Auto | Size: ₹70,000 | Entry zone: ~₹10,205 | Stop: ₹9,490 (-7%) | ~6 shares
   RSI: 64.8 (moderate) | ADV: ₹415.8Cr | Volatility: —

**Capital note**: 7 positions × ₹70,000 = ₹4,90,000 (98% deployed). Gate 6 fails for candidates 8 and 9 below (insufficient remaining cash).

**Deprioritised this session (capital exhausted — Gate 6):**
- ADANIENT (80) — HARD catalyst (OFAC/DoJ settlement), but RSI 71.2 overbought + gap-down environment + 8th in order; skipped due to capital
- MCX (80) — HARD catalyst (net profit +291%), but RSI 80.5 very overbought + 9th; skipped due to capital

**Rejected**
- DIVISLAB — Gate 8: earnings May 23 (binary event risk — 3 days)
- CIPLA — Gate 8: board/event May 23 (binary event risk)
- TORNTPHARM — Gate 8: earnings May 22 (binary event risk — 2 days)
- GRASIM — Gate 8: earnings today May 20 (binary event risk — today)
- ONGC — Gate 8: earnings May 26 (within 7 days)
- NYKAA — Gate 8: earnings May 21
- APOLLOHOSP — Gate 8: earnings today May 20
- BIOCON — Gate 3: SOFT catalyst + RSI 89.9 extremely overbought
- ADANIPORTS — Gate 3: SOFT catalyst (technical breakout only, no event)
- ADANIGREEN — Gate 3: SOFT catalyst (no specific event)
- DRREDDY — Gate 3: Q4 FY26 earnings MISSED estimates, Morgan Stanley reduced TP — no positive catalyst
- BHARTIARTL (yesterday) — Note: reclassified to HARD today after verifying Q4 results

**Key Events Today (2026-05-20)**
- Grasim Industries Q4 FY26 results (today)
- Apollo Hospitals Q4 FY26 results (today)
- Hindalco Q4 FY26 results (Novelis posted quarterly loss $84M, net sales +4.4%)
- Jubilant Foodworks, Bosch, Samvardhana Motherson, Aditya Birla Capital results due
- RBI: proposed Basel III revised disclosure framework for banks (final from Q2 FY27); scrapped IFR requirement
- Nvidia Q1 FY27 earnings after US close (AI demand bellwether — could lift IT/Tech sentiment tomorrow)
- US-Iran tensions ongoing; DXY at 6-week high; elevated bond yields
- Nifty support: 23,350–23,400 | resistance: 23,700–23,800

**Recommendation**: PROCEED with 7 candidates. All pass the 9-point buy-side gate. Total deployment: ₹4,90,000 (98% of ₹5L portfolio). VIX at 18.68 — elevated but within range. Gap-down open expected: wait for market to stabilize (first 5 min post-open) before placing orders. Execute from 9:20 AM IST.

---

### RESEARCH-2026-05-21

**Market Context**
- SGX Nifty (GIFT Nifty): 23,800–23,858 → gap UP +166.5 pts (+0.70%) vs Nifty close 23,659 — strong bullish open expected
- India VIX: 18.31–18.44 (closed May 20 at 18.68, -0.98%) — elevated (17–25 zone), gate CLEARS (<25)
- FII net flow (May 20 provisional): -₹1,597.35 Cr — net sellers; gate CLEARS (within -₹3,500 threshold)
- DII net flow (May 20 provisional): +₹1,968.35 Cr — net buyers, cushioning FII outflows
- Global cues: GEMINI RATE LIMITED — inferred: GIFT Nifty gap-up strongly suggests Nvidia Q1 FY27 earnings (released after May 20 US close) beat estimates; IT sector likely to rally; crude elevated at ~$110/bbl; DXY ~99.4 (6-wk high); Asia likely positive on Nvidia beat
- Regime: **bull** (Nifty 20d SMA slope: +2.07%, strong trend strength; Nifty close: 23,659; SMA20: 23,928)
- Nifty PCR: unavailable (NSE API 403 Forbidden) — assume neutral

**Sector Momentum** *(Gemini rate limited — inferred from signal scan changes)*
- Strong (inferred): Metals (HINDALCO 40→100, JSWSTEEL 100→80 still strong), Pharma (SUNPHARMA/DIVISLAB/CIPLA all 80), Infrastructure (GRASIM/ADANIPORTS both 80)
- Auto: BAJAJ-AUTO holds 80 (was 80 yesterday)
- Weakening: IT (TECHM 80→40, signals softening despite Nvidia beat possibility)
- Caution: Multiple RSI readings in 70–93 range (BIOCON 93.3, MARICO 78.9, APOLLOHOSP 76.1, MAXHEALTH 77.2) — overbought universe

**Signal Scan Results** (35 BUY signals ≥ 40)
- Score 100: HINDALCO
- Score 80: BHARTIARTL★, SUNPHARMA, JSWSTEEL★, ADANIENT, ADANIPORTS, DIVISLAB, CIPLA, GRASIM, TATACONSUM★, BAJAJ-AUTO★, PAGEIND, RADICO★
- Score 60: INFY, BAJAJFINSV, ONGC, APOLLOHOSP, COLPAL, MARICO, FEDERALBNK, MANAPPURAM★, TORNTPHARM, AUROPHARMA, BIOCON, ABCAPITAL, NYKAA, MCX
- Score 40: KOTAKBANK, ASIANPAINT, TECHM★, DRREDDY, PIDILITIND, MAXHEALTH, FORTIS, MFSL, ADANIGREEN, CAMS
*(★ = already held in portfolio)*

**Earnings Guard** *(NSE API 403; Gemini fallback unreliable due to rate limits — manual override from prior research)*
- NYKAA: earnings today May 21 → Gate 8 FAIL (binary event risk)
- TORNTPHARM: earnings May 22 → Gate 8 FAIL (1 day, binary event risk)
- DIVISLAB: earnings May 23 → Gate 8 FAIL (2 days)
- CIPLA: board/results May 23 → Gate 8 FAIL (2 days)
- ONGC: earnings May 26 → Gate 8 FAIL (5 days)
- APOLLOHOSP: results announced May 20 — post-event, but RSI 76.1 overbought + score 60 → low priority

**Chart Pattern Analysis** *(Gemini rate limited — monitors running, results pending)*
- HINDALCO: pending
- SUNPHARMA: pending
- ADANIPORTS: pending
- GRASIM: pending
- PAGEIND: pending (also excluded: only 1 share at ₹70k size → partial exit rule impossible)

**Trade Candidates** (Score ≥ 40, post-earnings-guard, post-catalyst-gate, sorted by score)

1. **HINDALCO** — Score: 100/100 — Catalyst: Q4 FY26 results announced May 20 (Novelis -$84M loss but Indian ops likely strong; volume_surge triggered = institutional buying) [LIKELY HARD — pending Gemini confirmation] — Chart: pending
   Sector: Metals | Size: ₹70,000 | Qty: 64 shares | Entry zone: ~₹1,085 | Stop: ₹1,009 (-7%) | Target: ₹1,302 (+20%)
   RSI: 59.9 (neutral) | ADV: ₹500.7 Cr | Volatility: 1.84%/day
   Gate 9: 2nd Metals position (JSWSTEEL already held) — allowed (max 2 per sector)

2. **SUNPHARMA** — Score: 80/100 — Catalyst: pending Gemini research (near 52w high, RSI 64.1, momentum +1.63% 10d) [PENDING — HARD if Q4 FY26 results positive]  — Chart: pending
   Sector: Pharma | Size: ₹70,000 | Qty: 37 shares | Entry zone: ~₹1,880 | Stop: ₹1,748 (-7%) | Target: ₹2,256 (+20%)
   RSI: 64.1 (neutral) | ADV: ₹943.7 Cr | Volatility: 2.04%/day

3. **ADANIPORTS** — Score: 80/100 — Catalyst: pending [sector: Infrastructure; part of Adani group — OFAC/DoJ legal resolution May 19 provides group-level tailwind MEDIUM/HARD] — Chart: pending
   Sector: Infrastructure | Size: ₹70,000 | Qty: 39 shares | Entry zone: ~₹1,772 | Stop: ₹1,648 (-7%) | Target: ₹2,127 (+20%)
   RSI: 64.3 (neutral) | ADV: ₹582.6 Cr | Volatility: 1.99%/day
   Note: Capital available = ₹27,575 after HINDALCO + SUNPHARMA → Gate 6 FAILS for 3rd ₹70k position

**Deprioritised / Capital Exhausted after top 2:**
- ADANIPORTS (80) — 3rd pick, but Gate 6 fails (insufficient cash after HINDALCO + SUNPHARMA)
- GRASIM (80) — RSI 73.2 overbought; catalyst pending (Q4 FY26 results May 20 — but Gemini rate limited); Gate 6 also fails
- ADANIENT (80) — RSI 71.0 overbought; Gate 6 fails
- INFY (60) — ₹50k size, but Gate 6 marginal + IT sector (TECHM already held = 2nd IT position allowed)

**Existing Position Review**
| Symbol | Avg | LTP | Stop | Buffer | P&L | Status |
|--------|-----|-----|------|--------|-----|--------|
| JSWSTEEL | ₹1,266.50 | ₹1,283.20 | ₹1,177.85 | 8.2% | +₹651 | SAFE |
| BHARTIARTL | ₹1,902.10 | ₹1,904.90 | ₹1,768.95 | 7.1% | +₹101 | SAFE |
| TECHM | ₹1,462.40 | ₹1,439.00 | ₹1,360.03 | 5.5% | -₹468 | SAFE — monitor |
| MANAPPURAM | ₹314.90 | ₹319.15 | ₹292.86 | 8.2% | +₹944 | SAFE |
| TATACONSUM | ₹1,196.70 | ₹1,208.70 | ₹1,112.93 | 7.9% | +₹492 | SAFE |
| RADICO | ₹3,615.00 | ₹3,565.90 | ₹3,361.95 | 5.7% | -₹638 | SAFE — monitor |
| BAJAJ-AUTO | ₹10,148.50 | ₹10,462.50 | ₹9,438.11 | 9.8% | +₹628 | SAFE |
*Portfolio unrealized P&L: +₹1,710 (+0.34%)*

**Rejected**
- NYKAA — Gate 8: earnings today May 21 (binary event risk)
- TORNTPHARM — Gate 8: earnings May 22 (binary event risk)
- DIVISLAB — Gate 8: earnings May 23 (binary event risk)
- CIPLA — Gate 8: earnings May 23 (binary event risk)
- ONGC — Gate 8: earnings May 26 (5 days, binary event risk)
- APOLLOHOSP — Score 60, RSI 76.1 overbought, low priority
- BIOCON — RSI 93.3 extremely overbought → Gate 3 likely SOFT
- PAGEIND — Score 80 but only 1 share at ₹70k → partial exit rule structurally impossible; excluded
- ADANIPORTS/GRASIM/ADANIENT/INFY — Gate 6 fails after top 2 positions
- MCX (60) — RSI 81.1 very overbought
- All score-40 stocks — lower priority, insufficient capital

**Key Events Today (2026-05-21)**
- Nvidia Q1 FY27 earnings: released after May 20 US close → results available this morning; likely strong (AI demand); key IT sector sentiment driver
- NYKAA Q4 FY26 results (today)
- HINDALCO Q4 FY26 follow-through (announced May 20)
- RBI board May 22: surplus transfer to government deliberations (~₹2.7-3L Cr FY27)
- TORNTPHARM earnings May 22 (tomorrow — gate blocker)
- DIVISLAB / CIPLA board meetings May 23
- Gate 3 verification needed for HINDALCO + SUNPHARMA before 9:20 AM execution

**Recommendation**: **PROCEED with 2 candidates** — HINDALCO (100/100, Gate 3 pending) and SUNPHARMA (80/100, Gate 3 pending). Both require catalyst confirmation before 9:20 AM execution. Total deployment if both enter: ₹1,39,043 (cash: ₹1,66,618 → remaining ₹27,575). All 7 existing positions SAFE — no stop actions needed.
*Note: Gemini API rate limited (20 req/min free tier); global cues, sector momentum, and chart analysis results pending from background monitors.*

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
