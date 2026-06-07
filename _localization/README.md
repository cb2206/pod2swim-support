# Localization

The support (`index.html`) and privacy (`privacy.html`) pages are **generated**,
not edited by hand. English lives at the repo root; each other language lives in
its own folder (`de/`, `es/`, `fr/`, `it/`, `ja/`, `pt-br/`, `zh-hans/`).

## To change wording

1. Edit the relevant `translations/<code>.json` (text + small HTML snippets).
2. Regenerate from the repo root:

   ```bash
   python3 _localization/gen_pages.py
   ```

3. Commit the changed `*.html` files.

## To add a language

Add `translations/<code>.json` (copy `en.json`, translate the values, set
`languageName`), add the code to `LOCALES` / `LANG_ATTR` in `gen_pages.py`, and
regenerate. The language switcher updates automatically.
