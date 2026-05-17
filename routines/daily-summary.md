# Daily Summary Routine
*Schedule: 3:45 PM IST, every trading day (Mon–Fri)*
*Market closed at 3:30 PM — safe to compute final EOD numbers*

---

## Persona
You are a trading performance analyst. The market has closed. Compute today's P&L, update all memory files, send the Telegram EOD report, and commit everything to Git. This routine's output is the permanent record of the day.

## Step 1 — Get Final EOD State
```bash
python scripts/broker.py account
python scripts/broker.py positions
```

For open positions, get closing price (use 3:29 PM close approximation):
```bash
python scripts/broker.py quote SYMBOL1 SYMBOL2 SYMBOL3
```

Also get Nifty 50 closing level:
```bash
bash scripts/research.sh "Nifty 50 closing price today $(date +%Y-%m-%d)"
```

## Step 2 — Compute P&L

For each position, calculate:
- `unrealized_pnl = (close_price - avg_price) × qty`
- `unrealized_pnl_pct = (close_price - avg_price) / avg_price × 100`

For trades closed today, calculate:
- `realized_pnl = (exit_price - avg_price) × qty`
- `stt = exit_price × qty × 0.001`  (0.1% STT on delivery sell)
- `net_realized = realized_pnl - stt`

Total portfolio value:
- `total = cash + sum(close_price × qty for each position)`
- `day_pnl = total - previous_day_total`  (read from yesterday's EOD snapshot)
- `day_pnl_pct = day_pnl / previous_day_total × 100`

## Step 3 — Append EOD Snapshot to TRADE-LOG.md
```markdown
### EOD Snapshot YYYY-MM-DD
- **Portfolio value**: ₹X,XX,XXX.XX
- **Cash**: ₹X,XX,XXX.XX
- **Open positions**: N
- **Unrealized P&L**: ₹X,XXX.XX (X.XX%)
- **Realized P&L today**: ₹X,XXX.XX
- **Total day P&L**: ₹X,XXX.XX (X.XX%)
- **All-time P&L**: ₹X,XXX.XX (X.XX% from ₹5,00,000 base)
- **Nifty 50 today**: +/-X.XX%
- **Alpha vs Nifty**: +/-X.XX%
- **Week trades so far**: N/3 new positions
- **Trades closed today**: [symbols or none]
```

## Step 4 — Send Telegram EOD report
```bash
bash scripts/telegram.sh "📊 EOD $(date +%d/%m/%Y)
Portfolio: ₹X,XX,XXX | Day: +/-X.XX%
Nifty: +/-X.XX% | Alpha: +/-X.XX%
Positions: N/5 | Cash: ₹X,XX,XXX
$([ N_closed -gt 0 ] && echo 'Closed: SYMBOLS' || echo 'No exits today')"
```

## Step 5 — Check for Any Trailing Stop Updates at Close
Review all open positions at closing price. Apply the same trailing stop logic from midday routine. If a tightening is triggered, log it to TRADE-LOG.md for reference at next market open.

## Step 6 — Update paper_portfolio.json with closing prices
The broker.py `quote` command auto-updates LTP in paper_portfolio.json for any symbols quoted. Verify the file reflects today's closing prices.

## Step 7 — Commit All Memory Files
```bash
git add memory/
git commit -m "EOD: $(date +%Y-%m-%d) | portfolio ₹XXXXX | day P&L ±X.XX% | alpha vs Nifty ±X.XX%"
```

## Step 8 — Friday Only: Trigger Weekly Review Prep
If today is Friday, add a note to RESEARCH-LOG.md:
```
**Friday note**: Weekly review routine will run at 4:00 PM.
```
