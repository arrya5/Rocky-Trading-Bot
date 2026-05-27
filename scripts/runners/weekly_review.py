#!/usr/bin/env python3
"""Weekly Review routine — Friday 4:30 PM IST.

Production-equivalent of CCR Weekly Strategy Review.
Runs performance_analyzer.py, generates qualitative weekly note via Gemini,
applies rule changes only if sufficient_data (>= 20 closed trades).
"""
import sys, os, json, re
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent))
from common import (
    gemini_research, gemini_reason, telegram_send, today_str, now_ist,
    memory_path, run_script, REPO_ROOT,
)

today = today_str()
print(f"[weekly-review] starting {today}")

# ── Step 1: Read context ─────────────────────────────────────────────────────
trade_log_path = memory_path('TRADE-LOG.md')
trade_log = trade_log_path.read_text(encoding='utf-8') if trade_log_path.exists() else ''

# ── Step 2: Nifty weekly perf ────────────────────────────────────────────────
nifty_q = gemini_research(f"Nifty 50 weekly performance week ending {today} — percentage change")
nifty_pct = 0.0
m = re.search(r'([\-\+]?\d+\.\d+)\s*%', nifty_q)
if m:
    try: nifty_pct = float(m.group(1))
    except ValueError: pass

# ── Step 3: Run performance analyzer ─────────────────────────────────────────
print("[2/5] running performance_analyzer.py")
analyzer_raw = run_script('scripts/performance_analyzer.py')
analyzer = {}
try:
    analyzer = json.loads(analyzer_raw)
except Exception as e:
    print(f"  performance_analyzer parse failed: {e}", file=sys.stderr)

sufficient = analyzer.get('sufficient_data', False)
n_closed = analyzer.get('total_closed_trades', 0)
recommendations = analyzer.get('recommendations', [])
print(f"  closed trades: {n_closed}, sufficient: {sufficient}")

# ── Step 4: Compute weekly stats from EOD snapshots ──────────────────────────
week_ago = (now_ist() - timedelta(days=6)).strftime('%Y-%m-%d')
eod_snapshots = re.findall(
    r'### EOD Snapshot (\d{4}-\d{2}-\d{2}).*?Portfolio value\*\*:\s*₹([\d,]+\.?\d*)',
    trade_log, re.DOTALL
)
this_week_snaps = [(d, float(v.replace(',', ''))) for d, v in eod_snapshots if d >= week_ago]

week_start_val = 500000.0
week_end_val = 500000.0
if this_week_snaps:
    week_end_val = this_week_snaps[-1][1]
    # Find Monday's start (i.e., previous EOD)
    earlier = [s for s in eod_snapshots if s[0] < week_ago]
    if earlier:
        week_start_val = float(earlier[-1][1].replace(',', ''))
    else:
        week_start_val = this_week_snaps[0][1]

week_pnl = week_end_val - week_start_val
week_pnl_pct = week_pnl / week_start_val * 100 if week_start_val else 0
alpha_pct = week_pnl_pct - nifty_pct

# Grade
if week_pnl_pct > 0 and alpha_pct > 0:
    grade = "A"
elif week_pnl_pct > 0 or alpha_pct > 0:
    grade = "B"
elif week_pnl_pct < 0 and alpha_pct > 0:
    grade = "C"
elif week_pnl_pct < -10:
    grade = "F"
else:
    grade = "D"

print(f"  week P&L: {week_pnl_pct:+.2f}% | Nifty: {nifty_pct:+.2f}% | Alpha: {alpha_pct:+.2f}% | Grade: {grade}")

# ── Step 5: Qualitative review via Gemini ────────────────────────────────────
qualitative = "(no analysis - insufficient data)"
overall_stats = analyzer.get('overall', {})
by_sector = analyzer.get('by_sector', {})
by_regime = analyzer.get('by_regime', {})
by_catalyst = analyzer.get('by_catalyst_type', {})

