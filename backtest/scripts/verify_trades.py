#!/usr/bin/env python3
"""
verify_trades.py — Independent verification of POC trade data.

Three layers of verification:

  1. PRICE VERIFICATION
     For each trade event (entry, partial, exit), re-fetch yfinance OHLC for that
     symbol/date and check the simulated fill price was plausible:
       - ENTRY: price ≈ that day's Open
       - PARTIAL (+15% target): yf High that day must be >= partial trigger
       - EXIT hard_stop / trailing_stop: yf Low must be <= stop price (or open <= stop for gap-down)
       - EXIT open_at_end: price = last day's Close

  2. RULES AUDIT
     Walk the trade timeline day-by-day and verify the constraints actually held:
       - Sector cap (Gate 9): no more than 2 positions in same sector at any time
       - Cash never went negative (per snapshot)
       - No re-entry while position is open

  3. SKIPPED-CANDIDATE SPOT-CHECK
     Sample N candidates that were rejected (e.g. for gate6_insufficient_cash)
     and re-run score_symbol_asof to confirm they were genuinely valid BUY signals
     at that date (right score, would have passed pre-filters).

Outputs:
  backtest/results/<base>_verification.md — human-readable summary + flagged rows
  backtest/results/<base>_verification.csv — full row-per-event for Excel review

Usage:
  python backtest/scripts/verify_trades.py backtest/results/poc_trades.json
  python backtest/scripts/verify_trades.py backtest/results/poc_smaller_trades.json
"""
import csv, json, sys, warnings
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
sys.path.insert(0, str(REPO))

from backtest.engine import signal_asof

TOLERANCE_PCT = 0.5  # match if simulated within 0.5% of yfinance OHLC


# ── PRICE VERIFICATION ───────────────────────────────────────────────────────

def _check_entry(sim_price: float, ohlc: dict) -> tuple[str, str]:
    """Entry should match yf Open."""
    pct_diff = abs(sim_price - ohlc["open"]) / ohlc["open"] * 100
    if pct_diff <= TOLERANCE_PCT:
        return "PASS", f"entry={sim_price:.2f} vs yf_open={ohlc['open']:.2f} ({pct_diff:.2f}% off)"
    return "FAIL", f"entry={sim_price:.2f} differs from yf_open={ohlc['open']:.2f} by {pct_diff:.2f}%"


def _check_partial(sim_price: float, ohlc: dict) -> tuple[str, str]:
    """Partial fires at entry*1.15. The day's High must reach that level."""
    if ohlc["high"] >= sim_price * (1 - TOLERANCE_PCT/100):
        return "PASS", f"partial={sim_price:.2f}, yf_high={ohlc['high']:.2f} (reachable)"
    return "FAIL", f"partial={sim_price:.2f} but yf_high={ohlc['high']:.2f} did not reach target"


def _check_exit_stop(sim_price: float, ohlc: dict) -> tuple[str, str]:
    """Hard/trailing stop. Either yf Low <= stop (intraday hit) OR yf Open <= stop (gap-down)."""
    if ohlc["low"] <= sim_price * (1 + TOLERANCE_PCT/100):
        return "PASS", f"stop={sim_price:.2f}, yf_low={ohlc['low']:.2f} (low <= stop, stop fired)"
    if ohlc["open"] <= sim_price * (1 + TOLERANCE_PCT/100):
        return "PASS", f"stop={sim_price:.2f}, yf_open={ohlc['open']:.2f} (gap-down fill at open)"
    return "FAIL", f"stop={sim_price:.2f} but yf_low={ohlc['low']:.2f} > stop (stop shouldn't fire)"


def _check_exit_end(sim_price: float, ohlc: dict) -> tuple[str, str]:
    """Force-closed at window end. Price should equal that day's Close."""
    pct_diff = abs(sim_price - ohlc["close"]) / ohlc["close"] * 100
    if pct_diff <= TOLERANCE_PCT:
        return "PASS", f"close={sim_price:.2f} vs yf_close={ohlc['close']:.2f} ({pct_diff:.2f}% off)"
    return "FAIL", f"close={sim_price:.2f} differs from yf_close={ohlc['close']:.2f}"


