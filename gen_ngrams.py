# -*- coding: utf-8 -*-
"""Genere les modeles de n-grammes de suggestion de lecture dans
convertisseur.html (bloc <models:generated>) et paste_watch.py (bloc <he_model:generated>).

Usage :
  python gen_ngrams.py [--corpus-dir DOSSIER] [--order N]
  python gen_ngrams.py --hebrew [--corpus-dir DOSSIER] [--order N]

Ajouter une langue de detection : une entree dans LANGS (code + sources
verifiees par SHA-256), puis relancer. Rien d'autre a toucher : le score,
l'UI et les tests iterent sur les donnees. --hebrew regenere le modele
hebreu de paste_watch.py (guetteur Ctrl+V), separe des modeles latins.

Sources : textes du domaine public (Project Gutenberg, Sefaria), telecharges et
verifies ; --corpus-dir reutilise des fichiers deja presents.
Format emis : table dense ALPHA^ORDER quantifiee en int8, base64 ;
octet -> log-probabilite / MODEL_SCALE - MODEL_OFFSET (nats).
normalize() est le miroir exact de normalizeForModel() dans la page
(test_page.py verifie la parite). Pour l'hebreu, normalize_he() supprime
les points combinants (niqqud, cantillation) au lieu de les remplacer
par des espaces, afin de ne pas couper les mots des textes vocalises.
"""
import argparse
import base64
import hashlib
import math
import os
import re
import sys
import urllib.request

HTML_FILE = 'convertisseur.html'
ALPHA = "abcdefghijklmnopqrstuvwxyz' .,:;!?" + "àâäçéèêëîïôöùûü"
SCALE, OFFSET = 8, 16
BEGIN = '// <models:generated>'
END = '// </models:generated>'
DEFAULT_ORDER = 3  # trigrammes par defaut

# Modele hebreu du guetteur de presse-papiers (paste_watch.py) : alphabet
# separe, donc les modeles latin de la page restent inchanges.
HE_ALPHA = ('\u05d0\u05d1\u05d2\u05d3\u05d4\u05d5\u05d6\u05d7\u05d8\u05d9'
            '\u05db\u05dc\u05de\u05e0\u05e1\u05e2\u05e4\u05e6\u05e7\u05e8'
            '\u05e9\u05ea\u05da\u05dd\u05df\u05e3\u05e5' + " '.,:;!?")
HE_SCALE, HE_OFFSET = 8, 16
HE_FILE = 'paste_watch.py'
HE_BEGIN = '# <he_model:generated>'
HE_END = '# </he_model:generated>'
HE_SOURCES = [
    ('pg5139.txt',
     'https://www.gutenberg.org/cache/epub/5139/pg5139.txt',
     'd105307feb42da018e2b6713247c3256f7ac4273a2f269e0f0fc1fd69bb7d903'),
    # Torah (5 livres) - Tanach with Text Only (non vocalise, domaine public)
    ('tanach_Genesis.txt',
     'https://storage.googleapis.com/sefaria-export/txt/Tanakh/Torah/Genesis/Hebrew/Tanach%20with%20Text%20Only.txt',
     '93369e5ed87944eab99536b46e6bdf127b4c7603dbcda1dcedd6322572c45f78'),
    ('tanach_Exodus.txt',
     'https://storage.googleapis.com/sefaria-export/txt/Tanakh/Torah/Exodus/Hebrew/Tanach%20with%20Text%20Only.txt',
     'c90df9b9c19ba852d1391c2528027d512b99162a01335ca7b085221af0c09980'),
    ('tanach_Leviticus.txt',
     'https://storage.googleapis.com/sefaria-export/txt/Tanakh/Torah/Leviticus/Hebrew/Tanach%20with%20Text%20Only.txt',
     '52af210734a8660045d785690ed8bb88ee8e8f8e02358cc8cf0274acc89d24b4'),
    ('tanach_Numbers.txt',
     'https://storage.googleapis.com/sefaria-export/txt/Tanakh/Torah/Numbers/Hebrew/Tanach%20with%20Text%20Only.txt',
     '2f1e55c8e18ff4d4d1ba7934ae05544d9f8ecddd962461003c47299c73d82bdc'),
    ('tanach_Deuteronomy.txt',
     'https://storage.googleapis.com/sefaria-export/txt/Tanakh/Torah/Deuteronomy/Hebrew/Tanach%20with%20Text%20Only.txt',
     '22fde766d1842a61547a3661a5cfa1ca0de0cf9c08bf6f3054e1ce61ea034c1d'),
    # Talmud Berakhot - Wikisource (non vocalise, domaine public)
    ('talmud_Berakhot.txt',
     'https://storage.googleapis.com/sefaria-export/txt/Talmud/Bavli/Seder%20Zeraim/Berakhot/Hebrew/Wikisource%20Talmud%20Bavli.txt',
     '3993b04529f7db9509dab996d620eea29c1b6015b5791ac9335149fee4afce4e'),
]
LANGS = [
    ('fr', [
        ('pg17489.txt',
         'https://www.gutenberg.org/cache/epub/17489/pg17489.txt',
         'a5de514ba7b9f2e1790e7e259c4e8b7a35ae1d29e4bf9a5f8767039c58b80503'),
        ('pg2600.txt',
         'https://www.gutenberg.org/cache/epub/2600/pg2600.txt',
         '2d5bb2ad5f422765e714617e21fa31bbaf8958aa79682c86fca6660fcc5d1b2b'),
    ]),
    ('en', [
        ('pg11.txt',
         'https://www.gutenberg.org/cache/epub/11/pg11.txt',
         '01b38ea4c710a84bc18d0bd41271a5a1a92b94e97b2812f4dece97d4a694725e'),
        ('pg1661.txt',
         'https://www.gutenberg.org/cache/epub/1661/pg1661.txt',
         '922e2a12ccb43a4c9544c260b2166c6ad2097aeb5957faeee113f173bb857cd0'),
    ]),
]


