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
import json, os

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


def linkify_support(content, loc):
    """Wrap the adapter noun-phrase in every FAQ answer with the affiliate link."""
    phrase = SUPPORT_ADAPTER.get(loc)
    if not phrase:
        return
    hit = False
    for key in ("gettingStarted", "using"):
        for item in content["support"].get(key, []):
            if phrase in item["a"]:
                item["a"] = item["a"].replace(phrase, adapter_link(phrase))
                hit = True
    if not hit:
        print(f"  WARNING: support adapter phrase not found for {loc}")


BASE_CSS = """  :root {
    --blue: #1f7ae0;
    --blue-dark: #0f4c91;
    --ink: #16202b;
    --muted: #5b6b7a;
    --surface: #f4f8fc;
    --card: #ffffff;
    --line: rgba(31,122,224,0.12);
  }
  * { box-sizing: border-box; }
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
  .brand:hover { text-decoration: none; }
  .brand img { width: 28px; height: 28px; border-radius: 7px; }
  .navright { display: flex; align-items: center; gap: 16px; }
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
  .hero {
    background: linear-gradient(165deg, var(--blue) 0%, var(--blue-dark) 100%);
    color: #fff; text-align: center; padding: 40px 20px 44px;
  }
  .hero .icon { width: 76px; height: 76px; border-radius: 18px; display: block;
    margin: 0 auto 16px; box-shadow: 0 14px 34px rgba(8,40,80,0.4); }
  .hero h1 { margin: 0 0 6px; font-size: 30px; font-weight: 800; letter-spacing: -0.6px; }
  .hero .subtitle { margin: 0; font-size: 16px; font-weight: 500; opacity: 0.93; }
  main { max-width: 720px; margin: 0 auto; padding: 28px 20px 56px; }
  .back { display: inline-block; margin-bottom: 22px; font-weight: 600; font-size: 14px; }
  footer {
    border-top: 1px solid var(--line); text-align: center;
    color: var(--muted); font-size: 14px; padding: 28px 20px 52px;
  }
  footer .links { margin-bottom: 10px; }
  footer .links a { margin: 0 8px; font-weight: 600; }
  footer .mail { display: block; margin: 4px 0 12px; }
  footer .copy { font-size: 13px; }"""

SUPPORT_CSS = """
  section { margin-bottom: 28px; }
  .sec-h {
    font-size: 13px; font-weight: 800; letter-spacing: 1.4px;
    text-transform: uppercase; color: var(--blue-dark); margin: 0 0 12px;
  }
  .card {
    background: var(--card); border: 1px solid var(--line);
    border-radius: 16px; padding: 22px 24px;
    box-shadow: 0 1px 3px rgba(15,76,145,0.05);
  }
  .faq { border-bottom: 1px solid var(--line); padding: 16px 0; }
  .faq:first-child { padding-top: 0; }
  .faq:last-child { border-bottom: 0; padding-bottom: 0; }
  .faq h3 { margin: 0 0 6px; font-size: 16px; font-weight: 700; }
  .faq p { margin: 0; color: var(--muted); font-size: 15px; }
  .contact a.email { font-weight: 700; font-size: 18px; }"""

PRIVACY_CSS = """
  main { line-height: 1.6; }
  .card {
    background: var(--card); border: 1px solid var(--line);
    border-radius: 16px; padding: 26px 28px;
    box-shadow: 0 1px 3px rgba(15,76,145,0.05);
  }
  .card h2 { font-size: 18px; font-weight: 700; margin: 26px 0 8px; }
  .card h2:first-child { margin-top: 0; }
  .card p { margin: 0 0 14px; color: #2a3a48; }
  .card ul { margin: 0 0 14px; padding-left: 20px; color: #2a3a48; }
  .card li { margin-bottom: 6px; }"""


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
  </span>
</nav>"""


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
