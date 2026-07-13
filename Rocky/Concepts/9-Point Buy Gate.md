---
type: concept
tags: [concept, gate, entry, risk]
created: 2026-07-13
updated: 2026-07-13
source: [memory/TRADING-STRATEGY.md, CLAUDE.md]
---

# 9-Point Buy Gate

## Definition
The mechanical entry filter for [[Swing v3]]. Before any buy order, **all** conditions must pass — no discretion, no overrides. One failure = skip the trade. Called "9+1" because a tenth [[Regime Detection|regime]] gate was bolted on in May 2026.

## Exact rule
1. Stock in Nifty 50 or Nifty Midcap 150
2. [[Swing Score]] ≥ 80 (4 of 5 factors) AND passed ADV + volatility pre-filters
3. Catalyst is HARD or MEDIUM tier ([[Catalyst Tiers]]) — SOFT = skip
4. Not at upper circuit; no large gap (> 18%)
5. [[India VIX]] < 25
6. Position cost ≤ available cash — flat ₹50,000 per trade
7. FII net flow > −₹3,500 Cr ([[FII-DII Flows]])
8. No earnings / board meeting within 7 calendar days
9. Sector concentration ≤ 2 open positions in the same sector after entry
10. **Regime gate**: skip ALL entries when regime == "bear" (Nifty 20d SMA slope < −1.5%)

## Implementation
Enforced in `scripts/runners/market_open.py`; supported by `scripts/earnings_guard.py` (gate 8), `scripts/regime_detector.py` (gate 10), and `models/signal_generator.py` (gates 2–3). In backtests gates 3, 7, 8 auto-pass (LLM lookahead / NSE scrape blocked).

## In practice
All 9 live entries (May 20–21 2026) cleared the gate in a **bull** regime with VIX ~18.3–18.7 and FII flow around −₹1,600 to −₹2,457 Cr — comfortably inside limits. The gate never blocked a real entry in the live run; the edge failure was downstream (see [[Swing v3]]). Skip logs from backtests show gates 6 (cash) and 9 (sector full) do the heavy lifting.

Related: [[Catalyst Tiers]] · [[Swing Score]] · [[Regime Detection]] · [[Swing v3]]
