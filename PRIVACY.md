# Politique de confidentialité — Convertisseur Clavier

Dernière mise à jour : 18 octobre 2026

Version en ligne : <https://28-create.github.io/convertisseur-clavier/confidentialite.html>

Cette politique couvre les trois façons d'utiliser le Convertisseur Clavier :

| Support | Fichier / paquet |
|---|---|
| Page web | `convertisseur.html` (et le site GitHub Pages) |
| Application Windows | `ConvertisseurClavier-X.Y.Z.exe`, `Setup_ConvertisseurClavier-X.Y.Z.exe` |
| Extension navigateur | dossier `extension/` (Chrome / Edge) |

## En une phrase

Aucune donnée ne sort de votre appareil : ni serveur, ni compte, ni
statistique, ni publicité, ni traceur.

## Données collectées

**Aucune.** Le Convertisseur Clavier ne collecte, ne transmet, ne vend et ne
partage aucune donnée personnelle. Il ne demande ni compte, ni adresse e-mail,
ni identifiant.

## Ce qui est traité, et où

- Les conversions sont calculées **localement** (dans la page, dans
  l'application ou dans l'extension), à partir de tables embarquées.
- Le **presse-papiers** n'est lu et écrit que sur une action explicite de votre
  part : `Ctrl+Alt+H` dans l'application, ou le menu clic droit de l'extension.
- Aucun texte converti n'est journalisé, envoyé, ni conservé après l'opération.

## Ce qui est stocké sur votre appareil

| Support | Stockage local |
|---|---|
| Page web | réglages et historique de la session (`localStorage`) |
| Extension | réglages de mode et de clavier (`chrome.storage.local`) |
| Application | rien en dehors de vos propres fichiers |

Ces données ne quittent pas votre machine. Vous les effacez en vidant les
données du site, en désinstallant l'extension, ou en supprimant
`%LOCALAPPDATA%\Programs\ConvertisseurClavier`.

## Permissions de l'extension

| Permission | Pourquoi |
|---|---|
| `contextMenus` | ajouter l'entrée « Convertir la sélection » au clic droit |
| `clipboardWrite` | copier le résultat quand le texte n'est pas dans un champ |
| `storage` | mémoriser vos réglages (mode, clavier) en local |
| accès aux pages (`content_scripts`) | lire la sélection et remplacer le texte dans le champ actif, **uniquement** quand vous déclenchez la conversion |

L'extension ne contient **aucun code distant** et n'émet **aucune requête
réseau**.

## Hébergement et tiers

La page web est publiée par **GitHub Pages**. Comme tout hébergeur, GitHub peut
journaliser techniquement les requêtes HTTP (adresse IP, agent utilisateur)
pour fournir et protéger le service ; nous n'avons pas accès à ces journaux et
n'en tirons aucune statistique. Voir la
[politique de confidentialité de GitHub](https://docs.github.com/fr/site-policy/privacy-policies/github-privacy-statement).
Aucun autre tiers n'intervient : pas de régie publicitaire, pas d'outil de
mesure d'audience, pas de police d'écriture distante.

## Vos droits (RGPD)

Aucune donnée personnelle n'étant traitée, il n'y a rien à consulter, corriger,
exporter ou supprimer. Pour toute question, ouvrez une *issue* sur le dépôt.

## Modifications

Toute évolution de cette politique sera publiée dans ce fichier et sur la page
`confidentialite.html`, avec la date de mise à jour ci-dessus.

---

## Privacy policy (English)

Last updated: 18 October 2026

The Convertisseur Clavier (web page, Windows application, browser extension)
collects **no data at all**. Conversions are computed locally from embedded
tables; nothing is sent anywhere. There is no server, no account, no analytics,
no advertising and no tracker.

- **Clipboard**: read and written only when you explicitly trigger a conversion
  (`Ctrl+Alt+H` in the application, or the extension's right-click menu).
- **Stored on your device**: your settings (`localStorage` in the page,
  `chrome.storage.local` in the extension). Clearing site data or uninstalling
  removes them.
- **Extension permissions**: `contextMenus` (add the right-click entry),
  `clipboardWrite` (copy the result), `storage` (remember your settings) and
  page access via `content_scripts` (read the selection and replace the text in
  the active field, only when you ask for it). No remote code, no network
  request.
- **Hosting**: the web page is served by GitHub Pages, which may keep standard
  technical request logs; we have no access to them. No other third party is
  involved.
- **Your rights**: since no personal data is processed, there is nothing to
  access or delete. For any question, open an issue on the repository.

## Contact

<https://github.com/28-create/convertisseur-clavier/issues>