def normalize(s):
    """Miroir exact de normalizeForModel() dans convertisseur.html."""
    s = s.lower().replace('\u2019', "'").replace('\u0153', 'oe')
    return re.sub(r'\s+', ' ',
                  ''.join(ch if ch in ALPHA else ' ' for ch in s)).strip()


def strip_gutenberg(raw):
    m = re.search(r'\*\*\* START OF[^\n]*\*\*\*', raw)
    if m:
        raw = raw[m.end():]
    m = re.search(r'\*\*\* END OF', raw)
    if m:
        raw = raw[:m.start()]
    return raw


def clean_sefaria(raw):
    """Nettoie les exports Sefaria (HTML, entetes)."""
    raw = re.sub(r'<[^>]+>', ' ', raw)
    raw = re.sub(r'&[a-z]+;', ' ', raw)
    lines = raw.splitlines()
    # Saute l'entete : titre, "merged", URL, notes de version
    start = 0
    for i, ln in enumerate(lines[:20]):
        if len(re.findall(r'[\u05d0-\u05ea]', ln)) > 8:
            start = i
            break
    return [ln for ln in lines[start:] if len(re.findall(r'[\u05d0-\u05ea]', ln)) >= 8]


def fetch_source(name, url, sha, corpus_dir):
    if corpus_dir:
        path = os.path.join(corpus_dir, name)
        try:
            with open(path, 'rb') as f:
                data = f.read()
        except OSError as e:
            raise SystemExit('fichier introuvable ou illisible : %s (%s)'
                             % (path, e.strerror or e))
        origin = path
    else:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=120) as r:
            data = r.read()
        origin = url
    got = hashlib.sha256(data).hexdigest()
    if got != sha:
        raise SystemExit('SHA-256 inattendu pour %s : %s' % (origin, got))
    return data.decode('utf-8', 'replace')


def build_matrix(texts, alpha, norm, order, scale=SCALE, offset=OFFSET):
    """Table dense quantifiee : len(alpha)^order octets.
    order=2 -> bigrammes, order=3 -> trigrammes, etc."""
    counts, tot = {}, {}
    for raw in texts:
        txt = norm(raw)
        for i in range(order - 1, len(txt)):
            ctx = txt[i - order + 1:i]
            ch = txt[i]
            counts[(ctx, ch)] = counts.get((ctx, ch), 0) + 1
            tot[ctx] = tot.get(ctx, 0) + 1
    V = len(alpha) ** order
    out = bytearray()
    # Parcours lexicographique pour ordre deterministe
    def gen_contexts(prefix, depth):
        if depth == 0:
            yield prefix
        else:
            for c in alpha:
                yield from gen_contexts(prefix + c, depth - 1)

    for ctx in gen_contexts('', order - 1):
        t = tot.get(ctx, 0)
        for c2 in alpha:
            logp = math.log((counts.get((ctx, c2), 0) + 0.5) / (t + 0.5 * len(alpha)))
            out.append(max(0, min(255, round((logp + offset) * scale))))
    return bytes(out)


def build_model(texts, order):
    return build_matrix(texts, ALPHA, normalize, order, SCALE, OFFSET)


def normalize_he(s):
    """Normalisation hebreu : supprime les points combinants (niqqud, cantillation),
    garde lettres, finales, ponctuation, gershayim. Miroir de normalize_hebrew()
    dans paste_watch.py (apres correction)."""
    import unicodedata
    # Supprime les marques combinantes (categorie Mn) : niqqud, cantillation
    s = ''.join(ch for ch in s if unicodedata.category(ch) != 'Mn')
    # gershayim U+05F3 -> apostrophe, gershayim double U+05F4 -> guillemet
    s = s.lower().replace('\u05f3', "'").replace('\u05f4', '"')
    return re.sub(r'\s+', ' ',
                  ''.join(ch if ch in HE_ALPHA else ' ' for ch in s)).strip()


def build_he_model(texts, order):
    return build_matrix(texts, HE_ALPHA, normalize_he, order, HE_SCALE, HE_OFFSET)


