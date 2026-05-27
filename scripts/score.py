#!/usr/bin/env python3
"""
score.py — Single fitness score for Rocky's strategy.

Composite of:
  - realized return vs target (goal.target_return_30d)
  - max drawdown vs cap (goal.max_drawdown)
  - Sharpe vs minimum (goal.min_sharpe)

Returns a float in [-1.0, +1.0]:
  +1.0 = crushing all three targets
   0.0 = roughly meeting targets
  -1.0 = blowing through the failure floor / max drawdown

Reads closed trades from memory/trade-outcomes.json and goal from memory/goal.yaml.

Usage:
  python scripts/score.py                 # score all closed trades
  python scripts/score.py --last 25       # score only the last 25 closed trades
  python scripts/score.py --json          # machine-readable output
"""
import json, sys, math
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUTCOMES_FILE = REPO / "memory" / "trade-outcomes.json"
GOAL_FILE     = REPO / "memory" / "goal.yaml"


def _load_goal() -> dict:
    """Minimal YAML reader (avoids pyyaml dependency for this simple file)."""
    defaults = {
        "target_return_30d": 0.05,
        "max_drawdown":      0.10,
        "min_sharpe":        1.0,
        "failure_below":    -0.04,
    }
    if not GOAL_FILE.exists():
        return defaults
    goal = dict(defaults)
    for line in GOAL_FILE.read_text(encoding="utf-8").splitlines():
        line = line.split("#")[0].strip()
        if ":" not in line:
            continue
        key, _, val = line.partition(":")
        key = key.strip()
        val = val.strip().strip('"')
        if key in defaults:
            try:
                goal[key] = float(val)
            except ValueError:
                pass
    return goal


def _closed_trades(last: int | None = None) -> list[dict]:
    if not OUTCOMES_FILE.exists():
        return []
    data = json.loads(OUTCOMES_FILE.read_text(encoding="utf-8"))
    closed = [t for t in data.get("trades", []) if t.get("exit_date") is not None]
    closed.sort(key=lambda t: t.get("exit_date", ""))
    if last:
        return closed[-last:]
    return closed


def _realized_return_pct(trades: list[dict]) -> float:
    """Sum of pnl_pct weighted equally (each trade = one unit of capital deployed)."""
    if not trades:
        return 0.0
    # Approximate portfolio return as the mean trade return × (trades / typical concurrent)
    # Simpler + honest: average pnl_pct across trades, treated as per-trade return.
    return sum(t.get("pnl_pct", 0) for t in trades) / len(trades)


def _max_drawdown_pct(trades: list[dict]) -> float:
    """Reconstruct equity curve from cumulative trade P&L %, return max peak-to-trough %."""
    if not trades:
        return 0.0
    equity = 100.0
    peak = 100.0
    max_dd = 0.0
    for t in trades:
        equity *= (1 + t.get("pnl_pct", 0) / 100.0)
        peak = max(peak, equity)
        dd = (equity - peak) / peak * 100
        if dd < max_dd:
            max_dd = dd
    return abs(max_dd)


def _sharpe(trades: list[dict]) -> float:
    """Trade-level Sharpe: mean / std of pnl_pct. Annualized by ~50 trades/yr assumption."""
    rets = [t.get("pnl_pct", 0) for t in trades]
    if len(rets) < 2:
        return 0.0
    mean = sum(rets) / len(rets)
    var = sum((r - mean) ** 2 for r in rets) / (len(rets) - 1)
    std = math.sqrt(var)
    if std == 0:
        return 0.0
    # Annualize: ~50 swing trades/year
    return (mean / std) * math.sqrt(50)


def _clamp(x: float, lo: float = -1.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


def score(trades: list[dict], goal: dict) -> dict:
    n = len(trades)
    if n == 0:
        return {"fitness": 0.0, "n_trades": 0, "note": "no closed trades yet",
                "realized_return_pct": 0.0, "max_drawdown_pct": 0.0, "sharpe": 0.0}

    realized = _realized_return_pct(trades)          # avg per-trade %
    max_dd   = _max_drawdown_pct(trades)             # %
    sharpe   = _sharpe(trades)

    target_pct  = goal["target_return_30d"] * 100    # e.g. 5.0
    maxdd_pct   = goal["max_drawdown"] * 100          # e.g. 10.0
    floor_pct   = goal["failure_below"] * 100         # e.g. -4.0
    min_sharpe  = goal["min_sharpe"]

    # ── Return component: scaled so meeting per-trade target ~ +0.5 ──────────
    # Use a per-trade target (target_30d spread over ~6 trades/30d for swing)
    per_trade_target = target_pct / 6.0  # ~0.83% per trade to hit 5%/30d
    if realized >= 0:
        ret_comp = _clamp(realized / (per_trade_target * 2))  # 2× target → +1
    else:
        # steeply negative below failure floor
        ret_comp = _clamp(realized / abs(floor_pct))          # at floor → -1

    # ── Drawdown component: 0 dd → +1, at cap → -1 ───────────────────────────
    dd_comp = _clamp(1.0 - 2.0 * (max_dd / maxdd_pct))

    # ── Sharpe component: at min → 0, 2×min → +1, 0 → -1 ─────────────────────
    if sharpe >= 0:
        sharpe_comp = _clamp((sharpe - min_sharpe) / min_sharpe + 0.0)
        sharpe_comp = _clamp(sharpe / (min_sharpe * 2))
    else:
        sharpe_comp = _clamp(sharpe / min_sharpe)

    # Weighted composite: return 50%, drawdown 30%, sharpe 20%
    fitness = _clamp(0.50 * ret_comp + 0.30 * dd_comp + 0.20 * sharpe_comp)

    return {
        "fitness":              round(fitness, 4),
        "n_trades":             n,
        "realized_return_pct":  round(realized, 3),
        "max_drawdown_pct":     round(max_dd, 3),
        "sharpe":               round(sharpe, 3),
        "components": {
            "return":   round(ret_comp, 3),
            "drawdown": round(dd_comp, 3),
            "sharpe":   round(sharpe_comp, 3),
        },
        "vs_goal": {
            "target_return_30d_pct": target_pct,
            "max_drawdown_pct":      maxdd_pct,
            "min_sharpe":            min_sharpe,
        },
    }


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--last", type=int, default=None)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    goal = _load_goal()
    trades = _closed_trades(args.last)
    result = score(trades, goal)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"Fitness: {result['fitness']:+.3f}  (n={result['n_trades']} closed trades)")
        print(f"  Realized avg/trade: {result['realized_return_pct']:+.2f}%")
        print(f"  Max drawdown:       {result['max_drawdown_pct']:.2f}%")
        print(f"  Sharpe:             {result['sharpe']:.2f}")
        if result["n_trades"] > 0:
            c = result["components"]
            print(f"  Components: return={c['return']:+.2f} drawdown={c['drawdown']:+.2f} sharpe={c['sharpe']:+.2f}")


if __name__ == "__main__":
    main()
