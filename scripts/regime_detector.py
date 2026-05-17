#!/usr/bin/env python3
"""
regime_detector.py — Classify current Nifty 50 market regime

Uses Nifty 50 (^NSEI) price data from yfinance to compute the 20-day SMA slope
and ADX(14) for trend strength confirmation.

Regime classification:
  bull:     20-day SMA slope > +1.5%
  bear:     20-day SMA slope < -1.5%
  sideways: slope between -1.5% and +1.5%

Usage:
  python scripts/regime_detector.py

Output:
  {"regime": "bull", "slope_pct": 2.3, "adx": 28.4, "trend_strength": "strong",
   "nifty_close": 24150.5, "sma_20": 23800.1, "generated_at": "2026-05-17T08:30:00"}
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


def detect():
    import yfinance as yf

    df = yf.download("^NSEI", period="90d", interval="1d", progress=False, auto_adjust=True)

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

    print(json.dumps({
        "regime":         regime,
        "slope_pct":      round(slope_pct, 2),
        "adx":            adx,
        "trend_strength": trend_strength,
        "nifty_close":    round(float(close.iloc[-1]), 2),
        "sma_20":         round(sma_now, 2),
        "generated_at":   datetime.now().isoformat(timespec="seconds"),
    }, indent=2))


if __name__ == "__main__":
    detect()
