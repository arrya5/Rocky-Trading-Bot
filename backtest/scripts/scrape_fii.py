#!/usr/bin/env python3
"""
scrape_fii.py — Scrape historical NSE FII net flows.

NSE publishes daily FII cash market provisional data at:
  https://archives.nseindia.com/content/fii/fii_DDMMYYYY.csv

Some dates use a slightly different URL. We try a couple of patterns.
Output: backtest/data/historical_fii.csv with columns: date, fii_net_cr
"""
import csv, io, sys, time
from datetime import date, timedelta
from pathlib import Path

import requests

OUT = Path(__file__).resolve().parents[1] / "data" / "historical_fii.csv"
OUT.parent.mkdir(parents=True, exist_ok=True)

START = date(2023, 1, 1)
END   = date(2026, 5, 17)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Referer": "https://www.nseindia.com/",
    "Accept": "text/csv,application/csv,*/*;q=0.8",
}

URL_PATTERNS = [
    "https://archives.nseindia.com/content/fii/fii_{ddmmyyyy}.csv",
    "https://www1.nseindia.com/content/fii/fii_{ddmmyyyy}.csv",
]


def parse_fii_csv(text: str) -> float | None:
    """
    NSE FII provisional CSVs vary. Typical structure:
      Category,Buy Value,Sell Value,Net Value
      FII/FPI,..,..,..
      DII,..,..,..
    We extract the FII/FPI net value (Cr). Returns None if can't parse.
    """
    reader = csv.reader(io.StringIO(text))
    for row in reader:
        if not row:
            continue
        first = row[0].strip().lower()
        if "fii" in first or "fpi" in first:
            # Net is usually last numeric column
            for val in reversed(row[1:]):
                v = val.strip().replace(",", "").replace("\"", "")
                try:
                    return float(v)
                except ValueError:
                    continue
    return None


def fetch_one(d: date) -> float | None:
    ddmm = d.strftime("%d%m%Y")
    for url_tmpl in URL_PATTERNS:
        url = url_tmpl.format(ddmmyyyy=ddmm)
        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            if r.status_code == 200 and r.text and "," in r.text:
                val = parse_fii_csv(r.text)
                if val is not None:
                    return val
        except Exception:
            continue
    return None


def main():
    rows = []
    d = START
    misses = 0
    consecutive_misses = 0
    while d <= END:
        if d.weekday() < 5:  # Mon-Fri
            val = fetch_one(d)
            if val is not None:
                rows.append((d.isoformat(), val))
                consecutive_misses = 0
                print(f"{d.isoformat()}: {val:+.0f} Cr", flush=True)
            else:
                misses += 1
                consecutive_misses += 1
                if consecutive_misses % 20 == 0:
                    print(f"[{d.isoformat()}] {consecutive_misses} consecutive misses, sleeping 5s...", file=sys.stderr)
                    time.sleep(5)
            time.sleep(0.3)  # be polite to NSE
        d += timedelta(days=1)

    if not rows:
        print("ERROR: No FII data scraped. NSE may have blocked us or URL pattern changed.", file=sys.stderr)
        print("Writing empty file; gate 7 will be disabled in POC run.", file=sys.stderr)

    with OUT.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["date", "fii_net_cr"])
        w.writerows(rows)
    print(f"\nWrote {len(rows)} FII rows ({misses} misses) -> {OUT}")


if __name__ == "__main__":
    main()
