"""Carsensor scraper: every left-hand-drive car (ST=L), all makes.

Usage:  python3 scraper/carsensor.py            # crawl list pages -> data/carsensor_list.json
        python3 scraper/carsensor.py --build    # only rebuild site/catalog/data.js from the saved crawl
Then site/catalog/data.js is written (encrypted, see seal.py).
"""
import html
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(__file__))
import cs_i18n  # noqa: E402
import seal  # noqa: E402

BASE = "https://www.carsensor.net"
LIST_URL = BASE + "/usedcar/{page}?ST=L"          # ST=L: 左ハンドル (left-hand drive)
DELAY = 2.0
MAX_PAGES = 600
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0 Safari/537.36"

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CRAWL_JSON = os.path.join(ROOT, "data", "carsensor_list.json")
SITE_JS = os.path.join(ROOT, "site", "catalog", "data.js")


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "ja"})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                body = r.read().decode("utf-8", errors="replace")
            time.sleep(DELAY)
            return body
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            print(f"  ! {url}: {e} (attempt {attempt + 1})", file=sys.stderr)
        except Exception as e:  # noqa: BLE001
            print(f"  ! {url}: {e} (attempt {attempt + 1})", file=sys.stderr)
        time.sleep(DELAY * 5)
    return None


def text(s):
    s = re.sub(r"<[^>]+>", " ", s)
    return re.sub(r"\s+", " ", html.unescape(s).replace("\xa0", " ")).strip()


def man_yen(s):
    m = re.search(r"([\d,]+(?:\.\d+)?)\s*万円", s)
    return round(float(m.group(1).replace(",", "")) * 10_000) if m else None


def parse_list(page_html):
    cars = []
    for block in page_html.split('<div class="cassette ')[1:]:
        cid = re.search(r'id="(A[A-Z]\d+)_cas"', block[:200])
        if not cid:
            continue
        b = re.sub(r"<script.*?</script>", "", block, flags=re.S)
        title = re.search(r'class="cassetteMain__link[^"]*"[^>]*>(.*?)</a>', b, re.S)
        parts = html.unescape(title.group(1)).split("\xa0") if title else []
        brand = re.search(r"</div>\s*<p>([^<]+)</p>\s*<h3 class=\"cassetteMain__title\"", b)
        photo = re.search(r'cassetteMain__mainImg.*?<img src="([^"]+)"', b, re.S)
        info = re.findall(r'<li class="carBodyInfoList__item">([^<]*)', b)
        def price(kind):
            m = re.search(r'class="%s__mainPriceNum">([^<]*)</span>(?:<span class="%s__subPriceNum">([^<]*)</span>)?' % (kind, kind), b)
            if not m or not re.search(r"\d", m.group(1)):
                return None   # 応談 / ASK
            return round(float(m.group(1).replace(",", "") + (m.group(2) or "")) * 10_000)
        spec = {text(k): text(v) for k, v in re.findall(
            r'<dt class="specList__title[^"]*">(.*?)</dt>\s*<dd class="specList__data[^"]*">(.*?)</dd>', b, re.S)}
        area = re.findall(r'<div class="cassetteSub__area">\s*<p>([^<]*)</p>\s*<p>([^<]*)</p>', b)
        shop = re.search(r'cassetteSub__shop">\s*<p class="js_shop"><a [^>]*title="([^"]*)"', b)
        year = re.search(r"(\d{4})", spec.get("年式", ""))
        cars.append({
            "cs_id": cid.group(1),
            "brand_jp": text(brand.group(1)) if brand else "",
            "model_jp": parts[0].strip() if parts else "",
            "grade_jp": parts[1].strip() if len(parts) > 1 else "",
            "body_jp": info[0].strip() if info else "",
            "color_jp": info[1].strip() if len(info) > 1 else "",
            "photo": ("https:" + photo.group(1)) if photo and photo.group(1).startswith("//") else (photo.group(1) if photo else ""),
            "price_total_jpy": price("totalPrice"),
            "price_jpy": price("basePrice"),
            "year": int(year.group(1)) if year else None,
            "mileage_jp": spec.get("走行距離", ""),
            "inspection_jp": spec.get("車検", ""),
            "repair_jp": spec.get("修復歴", ""),
            "warranty_jp": spec.get("保証", ""),
            "maintenance_jp": spec.get("整備", ""),
            "displacement_jp": spec.get("排気量", ""),
            "mission_jp": spec.get("ミッション", ""),
            "pref_jp": area[0][0].strip() if area else "",
            "city_jp": area[0][1].strip() if area else "",
            "shop": html.unescape(shop.group(1)) if shop else "",
        })
    return cars


