#!/bin/zsh
# Separate Chrome just for the Muslim World TikTok account (own cookies/login),
# so the other TikTok accounts in the normal Chrome stay untouched.
open -na "Google Chrome" --args --user-data-dir="/Users/emre.cya/Library/Application Support/MuslimWorld-Chrome" --profile-directory=Default --no-first-run "${1:-https://www.tiktok.com/login}"
