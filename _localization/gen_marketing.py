#!/usr/bin/env python3
"""Generate the Pod2Swim marketing landing page (repo root index.html).

Source of truth: the App Store metadata in the Pod2Swim app repo
(fastlane/metadata/<locale>/{description,subtitle,promotional_text,name}.txt).
Those descriptions are parsed into structured marketing content and merged with
the short UI-chrome strings defined below, then baked into a single
self-contained index.html with embedded translations, browser-language
detection and a language picker.

Usage (from the support repo root):
    python3 _localization/gen_marketing.py [path-to-Pod2Swim-app-repo]

Default app-repo path: ../Pod2Swim  (overridable via the argument or the
POD2SWIM_APP_REPO env var).
"""
import json, os, re, sys, html

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)

APP_REPO = (sys.argv[1] if len(sys.argv) > 1
            else os.environ.get("POD2SWIM_APP_REPO", "/Users/cb/dev/Pod2Swim"))
META = os.path.join(APP_REPO, "fastlane", "metadata")

# Live App Store listing (Pod2Swim, app id 6766092966). The id-only URL
# redirects to each visitor's local storefront.
APP_STORE_URL = "https://apps.apple.com/app/id6766092966"

# site code -> App Store locale folder
LOCALES = {
    "en": "en-US", "de": "de-DE", "es": "es-ES", "fr": "fr-FR",
    "it": "it", "ja": "ja", "pt-br": "pt-BR", "zh-hans": "zh-Hans",
}
LANG_ATTR = {"en": "en", "de": "de", "es": "es", "fr": "fr", "it": "it",
             "ja": "ja", "pt-br": "pt-BR", "zh-hans": "zh-Hans"}
ORDER = ["en", "de", "es", "fr", "it", "ja", "pt-br", "zh-hans"]
LANG_NAME = {"en": "English", "de": "Deutsch", "es": "Español", "fr": "Français",
             "it": "Italiano", "ja": "日本語", "pt-br": "Português", "zh-hans": "简体中文"}

# Short UI strings that are not part of the App Store description.
CHROME = {
    "en": {"badge": "Download on the",
           "shotsH": "A look inside", "support": "Support", "privacy": "Privacy Policy",
           "compatH": "Compatibility", "metaDesc": "Pod2Swim loads your favourite podcasts onto a Shokz OpenSwim or any USB-storage swim headset, so you can listen underwater — no Bluetooth, no phone at the poolside."},
    "de": {"badge": "Laden im",
           "shotsH": "Ein Blick in die App", "support": "Support", "privacy": "Datenschutz",
           "compatH": "Kompatibilität", "metaDesc": "Pod2Swim lädt deine Lieblingspodcasts auf einen Shokz OpenSwim oder jeden USB-Kopfhörer – zum Hören unter Wasser, ohne Bluetooth und ohne Handy am Beckenrand."},
    "es": {"badge": "Consíguelo en el",
           "shotsH": "Un vistazo a la app", "support": "Soporte", "privacy": "Privacidad",
           "compatH": "Compatibilidad", "metaDesc": "Pod2Swim carga tus pódcasts favoritos en un Shokz OpenSwim o cualquier auricular USB para escuchar bajo el agua, sin Bluetooth ni móvil en el borde."},
    "fr": {"badge": "Télécharger dans l'",
           "shotsH": "Un aperçu de l'app", "support": "Assistance", "privacy": "Confidentialité",
           "compatH": "Compatibilité", "metaDesc": "Pod2Swim charge tes podcasts préférés sur un Shokz OpenSwim ou tout casque USB pour écouter sous l'eau, sans Bluetooth ni téléphone au bord du bassin."},
    "it": {"badge": "Scaricala su",
           "shotsH": "Uno sguardo all'app", "support": "Supporto", "privacy": "Privacy",
           "compatH": "Compatibilità", "metaDesc": "Pod2Swim carica i tuoi podcast preferiti su Shokz OpenSwim o qualsiasi cuffia USB per ascoltarli sott'acqua, senza Bluetooth e senza telefono a bordo piscina."},
    "ja": {"badge": "ダウンロード",
           "shotsH": "アプリの中身をチラ見せ", "support": "サポート", "privacy": "プライバシー",
           "compatH": "対応機器", "metaDesc": "Pod2Swimは、お気に入りのポッドキャストをShokz OpenSwimなどのUSBヘッドセットに転送。Bluetoothもプールサイドのスマホもなしで、水中で楽しめます。"},
    "pt-br": {"badge": "Baixar na",
              "shotsH": "Um olhar pelo app", "support": "Suporte", "privacy": "Privacidade",
              "compatH": "Compatibilidade", "metaDesc": "O Pod2Swim carrega os seus podcasts favoritos num Shokz OpenSwim ou em qualquer fone USB para ouvir embaixo d'água, sem Bluetooth e sem celular na borda."},
    "zh-hans": {"badge": "前往下载",
                "shotsH": "先睹为快", "support": "支持", "privacy": "隐私政策",
                "compatH": "兼容设备", "metaDesc": "Pod2Swim 把你喜欢的播客导入 Shokz OpenSwim 等 USB 耳机，水下也能畅听——无需蓝牙，手机留在岸边。"},
}

