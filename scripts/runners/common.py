"""Shared utilities for all routine runners.

Uses Gemini 2.5 Flash for both research (Google Search grounded) and reasoning
(structured JSON output for orchestration tasks Claude used to handle).
"""
import os, json, sys, subprocess, re
import urllib.request, urllib.error
from datetime import datetime
from pathlib import Path

try:
    import pytz
    IST = pytz.timezone('Asia/Kolkata')
    def now_ist():
        return datetime.now(IST)
except ImportError:
    # Fallback if pytz missing
    from datetime import timezone, timedelta
    IST = timezone(timedelta(hours=5, minutes=30))
    def now_ist():
        return datetime.now(IST)


REPO_ROOT = Path(__file__).resolve().parents[2]


def today_str() -> str:
    return now_ist().strftime('%Y-%m-%d')


# ── Gemini calls ──────────────────────────────────────────────────────────────

def _gemini_call(payload: dict, model: str = 'gemini-2.5-flash', timeout: int = 30) -> dict | None:
    api_key = os.environ.get('GEMINI_API_KEY', '')
    if not api_key:
        return None
    url = f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}'
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        body = e.read().decode()[:200] if hasattr(e, 'read') else ''
        print(f'[Gemini API {e.code}] {body}', file=sys.stderr)
        return None
    except Exception as e:
        print(f'[Gemini error] {str(e)[:120]}', file=sys.stderr)
        return None


def _extract_text(resp: dict | None) -> str:
    if not resp:
        return ''
    cands = resp.get('candidates', [])
    if not cands:
        return ''
    parts = cands[0].get('content', {}).get('parts', [])
    return ''.join(p.get('text', '') for p in parts if not p.get('thought'))


def gemini_research(query: str, max_tokens: int = 512) -> str:
    """Gemini with Google Search grounding. Use for factual/market research."""
    payload = {
        'contents': [{'role': 'user', 'parts': [{'text': query}]}],
        'tools': [{'google_search': {}}],
        'systemInstruction': {'parts': [{'text': (
            'You are a financial research assistant for Indian stock markets (NSE/BSE). '
            'Be concise and factual. Extract specific numbers when present: '
            'VIX values, FII/DII flows in crores, index levels, percentages. '
            'Keep response to 2-3 sentences max unless multiple data points need listing.'
        )}]},
        'generationConfig': {'temperature': 0.1, 'maxOutputTokens': max_tokens},
    }
    text = _extract_text(_gemini_call(payload))
    return text or '[no response]'


def gemini_reason(system: str, user: str, schema_hint: str = '',
                  max_tokens: int = 600, json_mode: bool = True) -> dict | str:
    """Gemini for STRUCTURED reasoning (no web search).

    If json_mode=True, expects JSON output (responseMimeType=application/json).
    Returns parsed dict on success, or {'error': '...'} on failure.
    """
    full_user = user + ('\n\nReturn ONLY valid JSON: ' + schema_hint if schema_hint else '')
    cfg = {'temperature': 0.2, 'maxOutputTokens': max_tokens}
    if json_mode:
        cfg['responseMimeType'] = 'application/json'

    payload = {
        'contents': [{'role': 'user', 'parts': [{'text': full_user}]}],
        'systemInstruction': {'parts': [{'text': system}]},
        'generationConfig': cfg,
    }
    text = _extract_text(_gemini_call(payload))
    if not text:
        return {'error': 'empty_response'} if json_mode else ''

    if not json_mode:
        return text

    # Strip markdown fences if present
    text = re.sub(r'^```(?:json)?\s*', '', text).strip()
    text = re.sub(r'\s*```$', '', text).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {'error': 'parse_failed', 'raw': text[:300]}


def classify_catalyst(symbol: str, catalyst_text: str) -> dict:
    """Use Gemini to classify a catalyst as HARD / MEDIUM / SOFT."""
    schema = '{"tier": "HARD|MEDIUM|SOFT", "type": "earnings|upgrade|breakout|sector_tailwind|technical|other", "summary": "one-line"}'
    system = (
        'You classify trade catalysts for an Indian equity momentum bot. Three tiers:\n'
        '- HARD: earnings beat, analyst upgrade to BUY/Strong Buy, product launch, regulatory approval, '
        'M&A, QIP, buyback, court ruling, contract win. PASS.\n'
        '- MEDIUM: specific sector policy (PLI, budget allocation), index inclusion, '
        'management guidance upgrade, institutional block deal. PASS.\n'
        '- SOFT: "stock is trending", "sector doing well", pure technical breakout with no fundamental event, '
        'general sentiment, vague news. FAIL (reject).'
    )
    user = f'Symbol: {symbol}\n\nCatalyst description from research:\n{catalyst_text[:800]}'
    result = gemini_reason(system, user, schema)
    if isinstance(result, dict) and 'tier' in result:
        return result
    return {'tier': 'SOFT', 'type': 'other', 'summary': 'classification failed'}


