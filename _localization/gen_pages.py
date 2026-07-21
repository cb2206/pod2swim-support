#!/usr/bin/env python3
"""Generate localized support + privacy pages for pod2swim-support.

Source of truth: _localization/translations/<code>.json (one per language).
Output: support/<code>/index.html and support/<code>/privacy.html
(English at support/ ; the repo root index.html is the marketing page).

The chrome (sticky nav with brand + language picker, gradient hero, footer)
mirrors the marketing landing page so the two feel like one site. Each support
page links back to the marketing page via the brand and a "back" link.

Run from the repo root:  python3 _localization/gen_pages.py
"""
import json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
TRANS = os.path.join(HERE, "translations")

# Folder code -> BCP-47 lang attribute. "en" lives at support/ ; others nest.
LOCALES = ["en", "de", "es", "fr", "it", "ja", "pt-br", "zh-hans"]
LANG_ATTR = {"en": "en", "de": "de", "es": "es", "fr": "fr", "it": "it",
             "ja": "ja", "pt-br": "pt-BR", "zh-hans": "zh-Hans"}

EMAIL = "hello@pod2swim.com"

# Localized "back to the marketing page" link label.
BACK_HOME = {
    "en": "← Back to Pod2Swim", "de": "← Zurück zu Pod2Swim",
    "es": "← Volver a Pod2Swim", "fr": "← Retour à Pod2Swim",
    "it": "← Torna a Pod2Swim", "ja": "← Pod2Swim に戻る",
    "pt-br": "← Voltar para o Pod2Swim", "zh-hans": "← 返回 Pod2Swim",
}

# Amazon affiliate link for the USB-C / Lightning adapter. The support copy uses
# a non-breaking hyphen (U+2011) in "USB‑C", distinct from the marketing copy.
AMZN = "https://amzn.to/43mRukS"
SUPPORT_ADAPTER = {
    "en": "USB‑C or Lightning adapter",
    "de": "USB‑C- oder Lightning-Adapter",
    "es": "adaptador USB‑C o Lightning",
    "fr": "adaptateur USB‑C ou Lightning",
    "it": "adattatore USB‑C o Lightning",
    "ja": "USB‑CまたはLightningアダプタ",
    "pt-br": "adaptador USB‑C ou Lightning",
    "zh-hans": "USB‑C 或 Lightning 转接器",
}


def adapter_link(phrase):
    return (f'<a href="{AMZN}" target="_blank" '
            f'rel="nofollow sponsored noopener">{phrase}</a>')


# Shokz affiliate link (Impact). Brand names are Latin-script in every locale,
# so one regex covers all languages. Longest alternative first, so
# "Shokz OpenSwim Pro" becomes one link, not nested fragments.
SHOKZ = "https://shokzsingaporepteltd.pxf.io/QYAGnM"
SHOKZ_RE = re.compile(r"Shokz OpenSwim Pro|Shokz OpenSwim|OpenSwim Pro|OpenSwim|Shokz")


def shokz_link(match):
    return (f'<a href="{SHOKZ}" target="_blank" '
            f'rel="nofollow sponsored noopener">{match.group(0)}</a>')


def linkify_support(content, loc):
    """Wrap the adapter noun-phrase and Shokz/OpenSwim brand mentions in every
    FAQ answer with the respective affiliate link."""
    phrase = SUPPORT_ADAPTER.get(loc)
    hit = False
    for key in ("gettingStarted", "using"):
        for item in content["support"].get(key, []):
            if phrase and phrase in item["a"]:
                item["a"] = item["a"].replace(phrase, adapter_link(phrase))
                hit = True
            item["a"] = SHOKZ_RE.sub(shokz_link, item["a"])
    if not hit:
        print(f"  WARNING: support adapter phrase not found for {loc}")


