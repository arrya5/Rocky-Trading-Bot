# Trading Strategy — Indian Market Edition
*Last updated: 2026-05-17*

## Universe
- **Allowed**: Nifty 50 large caps + Nifty Midcap 150 stocks only
- **Exchange**: NSE primary (use .NS suffix for yfinance)
- **Instruments**: Equity delivery only — NO options, futures, or intraday
- **Excluded**: Penny stocks, stocks outside Nifty 200, PSU banks with government interference risk

## Capital & Position Sizing
- **Total capital**: ₹5,00,000
- **Max per position**: ₹1,00,000 (20% of capital) — NEVER exceed this
- **Max positions**: 5 simultaneous open positions
- **Min position**: ₹10,000 (avoid tiny positions with outsized brokerage impact)
- **New positions/week**: Max 3

## Entry Rules (ALL must pass — no exceptions)
1. Stock must be in Nifty 50 or Nifty Midcap 150
2. GRU signal must be BUY with confidence ≥ 60%
3. Catalyst documented in RESEARCH-LOG.md (earnings, sector tailwind, technical breakout)
4. Upper circuit NOT hit in the last 3 days (avoid extended stocks)
5. India VIX must be < 20 (high volatility = no new positions)
6. Max 5 total positions after entry
7. Max 3 new positions this week not exceeded
8. Position cost ≤ available cash
9. FII net buying must not be strongly negative (> -₹2000 Cr outflow)

## Exit Rules
### Hard stops (execute immediately, no exceptions)
- Unrealized loss ≥ -7% → CLOSE full position at market
- Lower circuit hit → attempt close at open next day; flag as illiquid
- Company fraud/scam news → CLOSE immediately regardless of P&L
- Thesis broken (key catalyst failed) → CLOSE regardless of P&L

### Trailing stop management
- Default trailing stop: 10% below cost
- At +15% gain: tighten trailing stop to 7% below current price
- At +20% gain: tighten trailing stop to 5% below current price
- NEVER move stop downward (only tighten)
- NEVER tighten stop within 3% of current LTP

### Sector rule
- After 2 consecutive failed trades in same sector → exit sector for 10 trading days

### Profit taking
- Target: +20% to +30% (exit fully or partially)
- Do NOT hold indefinitely — lock in gains

## Risk Controls
### Pre-order circuit check
Before every BUY order, verify:
- Stock is not at upper circuit (would reject order anyway, but log it)
- Stock has not been at lower circuit in last 3 sessions
- Circuit limit: 5% / 10% / 20% depending on category

### Margin check
- All trades are delivery (CNC product code) — no margin trading
- Ensure available cash > position cost before placing

### Costs to factor into P&L
- **STT**: 0.1% on delivery sell-side
- **Brokerage**: ₹20 flat per order (Upstox zero brokerage for delivery)
- **Exchange fees**: ~0.00345% of trade value
- **SEBI fee**: ₹10 per crore
- **GST**: 18% on brokerage + exchange fees
- **Stamp duty**: 0.015% on buy-side

## Market Hours (IST)
- Pre-open session: 9:00 AM – 9:15 AM (order collection, no execution)
- Regular session: 9:15 AM – 3:30 PM
- Post-close session: 3:40 PM – 4:00 PM
- **Place orders only between 9:20 AM and 3:20 PM**

## Settlement
- T+1 settlement: Shares credited/debited next trading day
- Delivery trades: Hold ≥ 1 day (no same-day reversal)
- No PDT rule in India — day trading allowed but we trade delivery only

## Benchmark
- Compare weekly performance against Nifty 50 index
- Target: Beat Nifty 50 by +2% per quarter

## Strategy Grade Scale
- A: Beat Nifty + positive absolute return
- B: Beat Nifty OR positive return (not both)
- C: Underperform Nifty but positive return
- D: Negative return
- F: > -10% total portfolio drawdown in a week
