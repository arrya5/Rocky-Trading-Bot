#!/usr/bin/env python3
"""
run_sector_phase_b.py — Walk-forward optimization for sector rotation.

Training: May 2023 - Oct 2024 (3 windows of 6 months each)
  W1 (May-Oct 2023): tune top_n (2 / 3 / 4)
  W2 (Nov 2023-Apr 2024): apply W1 winner, tune rebalance_freq_days (21 / 42 / 63)
  W3 (May-Oct 2024): apply W1+W2 winners, tune lookback_days (21 / 42 / 63)

Holdout: Nov 2024 - Apr 2025 (locked, no tuning)

Overfit check: if holdout return < 70% of avg training return -> REVERT_TO_BASELINE.
"""
import copy, json, sys, time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
sys.path.insert(0, str(REPO))

from backtest.engine.sector_rotation import run_sector_rotation_backtest


BASE_RULES = {
    "top_n":               3,
    "rebalance_freq_days": 21,
    "lookback_days":       21,
}

WINDOWS = [
    {
        "id": "W1",
        "start_date": "2023-05-01", "end_date": "2023-10-31",
        "tune_param": "top_n",
        "candidates": [
            {"name": "top_n=2", "overrides": {"top_n": 2}},
            {"name": "top_n=3 (baseline)", "overrides": {"top_n": 3}},
            {"name": "top_n=4", "overrides": {"top_n": 4}},
        ],
    },
    {
        "id": "W2",
        "start_date": "2023-11-01", "end_date": "2024-04-30",
        "tune_param": "rebalance_freq_days",
        "candidates": [
            {"name": "freq=21 (baseline)", "overrides": {"rebalance_freq_days": 21}},
            {"name": "freq=42 (~2 months)", "overrides": {"rebalance_freq_days": 42}},
            {"name": "freq=63 (~3 months)", "overrides": {"rebalance_freq_days": 63}},
        ],
    },
    {
        "id": "W3",
        "start_date": "2024-05-01", "end_date": "2024-10-31",
        "tune_param": "lookback_days",
        "candidates": [
            {"name": "lookback=21 (baseline)", "overrides": {"lookback_days": 21}},
            {"name": "lookback=42", "overrides": {"lookback_days": 42}},
            {"name": "lookback=63", "overrides": {"lookback_days": 63}},
        ],
    },
]

HOLDOUT = {"start_date": "2024-11-01", "end_date": "2025-04-30"}
MIN_EFFECT_PP = 1.5      # candidate must beat baseline by >= 1.5pp on return
OVERFIT_THRESH = 0.70    # holdout >= 70% of training avg, else revert


def run_one(window: dict, rules: dict) -> dict:
    result = run_sector_rotation_backtest(
        start_date=window["start_date"], end_date=window["end_date"],
        starting_capital=500_000,
        top_n=rules["top_n"],
        rebalance_freq_days=rules["rebalance_freq_days"],
        lookback_days=rules["lookback_days"],
    )
    snaps = result["snapshots"]
    starting = result["config"]["starting_capital"]
    final = snaps[-1]["total_value"] if snaps else starting
    return_pct = (final - starting) / starting * 100
    n_trades = len(result["trades"])
    n_wins = sum(1 for t in result["trades"] if t.get("pnl_pct", 0) > 0)

    # Max drawdown
    peak = starting; max_dd = 0.0
    for s in snaps:
        peak = max(peak, s["total_value"])
        dd = (s["total_value"] - peak) / peak * 100
        if dd < max_dd: max_dd = dd

    return {
        "return_pct": return_pct,
        "max_dd_pct": max_dd,
        "n_trades":   n_trades,
        "win_rate":   (n_wins / n_trades * 100) if n_trades else 0,
        "nifty_pct":  result["nifty_return_pct"],
        "alpha_pct":  return_pct - result["nifty_return_pct"],
        "final":      final,
        "trades":     result["trades"],
    }


