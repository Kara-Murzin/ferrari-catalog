#!/bin/bash
# Scrape Goo-net, then push site/data.js to GitHub (Pages redeploys automatically).
set -euo pipefail
cd "$(dirname "$0")/.."
export PATH="/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin:$PATH"

echo "== $(date '+%Y-%m-%d %H:%M') =="
python3 scraper/goonet.py

if git diff --quiet -- site/data.js; then
  echo "No changes."
  exit 0
fi
git add site/data.js
git commit -m "Update catalog $(date '+%Y-%m-%d')"
git push
