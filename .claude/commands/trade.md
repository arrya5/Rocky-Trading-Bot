# /trade — Manually place a trade (with gate check)

$ARGUMENTS format: "BUY RELIANCE 10" or "SELL TCS 5"

Parse the arguments to extract: side, symbol, quantity.

Before placing, run the full 9-point buy-side gate:
1. Check symbol is in Nifty 50 or Nifty Midcap 150
2. Run: `python models/signal_generator.py SYMBOL`
3. Confirm catalyst exists in today's RESEARCH-LOG.md
4. Check circuit status: `python scripts/broker.py quote SYMBOL`
5. Read India VIX from latest RESEARCH-LOG.md entry
6. Check position count: `python scripts/broker.py positions`
7. Check week trade count from TRADE-LOG.md
8. Verify cash: `python scripts/broker.py account`
9. Check FII flow from latest RESEARCH-LOG.md

If ALL 9 pass:
```bash
python scripts/broker.py order '{"symbol":"SYMBOL","qty":N,"side":"buy/sell","type":"market","product":"D"}'
bash scripts/telegram.sh "Manual trade: SIDE SYMBOL | N shares | ₹PRICE"
```

If any gate fails, state clearly WHICH gate failed and WHY. Do not place the order.

Update TRADE-LOG.md and commit.
