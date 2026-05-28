#!/usr/bin/env python3
"""Pre-market routine — 8:30 AM IST.

Production-equivalent of the CCR Pre-Market Research routine, but orchestrated
by Python + Gemini instead of Claude.

Steps:
  1. Macro research via Gemini (SGX, VIX, FII, global, events, sector momentum)
  2. VIX & FII gate check
  3. Regime detection + Nifty PCR
  4. Full universe scan via signal_generator.py (score >= 40)
  5. Earnings guard on top 10 candidates
  6. Chart pattern analysis via Gemini vision
  7. Catalyst research + Gemini HARD/MEDIUM/SOFT classification
  8. Write RESEARCH-LOG.md entry
  9. Send curated Telegram
"""
import sys, os, json, re, subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import (
    gemini_research, gemini_reason, classify_catalyst, telegram_send,
    today_str, parse_vix, parse_fii, run_script, insert_research_log,
    write_heartbeat, already_ran_today, REPO_ROOT,
)

today = today_str()
print(f"[pre-market] starting {today}")
if already_ran_today('pre_market'):
    print("[pre-market] already ran successfully today - skipping duplicate trigger")
    sys.exit(0)
write_heartbeat('pre_market', 'started')

# ── Step 1: Macro research ───────────────────────────────────────────────────
print("[1/9] Macro research")
sgx     = gemini_research(f"SGX Nifty premarket level today {today} — gap up or gap down signal for Nifty 50")
vix     = gemini_research(f"India VIX current level today {today} and what it signals for market volatility")
fii     = gemini_research(f"FII DII net buying selling NSE today {today} — figures in crores")
global_ = gemini_research(f"Global market cues today {today}: US futures, crude oil, dollar index, Asia markets")
events  = gemini_research(f"Indian stock market key events today {today}: earnings results, RBI, SEBI, economic data")
sector_strong = gemini_research(f"NSE sector performance today {today}: leading and lagging sectors vs Nifty 50")

vix_level = parse_vix(vix)
fii_level = parse_fii(fii)
vix_str = f"{vix_level:.2f}" if vix_level else "unknown"
fii_str = f"{fii_level:+.0f} Cr" if fii_level is not None else "unknown"
print(f"  VIX={vix_str} FII={fii_str}")

# ── Step 2: Macro gates ──────────────────────────────────────────────────────
high_vix = vix_level is not None and vix_level >= 25
big_outflow = fii_level is not None and fii_level < -3500

if high_vix:
    msg = f"🚫 Pre-Market {today} — NO TRADES TODAY\n\nReason: VIX {vix_level:.1f} ≥ 25\nMood: high volatility. Capital preserved.\nNext check: tomorrow 8:30 AM."
    insert_research_log(today, f"\n### RESEARCH-{today}\n\n**HIGH VIX — NO NEW POSITIONS TODAY** (VIX {vix_level:.1f})\n- FII: {fii_str}\n- Global: {global_[:200]}\n\n**Recommendation**: HIGH VIX — SKIP\n\n---\n")
    telegram_send(msg)
    print("[pre-market] HIGH VIX gate triggered — exit")
    sys.exit(0)

if big_outflow:
    msg = f"🚫 Pre-Market {today} — NO TRADES TODAY\n\nReason: FII outflow ₹{fii_level:.0f} Cr (beyond -3500)\nCapital preserved.\nNext check: tomorrow 8:30 AM."
    insert_research_log(today, f"\n### RESEARCH-{today}\n\n**LARGE FII OUTFLOW — SKIP TRADING TODAY** (FII {fii_level:+.0f} Cr)\n- VIX: {vix_str}\n- Global: {global_[:200]}\n\n**Recommendation**: LARGE FII OUTFLOW — SKIP\n\n---\n")
    telegram_send(msg)
    print("[pre-market] FII gate triggered — exit")
    sys.exit(0)

# ── Step 3: Regime + PCR ─────────────────────────────────────────────────────
print("[2/9] Regime + PCR")
regime_raw = run_script('scripts/regime_detector.py')
regime = "unknown"
slope = 0.0
markov_line = ""
p_bear_week = None
try:
    regime_data = json.loads(regime_raw)
    regime = regime_data.get('regime', 'unknown')
    slope = regime_data.get('slope_pct', 0.0)
    mk = regime_data.get('markov') or {}
    if isinstance(mk, dict) and mk.get('p_bear_next_week') is not None:
        p_bear_week = mk.get('p_bear_next_week')
        persist = (mk.get('persistence') or {}).get(mk.get('current_regime'))
        persist_str = f"{persist:.0f}%" if isinstance(persist, (int, float)) else "n/a"
        sm = mk.get('stationary_mix') or {}
        markov_line = (
            f"{mk.get('current_regime', '?')} persistence {persist_str}, "
            f"P(bear next week) {p_bear_week}%, "
            f"long-run mix bull/side/bear "
            f"{sm.get('bull', '?')}/{sm.get('sideways', '?')}/{sm.get('bear', '?')}%"
        )
