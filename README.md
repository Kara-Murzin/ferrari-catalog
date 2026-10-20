# Ferrari catalog MVP

Two independent parts:

- `scraper/` — collects Ferrari listings from Goo-net (year ≥ 2024, ≤ 50,000 km),
  translates fields to English and writes `site/data.js`. Python 3, no dependencies.
- `site/` — static catalog (`index.html` + `data.js`). Host it anywhere (Netlify, Vercel,
  Cloudflare Pages, any web server). Pages are marked `noindex`.

## Run

```bash
python3 scraper/goonet.py
```

Then open `site/index.html` in a browser.

Filters live at the top of `scraper/goonet.py` (`MIN_YEAR`, `MAX_KM`).
Model names and feature translations live in `scraper/i18n.py`.

## Daily update

Goo-net does not answer GitHub's servers, so the scraper runs on this Mac:
`scripts/update.sh` scrapes and pushes `site/data.js`; GitHub Actions then
publishes `site/` to GitHub Pages.

Schedule it with `crontab -e` (daily at 09:00, the Mac must be awake):

```
0 9 * * * /Users/zhanserik/ferrari-catalog/scripts/update.sh >> /Users/zhanserik/ferrari-catalog/update.log 2>&1
```

Each run rebuilds the list from scratch, so sold cars disappear automatically.
Car detail pages are cached in `data/cache/`, so only new cars are fetched.
If nothing is parsed (layout change / block), the script exits with an error and
keeps the previous `site/data.js`.

`data/cars_full.json` is internal (source URL and dealer for each car); it is not
used by the site — do not publish the `data/` folder.
