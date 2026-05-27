# Rocky — Autonomous AI Swing Trading Agent

An autonomous swing trading system for NSE/BSE that runs five daily routines on GitHub Actions. Gemini API handles macro research, chart vision analysis, and catalyst classification. A rules-based 5-factor momentum scorer screens 180+ Nifty 50 and Midcap 150 stocks. A 9+1 mechanical gate enforces every entry decision. Currently paper trading with ₹5,00,000 virtual capital.

---

## How It Works

```
Gemini API (macro research + chart vision + catalyst classification)
        ↓
Pre-market: score 180+ stocks on 5 momentum factors
        ↓
9+1 gate enforcement (regime, VIX, FII, earnings, sector concentration...)
        ↓
market_open: place orders via Upstox API v2
        ↓
midday: check trailing stops, trigger partial exits at +6%
        ↓
EOD: P&L snapshot → Telegram alert → Git commit (immutable audit trail)
        ↓
Weekly review: analyze closed trades, flag rule changes
```

Every decision is committed to Git with a timestamp. The system is fully reproducible — you can replay any trading day from the logs.

---

## Architecture

### 1. Daily Research Pipeline (Gemini-Orchestrated)

Each morning at 8:30 AM IST, the pre-market routine calls Gemini API to synthesize:
- SGX Nifty futures (overnight directional signal)
- India VIX (fear gauge)
- FII net flow (institutional positioning)
- Sector momentum (which sectors are leading/lagging)
- Catalyst classification: news events ranked HARD / MEDIUM / SOFT by market impact

Output is written to `memory/RESEARCH-LOG.md` and consumed by the market-open routine.

### 2. Momentum Scorer — Swing v3

Screens every stock in the Nifty 50 + Midcap 150 universe (180+ symbols) using five binary factors. Each factor contributes 20 points. Score ≥ 80 (4+ factors aligned) = BUY candidate.

| Factor | Condition | Points |
|--------|-----------|--------|
| Donchian breakout | Close ≥ 20-day high | 20 |
| Trend strength | ADX(14) > 25 | 20 |
| Sector relative strength | Sector index outperforms Nifty by >1pp over 10 days | 20 |
| Volume surge | Today's volume > 2.5× 20-day average | 20 |
| Price structure | Close > EMA(50) × 1.01 | 20 |

Pre-filters eliminate stocks before scoring: ADV < ₹50 Cr, 20-day volatility > 3.5%, or price below 200-day SMA.

### 3. 9+1 Execution Gates

All nine gates must pass before any order is placed. No discretion.

| Gate | Condition |
|------|-----------|
| Universe | Stock in Nifty 50 or Midcap 150 |
| Momentum | Score ≥ 80 |
| Catalyst | HARD or MEDIUM (LLM-classified) |
| Circuit gap | Not at upper circuit, gap < 18% |
| VIX | India VIX < 25 |
| Position sizing | Trade cost ≤ available cash (₹50,000 flat per trade) |
| FII flow | FII net > −₹3,500 Cr |
| Earnings guard | No earnings or board meeting within 7 days |
| Sector concentration | ≤ 2 open positions per sector |
| **+1 Regime gate** | **Block ALL entries when Nifty regime = bear** |

### 4. Regime Detection

Classifies the Nifty 50 market state daily using 20-day SMA slope:
- Bull: slope > +1.5%
- Bear: slope < −1.5%
- Sideways: between

A Markov persistence layer computes transition probabilities and long-run stationary distribution — regime calls are smoothed to avoid flip-flopping on borderline days. If regime = bear, the regime gate blocks all new entries regardless of momentum score.

### 5. Exit Rules (Swing v3)

| Condition | Action |
|-----------|--------|
| −5% from cost | Hard stop, close at market |
| +6% gain | Sell 50%, tighten trailing stop to −3% |
| +12% gain | Tighten trailing stop to −3% |
| 15 trading days held | Force close (momentum decays) |
| Thesis broken (fraud, catalyst invalid) | Close regardless of P&L |

Trailing stops only move in one direction — never loosened.

---

## Infrastructure

Five GitHub Actions routines run on a cron schedule at Mumbai market hours. Zero local machine dependency.

| Routine | IST Time | What It Does |
|---------|----------|--------------|
| `pre_market` | 8:30 AM Mon–Fri | Macro research, universe scan, earnings guard, candidate ranking |
| `market_open` | 9:20 AM Mon–Fri | Apply 9+1 gates, place orders, record trades |
| `midday` | 12:30 PM Mon–Fri | Check trailing stops, trigger partial exits |
| `eod` | 3:45 PM Mon–Fri | P&L snapshot, Telegram summary, Git commit |
| `weekly_review` | 4:00 PM Friday | Analyze closed trades, performance breakdown by regime/sector/VIX |
| `health_check` | Every 30 min | Alert via Telegram if a routine missed its window |

**Infrastructure cost: ₹0/month** (GitHub Actions free tier).

---

## Backtest Results

### POC v2 — Baseline Strategy (May–Oct 2025, 127 trading days)

