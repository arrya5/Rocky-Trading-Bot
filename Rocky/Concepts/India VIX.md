---
type: concept
tags: [concept, macro, volatility, gate]
created: 2026-07-13
updated: 2026-07-13
source: [memory/TRADING-STRATEGY.md, CLAUDE.md]
---

# India VIX

## Definition
NSE's volatility index — the market's fear gauge, derived from Nifty option prices. Rocky uses it as a risk-off switch: elevated VIX means no new entries. Read pre-market and checked at order time.

## Exact rule
Gate 5 of the [[9-Point Buy Gate]]: **India VIX < 25** to allow an entry. (Under [[Position Trading v1]] the threshold was a stricter < 20; loosened to < 25 for [[Swing v3]].)

## Implementation
Fetched in `scripts/runners/pre_market.py` via `scripts/research.sh`; the gate is enforced in `market_open.py`. VIX at entry is stamped onto every trade record (`vix_at_entry`).

## In practice
Never a binding constraint in the live run — VIX sat calm at **18.68** for the May-20 entries and **18.31** for the May-21 entries, well under the 25 ceiling. Every live trade was entered in a low-fear, bull-regime tape, so the loss came from stock selection, not a volatility spike.

Related: [[9-Point Buy Gate]] · [[FII-DII Flows]] · [[Regime Detection]] · [[Swing v3]]
