# -*- coding: utf-8 -*-
"""Test anti-derive : les tables de fix-presse-papiers.py doivent etre
identiques a celles de convertisseur.html (regenerer via gen_maps.py).

Usage : python test_maps.py   (exit 0 = OK, exit 1 = derive detectee)
"""
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

from gen_maps import MAP_NAMES, parse_js_maps, parse_caps_swap


def _safe(o):
    # affichage anti-crash sur consoles Windows (cp1252/cp1255)
    return ascii(o)


def load_fix():
    spec = importlib.util.spec_from_file_location(
        'fix_pp', 'fix-presse-papiers.py')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def run_js_smart(js_maps, caps, cases):
    """Execute convertSmart extrait du HTML sous node.
    Rend la liste des resultats, None si node absent,
    leve RuntimeError si l'execution echoue."""
    if not shutil.which('node'):
        return None
    with open('convertisseur.html', encoding='utf-8') as f:
        html = f.read()
    m = re.search(r'function convertSmart\(text, fullMap, swapCaps, toFrench\) \{[\s\S]*?\n\}',
                  html)
    if not m:
        raise RuntimeError('convertSmart introuvable dans convertisseur.html')
    prog = (
        'const MAPS = %s;\n'
        '%s\n'
        'const SWAP = %s;\n'
        'const cases = %s;\n'
        'const esc = s => s.replace(/[^\\x20-\\x7e]/g, c => "\\\\u" + c.codePointAt(0).toString(16).padStart(4, "0"));\n'
        'cases.forEach(([layout, dir, src, exp], i) => {\n'
        '  const toHe = layout === "azerty" ? MAPS.FR_TO_HE : MAPS.EN_TO_HE;\n'
        '  const toFr = layout === "azerty" ? MAPS.HE_TO_FR : MAPS.HE_TO_EN;\n'
        '  const toFrench = dir === "toFr";\n'
        '  const full = toFrench ? toFr : toHe;\n'
        '  const swap = toFrench ? (layout === "azerty" ? SWAP : null) : full;\n'
        '  const got = convertSmart(src, full, swap, toFrench);\n'
        '  console.log(i + ":" + (got === exp ? "OK" : "FAIL:" + esc(got)));\n'
        '});\n'
    ) % (json.dumps({n: dict(js_maps[n]) for n in MAP_NAMES}, ensure_ascii=True),
         m.group(0),
         json.dumps(dict(caps), ensure_ascii=True),
         json.dumps([[l, d, s, e] for l, d, s, e in cases], ensure_ascii=True))
    r = subprocess.run(['node', '-e', prog], capture_output=True, text=True,
                       encoding='utf-8', errors='replace')
    if r.returncode != 0:
        raise RuntimeError('node a echoue : ' + (r.stderr or '').strip()[:200])
    res = {}
    for line in r.stdout.splitlines():
        if ':' in line:
            i, _, status = line.partition(':')
            res[int(i)] = status
    if len(res) != len(cases):
        raise RuntimeError('sortie node incomplete : ' + repr(r.stdout[:200]))
    return [res[i] for i in range(len(cases))]


def run_js_autodir(cases):
    """Execute detectDir extrait du HTML sous node (parite avec autodir).
    Rend la liste des directions, None si node absent."""
    if not shutil.which('node'):
        return None
    with open('convertisseur.html', encoding='utf-8') as f:
        html = f.read()
    m = re.search(r'function detectDir\(text\) \{[\s\S]*?\n\}', html)
    if not m:
        raise RuntimeError('detectDir introuvable dans convertisseur.html')
    prog = ('%s\nconst cases = %s;\n'
            'cases.forEach((t, i) => console.log(i + ":" + detectDir(t)));\n'
            ) % (m.group(0), json.dumps(cases, ensure_ascii=True))
    r = subprocess.run(['node', '-e', prog], capture_output=True, text=True,
                       encoding='utf-8', errors='replace')
    if r.returncode != 0:
        raise RuntimeError('node a echoue : ' + (r.stderr or '').strip()[:200])
    res = {}
    for line in r.stdout.splitlines():
        if ':' in line:
            i, _, status = line.partition(':')
            res[int(i)] = status.strip()
    if len(res) != len(cases) or any(v not in ('toHe', 'toFr') for v in res.values()):
        raise RuntimeError('sortie node incomplete : ' + repr(r.stdout[:200]))
    return [res[i] for i in range(len(cases))]


