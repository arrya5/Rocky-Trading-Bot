# Trade Verification — `poc_trades`

_Generated: 2026-05-18T20:03:08_

## Summary

- **Trades audited**: 15
- **Total events checked**: 35 (entries + partials + exits)
- **PASS**: 35 (100.0%)
- **FAIL**: 0
- **NO_DATA**: 0

## Rules audit

- **Sector cap (≤2 per sector)**: PASS
- **No duplicate entries while open**: PASS
- **Cash never negative**: PASS (min cash: Rs 506.35)

## Skipped-candidate spot-check

Sampled 10 'insufficient cash' skips and re-scored each. **10/10 confirmed as valid BUY signals.**

| Symbol | Skip date | Re-score result |
|---|---|---|
| SBIN | 2025-09-19 | PASS: re-scored 2025-09-18 -> BUY 80/100 (sector Banking, suggested size Rs 70,000) |
| NUVAMA | 2025-06-02 | PASS: re-scored 2025-05-30 -> BUY 80/100 (sector Fin Services, suggested size Rs 70,000) |
| RADICO | 2025-05-13 | PASS: re-scored 2025-05-12 -> BUY 100/100 (sector FMCG, suggested size Rs 70,000) |
| AXISBANK | 2025-10-13 | PASS: re-scored 2025-10-10 -> BUY 80/100 (sector Banking, suggested size Rs 70,000) |
| PAGEIND | 2025-07-04 | PASS: re-scored 2025-07-03 -> BUY 80/100 (sector Consumer, suggested size Rs 70,000) |
| TITAN | 2025-07-01 | PASS: re-scored 2025-06-30 -> BUY 100/100 (sector Consumer, suggested size Rs 70,000) |
| M&M | 2025-06-26 | PASS: re-scored 2025-06-25 -> BUY 80/100 (sector Auto, suggested size Rs 70,000) |
| GRASIM | 2025-06-11 | PASS: re-scored 2025-06-10 -> BUY 100/100 (sector Infrastructure, suggested size Rs 70,000) |
| HINDALCO | 2025-10-10 | PASS: re-scored 2025-10-09 -> BUY 80/100 (sector Metals, suggested size Rs 70,000) |
| MRF | 2025-05-28 | PASS: re-scored 2025-05-27 -> BUY 80/100 (sector Auto, suggested size Rs 70,000) |

## Price verification — all events

