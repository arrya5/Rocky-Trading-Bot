#!/usr/bin/env python3
"""
signal_generator.py — Swing v3 scorer for NSE stocks.

Replaces the previous slow-momentum factors (20-SMA, 50-SMA, RSI, 52w-high, 10d-mom)
with swing-trading factors that catch 5-15 day momentum bursts.

Pre-filters (excluded entirely if any fails):
  ADV     20-day avg daily traded value >= Rs 50 Cr
  VOL     20-day daily return std <= 3.5%
  TREND   close > 200-day SMA (avoid falling knives)

Scoring (each factor = 20 points, max 100):
  +20  Donchian 20-day breakout      (close >= previous 20-day high)
  +20  ADX(14) > 25                   (strong trend confirmation)
  +20  Sector relative strength       (sector index outperforms Nifty by >1pp over 10d)
  +20  Volume surge 2.5x              (today vol > 2.5x 20-day avg)
  +20  Above 50-day EMA               (medium-term uptrend, >1% above EMA50)

BUY  : score >= 80 (4 of 5 factors aligned — high conviction only)
HOLD : score < 80

Position sizing: flat Rs 50,000 per BUY (only score >= 80 trades).

Usage:
  python models/signal_generator.py                    # scan full universe
  python models/signal_generator.py RELIANCE TCS INFY  # specific symbols only
  python models/signal_generator.py --min-score 60     # lower threshold
  python models/signal_generator.py --all              # output all symbols
"""

import json, sys, warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import yfinance as yf
from datetime import datetime

DEFAULT_MIN_SCORE = 80      # swing v3: require 4 of 5 factors
ADV_MIN_CR        = 50
VOL_MAX_PCT       = 3.5
POSITION_SIZE     = 50_000

# ── Sector map ────────────────────────────────────────────────────────────────
SECTOR_MAP = {
    # Energy & Power
    "RELIANCE":    "Energy",    "ONGC":        "Energy",    "BPCL":        "Energy",
    "ADANIENT":    "Energy",    "ADANIGREEN":  "Energy",    "ADANIPOWER":  "Energy",
    "JSWENERGY":   "Energy",    "TORNTPOWER":  "Energy",    "NHPC":        "Energy",
    "POWERGRID":   "Energy",    "NTPC":        "Energy",    "SUZLON":      "Energy",
    # IT & Technology
    "TCS":         "IT",        "INFY":        "IT",        "WIPRO":       "IT",
    "HCLTECH":     "IT",        "TECHM":       "IT",        "LTIM":        "IT",
    # Banking
    "HDFCBANK":    "Banking",   "ICICIBANK":   "Banking",   "SBIN":        "Banking",
    "KOTAKBANK":   "Banking",   "AXISBANK":    "Banking",   "INDUSINDBK":  "Banking",
    "BANDHANBNK":  "Banking",   "FEDERALBNK":  "Banking",   "IDFCFIRSTB":  "Banking",
    "PNB":         "Banking",   "BANKBARODA":  "Banking",
    # FMCG
    "HINDUNILVR":  "FMCG",     "ITC":         "FMCG",     "NESTLEIND":   "FMCG",
    "BRITANNIA":   "FMCG",     "DABUR":       "FMCG",     "MARICO":      "FMCG",
    "COLPAL":      "FMCG",     "GODREJCP":    "FMCG",     "TATACONSUM":  "FMCG",
    "MCDOWELL-N":  "FMCG",     "RADICO":      "FMCG",
    # Auto
    "MARUTI":      "Auto",      "TATAMOTORS":  "Auto",      "M&M":         "Auto",
    "BAJAJ-AUTO":  "Auto",      "HEROMOTOCO":  "Auto",      "EICHERMOT":   "Auto",
    "APOLLOTYRE":  "Auto",      "ESCORTS":     "Auto",      "MRF":         "Auto",
    "BALKRISIND":  "Auto",
    # Pharma & Healthcare
    "SUNPHARMA":   "Pharma",    "DRREDDY":     "Pharma",    "DIVISLAB":    "Pharma",
    "CIPLA":       "Pharma",    "TORNTPHARM":  "Pharma",    "AUROPHARMA":  "Pharma",
    "LUPIN":       "Pharma",    "ALKEM":       "Pharma",    "BIOCON":      "Pharma",
    "LALPATHLAB":  "Pharma",    "MAXHEALTH":   "Pharma",    "FORTIS":      "Pharma",
    # Finance & NBFC
    "BAJFINANCE":  "Finance",   "BAJAJFINSV":  "Finance",   "MUTHOOTFIN":  "Finance",
    "CHOLAFIN":    "Finance",   "MANAPPURAM":  "Finance",   "LICHSGFIN":   "Finance",
    "ABCAPITAL":   "Finance",   "MFSL":        "Finance",   "CANFIN":      "Finance",
    "POONAWALLA":  "Finance",   "SBILIFE":     "Finance",   "HDFCLIFE":    "Finance",
    "RECLTD":      "Finance",   "PFC":         "Finance",
    # Metals
    "TATASTEEL":   "Metals",    "JSWSTEEL":    "Metals",    "HINDALCO":    "Metals",
    "COALINDIA":   "Metals",
    # Consumer & Retail
    "ASIANPAINT":  "Consumer",  "TITAN":       "Consumer",  "VOLTAS":      "Consumer",
    "HAVELLS":     "Consumer",  "PAGEIND":     "Consumer",  "TRENT":       "Consumer",
    "JUBLFOOD":    "Consumer",  "DIXON":       "Consumer",  "KAYNES":      "Consumer",
    "NYKAA":       "Consumer",  "ZOMATO":      "Consumer",
    # Infrastructure
    "LT":          "Infrastructure", "ULTRACEMCO":  "Infrastructure",
    "GRASIM":      "Infrastructure", "AMBUJACEM":   "Infrastructure",
    "SHREECEM":    "Infrastructure", "RAMCOCEM":    "Infrastructure",
    "APLAPOLLO":   "Infrastructure", "RVNL":        "Infrastructure",
    "ADANIPORTS":  "Infrastructure",
    # Telecom
    "BHARTIARTL":  "Telecom",
    # Chemicals
    "PIDILITIND":  "Chemicals",  "BERGEPAINT":  "Chemicals",  "UPL": "Chemicals",
    # Fin Services
    "CAMS":        "Fin Services", "CDSL":    "Fin Services", "MCX":  "Fin Services",
    "NUVAMA":      "Fin Services", "IIFL":    "Fin Services",
    # Logistics
    "CONCOR":      "Logistics",  "IRCTC":    "Logistics",  "IRFC":    "Logistics",
    "RAILTEL":     "Logistics",
}

