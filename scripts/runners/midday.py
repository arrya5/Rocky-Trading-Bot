#!/usr/bin/env python3
"""Midday routine — 1:30 PM IST.

SWING v3 logic. Only intra-day stop check. No new entries.

Per position:
  - Hard stop -5% → close at LTP
  - +6% gain + no partial yet → sell half, tighten stop to -3% below LTP
  - +12% gain → tighten trail to -3% below LTP
  - Held >= 15 trading days → force close (swing max hold)
  - News check via Gemini; if thesis broken → close
"""
import sys, os, json, re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import (
    gemini_research, gemini_reason, telegram_send, broker, today_str,
    run_script, memory_path, write_heartbeat, REPO_ROOT,
)

today = today_str()
print(f"[midday] starting {today}")
write_heartbeat('midday', 'started')

# ── Step 1: Account + positions ──────────────────────────────────────────────
account   = broker('account')
positions = broker('positions')
if not isinstance(positions, list):
    positions = []

if not positions:
    telegram_send(f"☀️ Midday Check {today} — No open positions. Cash: ₹{account.get('cash', 0):,.0f}. Next check: EOD 3:45 PM.")
    print("[midday] no positions, exit")
    sys.exit(0)

# Refresh quotes for all positions (broker.py quote updates LTP in paper portfolio)
symbols = [p['symbol'] for p in positions]
broker('quote', *symbols)
positions = broker('positions')  # re-read with updated LTPs

# ── Step 2: Apply rules to each position ─────────────────────────────────────
stops_hit  = []
partials   = []
news_exits = []
holding    = []
log_lines  = []

outcomes_path = memory_path('trade-outcomes.json')
outcomes = json.loads(outcomes_path.read_text(encoding='utf-8')) if outcomes_path.exists() else {'trades': []}

def has_partial(sym: str) -> bool:
    for t in outcomes.get('trades', []):
        if t.get('symbol') == sym and t.get('exit_date') is None:
            return bool(t.get('partial_exits'))
    return False

def days_held(sym: str) -> int:
    """Trading days between entry and today. None if not found."""
    from datetime import date as _date
    for t in outcomes.get('trades', []):
        if t.get('symbol') == sym and t.get('exit_date') is None:
            try:
                ed = _date.fromisoformat(t.get('entry_date'))
                td = _date.today()
                # Approximate trading days = calendar days * 5/7 (close enough)
                return max(0, (td - ed).days)
            except Exception:
                return 0
    return 0

MAX_HOLD_DAYS = 15  # swing v3 hard limit

max_hold_exits = []

