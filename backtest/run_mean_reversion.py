#!/usr/bin/env python3
"""
run_mean_reversion.py — Run mean-reversion strategy backtest.
"""
import copy, json, sys, time
from datetime import datetime, date
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
sys.path.insert(0, str(REPO))

from backtest.engine import mean_reversion_signal_generator as scorer
from backtest.engine import gates, signal_asof
from backtest.engine.swing_portfolio import SwingPaperPortfolio


PERIODS = {
    "poc":     ("2025-05-01", "2025-10-31"),
    "holdout": ("2024-11-01", "2025-04-30"),
}


def load_universe():
    data = json.loads((ROOT / "data" / "universe.json").read_text())
    return data["symbols"], data["sectors"]


def previous_trading_day(d, all_days):
    earlier = [x for x in all_days if x < d]
    return earlier[-1] if earlier else None


def run(start_str: str, end_str: str, label: str):
    start = date.fromisoformat(start_str)
    end   = date.fromisoformat(end_str)
    universe, sectors = load_universe()

    cfg = {
        "start_date": start_str,
        "end_date":   end_str,
        "starting_capital": 500000,
        "rules": {
            "min_score": 60,
            "max_hold_days": 7,
            "circuit_gap_pct": 0.18,
            "vix_max": 25,
            "fii_min_cr": -3500,
            "sector_max_open": 2,
            "size_tier_high": 70000,
            "size_tier_mid":  50000,
            "size_tier_low":  30000,
        },
        "costs": {"stt_sell_pct": 0.001, "brokerage_per_order": 20},
    }

    scorer.set_tier_sizes(70000, 50000, 30000)
    signal_asof.prime_benchmark(start, end)
    scorer.prime_cache(universe, start, end, lookback_days=220)

    DATA = ROOT / "data"
    gates.load_vix(DATA / "historical_vix.csv")
    gates.load_fii(DATA / "historical_fii.csv")

    all_days = signal_asof.trading_days(start, end)
    if not all_days:
        raise RuntimeError("No trading days")
    print(f"Mean-reversion {label}: {all_days[0]} -> {all_days[-1]} ({len(all_days)} days)", file=sys.stderr)

    port = SwingPaperPortfolio(starting_cash=cfg["starting_capital"], config=cfg)
    rules = cfg["rules"]
    nifty_start = signal_asof.nifty_close(all_days[0]) or 0.0
    skip_log = []

    for i, d in enumerate(all_days):
        prev = previous_trading_day(d, all_days)
        if prev is None:
            port.snapshot(d, port.cash, signal_asof.nifty_close(d))
            continue

        ohlc_open = {}
        for sym in list(port.positions.keys()):
            o = signal_asof.get_ohlc(sym, d)
            if o is not None:
                ohlc_open[sym] = o
        port.process_day(d, ohlc_open)

        vix_ok, _ = gates.gate_5_vix(prev, rules["vix_max"])
        fii_ok, _ = gates.gate_7_fii(prev, rules["fii_min_cr"])

        if vix_ok and fii_ok:
            regime = signal_asof.compute_regime_asof(prev)
            scored = []
            for sym in universe:
                r = scorer.score_symbol_asof(sym, prev)
                if r is None or r.get("signal") != "BUY":
                    continue
                if r["confidence"] < rules["min_score"]:
                    continue
                scored.append(r)
            scored.sort(key=lambda x: x["confidence"], reverse=True)

            for cand in scored[:5]:  # top 5 picks per day for mean-reversion (rarer signals)
                sym = cand["symbol"]
                if sym in port.positions:
                    continue
                ohlc_today = signal_asof.get_ohlc(sym, d)
                if ohlc_today is None:
                    continue
                prev_ohlc = signal_asof.get_ohlc(sym, prev)
                if prev_ohlc is None:
                    continue
                gap_ok, _ = gates.gate_4_circuit(prev_ohlc["close"], ohlc_today["open"], rules["circuit_gap_pct"])
                if not gap_ok:
                    continue
                if port.sector_count(cand["sector"]) >= rules["sector_max_open"]:
                    continue

                entry = ohlc_today["open"]
                qty = int(cand["suggested_position_size"] // entry)
                if qty < 1 or qty * entry > port.cash:
                    continue

                ok = port.enter(
                    sym, cand["sector"], qty, entry, cand["confidence"], d, regime=regime,
                    stop_distance_pct=cand["stop_distance_pct"],
                    partial_target_pct=cand["partial_target_pct"],
                    trailing_trigger_pct=cand["trailing_trigger_pct"],
                    trailing_distance_pct=cand["trailing_distance_pct"],
                )
                if ok:
                    port.process_day(d, {sym: ohlc_today})

        mtm = {}
        for sym in port.positions.keys():
            o = signal_asof.get_ohlc(sym, d)
            if o is not None:
                mtm[sym] = o["close"]
        total_value = port.mark_to_market(d, mtm)
        port.snapshot(d, total_value, signal_asof.nifty_close(d))

        if (i + 1) % 30 == 0:
            print(f"  [{d}] Rs {total_value:,.0f} | open {len(port.positions)} | closed {len(port.closed)}", file=sys.stderr)

    last_day = all_days[-1]
    closes = {}
    for sym in port.positions.keys():
        o = signal_asof.get_ohlc(sym, last_day)
        if o is not None:
            closes[sym] = o["close"]
    port.force_close_all(last_day, closes)

    nifty_end = signal_asof.nifty_close(last_day) or nifty_start
    nifty_ret = (nifty_end - nifty_start) / nifty_start * 100 if nifty_start else 0

    trades = port.closed
    snaps = port.daily_snapshots
    final = snaps[-1]["total_value"] if snaps else cfg["starting_capital"]
    ret = (final - cfg["starting_capital"]) / cfg["starting_capital"] * 100
    n_w = sum(1 for t in trades if t.pnl_pct > 0)

    OUT = ROOT / "results"
    OUT.mkdir(exist_ok=True)
    from dataclasses import asdict
    (OUT / f"meanrev_{label}_trades.json").write_text(json.dumps([asdict(t) for t in trades], indent=2, default=str))
    (OUT / f"meanrev_{label}_summary.json").write_text(json.dumps({
        "trades": len(trades), "win_rate": n_w/len(trades)*100 if trades else 0,
        "total_return_pct": ret, "nifty_return_pct": nifty_ret,
        "alpha": ret - nifty_ret, "starting": cfg["starting_capital"], "final": final,
    }, indent=2))

    print(f"\n=== MEAN-REVERSION {label.upper()} ===")
    print(f"Trades:       {len(trades)}")
    print(f"Win rate:     {(n_w/len(trades)*100 if trades else 0):.1f}%")
    print(f"Total return: {ret:+.2f}%")
    print(f"Nifty:        {nifty_ret:+.2f}%")
    print(f"Alpha:        {ret - nifty_ret:+.2f}%")


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in PERIODS:
        print(f"Usage: {' | '.join(PERIODS.keys())}")
        sys.exit(1)
    label = sys.argv[1]
    run(*PERIODS[label], label)


if __name__ == "__main__":
    main()
