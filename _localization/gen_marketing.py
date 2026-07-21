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
# The app repo is a two-app monorepo; the iOS App Store metadata lives under ios/.
META = os.path.join(APP_REPO, "ios", "fastlane", "metadata")

# Live App Store listing (Pod2Swim, app id 6766092966). The id-only URL
# redirects to each visitor's local storefront. The Android build is submitted
# to Google Play but not yet live, so its tile shows a "coming soon" placeholder.
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
    "en": {"badge": "Download on the", "comingSoon": "Coming soon",
           "light": "Light", "dark": "Dark",
           "shotsH": "A look inside", "support": "Support", "privacy": "Privacy Policy",
           "compatH": "Compatibility", "metaDesc": "Pod2Swim loads your favourite podcasts onto a Shokz OpenSwim or any USB-storage swim headset, so you can listen underwater — no Bluetooth, no phone at the poolside."},
    "de": {"badge": "Laden im", "comingSoon": "Bald verfügbar",
           "light": "Hell", "dark": "Dunkel",
           "shotsH": "Ein Blick in die App", "support": "Support", "privacy": "Datenschutz",
           "compatH": "Kompatibilität", "metaDesc": "Pod2Swim lädt deine Lieblingspodcasts auf einen Shokz OpenSwim oder jeden USB-Kopfhörer – zum Hören unter Wasser, ohne Bluetooth und ohne Handy am Beckenrand."},
    "es": {"badge": "Consíguelo en el", "comingSoon": "Muy pronto",
           "light": "Claro", "dark": "Oscuro",
           "shotsH": "Un vistazo a la app", "support": "Soporte", "privacy": "Privacidad",
           "compatH": "Compatibilidad", "metaDesc": "Pod2Swim carga tus pódcasts favoritos en un Shokz OpenSwim o cualquier auricular USB para escuchar bajo el agua, sin Bluetooth ni móvil en el borde."},
    "fr": {"badge": "Télécharger dans l'", "comingSoon": "Bientôt disponible",
           "light": "Clair", "dark": "Sombre",
           "shotsH": "Un aperçu de l'app", "support": "Assistance", "privacy": "Confidentialité",
           "compatH": "Compatibilité", "metaDesc": "Pod2Swim charge tes podcasts préférés sur un Shokz OpenSwim ou tout casque USB pour écouter sous l'eau, sans Bluetooth ni téléphone au bord du bassin."},
    "it": {"badge": "Scaricala su", "comingSoon": "In arrivo",
           "light": "Chiaro", "dark": "Scuro",
           "shotsH": "Uno sguardo all'app", "support": "Supporto", "privacy": "Privacy",
           "compatH": "Compatibilità", "metaDesc": "Pod2Swim carica i tuoi podcast preferiti su Shokz OpenSwim o qualsiasi cuffia USB per ascoltarli sott'acqua, senza Bluetooth e senza telefono a bordo piscina."},
    "ja": {"badge": "ダウンロード", "comingSoon": "近日公開",
           "light": "ライト", "dark": "ダーク",
           "shotsH": "アプリの中身をチラ見せ", "support": "サポート", "privacy": "プライバシー",
           "compatH": "対応機器", "metaDesc": "Pod2Swimは、お気に入りのポッドキャストをShokz OpenSwimなどのUSBヘッドセットに転送。Bluetoothもプールサイドのスマホもなしで、水中で楽しめます。"},
    "pt-br": {"badge": "Baixar na", "comingSoon": "Em breve",
              "light": "Claro", "dark": "Escuro",
              "shotsH": "Um olhar pelo app", "support": "Suporte", "privacy": "Privacidade",
              "compatH": "Compatibilidade", "metaDesc": "O Pod2Swim carrega os seus podcasts favoritos num Shokz OpenSwim ou em qualquer fone USB para ouvir embaixo d'água, sem Bluetooth e sem celular na borda."},
    "zh-hans": {"badge": "前往下载", "comingSoon": "即将推出",
                "light": "浅色", "dark": "深色",
                "shotsH": "先睹为快", "support": "支持", "privacy": "隐私政策",
                "compatH": "兼容设备", "metaDesc": "Pod2Swim 把你喜欢的播客导入 Shokz OpenSwim 等 USB 耳机，水下也能畅听——无需蓝牙，手机留在岸边。"},
}

