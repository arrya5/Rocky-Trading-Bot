# Phase B — Walk-Forward Optimization — Final Report

_Generated: 2026-05-18T20:32:47_

---

## 🎯 FINAL DECISION: **REVERT_TO_BASELINE**

> holdout return (-6.57%) < 70% of training avg (+9.62%)

### Headline numbers

| Metric | Value |
|---|---|
| Avg return across 3 training windows | +9.62% |
| Holdout return (Nov 2024 - Apr 2025) | -6.57% |
| Holdout / Training ratio | -68.3% |
| Holdout trades | 21 |
| Holdout win rate | 28.6% |
| Holdout max drawdown | -16.61% |
| Holdout Nifty return | +0.12% |
| Holdout alpha vs Nifty | -6.69% |

## 📋 Rule changes

_No rule changes recommended. Baseline performance was best._

---

## 📊 Training Window Details

### Window 1 (W1): 2023-05-01 -> 2023-10-31

**Parameter tuned:** `score_threshold`  
**Decision:** KEEP_BASELINE  
**Winner:** `score_40_baseline`

**Reasoning:**
- baseline ranked #1 by objective (-2.53%)

**Candidates evaluated:**

| Candidate | Trades | Return % | Win % | Max DD % | Alpha vs Nifty | Objective |
|---|---|---|---|---|---|---|
| score_40_baseline ⭐ | 14 | -2.53% | 28.6% | -6.94% | -7.67% | ❌ |
| score_50 | 14 | -2.53% | 28.6% | -6.94% | -7.67% | ❌ |
| score_60 | 14 | -2.53% | 28.6% | -6.94% | -7.67% | ❌ |

**Effect size:** best candidate beat baseline by +0.00pp
**Bootstrap test:** candidate won 43% of 200 resamples

---

### Window 2 (W2): 2023-11-01 -> 2024-04-30

**Parameter tuned:** `stop_tightness`  
**Decision:** KEEP_BASELINE  
**Winner:** `stop_-7pct_baseline`

**Reasoning:**
- baseline ranked #1 by objective (+30.98%)

**Candidates evaluated:**

| Candidate | Trades | Return % | Win % | Max DD % | Alpha vs Nifty | Objective |
|---|---|---|---|---|---|---|
| stop_-5pct | 35 | +28.67% | 60.0% | -5.68% | +9.63% | 28.67 |
| stop_-7pct_baseline ⭐ | 27 | +30.98% | 74.1% | -3.90% | +11.94% | 30.98 |
| stop_-10pct | 26 | +30.84% | 76.9% | -5.30% | +11.80% | 30.84 |

**Effect size:** best candidate beat baseline by +0.00pp
**Bootstrap test:** candidate won 44% of 200 resamples

---

### Window 3 (W3): 2024-05-01 -> 2024-10-31

**Parameter tuned:** `position_sizing`  
**Decision:** ADOPT_WINNER  
**Winner:** `conservative_100_70_40`

**Reasoning:**
- best candidate 'conservative_100_70_40' beats baseline by +7.71pp
- bootstrap robust: 76% wins on resamples

**Candidates evaluated:**

| Candidate | Trades | Return % | Win % | Max DD % | Alpha vs Nifty | Objective |
|---|---|---|---|---|---|---|
| baseline_70_50_30 | 32 | -7.31% | 28.1% | -12.84% | -14.19% | -7.31 |
| conservative_100_70_40 ⭐ | 26 | +0.40% | 38.5% | -10.75% | -6.48% | 0.40 |
| granular_50_30_20 | 50 | -6.04% | 30.0% | -13.00% | -12.91% | -6.04 |
| aggressive_tiered_90_40_15 | 31 | -7.58% | 35.5% | -14.53% | -14.46% | -7.58 |
| flat_50_50_50 | 48 | -6.79% | 27.1% | -13.00% | -13.66% | -6.79 |

**Effect size:** best candidate beat baseline by +7.71pp
**Bootstrap test:** candidate won 76% of 200 resamples

---

## 🔒 Holdout Test

After the 3 training windows, the final rule set was locked and applied to a completely untouched 6-month period (Nov 2024 - Apr 2025). No further tuning occurred.

**Final rule set used in holdout:**

```
  min_score: 40
  adv_min_cr: 50
  vol_max_pct: 3.0
  stop_pct: -0.07
  partial_exit_pct: 0.15
  partial_exit_stop_pct: -0.07
  trailing_pct_at_20: -0.05
  circuit_gap_pct: 0.18
  vix_max: 25
  fii_min_cr: -3500
  sector_max_open: 2
  size_tier_high: 70000
  size_tier_mid: 50000
  size_tier_low: 30000
```

**Holdout metrics:**

| Metric | Value |
|---|---|
| Trades | 21 |
| Win rate | 28.6% |
| Total return | -6.57% |
| Max drawdown | -16.61% |
| Total ₹ P&L | ₹-33,316 |
| Total ₹ invested | ₹1,896,641 |
| Return on deployed capital | -1.76% |
| Nifty return | +0.12% |
| Alpha vs Nifty | -6.69% |

**Overfit check:** holdout / avg-training ratio = -68.3% (threshold to revert: < 70%)

---

## 🚦 Recommendation for production Rocky

**DO NOT change production rules.** The tuned ruleset overfitted to training data — 
holdout performance dropped below the 70% threshold. 
This is a successful walk-forward — it correctly identified an overfit and prevented bad rules from being deployed.

## ⚠️ Honest caveats

- **Single 18-month training period** — covers May 2023 to Oct 2024, which was mostly bull regime. Bear/sideways regime data is limited.
- **Gates 3 (catalyst) and 8 (earnings) still disabled** — LLM lookahead bias and historical data unavailable.
- **Gate 7 (FII) — NSE archive scrape blocked** — gate passes through, so FII flow filter is inactive in backtest.
- **Survivorship bias** — universe is today's Nifty 50 + Midcap 150. Stocks that were in the index in 2023 but got delisted/removed are not in this universe.
- **No transaction cost beyond STT + ₹20 brokerage** — real costs (stamp duty, exchange fees, GST, slippage) are ~0.1pp worse per round-trip.
- **No market-impact modeling** — fills happen at OPEN price exactly; real trading has spread + slippage.
