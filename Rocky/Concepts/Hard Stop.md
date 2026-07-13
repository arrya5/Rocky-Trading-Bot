---
type: concept
tags: [concept, exit, risk, stop]
created: 2026-07-13
updated: 2026-07-13
source: [memory/TRADING-STRATEGY.md, CLAUDE.md]
---

# Hard Stop

## Definition
The non-negotiable loss cut for [[Swing v3]]. No discretion, no averaging down, no "give it one more day." Tightened from −7% under [[Position Trading v1]] to −5% for the shorter swing horizon.

## Exact rule
- **−5% loss**: close immediately at market via `python scripts/broker.py close SYMBOL`
- **Lower circuit hit**: flag, attempt close at next day open
- **Fraud / scam news**: close immediately
- **Thesis broken**: close regardless of P&L
- **Max hold 15 trading days**: force close regardless of P&L (swing-specific)

## Implementation
Checked every run by `scripts/runners/midday.py` (and EOD); orders placed through `scripts/broker.py`.

## In practice
The hard stop fired on two live trades: [[BHARTIARTL-2026-05-20]] closed at −5.24% on 2026-06-04, and [[TATACONSUM-2026-05-20]] at −5.22% on 2026-06-05. [[TECHM-2026-05-20]] exited early on `thesis_broken` at +1.47%. Most other positions ran to the **max-hold** limit rather than the price stop. The recurring problem (see [[Swing v3]]): average loser −5.27% vs average winner +2.15% — the stop caps damage but winners are too small to compensate.

Related: [[Trailing Stop]] · [[Partial Exit]] · [[Swing v3]] · [[BHARTIARTL-2026-05-20]] · [[TATACONSUM-2026-05-20]]