BASE_CSS = """  :root {
    --bg: #f4f9fe; --heading: #0a1f36; --body: #3d5a78; --faint: #5f7891;
    --link: #1f6cc7; --accent: #1f7ae0;
    --nav-bg: rgba(244,249,254,0.92); --line: rgba(31,122,224,0.14);
    --card-bg: #ffffff; --card-border: rgba(31,122,224,0.16); --card-shadow: 0 2px 10px rgba(10,31,54,0.05);
    --seg-bg: rgba(31,122,224,0.07); --seg-border: rgba(31,122,224,0.18);
    --hero-bg: radial-gradient(900px 420px at 50% -20%, rgba(77,163,255,0.28), transparent 70%), #f4f9fe;
    --icon-shadow: 0 14px 34px rgba(10,31,54,0.25);
  }
  html[data-theme="dark"] {
    --bg: #061225; --heading: #ffffff; --body: #b9d1ec; --faint: #7f9cbd;
    --link: #9cc4f0; --accent: #4da3ff;
    --nav-bg: rgba(6,18,37,0.9); --line: rgba(88,166,255,0.14);
    --card-bg: rgba(255,255,255,0.03); --card-border: rgba(88,166,255,0.16); --card-shadow: none;
    --seg-bg: rgba(88,166,255,0.08); --seg-border: rgba(88,166,255,0.2);
    --hero-bg: radial-gradient(900px 420px at 50% -20%, rgba(31,122,224,0.42), transparent 70%), #061225;
    --icon-shadow: 0 14px 34px rgba(0,0,0,0.55);
  }
  * { box-sizing: border-box; }
  body {
    margin: 0;
    font-family: Sora, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    color: var(--body);
    background: var(--bg);
    line-height: 1.55;
    -webkit-font-smoothing: antialiased;
  }
  a { color: var(--link); text-decoration: none; }
  a:hover { text-decoration: underline; }
  .nav {
    position: sticky; top: 0; z-index: 20;
    display: flex; align-items: center; justify-content: space-between;
    padding: 14px 24px;
    background: var(--nav-bg);
    backdrop-filter: saturate(180%) blur(14px);
    -webkit-backdrop-filter: saturate(180%) blur(14px);
    border-bottom: 1px solid var(--line);
  }
  .brand { display: flex; align-items: center; gap: 10px; font-weight: 800;
    letter-spacing: -0.3px; color: var(--heading); font-size: 17px; }
  .brand:hover { text-decoration: none; }
  .brand img { width: 28px; height: 28px; border-radius: 7px; }
  .navright { display: flex; align-items: center; gap: 16px; }
  .picker { position: relative; }
  .picker select {
    appearance: none; -webkit-appearance: none;
    font: inherit; font-size: 13px; font-weight: 600; color: var(--link);
    background: var(--seg-bg); border: 1px solid var(--seg-border);
    border-radius: 999px; padding: 7px 30px 7px 14px; cursor: pointer;
  }
  .picker::after {
    content: ""; position: absolute; right: 13px; top: 50%;
    width: 6px; height: 6px; border-right: 2px solid var(--link);
    border-bottom: 2px solid var(--link); transform: translateY(-65%) rotate(45deg);
    pointer-events: none;
  }
  .theme-btn {
    appearance: none; -webkit-appearance: none; font: inherit; font-size: 15px;
    line-height: 1; cursor: pointer; color: var(--link);
    background: var(--seg-bg); border: 1px solid var(--seg-border);
    border-radius: 999px; width: 36px; height: 36px;
    display: inline-flex; align-items: center; justify-content: center; padding: 0;
  }
  .hero {
    background: var(--hero-bg);
    text-align: center; padding: 48px 20px 50px;
  }
  .hero .icon { width: 76px; height: 76px; border-radius: 18px; display: block;
    margin: 0 auto 16px; box-shadow: var(--icon-shadow); }
  .hero h1 { margin: 0 0 6px; font-size: 32px; font-weight: 800;
    letter-spacing: -1px; color: var(--heading); }
  .hero .subtitle { margin: 0; font-size: 16px; font-weight: 500; color: var(--body); }
  main { max-width: 720px; margin: 0 auto; padding: 28px 20px 56px; }
  .back { display: inline-block; margin-bottom: 22px; font-weight: 600; font-size: 14px; }
  footer {
    border-top: 1px solid var(--line); text-align: center;
    color: var(--faint); font-size: 14px; padding: 28px 20px 52px;
  }
  footer .links { margin-bottom: 10px; }
  footer .links a { margin: 0 8px; font-weight: 600; }
  footer .mail { display: block; margin: 4px 0 12px; }
  footer .copy { font-size: 13px; }"""

