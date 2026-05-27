#!/usr/bin/env python3
"""
regime_detector.py — Classify current Nifty 50 market regime

Uses Nifty 50 (^NSEI) price data from yfinance to compute the 20-day SMA slope
and ADX(14) for trend strength confirmation.

Regime classification (headline `regime` field):
  bull:     20-day SMA slope > +1.5%
  bear:     20-day SMA slope < -1.5%
  sideways: slope between -1.5% and +1.5%

Also reports a `markov` block: an observable Markov regime layer that labels
each historical day Bear/Sideways/Bull from the 20-day rolling return, builds
the 3x3 transition matrix, and reports regime persistence, the probability of
Bear ahead (1 day / 1 week), and the long-run regime mix. This is forward-
looking context for the reasoning layer — NOT a standalone trade signal.

Usage:
  python scripts/regime_detector.py

Output:
  {"regime": "bull", "slope_pct": 2.3, "adx": 28.4, "trend_strength": "strong",
   "nifty_close": 24150.5, "sma_20": 23800.1, "generated_at": "...",
   "markov": {"current_regime": "bull",
              "persistence": {"bear": 91.2, "sideways": 78.4, "bull": 93.1},
              "p_bear_next_day": 1.8, "p_bear_next_week": 7.5,
              "stationary_mix": {"bear": 22.1, "sideways": 28.0, "bull": 49.9},
              "n_days": 1230}}
"""

import json, sys, warnings
from datetime import datetime

warnings.filterwarnings("ignore")


def _compute_adx(df, period=14):
    """Compute ADX(14) from a DataFrame with High, Low, Close columns."""
    import pandas as pd
    import numpy as np

    high  = df["High"]
    low   = df["Low"]
    close = df["Close"]

    plus_dm  = high.diff()
    minus_dm = -low.diff()
    plus_dm  = plus_dm.where((plus_dm > minus_dm) & (plus_dm > 0), 0)
    minus_dm = minus_dm.where((minus_dm > plus_dm) & (minus_dm > 0), 0)

    tr = pd.concat([
        high - low,
        (high - close.shift()).abs(),
        (low  - close.shift()).abs(),
    ], axis=1).max(axis=1)

    atr      = tr.ewm(span=period, adjust=False).mean()
    plus_di  = 100 * (plus_dm.ewm(span=period, adjust=False).mean() / atr)
    minus_di = 100 * (minus_dm.ewm(span=period, adjust=False).mean() / atr)
    dx       = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di)
    adx      = dx.ewm(span=period, adjust=False).mean()

    return round(float(adx.iloc[-1]), 1)


def _markov_regime(close, window=20, threshold=0.02, week_steps=5, power=64):
    """Observable Markov regime layer on the Nifty close series.

    Labels each day Bear(0)/Sideways(1)/Bull(2) from the `window`-day rolling
    return (|return| > threshold => Bull/Bear, else Sideways), builds the 3x3
    transition matrix by maximum-likelihood counting, then reports persistence
    (the diagonal), the long-run regime mix (stationary distribution via matrix
    power), and the probability of Bear `week_steps` trading days ahead given
    today's state. Context for the reasoning layer — NOT a trade signal.
    """
    import numpy as np
    import pandas as pd

    roll = close.pct_change(window)
    labels = pd.Series(1, index=close.index, dtype=int)  # default Sideways (1)
    labels[roll > threshold]  = 2   # Bull
    labels[roll < -threshold] = 0   # Bear
    labels = labels[roll.notna()]
    arr = labels.to_numpy()
    if len(arr) < window + 30:
        return {"error": "insufficient history for transition matrix"}

    # MLE transition counts: counts[from, to]
    counts = np.zeros((3, 3), dtype=float)
    for i in range(len(arr) - 1):
        counts[arr[i], arr[i + 1]] += 1
    row_sums = counts.sum(axis=1, keepdims=True)
    row_sums[row_sums == 0] = 1.0  # uniform-safe: empty row won't divide-by-zero
    P = counts / row_sums

    current = int(arr[-1])
    P_week = np.linalg.matrix_power(P, week_steps)
    stationary = np.linalg.matrix_power(P, power)[0]  # converged row = long-run mix

    names = {0: "bear", 1: "sideways", 2: "bull"}
    pct = lambda x: round(float(x) * 100, 1)
    return {
        "current_regime": names[current],
        "persistence": {
            "bear":     pct(P[0, 0]),
            "sideways": pct(P[1, 1]),
            "bull":     pct(P[2, 2]),
        },
        "p_bear_next_day":  pct(P[current, 0]),
        "p_bear_next_week": pct(P_week[current, 0]),
        "stationary_mix": {
            "bear":     pct(stationary[0]),
            "sideways": pct(stationary[1]),
            "bull":     pct(stationary[2]),
        },
        "n_days": int(len(arr)),
    }


def detect():
    import yfinance as yf

    # 5y of daily data: enough transitions for a stable 3-state matrix while the
    # headline regime still keys off only the most recent 20-day SMA slope.
    df = yf.download("^NSEI", period="5y", interval="1d", progress=False, auto_adjust=True)

    if df.empty or len(df) < 25:
        print(json.dumps({"error": "Insufficient data from yfinance for ^NSEI"}))
        sys.exit(1)

    # Flatten MultiIndex columns if present
    if hasattr(df.columns, "levels"):
        df.columns = df.columns.get_level_values(0)

    close    = df["Close"]
    sma_20   = close.rolling(20).mean()
    sma_now  = float(sma_20.iloc[-1])
    sma_prev = float(sma_20.iloc[-21])  # 20 bars ago

    slope_pct = (sma_now - sma_prev) / sma_prev * 100

    if slope_pct > 1.5:
        regime = "bull"
    elif slope_pct < -1.5:
        regime = "bear"
    else:
        regime = "sideways"

    try:
        adx = _compute_adx(df)
        trend_strength = "strong" if adx >= 25 else ("moderate" if adx >= 20 else "weak")
    except Exception:
        adx = None
        trend_strength = "unknown"

    # Markov layer degrades gracefully: a failure here must never break the
    # headline regime that the bear gate depends on.
    try:
        markov = _markov_regime(close)
    except Exception as exc:
        markov = {"error": f"markov layer failed: {exc}"}

    print(json.dumps({
        "regime":         regime,
        "slope_pct":      round(slope_pct, 2),
        "adx":            adx,
        "trend_strength": trend_strength,
        "nifty_close":    round(float(close.iloc[-1]), 2),
        "sma_20":         round(sma_now, 2),
        "generated_at":   datetime.now().isoformat(timespec="seconds"),
        "markov":         markov,
    }, indent=2))


if __name__ == "__main__":
    detect()
