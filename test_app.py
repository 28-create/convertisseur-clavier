# -*- coding: utf-8 -*-
"""Test anti-derive de app.py : lecture des fichiers texte (encodages
Windows), injection du contenu precharge (menu clic droit / touche), et
verbes CLI reutilises par l'installeur.

Le prechargement a deja regresse une fois : WebView2 refuse une URL
file://...?text=... (il affiche une page d'erreur), d'ou l'injection du
texte apres chargement (voir app.preload_js).

Usage : python test_app.py   (exit 0 = OK, exit 1 = derive detectee)
"""
import importlib.util
import json
import os
import re
import shutil
import sys
import tempfile

import app

results = []


def check(name, cond, detail=''):
    results.append((name, bool(cond), detail))
    print('%s %s %s' % ('PASS' if cond else 'FAIL', name, detail))


def load_fix():
    spec = importlib.util.spec_from_file_location(
        'fix_pp', 'fix-presse-papiers.py')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    ok = True

    # 1. lecture des fichiers : UTF-8 (BOM ou non), cp1255 (hebreu ANSI
    #    Windows), cp1252 (Bloc-notes FR). Un fichier hebreu cp1255 doit
    #    se lire comme de l'hebreu, pas comme du cp1252 accentue.
    cases = [
        ('utf8.txt', 'nous avons mang\u00e9', 'utf-8', 'utf-8'),
        ('utf8bom.txt', '\u05e9\u05dc\u05d5\u05dd \u05e2\u05d5\u05dc\u05dd',
         'utf-8-sig', 'utf-8-bom'),
        ('he1255.txt', '\u05e0\u05dd\u05de\u05d7\u05dd\u05d5\u05e8',
         'cp1255', 'cp1255'),
        ('fr1252.txt', '\u00e9l\u00e8ve fran\u00e7ais \u0153uvre',
         'cp1252', 'cp1252'),
    ]
    tmp = tempfile.mkdtemp(prefix='conv_app_')
    try:
        for name, txt, enc, label in cases:
            path = os.path.join(tmp, name)
            with open(path, 'wb') as f:
                f.write(txt.encode(enc))
            check('lecture %s' % label, app.read_text_file(path) == txt)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    # 2. injection : json.dumps (ensure_ascii) doit rendre un litteral JS
    #    sur (guillemets, antislash, </script>, sauts de ligne, U+2028) et
    #    l'appel de doConvert() doit couvrir le mode sans conversion directe.
    durs = ['a"b', "c'd", 'e\\f', '</script>', 'l1\nl2', 'u\u2028v', '']
    for t in durs:
        js = app.preload_js(t)
        m = re.search(r'i\.value = ("(?:[^"\\]|\\.)*");', js)
        check('injection %s' % ascii(t),
              bool(m) and json.loads(m.group(1)) == t
              and 'doConvert()' in js and '?text=' not in js)

    # 3. verbes CLI (formes exactes du menu clic droit / des touches)
    ap = app.build_parser()
    a = ap.parse_args(['--convert-file', 'x.txt', '--layout', 'qwerty'])
    check('verbe --convert-file',
          a.convert_file == 'x.txt' and a.layout == 'qwerty')
    b = ap.parse_args(['C:\\un\\fichier.txt'])
    check('verbe fichier (ouvrir)',
          b.fichier.endswith('fichier.txt') and not b.convert_file)
    c = ap.parse_args(['--convert-clipboard', '--direction', 'toFr'])
    check('verbe --convert-clipboard',
          c.convert_clipboard and c.direction == 'toFr')
    d = ap.parse_args(['--paste-watch'])
    check('verbe --paste-watch', d.paste_watch and not d.paste_stop)
    e = ap.parse_args(['--paste-stop'])
    check('verbe --paste-stop', e.paste_stop and not e.paste_watch)

    # 4. conversion via fix-presse-papiers.py (source unique, aucune table
    #    dupliquee dans app.py)
    mod = load_fix()
    out, tag = app.convert_text(mod, 'nous', 'azerty', 'auto', 'hebrew', 'toAz')
    check('conversion FR->HE',
          bool(out) and all('\u0590' <= ch <= '\u05ff' for ch in out),
          '%s %s' % (tag, ascii(out)))
    lat, tag = app.convert_text(mod, 'qkuo', 'azerty', 'auto', 'latin', 'toAz')
    check('conversion QWERTY->AZERTY',
          lat == mod.convert('qkuo', mod.LATIN_MAPS['toAz']) and lat != 'qkuo',
          '%s %s' % (tag, ascii(lat)))

    for name, passed, *_ in results:
        if not passed:
            ok = False
    print('OK : app.py (lecture, injection, verbes)' if ok
          else 'ECHEC : voir ci-dessus')
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
