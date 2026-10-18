# Description longue (FR)

> À coller dans le champ « Description » de la fiche du store (limite :
> 16 000 caractères). Le Markdown y est affiché comme du texte brut : les
> puces et les titres restent lisibles.

Vous avez tapé un message en hébreu… avec le clavier resté en français (ou
l'inverse) ? Ce qui devait être `שלום` s'affiche `qkuo`. Le Convertisseur
Clavier répare le texte sur place, sans copier-coller dans un autre outil.

**Fonctionne dans les deux sens**, avec les claviers AZERTY et QWERTY :

- hébreu → latin et latin → hébreu ;
- AZERTY ⇄ QWERTY (texte latin tapé sur le mauvais clavier).

## Trois façons de convertir

- **Clic droit dans la page** — sélectionnez du texte : *Convertir la
  sélection* (sens détecté), *Convertir en hébreu* ou *Convertir en latin*.
  Dans un champ (`input`, `textarea`, zone éditable), le texte est remplacé
  sur place et reste annulable par `Ctrl+Z` ; ailleurs, le résultat est copié
  et affiché dans une notification.
- **`Ctrl+Maj+H`** — convertit la sélection du champ actif, où que vous soyez
  dans la page.
- **Popup de l'extension** — collez ou tapez du texte, le résultat se met à
  jour pendant la frappe ; bouton *Copier*. Vous y choisissez le mode
  (automatique, vers l'hébreu, vers le latin, AZERTY ⇄ QWERTY) et le clavier.

## 100 % local, aucune donnée collectée

Les conversions sont calculées dans votre navigateur, à partir de tables
embarquées : **aucun serveur, aucun compte, aucune statistique, aucune
publicité, aucune requête réseau**. Le presse-papiers n'est utilisé que lorsque
vous déclenchez une conversion ; vos réglages restent sur votre machine
(`chrome.storage.local`). Détail complet :
https://28-create.github.io/convertisseur-clavier/confidentialite.html

## Le même outil, partout

Le site https://28-create.github.io/convertisseur-clavier/ propose la même page
en version web (rien à installer), et une application Windows sait en plus
convertir le presse-papiers partout — y compris dans Word, un logiciel de
messagerie ou la barre de recherche Windows — avec `Ctrl+Alt+H`.

## Limites

- L'extension n'agit que dans les pages web : les menus de Word, des
  applications de bureau et de Windows appartiennent à ces programmes.
- Les pages `chrome://`, `edge://`, le Chrome Web Store et le lecteur PDF
  n'autorisent pas les extensions à lire la page.
- La barre d'outils de Firefox n'est pas prise en charge (version Chrome / Edge,
  Chromium).

## Mots-clés

convertisseur clavier, hébreu, ivrit, AZERTY, QWERTY, disposition, frappe,
clavier hébreu, conversion de texte, offline, local.
