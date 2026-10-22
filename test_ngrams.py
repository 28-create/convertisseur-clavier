# -*- coding: utf-8 -*-
"""Evaluation anti-regression de la detection de lecture (FR/EN <-> HE).

Principe : on simule une frappe avec la mauvaise disposition, puis on verifie
que detect_text retrouve le texte d'origine. Tout est calcule avec les tables
et les modeles du depot : aucun acces reseau, aucun corpus externe.

Le script affiche un taux par sens et echoue (exit 1) si un plancher est
franchi a la baisse. Les planchers sont volontairement un peu sous la mesure
courante : ils detectent une regression, pas une variation de modele.
"""
import importlib.util
import io
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))

# Planchers mesures sur la base trigrammes (modernisation, v1.12.5).
FLOOR = {
    'latin_to_he': 0.90,
    'he_to_fr': 0.90,
    'he_to_en': 0.90,
}

# Phrases latines : (langue, texte, disposition de l'utilisateur).
LATIN_CASES = [
    ('fr', 'bonjour tout le monde', 'azerty'),
    ('fr', "j'ai deux chats", 'azerty'),
    ('fr', "aujourd'hui il fait beau", 'azerty'),
    ('fr', "l'ecole est ouverte", 'azerty'),
    ('fr', 'je ne sais pas', 'azerty'),
    ('fr', "quelqu'un m'a dit", 'azerty'),
    ('fr', 'le 11 septembre', 'azerty'),
    ('fr', 'nous avons 2 enfants', 'azerty'),
    ('fr', 'merci beaucoup pour votre aide', 'azerty'),
    ('fr', 'demain nous partons ensemble', 'azerty'),
    ('en', 'hello world', 'qwerty'),
    ('en', 'the quick brown fox jumps over the lazy dog', 'qwerty'),
    ('en', 'we know the answer', 'qwerty'),
    ('en', 'work in progress', 'qwerty'),
    ('en', 'thank you very much', 'qwerty'),
    ('en', 'what a wonderful day', 'qwerty'),
    ('en', 'keep walking forward', 'qwerty'),
    ('en', 'i like this book', 'qwerty'),
]

# Mots et phrases hebreu : (texte, disposition utilisee pour la frappe).
HEBREW_CASES = [
    ('\u05e9\u05dc\u05d5\u05dd', 'azerty'),              # shalom
    ('\u05ea\u05d5\u05d3\u05d4 \u05e8\u05d1\u05d4', 'azerty'),  # toda raba
    ('\u05d1\u05d5\u05e7\u05e8 \u05d8\u05d5\u05d1', 'azerty'),  # boker tov
    ('\u05de\u05d4 \u05e9\u05dc\u05d5\u05de\u05da', 'azerty'),  # ma shlomkha
    ('\u05d0\u05e0\u05d9 \u05dc\u05d5\u05de\u05d3', 'azerty'),  # ani lomed
    ('\u05e1\u05e4\u05e8 \u05ea\u05d5\u05e8\u05d4', 'azerty'),  # sefer tora
    ('\u05d1\u05d9\u05ea \u05db\u05e0\u05e1\u05ea', 'azerty'),  # beit kneset
    ('\u05dc\u05d9\u05dc\u05d4 \u05d8\u05d5\u05d1', 'azerty'),  # laila tov
    ('\u05d0\u05d1\u05d0 \u05d5\u05d0\u05de\u05d0', 'azerty'),  # aba ve-ima
    ('\u05d4\u05e9\u05de\u05e9 \u05d6\u05d5\u05e8\u05d7\u05ea', 'azerty'),  # hashemesh zorachat
]

# Textes deja corrects : la detection ne doit rien proposer.
KEEPS = [
    'bonjour', 'merci', 'hello', 'Paris', 'Mimran',
    '\u05e9\u05dc\u05d5\u05dd', '\u05d1\u05d5\u05e7\u05e8 \u05d8\u05d5\u05d1',
    'https://example.com', 'user@example.com', 'C:\\Users\\x',
    'const x = 1;', 'a/b', 'abc', 'ok',
]


def load_module(name, filename):
    spec = importlib.util.spec_from_file_location(name, os.path.join(ROOT, filename))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def ascii_text(value):
    return ascii(value)[1:-1] if isinstance(value, str) else repr(value)


def main():
    paste_watch = load_module('paste_watch', 'paste_watch.py')
    fix = load_module('fix_pp', 'fix-presse-papiers.py')
    html = io.open(os.path.join(ROOT, 'convertisseur.html'), encoding='utf-8').read()
    models = paste_watch.load_models(html)

    failures = []
    stats = {'latin_to_he': [0, 0], 'he_to_fr': [0, 0], 'he_to_en': [0, 0]}
    details = []

    # 1. Latin -> HE : l'utilisateur voulait de l'hebreu et a frappe en latin.
    #    La source est la suite de touches (peu lisible), la cible est l'hebreu.
    for heb, layout in HEBREW_CASES:
        source = paste_watch.convert_for_layout(heb, layout, 'toFr', fix)
        got = paste_watch.detect_text(source, models, fix, layout)
        key = 'latin_to_he'
        stats[key][1] += 1
        ok = bool(got) and got['direction'] == 'toHe' and got['text'] == heb
        if ok:
            stats[key][0] += 1
        else:
            failures.append('%s: %s -> %s' % (
                key, ascii_text(source),
                'None' if not got else ascii_text(got['text'])))
        details.append('%s %-11s %s' % ('PASS' if ok else 'FAIL', key, ascii_text(heb)))

    # 2. HE -> latin : l'utilisateur voulait du latin et a frappe en hebreu.
    #    La source est le texte hebreu produit par la frappe ; la cible est
    #    la phrase latine d'origine.
    for lang, text, layout in LATIN_CASES:
        source = paste_watch.convert_for_layout(text, layout, 'toHe', fix)
        got = paste_watch.detect_text(source, models, fix, layout)
        key = 'he_to_%s' % lang
        stats[key][1] += 1
        ok = bool(got) and got['direction'] == 'toFr' and got['text'] == text
        if ok:
            stats[key][0] += 1
        else:
            failures.append('%s: %s -> %s' % (
                key, ascii_text(text),
                'None' if not got else ascii_text(got['text'])))
        details.append('%s %-11s %s' % ('PASS' if ok else 'FAIL', key, ascii_text(text)))

    # 4. Textes deja corrects : aucune proposition.
    for text in KEEPS:
        got = paste_watch.detect_text(text, models, fix)
        ok = got is None
        if not ok:
            failures.append('keep: %s -> %s' % (ascii_text(text), ascii_text(got['text'])))
        details.append('%s %-8s %s' % ('PASS' if ok else 'FAIL', 'keep', ascii_text(text)))

    rates = {}
    for key, (ok, total) in stats.items():
        rate = (float(ok) / total) if total else 1.0
        rates[key] = rate
        print('%s %-11s %d/%d (%.0f%%) plancher %.0f%%' % (
            'PASS' if rate >= FLOOR[key] else 'FAIL',
            key, ok, total, 100.0 * rate, 100.0 * FLOOR[key]))
    if '--verbose' in sys.argv:
        for line in details:
            print('  ' + line)

    for failure in failures:
        print('FAIL ' + failure)

    if failures or any(rates[k] < FLOOR[k] for k in FLOOR):
        print('NGRAMS-ECHEC')
        return 1
    print('NGRAMS-OK')
    return 0


if __name__ == '__main__':
    sys.exit(main())
