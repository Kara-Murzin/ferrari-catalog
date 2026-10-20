"""Goo-net scraper: Ferrari, model year >= MIN_YEAR, mileage <= MAX_KM.

Usage:  python3 scraper/goonet.py
Writes: data/cars_full.json   (internal: includes source URL and dealer)
        site/data.js          (public: what the catalog shows)
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
import i18n  # noqa: E402

BASE = "https://www.goo-net.com"
LIST_URL = BASE + "/usedcar/brand-FERRARI/list/{page}"
MIN_YEAR = 2024
MAX_KM = 50_000
DELAY = 2.0          # seconds between requests
MAX_PAGES = 40
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0 Safari/537.36"

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE_DIR = os.path.join(ROOT, "data", "cache")
FULL_JSON = os.path.join(ROOT, "data", "cars_full.json")
SITE_JS = os.path.join(ROOT, "site", "data.js")


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "ja"})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                raw = r.read()
            time.sleep(DELAY)
            return raw.decode("euc_jp", errors="replace")
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            print(f"  ! {url}: {e} (attempt {attempt + 1})", file=sys.stderr)
            time.sleep(DELAY * 3)
        except Exception as e:  # noqa: BLE001
            print(f"  ! {url}: {e} (attempt {attempt + 1})", file=sys.stderr)
            time.sleep(DELAY * 3)
    return None


def text(s):
    s = re.sub(r"<[^>]+>", " ", s)
    return re.sub(r"\s+", " ", html.unescape(s)).strip()


def man_yen(int_part, dec_part=""):
    """'1389.' + '1' (万円) -> 13_891_000"""
    try:
        return round(float(int_part.rstrip(".") + "." + (dec_part or "0")) * 10_000)
    except ValueError:
        return None


def km(s):
    s = i18n.nfkc(s).replace(",", "")
    m = re.search(r"([\d.]+)\s*万\s*km", s)
    if m:
        return round(float(m.group(1)) * 10_000)
    m = re.search(r"([\d.]+)\s*km", s)
    return round(float(m.group(1))) if m else None


def parse_list(page_html):
    cards = []
    for chunk in page_html.split('<div class="search-card" id="tr_')[1:]:
        goo_id = chunk.split('"', 1)[0]
        stock = re.search(r'stock_id="([^"]+)"', chunk[:200])
        link = re.search(r'class="search-card__title-link"[^>]*href="([^"]+)">(.*?)</a>', chunk, re.S)
        if not (stock and link):
            continue
        spec = dict(re.findall(
            r'search-card__spec-label">([^<]+)</dt><dd class="search-card__spec-value">([^<]*)<', chunk))
        prices = re.findall(
            r'price-value--(total|body)">\s*<span class="search-card__price-int">([^<]*)</span>'
            r'(?:<span class="search-card__price-dec">([^<]*)</span>)?', chunk)
        price = {kind: man_yen(i, d) for kind, i, d in prices}
        year = re.search(r"(\d{4})", spec.get("年式", ""))
        cover = re.search(r'src="(https://picture1\.goo-net\.com/[^"]+/Q/[^"]+\.jpg)"[^>]*id="disp_img_', chunk)
        cards.append({
            "id": goo_id,
            "stock_id": stock.group(1),
            "url": BASE + link.group(1),
            "title_jp": text(link.group(2)),
            "year": int(year.group(1)) if year else None,
            "mileage_km": km(spec.get("走行距離", "")),
            "price_total_jpy": price.get("total"),
            "price_jpy": price.get("body"),
            "repair_history_jp": spec.get("修復歴", ""),
            "cover": cover.group(1).replace("/Q/", "/J/") if cover else None,
        })
    return cards


def parse_detail(page_html, stock_id):
    specs = {}
    for k, v in re.findall(r"<th[^>]*>\s*(?:<[^>]+>\s*)*([^<]{1,20}?)\s*(?:<[^>]+>\s*)*</th>\s*<td[^>]*>(.*?)</td>",
                           page_html, re.S):
        specs.setdefault(k.strip(), text(v))
    num = re.escape(stock_id)
    photos = sorted(set(re.findall(r"https://picture1\.goo-net\.com/\d+/\d+/J/" + num + r"\d{2}\.jpg", page_html)))
    shop = re.search(r'class="[^"]*shop[_-]?name[^"]*"[^>]*>(.*?)</', page_html, re.S)
    pref = re.search(r"〒[\d-]+\s*(\S+?[都道府県])", specs.get("住所", ""))
    return {
        "photos": photos,
        "specs_jp": {k: specs.get(k, "") for k in (
            "年式(初度登録)", "走行距離", "車検", "修復歴", "ハンドル", "排気量", "駆動方式", "燃料",
            "ドア", "ミッション", "過給器", "車体色", "輸入経路", "ディーラー車", "保証期間", "ワンオーナー", "禁煙車")},
        "dealer": text(shop.group(1)) if shop else "",
        "prefecture_jp": pref.group(1) if pref else "",
    }


def get_detail(card):
    path = os.path.join(CACHE_DIR, card["id"] + ".json")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    page = fetch(card["url"])
    if page is None:
        return None
    d = parse_detail(page, card["stock_id"])
    with open(path, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False)
    return d


PREFECTURES = {
    "東京都": "Tokyo", "大阪府": "Osaka", "京都府": "Kyoto", "北海道": "Hokkaido", "神奈川県": "Kanagawa",
    "愛知県": "Aichi", "埼玉県": "Saitama", "千葉県": "Chiba", "兵庫県": "Hyogo", "福岡県": "Fukuoka",
    "静岡県": "Shizuoka", "広島県": "Hiroshima", "宮城県": "Miyagi", "茨城県": "Ibaraki", "群馬県": "Gunma",
    "栃木県": "Tochigi", "岐阜県": "Gifu", "三重県": "Mie", "長野県": "Nagano", "新潟県": "Niigata",
    "岡山県": "Okayama", "熊本県": "Kumamoto", "鹿児島県": "Kagoshima", "沖縄県": "Okinawa", "奈良県": "Nara",
    "滋賀県": "Shiga", "石川県": "Ishikawa", "富山県": "Toyama", "山梨県": "Yamanashi", "福島県": "Fukushima",
}


def to_public(card, d):
    s = d["specs_jp"]
    model, grade = i18n.model_name(card["title_jp"])
    disp = re.search(r"(\d+)", i18n.nfkc(s.get("排気量", "")))
    # The listing's cover photo is the one the dealer picked; galleries often start with ad banners.
    thumbs = ([card["cover"]] if card.get("cover") else []) + d["photos"]
    return {
        "id": card["id"],
        "source_url": card["url"],
        "make": "Ferrari",
        "model": model,
        "grade": grade,
        "year": card["year"],
        "mileage_km": card["mileage_km"],
        "price_jpy": card["price_jpy"],
        "price_total_jpy": card["price_total_jpy"],
        "color": i18n.color(s.get("車体色", "")),
        "steering": i18n.spec(s.get("ハンドル", "")),
        "engine_cc": int(disp.group(1)) if disp else None,
        "fuel": i18n.spec(s.get("燃料", "")),
        "transmission": i18n.transmission(s.get("ミッション", "")),
        "drive": i18n.nfkc(s.get("駆動方式", "")),
        "body": i18n.spec(s.get("ドア", "")),
        "inspection_until": i18n.month_year(s.get("車検", "")),
        "warranty_until": i18n.month_year(s.get("保証期間", "")),
        "accident_history": i18n.spec(card["repair_history_jp"] or s.get("修復歴", "")),
        "import": i18n.spec(s.get("輸入経路", "")),
        "location": PREFECTURES.get(d.get("prefecture_jp", ""), "Japan"),
        "features": i18n.features(card["title_jp"]),
        "photos": [p.replace("/J/", "/H/") for p in thumbs],
        "thumbs": thumbs,
    }


def main():
    os.makedirs(CACHE_DIR, exist_ok=True)
    os.makedirs(os.path.dirname(SITE_JS), exist_ok=True)

    all_cards = []
    for n in range(1, MAX_PAGES + 1):
        url = LIST_URL.format(page="" if n == 1 else f"index-{n}.html")
        page = fetch(url)
        cards = parse_list(page) if page else []
        print(f"page {n}: {len(cards)} cars")
        if not cards:
            break
        all_cards += cards

    if not all_cards:
        sys.exit("No cars parsed - Goo-net layout may have changed. Keeping previous data.")

    seen, matches = set(), []
    for c in all_cards:
        if c["id"] in seen:
            continue
        seen.add(c["id"])
        if (c["year"] or 0) >= MIN_YEAR and c["mileage_km"] is not None and c["mileage_km"] <= MAX_KM:
            matches.append(c)
    print(f"{len(seen)} Ferraris total, {len(matches)} match year>={MIN_YEAR} & <= {MAX_KM:,} km")

    full, public = [], []
    for i, c in enumerate(matches, 1):
        d = get_detail(c)
        if not d:
            continue
        print(f"  [{i}/{len(matches)}] {i18n.model_name(c['title_jp'])[0]} {c['year']} {len(d['photos'])} photos")
        full.append({**c, **d})
        public.append(to_public(c, d))

    public.sort(key=lambda x: (-(x["year"] or 0), x["mileage_km"] or 0))
    updated = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    with open(FULL_JSON, "w", encoding="utf-8") as f:
        json.dump({"updated": updated, "cars": full}, f, ensure_ascii=False, indent=1)
    with open(SITE_JS, "w", encoding="utf-8") as f:
        f.write("window.CATALOG = ")
        json.dump({"updated": updated, "cars": public}, f, ensure_ascii=False)
        f.write(";\n")
    print(f"Saved {len(public)} cars -> {SITE_JS}")


if __name__ == "__main__":
    main()
