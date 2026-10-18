# -*- coding: utf-8 -*-
"""Construit le paquet a deposer sur les stores (Chrome Web Store / Edge).

Usage :
  python build_extension.py          (ecrit dist\\ConvertisseurClavier-extension-<version>.zip)
  python build_extension.py --check  (verifie sans ecrire : version, manifeste,
                                      fichiers references, fichiers interdits)

Le ZIP contient le CONTENU de extension\\ (manifest.json a la racine), jamais le
dossier parent : c'est le format exige par les stores. La version suit
APP_VERSION (`gen_version.py` synchronise extension/manifest.json) et doit etre
incrementee a chaque envoi, sinon le store refuse le paquet.

Etapes : gen_version.py (synchronise le manifeste) -> zip reproductible.
"""
import json
import os
import sys
import zipfile

import gen_version

EXT_DIR = 'extension'
MANIFEST = os.path.join(EXT_DIR, 'manifest.json')
DIST_DIR = 'dist'

# Jamais dans le paquet : outils, fichiers systeme, caches, archives precedentes.
EXCLUDE_NAMES = {'.DS_Store', 'Thumbs.db', 'desktop.ini', '.gitignore'}
EXCLUDE_DIRS = {'__pycache__', 'node_modules', '.git', '.vscode', '.idea'}
EXCLUDE_SUFFIX = ('.pyc', '.pyo', '.map', '.log', '.zip', '.pem', '.key')

# Horodatage fixe : zip reproductible (memes octets pour une meme version).
ZIP_DATE = (1980, 1, 1, 0, 0, 0)

MAX_NAME = 75          # limite du manifeste Chrome
MAX_DESCRIPTION = 132  # limite de la description courte du store


def read_version():
    return gen_version.read_version()


def read_manifest(path=MANIFEST):
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def manifest_files(m):
    """Chemins relatifs (a extension\\) references par le manifeste."""
    out = set()
    bg = m.get('background') or {}
    if bg.get('service_worker'):
        out.add(bg['service_worker'])
    act = m.get('action') or {}
    if act.get('default_popup'):
        out.add(act['default_popup'])
    for rel in (act.get('default_icon') or {}).values():
        out.add(rel)
    for rel in (m.get('icons') or {}).values():
        out.add(rel)
    for cs in m.get('content_scripts') or []:
        out.update(cs.get('js') or [])
        out.update(cs.get('css') or [])
    for war in m.get('web_accessible_resources') or []:
        if isinstance(war, dict):
            out.update(war.get('resources') or [])
    return {rel for rel in out if isinstance(rel, str) and rel}


def package_files(ext_dir=EXT_DIR):
    """(inclus, ecartes) : listes triees de (chemin local, chemin dans le zip)."""
    include, skipped = [], []
    for root, dirs, files in os.walk(ext_dir):
        dirs[:] = sorted(d for d in dirs if d not in EXCLUDE_DIRS)
        for name in sorted(files):
            path = os.path.join(root, name)
            rel = os.path.relpath(path, ext_dir).replace(os.sep, '/')
            if name in EXCLUDE_NAMES or name.endswith(EXCLUDE_SUFFIX):
                skipped.append(rel)
            else:
                include.append((path, rel))
    include.sort(key=lambda item: item[1])
    return include, sorted(skipped)


def check():
    ver = read_version()
    if not os.path.isfile(MANIFEST):
        print('PROBLEME : manifeste absent : %s' % MANIFEST)
        return 1
    try:
        m = read_manifest()
    except (OSError, ValueError) as e:
        print('PROBLEME : manifeste illisible : %s' % e)
        return 1

    problems = []
    if m.get('manifest_version') != 3:
        problems.append('manifest_version != 3 (%r)' % m.get('manifest_version'))
    if m.get('version') != ver:
        problems.append('version manifeste=%s, page=%s'
                        % (m.get('version'), ver))
    name = m.get('name') or ''
    desc = m.get('description') or ''
    if not name:
        problems.append('name vide')
    elif len(name) > MAX_NAME:
        problems.append('name trop long (%d > %d)' % (len(name), MAX_NAME))
    if not desc:
        problems.append('description vide')
    elif len(desc) > MAX_DESCRIPTION:
        problems.append('description trop longue (%d > %d)'
                        % (len(desc), MAX_DESCRIPTION))

    wanted = manifest_files(m)
    for rel in sorted(wanted):
        if not os.path.isfile(os.path.join(EXT_DIR, rel)):
            problems.append('fichier manquant : %s' % rel)

    include, skipped = package_files()
    packed = {rel for _src, rel in include}
    if 'manifest.json' not in packed:
        problems.append('manifest.json absent du paquet')
    for rel in sorted(wanted - packed):
        problems.append('fichier non empaquete : %s' % rel)
    if skipped:
        problems.append('a nettoyer dans extension\\ : %s' % ', '.join(skipped))

    if problems:
        for p in problems:
            print('PROBLEME : %s' % p)
        return 1
    print('OK : paquet extension coherent (version %s, %d fichiers)'
          % (ver, len(include)))
    return 0


def build_zip(zip_path=None):
    """Ecrit le paquet et renvoie (chemin, fichiers inclus)."""
    if zip_path is None:
        zip_path = os.path.join(
            DIST_DIR, 'ConvertisseurClavier-extension-%s.zip' % read_version())
    include, _skipped = package_files()
    parent = os.path.dirname(zip_path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as z:
        for src, rel in include:
            info = zipfile.ZipInfo(rel, date_time=ZIP_DATE)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            with open(src, 'rb') as f:
                z.writestr(info, f.read())
    return zip_path, include


def main(argv=None):
    args = list(argv if argv is not None else sys.argv[1:])
    if args == ['--check']:
        return check()
    if args:
        raise SystemExit('argument inconnu : %s' % ' '.join(args))
    if gen_version.main() != 0:
        raise SystemExit('gen_version.py a echoue')
    if check() != 0:
        raise SystemExit('paquet incomplet : corrige les problemes ci-dessus')
    zip_path, include = build_zip()
    print('OK : %s (%d fichiers, %.1f Ko)'
          % (zip_path, len(include), os.path.getsize(zip_path) / 1024.0))
    return 0


if __name__ == '__main__':
    sys.exit(main())
