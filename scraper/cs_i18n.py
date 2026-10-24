"""Carsensor (Japanese) -> catalog fields: makes/models in Latin script, everything else in Russian."""
import json
import os
import re
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))

# Order of the compact rows written to data.js (the page reads the same list).
FIELDS = ["id", "make", "model", "grade", "year", "km", "total_jpy", "price_jpy", "body", "color",
          "engine_cc", "gearbox", "inspection", "accident", "warranty", "service", "region", "photo"]

MAKES = {
    "メルセデス・ベンツ": "Mercedes-Benz", "メルセデスAMG": "Mercedes-AMG", "メルセデス・AMG": "Mercedes-AMG",
    "メルセデス・マイバッハ": "Mercedes-Maybach", "マイバッハ": "Maybach", "BMW": "BMW", "BMWアルピナ": "BMW Alpina",
    "アルピナ": "Alpina", "アウディ": "Audi", "フォルクスワーゲン": "Volkswagen", "ポルシェ": "Porsche",
    "フェラーリ": "Ferrari", "ランボルギーニ": "Lamborghini", "マセラティ": "Maserati", "アルファロメオ": "Alfa Romeo",
    "フィアット": "Fiat", "アバルト": "Abarth", "ランチア": "Lancia", "ベントレー": "Bentley", "ロールスロイス": "Rolls-Royce",
    "アストンマーティン": "Aston Martin", "マクラーレン": "McLaren", "ジャガー": "Jaguar", "ランドローバー": "Land Rover",
    "MINI": "MINI", "ミニ": "MINI", "ロータス": "Lotus", "ボルボ": "Volvo", "プジョー": "Peugeot", "シトロエン": "Citroën",
    "ルノー": "Renault", "DS": "DS", "オペル": "Opel", "スマート": "smart", "テスラ": "Tesla", "シボレー": "Chevrolet",
    "キャデラック": "Cadillac", "フォード": "Ford", "リンカーン": "Lincoln", "ダッジ": "Dodge", "クライスラー": "Chrysler",
    "ジープ": "Jeep", "GMC": "GMC", "ハマー": "Hummer", "ポンティアック": "Pontiac", "ビュイック": "Buick",
    "マーキュリー": "Mercury", "シェルビー": "Shelby", "サリーン": "Saleen", "ラム": "Ram", "ヒョンデ": "Hyundai",
    "ヒュンダイ": "Hyundai", "キア": "Kia", "ジェネシス": "Genesis", "BYD": "BYD", "ポールスター": "Polestar",
    "アルピーヌ": "Alpine", "ブガッティ": "Bugatti", "ケータハム": "Caterham", "モーガン": "Morgan", "TVR": "TVR",
    "デ・トマソ": "De Tomaso", "ダイムラー": "Daimler", "ローバー": "Rover", "MG": "MG", "サーブ": "Saab",
    "オースチン": "Austin", "トライアンフ": "Triumph", "ルーフ": "RUF", "ブラバス": "Brabus", "ACシュニッツァー": "AC Schnitzer",
    "ヴィースマン": "Wiesmann", "ドンカーブート": "Donkervoort", "ケーニグセグ": "Koenigsegg", "パガーニ": "Pagani",
    "フィスカー": "Fisker", "ラーダ": "Lada", "シュコダ": "Škoda", "セアト": "SEAT", "クプラ": "Cupra", "ダチア": "Dacia",
    "トヨタ": "Toyota", "レクサス": "Lexus", "日産": "Nissan", "ホンダ": "Honda", "マツダ": "Mazda", "スバル": "Subaru",
    "三菱": "Mitsubishi", "スズキ": "Suzuki", "ダイハツ": "Daihatsu", "いすゞ": "Isuzu", "光岡": "Mitsuoka",
    "ミツオカ": "Mitsuoka", "インフィニティ": "Infiniti", "アキュラ": "Acura", "ロンドンタクシー": "London Taxi",
    "ベンツ": "Mercedes-Benz", "その他": "Другое",
    "アルファ ロメオ": "Alfa Romeo", "AMG": "Mercedes-AMG", "輸入車その他": "Другие марки", "国産車その他": "Другие японские",
    "プリムス": "Plymouth", "ポンテアック": "Pontiac", "サイオン": "Scion", "アウトビアンキ": "Autobianchi", "デイムラー": "Daimler",
    "ヒーレー": "Healey", "AMCジープ": "AMC Jeep", "モーク": "Moke", "デトマソ": "De Tomaso", "DMC": "DeLorean (DMC)",
    "ウィネベーゴ": "Winnebago", "日野自動車": "Hino", "アルテガ": "Artega", "光岡自動車": "Mitsuoka", "オールズモビル": "Oldsmobile",
    "AMC": "AMC", "ワズ": "UAZ",
}