def tune_window(window: dict, current_rules: dict) -> dict:
    print(f"\n{'='*80}", file=sys.stderr)
    print(f"WINDOW {window['id']}: tuning '{window['tune_param']}' over {window['start_date']} -> {window['end_date']}", file=sys.stderr)
    print(f"{'='*80}", file=sys.stderr)

    runs = []
    for cand in window["candidates"]:
        rules = copy.deepcopy(current_rules)
        rules.update(cand["overrides"])
        print(f"  running '{cand['name']}' with rules {rules}", file=sys.stderr)
        metrics = run_one(window, rules)
        runs.append({"name": cand["name"], "overrides": cand["overrides"], **metrics})

    # Identify baseline (matches current_rules for the tuned param)
    tune_param = window["tune_param"]
    baseline_value = current_rules[tune_param]
    baseline = next((r for r in runs if r["overrides"].get(tune_param) == baseline_value), runs[0])

    # Rank by return
    ranked = sorted(runs, key=lambda r: r["return_pct"], reverse=True)
    best = ranked[0]

    effect_pp = best["return_pct"] - baseline["return_pct"]

    if best["name"] == baseline["name"]:
        decision = "KEEP_BASELINE"
        reasoning = ["baseline ranked #1 by return"]
        winner = baseline
    elif effect_pp < MIN_EFFECT_PP:
        decision = "KEEP_BASELINE"
        reasoning = [f"effect size {effect_pp:+.2f}pp below threshold {MIN_EFFECT_PP}pp"]
        winner = baseline
    else:
        decision = "ADOPT_WINNER"
        reasoning = [f"best candidate '{best['name']}' beats baseline by {effect_pp:+.2f}pp"]
        winner = best

    for r in runs:
        marker = " ⭐" if r["name"] == winner["name"] else ""
        print(f"    {r['name']}{marker}: return={r['return_pct']:+.2f}%, "
              f"trades={r['n_trades']}, win%={r['win_rate']:.0f}, MaxDD={r['max_dd_pct']:.2f}%",
              file=sys.stderr)

    return {
        "window_id":    window["id"],
        "dates":        f"{window['start_date']} -> {window['end_date']}",
        "tune_param":   tune_param,
        "candidates":   [{k: v for k, v in r.items() if k != "trades"} for r in runs],
        "baseline":     baseline["name"],
        "best":         best["name"],
        "effect_pp":    effect_pp,
        "decision":     decision,
        "reasoning":    reasoning,
        "winner_name":  winner["name"],
        "winner_overrides": winner["overrides"],
        "winner_metrics":   {k: v for k, v in winner.items() if k not in ("trades", "overrides")},
    }


def write_report(result: dict, out_path: Path):
    decisions = result["decisions"]
    holdout = result["holdout"]
    final_rules = result["final_rules"]
    base_rules = result["base_rules"]

    L = []
    add = L.append
    add(f"# Sector Rotation — Walk-Forward Final Report")
    add(f"")
    add(f"_Generated: {datetime.now().isoformat(timespec='seconds')}_")
    add(f"")
    add(f"---")
    add(f"")
    add(f"## 🎯 FINAL DECISION: **{result['final_decision']}**")
    add(f"")
    add(f"> {result['final_msg']}")
    add(f"")
    add(f"### Headline numbers")
    add(f"")
    add(f"| Metric | Value |")
    add(f"|---|---|")
    add(f"| Avg return across 3 training windows | {result['avg_training_return']:+.2f}% |")
    add(f"| Holdout return (Nov 2024 - Apr 2025) | {holdout['return_pct']:+.2f}% |")
    add(f"| Holdout / Training ratio | {result['holdout_ratio']*100:.1f}% |")
    add(f"| Holdout trades | {holdout['n_trades']} |")
    add(f"| Holdout win rate | {holdout['win_rate']:.1f}% |")
    add(f"| Holdout max drawdown | {holdout['max_dd_pct']:+.2f}% |")
    add(f"| Holdout Nifty return | {holdout['nifty_pct']:+.2f}% |")
    add(f"| Holdout alpha vs Nifty | {holdout['alpha_pct']:+.2f}% |")
    add(f"")
    add(f"## 📋 Rule changes")
    add(f"")
    changes = {k: (base_rules[k], v) for k, v in final_rules.items() if v != base_rules.get(k)}
    if not changes:
        add(f"_No rule changes recommended. Baseline performance was best._")
    else:
        add(f"| Parameter | Baseline | Tuned to | Status |")
        add(f"|---|---|---|---|")
        for k, (bv, nv) in changes.items():
            applied = "ADOPTED" if result['final_decision'] == 'RECOMMEND_ADOPT' else "REVERTED"
            add(f"| {k} | {bv} | {nv} | {applied} |")
    add(f"")
    add(f"---")
    add(f"")
    add(f"## 📊 Training Window Details")
    add(f"")
    for d in decisions:
        add(f"### Window {d['window_id']}: {d['dates']}")
        add(f"")
        add(f"**Parameter tuned:** `{d['tune_param']}`  ")
        add(f"**Decision:** {d['decision']}  ")
        add(f"**Winner:** `{d['winner_name']}`")
        add(f"")
        for r in d['reasoning']:
            add(f"- {r}")
        add(f"")
        add(f"| Candidate | Trades | Return % | Win % | Max DD | Alpha vs Nifty |")
        add(f"|---|---|---|---|---|---|")
        for c in d['candidates']:
            star = " ⭐" if c['name'] == d['winner_name'] else ""
            add(f"| {c['name']}{star} | {c['n_trades']} | {c['return_pct']:+.2f}% | "
                f"{c['win_rate']:.0f}% | {c['max_dd_pct']:+.2f}% | {c['alpha_pct']:+.2f}% |")
        add(f"")
        add(f"---")
        add(f"")

    add(f"## 🔒 Holdout (Nov 2024 - Apr 2025)")
    add(f"")
    add(f"Final rules locked in. No tuning during holdout.")
    add(f"")
    add(f"**Final ruleset:**")
    add(f"")
    add(f"```")
    for k, v in final_rules.items():
        marker = "  # CHANGED from baseline" if v != base_rules.get(k) else ""
        add(f"  {k}: {v}{marker}")
    add(f"```")
    add(f"")
    add(f"## 🚦 Recommendation")
    add(f"")
    if result['final_decision'] == 'RECOMMEND_ADOPT':
        add(f"Sector rotation passed the walk-forward test. Consider adopting as a new")
        add(f"production strategy. Notes:")
        add(f"- Only one 18-month training period — sample size warning still applies")
        add(f"- Sector indices need to be reliably tradeable in your broker (most are)")
        add(f"- Cost structure (~36 trades/2yr, monthly rebalance) is far cheaper than current Rocky")
    else:
        add(f"**Do NOT adopt this strategy** — the walk-forward overfit-check failed.")
        add(f"The training periods looked good, but the holdout exposed the apparent edge as")
        add(f"likely overfitting. Keep production Rocky on its current rules.")
    add(f"")
    out_path.write_text("\n".join(L), encoding="utf-8")