SUPPORT_CSS = """
  section { margin-bottom: 28px; }
  .sec-h {
    font-size: 13px; font-weight: 700; letter-spacing: 2px;
    text-transform: uppercase; color: var(--accent); margin: 0 0 12px;
  }
  .card {
    background: var(--card-bg); border: 1px solid var(--card-border);
    border-radius: 20px; padding: 22px 24px;
    box-shadow: var(--card-shadow);
  }
  .faq { border-bottom: 1px solid var(--line); padding: 16px 0; }
  .faq:first-child { padding-top: 0; }
  .faq:last-child { border-bottom: 0; padding-bottom: 0; }
  .faq h3 { margin: 0 0 6px; font-size: 16px; font-weight: 700; color: var(--heading); }
  .faq p { margin: 0; color: var(--body); font-size: 15px; }
  .contact a.email { font-weight: 700; font-size: 18px; }"""

PRIVACY_CSS = """
  main { line-height: 1.6; }
  .card {
    background: var(--card-bg); border: 1px solid var(--card-border);
    border-radius: 20px; padding: 26px 28px;
    box-shadow: var(--card-shadow);
  }
  .card h2 { font-size: 18px; font-weight: 700; margin: 26px 0 8px; color: var(--heading); }
  .card h2:first-child { margin-top: 0; }
  .card p { margin: 0 0 14px; color: var(--body); }
  .card ul { margin: 0 0 14px; padding-left: 20px; color: var(--body); }
  .card li { margin-bottom: 6px; }"""


# Injected into <head> of every generated page: web font + a tiny script that
# applies the saved (or system) appearance before first paint to avoid a flash.
HEAD_EXTRA = """<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Sora:wght@400;600;700;800&display=swap" rel="stylesheet">
<script>
(function(){
  var t = null;
  try { t = localStorage.getItem("p2s_theme"); } catch(e){}
  if (t !== "light" && t !== "dark")
    t = (window.matchMedia && matchMedia("(prefers-color-scheme: dark)").matches) ? "dark" : "light";
  document.documentElement.setAttribute("data-theme", t);
})();
</script>"""

# Light/dark toggle wiring, emitted right after the nav on every page.
THEME_JS = """<script>
(function(){
  var b = document.getElementById("theme-toggle");
  function icon(){ b.textContent = document.documentElement.getAttribute("data-theme") === "dark" ? "\u2600" : "\u263e"; }
  b.addEventListener("click", function(){
    var next = document.documentElement.getAttribute("data-theme") === "dark" ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", next);
    try { localStorage.setItem("p2s_theme", next); } catch(e){}
    icon();
  });
  icon();
})();
</script>"""


def lang_select(current, page, names):
    opts = []
    for loc in LOCALES:
        prefix = "" if current == "en" else "../"
        target = page if loc == "en" else f"{loc}/{page}"
        href = prefix + target
        sel = " selected" if loc == current else ""
        opts.append(f'<option value="{href}"{sel}>{names[loc]}</option>')
    inner = "\n        ".join(opts)
    return ('<select aria-label="Language" '
            'onchange="if(this.value)location.href=this.value">\n        '
            + inner + "\n      </select>")


def nav_html(root_prefix, icon, select_html):
    return f"""<nav class="nav">
  <a class="brand" href="{root_prefix}"><img src="{icon}" alt="Pod2Swim"> Pod2Swim</a>
  <span class="navright">
    <span class="picker">{select_html}</span>
    <button type="button" class="theme-btn" id="theme-toggle" aria-label="Light / dark">\u263e</button>
  </span>
</nav>
{THEME_JS}"""


def support_html(c, loc, lang, root_prefix, icon, select_html):
    s = c["support"]
    faqs = lambda items: "\n".join(
        f'      <div class="faq">\n        <h3>{i["q"]}</h3>\n        <p>{i["a"]}</p>\n      </div>'
        for i in items)
    return f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{s["title"]}</title>
