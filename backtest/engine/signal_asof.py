#!/usr/bin/env python3
"""
signal_asof.py — As-of-date momentum scoring + helpers.

Improvements over POC v1:
  - Parquet-cached price data with 7-day TTL (instant reruns)
  - Ticker alias map (handles ZOMATO->ETERNAL, M&M URL-encoded, etc.)
  - Symbol exclusion list (TATAMOTORS demerged, LTIM, CANFIN unresolvable)
  - Nifty benchmark fallback chain (^NSEI -> NIFTYBEES.NS)
  - compute_regime_asof() — bull/bear/sideways for trade tagging
  - constituents_asof() — placeholder for Phase B quarterly constituents
"""
import json, sys, time, warnings
from datetime import date, datetime, timedelta
from pathlib import Path
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import yfinance as yf

REPO = Path(__file__).resolve().parents[2]
DATA = Path(__file__).resolve().parents[1] / "data"
PRICE_CACHE_DIR = DATA / "prices_cache"
PRICE_CACHE_TTL_DAYS = 7

sys.path.insert(0, str(REPO))
from models.signal_generator import SECTOR_MAP, UNIVERSE, ADV_MIN_CR, VOL_MAX_PCT, DEFAULT_MIN_SCORE


# ── Ticker alias resolution ───────────────────────────────────────────────────
_ALIASES: dict[str, str] = {}
_EXCLUDED: set[str] = set()


def _load_aliases() -> None:
    """Load ticker_aliases.json if present."""
    global _ALIASES, _EXCLUDED
    f = DATA / "ticker_aliases.json"
    if not f.exists():
        return
    obj = json.loads(f.read_text())
    _ALIASES = obj.get("aliases", {})
    _EXCLUDED = set(obj.get("exclude", []))


def resolve_ticker(symbol: str) -> str | None:
    """
    Map an NSE symbol to its yfinance ticker. Returns None if excluded.
    Default: 'SYMBOL.NS'. Aliases override.
    """
    sym = symbol.upper().replace(".NS", "")
    if sym in _EXCLUDED:
        return None
    if sym in _ALIASES:
        return _ALIASES[sym]
    return sym + ".NS"


# ── Per-symbol price cache (in-memory + on-disk parquet) ──────────────────────
_CACHE: dict[str, pd.DataFrame] = {}


def _parquet_path(symbol: str) -> Path:
    safe = symbol.upper().replace(".NS", "").replace("&", "AND").replace("-", "_")
    return PRICE_CACHE_DIR / f"{safe}.parquet"


def _load_from_disk(symbol: str) -> pd.DataFrame | None:
    p = _parquet_path(symbol)
    if not p.exists():
        return None
    age_days = (time.time() - p.stat().st_mtime) / 86400.0
    if age_days > PRICE_CACHE_TTL_DAYS:
        return None
    try:
        df = pd.read_parquet(p)
        return df
    except Exception:
        return None


def _save_to_disk(symbol: str, df: pd.DataFrame) -> None:
    PRICE_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    try:
        df.to_parquet(_parquet_path(symbol))
    except Exception as e:
        print(f"  warn: failed to cache {symbol} to parquet: {e}", file=sys.stderr)


