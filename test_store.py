# -*- coding: utf-8 -*-
"""Test du paquet store (Chrome Web Store / Edge) : manifeste et ses limites,
synchronisation de version, fichiers references par le manifeste, textes de la
fiche (longueurs), politique de confidentialite (locale, sans ressource
distante), et construction du ZIP (manifest.json a la racine, reproductible).

Usage : python test_store.py   (exit 0 = OK, exit 1 = probleme)
"""
import json
import os
import re
import shutil
import sys
import tempfile
import zipfile

import build_extension
from gen_version import read_version

MANIFEST = os.path.join('extension', 'manifest.json')
PRIVACY_MD = 'PRIVACY.md'
PRIVACY_HTML = 'confidentialite.html'
STORE = 'store'
PRIVACY_URL = 'https://28-create.github.io/convertisseur-clavier/confidentialite.html'
PERMISSIONS = ['clipboardWrite', 'contextMenus', 'storage']
MAX_LONG = 16000

results = []


def check(name, cond, detail=''):
    results.append(bool(cond))
    print('%s %s %s' % ('PASS' if cond else 'FAIL', name, detail))


def read(path):
    with open(path, encoding='utf-8') as f:
        return f.read()


def png_size(path):
    with open(path, 'rb') as f:
        head = f.read(24)
    if len(head) < 24 or head[:8] != b'\x89PNG\r\n\x1a\n' \
            or head[12:16] != b'IHDR':
        return None
    return (int.from_bytes(head[16:20], 'big'),
            int.from_bytes(head[20:24], 'big'))


