# -*- coding: utf-8 -*-
"""Construit l'application Windows versionnee (APP_VERSION).

Usage : python build_exe.py [--dist DOSSIER] [--onedir] [--onefile]

Etapes : gen_version.py -> PyInstaller. Deux artefacts :
  dist\\ConvertisseurClavier-<version>\\ConvertisseurClavier.exe
      build --onedir (dossier complet) : demarrage rapide, installe par le
      Setup (installer.iss) et par installer.ps1.
  dist\\ConvertisseurClavier-<version>.exe
      build --onefile (portable, un seul fichier) : demarrage plus lent
      (extraction a chaque lancement) mais copiable seul.
Les deux sont construits par defaut ; --onedir ou --onefile n'en construit
qu'un (build plus court).
Le nom du .exe reprend toujours APP_VERSION : impossible de publier un exe
sans version dans son nom.
--dist cible un autre dossier de sortie (utile si l'antivirus
surveille le dossier du projet) ; les fichiers sont ensuite a
copier dans dist\\.
Necessite : pip install pywebview pyinstaller (+ WebView2 sur la machine).
"""
import os
import re
import shutil
import subprocess
import sys

APP = 'app.py'
HTML = 'convertisseur.html'
FIX = 'fix-presse-papiers.py'
ICON = 'app.ico'
LOGO = os.path.join('extension', 'icons', 'icon128.png')
# Nom fixe du binaire dans le dossier --onedir : le Setup, les raccourcis et
# la cle Run pointent tous vers {app}\ConvertisseurClavier.exe.
SHORT_NAME = 'ConvertisseurClavier'


def read_version(html_path=HTML):
    with open(html_path, encoding='utf-8') as f:
        m = re.search(r"const APP_VERSION = '([^']+)'", f.read())
    if not m:
        raise SystemExit('APP_VERSION introuvable dans %s' % html_path)
    return m.group(1)


def folder_size(path):
    total = 0
    files = 0
    for root, _dirs, names in os.walk(path):
        for name in names:
            try:
                total += os.path.getsize(os.path.join(root, name))
            except OSError:
                pass
            files += 1
    return total / 1048576, files


def pyinstaller(name, onedir, outdir):
    cmd = [sys.executable, '-m', 'PyInstaller', '--noconfirm', '--noconsole',
           '--onedir' if onedir else '--onefile',
           '--version-file', 'version_info.txt',
           '--distpath', outdir,
           '--add-data', HTML + os.pathsep + '.',
           '--add-data', FIX + os.pathsep + '.',
           '--hidden-import', 'paste_watch',
           '--hidden-import', 'win32_clip',
           '--name', name]
    if os.path.exists(ICON):
        # L'icone sert a la fois de ressource de l'exe et d'image de la
        # zone de notification (chargee depuis le bundle au demarrage).
        cmd += ['--icon', ICON,
                '--add-data', ICON + os.pathsep + '.']
    if os.path.exists(LOGO):
        # Le logo carre du popup, deja optimise pour l'extension.
        cmd += ['--add-data', LOGO + os.pathsep + '.']
    cmd.append(APP)
    print('+ ' + ' '.join(cmd))
    r = subprocess.run(cmd)
    if r.returncode != 0:
        raise SystemExit('build echoue (%d)' % r.returncode)


def build_onedir(ver, outdir):
    # Dossier complet : aucun fichier a extraire au lancement (le --onefile
    # decompresse ~30 Mo sous %TEMP% a chaque demarrage : plusieurs secondes).
    target = os.path.join(outdir, 'ConvertisseurClavier-%s' % ver)
    raw = os.path.join(outdir, SHORT_NAME)
    for path in (target, raw):
        if os.path.isdir(path):
            shutil.rmtree(path)
    pyinstaller(SHORT_NAME, True, outdir)
    exe = os.path.join(raw, SHORT_NAME + '.exe')
    if not os.path.exists(exe):
        raise SystemExit('introuvable apres build : %s' % exe)
    os.replace(raw, target)
    exe = os.path.join(target, SHORT_NAME + '.exe')
    size, files = folder_size(target)
    print('OK : %s (%.1f Mo, %d fichiers)' % (exe, size, files))
    return exe


def build_onefile(ver, outdir):
    name = 'ConvertisseurClavier-%s' % ver
    pyinstaller(name, False, outdir)
    exe = os.path.join(outdir, name + '.exe')
    if not os.path.exists(exe):
        raise SystemExit('introuvable apres build : %s' % exe)
    print('OK : %s (%.1f Mo)' % (exe, os.path.getsize(exe) / 1048576))
    return exe


def main(argv=None):
    if sys.platform != 'win32':
        raise SystemExit('build_exe.py cible Windows uniquement '
                         '(PyInstaller --onefile / --onedir / --version-file).')
    outdir = 'dist'
    want_onedir = True
    want_onefile = True
    args = list(argv if argv is not None else sys.argv[1:])
    while args:
        arg = args.pop(0)
        if arg == '--dist':
            if not args:
                raise SystemExit('il manque le dossier apres --dist')
            outdir = args.pop(0)
        elif arg == '--onedir':
            want_onefile = False
        elif arg == '--onefile':
            want_onedir = False
        else:
            raise SystemExit('argument inconnu : %s' % arg)
    if not os.path.isdir(outdir):
        os.makedirs(outdir)
    ver = read_version()
    import gen_version
    if gen_version.main() != 0:
        raise SystemExit('gen_version.py a echoue')
    if want_onedir:
        build_onedir(ver, outdir)
    if want_onefile:
        build_onefile(ver, outdir)
    return 0


if __name__ == '__main__':
    sys.exit(main())
