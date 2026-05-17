#!/usr/bin/env python3
"""
record_trade.py — Log structured trade entries and exits to memory/trade-outcomes.json

Usage:
  # When a BUY executes (market-open routine):
  python scripts/record_trade.py entry SYMBOL SECTOR GRU_CONF VIX FII_FLOW REGIME ENTRY_PRICE QTY CATALYST_TYPE

  # When a position is closed (midday or EOD routine):
  python scripts/record_trade.py exit SYMBOL EXIT_PRICE EXIT_REASON

  # Sell half a position at +15% (midday partial exit):
  python scripts/record_trade.py partial_exit SYMBOL EXIT_PRICE QTY_SOLD

  EXIT_REASON options:   hard_stop | trailing_stop | thesis_broken | target | manual
  REGIME options:        bull | bear | sideways | unknown
  CATALYST_TYPE options: earnings | upgrade | breakout | sector_tailwind | technical | other

Examples:
  python scripts/record_trade.py entry RELIANCE "Energy" 0.72 16.2 -800 bull 2500.50 40 breakout
  python scripts/record_trade.py exit RELIANCE 2325.00 hard_stop
  python scripts/record_trade.py partial_exit RELIANCE 2750.00 20
"""

import json, sys
from datetime import date, datetime
from pathlib import Path

OUTCOMES_FILE = Path(__file__).parent.parent / "memory" / "trade-outcomes.json"


def load() -> dict:
    if OUTCOMES_FILE.exists():
        return json.loads(OUTCOMES_FILE.read_text())
    return {"trades": [], "metadata": {"total_closed": 0, "analyzer_min_trades": 20}}


def save(data: dict):
    data["metadata"]["last_updated"] = datetime.now().isoformat()
    data["metadata"]["total_closed"] = sum(
        1 for t in data["trades"] if t.get("exit_date") is not None
    )
    OUTCOMES_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTCOMES_FILE.write_text(json.dumps(data, indent=2))


def cmd_entry(args):
    if len(args) < 8:
        print(
            "Usage: record_trade.py entry SYMBOL SECTOR GRU_CONF VIX FII_FLOW REGIME ENTRY_PRICE QTY [CATALYST_TYPE]",
            file=sys.stderr,
        )
        sys.exit(1)

    symbol        = args[0].upper().replace(".NS", "")
    sector        = args[1]
    gru_conf      = float(args[2])
    vix           = float(args[3])
    fii_flow      = float(args[4])
    regime        = args[5]
    entry_price   = float(args[6])
    qty           = int(args[7])
    catalyst_type = args[8] if len(args) > 8 else "other"

    data = load()

    for t in data["trades"]:
        if t["symbol"] == symbol and t["exit_date"] is None:
            print(
                f"WARNING: open entry already exists for {symbol} — skipping duplicate",
                file=sys.stderr,
            )
            return

    trade = {
        "trade_id":          f"{symbol}-{date.today().isoformat()}",
        "symbol":            symbol,
        "sector":            sector,
        "catalyst_type":     catalyst_type,
        "entry_date":        date.today().isoformat(),
        "entry_price":       round(entry_price, 2),
        "qty":               qty,
        "gru_confidence":    round(gru_conf, 4),
        "vix_at_entry":      round(vix, 2),
        "fii_flow_at_entry": round(fii_flow, 0),
        "market_regime":     regime,
        "partial_exits":     [],
        "exit_date":         None,
        "exit_price":        None,
        "pnl_abs":           None,
        "pnl_pct":           None,
        "exit_reason":       None,
        "days_held":         None,
    }

    data["trades"].append(trade)
    save(data)
    print(json.dumps({
        "status":      "ENTRY_RECORDED",
        "trade_id":    trade["trade_id"],
        "symbol":      symbol,
        "entry_price": entry_price,
        "qty":         qty,
    }))


def cmd_exit(args):
    if len(args) < 3:
        print(
            "Usage: record_trade.py exit SYMBOL EXIT_PRICE EXIT_REASON",
            file=sys.stderr,
        )
        sys.exit(1)

    symbol      = args[0].upper().replace(".NS", "")
    exit_price  = float(args[1])
    exit_reason = args[2]

    data = load()

    trade = next(
        (t for t in data["trades"] if t["symbol"] == symbol and t["exit_date"] is None),
        None,
    )

    if trade is None:
        print(
            f"WARNING: no open entry found for {symbol} — exit not recorded",
            file=sys.stderr,
        )
        sys.exit(0)  # exit 0 so the calling routine does not crash

    pnl_abs   = (exit_price - trade["entry_price"]) * trade["qty"]
    pnl_pct   = (exit_price - trade["entry_price"]) / trade["entry_price"] * 100
    days_held = (date.today() - date.fromisoformat(trade["entry_date"])).days

    trade["exit_date"]   = date.today().isoformat()
    trade["exit_price"]  = round(exit_price, 2)
    trade["pnl_abs"]     = round(pnl_abs, 2)
    trade["pnl_pct"]     = round(pnl_pct, 2)
    trade["exit_reason"] = exit_reason
    trade["days_held"]   = days_held

    save(data)
    print(json.dumps({
        "status":      "EXIT_RECORDED",
        "symbol":      symbol,
        "exit_price":  exit_price,
        "pnl_abs":     round(pnl_abs, 2),
        "pnl_pct":     round(pnl_pct, 2),
        "exit_reason": exit_reason,
        "days_held":   days_held,
    }))


def cmd_partial_exit(args):
    if len(args) < 3:
        print(
            "Usage: record_trade.py partial_exit SYMBOL EXIT_PRICE QTY_SOLD",
            file=sys.stderr,
        )
        sys.exit(1)

    symbol     = args[0].upper().replace(".NS", "")
    exit_price = float(args[1])
    qty_sold   = int(args[2])

    data = load()

    trade = next(
        (t for t in data["trades"] if t["symbol"] == symbol and t["exit_date"] is None),
        None,
    )

    if trade is None:
        print(
            f"WARNING: no open entry found for {symbol} — partial exit not recorded",
            file=sys.stderr,
        )
        sys.exit(0)

    if trade["qty"] < qty_sold:
        print(
            f"WARNING: qty_sold ({qty_sold}) exceeds open qty ({trade['qty']}) — capping",
            file=sys.stderr,
        )
        qty_sold = trade["qty"]

    pnl_abs = (exit_price - trade["entry_price"]) * qty_sold
    pnl_pct = (exit_price - trade["entry_price"]) / trade["entry_price"] * 100

    if "partial_exits" not in trade:
        trade["partial_exits"] = []

    trade["partial_exits"].append({
        "date":    date.today().isoformat(),
        "price":   round(exit_price, 2),
        "qty":     qty_sold,
        "pnl_abs": round(pnl_abs, 2),
        "pnl_pct": round(pnl_pct, 2),
    })
    trade["qty"] -= qty_sold

    save(data)
    print(json.dumps({
        "status":       "PARTIAL_EXIT_RECORDED",
        "symbol":       symbol,
        "qty_sold":     qty_sold,
        "qty_remaining": trade["qty"],
        "exit_price":   round(exit_price, 2),
        "pnl_abs":      round(pnl_abs, 2),
        "pnl_pct":      round(pnl_pct, 2),
    }))


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(0)

    cmd = args[0].lower()
    if cmd == "entry":
        cmd_entry(args[1:])
    elif cmd == "exit":
        cmd_exit(args[1:])
    elif cmd == "partial_exit":
        cmd_partial_exit(args[1:])
    else:
        print(f"Unknown command: {cmd}", file=sys.stderr)
        sys.exit(1)
