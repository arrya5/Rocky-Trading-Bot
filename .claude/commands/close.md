# /close [SYMBOL | all] — Close a position or all positions

$ARGUMENTS: symbol name (e.g. "RELIANCE") or "all"

1. Get current position details:
```bash
python scripts/broker.py positions
python scripts/broker.py quote SYMBOL
```

2. Show the user current P&L for the position(s) to be closed

3. Close the position:
```bash
# Single position:
python scripts/broker.py close SYMBOL

# All positions:
python scripts/broker.py close-all
```

4. Send Telegram alert:
```bash
bash scripts/telegram.sh "Manual close: SYMBOL | P&L: ±X% | Reason: manual"
```

5. Update TRADE-LOG.md with exit details and reason "manual close"

6. Commit:
```bash
git add memory/ && git commit -m "manual close: SYMBOL | $(date +%Y-%m-%d)"
```
