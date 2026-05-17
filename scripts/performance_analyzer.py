#!/usr/bin/env python3
"""
performance_analyzer.py — Analyze trade outcomes and generate rule-change recommendations

Reads:  memory/trade-outcomes.json
Output: JSON with statistics and concrete change_instructions for TRADING-STRATEGY.md

The weekly-review routine runs this and applies recommendations to TRADING-STRATEGY.md.
Rule changes only activate when total_closed_trades >= 20.

Usage:
  python scripts/performance_analyzer.py
"""

import json
from collections import defaultdict
from datetime import date
from pathlib import Path

OUTCOMES_FILE = Path(__file__).parent.parent / "memory" / "trade-outcomes.json"
MIN_TRADES    = 20


def closed_trades() -> list:
    if not OUTCOMES_FILE.exists():
        return []
    data = json.loads(OUTCOMES_FILE.read_text())
    return [t for t in data.get("trades", []) if t.get("exit_date") is not None]


def win_rate(trades: list) -> dict:
    if not trades:
        return {"n": 0, "wins": 0, "win_rate_pct": None}
    wins = sum(1 for t in trades if (t.get("pnl_pct") or 0) > 0)
    return {"n": len(trades), "wins": wins, "win_rate_pct": round(wins / len(trades) * 100, 1)}


def avg_pnl(trades: list) -> dict:
    winners = [t["pnl_abs"] for t in trades if (t.get("pnl_abs") or 0) > 0]
    losers  = [t["pnl_abs"] for t in trades if (t.get("pnl_abs") or 0) <= 0]
    return {
        "avg_win_inr":  round(sum(winners) / len(winners), 0) if winners else 0,
        "avg_loss_inr": round(sum(losers)  / len(losers),  0) if losers  else 0,
    }


def band_analysis(trades: list, field: str, bands: list) -> list:
    out = []
    for low, high, label in bands:
        subset = [t for t in trades if t.get(field) is not None and low <= t[field] < high]
        out.append({"band": label, **win_rate(subset), **avg_pnl(subset)})
    return out


