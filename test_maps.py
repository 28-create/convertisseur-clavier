# -*- coding: utf-8 -*-
"""Test anti-derive : les tables de fix-presse-papiers.py doivent etre
identiques a celles de convertisseur.html (regenerer via gen_maps.py).

Usage : python test_maps.py   (exit 0 = OK, exit 1 = derive detectee)
"""
import importlib.util
import sys

from gen_maps import MAP_NAMES, parse_js_maps


def load_py_maps():
    spec = importlib.util.spec_from_file_location(
        'fix_pp', 'fix-presse-papiers.py')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return {n: list(getattr(mod, n).items()) for n in MAP_NAMES}


def main():
    with open('convertisseur.html', encoding='utf-8') as f:
        js_maps = parse_js_maps(f.read())
    py_maps = load_py_maps()
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
            print('DERIVE %s : seulement-HTML=%r seulement-PY=%r conflits=%r'
                  % (name, only_js, only_py, clash))
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
    ]
    tables = {'azerty': (dict(js_maps['FR_TO_HE']), dict(js_maps['HE_TO_FR'])),
              'qwerty': (dict(js_maps['EN_TO_HE']), dict(js_maps['HE_TO_EN']))}
    for layout, direction, src, exp in cases:
        to_he, to_fr = tables[layout]
        got = ''.join((to_fr if direction == 'toFr' else to_he).get(c, c) for c in src)
        if got != exp:
            ok = False
            print('REGRESSION %s %s %r -> %r (attendu %r)' % (layout, direction, src, got, exp))
    print('OK : mappings synchronises (%s)' % ', '.join(
        '%s=%d' % (n, len(js_maps[n])) for n in MAP_NAMES) if ok else 'ECHEC : voir ci-dessus')
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
