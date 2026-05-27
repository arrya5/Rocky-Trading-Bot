#!/usr/bin/env python3
"""
cache_vix.py — Download India VIX (^INDIAVIX) historical daily data
covering the POC + Phase B periods (2023-01-01 to today).
"""
import sys, warnings
from pathlib import Path
warnings.filterwarnings("ignore")

import yfinance as yf
import pandas as pd

OUT = Path(__file__).resolve().parents[1] / "data" / "historical_vix.csv"
OUT.parent.mkdir(parents=True, exist_ok=True)

df = yf.download("^INDIAVIX", start="2023-01-01", end="2026-12-31",
                 interval="1d", progress=False, auto_adjust=True)

if df.empty:
    print("ERROR: yfinance returned no VIX data", file=sys.stderr)
    sys.exit(1)

if isinstance(df.columns, pd.MultiIndex):
    df.columns = df.columns.get_level_values(0)

df = df[["Close"]].rename(columns={"Close": "vix"})
df.index.name = "date"
df = df.dropna()
df.to_csv(OUT)
print(f"Cached {len(df)} VIX rows from {df.index[0].date()} to {df.index[-1].date()} -> {OUT}")
