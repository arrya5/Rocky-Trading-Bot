---
type: concept
tags: [concept, macro, flows, gate]
created: 2026-07-13
updated: 2026-07-13
source: [memory/TRADING-STRATEGY.md, CLAUDE.md]
---

# FII-DII Flows

## Definition
Net daily buying/selling by Foreign Institutional Investors (FII) and Domestic Institutional Investors (DII) on NSE. Heavy FII outflow signals institutional risk-off; Rocky blocks new longs into a strong outflow.

## Exact rule
Gate 7 of the [[9-Point Buy Gate]]: **FII net flow > −₹3,500 Cr** (i.e. skip if the outflow is worse than −₹3,500 Cr). Stricter −₹2,000 Cr threshold under [[Position Trading v1]], relaxed for [[Swing v3]].

## Implementation
Pulled pre-market via `scripts/research.sh` (Gemini) into `RESEARCH-LOG.md`; the gate runs in `market_open.py`. Value at entry is recorded as `fii_flow_at_entry`.

## In practice
Comfortably passed on every live entry — FII flow was **−₹2,457 Cr** on 2026-05-20 and **−₹1,597 Cr** on 2026-05-21, both inside the −₹3,500 Cr limit. Important caveat carried from the backtests: the historical FII gate is **inactive** — the NSE bhavcopy/archive scrape is blocked, so in every replay (POC, Phase B) gate 7 auto-passes and the filter is effectively untested out-of-sample.

Related: [[9-Point Buy Gate]] · [[India VIX]] · [[Data Sources]] · [[Swing v3]]