SHOTS = ["p2s-1.png", "p2s-2.png", "p2s-3.png", "p2s-4.png",
         "p2s-5.png", "p2s-6.png", "p2s-7.png"]


# Amazon affiliate link for the USB-C / Lightning adapter. The exact adapter
# noun-phrase in each locale's compatibility line gets wrapped in this link.
AMZN = "https://amzn.to/43mRukS"
MARKETING_ADAPTER = {
    "en": "USB-C or Lightning adapter",
    "de": "USB-C- oder Lightning-Adapter",
    "es": "adaptador USB-C o Lightning",
    "fr": "adaptateur USB-C ou Lightning",
    "it": "adattatore USB-C o Lightning",
    "ja": "USB-CまたはLightningのアダプタ",
    "pt-br": "adaptador USB-C ou Lightning",
    "zh-hans": "USB-C 或 Lightning 转接头",
}


def adapter_link(phrase):
    return (f'<a href="{AMZN}" target="_blank" '
            f'rel="nofollow sponsored noopener">{phrase}</a>')


# Shokz affiliate link (Impact). Every Shokz / OpenSwim brand mention in the
# user-visible copy gets wrapped — except the trademark disclaimer, which has
# to stay a plain non-affiliation statement. The brand names are Latin-script
# in every locale, so one regex covers all languages. Longest alternative
# first, so "Shokz OpenSwim Pro" becomes one link, not nested fragments.
SHOKZ = "https://shokzsingaporepteltd.pxf.io/QYAGnM"
SHOKZ_RE = re.compile(r"Shokz OpenSwim Pro|Shokz OpenSwim|OpenSwim Pro|OpenSwim|Shokz")


def linkify_shokz(text):
    return SHOKZ_RE.sub(
        lambda m: (f'<a href="{SHOKZ}" target="_blank" '
                   f'rel="nofollow sponsored noopener">{m.group(0)}</a>'),
        text)


# Affiliate-disclosure sentence appended to the trademark disclaimer on the
# website only (the page is the sole place the affiliate links appear). Kept out
# of the App Store description source so the store copy stays link-free. Covers
# both the Shokz and Amazon adapter links — "links on this site" is deliberately
# generic since the line is only ever rendered on pod2swim.com.
DISCLOSURE = {
    "en": "As a Shokz affiliate, Pod2Swim may earn a commission on purchases made through links on this site.",
    "de": "Als Shokz-Partner kann Pod2Swim eine Provision für Käufe über Links auf dieser Website erhalten.",
    "es": "Como afiliado de Shokz, Pod2Swim puede ganar una comisión por las compras realizadas a través de los enlaces de este sitio.",
    "fr": "En tant qu'affilié Shokz, Pod2Swim peut percevoir une commission sur les achats effectués via les liens de ce site.",
    "it": "In qualità di affiliato Shokz, Pod2Swim può guadagnare una commissione sugli acquisti effettuati tramite i link di questo sito.",
    "ja": "ShokzのアフィリエイトとしてPod2Swimは、このサイト上のリンク経由の購入で手数料を得る場合があります。",
    "pt-br": "Como afiliado da Shokz, o Pod2Swim pode receber uma comissão por compras feitas através dos links neste site.",
    "zh-hans": "作为 Shokz 联盟会员，Pod2Swim 可能会从通过本网站链接完成的购买中获得佣金。",
}


