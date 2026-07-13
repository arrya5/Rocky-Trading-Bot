---
type: system
tags: [system, infrastructure, history]
created: 2026-07-13
updated: 2026-07-13
source: [README.md, scripts/runners/README.md, .github/workflows/pre_market.yml]
---

# Infrastructure Eras

Rocky's strategy stayed the experiment; the orchestrator underneath it was swapped three times. The [[Routines]] logic barely changed — only *who ran it* did. The driving goal was a **₹0/month** self-hosting infra experiment.

## Era 1 — Local Claude routines (2026-05-17 → ~06-08)

Claude Code Remote (CCR) orchestration. Claude ran each routine directly: clone → read memory → decide → commit → push. This era placed all nine opening trades (2026-05-20/21, see [[2026-W21]]) and carried the portfolio through its first stops.

## Era 2 — GitHub Actions + Gemini runners (~2026-06-11 → 06-19)

Migrated to Python runners (`scripts/runners/*.py`) driven by **Gemini 2.5 Flash**, fired on GitHub Actions cron at Mumbai market hours. Motivation: zero local-machine dependency and free-tier everything (GitHub Actions ~400 min/month, Gemini ~50–100 req/day). Five workflows (`pre_market`, `market_open`, `midday`, `eod`, `weekly_review`) plus a 30-min `health_check`. README was updated 2026-06-11 with the live track record. Last routine actually ran 2026-06-19.

## Era 3 — Migrating back to Claude routines (commit `039f1a5`, 2026-06-22 → present)

All GitHub Actions jobs disabled via `if: false` in their workflow YAML (annotated "Gemini routines retired, migrating back to Claude routines"). The `routines/*.md` prompts are the era-3, Claude-orchestrated definitions — now including an **afternoon-check** (2:30 PM) and an explicit **earnings guard** step not present in the Gemini runners. As of 2026-07-13 the routines are paused mid-migration; no trading has occurred since 2026-06-19.

Throughout all three eras: same [[Signal Generator]], same [[9-Point Buy Gate]], same `memory/` Git-committed state. That portability — swap the runner, keep the instrument — is the design lesson the project actually proved. See [[Timeline]].
