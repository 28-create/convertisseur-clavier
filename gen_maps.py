# -*- coding: utf-8 -*-
"""Source de verite : convertisseur.html -> genere les tables (et CAPS_SWAP)
de fix-presse-papiers.py.

Usage :
  python gen_maps.py    (met a jour le bloc <maps:generated> dans fix-presse-papiers.py)
  python test_maps.py   (verifie que les 2 fichiers sont synchronises)
"""
import re
import sys

HTML_FILE = 'convertisseur.html'
PY_FILE = 'fix-presse-papiers.py'
MAP_NAMES = ['FR_TO_HE', 'HE_TO_FR', 'EN_TO_HE', 'HE_TO_EN', 'QW_TO_AZ', 'AZ_TO_QW']
BEGIN = '# <maps:generated>'
END = '# </maps:generated>'

_STR = r"""('(?:[^'\\]|\\.)*'|"(?:[^"\\]|\\.)*")"""
_PAIR = re.compile(_STR + r'\s*:\s*' + _STR)

_ESCAPES = {'\\': '\\', "'": "'", '"': '"', 'n': '\n', 't': '\t', 'r': '\r'}


def _unesc(s):
    q, s = s[0], s[1:-1]
    out = []
    i = 0
    while i < len(s):
        if s[i] == '\\' and i + 1 < len(s):
            out.append(_ESCAPES.get(s[i + 1], s[i + 1]))
            i += 2
        else:
            out.append(s[i])
            i += 1
    return ''.join(out)


def parse_js_maps(html_text):
    """Rend {nom: [(cle, valeur), ...]} dans l'ordre du fichier."""
    maps = {}
    for name in MAP_NAMES:
        m = re.search(r'const %s = \{(.*?)\n\};' % name, html_text, re.S)
        if not m:
            raise ValueError('table %s introuvable dans %s' % (name, HTML_FILE))
        maps[name] = [(_unesc(k), _unesc(v)) for k, v in _PAIR.findall(m.group(1))]
    return maps


def parse_caps_swap(html_text):
    """Rend [('Q', 'A'), ...] (CAPS_SWAP) dans l'ordre du fichier."""
    m = re.search(r'const CAPS_SWAP = \{([^}]*)\};', html_text)
    if not m:
        raise ValueError('CAPS_SWAP introuvable dans %s' % HTML_FILE)
    return re.findall(r"(\w+)\s*:\s*'([^']*)'", m.group(1))


def emit_py(maps, caps):
    lines = []
    for name in MAP_NAMES:
        lines.append('%s = {' % name)
        row = []
        for k, v in maps[name]:
            row.append('%r: %r' % (k, v))
            if len(row) == 4:
                lines.append('    ' + ', '.join(row) + ',')
                row = []
        if row:
            lines.append('    ' + ', '.join(row) + ',')
        lines.append('}')
    lines.append('')
    lines.append('# Capitales isolees : seules Q/A/W/Z changent de touche.')
    lines.append('CAPS_SWAP = {%s}' % ', '.join(
        '%r: %r' % (k, v) for k, v in caps))
    return '\n'.join(lines) + '\n'


def main():
    with open(HTML_FILE, encoding='utf-8') as f:
        html = f.read()
    maps = parse_js_maps(html)
    caps = parse_caps_swap(html)
    block = emit_py(maps, caps)
    with open(PY_FILE, encoding='utf-8') as f:
        py = f.read()
    m = re.search('^%s$.*?^%s$' % (re.escape(BEGIN), re.escape(END)), py, re.S | re.M)
    if not m:
        print('marqueurs %s / %s introuvables dans %s' % (BEGIN, END, PY_FILE))
        return 1
    py = py[:m.start()] + BEGIN + '\n' + block + END + py[m.end():]
    with open(PY_FILE, 'w', encoding='utf-8', newline='\n') as f:
        f.write(py)
    counts = ', '.join('%s=%d' % (n, len(maps[n])) for n in MAP_NAMES)
    print('OK, tables regenerees (%s, CAPS_SWAP=%d)' % (counts, len(caps)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
