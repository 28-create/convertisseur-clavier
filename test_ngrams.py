# -*- coding: utf-8 -*-
"""Evaluation anti-regression de la detection de lecture (FR/EN <-> HE).

Principe : on simule une frappe avec la mauvaise disposition, puis on verifie
que detect_text retrouve le texte d'origine. Tout est calcule avec les tables
et les modeles du depot : aucun acces reseau, aucun corpus externe.

La comparaison se fait par similarite (>= SIMILARITY) et non par egalite
stricte : l'aller-retour des tables n'est pas parfait pour la ponctuation
(FR '.' -> tav -> ';' par exemple), et une phrase correctement detectee peut
donc differer de la cible sur un signe.

Le script affiche un taux par sens et echoue (exit 1) si un plancher est
franchi a la baisse. Les planchers sont volontairement un peu sous la mesure
courante : ils detectent une regression, pas une variation de modele.
"""
import difflib
import importlib.util
import io
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))

# Similarite minimale entre le texte rendu et la cible attendue.
SIMILARITY = 0.92

# Planchers mesures sur la base trigrammes (modernisation, v1.12.5).
FLOOR = {
    'latin_to_he': 0.90,
    'he_to_fr': 0.90,
    'he_to_en': 0.90,
}

# Corpus de reference (eval/corpus.json) : 100 FR + 100 EN + 80 HE.
# Mesure du 22 oct. 2026 : 93.8 / 93.8 / 95.0 / 99.0 %, 0 faux positif,
# 0 KEEPS propose. Planchers volontairement un peu sous cette mesure.
CORPUS_FLOOR = {
    'latin_to_he|azerty': 0.92,
    'latin_to_he|qwerty': 0.92,
    'he_to_fr|azerty': 0.93,
    'he_to_en|qwerty': 0.97,
}

# Phrases latines : (langue, texte, disposition de l'utilisateur).
# Les dernieres lignes couvrent la ponctuation, k/w et les chiffres : ce sont
# les cas que les penalites de disposition ont casses (point -> ';', chiffre
# colle, k/w). Elles doivent rester detectees.
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
    ('fr', 'il est parti ce matin. nous le verrons demain.', 'azerty'),
    ('fr', 'le week-end, nous marchions au bord du lac.', 'azerty'),
    ('fr', 'le 14 juillet, il y avait 200 personnes.', 'azerty'),
    ('fr', "c'est un long voyage; il durera trois jours.", 'azerty'),
    ('en', 'hello world', 'qwerty'),
    ('en', 'the quick brown fox jumps over the lazy dog', 'qwerty'),
    ('en', 'we know the answer', 'qwerty'),
    ('en', 'work in progress', 'qwerty'),
    ('en', 'thank you very much', 'qwerty'),
    ('en', 'what a wonderful day', 'qwerty'),
    ('en', 'keep walking forward', 'qwerty'),
    ('en', 'i like this book', 'qwerty'),
    ('en', "the meeting starts at 9 o'clock. don't be late.", 'qwerty'),
    # Le 'a' isole devient '/' avec la disposition hebraique : il ne doit pas
    # faire rejeter la lecture (penalite des caracteres rares retiree en toFr).
    ('fr', "il a dit a son ami qu'il partait demain matin", 'azerty'),
    ('fr', 'il a dit "bonjour" a tous les enfants du village', 'azerty'),
]

