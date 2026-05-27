#!/usr/bin/env python3
"""
swing_signal_generator.py v2 — REBUILT with real swing factors.

Replaces noisy v1 factors with professional swing-trading indicators:

Scoring (each factor = 20 points, max 100):
  +20  Donchian breakout       (close >= 20-day high of yesterday)
  +20  ADX > 25                (strong trend, not choppy)
  +20  Sector relative strength (sector 10d return > universe 10d return)
  +20  Volume surge             (today volume > 1.8x 20-day avg)
  +20  Above 50-day EMA         (in uptrend, not fighting it)

Pre-filters:
  ADV     20-day avg daily value >= Rs 50 Cr
  VOL     20-day daily return std <= 3.5%
  TREND   close > 50-day EMA (block counter-trend trades hard)

Each signal also returns ATR-based stop distances for use by swing_portfolio:
  stop_distance_pct = ATR_pct × 2.0
  partial_target_pct = ATR_pct × 1.5
  trailing_distance_pct = ATR_pct × 2.0

ATR scales stops to each stock's volatility instead of fixed 4%.
"""
import sys, warnings
from datetime import date
from pathlib import Path
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import yfinance as yf

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
from models.signal_generator import SECTOR_MAP, UNIVERSE

ADV_MIN_CR        = 50.0
VOL_MAX_PCT       = 3.5
DEFAULT_MIN_SCORE = 60   # raised from v1's 40 — only high-conviction setups

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


from backtest.engine.signal_asof import (
    _CACHE, prime_cache as _prime_cache_orig, prime_benchmark, get_ohlc,
    trading_days, nifty_close, compute_regime_asof, constituents_asof,
    resolve_ticker,
)


def prime_cache(symbols: list[str], start: date, end: date, lookback_days: int = 120) -> dict[str, str]:
    return _prime_cache_orig(symbols, start, end, lookback_days=lookback_days)


def _compute_adx(df: pd.DataFrame, period: int = 14) -> float:
    """ADX (Average Directional Index) — trend strength regardless of direction."""
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
    plus_di  = 100 * (plus_dm.ewm(span=period, adjust=False).mean() / atr.replace(0, np.nan))
    minus_di = 100 * (minus_dm.ewm(span=period, adjust=False).mean() / atr.replace(0, np.nan))
    dx       = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
    adx      = dx.ewm(span=period, adjust=False).mean()
    val = adx.iloc[-1]
    return float(val) if pd.notna(val) else 0.0


def _compute_atr_pct(df: pd.DataFrame, period: int = 14) -> float:
    """ATR as percentage of current price."""
    high  = df["High"]
    low   = df["Low"]
    close = df["Close"]
    tr = pd.concat([
        high - low,
        (high - close.shift()).abs(),
        (low  - close.shift()).abs(),
    ], axis=1).max(axis=1)
    atr = tr.rolling(period).mean().iloc[-1]
    current = float(close.iloc[-1])
    return float(atr / current * 100) if current > 0 and pd.notna(atr) else 0.0


# Sector RS — computed lazily, cached per date
_SECTOR_RS_CACHE: dict[tuple[str, str], float] = {}


def _compute_sector_relative_strength(sector: str, as_of: date) -> float:
    """
    Return (sector_10d_avg_return) - (universe_10d_avg_return).
    Positive value means sector is outperforming the broader universe.
    """
    key = (sector, as_of.isoformat())
    if key in _SECTOR_RS_CACHE:
        return _SECTOR_RS_CACHE[key]

    sector_returns = []
    universe_returns = []

    for sym, sym_sector in SECTOR_MAP.items():
        full = _CACHE.get(sym)
        if full is None:
            continue
        df = full[full.index.date <= as_of]
        if len(df) < 11:
            continue
        ret_10d = (df["Close"].iloc[-1] - df["Close"].iloc[-11]) / df["Close"].iloc[-11] * 100
        universe_returns.append(ret_10d)
        if sym_sector == sector:
            sector_returns.append(ret_10d)

    if not sector_returns or not universe_returns:
        _SECTOR_RS_CACHE[key] = 0.0
        return 0.0

    sector_avg = sum(sector_returns) / len(sector_returns)
    universe_avg = sum(universe_returns) / len(universe_returns)
    rs = sector_avg - universe_avg
    _SECTOR_RS_CACHE[key] = rs
    return rs


def clear_sector_cache():
    _SECTOR_RS_CACHE.clear()


