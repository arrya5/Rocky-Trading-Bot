"""EOD routine — 3:45 PM IST (also runs weekly review on Fridays).
Compute day P&L, write EOD snapshot, send Telegram report.
"""
import sys, os, re, json
from pathlib import Path
from datetime import datetime
import yfinance as yf

sys.path.insert(0, str(Path(__file__).parent))
from common import gemini_research, telegram_send, broker, today_str, now_ist

today = today_str()
now   = now_ist()
print(f"EOD starting: {today}")

# ── Step 1: Get final state ───────────────────────────────────────────────────
account   = broker('account')
positions = broker('positions')
if not isinstance(account, dict):
    telegram_send(f"EOD {today} | ERROR: broker unavailable")
    sys.exit(1)

cash        = float(account.get('cash', 500_000))
pos_list    = positions if isinstance(positions, list) else []

# ── Step 2: Get closing prices ────────────────────────────────────────────────
total_market_value = 0.0
pos_details        = []

for pos in pos_list:
    symbol    = pos.get('symbol', '')
    avg_price = float(pos.get('avg_price', 0))
    qty       = int(pos.get('qty', 0))
    try:
        tick  = yf.Ticker(f'{symbol}.NS')
        hist  = tick.history(period='1d')
        close = float(hist['Close'].iloc[-1]) if not hist.empty else avg_price
    except Exception:
        close = avg_price

    market_val   = close * qty
    unreal_pnl   = (close - avg_price) * qty
    unreal_pct   = (close - avg_price) / avg_price * 100 if avg_price else 0
    total_market_value += market_val
    pos_details.append({
        'symbol': symbol, 'qty': qty, 'avg': avg_price,
        'close': close, 'unreal_pnl': unreal_pnl, 'unreal_pct': unreal_pct
    })

portfolio_total = cash + total_market_value

# ── Step 3: Nifty 50 closing performance ─────────────────────────────────────
nifty_pct = None
try:
    nifty_hist = yf.Ticker('^NSEI').history(period='2d')
    if len(nifty_hist) >= 2:
        nifty_prev  = float(nifty_hist['Close'].iloc[-2])
        nifty_close = float(nifty_hist['Close'].iloc[-1])
        nifty_pct   = (nifty_close - nifty_prev) / nifty_prev * 100
except Exception as e:
    print(f"Nifty data error: {e}")

# ── Step 4: Compute day P&L vs yesterday's snapshot ──────────────────────────
trade_log_path  = Path('memory/TRADE-LOG.md')
trade_log       = trade_log_path.read_text(encoding='utf-8')

prev_total = 500_000.0  # base capital fallback
portfolio_matches = re.findall(r'\*\*Portfolio value\*\*: .([\d,]+\.?\d*)', trade_log)
if portfolio_matches:
    try:
        prev_total = float(portfolio_matches[-1].replace(',', ''))
    except ValueError:
        pass

day_pnl     = portfolio_total - prev_total
day_pnl_pct = day_pnl / prev_total * 100 if prev_total else 0
all_time_pnl     = portfolio_total - 500_000
all_time_pct     = all_time_pnl / 500_000 * 100
alpha            = day_pnl_pct - (nifty_pct or 0)

nifty_str = f"{nifty_pct:+.2f}%" if nifty_pct is not None else "N/A"
alpha_str = f"{alpha:+.2f}%" if nifty_pct is not None else "N/A"

# ── Step 5: Write EOD snapshot ────────────────────────────────────────────────
pos_lines = '\n'.join(
    f"  - {p['symbol']}: {p['qty']} @ {p['avg']:.2f} | "
    f"close {p['close']:.2f} | P&L {p['unreal_pnl']:+.0f} ({p['unreal_pct']:+.1f}%)"
    for p in pos_details
) or '  None'

