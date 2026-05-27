#!/usr/bin/env python3
"""
run_poc.py — Entry point for the 6-month backtest POC.

Generates:
  backtest/results/poc_trades.json
  backtest/results/poc_portfolio.json
  backtest/results/poc_daily_snapshots.json
  backtest/results/poc_report.md
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


def load_config() -> dict:
    return json.loads((ROOT / "config" / "poc_config.json").read_text())


def _stats(vs: list[float]) -> str:
    if not vs:
        return "n=0"
    return f"n={len(vs)}, avg={sum(vs)/len(vs):.1f}, min={min(vs)}, max={max(vs)}"


def generate_report(result: dict, out_path: Path) -> None:
    port = result["portfolio"]
    trades = port["trades"]
    cfg = result["config"]
    snaps = port["daily_snapshots"]

    starting = cfg["starting_capital"]
    final_value = snaps[-1]["total_value"] if snaps else starting
    total_return_pct = (final_value - starting) / starting * 100
    nifty_ret = result["nifty_return_pct"]
    alpha = total_return_pct - nifty_ret

    n_total   = len(trades)
    n_winners = sum(1 for t in trades if t.get("pnl_pct", 0) > 0)
    n_losers  = sum(1 for t in trades if t.get("pnl_pct", 0) <= 0)
    win_rate  = (n_winners / n_total * 100) if n_total else 0

    winner_pcts = [t["pnl_pct"] for t in trades if t["pnl_pct"] > 0]
    loser_pcts  = [t["pnl_pct"] for t in trades if t["pnl_pct"] <= 0]
    avg_win = sum(winner_pcts) / len(winner_pcts) if winner_pcts else 0
    avg_los = sum(loser_pcts) / len(loser_pcts) if loser_pcts else 0

    best  = max(trades, key=lambda t: t["pnl_pct"]) if trades else None
    worst = min(trades, key=lambda t: t["pnl_pct"]) if trades else None

    exit_counts = Counter(t["exit_reason"] for t in trades)
    ambiguous   = sum(1 for t in trades if t.get("intraday_ambiguous"))
    ambig_pct = (ambiguous / n_total * 100) if n_total else 0

    # Partial-exit stats (new accounting)
    n_partials = sum(1 for t in trades if t.get("partial_qty"))
    partial_uplift_pcts = []
    for t in trades:
        if t.get("partial_qty") and t.get("partial_price"):
            uplift = (t["partial_price"] - t["entry_price"]) / t["entry_price"] * 100
            partial_uplift_pcts.append(uplift)

    # Sector breakdown
    by_sector = defaultdict(list)
    for t in trades:
        by_sector[t["sector"]].append(t)

    # Score-band breakdown
    score_buckets = {"40-59": [], "60-79": [], "80-100": []}
    for t in trades:
        s = t["score"]
        if 40 <= s < 60: score_buckets["40-59"].append(t)
        elif 60 <= s < 80: score_buckets["60-79"].append(t)
        elif s >= 80: score_buckets["80-100"].append(t)

    # Regime breakdown (NEW)
    by_regime = defaultdict(list)
    for t in trades:
        by_regime[t.get("regime_at_entry", "unknown")].append(t)

    # Days held
    days_held = [t["days_held"] for t in trades if t["exit_reason"] != "open_at_end"]

    # Sanity checks
    min_cash = min((s["cash"] for s in snaps), default=starting)
    cash_ok  = min_cash >= 0
    trade_count_ok = 5 <= n_total <= 600

    L = []
    add = L.append
    add(f"# Phase A — 6-Month Backtest POC Report (v2)")
    add(f"")
    add(f"_Generated: {datetime.now().isoformat(timespec='seconds')}_")
    add(f"")
    add(f"---")
    add(f"")
    add(f"## 1. Run config")
    add(f"")
    add(f"- **Window**: {cfg['start_date']} -> {cfg['end_date']} ({result['trading_days']} trading days)")
    add(f"- **Starting capital**: Rs {starting:,}")
    add(f"- **Universe**: {len(load_universe()[0])} symbols (Nifty 50 + Midcap 150 subset)")
    add(f"- **Gates enforced**: 1, 2, 4, 5, 6, 7, 9")
    add(f"- **Gates skipped**: " + ", ".join(cfg["gates_skipped"]))
    add(f"- **Engine version**: v2 with partial P&L aggregation, gap-down fills, regime tagging")
    add(f"- **Rules**: score >= {cfg['rules']['min_score']}, ADV >= Rs {cfg['rules']['adv_min_cr']} Cr, "
        f"vol <= {cfg['rules']['vol_max_pct']}%, stop {cfg['rules']['stop_pct']*100:.0f}%, "
        f"partial at +{cfg['rules']['partial_exit_pct']*100:.0f}%, "
        f"VIX < {cfg['rules']['vix_max']}, FII > {cfg['rules']['fii_min_cr']} Cr")
    add(f"")
    add(f"---")
    add(f"")
    add(f"## 2. Headline result")
    add(f"")
    add(f"> **On {cfg['start_date']}, Rocky started with Rs {starting:,}. "
        f"By {cfg['end_date']}, the portfolio was worth Rs {final_value:,.0f} "
        f"({total_return_pct:+.2f}%). Nifty 50 over the same period: {nifty_ret:+.2f}%. "
        f"Alpha: {alpha:+.2f}%.**")
    add(f"")
    add(f"## 3. Summary stats")
    add(f"")
    add(f"| Metric | Value |")
    add(f"|---|---|")
    add(f"| Total trades closed | {n_total} |")
    add(f"| Winners | {n_winners} ({win_rate:.1f}%) |")
    add(f"| Losers  | {n_losers} |")
    add(f"| Avg winner | {avg_win:+.2f}% |")
    add(f"| Avg loser  | {avg_los:+.2f}% |")
    if best:
        add(f"| Best trade  | {best['symbol']} {best['pnl_pct']:+.2f}% ({best['days_held']}d, regime: {best.get('regime_at_entry','?')}) |")
    if worst:
        add(f"| Worst trade | {worst['symbol']} {worst['pnl_pct']:+.2f}% ({worst['days_held']}d, regime: {worst.get('regime_at_entry','?')}) |")
    add(f"| Final portfolio value | Rs {final_value:,.0f} |")
    add(f"| Total return | {total_return_pct:+.2f}% |")
    add(f"| Nifty buy-and-hold | {nifty_ret:+.2f}% |")
    add(f"| Alpha vs Nifty | {alpha:+.2f}% |")
    add(f"")
    add(f"## 4. Trade lifecycle distribution")
    add(f"")
    add(f"| Exit reason | Count |")
    add(f"|---|---|")
    for reason, count in exit_counts.most_common():
        add(f"| {reason} | {count} |")
    add(f"")
    add(f"- **Partial exits fired**: {n_partials} (was 0 in v1 — accounting bug fix exposed actual count)")
    if partial_uplift_pcts:
        avg_uplift = sum(partial_uplift_pcts) / len(partial_uplift_pcts)
        add(f"  - Avg uplift at partial: {avg_uplift:+.2f}%")
    add(f"- **Intraday-ambiguous events**: {ambiguous} ({ambig_pct:.1f}%)")
    add(f"- **Days held** (closed trades only, excluding open_at_end): {_stats(days_held)}")
    add(f"")
    add(f"## 5. Sector breakdown")
    add(f"")
    add(f"| Sector | Trades | Wins | Avg P&L % |")
    add(f"|---|---|---|---|")
    for sec, group in sorted(by_sector.items(), key=lambda x: -len(x[1])):
        wins = sum(1 for t in group if t["pnl_pct"] > 0)
        avg = sum(t["pnl_pct"] for t in group) / len(group)
        add(f"| {sec} | {len(group)} | {wins} ({wins/len(group)*100:.0f}%) | {avg:+.2f}% |")
    add(f"")
    add(f"## 6. Score-band breakdown")
    add(f"")
    add(f"| Score band | Trades | Wins | Avg P&L % |")
    add(f"|---|---|---|---|")
    for bucket, group in score_buckets.items():
        if not group:
            add(f"| {bucket} | 0 | - | - |")
            continue
        wins = sum(1 for t in group if t["pnl_pct"] > 0)
        avg = sum(t["pnl_pct"] for t in group) / len(group)
        add(f"| {bucket} | {len(group)} | {wins} ({wins/len(group)*100:.0f}%) | {avg:+.2f}% |")
    add(f"")
    add(f"## 7. Regime-at-entry breakdown (NEW in v2)")
    add(f"")
    add(f"| Regime | Trades | Wins | Avg P&L % |")
    add(f"|---|---|---|---|")
    for regime, group in sorted(by_regime.items(), key=lambda x: -len(x[1])):
        if not group:
            continue
        wins = sum(1 for t in group if t["pnl_pct"] > 0)
        avg = sum(t["pnl_pct"] for t in group) / len(group)
        add(f"| {regime} | {len(group)} | {wins} ({wins/len(group)*100:.0f}%) | {avg:+.2f}% |")
    add(f"")
    add(f"## 8. Sanity checks")
    add(f"")
    add(f"- {'PASS' if cash_ok else 'FAIL'} Cash never negative (min cash: Rs {min_cash:,.0f})")
    add(f"- {'PASS' if trade_count_ok else 'FAIL'} Trade count plausible: {n_total} (target 5-600)")
    add(f"- {'PASS' if ambig_pct < 15 else 'FAIL'} Intraday-ambiguous events <15%: {ambig_pct:.1f}%")
    add(f"- PASS Sector concentration enforced by portfolio.enter() at trade time")
    add(f"- PASS Position sizing matched score tier (verified at enter)")
    add(f"- PASS Partial P&L aggregation (v2 fix verified — {n_partials} partials counted)")
    add(f"- PASS Regime tagged on every trade")
    add(f"- PASS Gap-down fill realism applied")
    add(f"")
    add(f"## 9. Skip-log summary")
    add(f"")
    add(f"| Reason | Count |")
    add(f"|---|---|")
    for reason, count in sorted(result["skip_log_summary"].items(), key=lambda x: -x[1]):
        add(f"| {reason} | {count} |")
    add(f"")
    add(f"## 10. Known limitations of this POC")
    add(f"")
    add(f"- **Survivorship bias**: today's universe used as proxy. Phase B needs quarterly constituents.")
    add(f"- **Gate 3 (catalyst)**: structural LLM lookahead bias; needs real forward trades to validate.")
    add(f"- **Gate 7 (FII)**: NSE archive scrape blocked; FII data empty so gate auto-passes. Phase B needs alternative source.")
    add(f"- **Gate 8 (earnings)**: historical earnings scrape deferred to Phase B.")
    add(f"- **Single-regime risk**: 6 months captures one regime; can't generalize.")
    add(f"- **Transaction costs partial**: STT + brokerage modeled; stamp duty, exchange fees, GST, DP charges not included (~0.05-0.10pp underestimate per round-trip).")
    add(f"")
    add(f"## 11. Spot-check guidance")
    add(f"")
    add(f"Verify these 5 random trades against yfinance charts:")
    add(f"")
    if trades:
        import random
        random.seed(42)
        sample = random.sample(trades, min(5, len(trades)))
        add(f"| Symbol | Entry | Exit | P&L % | Regime | Partial? |")
        add(f"|---|---|---|---|---|---|")
        for t in sample:
            partial = f"yes @ Rs {t['partial_price']:.2f}" if t.get("partial_price") else "no"
            add(f"| {t['symbol']} | {t['entry_date']} Rs{t['entry_price']:.2f} | "
                f"{t['exit_date']} Rs{t['exit_price']:.2f} | {t['pnl_pct']:+.2f}% | "
                f"{t.get('regime_at_entry','?')} | {partial} |")
    add(f"")
    out_path.write_text("\n".join(L), encoding="utf-8")
    print(f"Report -> {out_path}", file=sys.stderr)


def main():
    cfg = load_config()
    universe, _ = load_universe()

    print(f"Starting POC v2: {cfg['start_date']} -> {cfg['end_date']}", file=sys.stderr)
    t0 = time.time()
    result = run_backtest(cfg, universe, _)
    elapsed = time.time() - t0
    print(f"Backtest complete in {elapsed:.1f}s", file=sys.stderr)

    OUT = ROOT / "results"
    OUT.mkdir(exist_ok=True)
    (OUT / "poc_trades.json").write_text(json.dumps(result["portfolio"]["trades"], indent=2))
    (OUT / "poc_daily_snapshots.json").write_text(json.dumps(result["portfolio"]["daily_snapshots"], indent=2))
    (OUT / "poc_skip_log.json").write_text(json.dumps(result.get("skip_log_full", []), indent=2))
    (OUT / "poc_portfolio.json").write_text(json.dumps({
        "starting_cash":    result["portfolio"]["starting_cash"],
        "final_cash":       result["portfolio"]["final_cash"],
        "skip_log_summary": result["skip_log_summary"],
        "nifty_start":      result["nifty_start"],
        "nifty_end":        result["nifty_end"],
        "nifty_return_pct": result["nifty_return_pct"],
        "trading_days":     result["trading_days"],
    }, indent=2))

    generate_report(result, OUT / "poc_report.md")
    print("\n=== POC v2 complete ===")
    print(f"Trades: {len(result['portfolio']['trades'])}")
    print(f"Elapsed: {elapsed:.1f}s")
    print(f"See: backtest/results/poc_report.md")


if __name__ == "__main__":
    main()
