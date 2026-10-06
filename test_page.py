# -*- coding: utf-8 -*-
"""Tests d'integrite de la page (structure, i18n, offline, version).

Usage : python test_page.py   (exit 0 = OK, exit 1 = probleme)
"""
import re
import shutil
import subprocess
import sys
import tempfile
import os

REQUIRED_IDS = ['input', 'output', 'detect', 'stats', 'swap', 'clear', 'copy',
                'openSettings', 'closeSettings', 'doneSettings', 'resetSettings',
                'settingsPanel', 'settingsOverlay', 'optLive', 'optAutocopy',
                'optRemember', 'heExamples', 'latinExamples', 'latinSeg']

results = []


def check(name, cond, detail=''):
    results.append((name, bool(cond), detail))


def main():
    with open('convertisseur.html', encoding='utf-8') as f:
        h = f.read()

    # 1. 100 % local : aucune ressource http(s) externe
    ext = re.findall(r'''(?:src|href)\s*=\s*["'](https?://[^"']+|//[^"']+)["']''', h)
    check('aucune ressource externe', not ext, str(ext))

    # 2. tous les ids requis existent
    missing = [i for i in REQUIRED_IDS if 'id="%s"' % i not in h]
    check('ids requis presents', not missing, str(missing))

    # 3. i18n : cles utilisees couvertes, jeux identiques fr/en/he
    used = set(re.findall(r'data-i18n="([^"]+)"', h))
    used |= set(re.findall(r'data-i18n-ph="([^"]+)"', h))
    used |= set(re.findall(r'data-i18n-aria="([^"]+)"', h))
    used |= set(re.findall(r'data-i18n-title="([^"]+)"', h))
    js = h.split('<script>')[1]
    used |= set(re.findall(r"""\bt\('(\w+)'\)""", js))
    used -= {'fieldset', 'textarea'}  # artefacts : createElement('...'), closest('...')
    starts = {m.group(1): m.start() for m in re.finditer(r'\n  (fr|en|he): \{', h)}
    order = ['fr', 'en', 'he']
    langs = {}
    for i, lang in enumerate(order):
        s = starts[lang]
        e = starts[order[i + 1]] if i + 1 < len(order) else len(h)
        seg = h[s:e]
        seg = seg.split('const DEFAULTS')[0]
        langs[lang] = set(re.findall(r'[{,]\s*(\w+):', seg))
    check('i18n cles couvertes', all(not (used - langs[l]) for l in order),
          str({l: sorted(used - langs[l]) for l in order}))
    check('i18n jeux identiques', langs['fr'] == langs['en'] == langs['he'],
          str({l: len(langs[l]) for l in order}))

    # 4. garde-fous structurels (non-regressions corrigees par le passe)
    check('panneau RTL ouvrable', 'html[dir="rtl"] #settingsPanel.open' in h)
    check('hidden prioritaire', '[hidden] { display: none !important; }' in h)
    check('7 groupes de reglages',
          h.count('<fieldset>') == 7 and h.count('<legend') == 7,
          '%d fieldset' % h.count('<fieldset>'))
    check('sortie hebreu alignee a droite', '.out[dir="rtl"]' in h)

    # 5. syntaxe JS (si node disponible)
    if shutil.which('node'):
        m = re.findall(r'<script>(.*?)</script>', h, re.S)
        with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False,
                                         encoding='utf-8') as f:
            f.write(m[0])
            tmp = f.name
        r = subprocess.run(['node', '--check', tmp], capture_output=True)
        os.unlink(tmp)
        check('syntaxe JS (node --check)', r.returncode == 0)
    else:
        check('syntaxe JS (node absent, ignore)', True, 'sans node')

    # 6. version APP_VERSION alignee sur le tag git
    m = re.search(r"const APP_VERSION = '([^']+)'", h)
    try:
        tag = subprocess.run(['git', 'describe', '--tags', '--abbrev=0'],
                             capture_output=True, text=True, check=True)
        tag = tag.stdout.strip().lstrip('v')
        check('version == tag git', m and m.group(1) == tag,
              'page=%s tag=%s' % (m.group(1) if m else '?', tag))
    except Exception as e:
        check('version == tag git (git indisponible, ignore)', True, str(e)[:80])

    ok = True
    for name, passed, *rest in results:
        if not passed:
            ok = False
        print(('PASS ' if passed else 'FAIL ') + name
              + (' [%s]' % rest[0] if rest and rest[0] else ''))
    print('PAGE-OK' if ok else 'PAGE-FAIL')
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