except Exception:
    pass

# SWING v3: bear regime gate — no trades when market is in confirmed downtrend
if regime == 'bear':
    msg = (
        f"🚫 Pre-Market {today} — NO TRADES TODAY\n\n"
        f"Reason: Bear regime (Nifty 20d slope {slope:+.1f}%)\n"
        f"Swing strategy blocks bear-regime entries — momentum factors fail in downtrends.\n"
        f"Next check: tomorrow 8:30 AM."
    )
    insert_research_log(today, f"\n### RESEARCH-{today}\n\n**BEAR REGIME — NO TRADES TODAY**\n- Nifty 20d slope: {slope:+.2f}%\n- VIX: {vix_str} | FII: {fii_str}\n\n**Recommendation**: BEAR REGIME — SKIP\n\n---\n")
    telegram_send(msg)
    print("[pre-market] BEAR REGIME gate triggered — exit")
    sys.exit(0)

pcr_raw = run_script('scripts/market_data.py', 'pcr')
pcr_val = None
pcr_interp = ""
try:
    pcr_data = json.loads(pcr_raw)
    pcr_val = pcr_data.get('pcr')
    pcr_interp = pcr_data.get('interpretation', '')
except Exception:
    pass
pcr_str = f"{pcr_val:.2f}" if pcr_val else "unknown"
print(f"  regime={regime} slope={slope}% PCR={pcr_str}" + (f" | markov: {markov_line}" if markov_line else ""))

# ── Step 4: Full universe scan ───────────────────────────────────────────────
print("[3/9] Universe scan via signal_generator.py")
scan_raw = run_script('models/signal_generator.py')
scan_data = {}
try:
    scan_data = json.loads(scan_raw)
except Exception as e:
    print(f"  signal_generator parse failed: {e}", file=sys.stderr)

# Filter for BUY signals score >= 40 and sort
all_buys = [
    {**v, 'symbol': k}
    for k, v in scan_data.items()
    if isinstance(v, dict) and v.get('signal') == 'BUY' and v.get('confidence', 0) >= 40
]
all_buys.sort(key=lambda x: -x['confidence'])
top_candidates = all_buys[:10]
print(f"  found {len(all_buys)} BUY signals, taking top {len(top_candidates)}")

if not top_candidates:
    msg = f"🌅 Pre-Market {today}\n\nMood: {regime}" + (f" | P(bear/wk) {p_bear_week}%" if p_bear_week is not None else "") + f" | VIX: {vix_str} | FII: {fii_str}\nNo BUY signals found in universe today.\n\nVerdict: WAIT — no candidates.\nNext check: tomorrow."
    insert_research_log(today, f"\n### RESEARCH-{today}\n\n**Market Context**\n- VIX: {vix_str} | FII: {fii_str} | Regime: {regime} (slope {slope}%) | PCR: {pcr_str}\n- Regime forecast (Markov): {markov_line or 'unavailable'}\n\n**Trade Candidates**: NONE — no BUY signals\n\n**Recommendation**: WAIT — No qualifying signals\n\n---\n")
    telegram_send(msg)
    sys.exit(0)

# ── Step 5: Earnings guard ───────────────────────────────────────────────────
print("[4/9] Earnings guard")
symbols = [c['symbol'] for c in top_candidates]
earnings_raw = run_script('scripts/earnings_guard.py', *symbols)
earnings_flags = {}
for line in earnings_raw.splitlines():
    try:
        d = json.loads(line)
        earnings_flags[d.get('symbol')] = d.get('earnings_within_7d', False)
    except Exception:
        continue

surviving = [c for c in top_candidates if not earnings_flags.get(c['symbol'], False)]
earnings_rejected = [c for c in top_candidates if earnings_flags.get(c['symbol'], False)]
print(f"  {len(surviving)} survived earnings guard ({len(earnings_rejected)} rejected)")

# ── Step 6: Chart analysis (up to 5 to save API calls) ───────────────────────
print("[5/9] Chart analysis (Gemini vision)")
chart_results = {}
chart_targets = surviving[:5]
if chart_targets:
    syms = [c['symbol'] for c in chart_targets]
    chart_raw = run_script('scripts/chart_analysis.py', *syms)
    for line in chart_raw.splitlines():
        try:
            d = json.loads(line)
            chart_results[d['symbol']] = d
        except Exception:
            continue

# Remove high-confidence bearish chart contradictions
final_candidates = []
for cand in surviving:
    chart = chart_results.get(cand['symbol'], {})
    if (chart.get('thesis_alignment') == 'contradicts'
        and chart.get('signal') == 'bearish'
        and chart.get('confidence') == 'high'):
        cand['rejected_reason'] = f"Chart bearish high-conf: {chart.get('pattern', '?')}"
        earnings_rejected.append(cand)
        continue
    cand['chart'] = chart
    final_candidates.append(cand)

