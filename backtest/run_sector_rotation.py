#!/usr/bin/env python3
"""
run_sector_rotation.py — Run monthly sector rotation backtest.
"""
import json, sys, time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
sys.path.insert(0, str(REPO))

from backtest.engine.sector_rotation import run_sector_rotation_backtest


PERIODS = {
    "poc":     ("2025-05-01", "2025-10-31"),
    "holdout": ("2024-11-01", "2025-04-30"),
    "full":    ("2023-05-01", "2025-04-30"),
}


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in PERIODS:
        print(f"Usage: {' | '.join(PERIODS.keys())}")
        sys.exit(1)

    label = sys.argv[1]
    start_str, end_str = PERIODS[label]

    print(f"Sector rotation {label}: {start_str} -> {end_str}", file=sys.stderr)
    t0 = time.time()
    result = run_sector_rotation_backtest(
        start_str, end_str,
        starting_capital=500_000,
        top_n=3,
        rebalance_freq_days=21,
    )
    print(f"Done in {time.time() - t0:.1f}s", file=sys.stderr)

    OUT = ROOT / "results"
    OUT.mkdir(exist_ok=True)

    trades = result["trades"]
    snaps  = result["snapshots"]
    starting = result["config"]["starting_capital"]
    final = snaps[-1]["total_value"] if snaps else starting
    ret = (final - starting) / starting * 100
    nifty_ret = result["nifty_return_pct"]

    n_w = sum(1 for t in trades if t.get("pnl_pct", 0) > 0)
    win_rate = (n_w / len(trades) * 100) if trades else 0

    (OUT / f"sectrot_{label}_trades.json").write_text(json.dumps(trades, indent=2, default=str))
    (OUT / f"sectrot_{label}_snapshots.json").write_text(json.dumps(snaps, indent=2, default=str))
    (OUT / f"sectrot_{label}_summary.json").write_text(json.dumps({
        "trades": len(trades), "win_rate": win_rate,
        "total_return_pct": ret, "nifty_return_pct": nifty_ret,
        "alpha": ret - nifty_ret, "starting": starting, "final": final,
        "rebalance_freq_days": result["config"]["rebalance_freq_days"],
        "top_n": result["config"]["top_n"],
    }, indent=2))

    print(f"\n=== SECTOR ROTATION {label.upper()} ===")
    print(f"Trades:       {len(trades)}")
    print(f"Win rate:     {win_rate:.1f}%")
    print(f"Total return: {ret:+.2f}%")
    print(f"Nifty:        {nifty_ret:+.2f}%")
    print(f"Alpha:        {ret - nifty_ret:+.2f}%")


if __name__ == "__main__":
    main()
