#!/usr/bin/env python3
"""
run_poc_smaller_tiers.py — Run POC with reduced position-tier sizes.

Same Rs 5L capital. Tiers: 55k / 35k / 20k (was 70k / 50k / 30k).
Tests whether more concurrent positions captures more strategy alpha.

Uses 'Rs' in stdout (no Unicode bug). Markdown/JSON outputs use UTF-8.
"""
import json, sys, time
from collections import defaultdict
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
sys.path.insert(0, str(REPO))

from backtest.engine.backtest_runner import run_backtest


def load_universe() -> tuple[list[str], dict[str, str]]:
    data = json.loads((ROOT / "data" / "universe.json").read_text())
    return data["symbols"], data["sectors"]


def main():
    cfg = json.loads((ROOT / "config" / "poc_smaller_tiers_config.json").read_text())
    universe, sectors = load_universe()

    print(f"Starting SMALLER-TIERS POC: {cfg['start_date']} -> {cfg['end_date']}", file=sys.stderr)
    print(f"Capital: Rs {cfg['starting_capital']:,} | "
          f"Tiers: {cfg['rules']['size_tier_high']}/{cfg['rules']['size_tier_mid']}/{cfg['rules']['size_tier_low']}",
          file=sys.stderr)

    t0 = time.time()
    result = run_backtest(cfg, universe, sectors)
    elapsed = time.time() - t0

    OUT = ROOT / "results"
    OUT.mkdir(exist_ok=True)
    (OUT / "poc_smaller_trades.json").write_text(json.dumps(result["portfolio"]["trades"], indent=2))
    (OUT / "poc_smaller_snapshots.json").write_text(json.dumps(result["portfolio"]["daily_snapshots"], indent=2))
    (OUT / "poc_smaller_skip_log.json").write_text(json.dumps(result.get("skip_log_full", []), indent=2))
    (OUT / "poc_smaller_portfolio.json").write_text(json.dumps({
        "starting_cash":    result["portfolio"]["starting_cash"],
        "final_cash":       result["portfolio"]["final_cash"],
        "skip_log_summary": result["skip_log_summary"],
        "nifty_return_pct": result["nifty_return_pct"],
        "trading_days":     result["trading_days"],
    }, indent=2))

    # ── Comparison-focused report ────────────────────────────────────────────
    trades = result["portfolio"]["trades"]
    snaps  = result["portfolio"]["daily_snapshots"]
    starting = cfg["starting_capital"]
    final_value = snaps[-1]["total_value"] if snaps else starting
    total_return_pct = (final_value - starting) / starting * 100

    total_invested = sum(t["entry_price"] * t["original_qty"] for t in trades)
    total_pnl      = sum(t["pnl_abs"] for t in trades)
    return_on_deployed = (total_pnl / total_invested * 100) if total_invested > 0 else 0

    max_concurrent = max((s["n_positions"] for s in snaps), default=0)
    avg_concurrent = sum(s["n_positions"] for s in snaps) / len(snaps) if snaps else 0

    n_winners = sum(1 for t in trades if t["pnl_pct"] > 0)
    n_losers  = len(trades) - n_winners
    win_rate  = (n_winners / len(trades) * 100) if trades else 0
    avg_win = sum(t["pnl_pct"] for t in trades if t["pnl_pct"] > 0) / max(1, n_winners)
    avg_los = sum(t["pnl_pct"] for t in trades if t["pnl_pct"] <= 0) / max(1, n_losers)
    n_partials = sum(1 for t in trades if t.get("partial_qty"))

    by_regime = defaultdict(list)
    for t in trades:
        by_regime[t.get("regime_at_entry", "unknown")].append(t)

    by_score_band = {"40-59": [], "60-79": [], "80-100": []}
    for t in trades:
        s = t["score"]
        if 40 <= s < 60: by_score_band["40-59"].append(t)
        elif 60 <= s < 80: by_score_band["60-79"].append(t)
        elif s >= 80: by_score_band["80-100"].append(t)

    # Sector simultaneous-open analysis
    sector_max_open = defaultdict(int)
    sector_current = defaultdict(int)
    events = []
    for t in trades:
        events.append((t["entry_date"], +1, t["sector"]))
        events.append((t["exit_date"],  -1, t["sector"]))
    events.sort()
    for _, delta, sec in events:
        sector_current[sec] += delta
        if sector_current[sec] > sector_max_open[sec]:
            sector_max_open[sec] = sector_current[sec]

    skip = result["skip_log_summary"]

    L = []
    add = L.append
    add(f"# POC — Smaller Position Tiers Experiment")
    add(f"")
    add(f"_Generated: {datetime.now().isoformat(timespec='seconds')}_")
    add(f"")
    add(f"## Setup")
    add(f"")
    add(f"- Starting capital: **Rs {starting:,}** (same as baseline POC)")
    add(f"- Tier sizes: **Rs {cfg['rules']['size_tier_high']:,} / Rs {cfg['rules']['size_tier_mid']:,} / Rs {cfg['rules']['size_tier_low']:,}** (baseline used 70k/50k/30k)")
    add(f"- Window: {cfg['start_date']} -> {cfg['end_date']}")
    add(f"")
    add(f"## Hypothesis")
    add(f"")
    add(f"In baseline POC, 836 candidates were rejected for 'insufficient cash' — meaning Rocky's rules said BUY but capacity was full. ")
    add(f"Smaller positions should free up capital sooner, allowing more concurrent trades. ")
    add(f"")
    add(f"- If win rate stays similar -> cash constraint was artificial scarcity, smaller tiers are better")
    add(f"- If win rate drops significantly -> original tier sizes were doing useful quality filtering")
    add(f"")
    add(f"## Headline comparison (smaller tiers vs baseline)")
    add(f"")
    add(f"| Metric | Smaller tiers (this) | Baseline POC | Δ |")
    add(f"|---|---|---|---|")
    add(f"| Total trades | **{len(trades)}** | 15 | {len(trades)-15:+d} |")
    add(f"| Win rate | {win_rate:.1f}% | 73.3% | {win_rate-73.3:+.1f}pp |")
    add(f"| Avg winner | {avg_win:+.2f}% | +11.02% | {avg_win-11.02:+.2f}pp |")
    add(f"| Avg loser | {avg_los:+.2f}% | -4.34% | — |")
    add(f"| Total Rs P&L | **Rs {total_pnl:,.0f}** | Rs 61,570 | {total_pnl-61570:+,.0f} |")
    add(f"| Total Rs deployed | Rs {total_invested:,.0f} | (capacity-capped ~5L) | — |")
    add(f"| Return on deployed | {return_on_deployed:+.2f}% | ~12% | — |")
    add(f"| Return on starting | **{total_return_pct:+.2f}%** | +12.31% | {total_return_pct-12.31:+.2f}pp |")
    add(f"| Max concurrent positions | {max_concurrent} | 11 | {max_concurrent-11:+d} |")
    add(f"| Avg concurrent positions | {avg_concurrent:.1f} | — | — |")
    add(f"| Partial exits fired | {n_partials} | 5 | {n_partials-5:+d} |")
    add(f"")
    add(f"## Skip-log breakdown")
    add(f"")
    add(f"| Reason | This run | Baseline |")
    add(f"|---|---|---|")
    add(f"| gate6_insufficient_cash | {skip.get('gate6_insufficient_cash_or_qty', 0)} | 836 |")
    add(f"| gate9_sector_full | {skip.get('gate9_sector_full', 0)} | 171 |")
    add(f"| gate4_circuit_gap | {skip.get('gate4_circuit_gap', 0)} | 0 |")
    add(f"| macro_skip | {skip.get('macro_skip_vix_or_fii', 0)} | 0 |")
    add(f"")
    add(f"## Sector concentration that actually happened")
    add(f"")
    add(f"Max simultaneous open positions per sector (Gate 9 cap = 2):")
    add(f"")
    add(f"| Sector | Max simultaneous | At cap? |")
    add(f"|---|---|---|")
    for sec, n in sorted(sector_max_open.items(), key=lambda x: -x[1]):
        capped = "**YES**" if n >= 2 else ""
        add(f"| {sec} | {n} | {capped} |")
    add(f"")
    add(f"## Regime-at-entry breakdown")
    add(f"")
    add(f"| Regime | Trades | Wins | Win % | Avg P&L |")
    add(f"|---|---|---|---|---|")
    for regime, group in sorted(by_regime.items(), key=lambda x: -len(x[1])):
        wins = sum(1 for t in group if t["pnl_pct"] > 0)
        avg = sum(t["pnl_pct"] for t in group) / len(group)
        add(f"| {regime} | {len(group)} | {wins} | {wins/len(group)*100:.0f}% | {avg:+.2f}% |")
    add(f"")
    add(f"## Score-band breakdown")
    add(f"")
    add(f"| Score band | Trades | Wins | Win % | Avg P&L |")
    add(f"|---|---|---|---|---|")
    for bucket, group in by_score_band.items():
        if not group:
            add(f"| {bucket} | 0 | - | - | - |")
            continue
        wins = sum(1 for t in group if t["pnl_pct"] > 0)
        avg = sum(t["pnl_pct"] for t in group) / len(group)
        add(f"| {bucket} | {len(group)} | {wins} | {wins/len(group)*100:.0f}% | {avg:+.2f}% |")
    add(f"")
    add(f"## Caveats")
    add(f"")
    add(f"- **Fixed brokerage hurts smaller positions more**: Rs 20/order is 0.10% of a Rs 20k position vs 0.029% of a Rs 70k position. Real costs erode small-position returns more.")
    add(f"- **Same single regime (May-Oct 2025)**: can't generalize to other market conditions yet.")
    add(f"- **Same gates skipped**: 3 (catalyst), 8 (earnings).")
    add(f"")

    (OUT / "poc_smaller_report.md").write_text("\n".join(L), encoding="utf-8")

    print(f"")
    print(f"=== SMALLER-TIERS POC complete ===")
    print(f"Trades:                {len(trades)}")
    print(f"Win rate:              {win_rate:.1f}%")
    print(f"Total Rs P&L:          Rs {total_pnl:,.0f}")
    print(f"Total Rs deployed:     Rs {total_invested:,.0f}")
    print(f"Return on deployed:    {return_on_deployed:+.2f}%")
    print(f"Return on starting:    {total_return_pct:+.2f}%")
    print(f"Max concurrent:        {max_concurrent}")
    print(f"Elapsed:               {elapsed:.1f}s")
    print(f"")
    print(f"See: backtest/results/poc_smaller_report.md")


if __name__ == "__main__":
    main()
