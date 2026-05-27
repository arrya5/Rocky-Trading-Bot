#!/usr/bin/env python3
"""
run_etf_swing.py — Apply swing v2 logic to Indian sector indices instead of
individual midcap stocks. Fewer instruments, less noise, smoother trends.
"""
import json, sys, time, warnings
from datetime import date, timedelta
from collections import defaultdict
from pathlib import Path
warnings.filterwarnings("ignore")

import pandas as pd
import yfinance as yf

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
sys.path.insert(0, str(REPO))

from backtest.engine import signal_asof, gates
from backtest.engine.swing_portfolio import SwingPaperPortfolio


# Sector indices (universe for ETF swing)
ETF_UNIVERSE = {
    "BANKBEES":   "^CNXBANK",
    "ITBEES":     "^CNXIT",
    "AUTOBEES":   "^CNXAUTO",
    "PHARMABEES": "^CNXPHARMA",
    "FMCGBEES":   "^CNXFMCG",
    "METALBEES":  "^CNXMETAL",
    "ENERGYBEES": "^CNXENERGY",
    "REALTYBEES": "^CNXREALTY",
    "INFRABEES":  "^CNXINFRA",
    "NIFTYBEES":  "^NSEI",
}

PERIODS = {
    "poc":     ("2025-05-01", "2025-10-31"),
    "holdout": ("2024-11-01", "2025-04-30"),
}


_ETF_CACHE: dict[str, pd.DataFrame] = {}


def prime_etf_cache(start: date, end: date) -> int:
    fetch_start = start - timedelta(days=300)
    fetch_end   = end + timedelta(days=2)
    ok = 0
    for name, ticker in ETF_UNIVERSE.items():
        try:
            df = yf.Ticker(ticker).history(start=fetch_start, end=fetch_end,
                                            interval="1d", auto_adjust=True)
            if df is None or df.empty or len(df) < 60:
                continue
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            if df.index.tz is not None:
                df.index = df.index.tz_localize(None)
            _ETF_CACHE[name] = df
            ok += 1
        except Exception:
            continue
    return ok


def _adx(df: pd.DataFrame, period: int = 14) -> float:
    import numpy as np
    high  = df["High"]; low = df["Low"]; close = df["Close"]
    plus_dm  = high.diff()
    minus_dm = -low.diff()
    plus_dm  = plus_dm.where((plus_dm > minus_dm) & (plus_dm > 0), 0)
    minus_dm = minus_dm.where((minus_dm > plus_dm) & (minus_dm > 0), 0)
    tr = pd.concat([high - low, (high - close.shift()).abs(), (low - close.shift()).abs()], axis=1).max(axis=1)
    atr = tr.ewm(span=period, adjust=False).mean()
    plus_di  = 100 * (plus_dm.ewm(span=period, adjust=False).mean() / atr.replace(0, float("nan")))
    minus_di = 100 * (minus_dm.ewm(span=period, adjust=False).mean() / atr.replace(0, float("nan")))
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, float("nan"))
    adx = dx.ewm(span=period, adjust=False).mean()
    val = adx.iloc[-1]
    return float(val) if pd.notna(val) else 0.0


def _atr_pct(df: pd.DataFrame, period: int = 14) -> float:
    high = df["High"]; low = df["Low"]; close = df["Close"]
    tr = pd.concat([high - low, (high - close.shift()).abs(), (low - close.shift()).abs()], axis=1).max(axis=1)
    atr = tr.rolling(period).mean().iloc[-1]
    cur = float(close.iloc[-1])
    return float(atr / cur * 100) if cur > 0 and pd.notna(atr) else 0.0


