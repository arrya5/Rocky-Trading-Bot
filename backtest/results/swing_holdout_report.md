# Swing Backtest — holdout

_Generated: 2026-05-19T20:37:21_

## Setup

- Period: 2024-11-01 -> 2025-04-30 (121 trading days)
- Starting capital: Rs 500,000
- Max hold: 10 days | ATR-adaptive stops/targets per trade

## Headline

> **Started Rs 500,000. Ended Rs 420,410 (-15.92%). Nifty over same period: +0.12%. Alpha: -16.04%.**

## Numbers

| Metric | Value |
|---|---|
| Total trades | 185 |
| Win rate | 45.9% |
| Avg winner | +2.94% |
| Avg loser | -3.89% |
| Best trade | JUBLFOOD +8.40% (10d) |
| Worst trade | IDFCFIRSTB -12.13% (3d) |
| Max drawdown | -21.29% |
| Total Rs P&L | Rs -80,117 |
| Total Rs deployed | Rs 10,647,931 |
| Return on deployed | -0.75% |
| Avg days held (closed only) | 7.5 days

## Exit reasons

| Reason | Count |
|---|---|
| max_hold_exit | 92 |
| hard_stop | 53 |
| partial_then_stop | 19 |
| trailing_stop | 15 |
| open_at_end | 6 |

## Regime breakdown

| Regime | Trades | Win % | Avg P&L |
|---|---|---|---|
| bear | 96 | 49% | -0.60% |
| sideways | 79 | 43% | -1.09% |
| bull | 10 | 40% | +0.56% |

## Skip log

| Reason | Count |
|---|---|
| gate6_insufficient_cash_or_qty | 260 |
| gate9_sector_full | 244 |
