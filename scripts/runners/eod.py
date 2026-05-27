#!/usr/bin/env python3
"""EOD routine — 3:45 PM IST.

Production-equivalent of CCR Daily EOD Summary.
Compute P&L, daily reflection on active days, send curated Telegram.
"""
import sys, os, json, re
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))
from common import (
    gemini_research, gemini_reason, telegram_send, broker, today_str, now_ist,
    memory_path, REPO_ROOT, run_script, write_heartbeat,
)

today = today_str()
print(f"[eod] starting {today}")
write_heartbeat('eod', 'started')

# ── Step 1: Final EOD state ──────────────────────────────────────────────────
account   = broker('account')
positions = broker('positions')
if not isinstance(positions, list):
    positions = []

# Refresh quotes to get closing prices
if positions:
    symbols = [p['symbol'] for p in positions]
    broker('quote', *symbols)
    positions = broker('positions')

cash = float(account.get('cash', 0))
total_val = float(account.get('total_value', cash))
market_val = total_val - cash

# ── Step 2: Find yesterday's portfolio total ─────────────────────────────────
trade_log_path = memory_path('TRADE-LOG.md')
trade_log = trade_log_path.read_text(encoding='utf-8') if trade_log_path.exists() else ''

prev_total = 500000.0
matches = re.findall(r'\*\*Portfolio value\*\*:\s*₹?([\d,]+\.?\d*)', trade_log)
if matches:
    try:
        prev_total = float(matches[-1].replace(',', ''))
    except ValueError:
        pass

day_pnl = total_val - prev_total
day_pnl_pct = day_pnl / prev_total * 100 if prev_total else 0
all_time_pnl = total_val - 500000
all_time_pct = all_time_pnl / 500000 * 100

# ── Step 3: Nifty close ──────────────────────────────────────────────────────
nifty_q = gemini_research(f"Nifty 50 closing price today {today} and percentage change vs previous close")
nifty_pct = 0.0
m = re.search(r'([\-\+]?\d+\.\d+)\s*%', nifty_q)
if m:
    try: nifty_pct = float(m.group(1))
    except ValueError: pass

alpha = day_pnl_pct - nifty_pct

# ── Step 4: Count today's activity ───────────────────────────────────────────
today_trades = re.findall(rf'### TRADE-{today.replace("-","")}-\d+', trade_log)
entries_today = len(today_trades)

# Closed trades today (from outcomes.json)
outcomes_path = memory_path('trade-outcomes.json')
outcomes = json.loads(outcomes_path.read_text(encoding='utf-8')) if outcomes_path.exists() else {'trades': []}
closed_today = [t for t in outcomes.get('trades', []) if t.get('exit_date') == today]
exits_today = len(closed_today)

# Determine active vs quiet
is_active = (entries_today + exits_today) >= 1 or abs(day_pnl_pct) >= 1.0

# Best/worst (only meaningful if positions exist)
best_pos = worst_pos = None
if positions:
    enriched = []
    for p in positions:
        ltp = float(p.get('ltp', p['avg_price']))
        pnl = (ltp - p['avg_price']) / p['avg_price'] * 100
        enriched.append({**p, 'pnl_pct': pnl})
    best_pos = max(enriched, key=lambda x: x['pnl_pct'])
    worst_pos = min(enriched, key=lambda x: x['pnl_pct'])

# ── Step 5: Daily reflection (active days only) ──────────────────────────────
surprise = None
if is_active:
    print("[eod] active day, generating reflection")
    # Gather context for Gemini
    research_path = memory_path('RESEARCH-LOG.md')
    research_log = research_path.read_text(encoding='utf-8') if research_path.exists() else ''
    today_research_match = re.search(
        rf'### RESEARCH-{today}(.*?)(?=### RESEARCH-|\Z)',
        research_log, re.DOTALL
    )
    today_research = today_research_match.group(1)[:2000] if today_research_match else ''

    # Get last N lines of TRADE-LOG to capture today's activity
    today_trade_lines = '\n'.join(
        line for line in trade_log.splitlines()[-200:]
        if today in line or any(t in line for t in today_trades)
    )[:3000]

    closed_summary = "\n".join(
        f"- {t['symbol']} closed at ₹{t['exit_price']} | {t['pnl_pct']:+.2f}% | {t['exit_reason']}"
        for t in closed_today
    )

    reflection = gemini_reason(
        system=(
            'You are a trading analyst writing a brief end-of-day reflection. '
            'Identify the ONE biggest surprise from today — the most unexpected moment, '
            'positive or negative. Be specific: include symbol names, actual % moves, '
            'and what was expected vs realized. Do NOT propose rule changes — that is for Friday review. '
            'Just record the observation in 1-2 sentences.'
        ),
        user=(
            f"Today: {today}\n"
            f"Day P&L: {day_pnl_pct:+.2f}% | Nifty: {nifty_pct:+.2f}% | Alpha: {alpha:+.2f}%\n"
            f"Entries today: {entries_today}, Exits today: {exits_today}\n\n"
            f"Closed positions today:\n{closed_summary}\n\n"
            f"Today's research log entry (key signals):\n{today_research[:1500]}\n"
        ),
        schema_hint='{"surprise": "1-2 sentence observation, specific and concrete"}'
    )
    if isinstance(reflection, dict) and 'surprise' in reflection:
        surprise = reflection['surprise']
    else:
        # DETERMINISTIC FALLBACK — both LLMs failed. Build surprise from numbers.
        if closed_today:
            biggest = max(closed_today, key=lambda t: abs(t.get('pnl_pct', 0)))
            surprise = (f"[auto] {biggest['symbol']} {biggest['pnl_pct']:+.1f}% "
                        f"({biggest.get('exit_reason','?')}) was today's largest move.")
        elif best_pos and worst_pos:
            surprise = (f"[auto] Open book ranged {worst_pos['pnl_pct']:+.1f}% "
                        f"({worst_pos['symbol']}) to {best_pos['pnl_pct']:+.1f}% ({best_pos['symbol']}).")
        else:
            surprise = f"[auto] Day moved {day_pnl_pct:+.2f}% vs Nifty {nifty_pct:+.2f}%."
    print(f"  surprise: {surprise}")

