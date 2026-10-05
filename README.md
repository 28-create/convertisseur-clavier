# Convertisseur Clavier Latin ⇄ Hébreu

Outil **100 % local** qui récupère un texte tapé avec le mauvais clavier :
oubli du basculement AZERTY / QWERTY ↔ hébreu → le texte est reconverti
dans le bon sens, automatiquement ou manuellement.

Aucun serveur, aucune donnée envoyée : tout tourne dans le navigateur
ou en local sur Windows.

## Fichiers

| Fichier | Rôle |
|---|---|
| `convertisseur.html` | Page web unique (offline). **Source de vérité des mappings.** |
| `fix-presse-papiers.py` / `.bat` | Raccourci presse-papiers Windows (usage quotidien). |
| `gen_maps.py` | Régénère les tables du `.py` depuis le HTML. |
| `test_maps.py` | Test anti-dérive + non-régression (à lancer après chaque modif). |

## 1. Page web

Ouvrir `convertisseur.html` dans un navigateur (double-clic suffit).

- Collez le texte : détection auto du sens, conversion en direct.
- Boutons : `⇄ Inverser`, `✕ Effacer`, `📋 Copier (Ctrl+Entrée)`.
  La conversion est en direct et le sens automatique (réglable dans ⚙).
- ⚙ **Réglages** : mode de conversion (**Latin ⇄ Hébreu** par défaut,
  ou **QWERTY ⇄ AZERTY**), langue d'interface (auto : FR / EN / עברית),
  clavier physique (AZERTY / QWERTY, mode hébreu), sens par défaut, thème
  (clair / sombre / auto), taille du texte, conversion live,
  copie auto, mémorisation du texte.

Exemples hébreu : `qkuo` (AZERTY) / `akuo` (QWERTY) → `שלום`,
`נםמחםור` → `bonjour`, `Bםמחםור` → `Bonjour`.
Exemples latin (mode QWERTY ⇄ AZERTY) : `qwerty` → `azerty` et inversement.
En mode latin, un mini-sélecteur de sens apparaît dans la page
(l'auto-détection étant impossible entre deux latins) et le bouton
⇄ bascule le sens car les tables sont exactement inverses.

## 2. Usage quotidien (Windows)

Sélectionnez le texte tapé avec le mauvais clavier, puis :

1. `Ctrl+C`
2. Lancez `fix-presse-papiers.bat`
   (astuce : clic droit → *Créer un raccourci* → Propriétés →
   *Touche de raccourci* : `Ctrl+Alt+H`)
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

## 3. Workflow mappings (important)

**Les tables JavaScript de `convertisseur.html` sont la source de vérité.
Ne jamais éditer les tables de `fix-presse-papiers.py` à la main.**

Après toute modification des mappings dans le HTML :

```sh
python gen_maps.py
python test_maps.py
```

`test_maps.py` compare les 4 tables (ordre + valeurs), détecte les clés
dupliquées et rejoue 5 cas connus (`qkuo`/`akuo` → `שלום`, etc.).
Exit `0` = synchronisé, `1` = dérive.

## Historique

Voir `git log`. Premier commit : page + réglages + script presse-papiers
+ générateur/test de mappings.