# Map sectors to NSE sector indices for relative-strength factor
SECTOR_TO_INDEX = {
    "Banking":        "^CNXBANK",
    "IT":             "^CNXIT",
    "Auto":           "^CNXAUTO",
    "Pharma":         "^CNXPHARMA",
    "FMCG":           "^CNXFMCG",
    "Metals":         "^CNXMETAL",
    "Energy":         "^CNXENERGY",
    "Infrastructure": "^CNXINFRA",
    "Finance":        "^CNXFIN",
    "Fin Services":   "^CNXFIN",
}
NIFTY_TICKER = "^NSEI"

# ── Universe ──────────────────────────────────────────────────────────────────
UNIVERSE = [
    # Nifty 50
    "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK", "HINDUNILVR",
    "SBIN", "BHARTIARTL", "ITC", "KOTAKBANK", "LT", "AXISBANK",
    "ASIANPAINT", "MARUTI", "SUNPHARMA", "TITAN", "BAJFINANCE", "WIPRO",
    "HCLTECH", "ULTRACEMCO", "BAJAJFINSV", "NESTLEIND", "TECHM",
    "POWERGRID", "NTPC", "ONGC", "JSWSTEEL", "TATAMOTORS", "TATASTEEL",
    "M&M", "ADANIENT", "ADANIPORTS", "COALINDIA", "DRREDDY", "DIVISLAB",
    "CIPLA", "GRASIM", "HEROMOTOCO", "HINDALCO", "INDUSINDBK",
    "BRITANNIA", "APOLLOHOSP", "BPCL", "EICHERMOT", "TATACONSUM",
    "BAJAJ-AUTO", "SBILIFE", "HDFCLIFE", "UPL", "LTIM",
    # Midcap representative
    "MUTHOOTFIN", "PIDILITIND", "BERGEPAINT", "COLPAL", "MARICO",
    "DABUR", "GODREJCP", "HAVELLS", "VOLTAS", "PAGEIND",
    "BANDHANBNK", "FEDERALBNK", "IDFCFIRSTB", "PNB", "BANKBARODA",
    "CHOLAFIN", "MANAPPURAM", "LICHSGFIN", "MAXHEALTH", "LALPATHLAB",
    "FORTIS", "NHPC", "RECLTD", "PFC", "IRCTC", "CONCOR",
    "APOLLOTYRE", "ESCORTS", "MRF", "BALKRISIND",
    "AMBUJACEM", "SHREECEM", "RAMCOCEM",
    "TORNTPHARM", "AUROPHARMA", "LUPIN", "ALKEM", "BIOCON",
    "JUBLFOOD", "TRENT", "MCDOWELL-N", "RADICO",
    "ABCAPITAL", "MFSL", "CANFIN",
    "ZOMATO", "NYKAA", "IRFC", "RVNL",
    "DIXON", "KAYNES", "APLAPOLLO",
    "JSWENERGY", "ADANIGREEN", "TORNTPOWER", "SUZLON",
    "CAMS", "CDSL", "MCX",
    "NUVAMA", "IIFL", "POONAWALLA",
]


