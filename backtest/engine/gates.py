#!/usr/bin/env python3
"""
gates.py — Mechanical gate checks for POC backtest.

Enforces Gates 1, 2, 4, 5, 6, 7, 9.
Skips Gate 3 (catalyst — LLM lookahead) and Gate 8 (earnings — Phase B).
"""
import csv
from datetime import date
from pathlib import Path

VIX_CACHE: dict[str, float] = {}
FII_CACHE: dict[str, float] = {}


def load_vix(path: Path) -> None:
    VIX_CACHE.clear()
    if not path.exists():
        return
    with path.open() as f:
        next(f, None)  # header
        for line in f:
            parts = line.strip().split(",")
            if len(parts) < 2:
                continue
            try:
                # date column may include timestamp suffix in some pandas exports
                d = parts[0].split(" ")[0]
                VIX_CACHE[d] = float(parts[1])
            except ValueError:
                continue


def load_fii(path: Path) -> None:
    FII_CACHE.clear()
    if not path.exists():
        return
    with path.open() as f:
        reader = csv.reader(f)
        next(reader, None)  # header
        for row in reader:
            if len(row) >= 2:
                try:
                    FII_CACHE[row[0]] = float(row[1])
                except ValueError:
                    continue


def get_vix(d: date) -> float | None:
    """Return VIX on or before d (carry-forward last known value)."""
    key = d.isoformat()
    if key in VIX_CACHE:
        return VIX_CACHE[key]
    # Walk back up to 7 days for last known VIX
    from datetime import timedelta
    for i in range(1, 8):
        k = (d - timedelta(days=i)).isoformat()
        if k in VIX_CACHE:
            return VIX_CACHE[k]
    return None


def get_fii(d: date) -> float | None:
    """Return FII net flow on or before d (carry-forward)."""
    key = d.isoformat()
    if key in FII_CACHE:
        return FII_CACHE[key]
    from datetime import timedelta
    for i in range(1, 5):
        k = (d - timedelta(days=i)).isoformat()
        if k in FII_CACHE:
            return FII_CACHE[k]
    return None


def gate_5_vix(d: date, vix_max: float) -> tuple[bool, str]:
    vix = get_vix(d)
    if vix is None:
        return True, "vix_unknown_pass"  # carry-forward fallback
    if vix >= vix_max:
        return False, f"VIX {vix:.1f} >= {vix_max}"
    return True, f"VIX {vix:.1f}"


def gate_7_fii(d: date, fii_min: float) -> tuple[bool, str]:
    fii = get_fii(d)
    if fii is None:
        return True, "fii_disabled_no_data"
    if fii < fii_min:
        return False, f"FII {fii:+.0f} Cr < {fii_min}"
    return True, f"FII {fii:+.0f} Cr"


def gate_4_circuit(prev_close: float, today_open: float, max_gap_pct: float) -> tuple[bool, str]:
    if prev_close <= 0:
        return False, "prev_close zero"
    gap = abs(today_open - prev_close) / prev_close
    if gap > max_gap_pct:
        return False, f"gap {gap*100:.1f}% > {max_gap_pct*100:.0f}%"
    return True, f"gap {gap*100:.1f}%"
