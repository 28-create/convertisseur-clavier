# -*- coding: utf-8 -*-
"""Construit dist\\ConvertisseurClavier-<version>.exe (nom versionne).

Usage : python build_exe.py [--dist DOSSIER]
Etapes : gen_version.py -> PyInstaller (noconsole, onefile, version-file,
page et script presse-papiers embarques, icone app.ico si presente). Cible Windows uniquement.
Le nom du .exe reprend toujours APP_VERSION :
impossible de publier un exe sans version dans son nom.
--dist cible un autre dossier de sortie (utile si l'antivirus
surveille le dossier du projet) ; le fichier est ensuite a
copier dans dist\\.
Necessite : pip install pywebview pyinstaller (+ WebView2 sur la machine).
"""
import os
import re
import subprocess
import sys

APP = 'app.py'
HTML = 'convertisseur.html'
FIX = 'fix-presse-papiers.py'
ICON = 'app.ico'


def read_version(html_path=HTML):
    with open(html_path, encoding='utf-8') as f:
        m = re.search(r"const APP_VERSION = '([^']+)'", f.read())
    if not m:
        raise SystemExit('APP_VERSION introuvable dans %s' % html_path)
    return m.group(1)


def main(argv=None):
    if sys.platform != 'win32':
        raise SystemExit('build_exe.py cible Windows uniquement '
                         '(PyInstaller --onefile / --version-file).')
    outdir = 'dist'
    args = list(argv if argv is not None else sys.argv[1:])
    while args and args[0] == '--dist':
        args.pop(0)
        if not args:
            raise SystemExit('il manque le dossier apres --dist')
        outdir = args.pop(0)
    if args:
        raise SystemExit('argument inconnu : %s' % ' '.join(args))
    ver = read_version()
    import gen_version
    if gen_version.main() != 0:
        raise SystemExit('gen_version.py a echoue')
    name = 'ConvertisseurClavier-%s' % ver
    cmd = [sys.executable, '-m', 'PyInstaller', '--noconsole', '--onefile',
           '--version-file', 'version_info.txt',
           '--distpath', outdir,
           '--add-data', HTML + os.pathsep + '.',
           '--add-data', FIX + os.pathsep + '.',
           '--name', name]
    if os.path.exists(ICON):
        cmd += ['--icon', ICON]
    cmd.append(APP)
    print('+ ' + ' '.join(cmd))
    r = subprocess.run(cmd)
    if r.returncode != 0:
        raise SystemExit('build echoue (%d)' % r.returncode)
    exe = os.path.join(outdir, name + '.exe')
    if not os.path.exists(exe):
        raise SystemExit('introuvable apres build : %s' % exe)
    print('OK : %s (%.1f Mo)' % (exe, os.path.getsize(exe) / 1048576))
    return 0


if __name__ == '__main__':
    sys.exit(main())
