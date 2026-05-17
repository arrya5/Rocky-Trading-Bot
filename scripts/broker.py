#!/usr/bin/env python3
"""
broker.py — Upstox API v2 wrapper for the Indian AI Trading Bot

Usage:
  python broker.py account                          # cash, margin, net value
  python broker.py positions                        # intraday/short-term positions
  python broker.py holdings                         # delivery holdings
  python broker.py quote RELIANCE [TCS INFY ...]   # LTP for symbols
  python broker.py orders                           # all orders today
  python broker.py order '{"symbol":"RELIANCE","qty":10,"side":"buy","type":"market"}'
  python broker.py cancel <order_id>
  python broker.py cancel-all
  python broker.py close RELIANCE                  # market sell open position
  python broker.py close-all                       # market sell all positions

Environment variables (set in .env or shell):
  UPSTOX_ACCESS_TOKEN   — daily access token from auth.py
  UPSTOX_BASE_URL       — default: https://api.upstox.com/v2 (live)
                          paper:   https://sandbox-api.upstox.com/v2
  PAPER_TRADING         — "true" (default) uses local paper portfolio
"""

import os, sys, json, requests
from datetime import date, datetime
from pathlib import Path

# ── Config ────────────────────────────────────────────────────────────────────

PAPER   = os.getenv("PAPER_TRADING", "true").lower() == "true"
TOKEN   = os.getenv("UPSTOX_ACCESS_TOKEN", "")
BASE    = os.getenv("UPSTOX_BASE_URL", "https://api.upstox.com/v2")

PAPER_FILE = Path(__file__).parent.parent / "memory" / "paper_portfolio.json"

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept":        "application/json",
    "Content-Type":  "application/json",
}

# ── Paper portfolio helpers ────────────────────────────────────────────────────

def load_paper() -> dict:
    if PAPER_FILE.exists():
        return json.loads(PAPER_FILE.read_text())
    return {"cash": 500000.0, "positions": {}, "orders": []}

def save_paper(p: dict):
    PAPER_FILE.parent.mkdir(parents=True, exist_ok=True)
    PAPER_FILE.write_text(json.dumps(p, indent=2))

# ── Live API helper ────────────────────────────────────────────────────────────

def api(method: str, path: str, **kwargs) -> dict | list:
    if not TOKEN:
        print("ERROR: UPSTOX_ACCESS_TOKEN not set. Run: python scripts/auth.py", file=sys.stderr)
        sys.exit(1)
    r = requests.request(method, f"{BASE}{path}", headers=HEADERS, timeout=10, **kwargs)
    if r.status_code not in (200, 201):
        print(f"ERROR {r.status_code}: {r.text}", file=sys.stderr)
        sys.exit(1)
    body = r.json()
    return body.get("data", body)

def instrument_key(symbol: str) -> str:
    return f"NSE_EQ|{symbol.upper().replace('.NS', '')}"

# ── Commands ──────────────────────────────────────────────────────────────────

def cmd_account():
    if PAPER:
        p = load_paper()
        pos_value = sum(
            v["qty"] * v.get("ltp", v["avg_price"])
            for v in p["positions"].values()
        )
        print(json.dumps({
            "mode":            "PAPER",
            "cash":            round(p["cash"], 2),
            "positions_value": round(pos_value, 2),
            "total_value":     round(p["cash"] + pos_value, 2),
            "as_of":           datetime.now().isoformat(),
        }, indent=2))
        return

    data    = api("GET", "/user/fund-and-margin")
    equity  = data.get("equity", {})
    print(json.dumps({
        "available_cash":  equity.get("available_margin", 0),
        "used_margin":     equity.get("used_margin", 0),
        "total_value":     equity.get("net", 0),
        "as_of":           datetime.now().isoformat(),
    }, indent=2))


