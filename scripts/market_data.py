#!/usr/bin/env python3
"""
market_data.py — Fetch NSE delivery % and Nifty Put-Call Ratio

Commands:
  python scripts/market_data.py delivery RELIANCE TCS INFY   # delivery % from NSE bhavcopy
  python scripts/market_data.py pcr                          # Nifty PCR from NSE F&O option chain

Delivery % interpretation:
  >= 60%: strong institutional interest
  40-60%: moderate
  < 40%:  weak institutional interest — note in research log

PCR interpretation:
  < 0.7:  euphoric market (too many calls vs puts — bearish contrarian signal)
  0.7-1.2: neutral
  > 1.2:  fearful market (too many puts — bullish contrarian signal)
"""

import json, sys, io, zipfile
from datetime import date, timedelta
from pathlib import Path


NSE_BHAVCOPY_URL = "https://nsearchives.nseindia.com/content/cm/BhavCopy_NSE_CM_0_0_0_{date}_F_0000.csv.zip"
NSE_OPTION_CHAIN_URL = "https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY"


def _nse_headers() -> dict:
    return {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Referer":    "https://www.nseindia.com/",
        "Accept":     "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
    }


def _get_session():
    import requests
    session = requests.Session()
    try:
        session.get("https://www.nseindia.com/", headers=_nse_headers(), timeout=10)
    except Exception:
        pass
    return session


def _latest_bhavcopy_date() -> str:
    """Walk back up to 5 trading days to find the most recent bhavcopy."""
    d = date.today()
    for _ in range(7):
        if d.weekday() < 5:  # Mon-Fri
            return d.strftime("%d%m%Y")
        d -= timedelta(days=1)
    return date.today().strftime("%d%m%Y")


def cmd_delivery(symbols: list):
    import requests
    symbols_upper = [s.upper().replace(".NS", "") for s in symbols]
    date_str = _latest_bhavcopy_date()
    url = NSE_BHAVCOPY_URL.format(date=date_str)
    date_iso = f"{date_str[4:]}-{date_str[2:4]}-{date_str[:2]}"

    session = _get_session()
    try:
        r = session.get(url, headers=_nse_headers(), timeout=30)
        r.raise_for_status()
    except Exception as e:
        print(json.dumps({"error": str(e), "url": url}))
        sys.exit(1)

    out = {}
    try:
        with zipfile.ZipFile(io.BytesIO(r.content)) as zf:
            csv_name = zf.namelist()[0]
            csv_text = zf.read(csv_name).decode("utf-8")

        for line in csv_text.splitlines():
            parts = line.split(",")
            if len(parts) < 2:
                continue
            sym = parts[0].strip().strip('"').upper()
            if sym not in symbols_upper:
                continue
            # Find DELIV_PER column — bhavcopy header varies, locate by position
            # Typical CM bhavcopy columns: SYMBOL,SERIES,OPEN,HIGH,LOW,CLOSE,LAST,PREVCLOSE,TOTTRDQTY,TOTTRDVAL,TIMESTAMP,TOTALTRADES,ISIN,DELIV_QTY,DELIV_PER
            try:
                deliv_per = float(parts[-1].strip()) if parts[-1].strip() not in ("", "-") else None
                if deliv_per is None and len(parts) >= 15:
                    deliv_per = float(parts[14].strip())
            except (ValueError, IndexError):
                deliv_per = None

            interp = "unknown"
            if deliv_per is not None:
                if deliv_per >= 60:
                    interp = "strong institutional"
                elif deliv_per >= 40:
                    interp = "moderate"
                else:
                    interp = "weak institutional"

            out[sym] = {
                "delivery_pct":    deliv_per,
                "interpretation":  interp,
                "date":            date_iso,
            }
    except Exception as e:
        print(json.dumps({"error": f"CSV parse failed: {e}"}))
        sys.exit(1)

    # Fill missing symbols
    for sym in symbols_upper:
        if sym not in out:
            out[sym] = {"delivery_pct": None, "interpretation": "data not found", "date": date_iso}

    print(json.dumps(out, indent=2))


def cmd_pcr():
    import requests
    session = _get_session()
    try:
        r = session.get(NSE_OPTION_CHAIN_URL, headers=_nse_headers(), timeout=15)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)

    records = data.get("records", {}).get("data", [])
    total_put_oi = 0
    total_call_oi = 0

    for record in records:
        pe = record.get("PE", {}) or {}
        ce = record.get("CE", {}) or {}
        total_put_oi  += pe.get("openInterest", 0) or 0
        total_call_oi += ce.get("openInterest", 0) or 0

    if total_call_oi == 0:
        print(json.dumps({"error": "No call OI found — option chain may be empty"}))
        sys.exit(1)

    pcr = round(total_put_oi / total_call_oi, 3)
    if pcr < 0.7:
        interp = "euphoric (too many calls — contrarian bearish signal)"
    elif pcr > 1.2:
        interp = "fearful (too many puts — contrarian bullish signal)"
    else:
        interp = "neutral"

    print(json.dumps({
        "pcr":            pcr,
        "put_oi":         total_put_oi,
        "call_oi":        total_call_oi,
        "interpretation": interp,
        "date":           date.today().isoformat(),
    }, indent=2))


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(0)

    cmd = args[0].lower()
    if cmd == "delivery":
        if len(args) < 2:
            print("Usage: market_data.py delivery SYMBOL [SYMBOL ...]", file=sys.stderr)
            sys.exit(1)
        cmd_delivery(args[1:])
    elif cmd == "pcr":
        cmd_pcr()
    else:
        print(f"Unknown command: {cmd}", file=sys.stderr)
        print(__doc__)
        sys.exit(1)
