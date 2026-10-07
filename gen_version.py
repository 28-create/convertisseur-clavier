# -*- coding: utf-8 -*-
"""Genere version_info.txt (ressource de version Windows pour --version-file).

Usage : python gen_version.py
Source de verite : const APP_VERSION dans convertisseur.html.
Le .exe affiche alors la version dans Proprietes > Details.
"""
import re
import sys

HTML_FILE = 'convertisseur.html'
OUT_FILE = 'version_info.txt'

TEMPLATE = """# UTF-8
#
# Fichier GENERE depuis convertisseur.html : python gen_version.py
# Ne pas modifier a la main.
#
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers={tup},
    prodvers={tup},
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
    ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        '040904B0',
        [StringStruct('CompanyName', 'Mimran'),
        StringStruct('FileDescription', 'Convertisseur Clavier Latin ⇄ Hébreu'),
        StringStruct('FileVersion', '{ver}'),
        StringStruct('InternalName', 'ConvertisseurClavier'),
        StringStruct('LegalCopyright', 'Copyright (c) 2026 Mimran (MIT)'),
        StringStruct('OriginalFilename', 'ConvertisseurClavier.exe'),
        StringStruct('ProductName', 'Convertisseur Clavier'),
        StringStruct('ProductVersion', '{ver}')])
      ]),
    VarFileInfo([VarStruct('Translation', [1033, 1200])])
  ]
)
"""


def read_version(html_path=HTML_FILE):
    with open(html_path, encoding='utf-8') as f:
        html = f.read()
    m = re.search(r"const APP_VERSION = '([^']+)'", html)
    if not m:
        raise ValueError('APP_VERSION introuvable dans %s' % html_path)
    return m.group(1)


def build_info(ver):
    parts = ver.split('.')
    if len(parts) != 3 or not all(p.isdigit() for p in parts):
        raise ValueError('version non X.Y.Z : %r' % ver)
    tup = '(%s, 0)' % ', '.join(parts)
    text = TEMPLATE.format(ver=ver, tup=tup)
    if text.count("'%s'" % ver) < 2 or text.count(tup) < 2:
        raise ValueError('gabarit incomplet pour %r' % ver)
    return text


def main():
    ver = read_version()
    with open(OUT_FILE, 'w', encoding='utf-8', newline='\n') as f:
        f.write(build_info(ver))
    print('OK : %s genere (version %s)' % (OUT_FILE, ver))
    return 0


if __name__ == '__main__':
    sys.exit(main())
