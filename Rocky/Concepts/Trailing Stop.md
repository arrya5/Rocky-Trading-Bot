---
type: concept
tags: [concept, exit, risk, stop]
created: 2026-07-13
updated: 2026-07-13
source: [memory/TRADING-STRATEGY.md, CLAUDE.md]
---

# Trailing Stop

## Definition
The moving stop that protects open profit. It ratchets in one direction only — it can tighten but is **never** moved down. Distinct from the fixed [[Hard Stop]] that caps the initial loss.

## Exact rule
- Default trail: −5% below cost (this *is* the hard stop until a gain appears)
- After [[Partial Exit]] at +6%: tighten to **3% below current price**
- At **+12% gain**: tighten remaining stop to 3% below current price (no double-tighten)
- NEVER move a stop downward; never tighten within 3% of LTP

## Implementation
Managed by `scripts/runners/midday.py`, evaluated against the latest quote from `scripts/broker.py`.

## In practice
No live trade ever reached +12%, so the +12% tighten never triggered. The only trail adjustment that happened was on [[BAJAJ-AUTO-2026-05-20]] after its +6.43% partial. In the swing-POC backtest (162 trades) trailing stops accounted for only 13 exits vs 110 max-holds and 30 hard stops — the trail rarely got a chance to work because so few positions trended far enough.

Related: [[Hard Stop]] · [[Partial Exit]] · [[Swing v3]]
