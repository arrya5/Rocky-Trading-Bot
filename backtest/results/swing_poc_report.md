# Swing Backtest — poc

_Generated: 2026-05-19T20:36:24_

## Setup

- Period: 2025-05-01 -> 2025-10-31 (127 trading days)
- Starting capital: Rs 500,000
- Max hold: 10 days | ATR-adaptive stops/targets per trade

## Headline

> **Started Rs 500,000. Ended Rs 487,668 (-2.47%). Nifty over same period: +5.65%. Alpha: -8.12%.**

## Numbers

| Metric | Value |
|---|---|
| Total trades | 162 |
| Win rate | 45.7% |
| Avg winner | +2.93% |
| Avg loser | -2.71% |
| Best trade | MCX +12.62% (10d) |
| Worst trade | INDUSINDBK -7.90% (7d) |
| Max drawdown | -9.84% |
| Total Rs P&L | Rs -12,934 |
| Total Rs deployed | Rs 10,021,748 |
| Return on deployed | -0.13% |
| Avg days held (closed only) | 8.9 days

## Exit reasons

| Reason | Count |
|---|---|
| max_hold_exit | 110 |
| hard_stop | 30 |
| trailing_stop | 13 |
| open_at_end | 7 |
| partial_then_stop | 2 |

## Regime breakdown

| Regime | Trades | Win % | Avg P&L |
|---|---|---|---|
| sideways | 80 | 49% | +0.05% |
| bull | 64 | 39% | -0.57% |
| bear | 18 | 56% | +0.60% |

## Skip log

| Reason | Count |
|---|---|
| gate6_insufficient_cash_or_qty | 431 |
| gate9_sector_full | 289 |
