#!/usr/bin/env python3
"""
run_swing.py — Run swing backtest over a specified period (POC or Phase B holdout).

Usage:
  python backtest/run_swing.py poc      # May-Oct 2025 (matches position POC)
  python backtest/run_swing.py holdout  # Nov 2024-Apr 2025 (Phase B holdout)
  python backtest/run_swing.py full     # May 2023-Apr 2025 (full Phase B period)
"""
import copy, json, sys, time
from collections import defaultdict
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
sys.path.insert(0, str(REPO))

from backtest.engine.swing_backtest_runner import run_swing_backtest


PERIODS = {
    "poc":     ("2025-05-01", "2025-10-31"),
    "holdout": ("2024-11-01", "2025-04-30"),
    "full":    ("2023-05-01", "2025-04-30"),
    "w2":      ("2023-11-01", "2024-04-30"),
    "w3":      ("2024-05-01", "2024-10-31"),
}


def load_universe():
    data = json.loads((ROOT / "data" / "universe.json").read_text())
    return data["symbols"], data["sectors"]


def write_report(result: dict, out_md: Path, label: str):
    trades = result["portfolio"]["trades"]
    snaps  = result["portfolio"]["daily_snapshots"]
    starting = result["portfolio"]["starting_cash"]
    final_value = snaps[-1]["total_value"] if snaps else starting
    total_return_pct = (final_value - starting) / starting * 100

    n_total   = len(trades)
    n_winners = sum(1 for t in trades if t["pnl_pct"] > 0)
    win_rate  = (n_winners / n_total * 100) if n_total else 0
    winner_pcts = [t["pnl_pct"] for t in trades if t["pnl_pct"] > 0]
    loser_pcts  = [t["pnl_pct"] for t in trades if t["pnl_pct"] <= 0]
    avg_win = sum(winner_pcts) / len(winner_pcts) if winner_pcts else 0
    avg_los = sum(loser_pcts)  / len(loser_pcts)  if loser_pcts  else 0
    days_held = [t["days_held"] for t in trades if t["exit_reason"] != "open_at_end"]

    # Max drawdown
    peak = starting
    max_dd = 0.0
    for s in snaps:
        peak = max(peak, s["total_value"])
        dd = (s["total_value"] - peak) / peak * 100
        if dd < max_dd:
            max_dd = dd

    from collections import Counter
    exit_counts = Counter(t["exit_reason"] for t in trades)

    by_regime = defaultdict(list)
    for t in trades:
        by_regime[t.get("regime_at_entry", "unknown")].append(t)

    best  = max(trades, key=lambda t: t["pnl_pct"]) if trades else None
    worst = min(trades, key=lambda t: t["pnl_pct"]) if trades else None

    total_pnl = sum(t["pnl_abs"] for t in trades)
    invested  = sum(t["entry_price"] * t["original_qty"] for t in trades)
    return_on_deployed = (total_pnl / invested * 100) if invested > 0 else 0

    L = []
    add = L.append
    add(f"# Swing Backtest — {label}")
    add(f"")
    add(f"_Generated: {datetime.now().isoformat(timespec='seconds')}_")
    add(f"")
    add(f"## Setup")
    add(f"")
    add(f"- Period: {result['config']['start_date']} -> {result['config']['end_date']} ({result['trading_days']} trading days)")
    add(f"- Starting capital: Rs {starting:,}")
    add(f"- Max hold: {result['config']['rules'].get('max_hold_days', '-')} days | ATR-adaptive stops/targets per trade")
    add(f"")
    add(f"## Headline")
    add(f"")
    add(f"> **Started Rs {starting:,}. Ended Rs {final_value:,.0f} ({total_return_pct:+.2f}%). "
        f"Nifty over same period: {result['nifty_return_pct']:+.2f}%. "
        f"Alpha: {total_return_pct - result['nifty_return_pct']:+.2f}%.**")
    add(f"")
    add(f"## Numbers")
    add(f"")
    add(f"| Metric | Value |")
    add(f"|---|---|")
    add(f"| Total trades | {n_total} |")
    add(f"| Win rate | {win_rate:.1f}% |")
    add(f"| Avg winner | {avg_win:+.2f}% |")
    add(f"| Avg loser | {avg_los:+.2f}% |")
    if best:
        add(f"| Best trade | {best['symbol']} {best['pnl_pct']:+.2f}% ({best['days_held']}d) |")
    if worst:
        add(f"| Worst trade | {worst['symbol']} {worst['pnl_pct']:+.2f}% ({worst['days_held']}d) |")
    add(f"| Max drawdown | {max_dd:+.2f}% |")
    add(f"| Total Rs P&L | Rs {total_pnl:,.0f} |")
    add(f"| Total Rs deployed | Rs {invested:,.0f} |")
    add(f"| Return on deployed | {return_on_deployed:+.2f}% |")
    add(f"| Avg days held (closed only) | {sum(days_held)/len(days_held):.1f} days" if days_held else "—")
    add(f"")
    add(f"## Exit reasons")
    add(f"")
    add(f"| Reason | Count |")
    add(f"|---|---|")
    for reason, count in exit_counts.most_common():
        add(f"| {reason} | {count} |")
    add(f"")
    add(f"## Regime breakdown")
    add(f"")
    add(f"| Regime | Trades | Win % | Avg P&L |")
    add(f"|---|---|---|---|")
    for regime, group in sorted(by_regime.items(), key=lambda x: -len(x[1])):
        wins = sum(1 for t in group if t["pnl_pct"] > 0)
        avg = sum(t["pnl_pct"] for t in group) / len(group)
        add(f"| {regime} | {len(group)} | {wins/len(group)*100:.0f}% | {avg:+.2f}% |")
    add(f"")
    add(f"## Skip log")
    add(f"")
    add(f"| Reason | Count |")
    add(f"|---|---|")
    for reason, count in sorted(result["skip_log_summary"].items(), key=lambda x: -x[1]):
        add(f"| {reason} | {count} |")
    add(f"")
    out_md.write_text("\n".join(L), encoding="utf-8")


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in PERIODS:
        print(f"Usage: python backtest/run_swing.py [{' | '.join(PERIODS.keys())}]", file=sys.stderr)
        sys.exit(1)

    label = sys.argv[1]
    start_str, end_str = PERIODS[label]

    cfg = json.loads((ROOT / "config" / "swing_config.json").read_text())
    cfg["start_date"] = start_str
    cfg["end_date"]   = end_str

    universe, sectors = load_universe()
    print(f"Swing backtest — {label}: {start_str} -> {end_str}", file=sys.stderr)
    t0 = time.time()
    result = run_swing_backtest(cfg, universe, sectors)
    print(f"Done in {time.time() - t0:.1f}s", file=sys.stderr)

    OUT = ROOT / "results"
    OUT.mkdir(exist_ok=True)
    (OUT / f"swing_{label}_trades.json").write_text(json.dumps(result["portfolio"]["trades"], indent=2))
    (OUT / f"swing_{label}_snapshots.json").write_text(json.dumps(result["portfolio"]["daily_snapshots"], indent=2))
    (OUT / f"swing_{label}_skip_log.json").write_text(json.dumps(result.get("skip_log_full", []), indent=2))
    write_report(result, OUT / f"swing_{label}_report.md", label)

    trades = result["portfolio"]["trades"]
    n_w = sum(1 for t in trades if t["pnl_pct"] > 0)
    snaps = result["portfolio"]["daily_snapshots"]
    final = snaps[-1]["total_value"] if snaps else cfg["starting_capital"]
    ret = (final - cfg["starting_capital"]) / cfg["starting_capital"] * 100

    print(f"")
    print(f"=== SWING {label.upper()} complete ===")
    print(f"Trades:       {len(trades)}")
    print(f"Win rate:     {(n_w/len(trades)*100 if trades else 0):.1f}%")
    print(f"Total return: {ret:+.2f}%")
    print(f"Nifty:        {result['nifty_return_pct']:+.2f}%")
    print(f"Alpha:        {ret - result['nifty_return_pct']:+.2f}%")
    print(f"")
    print(f"See: backtest/results/swing_{label}_report.md")


if __name__ == "__main__":
    main()