def emit_block(models, order):
    label = 'bigrammes' if order == 2 else 'trigrammes' if order == 3 else '%d-grammes' % order
    lines = [BEGIN]
    lines.append('// Modeles de %s generes par gen_ngrams.py.' % label)
    lines.append('// Ne pas editer a la main. Sources (domaine public) :')
    for code, sources in LANGS:
        for name, url, sha in sources:
            lines.append('//   %s <- %s (sha256 %s)' % (code, name, sha[:16]))
    lines.append('const MODEL_ALPHA = %r;' % ALPHA)
    lines.append('const MODEL_SCALE = %d, MODEL_OFFSET = %d;' % (SCALE, OFFSET))
    lines.append('const MODEL_ORDER = %d;' % order)
    lines.append('const MODEL_B64 = {')
    for i, (code, _sources) in enumerate(LANGS):
        b64 = base64.b64encode(models[code]).decode('ascii')
        lines.append("  %s: '%s'%s" % (code, b64, ',' if i < len(LANGS) - 1 else ''))
    lines.append('};')
    lines.append(END)
    return '\n'.join(lines)


def _py_unicode(s):
    # Litteral Python sur, en ASCII (le bloc genere reste lisible en cp1252).
    return ''.join(c if ord(c) < 128 else '\\u%04x' % ord(c) for c in s)


def emit_he_block(model, order):
    label = 'bigrammes' if order == 2 else 'trigrammes' if order == 3 else '%d-grammes' % order
    lines = [HE_BEGIN]
    lines.append('# Modele de %s hebreu genere par : python gen_ngrams.py --hebrew' % label)
    lines.append('# Sources (domaine public) :')
    for name, url, sha in HE_SOURCES:
        lines.append('#   %s <- %s (sha256 %s)' % (name, url, sha[:16]))
    lines.append('HE_ALPHA = "%s"' % _py_unicode(HE_ALPHA))
    lines.append('HE_SCALE = %d' % HE_SCALE)
    lines.append('HE_OFFSET = %d' % HE_OFFSET)
    lines.append('HE_ORDER = %d' % order)
    lines.append("HE_B64 = '%s'" % base64.b64encode(model).decode('ascii'))
    lines.append(HE_END)
    return '\n'.join(lines)


def sync_he_block(block):
    with open(HE_FILE, encoding='utf-8') as f:
        text = f.read()
    m = re.search('^%s$.*?^%s$' % (re.escape(HE_BEGIN), re.escape(HE_END)),
                  text, re.S | re.M)
    if not m:
        raise SystemExit('marqueurs %s / %s introuvables dans %s'
                         % (HE_BEGIN, HE_END, HE_FILE))
    text = text[:m.start()] + block + text[m.end():]
    with open(HE_FILE, 'w', encoding='utf-8', newline='\n') as f:
        f.write(text)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--corpus-dir', default='',
                    help='dossier contenant les fichiers sources (sinon telechargement)')
    ap.add_argument('--hebrew', action='store_true',
                    help='genere le modele hebreu de paste_watch.py')
    ap.add_argument('--order', type=int, default=DEFAULT_ORDER,
                    help='ordre des n-grammes (2=bigrammes, 3=trigrammes, defaut: %d)' % DEFAULT_ORDER)
    args = ap.parse_args(argv)

    if args.order < 2 or args.order > 4:
        raise SystemExit('ordre doit etre 2, 3 ou 4')

    if args.hebrew:
        texts = []
        for n, u, s in HE_SOURCES:
            raw = fetch_source(n, u, s, args.corpus_dir)
            if n.startswith('tanach_') or n.startswith('talmud_'):
                # Sefaria : nettoyage HTML + entetes
                raw = '\n'.join(clean_sefaria(raw))
            texts.append(raw)
        model = build_he_model(texts, args.order)
        sync_he_block(emit_he_block(model, args.order))
        print('OK, modele hebreu regenere (%d valeurs, ordre %d)' % (len(model), args.order))
        return 0

    models = {}
    for code, sources in LANGS:
        texts = []
        for n, u, s in sources:
            raw = fetch_source(n, u, s, args.corpus_dir)
            texts.append(raw)
        models[code] = build_model(texts, args.order)
        print('  %s : %d valeurs (%d %s possibles)'
              % (code, len(models[code]), len(ALPHA) ** args.order,
                 'bigrammes' if args.order == 2 else 'trigrammes' if args.order == 3 else '%d-grammes' % args.order))
    block = emit_block(models, args.order)
    with open(HTML_FILE, encoding='utf-8') as f:
        html = f.read()
    m = re.search('^%s$.*?^%s$' % (re.escape(BEGIN), re.escape(END)),
                  html, re.S | re.M)
    if not m:
        print('marqueurs %s / %s introuvables dans %s' % (BEGIN, END, HTML_FILE))
        return 1
    html = html[:m.start()] + block + html[m.end():]
    with open(HTML_FILE, 'w', encoding='utf-8', newline='\n') as f:
        f.write(html)
    print('OK, modeles regeneres (%s, ordre %d)' % (', '.join(sorted(models)), args.order))
    return 0


if __name__ == '__main__':
    sys.exit(main())