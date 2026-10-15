# -*- coding: utf-8 -*-
"""Tests d'integrite de la page (structure, i18n, offline, version).

Usage : python test_page.py   (exit 0 = OK, exit 1 = probleme)
"""
import re
import shutil
import subprocess
import sys
import tempfile
import json
import os

REQUIRED_IDS = ['input', 'output', 'detect', 'stats', 'swap', 'clear', 'copy',
                'openSettings', 'closeSettings', 'doneSettings', 'resetSettings',
                'settingsPanel', 'settingsOverlay', 'optLive', 'optAutocopy',
                'optRemember', 'optHistory', 'heExamples', 'latinExamples', 'latinSeg',
                'historyBox', 'historyList', 'historyClear', 'historyEmpty',
                'layoutSuggest', 'suggestText', 'suggestPreview', 'suggestApply',
                'suggestDismiss']

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
    starts = {}
    for m in re.finditer(r'^\s*(fr|en|he): \{', h, re.M):
        starts.setdefault(m.group(1), m.start())
    order = ['fr', 'en', 'he']
    langs = {}
    texts = {}
    for i, lang in enumerate(order):
        s = starts[lang]
        e = starts[order[i + 1]] if i + 1 < len(order) else len(h)
        seg = h[s:e]
        seg = seg.split('const DEFAULTS')[0]
        langs[lang] = set(re.findall(r'[{,]\s*(\w+):', seg))
        texts[lang] = {k: (v1 or v2) for k, v1, v2 in re.findall(
            r"([A-Za-z]\w*):\s*(?:'((?:[^'\\]|\\.)*)'|\"((?:[^\"\\]|\\.)*)\")",
            seg)}
    check('i18n cles couvertes', all(not (used - langs[l]) for l in order),
          str({l: sorted(used - langs[l]) for l in order}))
    check('i18n jeux identiques', langs['fr'] == langs['en'] == langs['he'],
          str({l: len(langs[l]) for l in order}))
    bad_ph = []
    for key in sorted(texts['fr']):
        if key not in texts['en'] or key not in texts['he']:
            continue
        ph = {l: set(re.findall(r'\{(\w+)\}', texts[l][key])) for l in order}
        if not (ph['fr'] == ph['en'] == ph['he']):
            bad_ph.append(key)
    check('i18n placeholders identiques', not bad_ph, str(bad_ph))

    # 4. garde-fous structurels (non-regressions corrigees par le passe)
    check('panneau RTL ouvrable', 'html[dir="rtl"] #settingsPanel.open' in h)
    check('hidden prioritaire', '[hidden] { display: none !important; }' in h)
    check('7 groupes de reglages',
          h.count('<fieldset>') == 7 and h.count('<legend') == 7,
          '%d fieldset' % h.count('<fieldset>'))
    check('sortie hebreu alignee a droite', '.out[dir="rtl"]' in h)
    mpanel = re.search(r'<aside id="settingsPanel"[^>]*>', h)
    check('panneau inerte quand ferme',
          bool(mpanel) and ' inert' in mpanel.group(0)
          and 'panel.inert = false' in h and 'panel.inert = true' in h)
    ids = re.findall(r'\bid="([^"]+)"', h)
    dupes = sorted({i for i in ids if ids.count(i) > 1})
    check('ids uniques', not dupes, str(dupes))
    check('un seul bloc script',
          h.count('<script>') == 1 and h.count('</script>') == 1)
    check('meta CSP presente', 'http-equiv="Content-Security-Policy"' in h)

    # 4b. migration des reglages : fonction pure extraite, rejouee sous node
    if shutil.which('node'):
        mdef = re.search(r'const DEFAULTS = \{.*?\};', h, re.S)
        mfun = re.search(
            r'function migrateSettings\(stored, legacy\) \{[\s\S]*?\n\}', h)
        if not (mdef and mfun):
            check('migration reglages testable', False, 'extraction impossible')
        else:
            cases = [
                [{'lang': 'fr'}, None, {'lang': 'auto', 'mig1': True}, True],
                [{'lang': 'fr', 'mig1': True}, None, {'lang': 'fr'}, False],
                [{'lang': 'he'}, None, {'lang': 'he', 'mig1': True}, True],
                [{'lang': 'xx'}, None, {'lang': 'auto'}, True],
                [{'mode': 'zzz', 'latinDir': 'nope'}, None,
                 {'mode': 'hebrew', 'latinDir': 'toAz'}, True],
                [None, {'layout': 'qwerty', 'autocopy': '1'},
                 {'layout': 'qwerty', 'autocopy': True, 'mig1': True}, True],
                [None, None, {'layout': 'azerty', 'mig1': True}, False],
            ]
            prog = (mdef.group(0) + '\n' + mfun.group(0) + '\n'
                    'const cases = ' + json.dumps(cases, ensure_ascii=True) + ';\n'
                    'let bad = 0;\n'
                    'cases.forEach((c, i) => {\n'
                    '  const r = migrateSettings(c[0], c[1]);\n'
                    '  let ok = r.changed === c[3];\n'
                    '  for (const k of Object.keys(c[2]))'
                    ' if (r.settings[k] !== c[2][k]) ok = false;\n'
                    '  if (!ok) { bad++; console.log("FAIL " + i + " "'
                    ' + JSON.stringify(r)); }\n'
                    '});\n'
                    'console.log(bad === 0 ? "OK" : "FAIL");\n')
            r = subprocess.run(['node', '-e', prog], capture_output=True,
                               text=True, encoding='utf-8', errors='replace')
            out = (r.stdout or '') + (r.stderr or '')
            check('migration reglages (node)',
                  r.returncode == 0 and (r.stdout or '').strip().endswith('OK'),
                  out.strip()[:120])
    else:
        check('migration reglages (node absent, ignore)', True, 'sans node')

    # 4c. historique : helpers purs extraits, rejoues sous node
    if shutil.which('node'):
        mcut = re.search(r'HIST_CUT = (\d+)', h)
        mh1 = re.search(r'function histInput\(text\) \{[^\n]*\}', h)
        mh2 = re.search(r'function isHistDup\(history, text\) \{[^\n]*\}', h)
        if not (mcut and mh1 and mh2):
            check('helpers historique testables', False, 'extraction impossible')
        else:
            prog = ('const HIST_CUT = ' + mcut.group(1) + ';\n'
                    + mh1.group(0) + '\n' + mh2.group(0) + '\n'
                    'const long = "a".repeat(HIST_CUT + 100);\n'
                    'const head = [{ i: histInput("hello") }];\n'
                    'const r = [\n'
                    '  histInput("abc") === "abc",\n'
                    '  histInput(long).length === HIST_CUT,\n'
                    '  isHistDup(head, "hello") === true,\n'
                    '  isHistDup(head, "hello!") === false,\n'
                    '  isHistDup([], "x") === false,\n'
                    '  isHistDup([{ i: histInput(long) }], long) === true\n'
                    '];\n'
                    'console.log(r.every(Boolean) ? "OK" : "FAIL");\n')
            r = subprocess.run(['node', '-e', prog], capture_output=True,
                               text=True, encoding='utf-8', errors='replace')
            out = (r.stdout or '') + (r.stderr or '')
            check('historique helpers (node)',
                  r.returncode == 0 and (r.stdout or '').strip().endswith('OK'),
                  out.strip()[:120])
    else:
        check('historique helpers (node absent, ignore)', True, 'sans node')

    # 4d. suggestion de lecture : fonctions pures + modeles rejoues sous node
    if shutil.which('node'):
        from gen_maps import parse_js_maps
        mm = {
            'block': re.search(r'// <models:generated>[\s\S]*?// </models:generated>', h),
            'norm': re.search(r'function normalizeForModel\(s\) \{[\s\S]*?\n\}', h),
            'lang': re.search(r'function scoreLang\(text, lang\) \{[\s\S]*?\n\}', h),
            'read': re.search(r'function scoreReading\(text\) \{[\s\S]*?\n\}', h),
            'sugg': re.search(
                r'function suggestReading\(text, currentLayout\) \{[\s\S]*?\n\}', h),
            'cv': re.search(
                r'function convertSmart\(text, fullMap, swapCaps, toFrench\)'
                r' \{[\s\S]*?\n\}', h),
            'maps': re.search(r'const MAPS = \{[\s\S]*?\n\};', h),
            'caps': re.search(r'const CAPS_SWAP = [^\n]*;', h),
            'cache': re.search(r'const modelCache = \{\};', h),
            'minh': re.search(r'const SUGGEST_MIN_HEB = \d+;', h),
            'marg': re.search(r'const SUGGEST_MARGIN = [\d.]+;', h),
        }
        missing = sorted(k for k, m in mm.items() if not m)
        if missing:
            check('suggestion lecture testable', False, str(missing))
        else:
            tables = parse_js_maps(h)
            # Assemblage dans l'ORDRE DU FICHIER : un bug d'ordre de
            # declaration (TDZ) dans la page se reproduit ici.
            ordered = [m.group(0) for _k, m in
                       sorted(mm.items(), key=lambda kv: kv[1].start())]
            prologue = '\n'.join(
                ['const %s = %s;' % (n, json.dumps(dict(tables[n]), ensure_ascii=True))
                 for n in ('FR_TO_HE', 'HE_TO_FR', 'EN_TO_HE', 'HE_TO_EN')]
                + ordered)
            ex = 'הרשןצקמא ב,קדא מ,ןצפםראק /וםן בקאאק יןדאםןרק'
            fr_az = 'nous avons mangé une délicieuse tarte aux pommes'
            en_qw = 'we should call the plumber tomorrow morning'
            t_fr_az = ''.join(dict(tables['FR_TO_HE']).get(c, c) for c in fr_az)
            t_en_qw = ''.join(dict(tables['EN_TO_HE']).get(c, c) for c in en_qw)
            cases = [
                [ex, 'azerty', 'qwerty'],
                [ex, 'qwerty', None],
                ['שלום', 'azerty', None],
                ['qkuo', 'azerty', None],
                [t_fr_az, 'qwerty', 'azerty'],
                [t_en_qw, 'azerty', 'qwerty'],
            ]
            prog = (prologue + '\nconst cases = %s;\n'
                    % json.dumps(cases, ensure_ascii=True)
                    + 'const out = cases.map(c => {\n'
                    '  const r = suggestReading(c[0], c[1]);\n'
                    '  return r ? {layout: r.layout, margin: r.margin,'
                    ' preview: r.preview} : null;\n'
                    '});\n'
                    'console.log("SUGGEST:" + JSON.stringify(out));\n')
            r = subprocess.run(['node', '-e', prog], capture_output=True,
                               text=True, encoding='utf-8', errors='replace')
            out_s = (r.stdout or '').strip()
            if r.returncode != 0 or 'SUGGEST:' not in out_s:
                check('suggestion lecture (node)', False,
                      ((r.stdout or '') + (r.stderr or '')).strip()[:140])
            else:
                got = json.loads(out_s.split('SUGGEST:', 1)[1])
                mrg = float(re.search(r'SUGGEST_MARGIN = ([\d.]+)', h).group(1))
                bad = []
                for (src, cur, exp), g in zip(cases, got):
                    gl = g['layout'] if g else None
                    if gl != exp:
                        bad.append('attendu=%s obtenu=%s' % (exp, gl))
                    elif g and g['margin'] < mrg:
                        bad.append('marge faible %.3f' % g['margin'])
                if got[0] and not got[0]['preview'].startswith('vraiment'):
                    bad.append('apercu=' + str(got[0]['preview'])[:40])
                check('suggestion lecture (node)', not bad, '; '.join(bad)[:140])
    else:
        check('suggestion lecture (node absent, ignore)', True, 'sans node')

    # 4e. normalisation identique entre la page et gen_ngrams.py
    if shutil.which('node'):
        import gen_ngrams
        mblk = re.search(r'// <models:generated>[\s\S]*?// </models:generated>', h)
        mnorm = re.search(r'function normalizeForModel\(s\) \{[\s\S]*?\n\}', h)
        if not (mblk and mnorm):
            check('normalisation testable', False, 'extraction impossible')
        else:
            samples = ['Café  \u2019\u0153uf\u2026  ÉTÉ ', 'a\tb\nc', 'x',
                       'ÀBÇ 12', 'a\u2014b', '  espaces   multiples  ']
            prog = (mblk.group(0) + '\n' + mnorm.group(0) + '\n'
                    'console.log(JSON.stringify(%s.map(s => normalizeForModel(s))));\n'
                    % json.dumps(samples, ensure_ascii=True))
            r = subprocess.run(['node', '-e', prog], capture_output=True,
                               text=True, encoding='utf-8', errors='replace')
            detail = ''
            norm_ok = False
            try:
                got_n = json.loads((r.stdout or '').strip())
                exp_n = [gen_ngrams.normalize(s) for s in samples]
                norm_ok = got_n == exp_n
                if not norm_ok:
                    detail = str(list(zip(exp_n, got_n)))[:140]
            except Exception as e:
                detail = str(e)[:140]
            check('normalisation page/script identique', norm_ok, detail)
    else:
        check('normalisation (node absent, ignore)', True, 'sans node')

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

    # 6. version APP_VERSION alignee sur le tag git ; en CI (fetch-depth: 0)
    # un echec git/tag est une vraie erreur, pas un skip silencieux.
    m = re.search(r"const APP_VERSION = '([^']+)'", h)
    try:
        tag = subprocess.run(['git', 'describe', '--tags', '--abbrev=0'],
                             capture_output=True, text=True, check=True)
        tag = tag.stdout.strip().lstrip('v')
        check('version == tag git', m and m.group(1) == tag,
              'page=%s tag=%s' % (m.group(1) if m else '?', tag))
    except Exception as e:
        if os.environ.get('GITHUB_ACTIONS'):
            check('version == tag git (git/tag indisponible en CI)', False,
                  str(e)[:80])
        else:
            check('version == tag git (git indisponible, ignore)', True,
                  str(e)[:80])

    # 7. contrastes WCAG AA (texte normal >= 4.5, cf. audit oct. 2026)
    css = h.split('<style>')[1].split('</style>')[0]

    def _lum(hexcode):
        hexcode = hexcode.strip().lstrip('#')
        r, g, b = [int(hexcode[i:i + 2], 16) / 255 for i in (0, 2, 4)]
        f = lambda c: c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
        return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)

    def _ratio(a, b):
        la, lb = _lum(a), _lum(b)
        return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)

    themes = {}
    for m in re.finditer(r'(html\[data-theme="dark"\]\s*\{[^}]*\}|:root\s*\{[^}]*\})', css):
        block = m.group(0)
        name = 'dark' if block.lstrip().startswith('html') else 'light'
        themes[name] = dict(re.findall(r'(--[\w-]+):\s*(#[0-9a-fA-F]{6})', block))
    wcag_detail = []
    for theme, vars_ in themes.items():
        for fg, bg in [('text', 'bg'), ('muted', 'bg'), ('text', 'card')]:
            r = _ratio(vars_['--' + fg], vars_['--' + bg])
            if r < 4.5:
                wcag_detail.append('%s %s/%s=%.2f' % (theme, fg, bg, r))
    r_light = _ratio('#ffffff', themes['light']['--accent'])
    r_dark = _ratio('#101725', themes['dark']['--accent'])
    if r_light < 4.5 or r_dark < 4.5:
        wcag_detail.append('bouton light=%.2f dark=%.2f' % (r_light, r_dark))
    check('contraste WCAG AA', not wcag_detail, '; '.join(wcag_detail))
    check('bouton primaire dark en texte sombre',
          'html[data-theme="dark"] button.primary' in css)

    # 8. version_info.txt synchronise avec APP_VERSION (pour --version-file)
    import gen_version
    mver = re.search(r"const APP_VERSION = '([^']+)'", h)
    expect = gen_version.build_info(mver.group(1))
    with open('version_info.txt', encoding='utf-8') as f:
        actual = f.read()
    check('version_info.txt a jour', actual == expect)

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
