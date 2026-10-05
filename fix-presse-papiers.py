# -*- coding: utf-8 -*-
"""Convertit le presse-papiers Latin <-> Hebreu (meme mapping que convertisseur.html).

Usage quotidien : selectionnez le texte tape avec le mauvais clavier, Ctrl+C,
lancez ce script (ou son raccourci), puis Ctrl+V.

  python fix-presse-papiers.py [--layout azerty|qwerty] [--direction auto|toHe|toFr]

Raccourci global conseille (Windows) :
  1. Clic droit sur fix-presse-papiers.bat > Creer un raccourci
  2. Clic droit sur le raccourci > Proprietes > Touche de raccourci : Ctrl+Alt+H
  3. Selectionnez texte > Ctrl+C > Ctrl+Alt+H > Ctrl+V
"""
import argparse
import re
import sys

# Les 4 tables ci-dessous sont GENEREES depuis convertisseur.html :
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
# </maps:generated>

MAPS = {
    'azerty': (FR_TO_HE, HE_TO_FR),
    'qwerty': (EN_TO_HE, HE_TO_EN),
}


def convert(text, mapping):
    return ''.join(mapping.get(ch, ch) for ch in text)


def autodir(text):
    h = len(re.findall(r'[\u0590-\u05FF]', text))
    l = len(re.findall(r'[A-Za-z]', text))
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
    ap.add_argument('text', nargs='?', help='texte direct (sinon presse-papiers)')
    args = ap.parse_args()

    src = args.text if args.text is not None else get_clipboard()
    if not src:
        print('Presse-papiers vide (ou texte manquant).')
        return 1
    to_he, to_fr = MAPS[args.layout]
    direction = autodir(src) if args.direction == 'auto' else args.direction
    out = convert(src, to_fr if direction == 'toFr' else to_he)
    if args.text is None:
        set_clipboard(out)
    msg = '[%s %s] %s' % (args.layout, direction, out)
    try:
        print(msg)
    except UnicodeEncodeError:
        # console Windows (cp1252...) incapable d'afficher l'hebreu :
        # le presse-papiers est deja a jour, on affiche en ASCII sur.
        print(msg.encode('ascii', 'backslashreplace').decode('ascii'))
    return 0


if __name__ == '__main__':
    sys.exit(main())