# Frequent katakana words in model and grade names.
WORDS = {
    "クラス": "-Class", "カブリオレ": "Cabriolet", "カブリオ": "Cabrio", "クーペ": "Coupe", "スパイダー": "Spider",
    "スパイダ": "Spyder", "ロードスター": "Roadster", "ワゴン": "Wagon", "ステーションワゴン": "Station Wagon",
    "ツーリング": "Touring", "スポーツバック": "Sportback", "アバント": "Avant", "オールロード": "Allroad",
    "ケイマン": "Cayman", "ボクスター": "Boxster", "カイエン": "Cayenne", "マカン": "Macan", "パナメーラ": "Panamera",
    "タイカン": "Taycan", "カレラ": "Carrera", "ターボ": "Turbo", "タルガ": "Targa", "スポーツ": "Sport",
    "スポーツツーリスモ": "Sport Turismo", "クロスツーリスモ": "Cross Turismo", "エグゼクティブ": "Executive",
    "4マチック": "4MATIC", "マチック": "MATIC", "ロング": "Long", "エディション": "Edition", "ファースト": "First",
    "プレミアム": "Premium", "ラグジュアリー": "Luxury", "パッケージ": "Package", "ライン": "Line",
    "エクスクルーシブ": "Exclusive", "エクスクルーシヴ": "Exclusive", "アバンギャルド": "Avantgarde",
    "エレガンス": "Elegance", "ブルーテック": "BlueTEC", "ブルーエフィシェンシー": "BlueEFFICIENCY",
    "ハイブリッド": "Hybrid", "プラグインハイブリッド": "Plug-in Hybrid", "ディーゼル": "Diesel", "ディーゼルターボ": "Diesel Turbo",
    "クワトロ": "quattro", "コンペティション": "Competition", "グランクーペ": "Gran Coupe", "グランツーリスモ": "Gran Turismo",
    "グランツアラー": "Gran Tourer", "アクティブツアラー": "Active Tourer", "ツアラー": "Tourer", "ハッチバック": "Hatchback",
    "セダン": "Sedan", "リムジン": "Limousine", "ランドローバー": "Land Rover", "レンジローバー": "Range Rover",
    "ディスカバリー": "Discovery", "ディフェンダー": "Defender", "イヴォーク": "Evoque", "ヴェラール": "Velar",
    "ヴォーグ": "Vogue", "オートバイオグラフィー": "Autobiography", "ダイナミック": "Dynamic", "ファーストエディション": "First Edition",
    "ラングラー": "Wrangler", "アンリミテッド": "Unlimited", "グランドチェロキー": "Grand Cherokee", "チェロキー": "Cherokee",
    "コンパス": "Compass", "レネゲード": "Renegade", "ルビコン": "Rubicon", "サハラ": "Sahara", "リミテッド": "Limited",
    "サミット": "Summit", "オーバーランド": "Overland", "ラレード": "Laredo", "カマロ": "Camaro", "コルベット": "Corvette",
    "タホ": "Tahoe", "サバーバン": "Suburban", "エスカレード": "Escalade", "マスタング": "Mustang", "エクスプローラー": "Explorer",
    "ナビゲーター": "Navigator", "チャレンジャー": "Challenger", "チャージャー": "Charger", "デュランゴ": "Durango",
    "ゴルフ": "Golf", "ポロ": "Polo", "パサート": "Passat", "ティグアン": "Tiguan", "トゥアレグ": "Touareg",
    "アルテオン": "Arteon", "シロッコ": "Scirocco", "ザ・ビートル": "The Beetle", "ビートル": "Beetle", "ヴァリアント": "Variant",
    "トゥーラン": "Touran", "シャラン": "Sharan", "ジェッタ": "Jetta", "アップ": "up!", "カリフォルニア": "California",
    "ローマ": "Roma", "ポルトフィーノ": "Portofino", "プロサングエ": "Purosangue", "スーパーファスト": "Superfast",
    "ストラダーレ": "Stradale", "トリブート": "Tributo", "ピスタ": "Pista", "イタリア": "Italia", "スペチアーレ": "Speciale",
    "ウラカン": "Huracan", "ウルス": "Urus", "アヴェンタドール": "Aventador", "ガヤルド": "Gallardo", "ムルシエラゴ": "Murcielago",
    "レヴエルト": "Revuelto", "ギブリ": "Ghibli", "クアトロポルテ": "Quattroporte", "レヴァンテ": "Levante", "グレカーレ": "Grecale",
    "グラントゥーリズモ": "GranTurismo", "グランカブリオ": "GranCabrio", "コンティネンタル": "Continental", "ベンテイガ": "Bentayga",
    "フライングスパー": "Flying Spur", "ミュルザンヌ": "Mulsanne", "ゴースト": "Ghost", "カリナン": "Cullinan", "ファントム": "Phantom",
    "レイス": "Wraith", "ドーン": "Dawn", "スペクター": "Spectre", "ヴァンテージ": "Vantage", "ヴァンキッシュ": "Vanquish",
    "ラピード": "Rapide", "アルテッツァ": "Altezza", "ジュリア": "Giulia", "ジュリエッタ": "Giulietta", "ステルヴィオ": "Stelvio",
    "トナーレ": "Tonale", "エスプリ": "Esprit", "エリーゼ": "Elise", "エキシージ": "Exige", "エヴォーラ": "Evora", "エミーラ": "Emira",
    "クロスオーバー": "Crossover", "クラブマン": "Clubman", "コンバーチブル": "Convertible", "カントリーマン": "Countryman",
    "クロスオーバー": "Crossover", "クーパー": "Cooper", "ジョンクーパーワークス": "John Cooper Works", "ワン": "One",
    "モデル": "Model", "ロングレンジ": "Long Range", "パフォーマンス": "Performance", "デュアルモーター": "Dual Motor",
    "シングルモーター": "Single Motor", "ベース": "Base", "ベースグレード": "Base", "スタンダード": "Standard",
    "カスタム": "Custom", "コンフォート": "Comfort", "インスクリプション": "Inscription", "モメンタム": "Momentum",
    "アールデザイン": "R-Design", "クロスカントリー": "Cross Country", "リチャージ": "Recharge", "アルティメット": "Ultimate",
    "プラス": "Plus", "セレクト": "Select", "ブラック": "Black", "ホワイト": "White", "シルバー": "Silver", "レッド": "Red",
    "ブルー": "Blue", "グレー": "Grey", "ナイト": "Night", "シャドー": "Shadow", "ファイナル": "Final", "アニバーサリー": "Anniversary",
    "シグネチャー": "Signature", "デザイン": "Design", "エレクトリック": "Electric", "クロス": "Cross", "オフロード": "Off-Road",
    "モノクローム": "Monochrome", "ゲレンデヴァーゲン": "G-Wagen", "マイスター": "Meister", "ハイライン": "Highline",
    "コンフォートライン": "Comfortline", "トレンドライン": "Trendline", "Rライン": "R-Line", "ブラックスタイル": "Black Style",
    "ウルトラ": "Ultra", "スピード": "Speed", "マリナー": "Mulliner", "アズール": "Azure", "Sライン": "S line",
}