<meta name="description" content="{s["metaDesc"]}">
<link rel="icon" type="image/png" href="{icon}">
{HEAD_EXTRA}
<style>
{BASE_CSS}{SUPPORT_CSS}
</style>
</head>
<body>
{nav_html(root_prefix, icon, select_html)}

<header class="hero">
  <img class="icon" src="{icon}" alt="Pod2Swim app icon">
  <h1>{s["headerTitle"]}</h1>
  <p class="subtitle">{s["headerSubtitle"]}</p>
</header>

<main>
  <a class="back" href="{root_prefix}">{BACK_HOME[loc]}</a>

  <section class="contact">
    <h2 class="sec-h">{s["contactH"]}</h2>
    <div class="card">
      <p style="margin:0 0 8px;">{s["contactText"]}</p>
      <a class="email" href="mailto:{EMAIL}">{EMAIL}</a>
    </div>
  </section>

  <section>
    <h2 class="sec-h">{s["gettingStartedH"]}</h2>
    <div class="card">
{faqs(s["gettingStarted"])}
    </div>
  </section>

  <section>
    <h2 class="sec-h">{s["usingH"]}</h2>
    <div class="card">
{faqs(s["using"])}
    </div>
  </section>

  <section>
    <h2 class="sec-h">{s["privacyH"]}</h2>
    <div class="card">
      <p style="margin:0;">{s["privacyBlurb"]}</p>
    </div>
  </section>
</main>

<footer>
  <div class="links">{s["footer"]}</div>
  <a class="mail" href="mailto:{EMAIL}">{EMAIL}</a>
  <div class="copy">© 2026 Christian Bartels</div>
</footer>
</body>
</html>
"""


def privacy_html(c, loc, lang, root_prefix, icon, select_html):
    p = c["privacy"]
    secs = "\n".join(f'    <h2>{x["h2"]}</h2>\n    {x["body"]}' for x in p["sections"])
    return f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{p["title"]}</title>
<meta name="description" content="{p["metaDesc"]}">
<link rel="icon" type="image/png" href="{icon}">
{HEAD_EXTRA}
<style>
{BASE_CSS}{PRIVACY_CSS}
</style>
</head>
<body>
{nav_html(root_prefix, icon, select_html)}

<header class="hero">
  <img class="icon" src="{icon}" alt="Pod2Swim app icon">
  <h1>{p["headerTitle"]}</h1>
  <p class="subtitle">{p["headerSub"]}</p>
</header>

<main>
  <a class="back" href="index.html">{p["back"]}</a>
  <div class="card">
{secs}
  </div>
</main>

<footer>
  <div class="links">{p["footer"]}</div>
  <a class="mail" href="mailto:{EMAIL}">{EMAIL}</a>
  <div class="copy">© 2026 Christian Bartels</div>
</footer>
</body>
</html>
"""


def main():
    global LOCALES
    present = [loc for loc in LOCALES
               if os.path.exists(os.path.join(TRANS, f"{loc}.json"))]
    content = {loc: json.load(open(os.path.join(TRANS, f"{loc}.json")))
               for loc in present}
    names = {loc: content[loc]["languageName"] for loc in present}
    LOCALES = present  # picker only links to locales we actually have
    support_root = os.path.join(REPO, "support")
    for loc in present:
        linkify_support(content[loc], loc)
        lang = LANG_ATTR[loc]
        root_prefix = "../" if loc == "en" else "../../"
        icon = root_prefix + "assets/icon.png"
        outdir = support_root if loc == "en" else os.path.join(support_root, loc)
        os.makedirs(outdir, exist_ok=True)
        idx_sel = lang_select(loc, "index.html", names)
        priv_sel = lang_select(loc, "privacy.html", names)
        open(os.path.join(outdir, "index.html"), "w").write(
            support_html(content[loc], loc, lang, root_prefix, icon, idx_sel))
        open(os.path.join(outdir, "privacy.html"), "w").write(
            privacy_html(content[loc], loc, lang, root_prefix, icon, priv_sel))
        print(f"  {loc}: index.html + privacy.html")
    print(f"Generated {len(LOCALES)} locales.")


if __name__ == "__main__":
    main()
