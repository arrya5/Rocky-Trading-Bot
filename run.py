"""
run.py — Standalone entry point for the trading bot.
No Claude Code subscription required.

Usage:
    python run.py pre_market     # 8:30 AM IST
    python run.py market_open    # 9:20 AM IST
    python run.py midday         # 12:30 PM IST
    python run.py eod            # 3:45 PM IST

Schedule with Windows Task Scheduler:
    powershell -ExecutionPolicy Bypass -File setup_scheduler.ps1
"""
import sys
import os
from pathlib import Path

# ── Load .env ─────────────────────────────────────────────────────────────────
# Try project root first, fall back to trading-bot-india subfolder
ROOT = Path(__file__).parent

try:
    from dotenv import load_dotenv
    for candidate in [ROOT / '.env', ROOT / 'trading-bot-india' / '.env']:
        if candidate.exists():
            load_dotenv(candidate)
            print(f"[run.py] Loaded env from {candidate}")
            break
except ImportError:
    print("[run.py] python-dotenv not installed — relying on system env vars")

# ── Validate key env vars ─────────────────────────────────────────────────────
missing = [v for v in ['GEMINI_API_KEY', 'TELEGRAM_BOT_TOKEN', 'TELEGRAM_CHAT_ID']
           if not os.environ.get(v)]
if missing:
    print(f"[run.py] WARNING: Missing env vars: {', '.join(missing)}")

# ── Route to correct runner ───────────────────────────────────────────────────
VALID_ROUTINES = ['pre_market', 'market_open', 'midday', 'eod']

if len(sys.argv) < 2:
    print(f"Usage: python run.py [{' | '.join(VALID_ROUTINES)}]")
    sys.exit(1)

routine = sys.argv[1].lower()
if routine not in VALID_ROUTINES:
    print(f"Unknown routine '{routine}'. Choose from: {', '.join(VALID_ROUTINES)}")
    sys.exit(1)

# Make sure the working directory is the project root
os.chdir(ROOT)

# Add runners to path so `from common import ...` works inside each runner
runners_dir = str(ROOT / 'scripts' / 'runners')
if runners_dir not in sys.path:
    sys.path.insert(0, runners_dir)

print(f"[run.py] Starting routine: {routine}")

# Importing the module executes all top-level code in it (that's the design)
if routine == 'pre_market':
    import scripts.runners.pre_market          # noqa: F401
elif routine == 'market_open':
    import scripts.runners.market_open         # noqa: F401
elif routine == 'midday':
    import scripts.runners.midday              # noqa: F401
elif routine == 'eod':
    import scripts.runners.eod                 # noqa: F401