def score_etf_asof(name: str, as_of: date) -> dict | None:
    df_full = _ETF_CACHE.get(name)
    if df_full is None:
        return None
    df = df_full[df_full.index.date <= as_of]
    if len(df) < 60:
        return None

    close = df["Close"]
    high  = df["High"]
    current = float(close.iloc[-1])

    # ETFs are inherently liquid, skip ADV filter
    # Volatility filter (looser for indices — usually <2.5%)
    vol_20d = float(close.pct_change().dropna().iloc[-20:].std() * 100)

    # Donchian 20-day breakout
    high_20d_yest = float(high.iloc[-21:-1].max())
    donchian = current >= high_20d_yest * 0.998

    # ADX > 20 (slightly looser for indices)
    adx = _adx(df)
    strong_trend = adx > 20

    # Volume surge (1.5x 20-day avg for indices)
    vol = df["Volume"]
    today_vol = float(vol.iloc[-1])
    avg_vol = float(vol.iloc[-21:-1].mean()) if not vol.iloc[-21:-1].empty else 0
    vol_surge = (today_vol > 1.5 * avg_vol) if avg_vol > 0 else False

    # Above 50d EMA
    ema50 = float(close.ewm(span=50, adjust=False).mean().iloc[-1])
    above_ema = current > ema50 * 1.01

    # 5-day return positive
    p5 = float(close.iloc[-6])
    mom5 = (current - p5) / p5 * 100
    has_momentum = mom5 > 0.5

    score = (
        (20 if donchian      else 0) +
        (20 if strong_trend  else 0) +
        (20 if vol_surge     else 0) +
        (20 if above_ema     else 0) +
        (20 if has_momentum  else 0)
    )

    atr_pct = _atr_pct(df)
    stop_dist = max(2.5, min(5.0, atr_pct * 2.0))
    partial_tgt = max(3.0, min(7.0, atr_pct * 1.5))
    trail_trig = max(5.0, min(10.0, atr_pct * 2.5))
    trail_dist = max(2.0, min(4.0, atr_pct * 1.5))

    return {
        "symbol": name,
        "signal": "BUY" if score >= 60 else "HOLD",
        "confidence": float(score),
        "current_price": round(current, 2),
        "sector": name.replace("BEES", ""),
        "suggested_position_size": 50000 if score >= 80 else 35000,
        "adx": round(adx, 1),
        "atr_pct": round(atr_pct, 2),
        "stop_distance_pct": stop_dist,
        "partial_target_pct": partial_tgt,
        "trailing_trigger_pct": trail_trig,
        "trailing_distance_pct": trail_dist,
    }


def get_etf_ohlc(name: str, d: date) -> dict | None:
    df = _ETF_CACHE.get(name)
    if df is None:
        return None
    rows = df[df.index.date == d]
    if rows.empty:
        return None
    row = rows.iloc[0]
    return {"open": float(row["Open"]), "high": float(row["High"]),
            "low": float(row["Low"]), "close": float(row["Close"])}


def previous_trading_day(d, all_days):
    earlier = [x for x in all_days if x < d]
    return earlier[-1] if earlier else None


