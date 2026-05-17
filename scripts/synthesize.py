#!/usr/bin/env python3
"""
synthesize.py — Pre-market synthesis using Claude extended thinking

Reads today's research data (regime, PCR, VIX, FII, candidates) from
memory/RESEARCH-LOG.md and TRADING-STRATEGY.md, then calls the Anthropic
API with extended thinking enabled to produce a nuanced verdict that catches
cross-signal contradictions a pure if/else gate cannot detect.

Usage:
  python scripts/synthesize.py --date 2026-05-19

Output (stdout):
  JSON with: verdict, reasoning_summary, risk_flags, confidence, trade_limit

Requires: ANTHROPIC_API_KEY environment variable
"""

import json, os, re, sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).parent.parent

STRATEGY_FILE = ROOT / "memory" / "TRADING-STRATEGY.md"
RESEARCH_FILE = ROOT / "memory" / "RESEARCH-LOG.md"
CLAUDE_FILE   = ROOT / "CLAUDE.md"

THINKING_BUDGET = 6000   # tokens — enough for cross-signal reasoning without over-spending
MODEL           = "claude-sonnet-4-6"


def _extract_today_research(date_str: str) -> str:
    """Pull today's RESEARCH-LOG.md entry (everything between ### RESEARCH-DATE and next ###)."""
    if not RESEARCH_FILE.exists():
        return "No research log found for today."
    text = RESEARCH_FILE.read_text(encoding="utf-8")
    pattern = rf"### RESEARCH-{re.escape(date_str)}(.*?)(?=\n### |\Z)"
    m = re.search(pattern, text, re.DOTALL)
    if not m:
        return f"No research entry found for {date_str}."
    return m.group(0).strip()


def synthesize(date_str: str) -> dict:
    import anthropic

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)

    today_research = _extract_today_research(date_str)
    strategy       = STRATEGY_FILE.read_text(encoding="utf-8") if STRATEGY_FILE.exists() else ""
    rulebook       = CLAUDE_FILE.read_text(encoding="utf-8")   if CLAUDE_FILE.exists() else ""

    system_prompt = (
        "You are Rocky, an autonomous Indian equity trading agent managing a ₹5,00,000 paper portfolio on NSE. "
        "You are doing the pre-market synthesis step. You have already collected macro data, market regime, PCR, "
        "FII flow, VIX, and candidate stocks. Your job is to reason through ALL the signals together and produce "
        "a single structured verdict. Be honest about contradictions — a borderline VIX with strong FII buying "
        "is different from the same VIX with weak FII. Nuance matters here. Return ONLY valid JSON."
    )

    user_message = f"""Today is {date_str}. Here is the pre-market data collected so far:

=== TODAY'S RESEARCH ===
{today_research}

=== TRADING STRATEGY RULES ===
{strategy}

=== RULEBOOK ===
{rulebook}

Based on ALL of the above signals together (VIX, FII flow, SGX Nifty, regime, PCR, sector momentum, candidates), \
produce a synthesis verdict. Consider contradictions and alignments across signals. For example:
- Is VIX borderline (17-19) but other signals strongly positive? → CAUTION rather than binary SKIP
- Are multiple signals aligned bearishly even if none triggers the hard gate alone? → flag the combined risk
- Does the candidate's sector align with today's sector momentum?

Return ONLY this JSON (no markdown, no extra text):
{{
  "verdict": "PROCEED" | "CAUTION-1-TRADE-MAX" | "CAUTION-AVOID-SECTORS" | "SKIP",
  "confidence": "high" | "medium" | "low",
  "reasoning_summary": "2-3 sentence synthesis of what the signals say together",
  "risk_flags": ["list of specific concerns, empty array if none"],
  "max_trades_today": 1 | 2 | 3,
  "sectors_to_avoid": ["list of sectors if any, empty array if none"],
  "gate_status": {{
    "vix_level": "calm | elevated | borderline | high",
    "fii_sentiment": "positive | neutral | negative | strongly_negative",
    "regime": "bull | bear | sideways",
    "pcr_signal": "euphoric | neutral | fearful"
  }}
}}"""

    response = client.messages.create(
        model=MODEL,
        max_tokens=2000,
        thinking={"type": "enabled", "budget_tokens": THINKING_BUDGET},
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
    )

    # Extract text output (skip thinking blocks)
    output_text = ""
    for block in response.content:
        if block.type == "text":
            output_text = block.text.strip()
            break

    # Strip markdown fences if present
    output_text = re.sub(r"^```(?:json)?\s*", "", output_text)
    output_text = re.sub(r"\s*```$", "", output_text)

    try:
        result = json.loads(output_text)
    except json.JSONDecodeError:
        result = {
            "verdict": "PROCEED",
            "confidence": "low",
            "reasoning_summary": "Synthesis parse error — defaulting to PROCEED. Check synthesize.py output.",
            "risk_flags": ["JSON parse failed on synthesis output"],
            "max_trades_today": 3,
            "sectors_to_avoid": [],
            "gate_status": {},
            "raw_output": output_text,
        }

    return result


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=date.today().isoformat())
    args = parser.parse_args()

    result = synthesize(args.date)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