# Mots et phrases hebreu : (texte, disposition utilisee pour la frappe).
# La derniere phrase contient un nombre suivi d'une virgule : le retour de la
# virgule en tsadi forme "2009צ", ce qui ne doit pas faire rejeter la lecture.
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
    ('\u05d1\u05e9\u05e0\u05ea 2009, \u05d4\u05e7\u05d1\u05d5\u05e6\u05d4 '
     '\u05d6\u05db\u05ea\u05d4 \u05d1\u05e4\u05e8\u05e1.', 'azerty'),
    # Mot etranger integre : il doit rester en latin dans la proposition.
    ('iOS \u05d4\u05d9\u05d0 \u05de\u05e2\u05e8\u05db\u05ea \u05d4\u05e4\u05e2\u05dc\u05d4',
     'azerty'),
    ('\u05de\u05e2\u05e8\u05db\u05ea \u05d4\u05d4\u05e4\u05e2\u05dc\u05d4 macOS '
     '\u05d4\u05d9\u05d0', 'azerty'),
    # Signes naturels (% et &) : ils ne doivent plus rejeter le texte.
    ('\u05d4\u05e9\u05d9\u05e2\u05d5\u05e8 \u05d4\u05d5\u05d0 50 % '
     '\u05de\u05d4\u05ea\u05dc\u05de\u05d9\u05d3\u05d9\u05dd', 'azerty'),
    ('\u05d4\u05d7\u05d1\u05e8\u05d4 AT&T \u05d2\u05d3\u05dc\u05d4', 'azerty'),
    # Guillemets hebreux : normaux, ils ne sont pas penalises.
    ('\u05d4\u05d5\u05d0 \u05d0\u05de\u05e8 "\u05e9\u05dc\u05d5\u05dd" '
     '\u05dc\u05db\u05d5\u05dc\u05dd', 'azerty'),
]

# Textes deja corrects : la detection ne doit rien proposer.
KEEPS = [
    'bonjour', 'merci', 'hello', 'Paris', 'Mimran',
    '\u05e9\u05dc\u05d5\u05dd', '\u05d1\u05d5\u05e7\u05e8 \u05d8\u05d5\u05d1',
    'https://example.com', 'user@example.com', 'C:\\Users\\x',
    'const x = 1;', 'a/b', 'abc', 'ok',
    'le week-end', 'il est 9 heures.',
    "c'est un long voyage; il durera trois jours.",
    'nous avons 200 personnes.',
    '#hashtag', 'AT&T', 'C++', '50 %', 'user_name',
]


def load_module(name, filename):
    spec = importlib.util.spec_from_file_location(name, os.path.join(ROOT, filename))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def ascii_text(value):
    return ascii(value)[1:-1] if isinstance(value, str) else repr(value)


def similar(a, b):
    return difflib.SequenceMatcher(None, a or '', b or '').ratio()


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
        ok = bool(got) and got['direction'] == 'toHe' and similar(got['text'], heb) >= SIMILARITY
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
        ok = bool(got) and got['direction'] == 'toFr' and similar(got['text'], text) >= SIMILARITY
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

    # 5. Corpus de reference : les quatre sens, puis la prudence.
    corpus_eval = load_module('eval_detection', os.path.join('eval', 'eval_detection.py'))
    corpus_stats, corpus_fp, corpus_keeps = corpus_eval.evaluate(
        paste_watch, fix, models)
    for key in sorted(CORPUS_FLOOR):
        item = corpus_stats[key]
        rate = float(item['ok']) / item['total']
        ok = rate >= CORPUS_FLOOR[key]
        print('%s corpus %-18s %d/%d (%.1f%%) plancher %.0f%%' % (
            'PASS' if ok else 'FAIL', key, item['ok'], item['total'],
            100.0 * rate, 100.0 * CORPUS_FLOOR[key]))
        if not ok:
            failures.append('corpus %s : %d/%d sous le plancher %.0f%%' % (
                key, item['ok'], item['total'], 100.0 * CORPUS_FLOOR[key]))
    ok = not corpus_fp
    print('%s corpus faux positifs %d' % ('PASS' if ok else 'FAIL', len(corpus_fp)))
    if not ok:
        failures.append('corpus : %d faux positif(s)' % len(corpus_fp))
    ok = not corpus_keeps
    print('%s corpus KEEPS proposes %d' % ('PASS' if ok else 'FAIL', len(corpus_keeps)))
    if not ok:
        failures.append('corpus : %d texte(s) deja correct(s) propose(s)' % len(corpus_keeps))

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