def run_js_fuzz(js_maps, caps, cases):
    """Execute convertSmart extrait du HTML sous node sur les memes cas que
    le fuzz Python : parite triangulaire page/script/reference.
    Fichier temporaire : la ligne de commande Windows est limitee en taille.
    Rend la liste des index en echec, None si node absent."""
    if not shutil.which('node'):
        return None
    with open('convertisseur.html', encoding='utf-8') as f:
        html = f.read()
    m = re.search(r'function convertSmart\(text, fullMap, swapCaps, toFrench\) \{[\s\S]*?\n\}',
                  html)
    if not m:
        raise RuntimeError('convertSmart introuvable dans convertisseur.html')
    prog = (
        'const MAPS = %s;\n'
        'const CAPS_SWAP = %s;\n'
        '%s\n'
        'const cases = %s;\n'
        'const esc = s => s.replace(/[^\\x20-\\x7e]/g, c => "\\\\u" + c.codePointAt(0).toString(16).padStart(4, "0"));\n'
        'let bad = 0;\n'
        'cases.forEach(([layout, dir, src, exp], i) => {\n'
        '  const toHe = layout === "azerty" ? MAPS.FR_TO_HE : MAPS.EN_TO_HE;\n'
        '  const toFr = layout === "azerty" ? MAPS.HE_TO_FR : MAPS.HE_TO_EN;\n'
        '  const toFrench = dir === "toFr";\n'
        '  const full = toFrench ? toFr : toHe;\n'
        '  const swap = toFrench ? (layout === "azerty" ? CAPS_SWAP : null) : full;\n'
        '  const got = convertSmart(src, full, swap, toFrench);\n'
        '  if (got !== exp) { bad++; console.log("FUZZ-JS " + i + " " + esc(src)); }\n'
        '});\n'
        'console.log(bad === 0 ? "FUZZ-OK" : "FUZZ-FAIL " + bad);\n'
    ) % (json.dumps({n: dict(js_maps[n]) for n in MAP_NAMES}, ensure_ascii=True),
         json.dumps(dict(caps), ensure_ascii=True),
         m.group(0),
         json.dumps(cases, ensure_ascii=True))
    with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False,
                                     encoding='utf-8') as f:
        f.write(prog)
        tmp = f.name
    try:
        r = subprocess.run(['node', tmp], capture_output=True, text=True,
                           encoding='utf-8', errors='replace')
    finally:
        os.unlink(tmp)
    if r.returncode != 0:
        raise RuntimeError('node a echoue : ' + (r.stderr or '').strip()[:200])
    fails = [int(line.split()[1]) for line in r.stdout.splitlines()
             if line.startswith('FUZZ-JS ')]
    if not fails and 'FUZZ-OK' not in r.stdout:
        raise RuntimeError('sortie node incomplete : ' + repr(r.stdout[:200]))
    return fails


