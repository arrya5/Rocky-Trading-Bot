# Trading Strategy — Swing v3
*Last updated: 2026-05-27 (migrated from position trading)*

## Strategy Type
**Short-to-medium term swing trading.** Hold positions 3–15 trading days. Tighter stops than position trading. Tighter targets. Higher conviction threshold. Block bear regime entries entirely.

## Universe
- **Allowed**: Nifty 50 large caps + Nifty Midcap 150 stocks only
- **Exchange**: NSE primary (yfinance .NS suffix)
- **Instruments**: Equity delivery only — NO options, futures, intraday
- **Excluded**: Penny stocks, stocks outside Nifty 200

## Capital & Position Sizing
- **Total capital**: ₹5,00,000 (paper trading)
- **Position size**: Flat **₹50,000 per trade** (only score ≥ 80 trades, single tier)
- **Max positions**: Unlimited (paper mode) — can hold up to ~10 concurrent
- **Pre-filters** (excluded entirely if any fails):
  - ADV (20-day avg daily value) ≥ ₹50 Cr
  - 20-day volatility ≤ 3.5%
  - **Above 200-day SMA** (no falling knives)

## Scoring Factors (5 × 20 = 100 max)
1. **Donchian 20-day breakout**: close ≥ previous 20-day high
2. **ADX(14) > 25**: strong trend confirmation
3. **Sector relative strength**: NSE sector index outperforms Nifty by > 1pp over 10 days
4. **Volume surge**: today's volume > 2.5× 20-day avg
5. **Above 50-day EMA**: current price > EMA50 × 1.01 (medium-term uptrend, with 1% buffer)

**BUY signal**: score ≥ 80 (4 of 5 factors aligned). Conservative threshold by design.

## 9+1 Point Buy-Side Gate (ALL must pass)
1. Stock in Nifty 50 or Midcap 150
2. Swing score ≥ 80
3. Catalyst is HARD or MEDIUM tier (LLM-classified)
4. Stock not at upper circuit; no large gap (> 18%)
5. India VIX < 25
6. Position cost ≤ available cash (₹50k per trade)
7. FII net flow > -₹3500 Cr
8. No earnings/board meeting within 7 days
9. Sector concentration ≤ 2 open positions in same sector
10. **NEW — Market regime gate**: skip ALL entries when regime == "bear" (Nifty 20d SMA slope < -1.5%)

## Catalyst Classification (Gate 3)
| Tier | Examples | Gate 3 |
|------|----------|--------|
| HARD | Earnings beat, analyst upgrade, product launch, regulatory approval, QIP/buyback, M&A | PASS |
| MEDIUM | Sector policy (PLI, budget), index inclusion, management guidance, block deal | PASS |
| SOFT | "Stock trending", "sector doing well", vague news | FAIL — skip |

## Exit Rules (Swing v3)

### Hard stops (no exceptions)
- **-5% loss**: close at market (was -7% in position trading; tighter for swing)
- Lower circuit hit: flag, attempt close next day
- Fraud/scam news: close immediately
- Thesis broken: close regardless of P&L
- **Max hold 15 trading days**: force close regardless of P&L (NEW — swing-specific)

### Partial profit booking (mandatory at +6%)
- At +6% gain: SELL exactly 50% of position at market — lock realized gain
- Tighten remaining 50% trailing stop to **3% below current price**
- ONE partial exit only per trade

### Trailing stop management
- Default trail: -5% below cost (the hard stop)
- After partial at +6%: trail tightens to -3% below current price
- At +12% gain: trail tightens further to -3% below current price (no double-tighten)
- NEVER move stop downward (only tighten)

### Sector rule
- After 2 consecutive failed trades in same sector → exit sector for 5 trading days (faster cycle than position trading)
- Max 2 simultaneous open positions per sector

## Market Context Signals
- **Regime** (pre-market): bull / bear / sideways based on Nifty 50 20-day SMA slope
  - Bull: slope > +1.5%
  - Bear: slope < -1.5% → **BLOCK ALL ENTRIES**
  - Sideways: between (allow entries)
- **Nifty PCR** (pre-market): informational
- **Delivery %**: informational when available

## Risk Controls
- Pre-order circuit check: not at upper circuit, no lower circuit in last 3 sessions
- All trades CNC (delivery) — no margin
- Available cash check before each entry

## Costs to factor (per round-trip)
- STT: 0.1% on delivery sell-side
- Brokerage: ₹20 flat per order
- Exchange fees: ~0.00345%
- GST: 18% on brokerage + exchange
- Stamp duty: 0.015% buy-side
- **Estimated round-trip cost**: ~0.15–0.20%

## Market Hours (IST)
- Regular session: 9:15 AM – 3:30 PM
- Place orders only between 9:20 AM and 3:20 PM

## Benchmark & Grading
- Compare weekly performance to Nifty 50
- Target: Beat Nifty by +1% per week (swing target — more aggressive than position)

## Strategy Grade Scale (weekly)
- A: Beat Nifty AND positive absolute return
- B: Beat Nifty OR positive return (not both)
- C: Underperform Nifty but positive return
- D: Negative return
- F: > -10% portfolio drawdown in a week

## Auto-tuning (after 20 closed trades)
- `scripts/performance_analyzer.py` activates at 20 closed trades
- Recommendations get logged to `memory/WEEKLY-REVIEW.md` for human review
- Recommendations are NOT auto-applied (human-in-loop safeguard)
- Reviewer can manually edit `models/signal_generator.py` constants or this file

## Exit criterion for the swing experiment
If after 30 days of live paper trading the win rate is < 45% AND alpha vs Nifty is < -3%, consider:
- Reverting to position trading rules
- Treating the collected data as research signal
- Re-evaluating which factors actually predict in real-forward data (NOT backtest)

## Migration history
- **2026-05-18**: Initial deployment with position trading rules (70k/50k/30k tiers, -7% stop, +15% partial, no max hold)
- **2026-05-27**: Migrated to Gemini + GitHub Actions infrastructure (CCR routines paused)
- **2026-05-27**: Swing v3 strategy adopted (this version)