def cmd_positions():
    if PAPER:
        p   = load_paper()
        out = []
        for sym, v in p["positions"].items():
            ltp = v.get("ltp", v["avg_price"])
            pnl = (ltp - v["avg_price"]) * v["qty"]
            pct = round((ltp - v["avg_price"]) / v["avg_price"] * 100, 2)
            out.append({
                "symbol":        sym,
                "qty":           v["qty"],
                "avg_price":     v["avg_price"],
                "ltp":           ltp,
                "pnl":           round(pnl, 2),
                "day_change_pct": pct,
            })
        print(json.dumps(out, indent=2))
        return

    data = api("GET", "/portfolio/short-term-positions")
    out  = []
    for p in (data if isinstance(data, list) else []):
        avg = p.get("average_price", 1) or 1
        ltp = p.get("last_price", avg)
        out.append({
            "symbol":         p.get("tradingsymbol"),
            "qty":            p.get("quantity"),
            "avg_price":      avg,
            "ltp":            ltp,
            "pnl":            round(p.get("pnl", 0), 2),
            "day_change_pct": round((ltp - avg) / avg * 100, 2),
        })
    print(json.dumps(out, indent=2))


def cmd_holdings():
    if PAPER:
        print(json.dumps({"mode": "PAPER", "holdings": []}, indent=2))
        return
    data = api("GET", "/portfolio/long-term-holdings")
    print(json.dumps(data if isinstance(data, list) else [], indent=2))


def cmd_quote(symbols: list[str]):
    keys = ",".join(instrument_key(s) for s in symbols)
    data = api("GET", f"/market-quote/ltp?symbol={keys}")
    out  = {}
    for k, v in (data.items() if isinstance(data, dict) else {}.items()):
        sym       = k.split("|")[-1]
        out[sym]  = {"price": v.get("last_price"), "timestamp": datetime.now().isoformat()}

        if PAPER:
            port = load_paper()
            if sym in port["positions"]:
                port["positions"][sym]["ltp"] = v.get("last_price")
                save_paper(port)

    print(json.dumps(out, indent=2))


def cmd_orders():
    if PAPER:
        p = load_paper()
        print(json.dumps(p.get("orders", []), indent=2))
        return
    data   = api("GET", "/order/retrieve-all")
    orders = []
    for o in (data if isinstance(data, list) else []):
        orders.append({
            "order_id":  o.get("order_id"),
            "symbol":    o.get("tradingsymbol"),
            "side":      o.get("transaction_type"),
            "qty":       o.get("quantity"),
            "status":    o.get("status"),
            "price":     o.get("average_price") or o.get("price"),
            "placed_at": o.get("order_timestamp"),
        })
    print(json.dumps(orders, indent=2))


def cmd_order(raw: str):
    req    = json.loads(raw)
    symbol = req["symbol"].upper().replace(".NS", "")
    qty    = int(req["qty"])
    side   = req["side"].upper()       # BUY or SELL
    otype  = req.get("type", "market").upper()
    price  = float(req.get("price", 0))

    if PAPER:
        p     = load_paper()
        now   = datetime.now().isoformat()
        # Get LTP for paper cost calculation
        try:
            keys = instrument_key(symbol)
            data = api("GET", f"/market-quote/ltp?symbol={keys}")
            ltp  = list(data.values())[0].get("last_price", price) if data else price
        except Exception:
            ltp = price or 0

        exec_price = ltp if otype == "MARKET" else price

        if side == "BUY":
            cost = exec_price * qty
            if cost > p["cash"]:
                print(json.dumps({"status": "REJECTED", "reason": f"Insufficient cash: need ₹{cost:.0f}, have ₹{p['cash']:.0f}"}))
                return
            p["cash"] -= cost
            if symbol in p["positions"]:
                existing  = p["positions"][symbol]
                new_qty   = existing["qty"] + qty
                new_avg   = (existing["avg_price"] * existing["qty"] + exec_price * qty) / new_qty
                p["positions"][symbol] = {"qty": new_qty, "avg_price": round(new_avg, 2), "ltp": exec_price, "entered_at": existing["entered_at"]}
            else:
                p["positions"][symbol] = {"qty": qty, "avg_price": exec_price, "ltp": exec_price, "entered_at": date.today().isoformat()}

        elif side == "SELL":
            if symbol not in p["positions"] or p["positions"][symbol]["qty"] < qty:
                print(json.dumps({"status": "REJECTED", "reason": f"No position or insufficient qty in {symbol}"}))
                return
            proceeds = exec_price * qty
            stt      = round(proceeds * 0.001, 2)   # 0.1% STT on delivery sell
            p["cash"] += proceeds - stt
            p["positions"][symbol]["qty"] -= qty
            if p["positions"][symbol]["qty"] == 0:
                del p["positions"][symbol]

        order_id = f"PAPER-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        p["orders"].append({
            "order_id":   order_id,
            "symbol":     symbol,
            "side":       side,
            "qty":        qty,
            "price":      round(exec_price, 2),
            "type":       otype,
            "status":     "COMPLETE",
            "placed_at":  now,
        })
        save_paper(p)
        print(json.dumps({"status": "PAPER_COMPLETE", "order_id": order_id, "symbol": symbol, "side": side, "qty": qty, "exec_price": exec_price}))
        return

    body = {
        "quantity":          qty,
        "product":           req.get("product", "D"),
        "validity":          "DAY",
        "price":             price,
        "instrument_token":  instrument_key(symbol),
        "order_type":        "MARKET" if otype == "MARKET" else "LIMIT",
        "transaction_type":  side,
        "disclosed_quantity": 0,
        "trigger_price":     float(req.get("trigger_price", 0)),
        "is_amo":            False,
    }
    result = api("POST", "/order/place", json=body)
    print(json.dumps(result, indent=2))


