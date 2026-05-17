"""Midday routine — 12:30 PM IST.
Scan open positions, enforce stops, check news, tighten trailing stops.
"""
import sys, os, re, json
from pathlib import Path
import yfinance as yf

sys.path.insert(0, str(Path(__file__).parent))
from common import gemini_research, telegram_send, broker, today_str

today = today_str()
print(f"Midday starting: {today}")

positions = broker('positions')
if not isinstance(positions, list) or not positions:
    telegram_send(f"Midday {today} | No open positions — nothing to scan")
    sys.exit(0)

trade_log_path = Path('memory/TRADE-LOG.md')
trade_log      = trade_log_path.read_text(encoding='utf-8')

stops_hit      = []
stops_tightened = []
holding        = []

for pos in positions:
    symbol    = pos.get('symbol', '')
    avg_price = float(pos.get('avg_price', 0))
    qty       = int(pos.get('qty', 0))
    if not symbol or avg_price <= 0:
        continue

    # Get current price via yfinance
    try:
        tick = yf.Ticker(f'{symbol}.NS')
        hist = tick.history(period='1d', interval='5m')
        if hist.empty:
            print(f"No intraday data for {symbol}")
            continue
        ltp = float(hist['Close'].iloc[-1])
    except Exception as e:
        print(f"Price error for {symbol}: {e}")
        continue

    pnl_pct    = (ltp - avg_price) / avg_price * 100
    hard_stop  = round(avg_price * 0.93, 2)
    print(f"{symbol}: LTP={ltp:.2f} avg={avg_price:.2f} P&L={pnl_pct:.1f}%")

    # Rule A: Hard stop -7%
    if ltp <= hard_stop:
        broker('close', symbol)
        telegram_send(
            f"STOP HIT: {symbol} | Closed @ {ltp:.2f} | "
            f"P&L: {pnl_pct:.1f}% | Rule: -7% hard stop"
        )
        stops_hit.append(symbol)
        trade_log += (
            f"\n**Midday {today} 12:30**: {symbol} STOP HIT | "
            f"LTP {ltp:.2f} | P&L: {pnl_pct:.1f}% | Status: CLOSED\n"
        )
        continue

    # Rules B/C: Trailing stop tighten
    new_stop = None
    tag      = ''
    if pnl_pct >= 20:
        new_stop = round(ltp * 0.95, 2)
        tag = f"5% trailing (P&L +{pnl_pct:.1f}%)"
    elif pnl_pct >= 15:
        new_stop = round(ltp * 0.93, 2)
        tag = f"7% trailing (P&L +{pnl_pct:.1f}%)"

    if new_stop and new_stop > hard_stop:
        stops_tightened.append(symbol)
        trade_log += (
            f"\n**Midday {today} 12:30**: {symbol} stop tightened to "
            f"{new_stop} ({tag})\n"
        )
    else:
        # Check for negative news
        news = gemini_research(
            f"{symbol} NSE news today {today} — any negative developments, "
            f"downgrade, fraud, earnings miss, regulatory issue"
        )
        negative_keywords = ['fraud', 'downgrade', 'miss', 'negative', 'concern',
                             'warning', 'penalty', 'probe', 'scam', 'recall']
        if any(kw in news.lower() for kw in negative_keywords):
            telegram_send(f"NEWS ALERT {symbol}: {news[:200]}")

        trade_log += (
            f"\n**Midday {today} 12:30**: {symbol} | LTP {ltp:.2f} | "
            f"P&L: {pnl_pct:.1f}% | Stop: {hard_stop} | HOLDING\n"
        )
        holding.append(symbol)

# Write updated trade log
trade_log_path.write_text(trade_log, encoding='utf-8')

# Telegram summary
telegram_send(
    f"Midday {today} | Positions: {len(positions)} | "
    f"Stops hit: {len(stops_hit)} | Tightened: {len(stops_tightened)} | "
    f"Holding: {len(holding)}"
)

print(f"Midday done. Hit={stops_hit}, Tightened={stops_tightened}, Holding={holding}")