def verify_trade_prices(trade: dict, trade_no: int) -> list[dict]:
    """Returns one row per event in the trade lifecycle (entry, optional partial, exit)."""
    sym = trade["symbol"]
    rows: list[dict] = []

    # ENTRY
    d = date.fromisoformat(trade["entry_date"])
    o = signal_asof.get_ohlc(sym, d)
    if o is None:
        rows.append({
            "trade_no": trade_no, "symbol": sym, "event": "ENTRY",
            "date": trade["entry_date"], "sim_price": trade["entry_price"],
            "yf_open": None, "yf_high": None, "yf_low": None, "yf_close": None,
            "status": "NO_DATA", "detail": "yfinance returned no OHLC for this date",
        })
    else:
        st, msg = _check_entry(trade["entry_price"], o)
        rows.append({
            "trade_no": trade_no, "symbol": sym, "event": "ENTRY",
            "date": trade["entry_date"], "sim_price": trade["entry_price"],
            "yf_open": o["open"], "yf_high": o["high"], "yf_low": o["low"], "yf_close": o["close"],
            "status": st, "detail": msg,
        })

    # PARTIAL (optional)
    if trade.get("partial_date") and trade.get("partial_price"):
        d = date.fromisoformat(trade["partial_date"])
        o = signal_asof.get_ohlc(sym, d)
        if o is None:
            rows.append({
                "trade_no": trade_no, "symbol": sym, "event": "PARTIAL",
                "date": trade["partial_date"], "sim_price": trade["partial_price"],
                "yf_open": None, "yf_high": None, "yf_low": None, "yf_close": None,
                "status": "NO_DATA", "detail": "no yfinance OHLC for partial date",
            })
        else:
            st, msg = _check_partial(trade["partial_price"], o)
            rows.append({
                "trade_no": trade_no, "symbol": sym, "event": "PARTIAL",
                "date": trade["partial_date"], "sim_price": trade["partial_price"],
                "yf_open": o["open"], "yf_high": o["high"], "yf_low": o["low"], "yf_close": o["close"],
                "status": st, "detail": msg,
            })

    # EXIT
    d = date.fromisoformat(trade["exit_date"])
    o = signal_asof.get_ohlc(sym, d)
    if o is None:
        rows.append({
            "trade_no": trade_no, "symbol": sym, "event": "EXIT",
            "date": trade["exit_date"], "sim_price": trade["exit_price"],
            "yf_open": None, "yf_high": None, "yf_low": None, "yf_close": None,
            "status": "NO_DATA", "detail": "no yfinance OHLC for exit date",
        })
    else:
        reason = trade.get("exit_reason", "")
        if reason in ("hard_stop", "trailing_stop", "partial_then_stop"):
            st, msg = _check_exit_stop(trade["exit_price"], o)
        elif reason == "open_at_end":
            st, msg = _check_exit_end(trade["exit_price"], o)
        else:
            st, msg = "UNKNOWN_REASON", reason
        rows.append({
            "trade_no": trade_no, "symbol": sym, "event": f"EXIT ({reason})",
            "date": trade["exit_date"], "sim_price": trade["exit_price"],
            "yf_open": o["open"], "yf_high": o["high"], "yf_low": o["low"], "yf_close": o["close"],
            "status": st, "detail": msg,
        })

    return rows


# ── RULES AUDIT ──────────────────────────────────────────────────────────────