| Metric | Value |
|--------|-------|
| Portfolio return | +12.31% |
| Nifty 50 return | +5.65% |
| Alpha | **+6.66%** |
| Closed trades | 15 |
| Win rate | 73% (11W / 4L) |
| Avg winner | +11.02% |
| Avg loser | −4.34% |
| Max drawdown | −3.5% |
| Best trade | MARUTI +22.75% |
| Worst trade | PAGEIND −7.18% |

Win rate by regime: Bull 91% (10/11), Sideways 0% (0/3), Bear 100% (1/1).

### Walk-Forward Validation (Phase B)

Trained parameters on three historical windows (2023–2024), then tested on holdout period (Nov 2024 – Apr 2025):

| | Training avg | Holdout |
|--|--|--|
| Return vs Nifty | +8.4% alpha | −6.57% alpha |
| Win rate | 50–74% | 28.6% |
| Max drawdown | −6–9% | −16.61% |

**Decision: revert to baseline.** Holdout underperformed by 13+ percentage points. Conclusion: parameters were overfitted to bull-regime conditions. No rule changes recommended until 20+ forward trades are logged under the current strategy.

---

## What's Proven vs Unproven

| Status | What |
|--------|------|
| ✅ Proven | POC v2: +6.66% alpha, 73% win rate, 127 trading days |
| ✅ Proven | GitHub Actions orchestration runs autonomously daily |
| ✅ Proven | Walk-forward validation ran and honestly caught overfitting |
| ✅ Proven | Upstox API v2 integration, paper order execution, P&L tracking |
| ✅ Proven | Telegram alerting, Git audit trail, regime detection |
| 🟡 Early | Swing v3 live (May 2026): 7 days, 9 open positions — needs 20 closed trades |
| 🟡 Early | Regime gate (bear-market block): added May 2026, not yet validated in a real bear |
| ❌ Not implemented | Deep learning / neural networks (TensorFlow in requirements but unused) |
| ❌ Blocked | FII gate historical data (NSE bhavcopy scrape blocked; gate auto-passes in backtest) |
| ❌ Deferred | Quarterly universe constituent updates (survivorship bias exists in backtests) |

The strategy has not been validated in live markets with real capital. Paper trading results may differ from live execution due to slippage, order rejection, and API latency.

---

## Tech Stack

| Layer | Tools |
|-------|-------|
| Orchestration | GitHub Actions (5 daily cron workflows) |
| LLM / Research | Gemini API (text + vision), Hermes-3 fallback via OpenRouter |
| Market data | yfinance (cached in Parquet, 7-day TTL), NSE bhavcopy |
| Broker | Upstox API v2 (paper trading mode; live-ready) |
| Signal generation | pandas, numpy, pandas-ta (ADX, EMA, Donchian) |
| Backtesting | Custom daily replay engine with as-of-date scoring |
| Alerting | Telegram Bot API |
| Audit trail | Git commits to `memory/` on every routine |
| Language | Python 3.12 |

---

## Repository Structure

```
Rocky-Trading-Bot/
├── .github/workflows/      # GitHub Actions: pre_market, market_open, midday, eod, weekly_review
├── models/
│   └── signal_generator.py # Swing v3 5-factor momentum scorer
├── scripts/
│   ├── runners/            # One file per routine (pre_market, market_open, midday, eod, weekly_review)
│   ├── broker.py           # Upstox API v2 wrapper
│   ├── regime_detector.py  # Nifty SMA slope + Markov persistence
│   ├── chart_analysis.py   # Candlestick PNG generation + Gemini vision
│   └── earnings_guard.py   # NSE corporate events check
├── backtest/
│   ├── engine/             # Daily replay engine, portfolio simulation, walk-forward validator
│   ├── config/             # poc_config.json, phase_b_config.json, swing_config.json
│   └── data/               # universe.json, ticker_aliases.json, price cache
├── memory/
│   ├── TRADING-STRATEGY.md # Current rules (Swing v3)
│   ├── RESEARCH-LOG.md     # Daily pre-market research output
│   ├── TRADE-LOG.md        # Verbose trade journal
│   ├── WEEKLY-REVIEW.md    # Weekly P&L and rule recommendations
│   ├── paper_portfolio.json# Current portfolio state
│   ├── trade-outcomes.json # Structured closed trade records
│   └── goal.yaml           # Success criteria and evaluation cadence
└── run.py                  # Entry point: python run.py <routine>
```

---

## Current Status

**Strategy:** Swing v3 (live since May 20, 2026)
**Portfolio:** ₹5,02,651 (started ₹5,00,000)
**Open positions:** 9 (capital fully deployed)
**Alpha vs Nifty (7-day):** +0.09% — too early to evaluate
**Next evaluation:** after 20 closed trades

---

## Setup

```bash
git clone https://github.com/arrya5/Rocky-Trading-Bot
cd Rocky-Trading-Bot
pip install -r requirements-runner.txt
cp env.template .env
# Fill in .env: GEMINI_API_KEY, UPSTOX credentials, TELEGRAM_BOT_TOKEN
python run.py pre_market   # run any routine locally
```

To run the POC backtest:
```bash
python backtest/run_poc.py
```

---

*Built and maintained by [Arrya Thakur](https://github.com/arrya5). Part of the [BLARAA Systems](https://blaraa-systems.vercel.app) portfolio.*
