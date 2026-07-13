---
type: system
tags: [system, routines, schedule]
created: 2026-07-13
updated: 2026-07-13
source: [routines/pre-market.md, routines/market-open.md, routines/midday.md, routines/afternoon-check.md, routines/daily-summary.md, routines/weekly-review.md]
---

# Routines

Six Claude routines drive Rocky's trading day, all times **IST**. Each is a self-contained prompt in `routines/*.md`: read context → act → Telegram alert → Git commit. They are stateless (fresh clone each run); only committed `memory/` files persist.

| Routine | IST | Does |
|---|---|---|
| pre-market | 8:30 AM | Macro research (VIX/FII/global), regime + PCR, scan universe via [[Signal Generator]], classify catalysts, earnings guard, chart vision → write RESEARCH-LOG |
| market-open | 9:20 AM | Validate each candidate against the [[9-Point Buy Gate]], place orders via [[Broker - Upstox]], record trades |
| midday | 12:30 PM | Price-only scan: [[Hard Stop]], [[Partial Exit]] at +6%, [[Trailing Stop]] tighten. No new entries |
| afternoon-check | 2:30 PM | Second risk scan, 1 hour before close. Same stop/trail rules, no research |
| daily-summary | 3:45 PM | EOD P&L snapshot, biggest-surprise reflection, Telegram summary, commit (tomorrow's P&L depends on it) |
| weekly-review | 4:30 PM Fri | Grade the week, run [[Fitness Score]], performance analyzer, rule-change check → WEEKLY-REVIEW → weekly journal page |

## Current status — disabled, mid-migration

As of commit `039f1a5` (2026-06-22) all routines are **paused**. During [[Infrastructure Eras]] era 2 they ran as GitHub Actions; those workflows carry `if: false`. The project is migrating back to Claude-orchestrated routines (era 3), and the `routines/*.md` prompts above are the era-3 definitions. Last live run: 2026-06-19.

Note: the midday note in older README/runner docs lists 1:30 PM; the current `routines/midday.md` prompt is **12:30 PM**. Earnings guard and afternoon-check are era-3 additions not present in the runner set.
