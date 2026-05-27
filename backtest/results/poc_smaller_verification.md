# Trade Verification — `poc_smaller_trades`

_Generated: 2026-05-18T20:03:17_

## Summary

- **Trades audited**: 25
- **Total events checked**: 59 (entries + partials + exits)
- **PASS**: 59 (100.0%)
- **FAIL**: 0
- **NO_DATA**: 0

## Rules audit

- **Sector cap (≤2 per sector)**: PASS
- **No duplicate entries while open**: PASS
- **Cash never negative**: PASS (min cash: Rs 110.22)

## Skipped-candidate spot-check

Sampled 10 'insufficient cash' skips and re-scored each. **10/10 confirmed as valid BUY signals.**

| Symbol | Skip date | Re-score result |
|---|---|---|
| ONGC | 2025-06-19 | PASS: re-scored 2025-06-18 -> BUY 80/100 (sector Energy, suggested size Rs 70,000) |
| PAGEIND | 2025-05-16 | PASS: re-scored 2025-05-15 -> BUY 80/100 (sector Consumer, suggested size Rs 70,000) |
| JSWSTEEL | 2025-08-01 | PASS: re-scored 2025-07-31 -> BUY 100/100 (sector Metals, suggested size Rs 70,000) |
| ICICIBANK | 2025-07-24 | PASS: re-scored 2025-07-23 -> BUY 80/100 (sector Banking, suggested size Rs 70,000) |
| NYKAA | 2025-07-16 | PASS: re-scored 2025-07-15 -> BUY 80/100 (sector Consumer, suggested size Rs 70,000) |
| HDFCLIFE | 2025-06-25 | PASS: re-scored 2025-06-24 -> BUY 80/100 (sector Finance, suggested size Rs 70,000) |
| APOLLOHOSP | 2025-06-17 | PASS: re-scored 2025-06-16 -> BUY 80/100 (sector Other, suggested size Rs 70,000) |
| M&M | 2025-06-12 | PASS: re-scored 2025-06-11 -> BUY 80/100 (sector Auto, suggested size Rs 70,000) |
| TORNTPHARM | 2025-09-23 | PASS: re-scored 2025-09-22 -> BUY 100/100 (sector Pharma, suggested size Rs 70,000) |
| NHPC | 2025-05-20 | PASS: re-scored 2025-05-19 -> BUY 80/100 (sector Energy, suggested size Rs 70,000) |

## Price verification — all events

