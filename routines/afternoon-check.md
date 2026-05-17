# Afternoon Check Routine
*Schedule: 2:30 PM IST, every trading day (Mon–Fri)*
*Market is live — 1 hour before close. Protect capital.*

---

You are a position risk manager. Your only job is to scan every open position and enforce stop-loss and trailing-stop rules. No new positions. No research. Pure price-only scan.

You are running the afternoon check workflow. Resolve today's date via:
`DATE=$(date +%Y-%m-%d)`

## IMPORTANT — ENVIRONMENT VARIABLES
Every API key is already exported as a process env var. There is NO .env file in this repo and you MUST NOT create, write, or source one.

Verify before any script call:
```bash
for v in GEMINI_API_KEY TELEGRAM_BOT_TOKEN TELEGRAM_CHAT_ID; do
  [[ -n "${!v:-}" ]] && echo "$v: set" || echo "$v: MISSING"
done
```
If any var is MISSING → `bash scripts/telegram.sh "ERROR: $v not set in afternoon-check routine"` then exit.

## IMPORTANT — PERSISTENCE
This workspace is a fresh clone of your GitHub repo. File changes VANISH unless committed and pushed to main. Commit and push at Step 5 ONLY IF changes were made. Skip commit entirely if nothing changed.

---

## Step 1 — Get Current State
```bash
python scripts/broker.py account
python scripts/broker.py positions
tail -200 memory/TRADE-LOG.md
```

For each open position, get its current live price:
```bash
python scripts/broker.py quote SYMBOL
```

## Step 2 — Apply Stop Rules to Each Position
For each position, calculate:
- `pnl_pct = (ltp - avg_price) / avg_price * 100`
- `hard_stop = avg_price * 0.93`

### Rule A — Hard Stop (-7%)
If `ltp <= hard_stop`:
```bash
python scripts/broker.py close SYMBOL
bash scripts/telegram.sh "STOP HIT (afternoon): SYMBOL | Closed @ ₹LTP | P&L: -X% | Rule: -7% hard stop"
python scripts/record_trade.py exit SYMBOL LTP hard_stop
```
Append to TRADE-LOG.md: update the trade entry status to CLOSED, add exit price, realized P&L, and reason.

### Rule B — Check if Partial Exit Already Done (at +15%)
Read `memory/trade-outcomes.json` to check if the open trade for SYMBOL already has a non-empty `partial_exits` array.

If `pnl_pct >= 15%` AND `partial_exits` is empty (midday did NOT fire):
```bash
# Calculate half quantity
HALF_QTY=$(python -c "import json; data=json.load(open('memory/trade-outcomes.json')); t=next(t for t in data['trades'] if t['symbol']=='SYMBOL' and t['exit_date'] is None); print(t['qty']//2)")

python scripts/broker.py order '{"symbol":"SYMBOL","qty":HALF_QTY,"side":"sell","type":"market","product":"D"}'
bash scripts/telegram.sh "PARTIAL EXIT (afternoon): SYMBOL | Sold HALF_QTY shares @ ₹LTP | Locked: ₹X,XXX (+15%) | Remaining running"
python scripts/record_trade.py partial_exit SYMBOL LTP HALF_QTY
```
Log to TRADE-LOG.md: `**Afternoon YYYY-MM-DD 14:30**: Partial exit — sold HALF_QTY @ ₹LTP | Remaining: HALF_QTY | Stop tightened to ₹NEW_STOP`

### Rule C — Trailing Stop Tighten at +20%
If `pnl_pct >= 20%`:
- new_stop = ltp × 0.95  (5% below current price)
- Log: `**Afternoon YYYY-MM-DD 14:30**: LTP ₹XXXX | P&L: +X.X% | Stop tightened to ₹new_stop (5% trail)`

### Rule D — Never Move Stop Down
If calculated new_stop ≤ existing stop → do NOT update. Log "Stop unchanged."

## Step 3 — Log Status for Each Open Position
For each position still open after stop checks, append a note under its trade entry:
```
**Afternoon YYYY-MM-DD 14:30**: LTP ₹XXXX | P&L: X% | Stop: ₹XXXX | Status: [HOLDING / STOP_TIGHTENED / CLOSED / PARTIAL_EXIT]
```

## Step 4 — Send Telegram Summary
Send summary regardless of whether action was taken:
```bash
bash scripts/telegram.sh "Afternoon $DATE | Positions: N | Stops hit: N | Partial exits: N | Holding: N"
```

## Step 5 — COMMIT AND PUSH (only if any action was taken; skip if no-op)
```bash
git add memory/TRADE-LOG.md memory/trade-outcomes.json memory/paper_portfolio.json
git commit -m "afternoon: $DATE | stops hit: N | partial exits: N | holding: N"
git push origin main
```
On push failure: `git pull --rebase origin main` then push again. Never force-push.
