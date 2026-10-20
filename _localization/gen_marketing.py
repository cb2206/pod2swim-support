#!/usr/bin/env python3
"""Generate the Pod2Swim marketing landing page (repo root index.html).

Source of truth: the App Store metadata in the Pod2Swim app repo
(ios/fastlane/metadata/<locale>/{description,subtitle,promotional_text,name}.txt).
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

# Live store listings. The App Store id-only URL redirects to each visitor's
# local storefront; Google Play localizes by account/browser language itself.
APP_STORE_URL = "https://apps.apple.com/app/id6766092966"
PLAY_STORE_URL = "https://play.google.com/store/apps/details?id=com.pod2swim"

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
    "en": {"badge": "Download on the", "playBadge": "Get it on",
           "light": "Light", "dark": "Dark",
           "shotsH": "A look inside", "support": "Support", "privacy": "Privacy Policy",
           "compatH": "Compatibility", "metaDesc": "Pod2Swim loads your favourite podcasts onto a Shokz OpenSwim or any USB-storage swim headset, so you can listen underwater — no Bluetooth, no phone at the poolside."},
    "de": {"badge": "Laden im", "playBadge": "Jetzt bei",
           "light": "Hell", "dark": "Dunkel",
           "shotsH": "Ein Blick in die App", "support": "Support", "privacy": "Datenschutz",
           "compatH": "Kompatibilität", "metaDesc": "Pod2Swim lädt deine Lieblingspodcasts auf einen Shokz OpenSwim oder jeden USB-Kopfhörer – zum Hören unter Wasser, ohne Bluetooth und ohne Handy am Beckenrand."},
    "es": {"badge": "Consíguelo en el", "playBadge": "Disponible en",
           "light": "Claro", "dark": "Oscuro",
           "shotsH": "Un vistazo a la app", "support": "Soporte", "privacy": "Privacidad",
           "compatH": "Compatibilidad", "metaDesc": "Pod2Swim carga tus pódcasts favoritos en un Shokz OpenSwim o cualquier auricular USB para escuchar bajo el agua, sin Bluetooth ni móvil en el borde."},
    "fr": {"badge": "Télécharger dans l'", "playBadge": "Disponible sur",
           "light": "Clair", "dark": "Sombre",
           "shotsH": "Un aperçu de l'app", "support": "Assistance", "privacy": "Confidentialité",
           "compatH": "Compatibilité", "metaDesc": "Pod2Swim charge tes podcasts préférés sur un Shokz OpenSwim ou tout casque USB pour écouter sous l'eau, sans Bluetooth ni téléphone au bord du bassin."},
    "it": {"badge": "Scaricala su", "playBadge": "Disponibile su",
           "light": "Chiaro", "dark": "Scuro",
           "shotsH": "Uno sguardo all'app", "support": "Supporto", "privacy": "Privacy",
           "compatH": "Compatibilità", "metaDesc": "Pod2Swim carica i tuoi podcast preferiti su Shokz OpenSwim o qualsiasi cuffia USB per ascoltarli sott'acqua, senza Bluetooth e senza telefono a bordo piscina."},
    "ja": {"badge": "ダウンロード", "playBadge": "アプリを入手",
           "light": "ライト", "dark": "ダーク",
           "shotsH": "アプリの中身をチラ見せ", "support": "サポート", "privacy": "プライバシー",
           "compatH": "対応機器", "metaDesc": "Pod2Swimは、お気に入りのポッドキャストをShokz OpenSwimなどのUSBヘッドセットに転送。Bluetoothもプールサイドのスマホもなしで、水中で楽しめます。"},
    "pt-br": {"badge": "Baixar na", "playBadge": "Disponível no",
              "light": "Claro", "dark": "Escuro",
              "shotsH": "Um olhar pelo app", "support": "Suporte", "privacy": "Privacidade",
              "compatH": "Compatibilidade", "metaDesc": "O Pod2Swim carrega os seus podcasts favoritos num Shokz OpenSwim ou em qualquer fone USB para ouvir embaixo d'água, sem Bluetooth e sem celular na borda."},
    "zh-hans": {"badge": "前往下载", "playBadge": "前往下载",
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
        "version": "1.4.1",
        # iOS only — submitted 2026-10-19, in App Store review. Swap the status
        # for "date": "<release day>" once it is live. (No Android release.)
        "date": None,
        "status": {
            "en": "Coming soon", "de": "Demnächst", "es": "Muy pronto",
            "fr": "Bientôt disponible", "it": "In arrivo", "ja": "近日公開",
            "pt-br": "Em breve", "zh-hans": "即将推出",
        },
        "entries": {
            "en": [
                "iOS: made for iPhone Duo. Unfolded, Latest and your queue sit side by side, so a tapped + lands in the queue right before your eyes.",
                "On iPhone Duo, Library shows your podcasts next to their episodes, and Queue shows what's already on your headset. The layout follows the fold.",
                "After a transfer, the headset list updates on its own.",
                "Fixes: the trial reminder no longer covers screen titles, and layouts work better with very large text.",
            ],
            "de": [
                "iOS: gemacht für das iPhone Duo. Aufgeklappt stehen „Neueste“ und deine Warteschlange nebeneinander – ein Tipp auf + landet direkt sichtbar in der Warteschlange.",
                "Auf dem iPhone Duo zeigt die Mediathek deine Podcasts neben ihren Folgen, und die Warteschlange zeigt, was schon auf deinem Kopfhörer ist. Die Ansicht folgt dem Falz.",
                "Nach einer Übertragung aktualisiert sich die Kopfhörer-Liste von selbst.",
                "Fehlerbehebungen: Der Hinweis zum Testzeitraum verdeckt keine Überschriften mehr, und bei sehr großer Schrift passt die Darstellung besser.",
            ],
            "es": [
                "iOS: diseñada para el iPhone Duo. Desplegado, Recientes y tu cola aparecen lado a lado, así ves al instante cómo llega a la cola cada episodio que añades con +.",
                "En el iPhone Duo, Biblioteca muestra tus podcasts junto a sus episodios, y Cola muestra lo que ya tienes en tus auriculares. La vista se adapta al pliegue.",
                "Tras una transferencia, la lista de los auriculares se actualiza sola.",
                "Correcciones: el aviso de la prueba ya no tapa los títulos y el diseño funciona mejor con textos muy grandes.",
            ],
            "fr": [
                "iOS : conçue pour l'iPhone Duo. Déplié, Récents et ta file d'attente s'affichent côte à côte : chaque épisode ajouté avec + arrive sous tes yeux dans la file.",
                "Sur iPhone Duo, Bibliothèque affiche tes podcasts à côté de leurs épisodes, et File d'attente montre ce qui est déjà sur ton casque. L'affichage suit le pli.",
                "Après un transfert, la liste du casque se met à jour toute seule.",
                "Corrections : le rappel de l'essai ne masque plus les titres, et la mise en page fonctionne mieux avec les très grandes tailles de texte.",
            ],
            "it": [
                "iOS: pensata per iPhone Duo. Da aperto, Recenti e la tua coda stanno fianco a fianco: ogni episodio aggiunto con + compare subito nella coda.",
                "Su iPhone Duo, Libreria mostra i tuoi podcast accanto ai loro episodi, e Coda mostra cosa c'è già sulle tue cuffie. La vista segue la piega.",
                "Dopo un trasferimento, l'elenco delle cuffie si aggiorna da solo.",
                "Correzioni: il promemoria della prova non copre più i titoli e il layout funziona meglio con testo molto grande.",
            ],
            "ja": [
                "iOS：iPhone Duoに対応。開いた状態では「最新」とキューが横に並び、+ をタップしたエピソードがキューに追加される様子がすぐに見えます。",
                "iPhone Duoでは、「ライブラリ」にポッドキャストとそのエピソードを並べて表示し、「キュー」ではヘッドセットに入っている内容も並べて表示します。画面は折り目に合わせて分かれます。",
                "転送が終わると、ヘッドセットの一覧が自動で更新されます。",
                "修正：無料体験のお知らせが画面のタイトルに重ならなくなり、文字サイズを大きくしたときのレイアウトも改善しました。",
            ],
            "pt-br": [
                "iOS: feito para o iPhone Duo. Aberto, Recentes e sua fila ficam lado a lado, e cada episódio adicionado com + aparece na hora na fila.",
                "No iPhone Duo, Biblioteca mostra seus podcasts ao lado dos episódios, e Fila mostra o que já está nos seus fones. O layout acompanha a dobra.",
                "Depois de uma transferência, a lista dos fones se atualiza sozinha.",
                "Correções: o aviso do período de teste não cobre mais os títulos, e o layout funciona melhor com textos muito grandes.",
            ],
            "zh-hans": [
                "iOS：为 iPhone Duo 打造。展开时，“最新”和播放队列并排显示，轻点 + 添加的单集会立即出现在队列中。",
                "在 iPhone Duo 上，“媒体库”将播客与其单集并排显示，“播放队列”旁边会显示耳机中已有的内容。布局随折叠变化。",
                "传输完成后，耳机列表会自动更新。",
                "修复：试用提醒不再遮挡页面标题，超大字号下的布局也更加合理。",
            ],
        },
    },
    {
        "version": "1.4",
        # iOS 1.4 went live on the App Store 2026-09-17; the Android 1.4 draft
        # was uploaded the same day and is rolled out from Play Console.
        "date": "2026-09-17",
        "entries": {
            "en": [
                "Add private and paid podcasts by their feed link — ideal for members-only feeds. Feeds that need a login ask for one; it's stored securely on your device.",
                "More reliable downloads, processing and headset transfers, and no more duplicate episodes.",
                "iOS: auto-delete now cleans up exported episodes on schedule, the app follows your text size and works better with VoiceOver, and Settings and Search no longer crash on a Mac.",
                "Android: unsubscribing asks first and removes all of the podcast's files, and notification permission is only requested when it's needed.",
            ],
            "de": [
                "Private und kostenpflichtige Podcasts per Feed-Link hinzufügen – ideal für Mitglieder-Feeds. Verlangt ein Feed eine Anmeldung, fragt die App danach; die Zugangsdaten bleiben sicher auf deinem Gerät.",
                "Zuverlässigere Downloads, Verarbeitung und Übertragung auf den Kopfhörer – und keine doppelten Folgen mehr.",
                "iOS: Das automatische Löschen räumt exportierte Folgen jetzt wie eingestellt auf, die App folgt deiner Textgröße und funktioniert besser mit VoiceOver, und auf dem Mac stürzen Einstellungen und Suche nicht mehr ab.",
                "Android: „Abo beenden“ fragt erst nach und löscht alle Dateien des Podcasts; die Erlaubnis für Benachrichtigungen wird erst bei Bedarf angefragt.",
            ],
            "es": [
                "Añade podcasts privados y de pago con el enlace de su feed, ideal para feeds exclusivos para miembros. Si un feed pide iniciar sesión, la app te lo pedirá; tus datos se guardan de forma segura en tu dispositivo.",
                "Descargas, procesamiento y transferencias a los auriculares más fiables, y sin episodios duplicados.",
                "iOS: el borrado automático ya elimina los episodios exportados según lo previsto, la app respeta tu tamaño de texto y funciona mejor con VoiceOver, y Ajustes y Buscar ya no se cierran en un Mac.",
                "Android: cancelar una suscripción pide confirmación y borra todos los archivos del podcast, y el permiso de notificaciones solo se pide cuando hace falta.",
            ],
            "fr": [
                "Ajoute des podcasts privés et payants grâce au lien de leur flux — idéal pour les flux réservés aux membres. Si un flux demande une connexion, l'app te la demande ; tes identifiants restent en sécurité sur ton appareil.",
                "Téléchargements, traitement et transferts vers le casque plus fiables, et plus d'épisodes en double.",
                "iOS : la suppression automatique efface désormais les épisodes exportés comme prévu, l'app suit ta taille de texte et fonctionne mieux avec VoiceOver, et les Réglages et la Recherche ne plantent plus sur Mac.",
                "Android : la désinscription demande confirmation et supprime tous les fichiers du podcast, et l'autorisation des notifications n'est demandée qu'au besoin.",
            ],
            "it": [
                "Aggiungi podcast privati e a pagamento tramite il link del feed, ideale per i feed riservati agli abbonati. Se un feed richiede l'accesso, l'app ti chiede le credenziali, che restano al sicuro sul tuo dispositivo.",
                "Download, elaborazione e trasferimenti sulle cuffie più affidabili, e niente più episodi doppi.",
                "iOS: l'eliminazione automatica ora rimuove gli episodi esportati come previsto, l'app segue la dimensione del testo e funziona meglio con VoiceOver, e Impostazioni e Cerca non vanno più in crash su Mac.",
                "Android: l'annullamento dell'iscrizione chiede conferma ed elimina tutti i file del podcast, e il permesso per le notifiche viene chiesto solo quando serve.",
            ],
            "ja": [
                "フィードのリンクから非公開・有料のポッドキャストを追加できるようになりました。会員限定のフィードに最適です。ログインが必要な場合は入力を求められ、ログイン情報はデバイス内に安全に保存されます。",
                "ダウンロード、変換処理、ヘッドセットへの転送の信頼性が向上し、エピソードの重複もなくなりました。",
                "iOS：自動削除で書き出し済みのエピソードが設定どおりに削除されるようになりました。文字サイズの設定に対応し、VoiceOverでも使いやすくなったほか、Macで「設定」と「検索」が終了する問題を修正しました。",
                "Android：登録解除の前に確認し、そのポッドキャストのファイルをすべて削除します。通知の許可は、必要になった時点で求めるようになりました。",
            ],
            "pt-br": [
                "Adicione podcasts privados e pagos pelo link do feed — ideal para feeds exclusivos para membros. Se um feed pedir login, o app vai solicitá-lo; seus dados ficam guardados com segurança no seu dispositivo.",
                "Downloads, processamento e transferências para os fones mais confiáveis, e chega de episódios duplicados.",
                "iOS: a exclusão automática agora apaga os episódios exportados como previsto, o app segue o tamanho de texto que você definiu e funciona melhor com o VoiceOver, e Ajustes e Buscar não travam mais no Mac.",
                "Android: cancelar uma assinatura pede confirmação e remove todos os arquivos do podcast, e a permissão de notificações só é pedida quando necessária.",
            ],
            "zh-hans": [
                "现在可以通过订阅源链接添加私密和付费播客——非常适合会员专属订阅源。需要登录的订阅源会提示你输入，登录信息安全地保存在你的设备上。",
                "下载、处理和传输到耳机更加可靠，也不再出现重复单集。",
                "iOS：自动删除现在会按设定删除已导出的单集；应用会遵循你的文字大小设置并更好地支持 VoiceOver；在 Mac 上“设置”和“搜索”不再崩溃。",
                "Android：取消订阅前会先确认，并删除该播客的所有文件；通知权限仅在需要时才会请求。",
            ],
        },
    },
    {
        "version": "1.3",
        # Live on both stores: iOS 1.3 shipped 2026-07-23, the first Android
        # release went public 2026-07-28. One combined entry, dated when 1.3
        # became available on both platforms.
        "date": "2026-07-28",
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


# The compatibility line is parsed from the *iOS* App Store description, so it
# only ever talks about iPhone + the Files app. Now that the Android app is live,
# append a per-locale Android sentence on the website only (same append-on-site
# pattern as DISCLOSURE above). minSdk 26 = Android 8.0; iOS min is 17.0.
ANDROID_COMPAT = {
    "en": "On Android, Pod2Swim talks to the headset directly over USB — connect it with a USB-C cable or an OTG adapter. Pod2Swim needs iOS 17 or later, or Android 8.0 or later.",
    "de": "Unter Android spricht Pod2Swim den Kopfhörer direkt über USB an – verbinde ihn per USB-C-Kabel oder OTG-Adapter. Pod2Swim benötigt iOS 17 oder neuer bzw. Android 8.0 oder neuer.",
    "es": "En Android, Pod2Swim se comunica con el auricular directamente por USB: conéctalo con un cable USB-C o un adaptador OTG. Pod2Swim requiere iOS 17 o posterior, o Android 8.0 o posterior.",
    "fr": "Sur Android, Pod2Swim communique directement avec le casque via USB : branche-le avec un câble USB-C ou un adaptateur OTG. Pod2Swim nécessite iOS 17 ou version ultérieure, ou Android 8.0 ou version ultérieure.",
    "it": "Su Android, Pod2Swim comunica con le cuffie direttamente via USB: collegale con un cavo USB-C o un adattatore OTG. Pod2Swim richiede iOS 17 o successivo, oppure Android 8.0 o successivo.",
    "ja": "Androidでは、Pod2SwimはUSB経由でヘッドセットに直接接続します。USB-CケーブルまたはOTGアダプタでつないでください。Pod2SwimにはiOS 17以降、またはAndroid 8.0以降が必要です。",
    "pt-br": "No Android, o Pod2Swim fala com o fone direto por USB — conecte com um cabo USB-C ou um adaptador OTG. O Pod2Swim precisa de iOS 17 ou posterior, ou Android 8.0 ou posterior.",
    "zh-hans": "在 Android 上，Pod2Swim 通过 USB 直接连接耳机——用 USB-C 数据线或 OTG 转接头连接即可。Pod2Swim 需要 iOS 17 或更高版本，或 Android 8.0 或更高版本。",
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
        "compat": (linkify_shokz(linkify_adapter(compat, code))
                   # CJK runs sentences together with no inter-sentence space.
                   + ("" if code in ("ja", "zh-hans") else " ")
                   + ANDROID_COMPAT[code]),
        # CJK runs sentences together with no inter-sentence space.
        "disclaimer": (disclaimer + ("" if code in ("ja", "zh-hans") else " ")
                       + DISCLOSURE[code]).strip(),
        "badge": c["badge"],
        "playBadge": c["playBadge"],
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
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Sora:wght@400;600;700;800&display=swap" rel="stylesheet">
<script>
// Apply the saved (or system) appearance before first paint to avoid a flash.
(function(){
  var t = null;
  try { t = localStorage.getItem("p2s_theme"); } catch(e){}
  if (t !== "light" && t !== "dark")
    t = (window.matchMedia && matchMedia("(prefers-color-scheme: dark)").matches) ? "dark" : "light";
  document.documentElement.setAttribute("data-theme", t);
})();
</script>
<style>
  :root {
    --bg: #f4f9fe; --heading: #0a1f36; --body: #3d5a78; --band-text: #29486a; --faint: #5f7891;
    --link: #1f6cc7; --accent: #1f7ae0; --accent-border: rgba(31,122,224,0.35);
    --nav-bg: rgba(244,249,254,0.92); --line: rgba(31,122,224,0.14);
    --card-bg: #ffffff; --card-border: rgba(31,122,224,0.16); --card-shadow: 0 2px 10px rgba(10,31,54,0.05);
    --dot-glow: 0 0 0 4px rgba(31,122,224,0.14);
    --band-bg: rgba(31,122,224,0.05);
    --btn-bg: #0a1f36; --btn-fg: #ffffff;
    --btn2-bg: #ffffff; --btn2-fg: #0a1f36; --btn2-border: rgba(31,122,224,0.22);
    --pill-bg: #1f7ae0; --pill-fg: #ffffff;
    --seg-bg: rgba(31,122,224,0.07); --seg-border: rgba(31,122,224,0.18);
    --seg-active-bg: #1f7ae0; --seg-active-fg: #ffffff; --seg-active-shadow: 0 2px 8px rgba(31,122,224,0.3);
    --shot-border: rgba(31,122,224,0.2); --shot-shadow: 0 22px 50px rgba(10,31,54,0.18); --shot-bg: #ffffff;
    --hero-bg: radial-gradient(1100px 620px at 78% -10%, rgba(77,163,255,0.28), transparent 65%), radial-gradient(800px 500px at 8% 110%, rgba(31,122,224,0.14), transparent 60%), #f4f9fe;
    --hero-shadow1: 0 40px 80px rgba(10,31,54,0.25); --hero-shadow2: 0 50px 100px rgba(10,31,54,0.3);
    --hero-link: #0a1f36;
  }
  html[data-theme="dark"] {
    --bg: #061225; --heading: #ffffff; --body: #b9d1ec; --band-text: #c4d9f2; --faint: #7f9cbd;
    --link: #9cc4f0; --accent: #4da3ff; --accent-border: rgba(77,163,255,0.35);
    --nav-bg: rgba(6,18,37,0.9); --line: rgba(88,166,255,0.14);
    --card-bg: rgba(255,255,255,0.03); --card-border: rgba(88,166,255,0.16); --card-shadow: none;
    --dot-glow: 0 0 12px rgba(77,163,255,0.8);
    --band-bg: rgba(77,163,255,0.05);
    --btn-bg: #ffffff; --btn-fg: #04101f;
    --btn2-bg: rgba(255,255,255,0.06); --btn2-fg: #ffffff; --btn2-border: rgba(255,255,255,0.16);
    --pill-bg: #4da3ff; --pill-fg: #04101f;
    --seg-bg: rgba(88,166,255,0.08); --seg-border: rgba(88,166,255,0.2);
    --seg-active-bg: #4da3ff; --seg-active-fg: #04101f; --seg-active-shadow: none;
    --shot-border: rgba(88,166,255,0.22); --shot-shadow: 0 22px 50px rgba(0,0,0,0.5); --shot-bg: #0a1e38;
    --hero-bg: radial-gradient(1100px 620px at 78% -10%, rgba(31,122,224,0.42), transparent 65%), radial-gradient(800px 500px at 8% 110%, rgba(13,60,110,0.55), transparent 60%), #061225;
    --hero-shadow1: 0 40px 80px rgba(0,0,0,0.55); --hero-shadow2: 0 50px 100px rgba(0,0,0,0.6);
    --hero-link: #ffffff;
  }
  * { box-sizing: border-box; }
  html { scroll-behavior: smooth; }
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

  /* top nav */
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
  .brand img { width: 28px; height: 28px; border-radius: 7px; }
  .navright { display: flex; align-items: center; gap: 16px; }
  .navlink { font-weight: 600; font-size: 14px; color: var(--link); }
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

  /* hero */
  .hero { background: var(--hero-bg); overflow: hidden; }
  .hero-grid {
    position: relative; display: grid; grid-template-columns: 1.05fr 1fr;
    gap: 40px; align-items: center;
    max-width: 1180px; margin: 0 auto; padding: 76px 32px 88px;
  }
  .hero h1 { margin: 0 0 18px; font-size: 52px; line-height: 1.06; font-weight: 800;
    letter-spacing: -1.8px; color: var(--heading); text-wrap: balance; }
  .hero .appname { display: flex; align-items: center; gap: 12px; font-weight: 800;
    font-size: 18px; color: var(--heading); margin: 0 0 22px; }
  .hero .appname img { width: 44px; height: 44px; border-radius: 11px;
    box-shadow: 0 10px 26px rgba(10,31,54,0.25); }
  .hero .tagline { margin: 0 0 32px; font-size: 19px; color: var(--body);
    max-width: 480px; text-wrap: pretty; }
  .hero .tagline a { color: var(--hero-link); text-decoration: underline; text-underline-offset: 3px; }
  .hero-shots { position: relative; height: 560px; }
  .hero-shots img { position: absolute; border-radius: 26px;
    border: 1px solid var(--shot-border); background: var(--shot-bg); }
  .hero-shots .hs1 { left: 0; top: 60px; width: 235px; transform: rotate(-7deg);
    box-shadow: var(--hero-shadow1); }
  .hero-shots .hs2 { left: 190px; top: 0; width: 262px; border-radius: 28px;
    box-shadow: var(--hero-shadow2); z-index: 2; }
  .hero-shots .hs3 { left: 400px; top: 80px; width: 235px; transform: rotate(7deg);
    box-shadow: var(--hero-shadow1); }

  /* store download badges */
  .badgewrap { display: inline-flex; flex-wrap: wrap; align-items: center; gap: 13px; }
  .storebadge {
    display: inline-flex; align-items: center; gap: 11px;
    background: var(--btn-bg); color: var(--btn-fg); border-radius: 13px;
    padding: 11px 20px; text-decoration: none; text-align: left;
    user-select: none;
    transition: transform .12s ease, box-shadow .12s ease;
  }
  a.storebadge:hover {
    text-decoration: none; transform: translateY(-1px);
    box-shadow: 0 14px 34px rgba(77,163,255,0.35);
  }
  a.storebadge:active { transform: translateY(0); }
  .storebadge svg { width: 26px; height: 26px; }
  .appstore svg { fill: var(--btn-fg); }
  .storebadge .small { font-size: 11px; line-height: 1; opacity: 0.8; }
  .storebadge .big { font-size: 18px; font-weight: 700; line-height: 1.15; letter-spacing: -0.2px; }
  /* Google Play tile — live; the logo keeps its own brand colours (per-path
     fills in the SVG), so no fill override here. */
  .playstore {
    background: var(--btn2-bg); color: var(--btn2-fg); border: 1px solid var(--btn2-border); }

  /* full-bleed pitch band */
  .pitchband {
    border-top: 1px solid var(--line); border-bottom: 1px solid var(--line);
    background: var(--band-bg); padding: 34px 24px; text-align: center;
  }
  .pitch { font-size: 18px; color: var(--band-text); max-width: 860px;
    margin: 0 auto; text-wrap: pretty; }
  .pitch a { color: var(--accent); }

  main { max-width: 1080px; margin: 0 auto; padding: 0 24px; }

  .features { display: grid; gap: 22px; margin: 52px 0 8px;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); }
  .feature {
    background: var(--card-bg); border: 1px solid var(--card-border); border-radius: 20px;
    padding: 26px 28px 12px; box-shadow: var(--card-shadow);
  }
  .feature h2 {
    font-size: 13px; font-weight: 700; letter-spacing: 2px; text-transform: uppercase;
    color: var(--accent); margin: 0 0 16px;
  }
  .feature ul { list-style: none; margin: 0; padding: 0; }
  .feature li {
    position: relative; padding: 0 0 15px 24px; font-size: 15px; color: var(--body);
  }
  .feature li::before {
    content: ""; position: absolute; left: 0; top: 8px;
    width: 8px; height: 8px; border-radius: 50%;
    background: var(--accent); box-shadow: var(--dot-glow);
  }

  .shots { margin: 56px 0 8px; }
  .shots h2 { text-align: center; font-size: 30px; font-weight: 800;
    letter-spacing: -1px; margin: 0 0 20px; color: var(--heading); }
  .gallery-controls {
    display: flex; flex-wrap: wrap; justify-content: center; gap: 12px;
    margin: 0 0 24px;
  }
  .seg {
    display: inline-flex; background: var(--seg-bg);
    border: 1px solid var(--seg-border); border-radius: 999px; padding: 3px; gap: 2px;
  }
  .seg-btn {
    appearance: none; border: 0; background: transparent; cursor: pointer;
    font: inherit; font-size: 14px; font-weight: 600; color: var(--link);
    padding: 7px 18px; border-radius: 999px; display: inline-flex;
    align-items: center; gap: 6px;
    transition: background .15s ease, color .15s ease;
  }
  .seg-btn.is-active { background: var(--seg-active-bg); color: var(--seg-active-fg);
    box-shadow: var(--seg-active-shadow); }
  .seg-ico { font-size: 13px; line-height: 1; }
  .gallery {
    display: flex; gap: 20px; overflow-x: auto; padding: 8px 4px 24px;
    scroll-snap-type: x mandatory; -webkit-overflow-scrolling: touch;
  }
  .gallery img {
    width: 226px; flex: 0 0 auto; border-radius: 24px;
    border: 1px solid var(--shot-border); scroll-snap-align: center;
    box-shadow: var(--shot-shadow); background: var(--shot-bg);
  }

  /* changelog */
  .changelog { margin: 52px 0 8px; }
  .changelog h2 { text-align: center; font-size: 30px; font-weight: 800;
    letter-spacing: -1px; margin: 0 0 28px; color: var(--heading); }
  .release {
    background: var(--card-bg); border: 1px solid var(--card-border); border-radius: 20px;
    padding: 24px 28px 10px; margin: 0 auto 18px; max-width: 760px;
    box-shadow: var(--card-shadow);
  }
  .release-head {
    display: flex; align-items: baseline; justify-content: space-between;
    gap: 12px; flex-wrap: wrap; margin: 0 0 16px;
  }
  .release-head .ver { font-size: 17px; font-weight: 800; letter-spacing: -0.2px;
    color: var(--heading); }
  .release-head .date { font-size: 13px; font-weight: 600; color: var(--accent); }
  .release ul { list-style: none; margin: 0; padding: 0; }
  .release li {
    position: relative; padding: 0 0 14px 24px; font-size: 15px; color: var(--body);
  }
  .release li::before {
    content: ""; position: absolute; left: 0; top: 8px;
    width: 8px; height: 8px; border-radius: 50%;
    background: var(--accent); box-shadow: var(--dot-glow);
  }

  .fineprint { max-width: 760px; margin: 40px auto 0; }
  .fineprint h2 { font-size: 12.5px; font-weight: 700; letter-spacing: 2px;
    text-transform: uppercase; color: var(--accent); margin: 0 0 8px; }
  .fineprint p { margin: 0 0 12px; color: var(--faint); font-size: 14px; }

  footer {
    margin-top: 56px; border-top: 1px solid var(--line);
    text-align: center; color: var(--faint); font-size: 14px;
    padding: 32px 20px 56px;
  }
  footer .links { margin-bottom: 12px; }
  footer .links a { margin: 0 10px; font-weight: 600; }
  footer .mail { display: block; margin: 6px 0 14px; }

  @media (max-width: 960px) {
    .hero-grid { grid-template-columns: 1fr; padding: 56px 24px 64px; }
    .hero-shots { height: 480px; max-width: 640px; }
  }
  @media (max-width: 560px) {
    .hero h1 { font-size: 34px; letter-spacing: -1px; }
    .hero-shots { display: none; }
    .hero-grid { padding: 44px 20px 52px; }
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
    <button type="button" class="theme-btn" id="theme-toggle" aria-label="Light / dark">☾</button>
  </span>
</nav>

<header class="hero">
  <div class="hero-grid">
    <div>
      <p class="appname"><img src="assets/icon.png" alt=""> <span id="h-name">Pod2Swim</span></p>
      <h1 id="h-subtitle"></h1>
      <p class="tagline" id="h-tagline"></p>
      <div class="badgewrap">
    <a class="storebadge appstore" id="appstore-link" href="__APPSTORE__" target="_blank" rel="noopener" aria-label="Download Pod2Swim on the App Store">
      <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M16.36 12.78c-.02-2.3 1.88-3.4 1.96-3.46-1.07-1.56-2.73-1.78-3.32-1.8-1.41-.14-2.76.83-3.48.83-.72 0-1.82-.81-3-.79-1.54.02-2.96.9-3.75 2.28-1.6 2.78-.41 6.89 1.15 9.14.76 1.1 1.67 2.34 2.86 2.29 1.15-.05 1.58-.74 2.97-.74 1.38 0 1.77.74 2.98.72 1.23-.02 2.01-1.12 2.76-2.23.87-1.28 1.23-2.52 1.25-2.58-.03-.01-2.4-.92-2.42-3.65zM14.13 6.04c.64-.78 1.07-1.85.95-2.92-.92.04-2.03.61-2.69 1.38-.59.68-1.11 1.78-.97 2.83 1.03.08 2.07-.52 2.71-1.29z"/></svg>
      <span><span class="small" id="b-small">Download on the</span><br><span class="big">App Store</span></span>
    </a>
    <a class="storebadge playstore" id="playstore-link" href="__PLAYSTORE__" target="_blank" rel="noopener" aria-label="Get Pod2Swim on Google Play">
      <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3.6 2.4c-.24.25-.38.63-.38 1.13v16.94c0 .5.14.88.39 1.13l.06.05L13.1 12.1v-.22L3.67 2.35l-.07.05z" fill="#00d0ff"/><path d="M16.24 15.24 13.1 12.1v-.22l3.14-3.14.07.04 3.72 2.12c1.06.6 1.06 1.59 0 2.2l-3.72 2.11-.07.03z" fill="#ffc107"/><path d="m16.31 15.2-3.21-3.21-9.28 9.28c.35.37.93.42 1.58.05l10.91-6.12z" fill="#ff3d47"/><path d="M16.31 8.8 5.4 2.68c-.65-.37-1.23-.32-1.58.05l9.28 9.27L16.31 8.8z" fill="#00e676"/></svg>
      <span><span class="small" id="ps-small">Get it on</span><br><span class="big">Google Play</span></span>
    </a>
  </div>
    </div>
    <div class="hero-shots" aria-hidden="true">
      <img class="hs1" id="hs1" alt="">
      <img class="hs2" id="hs2" alt="">
      <img class="hs3" id="hs3" alt="">
    </div>
  </div>
</header>

<div class="pitchband"><p class="pitch" id="m-pitch"></p></div>

<main>

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
// appearance: <html data-theme> is set before first paint (head script);
// the gallery's light/dark filter starts on the page theme and stays in sync
// when the user toggles it, while remaining independently switchable.
function currentTheme(){
  return document.documentElement.getAttribute("data-theme") === "dark" ? "dark" : "light";
}
let galMode = currentTheme();
let galText = null;
const HERO_SHOTS = ["02", "01", "04"];
function renderHeroShots(){
  const base = "assets/shots/" + galLang + "/ios/" + currentTheme() + "/";
  HERO_SHOTS.forEach((n, i) => {
    const img = document.getElementById("hs" + (i + 1));
    img.src = base + n + ".webp";
    if (galText) img.alt = galText.name + " — screenshot " + (i + 1);
  });
  document.getElementById("theme-toggle").textContent = currentTheme() === "dark" ? "\u2600" : "\u263e";
}
function syncModeSeg(){
  document.querySelectorAll("#mode-seg .seg-btn").forEach(b => {
    const on = b.dataset.mode === galMode;
    b.classList.toggle("is-active", on);
    b.setAttribute("aria-pressed", on ? "true" : "false");
  });
}
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
  document.getElementById("ps-small").textContent = t.playBadge;
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
  renderHeroShots();
  document.getElementById("theme-toggle").title = t.light + " / " + t.dark;

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
  document.getElementById("theme-toggle").addEventListener("click", () => {
    const next = currentTheme() === "dark" ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", next);
    try { localStorage.setItem("p2s_theme", next); } catch(e){}
    galMode = next;
    syncModeSeg();
    renderGallery();
    renderHeroShots();
  });
  syncModeSeg();
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
            .replace("__PLAYSTORE__", PLAY_STORE_URL)
            .replace("__SHOT_NAMES__", json.dumps(SHOT_NAMES))
            .replace("__I18N__", json.dumps(data, ensure_ascii=False))
            .replace("__ORDER__", json.dumps(ORDER))
            .replace("__LANG_ATTR__", json.dumps(LANG_ATTR)))
    with open(os.path.join(REPO, "index.html"), "w", encoding="utf-8") as f:
        f.write(page)
    print("Wrote index.html (%d locales) + _localization/marketing/*.json" % len(ORDER))


if __name__ == "__main__":
    main()
