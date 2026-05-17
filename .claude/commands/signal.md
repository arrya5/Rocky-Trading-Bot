# /signal [SYMBOL ...] — Get GRU trade signal for one or more NSE stocks

Run the signal generator for the provided symbols (or default to Nifty 50 top picks):

```bash
python models/signal_generator.py $ARGUMENTS
```

Display results as a formatted table:
| Symbol | Signal | Confidence | Current ₹ | 5d Forecast ₹ | Change % | Dir Accuracy |
|--------|--------|------------|-----------|---------------|----------|--------------|

If no symbols provided, run for: RELIANCE TCS INFY HDFCBANK ICICIBANK HINDUNILVR BAJFINANCE SBIN WIPRO ADANIENT

Highlight BUY signals with confidence ≥ 60% — these are candidates for the next market-open routine.
