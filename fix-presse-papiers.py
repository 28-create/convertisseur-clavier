# -*- coding: utf-8 -*-
"""Convertit le presse-papiers francais/anglais <-> hebreu
(meme mapping que convertisseur.html).

Usage quotidien : selectionnez le texte tape avec le mauvais clavier, Ctrl+C,
lancez ce script (ou son raccourci), puis Ctrl+V.

  python fix-presse-papiers.py [--layout azerty|qwerty] [--direction auto|toHe|toFr]
  python fix-presse-papiers.py --mode latin [--latin-dir toAz|toQw]

Raccourci global conseille (Windows) :
  1. Clic droit sur fix-presse-papiers.bat > Creer un raccourci
  2. Clic droit sur le raccourci > Proprietes > Touche de raccourci : Ctrl+Alt+H
  3. Selectionnez texte > Ctrl+C > Ctrl+Alt+H > Ctrl+V
"""
import argparse
import re
import sys

# Les tables ci-dessous sont GENEREES depuis convertisseur.html :
#   python gen_maps.py   (puis python test_maps.py pour verifier)
# Ne pas les modifier a la main.
# <maps:generated>
FR_TO_HE = {
    'a': '/', 'A': '/', 'z': "'", 'Z': "'",
    'e': 'ק', 'E': 'ק', 'r': 'ר', 'R': 'ר',
    't': 'א', 'T': 'א', 'y': 'ט', 'Y': 'ט',
    'u': 'ו', 'U': 'ו', 'i': 'ן', 'I': 'ן',
    'o': 'ם', 'O': 'ם', 'p': 'פ', 'P': 'פ',
    '^': ']', '¨': '}', '$': '[', '£': '{',
    '¤': '{', 'q': 'ש', 'Q': 'ש', 's': 'ד',
    'S': 'ד', 'd': 'ג', 'D': 'ג', 'f': 'כ',
    'F': 'כ', 'g': 'ע', 'G': 'ע', 'h': 'י',
    'H': 'י', 'j': 'ח', 'J': 'ח', 'k': 'ל',
    'K': 'ל', 'l': 'ך', 'L': 'ך', 'm': 'ף',
    'M': 'ף', 'ù': ',', 'Ù': ',', '%': ',',
    '*': '\\', 'w': 'ז', 'W': 'ז', 'x': 'ס',
    'X': 'ס', 'c': 'ב', 'C': 'ב', 'v': 'ה',
    'V': 'ה', 'b': 'נ', 'B': 'נ', 'n': 'מ',
    'N': 'מ', ',': 'צ', '?': 'צ', ';': 'ת',
    '.': 'ת', ':': 'ץ', '/': 'ץ', '!': '.',
    '§': '.', '²': ';', '&': '1', '1': '1',
    'é': '2', '2': '2', '~': '2', '"': '3',
    '3': '3', '#': '3', "'": '4', '4': '4',
    '{': '4', '(': '5', '5': '5', '[': '5',
    '-': '6', '6': '6', '|': '6', 'è': '7',
    '7': '7', '`': '7', '_': '8', '8': '8',
    '\\': '8', 'ç': '9', '9': '9', 'à': '0',
    '0': '0', '@': '0', ')': '-', '°': '_',
    ']': '-', '=': '=', '+': '+', '}': '=',
}
HE_TO_FR = {
    '/': 'a', "'": 'z', 'ק': 'e', 'ר': 'r',
    'א': 't', 'ט': 'y', 'ו': 'u', 'ן': 'i',
    'ם': 'o', 'פ': 'p', ']': '^', '[': '$',
    'ש': 'q', 'ד': 's', 'ג': 'd', 'כ': 'f',
    'ע': 'g', 'י': 'h', 'ח': 'j', 'ל': 'k',
    'ך': 'l', 'ף': 'm', ',': 'ù', 'ז': 'w',
    'ס': 'x', 'ב': 'c', 'ה': 'v', 'נ': 'b',
    'מ': 'n', 'צ': ',', 'ת': ';', 'ץ': ':',
    '.': '!', ';': '²', '1': '&', '2': 'é',
    '3': '"', '4': "'", '5': '(', '6': '-',
    '7': 'è', '8': '_', '9': 'ç', '0': 'à',
    '-': ')', '=': '=', 'Q': 'A', 'W': 'Z',
    'E': 'E', 'R': 'R', 'T': 'T', 'Y': 'Y',
    'U': 'U', 'I': 'I', 'O': 'O', 'P': 'P',
    'A': 'Q', 'S': 'S', 'D': 'D', 'F': 'F',
    'G': 'G', 'H': 'H', 'J': 'J', 'K': 'K',
    'L': 'L', 'Z': 'W', 'X': 'X', 'C': 'C',
    'V': 'V', 'B': 'B', 'N': 'N', 'M': ',',
    ':': 'M', '"': 'ù', ')': 'ç', '(': 'à',
}
EN_TO_HE = {
    'q': '/', 'Q': '/', 'w': "'", 'W': "'",
    'e': 'ק', 'E': 'ק', 'r': 'ר', 'R': 'ר',
    't': 'א', 'T': 'א', 'y': 'ט', 'Y': 'ט',
    'u': 'ו', 'U': 'ו', 'i': 'ן', 'I': 'ן',
    'o': 'ם', 'O': 'ם', 'p': 'פ', 'P': 'פ',
    '[': ']', '{': '}', ']': '[', '}': '{',
    '\\': '\\', '|': '|', 'a': 'ש', 'A': 'ש',
    's': 'ד', 'S': 'ד', 'd': 'ג', 'D': 'ג',
    'f': 'כ', 'F': 'כ', 'g': 'ע', 'G': 'ע',
    'h': 'י', 'H': 'י', 'j': 'ח', 'J': 'ח',
    'k': 'ל', 'K': 'ל', 'l': 'ך', 'L': 'ך',
    ';': 'ף', ':': 'ף', "'": ',', '"': ',',
    'z': 'ז', 'Z': 'ז', 'x': 'ס', 'X': 'ס',
    'c': 'ב', 'C': 'ב', 'v': 'ה', 'V': 'ה',
    'b': 'נ', 'B': 'נ', 'n': 'מ', 'N': 'מ',
    'm': 'צ', 'M': 'צ', ',': 'ת', '<': '>',
    '.': 'ץ', '>': '<', '/': '.', '?': '.',
    '`': ';', '~': ';', '1': '1', '!': '!',
    '2': '2', '@': '@', '3': '3', '#': '#',
    '4': '4', '$': '$', '5': '5', '%': '%',
    '6': '6', '^': '^', '7': '7', '&': '&',
    '8': '8', '*': '*', '9': '9', '(': ')',
    '0': '0', ')': '(', '-': '-', '_': '_',
    '=': '=', '+': '+',
}
HE_TO_EN = {
    '/': 'q', "'": 'w', 'ק': 'e', 'ר': 'r',
    'א': 't', 'ט': 'y', 'ו': 'u', 'ן': 'i',
    'ם': 'o', 'פ': 'p', ']': '[', '[': ']',
    '}': '{', '{': '}', 'ש': 'a', 'ד': 's',
    'ג': 'd', 'כ': 'f', 'ע': 'g', 'י': 'h',
    'ח': 'j', 'ל': 'k', 'ך': 'l', 'ף': ';',
    ',': "'", 'ז': 'z', 'ס': 'x', 'ב': 'c',
    'ה': 'v', 'נ': 'b', 'מ': 'n', 'צ': 'm',
    'ת': ',', 'ץ': '.', '.': '/', ';': '`',
    ')': '(', '(': ')', '>': '<', '<': '>',
}
QW_TO_AZ = {
    'q': 'a', 'Q': 'A', 'w': 'z', 'W': 'Z',
    'a': 'q', 'A': 'Q', 'z': 'w', 'Z': 'W',
    'm': ',', 'M': '?', ';': 'm', ':': 'M',
    "'": 'ù', '"': '%', ',': ';', '<': '.',
    '.': ':', '>': '/', '/': '!', '?': '§',
    '[': '^', '{': '¨', ']': '$', '}': '£',
    '\\': '*', '|': 'μ', '`': '²', '1': '&',
    '2': 'é', '3': '"', '4': "'", '5': '(',
    '6': '-', '7': 'è', '8': '_', '9': 'ç',
    '0': 'à', '-': ')', '!': '1', '@': '2',
    '#': '3', '$': '4', '%': '5', '^': '6',
    '&': '7', '*': '8', '(': '9', ')': '0',
    '_': '°',
}
AZ_TO_QW = {
    'a': 'q', 'A': 'Q', 'z': 'w', 'Z': 'W',
    'q': 'a', 'Q': 'A', 'w': 'z', 'W': 'Z',
    ',': 'm', '?': 'M', 'm': ';', 'M': ':',
    'ù': "'", '%': '"', ';': ',', '.': '<',
    ':': '.', '/': '>', '!': '/', '§': '?',
    '^': '[', '¨': '{', '$': ']', '£': '}',
    '*': '\\', 'μ': '|', '²': '`', '&': '1',
    'é': '2', '"': '3', "'": '4', '(': '5',
    '-': '6', 'è': '7', '_': '8', 'ç': '9',
    'à': '0', ')': '-', '1': '!', '2': '@',
    '3': '#', '4': '$', '5': '%', '6': '^',
    '7': '&', '8': '*', '9': '(', '0': ')',
    '°': '_',
}
# </maps:generated>