def rules_audit(trades: list[dict], snapshots: list[dict]) -> dict:
    """
    Walk timeline event-by-event and verify constraints:
      - Sector cap: at most 2 simultaneous positions per sector
      - Cash never negative (from snapshots)
      - No re-entry while position is open (sym already in open set)
    Returns dict with pass/fail per check + list of violations.
    """
    events = []
    for i, t in enumerate(trades, 1):
        events.append((t["entry_date"], "ENTER", i, t["symbol"], t["sector"]))
        events.append((t["exit_date"],  "EXIT",  i, t["symbol"], t["sector"]))
    events.sort(key=lambda e: (e[0], e[1] == "ENTER"))  # exits first on same date

    open_positions: dict[str, str] = {}  # symbol -> sector
    sector_counts = defaultdict(int)
    sector_cap_violations = []
    duplicate_entry_violations = []

    for date_str, kind, i, sym, sec in events:
        if kind == "ENTER":
            if sym in open_positions:
                duplicate_entry_violations.append(
                    f"Trade #{i}: re-entered {sym} on {date_str} while still open"
                )
            else:
                open_positions[sym] = sec
                sector_counts[sec] += 1
                if sector_counts[sec] > 2:
                    sector_cap_violations.append(
                        f"{date_str}: Trade #{i} entered {sym} bringing {sec} sector to {sector_counts[sec]} open"
                    )
        else:  # EXIT
            if sym in open_positions:
                sector_counts[open_positions[sym]] -= 1
                del open_positions[sym]

    # Cash check
    min_cash = min((s["cash"] for s in snapshots), default=0)
    cash_violations = [
        f"{s['date']}: cash = Rs {s['cash']:,.2f}" for s in snapshots if s["cash"] < 0
    ]

    return {
        "sector_cap": {
            "pass": len(sector_cap_violations) == 0,
            "violations": sector_cap_violations,
        },
        "duplicate_entry": {
            "pass": len(duplicate_entry_violations) == 0,
            "violations": duplicate_entry_violations,
        },
        "cash_non_negative": {
            "pass": min_cash >= 0,
            "min_cash": min_cash,
            "violations": cash_violations[:10],
        },
    }


# ── SKIPPED-CANDIDATE SPOT-CHECK ─────────────────────────────────────────────

def skipped_spot_check(skip_log: list[dict], n_samples: int = 10) -> list[dict]:
    """
    Pick N skip events of reason 'gate6_insufficient_cash_or_qty', re-score the
    symbol AS-OF (date - 1 trading day), confirm it would have been a valid BUY.
    Returns one row per checked skip with verification result.
    """
    import random
    cash_skips = [s for s in skip_log if "gate6" in s.get("reason", "")]
    if not cash_skips:
        return []

    random.seed(42)
    sample = random.sample(cash_skips, min(n_samples, len(cash_skips)))
    results: list[dict] = []

    for s in sample:
        sym = s.get("symbol")
        d_str = s.get("date")
        if not (sym and d_str):
            continue
        d = date.fromisoformat(d_str)
        # Re-score as-of yesterday (signal uses prev day's close)
        prev_days = [(d.replace(day=d.day - x) if d.day > x else None) for x in range(1, 5)]
        # Just walk back through cached days
        full = signal_asof._CACHE.get(sym)
        if full is None:
            results.append({
                "symbol": sym, "date": d_str, "status": "NO_DATA",
                "detail": "symbol not in price cache",
            })
            continue
        # Find prev trading day (last date in cache strictly before d)
        prev_rows = full[full.index.date < d]
        if prev_rows.empty:
            results.append({
                "symbol": sym, "date": d_str, "status": "NO_DATA",
                "detail": "no prior trading day in cache",
            })
            continue
        prev_date = prev_rows.index[-1].date()
        r = signal_asof.score_symbol_asof(sym, prev_date)
        if r is None:
            results.append({
                "symbol": sym, "date": d_str, "status": "FAIL",
                "detail": "score_symbol_asof returned None",
            })
            continue
        if r.get("signal") == "BUY" and r.get("confidence", 0) >= 40:
            results.append({
                "symbol": sym, "date": d_str, "status": "PASS",
                "detail": f"re-scored {prev_date} -> BUY {r['confidence']:.0f}/100 "
                          f"(sector {r['sector']}, suggested size Rs {r['suggested_position_size']:,})",
            })
        else:
            results.append({
                "symbol": sym, "date": d_str, "status": "FAIL",
                "detail": f"re-scored {prev_date} -> signal={r.get('signal')} "
                          f"confidence={r.get('confidence', 0):.0f}",
            })

    return results


# ── OUTPUT GENERATION ────────────────────────────────────────────────────────

