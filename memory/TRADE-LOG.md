# Trade Log — Indian AI Trading Bot
*Paper trading mode | Capital: ₹5,00,000*

---

## Open Positions
*None yet — Day 0*

---

## Closed Trades
*None yet*

---

## EOD Snapshots

### 2026-05-17 (Day 0 — Initialization)
- **Portfolio value**: ₹5,00,000.00
- **Cash**: ₹5,00,000.00
- **Positions**: 0
- **Total P&L (all time)**: ₹0.00 (0.00%)
- **Nifty 50 today**: — (baseline day)
- **Week P&L**: ₹0.00
- **Note**: Bot initialized. Paper trading mode active. No trades yet.

---

### EOD Snapshot 2026-05-18
- **Portfolio value**: ₹5,00,000.00
- **Cash**: ₹5,00,000.00
- **Open positions**: 0
- **Market value**: ₹0.00
- **Unrealized P&L**: ₹0.00
- **Day P&L**: ₹0.00 (0.00%)
- **All-time P&L**: ₹0.00 (0.00% from ₹5,00,000 base)
- **Nifty 50 today**: +0.03% (closed at 23,649.95 vs prev 23,643.50)
- **Alpha vs Nifty**: -0.03%
- **Positions**: None — no trades placed yet
- **Note**: Day 1 of live operation. No signals passed the 9-point buy-side gate today. Capital fully in cash.

---

## Trade Entry Template
```
### TRADE-YYYYMMDD-NNN
- **Date**: YYYY-MM-DD
- **Symbol**: RELIANCE (NSE)
- **Action**: BUY / SELL
- **Qty**: N shares
- **Price**: ₹X,XXX.XX
- **Total value**: ₹X,XX,XXX.XX
- **Catalyst**: [reason for trade]
- **GRU signal**: BUY | confidence: XX%
- **Stop loss**: ₹X,XXX.XX (-7%)
- **Target**: ₹X,XXX.XX (+20%)
- **Status**: OPEN / CLOSED
- **P&L at close**: ₹X,XXX.XX (+X.XX%)
- **Exit reason**: Stop loss / Target / Strategy rule
```
