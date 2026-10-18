# Journal des modifications

## v1.9.1 — 18 oct. 2026
- Correctif menu clic droit : le contenu du fichier est injecté dans la page
  après chargement (`app.preload_js`) — WebView2 refuse une URL
  `file://…?text=…` et affichait une page d'erreur.
- Lecture des fichiers `.txt` : décodage cp1255 (hébreu ANSI Windows) en plus
  d'UTF-8 et cp1252, sans confondre un fichier français accentué.
- Nouveau `test_app.py` (encodages, injection, verbes CLI), ajouté à la CI.
- Exe Windows à jour.

## v1.9.0 — 16 oct. 2026
- Vrai Setup Windows : `Setup_ConvertisseurClavier-X.Y.Z.exe` (Inno Setup,
  sans admin) avec menu Démarrer, `Ctrl+Alt+K`, `Ctrl+Alt+H` et case
  « menu clic droit » (`installer.iss`, `build_setup.py`).
- Menu clic droit de l'Explorateur : ouvrir un fichier (contenu
  pré-chargé), convertir un `.txt` (`--convert-file`), ouvrir depuis un
  dossier ; aussi via `installer.ps1` (désactivable), ménage complet à la
  désinstallation.
- L'exe convertit sans fenêtre ni Python : `--convert-clipboard`
  (texte sélectionné partout : `Ctrl+C`, `Ctrl+Alt+H`, `Ctrl+V` —
  Word, navigateur, recherche Windows, dont le clic droit appartient à
  chaque appli) et `--convert-file`.
- Exe Windows à jour.

## v1.8.1 — 16 oct. 2026
- Suggestion de lecture : touche `↓` dans le champ pour appliquer la lecture
  proposée quand le bandeau est visible (bouton « Afficher cette lecture (↓) »).
- Exe Windows à jour.

## v1.8.0 — 15 oct. 2026
- Suggestion de lecture AZERTY/QWERTY : si un texte hébreu (≥ 11 lettres,
  marge renforcée entre 11 et 14) se lit nettement mieux avec l'autre
  disposition, un bandeau en propose un aperçu (« Afficher cette lecture »),
  jamais appliqué automatiquement.
- Moteur de bigrammes embarqué (fr/en, ~2,4 Ko/langue, 100 % hors-ligne),
  généré par `gen_ngrams.py` (sources Gutenberg vérifiées par SHA-256).
- Exe Windows à jour.

## v1.7.3 — 15 oct. 2026
- Cohérence : badge « converti vers Français/Anglais » (fini « vers AZERTY »).
- Accessibilité Lighthouse 1.0 : repère `<main>`, titres h1→h2 sans saut.
- Mobile <560px : barre centrale et sélecteur en retour à la ligne.

## v1.7.2 — 15 oct. 2026
- Performance : conversion ~6x plus rapide (tables C, court-circuit et
  substitutions sans segmentation), sémantique prouvée identique
  (batterie + 1200 comparaisons fuzz).

## v1.7.1 — 14 oct. 2026
- Parité de détection auto page/script (accents), `.bat` avec message
  guidé si Python absent, CI en Python 3.14, installation documentée.
- Tests : diagnostics CI de l'installeur, noms courts 8.3.

## v1.7.0 — 7 oct. 2026
- Vrai programme installable : menu Démarrer (recherche), touche globale
  `Ctrl+Alt+K`, entrée de désinstallation (`installer.ps1`).
- Exe nommé avec sa version (`build_exe.py`).

## v1.6.0 — 7 oct. 2026
- Historique local des conversions (copies explicites), restauration
  au clic, désactivable.
- Véritable logo « touche bilingue Aא » : marque, favicon, README.
- Exe Windows à jour.

## v1.5.4 — 7 oct. 2026
- Version intégrée à l'exécutable (`gen_version.py` + `version_info.txt`,
  Propriétés > Détails) et exe à jour.

## v1.5.3 — 7 oct. 2026
- Icones SVG dessinées + mini-drapeaux FR/GB/IL (plus d'emoji).
- Exe Windows à jour.

## v1.5.2 — 7 oct. 2026
- Texte mixte : en sens hébreu→français, seuls les segments contenant de
  l'hébreu sont convertis ; le reste est préservé (mots, chiffres,
  ponctuation, `M`). Capitales Q/A/W/Z traitées (AZERTY).

## v1.5.1 — 6 oct. 2026
- « Latin » remplacé par « Français » / « Anglais » selon le clavier,
  dans les 3 langues (page, script, docs).

## v1.5.0 — 6 oct. 2026
- Application Windows `ConvertisseurClavier.exe` : la page dans une
  fenêtre native (`app.py`, PyInstaller, runtime WebView2 requis).

## v1.4.2 — 6 oct. 2026
- Bouton Copier déplacé après la zone de résultat.
- Pages : `index.html` de redirection + lien démo dans le README.

## v1.4.1 — 6 oct. 2026
- Contraste AA en thème sombre : texte sombre sur boutons primaires et
  marque (mesuré 2,98 → ≥ 6), test de contraste intégré à `test_page.py`.
- CI GitHub Actions (Ubuntu + Windows), release GitHub, déploiement Pages.

## v1.4.0 — 6 oct. 2026
- Mode QWERTY ⇄ AZERTY : choix du mode dans les réglages, mini-sélecteur
  de sens dans la page, exemples adaptés, ⇄ bascule le sens
  (tables exactement inverses, prouvé par test).
- Pro : favicon, métas traduits + theme-color synchronisé, copie
  infaillible (repli execCommand), version affichée v1.4.0.
- Page épurée : boutons de sens manuel supprimés, 100 % automatique.
- En-tête centré, refonte visuelle (marque, cartes, puces, pied de page).
- RTL hébreu cohérent : paires en LTR, tooltips traduits, isolates bidi,
  panneau réglages ouvrable (fix spécificité CSS).
- Langue d'interface auto (navigateur) par défaut, réglable.
- Accessibilité : focus trap, fieldset/legend, titre traduit, noscript.
- Quotidien : script presse-papiers + `.bat` + installeur de raccourci
  global (`Ctrl+Alt+H`), message console ASCII sur Windows.
- Qualité : source de vérité unique (HTML), `gen_maps.py`,
  `test_maps.py`, `test_page.py`, README, repo git tagué.
