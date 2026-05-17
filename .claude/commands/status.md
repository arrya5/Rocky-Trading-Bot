# /status — Quick health check of the entire bot system

Run these checks and report status:

## 1. Broker Connection
```bash
python scripts/broker.py account
```
Report: PAPER mode / LIVE mode, cash available, portfolio value

## 2. Last Routine Execution
Read memory/TRADE-LOG.md — when was the last EOD snapshot?
Report: last run date/time, any missed days

## 3. Open Positions Count
```bash
python scripts/broker.py positions
```
Report: N/5 positions used

## 4. Signal Generator Check
```bash
python models/signal_generator.py RELIANCE
```
Report: working / error

## 5. Memory Files Check
Check that all 5 memory files exist and have been updated recently:
- memory/TRADING-STRATEGY.md
- memory/TRADE-LOG.md
- memory/RESEARCH-LOG.md
- memory/WEEKLY-REVIEW.md
- memory/PROJECT-CONTEXT.md

## 6. Environment Check
Verify these env vars are set (don't print values, just confirm set/not set):
- UPSTOX_ACCESS_TOKEN
- TELEGRAM_BOT_TOKEN
- TELEGRAM_CHAT_ID
- GEMINI_API_KEY
- PAPER_TRADING

## Output
Present a clean status dashboard:
```
=== Bot Status ===
Mode:           PAPER / LIVE
Broker:         ✅ Connected / ❌ Error
Signal model:   ✅ Working / ❌ Error
Positions:      N/5
Last routine:   YYYY-MM-DD HH:MM
Memory files:   ✅ All present
Env vars:       ✅ All set / ⚠️ Missing: [vars]
```
