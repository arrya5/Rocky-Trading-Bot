#!/usr/bin/env python3
"""Midday routine — 1:30 PM IST.

Production-equivalent of CCR Midday Risk Scan.
Only intra-day stop check. No new entries.

Per position:
  - Hard stop -7% → close at LTP
  - +15% gain + no partial yet → sell half, tighten stop to -7% below LTP
  - +20% gain → tighten trail to -5% below LTP
  - News check via Gemini; if thesis broken → close
"""
import sys, os, json, re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import (
    gemini_research, gemini_reason, telegram_send, broker, today_str,
    run_script, memory_path, REPO_ROOT,
)

today = today_str()
print(f"[midday] starting {today}")

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

for pos in positions:
    sym = pos['symbol']
    ltp = float(pos.get('ltp', pos.get('avg_price', 0)))
    avg = float(pos['avg_price'])
    qty = int(pos['qty'])
    pnl_pct = (ltp - avg) / avg * 100

    print(f"\n[{sym}] LTP=₹{ltp:.2f} avg=₹{avg:.2f} P&L={pnl_pct:+.2f}%")

    hard_stop = avg * 0.93

    # Rule A — Hard stop
    if ltp <= hard_stop:
        print(f"  HARD STOP triggered")
        broker('close', sym)
        run_script('scripts/record_trade.py', 'exit', sym, f"{ltp:.2f}", 'hard_stop', capture=False)
        telegram_send(
            f"⚠️ STOP HIT: {sym} | Closed @ ₹{ltp:.2f} | P&L: {pnl_pct:+.2f}% | -7% hard stop"
        )
        log_lines.append(
            f"**Midday {today} 13:30**: {sym} STOP HIT @ ₹{ltp:.2f} ({pnl_pct:+.2f}%) — CLOSED"
        )
        stops_hit.append(sym)
        continue

    # Rule B — Partial exit at +15%
    if pnl_pct >= 15 and not has_partial(sym):
        half = qty // 2
        if half >= 1:
            print(f"  PARTIAL EXIT: selling {half}")
            order_payload = json.dumps({
                'symbol': sym, 'qty': half, 'side': 'sell',
                'type': 'market', 'product': 'D'
            })
            broker('order', order_payload)
            run_script('scripts/record_trade.py', 'partial_exit', sym, f"{ltp:.2f}", str(half), capture=False)
            new_stop = round(ltp * 0.93, 2)
            telegram_send(
                f"🟡 PARTIAL EXIT: {sym} | Sold {half} @ ₹{ltp:.2f} | "
                f"Locked +{pnl_pct:.1f}% | Stop tightened to ₹{new_stop}"
            )
            log_lines.append(
                f"**Midday {today} 13:30**: {sym} PARTIAL — sold {half} @ ₹{ltp:.2f}, "
                f"remaining {qty - half} | stop ₹{new_stop}"
            )
            partials.append(sym)
            continue

    # Rule C — Trailing stop tighten at +20%
    if pnl_pct >= 20:
        new_stop = round(ltp * 0.95, 2)
        print(f"  +20% gain — trail stop tightened to ₹{new_stop}")
        log_lines.append(
            f"**Midday {today} 13:30**: {sym} HOLD @ ₹{ltp:.2f} ({pnl_pct:+.2f}%) — trail stop ₹{new_stop}"
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
        f"**Midday {today} 13:30**: {sym} HOLD @ ₹{ltp:.2f} ({pnl_pct:+.2f}%) — stop ₹{hard_stop:.2f}"
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
if stops_hit:  actions_lines.append(f"• Stops hit: {', '.join(stops_hit)}")
if partials:   actions_lines.append(f"• Partial exits: {', '.join(partials)}")
if news_exits: actions_lines.append(f"• Thesis broken: {', '.join(news_exits)}")

reading = (
    "All positions holding — no action needed"
    if not (stops_hit or partials or news_exits)
    else f"Took {len(stops_hit) + len(partials) + len(news_exits)} risk actions, riding remaining {len(holding)}"
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
print(f"[midday] done. stops={len(stops_hit)} partials={len(partials)} news_exits={len(news_exits)} holding={len(holding)}")
