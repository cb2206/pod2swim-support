#!/usr/bin/env python3
"""Generate localized support + privacy pages for pod2swim-support.

Source of truth: _localization/translations/<code>.json (one per language).
Output: <code>/index.html and <code>/privacy.html (English at repo root).
Run from the repo root:  python3 _localization/gen_pages.py
"""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
TRANS = os.path.join(HERE, "translations")

# Folder code -> BCP-47 lang attribute. "en" lives at the repo root.
LOCALES = ["en", "de", "es", "fr", "it", "ja", "pt-br", "zh-hans"]
LANG_ATTR = {"en": "en", "de": "de", "es": "es", "fr": "fr", "it": "it",
             "ja": "ja", "pt-br": "pt-BR", "zh-hans": "zh-Hans"}

EMAIL = "pod2swim@cbgroup.global"

SUPPORT_CSS = """  :root {
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
  }
  header {
    background: linear-gradient(160deg, var(--blue) 0%, var(--blue-dark) 100%);
    color: #fff;
    padding: 56px 20px 48px;
    text-align: center;
  }
  header .drop { font-size: 52px; line-height: 1; }
  header h1 { margin: 14px 0 6px; font-size: 30px; font-weight: 800; letter-spacing: -0.5px; }
  header p { margin: 0; opacity: 0.92; font-size: 16px; }
  main { max-width: 720px; margin: 0 auto; padding: 32px 20px 64px; }
  section { margin-bottom: 28px; }
  h2 {
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
  a { color: var(--blue); text-decoration: none; }
  a:hover { text-decoration: underline; }
  .contact a { font-weight: 700; font-size: 18px; }
  footer { text-align: center; color: var(--muted); font-size: 13px; padding: 0 20px 48px; }"""

PRIVACY_CSS = """  :root {
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
    line-height: 1.6;
  }
  header {
    background: linear-gradient(160deg, var(--blue) 0%, var(--blue-dark) 100%);
    color: #fff;
    padding: 48px 20px 40px;
    text-align: center;
  }
  header h1 { margin: 0; font-size: 26px; font-weight: 800; letter-spacing: -0.5px; }
  header p { margin: 8px 0 0; opacity: 0.9; font-size: 14px; }
  main { max-width: 720px; margin: 0 auto; padding: 32px 20px 64px; }
  .card {
    background: var(--card); border: 1px solid var(--line);
    border-radius: 16px; padding: 26px 28px;
    box-shadow: 0 1px 3px rgba(15,76,145,0.05);
  }
  h2 { font-size: 18px; font-weight: 700; margin: 26px 0 8px; }
  h2:first-child { margin-top: 0; }
  p { margin: 0 0 14px; color: #2a3a48; }
  ul { margin: 0 0 14px; padding-left: 20px; color: #2a3a48; }
  li { margin-bottom: 6px; }
  a { color: var(--blue); text-decoration: none; }
  a:hover { text-decoration: underline; }
  .back { display: inline-block; margin-bottom: 20px; font-weight: 600; font-size: 14px; }
  footer { text-align: center; color: var(--muted); font-size: 13px; padding: 0 20px 48px; }"""

LANGBAR_CSS = """
  .langbar { background: var(--card); border-bottom: 1px solid var(--line);
    text-align: center; padding: 10px 16px; font-size: 13px; }
  .langbar a { margin: 0 7px; color: var(--muted); white-space: nowrap; }
  .langbar a.active { color: var(--blue-dark); font-weight: 700; }"""


def langbar(current, page, names):
    links = []
    for loc in LOCALES:
        prefix = "" if current == "en" else "../"
        target = page if loc == "en" else f"{loc}/{page}"
        href = prefix + target
        cls = ' class="active"' if loc == current else ""
        links.append(f'<a href="{href}"{cls}>{names[loc]}</a>')
    return '<nav class="langbar">\n  ' + "\n  ".join(links) + "\n</nav>"


def support_html(c, lang, bar):
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
<style>
{SUPPORT_CSS}{LANGBAR_CSS}
</style>
</head>
<body>
<header>
  <div class="drop">💧</div>
  <h1>{s["headerTitle"]}</h1>
  <p>{s["headerSubtitle"]}</p>
</header>
{bar}

<main>
  <section class="contact">
    <h2>{s["contactH"]}</h2>
    <div class="card">
      <p style="margin:0 0 8px;">{s["contactText"]}</p>
      <a href="mailto:{EMAIL}">{EMAIL}</a>
    </div>
  </section>

  <section>
    <h2>{s["gettingStartedH"]}</h2>
    <div class="card">
{faqs(s["gettingStarted"])}
    </div>
  </section>

  <section>
    <h2>{s["usingH"]}</h2>
    <div class="card">
{faqs(s["using"])}
    </div>
  </section>

  <section>
    <h2>{s["privacyH"]}</h2>
    <div class="card">
      <p style="margin:0;">{s["privacyBlurb"]}</p>
    </div>
  </section>
</main>

<footer>
  {s["footer"]}
</footer>
</body>
</html>
"""


def privacy_html(c, lang, bar):
    p = c["privacy"]
    secs = "\n".join(f"    <h2>{x['h2']}</h2>\n    {x['body']}" for x in p["sections"])
    return f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{p["title"]}</title>
<meta name="description" content="{p["metaDesc"]}">
<style>
{PRIVACY_CSS}{LANGBAR_CSS}
</style>
</head>
<body>
<header>
  <h1>{p["headerTitle"]}</h1>
  <p>{p["headerSub"]}</p>
</header>
{bar}

<main>
  <a class="back" href="index.html">{p["back"]}</a>
  <div class="card">
{secs}
  </div>
</main>

<footer>
  {p["footer"]}
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
    LOCALES = present  # langbar only links to locales we actually have
    for loc in present:
        lang = LANG_ATTR[loc]
        outdir = REPO if loc == "en" else os.path.join(REPO, loc)
        os.makedirs(outdir, exist_ok=True)
        open(os.path.join(outdir, "index.html"), "w").write(
            support_html(content[loc], lang, langbar(loc, "index.html", names)))
        open(os.path.join(outdir, "privacy.html"), "w").write(
            privacy_html(content[loc], lang, langbar(loc, "privacy.html", names)))
        print(f"  {loc}: index.html + privacy.html")
    print(f"Generated {len(LOCALES)} locales.")


if __name__ == "__main__":
    main()
