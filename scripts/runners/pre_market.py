"""Pre-market routine — 8:30 AM IST.
Research macro conditions, get GRU signals, write RESEARCH-LOG.md.
"""
import sys, os, re, subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import gemini_research, telegram_send, today_str

today = today_str()
print(f"Pre-market starting: {today}")

# ── Step 1: Macro research ────────────────────────────────────────────────────
print("Running macro research...")
sgx     = gemini_research(f"SGX Nifty premarket level today {today} — gap up or gap down for Nifty 50")
vix     = gemini_research(f"India VIX current level today {today} and what it signals for volatility")
fii     = gemini_research(f"FII DII net buying selling NSE today {today} — figures in crores")
global_ = gemini_research(f"Global market cues {today}: US futures, crude oil, dollar index, Asia")
events  = gemini_research(f"Indian stock market key events {today}: earnings, RBI, SEBI, macro data")
sector  = gemini_research(f"NSE sector performance {today}: leading and lagging sectors vs Nifty 50")

# ── Step 2: Parse VIX number ─────────────────────────────────────────────────
vix_level = None
for pattern in [r'VIX[^\d]*?(\d+\.\d+)', r'(\d+\.\d+)[^\d]*?VIX']:
    m = re.search(pattern, vix, re.IGNORECASE)
    if m:
        vix_level = float(m.group(1))
        break

high_vix = vix_level is not None and vix_level >= 20
vix_str  = f"{vix_level:.2f}" if vix_level else "unknown"
print(f"India VIX: {vix_str} | High VIX: {high_vix}")

# ── Step 3: Parse FII flow ────────────────────────────────────────────────────
fii_level = None
m = re.search(r'FII[^₹\d\-]*?([\-\+]?\s*[\d,]+\.?\d*)\s*[Cc]r', fii)
if m:
    try:
        fii_level = float(m.group(1).replace(',', '').replace(' ', ''))
    except ValueError:
        pass
fii_str = f"{fii_level:+.0f} Cr" if fii_level is not None else "unknown"

# ── Step 4: Ask Gemini for today's top stock candidates ───────────────────────
candidates = []
if not high_vix:
    print("Getting stock candidates from Gemini...")
    raw = gemini_research(
        f"Today is {today}. Name exactly 5 NSE stock symbols (Nifty 50 or Nifty Midcap 150) "
        f"with the strongest momentum and catalysts right now. "
        f"Return ONLY the NSE ticker symbols comma-separated, nothing else. "
        f"Example: RELIANCE,TCS,INFY,HDFCBANK,ICICIBANK"
    )
    # Extract uppercase symbols (2-15 chars, letters/digits/hyphen/ampersand)
    raw_symbols = re.findall(r'\b([A-Z][A-Z0-9&\-]{1,14})\b', raw)
    candidates = [s for s in raw_symbols if len(s) >= 2][:5]
    print(f"Candidates: {candidates}")

# ── Step 5: GRU signals on candidates ────────────────────────────────────────
buy_signals = []
if candidates:
    print(f"Running GRU signals on: {candidates}")
    result = subprocess.run(
        ['python', 'models/signal_generator.py'] + candidates,
        capture_output=True, text=True
    )
    print(result.stdout)
    if result.returncode == 0:
        for line in result.stdout.splitlines():
            line_up = line.upper()
            if 'BUY' in line_up:
                m = re.search(r'([A-Z][A-Z0-9&\-]{1,14})', line)
                c = re.search(r'(\d+\.?\d*)%', line)
                if m and c:
                    conf = float(c.group(1))
                    if conf >= 60:
                        buy_signals.append({'symbol': m.group(1), 'confidence': conf})

print(f"BUY signals (>=60%): {buy_signals}")

# ── Step 6: Research each buy candidate ──────────────────────────────────────
stock_notes = {}
for sig in buy_signals[:5]:
    sym = sig['symbol']
    stock_notes[sym] = gemini_research(
        f"{sym} NSE catalyst today {today}: earnings, upgrade, technical breakout, news"
    )

# ── Step 7: Write RESEARCH-LOG.md ────────────────────────────────────────────
candidates_md = ""
if not high_vix and buy_signals:
    for i, sig in enumerate(buy_signals, 1):
        sym  = sig['symbol']
        conf = sig['confidence']
        note = stock_notes.get(sym, 'No catalyst data')
        candidates_md += f"\n{i}. {sym} — GRU: BUY {conf:.0f}% | {note[:150]}\n"
elif high_vix:
    candidates_md = "\nNone — HIGH VIX, no new positions today.\n"
else:
    candidates_md = "\nNone — No GRU BUY signals >= 60% today.\n"

recommendation = (
    "HIGH VIX — NO NEW POSITIONS TODAY" if high_vix
    else (f"PROCEED — {len(buy_signals)} candidate(s)" if buy_signals
          else "WAIT — No qualifying signals")
)

entry = f"""
### RESEARCH-{today}

**Market Context**
- SGX Nifty: {sgx[:200]}
- India VIX: {vix_str} — {'HIGH: no new positions' if high_vix else vix[:150]}
- FII/DII: {fii_str} | {fii[:150]}
- Global: {global_[:200]}

**Sector Momentum**
{sector[:300]}

**Trade Candidates** (GRU BUY >= 60%){candidates_md}
**Key Events**
{events[:300]}

**Recommendation**: {recommendation}

**Sources**: [Gemini + Google Search]

---
"""

log_path = Path('memory/RESEARCH-LOG.md')
existing = log_path.read_text(encoding='utf-8')

# Insert after the last --- in the template header
insert_marker = '---\n'
idx = existing.rfind(insert_marker)
if idx != -1:
    updated = existing[:idx + len(insert_marker)] + entry + existing[idx + len(insert_marker):]
else:
    updated = existing + entry

log_path.write_text(updated, encoding='utf-8')
print("RESEARCH-LOG.md updated.")

# ── Step 8: Telegram alert ────────────────────────────────────────────────────
top = buy_signals[0]['symbol'] if buy_signals else 'None'
telegram_send(
    f"Pre-market {today} | VIX: {vix_str} | "
    f"{len(buy_signals)} BUY signal(s) | Top: {top} | "
    f"FII: {fii_str} | Market-open at 9:20 AM IST"
)

print(f"Pre-market done. VIX={vix_str}, candidates={len(buy_signals)}")
