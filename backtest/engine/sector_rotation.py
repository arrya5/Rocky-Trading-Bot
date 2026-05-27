#!/usr/bin/env python3
"""
sector_rotation.py — Monthly sector momentum rotation.

Hypothesis: Sector momentum is more reliable than individual-stock momentum.
At month-end, rank sectors by 1-month return. Hold top 3 sectors equally
weighted via their ETFs/indices. Rotate monthly.

Indian sector indices/ETFs (via yfinance):
  ^NSEI         Nifty 50 (broad market)
  ^CNXBANK      Nifty Bank
  ^CNXIT        Nifty IT
  ^CNXAUTO      Nifty Auto
  ^CNXPHARMA    Nifty Pharma
  ^CNXFMCG      Nifty FMCG
  ^CNXMETAL     Nifty Metal
  ^CNXENERGY    Nifty Energy
  ^CNXREALTY    Nifty Realty
  ^CNXMEDIA     Nifty Media
"""
import sys, warnings
from datetime import date, timedelta
from pathlib import Path
warnings.filterwarnings("ignore")

import pandas as pd
import yfinance as yf

REPO = Path(__file__).resolve().parents[2]


SECTOR_TICKERS = {
    "Bank":     "^CNXBANK",
    "IT":       "^CNXIT",
    "Auto":     "^CNXAUTO",
    "Pharma":   "^CNXPHARMA",
    "FMCG":     "^CNXFMCG",
    "Metal":    "^CNXMETAL",
    "Energy":   "^CNXENERGY",
    "Realty":   "^CNXREALTY",
    "Media":    "^CNXMEDIA",
    "Infra":   "^CNXINFRA",
}


_DATA: dict[str, pd.DataFrame] = {}


def prime_sector_data(start: date, end: date) -> dict[str, bool]:
    """Fetch all sector indices for the backtest period."""
    fetch_start = start - timedelta(days=90)  # need 60+ days lookback for 1-month return
    fetch_end   = end + timedelta(days=2)
    status = {}
    for sector, ticker in SECTOR_TICKERS.items():
        try:
            df = yf.Ticker(ticker).history(start=fetch_start, end=fetch_end,
                                            interval="1d", auto_adjust=True)
            if df is None or df.empty or len(df) < 30:
                status[sector] = False
                continue
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            if df.index.tz is not None:
                df.index = df.index.tz_localize(None)
            _DATA[sector] = df
            status[sector] = True
        except Exception as e:
            print(f"  failed to fetch {sector} ({ticker}): {e}", file=sys.stderr)
            status[sector] = False
    return status


def rank_sectors_at(d: date, lookback_days: int = 21) -> list[tuple[str, float]]:
    """Return (sector, N-day return %) sorted descending."""
    rankings = []
    for sector, df in _DATA.items():
        rows = df[df.index.date <= d]
        if len(rows) < lookback_days + 1:
            continue
        end_price   = float(rows["Close"].iloc[-1])
        start_price = float(rows["Close"].iloc[-lookback_days-1])
        ret_pct = (end_price - start_price) / start_price * 100
        rankings.append((sector, ret_pct))
    rankings.sort(key=lambda x: -x[1])
    return rankings


def get_sector_price(sector: str, d: date, field: str = "Open") -> float | None:
    df = _DATA.get(sector)
    if df is None:
        return None
    rows = df[df.index.date == d]
    if rows.empty:
        return None
    return float(rows.iloc[0][field])


def get_sector_trading_days(start: date, end: date) -> list[date]:
    """Use Bank Nifty as the calendar (most reliable)."""
    src = _DATA.get("Bank") or next(iter(_DATA.values()), None)
    if src is None:
        return []
    return [d.date() for d in src.index if start <= d.date() <= end]


