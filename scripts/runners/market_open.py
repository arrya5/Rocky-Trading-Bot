#!/usr/bin/env python3
"""Market-open routine — 9:20 AM IST.

Production-equivalent of CCR Market Open Execution.
Reads today's RESEARCH-LOG entry, applies 9-point gate, places paper orders.

9-point gate:
  1. Universe (Nifty 50 + Midcap 150)
  2. Momentum score >= 40 (re-check)
  3. Catalyst tier HARD or MEDIUM (from research log)
  4. Circuit gap < 18%
  5. VIX < 25 (from research log)
  6. Position sizing (tiered 70/50/30k from suggested_position_size)
  7. FII flow > -₹3500 Cr (from research log)
  8. Earnings guard (no earnings within 7 days)
  9. Sector concentration <= 2 open
"""
import sys, os, json, re, subprocess
from pathlib import Path
from datetime import datetime, date

sys.path.insert(0, str(Path(__file__).parent))
from common import (
    gemini_research, telegram_send, broker, today_str, now_ist,
    run_script, memory_path, write_heartbeat, already_ran_today, REPO_ROOT,
)


today = today_str()
print(f"[market-open] starting {today}")
if already_ran_today('market_open'):
    print("[market-open] already ran successfully today - skipping duplicate trigger")
    sys.exit(0)
write_heartbeat('market_open', 'started')

# ── Step 1: Read research log ────────────────────────────────────────────────
log_path = memory_path('RESEARCH-LOG.md')
if not log_path.exists():
    telegram_send(f"📋 Market Open {today} | 0 trades | No RESEARCH-LOG.md found")
    sys.exit(0)

log_text = log_path.read_text(encoding='utf-8')
today_entry_match = re.search(
    rf'### RESEARCH-{today}(.*?)(?=### RESEARCH-|\Z)',
    log_text, re.DOTALL
)
if not today_entry_match:
    telegram_send(f"📋 Market Open {today} | 0 trades | No pre-market research found for today")
    sys.exit(0)

today_entry = today_entry_match.group(1)

# Check macro gates from research log
if 'HIGH VIX' in today_entry:
    telegram_send(f"📋 Market Open {today} | 0 trades | HIGH VIX gate triggered in pre-market")
    sys.exit(0)
if 'LARGE FII OUTFLOW' in today_entry:
    telegram_send(f"📋 Market Open {today} | 0 trades | FII outflow gate triggered in pre-market")
    sys.exit(0)

# Parse VIX and FII from research log for record_trade
vix_val = None
m = re.search(r'India VIX:\s*([\d.]+)', today_entry)
if m: vix_val = float(m.group(1))
fii_val = None
m = re.search(r'FII net flow:\s*([\-\+]?[\d,]+)\s*Cr', today_entry)
if m:
    try:
        fii_val = float(m.group(1).replace(',', '').replace('+', ''))
    except ValueError: pass
regime_val = "unknown"
m = re.search(r'Regime:\s*(\w+)', today_entry)
if m: regime_val = m.group(1).lower()

# ── Step 2: Extract candidates ───────────────────────────────────────────────
candidates = []
cand_section = re.search(
    r'\*\*Trade Candidates\*\*[^\n]*\n(.*?)(?=\*\*Rejected|\*\*Key Events|\Z)',
    today_entry, re.DOTALL
)
if cand_section:
    for block in re.finditer(
        r'\d+\.\s+\*\*([A-Z][A-Z0-9&\-]{1,14})\*\*\s*[—\-]\s*Score:\s*(\d+)/100\s*[—\-]\s*Catalyst:\s*(.+?)\s*\[(HARD|MEDIUM|SOFT)\]\s*[—\-]\s*Chart:\s*([^\n]+)',
        cand_section.group(1)
    ):
        candidates.append({
            'symbol': block.group(1),
            'score': int(block.group(2)),
            'catalyst': block.group(3).strip(),
            'tier': block.group(4),
            'chart': block.group(5).strip(),
        })

if not candidates:
    telegram_send(f"📋 Market Open {today} | 0 trades | No candidates parsed from research log")
    sys.exit(0)

print(f"  parsed {len(candidates)} candidates")

# ── Step 3: Account state ────────────────────────────────────────────────────
account = broker('account')
positions = broker('positions')
if not isinstance(account, dict):
    telegram_send(f"📋 Market Open {today} | ERROR: broker account unavailable")
    sys.exit(1)

cash = float(account.get('cash', 0))
open_positions = positions if isinstance(positions, list) else []
print(f"  cash=₹{cash:,.0f}, {len(open_positions)} open positions")

