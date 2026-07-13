---
type: system
tags: [system, data, research]
created: 2026-07-13
updated: 2026-07-13
source: [README.md, CLAUDE.md, memory/PROJECT-CONTEXT.md]
---

# Data Sources

What feeds Rocky's decisions. All free-tier — the infra experiment targeted **₹0/month** (see [[Infrastructure Eras]]).

## Market data

- **yfinance** — daily OHLCV for the 180+ stock universe and sector indices (`.NS` suffix, `^NSEI`, `^CNXIT`, etc.). Powers the [[Signal Generator]]. Cached in Parquet (7-day TTL) during backtests.
- **NSE bhavcopy** — end-of-day delivery % per symbol (`market_data.py delivery`). FII-gate historical scrape is blocked in backtest, so the gate auto-passes there.
- **NSE F&O option chain** — Nifty Put-Call Ratio (`market_data.py pcr`), informational only (euphoria/fear signal, not a hard gate).
- **Regime** — `regime_detector.py`: Nifty 20-day SMA slope + Markov persistence → bull/bear/sideways. See [[Regime Detection]].

## LLM research — Gemini API

Gemini is Rocky's sole LLM (Google Search grounded, free tier ~1500 req/day). Called via `scripts/research.sh`. It handles:

- **Macro research** — SGX Nifty, India VIX ([[India VIX]]), FII/DII net flow ([[FII-DII Flows]]), global cues, key events.
- **Catalyst classification** — news ranked HARD / MEDIUM / SOFT ([[Catalyst Tiers]]). A Gemini quota outage once silently returned SOFT for everything, auto-rejecting all trades; fixed with a deterministic keyword fallback (commit 2026-06-09).
- **Chart vision** — `chart_analysis.py` renders a candlestick PNG and asks Gemini Vision to confirm/contradict the BUY thesis.

> PROJECT-CONTEXT.md still names **Perplexity** as the research provider — stale. All research is Gemini now (Perplexity retired early). A dormant Hermes-3/OpenRouter fallback exists but is not used.

## Alerting & audit

- **Telegram Bot API** (`scripts/telegram.sh`) — mandatory alert after every buy, sell, stop, and EOD summary.
- **Git** — every routine commits `memory/` as the immutable audit trail. See [[Architecture]].