WORDS.update({
    "タンドラ": "Tundra", "アストロ": "Astro", "ラムバン": "Ram Van", "ラムトラック": "Ram Truck", "ラムメガキャブ": "Ram Mega Cab",
    "タコマ": "Tacoma", "ドア": "-Door", "シエナ": "Sienna", "チリンドリ": "Cilindri", "マグナム": "Magnum", "シルバラード": "Silverado",
    "ミディアム": "Medium", "エクスプレス": "Express", "インパラ": "Impala", "シリーズ": " Series", "グランドワゴニア": "Grand Wagoneer",
    "ワゴニア": "Wagoneer", "ステラート": "Sterrato", "チンクエチェント": "Cinquecento", "ブロンコ": "Bronco", "ブラックバッジ": "Black Badge",
    "エルカミーノ": "El Camino", "ルッソ": "Lusso", "エコノライン": "Econoline", "クルーザー": "Cruiser", "セコイア": "Sequoia",
    "アルファード": "Alphard", "アルファ": "Alfa", "タイプ": "Type", "チェロ": "Cielo", "デュカト": "Ducato", "ランナー": "Runner",
    "モデナ": "Modena", "バン": "Van", "シエラ": "Sierra", "ベルエア": "Bel Air", "シェベル": "Chevelle", "フェラーリ": "Ferrari",
    "アルナージ": "Arnage", "トゥインゴ": "Twingo", "デルタ": "Delta", "トラック": "Truck", "イプシロン": "Ypsilon", "アルトゥーラ": "Artura",
    "フリートウッド": "Fleetwood", "バルケッタ": "Barchetta", "トレイルブレイザー": "Trailblazer", "ブレイザー": "Blazer", "シェビー": "Chevy",
    "サンダーバード": "Thunderbird", "フェアレディ": "Fairlady", "グラディエーター": "Gladiator", "プリウス": "Prius", "スプリンター": "Sprinter",
    "ミニ": "Mini", "タイタン": "Titan", "リッジライン": "Ridgeline", "タウンカー": "Town Car", "オデッセイ": "Odyssey", "ウインド": "Wind",
    "エルドラド": "Eldorado", "エクスペディション": "Expedition", "ニュー": "New", "カプリス": "Caprice", "サバナ": "Savana",
    "エクスカージョン": "Excursion", "トランザム": "Trans Am", "スーパーレッジェーラ": "Superleggera", "セッタンタ": "Settanta",
    "チンクエ": "Cinque", "アニヴェルサーリオ": "Anniversario", "リーガル": "Regal", "テスタロッサ": "Testarossa", "ヴァナゴン": "Vanagon",
    "ミト": "MiTo", "サファリ": "Safari", "テメラリオ": "Temerario", "ハイランダー": "Highlander", "エクリプス": "Eclipse", "プント": "Punto",
    "モンテカルロ": "Monte Carlo", "カウンタック": "Countach", "クエスト": "Quest", "ベルリネッタ": "Berlinetta", "ディーノ": "Dino",
    "ヨーロッパ": "Europa", "コーニッシュ": "Corniche", "アコード": "Accord", "スカリエッティ": "Scaglietti", "バンデューラ": "Vandura",
    "バリアント": "Variant", "ステップバン": "Step Van", "デイムラー": "Daimler", "スクーデリア": "Scuderia", "ヴォランテ": "Volante",
    "クーガー": "Cougar", "カルマンギア": "Karmann Ghia", "バラクーダ": "Barracuda", "スパー": "Spur", "マーク": "Mark", "マラネロ": "Maranello",
    "バイパー": "Viper", "ダットサン": "Datsun", "コンコース": "Concours", "ウニモグ": "Unimog", "ファイアーバード": "Firebird",
    "セビル": "Seville", "ミジェット": "Midget", "フレックス": "Flex", "ロードランナー": "Road Runner", "グランデ": "Grande",
    "キャラバン": "Caravan", "トラバース": "Traverse", "パークアベニュー": "Park Avenue", "サクソ": "Saxo", "シャドウ": "Shadow",
    "ブロアム": "Brougham", "ダート": "Dart", "パスファインダー": "Pathfinder", "ロードマスター": "Roadmaster", "ムルティプラ": "Multipla",
    "モーク": "Moke", "デ・ビル": "De Ville", "デビル": "DeVille", "ドゥビル": "DeVille", "セラフ": "Seraph", "トライク": "Trike",
    "スピットファイア": "Spitfire", "カングー": "Kangoo", "アルピーヌ": "Alpine", "フォワード": "Forward", "パンテーラ": "Pantera",
    "スプライト": "Sprite", "アンノ": "Anno", "デル": "del", "トーロ": "Toro", "ダコタ": "Dakota", "フィット": "Fit",
    "コロニーパーク": "Colony Park", "リビエラ": "Riviera", "ブレラ": "Brera", "コラード": "Corrado", "ハイゼット": "Hijet", "カーゴ": "Cargo",
    "アストラ": "Astra", "ミアータ": "Miata", "ランチア": "Lancia", "レンジャー": "Ranger", "ルーテシア": "Lutecia", "ノーバ": "Nova", "ノバ": "Nova",
    "スペース": "Space", "ディアブロ": "Diablo", "エヴォ": "Evo", "カムリ": "Camry", "ソラーラ": "Solara", "シューティングブレーク": "Shooting Brake",
    "シビック": "Civic", "エラン": "Elan", "エレクトラ": "Electra", "コルベア": "Corvair", "ニーヴァ": "Niva", "キャンピングカー": "Camper",
    "キャンピング": "Camping", "トラフィック": "Trafic", "グランプリ": "Grand Prix", "ドロップヘッド": "Drophead", "トール": "Thor",
    "トーラス": "Taurus", "スポール": "Sport", "ランドクルーザー": "Land Cruiser", "アルティマ": "Altima", "ジャガー": "Jaguar",
    "ハーレーダビッドソン": "Harley-Davidson", "コブラ": "Cobra", "ユーロバン": "EuroVan", "フェアレーン": "Fairlane",
    "トランスポーター": "Transporter", "トリノ": "Torino", "ヴェント": "Vento", "セレナ": "Serena", "センチュリー": "Century",
    "ヴォクシー": "Voxy", "フリード": "Freed", "ランチェロ": "Ranchero", "ヤリス": "Yaris", "メガーヌ": "Megane", "ジューク": "Juke",
    "ヴィッツ": "Vitz", "ライズ": "Raize", "セナ": "Senna", "タント": "Tanto", "アラスカン": "Alaskan", "ルータン": "Routan",
    "コロラド": "Colorado", "エッセエッセ": "esseesse", "ピカソ": "Picasso", "ヴェロスター": "Veloster", "ニューポート": "Newport",
    "ハネベン": "Fintail", "ソルスティス": "Solstice", "ジュニア": "Junior", "ザガート": "Zagato", "ザガード": "Zagato", "リヴァーレ": "Rivale",
    "マスター": "Master", "チャレンジ": "Challenge", "オスカ": "OSCA", "アスペン": "Aspen", "スタイルライン": "Styleline", "ドブロ": "Doblo",
    "フリートライン": "Fleetline", "ポントン": "Ponton", "ハドソン": "Hudson", "エステート": "Estate", "オートグラフ": "Autograph",
    "ウィネベーゴ": "Winnebago", "ウィネべーゴ": "Winnebago", "マクラーレン": "McLaren", "ギャラクシー": "Galaxie", "ベック": "Beck",
    "ラ フェラーリ": "LaFerrari", "スピリット": "Spirit", "ウィンドウ": "Window", "エッジ": "Edge", "エクステラ": "Xterra", "スポルト": "Sport",
    "エスパス": "Espace", "フォレスター": "Forester", "ラグナ": "Laguna", "ポルシェ": "Porsche", "ブルーバード": "Bluebird", "ネクスト": "Next",
    "オペル": "Opel", "パッセンジャー": "Passenger", "タンク": "Tank", "セイチェント": "Seicento", "エディツィオーネ": "Edizione",
    "マセラティ": "Maserati", "レプリカ": "Replica", "ダカール": "Dakar", "ジープ": "Jeep", "エンツォ": "Enzo", "フォーカス": "Focus",
    "デュトロ": "Dutro", "グランドマーキー": "Grand Marquis", "インターメカニカ": "Intermeccanica", "プジョー": "Peugeot", "プリムス": "Plymouth",
    "キャデラック": "Cadillac", "フォード": "Ford", "グラマン": "Grumman", "カスタムライン": "Customline", "カイザー": "Kaiser",
    "プロウラー": "Prowler", "プラウラー": "Prowler", "パッカード": "Packard", "プローブ": "Probe", "カマーグ": "Camargue",
    "クロスブレード": "Crossblade", "エイト": "Eight", "フランクリン": "Franklin", "デューンバギー": "Dune Buggy", "インターナショナル": "International",
    "カラベル": "Caravelle", "スポルティング": "Sporting", "アバルト": "Abarth", "キューブ": "Cube", "ルセーバー": "LeSabre", "パシフィカ": "Pacifica",
    "ローウインド": "Low Window", "プリマスター": "Primastar", "コンビ": "Kombi", "シュタイア": "Steyr", "プフ": "Puch", "ピンツガウアー": "Pinzgauer",
    "カントリースクワイヤ": "Country Squire", "オートクラフト": "Autokraft", "リトモ": "Ritmo", "サテライト": "Satellite", "アミーゴ": "Amigo",
    "カンパーニャ": "Campagna", "ヒーレー": "Healey", "ハイラックス": "Hilux", "カローラ": "Corolla", "ホロ": "soft top", "フォーツー": "fortwo",
    "バハ": "Baja", "パンプキン": "Pumpkin", "プロエース": "ProAce", "ベルベディア": "Belvedere", "ベルべデイア": "Belvedere", "インペリアル": "Imperial",
    "クラウド": "Cloud", "トランジット": "Transit", "コマンダー": "Commander", "メルセデスベンツ": "Mercedes-Benz", "メルセデス・ベンツ": "Mercedes-Benz",
    "シムカ": "Simca", "ウェストファリア": "Westfalia", "ハイエース": "HiAce", "テーマ": "Thema", "フルヴィア": "Fulvia", "フルビア": "Fulvia",
    "エルバ": "Elva", "クレネ": "Clenet", "ゴルディーニ": "Gordini", "ルバロン": "LeBaron", "トロネード": "Toronado", "ウィリス": "Willys",
    "グレムリン": "Gremlin", "ブルックランズ": "Brooklands", "スーパースポーツ": "Supersports", "スターチーフ": "Star Chief",
    "ビアンキーナ": "Bianchina", "アビエーター": "Aviator", "アウトバック": "Outback", "ラッセル": "Russell", "コンバー": "Convertible",
    "シャマル": "Shamal", "カントリー": "Country", "ワズ": "UAZ", "エラントラ": "Elantra", "コロネット": "Coronet", "パナール": "Panhard",
    "グラース": "Glas", "ゴッゴモビル": "Goggomobil", "フラッドヘッド": "Flathead", "ヘラルド": "Herald", "リエッセ": "Liesse",
    "ダスター": "Duster", "ヴィータ": "Vita", "プルリエル": "Pluriel", "タウンカントリー": "Town & Country", "クーボ": "Qubo",
    "ナッシュ": "Nash", "メトロポリタン": "Metropolitan", "アイゴ": "Aygo", "ジミー": "Jimmy", "キャタピラー": "Caterpillar",
    "ホイルローダー": "Wheel Loader", "トラクター": "Tractor", "パネルバン": "Panel Van", "ノート": "Note", "チゼータ": "Cizeta",
    "ミラトコット": "Mira Tocot", "ミウラ": "Miura", "ティファニー": "Tiffany", "スウィング": "Swing", "マリブ": "Malibu", "ポラーラ": "Polara",
    "スタッグ": "Stag", "リンカーン": "Lincoln", "ダッジ": "Dodge", "シボレー": "Chevrolet", "オースチン": "Austin", "ラム": "Ram",
    "シェビーバン": "Chevy Van", "スーパフォーマンス": "Superformance", "スーパーフォーマンス": "Superformance", "アレグロ": "Allegro",
    "トロフェオ": "Trofeo", "ストロンガーザンタイム": "Stronger Than Time", "モデル": "Model", "ファーストエディション": "First Edition",
    "コンチネンタル": "Continental", "シルバー": "Silver", "スーパー": "Super",
})

