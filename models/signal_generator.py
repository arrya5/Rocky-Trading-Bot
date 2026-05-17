#!/usr/bin/env python3
"""
signal_generator.py — Rules-based momentum scorer for NSE stocks

Screens the full Nifty 50 + Midcap 150 universe daily using 5 momentum factors.
No ML, no training — pure arithmetic on real price data via yfinance.

Pre-filters (applied before scoring — stock is excluded entirely if it fails):
  ADV   Average daily traded value (20-day) must be >= Rs 50 Cr
  VOL   20-day daily return std must be <= 3% (exclude hyper-volatile stocks)

Scoring (each factor = 20 points, max 100):
  +20  Price above both 20-SMA and 50-SMA        (confirmed uptrend)
  +20  RSI between 50-65                          (trending, not overbought)
  +20  5-day avg volume > 1.2x 20-day avg volume  (institutional accumulation)
  +20  Price within 5% of 52-week high            (breakout zone)
  +20  10-day return > +1%                        (recent momentum)

BUY  : score >= 40  (2+ factors aligned)
HOLD : score < 40
Confidence = score  (80 score = 80% confidence)

Tiered position sizing (suggested_position_size field):
  score 80-100 -> Rs 70,000
  score 60-79  -> Rs 50,000
  score 40-59  -> Rs 30,000

Usage:
  python models/signal_generator.py                    # scan full universe
  python models/signal_generator.py RELIANCE TCS INFY  # specific symbols only
  python models/signal_generator.py --min-score 60     # raise threshold
  python models/signal_generator.py --all              # include HOLD signals too
"""

import json, sys, warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import yfinance as yf
from datetime import datetime

DEFAULT_MIN_SCORE = 40
ADV_MIN_CR        = 50          # minimum avg daily value in crores
VOL_MAX_PCT       = 3.0         # maximum 20-day daily return std (%)

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
    # Auto & Auto Ancillary
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
    # Metals & Mining
    "TATASTEEL":   "Metals",    "JSWSTEEL":    "Metals",    "HINDALCO":    "Metals",
    "COALINDIA":   "Metals",
    # Consumer & Retail
    "ASIANPAINT":  "Consumer",  "TITAN":       "Consumer",  "VOLTAS":      "Consumer",
    "HAVELLS":     "Consumer",  "PAGEIND":     "Consumer",  "TRENT":       "Consumer",
    "JUBLFOOD":    "Consumer",  "DIXON":       "Consumer",  "KAYNES":      "Consumer",
    "NYKAA":       "Consumer",  "ZOMATO":      "Consumer",
    # Infrastructure & Construction
    "LT":          "Infrastructure", "ULTRACEMCO":  "Infrastructure",
    "GRASIM":      "Infrastructure", "AMBUJACEM":   "Infrastructure",
    "SHREECEM":    "Infrastructure", "RAMCOCEM":    "Infrastructure",
    "APLAPOLLO":   "Infrastructure", "RVNL":        "Infrastructure",
    "ADANIPORTS":  "Infrastructure",
    # Telecom
    "BHARTIARTL":  "Telecom",
    # Chemicals
    "PIDILITIND":  "Chemicals",  "BERGEPAINT":  "Chemicals",  "UPL": "Chemicals",
    # Financial Services / Exchanges
    "CAMS":        "Fin Services", "CDSL":    "Fin Services", "MCX":  "Fin Services",
    "NUVAMA":      "Fin Services", "IIFL":    "Fin Services",
    # Logistics & Railways
    "CONCOR":      "Logistics",  "IRCTC":    "Logistics",  "IRFC":    "Logistics",
    "RAILTEL":     "Logistics",
}

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
    # Nifty Midcap 150 (representative liquid names)
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


def _rsi(series: pd.Series, period: int = 14) -> float:
    delta = series.diff()
    gain  = delta.clip(lower=0).rolling(period).mean()
    loss  = (-delta.clip(upper=0)).rolling(period).mean()
    rs    = gain / loss.replace(0, np.nan)
    rsi_s = 100 - 100 / (1 + rs)
    val   = rsi_s.iloc[-1]
    return float(val) if pd.notna(val) else 50.0


def _suggested_size(score: int) -> int:
    if score >= 80:
        return 70_000
    elif score >= 60:
        return 50_000
    else:
        return 30_000


