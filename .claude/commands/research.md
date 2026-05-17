# /research [SYMBOL or topic] — Run Gemini + Google Search research on demand

$ARGUMENTS: a stock symbol or free-form topic

If a stock symbol (e.g. "RELIANCE"):
```bash
bash scripts/research.sh "RELIANCE NSE stock analysis today $(date +%Y-%m-%d): fundamentals, technicals, recent news, analyst rating"
bash scripts/research.sh "RELIANCE Industries latest earnings results and guidance"
bash scripts/research.sh "RELIANCE NSE technical analysis support resistance levels"
```

If a market topic (e.g. "India VIX" or "FII flow"):
```bash
bash scripts/research.sh "$ARGUMENTS Indian stock market $(date +%Y-%m-%d)"
```

Display the findings clearly and note whether they support or contradict any current open positions.

Append a note to today's RESEARCH-LOG.md entry with the findings.
