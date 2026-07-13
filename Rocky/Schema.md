---
type: meta
tags: [meta, schema]
created: 2026-07-13
updated: 2026-07-13
source: [CLAUDE.md]
---

# Schema — how this wiki works

This vault is Rocky's **second brain**: a persistent, LLM-maintained wiki over the trading bot's raw records, built on Karpathy's LLM Wiki Pattern (gist `442a6bf555914893e9891c11519de94f`). Any Claude session operating on this vault must follow this document. Humans read the wiki; the LLM writes it. This schema is co-evolved — improve it deliberately, log every change in [[Log]].

## The three layers

| Layer | Location | Rule |
|---|---|---|
| **Raw sources** | `memory/`, `README.md`, `backtest/results/`, `routines/`, `trading-bot-india/` (v1 snapshot) | Immutable to wiki operations. Read, never edit. Source of truth on conflict. |
| **Wiki** | `Rocky/` (this vault) | LLM-generated and LLM-owned. Every claim traceable to a raw source via `source:` frontmatter. |
| **Schema** | `Rocky/Schema.md` (this file) | Conventions, page types, operations. Change only with intent + a [[Log]] entry. |

## Conventions

- **Links**: use `[[Basename]]` wiki-links liberally — graph connectivity is a design goal. Obsidian resolves by basename across folders. Every page should link to at least 2 others; every page must be reachable from [[Home]].
- **Filenames**: Title Case for concept-like pages (`Regime Detection.md`); verbatim identifiers for entities (`JSWSTEEL.md`, `JSWSTEEL-2026-05-20.md`); ISO week for journal (`2026-W21.md`).
- **Dates**: absolute ISO (`2026-05-20`), never relative. Currency: `₹`. Times: IST.
- **Tone**: factual, compressed, honest — losses and failed hypotheses are recorded as plainly as wins.
- **Frontmatter** (all pages, YAML):

```yaml
---
type: trade | stock | sector | concept | strategy | system | journal | insight | meta
tags: [..]
created: 2026-07-13   # date page was created
updated: 2026-07-13   # bump on every edit
source: [memory/TRADE-LOG.md]   # repo-relative raw-source paths backing this page
---
```

- **Trade pages** add: `symbol, sector, entry_date, entry_price, exit_date, exit_price, qty, pnl_abs, pnl_pct, exit_reason, catalyst_type, regime, days_held, partial_exit` (bool). Values come verbatim from `memory/trade-outcomes.json` — never recompute.

## Page types & canonical inventory

| Folder | type | Pages |
|---|---|---|
| `/` | meta | [[Home]] (catalog), [[Log]] (append-only), [[Schema]] (this) |
| `Trades/` | trade | One per closed trade, named by trade_id: [[JSWSTEEL-2026-05-20]], [[BHARTIARTL-2026-05-20]], [[TECHM-2026-05-20]], [[MANAPPURAM-2026-05-20]], [[TATACONSUM-2026-05-20]], [[RADICO-2026-05-20]], [[BAJAJ-AUTO-2026-05-20]], [[HINDALCO-2026-05-21]], [[ADANIPORTS-2026-05-21]] |
| `Stocks/` | stock | One per traded/researched symbol: [[JSWSTEEL]], [[BHARTIARTL]], [[TECHM]], [[MANAPPURAM]], [[TATACONSUM]], [[RADICO]], [[BAJAJ-AUTO]], [[HINDALCO]], [[ADANIPORTS]] |
| `Sectors/` | sector | [[Metals]], [[Telecom]], [[IT]], [[Finance]], [[FMCG]], [[Auto]], [[Infrastructure]] |
| `Concepts/` | concept | [[9-Point Buy Gate]], [[Catalyst Tiers]], [[Regime Detection]], [[Swing Score]], [[Hard Stop]], [[Partial Exit]], [[Trailing Stop]], [[Fitness Score]], [[Walk-Forward Validation]], [[Overfitting]], [[India VIX]], [[FII-DII Flows]] |
| `Strategy/` | strategy | [[Swing v3]], [[Position Trading v1]], [[POC v2 Backtest]], [[Phase B Walk-Forward]], [[Mean Reversion Experiment]], [[Sector Rotation Experiment]] |
| `System/` | system | [[Architecture]], [[Routines]], [[Signal Generator]], [[Broker - Upstox]], [[Data Sources]], [[Infrastructure Eras]] |
| `Journal/` | journal | [[Timeline]] + one per weekly review: [[2026-W21]], [[2026-W22]], [[2026-W23]], [[2026-W24]], [[2026-W25]] |
| `Insights/` | insight | [[Lessons Learned]], [[Strategy Verdict]], [[Open Questions]] |

New pages of an existing type follow the same naming; a genuinely new page type requires a schema edit here first.

## Operations

### Ingest (after every routine run, or when the user shares a new source)
1. Read [[Log]]'s last entry date; read everything in `memory/` newer than it (new trades in `trade-outcomes.json`, new TRADE-LOG/RESEARCH-LOG/WEEKLY-REVIEW entries).
2. Create/update affected pages: new closed trade → Trade page + update its Stock, Sector, and week Journal pages; research day → update mentioned Stock pages if material; weekly review → new `Journal/2026-Wnn` page; rule change → update the Concept/Strategy page and note the change date.
3. Update the [[Home]] catalog if pages were added/removed.
4. Append one dated entry to [[Log]]: what was ingested, pages touched.
5. Commit: `git add Rocky/ && git commit -m "wiki: ingest <date>"` (routines bundle this with their `memory/` commit).

### Query (answering questions from the vault)
1. Search the wiki first ([[Home]] → relevant pages); fall back to raw sources only for detail the wiki lacks.
2. Cite wiki pages in the answer.
3. If the answer produced durable synthesis (a comparison, a verdict, a pattern across trades), file it into `Insights/` and log it.

### Lint (weekly, with the Friday review)
1. Orphans: pages with no incoming links / unreachable from [[Home]].
2. Broken links: `[[targets]]` with no matching note (unless deliberately marked as a future page).
3. Contradictions: wiki claims vs current raw sources (numbers, rule parameters).
4. Staleness: `updated:` far behind the facts a page states. Known upstream staleness to preserve as *annotations, not fixes*: `memory/PROJECT-CONTEXT.md` still describes v1 parameters/Perplexity; `README.md` says "7 closed trades" (actual: 9).
5. Report findings + fixes as a [[Log]] entry.
