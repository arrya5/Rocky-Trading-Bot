# Sector Rotation — Walk-Forward Final Report

_Generated: 2026-05-19T21:15:52_

---

## 🎯 FINAL DECISION: **REVERT_TO_BASELINE**

> holdout return (-9.69%) < 70% of training avg (+31.08%)

### Headline numbers

| Metric | Value |
|---|---|
| Avg return across 3 training windows | +31.08% |
| Holdout return (Nov 2024 - Apr 2025) | -9.69% |
| Holdout / Training ratio | -31.2% |
| Holdout trades | 4 |
| Holdout win rate | 25.0% |
| Holdout max drawdown | -18.06% |
| Holdout Nifty return | +0.00% |
| Holdout alpha vs Nifty | -9.69% |

## 📋 Rule changes

_No rule changes recommended. Baseline performance was best._

---

## 📊 Training Window Details

### Window W1: 2023-05-01 -> 2023-10-31

**Parameter tuned:** `top_n`  
**Decision:** ADOPT_WINNER  
**Winner:** `top_n=2`

- best candidate 'top_n=2' beats baseline by +8.80pp

| Candidate | Trades | Return % | Win % | Max DD | Alpha vs Nifty |
|---|---|---|---|---|---|
| top_n=2 ⭐ | 6 | +32.84% | 83% | -6.59% | +27.70% |
| top_n=3 (baseline) | 10 | +24.03% | 80% | -6.89% | +24.03% |
| top_n=4 | 15 | +18.03% | 80% | -7.41% | +18.03% |

---

### Window W2: 2023-11-01 -> 2024-04-30

**Parameter tuned:** `rebalance_freq_days`  
**Decision:** ADOPT_WINNER  
**Winner:** `freq=42 (~2 months)`

- best candidate 'freq=42 (~2 months)' beats baseline by +3.57pp

| Candidate | Trades | Return % | Win % | Max DD | Alpha vs Nifty |
|---|---|---|---|---|---|
| freq=21 (baseline) | 8 | +45.64% | 88% | -15.71% | +45.64% |
| freq=42 (~2 months) ⭐ | 4 | +49.21% | 100% | -22.82% | +49.21% |
| freq=63 (~3 months) | 4 | +20.01% | 75% | -16.16% | +20.01% |

---

### Window W3: 2024-05-01 -> 2024-10-31

**Parameter tuned:** `lookback_days`  
**Decision:** KEEP_BASELINE  
**Winner:** `lookback=21 (baseline)`

- baseline ranked #1 by return

| Candidate | Trades | Return % | Win % | Max DD | Alpha vs Nifty |
|---|---|---|---|---|---|
| lookback=21 (baseline) ⭐ | 4 | +11.19% | 75% | -9.66% | +11.19% |
| lookback=42 | 5 | +9.52% | 60% | -7.28% | +9.52% |
| lookback=63 | 4 | -4.92% | 25% | -7.90% | -4.92% |

---

## 🔒 Holdout (Nov 2024 - Apr 2025)

Final rules locked in. No tuning during holdout.

**Final ruleset:**

```
  top_n: 3
  rebalance_freq_days: 21
  lookback_days: 21
```

## 🚦 Recommendation

**Do NOT adopt this strategy** — the walk-forward overfit-check failed.
The training periods looked good, but the holdout exposed the apparent edge as
likely overfitting. Keep production Rocky on its current rules.
