# -*- coding: utf-8 -*-
"""Construit dist\\Setup_ConvertisseurClavier-<version>.exe via Inno Setup.

Usage :
  python build_setup.py          (compile avec ISCC.exe, Windows uniquement)
  python build_setup.py --check  (verifie la coherence sans compiler :
                                  version, sections, menu contextuel,
                                  surveillance au demarrage)

Etapes : gen_version.py (synchronise installer.iss) -> ISCC installer.iss.
Le .exe versionne doit exister dans dist\\ (voir build_exe.py).
Inno Setup 6 : https://jrsoftware.org/isdl.php (ISCC.exe ajoute au PATH
ou dans C:\\Program Files (x86)\\Inno Setup 6\\).
"""
import os
import re
import shutil
import subprocess
import sys

ISS_FILE = 'installer.iss'

REQUIRED_TOKENS = [
    '#define MyAppVersion',
    'PrivilegesRequired=lowest',
    'Tasks: contextmenu',
    'Software\\Classes\\*\\shell\\ConvertisseurClavier',
    'SystemFileAssociations\\.txt\\shell\\ConvertirClavier',
    'Software\\Classes\\Directory\\shell\\ConvertisseurClavier',
    'Software\\Classes\\Directory\\Background\\shell\\ConvertisseurClavier',
    '--convert-clipboard',
    '--convert-file',
    '--paste-watch',
    '--paste-stop',
    'Software\\Microsoft\\Windows\\CurrentVersion\\Run',
    'Tasks: surveillance',
    '[UninstallRun]',
    'HotKey',
]

ISCC_CANDIDATES = [
    'ISCC.exe',
    'iscc',
    r'C:\Program Files (x86)\Inno Setup 6\ISCC.exe',
    r'C:\Program Files\Inno Setup 6\ISCC.exe',
]


def _user_iscc():
    # Installation per-user (sans admin) : %LOCALAPPDATA%\Programs\Inno...
    local = os.environ.get('LOCALAPPDATA')
    if not local:
        return []
    return [os.path.join(local, 'Programs', 'Inno Setup 6', 'ISCC.exe'),
            os.path.join(local, 'Programs', 'Inno', 'ISCC.exe')]


def read_version(html_path='convertisseur.html'):
    with open(html_path, encoding='utf-8') as f:
        m = re.search(r"const APP_VERSION = '([^']+)'", f.read())
    if not m:
        raise SystemExit('APP_VERSION introuvable dans %s' % html_path)
    return m.group(1)


def iss_version(iss_path=ISS_FILE):
    with open(iss_path, encoding='utf-8') as f:
        m = re.search(r'#define MyAppVersion "([^"]+)"', f.read())
    if not m:
        raise SystemExit('MyAppVersion introuvable dans %s' % iss_path)
    return m.group(1)


def check():
    ver = read_version()
    iver = iss_version()
    problems = []
    if iver != ver:
        problems.append('version iss=%s, page=%s' % (iver, ver))
    with open(ISS_FILE, encoding='utf-8') as f:
        iss = f.read()
    for tok in REQUIRED_TOKENS:
        if tok not in iss:
            problems.append('manquant dans installer.iss : %s' % tok)
    if problems:
        for p in problems:
            print('MANQUE : %s' % p)
        return 1
    print('OK : installer.iss coherent (version %s, menu contextuel, '
          'surveillance)' % ver)
    return 0


def find_iscc():
    env = os.environ.get('INNO_ISCC')
    if env and os.path.exists(env):
        return env
    for cand in ISCC_CANDIDATES + _user_iscc():
        if os.path.isabs(cand):
            if os.path.exists(cand):
                return cand
        elif shutil.which(cand):
            return shutil.which(cand)
    return None


def main(argv=None):
    args = list(argv if argv is not None else sys.argv[1:])
    if args == ['--check']:
        return check()
    if args:
        raise SystemExit('argument inconnu : %s' % ' '.join(args))
    if sys.platform != 'win32':
        raise SystemExit('build_setup.py compile sur Windows uniquement '
                         '(ISCC.exe) ; --check reste possible partout.')
    import gen_version
    if gen_version.main() != 0:
        raise SystemExit('gen_version.py a echoue')
    ver = read_version()
    exe = os.path.join('dist', 'ConvertisseurClavier-%s.exe' % ver)
    if not os.path.exists(exe):
        raise SystemExit('introuvable : %s (lance python build_exe.py)' % exe)
    iscc = find_iscc()
    if not iscc:
        raise SystemExit('ISCC.exe introuvable : installe Inno Setup 6 '
                         '(https://jrsoftware.org/isdl.php) puis relance.')
    cmd = [iscc, ISS_FILE, '/Odist']
    print('+ ' + ' '.join(cmd))
    r = subprocess.run(cmd)
    if r.returncode != 0:
        raise SystemExit('compilation echouee (%d)' % r.returncode)
    setup = os.path.join('dist', 'Setup_ConvertisseurClavier-%s.exe' % ver)
    if not os.path.exists(setup):
        raise SystemExit('introuvable apres compilation : %s' % setup)
    print('OK : %s (%.1f Mo)' % (setup, os.path.getsize(setup) / 1048576))
    return 0


if __name__ == '__main__':
    sys.exit(main())
