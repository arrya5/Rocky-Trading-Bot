---
type: system
tags: [system, broker, execution]
created: 2026-07-13
updated: 2026-07-13
source: [scripts/broker.py, CLAUDE.md, memory/PROJECT-CONTEXT.md]
---

# Broker - Upstox

`scripts/broker.py` wraps the Upstox API v2. It is the only path to place, cancel, or close orders and to read account/positions/quotes. Commands: `account`, `positions`, `quote SYMBOL`, `order '<json>'`, `cancel`, `close SYMBOL`.

## Paper trading mode

`PAPER_TRADING=true` is set. Orders are **simulated** — no real money moves and no live Upstox token is needed. Portfolio state lives in `memory/paper_portfolio.json` (cash + open positions), which every routine reads and writes, then commits to Git. Closed trades also land in `trade-outcomes.json` (read by the performance analyzer / [[Fitness Score]]).

Switch to live: set `PAPER_TRADING=false` and supply real Upstox credentials via `scripts/auth.py` (token generation/refresh). Integration is proven end-to-end in paper mode; live has never run with real capital.

## Order format

```bash
python scripts/broker.py order '{"symbol":"RELIANCE","qty":10,"side":"buy","type":"market","product":"D"}'
```

- `product`: always **"D"** (delivery / CNC) — never intraday, never F&O.
- `side`: `buy` | `sell`
- `type`: `market` (preferred) | `limit`

Position sizing is a flat ₹50,000 per trade (the [[9-Point Buy Gate]] Gate 6), capped so cost ≤ available cash; hard ceiling ₹1,00,000 per position.

> **Stale note**: PROJECT-CONTEXT.md still lists v1 parameters (₹1,00,000 max position at 20%, 5-position cap, −7% stop). Current [[Swing v3]] uses flat ₹50k sizing, no position cap in paper mode, and a −5% [[Hard Stop]].

Orders are placed only by the market-open [[Routines|routine]]; every fill triggers a mandatory Telegram alert (see [[Data Sources]]).
