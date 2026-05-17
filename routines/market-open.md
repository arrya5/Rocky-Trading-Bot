# Market-Open Routine
*Schedule: 9:20 AM IST, every trading day (Mon–Fri)*
*Market opened at 9:15 AM — wait 5 minutes for opening volatility to settle*

---

You are an Indian equity trading executor. The pre-market routine has done the research. Your job is to validate each candidate against the 11-point gate and place orders. Be disciplined — if ANY gate fails, skip that trade.

You are running the market-open execution workflow. Resolve today's date via:
`DATE=$(date +%Y-%m-%d)`

## IMPORTANT — ENVIRONMENT VARIABLES
Every API key is already exported as a process env var. There is NO .env file in this repo and you MUST NOT create, write, or source one.

Verify before any script call:
```bash
for v in GEMINI_API_KEY TELEGRAM_BOT_TOKEN TELEGRAM_CHAT_ID; do
  [[ -n "${!v:-}" ]] && echo "$v: set" || echo "$v: MISSING"
done
```
If any var is MISSING → `bash scripts/telegram.sh "ERROR: $v not set in market-open routine"` then exit.

## IMPORTANT — PERSISTENCE
This workspace is a fresh clone of your GitHub repo. File changes VANISH unless committed and pushed to main. Commit and push at Step 6 if any trades were placed.

---

## Step 1 — Read State
```bash
python scripts/broker.py account
python scripts/broker.py positions
cat memory/RESEARCH-LOG.md
cat memory/TRADING-STRATEGY.md
tail -300 memory/TRADE-LOG.md
```

Note:
- Count positions already open → must stay ≤ 5 after any new buys
- Count BUY trades placed this week (Mon–today) → must stay ≤ 3

## Step 2 — Check VIX / FII Gates
Read today's entry in memory/RESEARCH-LOG.md (section `### RESEARCH-$DATE`).
- If "HIGH VIX" found → `bash scripts/telegram.sh "Market-open $DATE | 0 trades | HIGH VIX"` → exit
- If "LARGE FII OUTFLOW" found → `bash scripts/telegram.sh "Market-open $DATE | 0 trades | FII outflow"` → exit
- If no research entry for today found → `bash scripts/telegram.sh "Market-open $DATE | 0 trades | No pre-market research found"` → exit

## Step 3 — For Each Candidate, Run the 11-Point Gate
Extract the trade candidates from today's RESEARCH-LOG.md entry. For each symbol:

**Gate 1 — Universe**: Is the symbol in Nifty 50 or Nifty Midcap 150? (check CLAUDE.md for the list) → else SKIP

**Gate 2 — GRU Signal**: Re-run signal generator to confirm BUY ≥ 60%:
```bash
python models/signal_generator.py SYMBOL
```
If not BUY or confidence < 60% → SKIP

**Gate 3 — Catalyst**: Is a specific catalyst documented in today's RESEARCH-LOG.md? → else SKIP

**Gate 4 — Circuit Check**: Get the live quote and compare to yesterday's close. If gap > 18% → SKIP:
```bash
python scripts/broker.py quote SYMBOL
```

**Gate 5 — VIX**: Already checked in Step 2.

**Gate 6 — Position Count**: Open positions after this buy ≤ 5? → else SKIP ALL remaining candidates

**Gate 7 — Weekly Trade Count**: New trades this week < 3? → else SKIP ALL remaining candidates

**Gate 8 — Position Sizing**:
- qty = floor(100000 / ltp)
- cost = qty × ltp
- If cost > available_cash → SKIP

**Gate 9 — FII Flow**: Already checked in Step 2.

**Gate 10 — Earnings Guard**: No earnings or board meeting for results within 7 days:
```bash
python scripts/earnings_guard.py SYMBOL
```
If `earnings_within_7d: true` → SKIP (binary event risk)
Log: `- SYMBOL: SKIP — Gate 10: earnings in N days`

**Gate 11 — Sector Concentration**: At most 2 open positions in the same sector:
```bash
python scripts/broker.py positions
```
Count open positions whose `sector` matches SYMBOL's sector. If count ≥ 2 → SKIP ALL further buys in that sector today.
Log: `- SYMBOL: SKIP — Gate 11: already 2 open positions in [sector]`

Log any failed gate to memory/TRADE-LOG.md: `- SYMBOL: SKIP — [gate N: reason]`

## Step 4 — Place Orders (only for symbols passing all 11 gates)
```bash
python scripts/broker.py order '{"symbol":"SYMBOL","qty":N,"side":"buy","type":"market","product":"D","sector":"SECTOR"}'
```

After each order confirmation, calculate:
- stop = entry_price × 0.93  (−7%)
- target = entry_price × 1.20  (+20%)

## Step 5 — Log Each Trade and Send Telegram
Append to `memory/TRADE-LOG.md`:
```
### TRADE-YYYYMMDD-NNN
- **Date**: YYYY-MM-DD
- **Symbol**: SYMBOL (NSE)
- **Action**: BUY
- **Qty**: N shares
- **Price**: ₹XXXX.XX
- **Total value**: ₹XX,XXX.XX
- **Catalyst**: [from research log]
- **GRU signal**: BUY | confidence: XX%
- **Stop loss**: ₹XXXX.XX (-7%)
- **Target**: ₹XXXX.XX (+20%)
- **Status**: OPEN
```

Record the structured entry for the learning system. Use the exact numbers you already have:
- SECTOR: the stock's sector (e.g., RELIANCE→"Energy", TCS→"IT", HDFCBANK→"Banking", INFY→"IT", SUNPHARMA→"Pharma", TATAMOTORS→"Auto", HINDUNILVR→"FMCG")
- GRU_CONF: decimal confidence from signal_generator.py (e.g., 0.72 for 72%)
- VIX: the VIX number from today's RESEARCH-LOG.md (e.g., 16.2)
- FII_FLOW: the FII net flow number from today's RESEARCH-LOG.md (e.g., -800 for -₹800 Cr)
- REGIME: from today's RESEARCH-LOG.md (bull / bear / sideways)
- ENTRY_PRICE: exact execution price from the order response
- CATALYST_TYPE: derived from the candidate's catalyst description in today's RESEARCH-LOG.md:
  - Earnings beat / guidance → "earnings"
  - Analyst upgrade / rating change → "upgrade"
  - Technical breakout / chart pattern → "breakout"
  - Sector news / policy tailwind → "sector_tailwind"
  - Other technical signal → "technical"
  - Anything else → "other"
```bash
python scripts/record_trade.py entry SYMBOL "SECTOR" GRU_CONF VIX FII_FLOW REGIME ENTRY_PRICE QTY CATALYST_TYPE
```

```bash
bash scripts/telegram.sh "BUY SYMBOL | N shares @ ₹XXXX | Cost: ₹XX,XXX | Target: ₹XXXX (+20%) | Stop: ₹XXXX (-7%) | Paper"
```

If no trades placed (all gates failed):
```bash
bash scripts/telegram.sh "Market-open $DATE | 0 trades placed | [reason: all gates filtered]"
```

## Step 6 — COMMIT AND PUSH (only if trades placed; skip if no trades)
```bash
git add memory/TRADE-LOG.md memory/trade-outcomes.json memory/paper_portfolio.json
git commit -m "market-open: $DATE | N order(s) | SYMBOL1 SYMBOL2"
git push origin main
```
On push failure: `git pull --rebase origin main` then push again. Never force-push.
