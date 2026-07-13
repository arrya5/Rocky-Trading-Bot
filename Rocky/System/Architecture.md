---
type: system
tags: [system, architecture, pipeline]
created: 2026-07-13
updated: 2026-07-13
source: [README.md, memory/PROJECT-CONTEXT.md, CLAUDE.md]
---

# Architecture

Rocky is an autonomous swing-trading agent for NSE/BSE, running a ₹5,00,000 paper portfolio. Its design pattern: **build the measuring instrument first, then swap strategies through it.** Every decision is committed to Git, so any trading day is replayable from the logs.

## The pipeline

```
Gemini API  ─ macro research + catalyst classify + chart vision
      │
      ▼
RESEARCH-LOG.md  ─ candidates, VIX/FII/regime context
      │
      ▼
[[Signal Generator]]  ─ score 180+ stocks on 5 factors (≥80 = BUY)
      │
      ▼
[[9-Point Buy Gate]]  ─ 9+1 mechanical checks, no discretion
      │
      ▼
[[Broker - Upstox]]  ─ place order, product=D (delivery), paper mode
      │
      ▼
TRADE-LOG.md + trade-outcomes.json  ─ audit + structured records
      │
      ▼
Telegram alert  ─── then ──▶  git commit (memory/ = permanent record)
```

## Layers

- **Research** — [[Data Sources]]: Gemini (macro, catalyst tiers, chart PNG vision), yfinance prices, NSE bhavcopy/PCR.
- **Decision** — the [[Signal Generator]] scores momentum; the [[9-Point Buy Gate]] + [[Regime Detection]] veto. Exits are mechanical ([[Hard Stop]], [[Partial Exit]], [[Trailing Stop]], 15-day max hold).
- **Execution & memory** — [[Broker - Upstox]] simulates fills into `paper_portfolio.json`; every routine ends with a Telegram alert and a Git commit.
- **Orchestration** — has moved across three [[Infrastructure Eras]]; the [[Routines]] themselves stayed stable while the runner changed.

The current strategy is [[Swing v3]]. See [[Timeline]] for milestones and the [[Fitness Score]] for how the system grades itself.
