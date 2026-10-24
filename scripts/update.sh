#!/bin/bash
# Scrape Carsensor (left-hand drive, all makes), then push site/catalog/data.js to GitHub (Pages redeploys automatically).
set -euo pipefail
cd "$(dirname "$0")/.."
export PATH="/opt/miniconda3/bin:/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin:$PATH"

echo "== $(date '+%Y-%m-%d %H:%M') =="
python3 scraper/carsensor.py

if git diff --quiet -- site/catalog/data.js; then
  echo "No changes."
  exit 0
fi
git add site/catalog/data.js
git commit -m "Update catalog $(date '+%Y-%m-%d')"
git push
