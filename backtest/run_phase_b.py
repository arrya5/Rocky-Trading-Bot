#!/usr/bin/env python3
"""
run_phase_b.py — Phase B entry point.

Loads phase_b_config.json, runs the walk-forward orchestrator, generates
the final decision report.
"""
import json, sys, time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
sys.path.insert(0, str(REPO))

from backtest.engine.walk_forward import run_walk_forward


def load_universe() -> tuple[list[str], dict[str, str]]:
    data = json.loads((ROOT / "data" / "universe.json").read_text())
    return data["symbols"], data["sectors"]


def write_report(wf_result: dict, out_path: Path) -> None:
    cfg = wf_result["phase_b_cfg"]
    decisions = wf_result["training_decisions"]
    holdout = wf_result["holdout"]

    L = []
    add = L.append
    add(f"# Phase B — Walk-Forward Optimization — Final Report")
    add(f"")
    add(f"_Generated: {datetime.now().isoformat(timespec='seconds')}_")
    add(f"")
    add(f"---")
    add(f"")
    add(f"## 🎯 FINAL DECISION: **{wf_result['final_decision']}**")
    add(f"")
    add(f"> {wf_result['final_msg']}")
    add(f"")
    add(f"### Headline numbers")
    add(f"")
    add(f"| Metric | Value |")
    add(f"|---|---|")
    add(f"| Avg return across 3 training windows | {wf_result['avg_training_return_pct']:+.2f}% |")
    add(f"| Holdout return (Nov 2024 - Apr 2025) | {holdout['metrics']['total_return_pct']:+.2f}% |")
    add(f"| Holdout / Training ratio | {wf_result['holdout_ratio']*100:.1f}% |")
    add(f"| Holdout trades | {holdout['metrics']['n_trades']} |")
    add(f"| Holdout win rate | {holdout['metrics']['win_rate_pct']:.1f}% |")
    add(f"| Holdout max drawdown | {holdout['metrics']['max_drawdown_pct']:+.2f}% |")
    add(f"| Holdout Nifty return | {holdout['metrics']['nifty_return_pct']:+.2f}% |")
    add(f"| Holdout alpha vs Nifty | {holdout['metrics']['alpha']:+.2f}% |")
    add(f"")
    add(f"## 📋 Rule changes")
    add(f"")
    base = wf_result["base_rules"]
    final = wf_result["final_rules"]
    changes = {k: (base[k], v) for k, v in final.items() if v != base.get(k)}
    if not changes:
        add(f"_No rule changes recommended. Baseline performance was best._")
    else:
        add(f"| Parameter | Baseline | Tuned to | Status |")
        add(f"|---|---|---|---|")
        for k, (bv, nv) in changes.items():
            applied = "ADOPTED" if wf_result["final_decision"] == "RECOMMEND_ADOPT" else "REVERTED"
            add(f"| {k} | {bv} | {nv} | {applied} |")
    add(f"")
    add(f"---")
    add(f"")
    add(f"## 📊 Training Window Details")
    add(f"")
    for i, d in enumerate(decisions, 1):
        add(f"### Window {i} ({d['window_id']}): {d['window_dates']}")
        add(f"")
        add(f"**Parameter tuned:** `{d['tune_param']}`  ")
        add(f"**Decision:** {d['decision']}  ")
        add(f"**Winner:** `{d['winner_name']}`")
        add(f"")
        add(f"**Reasoning:**")
        for r in d['reasoning']:
            add(f"- {r}")
        add(f"")
        add(f"**Candidates evaluated:**")
        add(f"")
        add(f"| Candidate | Trades | Return % | Win % | Max DD % | Alpha vs Nifty | Objective |")
        add(f"|---|---|---|---|---|---|---|")
        for c in d['candidates']:
            m = c["metrics"]
            obj = f"{c['objective']:.2f}" if c["objective"] is not None else "❌"
            star = " ⭐" if c["name"] == d["winner_name"] else ""
            add(f"| {c['name']}{star} | {m['n_trades']} | {m['total_return_pct']:+.2f}% | "
                f"{m['win_rate_pct']:.1f}% | {m['max_drawdown_pct']:+.2f}% | "
                f"{m['alpha']:+.2f}% | {obj} |")
        add(f"")
        add(f"**Effect size:** best candidate beat baseline by {d['effect_pp']:+.2f}pp")
        add(f"**Bootstrap test:** candidate won {d['bootstrap']['candidate_wins_pct']*100:.0f}% "
            f"of {d['bootstrap']['n_iter']} resamples")
        add(f"")
        add(f"---")
        add(f"")

    add(f"## 🔒 Holdout Test")
    add(f"")
    add(f"After the 3 training windows, the final rule set was locked and applied to a completely untouched 6-month period (Nov 2024 - Apr 2025). No further tuning occurred.")
    add(f"")
    add(f"**Final rule set used in holdout:**")
    add(f"")
    add(f"```")
    for k, v in final.items():
        marker = "  # CHANGED" if v != base.get(k) else ""
        add(f"  {k}: {v}{marker}")
    add(f"```")
    add(f"")
    add(f"**Holdout metrics:**")
    add(f"")
    add(f"| Metric | Value |")
    add(f"|---|---|")
    add(f"| Trades | {holdout['metrics']['n_trades']} |")
    add(f"| Win rate | {holdout['metrics']['win_rate_pct']:.1f}% |")
    add(f"| Total return | {holdout['metrics']['total_return_pct']:+.2f}% |")
    add(f"| Max drawdown | {holdout['metrics']['max_drawdown_pct']:+.2f}% |")
    add(f"| Total ₹ P&L | ₹{holdout['metrics']['total_pnl']:,.0f} |")
    add(f"| Total ₹ invested | ₹{holdout['metrics']['total_invested']:,.0f} |")
    add(f"| Return on deployed capital | {holdout['metrics']['return_on_deployed_pct']:+.2f}% |")
    add(f"| Nifty return | {holdout['metrics']['nifty_return_pct']:+.2f}% |")
    add(f"| Alpha vs Nifty | {holdout['metrics']['alpha']:+.2f}% |")
    add(f"")
    add(f"**Overfit check:** holdout / avg-training ratio = "
        f"{wf_result['holdout_ratio']*100:.1f}% "
        f"(threshold to revert: < {cfg['overfit_check']['holdout_min_pct_of_training_avg']*100:.0f}%)")
    add(f"")
    add(f"---")
    add(f"")
    add(f"## 🚦 Recommendation for production Rocky")
    add(f"")
    if wf_result["final_decision"] == "RECOMMEND_ADOPT" and changes:
        add(f"Push the following changes to `memory/TRADING-STRATEGY.md` and `CLAUDE.md`:")
        add(f"")
        for k, (bv, nv) in changes.items():
            add(f"- Change `{k}` from `{bv}` to `{nv}`")
        add(f"")
        add(f"These changes survived 3 sequential walk-forward windows + 1 untouched holdout. ")
        add(f"Confidence is **moderate** — single 18-month training period in one market regime. ")
        add(f"Recommend monitoring real paper-trade outcomes for 4 weeks before considering live trading.")
    elif wf_result["final_decision"] == "REVERT_TO_BASELINE":
        add(f"**DO NOT change production rules.** The tuned ruleset overfitted to training data — ")
        add(f"holdout performance dropped below the {cfg['overfit_check']['holdout_min_pct_of_training_avg']*100:.0f}% threshold. ")
        add(f"This is a successful walk-forward — it correctly identified an overfit and prevented bad rules from being deployed.")
    else:
        add(f"No rule changes recommended. Baseline survived all 3 tuning windows. Keep production rules as-is.")
    add(f"")
    add(f"## ⚠️ Honest caveats")
    add(f"")
    add(f"- **Single 18-month training period** — covers May 2023 to Oct 2024, which was mostly bull regime. Bear/sideways regime data is limited.")
    add(f"- **Gates 3 (catalyst) and 8 (earnings) still disabled** — LLM lookahead bias and historical data unavailable.")
    add(f"- **Gate 7 (FII) — NSE archive scrape blocked** — gate passes through, so FII flow filter is inactive in backtest.")
    add(f"- **Survivorship bias** — universe is today's Nifty 50 + Midcap 150. Stocks that were in the index in 2023 but got delisted/removed are not in this universe.")
    add(f"- **No transaction cost beyond STT + ₹20 brokerage** — real costs (stamp duty, exchange fees, GST, slippage) are ~0.1pp worse per round-trip.")
    add(f"- **No market-impact modeling** — fills happen at OPEN price exactly; real trading has spread + slippage.")
    add(f"")

    out_path.write_text("\n".join(L), encoding="utf-8")
    print(f"\nReport -> {out_path}", file=sys.stderr)


