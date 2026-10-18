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
- Setup Windows (assistant, sans admin) : menu Démarrer, touches globales
  et menu clic droit de l'Explorateur.
- Jeux de tests automatisés (mappings, intégrité de la page).

## Fichiers

| Fichier | Rôle |
|---|---|
| `convertisseur.html` | Page web unique (hors ligne). **Source de vérité des mappings.** |
| `fix-presse-papiers.py` / `.bat` | Raccourci presse-papiers Windows (usage quotidien). |
| `installer-raccourci.ps1` | Crée le raccourci Bureau + touche globale (`Ctrl+Alt+H`). |
| `installer.ps1` / `desinstaller.ps1` | Installe le vrai programme (menu Démarrer + `Ctrl+Alt+K` + `Ctrl+Alt+H` + menu clic droit + désinstallation). |
| `installer.iss` | Script Inno Setup : construit `Setup_ConvertisseurClavier-X.Y.Z.exe` (assistant graphique, case menu clic droit). |
| `build_setup.py` | Compile le Setup (`--check` seul en CI, sans Inno). |
| `app.py` | Application Windows : la page dans une fenêtre native (PyInstaller). |
| `gen_maps.py` | Régénère les tables du `.py` depuis le HTML. |
| `gen_ngrams.py` | Régénère les modèles de bigrammes (suggestion de lecture). |
| `test_maps.py` | Test anti-dérive + non-régression des mappings. |
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
2. L'assistant installe : menu Démarrer, touche `Ctrl+Alt+K` (ouvrir
   l'appli), touche `Ctrl+Alt+H` (convertir le presse-papiers), et —
   case cochée par défaut — le menu clic droit de l'Explorateur.
3. Désinstallation : Paramètres Windows → Applications (ménage complet,
   menu clic droit inclus).

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
> ou l'application.

## 4. Développement

**Les tables JavaScript de `convertisseur.html` sont la source de vérité.
Ne jamais éditer les tables (ni `CAPS_SWAP`) de `fix-presse-papiers.py`
à la main.**

Après toute modification des mappings dans le HTML :

```sh
python gen_maps.py
python test_maps.py
python test_page.py
```

`test_maps.py` compare les 6 tables et `CAPS_SWAP` (ordre + valeurs),
détecte les clés dupliquées, vérifie la réversibilité exacte, rejoue des
cas connus (`qkuo`/`akuo` → `שלום`, etc.) puis confronte le JS au Python
sur 1200 textes aléatoires. Exit `0` = synchronisé, `1` = dérive.
La CI GitHub Actions rejoue les deux suites (Ubuntu + Windows,
Python 3.11 à 3.14) à chaque push.

`gen_ngrams.py` régénère les modèles de bigrammes (textes du domaine public,
vérifiés par SHA-256) qui alimentent la suggestion de lecture :
`python gen_ngrams.py` (téléchargement, ou `--corpus-dir` pour réutiliser
des fichiers locaux). Ajouter une langue de détection = une entrée dans
`LANGS`, puis relancer.

## Version et historique

Version affichée dans le pied de page (`APP_VERSION`), alignée sur le
tag git (`test_page.py` le vérifie : entre un bump et la création du tag,
le test échoue volontairement). Ordre de release : bump → `python
gen_version.py` → entrée CHANGELOG → commit `Release vX.Y.Z` → tag.
Historique : voir
[CHANGELOG.md](CHANGELOG.md) et `git log`.

## Licence

MIT — voir [LICENSE](LICENSE).
