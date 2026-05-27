#!/usr/bin/env python3
"""
backtest_runner.py — Daily replay loop.

Now uses:
  - prime_benchmark() to load Nifty 50 (with NIFTYBEES fallback) BEFORE individual symbols
  - compute_regime_asof() to tag every entry with bull/bear/sideways
  - constituents_asof() to query the active universe per date (Phase B will populate)
"""
import sys
from datetime import date, timedelta
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from backtest.engine import signal_asof, gates
from backtest.engine.portfolio import PaperPortfolio


def previous_trading_day(d: date, all_days: list[date]) -> date | None:
    earlier = [x for x in all_days if x < d]
    return earlier[-1] if earlier else None


def run_backtest(cfg: dict, universe: list[str], sector_map: dict[str, str]) -> dict:
    start = date.fromisoformat(cfg["start_date"])
    end   = date.fromisoformat(cfg["end_date"])

    # 0. Apply configurable tier sizes (defaults: 70k/50k/30k)
    rules_cfg = cfg["rules"]
    signal_asof.set_tier_sizes(
        rules_cfg.get("size_tier_high", 70_000),
        rules_cfg.get("size_tier_mid",  50_000),
        rules_cfg.get("size_tier_low",  30_000),
    )
    print(f"Tier sizes: high={rules_cfg.get('size_tier_high',70_000)} "
          f"mid={rules_cfg.get('size_tier_mid',50_000)} "
          f"low={rules_cfg.get('size_tier_low',30_000)}", file=sys.stderr)

    # 1. Prime benchmark FIRST (separate from individual symbols)
    bench_ok = signal_asof.prime_benchmark(start, end)
    if not bench_ok:
        print("  WARNING: benchmark unavailable; alpha will not be computed", file=sys.stderr)

    # 2. Prime individual symbols (filtered through ticker aliases)
    signal_asof.prime_cache(universe, start, end, lookback_days=400)

    # 3. Load macro gate data
    DATA = Path(__file__).resolve().parents[1] / "data"
    gates.load_vix(DATA / "historical_vix.csv")
    gates.load_fii(DATA / "historical_fii.csv")
    print(f"VIX rows: {len(gates.VIX_CACHE)} | FII rows: {len(gates.FII_CACHE)}",
          file=sys.stderr)

    all_days = signal_asof.trading_days(start, end)
    if not all_days:
        raise RuntimeError("No trading days in window")
    print(f"Replay window: {all_days[0]} -> {all_days[-1]} ({len(all_days)} trading days)",
          file=sys.stderr)

    port = PaperPortfolio(starting_cash=cfg["starting_capital"], config=cfg)
    rules = cfg["rules"]
    nifty_start = signal_asof.nifty_close(all_days[0]) or 0.0
    skip_log: list[dict] = []

    for i, d in enumerate(all_days):
        prev = previous_trading_day(d, all_days)
        if prev is None:
            port.snapshot(d, port.cash, signal_asof.nifty_close(d))
            continue

        # Process open positions FIRST (today's stops/partials)
        ohlc_open = {}
        for sym in list(port.positions.keys()):
            o = signal_asof.get_ohlc(sym, d)
            if o is not None:
                ohlc_open[sym] = o
        port.process_day(d, ohlc_open)

        # Macro gates for new entries
        vix_ok, vix_msg = gates.gate_5_vix(prev, rules["vix_max"])
        fii_ok, fii_msg = gates.gate_7_fii(prev, rules["fii_min_cr"])

        if not vix_ok:
            skip_log.append({"date": d.isoformat(), "reason": f"macro_skip: {vix_msg}"})
        elif not fii_ok:
            skip_log.append({"date": d.isoformat(), "reason": f"macro_skip: {fii_msg}"})
        else:
            # Resolve as-of constituents (Phase B will use quarterly historicals)
            active_universe = signal_asof.constituents_asof(d, universe)

            # Tag this day's regime
            regime = signal_asof.compute_regime_asof(prev)

            # Score the active universe as-of prev day's close
            scored = []
            for sym in active_universe:
                r = signal_asof.score_symbol_asof(sym, prev)
                if r is None or r.get("signal") != "BUY":
                    continue
                if r["confidence"] < rules["min_score"]:
                    continue
                scored.append(r)
            scored.sort(key=lambda x: x["confidence"], reverse=True)
            top10 = scored[:10]

            for cand in top10:
                sym = cand["symbol"]
                if sym in port.positions:
                    continue
                ohlc_today = signal_asof.get_ohlc(sym, d)
                if ohlc_today is None:
                    skip_log.append({"date": d.isoformat(), "symbol": sym, "reason": "no_ohlc_today"})
                    continue
                prev_ohlc = signal_asof.get_ohlc(sym, prev)
                if prev_ohlc is None:
                    continue

                gap_ok, gap_msg = gates.gate_4_circuit(prev_ohlc["close"], ohlc_today["open"],
                                                       rules["circuit_gap_pct"])
                if not gap_ok:
                    skip_log.append({"date": d.isoformat(), "symbol": sym,
                                     "reason": f"gate4_{gap_msg}"})
                    continue

                sector = cand["sector"]
                if port.sector_count(sector) >= rules["sector_max_open"]:
                    skip_log.append({"date": d.isoformat(), "symbol": sym,
                                     "reason": f"gate9_sector_{sector}_full"})
                    continue

                size  = cand["suggested_position_size"]
                entry = ohlc_today["open"]
                qty   = int(size // entry)
                if qty < 1 or qty * entry > port.cash:
                    skip_log.append({"date": d.isoformat(), "symbol": sym,
                                     "reason": "gate6_insufficient_cash_or_qty"})
                    continue

                ok = port.enter(sym, sector, qty, entry, cand["confidence"], d, regime=regime)
                if not ok:
                    skip_log.append({"date": d.isoformat(), "symbol": sym,
                                     "reason": "enter_failed"})
                    continue

                # Same-day stop check on newly opened position
                port.process_day(d, {sym: ohlc_today})

        # Mark-to-market + snapshot
        mtm = {}
        for sym in port.positions.keys():
            o = signal_asof.get_ohlc(sym, d)
            if o is not None:
                mtm[sym] = o["close"]
        total_value = port.mark_to_market(d, mtm)
        port.snapshot(d, total_value, signal_asof.nifty_close(d))

        if (i + 1) % 20 == 0:
            print(f"  [{d}] {i+1}/{len(all_days)} | value: Rs {total_value:,.0f} | "
                  f"open: {len(port.positions)} | closed: {len(port.closed)}",
                  file=sys.stderr)

    last_day = all_days[-1]
    last_closes = {}
    for sym in port.positions.keys():
        o = signal_asof.get_ohlc(sym, last_day)
        if o is not None:
            last_closes[sym] = o["close"]
    port.force_close_all(last_day, last_closes)

    nifty_end = signal_asof.nifty_close(last_day) or nifty_start
    return {
        "config":            cfg,
        "portfolio":         port.to_dict(),
        "skip_log_summary":  _summarize_skips(skip_log),
        "skip_log_full":     skip_log,  # FULL per-event skip records for verification
        "nifty_start":       nifty_start,
        "nifty_end":         nifty_end,
        "nifty_return_pct":  (nifty_end - nifty_start) / nifty_start * 100 if nifty_start else 0.0,
        "trading_days":      len(all_days),
    }


def _summarize_skips(skip_log: list[dict]) -> dict:
    from collections import Counter
    reasons = Counter()
    for s in skip_log:
        r = s.get("reason", "unknown")
        if r.startswith("gate4_"):     reasons["gate4_circuit_gap"] += 1
        elif r.startswith("gate9_"):   reasons["gate9_sector_full"] += 1
        elif r.startswith("macro_skip"): reasons["macro_skip_vix_or_fii"] += 1
        else:                          reasons[r] += 1
    return dict(reasons)