# ── Telegram ─────────────────────────────────────────────────────────────────

def telegram_send(message: str) -> bool:
    token = os.environ.get('TELEGRAM_BOT_TOKEN', '')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID', '')
    if not token or not chat_id:
        print(f'[Telegram not configured] {message[:200]}')
        return False
    payload = json.dumps({'chat_id': chat_id, 'text': message}).encode('utf-8')
    url = f'https://api.telegram.org/bot{token}/sendMessage'
    req = urllib.request.Request(url, data=payload,
                                 headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=10):
            return True
    except Exception as e:
        print(f'Telegram error: {e}', file=sys.stderr)
        return False


# ── Broker ──────────────────────────────────────────────────────────────────

def broker(cmd: str, *args):
    """Call scripts/broker.py and return parsed JSON output."""
    result = subprocess.run(
        ['python', str(REPO_ROOT / 'scripts' / 'broker.py'), cmd, *args],
        capture_output=True, text=True, cwd=str(REPO_ROOT)
    )
    out = result.stdout.strip()
    try:
        return json.loads(out)
    except json.JSONDecodeError:
        return out


def run_script(path: str, *args, capture: bool = True) -> str:
    """Run a project script and return its stdout."""
    result = subprocess.run(
        ['python', str(REPO_ROOT / path), *args],
        capture_output=capture, text=True, cwd=str(REPO_ROOT)
    )
    if capture:
        return result.stdout
    return ''


# ── Memory file helpers ─────────────────────────────────────────────────────

def memory_path(name: str) -> Path:
    return REPO_ROOT / 'memory' / name


def append_to_memory(filename: str, content: str) -> None:
    p = memory_path(filename)
    existing = p.read_text(encoding='utf-8') if p.exists() else ''
    p.write_text(existing + content, encoding='utf-8')


def insert_research_log(today: str, entry: str) -> None:
    """Insert a RESEARCH-LOG entry after the header template (or append)."""
    p = memory_path('RESEARCH-LOG.md')
    existing = p.read_text(encoding='utf-8') if p.exists() else '# Research Log\n\n'
    # Find first '---' marker (end of template section) and insert after
    marker = '\n---\n'
    idx = existing.find(marker)
    if idx >= 0:
        # Insert after the FIRST --- (which ends the header template)
        insert_pos = idx + len(marker)
        updated = existing[:insert_pos] + '\n' + entry + existing[insert_pos:]
    else:
        updated = existing + '\n' + entry
    p.write_text(updated, encoding='utf-8')


# ── Number parsing helpers ──────────────────────────────────────────────────

def parse_vix(text: str) -> float | None:
    """Extract VIX value from Gemini research text."""
    patterns = [
        r'India\s*VIX[^\d]{0,30}?(\d+\.\d+)',
        r'VIX[^\d]{0,30}?(\d+\.\d+)',
        r'(\d+\.\d+)\s*[^\d]{0,10}?VIX',
    ]
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            try:
                v = float(m.group(1))
                if 5 < v < 100:  # sanity range
                    return v
            except ValueError:
                continue
    return None


def parse_fii(text: str) -> float | None:
    """Extract FII net flow in Cr from text. Negative = outflow."""
    # Look for patterns like "FII net sold ₹2,500 Cr" or "FII bought ₹1,200 crore"
    patterns = [
        r'FII[^.]*?(?:sold|outflow|net sell|sellers)[^\d\-]*?([\d,]+\.?\d*)\s*(?:Cr|crore)',
        r'FII[^.]*?(?:bought|inflow|net buy|buyers)[^\d\-]*?([\d,]+\.?\d*)\s*(?:Cr|crore)',
        r'FII[^.]*?net[^\d\-+]*?([\-\+]?[\d,]+\.?\d*)\s*(?:Cr|crore)',
        r'FII[^₹\d\-+]*?([\-\+]?\s*[\d,]+\.?\d*)\s*[Cc]r',
    ]
    for i, pat in enumerate(patterns):
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            try:
                v = float(m.group(1).replace(',', '').replace(' ', ''))
                if i == 0:  # "sold/outflow" → negative
                    return -abs(v)
                if i == 1:  # "bought/inflow" → positive
                    return abs(v)
                return v
            except ValueError:
                continue
    return None