def run_sector_rotation_backtest(start_date: str, end_date: str,
                                  starting_capital: int = 500_000,
                                  top_n: int = 3,
                                  rebalance_freq_days: int = 21,
                                  lookback_days: int = 21,
                                  costs: dict | None = None) -> dict:
    """
    Monthly sector rotation:
    - Every `rebalance_freq_days` trading days, rank sectors by previous N-day return
    - Hold top `top_n` sectors equally weighted
    - Sell anything that drops out of top_n
    - Buy new entrants
    """
    if costs is None:
        costs = {"stt_sell_pct": 0.001, "brokerage_per_order": 20}

    start = date.fromisoformat(start_date)
    end   = date.fromisoformat(end_date)

    print(f"Priming sector data...", file=sys.stderr)
    status = prime_sector_data(start, end)
    available = [s for s, ok in status.items() if ok]
    print(f"  available sectors: {available}", file=sys.stderr)

    all_days = get_sector_trading_days(start, end)
    if not all_days:
        raise RuntimeError("No trading days for sector rotation")

    print(f"Sector rotation: {all_days[0]} -> {all_days[-1]} ({len(all_days)} days)", file=sys.stderr)

    cash = float(starting_capital)
    holdings: dict[str, dict] = {}  # sector -> {units, entry_price, entry_date}
    trade_log: list[dict] = []
    snapshots: list[dict] = []

    days_since_rebalance = rebalance_freq_days  # rebalance on day 1

    for i, d in enumerate(all_days):
        # Mark-to-market
        mv = sum(h["units"] * (get_sector_price(s, d, "Close") or h["entry_price"])
                 for s, h in holdings.items())
        total_value = cash + mv

        # Check if it's a rebalance day
        if days_since_rebalance >= rebalance_freq_days:
            # Rank sectors
            ranked = rank_sectors_at(d, lookback_days=lookback_days)
            new_top = [s for s, _ in ranked[:top_n]]

            # Exit positions not in new_top
            for sector in list(holdings.keys()):
                if sector not in new_top:
                    price = get_sector_price(sector, d, "Open") or holdings[sector]["entry_price"]
                    units = holdings[sector]["units"]
                    gross_proceeds = units * price
                    stt = gross_proceeds * costs["stt_sell_pct"]
                    brk = costs["brokerage_per_order"]
                    cash += gross_proceeds - stt - brk

                    pnl_pct = (price - holdings[sector]["entry_price"]) / holdings[sector]["entry_price"] * 100
                    days_held = (d - holdings[sector]["entry_date"]).days

                    trade_log.append({
                        "sector":      sector,
                        "entry_date":  holdings[sector]["entry_date"].isoformat(),
                        "exit_date":   d.isoformat(),
                        "entry_price": holdings[sector]["entry_price"],
                        "exit_price":  price,
                        "units":       units,
                        "pnl_pct":     round(pnl_pct, 2),
                        "pnl_abs":     round(gross_proceeds - stt - brk - (units * holdings[sector]["entry_price"]), 2),
                        "days_held":   days_held,
                        "reason":      "rotated_out",
                    })
                    del holdings[sector]

            # Enter new positions (equal weight across top_n slots)
            entries_to_make = [s for s in new_top if s not in holdings]
            if entries_to_make:
                # Allocate cash equally across the empty slots
                target_slots = top_n - len(holdings)
                if target_slots > 0:
                    per_position = cash * 0.95 / target_slots  # keep 5% buffer
                    for sector in entries_to_make[:target_slots]:
                        price = get_sector_price(sector, d, "Open")
                        if price is None or price <= 0:
                            continue
                        units = per_position / price  # fractional units OK for indices
                        cost = units * price + costs["brokerage_per_order"]
                        if cost > cash:
                            continue
                        cash -= cost
                        holdings[sector] = {
                            "units":        units,
                            "entry_price":  price,
                            "entry_date":   d,
                        }

            days_since_rebalance = 0
        else:
            days_since_rebalance += 1

        # Re-mark-to-market after rebalance
        mv = sum(h["units"] * (get_sector_price(s, d, "Close") or h["entry_price"])
                 for s, h in holdings.items())
        total_value = cash + mv

        snapshots.append({
            "date":        d.isoformat(),
            "cash":        round(cash, 2),
            "n_holdings":  len(holdings),
            "total_value": round(total_value, 2),
            "holdings":    list(holdings.keys()),
        })

        if (i + 1) % 50 == 0:
            print(f"  [{d}] {i+1}/{len(all_days)} | Rs {total_value:,.0f} | "
                  f"holdings: {list(holdings.keys())}", file=sys.stderr)

    # Close all at end
    last_day = all_days[-1]
    for sector in list(holdings.keys()):
        price = get_sector_price(sector, last_day, "Close") or holdings[sector]["entry_price"]
        units = holdings[sector]["units"]
        gross = units * price
        stt = gross * costs["stt_sell_pct"]
        brk = costs["brokerage_per_order"]
        cash += gross - stt - brk
        pnl_pct = (price - holdings[sector]["entry_price"]) / holdings[sector]["entry_price"] * 100
        trade_log.append({
            "sector": sector, "entry_date": holdings[sector]["entry_date"].isoformat(),
            "exit_date": last_day.isoformat(), "entry_price": holdings[sector]["entry_price"],
            "exit_price": price, "units": units,
            "pnl_pct": round(pnl_pct, 2),
            "pnl_abs": round(gross - stt - brk - (units * holdings[sector]["entry_price"]), 2),
            "days_held": (last_day - holdings[sector]["entry_date"]).days,
            "reason": "final_close",
        })
        del holdings[sector]

    # Nifty benchmark
    nifty_df = _DATA.get("Bank")  # use whatever we have
    nifty_ret_pct = 0.0
    if "^NSEI" not in _DATA:
        try:
            nifty_df = yf.Ticker("^NSEI").history(start=start - timedelta(days=5),
                                                    end=end + timedelta(days=2),
                                                    interval="1d", auto_adjust=True)
            if nifty_df is not None and not nifty_df.empty:
                if isinstance(nifty_df.columns, pd.MultiIndex):
                    nifty_df.columns = nifty_df.columns.get_level_values(0)
                _DATA["^NSEI"] = nifty_df
                start_p = float(nifty_df[nifty_df.index.date >= start]["Close"].iloc[0])
                end_p   = float(nifty_df[nifty_df.index.date <= end]["Close"].iloc[-1])
                nifty_ret_pct = (end_p - start_p) / start_p * 100
        except Exception:
            pass

    return {
        "config": {"start_date": start_date, "end_date": end_date,
                   "starting_capital": starting_capital,
                   "top_n": top_n, "rebalance_freq_days": rebalance_freq_days,
                   "lookback_days": lookback_days},
        "snapshots": snapshots,
        "trades":    trade_log,
        "nifty_return_pct": nifty_ret_pct,
        "trading_days": len(all_days),
    }
