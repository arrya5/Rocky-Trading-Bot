#!/usr/bin/env python3
"""
auth.py — Upstox OAuth2 token generator (run once per trading day)

Steps:
  1. python scripts/auth.py            → prints auth URL
  2. Open URL in browser, log in, copy the 'code' from redirect URL
  3. python scripts/auth.py <code>     → exchanges code for access_token
  4. Token is saved to .upstox_token and printed for UPSTOX_ACCESS_TOKEN

The access token expires daily. Run this each morning before 9:15 AM IST.
"""

import os, sys, json, requests
from datetime import date
from pathlib import Path

API_KEY      = os.getenv("UPSTOX_API_KEY", "")
API_SECRET   = os.getenv("UPSTOX_API_SECRET", "")
REDIRECT_URI = os.getenv("UPSTOX_REDIRECT_URI", "http://localhost")
TOKEN_FILE   = Path(__file__).parent.parent / ".upstox_token"
BASE         = "https://api.upstox.com/v2"

def get_auth_url() -> str:
    return (
        f"https://api.upstox.com/v2/login/authorization/dialog"
        f"?response_type=code"
        f"&client_id={API_KEY}"
        f"&redirect_uri={REDIRECT_URI}"
    )

def exchange_code(auth_code: str) -> str:
    r = requests.post(
        f"{BASE}/login/authorization/token",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "code":          auth_code,
            "client_id":     API_KEY,
            "client_secret": API_SECRET,
            "redirect_uri":  REDIRECT_URI,
            "grant_type":    "authorization_code",
        },
        timeout=10,
    )
    if r.status_code != 200:
        print(f"ERROR {r.status_code}: {r.text}", file=sys.stderr)
        sys.exit(1)
    return r.json()["access_token"]

def load_token() -> str | None:
    if not TOKEN_FILE.exists():
        return None
    data = json.loads(TOKEN_FILE.read_text())
    if data.get("date") == date.today().isoformat():
        return data["token"]
    return None

def save_token(token: str):
    TOKEN_FILE.write_text(json.dumps({"token": token, "date": date.today().isoformat()}))
    TOKEN_FILE.chmod(0o600)

if __name__ == "__main__":
    if not API_KEY or not API_SECRET:
        print("ERROR: Set UPSTOX_API_KEY and UPSTOX_API_SECRET in your .env file")
        sys.exit(1)

    # Check if today's token already exists
    cached = load_token()
    if cached and len(sys.argv) == 1:
        print(f"Today's token already cached.\nUPSTOX_ACCESS_TOKEN={cached}")
        sys.exit(0)

    if len(sys.argv) == 1:
        # Step 1 — print auth URL
        url = get_auth_url()
        print(f"\nOpen this URL in your browser and log in:\n\n  {url}\n")
        print("After login, copy the 'code' parameter from the redirect URL.")
        print("Then run:  python scripts/auth.py <code>\n")

    elif len(sys.argv) == 2:
        # Step 2 — exchange code for token
        code  = sys.argv[1]
        token = exchange_code(code)
        save_token(token)
        print(f"\nAccess token obtained and saved.\n")
        print(f"Add to your shell or .env:\n  UPSTOX_ACCESS_TOKEN={token}\n")
        print(f"Token expires at midnight IST. Run auth.py again tomorrow.")