for pos in positions:
    sym = pos['symbol']
    ltp = float(pos.get('ltp', pos.get('avg_price', 0)))
    avg = float(pos['avg_price'])
    qty = int(pos['qty'])
    pnl_pct = (ltp - avg) / avg * 100
    held = days_held(sym)

    print(f"\n[{sym}] LTP=Rs{ltp:.2f} avg=Rs{avg:.2f} P&L={pnl_pct:+.2f}% held={held}d")

    # SWING v3 thresholds
    hard_stop = avg * 0.95   # -5% (was -7%)

    # Rule MAX-HOLD — force close at 15 trading days
    if held >= MAX_HOLD_DAYS:
        print(f"  MAX HOLD ({held}d >= {MAX_HOLD_DAYS}d) — closing")
        broker('close', sym)
        run_script('scripts/record_trade.py', 'exit', sym, f"{ltp:.2f}", 'max_hold', capture=False)
        telegram_send(
            f"⏰ MAX HOLD: {sym} | Closed @ Rs{ltp:.2f} | P&L: {pnl_pct:+.2f}% | "
            f"Held {held}d (swing v3 max=15d)"
        )
        log_lines.append(
            f"**Midday {today} 13:30**: {sym} MAX-HOLD @ Rs{ltp:.2f} ({pnl_pct:+.2f}%) — held {held}d, CLOSED"
        )
        max_hold_exits.append(sym)
        continue

    # Rule A — Hard stop (-5% in swing v3)
    if ltp <= hard_stop:
        print(f"  HARD STOP triggered")
        broker('close', sym)
        run_script('scripts/record_trade.py', 'exit', sym, f"{ltp:.2f}", 'hard_stop', capture=False)
        telegram_send(
            f"⚠️ STOP HIT: {sym} | Closed @ Rs{ltp:.2f} | P&L: {pnl_pct:+.2f}% | -5% hard stop"
        )
        log_lines.append(
            f"**Midday {today} 13:30**: {sym} STOP HIT @ Rs{ltp:.2f} ({pnl_pct:+.2f}%) — CLOSED"
        )
        stops_hit.append(sym)
        continue

    # Rule B — Partial exit at +6% (was +15%)
    if pnl_pct >= 6 and not has_partial(sym):
        half = qty // 2
        if half >= 1:
            print(f"  PARTIAL EXIT: selling {half}")
            order_payload = json.dumps({
                'symbol': sym, 'qty': half, 'side': 'sell',
                'type': 'market', 'product': 'D'
            })
            broker('order', order_payload)
            run_script('scripts/record_trade.py', 'partial_exit', sym, f"{ltp:.2f}", str(half), capture=False)
            new_stop = round(ltp * 0.97, 2)  # tightened to -3% below current
            telegram_send(
                f"🟡 PARTIAL EXIT: {sym} | Sold {half} @ Rs{ltp:.2f} | "
                f"Locked +{pnl_pct:.1f}% | Stop tightened to Rs{new_stop} (-3%)"
            )
            log_lines.append(
                f"**Midday {today} 13:30**: {sym} PARTIAL — sold {half} @ Rs{ltp:.2f}, "
                f"remaining {qty - half} | stop Rs{new_stop}"
            )
            partials.append(sym)
            continue

    # Rule C — Trail stop tighten at +12% (was +20%)
    if pnl_pct >= 12:
        new_stop = round(ltp * 0.97, 2)  # -3% trail (was -5%)
        print(f"  +12% gain — trail stop tightened to Rs{new_stop}")
        log_lines.append(
            f"**Midday {today} 13:30**: {sym} HOLD @ Rs{ltp:.2f} ({pnl_pct:+.2f}%, {held}d) — trail Rs{new_stop}"
        )
        holding.append((sym, pnl_pct))
        continue

    # Rule D — News check
    news = gemini_research(
        f"{sym} NSE news today {today}: any negative developments, downgrade, fraud, "
        f"earnings miss, regulatory issue. Be brief — 1 sentence."
    )
    if news and '[no response]' not in news.lower() and '[gemini_api_key not set]' not in news.lower():
        broken_check = gemini_reason(
            system='You decide if news represents a thesis-breaking event for a momentum trade. '
                   'Negative downgrade, fraud allegations, confirmed earnings miss, regulatory action = broken. '
                   'Minor news, general market commentary = not broken.',
            user=f"News snippet: {news[:500]}",
            schema_hint='{"broken": true|false, "reason": "one-line"}'
        )
        if isinstance(broken_check, dict) and broken_check.get('broken'):
            print(f"  THESIS BROKEN: {broken_check.get('reason')}")
            broker('close', sym)
            run_script('scripts/record_trade.py', 'exit', sym, f"{ltp:.2f}", 'thesis_broken', capture=False)
            telegram_send(
                f"🔴 THESIS BROKEN: {sym} | Closed @ ₹{ltp:.2f} | "
                f"P&L: {pnl_pct:+.2f}% | {broken_check.get('reason', 'news')}"
            )
            log_lines.append(
                f"**Midday {today} 13:30**: {sym} THESIS BROKEN @ ₹{ltp:.2f} ({pnl_pct:+.2f}%) — "
                f"{broken_check.get('reason')}"
            )
            news_exits.append(sym)
            continue

    # Otherwise — holding
    log_lines.append(
        f"**Midday {today} 13:30**: {sym} HOLD @ Rs{ltp:.2f} ({pnl_pct:+.2f}%, {held}d) — stop Rs{hard_stop:.2f} (-5%)"
    )
    holding.append((sym, pnl_pct))

# ── Step 3: Append midday notes to TRADE-LOG ─────────────────────────────────
if log_lines:
    p = memory_path('TRADE-LOG.md')
    existing = p.read_text(encoding='utf-8') if p.exists() else '# Trade Log\n\n'
    p.write_text(existing + '\n' + '\n'.join(log_lines) + '\n', encoding='utf-8')

# ── Step 4: Curated Telegram summary ─────────────────────────────────────────
positions_lines = []
account2 = broker('account')
total_val = float(account2.get('total_value', 0)) if isinstance(account2, dict) else 0

for sym, pnl in holding:
    state = "HOLD" if abs(pnl) < 5 else ("WATCH ↑" if pnl > 0 else "WATCH ↓")
    positions_lines.append(f"• {sym}: {pnl:+.1f}% — {state}")

actions_lines = []
if stops_hit:       actions_lines.append(f"• Stops hit (-5%): {', '.join(stops_hit)}")
if partials:        actions_lines.append(f"• Partial exits (+6%): {', '.join(partials)}")
if max_hold_exits:  actions_lines.append(f"• Max-hold exits (15d): {', '.join(max_hold_exits)}")
if news_exits:      actions_lines.append(f"• Thesis broken: {', '.join(news_exits)}")

total_actions = len(stops_hit) + len(partials) + len(max_hold_exits) + len(news_exits)
reading = (
    "All positions holding — no action needed"
    if total_actions == 0
    else f"Took {total_actions} risk actions, riding remaining {len(holding)}"
)

msg = (
    f"☀️ Midday Check {today}\n\n"
    f"Portfolio: ₹{total_val:,.0f}\n\n"
)
if positions_lines:
    msg += "Positions:\n" + "\n".join(positions_lines) + "\n\n"
if actions_lines:
    msg += "Actions today:\n" + "\n".join(actions_lines) + "\n\n"
msg += f"Reading: {reading}\nNext check: EOD 3:45 PM."

telegram_send(msg)
write_heartbeat('midday', 'ok', f"stops={len(stops_hit)} partials={len(partials)} maxhold={len(max_hold_exits)} holding={len(holding)}")
print(f"[midday] done. stops={len(stops_hit)} partials={len(partials)} max_hold={len(max_hold_exits)} news_exits={len(news_exits)} holding={len(holding)}")