# ── Step 7: Catalyst research + classification ──────────────────────────────
print(f"[6/9] Catalyst research for {len(final_candidates)} candidates")
for cand in final_candidates:
    sym = cand['symbol']
    catalyst_text = gemini_research(
        f"{sym} NSE catalyst today {today}: earnings, upgrade, technical breakout, sector news, "
        f"company-specific announcements"
    )
    cand['catalyst_text'] = catalyst_text
    cls = classify_catalyst(sym, catalyst_text)
    cand['catalyst_tier'] = cls.get('tier', 'SOFT')
    cand['catalyst_type'] = cls.get('type', 'other')
    cand['catalyst_summary'] = cls.get('summary', catalyst_text[:80])
    print(f"  {sym}: {cand['catalyst_tier']} — {cand['catalyst_summary'][:80]}")

# ── Step 8: Write RESEARCH-LOG.md entry ──────────────────────────────────────
print("[7/9] Writing RESEARCH-LOG.md")
candidates_md = ""
for i, cand in enumerate(final_candidates, 1):
    chart = cand.get('chart', {})
    chart_str = f"{chart.get('signal', '-')}/{chart.get('thesis_alignment', '-')}" if chart else "-"
    candidates_md += (
        f"{i}. **{cand['symbol']}** — Score: {cand['confidence']:.0f}/100 — "
        f"Catalyst: {cand['catalyst_summary'][:100]} [{cand['catalyst_tier']}] — Chart: {chart_str}\n"
        f"   Sector: {cand.get('sector', '?')} | "
        f"Size: ₹{cand.get('suggested_position_size', 0):,} | "
        f"Entry: ~₹{cand.get('current_price', 0)} | "
        f"Stop: ₹{cand.get('current_price', 0) * 0.93:.2f} (-7%)\n"
    )

rejected_md = ""
for cand in earnings_rejected:
    reason = cand.get('rejected_reason') or f"earnings within 7 days"
    rejected_md += f"- {cand['symbol']} — {reason}\n"
if not rejected_md:
    rejected_md = "- (none)\n"

entry = f"""
### RESEARCH-{today}

**Market Context**
- SGX Nifty: {sgx[:200]}
- India VIX: {vix_str} — {'HIGH' if high_vix else ('elevated' if vix_level and vix_level >= 18 else 'calm')}
- FII net flow: {fii_str}
- Global cues: {global_[:250]}
- Regime: {regime} (slope: {slope}%)
- Regime forecast (Markov): {markov_line or 'unavailable'}
- Nifty PCR: {pcr_str} — {pcr_interp}

**Sector Momentum**
{sector_strong[:300]}

**Trade Candidates** (Score ≥ 40, sorted by score)
{candidates_md or '(none after filtering)'}

**Rejected**
{rejected_md}

**Key Events Today**
{events[:300]}

**Recommendation**: PROCEED with {len(final_candidates)} candidates

---
"""
insert_research_log(today, entry)

# ── Step 9: Curated Telegram ─────────────────────────────────────────────────
print("[8/9] Sending Telegram")
top_picks_md = ""
for cand in final_candidates[:3]:
    chart = cand.get('chart', {})
    chart_marker = (
        "✓" if chart.get('thesis_alignment') == 'confirms' else
        "✗" if chart.get('thesis_alignment') == 'contradicts' else
        "○"
    )
    top_picks_md += f"• {cand['symbol']} ({cand['confidence']:.0f}/100) {chart_marker} — {cand['catalyst_summary'][:60]} [{cand['catalyst_tier']}]\n"

# Group skipped reasons
n_earn = len([c for c in earnings_rejected if 'earnings' in c.get('rejected_reason', '')]) + sum(1 for s in symbols if earnings_flags.get(s, False))
n_chart = sum(1 for c in earnings_rejected if 'Chart' in c.get('rejected_reason', ''))
skipped_summary_parts = []
if n_earn:  skipped_summary_parts.append(f"{n_earn} earnings <7d")
if n_chart: skipped_summary_parts.append(f"{n_chart} chart contradicts")
skipped_summary = ", ".join(skipped_summary_parts) or "0"

msg = (
    f"🌅 Pre-Market {today}\n\n"
    f"Mood: {regime} (slope {slope:+.1f}%)" + (f" | P(bear/wk) {p_bear_week}%" if p_bear_week is not None else "") + f" | VIX: {vix_str}\n"
    f"FII: {fii_str} | PCR: {pcr_str}\n\n"
    f"Top picks (score ≥40):\n{top_picks_md}"
    f"\nSkipped {len(earnings_rejected)}: {skipped_summary}\n"
    f"\nVerdict: PROCEED with {len(final_candidates)} candidates. Executing 9:20 AM."
)
telegram_send(msg)

write_heartbeat('pre_market', 'ok', f"{len(final_candidates)} candidates, regime={regime}")
print(f"[pre-market] done. {len(final_candidates)} candidates carried forward.")