def main():
    with open('convertisseur.html', encoding='utf-8') as f:
        html_text = f.read()
    js_maps = parse_js_maps(html_text)
    caps = parse_caps_swap(html_text)
    fix_mod = load_fix()
    py_maps = {n: list(getattr(fix_mod, n).items()) for n in MAP_NAMES}
    ok = True
    for name in MAP_NAMES:
        js_pairs, py_pairs = js_maps[name], py_maps[name]
        if [k for k, _ in js_pairs] != [k for k, _ in py_pairs] or \
           [v for _, v in js_pairs] != [v for _, v in py_pairs]:
            ok = False
            js_d, py_d = dict(js_pairs), dict(py_pairs)
            only_js = [k for k in js_d if k not in py_d]
            only_py = [k for k in py_d if k not in js_d]
            clash = [k for k in js_d if k in py_d and js_d[k] != py_d[k]]
            print('DERIVE %s : seulement-HTML=%s seulement-PY=%s conflits=%s'
                  % (name, _safe(only_js), _safe(only_py), _safe(clash)))
        js_keys = [k for k, _ in js_pairs]
        py_keys = [k for k, _ in py_pairs]
        for label, keys in (('HTML', js_keys), ('PY', py_keys)):
            dupes = sorted({k for k in keys if keys.count(k) > 1})
            if dupes:
                ok = False
                print('DOUBLON %s dans %s : %r' % (name, label, dupes))
    py_caps = list(fix_mod.CAPS_SWAP.items())
    if py_caps != caps:
        ok = False
        print('DERIVE CAPS_SWAP : HTML=%s PY=%s'
              % (_safe(dict(caps)), _safe(dict(py_caps))))
    # garde-fous fonctionnels (non-regression sur des cas connus)
    cases = [
        ('azerty', 'toHe', 'qkuo', 'שלום'),
        ('qwerty', 'toHe', 'akuo', 'שלום'),
        ('azerty', 'toFr', 'שלום', 'qkuo'),
        ('qwerty', 'toFr', 'שלום', 'akuo'),
        ('azerty', 'toFr', 'Bםמחםור', 'Bonjour'),
        ('latin', 'toAz', 'qwerty', 'azerty'),
        ('latin', 'toQw', 'azerty', 'qwerty'),
        ('latin', 'toAz', 'QM?,', 'A?§;'),
    ]
    # batterie texte mixte : memes attendus cote JS (node) et Python (fix)
    smart_cases = [
        ('azerty', 'toFr', 'נםמחםור', 'bonjour'),
        ('azerty', 'toFr', 'Bםמחםור', 'Bonjour'),
        ('azerty', 'toFr', 'Salut, נםמחםור !', 'Salut, bonjour !'),
        ('azerty', 'toFr', "C'est bon נםמחםור", "C'est bon bonjour"),
        ('azerty', 'toFr', 'Appel en 2024 נםמחםור', 'Appel en 2024 bonjour'),
        ('azerty', 'toFr', 'AQ', 'QA'),
        ('azerty', 'toFr', 'APPEL Q R2', 'QPPEL A R2'),
        ('azerty', 'toFr', 'M.', 'M.'),
        ('azerty', 'toFr', 'abc 123', 'abc 123'),
        ('azerty', 'toFr', 'שלום2024', 'qkuoéàé\''),
        ('azerty', 'toHe', 'bonjour', 'נםמחםור'),
        ('azerty', 'toHe', 'bonjour שלום', 'נםמחםור שלום'),
        ('azerty', 'toHe', 'abcש', 'abcש'),
        ('qwerty', 'toFr', 'Bםמחםור', 'Bonjour'),
        ('qwerty', 'toFr', 'Hello, נםמחםור !', 'Hello, bonjour !'),
    ]
    tables = {'azerty': (dict(js_maps['FR_TO_HE']), dict(js_maps['HE_TO_FR'])),
              'qwerty': (dict(js_maps['EN_TO_HE']), dict(js_maps['HE_TO_EN'])),
              'latin': (dict(js_maps['QW_TO_AZ']), dict(js_maps['AZ_TO_QW']))}
    swap_az = dict(caps)
    for layout, direction, src, exp in smart_cases:
        to_he, to_fr = tables[layout]
        to_french = direction == 'toFr'
        full = to_fr if to_french else to_he
        swap = (swap_az if layout == 'azerty' else None) if to_french else full
        got_py = fix_mod.convert_smart(src, full, swap, to_french)
        if got_py != exp:
            ok = False
            print('SMART-PY %s %s %s -> %s (attendu %s)'
                  % (layout, direction, _safe(src), _safe(got_py), _safe(exp)))
    got_js = run_js_smart(js_maps, caps, smart_cases)
    if got_js is None:
        print('SMART-JS ignore (node indisponible)')
    else:
        for (layout, direction, src, exp), status in zip(smart_cases, got_js):
            if status != 'OK':
                ok = False
                print('SMART-JS %s %s %s -> %s (attendu %s)'
                      % (layout, direction, _safe(src), _safe(status), _safe(exp)))
    # parite de detection : page et script doivent choisir le meme sens,
    # y compris avec accents (non-regression : 'abcdéèב' divergeait avant)
    auto_cases = ['abcdéèב', 'café שלום', 'àב', 'שלום', 'bonjour',
                  'BONJOUR שלום', '123 שלום', 'שלום!', 'qkuo', 'שלום2024']
    try:
        got_js_dir = run_js_autodir(auto_cases)
    except RuntimeError as e:
        ok = False
        print('AUTODIR-JS ' + str(e))
        got_js_dir = []
    if got_js_dir is None:
        print('AUTODIR-JS ignore (node indisponible)')
    else:
        for src, js_dir in zip(auto_cases, got_js_dir):
            py_dir = fix_mod.autodir(src)
            if py_dir != js_dir:
                ok = False
                print('DIVERGENCE %s : PY=%s JS=%s'
                      % (_safe(src), py_dir, js_dir))
    for layout, direction, src, exp in cases:
        to_he, to_fr = tables[layout]
        if layout == 'latin':
            table = to_he if direction == 'toAz' else to_fr
        else:
            table = to_fr if direction == 'toFr' else to_he
        got = src.translate(str.maketrans(table))
        if got != exp:
            ok = False
            print('REGRESSION %s %s %s -> %s (attendu %s)' % (layout, direction, _safe(src), _safe(got), _safe(exp)))
    # reversibilite exacte sur le COEUR : caracteres frappables directement
    # sur les deux dispositions. Les touches mono-clavier (ex. é [ \)
    # sont une limite v1 documentee : l'aller est exact, le retour n'est
    # avec perte que pour du texte colle, jamais pour du texte frappe.
    import string
    core = string.ascii_letters + string.digits + " ,;:.!?'\"()-_=+/*%$&"
    qa, aq = dict(js_maps['QW_TO_AZ']), dict(js_maps['AZ_TO_QW'])
    qa_t, aq_t = str.maketrans(qa), str.maketrans(aq)
    for ch in core:
        if ch.translate(qa_t).translate(aq_t) != ch:
            ok = False
            print('NON-REVERSIBLE QW->AZ->QW: %r' % ch)
        if ch.translate(aq_t).translate(qa_t) != ch:
            ok = False
            print('NON-REVERSIBLE AZ->QW->AZ: %r' % ch)
    # fuzz : chemin rapide (sans hebreu) == chemin lent, sur textes aleatoires
    import random
    rng = random.Random(20261015)
    alphabet = ('abcdAQWZ ,;:.!?\'"()-_=+/*%$&0123456789 \t\n'
                'éèçàùâäîïôöûü') + 'שלוםאבג'
    def _slow(text, full_map, swap_caps, to_french):
        parts = re.split(r'(\s+)', text)
        out = []
        for tok in parts:
            if not tok or tok.isspace():
                out.append(tok)
                continue
            has_he = bool(re.search(r'[\u0590-\u05FF]', tok))
            if has_he:
                if not to_french:
                    out.append(tok)
                    continue
            elif to_french:
                if not swap_caps:
                    out.append(tok)
                    continue
                letters = re.sub(r'[^A-Za-z]', '', tok)
                if letters and letters == letters.upper():
                    out.append(''.join(swap_caps.get(ch, ch) for ch in tok))
                else:
                    out.append(tok)
                continue
            out.append(''.join(full_map.get(ch, ch) for ch in tok))
        return ''.join(out)
    fuzz_cases = []
    for trial in range(300):
        t = ''.join(rng.choice(alphabet) for _ in range(rng.randint(0, 120)))
        for layout in ('azerty', 'qwerty'):
            for to_french in (True, False):
                to_he, to_fr = tables[layout]
                full = to_fr if to_french else to_he
                swap = (swap_az if layout == 'azerty' else None) if to_french else full
                a = fix_mod.convert_smart(t, full, swap, to_french)
                b = _slow(t, full, swap, to_french)
                if a != b:
                    ok = False
                    print('FUZZ %s %s %s' % (layout, to_french, _safe(t)))
                    break
                fuzz_cases.append([layout, 'toFr' if to_french else 'toHe', t, a])
    # parite triangulaire : node doit rendre les memes resultats que le
    # chemin Python (lui-meme identique a la reference _slow ci-dessus)
    try:
        fails = run_js_fuzz(js_maps, caps, fuzz_cases)
    except RuntimeError as e:
        ok = False
        fails = []
        print('FUZZ-JS ' + str(e))
    if fails is None:
        print('FUZZ-JS ignore (node indisponible)')
    else:
        for i in fails:
            ok = False
            layout, direction, src, _exp = fuzz_cases[i]
            print('FUZZ-JS %s %s %s' % (layout, direction, _safe(src)))
    print('OK : mappings synchronises (%s)' % ', '.join(
        '%s=%d' % (n, len(js_maps[n])) for n in MAP_NAMES) if ok else 'ECHEC : voir ci-dessus')
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