# ── Step 6: Append EOD snapshot to TRADE-LOG ─────────────────────────────────
print("[eod] appending EOD snapshot")
positions_md = ""
for p in positions:
    ltp = float(p.get('ltp', p['avg_price']))
    pnl = (ltp - p['avg_price']) / p['avg_price'] * 100
    positions_md += f"  - {p['symbol']}: {p['qty']} sh @ avg ₹{p['avg_price']:.2f} | close ₹{ltp:.2f} | P&L {pnl:+.2f}%\n"

snapshot = (
    f"\n### EOD Snapshot {today}\n"
    f"- **Portfolio value**: ₹{total_val:,.2f}\n"
    f"- **Cash**: ₹{cash:,.2f}\n"
    f"- **Open positions**: {len(positions)}\n"
    f"- **Market value**: ₹{market_val:,.2f}\n"
    f"- **Day P&L**: ₹{day_pnl:,.2f} ({day_pnl_pct:+.2f}%)\n"
    f"- **All-time P&L**: ₹{all_time_pnl:,.2f} ({all_time_pct:+.2f}% from ₹5,00,000 base)\n"
    f"- **Nifty 50 today**: {nifty_pct:+.2f}%\n"
    f"- **Alpha vs Nifty**: {alpha:+.2f}%\n"
)
if positions_md:
    snapshot += f"- **Positions**:\n{positions_md}"
if surprise:
    snapshot += f"\n**🎯 Biggest surprise today**: {surprise}\n"

p = memory_path('TRADE-LOG.md')
existing = p.read_text(encoding='utf-8') if p.exists() else '# Trade Log\n\n'
p.write_text(existing + snapshot, encoding='utf-8')

# Friday note if today is Friday
if now_ist().weekday() == 4:
    rlog = memory_path('RESEARCH-LOG.md')
    if rlog.exists():
        txt = rlog.read_text(encoding='utf-8')
        rlog.write_text(txt + f"\n**Friday note {today}**: Weekly review routine runs at 4:30 PM IST.\n", encoding='utf-8')

# ── Step 7: Curated Telegram ─────────────────────────────────────────────────
print("[eod] sending Telegram")
positions_brief = ", ".join(
    f"{p['symbol']} {((float(p.get('ltp', p['avg_price'])) - p['avg_price']) / p['avg_price'] * 100):+.0f}%"
    for p in positions[:5]
) or "none"

if is_active:
    msg = (
        f"🌙 EOD {today}\n\n"
        f"📊 P&L: ₹{day_pnl:,.0f} ({day_pnl_pct:+.2f}%) | Nifty: {nifty_pct:+.2f}% | Alpha: {alpha:+.2f}%\n"
        f"Portfolio: ₹{total_val:,.0f} (all-time {all_time_pct:+.2f}%)\n\n"
        f"Today: entered {entries_today}, exited {exits_today}\n"
    )
    if best_pos:
        msg += f"Best: {best_pos['symbol']} {best_pos['pnl_pct']:+.1f}%"
    if worst_pos and worst_pos['symbol'] != (best_pos['symbol'] if best_pos else None):
        msg += f" | Worst: {worst_pos['symbol']} {worst_pos['pnl_pct']:+.1f}%"
    msg += f"\n\nOpen ({len(positions)}): {positions_brief}\nCash: ₹{cash:,.0f}\n"
    if surprise:
        msg += f"\n🎯 Biggest surprise: {surprise}\n"
    msg += "\nTomorrow: pre-market 8:30 AM."
else:
    msg = (
        f"🌙 EOD {today}\n\n"
        f"Day P&L: ₹{day_pnl:,.0f} ({day_pnl_pct:+.2f}%) | Nifty: {nifty_pct:+.2f}% | Alpha: {alpha:+.2f}%\n"
        f"Portfolio: ₹{total_val:,.0f}\n\n"
        f"Open ({len(positions)}): {positions_brief}\n"
        f"Cash: ₹{cash:,.0f}\n\n"
        f"Tomorrow: pre-market 8:30 AM."
    )

telegram_send(msg)
write_heartbeat('eod', 'ok', f"day {day_pnl_pct:+.2f}%, portfolio Rs {total_val:,.0f}")
print(f"[eod] done. day_pnl_pct={day_pnl_pct:+.2f}% active={is_active}")
