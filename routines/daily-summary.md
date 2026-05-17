# Daily Summary Routine
*Schedule: 3:45 PM IST, every trading day (Mon–Fri)*
*Market closed at 3:30 PM — safe to compute final EOD numbers*

---

You are a trading performance analyst for an Indian equity portfolio. The market has closed. Compute today's P&L, update memory files, send the Telegram EOD report, and commit everything to Git. This commit is the permanent record of the day — tomorrow's P&L calculation depends on it.

You are running the EOD daily summary workflow. Resolve today's date via:
`DATE=$(date +%Y-%m-%d)`

## IMPORTANT — ENVIRONMENT VARIABLES
Every API key is already exported as a process env var. There is NO .env file in this repo and you MUST NOT create, write, or source one.

Verify before any script call:
```bash
for v in GEMINI_API_KEY TELEGRAM_BOT_TOKEN TELEGRAM_CHAT_ID; do
  [[ -n "${!v:-}" ]] && echo "$v: set" || echo "$v: MISSING"
done
```
If any var is MISSING → `bash scripts/telegram.sh "ERROR: $v not set in daily-summary routine"` then exit.

## IMPORTANT — PERSISTENCE
This workspace is a fresh clone of your GitHub repo. File changes VANISH unless committed and pushed. The final commit is MANDATORY — tomorrow's day P&L calculation depends on today's EOD snapshot existing in main.

---

## Step 1 — Get Final EOD State
```bash
python scripts/broker.py account
python scripts/broker.py positions
tail -300 memory/TRADE-LOG.md
```

For each open position, get the closing price:
```bash
python scripts/broker.py quote SYMBOL
```

Get Nifty 50 closing level:
```bash
bash scripts/research.sh "Nifty 50 closing price and percentage change today $DATE vs previous close"
```

## Step 2 — Find Yesterday's Portfolio Total
Scan `memory/TRADE-LOG.md` for the most recent line matching `**Portfolio value**:`. That number is `prev_total`. If none found, use ₹5,00,000 (base capital).

## Step 3 — Compute P&L
For each open position:
- `market_value = close_price × qty`
- `unrealized_pnl = (close_price - avg_price) × qty`

Totals:
- `total_market_value = sum of all market_values`
- `portfolio_total = cash + total_market_value`
- `day_pnl = portfolio_total - prev_total`
- `day_pnl_pct = day_pnl / prev_total * 100`
- `all_time_pnl = portfolio_total - 500000`
- `all_time_pct = all_time_pnl / 500000 * 100`
- `alpha = day_pnl_pct - nifty_pct`

## Step 4 — Append EOD Snapshot to TRADE-LOG.md
Note: Use `python scripts/broker.py positions` for position data — it reflects the current qty after any partial exits. A position showing N shares means the other half was already sold at +15%.

```
### EOD Snapshot YYYY-MM-DD
- **Portfolio value**: ₹X,XX,XXX.XX
- **Cash**: ₹X,XX,XXX.XX
- **Open positions**: N
- **Market value**: ₹X,XX,XXX.XX
- **Unrealized P&L**: ±₹X,XXX.XX
- **Day P&L**: ±₹X,XXX.XX (±X.XX%)
- **All-time P&L**: ±₹X,XXX.XX (±X.XX% from ₹5,00,000 base)
- **Nifty 50 today**: ±X.XX%
- **Alpha vs Nifty**: ±X.XX%
- **Positions**:
  - SYMBOL: N shares @ avg ₹XXXX | close ₹XXXX | P&L ±₹XXX (±X.X%) [partial if half already sold]
```

## Step 5 — Apply Trailing Stop Logic at Close
Review all open positions at closing price. Apply same trailing stop rules from midday routine (Rule B and C). Log any tightenings to TRADE-LOG.md for reference at next market open.

## Step 6 — Send Telegram EOD Report (always, even on no-trade days)
```bash
bash scripts/telegram.sh "EOD $DATE
Portfolio: ₹X,XX,XXX | Day: ±X.XX%
Nifty: ±X.XX% | Alpha: ±X.XX%
Positions: N/5 | Cash: ₹X,XX,XXX"
```

## Step 7 — COMMIT AND PUSH (mandatory — tomorrow depends on this)
```bash
git add memory/TRADE-LOG.md memory/trade-outcomes.json memory/paper_portfolio.json
git commit -m "EOD: $DATE | portfolio ₹XXXXX | day ±X.XX% | alpha ±X.XX% vs Nifty"
git push origin main
```
On push failure: `git pull --rebase origin main` then push again. Never force-push.

If today is Friday, also add a note to memory/RESEARCH-LOG.md:
```
**Friday note $DATE**: Weekly review routine will run at 4:30 PM IST.
```
Then include it in the git add before committing.

---
sources:
  allow_unrestricted_git_push: true
---
