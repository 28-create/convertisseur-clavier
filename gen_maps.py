# -*- coding: utf-8 -*-
"""Source de verite : convertisseur.html -> genere les tables (et CAPS_SWAP)
de fix-presse-papiers.py ET le coeur de l'extension (extension/js/core.js).

Usage :
  python gen_maps.py    (met a jour les blocs generes dans les deux fichiers)
  python test_maps.py   (verifie que tout est synchronise)
"""
import json
import re
import sys

HTML_FILE = 'convertisseur.html'
PY_FILE = 'fix-presse-papiers.py'
JS_FILE = 'extension/js/core.js'
MAP_NAMES = ['FR_TO_HE', 'HE_TO_FR', 'EN_TO_HE', 'HE_TO_EN', 'QW_TO_AZ', 'AZ_TO_QW']
BEGIN = '# <maps:generated>'
END = '# </maps:generated>'
JS_BEGIN = '// <maps:generated>'
JS_END = '// </maps:generated>'
JS_CORE_BEGIN = '// <core:generated>'
JS_CORE_END = '// </core:generated>'

_STR = r"""('(?:[^'\\]|\\.)*'|"(?:[^"\\]|\\.)*")"""
_PAIR = re.compile(_STR + r'\s*:\s*' + _STR)

_ESCAPES = {'\\': '\\', "'": "'", '"': '"', 'n': '\n', 't': '\t', 'r': '\r'}

# Fonctions pures copiees telles quelles dans l'extension : une seule
# implementation (page), donc aucune derive possible.
_CORE_SIGS = (
    r'function convertSmart\(text, fullMap, swapCaps, toFrench\) \{[\s\S]*?\n\}',
    r'function detectDir\(text\) \{[\s\S]*?\n\}',
)


def _unesc(s):
    q, s = s[0], s[1:-1]
    out = []
    i = 0
    while i < len(s):
        if s[i] == '\\' and i + 1 < len(s):
            nxt = s[i + 1]
            if nxt == 'u' and re.fullmatch(r'[0-9a-fA-F]{4}', s[i + 2:i + 6] or ''):
                out.append(chr(int(s[i + 2:i + 6], 16)))
                i += 6
                continue
            out.append(_ESCAPES.get(nxt, nxt))
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
    return re.findall(r"""['"]?(\w+)['"]?\s*:\s*['"]([^'"]*)['"]""",
                      m.group(1))


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


def _js_str(s):
    # Litteral JS sur : json.dumps echappe guillemets, antislash, controles et
    # tout non-ASCII (\uXXXX), donc le fichier genere reste en ASCII.
    return json.dumps(s, ensure_ascii=True)


def emit_js_maps(maps, caps):
    lines = []
    for name in MAP_NAMES:
        lines.append('const %s = {' % name)
        row = []
        for k, v in maps[name]:
            row.append('%s: %s' % (_js_str(k), _js_str(v)))
            if len(row) == 4:
                lines.append('  ' + ', '.join(row) + ',')
                row = []
        if row:
            lines.append('  ' + ', '.join(row) + ',')
        lines.append('};')
        lines.append('')
    lines.append('const CAPS_SWAP = {%s};' % ', '.join(
        '%s: %s' % (_js_str(k), _js_str(v)) for k, v in caps))
    return '\n'.join(lines) + '\n'


def extract_core(html_text):
    """Copie verbatim convertSmart + detectDir (fonctions pures du HTML)."""
    parts = []
    for sig in _CORE_SIGS:
        m = re.search(sig, html_text)
        if not m:
            raise ValueError('fonction introuvable dans %s : %s'
                             % (HTML_FILE, sig[:30]))
        parts.append(m.group(0))
    return '\n\n'.join(parts) + '\n'


def replace_block(path, begin, end, block):
    """Remplace le bloc entre deux marqueurs. Rend True si le fichier change."""
    with open(path, encoding='utf-8') as f:
        text = f.read()
    m = re.search('^%s$.*?^%s$' % (re.escape(begin), re.escape(end)),
                  text, re.S | re.M)
    if not m:
        raise ValueError('marqueurs %s / %s introuvables dans %s'
                         % (begin, end, path))
    new = text[:m.start()] + begin + '\n' + block + end + text[m.end():]
    if new != text:
        with open(path, 'w', encoding='utf-8', newline='\n') as f:
            f.write(new)
        return True
    return False


def main():
    with open(HTML_FILE, encoding='utf-8') as f:
        html = f.read()
    maps = parse_js_maps(html)
    caps = parse_caps_swap(html)
    replace_block(PY_FILE, BEGIN, END, emit_py(maps, caps))
    replace_block(JS_FILE, JS_BEGIN, JS_END, emit_js_maps(maps, caps))
    replace_block(JS_FILE, JS_CORE_BEGIN, JS_CORE_END, extract_core(html))
    counts = ', '.join('%s=%d' % (n, len(maps[n])) for n in MAP_NAMES)
    print('OK, tables regenerees (%s, CAPS_SWAP=%d)' % (counts, len(caps)))
    print('OK, extension synchronisee (%s)' % JS_FILE)
    return 0


if __name__ == '__main__':
    sys.exit(main())