if n_closed > 0:
    review = gemini_reason(
        system=(
            'You are an equity trading strategist writing a weekly review. '
            'Be honest and specific. Use real numbers from the data. '
            'Highlight patterns the human should notice. Do NOT propose rule changes '
            '(that is done separately via the analyzer recommendations). '
            'Focus on: what worked, what did not, and one observation worth tracking.'
        ),
        user=(
            f"Week ending {today}\n"
            f"Week P&L: {week_pnl_pct:+.2f}% | Nifty: {nifty_pct:+.2f}% | Alpha: {alpha_pct:+.2f}%\n"
            f"Grade: {grade}\n"
            f"Total closed trades (all time): {n_closed}\n\n"
            f"Overall stats: {json.dumps(overall_stats)[:500]}\n\n"
            f"By sector: {json.dumps(by_sector)[:500]}\n\n"
            f"By regime: {json.dumps(by_regime)[:300]}\n\n"
            f"By catalyst type: {json.dumps(by_catalyst)[:500]}\n"
        ),
        schema_hint='{"worked": "1-2 sentences", "didnt_work": "1-2 sentences", "observation": "1 sentence worth tracking"}'
    )
    if isinstance(review, dict):
        qualitative = (
            f"What worked: {review.get('worked', '-')}\n"
            f"What didn't: {review.get('didnt_work', '-')}\n"
            f"Observation: {review.get('observation', '-')}"
        )

# ── Step 6: Apply rule changes (only if sufficient_data) ─────────────────────
applied_changes = []
if sufficient and recommendations:
    print(f"[3/5] {len(recommendations)} recommendations to evaluate")
    strategy_path = memory_path('TRADING-STRATEGY.md')
    strategy_text = strategy_path.read_text(encoding='utf-8') if strategy_path.exists() else ''

    # Apply the FIRST recommendation only (one change per week per CCR design)
    rec = recommendations[0]
    if 'change_instruction' in rec and 'parameter' in rec:
        instruction = rec['change_instruction']
        # Append a CHANGELOG line to TRADING-STRATEGY.md at end
        strategy_text += (
            f"\n\n<!-- AUTO-APPLIED {today}: {rec['parameter']} -->\n"
            f"<!-- Evidence: {rec.get('evidence', '')} -->\n"
            f"<!-- Action: {instruction} -->\n"
        )
        strategy_path.write_text(strategy_text, encoding='utf-8')
        applied_changes.append(rec)
        print(f"  applied: {rec['parameter']}")
else:
    print(f"[3/5] no rule changes (sufficient_data={sufficient}, {len(recommendations)} recs)")

# ── Step 7: Write WEEKLY-REVIEW.md entry ─────────────────────────────────────
print("[4/5] writing WEEKLY-REVIEW.md")
changes_md = "- None this week"
if applied_changes:
    changes_md = "\n".join(
        f"- {r['parameter']}: {r.get('recommended', r.get('change_instruction', ''))[:150]}"
        for r in applied_changes
    )
elif recommendations and not sufficient:
    changes_md = f"- No rule changes (only {n_closed}/20 closed trades — observing, not changing rules yet)"

entry = (
    f"\n### WEEK OF {(now_ist() - timedelta(days=4)).strftime('%Y-%m-%d')} to {today}\n\n"
    f"**P&L Summary**\n"
    f"- Week P&L: ₹{week_pnl:,.2f} ({week_pnl_pct:+.2f}%)\n"
    f"- Nifty 50 this week: {nifty_pct:+.2f}%\n"
    f"- Alpha vs Nifty: {alpha_pct:+.2f}%\n"
    f"- Grade: {grade}\n\n"
    f"**Closed trades (all time)**: {n_closed}\n"
    f"**Performance analyzer data sufficient**: {sufficient}\n\n"
    f"**Qualitative**\n{qualitative}\n\n"
    f"**Strategy Changes This Week**\n{changes_md}\n\n"
    f"---\n"
)

review_path = memory_path('WEEKLY-REVIEW.md')
existing = review_path.read_text(encoding='utf-8') if review_path.exists() else '# Weekly Review Log\n\n'
review_path.write_text(existing + entry, encoding='utf-8')

# ── Step 8: Telegram ─────────────────────────────────────────────────────────
print("[5/5] sending Telegram")
msg = (
    f"📅 Weekly Review {today}\n"
    f"Grade: {grade}\n"
    f"Week P&L: ₹{week_pnl:,.0f} ({week_pnl_pct:+.2f}%)\n"
    f"Nifty: {nifty_pct:+.2f}% | Alpha: {alpha_pct:+.2f}%\n"
    f"Closed trades (all time): {n_closed}\n"
)
if applied_changes:
    msg += f"\nRule changes applied: {len(applied_changes)}\n"
elif n_closed < 20:
    msg += f"\nNo rule changes — {n_closed}/20 trades needed for analyzer to activate.\n"
else:
    msg += f"\nNo rule changes recommended this week.\n"

telegram_send(msg)
print(f"[weekly-review] done. grade={grade} changes_applied={len(applied_changes)}")