def prime_cache(symbols: list[str], start: date, end: date,
                lookback_days: int = 400) -> dict[str, str]:
    """
    Bulk-fetch all symbols. Disk-cached so reruns are instant.
    Returns: {symbol: status} where status in {ok, cached, excluded, failed}
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed

    _load_aliases()

    fetch_start = start - timedelta(days=lookback_days)
    fetch_end   = end + timedelta(days=2)
    status: dict[str, str] = {}

    def fetch_one(sym: str) -> tuple[str, pd.DataFrame | None, str]:
        sym = sym.upper().replace(".NS", "")
        ticker = resolve_ticker(sym)
        if ticker is None:
            return sym, None, "excluded"

        # Try disk cache first
        cached = _load_from_disk(sym)
        if cached is not None and len(cached) >= 60:
            cmin, cmax = cached.index.min().date(), cached.index.max().date()
            # Allow cmin to be up to 7 days AFTER fetch_start (yfinance start
            # is inclusive but actual data may begin a few days later due to
            # holidays/weekends). Require cmax to cover the end window.
            if cmin <= fetch_start + timedelta(days=7) and cmax >= fetch_end - timedelta(days=2):
                return sym, cached, "cached"

        # Network fetch
        try:
            tkr = yf.Ticker(ticker)
            df = tkr.history(start=fetch_start, end=fetch_end,
                             interval="1d", auto_adjust=True)
            if df is None or df.empty or len(df) < 60:
                return sym, None, "failed"
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            if df.index.tz is not None:
                df.index = df.index.tz_localize(None)
            _save_to_disk(sym, df)
            return sym, df, "ok"
        except Exception:
            return sym, None, "failed"

    print(f"Priming cache for {len(symbols)} symbols "
          f"({fetch_start} to {fetch_end}, lookback {lookback_days}d)...",
          file=sys.stderr)
    counts = {"ok": 0, "cached": 0, "excluded": 0, "failed": 0}
    with ThreadPoolExecutor(max_workers=8) as ex:
        futures = {ex.submit(fetch_one, s): s for s in symbols}
        for fut in as_completed(futures):
            sym, df, st = fut.result()
            status[sym] = st
            counts[st] = counts.get(st, 0) + 1
            if df is not None:
                _CACHE[sym] = df

    print(f"Cache primed — ok: {counts['ok']}, cached: {counts['cached']}, "
          f"excluded: {counts['excluded']}, failed: {counts['failed']}",
          file=sys.stderr)
    return status


# ── Scoring (as-of-date) ──────────────────────────────────────────────────────
def _rsi(series: pd.Series, period: int = 14) -> float:
    delta = series.diff()
    gain  = delta.clip(lower=0).rolling(period).mean()
    loss  = (-delta.clip(upper=0)).rolling(period).mean()
    rs    = gain / loss.replace(0, np.nan)
    rsi_s = 100 - 100 / (1 + rs)
    val   = rsi_s.iloc[-1]
    return float(val) if pd.notna(val) else 50.0


# Tier sizes — overridable via set_tier_sizes() before backtest runs
_TIER_HIGH = 70_000  # score 80-100
_TIER_MID  = 50_000  # score 60-79
_TIER_LOW  = 30_000  # score 40-59


def set_tier_sizes(high: int, mid: int, low: int) -> None:
    """Override default position-size tiers. Call before prime_cache/score loop."""
    global _TIER_HIGH, _TIER_MID, _TIER_LOW
    _TIER_HIGH, _TIER_MID, _TIER_LOW = int(high), int(mid), int(low)


def _suggested_size(score: int) -> int:
    if score >= 80:   return _TIER_HIGH
    elif score >= 60: return _TIER_MID
    else:             return _TIER_LOW


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
    if not isinstance(close, pd.Series) or len(close) < 60:
        return None

    current_price = float(close.iloc[-1])

    daily_value = close * volume
    adv_20d = float(daily_value.rolling(20).mean().iloc[-1])
    adv_cr  = adv_20d / 1e7
    if adv_cr < ADV_MIN_CR:
        return {"symbol": sym, "signal": "FILTERED", "confidence": 0.0,
                "filter_reason": f"ADV {adv_cr:.1f} Cr < {ADV_MIN_CR}"}

    daily_returns = close.pct_change().dropna()
    vol_20d = float(daily_returns.iloc[-20:].std() * 100)
    if vol_20d > VOL_MAX_PCT:
        return {"symbol": sym, "signal": "FILTERED", "confidence": 0.0,
                "filter_reason": f"Volatility {vol_20d:.1f}% > {VOL_MAX_PCT}%"}

    sma20      = float(close.rolling(20).mean().iloc[-1])
    sma50      = float(close.rolling(50).mean().iloc[-1])
    above_smas = current_price > sma20 and current_price > sma50

    rsi    = _rsi(close)
    rsi_ok = 50.0 <= rsi <= 65.0

    vol_5d    = float(volume.iloc[-5:].mean())
    vol_20d_m = float(volume.rolling(20).mean().iloc[-1])
    vol_surge = (vol_5d > 1.2 * vol_20d_m) if vol_20d_m > 0 else False

    high_52w  = float(close.rolling(min(252, len(close))).max().iloc[-1])
    near_high = current_price >= 0.95 * high_52w

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

    return {
        "symbol":                  sym,
        "signal":                  "BUY" if score >= DEFAULT_MIN_SCORE else "HOLD",
        "confidence":              float(score),
        "current_price":           round(current_price, 2),
        "sector":                  SECTOR_MAP.get(sym, "Other"),
        "suggested_position_size": _suggested_size(score),
        "rsi":                     round(rsi, 1),
        "momentum_10d_pct":        round(mom_10d, 2),
        "adv_cr":                  round(adv_cr, 1),
        "volatility_20d":          round(vol_20d, 2),
    }


# ── OHLC + trading day helpers ────────────────────────────────────────────────
def get_ohlc(symbol: str, d: date) -> dict | None:
    sym = symbol.upper().replace(".NS", "")
    full = _CACHE.get(sym)
    if full is None:
        return None
    rows = full[full.index.date == d]
    if rows.empty:
        return None
    row = rows.iloc[0]
    return {
        "open":   float(row["Open"]),
        "high":   float(row["High"]),
        "low":    float(row["Low"]),
        "close":  float(row["Close"]),
        "volume": float(row["Volume"]),
    }


# ── Nifty 50 benchmark with fallback chain ────────────────────────────────────
def _fetch_benchmark(start: date, end: date) -> pd.DataFrame | None:
    """Try ^NSEI first, then NIFTYBEES.NS. Cache to disk.
    Cache hit requires the cached data to actually cover the requested range."""
    needed_start = start - timedelta(days=120)
    needed_end   = end
    for tk in ("^NSEI", "NIFTYBEES.NS"):
        cached = _load_from_disk(tk)
        if cached is not None and len(cached) >= 60:
            cmin, cmax = cached.index.min().date(), cached.index.max().date()
            if cmin <= needed_start + timedelta(days=7) and cmax >= needed_end - timedelta(days=2):
                print(f"  benchmark loaded from disk: {tk} ({cmin} -> {cmax})", file=sys.stderr)
                return cached
            print(f"  benchmark disk cache stale for {tk} ({cmin} -> {cmax}), refetching", file=sys.stderr)
        for attempt in range(3):
            try:
                df = yf.Ticker(tk).history(
                    start=start - timedelta(days=120),  # need ≥20 trading days for SMA slope
                    end=end + timedelta(days=2),
                    interval="1d", auto_adjust=True,
                )
                if df is not None and not df.empty:
                    if isinstance(df.columns, pd.MultiIndex):
                        df.columns = df.columns.get_level_values(0)
                    if df.index.tz is not None:
                        df.index = df.index.tz_localize(None)
                    _save_to_disk(tk, df)
                    print(f"  benchmark fetched: {tk}", file=sys.stderr)
                    return df
            except Exception:
                pass
            time.sleep(2 ** attempt)
        print(f"  benchmark {tk} failed all retries", file=sys.stderr)
    return None


def prime_benchmark(start: date, end: date) -> bool:
    """Prime Nifty benchmark cache. Returns True if available."""
    df = _fetch_benchmark(start, end)
    if df is not None:
        _CACHE["^NSEI"] = df  # store under canonical key
        return True
    return False


def trading_days(start: date, end: date) -> list[date]:
    src = _CACHE.get("^NSEI")
    if src is None or src.empty:
        src = _CACHE.get("RELIANCE")  # last-resort fallback
    if src is None or src.empty:
        all_dates = set()
        for df in _CACHE.values():
            if not df.empty:
                all_dates.update(d.date() for d in df.index)
        return sorted(d for d in all_dates if start <= d <= end)
    return [d.date() for d in src.index if start <= d.date() <= end]


def nifty_close(d: date) -> float | None:
    src = _CACHE.get("^NSEI")
    if src is None or src.empty:
        return None
    rows = src[src.index.date == d]
    if rows.empty:
        return None
    return float(rows.iloc[0]["Close"])


# ── Regime detection (as-of-date) ─────────────────────────────────────────────
def compute_regime_asof(d: date) -> str:
    """Compute regime as-of date d using Nifty 20-day SMA slope.

    bull:     slope > +1.5%
    bear:     slope < -1.5%
    sideways: in between
    """
    src = _CACHE.get("^NSEI")
    if src is None or src.empty:
        return "unknown"
    df = src[src.index.date <= d]
    if len(df) < 22:
        return "unknown"
    sma20 = df["Close"].rolling(20).mean()
    sma_now = float(sma20.iloc[-1])
    sma_prev = float(sma20.iloc[-21]) if len(sma20) >= 21 else float(sma20.dropna().iloc[0])
    if sma_prev <= 0:
        return "unknown"
    slope_pct = (sma_now - sma_prev) / sma_prev * 100
    if slope_pct > 1.5:
        return "bull"
    if slope_pct < -1.5:
        return "bear"
    return "sideways"


# ── Quarterly constituents (stubbed for POC; Phase B populates) ───────────────
_CONSTITUENTS: dict[str, dict] | None = None


def _load_constituents() -> dict:
    global _CONSTITUENTS
    if _CONSTITUENTS is not None:
        return _CONSTITUENTS
    f = DATA / "index_constituents.json"
    if f.exists():
        _CONSTITUENTS = json.loads(f.read_text())
    else:
        _CONSTITUENTS = {"quarters": {}}
    return _CONSTITUENTS


def _date_to_quarter(d: date) -> str:
    q = (d.month - 1) // 3 + 1
    return f"{d.year}-Q{q}"


def constituents_asof(d: date, default_universe: list[str]) -> list[str]:
    """
    Return the index constituents valid as-of date d. Stubbed for POC: returns
    default_universe unless a quarter-specific list is configured.
    Phase B should populate quarterly constituent lists from NSE archives.
    """
    cfg = _load_constituents()
    q = _date_to_quarter(d)
    quarters = cfg.get("quarters", {})
    q_entry = quarters.get(q)
    if q_entry is None or q_entry.get("use_default_universe", True):
        return default_universe
    return q_entry.get("symbols", default_universe)