def analyze():
    trades = closed_trades()
    n      = len(trades)

    result = {
        "analysis_date":               date.today().isoformat(),
        "total_closed_trades":         n,
        "min_trades_for_rule_changes": MIN_TRADES,
        "sufficient_data":             n >= MIN_TRADES,
    }

    if n == 0:
        result["message"] = "No closed trades yet. Rocky has not exited any positions."
        print(json.dumps(result, indent=2))
        return

    # ── Overall stats ──────────────────────────────────────────────────────────
    result["overall"] = {
        **win_rate(trades),
        **avg_pnl(trades),
        "total_pnl_inr": round(sum(t["pnl_abs"] for t in trades if t.get("pnl_abs")), 2),
        "best_trade":    max(trades, key=lambda t: t.get("pnl_pct") or -999)["symbol"],
        "worst_trade":   min(trades, key=lambda t: t.get("pnl_pct") or 999)["symbol"],
    }

    # ── By GRU confidence band ─────────────────────────────────────────────────
    result["by_gru_confidence"] = band_analysis(trades, "gru_confidence", [
        (0.60, 0.65, "60-65%"),
        (0.65, 0.70, "65-70%"),
        (0.70, 0.75, "70-75%"),
        (0.75, 0.80, "75-80%"),
        (0.80, 1.01, "80%+"),
    ])

    # ── By VIX level ───────────────────────────────────────────────────────────
    result["by_vix"] = band_analysis(trades, "vix_at_entry", [
        (0,   13,  "VIX <13"),
        (13,  16,  "VIX 13-16"),
        (16,  18,  "VIX 16-18"),
        (18,  20,  "VIX 18-20"),
        (20,  999, "VIX 20+"),
    ])

    # ── By FII flow ────────────────────────────────────────────────────────────
    result["by_fii_flow"] = band_analysis(trades, "fii_flow_at_entry", [
        (-99999, -2000, "FII < -2000Cr"),
        (-2000,  -1000, "FII -1000 to -2000Cr"),
        (-1000,  0,     "FII -1000 to 0"),
        (0,      99999, "FII positive"),
    ])

    # ── By sector ─────────────────────────────────────────────────────────────
    by_sector = defaultdict(list)
    for t in trades:
        by_sector[t.get("sector", "unknown")].append(t)
    result["by_sector"] = {s: {**win_rate(g), **avg_pnl(g)} for s, g in by_sector.items()}

    # ── By market regime ───────────────────────────────────────────────────────
    by_regime = defaultdict(list)
    for t in trades:
        by_regime[t.get("market_regime", "unknown")].append(t)
    result["by_regime"] = {r: {**win_rate(g), **avg_pnl(g)} for r, g in by_regime.items()}

    # ── By exit reason ─────────────────────────────────────────────────────────
    by_exit = defaultdict(list)
    for t in trades:
        by_exit[t.get("exit_reason", "unknown")].append(t)
    result["by_exit_reason"] = {r: win_rate(g) for r, g in by_exit.items()}

    # ── Days held: winners vs losers ───────────────────────────────────────────
    w_days = [t["days_held"] for t in trades if (t.get("pnl_abs") or 0) > 0 and t.get("days_held")]
    l_days = [t["days_held"] for t in trades if (t.get("pnl_abs") or 0) <= 0 and t.get("days_held")]
    result["days_held"] = {
        "avg_winner": round(sum(w_days) / len(w_days), 1) if w_days else None,
        "avg_loser":  round(sum(l_days) / len(l_days), 1) if l_days else None,
    }

    # ── Recommendations ────────────────────────────────────────────────────────
    recs = []

    if n >= MIN_TRADES:

        # GRU confidence floor
        low_conf  = [t for t in trades if 0.60 <= (t.get("gru_confidence") or 0) < 0.70]
        high_conf = [t for t in trades if (t.get("gru_confidence") or 0) >= 0.70]
        if len(low_conf) >= 5:
            lwr = win_rate(low_conf)["win_rate_pct"]
            hwr = win_rate(high_conf)["win_rate_pct"]
            if lwr is not None and lwr < 40:
                recs.append({
                    "parameter":          "gru_confidence_floor",
                    "current":            "60%",
                    "recommended":        "70%",
                    "evidence":           f"Win rate at 60-69% confidence: {lwr}% ({len(low_conf)} trades). Win rate at 70%+: {hwr}% ({len(high_conf)} trades).",
                    "change_instruction": "In memory/TRADING-STRATEGY.md and CLAUDE.md, change 'confidence >= 60%' to 'confidence >= 70%' in Gate 2.",
                })

        # VIX gate
        high_vix = [t for t in trades if 18 <= (t.get("vix_at_entry") or 0) < 20]
        if len(high_vix) >= 3:
            hvwr = win_rate(high_vix)["win_rate_pct"]
            if hvwr is not None and hvwr < 35:
                recs.append({
                    "parameter":          "vix_gate",
                    "current":            "VIX < 20",
                    "recommended":        "VIX < 18",
                    "evidence":           f"Win rate when VIX 18-20 at entry: {hvwr}% ({len(high_vix)} trades).",
                    "change_instruction": "In memory/TRADING-STRATEGY.md and CLAUDE.md, change 'India VIX < 20' to 'India VIX < 18' in Gate 5.",
                })

        # FII flow gate
        weak_fii = [t for t in trades if -2000 <= (t.get("fii_flow_at_entry") or 0) < -1000]
        if len(weak_fii) >= 3:
            wfwr = win_rate(weak_fii)["win_rate_pct"]
            if wfwr is not None and wfwr < 35:
                recs.append({
                    "parameter":          "fii_flow_gate",
                    "current":            "-2000 Cr",
                    "recommended":        "-1000 Cr",
                    "evidence":           f"Win rate when FII flow -1000 to -2000 Cr: {wfwr}% ({len(weak_fii)} trades).",
                    "change_instruction": "In memory/TRADING-STRATEGY.md and CLAUDE.md, change '-2000 Cr' to '-1000 Cr' in Gate 9.",
                })

        # Sector blocks
        for sector, group in by_sector.items():
            if sector == "unknown" or len(group) < 3:
                continue
            swr = win_rate(group)["win_rate_pct"]
            if swr is not None and swr < 25:
                safe_name = sector.lower().replace(" ", "_")
                recs.append({
                    "parameter":          f"sector_block_{safe_name}",
                    "current":            "no block",
                    "recommended":        f"block {sector}",
                    "evidence":           f"Win rate in {sector}: {swr}% ({len(group)} trades).",
                    "change_instruction": (
                        f"Add to memory/TRADING-STRATEGY.md under a 'Sector Blocks' section: "
                        f"'BLOCK {sector.upper()}: win rate {swr}% on {len(group)} trades — skip until 4 consecutive wins.' "
                        f"Reference this block in Gate 1 of the 9-point gate."
                    ),
                })

    else:
        recs.append({
            "note":   f"Only {n} closed trades — need {MIN_TRADES} before changing rules.",
            "action": "Observe patterns. Do NOT change any gate parameters yet.",
        })

    result["recommendations"] = recs
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    analyze()
