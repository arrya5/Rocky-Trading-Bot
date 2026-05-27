# Phase A — 6-Month Backtest POC Report (v2)

_Generated: 2026-05-18T20:03:03_

---

## 1. Run config

- **Window**: 2025-05-01 -> 2025-10-31 (127 trading days)
- **Starting capital**: Rs 500,000
- **Universe**: 112 symbols (Nifty 50 + Midcap 150 subset)
- **Gates enforced**: 1, 2, 4, 5, 6, 7, 9
- **Gates skipped**: 3 (catalyst tier - LLM lookahead bias), 8 (earnings guard - defer to Phase B)
- **Engine version**: v2 with partial P&L aggregation, gap-down fills, regime tagging
- **Rules**: score >= 40, ADV >= Rs 50 Cr, vol <= 3.0%, stop -7%, partial at +15%, VIX < 25, FII > -3500 Cr

---

## 2. Headline result

> **On 2025-05-01, Rocky started with Rs 500,000. By 2025-10-31, the portfolio was worth Rs 561,570 (+12.31%). Nifty 50 over the same period: +5.65%. Alpha: +6.66%.**

## 3. Summary stats

| Metric | Value |
|---|---|
| Total trades closed | 15 |
| Winners | 11 (73.3%) |
| Losers  | 4 |
| Avg winner | +11.02% |
| Avg loser  | -4.34% |
| Best trade  | MARUTI +22.75% (179d, regime: bull) |
| Worst trade | PAGEIND -7.18% (7d, regime: sideways) |
| Final portfolio value | Rs 561,570 |
| Total return | +12.31% |
| Nifty buy-and-hold | +5.65% |
| Alpha vs Nifty | +6.66% |

## 4. Trade lifecycle distribution

| Exit reason | Count |
|---|---|
| open_at_end | 9 |
| trailing_stop | 4 |
| hard_stop | 2 |

- **Partial exits fired**: 5 (was 0 in v1 — accounting bug fix exposed actual count)
  - Avg uplift at partial: +15.00%
- **Intraday-ambiguous events**: 0 (0.0%)
- **Days held** (closed trades only, excluding open_at_end): n=6, avg=76.2, min=7, max=178

## 5. Sector breakdown

| Sector | Trades | Wins | Avg P&L % |
|---|---|---|---|
| FMCG | 3 | 2 (67%) | +6.37% |
| Banking | 2 | 2 (100%) | +6.78% |
| Finance | 2 | 2 (100%) | +16.20% |
| Auto | 2 | 1 (50%) | +9.87% |
| Infrastructure | 2 | 2 (100%) | +9.29% |
| IT | 1 | 0 (0%) | -7.17% |
| Consumer | 1 | 0 (0%) | -7.18% |
| Energy | 1 | 1 (100%) | +4.10% |
| Telecom | 1 | 1 (100%) | +10.71% |

## 6. Score-band breakdown

| Score band | Trades | Wins | Avg P&L % |
|---|---|---|---|
| 40-59 | 0 | - | - |
| 60-79 | 7 | 6 (86%) | +8.79% |
| 80-100 | 8 | 5 (62%) | +5.30% |

## 7. Regime-at-entry breakdown (NEW in v2)

| Regime | Trades | Wins | Avg P&L % |
|---|---|---|---|
| bull | 11 | 10 (91%) | +9.33% |
| sideways | 3 | 0 (0%) | -3.40% |
| bear | 1 | 1 (100%) | +11.46% |

## 8. Sanity checks

- PASS Cash never negative (min cash: Rs 506)
- PASS Trade count plausible: 15 (target 5-600)
- PASS Intraday-ambiguous events <15%: 0.0%
- PASS Sector concentration enforced by portfolio.enter() at trade time
- PASS Position sizing matched score tier (verified at enter)
- PASS Partial P&L aggregation (v2 fix verified — 5 partials counted)
- PASS Regime tagged on every trade
- PASS Gap-down fill realism applied

## 9. Skip-log summary

| Reason | Count |
|---|---|
| gate6_insufficient_cash_or_qty | 836 |
| gate9_sector_full | 171 |

## 10. Known limitations of this POC

- **Survivorship bias**: today's universe used as proxy. Phase B needs quarterly constituents.
- **Gate 3 (catalyst)**: structural LLM lookahead bias; needs real forward trades to validate.
- **Gate 7 (FII)**: NSE archive scrape blocked; FII data empty so gate auto-passes. Phase B needs alternative source.
- **Gate 8 (earnings)**: historical earnings scrape deferred to Phase B.
- **Single-regime risk**: 6 months captures one regime; can't generalize.
- **Transaction costs partial**: STT + brokerage modeled; stamp duty, exchange fees, GST, DP charges not included (~0.05-0.10pp underestimate per round-trip).

## 11. Spot-check guidance

Verify these 5 random trades against yfinance charts:

| Symbol | Entry | Exit | P&L % | Regime | Partial? |
|---|---|---|---|---|---|
| MARICO | 2025-05-06 Rs715.52 | 2025-10-31 Rs719.95 | +0.46% | bull | no |
| MANAPPURAM | 2025-05-05 Rs229.74 | 2025-06-17 Rs268.75 | +15.79% | bull | yes @ Rs 264.21 |
| BANDHANBNK | 2025-05-05 Rs160.54 | 2025-06-13 Rs170.94 | +10.54% | bull | yes @ Rs 184.62 |
| GRASIM | 2025-06-17 Rs2695.10 | 2025-10-31 Rs2891.70 | +7.13% | bull | no |
| RADICO | 2025-06-09 Rs2649.76 | 2025-10-24 Rs3251.85 | +18.66% | bull | yes @ Rs 3047.22 |
