"""Japanese -> English dictionaries for Goo-net Ferrari listings."""
import re
import unicodedata

# Longest keys first so "ローマスパイダー" wins over "ローマ".
MODELS = {
    "12チリンドリスパイダー": "12Cilindri Spider",
    "12チリンドリ": "12Cilindri",
    "296スペチアーレA": "296 Speciale A",
    "296スペチアーレ": "296 Speciale",
    "296GTB": "296 GTB",
    "296GTS": "296 GTS",
    "SF90XXストラダーレ": "SF90 XX Stradale",
    "SF90XXスパイダー": "SF90 XX Spider",
    "SF90ストラダーレ": "SF90 Stradale",
    "SF90スパイダー": "SF90 Spider",
    "812コンペティツィオーネA": "812 Competizione A",
    "812コンペティツィオーネ": "812 Competizione",
    "812スーパーファスト": "812 Superfast",
    "812GTS": "812 GTS",
    "F8トリブート": "F8 Tributo",
    "F8スパイダー": "F8 Spider",
    "ローマスパイダー": "Roma Spider",
    "ローマ": "Roma",
    "アマルフィ": "Amalfi",
    "プロサングエ": "Purosangue",
    "ポルトフィーノM": "Portofino M",
    "ポルトフィーノ": "Portofino",
    "デイトナSP3": "Daytona SP3",
    "モンツァSP2": "Monza SP2",
    "モンツァSP1": "Monza SP1",
    "F80": "F80",
}

GRADES = {
    "ベースグレード": "",
    "アセットフィオラノパッケージ": "Assetto Fiorano",
    "アセットフィオラノ": "Assetto Fiorano",
}

# Equipment / condition keywords found in the free-text listing title.
FEATURES = [
    ("フェラーリ認定中古車", "Ferrari Approved (certified pre-owned)"),
    ("Ferrari認定中古車", "Ferrari Approved (certified pre-owned)"),
    ("認定中古車", "Certified pre-owned"),
    ("新車保証継承", "Factory warranty transferred"),
    ("メーカー保証", "Manufacturer warranty"),
    ("正規ディーラー車", "Official dealer car"),
    ("正規D車", "Official dealer car"),
    ("ワンオーナー", "One owner"),
    ("禁煙", "Non-smoker"),
    ("記録簿", "Service records"),
    ("屋内保管", "Garage kept"),
    ("リフター", "Front lifter"),
    ("フロントリフト", "Front lifter"),
    ("カーボンセラミック", "Carbon-ceramic brakes"),
    ("カーボン", "Carbon fibre options"),
    ("LED", "LED steering wheel"),
    ("デイトナシート", "Daytona seats"),
    ("レーシングシート", "Racing seats"),
    ("パノラミックルーフ", "Panoramic roof"),
    ("マグネライド", "MagneRide suspension"),
    ("鍛造", "Forged wheels"),
    ("Apple CarPlay", "Apple CarPlay"),
    ("AppleCarPlay", "Apple CarPlay"),
    ("アップルカープレイ", "Apple CarPlay"),
    ("JBL", "JBL sound system"),
    ("ADAS", "ADAS driver assistance"),
    ("サラウンドビュー", "Surround-view camera"),
    ("リアカメラ", "Rear camera"),
    ("バックカメラ", "Rear camera"),
    ("パッセンジャーディスプレイ", "Passenger display"),
    ("助手席ディスプレイ", "Passenger display"),
    ("ベンチレーション", "Ventilated seats"),
    ("シートヒーター", "Heated seats"),
    ("スポーツエキゾースト", "Sports exhaust"),
    ("テーラーメイド", "Tailor Made"),
    ("Tailor Made", "Tailor Made"),
    ("特注カラー", "Special order colour"),
    ("プロテクションフィルム", "Paint protection film"),
]

COLOR_WORDS = {
    "ロッソ": "Rosso", "ビアンコ": "Bianco", "ネロ": "Nero", "グリジオ": "Grigio",
    "ジアッロ": "Giallo", "ブルー": "Blu", "ブル": "Blu", "アズーロ": "Azzurro",
    "ヴェルデ": "Verde", "アルジェント": "Argento", "オッカジオーネ": "Occasione", "ドーロ": "d'Oro",
    "コルサ": "Corsa", "アヴス": "Avus", "アブス": "Avus", "セルビノ": "Cervino", "セルヴィノ": "Cervino",
    "チェルヴィーノ": "Cervino", "スクーロ": "Scuro", "イモラ": "Imola", "モデナ": "Modena",
    "イタリア": "Italia", "デイトナ": "Daytona", "アルティコ": "Artico", "ポッジ": "Pozzi",
    "ニュルブルクリンク": "Nürburgring", "オパコ": "Opaco", "ポルトフィーノ": "Portofino",
    "キアーロ": "Chiaro", "ディーエス": "DS", "モナコ": "Monaco", "フェラーリ": "Ferrari",
    "ムジェロ": "Mugello", "フォーミュラー": "Formula", "スクーデリア": "Scuderia",
    "プロサングエ": "Purosangue", "カリフォルニア": "California", "マグマ": "Magma",
    "チタニオ": "Titanio", "シルバーストーン": "Silverstone", "フジ": "Fuji",
    "ステルスフィルム": "stealth film", "フルPPF": "full PPF",
    "ホワイト": "White", "ブラック": "Black", "レッド": "Red", "ゴールド": "Gold",
    "シルバー": "Silver", "グレー": "Grey", "イエロー": "Yellow", "グリーン": "Green",
    "オレンジ": "Orange", "パープル": "Purple", "ペール": "Pale", "パール": "Pearl",
    "メタリック": "Metallic", "ガン": "Gun", "ツートン": "Two-tone", "マット": "Matte",
    "ダーク": "Dark", "ライト": "Light", "茶": "Brown", "白": "White", "黒": "Black",
    "赤": "Red", "青": "Blue", "黄": "Yellow", "銀": "Silver", "灰": "Grey",
}

