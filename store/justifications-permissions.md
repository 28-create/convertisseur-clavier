# Justifications à coller dans le tableau de bord

C'est l'onglet « Confidentialité » qui fait recaler ou retarder une extension :
il faut y justifier **chaque** permission demandée, en une ou deux phrases
concrètes. Les textes ci-dessous sont prêts à copier.

## Objectif unique (Single purpose)

**FR** — Convertisseur Clavier convertit le texte saisi avec la mauvaise
disposition de clavier (AZERTY/QWERTY ⇄ hébreu, AZERTY ⇄ QWERTY). C'est son
seul rôle : aucune autre fonction, aucun autre usage des données.

**EN** — Convertisseur Clavier converts text typed with the wrong keyboard
layout (AZERTY/QWERTY ⇄ Hebrew, AZERTY ⇄ QWERTY). This is its only purpose.

## Justification des permissions

| Permission | Texte à coller (FR / EN) |
|---|---|
| `contextMenus` | **FR** — Ajoute trois entrées au menu clic droit (*Convertir la sélection*, *Convertir en hébreu*, *Convertir en latin*) pour convertir le texte que l'utilisateur vient de sélectionner. Aucune entrée n'est créée pour autre chose.<br>**EN** — Adds three right-click entries (*Convert selection*, *Convert to Hebrew*, *Convert to Latin*) so the user can convert the text they just selected. Nothing else is added. |
| `clipboardWrite` | **FR** — Quand la sélection n'est pas dans un champ modifiable, la conversion ne peut pas remplacer le texte : elle copie alors le résultat dans le presse-papiers, uniquement après un clic ou un raccourci de l'utilisateur.<br>**EN** — When the selection is not inside an editable field, the result cannot replace it in place, so it is copied to the clipboard — only after the user clicks the menu entry or presses the shortcut. |
| `storage` | **FR** — Mémorise localement les deux réglages de l'utilisateur (mode de conversion et disposition du clavier) pour les réutiliser dans le popup et le menu clic droit. Rien n'est synchronisé ni transmis.<br>**EN** — Stores the user's two settings (conversion mode, keyboard layout) locally so the popup and the context menu reuse them. Nothing is synced or transmitted. |
| Accès aux pages — `content_scripts` sur `<all_urls>` | **FR** — Le texte à convertir peut se trouver dans n'importe quel site (webmail, réseau social, forum, outil interne). Le contenu de la page n'est lu **que** sur action explicite de l'utilisateur (clic droit ou `Ctrl+Maj+H`) et sert uniquement à calculer la conversion ; il n'est ni stocké, ni analysé, ni envoyé. L'extension n'injecte aucun script distant et n'utilise ni `eval`, ni `innerHTML`. Si l'accès pouvait être limité, il le serait — mais un convertisseur « de partout » a besoin de `<all_urls>`.<br>**EN** — The text to convert may be in any site (webmail, social network, forum, internal tool). Page content is read **only** when the user explicitly acts (right-click or `Ctrl+Shift+H`) and only to compute the conversion; it is never stored, profiled or sent anywhere. No remote code, no `eval`, no `innerHTML`. If the access could be narrowed, it would be — but an "anywhere" converter needs `<all_urls>`. |

## Onglet « Confidentialité » — réponses

- **Code distant** (*remote code*) : **Non**. Tout le code est dans le paquet ;
  l'extension ne charge et n'exécute rien à distance.
- **Données collectées** : **aucune**. Ne cocher aucune catégorie (ni
  « Informations d'identification », ni « Activité de l'utilisateur », ni
  « Contenu du site »). Aucune donnée n'est transmise à qui que ce soit.
- **Utilisation** : pas de vente, pas de transfert à des tiers, pas d'usage à
  des fins de solvabilité ni de publicité. Les trois certifications
  d'utilisation limitée peuvent être cochées telles quelles.
- **Politique de confidentialité** :
  `https://28-create.github.io/convertisseur-clavier/confidentialite.html`
- **Statut UE (DSA)** : *Non-commerçant* (non-trader), publié à titre gratuit
  par un particulier.

## Ce que l'extension ne fait pas

- aucune requête réseau, aucun `fetch`, aucun `XMLHttpRequest` ;
- aucune police, image ou script distant ;
- aucun cookie, aucun traceur, aucun identifiant d'utilisateur ;
- aucune modification du texte sans action de l'utilisateur.