def main():
    print("Starting sector-rotation walk-forward...", file=sys.stderr)
    t0 = time.time()

    current_rules = copy.deepcopy(BASE_RULES)
    decisions = []
    training_returns = []

    for window in WINDOWS:
        d = tune_window(window, current_rules)
        decisions.append(d)
        current_rules.update(d["winner_overrides"])
        training_returns.append(d["winner_metrics"]["return_pct"])

    # Holdout
    print(f"\n{'='*80}\nHOLDOUT — locked rules\n{'='*80}", file=sys.stderr)
    print(f"  final rules: {current_rules}", file=sys.stderr)
    holdout_metrics = run_one(HOLDOUT, current_rules)

    avg_train = sum(training_returns) / len(training_returns) if training_returns else 0
    holdout_ratio = (holdout_metrics["return_pct"] / avg_train) if avg_train != 0 else 0

    overfit = (avg_train > 0 and holdout_metrics["return_pct"] < avg_train * OVERFIT_THRESH)

    if overfit:
        final_decision = "REVERT_TO_BASELINE"
        final_rules    = copy.deepcopy(BASE_RULES)
        final_msg = (f"holdout return ({holdout_metrics['return_pct']:+.2f}%) < "
                     f"{OVERFIT_THRESH*100:.0f}% of training avg ({avg_train:+.2f}%)")
    elif holdout_metrics["return_pct"] < holdout_metrics["nifty_pct"] + 3.0:
        final_decision = "ADOPT_WITH_CAUTION"
        final_rules    = current_rules
        final_msg = (f"holdout return positive but only {holdout_metrics['alpha_pct']:+.2f}pp alpha vs Nifty. "
                     f"Margin is thin; consider one more validation period before deploying real money.")
    else:
        final_decision = "RECOMMEND_ADOPT"
        final_rules    = current_rules
        final_msg = (f"holdout return ({holdout_metrics['return_pct']:+.2f}%) within tolerance of "
                     f"training avg ({avg_train:+.2f}%) AND beats Nifty by {holdout_metrics['alpha_pct']:+.2f}pp")

    result = {
        "base_rules":           BASE_RULES,
        "tuned_rules":          current_rules,
        "final_rules":          final_rules,
        "final_decision":       final_decision,
        "final_msg":            final_msg,
        "decisions":            decisions,
        "training_returns":     training_returns,
        "avg_training_return":  avg_train,
        "holdout":              {k: v for k, v in holdout_metrics.items() if k != "trades"},
        "holdout_ratio":        holdout_ratio,
        "overfit_detected":     overfit,
    }

    OUT = ROOT / "results"
    OUT.mkdir(exist_ok=True)
    (OUT / "sector_phase_b_summary.json").write_text(json.dumps(result, indent=2, default=str))
    write_report(result, OUT / "sector_phase_b_report.md")

    elapsed = time.time() - t0
    print(f"\nWalk-forward complete in {elapsed:.1f}s ({elapsed/60:.1f} min)", file=sys.stderr)

    print(f"")
    print(f"=== SECTOR ROTATION PHASE B ===")
    print(f"Decision:             {final_decision}")
    print(f"Avg training return:  {avg_train:+.2f}%")
    print(f"Holdout return:       {holdout_metrics['return_pct']:+.2f}%")
    print(f"Holdout Nifty:        {holdout_metrics['nifty_pct']:+.2f}%")
    print(f"Holdout alpha:        {holdout_metrics['alpha_pct']:+.2f}%")
    print(f"Holdout / training:   {holdout_ratio*100:.1f}%")
    print(f"")
    print(f"Report: backtest/results/sector_phase_b_report.md")


if __name__ == "__main__":
    main()
