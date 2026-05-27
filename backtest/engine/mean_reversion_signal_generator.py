#!/usr/bin/env python3
"""
mean_reversion_signal_generator.py — Buy oversold dips in uptrends.

Hypothesis: Indian midcaps in long-term uptrends often overshoot to the downside
on short-term panic selling, then bounce back. Catch those bounces.

Factors (each +20, max 100):
  +20  RSI(7) < 30                    (oversold)
  +20  Price below lower 20-day BB    (extended below mean)
  +20  Down >= 5% from 10-day high    (real pullback, not just consolidation)
  +20  Volume spike on down day       (capitulation — today vol > 1.5x avg)
  +20  Above 100-day SMA              (long-term uptrend intact)

Pre-filters:
  ADV >= Rs 50 Cr
  20-day volatility <= 4% (slightly higher than swing since dips are inherently volatile)
  Stock must be above 200-day SMA (only buy dips in real uptrends)

Exit logic (different from momentum swing):
  - Target: return to 20-day SMA (the mean)
  - Stop: another -3% below entry (extended falls can keep falling)
  - Partial at +2% (small move back toward mean)
  - Max hold: 7 days (bounces happen fast or don't happen)
"""
import sys, warnings
from datetime import date
from pathlib import Path
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
from models.signal_generator import SECTOR_MAP

ADV_MIN_CR        = 50.0
VOL_MAX_PCT       = 4.0
DEFAULT_MIN_SCORE = 60   # need 3+ of 5 factors

_TIER_HIGH = 70_000
_TIER_MID  = 50_000
_TIER_LOW  = 30_000


def set_tier_sizes(high: int, mid: int, low: int) -> None:
    global _TIER_HIGH, _TIER_MID, _TIER_LOW
    _TIER_HIGH, _TIER_MID, _TIER_LOW = int(high), int(mid), int(low)


def _suggested_size(score: int) -> int:
    if score >= 80:   return _TIER_HIGH
    elif score >= 60: return _TIER_MID
    else:             return _TIER_LOW


from backtest.engine.signal_asof import _CACHE, prime_cache as _prime_cache_orig


def prime_cache(symbols: list[str], start: date, end: date, lookback_days: int = 220) -> dict[str, str]:
    return _prime_cache_orig(symbols, start, end, lookback_days=lookback_days)


def _rsi(series: pd.Series, period: int = 7) -> float:
    delta = series.diff()
    gain  = delta.clip(lower=0).rolling(period).mean()
    loss  = (-delta.clip(upper=0)).rolling(period).mean()
    rs    = gain / loss.replace(0, np.nan)
    rsi_s = 100 - 100 / (1 + rs)
    val   = rsi_s.iloc[-1]
    return float(val) if pd.notna(val) else 50.0


def score_symbol_asof(symbol: str, as_of: date) -> dict | None:
    sym = symbol.upper().replace(".NS", "")
    full = _CACHE.get(sym)
    if full is None:
        return None

    df = full[full.index.date <= as_of]
    if df.empty or len(df) < 210:
        return None

    close  = df["Close"].squeeze()
    volume = df["Volume"].squeeze()
    if not isinstance(close, pd.Series) or len(close) < 210:
        return None

    current_price = float(close.iloc[-1])

    # Pre-filter 1: ADV
    daily_value = close * volume
    adv_cr = float(daily_value.rolling(20).mean().iloc[-1]) / 1e7
    if adv_cr < ADV_MIN_CR:
        return {"symbol": sym, "signal": "FILTERED", "filter_reason": f"ADV {adv_cr:.1f} Cr"}

    # Pre-filter 2: volatility
    vol_20d = float(close.pct_change().dropna().iloc[-20:].std() * 100)
    if vol_20d > VOL_MAX_PCT:
        return {"symbol": sym, "signal": "FILTERED", "filter_reason": f"Vol {vol_20d:.1f}%"}

    # Pre-filter 3: long-term uptrend — must be above 200d SMA
    sma200 = float(close.rolling(200).mean().iloc[-1])
    if current_price < sma200:
        return {"symbol": sym, "signal": "FILTERED",
                "filter_reason": f"Below 200d SMA ({current_price:.2f} < {sma200:.2f})"}

    # ── Factor 1: RSI(7) < 30 (oversold) ────────────────────────────────
    rsi7 = _rsi(close, period=7)
    oversold = rsi7 < 30

    # ── Factor 2: Price below lower 20-day BB ───────────────────────────
    sma20 = float(close.rolling(20).mean().iloc[-1])
    std20 = float(close.rolling(20).std().iloc[-1])
    bb_lower = sma20 - 2 * std20
    below_lower_bb = current_price < bb_lower

    # ── Factor 3: Down >= 5% from 10-day high ───────────────────────────
    high_10d = float(close.iloc[-11:-1].max())
    drop_from_high_pct = (current_price - high_10d) / high_10d * 100
    real_pullback = drop_from_high_pct <= -5.0

    # ── Factor 4: Volume spike (today vol > 1.5x 20d avg) ───────────────
    today_vol = float(volume.iloc[-1])
    vol_20d_avg = float(volume.iloc[-21:-1].mean())
    vol_spike = (today_vol > 1.5 * vol_20d_avg) if vol_20d_avg > 0 else False

    # ── Factor 5: Above 100-day SMA (medium-term uptrend) ───────────────
    sma100 = float(close.rolling(100).mean().iloc[-1])
    above_sma100 = current_price > sma100

    score = (
        (20 if oversold       else 0) +
        (20 if below_lower_bb else 0) +
        (20 if real_pullback  else 0) +
        (20 if vol_spike      else 0) +
        (20 if above_sma100   else 0)
    )

    sector = SECTOR_MAP.get(sym, "Other")

    # Target = return to 20-day SMA. Compute % move needed.
    target_pct = (sma20 - current_price) / current_price * 100
    target_pct = max(2.0, min(8.0, target_pct))  # bound between 2-8%

    return {
        "symbol":                  sym,
        "signal":                  "BUY" if score >= DEFAULT_MIN_SCORE else "HOLD",
        "confidence":              float(score),
        "current_price":           round(current_price, 2),
        "sector":                  sector,
        "suggested_position_size": _suggested_size(score),
        "rsi7":                    round(rsi7, 1),
        "drop_from_high_pct":      round(drop_from_high_pct, 2),
        "sma20":                   round(sma20, 2),
        # Mean-reversion exit: target back to 20-day SMA
        "stop_distance_pct":       3.0,
        "partial_target_pct":      max(2.0, target_pct * 0.5),
        "trailing_trigger_pct":    target_pct,
        "trailing_distance_pct":   1.5,
        "score_breakdown": {
            "oversold":       oversold,
            "below_lower_bb": below_lower_bb,
            "real_pullback":  real_pullback,
            "vol_spike":      vol_spike,
            "above_sma100":   above_sma100,
        },
    }
