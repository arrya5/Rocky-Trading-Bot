"""Shared utilities for all routine runners."""
import os, json, sys, subprocess
import urllib.request, urllib.error
from datetime import datetime
import pytz

IST = pytz.timezone('Asia/Kolkata')

def now_ist():
    return datetime.now(IST)

def today_str():
    return now_ist().strftime('%Y-%m-%d')


def gemini_research(query: str) -> str:
    api_key = os.environ.get('GEMINI_API_KEY', '')
    if not api_key:
        return '[GEMINI_API_KEY not set]'

    payload = {
        'contents': [{'role': 'user', 'parts': [{'text': query}]}],
        'tools': [{'google_search': {}}],
        'systemInstruction': {
            'parts': [{'text': (
                'You are a financial research assistant for Indian stock markets (NSE/BSE). '
                'Be concise and factual. Extract specific numbers when present: '
                'VIX values, FII/DII flows in crores, index levels, percentages. '
                'Keep response to 2-3 sentences max.'
            )}]
        },
        'generationConfig': {'temperature': 0.1, 'maxOutputTokens': 512}
    }

    url = (
        'https://generativelanguage.googleapis.com/v1beta/models/'
        f'gemini-2.5-flash:generateContent?key={api_key}'
    )
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.load(r)
    except urllib.error.HTTPError as e:
        return f'[API error {e.code}]'
    except Exception as e:
        return f'[Request error: {str(e)[:80]}]'

    candidates = data.get('candidates', [])
    if not candidates:
        return '[No response]'
    content = candidates[0].get('content', {})
    return ''.join(p.get('text', '') for p in content.get('parts', []))


def telegram_send(message: str):
    token   = os.environ.get('TELEGRAM_BOT_TOKEN', '')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID', '')
    if not token or not chat_id:
        print(f'[Telegram not configured] {message}')
        return
    payload = json.dumps({'chat_id': chat_id, 'text': message}).encode('utf-8')
    url = f'https://api.telegram.org/bot{token}/sendMessage'
    req = urllib.request.Request(url, data=payload,
                                 headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=10):
            pass
    except Exception as e:
        print(f'Telegram error: {e}', file=sys.stderr)


def broker(cmd: str, *args):
    """Call broker.py and return parsed JSON output."""
    result = subprocess.run(
        ['python', 'scripts/broker.py', cmd, *args],
        capture_output=True, text=True
    )
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return result.stdout.strip()
