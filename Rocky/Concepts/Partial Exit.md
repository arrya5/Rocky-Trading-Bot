---
type: concept
tags: [concept, exit, profit-taking]
created: 2026-07-13
updated: 2026-07-13
source: [memory/TRADING-STRATEGY.md, CLAUDE.md, memory/trade-outcomes.json]
---

# Partial Exit

## Definition
Mandatory profit-booking mechanic: at +6% unrealized gain, sell half the position to lock in a realized gain, then tighten the remaining half's [[Trailing Stop]]. One partial exit per trade, ever.

## Exact rule
- At **+6% gain**: SELL exactly **50%** of the position at market
- Then tighten the remaining 50% trailing stop to **3% below current price**
- ONE partial exit only per trade (skip if `partial_exits` in trade-outcomes.json is non-empty)

## Implementation
Triggered by `scripts/runners/midday.py`; logged via `python scripts/record_trade.py partial_exit SYMBOL EXIT_PRICE QTY_SOLD`.

## In practice
Exactly **one** partial exit fired in the entire live run: [[BAJAJ-AUTO-2026-05-20]] hit +6.43% on 2026-05-28 and sold 1 of its 1-share position (qty was tiny at a ~₹10,148 price). The remainder rode to max-hold and closed at +3.38% overall. No other live trade ever reached +6%, which is the core symptom of the strategy's dead edge — winners rarely cleared the profit-booking threshold.

Related: [[Trailing Stop]] · [[Hard Stop]] · [[Swing v3]] · [[BAJAJ-AUTO-2026-05-20]]