def score_symbol(symbol: str) -> dict | None:
    sym_clean = symbol.upper().replace(".NS", "")
    ticker    = sym_clean + ".NS"

    try:
        df = yf.download(ticker, period="1y", interval="1d",
                         progress=False, auto_adjust=True)
        if df.empty or len(df) < 60:
            return None

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        close  = df["Close"].squeeze()
        volume = df["Volume"].squeeze()

        if not isinstance(close, pd.Series) or len(close) < 60:
            return None

        current_price = float(close.iloc[-1])

        # ── Pre-filter 1: ADV >= Rs 50 Cr ─────────────────────────────────────
        daily_value    = close * volume
        adv_20d        = float(daily_value.rolling(20).mean().iloc[-1])
        adv_cr         = adv_20d / 1e7          # convert to crores
        if adv_cr < ADV_MIN_CR:
            return {
                "symbol": sym_clean, "signal": "FILTERED",
                "confidence": 0.0, "filter_reason": f"ADV {adv_cr:.1f} Cr < {ADV_MIN_CR} Cr minimum",
                "generated_at": datetime.now().isoformat(),
            }

        # ── Pre-filter 2: 20-day volatility <= 3% ─────────────────────────────
        daily_returns = close.pct_change().dropna()
        vol_20d       = float(daily_returns.iloc[-20:].std() * 100)
        if vol_20d > VOL_MAX_PCT:
            return {
                "symbol": sym_clean, "signal": "FILTERED",
                "confidence": 0.0, "filter_reason": f"Volatility {vol_20d:.1f}% > {VOL_MAX_PCT}% cap",
                "generated_at": datetime.now().isoformat(),
            }

        # ── Factor 1: Price above 20-SMA and 50-SMA ───────────────────────────
        sma20      = float(close.rolling(20).mean().iloc[-1])
        sma50      = float(close.rolling(50).mean().iloc[-1])
        above_smas = current_price > sma20 and current_price > sma50

        # ── Factor 2: RSI 50-65 ────────────────────────────────────────────────
        rsi    = _rsi(close)
        rsi_ok = 50.0 <= rsi <= 65.0

        # ── Factor 3: 5-day avg volume > 1.2x 20-day avg volume ───────────────
        vol_5d    = float(volume.iloc[-5:].mean())
        vol_20d_m = float(volume.rolling(20).mean().iloc[-1])
        vol_surge = (vol_5d > 1.2 * vol_20d_m) if vol_20d_m > 0 else False

        # ── Factor 4: Within 5% of 52-week high ───────────────────────────────
        high_52w  = float(close.rolling(min(252, len(close))).max().iloc[-1])
        near_high = current_price >= 0.95 * high_52w

        # ── Factor 5: 10-day return > +1% ─────────────────────────────────────
        p10     = float(close.iloc[-11]) if len(close) >= 11 else current_price
        mom_10d = (current_price - p10) / p10 * 100
        has_mom = mom_10d > 1.0

        score = (
            (20 if above_smas else 0) +
            (20 if rsi_ok     else 0) +
            (20 if vol_surge  else 0) +
            (20 if near_high  else 0) +
            (20 if has_mom    else 0)
        )

        sector = SECTOR_MAP.get(sym_clean, "Other")

        return {
            "symbol":                 sym_clean,
            "signal":                 "BUY" if score >= DEFAULT_MIN_SCORE else "HOLD",
            "confidence":             float(score),
            "current_price":          round(current_price, 2),
            "sector":                 sector,
            "suggested_position_size": _suggested_size(score),
            "score_breakdown": {
                "above_20_50_sma": above_smas,
                "rsi_trending":    rsi_ok,
                "volume_surge":    vol_surge,
                "near_52w_high":   near_high,
                "momentum_10d":    has_mom,
            },
            "rsi":              round(rsi, 1),
            "momentum_10d_pct": round(mom_10d, 2),
            "adv_cr":           round(adv_cr, 1),
            "volatility_20d":   round(vol_20d, 2),
            "sma20":            round(sma20, 2),
            "sma50":            round(sma50, 2),
            "generated_at":     datetime.now().isoformat(),
        }

    except Exception as e:
        return {
            "symbol":       sym_clean,
            "signal":       "ERROR",
            "confidence":   0.0,
            "error":        str(e)[:120],
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
