#!/usr/bin/env bash
# telegram.sh — Send Telegram notifications via Bot API (free, no third-party number needed)
#
# Setup (one-time, takes 2 minutes):
#   1. Open Telegram → search @BotFather → send /newbot
#   2. Give it a name (e.g. "India Trading Bot") and a username (e.g. "myindia_trade_bot")
#   3. BotFather gives you a TOKEN — set it as TELEGRAM_BOT_TOKEN env var on the cloud routine
#   4. Open your new bot in Telegram and send it any message (e.g. "hello")
#   5. Visit in browser: https://api.telegram.org/bot<TOKEN>/getUpdates
#   6. Find "chat":{"id": XXXXXXXXX} — that number is your TELEGRAM_CHAT_ID
#   7. Set TELEGRAM_CHAT_ID as env var on the cloud routine
#
# Usage:
#   ./scripts/telegram.sh "Your message here"
#   ./scripts/telegram.sh "Trade executed: RELIANCE BUY 10 @ ₹2500"

set -euo pipefail

MESSAGE="${1:-}"
if [[ -z "$MESSAGE" ]]; then
    echo "Usage: $0 \"Your message\"" >&2
    exit 1
fi

BOT_TOKEN="${TELEGRAM_BOT_TOKEN:-}"
CHAT_ID="${TELEGRAM_CHAT_ID:-}"

if [[ -z "$BOT_TOKEN" || -z "$CHAT_ID" ]]; then
    echo "ERROR: TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID environment variables are not set" >&2
    exit 1
fi

RESPONSE=$(curl -s -w "\n%{http_code}" \
    -X POST "https://api.telegram.org/bot${BOT_TOKEN}/sendMessage" \
    -H "Content-Type: application/json" \
    -d "{\"chat_id\": \"${CHAT_ID}\", \"text\": $(python3 -c "import json,sys; print(json.dumps(sys.argv[1]))" "$MESSAGE"), \"parse_mode\": \"HTML\"}")

HTTP_CODE=$(echo "$RESPONSE" | tail -1)
BODY=$(echo "$RESPONSE" | head -1)

if [[ "$HTTP_CODE" == "200" ]]; then
    echo "Telegram sent: $MESSAGE"
else
    echo "ERROR sending Telegram (HTTP $HTTP_CODE): $BODY" >&2
    exit 1
fi
