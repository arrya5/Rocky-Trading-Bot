"""Market-open routine — 9:20 AM IST.
Reads today's research log, applies 9-point gate, places paper orders.
"""
import sys, os, re, json, subprocess
from pathlib import Path
from datetime import datetime, date
import yfinance as yf
import pytz

sys.path.insert(0, str(Path(__file__).parent))
from common import gemini_research, telegram_send, broker, today_str, now_ist

today     = today_str()
now       = now_ist()
week_start = now - __import__('datetime').timedelta(days=now.weekday())

# ── Nifty 50 + top Midcap 150 universe ───────────────────────────────────────
UNIVERSE = {
    'RELIANCE','TCS','HDFCBANK','INFY','ICICIBANK','HINDUNILVR','ITC',
    'SBIN','BAJFINANCE','BHARTIARTL','KOTAKBANK','LT','AXISBANK',
    'ASIANPAINT','MARUTI','TITAN','WIPRO','SUNPHARMA','ULTRACEMCO',
    'NESTLEIND','POWERGRID','NTPC','HCLTECH','TECHM','ONGC','COALINDIA',
    'DRREDDY','BPCL','DIVISLAB','GRASIM','BAJAJFINSV','TATAMOTORS',
    'TATASTEEL','JSWSTEEL','HDFCLIFE','SBILIFE','APOLLOHOSP','CIPLA',
    'EICHERMOT','HEROMOTOCO','SHREECEM','BRITANNIA','INDUSINDBK','UPL',
    'TATACONSUM','LTIM','IRCTC','MARICO','GODREJCP','AMBUJACEM',
    'BANDHANBNK','AUBANK','FEDERALBNK','PERSISTENT','COFORGE','MPHASIS',
    'ALKEM','AUROPHARMA','ASHOKLEY','BALKRISIND','ESCORTS','VOLTAS',
    'JUBLFOOD','DMART','TRENT','VBL','INDHOTEL',
}

print(f"Market-open starting: {today}")

# ── Step 1: Read today's research log ────────────────────────────────────────
log_path = Path('memory/RESEARCH-LOG.md')
log_text = log_path.read_text(encoding='utf-8')

# Find today's entry
today_entry_match = re.search(
    rf'### RESEARCH-{today}(.*?)(?=### RESEARCH-|\Z)',
    log_text, re.DOTALL
)
if not today_entry_match:
    msg = f"Market-open {today}: No pre-market research found — skipping all trades."
    print(msg)
    telegram_send(f"Market-open {today} | 0 trades | Reason: No pre-market research log")
    sys.exit(0)

today_entry = today_entry_match.group(1)

# ── Gate 5: VIX check ────────────────────────────────────────────────────────
if 'HIGH VIX' in today_entry or 'HIGH: no new positions' in today_entry:
    telegram_send(f"Market-open {today} | 0 trades | Reason: HIGH VIX")
    sys.exit(0)

vix_level = None
m = re.search(r'VIX[^\d]*?(\d+\.?\d*)', today_entry)
if m:
    try:
        vix_level = float(m.group(1))
    except ValueError:
        pass

if vix_level and vix_level >= 20:
    telegram_send(f"Market-open {today} | 0 trades | Reason: VIX {vix_level:.1f} >= 20")
    sys.exit(0)

# ── Gate 9: FII flow check ────────────────────────────────────────────────────
fii_level = None
m = re.search(r'FII[^₹\d\-]*?([\-\+]?\s*[\d,]+\.?\d*)\s*[Cc]r', today_entry)
if m:
    try:
        fii_level = float(m.group(1).replace(',', '').replace(' ', ''))
    except ValueError:
        pass
if fii_level is not None and fii_level < -2000:
    telegram_send(f"Market-open {today} | 0 trades | Reason: FII outflow {fii_level:.0f} Cr")
    sys.exit(0)

# ── Extract candidates from research log ─────────────────────────────────────
candidate_section = re.search(
    r'\*\*Trade Candidates\*\*.*?\n(.*?)(?=\*\*Key Events|\Z)',
    today_entry, re.DOTALL
)
raw_candidates = []
if candidate_section:
    for line in candidate_section.group(1).splitlines():
        m = re.search(r'\d+\.\s+([A-Z][A-Z0-9&\-]{1,14})', line)
        if m:
            raw_candidates.append(m.group(1))

if not raw_candidates:
    telegram_send(f"Market-open {today} | 0 trades | Reason: No BUY candidates in research log")
    sys.exit(0)

print(f"Candidates from research: {raw_candidates}")

# ── Step 2: Account state ─────────────────────────────────────────────────────
account   = broker('account')
positions = broker('positions')
if not isinstance(account, dict):
    telegram_send(f"Market-open {today} | ERROR: broker account unavailable")
    sys.exit(1)

cash         = float(account.get('cash', 0))
n_positions  = len(positions) if isinstance(positions, list) else 0

# Count trades placed this week
trade_log    = Path('memory/TRADE-LOG.md').read_text(encoding='utf-8')
week_str     = week_start.strftime('%Y-%m-%d')
week_buys    = len(re.findall(rf'Date.*?{week_str[:7]}.*?\n.*?Action.*?BUY', trade_log, re.DOTALL))

print(f"Cash: {cash} | Positions: {n_positions}/5 | Week buys: {week_buys}/3")

# ── Step 3: 9-point gate for each candidate ───────────────────────────────────
orders_placed = 0
trade_log_additions = []