# Screenshot gallery. Localized sets of the same 7 screens, one per
# (language × platform × appearance), stored at
# assets/shots/<lang>/<platform>/<mode>/NN.webp. The page has a platform tab
# (iOS / Android) and a light/dark toggle; the language picker swaps the set too.
# Rebuild the assets with screenshots/… via the build_shots helper.
SHOT_NAMES = ["01", "02", "03", "04", "05", "06", "07"]


# ---------------------------------------------------------------------------
# Changelog. Rendered on the landing page and maintained going forward: for
# each App Store release, PREPEND one entry (newest first) with the version, an
# ISO release date (formatted per-locale in the browser), and 3-5 short bullets
# per locale. Keep it concise — the full notes live in the App Store "What's
# New" (ios/fastlane/metadata/<locale>/release_notes.txt).
# An entry may instead carry `"date": None` plus a per-locale `status` dict; the
# status string then renders in place of the date (used for a not-yet-live
# release, e.g. "Coming soon"). Swap it back to a `date` once the stores approve.
# ---------------------------------------------------------------------------
CHANGELOG_H = {
    "en": "What's new", "de": "Neuigkeiten", "es": "Novedades",
    "fr": "Nouveautés", "it": "Novità", "ja": "新着情報",
    "pt-br": "Novidades", "zh-hans": "更新内容",
}

