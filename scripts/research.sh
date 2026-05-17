#!/usr/bin/env bash
# research.sh — AI-summarized research via Gemini API + Google Search grounding
#
# Usage:
#   bash scripts/research.sh "your research question"
#   bash scripts/research.sh "India VIX level today 2026-05-17"
#
# Free tier: 1,500 requests/day via Google AI Studio
# Get key at: https://aistudio.google.com/apikey

set -euo pipefail

QUERY="${1:-}"
if [[ -z "$QUERY" ]]; then
    echo "Usage: $0 \"your question\"" >&2
    exit 1
fi

API_KEY="${GEMINI_API_KEY:-}"
if [[ -z "$API_KEY" ]]; then
    echo "ERROR: Set GEMINI_API_KEY in .env" >&2
    exit 1
fi

PYTHONUTF8=1 python -c "
import json, sys, urllib.request, urllib.error

query   = sys.argv[1]
api_key = sys.argv[2]

payload = {
    'contents': [
        {'role': 'user', 'parts': [{'text': query}]}
    ],
    'tools': [{'google_search': {}}],
    'systemInstruction': {
        'parts': [{
            'text': (
                'You are a financial research assistant focused on Indian stock markets (NSE/BSE). '
                'Be concise and factual. Extract specific numbers when available: '
                'index levels, VIX values, FII/DII flows in crores, percentages. '
                'Focus on actionable trading information.'
            )
        }]
    },
    'generationConfig': {'temperature': 0.1, 'maxOutputTokens': 1024}
}

url = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}'
req = urllib.request.Request(
    url,
    data=json.dumps(payload).encode(),
    headers={'Content-Type': 'application/json'}
)

try:
    with urllib.request.urlopen(req) as resp:
        data = json.load(resp)
except urllib.error.HTTPError as e:
    print(f'ERROR {e.code}: {e.read().decode()}', file=sys.stderr)
    sys.exit(1)

candidates = data.get('candidates', [])
if not candidates:
    print('No response from Gemini.')
    sys.exit(0)

content = candidates[0].get('content', {})
text = ''.join(p.get('text', '') for p in content.get('parts', []))

print(f'Research: {query}')
print('=' * 60)
print(text)

grounding = candidates[0].get('groundingMetadata', {})
chunks = grounding.get('groundingChunks', [])
if chunks:
    print()
    print('Sources:')
    for i, chunk in enumerate(chunks[:6], 1):
        web = chunk.get('web', {})
        title = web.get('title', 'No title')
        uri   = web.get('uri', '')
        print(f'  [{i}] {title}')
        print(f'       {uri}')
" "$QUERY" "$API_KEY"
