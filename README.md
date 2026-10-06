# Convertisseur Clavier Latin ⇄ Hébreu

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

- Conversion **Latin ⇄ Hébreu** (claviers physiques AZERTY et QWERTY),
  sens détecté automatiquement, conversion en direct pendant la frappe.
- Conversion **QWERTY ⇄ AZERTY**, avec sélecteur de sens intégré.
- Interface en **français, anglais et hébreu** (langue détectée
  automatiquement), prise en charge complète du RTL, thèmes
  clair / sombre / automatique.
- Réglages persistants en stockage local — rien ne quitte l'appareil.
- Raccourci presse-papiers Windows : `Ctrl+C`, `Ctrl+Alt+H`, `Ctrl+V`.
- Jeux de tests automatisés (mappings, intégrité de la page).

## Fichiers

| Fichier | Rôle |
|---|---|
| `convertisseur.html` | Page web unique (hors ligne). **Source de vérité des mappings.** |
| `fix-presse-papiers.py` / `.bat` | Raccourci presse-papiers Windows (usage quotidien). |
| `installer-raccourci.ps1` | Crée le raccourci Bureau + touche globale (`Ctrl+Alt+H`). |
| `app.py` | Application Windows : la page dans une fenêtre native (PyInstaller). |
| `gen_maps.py` | Régénère les tables du `.py` depuis le HTML. |
| `test_maps.py` | Test anti-dérive + non-régression des mappings. |
| `test_page.py` | Test d'intégrité : hors ligne, ids, i18n, RTL, syntaxe JS, version. |

## 1. Page web

Ouvrir `convertisseur.html` dans un navigateur (un double-clic suffit).

- Collez le texte : le sens est détecté et la conversion est immédiate.
- Boutons : `⇄ Inverser`, `✕ Effacer`, `📋 Copier (Ctrl+Entrée)`.
- ⚙ **Réglages** : mode de conversion (**Latin ⇄ Hébreu** par défaut,
  ou **QWERTY ⇄ AZERTY**), langue d'interface (auto : FR / EN / עברית),
  clavier physique (AZERTY / QWERTY, mode hébreu), sens par défaut, thème
  (clair / sombre / auto), taille du texte, conversion en direct,
  copie automatique, mémorisation du texte.

Exemples hébreu : `qkuo` (AZERTY) / `akuo` (QWERTY) → `שלום`,
`נםמחםור` → `bonjour`, `Bםמחםור` → `Bonjour`.
Exemples latin (mode QWERTY ⇄ AZERTY) : `qwerty` → `azerty` et inversement.
En mode latin, un mini-sélecteur de sens apparaît dans la page
(l'auto-détection étant impossible entre deux latins) et le bouton
⇄ bascule le sens, car les tables sont exactement inverses.

## 2. Usage quotidien (Windows)

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

## 3. Application Windows (.exe)

`ConvertisseurClavier.exe` (onglet *Releases* GitHub) : la même page dans
une fenêtre native, sans navigateur ni Python. Nécessite le runtime
WebView2 (présent par défaut sur Windows 11 et Windows 10 à jour).

Construire soi-même :

```sh
pip install pywebview pyinstaller
pyinstaller --noconsole --onefile --add-data "convertisseur.html;." --name ConvertisseurClavier app.py
```

Le `.exe` est dans `dist\` (non versionné, voir `.gitignore`).

> Antivirus : un `.exe` PyInstaller fraîchement construit est parfois
> bloqué à tort (faux positif de réputation, ex. Avast qui verrouille
> ou met en quarantaine). Dans ce cas, déclarez une exception pour le
> dossier dans l'antivirus, restaurez le fichier, puis relancez le build
> ou l'application.

## 4. Développement

**Les tables JavaScript de `convertisseur.html` sont la source de vérité.
Ne jamais éditer les tables de `fix-presse-papiers.py` à la main.**

Après toute modification des mappings dans le HTML :

```sh
python gen_maps.py
python test_maps.py
python test_page.py
```

`test_maps.py` compare les 6 tables (ordre + valeurs), détecte les clés
dupliquées, vérifie la réversibilité exacte et rejoue des cas connus
(`qkuo`/`akuo` → `שלום`, etc.). Exit `0` = synchronisé, `1` = dérive.
La CI GitHub Actions rejoue les deux suites (Ubuntu + Windows) à chaque push.

## Version et historique

Version affichée dans le pied de page (`APP_VERSION`), alignée sur le
tag git (`test_page.py` le vérifie). Historique : voir
[CHANGELOG.md](CHANGELOG.md) et `git log`.

## Licence

MIT — voir [LICENSE](LICENSE).
