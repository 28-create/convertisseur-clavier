# -*- coding: utf-8 -*-
"""Construit dist\\ConvertisseurClavier-<version>.exe (nom versionne).

Usage : python build_exe.py
Etapes : gen_version.py -> PyInstaller (noconsole, onefile, version-file,
page embarquee). Le nom du .exe reprend toujours APP_VERSION :
impossible de publier un exe sans version dans son nom.
Necessite : pip install pywebview pyinstaller (+ WebView2 sur la machine).
"""
import os
import re
import subprocess
import sys

APP = 'app.py'
HTML = 'convertisseur.html'


def read_version(html_path=HTML):
    with open(html_path, encoding='utf-8') as f:
        m = re.search(r"const APP_VERSION = '([^']+)'", f.read())
    if not m:
        raise SystemExit('APP_VERSION introuvable dans %s' % html_path)
    return m.group(1)


def main():
    ver = read_version()
    import gen_version
    if gen_version.main() != 0:
        raise SystemExit('gen_version.py a echoue')
    name = 'ConvertisseurClavier-%s' % ver
    cmd = [sys.executable, '-m', 'PyInstaller', '--noconsole', '--onefile',
           '--version-file', 'version_info.txt',
           '--add-data', 'convertisseur.html;.',
           '--name', name, APP]
    print('+ ' + ' '.join(cmd))
    r = subprocess.run(cmd)
    if r.returncode != 0:
        raise SystemExit('build echoue (%d)' % r.returncode)
    exe = os.path.join('dist', name + '.exe')
    if not os.path.exists(exe):
        raise SystemExit('introuvable apres build : %s' % exe)
    print('OK : %s (%.1f Mo)' % (exe, os.path.getsize(exe) / 1048576))
    return 0


if __name__ == '__main__':
    sys.exit(main())