# Universe set (must match models/signal_generator.py UNIVERSE)
try:
    sys.path.insert(0, str(REPO_ROOT))
    from models.signal_generator import UNIVERSE as UNIVERSE_LIST, SECTOR_MAP
    UNIVERSE = set(UNIVERSE_LIST)
except Exception as e:
    print(f"  warn: couldn't import UNIVERSE: {e}", file=sys.stderr)
    UNIVERSE = set()
    SECTOR_MAP = {}


# ── Step 4: 9-point gate for each candidate ──────────────────────────────────
orders_placed = []
skipped = []
log_lines = []

for cand in candidates:
    sym = cand['symbol']
    print(f"\n[{sym}] checking gates")

    # Gate 1: Universe
    if UNIVERSE and sym not in UNIVERSE:
        skipped.append((sym, 'Gate 1: not in universe'))
        log_lines.append(f"- {sym}: SKIP — Gate 1: not in Nifty 50/Midcap 150")
        continue

    # Gate 3: Catalyst tier
    if cand['tier'] == 'SOFT':
        skipped.append((sym, 'Gate 3: SOFT catalyst'))
        log_lines.append(f"- {sym}: SKIP — Gate 3: soft catalyst only")
        continue

    # Gate 2: Re-verify momentum score >= 40
    sig_raw = run_script('models/signal_generator.py', sym)
    try:
        sig_data = json.loads(sig_raw)
        sig_info = sig_data.get(sym, {})
    except Exception:
        sig_info = {}
    if sig_info.get('signal') != 'BUY' or sig_info.get('confidence', 0) < 80:
        skipped.append((sym, f'Gate 2: signal={sig_info.get("signal","?")} conf={sig_info.get("confidence", 0)}'))
        log_lines.append(f"- {sym}: SKIP — Gate 2: not BUY >=80 (swing v3 threshold)")
        continue

    # Gate 8: Earnings guard
    eg_raw = run_script('scripts/earnings_guard.py', sym)
    try:
        eg_data = json.loads(eg_raw.strip().split('\n')[-1])
    except Exception:
        eg_data = {}
    if eg_data.get('earnings_within_7d'):
        skipped.append((sym, f'Gate 8: earnings in {eg_data.get("event_date", "?")}'))
        log_lines.append(f"- {sym}: SKIP — Gate 8: earnings within 7 days")
        continue

    # Gate 4: Circuit gap check
    quote = broker('quote', sym)
    if not isinstance(quote, dict) or sym not in quote:
        skipped.append((sym, 'Gate 4: no quote'))
        log_lines.append(f"- {sym}: SKIP — Gate 4: no quote available")
        continue
    ltp = float(quote[sym].get('price', 0))
    prev_close = sig_info.get('current_price', ltp)
    gap_pct = abs(ltp - prev_close) / prev_close * 100 if prev_close > 0 else 0
    if gap_pct > 18:
        skipped.append((sym, f'Gate 4: gap {gap_pct:.1f}%'))
        log_lines.append(f"- {sym}: SKIP — Gate 4: gap {gap_pct:.1f}% > 18%")
        continue

    # Gate 9: Sector concentration
    sector = sig_info.get('sector', SECTOR_MAP.get(sym, 'Other'))
    sec_count = sum(1 for p in open_positions if p.get('sector') == sector)
    if sec_count >= 2:
        skipped.append((sym, f'Gate 9: 2 already in {sector}'))
        log_lines.append(f"- {sym}: SKIP — Gate 9: already 2 open in {sector}")
        continue

    # Gate 6: Position sizing (tiered)
    size = sig_info.get('suggested_position_size', 30_000)
    qty = int(size // ltp)
    cost = qty * ltp
    if qty < 1:
        skipped.append((sym, f'Gate 6: qty < 1 at ₹{ltp:.0f}'))
        log_lines.append(f"- {sym}: SKIP — Gate 6: position too small (price ₹{ltp:.0f})")
        continue
    if cost > cash:
        skipped.append((sym, f'Gate 6: cost ₹{cost:.0f} > cash ₹{cash:.0f}'))
        log_lines.append(f"- {sym}: SKIP — Gate 6: insufficient cash")
        continue

    # ── ALL GATES PASSED — place order ───────────────────────────────────────
    print(f"  ✓ all gates passed. BUY {qty} @ ~₹{ltp:.2f}")
    order_payload = json.dumps({
        'symbol': sym, 'qty': qty, 'side': 'buy', 'type': 'market',
        'product': 'D', 'sector': sector,
    })
    order_resp = broker('order', order_payload)
    exec_price = ltp
    if isinstance(order_resp, dict) and order_resp.get('exec_price'):
        exec_price = float(order_resp['exec_price'])

    cash -= exec_price * qty
    open_positions.append({'symbol': sym, 'sector': sector, 'qty': qty, 'avg_price': exec_price})

    # Swing v3 exits: tighter stop (-5%), faster partial (+6%), trail trigger (+12%)
    stop          = round(exec_price * 0.95, 2)   # -5% hard stop
    partial_at    = round(exec_price * 1.06, 2)   # +6% partial exit
    trail_trigger = round(exec_price * 1.12, 2)   # +12% trail activation

    # Record structured trade for learning system
    gru_conf_dec = sig_info.get('confidence', 0) / 100.0
    run_script(
        'scripts/record_trade.py', 'entry',
        sym, sector, f"{gru_conf_dec:.4f}",
        f"{vix_val:.2f}" if vix_val else "0",
        f"{fii_val:.0f}" if fii_val is not None else "0",
        regime_val,
        f"{exec_price:.2f}", str(qty),
        cand.get('catalyst_type', 'other'),
        capture=False,
    )

    # Append to TRADE-LOG.md
    trade_block = (
        f"\n### TRADE-{today.replace('-','')}-{len(orders_placed)+1:03d}\n"
        f"- **Date**: {today}\n"
        f"- **Symbol**: {sym} (NSE)\n"
        f"- **Action**: BUY\n"
        f"- **Qty**: {qty} shares\n"
        f"- **Price**: ₹{exec_price:.2f}\n"
        f"- **Total value**: ₹{exec_price * qty:,.2f}\n"
        f"- **Momentum score**: {sig_info.get('confidence', 0):.0f}/100 | sector: {sector}\n"
        f"- **Catalyst**: {cand['catalyst'][:120]} | tier: {cand['tier']}\n"
        f"- **Stop loss**: ₹{stop} (-5%)\n"
        f"- **Partial exit at**: ₹{partial_at} (+6%, sells half)\n"
        f"- **Trail trigger**: ₹{trail_trigger} (+12%, tightens stop)\n"
        f"- **Max hold**: 15 trading days\n"
        f"- **Status**: OPEN\n"
    )
    log_lines.append(trade_block)

    # Per-trade Telegram
    telegram_send(
        f"🟢 BUY {sym} — ₹{exec_price * qty:,.0f}\n"
        f"{qty} shares @ ₹{exec_price:.2f} | Score {sig_info.get('confidence', 0):.0f}/100 | {sector}\n"
        f"Why: {cand['catalyst'][:100]} [{cand['tier']}]\n"
        f"Stop ₹{stop} (-5%) | Partial ₹{partial_at} (+6%) | Trail ₹{trail_trigger} (+12%) | Max 15d hold"
    )

    orders_placed.append({'symbol': sym, 'qty': qty, 'price': exec_price, 'score': sig_info.get('confidence', 0)})

# ── Step 5: Update TRADE-LOG.md ──────────────────────────────────────────────
if log_lines:
    p = memory_path('TRADE-LOG.md')
    existing = p.read_text(encoding='utf-8') if p.exists() else '# Trade Log\n\n'
    p.write_text(existing + '\n' + '\n'.join(log_lines) + '\n', encoding='utf-8')

# ── Step 6: Summary Telegram ─────────────────────────────────────────────────
if orders_placed:
    top = max(orders_placed, key=lambda o: o['score'])
    skipped_str = "\n".join(f"• {s[0]} — {s[1]}" for s in skipped[:3]) or "• (none)"
    deployed = sum(o['price'] * o['qty'] for o in orders_placed)
    telegram_send(
        f"📋 Market Open Summary\n\n"
        f"Took {len(orders_placed)} trade(s), deployed ₹{deployed:,.0f}\n"
        f"Highest conviction: {top['symbol']} ({top['score']:.0f}/100)\n\n"
        f"Skipped:\n{skipped_str}\n\n"
        f"Cash left: ₹{cash:,.0f} | Watching {len(open_positions)} positions for stops."
    )
else:
    skipped_str = "\n".join(f"• {s[0]} — {s[1]}" for s in skipped[:5]) or "• (no candidates)"
    telegram_send(
        f"📋 Market Open {today} — 0 trades placed\n\n"
        f"All {len(candidates)} candidates filtered:\n{skipped_str}\n\n"
        f"Cash unchanged: ₹{cash:,.0f}. Next opportunity: tomorrow."
    )

write_heartbeat('market_open', 'ok', f"{len(orders_placed)} orders placed")
print(f"[market-open] done. {len(orders_placed)} orders placed.")
