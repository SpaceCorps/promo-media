#!/bin/bash
# Rebuild the feeds from schedule.json and push them if anything new is due (used by .github/workflows/feeds.yml).
set -euo pipefail
git config user.name "spacecorps-promo"
git config user.email "promo@users.noreply.github.com"
git pull --quiet --rebase origin main
python3 scripts/feeds.py
git add feeds
git diff --cached --quiet || { git commit -m "feeds: $(date -u +%FT%H:%MZ)"; git push --quiet origin HEAD:main; }