def score_symbol_asof(symbol: str, as_of: date) -> dict | None:
    sym = symbol.upper().replace(".NS", "")
    full = _CACHE.get(sym)
    if full is None:
        return None

    df = full[full.index.date <= as_of]
    if df.empty or len(df) < 60:
        return None

    close  = df["Close"].squeeze()
    volume = df["Volume"].squeeze()
    high   = df["High"].squeeze()
    low    = df["Low"].squeeze()
    if not isinstance(close, pd.Series) or len(close) < 60:
        return None

    current_price = float(close.iloc[-1])

    # ── Pre-filter 1: ADV >= 50 Cr ──────────────────────────────────────
    daily_value = close * volume
    adv_20d = float(daily_value.rolling(20).mean().iloc[-1])
    adv_cr  = adv_20d / 1e7
    if adv_cr < ADV_MIN_CR:
        return {"symbol": sym, "signal": "FILTERED", "confidence": 0.0,
                "filter_reason": f"ADV {adv_cr:.1f} Cr < {ADV_MIN_CR}"}

    # ── Pre-filter 2: volatility <= 3.5% ────────────────────────────────
    daily_returns = close.pct_change().dropna()
    vol_20d = float(daily_returns.iloc[-20:].std() * 100)
    if vol_20d > VOL_MAX_PCT:
        return {"symbol": sym, "signal": "FILTERED", "confidence": 0.0,
                "filter_reason": f"Volatility {vol_20d:.1f}% > {VOL_MAX_PCT}%"}

    # ── Pre-filter 3: TREND — must be above 50-day EMA ──────────────────
    ema50 = close.ewm(span=50, adjust=False).mean().iloc[-1]
    if current_price < float(ema50):
        return {"symbol": sym, "signal": "FILTERED", "confidence": 0.0,
                "filter_reason": f"Below 50d EMA ({current_price:.2f} < {float(ema50):.2f})"}

    # ── Factor 1: Donchian breakout (close >= 20-day high of YESTERDAY) ─
    high_20d_yest = float(high.iloc[-21:-1].max())
    donchian_break = current_price >= high_20d_yest * 0.998  # 0.2% tolerance

    # ── Factor 2: ADX > 25 (strong trend) ───────────────────────────────
    adx_val = _compute_adx(df)
    strong_trend = adx_val > 25

    # ── Factor 3: Sector relative strength ──────────────────────────────
    sector = SECTOR_MAP.get(sym, "Other")
    sector_rs = _compute_sector_relative_strength(sector, as_of)
    sector_strong = sector_rs > 0.5  # sector outperforms universe by 0.5pp+ over 10d

    # ── Factor 4: Volume surge (today > 1.8x 20-day avg) ────────────────
    today_vol = float(volume.iloc[-1])
    vol_20d_avg = float(volume.iloc[-21:-1].mean())  # exclude today
    vol_surge = (today_vol > 1.8 * vol_20d_avg) if vol_20d_avg > 0 else False

    # ── Factor 5: Solidly above 50d EMA (not just at the line) ──────────
    above_ema_buffer = current_price > float(ema50) * 1.02  # at least 2% above

    score = (
        (20 if donchian_break  else 0) +
        (20 if strong_trend    else 0) +
        (20 if sector_strong   else 0) +
        (20 if vol_surge       else 0) +
        (20 if above_ema_buffer else 0)
    )

    # ── ATR-based stop sizes ────────────────────────────────────────────
    atr_pct = _compute_atr_pct(df)
    # Cap ATR-based stops to reasonable bounds (between 3% and 8%)
    stop_distance_pct    = max(3.0, min(8.0, atr_pct * 2.0))
    partial_target_pct   = max(4.0, min(10.0, atr_pct * 1.5))
    trailing_trigger_pct = max(6.0, min(15.0, atr_pct * 2.5))
    trailing_distance_pct = max(2.5, min(6.0, atr_pct * 1.5))

    return {
        "symbol":                  sym,
        "signal":                  "BUY" if score >= DEFAULT_MIN_SCORE else "HOLD",
        "confidence":              float(score),
        "current_price":           round(current_price, 2),
        "sector":                  sector,
        "suggested_position_size": _suggested_size(score),
        "adx":                     round(adx_val, 1),
        "atr_pct":                 round(atr_pct, 2),
        "sector_rs":               round(sector_rs, 2),
        "vol_ratio":               round(today_vol / vol_20d_avg, 2) if vol_20d_avg > 0 else 0,
        "ema50":                   round(float(ema50), 2),
        "donchian_high_yest":      round(high_20d_yest, 2),
        # Per-trade exit distances (passed to portfolio.enter)
        "stop_distance_pct":       round(stop_distance_pct, 2),
        "partial_target_pct":      round(partial_target_pct, 2),
        "trailing_trigger_pct":    round(trailing_trigger_pct, 2),
        "trailing_distance_pct":   round(trailing_distance_pct, 2),
        "score_breakdown": {
            "donchian_break":   donchian_break,
            "adx_above_25":     strong_trend,
            "sector_strong":    sector_strong,
            "volume_surge":     vol_surge,
            "above_ema50":      above_ema_buffer,
        },
    }
