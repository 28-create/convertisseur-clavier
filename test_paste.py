# -*- coding: utf-8 -*-
"""Test du guetteur de presse-papiers (paste_watch.py) et de son
integration Windows : detection prudente, modele hebreu genere, parite
avec la page, demarrage automatique dans les deux installateurs.

Aucune dependance Windows : le module est importable sous Linux pour la CI
(le crochet clavier n'est installe qu'au demarrage reel).

Usage : python test_paste.py   (exit 0 = OK, exit 1 = derive detectee)
"""
import base64
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys

import gen_ngrams
import paste_watch

ROOT = os.path.dirname(os.path.abspath(__file__))
results = []


def check(name, cond, detail=''):
    results.append((name, bool(cond), detail))
    print('%s %s %s' % ('PASS' if cond else 'FAIL', name, detail))


def read(name):
    with open(os.path.join(ROOT, name), encoding='utf-8') as f:
        return f.read()


def load_fix():
    path = os.path.join(ROOT, 'fix-presse-papiers.py')
    spec = importlib.util.spec_from_file_location('fix_pp_paste', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def model_checks():
    src = read('paste_watch.py')
    block = re.search(r'# <he_model:generated>[\s\S]*?# </he_model:generated>',
                      src)
    check('bloc modele hebreu present', bool(block))
    check('alphabet hebreu identique au generateur',
          paste_watch.HE_ALPHA == gen_ngrams.HE_ALPHA)
    check('quantification hebreu identique au generateur',
          (paste_watch.HE_SCALE, paste_watch.HE_OFFSET)
          == (gen_ngrams.HE_SCALE, gen_ngrams.HE_OFFSET))
    try:
        raw = base64.b64decode(paste_watch.HE_B64)
    except Exception:
        raw = b''
    check('modele hebreu decodable',
          len(raw) == len(paste_watch.HE_ALPHA) ** 2,
          '%d/%d' % (len(raw), len(paste_watch.HE_ALPHA) ** 2))
    sha = gen_ngrams.HE_SOURCES[0][2]
    check('source hebreu epinglee par SHA-256',
          sha == 'd105307feb42da018e2b6713247c3256f7ac4273a2f269e0f0fc1fd69bb7d903'
          and gen_ngrams.HE_SOURCES[0][1].startswith('https://www.gutenberg.org/'),
          sha[:16])


def page_model_checks(html):
    models = paste_watch.load_models(html)
    check('deux modeles latins lus dans la page',
          sorted(models['latin']) == ['en', 'fr'],
          str(sorted(models['latin'])))
    check('alphabet latin de la page',
          len(models['alpha']) ** 2
          == len(models['latin']['fr']) == len(models['latin']['en']))
    return models


def node_checks(html, models):
    node = shutil.which('node')
    if not node:
        check('parite page/guetteur (node absent, ignore)', True, 'sans node')
        return
    mblk = re.search(r'// <models:generated>[\s\S]*?// </models:generated>',
                     html)
    mnorm = re.search(r'function normalizeForModel\(s\) \{[\s\S]*?\n\}', html)
    mscore = re.search(r'function scoreLang\(text, lang\) \{[\s\S]*?\n\}',
                       html)
    mread = re.search(r'function scoreReading\(text\) \{[\s\S]*?\n\}', html)
    if not (mblk and mnorm and mscore and mread):
        check('parite page/guetteur (extraction impossible)', False)
        return
    samples = ['bonjour', 'qkuo', 'Caf\u00e9  \u2019\u0153uf',
               'hello world', 'abc', 'x', '\u00c9L\u00c8VE']
    prog = (mblk.group(0) + '\nconst modelCache = {};\n'
            + mnorm.group(0) + '\n'
            + mscore.group(0) + '\n' + mread.group(0) + '\n'
            'console.log(JSON.stringify(%s.map(s => '
            '[normalizeForModel(s), scoreReading(s)])));\n'
            % json.dumps(samples, ensure_ascii=True))
    r = subprocess.run([node, '-e', prog], capture_output=True, text=True,
                       encoding='utf-8', errors='replace')
    try:
        got = json.loads((r.stdout or '').strip())
    except Exception as e:
        check('parite page/guetteur (node)', False, str(e)[:140])
        return
    expected = [[paste_watch.normalize_latin(s, models['alpha']),
                 paste_watch.score_latin(models, s)] for s in samples]
    ok = len(got) == len(expected)
    detail = ''
    if ok:
        for (gn, gs), (en, es) in zip(got, expected):
            if gn != en:
                ok = False
                detail = 'normalisation %r != %r' % (gn, en)
                break
            if (gs is None) != (es is None):
                ok = False
                detail = 'score nul %r/%r' % (gs, es)
                break
            if gs is not None and abs(gs - es) > 1e-9:
                ok = False
                detail = 'score %r != %r' % (gs, es)
                break
    check('parite page/guetteur (node)', ok, detail[:140])


def detection_checks(models, fix):
    cases = [
        ('qkuo', 'toHe', 'azerty', '\u05e9\u05dc\u05d5\u05dd'),
        ('akuo', 'toHe', 'qwerty', '\u05e9\u05dc\u05d5\u05dd'),
        ('QKUO', 'toHe', 'azerty', '\u05e9\u05dc\u05d5\u05dd'),
        ('qkuo!', 'toHe', 'azerty', '\u05e9\u05dc\u05d5\u05dd.'),
        ('\u05e0\u05dd\u05de\u05d7\u05dd\u05d5\u05e8', 'toFr', 'azerty',
         'bonjour'),
    ]
    for text, direction, layout, target in cases:
        r = paste_watch.detect_text(text, models, fix)
        check('detection %s' % ascii(text),
              bool(r) and r['direction'] == direction
              and r['layout'] == layout and r['text'] == target,
              '' if not r else '%s/%s %s' % (r['direction'], r['layout'],
                                            ascii(r['text'])))
        if r:
            check('source conservee %s' % ascii(text),
                  r['source_text'] == text)

    keeps = [
        'bonjour', 'bonsoir', 'merci', 'salut', 'hello', 'hello world',
        'bonne nuit', 'il fait beau', 'Mimran', 'Jean', 'Paris', 'the',
        'azerty', 'qwerty', 'sdfgh', 'fghj', 'wxcv',
        '\u05e9\u05dc\u05d5\u05dd',
        '\u05d1\u05d5\u05e7\u05e8 \u05d8\u05d5\u05d1',
        '\u05de\u05e8\u05d1\u05d9', '\u05d4\u05dc\u05dc\u05d5',
        'https://example.com', 'user@example.com', 'C:\\Users\\x',
        'const x = 1;', 'a/b', 'test123', 'abc', 'ok',
        'bonjour \u05e9\u05dc\u05d5\u05dd', '', '   ', None,
    ]
    for text in keeps:
        check('pas de proposition %s' % ascii(text),
              paste_watch.detect_text(text, models, fix) is None)
    check('texte trop long ignore',
          paste_watch.detect_text('bonjour ' * 600, models, fix) is None)


def installer_checks():
    iss = read('installer.iss')
    for tok in ('--paste-watch', '--paste-stop',
                'CurrentVersion\\Run', 'Tasks: surveillance',
                '[UninstallRun]', 'PrepareToInstall'):
        check('installer.iss : %s' % tok, tok in iss)
    ps = read('installer.ps1')
    for tok in ('--paste-watch', '--paste-stop', 'CurrentVersion\\Run',
                '-SansSurveillance', 'RunName'):
        check('installer.ps1 : %s' % tok, tok in ps)
    des = read('desinstaller.ps1')
    for tok in ('--paste-stop', 'CurrentVersion\\Run', 'RunName'):
        check('desinstaller.ps1 : %s' % tok, tok in des)
    bs = read('build_setup.py')
    for tok in ('--paste-watch', '--paste-stop', 'surveillance'):
        check('build_setup.py : %s' % tok, tok in bs)
    be = read('build_exe.py')
    check('build_exe.py embarque app.ico',
          'ICON + os.pathsep' in be)
    check('build_exe.py embarque paste_watch/win32_clip',
          be.count('--hidden-import') >= 2
          and 'paste_watch' in be and 'win32_clip' in be)
    ap = read('app.py')
    check('app.py : verbes de surveillance',
          '--paste-watch' in ap and '--paste-stop' in ap)
    test = read('test_installer.ps1')
    check('test_installer.ps1 verifie la valeur Run',
          '--paste-watch' in test and 'RunName' in test)
    priv = read('PRIVACY.md').lower()
    check('PRIVACY.md couvre la surveillance',
          'surveillance avant' in priv and 'guetteur' in priv)
    page = read('confidentialite.html').lower()
    check('page confidentialite couvre la surveillance',
          'surveillance avant' in page and 'guetteur' in page)


def main():
    html = read('convertisseur.html')
    fix = load_fix()
    model_checks()
    models = page_model_checks(html)
    detection_checks(models, fix)
    node_checks(html, models)
    installer_checks()

    ok = all(passed for _name, passed, _detail in results)
    print('OK : surveillance du presse-papiers' if ok
          else 'ECHEC : voir ci-dessus')
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