# Kanji / mixed phrases worth keeping (others are dropped from grade names).
PHRASES = {"搭載モデル": "", "搭載車": "", "左ハンドル": "LHD", "右ハンドル": "RHD", "本革": "кожа", "限定車": "Limited",
           "記念車": "Edition", "後期型": "facelift", "前期型": "", "正規輸入車": "", "並行輸入車": "parallel import"}

BODIES = {"セダン": "Седан", "クーペ": "Купе", "オープン": "Кабриолет", "ステーションワゴン": "Универсал",
          "SUV・クロカン": "Внедорожник", "ハッチバック": "Хэтчбек", "ミニバン": "Минивэн", "ピックアップトラック": "Пикап",
          "軽自動車": "Кей-кар", "トラック": "Грузовик", "バス": "Автобус", "キャンピングカー": "Автодом",
          "ワンボックス": "Микроавтобус", "福祉車両": "Спецтранспорт", "その他": "Другое", "SUV": "Внедорожник",
          "クロカン・SUV": "Внедорожник"}

COLORS = [("パール", "Перламутровый"), ("ガンメタ", "Графитовый"), ("ワイン", "Бордовый"), ("ベージュ", "Бежевый"),
          ("ピンク", "Розовый"), ("水色", "Голубой"), ("紺", "Тёмно-синий"), ("白", "Белый"), ("黒", "Чёрный"),
          ("銀", "Серебристый"), ("灰", "Серый"), ("グレー", "Серый"), ("赤", "Красный"), ("青", "Синий"),
          ("緑", "Зелёный"), ("黄", "Жёлтый"), ("橙", "Оранжевый"), ("オレンジ", "Оранжевый"), ("茶", "Коричневый"),
          ("金", "Золотой"), ("紫", "Фиолетовый"), ("その他", "Другой")]