MAPS = {
    'azerty': (FR_TO_HE, HE_TO_FR),
    'qwerty': (EN_TO_HE, HE_TO_EN),
}
LATIN_MAPS = {
    'toAz': QW_TO_AZ,
    'toQw': AZ_TO_QW,
}
# Capitales isolees : seules Q/A/W/Z changent de touche (miroir JS CAPS_SWAP).
CAPS_SWAP = {'Q': 'A', 'A': 'Q', 'W': 'Z', 'Z': 'W'}

_HE_RE = re.compile(r'[\u0590-\u05FF]')
_HE_TOKEN_RE = re.compile(r'[^\s]*[\u0590-\u05FF][^\s]*')
_CAP_TOKEN_RE = re.compile(r'[^\s]*[A-Z][^\s]*')

# Tables de traduction C (str.translate), construites une fois par mapping.
# Semantique identique a mapping.get(ch, ch) : cles = 1 caractere,
# absents = inchanges. Les dicts module vivent toujours : id() stable.
_TR_CACHE = {}


def _table(mapping):
    t = _TR_CACHE.get(id(mapping))
    if t is None:
        t = str.maketrans(mapping)
        _TR_CACHE[id(mapping)] = t
    return t


def _map_with(text, mapping):
    return text.translate(_table(mapping))


