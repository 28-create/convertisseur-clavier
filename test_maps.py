# -*- coding: utf-8 -*-
"""Test anti-derive : les tables de fix-presse-papiers.py doivent etre
identiques a celles de convertisseur.html (regenerer via gen_maps.py).

Usage : python test_maps.py   (exit 0 = OK, exit 1 = derive detectee)
"""
import importlib.util
import json
import re
import shutil
import subprocess
import sys

from gen_maps import MAP_NAMES, parse_js_maps


def _safe(o):
    # affichage anti-crash sur consoles Windows (cp1252/cp1255)
    return ascii(o)


def load_fix():
    spec = importlib.util.spec_from_file_location(
        'fix_pp', 'fix-presse-papiers.py')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def run_js_smart(js_maps, cases):
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
        'const SWAP = {Q:"A",A:"Q",W:"Z",Z:"W"};\n'
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


def main():
    with open('convertisseur.html', encoding='utf-8') as f:
        js_maps = parse_js_maps(f.read())
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
        ('azerty', 'toFr', 'M.', 'M.'),
        ('azerty', 'toFr', 'abc 123', 'abc 123'),
        ('azerty', 'toFr', 'שלום2024', 'qkuoéàé\''),
        ('azerty', 'toHe', 'bonjour', 'נםמחםור'),
        ('azerty', 'toHe', 'bonjour שלום', 'נםמחםור שלום'),
        ('qwerty', 'toFr', 'Bםמחםור', 'Bonjour'),
        ('qwerty', 'toFr', 'Hello, נםמחםור !', 'Hello, bonjour !'),
    ]
    tables = {'azerty': (dict(js_maps['FR_TO_HE']), dict(js_maps['HE_TO_FR'])),
              'qwerty': (dict(js_maps['EN_TO_HE']), dict(js_maps['HE_TO_EN'])),
              'latin': (dict(js_maps['QW_TO_AZ']), dict(js_maps['AZ_TO_QW']))}
    swap_az = {'Q': 'A', 'A': 'Q', 'W': 'Z', 'Z': 'W'}
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
    got_js = run_js_smart(js_maps, smart_cases)
    if got_js is None:
        print('SMART-JS ignore (node indisponible)')
    else:
        for (layout, direction, src, exp), status in zip(smart_cases, got_js):
            if status != 'OK':
                ok = False
                print('SMART-JS %s %s %s -> %s (attendu %s)'
                      % (layout, direction, _safe(src), _safe(status), _safe(exp)))
    for layout, direction, src, exp in cases:
        to_he, to_fr = tables[layout]
        if layout == 'latin':
            table = to_he if direction == 'toAz' else to_fr
        else:
            table = to_fr if direction == 'toFr' else to_he
        got = ''.join(table.get(c, c) for c in src)
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
    for ch in core:
        if aq.get(qa.get(ch, ch), qa.get(ch, ch)) != ch:
            ok = False
            print('NON-REVERSIBLE QW->AZ->QW: %r' % ch)
        if qa.get(aq.get(ch, ch), aq.get(ch, ch)) != ch:
            ok = False
            print('NON-REVERSIBLE AZ->QW->AZ: %r' % ch)
    print('OK : mappings synchronises (%s)' % ', '.join(
        '%s=%d' % (n, len(js_maps[n])) for n in MAP_NAMES) if ok else 'ECHEC : voir ci-dessus')
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