def write_markdown(price_rows: list[dict], rules: dict, skip_rows: list[dict],
                   trades: list[dict], base: str, out_path: Path) -> None:
    n_total = len(price_rows)
    n_pass  = sum(1 for r in price_rows if r["status"] == "PASS")
    n_fail  = sum(1 for r in price_rows if r["status"] == "FAIL")
    n_nodata = sum(1 for r in price_rows if r["status"] == "NO_DATA")

    L = []
    add = L.append
    add(f"# Trade Verification — `{base}`")
    add(f"")
    add(f"_Generated: {datetime.now().isoformat(timespec='seconds')}_")
    add(f"")
    add(f"## Summary")
    add(f"")
    add(f"- **Trades audited**: {len(trades)}")
    add(f"- **Total events checked**: {n_total} (entries + partials + exits)")
    add(f"- **PASS**: {n_pass} ({n_pass/n_total*100 if n_total else 0:.1f}%)")
    add(f"- **FAIL**: {n_fail}")
    add(f"- **NO_DATA**: {n_nodata}")
    add(f"")
    add(f"## Rules audit")
    add(f"")
    sc = rules["sector_cap"]
    de = rules["duplicate_entry"]
    cn = rules["cash_non_negative"]
    add(f"- **Sector cap (≤2 per sector)**: {'PASS' if sc['pass'] else 'FAIL'}")
    if not sc["pass"]:
        for v in sc["violations"][:10]:
            add(f"  - {v}")
    add(f"- **No duplicate entries while open**: {'PASS' if de['pass'] else 'FAIL'}")
    if not de["pass"]:
        for v in de["violations"][:10]:
            add(f"  - {v}")
    add(f"- **Cash never negative**: {'PASS' if cn['pass'] else 'FAIL'} (min cash: Rs {cn['min_cash']:,.2f})")
    if not cn["pass"]:
        for v in cn["violations"][:5]:
            add(f"  - {v}")
    add(f"")
    add(f"## Skipped-candidate spot-check")
    add(f"")
    if skip_rows:
        n_skip_pass = sum(1 for r in skip_rows if r["status"] == "PASS")
        add(f"Sampled {len(skip_rows)} 'insufficient cash' skips and re-scored each. "
            f"**{n_skip_pass}/{len(skip_rows)} confirmed as valid BUY signals.**")
        add(f"")
        add(f"| Symbol | Skip date | Re-score result |")
        add(f"|---|---|---|")
        for r in skip_rows:
            add(f"| {r['symbol']} | {r['date']} | {r['status']}: {r['detail']} |")
    else:
        add(f"_No skip-log events available (or skip log empty)._")
    add(f"")
    add(f"## Price verification — all events")
    add(f"")
    add(f"| # | Symbol | Event | Date | Sim Price | yf Open | yf High | yf Low | yf Close | Status |")
    add(f"|---|---|---|---|---|---|---|---|---|---|")
    for r in price_rows:
        sp = f"Rs {r['sim_price']:.2f}" if r["sim_price"] is not None else "—"
        ya = f"{r['yf_open']:.2f}"  if r["yf_open"] is not None else "—"
        yh = f"{r['yf_high']:.2f}"  if r["yf_high"] is not None else "—"
        yl = f"{r['yf_low']:.2f}"   if r["yf_low"]  is not None else "—"
        yc = f"{r['yf_close']:.2f}" if r["yf_close"] is not None else "—"
        add(f"| {r['trade_no']} | {r['symbol']} | {r['event']} | {r['date']} | {sp} | {ya} | {yh} | {yl} | {yc} | {r['status']} |")
    add(f"")
    add(f"## Failed events detail (if any)")
    add(f"")
    fails = [r for r in price_rows if r["status"] == "FAIL"]
    if not fails:
        add(f"_No failures._")
    else:
        for r in fails:
            add(f"- **#{r['trade_no']} {r['symbol']} {r['event']} on {r['date']}**: {r['detail']}")
    add(f"")
    add(f"## How to spot-check manually")
    add(f"")
    add(f"For any row above, open yfinance.com (or `yf.Ticker('SYMBOL.NS').history(...)`) for the listed date. ")
    add(f"Compare yf Open/High/Low/Close with the values shown here. If they match, the engine read real data correctly.")
    add(f"")

    out_path.write_text("\n".join(L), encoding="utf-8")
    print(f"Markdown -> {out_path}", file=sys.stderr)