def _caps_tok(tok, swap_caps):
    letters = re.sub(r'[^A-Za-z]', '', tok)
    if letters and letters == letters.upper():
        return _map_with(tok, swap_caps)
    return tok


def convert_smart(text, full_map, swap_caps, to_french):
    """Texte mixte : voir convertSmart dans convertisseur.html (miroir exact).

    Sans segmentation : les substitutions preservent d'elles-memes les
    separateurs. L'ordre des deux passages est sans effet : un mot
    reconverti ne peut pas devenir "tout en capitales" (les lettres
    hebraiques n'emettent que des minuscules), donc le second passage
    ne retouche jamais le premier.
    """
    if not _HE_RE.search(text):
        # Sans hebreu, pas de segmentation : un seul passage C.
        if not to_french:
            return _map_with(text, full_map)
        if not swap_caps:
            return text
        return _CAP_TOKEN_RE.sub(lambda m: _caps_tok(m.group(0), swap_caps), text)
    if not to_french:
        # Avec hebreu : boucle classique — le contexte mot-entier compte
        # (ex. "abcש" reste intact : on ne convertit que les mots 100 % latins).
        out = []
        for tok in re.split(r'(\s+)', text):
            if not tok or tok.isspace() or _HE_RE.search(tok):
                out.append(tok)
            else:
                out.append(_map_with(tok, full_map))
        return ''.join(out)
    out = _HE_TOKEN_RE.sub(lambda m: _map_with(m.group(0), full_map), text)
    if swap_caps:
        out = _CAP_TOKEN_RE.sub(lambda m: _caps_tok(m.group(0), swap_caps), out)
    return out