def linkify_adapter(text, code):
    phrase = MARKETING_ADAPTER.get(code)
    if phrase and phrase in text:
        return text.replace(phrase, adapter_link(phrase), 1)
    print(f"  WARNING: marketing adapter phrase not found for {code}")
    return text


def read(loc_folder, field):
    p = os.path.join(META, loc_folder, field + ".txt")
    with open(p, encoding="utf-8") as f:
        return f.read().strip()


def parse_description(text):
    """Split an App Store description into intro, pitch, bullet-sections, tail."""
    paras = [p.strip() for p in text.replace("\r\n", "\n").split("\n\n") if p.strip()]
    intro, pitch = paras[0], paras[1]
    sections, tail = [], []
    for p in paras[2:]:
        if "•" in p:
            lines = [l.strip() for l in p.split("\n") if l.strip()]
            title = lines[0]
            bullets = [l.lstrip("•").strip() for l in lines[1:]]
            sections.append({"title": title, "bullets": bullets})
        else:
            tail.append(p)
    compat = tail[0] if tail else ""
    disclaimer = tail[1] if len(tail) > 1 else ""
    return intro, pitch, sections, compat, disclaimer


def build_locale(code):
    folder = LOCALES[code]
    intro, pitch, sections, compat, disclaimer = parse_description(read(folder, "description"))
    c = CHROME[code]
    return {
        "langName": LANG_NAME[code],
        "name": read(folder, "name"),
        "subtitle": read(folder, "subtitle"),
        "tagline": linkify_shokz(read(folder, "promotional_text")),
        "intro": intro,
        "pitch": linkify_shokz(pitch),
        "sections": sections,
        "compatH": c["compatH"],
        "compat": linkify_shokz(linkify_adapter(compat, code)),
        # CJK runs sentences together with no inter-sentence space.
        "disclaimer": (disclaimer + ("" if code in ("ja", "zh-hans") else " ")
                       + DISCLOSURE[code]).strip(),
        "badge": c["badge"],
        "shotsH": c["shotsH"],
        "support": c["support"],
        "privacy": c["privacy"],
        "metaDesc": c["metaDesc"],
    }


PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Pod2Swim — Podcasts on your swim headset</title>
<meta name="description" id="metaDesc" content="">
<meta property="og:title" content="Pod2Swim">
<meta property="og:description" content="Podcasts on your swim headset. Load episodes onto your OpenSwim and listen underwater — no Bluetooth, no phone at the poolside.">
<meta property="og:type" content="website">
<meta property="og:image" content="assets/icon.png">
<meta name="impact-site-verification" value="e8cd3ad2-3b6c-485b-94a3-6e549ba2b57e">
<link rel="icon" type="image/png" href="assets/icon.png">
<style>
  :root {
    --blue: #1f7ae0;
    --blue-dark: #0f4c91;
    --ink: #16202b;
    --muted: #5b6b7a;
    --surface: #f4f8fc;
    --card: #ffffff;
    --line: rgba(31,122,224,0.12);
  }
  * { box-sizing: border-box; }
  html { scroll-behavior: smooth; }
  body {
    margin: 0;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    color: var(--ink);
    background: var(--surface);
    line-height: 1.55;
    -webkit-font-smoothing: antialiased;
  }
  a { color: var(--blue); text-decoration: none; }
  a:hover { text-decoration: underline; }

  /* top nav */
  .nav {
    position: sticky; top: 0; z-index: 20;
    display: flex; align-items: center; justify-content: space-between;
    padding: 12px 20px;
    background: rgba(255,255,255,0.82);
    backdrop-filter: saturate(180%) blur(14px);
    -webkit-backdrop-filter: saturate(180%) blur(14px);
    border-bottom: 1px solid var(--line);
  }
  .brand { display: flex; align-items: center; gap: 10px; font-weight: 800;
    letter-spacing: -0.3px; color: var(--ink); font-size: 17px; }
  .brand img { width: 28px; height: 28px; border-radius: 7px; }
  .navright { display: flex; align-items: center; gap: 16px; }
  .navlink { font-weight: 600; font-size: 14px; color: var(--blue-dark); }
  .picker { position: relative; }
  .picker select {
    appearance: none; -webkit-appearance: none;
    font: inherit; font-size: 14px; font-weight: 600; color: var(--blue-dark);
    background: rgba(31,122,224,0.08); border: 1px solid var(--line);
    border-radius: 999px; padding: 7px 30px 7px 14px; cursor: pointer;
  }
  .picker::after {
    content: ""; position: absolute; right: 13px; top: 50%;
    width: 7px; height: 7px; border-right: 2px solid var(--blue-dark);
    border-bottom: 2px solid var(--blue-dark); transform: translateY(-65%) rotate(45deg);
    pointer-events: none;
  }

  /* hero */
  .hero {
    background: linear-gradient(165deg, var(--blue) 0%, var(--blue-dark) 100%);
    color: #fff; text-align: center; padding: 64px 20px 72px;
    position: relative; overflow: hidden;
  }
  .hero .icon {
    width: 116px; height: 116px; border-radius: 26px; display: block; margin: 0 auto 22px;
    box-shadow: 0 20px 50px rgba(8,40,80,0.45); }
  .hero h1 { margin: 0 0 6px; font-size: 38px; font-weight: 800; letter-spacing: -0.8px; }
  .hero .subtitle { margin: 0 0 18px; font-size: 19px; font-weight: 600; opacity: 0.95; }
  .hero .tagline { max-width: 560px; margin: 0 auto 30px; font-size: 17px; opacity: 0.92; }
  .hero .tagline a { color: #fff; text-decoration: underline; text-underline-offset: 3px; }

  /* App Store download badge */
  .badgewrap { display: inline-flex; flex-direction: column; align-items: center; gap: 9px; }
  .appstore {
    display: inline-flex; align-items: center; gap: 11px;
    background: #0c0c0c; color: #fff; border-radius: 11px;
    padding: 10px 18px; text-decoration: none;
    border: 1px solid rgba(255,255,255,0.25); user-select: none;
    transition: transform .12s ease, box-shadow .12s ease;
  }
  .appstore:hover {
    text-decoration: none; transform: translateY(-1px);
    box-shadow: 0 12px 28px rgba(8,40,80,0.4);
  }
  .appstore:active { transform: translateY(0); }
  .appstore svg { width: 26px; height: 26px; fill: #fff; }
  .appstore .small { font-size: 11px; line-height: 1; opacity: 0.85; }
  .appstore .big { font-size: 19px; font-weight: 600; line-height: 1.15; letter-spacing: -0.2px; }

  main { max-width: 860px; margin: 0 auto; padding: 0 20px; }
  .pitch { font-size: 18px; color: #25323f; max-width: 680px;
    margin: 44px auto 8px; text-align: center; }

  .features { display: grid; gap: 18px; margin: 40px 0 8px;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); }
  .feature {
    background: var(--card); border: 1px solid var(--line); border-radius: 18px;
    padding: 24px 24px 8px; box-shadow: 0 1px 3px rgba(15,76,145,0.05);
  }
  .feature h2 {
    font-size: 13px; font-weight: 800; letter-spacing: 1.2px; text-transform: uppercase;
    color: var(--blue-dark); margin: 0 0 14px;
  }
  .feature ul { list-style: none; margin: 0; padding: 0; }
  .feature li {
    position: relative; padding: 0 0 16px 26px; font-size: 15px; color: #2a3a48;
  }
  .feature li::before {
    content: ""; position: absolute; left: 2px; top: 7px;
    width: 9px; height: 9px; border-radius: 50%;
    background: var(--blue); box-shadow: 0 0 0 4px rgba(31,122,224,0.14);
  }

  .shots { margin: 56px 0 8px; }
  .shots h2 { text-align: center; font-size: 24px; font-weight: 800;
    letter-spacing: -0.4px; margin: 0 0 26px; color: var(--ink); }
  .gallery {
    display: flex; gap: 18px; overflow-x: auto; padding: 8px 4px 22px;
    scroll-snap-type: x mandatory; -webkit-overflow-scrolling: touch;
  }
  .gallery img {
    width: 232px; flex: 0 0 auto; border-radius: 22px;
    border: 1px solid var(--line); scroll-snap-align: center;
    box-shadow: 0 14px 36px rgba(15,76,145,0.16); background: #fff;
  }

  .fineprint { max-width: 680px; margin: 40px auto 0; }
  .fineprint h2 { font-size: 13px; font-weight: 800; letter-spacing: 1.2px;
    text-transform: uppercase; color: var(--blue-dark); margin: 0 0 8px; }
  .fineprint p { margin: 0 0 12px; color: var(--muted); font-size: 14px; }

  footer {
    margin-top: 56px; border-top: 1px solid var(--line);
    text-align: center; color: var(--muted); font-size: 14px;
    padding: 30px 20px 56px;
  }
  footer .links { margin-bottom: 12px; }
  footer .links a { margin: 0 10px; font-weight: 600; }
  footer .mail { display: block; margin: 6px 0 14px; }

  @media (max-width: 560px) {
    .hero h1 { font-size: 31px; }
    .hero { padding: 48px 18px 56px; }
  }
</style>
</head>
<body>
<nav class="nav">
  <span class="brand"><img src="assets/icon.png" alt="Pod2Swim"> Pod2Swim</span>
  <span class="navright">
    <a class="navlink" id="nav-support" href="support/">Support</a>
    <span class="picker"><select id="lang" aria-label="Language"></select></span>
  </span>
</nav>

<header class="hero">
  <img class="icon" src="assets/icon.png" alt="Pod2Swim app icon">
  <h1 id="h-name">Pod2Swim</h1>
  <p class="subtitle" id="h-subtitle"></p>
  <p class="tagline" id="h-tagline"></p>
  <div class="badgewrap">
    <a class="appstore" id="appstore-link" href="__APPSTORE__" target="_blank" rel="noopener" aria-label="Download Pod2Swim on the App Store">
      <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M16.36 12.78c-.02-2.3 1.88-3.4 1.96-3.46-1.07-1.56-2.73-1.78-3.32-1.8-1.41-.14-2.76.83-3.48.83-.72 0-1.82-.81-3-.79-1.54.02-2.96.9-3.75 2.28-1.6 2.78-.41 6.89 1.15 9.14.76 1.1 1.67 2.34 2.86 2.29 1.15-.05 1.58-.74 2.97-.74 1.38 0 1.77.74 2.98.72 1.23-.02 2.01-1.12 2.76-2.23.87-1.28 1.23-2.52 1.25-2.58-.03-.01-2.4-.92-2.42-3.65zM14.13 6.04c.64-.78 1.07-1.85.95-2.92-.92.04-2.03.61-2.69 1.38-.59.68-1.11 1.78-.97 2.83 1.03.08 2.07-.52 2.71-1.29z"/></svg>
      <span><span class="small" id="b-small">Download on the</span><br><span class="big">App Store</span></span>
    </a>
  </div>
</header>

<main>
  <p class="pitch" id="m-pitch"></p>

  <div class="features" id="m-features"></div>

  <section class="shots">
    <h2 id="m-shotsH"></h2>
    <div class="gallery" id="m-gallery"></div>
  </section>

  <section class="fineprint">
    <h2 id="m-compatH"></h2>
    <p id="m-compat"></p>
    <p id="m-disclaimer"></p>
  </section>
</main>

<footer>
  <div class="links">
    <a id="f-support" href="support/">Support</a>
    <a id="f-privacy" href="support/privacy.html">Privacy Policy</a>
  </div>
  <a class="mail" href="mailto:hello@pod2swim.com">hello@pod2swim.com</a>
  <div id="f-copy">© 2026 Christian Bartels</div>
</footer>

<script>
const SHOTS = __SHOTS__;
const I18N = __I18N__;
const ORDER = __ORDER__;
const LANG_ATTR = __LANG_ATTR__;
// support deep-link path per locale (en lives at support/, others under support/<code>/)
function supportPath(code){ return code === "en" ? "support/" : "support/" + code + "/"; }
function privacyPath(code){ return code === "en" ? "support/privacy.html" : "support/" + code + "/privacy.html"; }

function pick(){
  const saved = localStorage.getItem("p2s_lang");
  if (saved && I18N[saved]) return saved;
  for (const pref of (navigator.languages || [navigator.language || "en"])){
    const low = pref.toLowerCase();
    if (low.startsWith("zh")) return "zh-hans";
    if (low.startsWith("pt")) return "pt-br";
    const base = low.split("-")[0];
    if (I18N[base]) return base;
  }
  return "en";
}

function el(tag, cls, html){ const e = document.createElement(tag); if(cls) e.className = cls; if(html!=null) e.innerHTML = html; return e; }

function render(code){
  const t = I18N[code];
  document.documentElement.lang = LANG_ATTR[code] || code;
  document.title = t.name + " — " + t.subtitle;
  document.getElementById("metaDesc").setAttribute("content", t.metaDesc);

  document.getElementById("h-name").textContent = t.name;
  document.getElementById("h-subtitle").textContent = t.subtitle;
  document.getElementById("h-tagline").innerHTML = t.tagline;
  document.getElementById("b-small").textContent = t.badge;
  document.getElementById("m-pitch").innerHTML = t.pitch;
  document.getElementById("m-shotsH").textContent = t.shotsH;
  document.getElementById("m-compatH").textContent = t.compatH;
  document.getElementById("m-compat").innerHTML = t.compat;
  document.getElementById("m-disclaimer").textContent = t.disclaimer;

  const feats = document.getElementById("m-features");
  feats.innerHTML = "";
  for (const s of t.sections){
    const card = el("div", "feature");
    card.appendChild(el("h2", null, ""));
    card.firstChild.textContent = s.title;
    const ul = el("ul");
    for (const b of s.bullets){ const li = el("li"); li.textContent = b; ul.appendChild(li); }
    card.appendChild(ul);
    feats.appendChild(card);
  }

  const g = document.getElementById("m-gallery");
  if (!g.dataset.filled){
    SHOTS.forEach((src, i) => {
      const img = el("img");
      img.src = "assets/shots/" + src;
      img.loading = "lazy";
      img.alt = t.name + " screenshot " + (i+1);
      g.appendChild(img);
    });
    g.dataset.filled = "1";
  } else {
    [...g.children].forEach((img, i) => img.alt = t.name + " screenshot " + (i+1));
  }

  const sup = document.getElementById("f-support");
  sup.textContent = t.support; sup.href = supportPath(code);
  const pri = document.getElementById("f-privacy");
  pri.textContent = t.privacy; pri.href = privacyPath(code);
  const navSup = document.getElementById("nav-support");
  navSup.textContent = t.support; navSup.href = supportPath(code);

  document.getElementById("lang").value = code;
}

(function init(){
  const sel = document.getElementById("lang");
  for (const code of ORDER){
    const o = document.createElement("option");
    o.value = code; o.textContent = I18N[code].langName;
    sel.appendChild(o);
  }
  sel.addEventListener("change", e => {
    localStorage.setItem("p2s_lang", e.target.value);
    render(e.target.value);
  });
  render(pick());
})();
</script>
</body>
</html>
"""


def main():
    data = {code: build_locale(code) for code in ORDER}
    # persist source-of-truth marketing JSON (mirrors translations/ pattern)
    mdir = os.path.join(HERE, "marketing")
    os.makedirs(mdir, exist_ok=True)
    for code in ORDER:
        with open(os.path.join(mdir, code + ".json"), "w", encoding="utf-8") as f:
            json.dump(data[code], f, ensure_ascii=False, indent=2)
    page = (PAGE
            .replace("__APPSTORE__", APP_STORE_URL)
            .replace("__SHOTS__", json.dumps(SHOTS))
            .replace("__I18N__", json.dumps(data, ensure_ascii=False))
            .replace("__ORDER__", json.dumps(ORDER))
            .replace("__LANG_ATTR__", json.dumps(LANG_ATTR)))
    with open(os.path.join(REPO, "index.html"), "w", encoding="utf-8") as f:
        f.write(page)
    print("Wrote index.html (%d locales) + _localization/marketing/*.json" % len(ORDER))


if __name__ == "__main__":
    main()