def main():
    cfg = json.loads((ROOT / "config" / "phase_b_config.json").read_text())
    universe, sectors = load_universe()

    print(f"Starting Phase B walk-forward...", file=sys.stderr)
    t0 = time.time()
    result = run_walk_forward(cfg, universe, sectors)
    elapsed = time.time() - t0
    print(f"\nWalk-forward complete in {elapsed:.1f}s ({elapsed/60:.1f} min)", file=sys.stderr)

    OUT = ROOT / "results"
    OUT.mkdir(exist_ok=True)

    # Save JSON artifacts (without full trade lists to keep files small)
    def _strip_trades(d):
        d2 = {k: v for k, v in d.items() if k != "trades"}
        return d2

    summary = {
        "phase_b_cfg":             result["phase_b_cfg"],
        "base_rules":              result["base_rules"],
        "tuned_rules":             result["tuned_rules"],
        "final_rules":             result["final_rules"],
        "final_decision":          result["final_decision"],
        "final_msg":               result["final_msg"],
        "avg_training_return_pct": result["avg_training_return_pct"],
        "training_returns":        result["training_returns"],
        "holdout_metrics":         result["holdout"]["metrics"],
        "holdout_ratio":           result["holdout_ratio"],
        "overfit_detected":        result["overfit_detected"],
        "training_decisions":      [_strip_trades(d) for d in result["training_decisions"]],
    }
    (OUT / "phase_b_summary.json").write_text(json.dumps(summary, indent=2, default=str))
    (OUT / "phase_b_holdout_trades.json").write_text(json.dumps(result["holdout"]["trades"], indent=2))

    write_report(result, OUT / "phase_b_final_report.md")

    print(f"")
    print(f"=== PHASE B COMPLETE ===")
    print(f"Decision: {result['final_decision']}")
    print(f"Avg training return:  {result['avg_training_return_pct']:+.2f}%")
    print(f"Holdout return:       {result['holdout']['metrics']['total_return_pct']:+.2f}%")
    print(f"Holdout / training:   {result['holdout_ratio']*100:.1f}%")
    print(f"")
    print(f"See: backtest/results/phase_b_final_report.md")


if __name__ == "__main__":
    main()
