---
type: concept
tags: [concept, regime, macro, gate]
created: 2026-07-13
updated: 2026-07-13
source: [memory/TRADING-STRATEGY.md, README.md]
---

# Regime Detection

## Definition
Daily classification of the Nifty 50 market state (bull / bear / sideways) from the slope of its 20-day SMA. Feeds gate 10 of the [[9-Point Buy Gate]] — the bear-regime block.

## Exact rule
- **Bull**: 20d SMA slope > +1.5%
- **Bear**: slope < −1.5% → **BLOCK ALL ENTRIES**
- **Sideways**: between the two (entries allowed)

A Markov persistence layer computes transition probabilities and a long-run stationary distribution to smooth borderline calls and avoid flip-flopping.

## Implementation
`scripts/regime_detector.py` — Nifty SMA slope + Markov smoothing.

## In practice
Every one of the 9 live entries was tagged `market_regime: bull` at entry, so the bear gate never actually fired in the live run — it remains **early / unvalidated** (README: "not yet validated in a real bear"). Backtest regime splits are unflattering to momentum: POC v2 won 91% in bull but 0% in sideways, and the swing-POC replay actually did *better* in bear (56% win) than bull (39%), hinting the regime tag alone doesn't predict edge.

Related: [[9-Point Buy Gate]] · [[Swing v3]] · [[POC v2 Backtest]]