def main():
    ver = read_version()

    # --- manifeste et limites du store -------------------------------------
    if not os.path.isfile(MANIFEST):
        check('manifeste present', False, MANIFEST)
        print('ECHEC : voir ci-dessus')
        return 1
    try:
        m = json.loads(read(MANIFEST))
    except ValueError as e:
        check('manifeste JSON valide', False, str(e)[:120])
        print('ECHEC : voir ci-dessus')
        return 1

    check('manifeste JSON valide', True)
    check('version == APP_VERSION', m.get('version') == ver,
          '%s/%s' % (m.get('version'), ver))
    name = m.get('name') or ''
    desc = m.get('description') or ''
    check('nom <= %d caracteres' % build_extension.MAX_NAME,
          bool(name) and len(name) <= build_extension.MAX_NAME,
          '%d' % len(name))
    check('description <= %d caracteres' % build_extension.MAX_DESCRIPTION,
          bool(desc) and len(desc) <= build_extension.MAX_DESCRIPTION,
          '%d' % len(desc))
    icon128 = (m.get('icons') or {}).get('128')
    check('icone 128x128 reelle',
          bool(icon128) and os.path.isfile(os.path.join('extension', icon128))
          and png_size(os.path.join('extension', icon128)) == (128, 128),
          str(icon128))

    # --- textes de la fiche -------------------------------------------------
    for lang in ('fr', 'en'):
        p = os.path.join(STORE, 'description-courte-%s.txt' % lang)
        text = read(p).strip() if os.path.isfile(p) else ''
        check('description courte %s (<= 132)' % lang, 0 < len(text) <= 132,
              '%d car.' % len(text))
        p = os.path.join(STORE, 'description-longue-%s.md' % lang)
        text = read(p).strip() if os.path.isfile(p) else ''
        check('description longue %s (<= %d)' % (lang, MAX_LONG),
              0 < len(text) <= MAX_LONG, '%d car.' % len(text))

    just = os.path.join(STORE, 'justifications-permissions.md')
    text = read(just) if os.path.isfile(just) else ''
    check('justifications presentes', bool(text), just)
    check('justifications : chaque permission',
          all(p in text for p in PERMISSIONS), str(PERMISSIONS))
    check('justifications : acces aux pages', '<all_urls>' in text)
    check('justifications : aucune donnee collectee',
          'aucune' in text.lower() and 'remote code' in text.lower())

    checklist = os.path.join(STORE, 'checklist.md')
    text = read(checklist) if os.path.isfile(checklist) else ''
    check('checklist presente', bool(text), checklist)
    check('checklist : commande de build',
          'build_extension.py' in text and 'test_store.py' in text)

    # --- politique de confidentialite --------------------------------------
    text = read(PRIVACY_MD) if os.path.isfile(PRIVACY_MD) else ''
    check('PRIVACY.md present', bool(text), PRIVACY_MD)
    check('PRIVACY.md : francais et anglais',
          'confidentialit' in text.lower() and 'Privacy policy' in text)
    check('PRIVACY.md : permissions de l extension',
          all(p in text for p in PERMISSIONS))

    html = read(PRIVACY_HTML) if os.path.isfile(PRIVACY_HTML) else ''
    check('confidentialite.html presente', bool(html), PRIVACY_HTML)
    check('page : CSP declaree',
          bool(re.search(r'http-equiv=["\']Content-Security-Policy["\']', html)))
    check('page : francais et anglais',
          'Politique de confidentialit' in html and 'Privacy policy' in html)
    bad = []
    if re.search(r'<script\b', html, re.I):
        bad.append('script')
    if re.search(r'\bsrc\s*=\s*["\']https?://', html, re.I):
        bad.append('src distant')
    if re.search(r'<link\b[^>]*\bhref\s*=\s*["\']https?://', html, re.I):
        bad.append('feuille distante')
    if re.search(r'@import\s+url\(\s*["\']?https?://', html, re.I):
        bad.append('@import distant')
    check('page : rien de distant ni de script', not bad, str(bad))
    local_imgs = re.findall(r'<img\b[^>]*\bsrc\s*=\s*["\']([^"\']+)["\']', html)
    missing = [s for s in local_imgs if not re.match(r'^(https?:|data:)', s)
               and not os.path.isfile(s)]
    check('page : images locales presentes', bool(local_imgs) and not missing,
          str(missing))
    check('page : URL de confidentialite publiee',
          PRIVACY_URL in html or PRIVACY_URL in text)

    # --- paquet -------------------------------------------------------------
    include, skipped = build_extension.package_files()
    check('extension : aucun fichier a nettoyer', not skipped, str(skipped))
    expected = sorted(rel for _src, rel in include)
    check('extension : manifest.json a la racine', 'manifest.json' in expected,
          str(expected[:3]))

    tmp = tempfile.mkdtemp(prefix='store-')
    try:
        zip1, _inc = build_extension.build_zip(os.path.join(tmp, 'a.zip'))
        zip2, _inc = build_extension.build_zip(os.path.join(tmp, 'b.zip'))
        with open(zip1, 'rb') as f1, open(zip2, 'rb') as f2:
            check('paquet reproductible', f1.read() == f2.read())

        with zipfile.ZipFile(zip1) as z:
            names = z.namelist()
            check('paquet : contenu attendu', sorted(names) == expected,
                  '%d fichiers' % len(names))
            check('paquet : pas de dossier parent',
                  not any(n.startswith('extension/') for n in names))
            check('paquet : chemins surs',
                  not any(n.startswith('/') or '..' in n.split('/')
                          for n in names))
            inner = json.loads(z.read('manifest.json').decode('utf-8'))
            check('paquet : version du manifeste',
                  inner.get('version') == ver, str(inner.get('version')))
            wanted = build_extension.manifest_files(inner)
            check('paquet : fichiers references inclus',
                  wanted <= set(names), str(sorted(wanted - set(names))))
            check('paquet : icones incluses',
                  all(n.startswith('icons/') for n in names
                      if n.endswith('.png')), '')
            if z.testzip() is not None:
                check('paquet : archive lisible', False, 'CRC')
            else:
                check('paquet : archive lisible', True)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    ok = all(results)
    print(('OK : store (%d verifications)' % len(results)) if ok
          else 'ECHEC : voir ci-dessus')
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