def convert(text, mapping):
    return _map_with(text, mapping)


def autodir(text):
    # Doit rester identique a detectDir() dans convertisseur.html
    # (meme classe latine accentuee, meme seuil 0.2).
    # Heuristique : du francais normal ne contient aucun hebreu ; si au
    # moins 20 % des lettres latines sont en fait de l'hebreu, c'est une
    # frappe en clavier hebreu a reconvertir. En dessous, l'hebreu present
    # est preserve tel quel (melange avec du vrai hebreu).
    h = len(re.findall(r'[\u0590-\u05FF]', text))
    l = len(re.findall(r'[A-Za-zéèêëàâäçîïôöùûüÉÈÀÇÙ]', text))
    return 'toFr' if (h > 0 and h >= l * 0.2) else 'toHe'


def get_clipboard():
    import tkinter as tk
    r = tk.Tk()
    r.withdraw()
    try:
        return r.clipboard_get()
    except Exception:
        return ''
    finally:
        r.destroy()


def set_clipboard(text):
    import tkinter as tk
    r = tk.Tk()
    r.withdraw()
    r.clipboard_clear()
    r.clipboard_append(text)
    r.update()
    r.destroy()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--layout', default='azerty', choices=['azerty', 'qwerty'])
    ap.add_argument('--direction', default='auto', choices=['auto', 'toHe', 'toFr'])
    ap.add_argument('--mode', default='hebrew', choices=['hebrew', 'latin'],
                    help='hebrew = francais/anglais<->hebreu (defaut), latin = QWERTY<->AZERTY')
    ap.add_argument('--latin-dir', default='toAz', choices=['toAz', 'toQw'],
                    help='sens en mode latin (pas d\'auto-detection possible)')
    ap.add_argument('text', nargs='?', help='texte direct (sinon presse-papiers)')
    args = ap.parse_args()

    src = args.text if args.text is not None else get_clipboard()
    if not src:
        print('Presse-papiers vide (ou texte manquant).')
        return 1
    if args.mode == 'latin':
        direction = args.latin_dir
        out = convert(src, LATIN_MAPS[direction])
        tag = 'latin %s' % direction
    else:
        to_he, to_fr = MAPS[args.layout]
        direction = autodir(src) if args.direction == 'auto' else args.direction
        to_french = direction == 'toFr'
        full = to_fr if to_french else to_he
        swap = CAPS_SWAP if args.layout == 'azerty' else None
        out = convert_smart(src, full, swap, to_french)
        langue = {'azerty': 'francais', 'qwerty': 'anglais'}[args.layout]
        tag = '%s %s' % (langue, direction)
    if args.text is None:
        set_clipboard(out)
    msg = '[%s] %s' % (tag, out)
    try:
        print(msg)
    except UnicodeEncodeError:
        # console Windows (cp1252...) incapable d'afficher l'hebreu :
        # le presse-papiers est deja a jour, on affiche en ASCII sur.
        print(msg.encode('ascii', 'backslashreplace').decode('ascii'))
    return 0


if __name__ == '__main__':
    sys.exit(main())
