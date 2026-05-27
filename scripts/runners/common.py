"""Shared utilities for all routine runners.

LLM strategy (tiered, free):
  - RESEARCH (factual market data): Gemini ONLY, with Google Search grounding.
    Hermes has no web access, so it is NOT used for research (would hallucinate
    live VIX/FII numbers). On Gemini failure, returns a clear unavailable marker.
  - REASONING (catalyst classification, reflections): Gemini PRIMARY → Hermes
    FALLBACK. Both reason over provided text, no web needed. When Gemini's free
    tier (1500 req/day) is exhausted or errors, Hermes (open-source, via
    OpenRouter or local Ollama) takes over.

Reliability:
  - Retry-with-backoff on all LLM calls
  - Heartbeat written by each routine (memory/heartbeat.json) for health checks
"""
import os, json, sys, subprocess, re, time
import urllib.request, urllib.error
from datetime import datetime
from pathlib import Path

try:
    import pytz
    IST = pytz.timezone('Asia/Kolkata')
    def now_ist():
        return datetime.now(IST)
except ImportError:
    from datetime import timezone, timedelta
    IST = timezone(timedelta(hours=5, minutes=30))
    def now_ist():
        return datetime.now(IST)


REPO_ROOT = Path(__file__).resolve().parents[2]


def today_str() -> str:
    return now_ist().strftime('%Y-%m-%d')


# ── Raw Gemini call (with retry + quota detection) ────────────────────────────

