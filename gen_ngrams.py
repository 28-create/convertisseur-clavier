# -*- coding: utf-8 -*-
"""Genere les modeles de bigrammes de suggestion de lecture dans
convertisseur.html (bloc <models:generated>).

Usage :
  python gen_ngrams.py [--corpus-dir DOSSIER]
  python gen_ngrams.py --hebrew [--corpus-dir DOSSIER]

Ajouter une langue de detection : une entree dans LANGS (code + sources
verifiees par SHA-256), puis relancer. Rien d'autre a toucher : le score,
l'UI et les tests iterent sur les donnees. --hebrew regenere le modele
hebreu de paste_watch.py (guetteur Ctrl+V), separe des modeles latins.

Sources : textes du domaine public (Project Gutenberg), telecharges et
verifies ; --corpus-dir reutilise des fichiers deja presents.
Format emis : table dense ALPHA x ALPHA quantifiee en int8, base64 ;
octet b -> log-probabilite b / MODEL_SCALE - MODEL_OFFSET (nats).
normalize() est le miroir exact de normalizeForModel() dans la page
(test_page.py verifie la parite).
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
# Modele hebreu du guetteur de presse-papiers (paste_watch.py) : alphabet
# separe, donc les modeles latin de la page restent inchanges.
HE_ALPHA = ('\u05d0\u05d1\u05d2\u05d3\u05d4\u05d5\u05d6\u05d7\u05d8\u05d9'
            '\u05db\u05dc\u05de\u05e0\u05e1\u05e2\u05e4\u05e6\u05e7\u05e8'
            '\u05e9\u05ea\u05da\u05dd\u05df\u05e3\u05e5' + " '.,:;!?")
HE_SCALE, HE_OFFSET = 8, 16
HE_FILE = 'paste_watch.py'
HE_BEGIN = '# <he_model:generated>'
HE_END = '# </he_model:generated>'
HE_SOURCES = [('pg5139.txt',
               'https://www.gutenberg.org/cache/epub/5139/pg5139.txt',
               'd105307feb42da018e2b6713247c3256f7ac4273a2f269e0f0fc1fd69bb7d903')]
LANGS = [
    ('fr', [('pg17489.txt',
             'https://www.gutenberg.org/cache/epub/17489/pg17489.txt',
             'a5de514ba7b9f2e1790e7e259c4e8b7a35ae1d29e4bf9a5f8767039c58b80503')]),
    ('en', [('pg11.txt',
             'https://www.gutenberg.org/cache/epub/11/pg11.txt',
             '01b38ea4c710a84bc18d0bd41271a5a1a92b94e97b2812f4dece97d4a694725e')]),
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
        with urllib.request.urlopen(url, timeout=60) as r:
            data = r.read()
        origin = url
    got = hashlib.sha256(data).hexdigest()
    if got != sha:
        raise SystemExit('SHA-256 inattendu pour %s : %s' % (origin, got))
    return data.decode('utf-8', 'replace')


def build_matrix(texts, alpha, norm, scale=SCALE, offset=OFFSET):
    """Table dense quantifiee : len(alpha) x len(alpha) octets."""
    counts, tot = {}, {}
    for raw in texts:
        txt = norm(strip_gutenberg(raw))
        prev = None
        for ch in txt:
            if prev is not None:
                counts[(prev, ch)] = counts.get((prev, ch), 0) + 1
                tot[prev] = tot.get(prev, 0) + 1
            prev = ch
    V = len(alpha) ** 2
    out = bytearray()
    for c1 in alpha:
        t = tot.get(c1, 0)
        for c2 in alpha:
            logp = math.log((counts.get((c1, c2), 0) + 0.5) / (t + 0.5 * V))
            out.append(max(0, min(255, round((logp + offset) * scale))))
    return bytes(out)


def build_model(texts):
    return build_matrix(texts, ALPHA, normalize, SCALE, OFFSET)


def normalize_he(s):
    # Meme principe que normalize() : tout ce qui n'est pas dans l'alphabet
    # devient une espace (niqqud, cantillation, chiffres, latin...).
    s = s.lower().replace('\u05f3', "'").replace('\u05f4', '"')
    return re.sub(r'\s+', ' ',
                  ''.join(ch if ch in HE_ALPHA else ' ' for ch in s)).strip()


def build_he_model(texts):
    return build_matrix(texts, HE_ALPHA, normalize_he, HE_SCALE, HE_OFFSET)


def emit_block(models):
    lines = [BEGIN]
    lines.append('// Modeles de bigrammes generes par gen_ngrams.py.')
    lines.append('// Ne pas editer a la main. Sources (domaine public) :')
    for code, sources in LANGS:
        for name, url, sha in sources:
            lines.append('//   %s <- %s (sha256 %s)' % (code, name, sha[:16]))
    lines.append('const MODEL_ALPHA = %r;' % ALPHA)
    lines.append('const MODEL_SCALE = %d, MODEL_OFFSET = %d;' % (SCALE, OFFSET))
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


def emit_he_block(model):
    lines = [HE_BEGIN]
    lines.append('# Modele de bigrammes hebreu genere par : python gen_ngrams.py --hebrew')
    lines.append('# Source (domaine public) :')
    for name, url, sha in HE_SOURCES:
        lines.append('#   %s <- %s (sha256 %s)' % (name, url, sha[:16]))
    lines.append('HE_ALPHA = "%s"' % _py_unicode(HE_ALPHA))
    lines.append('HE_SCALE = %d' % HE_SCALE)
    lines.append('HE_OFFSET = %d' % HE_OFFSET)
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
    args = ap.parse_args(argv)
    if args.hebrew:
        texts = [fetch_source(n, u, s, args.corpus_dir)
                 for n, u, s in HE_SOURCES]
        model = build_he_model(texts)
        sync_he_block(emit_he_block(model))
        print('OK, modele hebreu regenere (%d valeurs)' % len(model))
        return 0
    models = {}
    for code, sources in LANGS:
        texts = [fetch_source(n, u, s, args.corpus_dir) for n, u, s in sources]
        models[code] = build_model(texts)
        print('  %s : %d valeurs (%d bigrammes possibles)'
              % (code, len(models[code]), len(ALPHA) ** 2))
    block = emit_block(models)
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
    print('OK, modeles regeneres (%s)' % ', '.join(sorted(models)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
