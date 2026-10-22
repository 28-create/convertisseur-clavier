# -*- coding: utf-8 -*-
"""Evalue la detection de lecture sur le corpus de reference (280 textes).

Usage :
  python eval/eval_detection.py            (resume par sens)
  python eval/eval_detection.py --details  (8 echecs par sens)

Le corpus est fige dans eval/corpus.json : 100 phrases francaises, 100
anglaises et 80 hebraiques. On simule une frappe avec la mauvaise disposition,
puis on verifie que detect_text retrouve le texte d'origine (similarite >= 0.92).
Les textes deja corrects ne doivent produire aucune proposition (faux positifs).
Aucun acces reseau.
"""
import difflib
import importlib.util
import io
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORPUS_PATH = os.path.join(ROOT, 'eval', 'corpus.json')

ACCENTS = {
    '\u0153': 'oe', '\u00e6': 'ae', '\u00e0': 'a', '\u00e2': 'a',
    '\u00e4': 'a', '\u00e7': 'c', '\u00e9': 'e', '\u00e8': 'e',
    '\u00ea': 'e', '\u00eb': 'e', '\u00ee': 'i', '\u00ef': 'i',
    '\u00f4': 'o', '\u00f6': 'o', '\u00f9': 'u', '\u00fb': 'u',
    '\u00fc': 'u', '\u00c0': 'A', '\u00c2': 'A', '\u00c7': 'C',
    '\u00c9': 'E', '\u00c8': 'E', '\u00ca': 'E', '\u00ce': 'I',
    '\u00cf': 'I', '\u00d4': 'O', '\u00d9': 'U', '\u00db': 'U',
    '\u00dc': 'U',
}

KEEPS = [
    'bonjour', 'merci', 'hello', 'Paris', 'Mimran',
    '\u05e9\u05dc\u05d5\u05dd',
    '\u05d1\u05d5\u05e7\u05e8 \u05d8\u05d5\u05d1',
    'https://example.com', 'user@example.com', 'C:\\Users\\x',
    'const x = 1;', 'a/b', 'abc', 'ok', 'test123',
    '#hashtag', 'AT&T', 'C++', '50 %', 'user_name',
    'bonjour \u05e9\u05dc\u05d5\u05dd',
]


def load_module(name, filename):
    path = os.path.join(ROOT, filename)
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def fold(text):
    return ''.join(ACCENTS.get(ch, ch) for ch in text)


def load_corpus(path=CORPUS_PATH):
    with io.open(path, encoding='utf-8') as f:
        corpus = json.load(f)
    for key in ('fr', 'en', 'he'):
        if key not in corpus or not corpus[key]:
            raise ValueError('corpus incomplet : %s' % key)
    return corpus


def evaluate(pw, fix, models, corpus=None):
    """Rejoue les quatre sens et renvoie (stats, faux positifs, KEEPS)."""
    corpus = corpus if corpus is not None else load_corpus()
    stats = {}
    for key, sentences, wanted, layout in (
            ('latin_to_he|azerty', corpus['he'], 'toHe', 'azerty'),
            ('latin_to_he|qwerty', corpus['he'], 'toHe', 'qwerty'),
            ('he_to_fr|azerty', corpus['fr'], 'toFr', 'azerty'),
            ('he_to_en|qwerty', corpus['en'], 'toFr', 'qwerty')):
        ok = 0
        details = []
        for text in sentences:
            if key.startswith('latin_to_he'):
                source = pw.convert_for_layout(text, layout, 'toFr', fix)
                target = text
            else:
                source = pw.convert_for_layout(fold(text), layout, 'toHe', fix)
                target = fold(text)
            got = pw.detect_text(source, models, fix, layout)
            if got and got['direction'] == wanted:
                ratio = difflib.SequenceMatcher(None, got['text'], target).ratio()
                if ratio >= 0.92:
                    ok += 1
                else:
                    details.append((ratio, got['text'], target))
            else:
                details.append((0.0, '' if not got else got['text'], target))
        stats[key] = {
            'ok': ok,
            'total': len(sentences),
            'wrong': len(sentences) - ok,
            'details': details,
        }

    false_positives = []
    for lang in ('fr', 'en', 'he'):
        for text in corpus[lang]:
            got = pw.detect_text(text, models, fix)
            if got:
                false_positives.append((lang, text, got['text']))

    keeps_bad = [text for text in KEEPS if pw.detect_text(text, models, fix)]
    return stats, false_positives, keeps_bad


def main():
    paste_watch = load_module('paste_watch', 'paste_watch.py')
    fix = load_module('fix_pp', 'fix-presse-papiers.py')
    with io.open(os.path.join(ROOT, 'convertisseur.html'), encoding='utf-8') as f:
        models = paste_watch.load_models(f.read())

    stats, false_positives, keeps_bad = evaluate(paste_watch, fix, models)
    for key, item in stats.items():
        print('%-18s %3d/%d (%5.1f%%)  sous 0.92=%d' % (
            key, item['ok'], item['total'],
            100.0 * item['ok'] / item['total'], item['wrong']))
        if '--details' in sys.argv:
            for ratio, got, target in item['details'][:8]:
                print('   %.2f  %s' % (ratio, ascii(got)[:70]))
                print('         cible %s' % ascii(target)[:70])
    print('faux positifs corpus : %d' % len(false_positives))
    for lang, text, got in false_positives[:5]:
        print('  ', lang, ascii(text)[:60], '->', ascii(got)[:40])
    print('KEEPS proposes : %d' % len(keeps_bad))
    for text in keeps_bad:
        print('  ', ascii(text))

    return 0 if not false_positives and not keeps_bad else 1


if __name__ == '__main__':
    sys.exit(main())