PREFS = {
    "北海道": "Хоккайдо", "青森県": "Аомори", "岩手県": "Иватэ", "宮城県": "Мияги", "秋田県": "Акита", "山形県": "Ямагата",
    "福島県": "Фукусима", "茨城県": "Ибараки", "栃木県": "Тотиги", "群馬県": "Гумма", "埼玉県": "Сайтама", "千葉県": "Тиба",
    "東京都": "Токио", "神奈川県": "Канагава", "新潟県": "Ниигата", "富山県": "Тояма", "石川県": "Исикава", "福井県": "Фукуи",
    "山梨県": "Яманаси", "長野県": "Нагано", "岐阜県": "Гифу", "静岡県": "Сидзуока", "愛知県": "Айти", "三重県": "Миэ",
    "滋賀県": "Сига", "京都府": "Киото", "大阪府": "Осака", "兵庫県": "Хёго", "奈良県": "Нара", "和歌山県": "Вакаяма",
    "鳥取県": "Тоттори", "島根県": "Симанэ", "岡山県": "Окаяма", "広島県": "Хиросима", "山口県": "Ямагути", "徳島県": "Токусима",
    "香川県": "Кагава", "愛媛県": "Эхимэ", "高知県": "Коти", "福岡県": "Фукуока", "佐賀県": "Сага", "長崎県": "Нагасаки",
    "熊本県": "Кумамото", "大分県": "Оита", "宮崎県": "Миядзаки", "鹿児島県": "Кагосима", "沖縄県": "Окинава",
}

