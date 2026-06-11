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
| ❌ Disproven (so far) | Swing v3 forward: 30+ days, 7 closed, win rate 43%, EV −2.09%/trade, self-grade D. Walk-forward called it; live results confirmed |
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

## Current Status *(updated 2026-06-11)*

**Strategy:** Swing v3 (live since May 20, 2026)
**Portfolio:** ₹4,87,431 (started ₹5,00,000 → **−2.51% all-time**)
**Cash:** ₹3,70,664 (76% in cash)
**Open positions:** 2 (HINDALCO, ADANIPORTS)
**Closed trades:** 7 — see Live Track Record below
**Weekly-review self-grade:** **D** (fitness −0.875 / 1.0)
**Next evaluation:** after 20 closed trades; the revert criterion (win < 45% AND alpha < −3%) is currently knocking at win 43% / alpha −2.51%.

---

## Live Track Record *(paper, ₹5,00,000 base)*

The bot has been live in paper mode for 30+ trading days since the Swing v3 conversion. Reporting the honest result, not the optimistic one.

| Symbol | Entry | Exit | Days held | P&L | Exit reason |
|---|---|---|---|---|---|
| TECHM | 2026-05-20 | 2026-05-29 | 9 | **+1.47%** | thesis_broken |
| BHARTIARTL | 2026-05-20 | 2026-06-04 | 15 | −5.24% | hard_stop |
| TATACONSUM | 2026-05-20 | 2026-06-05 | 16 | −5.22% | hard_stop |
| JSWSTEEL | 2026-05-20 | 2026-06-10 | 21 | **+1.60%** | max_hold |
| MANAPPURAM | 2026-05-20 | 2026-06-10 | 21 | −7.00% | max_hold |
| RADICO | 2026-05-20 | 2026-06-10 | 21 | −3.60% | max_hold |
| BAJAJ-AUTO | 2026-05-20 | 2026-06-10 | 21 | **+3.38%** | max_hold |

**Win rate: 43% (3W / 4L)** · Avg winner **+2.15%** · Avg loser **−5.27%** · **Expected value per trade: −2.09%**

What the numbers say: the strategy is losing about 2% per trade on average, with losers nearly 2.5× the size of winners. The bot's own self-grading correctly flags this — fitness score −0.875 against the goal in `memory/goal.yaml`. The 30-day kill-switch is approaching trigger. **This is what an honest self-evaluating system looks like — it tells you when it isn't working.**

---

## Lessons Learned

The strategy is the experiment; the engineering is the asset. After 30+ live days, what the project actually proved:

1. **The original +5%/month goal was unattainable from day one.** Under a delivery-only, long-only, no-F&O mandate, +60%/year is hedge-fund-elite territory. A goal you mathematically can't hit makes every honest result look like failure when the result is just hitting reality. *Fix in next iteration: set a realistic +1.5–2%/month target so the self-evaluation grades a real bar, not an aspirational one.*

2. **Backtest results don't transfer unless walk-forward says so.** POC v2 showed +12.31% / 73% win rate (May–Oct 2025). Walk-forward correctly flagged overfit. Forward results confirmed walk-forward, not POC. **Trust the walk-forward, not the in-sample.**

3. **Mechanical signals on NSE midcaps may have no durable edge.** Three strategy classes — position trading, swing v3, sector rotation — all collapsed forward. The lesson isn't *"this strategy was wrong"*; it's *"this category was wrong."* The next system will test the **AI-reasoning-driven** path where the edge is the reasoning itself, not the rule.

4. **AI dependencies are brittle without deterministic backstops.** The catalyst classifier silently auto-rejected every trade for days when Gemini hit its quota — because the failure path returned `SOFT` for everything. Fixed with a keyword-based fallback. *Generalisable lesson: never let an LLM failure silently kill behavior; always have a deterministic floor.*

5. **The infrastructure was the right bet; the strategy was the experiment.** Because the measuring instrument was built before betting on a strategy, the strategy can be swapped out without rebuilding anything. That's the design pattern, not the trading result, that carries forward.

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