# ── Sector index cache (one-time fetch per process) ───────────────────────────
_SECTOR_DATA: dict[str, pd.DataFrame | None] = {}


def _fetch_index(ticker: str) -> pd.DataFrame | None:
    if ticker in _SECTOR_DATA:
        return _SECTOR_DATA[ticker]
    try:
        df = yf.Ticker(ticker).history(period="60d", interval="1d", auto_adjust=True)
        if df is None or df.empty or len(df) < 11:
            _SECTOR_DATA[ticker] = None
            return None
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        _SECTOR_DATA[ticker] = df
        return df
    except Exception:
        _SECTOR_DATA[ticker] = None
        return None


def _ten_day_return(df: pd.DataFrame | None) -> float | None:
    if df is None or len(df) < 11:
        return None
    end = float(df["Close"].iloc[-1])
    start = float(df["Close"].iloc[-11])
    if start <= 0:
        return None
    return (end - start) / start * 100


def _sector_relative_strength(sector: str) -> tuple[float | None, float | None, float | None]:
    """Return (sector_10d_ret, nifty_10d_ret, sector_rs_pp). None if unavailable."""
    idx = SECTOR_TO_INDEX.get(sector)
    if not idx:
        return None, None, None
    sec_df = _fetch_index(idx)
    nif_df = _fetch_index(NIFTY_TICKER)
    sec_ret = _ten_day_return(sec_df)
    nif_ret = _ten_day_return(nif_df)
    if sec_ret is None or nif_ret is None:
        return sec_ret, nif_ret, None
    return sec_ret, nif_ret, sec_ret - nif_ret


def _compute_adx(df: pd.DataFrame, period: int = 14) -> float:
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


def _suggested_size(score: int) -> int:
    # Flat ₹50k for score >= 80; lower scores get ₹30k (but won't trade at min_score=80)
    return POSITION_SIZE if score >= 80 else 30_000