# Hepburn romanisation for katakana that no dictionary covers.
_KANA = dict(zip(
    "アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲンガギグゲゴザジズゼゾダヂヅデドバビブベボパピプペポヴ",
    "a i u e o ka ki ku ke ko sa shi su se so ta chi tsu te to na ni nu ne no ha hi fu he ho ma mi mu me mo ya yu yo ra ri ru re ro wa o n ga gi gu ge go za ji zu ze zo da ji zu de do ba bi bu be bo pa pi pu pe po vu".split()))
_SMALL = {"ャ": "ya", "ュ": "yu", "ョ": "yo", "ァ": "a", "ィ": "i", "ゥ": "u", "ェ": "e", "ォ": "o"}
KATA = re.compile(r"[ァ-ヴー・]+")
CJK = re.compile(r"[぀-ヿ一-鿿]")

_models = {}
_models_path = os.path.join(HERE, "cs_models.json")
if os.path.exists(_models_path):
    with open(_models_path, encoding="utf-8") as f:
        _models = json.load(f)


def nfkc(s):
    return unicodedata.normalize("NFKC", s or "").strip()


def romanize(word):
    out, i = "", 0
    while i < len(word):
        ch = word[i]
        nxt = word[i + 1] if i + 1 < len(word) else ""
        if ch == "ッ" and nxt in _KANA:
            out += _KANA[nxt][0]
        elif ch == "ー":
            pass
        elif ch == "・":
            out += " "
        elif nxt in _SMALL and ch in _KANA:
            base = _KANA[ch]
            out += (base[:-1] if base.endswith("i") else base) + _SMALL[nxt]
            i += 1
        elif ch in _KANA:
            out += _KANA[ch]
        i += 1
    return out[:1].upper() + out[1:]