def crawl():
    all_cars, seen, stale = [], set(), 0
    for n in range(1, MAX_PAGES + 1):
        url = LIST_URL.format(page="" if n == 1 else f"index{n}.html")
        page = fetch(url)
        cars = parse_list(page) if page else []
        new = [c for c in cars if c["cs_id"] not in seen]
        seen.update(c["cs_id"] for c in new)
        all_cars += new
        stale = stale + 1 if not new else 0
        if n % 10 == 0 or not cars:
            print(f"page {n}: {len(cars)} cars, total {len(all_cars)}", flush=True)
        # Past the last page Carsensor serves the last page again, so stop once nothing new appears.
        if not cars or stale >= 3:
            break
    if len(all_cars) < 100:
        sys.exit(f"Only {len(all_cars)} cars parsed - Carsensor layout may have changed. Keeping previous data.")
    os.makedirs(os.path.dirname(CRAWL_JSON), exist_ok=True)
    crawled = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    with open(CRAWL_JSON, "w", encoding="utf-8") as f:
        json.dump({"crawled": crawled, "cars": all_cars}, f, ensure_ascii=False)
    print(f"Saved {len(all_cars)} cars -> {CRAWL_JSON}")
    return crawled, all_cars


def usd_rate():
    """JPY -> USD reference rate (open.er-api.com); falls back to the last saved rate."""
    cache = os.path.join(ROOT, "data", "fx.json")
    try:
        with urllib.request.urlopen("https://open.er-api.com/v6/latest/JPY", timeout=20) as r:
            rates = json.load(r)["rates"]
        with open(cache, "w") as f:
            json.dump({"JPY_USD": rates["USD"], "JPY_KZT": rates.get("KZT"), "JPY_RUB": rates.get("RUB")}, f)
        return rates["USD"]
    except Exception as e:  # noqa: BLE001
        print(f"  ! FX rate: {e}; using cached rate", file=sys.stderr)
        with open(cache) as f:
            return json.load(f)["JPY_USD"]


# Listings that are not cars: trikes, three-wheelers, UTVs, tractors, construction machinery.
NOT_A_CAR = re.compile(r"トライク|TRIKE|トラクター|TRACTOR|ホイルローダー|タイヤショベル|キャタピラー|POLARIS|ポラリス|カンパーニャ|T-REX", re.I)


def is_car(c):
    return not NOT_A_CAR.search(cs_i18n.nfkc(f"{c['brand_jp']} {c['model_jp']} {c['grade_jp']}"))


def build(crawled, cars):
    rate = usd_rate()
    dropped = [c for c in cars if not is_car(c)]
    cars = [c for c in cars if is_car(c)]
    if dropped:
        print(f"  skipped {len(dropped)} non-car listings (trikes, UTVs, tractors...)")
    public, sources, unknown = [], {}, set()
    for c in cars:
        pid = seal.short_id(c["cs_id"])
        car = cs_i18n.to_public(c)
        car["id"] = pid
        public.append(car)
        sources[pid] = f"{BASE}/usedcar/detail/{c['cs_id']}/index.html"
        if car["make"] == c["brand_jp"]:
            unknown.add(c["brand_jp"])
    if unknown:
        print("  untranslated makes:", ", ".join(sorted(unknown)))
    cat_pw, admin_pw = seal.load_passwords()
    payload = {"updated": crawled, "jpy_usd": rate, "fields": cs_i18n.FIELDS, "cars": [[car[k] for k in cs_i18n.FIELDS] for car in public]}
    with open(SITE_JS, "w", encoding="utf-8") as f:
        f.write("window.CATALOG_ENC = ")
        json.dump(seal.encrypt(payload, cat_pw), f)
        f.write(";\nwindow.ADMIN_ENC = ")
        json.dump(seal.encrypt({"sources": sources}, admin_pw), f)
        f.write(";\n")
    print(f"Built {len(public)} cars -> {SITE_JS} ({os.path.getsize(SITE_JS) // 1024} KB), 1 JPY = {rate} USD")


def main():
    if "--build" in sys.argv:
        with open(CRAWL_JSON, encoding="utf-8") as f:
            d = json.load(f)
        build(d["crawled"], d["cars"])
    else:
        build(*crawl())


if __name__ == "__main__":
    main()
