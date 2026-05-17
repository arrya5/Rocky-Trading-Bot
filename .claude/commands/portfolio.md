# /portfolio — Show current portfolio state

```bash
echo "=== ACCOUNT ===" && python scripts/broker.py account
echo ""
echo "=== OPEN POSITIONS ===" && python scripts/broker.py positions
echo ""
echo "=== TODAY'S ORDERS ===" && python scripts/broker.py orders
```

Then read and summarize the last EOD snapshot from memory/TRADE-LOG.md.

Output a clean table showing:
- Each position: symbol, qty, avg price, current LTP, unrealized P&L (₹ and %)
- Total portfolio value and all-time P&L vs ₹5,00,000 base
