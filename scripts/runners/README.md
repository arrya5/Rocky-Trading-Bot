# Rocky Runners (Gemini + GitHub Actions Edition)

This replaces Claude Code Remote (CCR) orchestration with Python scripts that use **Gemini 2.5 Flash** for LLM reasoning and run on **GitHub Actions** cron.

## Files

```
scripts/runners/
├── common.py           # Shared helpers: Gemini calls, Telegram, broker, parsers
├── pre_market.py       # 8:30 AM IST — research, scoring, candidate selection
├── market_open.py      # 9:20 AM IST — 9-point gate, place orders
├── midday.py           # 1:30 PM IST — stops, partial exits, news check
├── eod.py              # 3:45 PM IST — P&L snapshot, daily reflection
└── weekly_review.py    # 4:30 PM IST Friday — performance analyzer, qualitative review

.github/workflows/
├── pre_market.yml      # cron: 0 3 * * 1-5 (03:00 UTC)
├── market_open.yml     # cron: 50 3 * * 1-5 (03:50 UTC)
├── midday.yml          # cron: 0 8 * * 1-5 (08:00 UTC)
├── eod.yml             # cron: 15 10 * * 1-5 (10:15 UTC)
└── weekly_review.yml   # cron: 0 11 * * 5 (11:00 UTC Fridays)

requirements-runner.txt  # slim dependencies for CI (no tensorflow, no dotenv)
```

## Setup (one-time)

### 1. Add GitHub Secrets

Go to **Settings → Secrets and variables → Actions** in the repo:

| Secret name | Where to get it |
|---|---|
| `GEMINI_API_KEY` | https://aistudio.google.com/apikey (free tier) |
| `TELEGRAM_BOT_TOKEN` | Same as today's CCR bot |
| `TELEGRAM_CHAT_ID` | Same as today's CCR bot |
| `UPSTOX_ACCESS_TOKEN` | Only if going live; paper mode doesn't need it |

### 2. Push code to GitHub

```bash
git add scripts/runners/ .github/workflows/ requirements-runner.txt
git commit -m "feat: add Gemini-based runners + GitHub Actions workflows"
git push origin master
```

### 3. Verify workflows show up

Visit the **Actions** tab in your GitHub repo. You should see five workflows:
- Pre-Market Research
- Market Open Execution
- Midday Risk Scan
- EOD Daily Summary
- Weekly Strategy Review

Each can be manually triggered via `workflow_dispatch` ("Run workflow" button).

### 4. Test a single workflow manually

Trigger **Pre-Market Research** from the Actions tab. Watch the run logs. If you get a Telegram message → success.

### 5. Disable CCR routines

In claude.ai/code/routines, set each routine to `enabled: false`. This pauses them (no data lost). If anything breaks with GitHub Actions, re-enable in one click.

## How state is preserved

All memory files live in the GitHub repo:
- `memory/paper_portfolio.json` — cash + open positions
- `memory/trade-outcomes.json` — closed trades for learning
- `memory/TRADE-LOG.md` — human-readable trade log
- `memory/RESEARCH-LOG.md` — daily research entries
- `memory/WEEKLY-REVIEW.md` — weekly reviews

Each workflow:
1. Checks out the latest repo state
2. Runs the routine (reading + writing memory files)
3. Commits + pushes changes back to main

So the paper portfolio, trade history, and all learning data carry forward from CCR seamlessly. The CCR routines were doing exactly this — clone, modify memory files, commit, push. The new runners do the same; only the orchestrator changed.

## Concurrency

All workflows share the `concurrency: rocky-routine` group, so they queue and never overlap. If a pre-market run is still finishing at 9:20 AM IST, market-open waits.

## What Gemini handles vs Python handles

| Task | Done by |
|---|---|
| Macro research (VIX, FII, news, events) | Gemini (Google Search grounded) |
| Score universe + apply gates | Python (`models/signal_generator.py`) |
| Catalyst HARD/MEDIUM/SOFT classification | Gemini (structured JSON reasoning) |
| Chart pattern analysis | Gemini Vision (existing `chart_analysis.py`) |
| Earnings guard check | Python + NSE API |
| Place orders / track cash | Python (`scripts/broker.py`) |
| Daily reflection / biggest surprise | Gemini (structured reasoning) |
| Weekly qualitative review | Gemini |
| Performance analyzer | Python (`scripts/performance_analyzer.py`) |
| Apply rule changes | Python (only if `sufficient_data: true`) |

## Cost

**₹0/month.**
- GitHub Actions: free tier (2000 min/month). Rocky uses ~15-20 min/day = ~400-500 min/month.
- Gemini 2.5 Flash: free tier (1500 req/day). Rocky uses ~50-100 req/day.
- yfinance, Telegram, Upstox sandbox: all free.

## Troubleshooting

**Workflow shows ❌ "GEMINI_API_KEY not set":** Add the secret in repo settings.

**Pre-market message says VIX or FII "unknown":** Gemini's web search didn't return parseable numbers. Routine continues with conservative defaults (gate passes through). Check `memory/RESEARCH-LOG.md` for the raw text.

**Cron didn't fire at exact time:** GitHub Actions cron has 5-15 minute jitter on free tier. This is normal. Pre-market at 8:30 IST might fire 8:30-8:45.

**Two workflows committed at the same time (rare race):** `git pull --rebase` in the workflow handles this. If push still fails, the next routine's pull will reconcile.

**Want to roll back to CCR:** re-enable the CCR routines in claude.ai/code/routines. They will resume from current memory state. The GitHub Actions can be disabled by setting workflow file `on:` to comment out the schedule.