def latin(s):
    """Model / grade text in Latin script: dictionary first, then romanisation; leftover kanji is dropped."""
    s = nfkc(s)
    for jp, en in PHRASES.items():
        s = s.replace(jp, f" {en} " if en else " ")
    for jp in sorted(WORDS, key=len, reverse=True):
        s = s.replace(jp, f" {WORDS[jp]} ")
    s = KATA.sub(lambda m: " " + romanize(m.group(0)) + " ", s)
    s = CJK.sub(" ", s)
    s = re.sub(r"\(\s*\)", "", s)
    s = re.sub(r"\s+-Class", "-Class", s)
    s = re.sub(r"(\d)\s+-Door", r"\1-Door", s)
    s = re.sub(r"\s+ Series", " Series", s)
    return re.sub(r"\s+", " ", s).strip(" ,/")


def make(jp):
    k = nfkc(jp)
    k = re.sub(r"^(米国|欧州)", "", k)
    return MAKES.get(k) or MAKES.get(jp) or latin(k) or jp


def model(brand_jp, model_jp):
    key = f"{nfkc(brand_jp)}|{nfkc(model_jp)}"
    if key in _models:
        return _models[key]
    m = nfkc(model_jp)
    if "その他" in m or m.startswith("他"):
        return "Другое"
    out = latin(m)
    mk = make(brand_jp)
    if out.lower() == mk.lower() or out.lower() == mk.split()[0].lower():
        return ""
    return out


