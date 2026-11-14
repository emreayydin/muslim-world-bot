#!/bin/zsh
# Separate Chrome just for the Muslim World TikTok account (own cookies/login),
# so the other TikTok accounts in the normal Chrome stay untouched.
# Port 9341 (localhost only) lets the bot drive exactly this window via CDP.
D="$HOME/Library/Application Support/MuslimWorld-Chrome"
if pgrep -f "user-data-dir=$D" >/dev/null && curl -s -m 2 http://127.0.0.1:9341/json/version >/dev/null; then
  exit 0  # already running with the control port
fi
open -na "Google Chrome" --args --user-data-dir="$D" --profile-directory=Default --no-first-run \
  --remote-debugging-port=9341 --remote-debugging-address=127.0.0.1 "${1:-https://www.tiktok.com/tiktokstudio/upload}"
for i in {1..20}; do curl -s -m 1 http://127.0.0.1:9341/json/version >/dev/null && exit 0; sleep 0.5; done
echo "Chrome control port did not come up" >&2; exit 1