def _gemini_call(payload: dict, model: str = 'gemini-2.5-flash',
                 timeout: int = 30, retries: int = 3) -> dict | None:
    api_key = os.environ.get('GEMINI_API_KEY', '')
    if not api_key:
        return None
    url = f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}'
    for attempt in range(retries):
        req = urllib.request.Request(
            url, data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            code = e.code
            body = e.read().decode()[:200] if hasattr(e, 'read') else ''
            if code == 429:
                print(f'[Gemini quota/rate 429] attempt {attempt+1} — will fall back to Hermes', file=sys.stderr)
                return None  # quota exhausted → signal fallback immediately
            print(f'[Gemini API {code}] attempt {attempt+1}: {body}', file=sys.stderr)
        except Exception as e:
            print(f'[Gemini error attempt {attempt+1}] {str(e)[:120]}', file=sys.stderr)
        if attempt < retries - 1:
            time.sleep(2 ** attempt)
    return None


def _extract_text(resp: dict | None) -> str:
    if not resp:
        return ''
    cands = resp.get('candidates', [])
    if not cands:
        return ''
    parts = cands[0].get('content', {}).get('parts', [])
    return ''.join(p.get('text', '') for p in parts if not p.get('thought'))


# ── Raw Hermes call (OpenAI-compatible: OpenRouter OR local Ollama) ───────────

def _hermes_call(system: str, user: str, json_mode: bool = True,
                 timeout: int = 60, retries: int = 2) -> str:
    """
    Hermes via any OpenAI-compatible endpoint.

    Config via env vars (set in GitHub Secrets or local .env):
      HERMES_API_URL   default: https://openrouter.ai/api/v1/chat/completions
                       local Ollama: http://localhost:11434/v1/chat/completions
      HERMES_API_KEY   OpenRouter/Nous key (not needed for local Ollama)
      HERMES_MODEL     default: nousresearch/hermes-3-llama-3.1-405b
                       local Ollama example: hermes3
    """
    # `or default` handles both unset AND empty-string env vars (GitHub passes
    # empty strings for undefined vars/secrets)
    base_url = os.environ.get('HERMES_API_URL') or 'https://openrouter.ai/api/v1/chat/completions'
    api_key  = os.environ.get('HERMES_API_KEY') or os.environ.get('OPENROUTER_API_KEY') or ''
    model    = os.environ.get('HERMES_MODEL') or 'nousresearch/hermes-3-llama-3.1-405b'

    is_local = 'localhost' in base_url or '127.0.0.1' in base_url
    if not api_key and not is_local:
        return ''  # no key and not local → Hermes unavailable

    payload = {
        'model': model,
        'messages': [
            {'role': 'system', 'content': system},
            {'role': 'user', 'content': user},
        ],
        'temperature': 0.2,
        'max_tokens': 700,
    }
    if json_mode:
        payload['response_format'] = {'type': 'json_object'}

    headers = {'Content-Type': 'application/json'}
    if api_key:
        headers['Authorization'] = f'Bearer {api_key}'

    for attempt in range(retries):
        try:
            req = urllib.request.Request(
                base_url, data=json.dumps(payload).encode('utf-8'), headers=headers
            )
            with urllib.request.urlopen(req, timeout=timeout) as r:
                data = json.load(r)
            return data['choices'][0]['message']['content']
        except Exception as e:
            print(f'[Hermes error attempt {attempt+1}] {str(e)[:120]}', file=sys.stderr)
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
    return ''


def _parse_json_or_text(text: str, json_mode: bool):
    if not json_mode:
        return text
    text = re.sub(r'^```(?:json)?\s*', '', text).strip()
    text = re.sub(r'\s*```$', '', text).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {'error': 'parse_failed', 'raw': text[:300]}


# ── RESEARCH (Gemini only — needs web search) ─────────────────────────────────

def gemini_research(query: str, max_tokens: int = 512) -> str:
    """Gemini with Google Search grounding. NO Hermes fallback — Hermes can't
    search the web and would hallucinate live market numbers."""
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
    return text or '[research unavailable — Gemini failed, no web fallback]'


# ── REASONING (Gemini primary → Hermes fallback) ──────────────────────────────

def gemini_reason(system: str, user: str, schema_hint: str = '',
                  max_tokens: int = 600, json_mode: bool = True) -> dict | str:
    """Structured reasoning. Tries Gemini first; on failure/quota, falls back to
    Hermes (open-source). Both reason over provided context — no web needed."""
    full_user = user + ('\n\nReturn ONLY valid JSON: ' + schema_hint if schema_hint else '')

    # ── Attempt 1: Gemini ────────────────────────────────────────────────────
    cfg = {'temperature': 0.2, 'maxOutputTokens': max_tokens}
    if json_mode:
        cfg['responseMimeType'] = 'application/json'
    payload = {
        'contents': [{'role': 'user', 'parts': [{'text': full_user}]}],
        'systemInstruction': {'parts': [{'text': system}]},
        'generationConfig': cfg,
    }
    text = _extract_text(_gemini_call(payload))
    if text:
        parsed = _parse_json_or_text(text, json_mode)
        if not (isinstance(parsed, dict) and parsed.get('error')):
            return parsed

    # ── Attempt 2: Hermes fallback ───────────────────────────────────────────
    print('[reason] Gemini unavailable → trying Hermes fallback', file=sys.stderr)
    htext = _hermes_call(system, full_user, json_mode=json_mode)
    if htext:
        parsed = _parse_json_or_text(htext, json_mode)
        if not (isinstance(parsed, dict) and parsed.get('error')):
            print('[reason] Hermes fallback succeeded', file=sys.stderr)
            return parsed

    return {'error': 'all_llms_failed'} if json_mode else ''


def classify_catalyst(symbol: str, catalyst_text: str) -> dict:
    """Classify a catalyst as HARD / MEDIUM / SOFT. Uses Gemini→Hermes routing."""
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
    p = memory_path('RESEARCH-LOG.md')
    existing = p.read_text(encoding='utf-8') if p.exists() else '# Research Log\n\n'
    marker = '\n---\n'
    idx = existing.find(marker)
    if idx >= 0:
        insert_pos = idx + len(marker)
        updated = existing[:insert_pos] + '\n' + entry + existing[insert_pos:]
    else:
        updated = existing + '\n' + entry
    p.write_text(updated, encoding='utf-8')


# ── Heartbeat / health monitoring ─────────────────────────────────────────────

def write_heartbeat(routine: str, status: str = 'ok', detail: str = '') -> None:
    """Record that a routine ran. Read by scripts/health_check.py."""
    hb = memory_path('heartbeat.json')
    data = {}
    if hb.exists():
        try:
            data = json.loads(hb.read_text(encoding='utf-8'))
        except Exception:
            data = {}
    data[routine] = {
        'last_run_iso': now_ist().isoformat(timespec='seconds'),
        'date':         today_str(),
        'status':       status,
        'detail':       detail[:200],
    }
    hb.write_text(json.dumps(data, indent=2), encoding='utf-8')


# ── Number parsing helpers ──────────────────────────────────────────────────

def parse_vix(text: str) -> float | None:
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
                if 5 < v < 100:
                    return v
            except ValueError:
                continue
    return None


def parse_fii(text: str) -> float | None:
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
                if i == 0:
                    return -abs(v)
                if i == 1:
                    return abs(v)
                return v
            except ValueError:
                continue
    return None
