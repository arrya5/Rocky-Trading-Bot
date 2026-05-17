#!/usr/bin/env python3
"""
chart_analysis.py — Generate candlestick charts and analyze patterns with Gemini vision

Downloads 60 days of OHLCV data via yfinance, generates a candlestick PNG using
mplfinance, then passes the image to Gemini 2.5 Flash with vision to identify
chart patterns and assess alignment with a BUY thesis.

Usage:
  python scripts/chart_analysis.py RELIANCE TCS INFY
  python scripts/chart_analysis.py RELIANCE --days 30

Output (one JSON object per symbol, printed to stdout):
  {"symbol": "RELIANCE", "pattern": "Bullish engulfing", "signal": "bullish",
   "confidence": "high", "thesis_alignment": "confirms",
   "key_levels": {"support": 2480.0, "resistance": 2600.0},
   "interpretation": "3-day pullback to 20-day SMA with bullish engulfing candle..."}

Requires: GEMINI_API_KEY environment variable, mplfinance package
"""

import base64, json, os, sys, tempfile, warnings
import urllib.request, urllib.error
from pathlib import Path

warnings.filterwarnings("ignore")

GEMINI_MODEL = "gemini-2.5-flash"
DEFAULT_DAYS = 60


def _generate_chart(symbol: str, days: int, outfile: str) -> bool:
    """Download OHLCV data and save a candlestick chart PNG. Returns True on success."""
    import yfinance as yf
    import mplfinance as mpf

    ticker = symbol.upper() if symbol.upper().endswith(".NS") else symbol.upper() + ".NS"
    df = yf.download(ticker, period=f"{days}d", interval="1d", progress=False, auto_adjust=True)

    if df.empty or len(df) < 10:
        return False

    # Flatten MultiIndex columns if present
    if hasattr(df.columns, "levels"):
        df.columns = df.columns.get_level_values(0)

    df.index.name = "Date"

    mpf.plot(
        df,
        type="candle",
        style="charles",
        title=f"{symbol} — {days}d Daily",
        ylabel="Price (₹)",
        volume=True,
        mav=(20, 50),
        savefig=dict(fname=outfile, dpi=100, bbox_inches="tight"),
        figsize=(10, 6),
        warn_too_much_data=1000,
    )
    return True


def _analyze_chart(symbol: str, image_path: str) -> dict:
    """Pass chart image to Gemini vision and get pattern analysis."""
    import re

    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        print("ERROR: GEMINI_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    with open(image_path, "rb") as f:
        image_data = base64.standard_b64encode(f.read()).decode("utf-8")

    prompt = (
        f"You are a technical analyst for Indian equity markets (NSE). "
        f"Analyze this 60-day daily candlestick chart for {symbol}. "
        f"The chart includes 20-day and 50-day moving averages and volume bars.\n\n"
        f"Identify:\n"
        f"1. The dominant candlestick or chart pattern visible (e.g., 'Bullish engulfing', 'Head and shoulders', "
        f"'Doji after rally', 'Cup and handle', 'Double top', 'Ascending triangle', etc.)\n"
        f"2. Overall signal: bullish / bearish / neutral\n"
        f"3. Confidence: high / medium / low\n"
        f"4. Approximate support and resistance levels visible on the chart (in rupees)\n"
        f"5. Whether this chart CONFIRMS, CONTRADICTS, or is NEUTRAL to a BUY thesis\n"
        f"6. One clear 2-sentence interpretation explaining the pattern and its implication\n\n"
        f"Return ONLY valid JSON, no markdown:\n"
        f'{{"symbol":"{symbol}","pattern":"...","signal":"bullish|bearish|neutral",'
        f'"confidence":"high|medium|low","key_levels":{{"support":0.0,"resistance":0.0}},'
        f'"thesis_alignment":"confirms|contradicts|neutral","interpretation":"..."}}'
    )

    payload = {
        "contents": [{
            "parts": [
                {"inlineData": {"mimeType": "image/png", "data": image_data}},
                {"text": prompt},
            ]
        }],
        "generationConfig": {
            "maxOutputTokens": 500,
            "temperature": 0.1,
            "responseMimeType": "application/json",
        },
    }

    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{GEMINI_MODEL}:generateContent?key={api_key}"
    )
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.load(resp)
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        return {
            "symbol": symbol, "pattern": "api_error", "signal": "neutral",
            "confidence": "low", "key_levels": {"support": None, "resistance": None},
            "thesis_alignment": "neutral",
            "interpretation": f"Gemini API error {e.code}: {body[:200]}",
        }
    except Exception as e:
        return {
            "symbol": symbol, "pattern": "api_error", "signal": "neutral",
            "confidence": "low", "key_levels": {"support": None, "resistance": None},
            "thesis_alignment": "neutral",
            "interpretation": f"Request error: {str(e)[:200]}",
        }

    candidates = data.get("candidates", [])
    if not candidates:
        return {
            "symbol": symbol, "pattern": "no_response", "signal": "neutral",
            "confidence": "low", "key_levels": {"support": None, "resistance": None},
            "thesis_alignment": "neutral", "interpretation": "No response from Gemini.",
        }

    parts = candidates[0].get("content", {}).get("parts", [])
    output = "".join(
        p.get("text", "") for p in parts if not p.get("thought", False)
    ).strip()

    output = re.sub(r"^```(?:json)?\s*", "", output)
    output = re.sub(r"\s*```$", "", output)

    try:
        return json.loads(output)
    except json.JSONDecodeError:
        return {
            "symbol":           symbol,
            "pattern":          "parse_error",
            "signal":           "neutral",
            "confidence":       "low",
            "key_levels":       {"support": None, "resistance": None},
            "thesis_alignment": "neutral",
            "interpretation":   f"Chart analysis completed but JSON parse failed. Raw: {output[:200]}",
        }


def analyze_symbol(symbol: str, days: int = DEFAULT_DAYS) -> dict:
    symbol_clean = symbol.upper().replace(".NS", "")
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        chart_path = f.name

    try:
        ok = _generate_chart(symbol_clean, days, chart_path)
        if not ok:
            return {
                "symbol":          symbol_clean,
                "pattern":         "no_data",
                "signal":          "neutral",
                "confidence":      "low",
                "key_levels":      {"support": None, "resistance": None},
                "thesis_alignment": "neutral",
                "interpretation":  f"Insufficient price data for {symbol_clean} — chart not generated.",
            }
        return _analyze_chart(symbol_clean, chart_path)
    finally:
        try:
            Path(chart_path).unlink(missing_ok=True)
        except Exception:
            pass


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("symbols", nargs="+", help="NSE ticker symbols")
    parser.add_argument("--days", type=int, default=DEFAULT_DAYS)
    args = parser.parse_args()

    for symbol in args.symbols:
        result = analyze_symbol(symbol, args.days)
        print(json.dumps(result))


if __name__ == "__main__":
    main()
