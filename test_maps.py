# -*- coding: utf-8 -*-
"""Test anti-derive : les tables de fix-presse-papiers.py doivent etre
identiques a celles de convertisseur.html (regenerer via gen_maps.py).

Usage : python test_maps.py   (exit 0 = OK, exit 1 = derive detectee)
"""
import importlib.util
import sys

from gen_maps import MAP_NAMES, parse_js_maps


def _safe(o):
    # affichage anti-crash sur consoles Windows (cp1252/cp1255)
    return ascii(o)


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
    tables = {'azerty': (dict(js_maps['FR_TO_HE']), dict(js_maps['HE_TO_FR'])),
              'qwerty': (dict(js_maps['EN_TO_HE']), dict(js_maps['HE_TO_EN'])),
              'latin': (dict(js_maps['QW_TO_AZ']), dict(js_maps['AZ_TO_QW']))}
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
