# Journal des modifications

## Non publié
- Historique local des conversions (copies explicites), restauration
  au clic, désactivable.

## Non publié
- Véritable logo « touche bilingue Aא » : marque, favicon, README.

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