| # | Symbol | Event | Date | Sim Price | yf Open | yf High | yf Low | yf Close | Status |
|---|---|---|---|---|---|---|---|---|---|
| 1 | BANDHANBNK | ENTRY | 2025-05-05 | Rs 160.54 | 160.54 | 164.40 | 159.85 | 162.91 | PASS |
| 1 | BANDHANBNK | PARTIAL | 2025-06-09 | Rs 184.62 | 173.71 | 185.76 | 173.40 | 184.55 | PASS |
| 1 | BANDHANBNK | EXIT (trailing_stop) | 2025-06-13 | Rs 170.94 | 170.94 | 175.29 | 170.94 | 173.60 | PASS |
| 2 | MANAPPURAM | ENTRY | 2025-05-05 | Rs 229.74 | 229.74 | 230.86 | 227.10 | 227.86 | PASS |
| 2 | MANAPPURAM | PARTIAL | 2025-06-09 | Rs 264.21 | 249.21 | 264.88 | 248.32 | 262.92 | PASS |
| 2 | MANAPPURAM | EXIT (trailing_stop) | 2025-06-17 | Rs 268.75 | 275.46 | 276.82 | 267.02 | 268.02 | PASS |
| 3 | INFY | ENTRY | 2025-06-09 | Rs 1554.21 | 1554.21 | 1564.06 | 1547.31 | 1549.18 | PASS |
| 3 | INFY | EXIT (hard_stop) | 2025-08-01 | Rs 1445.41 | 1471.37 | 1476.10 | 1443.40 | 1447.44 | PASS |
| 4 | PAGEIND | ENTRY | 2025-08-01 | Rs 47645.70 | 47645.70 | 47645.70 | 46027.32 | 46334.16 | PASS |
| 4 | PAGEIND | EXIT (hard_stop) | 2025-08-08 | Rs 44310.50 | 45032.53 | 45032.53 | 43374.56 | 44408.94 | PASS |
| 5 | RADICO | ENTRY | 2025-06-09 | Rs 2649.76 | 2649.76 | 2652.05 | 2617.20 | 2646.16 | PASS |
| 5 | RADICO | PARTIAL | 2025-09-19 | Rs 3047.22 | 3016.90 | 3067.00 | 3003.00 | 3052.50 | PASS |
| 5 | RADICO | EXIT (trailing_stop) | 2025-10-24 | Rs 3251.85 | 3290.90 | 3326.90 | 3208.10 | 3220.00 | PASS |
| 6 | BAJFINANCE | ENTRY | 2025-05-05 | Rs 882.31 | 882.31 | 897.76 | 881.16 | 887.72 | PASS |
| 6 | BAJFINANCE | PARTIAL | 2025-09-15 | Rs 1014.65 | 999.00 | 1025.70 | 998.10 | 1009.85 | PASS |
| 6 | BAJFINANCE | EXIT (trailing_stop) | 2025-10-30 | Rs 1047.38 | 1063.00 | 1066.80 | 1045.00 | 1052.30 | PASS |
| 7 | RELIANCE | ENTRY | 2025-05-05 | Rs 1425.31 | 1425.31 | 1433.77 | 1421.22 | 1425.61 | PASS |
| 7 | RELIANCE | EXIT (open_at_end) | 2025-10-31 | Rs 1486.40 | 1490.40 | 1497.50 | 1482.30 | 1486.40 | PASS |
| 8 | HDFCBANK | ENTRY | 2025-05-05 | Rs 956.57 | 956.57 | 962.98 | 953.26 | 955.48 | PASS |
| 8 | HDFCBANK | EXIT (open_at_end) | 2025-10-31 | Rs 987.30 | 994.00 | 1004.45 | 981.15 | 987.30 | PASS |
| 9 | BHARTIARTL | ENTRY | 2025-05-05 | Rs 1852.51 | 1852.51 | 1857.97 | 1833.87 | 1850.53 | PASS |
| 9 | BHARTIARTL | EXIT (open_at_end) | 2025-10-31 | Rs 2054.50 | 2056.00 | 2073.80 | 2051.70 | 2054.50 | PASS |
| 10 | MARUTI | ENTRY | 2025-05-05 | Rs 12356.26 | 12356.26 | 12356.26 | 12229.63 | 12324.61 | PASS |
| 10 | MARUTI | PARTIAL | 2025-08-19 | Rs 14209.70 | 14070.00 | 14270.00 | 13979.00 | 14250.00 | PASS |
| 10 | MARUTI | EXIT (open_at_end) | 2025-10-31 | Rs 16186.00 | 16204.00 | 16516.00 | 15949.00 | 16186.00 | PASS |
| 11 | MARICO | ENTRY | 2025-05-06 | Rs 715.52 | 715.52 | 720.52 | 706.51 | 713.00 | PASS |
| 11 | MARICO | EXIT (open_at_end) | 2025-10-31 | Rs 719.95 | 721.50 | 728.65 | 718.65 | 719.95 | PASS |
| 12 | GRASIM | ENTRY | 2025-06-17 | Rs 2695.10 | 2695.10 | 2696.49 | 2655.34 | 2661.72 | PASS |
| 12 | GRASIM | EXIT (open_at_end) | 2025-10-31 | Rs 2891.70 | 2950.40 | 2954.40 | 2880.00 | 2891.70 | PASS |
| 13 | LT | ENTRY | 2025-08-11 | Rs 3610.00 | 3610.00 | 3676.90 | 3600.00 | 3668.40 | PASS |
| 13 | LT | EXIT (open_at_end) | 2025-10-31 | Rs 4030.90 | 4001.10 | 4045.90 | 3980.20 | 4030.90 | PASS |
| 14 | M&M | ENTRY | 2025-09-15 | Rs 3590.00 | 3590.00 | 3603.40 | 3526.60 | 3530.30 | PASS |
| 14 | M&M | EXIT (open_at_end) | 2025-10-31 | Rs 3487.20 | 3516.10 | 3526.70 | 3483.70 | 3487.20 | PASS |
| 15 | TATACONSUM | ENTRY | 2025-10-24 | Rs 1163.30 | 1163.30 | 1163.30 | 1144.40 | 1155.30 | PASS |
| 15 | TATACONSUM | EXIT (open_at_end) | 2025-10-31 | Rs 1165.00 | 1171.00 | 1183.50 | 1157.80 | 1165.00 | PASS |

## Failed events detail (if any)

_No failures._

## How to spot-check manually

For any row above, open yfinance.com (or `yf.Ticker('SYMBOL.NS').history(...)`) for the listed date. 
Compare yf Open/High/Low/Close with the values shown here. If they match, the engine read real data correctly.