CHANGELOG = [
    {
        "version": "1.3",
        # No release date yet — 1.3 is submitted but not live. A per-locale
        # `status` string shows in place of the date until the stores approve it;
        # swap `status` for a `"date": "YYYY-MM-DD"` once both releases are live.
        "date": None,
        "status": {
            "en": "Coming soon for Android and iOS",
            "de": "Bald für Android und iOS",
            "es": "Muy pronto para Android y iOS",
            "fr": "Bientôt sur Android et iOS",
            "it": "Presto su Android e iOS",
            "ja": "AndroidとiOSで近日公開",
            "pt-br": "Em breve para Android e iOS",
            "zh-hans": "Android 和 iOS 即将推出",
        },
        "entries": {
            "en": [
                "Pod2Swim is now free to download — try everything for 7 days.",
                "After the trial, one single purchase unlocks the app forever — no subscription.",
                "Already bought Pod2Swim when it was a paid app? You stay unlocked automatically, at no extra cost.",
                "iOS: bug fixes and polish, including a more reliable paywall and smoother headset-transfer progress.",
                "First Android release — the same Pod2Swim, now on Google Play.",
            ],
            "de": [
                "Pod2Swim ist jetzt gratis – teste 7 Tage lang alle Funktionen.",
                "Danach schaltet ein einmaliger Kauf die App für immer frei – kein Abo.",
                "Schon als Bezahl-App gekauft? Du bleibst automatisch freigeschaltet – ohne Aufpreis.",
                "iOS: Fehlerbehebungen und Feinschliff, u. a. eine zuverlässigere Kaufseite und flüssigere Übertragungsanzeige.",
                "Erste Android-Version – das gleiche Pod2Swim, jetzt bei Google Play.",
            ],
            "es": [
                "Pod2Swim ahora es gratis: pruébalo todo durante 7 días.",
                "Tras la prueba, una única compra desbloquea la app para siempre, sin suscripción.",
                "¿La compraste cuando era de pago? Sigues desbloqueado automáticamente, sin coste adicional.",
                "iOS: correcciones de errores y mejoras, con una pantalla de compra más fiable y una barra de transferencia más suave.",
                "Primera versión para Android: el mismo Pod2Swim, ahora en Google Play.",
            ],
            "fr": [
                "Pod2Swim est désormais gratuit — essaie tout pendant 7 jours.",
                "Après l'essai, un seul achat débloque l'app pour toujours, sans abonnement.",
                "Tu l'avais achetée quand elle était payante ? Tu restes débloqué automatiquement, sans frais.",
                "iOS : corrections de bugs et finitions, dont un écran d'achat plus fiable et une progression de transfert plus fluide.",
                "Première version Android — le même Pod2Swim, désormais sur Google Play.",
            ],
            "it": [
                "Pod2Swim ora è gratis: prova tutto per 7 giorni.",
                "Dopo la prova, un unico acquisto sblocca l'app per sempre, senza abbonamento.",
                "L'avevi comprata quando era a pagamento? Resti sbloccato automaticamente, senza costi aggiuntivi.",
                "iOS: correzioni di bug e rifiniture, con una schermata d'acquisto più affidabile e una barra di trasferimento più fluida.",
                "Prima versione per Android: lo stesso Pod2Swim, ora su Google Play.",
            ],
            "ja": [
                "Pod2Swimが無料になりました。7日間すべての機能を試せます。",
                "トライアル終了後は、一度の買い切り購入でずっと利用できます。サブスクリプションはありません。",
                "有料アプリだった頃に購入した方は、追加料金なしで自動的にロック解除されたままです。",
                "iOS：不具合の修正と改善。購入画面の信頼性向上や、転送の進捗表示をよりスムーズに。",
                "Android版が初登場 — 同じPod2SwimがGoogle Playに。",
            ],
            "pt-br": [
                "O Pod2Swim agora é grátis — experimente tudo por 7 dias.",
                "Depois do teste, uma única compra desbloqueia o app para sempre, sem assinatura.",
                "Comprou quando era pago? Você continua desbloqueado automaticamente, sem custo extra.",
                "iOS: correções de bugs e melhorias, com uma tela de compra mais confiável e barra de transferência mais suave.",
                "Primeira versão para Android — o mesmo Pod2Swim, agora no Google Play.",
            ],
            "zh-hans": [
                "Pod2Swim 现在可以免费下载——7 天内体验全部功能。",
                "试用结束后，一次性购买即可永久解锁，无订阅。",
                "在付费时期购买过？应用会自动保持解锁，无需额外付费。",
                "iOS：修复问题并优化体验，包括更可靠的购买页面和更流畅的传输进度。",
                "首个 Android 版本——同样的 Pod2Swim，现已登陆 Google Play。",
            ],
        },
    },
    {
        "version": "1.2",
        "date": "2026-06-16",
        "entries": {
            "en": [
                "Global episode search — find any episode across all your podcasts from the Latest tab, with smarter title-match ranking.",
                "More reliable headset transfers — no more truncated or unplayable episodes.",
                "Speed changes now re-process queued episodes in place, and Retry keeps an episode's spot in the queue.",
                "Fixed a Latest-tab scroll freeze, hardened podcast feed and URL handling, and polished wording.",
            ],
            "de": [
                "Globale Folgensuche – finde jede Folge aus all deinen Podcasts direkt im Tab „Neueste“, mit besserer Sortierung nach Titeltreffern.",
                "Zuverlässigere Übertragung auf den Kopfhörer – keine abgeschnittenen oder unspielbaren Folgen mehr.",
                "Tempoänderungen verarbeiten eingereihte Folgen direkt neu, und „Erneut versuchen“ behält die Position in der Warteschlange bei.",
                "Einfrieren im Tab „Neueste“ behoben, robustere Feed- und URL-Verarbeitung und feinere Formulierungen.",
            ],
            "es": [
                "Búsqueda global de episodios: encuentra cualquier episodio de todos tus pódcasts desde la pestaña «Recientes», con mejor orden por coincidencia de título.",
                "Transferencias al auricular más fiables: se acabaron los episodios cortados o que no se reproducen.",
                "Los cambios de velocidad reprocesan en el sitio los episodios en cola, y Reintentar mantiene su posición en la cola.",
                "Corregido un bloqueo al desplazar la pestaña «Recientes», gestión de feeds y URL más robusta y textos pulidos.",
            ],
            "fr": [
                "Recherche globale d'épisodes — retrouve n'importe quel épisode de tous tes podcasts depuis l'onglet « Récents », avec un meilleur classement par titre.",
                "Transferts vers le casque plus fiables — fini les épisodes tronqués ou illisibles.",
                "Les changements de vitesse retraitent les épisodes en file sur place, et Réessayer conserve la place dans la file.",
                "Correction d'un blocage au défilement de l'onglet « Récents », gestion des flux et URL plus robuste, formulations peaufinées.",
            ],
            "it": [
                "Ricerca globale degli episodi — trova qualsiasi episodio fra tutti i tuoi podcast dalla scheda «Recenti», con un ordinamento migliore per titolo.",
                "Trasferimenti alle cuffie più affidabili — niente più episodi troncati o non riproducibili.",
                "I cambi di velocità rielaborano sul posto gli episodi in coda, e Riprova mantiene la posizione nella coda.",
                "Risolto un blocco nello scorrimento della scheda «Recenti», gestione di feed e URL più robusta, formulazioni rifinite.",
            ],
            "ja": [
                "全エピソード横断の検索 — 「最新」タブから、登録中のすべてのポッドキャストのエピソードを検索。タイトル一致の並び順も改善。",
                "ヘッドセットへの転送がより確実に — 途中で切れたり再生できないエピソードがなくなりました。",
                "速度変更でキュー内のエピソードをその場で再処理。「再試行」はキュー内の位置を保持します。",
                "「最新」タブのスクロール時の固まりを修正、フィードとURLの処理を強化、文言を調整。",
            ],
            "pt-br": [
                "Busca global de episódios — encontre qualquer episódio entre todos os seus podcasts na aba “Recentes”, com melhor ordenação por título.",
                "Transferências para o fone mais confiáveis — sem mais episódios cortados ou que não tocam.",
                "Mudanças de velocidade reprocessam no lugar os episódios na fila, e Tentar de novo mantém a posição na fila.",
                "Corrigido um congelamento ao rolar a aba “Recentes”, tratamento de feeds e URLs mais robusto e textos refinados.",
            ],
            "zh-hans": [
                "全局单集搜索——在“最新”标签页中查找你订阅的所有播客的任意单集，并优化了标题匹配排序。",
                "更可靠的耳机传输——不再出现被截断或无法播放的单集。",
                "更改倍速会就地重新处理队列中的单集，“重试”会保留其在队列中的位置。",
                "修复「最新」标签页滚动卡顿，增强信息流与 URL 处理，并润色文案。",
            ],
        },
    },
]


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
        "comingSoon": c["comingSoon"],
        "light": c["light"],
        "dark": c["dark"],
        "shotsH": c["shotsH"],
        "support": c["support"],
        "privacy": c["privacy"],
        "metaDesc": c["metaDesc"],
        "changelogH": CHANGELOG_H[code],
        "changelog": [{"version": e["version"], "date": e["date"],
                       "status": e.get("status", {}).get(code),
                       "entries": e["entries"][code]} for e in CHANGELOG],
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

  /* store download badges */
  .badgewrap { display: inline-flex; flex-wrap: wrap; align-items: center;
    justify-content: center; gap: 12px; }
  .storebadge {
    display: inline-flex; align-items: center; gap: 11px;
    background: #0c0c0c; color: #fff; border-radius: 11px;
    padding: 10px 18px; text-decoration: none;
    border: 1px solid rgba(255,255,255,0.25); user-select: none;
    transition: transform .12s ease, box-shadow .12s ease;
  }
  a.storebadge:hover {
    text-decoration: none; transform: translateY(-1px);
    box-shadow: 0 12px 28px rgba(8,40,80,0.4);
  }
  a.storebadge:active { transform: translateY(0); }
  .storebadge svg { width: 26px; height: 26px; }
  .appstore svg { fill: #fff; }
  .storebadge .small { font-size: 11px; line-height: 1; opacity: 0.85; }
  .storebadge .big { font-size: 19px; font-weight: 600; line-height: 1.15; letter-spacing: -0.2px; }
  /* Google Play — not live yet, so the tile is a dimmed, non-interactive placeholder */
  .playstore { position: relative; cursor: default; opacity: 0.55; }
  .playstore .small { text-transform: uppercase; letter-spacing: 0.4px; }

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
    letter-spacing: -0.4px; margin: 0 0 18px; color: var(--ink); }
  .gallery-controls {
    display: flex; flex-wrap: wrap; justify-content: center; gap: 12px;
    margin: 0 0 22px;
  }
  .seg {
    display: inline-flex; background: rgba(31,122,224,0.08);
    border: 1px solid var(--line); border-radius: 999px; padding: 3px;
  }
  .seg-btn {
    appearance: none; border: 0; background: transparent; cursor: pointer;
    font: inherit; font-size: 14px; font-weight: 600; color: var(--blue-dark);
    padding: 7px 16px; border-radius: 999px; display: inline-flex;
    align-items: center; gap: 6px;
    transition: background .15s ease, color .15s ease;
  }
  .seg-btn.is-active { background: var(--blue); color: #fff;
    box-shadow: 0 2px 8px rgba(31,122,224,0.35); }
  .seg-ico { font-size: 13px; line-height: 1; }
  .gallery {
    display: flex; gap: 18px; overflow-x: auto; padding: 8px 4px 22px;
    scroll-snap-type: x mandatory; -webkit-overflow-scrolling: touch;
  }
  .gallery img {
    width: 232px; flex: 0 0 auto; border-radius: 22px;
    border: 1px solid var(--line); scroll-snap-align: center;
    box-shadow: 0 14px 36px rgba(15,76,145,0.16); background: #fff;
  }

  /* changelog */
  .changelog { margin: 56px 0 8px; }
  .changelog h2 { text-align: center; font-size: 24px; font-weight: 800;
    letter-spacing: -0.4px; margin: 0 0 26px; color: var(--ink); }
  .release {
    background: var(--card); border: 1px solid var(--line); border-radius: 18px;
    padding: 22px 24px 8px; margin: 0 auto 18px; max-width: 680px;
    box-shadow: 0 1px 3px rgba(15,76,145,0.05);
  }
  .release-head {
    display: flex; align-items: baseline; justify-content: space-between;
    gap: 12px; flex-wrap: wrap; margin: 0 0 14px;
  }
  .release-head .ver { font-size: 17px; font-weight: 800; letter-spacing: -0.2px;
    color: var(--blue-dark); }
  .release-head .date { font-size: 13px; font-weight: 600; color: var(--muted); }
  .release ul { list-style: none; margin: 0; padding: 0; }
  .release li {
    position: relative; padding: 0 0 16px 26px; font-size: 15px; color: #2a3a48;
  }
  .release li::before {
    content: ""; position: absolute; left: 2px; top: 7px;
    width: 9px; height: 9px; border-radius: 50%;
    background: var(--blue); box-shadow: 0 0 0 4px rgba(31,122,224,0.14);
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
    <a class="navlink" id="nav-changelog" href="#changelog">What's new</a>
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
    <a class="storebadge appstore" id="appstore-link" href="__APPSTORE__" target="_blank" rel="noopener" aria-label="Download Pod2Swim on the App Store">
      <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M16.36 12.78c-.02-2.3 1.88-3.4 1.96-3.46-1.07-1.56-2.73-1.78-3.32-1.8-1.41-.14-2.76.83-3.48.83-.72 0-1.82-.81-3-.79-1.54.02-2.96.9-3.75 2.28-1.6 2.78-.41 6.89 1.15 9.14.76 1.1 1.67 2.34 2.86 2.29 1.15-.05 1.58-.74 2.97-.74 1.38 0 1.77.74 2.98.72 1.23-.02 2.01-1.12 2.76-2.23.87-1.28 1.23-2.52 1.25-2.58-.03-.01-2.4-.92-2.42-3.65zM14.13 6.04c.64-.78 1.07-1.85.95-2.92-.92.04-2.03.61-2.69 1.38-.59.68-1.11 1.78-.97 2.83 1.03.08 2.07-.52 2.71-1.29z"/></svg>
      <span><span class="small" id="b-small">Download on the</span><br><span class="big">App Store</span></span>
    </a>
    <span class="storebadge playstore" id="playstore-badge" aria-disabled="true" role="img">
      <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3.6 2.4c-.24.25-.38.63-.38 1.13v16.94c0 .5.14.88.39 1.13l.06.05L13.1 12.1v-.22L3.67 2.35l-.07.05z" fill="#00d0ff"/><path d="M16.24 15.24 13.1 12.1v-.22l3.14-3.14.07.04 3.72 2.12c1.06.6 1.06 1.59 0 2.2l-3.72 2.11-.07.03z" fill="#ffc107"/><path d="m16.31 15.2-3.21-3.21-9.28 9.28c.35.37.93.42 1.58.05l10.91-6.12z" fill="#ff3d47"/><path d="M16.31 8.8 5.4 2.68c-.65-.37-1.23-.32-1.58.05l9.28 9.27L16.31 8.8z" fill="#00e676"/></svg>
      <span><span class="small" id="ps-small">Coming soon</span><br><span class="big">Google Play</span></span>
    </span>
  </div>
</header>

<main>
  <p class="pitch" id="m-pitch"></p>

  <div class="features" id="m-features"></div>

  <section class="shots">
    <h2 id="m-shotsH"></h2>
    <div class="gallery-controls">
      <div class="seg" id="platform-seg" role="tablist" aria-label="Platform">
        <button type="button" class="seg-btn is-active" data-platform="ios" role="tab" aria-selected="true">iOS</button>
        <button type="button" class="seg-btn" data-platform="android" role="tab" aria-selected="false">Android</button>
      </div>
      <div class="seg" id="mode-seg" role="group" aria-label="Appearance">
        <button type="button" class="seg-btn is-active" data-mode="light" aria-pressed="true"><span class="seg-ico" aria-hidden="true">☀</span><span id="lbl-light">Light</span></button>
        <button type="button" class="seg-btn" data-mode="dark" aria-pressed="false"><span class="seg-ico" aria-hidden="true">☾</span><span id="lbl-dark">Dark</span></button>
      </div>
    </div>
    <div class="gallery" id="m-gallery"></div>
  </section>

  <section class="changelog" id="changelog">
    <h2 id="m-changelogH"></h2>
    <div id="m-changelog"></div>
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
const SHOT_NAMES = __SHOT_NAMES__;
const I18N = __I18N__;
const ORDER = __ORDER__;
const LANG_ATTR = __LANG_ATTR__;
// gallery state: current language + platform tab + appearance. renderGallery()
// swaps the image set live for the current (lang, platform, mode) triple. The
// screenshots are localized: assets/shots/<lang>/<platform>/<mode>/NN.webp.
let galLang = "en";
let galPlatform = "ios";
let galMode = "light";
let galText = null;
function platformLabel(p){ return p === "android" ? "Android" : "iOS"; }
function renderGallery(){
  if (!galText) return;
  const g = document.getElementById("m-gallery");
  g.innerHTML = "";
  const plabel = platformLabel(galPlatform);
  const base = "assets/shots/" + galLang + "/" + galPlatform + "/" + galMode + "/";
  SHOT_NAMES.forEach((n, i) => {
    const img = document.createElement("img");
    img.src = base + n + ".webp";
    // lazy: only the shots scrolled into view load, so switching language /
    // platform / appearance fetches just the newly-shown set, on demand.
    img.loading = "lazy";
    img.decoding = "async";
    img.alt = galText.name + " on " + plabel + " — screenshot " + (i+1);
    g.appendChild(img);
  });
}
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
  document.getElementById("ps-small").textContent = t.comingSoon;
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

  document.getElementById("m-changelogH").textContent = t.changelogH;
  const cl = document.getElementById("m-changelog");
  cl.innerHTML = "";
  let dfmt;
  try { dfmt = new Intl.DateTimeFormat(LANG_ATTR[code] || code, {year:"numeric", month:"long", day:"numeric"}); }
  catch(e){ dfmt = null; }
  for (const v of t.changelog){
    const rel = el("div", "release");
    const head = el("div", "release-head");
    const ver = el("span", "ver"); ver.textContent = t.name + " " + v.version;
    const date = el("span", "date");
    let dstr;
    if (v.status){ dstr = v.status; }               // not-yet-live: show a status label
    else { dstr = v.date;
      if (dfmt){ try { dstr = dfmt.format(new Date(v.date + "T00:00:00")); } catch(e){} } }
    date.textContent = dstr;
    head.appendChild(ver); head.appendChild(date);
    rel.appendChild(head);
    const ul = el("ul");
    for (const item of v.entries){ const li = el("li"); li.textContent = item; ul.appendChild(li); }
    rel.appendChild(ul);
    cl.appendChild(rel);
  }

  document.getElementById("lbl-light").textContent = t.light;
  document.getElementById("lbl-dark").textContent = t.dark;
  galLang = code;
  galText = t;
  renderGallery();

  const sup = document.getElementById("f-support");
  sup.textContent = t.support; sup.href = supportPath(code);
  const pri = document.getElementById("f-privacy");
  pri.textContent = t.privacy; pri.href = privacyPath(code);
  const navSup = document.getElementById("nav-support");
  navSup.textContent = t.support; navSup.href = supportPath(code);
  document.getElementById("nav-changelog").textContent = t.changelogH;

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
  // gallery platform tabs (iOS / Android) + light/dark toggle
  document.querySelectorAll("#platform-seg .seg-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      galPlatform = btn.dataset.platform;
      document.querySelectorAll("#platform-seg .seg-btn").forEach(b => {
        const on = b === btn;
        b.classList.toggle("is-active", on);
        b.setAttribute("aria-selected", on ? "true" : "false");
      });
      renderGallery();
    });
  });
  document.querySelectorAll("#mode-seg .seg-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      galMode = btn.dataset.mode;
      document.querySelectorAll("#mode-seg .seg-btn").forEach(b => {
        const on = b === btn;
        b.classList.toggle("is-active", on);
        b.setAttribute("aria-pressed", on ? "true" : "false");
      });
      renderGallery();
    });
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
            .replace("__SHOT_NAMES__", json.dumps(SHOT_NAMES))
            .replace("__I18N__", json.dumps(data, ensure_ascii=False))
            .replace("__ORDER__", json.dumps(ORDER))
            .replace("__LANG_ATTR__", json.dumps(LANG_ATTR)))
    with open(os.path.join(REPO, "index.html"), "w", encoding="utf-8") as f:
        f.write(page)
    print("Wrote index.html (%d locales) + _localization/marketing/*.json" % len(ORDER))


if __name__ == "__main__":
    main()
