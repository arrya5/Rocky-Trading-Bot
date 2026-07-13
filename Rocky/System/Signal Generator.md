---
type: system
tags: [system, signal, momentum]
created: 2026-07-13
updated: 2026-07-13
source: [models/signal_generator.py, README.md]
---

# Signal Generator

`models/signal_generator.py` — the [[Swing v3]] momentum scorer. It screens every stock in the Nifty 50 + Midcap 150 universe (180+ symbols) on five binary factors, each worth 20 points. See [[Swing Score]] for the concept.

> **Naming caveat**: CLAUDE.md and older docs call this the "GRU signal" and PROJECT-CONTEXT.md describes a GRU deep-learning model trained on NSE data. That is **legacy/aspirational** — no neural network runs. TensorFlow sits unused in requirements; scoring is pure rules over pandas/numpy price data. See [[Infrastructure Eras]].

## Pre-filters (excluded before scoring)

- ADV (20-day avg traded value) ≥ ₹50 Cr
- 20-day daily-return volatility ≤ 3.5%
- Close > 200-day SMA (avoid falling knives)

## The five factors (20 pts each, max 100)

| Factor | Condition |
|---|---|
| Donchian breakout | Close ≥ previous 20-day high |
| Trend strength | ADX(14) > 25 |
| Sector relative strength | Sector index beats Nifty by >1pp over 10 days |
| Volume surge | Today's volume > 2.5× 20-day average |
| Price structure | Close > EMA(50) × 1.01 |

## Scoring

- **Score ≥ 80** (4+ factors aligned) → `BUY` candidate, flat ₹50,000 sizing.
- **Score < 80** → `HOLD`. Pre-market can lower the threshold to ≥40 to widen the candidate list (used for logging/ranking, but the gate still demands the catalyst).

Output is JSON per symbol with the score breakdown, ADX, sector RS, volume ratio, EMA50/SMA200. Prices come from [[Data Sources]] (yfinance, `.NS` suffix). The score is only the entry trigger — it must still clear the [[9-Point Buy Gate]] and [[Regime Detection]].

Historically, low-score high-catalyst names (BAJAJ-AUTO, score 40) outperformed 80-score entries early on — see [[2026-W21]]. Catalyst quality can beat raw momentum score short-term.
