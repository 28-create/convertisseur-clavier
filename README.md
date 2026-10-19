<p align="center"><img src="logo.svg" width="96" alt="Logo Convertisseur Clavier"></p>

# Convertisseur Clavier Français/Anglais ⇄ Hébreu

[![Version](https://img.shields.io/github/v/tag/28-create/convertisseur-clavier?label=version)](https://github.com/28-create/convertisseur-clavier/tags)
[![Licence](https://img.shields.io/github/license/28-create/convertisseur-clavier)](LICENSE)
[![Tests](https://github.com/28-create/convertisseur-clavier/actions/workflows/tests.yml/badge.svg)](https://github.com/28-create/convertisseur-clavier/actions)
![100 % local](https://img.shields.io/badge/100%25-local-brightgreen)

**Démo en ligne : https://28-create.github.io/convertisseur-clavier/**

Outil **100 % local** qui récupère un texte tapé avec le mauvais clavier :
quand on oublie de basculer entre AZERTY / QWERTY et hébreu, le texte
est reconverti dans le bon sens, automatiquement.

Aucun serveur, aucune donnée envoyée : tout s'exécute dans le navigateur
ou sur votre machine Windows.

## Fonctionnalités

- Conversion **Français/Anglais ⇄ Hébreu** (claviers physiques AZERTY et QWERTY),
  sens détecté automatiquement, conversion en direct pendant la frappe.
- Conversion **QWERTY ⇄ AZERTY**, avec sélecteur de sens intégré.
- Interface en **français, anglais et hébreu** (langue détectée
  automatiquement), prise en charge complète du RTL, thèmes
  clair / sombre / automatique.
- Réglages persistants en stockage local — rien ne quitte l'appareil.
- Raccourci presse-papiers Windows : `Ctrl+C`, `Ctrl+Alt+H`, `Ctrl+V`.
- **Surveillance avant `Ctrl+V`** : si le texte collé se lit nettement mieux
  avec l'autre clavier, une proposition apparaît avant l'insertion
  (`Entrée` = convertir, `Maj+Entrée` = coller l'original, `Échap` = annuler).
- Setup Windows (assistant, sans admin) : menu Démarrer, touches globales,
  menu clic droit de l'Explorateur et démarrage automatique de la surveillance.
- Extension navigateur Chrome/Edge : clic droit sur une sélection,
  `Ctrl+Maj+H`, popup de conversion (section 4).
- Jeux de tests automatisés (mappings, intégrité de la page, extension).

## Fichiers

| Fichier | Rôle |
|---|---|
| `convertisseur.html` | Page web unique (hors ligne). **Source de vérité des mappings.** |
| `fix-presse-papiers.py` / `.bat` | Raccourci presse-papiers Windows (usage quotidien). |
| `installer-raccourci.ps1` | Crée le raccourci Bureau + touche globale (`Ctrl+Alt+H`). |
| `installer.ps1` / `desinstaller.ps1` | Installe le vrai programme (menu Démarrer + `Ctrl+Alt+K` + `Ctrl+Alt+H` + menu clic droit + désinstallation). |
| `installer.iss` | Script Inno Setup : construit `Setup_ConvertisseurClavier-X.Y.Z.exe` (assistant graphique avec logo, case menu clic droit). |
| `build_setup.py` | Compile le Setup (`--check` seul en CI, sans Inno). |
| `build_extension.py` | Construit `dist\ConvertisseurClavier-extension-X.Y.Z.zip` (paquet à déposer sur les stores). |
| `app.py` | Application Windows : la page dans une fenêtre native (PyInstaller), verbes CLI et surveillance. |
| `paste_watch.py` | Guetteur `Ctrl+V` : détection, fenêtre de proposition, icône de notification, crochet clavier Win32. |
| `win32_clip.py` | Presse-papiers Unicode Win32 partagé par `app.py` et `paste_watch.py`. |
| `extension/` | Extension Chrome/Edge (Manifest V3) : clic droit, `Ctrl+Maj+H`, popup. |
| `PRIVACY.md` / `confidentialite.html` | Politique de confidentialité (page publiée par GitHub Pages). |
| `gen_maps.py` | Régénère les tables du `.py` **et le cœur de l'extension** depuis le HTML. |
| `gen_ngrams.py` | Régénère les modèles de bigrammes (suggestion de lecture). |
| `test_maps.py` | Test anti-dérive + non-régression des mappings. |
| `test_app.py` | Test de l'app : encodages `.txt`, injection du préchargement, verbes CLI. |
| `test_paste.py` | Test de la surveillance : détection, modèle hébreu, parité page, démarrage auto. |
| `test_extension.py` | Test de l'extension : manifeste, icônes, CSP, câblage du clic droit, conversions. |
| `test_store.py` | Test du paquet store : manifeste et ses limites, textes de fiche, zip reproductible. |
| `store/` | Textes de la fiche (fr/en) et justifications de permissions, prêts à coller. |
| `test_page.py` | Test d'intégrité : hors ligne, ids, i18n, RTL, syntaxe JS, version. |
| `build_exe.py` | Construit `dist\ConvertisseurClavier-X.Y.Z.exe` (nom versionné, icône `app.ico`). |
| `app.ico` | Icône de l'exe (dérivée de `logo.svg`). |
| `gen_version.py` | Régénère `version_info.txt` (tampon de version de l'exe). |
| `test_installer.ps1` | Test bout-en-bout de l'installeur (bac à sable). |

## 1. Page web

Ouvrir `convertisseur.html` dans un navigateur (un double-clic suffit).

- Collez le texte : le sens est détecté et la conversion est immédiate.
- Texte mixte : en sens hébreu→français, seuls les mots contenant de
  l'hébreu sont convertis ; le français (mots, chiffres, ponctuation)
  est préservé. Mots tout en capitales : seules Q/A/W/Z commutent.
- Boutons : `⇄ Inverser`, `✕ Effacer`, `📋 Copier (Ctrl+Entrée)`.
- **Historique** (replié sous le résultat) : chaque copie explicite y est
  mémorisée **localement** (navigateur uniquement, effaçable, désactivable
  dans ⚙) ; clic pour restaurer.
- ⚙ **Réglages** : mode de conversion (**Français/Anglais ⇄ Hébreu** par défaut,
  ou **QWERTY ⇄ AZERTY**), langue d'interface (auto : FR / EN / עברית),
  clavier physique (AZERTY / QWERTY, mode hébreu), sens par défaut, thème
  (clair / sombre / auto), taille du texte, conversion en direct,
  copie automatique, mémorisation du texte.
- **Suggestion de lecture** : si un texte hébreu (≥ 11 lettres, marge de
  confiance renforcée entre 11 et 14) se lit nettement mieux avec l'autre
  disposition, un bandeau en propose un aperçu (« Afficher cette lecture »)
  — jamais appliqué automatiquement (touche `↓` dans le champ pour appliquer).

Exemples hébreu : `qkuo` (AZERTY) / `akuo` (QWERTY) → `שלום`,
`נםמחםור` → `bonjour`, `Bםמחםור` → `Bonjour`.
Exemples latin (mode QWERTY ⇄ AZERTY) : `qwerty` → `azerty` et inversement.
En mode latin, un mini-sélecteur de sens apparaît dans la page
(l'auto-détection étant impossible entre deux latins) et le bouton
⇄ bascule le sens, car les tables sont exactement inverses.

## 2. Usage quotidien (Windows)

### Sans rien installer (script Python)

Sélectionnez le texte tapé avec le mauvais clavier, puis :

1. `Ctrl+C`
2. Lancez `fix-presse-papiers.bat`
   (ou `installer-raccourci.ps1` : crée le raccourci Bureau
   avec la touche globale `Ctrl+Alt+H` en une commande)
3. `Ctrl+V`

Options :

```bat
fix-presse-papiers.bat --layout qwerty
fix-presse-papiers.bat "texte direct" --layout azerty --direction toFr
```

`--layout` : `azerty` (défaut) ou `qwerty` (mode hébreu).
`--direction` : `auto` (défaut), `toHe`, `toFr` (mode hébreu).
`--mode latin` + `--latin-dir toAz|toQw` : conversion QWERTY ⇄ AZERTY.
Sans argument texte, le script lit et réécrit le presse-papiers.

Prérequis : Python 3 (`py` ou `python` dans le PATH, `tkinter` inclus).
Si la console Windows ne peut pas afficher l'hébreu, le script affiche
un repli ASCII `\uXXXX` au lieu de planter — le presse-papiers,
lui, est toujours correct.

### Sans Python (Setup installé)

Une fois le programme installé (section 3), la touche `Ctrl+Alt+H`
convertit directement le presse-papiers, sans fenêtre ni Python :
`Ctrl+C`, `Ctrl+Alt+H`, `Ctrl+V`. C'est le moyen universel pour du
texte saisi dans Word, un navigateur, la barre de recherche Windows…

La **surveillance du presse-papiers** (option cochée par défaut dans le
Setup) fait encore plus court : copiez normalement, puis appuyez sur
`Ctrl+V`. Si le texte copié est manifestement tapé avec le mauvais
clavier, une petite fenêtre propose la conversion avant l'insertion :

- `Entrée` ou **Convertir et coller** : convertit puis colle ;
- `Maj+Entrée` ou **Coller tel quel** : colle l'original ;
- `Échap` ou **Annuler** : ne colle rien (le presse-papiers reste intact).

La fenêtre affiche la disposition détectée dans un petit menu **AZERTY ▾** :
on peut y choisir **AZERTY** ou **QWERTY**, et l'aperçu comme le texte collé
suivent immédiatement le choix. Le même menu propose **Défaut si ambigu :
AZERTY / QWERTY**, utilisé quand le texte est trop court pour distinguer les
deux dispositions. Ce réglage est mémorisé dans
`%LOCALAPPDATA%\ConvertisseurClavier\paste_watch.json` et se change aussi
depuis le menu de l'icône de notification.

La proposition disparaît seule au bout de 12 secondes. Les `Ctrl+Maj+V`,
`Ctrl+Alt+V` et `Win+V` ne sont jamais interceptés ; la surveillance se
suspend ou se quitte par un clic droit sur son icône dans la zone de
notification (ou `--paste-stop`).

## 3. Application Windows (.exe + Setup)

`ConvertisseurClavier.exe` (onglet *Releases* GitHub) : la même page dans
une fenêtre native, sans navigateur ni Python. Nécessite le runtime
WebView2 (présent par défaut sur Windows 11 et Windows 10 à jour).
L'exe sait aussi convertir sans fenêtre (`--convert-clipboard`,
`--convert-file`) : c'est ce qu'utilisent le menu clic droit et la
touche `Ctrl+Alt+H`, sans Python installé.

### Installation recommandée : Setup.exe

1. Téléchargez `Setup_ConvertisseurClavier-X.Y.Z.exe` depuis l'onglet
   *Releases*, double-cliquez, Suivant/Suivant (aucun droit admin requis).
   Le Setup et l'assistant affichent le logo de l'application. L'assistant
   est disponible en français, anglais et hébreu.
2. L'assistant installe : menu Démarrer, touche `Ctrl+Alt+K` (ouvrir
   l'appli), touche `Ctrl+Alt+H` (convertir le presse-papiers), — case
   cochée par défaut — le menu clic droit de l'Explorateur, et le
   démarrage automatique de la surveillance `Ctrl+V` (décochez la case
   *Surveiller le presse-papiers au démarrage* pour l'éviter).
3. Désinstallation : Paramètres Windows → Applications (ménage complet,
   menu clic droit et démarrage automatique inclus).

### Menu clic droit (Explorateur Windows)

- Clic droit sur un **fichier** : *Ouvrir avec Convertisseur Clavier*
  (le contenu est pré-chargé dans la fenêtre).
- Clic droit sur un **.txt** : *Convertir avec Convertisseur Clavier*
  (écrit un `nom.converti.txt` à côté, l'original est conservé).
- Clic droit sur un **dossier** ou son **fond** : ouvrir l'application.

Dans le Setup, c'est la case *« menu clic droit »*. En script,
`installer.ps1` l'ajoute par défaut (`-SansMenuContextuel` pour l'ignorer).

### Convertir du texte sélectionné partout (Word, navigateur, recherche…)

Le menu clic droit de Word, du navigateur ou de la barre de recherche
appartient à chaque application : aucun installeur ne peut y ajouter une
entrée. Le flux universel (installé par le Setup et `installer.ps1`) :

1. Sélectionnez le texte, `Ctrl+C`
2. `Ctrl+Alt+H` (l'exe convertit le presse-papiers, sans fenêtre ni Python)
3. `Ctrl+V`

### Surveillance avant `Ctrl+V` (option du Setup)

La surveillance est un petit processus dans la zone de notification
(`--paste-watch`), lancé au démarrage de session par une valeur
`HKCU\...\Run` (aucun droit admin). Elle lit le presse-papiers en local et
installe un crochet clavier bas niveau qui n'intercepte que le `Ctrl+V`
simple ; tout le reste passe normalement. Le texte n'est jamais envoyé
sur le réseau, et le presse-papiers n'est modifié qu'après un choix
explicite.

En script, `installer.ps1` l'active par défaut (`-SansSurveillance` pour
ne pas l'installer, `-SansDemarrage` pour l'installer sans la lancer).
`desinstaller.ps1` arrête le guetteur et retire la valeur `Run`.
L'arrêt manuel se fait par `ConvertisseurClavier.exe --paste-stop`.

> Un crochet clavier bas niveau peut attirer les faux positifs de
> certains antivirus. Si la surveillance est bloquée, ajoutez une
> exception pour `ConvertisseurClavier.exe` (voir aussi la note
> antivirus plus bas).

### Installation par script (sans assistant)

Téléchargez `ConvertisseurClavier-X.Y.Z.exe`, `installer.ps1` et
`desinstaller.ps1` depuis l'onglet *Releases*, placez les trois fichiers
dans un même dossier, puis :

```powershell
powershell -ExecutionPolicy Bypass -File installer.ps1
```

Le programme devient cherchable dans le menu Démarrer et s'ouvre depuis
n'importe où avec `Ctrl+Alt+K` (si cette combinaison est déjà prise par
une autre application, relancez avec `-Raccourci 'CTRL+ALT+J'` par exemple).
Désinstallation : Paramètres Windows → Applications, ou `desinstaller.ps1`.

Construire soi-même (nom versionné automatiquement) :

```sh
pip install pywebview pyinstaller
python build_exe.py
```

Le `.exe` est dans `dist\` (non versionné, voir `.gitignore`).
Puis le Setup (Windows, Inno Setup 6 requis) :

```sh
python build_setup.py
```

Le `Setup_ConvertisseurClavier-X.Y.Z.exe` est dans `dist\`.
Sans Inno installé, `python build_setup.py --check` vérifie au moins la
cohérence (`installer.iss` : version, menu clic droit).

> Antivirus : un `.exe` PyInstaller fraîchement construit est parfois
> bloqué à tort (faux positif de réputation, ex. Avast qui verrouille
> ou met en quarantaine). Dans ce cas, déclarez une exception pour le
> dossier dans l'antivirus, restaurez le fichier, puis relancez le build
> ou l'application. Le `Setup.exe` peut lui aussi être freiné : ajoutez
> une exception pour le fichier d'installation et pour
> `%LOCALAPPDATA%\Programs\ConvertisseurClavier`. La surveillance
> (`--paste-watch`) installe un crochet clavier local : si elle est
> bloquée, excluez aussi `ConvertisseurClavier.exe`.

## 4. Extension navigateur (Chrome / Edge)

Dossier `extension/` — Manifest V3, **100 % local**, aucune permission
réseau (voir `test_extension.py`). L'extension n'est pas publiée sur le
store : on la charge en mode développeur.

1. Chrome : `chrome://extensions` (Edge : `edge://extensions`).
2. Activez **Mode développeur**.
3. **Charger l'extension non empaquetée** → choisissez le dossier
   `extension/`.

Utilisation :

- **Popup** (icône de la barre d'outils) : le résultat se met à jour
  pendant la frappe ; choix du mode (auto, vers l'hébreu, vers le latin,
  QWERTY ⇄ AZERTY) et du clavier (AZERTY / QWERTY). Les réglages sont
  mémorisés localement.
- **Clic droit sur une sélection** : *Convertir la sélection* (sens
  détecté), *Convertir en hébreu*, *Convertir en latin*. Dans un champ
  (`input`, `textarea`, zone éditable), le texte est remplacé sur place
  et reste annulable avec `Ctrl+Z` ; ailleurs, le résultat est copié et
  affiché dans une notification.
- **`Ctrl+Maj+H`** : convertit la sélection du champ actif.

Limite : le clic droit **dans Word** ou dans la barre de recherche Windows
appartient à ces applications et reste hors de portée d'une extension.
Dans le navigateur, l'extension le permet ; partout ailleurs, utilisez
`Ctrl+Alt+H` (section 3).

Après une modification des mappings, `python gen_maps.py` met à jour
`extension/js/core.js` ; cliquez ensuite sur **Recharger** dans la page
Extensions.

### Publier sur le store (Chrome / Edge)

L'extension **n'est pas publiée** : elle se charge en mode développeur
(ci-dessus). Pour préparer le paquet à déposer :

```sh
python build_extension.py --check   # manifeste, fichiers references, version
python build_extension.py           # dist\ConvertisseurClavier-extension-X.Y.Z.zip
```

Le ZIP contient le contenu de `extension/`, `manifest.json` à la racine, et le
numéro de version doit augmenter à chaque envoi. Les textes de la fiche, les
justifications de permissions à coller dans le tableau de bord et la marche à
suivre sont dans `store/` (voir **`store/checklist.md`**). Politique de
confidentialité :
<https://28-create.github.io/convertisseur-clavier/confidentialite.html>.

## 5. Développement

**Les tables JavaScript de `convertisseur.html` sont la source de vérité.
Ne jamais éditer à la main les tables (ni `CAPS_SWAP`) de
`fix-presse-papiers.py` ni les blocs générés de `extension/js/core.js`.**

Après toute modification des mappings dans le HTML :

```sh
python gen_maps.py
python test_maps.py
python test_app.py
python test_paste.py
python test_extension.py
python test_store.py
python test_page.py
```

`test_maps.py` compare les 6 tables et `CAPS_SWAP` (ordre + valeurs) dans
le HTML, le script Python et l'extension, détecte les clés dupliquées,
vérifie la réversibilité exacte, rejoue des cas connus
(`qkuo`/`akuo` → `שלום`, etc.) puis confronte le JS au Python sur
1200 textes aléatoires. Exit `0` = synchronisé, `1` = dérive.
`test_extension.py` vérifie en plus le manifeste, les icônes, l'absence de
code distant ou inline, la syntaxe JS, le câblage du clic droit et des
conversions réelles. `test_paste.py` couvre la détection prudente
(`qkuo`/`akuo`/`נםמחםור`, faux positifs), le bloc de modèle hébreu, la
parité des scores avec la page et la présence du démarrage automatique
dans les deux installateurs.
La CI GitHub Actions rejoue les suites (Ubuntu + Windows, Python 3.11 à
3.14) à chaque push.

`gen_ngrams.py` régénère les modèles de bigrammes (textes du domaine public,
vérifiés par SHA-256) qui alimentent la suggestion de lecture :
`python gen_ngrams.py` (téléchargement, ou `--corpus-dir` pour réutiliser
des fichiers locaux). Ajouter une langue de détection = une entrée dans
`LANGS`, puis relancer. Pour le guetteur, `python gen_ngrams.py --hebrew`
régénère le modèle hébreu de `paste_watch.py` (même source Gutenberg
épinglée, bloc généré à ne pas éditer à la main).

## Version et historique

Version affichée dans le pied de page (`APP_VERSION`), alignée sur le
tag git (`test_page.py` le vérifie : entre un bump et la création du tag,
le test échoue volontairement). Ordre de release : bump → `python
gen_version.py` → entrée CHANGELOG → commit `Release vX.Y.Z` → tag.
Historique : voir
[CHANGELOG.md](CHANGELOG.md) et `git log`.

## Licence

MIT — voir [LICENSE](LICENSE).