def km(s):
    s = nfkc(s).replace(",", "")
    m = re.search(r"([\d.]+)\s*万\s*km", s, re.I)
    if m:
        return round(float(m.group(1)) * 10_000)
    m = re.search(r"([\d.]+)\s*km", s, re.I)
    return round(float(m.group(1))) if m else None


def color(s):
    s = nfkc(s)
    for jp, ru in COLORS:
        if jp in s:
            return ru
    return ""


def gearbox(s):
    s = nfkc(s).upper()
    if not s:
        return ""
    if "CVT" in s:
        return "Вариатор"
    if "AT" in s or "DCT" in s:
        return "Автомат"
    if "MT" in s:
        return "Механика"
    return ""


def inspection(s):
    s = nfkc(s)
    m = re.search(r"(\d{4})(?:\([^)]*\))?\s*年\s*(\d{1,2})月", s)
    if m:
        return f"{int(m.group(2)):02d}.{m.group(1)}"
    if "車検整備付" in s:
        return "Будет пройден перед продажей"
    if "車検整備無" in s or "なし" in s:
        return "Нет"
    return ""


def yes_no(s, yes, no):
    s = nfkc(s)
    if not s or s in ("-", "－"):
        return ""
    if any(w in s for w in no):
        return "Нет"
    if any(w in s for w in yes):
        return "Есть"
    return ""


def to_public(c):
    disp = re.search(r"(\d{3,5})", nfkc(c.get("displacement_jp", "")))
    grade = latin(c.get("grade_jp", ""))
    return {
        "make": make(c["brand_jp"]),
        "model": model(c["brand_jp"], c["model_jp"]),
        "grade": grade[:80],
        "year": c.get("year"),
        "km": km(c.get("mileage_jp", "")),
        "total_jpy": c.get("price_total_jpy"),
        "price_jpy": c.get("price_jpy"),
        "body": BODIES.get(nfkc(c.get("body_jp", "")), ""),
        "color": color(c.get("color_jp", "")),
        "engine_cc": int(disp.group(1)) if disp else None,
        "gearbox": gearbox(c.get("mission_jp", "")),
        "inspection": inspection(c.get("inspection_jp", "")),
        "accident": yes_no(c.get("repair_jp", ""), ["あり", "有"], ["なし", "無"]),
        "warranty": yes_no(c.get("warranty_jp", ""), ["保証付", "付"], ["保証無", "無"]),
        "service": yes_no(c.get("maintenance_jp", ""), ["整備付", "付"], ["整備無", "無"]),
        "region": PREFS.get(c.get("pref_jp", ""), ""),
        "photo": c.get("photo", ""),
    }
