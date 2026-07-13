---
type: concept
tags: [concept, signal, momentum, scoring]
created: 2026-07-13
updated: 2026-07-13
source: [memory/TRADING-STRATEGY.md, models/signal_generator.py]
---

# Swing Score

## Definition
The 5-factor momentum score (0–100) that ranks the Nifty 50 + Midcap 150 universe. Gate 2 of the [[9-Point Buy Gate]] requires **score ≥ 80** — 4 of 5 factors aligned, a deliberately conservative, high-conviction threshold.

## Exact rule
Each factor = 20 points:
1. **Donchian 20-day breakout**: close ≥ previous 20-day high
2. **ADX(14) > 25**: strong trend confirmation
3. **Sector relative strength**: sector index outperforms Nifty by > 1pp over 10 days
4. **Volume surge**: today's volume > 2.5× 20-day avg
5. **Above 50-day EMA**: close > EMA50 × 1.01

**Pre-filters** (excluded before scoring if any fails): ADV (20-day avg daily value) ≥ ₹50 Cr; 20-day volatility ≤ 3.5%; price above 200-day SMA (no falling knives).

## Implementation
`models/signal_generator.py` (constants `DEFAULT_MIN_SCORE=80`, `ADV_MIN_CR=50`, `VOL_MAX_PCT=3.5`, `POSITION_SIZE=50_000`). Uses pandas-ta for ADX/EMA/Donchian.

## In practice
The score got 9 candidates past the gate in the live run. Note the file is still invoked as a "GRU signal" in CLAUDE.md and trade logs (`gru_confidence` field), but the actual scorer is rules-based momentum — no neural net is used. POC v2's score-band split was counter-intuitive: the 60–79 band won 86% vs 62% for the 80–100 band, suggesting the high threshold isn't where the edge lives.

Related: [[9-Point Buy Gate]] · [[Swing v3]] · [[Signal Generator]]