def score_symbol(symbol: str) -> dict | None:
    sym_clean = symbol.upper().replace(".NS", "")
    ticker    = sym_clean + ".NS"

    try:
        df = yf.download(ticker, period="1y", interval="1d",
                         progress=False, auto_adjust=True)
        if df.empty or len(df) < 210:
            return None

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        close  = df["Close"].squeeze()
        high   = df["High"].squeeze()
        low    = df["Low"].squeeze()
        volume = df["Volume"].squeeze()

        if not isinstance(close, pd.Series) or len(close) < 210:
            return None

        current_price = float(close.iloc[-1])

        # Pre-filter 1: ADV >= Rs 50 Cr
        daily_value = close * volume
        adv_20d     = float(daily_value.rolling(20).mean().iloc[-1])
        adv_cr      = adv_20d / 1e7
        if adv_cr < ADV_MIN_CR:
            return {
                "symbol": sym_clean, "signal": "FILTERED",
                "confidence": 0.0,
                "filter_reason": f"ADV {adv_cr:.1f} Cr < {ADV_MIN_CR} Cr minimum",
                "generated_at": datetime.now().isoformat(),
            }

        # Pre-filter 2: 20-day volatility <= 3.5%
        daily_returns = close.pct_change().dropna()
        vol_20d       = float(daily_returns.iloc[-20:].std() * 100)
        if vol_20d > VOL_MAX_PCT:
            return {
                "symbol": sym_clean, "signal": "FILTERED",
                "confidence": 0.0,
                "filter_reason": f"Volatility {vol_20d:.1f}% > {VOL_MAX_PCT}% cap",
                "generated_at": datetime.now().isoformat(),
            }

        # Pre-filter 3: above 200-day SMA (long-term uptrend, avoid falling knives)
        sma200 = float(close.rolling(200).mean().iloc[-1])
        if current_price < sma200:
            return {
                "symbol": sym_clean, "signal": "FILTERED",
                "confidence": 0.0,
                "filter_reason": f"Below 200d SMA (Rs {current_price:.2f} < Rs {sma200:.2f})",
                "generated_at": datetime.now().isoformat(),
            }

        # ── Factor 1: Donchian 20-day breakout ────────────────────────────────
        high_20d_yest = float(high.iloc[-21:-1].max())
        donchian = current_price >= high_20d_yest * 0.998

        # ── Factor 2: ADX > 25 ────────────────────────────────────────────────
        adx = _compute_adx(df)
        strong_trend = adx > 25

        # ── Factor 3: Sector relative strength ────────────────────────────────
        sector = SECTOR_MAP.get(sym_clean, "Other")
        sec_ret, nif_ret, sec_rs = _sector_relative_strength(sector)
        sector_strong = sec_rs is not None and sec_rs > 1.0

        # ── Factor 4: Volume surge 2.5x ───────────────────────────────────────
        today_vol   = float(volume.iloc[-1])
        vol_20d_avg = float(volume.iloc[-21:-1].mean())
        vol_surge   = (today_vol > 2.5 * vol_20d_avg) if vol_20d_avg > 0 else False

        # ── Factor 5: Above 50-day EMA (medium-term uptrend, >1% above) ───────
        ema50 = float(close.ewm(span=50, adjust=False).mean().iloc[-1])
        above_ema = current_price > ema50 * 1.01

        score = (
            (20 if donchian      else 0) +
            (20 if strong_trend  else 0) +
            (20 if sector_strong else 0) +
            (20 if vol_surge     else 0) +
            (20 if above_ema     else 0)
        )

        return {
            "symbol":                  sym_clean,
            "signal":                  "BUY" if score >= DEFAULT_MIN_SCORE else "HOLD",
            "confidence":              float(score),
            "current_price":           round(current_price, 2),
            "sector":                  sector,
            "suggested_position_size": _suggested_size(score),
            "adx":                     round(adx, 1),
            "sector_rs":               round(sec_rs, 2) if sec_rs is not None else None,
            "vol_ratio":               round(today_vol / vol_20d_avg, 2) if vol_20d_avg > 0 else 0,
            "ema50":                   round(ema50, 2),
            "sma200":                  round(sma200, 2),
            "donchian_high_yest":      round(high_20d_yest, 2),
            "adv_cr":                  round(adv_cr, 1),
            "volatility_20d":          round(vol_20d, 2),
            "score_breakdown": {
                "donchian":      donchian,
                "adx_above_25":  strong_trend,
                "sector_strong": sector_strong,
                "vol_surge":     vol_surge,
                "uptrend":       above_ema,
            },
            "generated_at": datetime.now().isoformat(),
        }

    except Exception as e:
        return {
            "symbol":     sym_clean,
            "signal":     "ERROR",
            "confidence": 0.0,
            "error":      str(e)[:120],
            "generated_at": datetime.now().isoformat(),
        }


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("symbols", nargs="*",
                        help="NSE symbols to score (default: full universe)")
    parser.add_argument("--min-score", type=int, default=DEFAULT_MIN_SCORE)
    parser.add_argument("--all", action="store_true",
                        help="Output all symbols including HOLD and FILTERED")
    args = parser.parse_args()

    symbols   = args.symbols if args.symbols else UNIVERSE
    min_score = args.min_score

    results = {}
    for sym in symbols:
        print(f"Scoring {sym}...", file=sys.stderr)
        r = score_symbol(sym)
        if r:
            results[r["symbol"]] = r

    if args.all:
        output = dict(sorted(results.items(),
                             key=lambda x: x[1]["confidence"], reverse=True))
    else:
        output = {
            k: v for k, v in sorted(
                results.items(),
                key=lambda x: x[1]["confidence"], reverse=True
            )
            if v.get("confidence", 0) >= min_score and v.get("signal") == "BUY"
        }

    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
