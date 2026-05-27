#!/usr/bin/env python3
"""
walk_forward.py — Orchestrate the 3 sequential training windows in Phase B.
"""
import copy
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from backtest.engine.parameter_tuner import tune_window, run_with_overrides


def run_walk_forward(phase_b_cfg: dict, universe: list[str], sectors: dict) -> dict:
    """
    Run the 3 training windows sequentially. After each window, the winning
    override is merged into the rules for subsequent windows.
    """
    base_rules = copy.deepcopy(phase_b_cfg["base_rules"])
    starting_capital = phase_b_cfg["starting_capital"]
    costs = phase_b_cfg["costs"]
    gates = phase_b_cfg["statistical_gates"]

    current_rules = copy.deepcopy(base_rules)
    decisions: list[dict] = []
    training_returns: list[float] = []

    for window_cfg in phase_b_cfg["training_windows"]:
        print(f"\n{'='*80}", file=sys.stderr)
        print(f"WALK-FORWARD WINDOW: {window_cfg['id']}", file=sys.stderr)
        print(f"{'='*80}", file=sys.stderr)

        decision = tune_window(window_cfg, current_rules, starting_capital,
                               costs, universe, sectors, gates)
        decisions.append(decision)

        # Apply winning override to current_rules for subsequent windows
        current_rules.update(decision["winner_overrides"])
        training_returns.append(decision["winner_metrics"]["total_return_pct"])

        print(f"\n  [{decision['window_id']}] DECISION: {decision['decision']}", file=sys.stderr)
        for r in decision["reasoning"]:
            print(f"    - {r}", file=sys.stderr)
        print(f"  [{decision['window_id']}] Rules for next window: ", file=sys.stderr)
        for k, v in decision["winner_overrides"].items():
            print(f"    {k} = {v}", file=sys.stderr)

    # ── Holdout test ─────────────────────────────────────────────────────────
    print(f"\n{'='*80}", file=sys.stderr)
    print(f"HOLDOUT TEST — LOCKED RULES", file=sys.stderr)
    print(f"{'='*80}", file=sys.stderr)
    print(f"  Final rules carried forward:", file=sys.stderr)
    for k, v in current_rules.items():
        if v != base_rules.get(k):
            print(f"    {k}: {base_rules.get(k)} -> {v}  (TUNED)", file=sys.stderr)

    holdout_run = run_with_overrides(
        phase_b_cfg["holdout"], base_rules,
        {k: v for k, v in current_rules.items() if v != base_rules.get(k)},
        starting_capital, costs, universe, sectors,
    )

    # ── Overfit check ────────────────────────────────────────────────────────
    avg_training_return = sum(training_returns) / len(training_returns) if training_returns else 0
    holdout_return = holdout_run["metrics"]["total_return_pct"]
    holdout_ratio = (holdout_return / avg_training_return) if avg_training_return != 0 else 0

    overfit_threshold = phase_b_cfg["overfit_check"]["holdout_min_pct_of_training_avg"]
    overfit_detected = (
        avg_training_return > 0
        and holdout_return < avg_training_return * overfit_threshold
    )

    if overfit_detected:
        final_decision = "REVERT_TO_BASELINE"
        final_rules    = copy.deepcopy(base_rules)
        final_msg = (f"holdout return ({holdout_return:+.2f}%) < "
                     f"{overfit_threshold*100:.0f}% of training avg ({avg_training_return:+.2f}%)")
    else:
        final_decision = "RECOMMEND_ADOPT"
        final_rules    = current_rules
        final_msg = (f"holdout ({holdout_return:+.2f}%) within tolerance of "
                     f"training avg ({avg_training_return:+.2f}%)")

    return {
        "phase_b_cfg":       phase_b_cfg,
        "base_rules":        base_rules,
        "tuned_rules":       current_rules,
        "training_decisions": decisions,
        "training_returns":  training_returns,
        "avg_training_return_pct": round(avg_training_return, 2),
        "holdout":           {
            "window":   phase_b_cfg["holdout"],
            "metrics":  holdout_run["metrics"],
            "trades":   holdout_run["result"]["portfolio"]["trades"],
            "skip_log": holdout_run["result"].get("skip_log_full", []),
        },
        "holdout_ratio":     round(holdout_ratio, 3),
        "overfit_detected":  overfit_detected,
        "final_decision":    final_decision,
        "final_rules":       final_rules,
        "final_msg":         final_msg,
    }
