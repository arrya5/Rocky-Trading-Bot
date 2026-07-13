---
type: meta
tags: [meta, log, operations]
created: 2026-07-13
updated: 2026-07-13
source: [CLAUDE.md, Rocky/Schema.md]
---

# Log

Append-only operation log for this vault, per the Karpathy LLM-wiki pattern (gist `442a6bf555914893e9891c11519de94f`). Every build, ingest, and lint pass adds one dated entry below — newest at the bottom, never rewrite history. Each entry records what changed, which pages were touched, and any known-staleness or data-discrepancy annotations carried forward. The [[Schema]] defines the operations (Ingest / Query / Lint) that generate these entries; humans read the [[Home]] catalog, the LLM writes here.

---

## 2026-07-13 — Initial build

Vault created from scratch over Rocky's raw records, following the LLM-wiki pattern defined in [[Schema]].

- **Scope:** 61 notes across 9 folders — `/` (meta: 3), `Insights/` (3), `Strategy/` (6), `Trades/` (9), `Stocks/` (9), `Sectors/` (7), `Concepts/` (12), `System/` (6), `Journal/` (6).
- **Sources ingested (read-only):** `memory/` (`trade-outcomes.json`, `TRADE-LOG.md`, `RESEARCH-LOG.md`, `WEEKLY-REVIEW.md`, `TRADING-STRATEGY.md`, `goal.yaml`), `README.md`, `backtest/results/` (POC, Phase B, sector, mean-reversion reports), `routines/*.md`, and the `trading-bot-india/` v1 snapshot.
- **Anchor pages written this pass:** [[Strategy Verdict]], [[Lessons Learned]], [[Open Questions]], [[Home]] (catalog), this [[Log]].
- **Trade record:** nine closed trades, values taken verbatim from `trade-outcomes.json` (authoritative per [[Schema]]) — never recomputed.

### Known upstream staleness (preserved as annotations, not fixed)
- `memory/PROJECT-CONTEXT.md` still describes **v1 parameters** (−7% stop, +15% partial, ₹1,00,000 tiered sizing) and **Perplexity** as the research LLM — annotated on [[Position Trading v1]]; the current stack is [[Swing v3]] on Gemini.
- `README.md` "Current Status" says **7 closed trades** and portfolio ₹4,87,431 (snapshot dated 2026-06-11); the actual final count is **9** and the flat portfolio is ₹4,85,218 (−2.96%). Annotated on [[Timeline]] and [[Swing v3]].
- [[Fitness Score]] is quoted as **−0.875** in `README.md` / the strategy page but **−0.768** in the weekly journals ([[2026-W24]], [[2026-W25]]) — same drift, flagged for reconciliation.

### Data discrepancies flagged on affected trade pages
- **[[TECHM-2026-05-20]]** — `TRADE-LOG.md` shows a June hold with a partial sale (10 @ ₹1,561, 06-01); `trade-outcomes.json` (authoritative) records a 2026-05-29 `thesis_broken` close with no partial. Wiki follows the JSON; discrepancy noted on the page.
- **[[BAJAJ-AUTO-2026-05-20]]** — `TRADE-LOG.md` shows qty 2 (₹20,297) and a ~06-01 partial; `trade-outcomes.json` shows qty 1 and a 2026-05-28 partial. Wiki follows the JSON; discrepancy noted on the page.

### Next scheduled op
- **Ingest** after the next routine run (era-3 Claude routines, once resumed) — new closed trades → Trade + Stock + Sector + week Journal pages, per [[Schema]] Ingest steps.
- **Lint** with the Friday weekly review — check for orphans, broken links, contradictions vs raw sources, and staleness; report findings as the next [[Log]] entry.
