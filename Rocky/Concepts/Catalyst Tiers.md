---
type: concept
tags: [concept, gate, catalyst, llm]
created: 2026-07-13
updated: 2026-07-13
source: [memory/TRADING-STRATEGY.md, CLAUDE.md]
---

# Catalyst Tiers

## Definition
Gate 3 of the [[9-Point Buy Gate]]. Every candidate must have an identifiable *event* driving it, classified by Gemini (with a keyword fallback) into one of three tiers. "The stock is going up" is not a reason to buy.

## Exact rule
| Tier | Examples | Gate 3 |
|------|----------|--------|
| HARD | Earnings beat, analyst upgrade, product launch, regulatory approval, QIP/buyback, M&A | PASS |
| MEDIUM | Sector policy (PLI, budget), index inclusion, management guidance, block deal | PASS |
| SOFT | "Stock trending", "sector doing well", vague news | FAIL — skip |

## Implementation
LLM classification lives in `scripts/runners/pre_market.py` via the Gemini call in `scripts/research.sh`; results feed the gate in `market_open.py`. A deterministic keyword fallback exists after the quota incident (below).

## In practice
Every live entry was tagged `earnings` (HARD) except [[ADANIPORTS-2026-05-21]], logged as `other`. The classifier's failure mode is the sharpest engineering lesson of the run: when Gemini hit its quota, the failure path returned **SOFT for everything**, silently auto-rejecting all trades for days until a keyword-based deterministic floor was added. Never let an LLM failure quietly kill behaviour.

Related: [[9-Point Buy Gate]] · [[Swing Score]] · [[Swing v3]]
