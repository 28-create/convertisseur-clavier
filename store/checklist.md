# Publier l'extension sur le store — pas à pas

## 1. Construire le paquet

```sh
python build_extension.py --check   # verifie (version, manifeste, fichiers)
python build_extension.py           # ecrit dist\ConvertisseurClavier-extension-X.Y.Z.zip
```

Le ZIP contient le **contenu** de `extension/`, `manifest.json` à la racine —
c'est le format exigé. Il est écrit dans `dist/` (non versionné).

> Le numéro de version doit **augmenter à chaque envoi**, sinon le store refuse
> le paquet. Il suit `APP_VERSION` (`gen_version.py` synchronise
> `extension/manifest.json`) : passer à la version suivante = éditer
> `APP_VERSION` dans `convertisseur.html`, relancer `python gen_version.py`.

## 2. Images demandées par les stores

| Image | Taille | Obligatoire |
|---|---|---|
| Icône de la fiche | 128×128 PNG | oui (déjà : `extension/icons/icon128.png`) |
| Captures d'écran | 1280×800 **ou** 640×400, 1 à 5 | oui (au moins 1) |
| Petite tuile promotionnelle | 440×280 | fortement recommandée |
| Grande tuile (mise en avant) | 1400×560 | optionnelle |

Pour les captures : charge l'extension, ouvre un onglet, sélectionne un texte
hébreu mal converti, puis capture le **popup** et le **clic droit** en action
(touche `Impr. écran` ou `Win+Maj+S`). Évite les mockups : la revue compare les
images au comportement réel.

## 3. Chrome Web Store

1. Compte développeur : <https://chrome.google.com/webstore/devconsole> —
   **5 $ une seule fois**, et la **validation en deux étapes** du compte Google
   est obligatoire pour publier.
2. **Nouveau contenu** → dépose `dist\ConvertisseurClavier-extension-X.Y.Z.zip`.
3. **Fiche du store** : nom, description courte
   (`store/description-courte-fr.txt`), description longue
   (`store/description-longue-fr.md`), catégorie *Productivité*, langue
   *Français*, puis les images du point 2.
4. **Confidentialité** : reprendre `store/justifications-permissions.md`
   (objectif unique, justification de chaque permission, « aucune donnée
   collectée », URL de la politique de confidentialité).
5. **Distribution** : visibilité *Publique*, pays, et statut **non-commerçant**
   (DSA).
6. **Envoyer pour examen**.

Délais : le plus souvent moins de 24 h, mais un **nouveau développeur** avec
une **nouvelle extension** demandant l'accès à toutes les pages peut attendre
plusieurs jours (jusqu'à ~3 semaines). Au-delà de 3 semaines, écrire au support.

## 4. Edge Add-ons (gratuit)

Même ZIP, via le **Microsoft Partner Center** (> Edge > *Créer une extension*) :
compte Microsoft, gratuit, pas d'adaptation (Chromium MV3). Revue de quelques
jours en général.

## 5. Mises à jour

1. Incrémenter `APP_VERSION`, relancer `python gen_version.py`.
2. `python build_extension.py`.
3. Dashboard → *Paquet* → déposer le nouveau ZIP → *Envoyer pour examen*.

La fiche, les notes de version et les images se modifient sans nouvelle revue ;
seul le code en déclenche une.

## 6. Si c'est refusé

Le courriel indique la politique violée. Les causes les plus probables ici :

| Motif | Correction |
|---|---|
| Accès `<all_urls>` insuffisamment justifié | détailler la justification (déjà rédigée dans `justifications-permissions.md`) |
| Objectif unique pas clair | reprendre la phrase du même fichier, sans élargir |
| Capture d'écran non représentative | refaire une capture réelle du popup / clic droit |
| Politique de confidentialité manquante | vérifier que l'URL Pages répond bien |

Tu peux corriger et resoumettre autant de fois que nécessaire : un rejet n'est
pas une exclusion.

## 7. Rappel des vérifications automatiques

`python test_store.py` contrôle, à chaque push en CI : le manifeste, la
synchronisation de version, la présence des textes de fiche, les limites de
longueur, l'absence de ressource distante dans la page de confidentialité, et
que le ZIP est bien construit avec `manifest.json` à la racine.
