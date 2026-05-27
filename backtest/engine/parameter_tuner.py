#!/usr/bin/env python3
"""
parameter_tuner.py — Phase B parameter tuning with statistical gates.

For one window:
  1. Run baseline with current rules
  2. Run each candidate variation (rules with one parameter overridden)
  3. Compare each candidate to baseline using bootstrap resampling
  4. Pick winner if it beats baseline on objective AND passes bootstrap test
"""
import copy
import random
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from backtest.engine.backtest_runner import run_backtest


# ── Objective function ────────────────────────────────────────────────────────
def objective(metrics: dict) -> float:
    """
    Primary objective: total return on starting capital (%).
    Penalty: trade count under 15 makes the result statistically meaningless,
             so we return -inf to disqualify.
    Sanity: max drawdown should not exceed -20%.
    """
    if metrics["n_trades"] < 15:
        return float("-inf")
    if metrics["max_drawdown_pct"] < -20.0:
        return float("-inf")
    return metrics["total_return_pct"]


# ── Run a single backtest configuration ───────────────────────────────────────
def run_with_overrides(window_cfg: dict, base_rules: dict, overrides: dict,
                       starting_capital: int, costs: dict,
                       universe: list[str], sectors: dict) -> dict:
    """Build a runtime config with overrides applied and run the backtest."""
    rules = copy.deepcopy(base_rules)
    rules.update(overrides)
    cfg = {
        "start_date":       window_cfg["start_date"],
        "end_date":         window_cfg["end_date"],
        "starting_capital": starting_capital,
        "rules":            rules,
        "costs":            costs,
    }
    result = run_backtest(cfg, universe, sectors)
    metrics = _compute_metrics(result)
    return {"cfg": cfg, "result": result, "metrics": metrics}


def _compute_metrics(result: dict) -> dict:
    """Extract the metrics we'll compare on."""
    trades = result["portfolio"]["trades"]
    snaps  = result["portfolio"]["daily_snapshots"]
    starting = result["portfolio"]["starting_cash"]

    final_value = snaps[-1]["total_value"] if snaps else starting
    total_return_pct = (final_value - starting) / starting * 100

    n_trades = len(trades)
    n_wins   = sum(1 for t in trades if t["pnl_pct"] > 0)
    win_rate = (n_wins / n_trades * 100) if n_trades else 0

    # Max drawdown from snapshot values
    peak = starting
    max_dd_pct = 0.0
    for s in snaps:
        peak = max(peak, s["total_value"])
        dd_pct = (s["total_value"] - peak) / peak * 100
        if dd_pct < max_dd_pct:
            max_dd_pct = dd_pct

    total_pnl = sum(t["pnl_abs"] for t in trades)
    invested  = sum(t["entry_price"] * t["original_qty"] for t in trades)
    return_on_deployed = (total_pnl / invested * 100) if invested > 0 else 0

    return {
        "n_trades":          n_trades,
        "win_rate_pct":      round(win_rate, 2),
        "total_return_pct":  round(total_return_pct, 3),
        "max_drawdown_pct":  round(max_dd_pct, 2),
        "total_pnl":         round(total_pnl, 2),
        "total_invested":    round(invested, 2),
        "return_on_deployed_pct": round(return_on_deployed, 2),
        "nifty_return_pct":  round(result["nifty_return_pct"], 2),
        "alpha":             round(total_return_pct - result["nifty_return_pct"], 2),
    }


# ── Bootstrap test ────────────────────────────────────────────────────────────
def bootstrap_compare(baseline_trades: list[dict], candidate_trades: list[dict],
                      n_iter: int = 200, seed: int = 42) -> dict:
    """
    Resample trade outcomes with replacement, compare candidate's total P&L
    pct vs baseline's. Returns the fraction of resamples where candidate wins.

    Note: this compares the empirical distribution of trade-level P&L %.
    It's not a perfect substitute for path-dependent return (because partial
    exits and cash recycling matter), but it's a meaningful robustness check
    on whether the candidate's edge survives sampling variability.
    """
    if not baseline_trades or not candidate_trades:
        return {"candidate_wins_pct": 0.0, "n_iter": 0, "robust": False,
                "note": "insufficient trades for bootstrap"}

    rng = random.Random(seed)
    bN = len(baseline_trades)
    cN = len(candidate_trades)
    b_pcts = [t["pnl_pct"] for t in baseline_trades]
    c_pcts = [t["pnl_pct"] for t in candidate_trades]

    wins = 0
    for _ in range(n_iter):
        bs = [rng.choice(b_pcts) for _ in range(bN)]
        cs = [rng.choice(c_pcts) for _ in range(cN)]
        b_mean = sum(bs) / bN
        c_mean = sum(cs) / cN
        if c_mean > b_mean:
            wins += 1

    return {
        "candidate_wins_pct": round(wins / n_iter, 3),
        "n_iter": n_iter,
    }


