#!/usr/bin/env python3
"""
earnings_guard.py — Check if NSE symbols have earnings/corporate events within N days

Fetches NSE corporate event calendar. Returns True if earnings or board meeting
for results is scheduled within 7 days of today.

Usage:
  python scripts/earnings_guard.py RELIANCE
  python scripts/earnings_guard.py RELIANCE TCS INFY

Output (one JSON object per symbol):
  {"symbol": "RELIANCE", "earnings_within_7d": false, "event_date": null, "event_type": null}
  {"symbol": "TCS", "earnings_within_7d": true, "event_date": "2026-05-22", "event_type": "Board Meeting"}
"""

import json, os, sys
from datetime import date, timedelta
from pathlib import Path

WINDOW_DAYS = 7
NSE_EVENTS_URL = "https://www.nseindia.com/api/event-calendar"
RESEARCH_SCRIPT = Path(__file__).parent / "research.sh"


def _nse_headers() -> dict:
    return {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Referer":    "https://www.nseindia.com/",
        "Accept":     "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive",
    }


def _fetch_nse_events() -> list:
    """Fetch NSE corporate event calendar. Returns list of event dicts."""
    import requests
    session = requests.Session()
    # Prime the session cookie by hitting the main page first
    try:
        session.get("https://www.nseindia.com/", headers=_nse_headers(), timeout=10)
    except Exception:
        pass
    r = session.get(NSE_EVENTS_URL, headers=_nse_headers(), timeout=10)
    r.raise_for_status()
    data = r.json()
    # NSE returns a list directly or {"data": [...]}
    if isinstance(data, list):
        return data
    return data.get("data", [])


def _gemini_fallback(symbol: str) -> dict:
    """Use Gemini research as fallback when NSE API is unavailable."""
    import subprocess
    today_str = date.today().isoformat()
    query = (
        f"{symbol} NSE earnings results board meeting date next 7 days from {today_str}. "
        f"Answer with ONLY: YES <date YYYY-MM-DD> <event_type> or NO"
    )
    try:
        result = subprocess.run(
            ["bash", str(RESEARCH_SCRIPT), query],
            capture_output=True, text=True, timeout=30
        )
        output = result.stdout.strip().upper()
        if output.startswith("YES"):
            parts = output.split()
            event_date = parts[1] if len(parts) > 1 else None
            event_type = " ".join(parts[2:]) if len(parts) > 2 else "Results"
            return {"earnings_within_7d": True, "event_date": event_date, "event_type": event_type, "source": "gemini_fallback"}
    except Exception:
        pass
    return {"earnings_within_7d": False, "event_date": None, "event_type": None, "source": "gemini_fallback"}


def check_symbol(symbol: str, events: list) -> dict:
    symbol_upper = symbol.upper().replace(".NS", "")
    today = date.today()
    cutoff = today + timedelta(days=WINDOW_DAYS)

    RESULT_KEYWORDS = {"results", "board meeting", "dividend", "agm", "egm", "quarterly"}

    for event in events:
        # NSE event fields vary — try common field names
        sym_field = (
            event.get("symbol") or event.get("companyName") or ""
        ).upper()
        if symbol_upper not in sym_field and sym_field not in symbol_upper:
            continue

        purpose = (event.get("purpose") or event.get("type") or "").lower()
        if not any(kw in purpose for kw in RESULT_KEYWORDS):
            continue

        raw_date = event.get("date") or event.get("bm_date") or event.get("record_date") or ""
        if not raw_date:
            continue

        # Parse various NSE date formats: "22-May-2026", "2026-05-22", "22/05/2026"
        for fmt in ("%d-%b-%Y", "%Y-%m-%d", "%d/%m/%Y", "%b %d, %Y"):
            try:
                event_date = date.fromisoformat(raw_date) if "-" in raw_date and len(raw_date) == 10 and raw_date[4] == "-" else None
                if event_date is None:
                    from datetime import datetime
                    event_date = datetime.strptime(raw_date, fmt).date()
                if today <= event_date <= cutoff:
                    return {
                        "symbol":           symbol_upper,
                        "earnings_within_7d": True,
                        "event_date":       event_date.isoformat(),
                        "event_type":       event.get("purpose") or event.get("type"),
                        "source":           "nse_api",
                    }
                break
            except Exception:
                continue

    return {
        "symbol":           symbol_upper,
        "earnings_within_7d": False,
        "event_date":       None,
        "event_type":       None,
        "source":           "nse_api",
    }


def main():
    symbols = [s.upper().replace(".NS", "") for s in sys.argv[1:]]
    if not symbols:
        print(__doc__)
        sys.exit(0)

    events = []
    use_fallback = False

    try:
        events = _fetch_nse_events()
    except Exception as e:
        print(f"WARNING: NSE API failed ({e}) — using Gemini fallback", file=sys.stderr)
        use_fallback = True

    for symbol in symbols:
        if use_fallback:
            result = _gemini_fallback(symbol)
            result["symbol"] = symbol
        else:
            result = check_symbol(symbol, events)
        print(json.dumps(result))


if __name__ == "__main__":
    main()