snapshot = (
    f"\n### EOD Snapshot {today}\n"
    f"- **Portfolio value**: {portfolio_total:,.2f}\n"
    f"- **Cash**: {cash:,.2f}\n"
    f"- **Open positions**: {len(pos_list)}\n"
    f"- **Market value**: {total_market_value:,.2f}\n"
    f"- **Unrealized P&L**: {total_market_value - sum(p['avg']*p['qty'] for p in pos_details):+,.2f}\n"
    f"- **Day P&L**: {day_pnl:+,.2f} ({day_pnl_pct:+.2f}%)\n"
    f"- **All-time P&L**: {all_time_pnl:+,.2f} ({all_time_pct:+.2f}% from base 5,00,000)\n"
    f"- **Nifty 50 today**: {nifty_str}\n"
    f"- **Alpha vs Nifty**: {alpha_str}\n"
    f"- **Positions**:\n{pos_lines}\n"
)

trade_log_path.write_text(trade_log + snapshot, encoding='utf-8')
print("EOD snapshot written.")

# ── Step 6: Telegram EOD report ───────────────────────────────────────────────
telegram_send(
    f"EOD {today}\n"
    f"Portfolio: {portfolio_total:,.0f} | Day: {day_pnl_pct:+.2f}%\n"
    f"Nifty: {nifty_str} | Alpha: {alpha_str}\n"
    f"Positions: {len(pos_list)}/5 | Cash: {cash:,.0f}"
)

# ── Step 7: Weekly review (Fridays only) ─────────────────────────────────────
if now.weekday() == 4:  # Friday
    print("Friday — running weekly review...")
    _run_weekly_review(today, trade_log + snapshot, portfolio_total, nifty_pct)


def _run_weekly_review(today: str, trade_log: str, portfolio_total: float, nifty_pct):
    from datetime import timedelta
    week_ago = (now_ist() - timedelta(days=4)).strftime('%Y-%m-%d')

    # Parse week's EOD snapshots to get Monday total
    snapshots = re.findall(
        r'### EOD Snapshot (\d{4}-\d{2}-\d{2})\n.*?\*\*Portfolio value\*\*: .([\d,]+\.?\d*)',
        trade_log, re.DOTALL
    )
    week_start_total = 500_000.0
    if snapshots:
        try:
            week_start_total = float(snapshots[-min(5, len(snapshots))][1].replace(',', ''))
        except (ValueError, IndexError):
            pass

    week_pnl     = portfolio_total - week_start_total
    week_pnl_pct = week_pnl / week_start_total * 100 if week_start_total else 0

    nifty_week = gemini_research(
        f"Nifty 50 weekly performance this week ending {today} — net gain or loss percentage"
    )

    # Count this week's trades
    week_buys = len(re.findall(r'Action\*\*: BUY', trade_log))

    # Grade
    if week_pnl_pct > 0 and (nifty_pct or 0) >= 0 and week_pnl_pct > (nifty_pct or 0):
        grade = 'A'
    elif week_pnl_pct > 0:
        grade = 'B'
    elif week_pnl_pct > (nifty_pct or 0):
        grade = 'C'
    elif week_pnl_pct > -10:
        grade = 'D'
    else:
        grade = 'F'

    review_entry = (
        f"\n### WEEK OF {week_ago} to {today}\n"
        f"- Week P&L: {week_pnl:+,.2f} ({week_pnl_pct:+.2f}%)\n"
        f"- Nifty this week: {nifty_week[:150]}\n"
        f"- Grade: {grade}\n"
        f"- Trades placed: {week_buys}\n\n"
        f"---\n"
    )
    weekly_path = Path('memory/WEEKLY-REVIEW.md')
    weekly_path.write_text(
        weekly_path.read_text(encoding='utf-8') + review_entry,
        encoding='utf-8'
    )

    telegram_send(
        f"Weekly Review {today}\n"
        f"Grade: {grade} | Week P&L: {week_pnl_pct:+.2f}%\n"
        f"Nifty: {nifty_week[:100]}"
    )
    print(f"Weekly review done. Grade: {grade}")


print(f"EOD done. Portfolio: {portfolio_total:,.0f} | Day P&L: {day_pnl_pct:+.2f}%")