for symbol in raw_candidates:
    print(f"\nChecking gate for {symbol}...")
    gate_log = []

    # Gate 1: Universe check
    if symbol not in UNIVERSE:
        gate_log.append(f"FAIL Gate 1: {symbol} not in Nifty 50 + Midcap 150")
        print(gate_log[-1])
        trade_log_additions.append(f"- {symbol}: SKIP — {gate_log[-1]}")
        continue

    # Gate 2: GRU signal
    result = subprocess.run(
        ['python', 'models/signal_generator.py', symbol],
        capture_output=True, text=True
    )
    conf = None
    for line in result.stdout.splitlines():
        if 'BUY' in line.upper():
            cm = re.search(r'(\d+\.?\d*)%', line)
            if cm:
                conf = float(cm.group(1))
    if conf is None or conf < 60:
        gate_log.append(f"FAIL Gate 2: GRU signal not BUY >= 60% (got {conf}%)")
        print(gate_log[-1])
        trade_log_additions.append(f"- {symbol}: SKIP — {gate_log[-1]}")
        continue

    # Gate 6: Position count
    if n_positions >= 5:
        gate_log.append("FAIL Gate 6: Already at 5 positions")
        trade_log_additions.append(f"- {symbol}: SKIP — {gate_log[-1]}")
        break

    # Gate 7: Weekly trade count
    if week_buys >= 3:
        gate_log.append("FAIL Gate 7: 3 trades already placed this week")
        trade_log_additions.append(f"- {symbol}: SKIP — {gate_log[-1]}")
        break

    # Gate 4: Circuit check via yfinance
    try:
        tick = yf.Ticker(f'{symbol}.NS')
        hist = tick.history(period='2d')
        if len(hist) >= 2:
            prev_close = float(hist['Close'].iloc[-2])
            ltp        = float(hist['Close'].iloc[-1])
            gap_pct    = abs(ltp - prev_close) / prev_close * 100
            if gap_pct > 18:
                gate_log.append(f"FAIL Gate 4: Near circuit ({gap_pct:.1f}% gap)")
                trade_log_additions.append(f"- {symbol}: SKIP — {gate_log[-1]}")
                continue
        else:
            ltp = None
    except Exception as e:
        print(f"yfinance error for {symbol}: {e}")
        ltp = None

    # Gate 8: Position sizing
    if ltp is None:
        quote = broker('quote', symbol)
        ltp   = float(quote.get('ltp', 0)) if isinstance(quote, dict) else 0
    if ltp <= 0:
        trade_log_additions.append(f"- {symbol}: SKIP — could not get price")
        continue

    qty  = int(100_000 / ltp)
    cost = qty * ltp
    if qty < 1:
        trade_log_additions.append(f"- {symbol}: SKIP — price too high for min qty")
        continue
    if cost > cash:
        gate_log.append(f"FAIL Gate 8: Insufficient cash (need {cost:.0f}, have {cash:.0f})")
        trade_log_additions.append(f"- {symbol}: SKIP — {gate_log[-1]}")
        continue

    # Gate 3: Catalyst present (already in research log since we read from it)
    # Gate 5: VIX (already checked above)
    # Gate 9: FII (already checked above)
    # All gates passed — place order
    print(f"All gates passed for {symbol}. Placing BUY {qty} @ ~{ltp:.2f}")
    order = json.dumps({'symbol': symbol, 'qty': qty, 'side': 'buy',
                        'type': 'market', 'product': 'D'})
    broker('order', order)

    stop   = round(ltp * 0.93, 2)
    target = round(ltp * 1.20, 2)
    cost_r = round(cost, 2)

    telegram_send(
        f"BUY {symbol} | {qty} shares @ ~{ltp:.2f} | "
        f"Cost: {cost_r:,.0f} | Target: {target} (+20%) | Stop: {stop} (-7%) | Paper"
    )

    trade_log_additions.append(
        f"\n### TRADE-{today}-{orders_placed+1:03d}\n"
        f"- **Date**: {today}\n"
        f"- **Symbol**: {symbol} (NSE)\n"
        f"- **Action**: BUY\n"
        f"- **Qty**: {qty} shares\n"
        f"- **Price**: {ltp:.2f}\n"
        f"- **Total value**: {cost_r:,.2f}\n"
        f"- **GRU signal**: BUY | confidence: {conf:.0f}%\n"
        f"- **Stop loss**: {stop} (-7%)\n"
        f"- **Target**: {target} (+20%)\n"
        f"- **Status**: OPEN\n"
    )

    orders_placed += 1
    n_positions   += 1
    week_buys     += 1
    cash          -= cost

# ── Step 4: Update TRADE-LOG.md ──────────────────────────────────────────────
if trade_log_additions:
    trade_log_path = Path('memory/TRADE-LOG.md')
    updated = trade_log_path.read_text(encoding='utf-8') + '\n' + '\n'.join(trade_log_additions)
    trade_log_path.write_text(updated, encoding='utf-8')

# ── Step 5: Telegram summary ──────────────────────────────────────────────────
if orders_placed == 0:
    telegram_send(f"Market-open {today} | 0 trades placed | Gates filtered all candidates")
else:
    telegram_send(f"Market-open {today} | {orders_placed} order(s) placed | Cash remaining: {cash:,.0f}")

print(f"Market-open done. Orders placed: {orders_placed}")