# ── Tune one window ───────────────────────────────────────────────────────────
def tune_window(window_cfg: dict, base_rules: dict, starting_capital: int,
                costs: dict, universe: list[str], sectors: dict,
                gates: dict) -> dict:
    """
    Run all candidates for this window, find the winner via objective + bootstrap.

    Returns dict with:
      window_id, tune_param, candidates (list of {name, overrides, metrics, vs_baseline}),
      winner (name + overrides), decision (one of: ADOPT_WINNER, KEEP_BASELINE, INSUFFICIENT_DATA),
      reasoning
    """
    window_id = window_cfg["id"]
    tune_param = window_cfg["tune_param"]
    candidates = window_cfg["candidates"]

    print(f"\n  [{window_id}] Tuning '{tune_param}' over {window_cfg['start_date']} -> {window_cfg['end_date']}", file=sys.stderr)
    print(f"  [{window_id}] Testing {len(candidates)} candidates: " +
          ", ".join(c["name"] for c in candidates), file=sys.stderr)

    runs: list[dict] = []
    for cand in candidates:
        print(f"  [{window_id}] -> running candidate '{cand['name']}'", file=sys.stderr)
        run = run_with_overrides(window_cfg, base_rules, cand["overrides"],
                                 starting_capital, costs, universe, sectors)
        runs.append({
            "name":      cand["name"],
            "overrides": cand["overrides"],
            "metrics":   run["metrics"],
            "trades":    run["result"]["portfolio"]["trades"],
        })

    # Identify "baseline" candidate (first one matching base_rules for this param)
    # If no exact match, baseline = the first candidate
    baseline_idx = 0
    for i, r in enumerate(runs):
        match = True
        for k, v in r["overrides"].items():
            if base_rules.get(k) != v:
                match = False
                break
        if match:
            baseline_idx = i
            break
    baseline_run = runs[baseline_idx]

    print(f"  [{window_id}] Baseline = '{baseline_run['name']}' "
          f"({baseline_run['metrics']['total_return_pct']:+.2f}%, "
          f"{baseline_run['metrics']['n_trades']} trades)", file=sys.stderr)

    # Score each candidate
    for r in runs:
        r["objective"] = objective(r["metrics"])

    # Sort by objective descending
    ranked = sorted(runs, key=lambda r: r["objective"], reverse=True)
    best = ranked[0]

    # Bootstrap test best vs baseline
    bootstrap_result = bootstrap_compare(
        baseline_run["trades"], best["trades"],
        n_iter=gates["bootstrap_iterations"],
    )

    # Compute effect size
    effect_pp = best["metrics"]["total_return_pct"] - baseline_run["metrics"]["total_return_pct"]

    # Decision logic
    decision = "KEEP_BASELINE"
    reasoning = []

    if best["name"] == baseline_run["name"]:
        decision = "KEEP_BASELINE"
        reasoning.append(f"baseline ranked #1 by objective ({baseline_run['metrics']['total_return_pct']:+.2f}%)")
    elif best["objective"] == float("-inf"):
        decision = "INSUFFICIENT_DATA"
        reasoning.append(f"best candidate failed sanity checks (min trades or max DD)")
    elif effect_pp < gates["min_effect_pp_return"]:
        decision = "KEEP_BASELINE"
        reasoning.append(f"effect size {effect_pp:+.2f}pp < required {gates['min_effect_pp_return']}pp")
    elif bootstrap_result["candidate_wins_pct"] < gates["bootstrap_win_threshold"]:
        decision = "KEEP_BASELINE"
        reasoning.append(f"bootstrap win rate {bootstrap_result['candidate_wins_pct']*100:.0f}% < required {gates['bootstrap_win_threshold']*100:.0f}%")
    else:
        decision = "ADOPT_WINNER"
        reasoning.append(f"best candidate '{best['name']}' beats baseline by {effect_pp:+.2f}pp")
        reasoning.append(f"bootstrap robust: {bootstrap_result['candidate_wins_pct']*100:.0f}% wins on resamples")

    winner = best if decision == "ADOPT_WINNER" else baseline_run

    return {
        "window_id":       window_id,
        "window_dates":    f"{window_cfg['start_date']} -> {window_cfg['end_date']}",
        "tune_param":      tune_param,
        "candidates":      [{"name": r["name"], "overrides": r["overrides"],
                             "metrics": r["metrics"], "objective": r["objective"]
                             if r["objective"] != float("-inf") else None}
                            for r in runs],
        "baseline_name":   baseline_run["name"],
        "best_name":       best["name"],
        "effect_pp":       round(effect_pp, 2),
        "bootstrap":       bootstrap_result,
        "decision":        decision,
        "reasoning":       reasoning,
        "winner_name":     winner["name"],
        "winner_overrides": winner["overrides"],
        "winner_metrics":  winner["metrics"],
    }