SPEC_VALUES = {
    "なし": "None", "あり": "Yes", "有": "Yes", "無し": "None", "無": "None",
    "左": "LHD", "右": "RHD",
    "ガソリン": "Petrol", "ハイオク": "Petrol (premium)",
    "プラグインハイブリッド": "Plug-in hybrid", "ハイブリッド": "Hybrid",
    "コラムAT": "Automatic (DCT)", "フロアAT": "Automatic (DCT)", "インパネAT": "Automatic (DCT)",
    "AT": "Automatic (DCT)", "MT": "Manual", "フロアMT": "Manual",
    "クーペ": "Coupe", "オープン": "Convertible", "5ドア": "5-door", "4ドア": "4-door", "2ドア": "2-door",
    "ターボチャージャー": "Turbo", "スーパーチャージャー": "Supercharger",
    "5D": "SUV (5-door)", "2D": "Coupe",
    "正規輸入車": "Official import", "並行輸入車": "Parallel import", "中古並行": "Parallel import",
}


def nfkc(s):
    return unicodedata.normalize("NFKC", s or "").strip()


def model_name(title):
    """Return (model_en, grade_en) from a listing title like '296GTB アセットフィオラノパッケージ ...'."""
    t = nfkc(title)
    model = None
    for jp in sorted(MODELS, key=len, reverse=True):
        if t.startswith(jp):
            model, rest = MODELS[jp], t[len(jp):]
            break
    if model is None:
        first, _, rest = t.partition(" ")
        model = first
    grade = ""
    for jp, en in GRADES.items():
        if rest.strip().startswith(jp):
            grade = en
            break
    return model, grade


def features(title):
    t = nfkc(title)
    out = []
    for jp, en in FEATURES:
        if jp in t and en not in out:
            # Skip the generic entries when a more specific one already matched.
            if en == "Certified pre-owned" and any("Approved" in f for f in out):
                continue
            if en == "Carbon fibre options" and "Carbon-ceramic brakes" in out and t.count("カーボン") == 1:
                continue
            if en == "LED steering wheel" and "ステア" not in t and "ハンドル" not in t:
                continue
            out.append(en)
    return out


COLOR_TYPOS = {"Imora": "Imola", "Itaria": "Italia", "Maguma": "Magma", "Taylor Made": "Tailor Made",
               "Argent ": "Argento ", "Nurburgring": "Nürburgring", "Tour De": "Tour de", "Ds": "DS", " Met": " Metallic"}


def color(jp):
    out = _color(jp)
    for bad, good in COLOR_TYPOS.items():
        out = re.sub(r"\b" + re.escape(bad.strip()) + r"\b", good.strip(), out) if bad.strip() else out
    return out


def _color(jp):
    s = nfkc(jp)
    if not s or s == "-" or s == "−":
        return ""
    if re.fullmatch(r"[A-Za-z0-9 ()/.'&-]+", s):
        # Latin already, e.g. "BiancoCervino" / "ROSSO CORSA" -> "Bianco Cervino" / "Rosso Corsa"
        s = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", s).strip()
        return s.title() if s.isupper() else s
    out = s.replace("・", " ")
    for k in sorted(COLOR_WORDS, key=len, reverse=True):
        out = out.replace(k, " " + COLOR_WORDS[k] + " ")
    out = re.sub(r"(?<=Gun)\s+M\b", "metal", out)          # "ガンM" -> Gunmetal
    out = re.sub(r"\s+M\b", " Metallic", out)               # "ライトゴールドM"
    out = re.sub(r"\s*\(\s*", " (", out)
    out = re.sub(r"\s*\)\s*", ")", out)
    out = re.sub(r"\s+", " ", out).strip()
    out = out.replace("Gun metal", "Gunmetal")
    return out if not re.search(r"[぀-ヿ一-鿿]", out) else s


def spec(value):
    v = nfkc(value)
    return SPEC_VALUES.get(v, v)


def transmission(value):
    v = nfkc(value)
    if "MT" in v and "AT" not in v:
        return "Manual"
    return "Automatic (F1 DCT)" if v else ""


def month_year(jp):
    """'2028(令和10)年9月 ...' -> 'Sep 2028'."""
    m = re.search(r"(\d{4})\D*?年\s*(\d{1,2})月", nfkc(jp))
    if not m:
        return ""
    months = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()
    return f"{months[int(m.group(2)) - 1]} {m.group(1)}"
