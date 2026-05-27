#!/usr/bin/env python3
"""
health_check.py — Verify Rocky's routines actually fired.

Reads memory/heartbeat.json and checks each expected routine ran today
(on weekdays). Sends a Telegram alert if a routine silently failed to fire.

Run this from a dedicated GitHub Actions workflow at ~4:15 PM IST (after EOD
should have run), or manually any time.

Usage:
  python scripts/health_check.py            # check + alert if stale
  python scripts/health_check.py --quiet    # check, print only (no Telegram)
"""
import json, os, sys, urllib.request
from datetime import datetime, timedelta
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HB_FILE = REPO / "memory" / "heartbeat.json"

try:
    import pytz
    IST = pytz.timezone('Asia/Kolkata')
    def now_ist(): return datetime.now(IST)
except ImportError:
    from datetime import timezone
    IST = timezone(timedelta(hours=5, minutes=30))
    def now_ist(): return datetime.now(IST)


# Routines expected to run each WEEKDAY, with the IST hour by which they should
# have fired. Weekly review only on Friday.
EXPECTED_WEEKDAY = {
    "pre_market":  8,    # 8:30 AM
    "market_open": 9,    # 9:20 AM
    "midday":      13,   # 1:30 PM
    "eod":         15,   # 3:45 PM
}
EXPECTED_FRIDAY_EXTRA = {
    "weekly_review": 16,  # 4:30 PM Friday
}


def telegram_send(message: str) -> bool:
    token = os.environ.get('TELEGRAM_BOT_TOKEN', '')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID', '')
    if not token or not chat_id:
        print(f'[Telegram not configured] {message}')
        return False
    payload = json.dumps({'chat_id': chat_id, 'text': message}).encode('utf-8')
    url = f'https://api.telegram.org/bot{token}/sendMessage'
    req = urllib.request.Request(url, data=payload, headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=10):
            return True
    except Exception as e:
        print(f'Telegram error: {e}', file=sys.stderr)
        return False


def main():
    quiet = '--quiet' in sys.argv
    now = now_ist()
    today = now.strftime('%Y-%m-%d')
    weekday = now.weekday()  # 0=Mon ... 4=Fri, 5=Sat, 6=Sun

    if weekday >= 5:
        print(f"[health] {today} is weekend — no routines expected. OK.")
        return

    expected = dict(EXPECTED_WEEKDAY)
    if weekday == 4:  # Friday
        expected.update(EXPECTED_FRIDAY_EXTRA)

    if not HB_FILE.exists():
        msg = f"⚠️ Rocky health check {today}: heartbeat.json missing — NO routines have run."
        print(msg)
        if not quiet:
            telegram_send(msg)
        sys.exit(1)

    hb = json.loads(HB_FILE.read_text(encoding='utf-8'))

    stale = []
    ran = []
    for routine, due_hour in expected.items():
        rec = hb.get(routine, {})
        last_date = rec.get('date')
        # Only flag if the routine's due hour has passed and it didn't run today
        if now.hour >= due_hour:
            if last_date == today:
                ran.append(f"{routine} ✓ ({rec.get('status','?')})")
            else:
                stale.append(f"{routine} ✗ (last ran {last_date or 'never'})")
        else:
            ran.append(f"{routine} ⏳ (not due yet)")

    if stale:
        msg = (
            f"⚠️ Rocky health check {today}\n"
            f"ROUTINES THAT DID NOT FIRE:\n" + "\n".join(f"  • {s}" for s in stale) +
            f"\n\nRan OK:\n" + "\n".join(f"  • {r}" for r in ran) +
            f"\n\nCheck GitHub Actions tab — a workflow may have failed or been skipped."
        )
        print(msg)
        if not quiet:
            telegram_send(msg)
        sys.exit(1)
    else:
        print(f"[health] {today} OK — all due routines fired:")
        for r in ran:
            print(f"  {r}")


if __name__ == "__main__":
    main()
