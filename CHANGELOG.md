# Journal des modifications

## Non publié
- Détection `Ctrl+V` : les artefacts de ponctuation des tables (par exemple
  `:` rendu en lettre finale `ף`) ne bloquent plus une lecture correcte. Deux
  lettres finales de suite sont ignorées et le poids d'un sofit isolé est
  réduit, sans retirer la surveillance des sofits au milieu d'un mot.
- Corpus de référence : la détection correcte latin → hébreu passe de 93,8 %
  à 97,5 % (AZERTY) et 98,8 % (QWERTY), avec 0 faux positif et 0 KEEPS.

## v1.13.0 - 22 oct. 2026
- Détection des dispositions beaucoup plus fiable : modèles de **trigrammes**
  (au lieu de bigrammes) pour le français, l'anglais et l'hébreu, avec un
  corpus hébreu élargi (Torah et Talmud, domaine public).
- Moins de refus à tort : les pénalités de disposition trop sévères sont
  retirées ; les symboles naturels (`%`, `&`, `+`, `_`, `*`), les guillemets
  et les mots étrangers intégrés (`iOS`, `macOS`, `Berklee`) ne bloquent plus
  une proposition justifiée.
- Les lettres finales hébraïques (sofit) restent surveillées : une conversion
  qui en produit au milieu d'un mot n'est pas proposée.
- Résultats mesurés sur un corpus de 280 textes : la détection correcte passe
  de 56 à 94 % (français → hébreu), de 63 à 94 % (anglais → hébreu), de 65 à
  100 % (hébreu → français) et de 92 à 100 % (hébreu → anglais), sans aucun
  faux positif.
- Tests : nouveau harnais `test_ngrams.py` et cas de non-régression ajoutés
  à `test_paste.py` (mots étrangers, symboles, guillemets hébreux, sofits).

## v1.12.5 - 21 oct. 2026
- Interface principale modernisée : en-tête compact, espace de travail en
  deux panneaux (saisie / résultat), palette indigo-violet, cartes historique
  et exemples, et réglages en tiroir avec sélecteurs et interrupteurs.
- Fenêtre de proposition `Ctrl+V` harmonisée avec la page : mêmes couleurs,
  aperçu avec barre d'accent, boutons et espacements revus, coins arrondis
  fiabilisés (DWM Windows 11 + découpe GDI) et logo net.
- Comportement inchangé : conversion locale, thèmes clair/sombre, RTL,
  traductions fr/en/he et choix explicite avant chaque collage.
- Tests : contrôles de contraste, de structure et de rendu des deux fenêtres.

## v1.12.4 - 20 oct. 2026
- Fenêtre de proposition avant `Ctrl+V` : thème clair haute lisibilité
  (fond blanc, texte presque noir, accents bleu foncé), avec des contrastes
  WCAG AA vérifiés par les tests.
- Coins arrondis au niveau de la fenêtre et vrai logo de l'application
  (icône 128 px) à la place du badge dessiné, pour un rendu net.
- Boutons et menu avec anneaux de focus visibles, tailles de texte
  légèrement augmentées pour l'accessibilité.

## v1.12.3 - 20 oct. 2026
- Surveillance avant `Ctrl+V` : fenêtre de proposition agrandie et
  redessinée (aperçu, badge, boutons et aide clavier plus lisibles).
- La fenêtre ne se ferme plus toute seule après 12 secondes : elle reste
  ouverte jusqu'à un choix ou un clic ailleurs.
- Un clic ailleurs la ferme sans rien coller ; si aucun choix n'a été fait,
  la proposition réapparaît au `Ctrl+V` suivant. `Annuler`/`Échap` la
  consomme pour le presse-papiers courant.
- Test de la surveillance : état de la proposition après clic ailleurs ou
  annulation, et absence de minuterie de fermeture.

## v1.12.2 — 19 oct. 2026
- Installateur : logo haute résolution (rendu 1024 px de `logo.svg`) pour
  l'assistant, le Setup et le désinstalleur ; `app.ico` est régénérée à
  partir du même logo vectoriel.
