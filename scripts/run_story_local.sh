#!/bin/zsh
# Local autopilot for the animated story Shorts (launchd: de.muslimworld.story).
# Runs twice daily; story_short.py keeps the hard cap at 2/day and >= 3h apart.
# caffeinate keeps the Mac awake while each run works.
set -u
REPO="/Users/emre.cya/Projects/muslim-world-bot"
LOCK="/tmp/muslimworld-story.lock"
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:$HOME/.local/bin"
cd "$REPO" || exit 1
mkdir -p logs

# one run at a time
if ! mkdir "$LOCK" 2>/dev/null; then
  echo "$(date) already running - skip"; exit 0
fi
trap 'rmdir "$LOCK"' EXIT

echo "=== $(date) ==="
git pull --rebase --autostash -q origin main || { echo "git sync failed - skip upload so the post history stays safe"; exit 1; }

cd src
caffeinate -i -s ../venv/bin/python story_short.py
rc=$?
cd "$REPO"

if ! git diff --quiet -- history.json tiktok_history.json || [ -n "$(git ls-files --others -- tiktok_history.json)" ]; then
  git add history.json tiktok_history.json
  git commit -q -m "Update history (story short) [skip ci]"
  git push -q origin HEAD:main || echo "git push failed - will retry next run"
fi
exit $rc