| # | Symbol | Event | Date | Sim Price | yf Open | yf High | yf Low | yf Close | Status |
|---|---|---|---|---|---|---|---|---|---|
| 1 | ADANIENT | ENTRY | 2025-05-06 | Rs 2452.78 | 2452.78 | 2461.98 | 2342.34 | 2352.83 | PASS |
| 1 | ADANIENT | EXIT (hard_stop) | 2025-05-08 | Rs 2281.09 | 2360.83 | 2366.63 | 2258.88 | 2284.17 | PASS |
| 2 | BANDHANBNK | ENTRY | 2025-05-05 | Rs 160.54 | 160.54 | 164.40 | 159.85 | 162.91 | PASS |
| 2 | BANDHANBNK | PARTIAL | 2025-06-09 | Rs 184.62 | 173.71 | 185.76 | 173.40 | 184.55 | PASS |
| 2 | BANDHANBNK | EXIT (trailing_stop) | 2025-06-13 | Rs 170.94 | 170.94 | 175.29 | 170.94 | 173.60 | PASS |
| 3 | MANAPPURAM | ENTRY | 2025-05-05 | Rs 229.74 | 229.74 | 230.86 | 227.10 | 227.86 | PASS |
| 3 | MANAPPURAM | PARTIAL | 2025-06-09 | Rs 264.21 | 249.21 | 264.88 | 248.32 | 262.92 | PASS |
| 3 | MANAPPURAM | EXIT (trailing_stop) | 2025-06-17 | Rs 268.75 | 275.46 | 276.82 | 267.02 | 268.02 | PASS |
| 4 | TCS | ENTRY | 2025-06-18 | Rs 3431.78 | 3431.78 | 3450.21 | 3357.67 | 3365.76 | PASS |
| 4 | TCS | EXIT (hard_stop) | 2025-07-11 | Rs 3191.56 | 3218.02 | 3252.25 | 3180.18 | 3184.96 | PASS |
| 5 | HCLTECH | ENTRY | 2025-06-13 | Rs 1597.58 | 1597.58 | 1640.73 | 1596.23 | 1625.67 | PASS |
| 5 | HCLTECH | EXIT (hard_stop) | 2025-07-17 | Rs 1485.75 | 1499.38 | 1502.45 | 1479.05 | 1480.49 | PASS |
| 6 | DIVISLAB | ENTRY | 2025-05-06 | Rs 6082.30 | 6082.30 | 6150.49 | 5942.94 | 6133.07 | PASS |
| 6 | DIVISLAB | PARTIAL | 2025-07-08 | Rs 6994.65 | 6970.26 | 7039.45 | 6879.67 | 6906.55 | PASS |
| 6 | DIVISLAB | EXIT (trailing_stop) | 2025-07-29 | Rs 6505.03 | 6580.00 | 6688.00 | 6473.00 | 6676.50 | PASS |
| 7 | MAXHEALTH | ENTRY | 2025-05-07 | Rs 1121.71 | 1121.71 | 1166.65 | 1121.71 | 1150.67 | PASS |
| 7 | MAXHEALTH | PARTIAL | 2025-06-27 | Rs 1289.96 | 1268.54 | 1295.31 | 1253.65 | 1277.83 | PASS |
| 7 | MAXHEALTH | EXIT (trailing_stop) | 2025-08-26 | Rs 1199.66 | 1212.00 | 1217.80 | 1177.40 | 1183.40 | PASS |
| 8 | PAGEIND | ENTRY | 2025-08-26 | Rs 46263.93 | 46263.93 | 46571.83 | 44913.16 | 45196.23 | PASS |
| 8 | PAGEIND | EXIT (hard_stop) | 2025-09-22 | Rs 43025.46 | 43254.49 | 43527.63 | 43006.19 | 43110.48 | PASS |
| 9 | M&M | ENTRY | 2025-07-17 | Rs 3186.30 | 3186.30 | 3238.00 | 3171.00 | 3195.00 | PASS |
| 9 | M&M | PARTIAL | 2025-09-09 | Rs 3664.25 | 3702.20 | 3723.80 | 3673.10 | 3696.30 | PASS |
| 9 | M&M | EXIT (trailing_stop) | 2025-09-26 | Rs 3407.75 | 3510.00 | 3547.50 | 3391.60 | 3396.50 | PASS |
| 10 | ICICIBANK | ENTRY | 2025-07-29 | Rs 1468.57 | 1468.57 | 1478.39 | 1464.10 | 1474.82 | PASS |
| 10 | ICICIBANK | EXIT (hard_stop) | 2025-09-26 | Rs 1365.77 | 1368.00 | 1372.70 | 1357.00 | 1359.60 | PASS |
| 11 | RADICO | ENTRY | 2025-06-09 | Rs 2649.76 | 2649.76 | 2652.05 | 2617.20 | 2646.16 | PASS |
| 11 | RADICO | PARTIAL | 2025-09-19 | Rs 3047.22 | 3016.90 | 3067.00 | 3003.00 | 3052.50 | PASS |
| 11 | RADICO | EXIT (trailing_stop) | 2025-10-24 | Rs 3251.85 | 3290.90 | 3326.90 | 3208.10 | 3220.00 | PASS |
| 12 | BAJFINANCE | ENTRY | 2025-05-05 | Rs 882.31 | 882.31 | 897.76 | 881.16 | 887.72 | PASS |
| 12 | BAJFINANCE | PARTIAL | 2025-09-15 | Rs 1014.65 | 999.00 | 1025.70 | 998.10 | 1009.85 | PASS |
| 12 | BAJFINANCE | EXIT (trailing_stop) | 2025-10-30 | Rs 1047.38 | 1063.00 | 1066.80 | 1045.00 | 1052.30 | PASS |
| 13 | DRREDDY | ENTRY | 2025-09-15 | Rs 1308.90 | 1308.90 | 1311.80 | 1292.50 | 1300.80 | PASS |
| 13 | DRREDDY | EXIT (hard_stop) | 2025-10-30 | Rs 1196.00 | 1196.00 | 1207.20 | 1180.90 | 1202.20 | PASS |
| 14 | RELIANCE | ENTRY | 2025-05-05 | Rs 1425.31 | 1425.31 | 1433.77 | 1421.22 | 1425.61 | PASS |
| 14 | RELIANCE | EXIT (open_at_end) | 2025-10-31 | Rs 1486.40 | 1490.40 | 1497.50 | 1482.30 | 1486.40 | PASS |
| 15 | HDFCBANK | ENTRY | 2025-05-05 | Rs 956.57 | 956.57 | 962.98 | 953.26 | 955.48 | PASS |
| 15 | HDFCBANK | EXIT (open_at_end) | 2025-10-31 | Rs 987.30 | 994.00 | 1004.45 | 981.15 | 987.30 | PASS |
| 16 | BHARTIARTL | ENTRY | 2025-05-05 | Rs 1852.51 | 1852.51 | 1857.97 | 1833.87 | 1850.53 | PASS |
| 16 | BHARTIARTL | EXIT (open_at_end) | 2025-10-31 | Rs 2054.50 | 2056.00 | 2073.80 | 2051.70 | 2054.50 | PASS |
| 17 | MARUTI | ENTRY | 2025-05-05 | Rs 12356.26 | 12356.26 | 12356.26 | 12229.63 | 12324.61 | PASS |
| 17 | MARUTI | PARTIAL | 2025-08-19 | Rs 14209.70 | 14070.00 | 14270.00 | 13979.00 | 14250.00 | PASS |
| 17 | MARUTI | EXIT (open_at_end) | 2025-10-31 | Rs 16186.00 | 16204.00 | 16516.00 | 15949.00 | 16186.00 | PASS |
| 18 | MARICO | ENTRY | 2025-05-06 | Rs 715.52 | 715.52 | 720.52 | 706.51 | 713.00 | PASS |
| 18 | MARICO | EXIT (open_at_end) | 2025-10-31 | Rs 719.95 | 721.50 | 728.65 | 718.65 | 719.95 | PASS |
| 19 | ADANIPORTS | ENTRY | 2025-05-06 | Rs 1343.46 | 1343.46 | 1349.73 | 1308.63 | 1314.41 | PASS |
| 19 | ADANIPORTS | EXIT (open_at_end) | 2025-10-31 | Rs 1451.50 | 1457.90 | 1461.70 | 1443.00 | 1451.50 | PASS |
| 20 | LT | ENTRY | 2025-05-08 | Rs 3279.51 | 3279.51 | 3334.90 | 3269.31 | 3293.19 | PASS |
| 20 | LT | PARTIAL | 2025-09-26 | Rs 3771.44 | 3664.00 | 3794.90 | 3661.00 | 3729.50 | PASS |
| 20 | LT | EXIT (open_at_end) | 2025-10-31 | Rs 4030.90 | 4001.10 | 4045.90 | 3980.20 | 4030.90 | PASS |
| 21 | APOLLOHOSP | ENTRY | 2025-07-11 | Rs 7335.86 | 7335.86 | 7364.78 | 7140.37 | 7170.79 | PASS |
| 21 | APOLLOHOSP | EXIT (open_at_end) | 2025-10-31 | Rs 7670.82 | 7822.61 | 7822.61 | 7640.86 | 7670.82 | PASS |
| 22 | SBILIFE | ENTRY | 2025-09-22 | Rs 1852.42 | 1852.42 | 1877.09 | 1850.23 | 1855.12 | PASS |
| 22 | SBILIFE | EXIT (open_at_end) | 2025-10-31 | Rs 1952.99 | 1962.27 | 1975.95 | 1949.09 | 1952.99 | PASS |
| 23 | SBIN | ENTRY | 2025-09-26 | Rs 846.74 | 846.74 | 849.05 | 837.90 | 841.78 | PASS |
| 23 | SBIN | EXIT (open_at_end) | 2025-10-31 | Rs 920.41 | 918.35 | 929.94 | 913.78 | 920.41 | PASS |
| 24 | TATACONSUM | ENTRY | 2025-10-24 | Rs 1163.30 | 1163.30 | 1163.30 | 1144.40 | 1155.30 | PASS |
| 24 | TATACONSUM | EXIT (open_at_end) | 2025-10-31 | Rs 1165.00 | 1171.00 | 1183.50 | 1157.80 | 1165.00 | PASS |
| 25 | BAJFINANCE | ENTRY | 2025-10-30 | Rs 1063.00 | 1063.00 | 1066.80 | 1045.00 | 1052.30 | PASS |
| 25 | BAJFINANCE | EXIT (open_at_end) | 2025-10-31 | Rs 1042.80 | 1052.00 | 1069.45 | 1041.40 | 1042.80 | PASS |

## Failed events detail (if any)

_No failures._

## How to spot-check manually

For any row above, open yfinance.com (or `yf.Ticker('SYMBOL.NS').history(...)`) for the listed date. 
Compare yf Open/High/Low/Close with the values shown here. If they match, the engine read real data correctly.