- Installateur : les cases **menu clic droit** et **surveillance du
  presse-papiers** sont cochées par défaut à chaque installation.
- Installateur : ajout de l'**hébreu** aux langues (français, anglais,
  hébreu), avec traduction des tâches, raccourcis, commentaires et entrées
  du menu clic droit.

## v1.12.1 — 19 oct. 2026
- Installateur : le Setup, le désinstalleur et l'assistant utilisent
  maintenant le logo **Aא** de l'application (`SetupIconFile`,
  `UninstallDisplayIcon`, `WizardSmallImageFile`).
- `build_setup.py --check` vérifie la présence des logos et leur présence
  dans `installer.iss`.

## v1.12.0 — 19 oct. 2026
- Page : icône **Réglages** redessinée en engrenage à 6 dents, plus lisible en
  petit.
- Fenêtre de proposition `Ctrl+V` affinée : la disposition détectée est un
  petit menu **AZERTY ▾** qui permet de choisir manuellement AZERTY/QWERTY ;
  l'aperçu et le collage suivent immédiatement le choix.
- Le même menu propose **« Défaut si ambigu : AZERTY / QWERTY »** : quand les
  deux dispositions restent plausibles sur un texte court, le guetteur utilise
  ce choix par défaut. Le réglage est mémorisé localement et se change aussi
  depuis le menu de l'icône de notification.
- Détection des dispositions améliorée : une sortie qui laisse des lettres de
  l'écriture source ou des symboles de code (`/`, `\`, etc.) est pénalisée,
  pour éviter de choisir une disposition manifestement fausse.
- Tests : disposition par défaut, conversion imposée, lecture/écriture des
  réglages et présence des contrôles dans la fenêtre.

## v1.11.0 — 19 oct. 2026
- Nouvelle **surveillance avant `Ctrl+V`** (Windows, 100 % local) : quand le
  texte copié se lit nettement mieux avec l'autre clavier, une fenêtre
  propose la conversion avant l'insertion. `Entrée` convertit et colle,
  `Maj+Entrée` colle l'original, `Échap` annule ; fermeture automatique
  après 12 secondes.
- Détection prudente dans les deux sens (latin → hébreu et hébreu → latin),
  AZERTY et QWERTY, avec marge de confiance ; textes courts, mixtes, URL,
  chemins et code ne déclenchent rien.
- Icône dans la zone de notification : suspendre/reprendre, ouvrir
  l'application, quitter ; `--paste-watch` / `--paste-stop` pour le piloter.
- Démarrage automatique avec Windows (valeur `Run` HKCU) dans le Setup et
  `installer.ps1` ; `desinstaller.ps1` et l'UninstallRun arrêtent le guetteur
  avant de supprimer l'exe.
- Modèle de bigrammes hébreu généré depuis un texte Gutenberg du domaine
  public (`python gen_ngrams.py --hebrew`), séparé des modèles latins de la
  page.
- Nouveau `win32_clip.py` (presse-papiers Unicode Win32 partagé) et
  `test_paste.py` (détection, modèle, parité page, démarrage automatique),
  ajouté à la CI. L'exe embarque `app.ico` pour la zone de notification.

## v1.10.0 — 18 oct. 2026
- Nouvelle extension navigateur (Chrome/Edge, Manifest V3) dans `extension/` :
  clic droit sur une sélection → conversion dans le champ actif (input,
  textarea, contenteditable) ou copie du résultat ; raccourci `Ctrl+Maj+H` ;
  popup de conversion avec réglages mémorisés localement.
- Les tables et le cœur de conversion (`convertSmart`, `detectDir`) de
  l'extension sont **générés** depuis `convertisseur.html` par `gen_maps.py` :
  une seule implémentation, aucune dérive possible (vérifié par les tests).
- `gen_version.py` synchronise aussi la version du manifeste de l'extension.
- Nouveau `test_extension.py` (manifeste, icônes, CSP, syntaxe JS, câblage du
  clic droit et conversions), ajouté à la CI et à `test_maps.py`.

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
