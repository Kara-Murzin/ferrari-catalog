// =====================================================================
//  Lion Motors — company details used by every page of the site.
//  Fill in the empty strings; leave a field "" until the data is known
//  and the page shows "未設定 / To be announced" in its place.
// =====================================================================
window.COMPANY = {
  // --- Legal entity -------------------------------------------------
  nameEn: "",            // e.g. "Lion Motors Co., Ltd."
  nameJa: "",            // e.g. "株式会社ライオンモーターズ"
  representativeEn: "",  // Representative director, e.g. "Taro Yamada"
  representativeJa: "",  // 代表者, e.g. "代表取締役 山田 太郎"
  postalCode: "",        // e.g. "105-0011"
  addressEn: "",         // e.g. "1-2-3 Shibakoen, Minato-ku, Tokyo"
  addressJa: "",         // e.g. "東京都港区芝公園1-2-3"
  phone: "",             // e.g. "+81-3-1234-5678"
  email: "",             // e.g. "info@lionmotors.jp" — also enables the request form
  hours: "Mon–Sat, 10:00–19:00 JST",
  hoursJa: "月〜土 10:00〜19:00(日本時間)",

  // --- Secondhand dealer licence (古物営業法) -------------------------
  licenceCommissionJa: "", // 許可をした公安委員会, e.g. "東京都公安委員会"
  licenceCommissionEn: "", // e.g. "Tokyo Metropolitan Public Safety Commission"
  licenceNo: "",           // 12-digit 許可証番号, e.g. "301234567890"
  goodsCategoryJa: "自動車",
  goodsCategoryEn: "Automobiles",

  // --- Messaging ------------------------------------------------------
  whatsapp: "",   // digits only, e.g. "819012345678"
  telegram: "",   // username without @

  // --- Sales terms for 特定商取引法に基づく表記 --------------------------
  // Leave "" until the CEO confirms; suggested wording is in the comments.
  paymentMethodJa: "",  // e.g. "銀行振込(海外送金/電信送金)"
  paymentMethodEn: "",  // e.g. "Bank transfer (international wire / SWIFT)"
  paymentTimingJa: "",  // e.g. "ご契約後3営業日以内に車両代金の全額をお支払いください。"
  paymentTimingEn: "",  // e.g. "Full payment within 3 business days after the contract."
  deliveryJa: "",       // e.g. "ご入金確認後、輸出手続きを行い、通常2〜6週間以内に船積みいたします。"
  deliveryEn: "",       // e.g. "After payment we complete export procedures; shipping usually within 2–6 weeks."
  returnsJa: "",        // e.g. "中古車の性質上、契約成立後のお客様都合による返品・キャンセルはお受けできません。…"
  returnsEn: "",        // e.g. "Due to the nature of used vehicles, returns or cancellations for the buyer's convenience are not accepted after the contract…"

  // --- Policy dates -----------------------------------------------------
  privacyDate: "",      // 制定日, e.g. "2026年11月1日"
  privacyDateEn: "",    // e.g. "1 November 2026"
};

// Fills every element with data-co="field" (and data-co-href="mailto|tel|wa|tg").
(function () {
  const C = window.COMPANY;
  const has = (v) => typeof v === "string" && v.trim() !== "";
  window.COMPANY_HAS = has;
  const TBA = '<span class="tba">未設定 / To be announced</span>';
  const esc = (s) => s.replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  function fill() {
    document.querySelectorAll("[data-co]").forEach((el) => {
      const keys = el.dataset.co.split("+");
      const vals = keys.map((k) => C[k]).filter(has);
      if (vals.length) el.textContent = vals.join(" ");
      else el.innerHTML = el.dataset.coEmpty ? esc(el.dataset.coEmpty) : TBA;
    });
    document.querySelectorAll("[data-co-href]").forEach((el) => {
      const [kind, key] = el.dataset.coHref.split(":");
      const v = C[key];
      if (!has(v)) return;
      el.href = { mailto: "mailto:" + v, tel: "tel:" + v.replace(/[^\d+]/g, ""), wa: "https://wa.me/" + v, tg: "https://t.me/" + v }[kind];
    });
  }
  document.readyState === "loading" ? document.addEventListener("DOMContentLoaded", fill) : fill();
})();
