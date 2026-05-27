#!/usr/bin/env python3
"""
run_poc_unlimited.py — Run POC with ₹10 crore starting capital.

Compares against the ₹5L baseline POC to isolate:
  - Total trade count (was 15 with limited cash; how many with unlimited?)
  - Gross return on deployed capital (was 12.31% on ₹5L base)
  - Per-rupee return — does the strategy retain edge at scale?
  - Sector cap binding rate (with cash unconstrained, is Gate 9 the new bottleneck?)
"""
import json, sys, time
from collections import Counter, defaultdict
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
    cfg = json.loads((ROOT / "config" / "poc_unlimited_config.json").read_text())
    universe, sectors = load_universe()

    print(f"Starting UNLIMITED-CAPITAL POC: {cfg['start_date']} -> {cfg['end_date']}", file=sys.stderr)
    print(f"Starting capital: Rs {cfg['starting_capital']:,}", file=sys.stderr)
    t0 = time.time()
    result = run_backtest(cfg, universe, sectors)
    elapsed = time.time() - t0
    print(f"Backtest complete in {elapsed:.1f}s", file=sys.stderr)

    OUT = ROOT / "results"
    OUT.mkdir(exist_ok=True)
    (OUT / "poc_unlimited_trades.json").write_text(json.dumps(result["portfolio"]["trades"], indent=2))
    (OUT / "poc_unlimited_snapshots.json").write_text(json.dumps(result["portfolio"]["daily_snapshots"], indent=2))
    (OUT / "poc_unlimited_portfolio.json").write_text(json.dumps({
        "starting_cash":    result["portfolio"]["starting_cash"],
        "final_cash":       result["portfolio"]["final_cash"],
        "skip_log_summary": result["skip_log_summary"],
        "nifty_return_pct": result["nifty_return_pct"],
        "trading_days":     result["trading_days"],
    }, indent=2))

    # ── Generate comparison-focused report ────────────────────────────────────
    trades = result["portfolio"]["trades"]
    snaps  = result["portfolio"]["daily_snapshots"]
    starting = cfg["starting_capital"]
    final_value = snaps[-1]["total_value"] if snaps else starting
    total_return_pct = (final_value - starting) / starting * 100

    # Compute deployed-capital return (different from total return)
    total_invested = sum(t["entry_price"] * t["original_qty"] for t in trades)
    total_pnl      = sum(t["pnl_abs"] for t in trades)
    return_on_deployed = (total_pnl / total_invested * 100) if total_invested > 0 else 0

    # Compute max concurrent positions
    max_concurrent = max((s["n_positions"] for s in snaps), default=0)
    avg_concurrent = sum(s["n_positions"] for s in snaps) / len(snaps) if snaps else 0

    # Sector heat (max simultaneous positions per sector)
    # We can approximate this by walking trades — start active when entered, end when exited
    sector_max_open = defaultdict(int)
    sector_current  = defaultdict(int)
    events = []
    for t in trades:
        events.append((t["entry_date"], +1, t["sector"]))
        events.append((t["exit_date"],  -1, t["sector"]))
    events.sort()
    for _, delta, sec in events:
        sector_current[sec] += delta
        if sector_current[sec] > sector_max_open[sec]:
            sector_max_open[sec] = sector_current[sec]

    n_winners = sum(1 for t in trades if t["pnl_pct"] > 0)
    win_rate  = (n_winners / len(trades) * 100) if trades else 0
    n_partials = sum(1 for t in trades if t.get("partial_qty"))
    avg_win = sum(t["pnl_pct"] for t in trades if t["pnl_pct"] > 0) / max(1, n_winners)
    n_losers = len(trades) - n_winners
    avg_los = sum(t["pnl_pct"] for t in trades if t["pnl_pct"] <= 0) / max(1, n_losers)

    by_regime = defaultdict(list)
    for t in trades:
        by_regime[t.get("regime_at_entry", "unknown")].append(t)

    by_score_band = {"40-59": [], "60-79": [], "80-100": []}
    for t in trades:
        s = t["score"]
        if 40 <= s < 60: by_score_band["40-59"].append(t)
        elif 60 <= s < 80: by_score_band["60-79"].append(t)
        elif s >= 80: by_score_band["80-100"].append(t)

    skip = result["skip_log_summary"]

    L = []
    add = L.append
    add(f"# POC — Unlimited Capital Experiment")
    add(f"")
    add(f"_Generated: {datetime.now().isoformat(timespec='seconds')}_")
    add(f"")
    add(f"## Setup")
    add(f"")
    add(f"- Starting capital: **Rs {starting:,}** (vs Rs 5,00,000 in baseline POC)")
    add(f"- Same rules, same window ({cfg['start_date']} -> {cfg['end_date']})")
    add(f"- Gate 9 (sector cap = 2) STILL ENFORCED -> max ~28 concurrent positions")
    add(f"- Real-world caveat: market impact NOT modeled. Real returns at this scale would be 0.5-2% worse.")
    add(f"")
    add(f"## Headline numbers")
    add(f"")
    add(f"| Metric | Unlimited (this) | Baseline ₹5L POC | Multiplier |")
    add(f"|---|---|---|---|")
    add(f"| Total trades closed | **{len(trades)}** | 15 | {len(trades)/15:.1f}x |")
    add(f"| Win rate | {win_rate:.1f}% | 73.3% | — |")
    add(f"| Total ₹ P&L | **Rs {total_pnl:,.0f}** | Rs 61,570 | {total_pnl/61570:.1f}x |")
    add(f"| Total ₹ deployed | Rs {total_invested:,.0f} | — | — |")
    add(f"| Return on deployed capital | **{return_on_deployed:+.2f}%** | ~12% | — |")
    add(f"| Total return on starting | {total_return_pct:+.2f}% | +12.31% | — |")
    add(f"| Max concurrent positions | {max_concurrent} | 11 | — |")
    add(f"| Avg concurrent positions | {avg_concurrent:.1f} | — | — |")
    add(f"| Partial exits fired | {n_partials} | 5 | — |")
    add(f"")
    add(f"## What this tells us")
    add(f"")
    add(f"### 1. Cash constraint cost vs Gate 9 binding rate")
    add(f"")
    add(f"| Skip reason | Unlimited run | Baseline ₹5L run |")
    add(f"|---|---|---|")
    add(f"| gate6_insufficient_cash | {skip.get('gate6_insufficient_cash_or_qty', 0)} | 836 |")
    add(f"| gate9_sector_full | {skip.get('gate9_sector_full', 0)} | 171 |")
    add(f"| gate4_circuit_gap | {skip.get('gate4_circuit_gap', 0)} | — |")
    add(f"| macro_skip_vix_or_fii | {skip.get('macro_skip_vix_or_fii', 0)} | — |")
    add(f"")
    add(f"If sector-full count exploded, Gate 9 is now the binding constraint — cash was just the most visible cap.")
    add(f"")
    add(f"### 2. Win-rate / per-rupee return — did edge survive scaling?")
    add(f"")
    add(f"- Baseline ₹5L POC: 73.3% win rate, ~12% return on deployed capital")
    add(f"- Unlimited: {win_rate:.1f}% win rate, {return_on_deployed:+.2f}% return on deployed")
    add(f"")
    add(f"If per-rupee return is similar (~12%), the strategy edge is consistent — cash was just an artificial cap.")
    add(f"If per-rupee return dropped significantly, the additional trades are LOWER quality (marginal signals)")
    add(f"and the cash constraint was acting as a useful quality filter.")
    add(f"")
    add(f"### 3. Sector concentration that actually happened")
    add(f"")
    add(f"Max simultaneous open positions per sector (Gate 9 capped at 2):")
    add(f"")
    add(f"| Sector | Max simultaneous | At cap? |")
    add(f"|---|---|---|")
    for sec, n in sorted(sector_max_open.items(), key=lambda x: -x[1]):
        capped = "**YES**" if n >= 2 else ""
        add(f"| {sec} | {n} | {capped} |")
    add(f"")
    add(f"### 4. Regime-at-entry — does the pattern hold with more trades?")
    add(f"")
    add(f"| Regime | Trades | Wins | Win % | Avg P&L |")
    add(f"|---|---|---|---|---|")
    for regime, group in sorted(by_regime.items(), key=lambda x: -len(x[1])):
        wins = sum(1 for t in group if t["pnl_pct"] > 0)
        avg = sum(t["pnl_pct"] for t in group) / len(group)
        add(f"| {regime} | {len(group)} | {wins} | {wins/len(group)*100:.0f}% | {avg:+.2f}% |")
    add(f"")
    add(f"In the ₹5L POC, sideways regime trades were 0/3. With more samples, does that hold?")
    add(f"")
    add(f"### 5. Score-band — does score 60-79 still beat 80-100?")
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
    add(f"## Important caveat")
    add(f"")
    add(f"This experiment is a **diagnostic**, not a strategy recommendation. The ₹{total_pnl:,.0f} P&L is mathematical not realistic:")
    add(f"")
    add(f"- **Market impact ignored**: ₹{starting:,} deployed across {len(set(t['symbol'] for t in trades))} unique stocks "
        f"would move prices on entry and exit. Real fills would be 0.5-2% worse, eroding 5-20% of the displayed P&L.")
    add(f"- **Liquidity ignored**: Some midcap stocks in this universe trade only ₹50 Cr/day — the ADV filter. A "
        f"₹3-5cr position in those stocks IS the daily volume.")
    add(f"- **Cost model is partial**: stamp duty, exchange fees, GST not included. These hurt more at scale due to ₹ amounts.")
    add(f"")
    add(f"**Honest interpretation:** Use return ON DEPLOYED CAPITAL ({return_on_deployed:+.2f}%) — not total return ({total_return_pct:+.2f}%) — when comparing to the ₹5L baseline. The fair scaling question is 'per rupee invested,' not 'per rupee started.'")
    add(f"")

    (OUT / "poc_unlimited_report.md").write_text("\n".join(L), encoding="utf-8")

    print(f"\n=== UNLIMITED POC complete ===")
    print(f"Trades:                {len(trades)}")
    print(f"Total ₹ P&L:           Rs {total_pnl:,.0f}")
    print(f"Total ₹ deployed:      Rs {total_invested:,.0f}")
    print(f"Return on deployed:    {return_on_deployed:+.2f}%")
    print(f"Return on starting:    {total_return_pct:+.2f}%")
    print(f"Max concurrent:        {max_concurrent}")
    print(f"Elapsed:               {elapsed:.1f}s")
    print(f"\nSee: backtest/results/poc_unlimited_report.md")


if __name__ == "__main__":
    main()
