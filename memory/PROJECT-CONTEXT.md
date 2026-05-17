# Project Context — Indian AI Trading Bot
*Initialized: 2026-05-17*

## What This Bot Does
An autonomous AI trading agent that runs on Claude Code cloud routines. It:
1. Researches Indian market conditions each morning via Perplexity
2. Generates trade signals using a GRU deep learning model (trained on NSE price data)
3. Enforces strict buy-side rules before placing any order
4. Manages positions intraday (stop losses, trailing stops)
5. Sends all alerts via Telegram
6. Keeps all state in Git — every trade, every decision is logged

## Architecture
```
Perplexity API (market research)
        ↓
RESEARCH-LOG.md (trade ideas + catalysts)
        ↓
Claude Code Routine (cloud-hosted, fires on cron)
        ↓
Buy-side Gate (9 rules — all must pass)
        ↓
models/signal_generator.py (GRU signal: BUY/SELL/HOLD)
        ↓
scripts/broker.py (Upstox API v2 wrapper)
        ↓
NSE order placed → TRADE-LOG.md updated
        ↓
scripts/telegram.sh (Telegram notification)
        ↓
git commit (all memory files → permanent record)
```

## Key Parameters
- Capital: ₹5,00,000
- Max position: ₹1,00,000 (20%)
- Max positions: 5
- Stop loss: -7% hard
- Trailing stop: 10% default
- Universe: Nifty 50 + Nifty Midcap 150
- Broker: Upstox (delivery CNC, paper trading mode initially)

## Routine Schedule (IST)
| Routine         | Time          | Purpose                           |
|-----------------|---------------|-----------------------------------|
| pre-market      | 8:30 AM       | Perplexity research, write ideas  |
| market-open     | 9:20 AM       | Validate ideas, place orders      |
| midday          | 12:30 PM      | Scan positions, manage stops      |
| daily-summary   | 3:45 PM       | EOD P&L, Telegram report, commit  |
| weekly-review   | 4:00 PM Fri   | Full week analysis, strategy check|

## Technology Stack
- Claude Code cloud routines (orchestrator)
- Python 3.12 + TensorFlow 2.x (GRU model)
- Upstox API v2 (broker)
- yfinance (market data via Yahoo Finance, .NS suffix)
- Gemini API + Google Search grounding (market research, 1,500 free requests/day)
- Telegram Bot API
- Git (memory/state store)

## Mode
- **Current**: PAPER TRADING (sandbox)
- Switch to live: change PAPER_TRADING=false in .env and set live Upstox credentials

## Important Indian Market Notes
- Circuit limits: stocks freeze at ±5%, ±10%, or ±20% — always check before entry
- FII/DII flow is a key macro signal — check daily in pre-market
- India VIX > 20 = high fear = no new positions
- SGX Nifty (Singapore exchange) = best premarket indicator for Nifty gap-up/gap-down
- RBI policy dates are high-impact events — avoid new positions on MPC meeting days
- Results season: Q1 (Jul-Aug), Q2 (Oct-Nov), Q3 (Jan-Feb), Q4 (Apr-May)