def run(start_str: str, end_str: str, label: str):
    start = date.fromisoformat(start_str)
    end   = date.fromisoformat(end_str)

    n_ok = prime_etf_cache(start, end)
    print(f"  loaded {n_ok}/{len(ETF_UNIVERSE)} ETF/index series", file=sys.stderr)

    signal_asof.prime_benchmark(start, end)

    # Use Nifty for trading days
    nifty_df = signal_asof._CACHE.get("^NSEI")
    if nifty_df is None or nifty_df.empty:
        raise RuntimeError("Nifty 50 data missing")
    all_days = [d.date() for d in nifty_df.index if start <= d.date() <= end]

    cfg = {
        "rules": {"max_hold_days": 10, "sector_max_open": 99},  # no sector cap for ETFs
        "costs": {"stt_sell_pct": 0.001, "brokerage_per_order": 20},
    }

    port = SwingPaperPortfolio(starting_cash=500000, config=cfg)
    nifty_start = signal_asof.nifty_close(all_days[0]) or 0.0

    print(f"ETF swing {label}: {all_days[0]} -> {all_days[-1]} ({len(all_days)} days)", file=sys.stderr)

    for i, d in enumerate(all_days):
        prev = previous_trading_day(d, all_days)
        if prev is None:
            port.snapshot(d, port.cash, signal_asof.nifty_close(d))
            continue

        # Process open
        ohlc_open = {}
        for name in list(port.positions.keys()):
            o = get_etf_ohlc(name, d)
            if o is not None:
                ohlc_open[name] = o
        port.process_day(d, ohlc_open)

        # Score ETFs as of yesterday
        scored = []
        for name in ETF_UNIVERSE.keys():
            r = score_etf_asof(name, prev)
            if r is None or r["signal"] != "BUY":
                continue
            scored.append(r)
        scored.sort(key=lambda x: -x["confidence"])

        for cand in scored[:5]:
            name = cand["symbol"]
            if name in port.positions:
                continue
            ohlc_today = get_etf_ohlc(name, d)
            if ohlc_today is None:
                continue

            entry = ohlc_today["open"]
            qty = int(cand["suggested_position_size"] // entry)
            if qty < 1 or qty * entry > port.cash:
                continue

            ok = port.enter(
                name, cand["sector"], qty, entry, cand["confidence"], d,
                regime="unknown",
                stop_distance_pct=cand["stop_distance_pct"],
                partial_target_pct=cand["partial_target_pct"],
                trailing_trigger_pct=cand["trailing_trigger_pct"],
                trailing_distance_pct=cand["trailing_distance_pct"],
            )
            if ok:
                port.process_day(d, {name: ohlc_today})

        mtm = {}
        for name in port.positions.keys():
            o = get_etf_ohlc(name, d)
            if o is not None:
                mtm[name] = o["close"]
        tv = port.mark_to_market(d, mtm)
        port.snapshot(d, tv, signal_asof.nifty_close(d))

        if (i + 1) % 30 == 0:
            print(f"  [{d}] Rs {tv:,.0f} | open {len(port.positions)} | closed {len(port.closed)}", file=sys.stderr)

    last = all_days[-1]
    closes = {}
    for name in port.positions.keys():
        o = get_etf_ohlc(name, last)
        if o is not None:
            closes[name] = o["close"]
    port.force_close_all(last, closes)

    nifty_end = signal_asof.nifty_close(last) or nifty_start
    nifty_ret = (nifty_end - nifty_start) / nifty_start * 100 if nifty_start else 0

    trades = port.closed
    snaps = port.daily_snapshots
    final = snaps[-1]["total_value"] if snaps else 500000
    ret = (final - 500000) / 500000 * 100
    n_w = sum(1 for t in trades if t.pnl_pct > 0)

    OUT = ROOT / "results"
    OUT.mkdir(exist_ok=True)
    from dataclasses import asdict
    (OUT / f"etfswing_{label}_trades.json").write_text(json.dumps([asdict(t) for t in trades], indent=2, default=str))
    (OUT / f"etfswing_{label}_summary.json").write_text(json.dumps({
        "trades": len(trades), "win_rate": n_w/len(trades)*100 if trades else 0,
        "total_return_pct": ret, "nifty_return_pct": nifty_ret,
        "alpha": ret - nifty_ret,
    }, indent=2))

    print(f"\n=== ETF SWING {label.upper()} ===")
    print(f"Trades:       {len(trades)}")
    print(f"Win rate:     {(n_w/len(trades)*100 if trades else 0):.1f}%")
    print(f"Total return: {ret:+.2f}%")
    print(f"Nifty:        {nifty_ret:+.2f}%")
    print(f"Alpha:        {ret - nifty_ret:+.2f}%")


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in PERIODS:
        print(f"Usage: {' | '.join(PERIODS.keys())}")
        sys.exit(1)
    label = sys.argv[1]
    run(*PERIODS[label], label)


if __name__ == "__main__":
    main()