def write_csv(price_rows: list[dict], out_path: Path) -> None:
    if not price_rows:
        return
    keys = ["trade_no", "symbol", "event", "date", "sim_price",
            "yf_open", "yf_high", "yf_low", "yf_close", "status", "detail"]
    with out_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        for r in price_rows:
            w.writerow({k: r.get(k) for k in keys})
    print(f"CSV -> {out_path}", file=sys.stderr)


# ── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print("Usage: python backtest/scripts/verify_trades.py backtest/results/<trades>.json",
              file=sys.stderr)
        sys.exit(1)

    trades_path = Path(sys.argv[1]).resolve()
    if not trades_path.exists():
        print(f"ERROR: {trades_path} not found", file=sys.stderr)
        sys.exit(1)

    trades = json.loads(trades_path.read_text())
    base = trades_path.stem  # e.g. "poc_trades" or "poc_smaller_trades"

    # Try to load matching snapshots and skip log
    results_dir = trades_path.parent
    snap_path = results_dir / f"{base.replace('_trades', '_snapshots').replace('trades','snapshots')}.json"
    skip_path = results_dir / f"{base.replace('_trades', '_skip_log').replace('trades','skip_log')}.json"

    # Try alternative naming
    if not snap_path.exists():
        snap_path = results_dir / "poc_daily_snapshots.json"
    if not skip_path.exists():
        skip_path = results_dir / "poc_skip_log.json"

    snapshots = json.loads(snap_path.read_text()) if snap_path.exists() else []
    skip_log  = json.loads(skip_path.read_text()) if skip_path.exists() else []

    print(f"Loaded {len(trades)} trades, {len(snapshots)} snapshots, {len(skip_log)} skip events",
          file=sys.stderr)

    # Need to prime price cache for verification (uses same parquet cache)
    if trades:
        first_date = min(date.fromisoformat(t["entry_date"]) for t in trades)
        last_date  = max(date.fromisoformat(t["exit_date"])  for t in trades)
        symbols = sorted({t["symbol"] for t in trades} | {s["symbol"] for s in skip_log if s.get("symbol")})
        print(f"Priming cache for {len(symbols)} symbols ({first_date} -> {last_date})...",
              file=sys.stderr)
        signal_asof.prime_cache(symbols, first_date, last_date, lookback_days=60)

    # 1. Price verification per event
    price_rows: list[dict] = []
    for i, t in enumerate(trades, 1):
        price_rows.extend(verify_trade_prices(t, i))

    # 2. Rules audit
    rules = rules_audit(trades, snapshots)

    # 3. Skipped-candidate spot-check
    skip_rows = skipped_spot_check(skip_log, n_samples=10)

    out_md  = results_dir / f"{base.replace('_trades', '')}_verification.md"
    out_csv = results_dir / f"{base.replace('_trades', '')}_verification.csv"
    write_markdown(price_rows, rules, skip_rows, trades, base, out_md)
    write_csv(price_rows, out_csv)

    # Stdout summary
    n_pass = sum(1 for r in price_rows if r["status"] == "PASS")
    n_fail = sum(1 for r in price_rows if r["status"] == "FAIL")
    n_nodata = sum(1 for r in price_rows if r["status"] == "NO_DATA")
    print(f"")
    print(f"=== Verification complete for {base} ===")
    print(f"Trades: {len(trades)}")
    print(f"Price events: {len(price_rows)}  PASS={n_pass}  FAIL={n_fail}  NO_DATA={n_nodata}")
    print(f"Rules audit: sector_cap={'PASS' if rules['sector_cap']['pass'] else 'FAIL'}  "
          f"dup_entry={'PASS' if rules['duplicate_entry']['pass'] else 'FAIL'}  "
          f"cash={'PASS' if rules['cash_non_negative']['pass'] else 'FAIL'}")
    print(f"Skipped spot-check: {sum(1 for r in skip_rows if r['status']=='PASS')}/{len(skip_rows)} valid signals confirmed")
    print(f"")
    print(f"See: {out_md}")
    print(f"See: {out_csv}")


if __name__ == "__main__":
    main()
