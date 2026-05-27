#!/usr/bin/env python3
"""
build_universe.py — Extract UNIVERSE + SECTOR_MAP from production signal_generator
and write to backtest/data/universe.json. No code duplication — single source of truth.
"""
import json, sys, os
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from models.signal_generator import UNIVERSE, SECTOR_MAP

OUT = REPO / "backtest" / "data" / "universe.json"
OUT.parent.mkdir(parents=True, exist_ok=True)

data = {
    "symbols": UNIVERSE,
    "sectors": SECTOR_MAP,
    "note": "Snapshot of production UNIVERSE and SECTOR_MAP. POC accepts survivorship bias.",
}
OUT.write_text(json.dumps(data, indent=2))
print(f"Wrote {len(UNIVERSE)} symbols across {len(set(SECTOR_MAP.values()))} sectors to {OUT}")
