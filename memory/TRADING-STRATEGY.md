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
10. No earnings announcement or board meeting for results within 7 calendar days (binary event risk)
11. Sector concentration ≤ 2 open positions in the same sector after entry

## Exit Rules
### Hard stops (execute immediately, no exceptions)
- Unrealized loss ≥ -7% → CLOSE full position at market
- Lower circuit hit → attempt close at open next day; flag as illiquid
- Company fraud/scam news → CLOSE immediately regardless of P&L
- Thesis broken (key catalyst failed) → CLOSE regardless of P&L

### Partial profit booking (mandatory at +15%)
- At +15% gain: SELL exactly 50% of position at market — lock in realized gain
- Remaining 50%: tighten trailing stop to 7% below current price
- ONE partial exit only per trade — do NOT take another 50% exit on the same position
- After partial exit at +15%: At +20% on remaining → tighten stop to 5% below current price
- At +30% on remaining: close full remaining position

### Trailing stop management
- Default trailing stop: 10% below cost
- At +15% gain: tighten trailing stop to 7% below current price (after partial exit)
- At +20% gain: tighten trailing stop to 5% below current price
- NEVER move stop downward (only tighten)
- NEVER tighten stop within 3% of current LTP

### Sector rule
- After 2 consecutive failed trades in same sector → exit sector for 10 trading days
- Max 2 simultaneous open positions in any single sector (Gate 11)

### Profit taking
- Target: +20% to +30% (exit remaining position)
- Do NOT hold indefinitely — lock in gains

## Pre-Market Synthesis (Extended Thinking — Step 2.7)
- `scripts/synthesize.py` calls Claude with extended thinking to reason across ALL macro signals together
- Output: verdict (PROCEED / CAUTION-1-TRADE-MAX / CAUTION-AVOID-SECTORS / SKIP) + reasoning_summary + risk_flags
- `max_trades_today` from synthesis overrides the weekly 3-trade limit for today only
- `sectors_to_avoid` from synthesis adds to today's rejected list (not a permanent sector block)
- Extended thinking catches cross-signal contradictions: borderline VIX + strong FII ≠ same as borderline VIX + weak FII

## Chart Pattern Analysis (Vision — Step 4.7)
- `scripts/chart_analysis.py` generates a 60-day candlestick chart from yfinance → passes to Claude vision
- Output per symbol: pattern, signal (bullish/bearish/neutral), thesis_alignment (confirms/contradicts/neutral), key levels
- `thesis_alignment: contradicts` + high confidence → remove candidate from shortlist
- `thesis_alignment: contradicts` + low confidence → keep candidate, note warning in research log
- Chart analysis is informational — NOT a hard gate. Strong GRU + fundamentals override weak chart signal
- Adds pattern recognition (doji, engulfing, double top, etc.) the GRU model cannot see numerically

## Market Context Signals (informational — not hard gates unless noted)
- **Regime** (pre-market): bull/bear/sideways based on Nifty 50 20-day SMA slope
  - Bull: slope > +1.5% | Bear: slope < -1.5% | Sideways: between
  - Log regime in each day's RESEARCH-LOG.md entry
- **Nifty PCR** (pre-market):
  - PCR < 0.5: extreme euphoria — add caution note, proceed with extra care
  - PCR < 0.7: euphoric market — log as caution
  - PCR 0.7–1.2: neutral
  - PCR > 1.2: fearful market (contrarian bullish signal)
- **Delivery %** (when available):
  - ≥ 60%: strong institutional interest in the stock
  - 40–60%: moderate
  - < 40%: weak institutional interest — note in research log, not a hard gate
- **Catalyst type**: tracked per trade for learning. Performance analyzer will flag catalyst types with < 30% win rate across 5+ trades.

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