def cmd_cancel(order_id: str):
    if PAPER:
        p = load_paper()
        for o in p["orders"]:
            if o["order_id"] == order_id:
                o["status"] = "CANCELLED"
        save_paper(p)
        print(json.dumps({"status": "PAPER_CANCELLED", "order_id": order_id}))
        return
    result = api("DELETE", f"/order/cancel?order_id={order_id}")
    print(json.dumps(result, indent=2))


def cmd_cancel_all():
    if PAPER:
        p = load_paper()
        cancelled = []
        for o in p["orders"]:
            if o["status"] not in ("COMPLETE", "CANCELLED", "REJECTED"):
                o["status"] = "CANCELLED"
                cancelled.append(o["order_id"])
        save_paper(p)
        print(json.dumps({"status": "PAPER_CANCEL_ALL", "cancelled": cancelled}))
        return
    data      = api("GET", "/order/retrieve-all")
    cancelled = []
    for o in (data if isinstance(data, list) else []):
        if o.get("status") in ("open", "trigger pending", "pending"):
            api("DELETE", f"/order/cancel?order_id={o['order_id']}")
            cancelled.append(o["order_id"])
    print(json.dumps({"cancelled": cancelled}))


def cmd_close(symbol: str):
    symbol = symbol.upper().replace(".NS", "")
    if PAPER:
        p = load_paper()
        if symbol not in p["positions"] or p["positions"][symbol]["qty"] == 0:
            print(json.dumps({"status": "NO_POSITION", "symbol": symbol}))
            return
        qty = p["positions"][symbol]["qty"]
        cmd_order(json.dumps({"symbol": symbol, "qty": qty, "side": "sell", "type": "market"}))
        return
    data = api("GET", "/portfolio/short-term-positions")
    for pos in (data if isinstance(data, list) else []):
        if pos.get("tradingsymbol", "").upper() == symbol and pos.get("quantity", 0) > 0:
            cmd_order(json.dumps({"symbol": symbol, "qty": pos["quantity"], "side": "sell", "type": "market"}))
            return
    print(json.dumps({"status": "NO_POSITION", "symbol": symbol}))


def cmd_close_all():
    if PAPER:
        p      = load_paper()
        closed = list(p["positions"].keys())
        for sym in closed:
            cmd_close(sym)
        return
    data   = api("GET", "/portfolio/short-term-positions")
    closed = []
    for pos in (data if isinstance(data, list) else []):
        if pos.get("quantity", 0) > 0:
            sym = pos["tradingsymbol"]
            cmd_order(json.dumps({"symbol": sym, "qty": pos["quantity"], "side": "sell", "type": "market"}))
            closed.append(sym)
    print(json.dumps({"closed": closed}))


# ── Dispatch ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(0)

    cmd = args[0].lower()

    match cmd:
        case "account":    cmd_account()
        case "positions":  cmd_positions()
        case "holdings":   cmd_holdings()
        case "quote":      cmd_quote(args[1:])
        case "orders":     cmd_orders()
        case "order":      cmd_order(args[1])
        case "cancel":     cmd_cancel(args[1])
        case "cancel-all": cmd_cancel_all()
        case "close":      cmd_close(args[1])
        case "close-all":  cmd_close_all()
        case _:
            print(f"Unknown command: {cmd}", file=sys.stderr)
            print(__doc__)
            sys.exit(1)
