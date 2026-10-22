# -*- coding: utf-8 -*-
"""Prepare et publie une release (bump, tests, build, release GitHub).

Usage :
  python release.py --check
  python release.py --bump minor --summary "detection plus fiable" --yes
  python release.py --version 1.14.0 --notes-file C:\\tmp\\notes.md --yes

Le script exige un arbre propre (sauf CHANGELOG.md) et une section
"## vX.Y.Z" dans CHANGELOG.md. Il enchaine ensuite : bump de APP_VERSION,
gen_version.py, tests, commit, tag, test_page.py, build, SHA256SUMS,
push et creation de la release GitHub via l'API (corps JSON UTF-8).

Options utiles :
  --skip-tests      ne pas rejouer les suites avant le commit
  --skip-build      ne pas construire exe / Setup / extension
  --skip-publish    commit + tag + build locaux, sans push ni release
  --dry-run         affiche le plan sans rien modifier
  --notes-file F    corps de release explicite (sinon section CHANGELOG)
  --branch NAME     branche distante cible (master par defaut)
"""
import argparse
import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.abspath(__file__))
HTML = 'convertisseur.html'
CHANGELOG = 'CHANGELOG.md'
VERSION_RE = re.compile(r"const APP_VERSION = '(\d+\.\d+\.\d+)'")
TESTS = [
    'test_maps.py',
    'test_app.py',
    'test_paste.py',
    'test_ngrams.py',
    'test_extension.py',
    'test_store.py',
]
TAG_TEST = 'test_page.py'

# Corps commun ajoute aux notes de release (source ASCII, sortie UTF-8).
DOWNLOADS = """## T\u00e9l\u00e9chargements

- **`Setup_ConvertisseurClavier-%(v)s.exe`** : installation compl\u00e8te (assistant, menu D\u00e9marrer, raccourcis, menu clic droit et surveillance du presse-papiers).
- **`ConvertisseurClavier-%(v)s.exe`** : application portable.
- **`ConvertisseurClavier-extension-%(v)s.zip`** : extension Chrome/Edge \u00e0 charger non empaquet\u00e9e.
- **`installer.ps1` / `desinstaller.ps1`** : installation et d\u00e9sinstallation en PowerShell.
- **`SHA256SUMS-%(v)s.txt`** : empreintes SHA-256 des fichiers.
"""


def safe(text):
    """Sortie console ASCII (les consoles Windows cp1252/cp1255 cassent sinon)."""
    return text.encode('ascii', 'replace').decode('ascii')


def run(cmd, check=True):
    """Execute une commande en streamant sa sortie."""
    print('+ ' + safe(' '.join(cmd)))
    result = subprocess.run(cmd)
    if check and result.returncode != 0:
        raise SystemExit('ECHEC : %s (code %d)' % (safe(' '.join(cmd)), result.returncode))
    return result


def git(*args, **kwargs):
    """Execute git et renvoie la sortie standard (ou leve une erreur)."""
    cmd = ['git'] + list(args)
    result = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True,
                            encoding='utf-8', errors='replace', **kwargs)
    if result.returncode != 0:
        raise SystemExit('ECHEC git %s\n%s' % (' '.join(args), safe(result.stderr.strip())))
    return result.stdout


def read_version():
    with open(os.path.join(ROOT, HTML), encoding='utf-8') as f:
        match = VERSION_RE.search(f.read())
    if not match:
        raise SystemExit('APP_VERSION introuvable dans %s' % HTML)
    return match.group(1)


def bump_version(current, kind):
    major, minor, patch = [int(part) for part in current.split('.')]
    if kind == 'major':
        major, minor, patch = major + 1, 0, 0
    elif kind == 'minor':
        minor, patch = minor + 1, 0
    else:
        patch += 1
    return '%d.%d.%d' % (major, minor, patch)


def tag_exists(version):
    result = subprocess.run(['git', 'rev-parse', '-q', '--verify', 'refs/tags/v' + version],
                            cwd=ROOT, capture_output=True)
    return result.returncode == 0


def check_clean():
    """Arbre propre, sauf CHANGELOG.md qui peut etre prepare pour la release."""
    status = git('status', '--porcelain')
    blockers = []
    for line in status.splitlines():
        if not line.strip():
            continue
        path = line[3:].strip().strip('"')
        if path != CHANGELOG:
            blockers.append(line)
    if blockers:
        raise SystemExit('Arbre non propre (committer ou remiser avant la release) :\n'
                         + safe('\n'.join(blockers)))


def check_sync(branch):
    """origin/<branch> doit etre un ancetre de HEAD (pas de commit distant en avance)."""
    git('fetch', 'origin', '--tags')
    try:
        git('rev-parse', '--verify', 'origin/' + branch)
    except SystemExit:
        raise SystemExit('branche distante introuvable : origin/%s' % branch)
    result = subprocess.run(['git', 'merge-base', '--is-ancestor',
                             'origin/' + branch, 'HEAD'], cwd=ROOT)
    if result.returncode != 0:
        raise SystemExit("origin/%s n'est pas un ancetre de HEAD : mettre la branche a jour."
                         % branch)


def check_gh():
    if not shutil.which('gh'):
        raise SystemExit('gh introuvable : installer GitHub CLI pour publier la release.')
    result = subprocess.run(['gh', 'auth', 'status'], cwd=ROOT,
                            capture_output=True, text=True,
                            encoding='utf-8', errors='replace')
    if result.returncode != 0:
        raise SystemExit('gh n\'est pas authentifie : lancer "gh auth login".')


def find_iscc():
    try:
        import build_setup
        return build_setup.find_iscc()
    except Exception:
        return shutil.which('ISCC.exe')


def check_build_tools():
    if sys.platform != 'win32':
        print('INFO : build exe/Setup ignore (plateforme %s).' % sys.platform)
        return
    if importlib.util.find_spec('PyInstaller') is None:
        raise SystemExit('PyInstaller absent : pip install pyinstaller pywebview')
    if importlib.util.find_spec('webview') is None:
        raise SystemExit('pywebview absent : pip install pywebview')
    if find_iscc() is None:
        raise SystemExit('Inno Setup 6 introuvable (ISCC.exe).')


def changelog_section(text, version):
    marker = '## v%s' % version
    start = text.find(marker)
    if start < 0:
        return None
    end = text.find('\n## ', start + len(marker))
    section = text[start:end if end >= 0 else len(text)]
    return section.strip()


def release_body(section, notes, version):
    body = (notes if notes is not None else section).strip()
    marker = '## T\u00e9l\u00e9chargements'
    if marker not in body:
        body += '\n\n' + (DOWNLOADS % {'v': version}).strip()
    return body + '\n'


def replace_version(version):
    path = os.path.join(ROOT, HTML)
    with open(path, encoding='utf-8') as f:
        text = f.read()
    text, count = re.subn(r"const APP_VERSION = '\d+\.\d+\.\d+';",
                          "const APP_VERSION = '%s';" % version, text, count=1)
    if count != 1:
        raise SystemExit('APP_VERSION introuvable dans %s' % HTML)
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(text)


def expected_files(version, dist):
    return [
        os.path.join(dist, 'Setup_ConvertisseurClavier-%s.exe' % version),
        os.path.join(dist, 'ConvertisseurClavier-%s.exe' % version),
        os.path.join(dist, 'ConvertisseurClavier-extension-%s.zip' % version),
        'installer.ps1',
        'desinstaller.ps1',
    ]


def write_checksums(version, dist, assets):
    path = os.path.join(dist, 'SHA256SUMS-%s.txt' % version)
    lines = []
    for asset in assets:
        if not os.path.exists(os.path.join(ROOT, asset)):
            raise SystemExit('asset absent : %s' % asset)
        with open(os.path.join(ROOT, asset), 'rb') as f:
            digest = hashlib.sha256(f.read()).hexdigest()
        lines.append('%s  %s' % (digest, os.path.basename(asset)))
    with open(os.path.join(ROOT, path), 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(lines) + '\n')
    print('OK : %s' % path)
    return path


def build_assets(version, dist):
    if not os.path.isdir(os.path.join(ROOT, dist)):
        os.makedirs(os.path.join(ROOT, dist))
    if sys.platform == 'win32':
        run([sys.executable, 'build_exe.py'])
        run([sys.executable, 'build_setup.py'])
    else:
        print('INFO : exe et Setup ignores (Windows uniquement).')
    run([sys.executable, 'build_extension.py'])
    assets = expected_files(version, dist)
    checksums = write_checksums(version, dist, assets)
    return assets + [checksums]


def publish(version, body, assets):
    slug = subprocess.check_output(
        ['gh', 'repo', 'view', '--json', 'nameWithOwner', '-q', '.nameWithOwner'],
        cwd=ROOT, text=True, encoding='utf-8', errors='replace').strip()
    payload = {
        'tag_name': 'v' + version,
        'name': 'Convertisseur Clavier ' + version,
        'draft': False,
        'prerelease': False,
        'body': body,
    }
    fd, tmp = tempfile.mkstemp(prefix='release-', suffix='.json')
    os.close(fd)
    try:
        with open(tmp, 'w', encoding='utf-8', newline='') as f:
            json.dump(payload, f, ensure_ascii=False)
        run(['gh', 'api', '--method', 'POST',
             'repos/%s/releases' % slug, '--input', tmp])
    finally:
        os.unlink(tmp)
    if assets:
        run(['gh', 'release', 'upload', 'v' + version] + assets + ['--clobber'])
    print('OK : https://github.com/%s/releases/tag/v%s' % (slug, version))


def read_notes(path):
    if not path:
        return None
    with open(path, encoding='utf-8') as f:
        return f.read()


def main(argv=None):
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(line_buffering=True)
    parser = argparse.ArgumentParser(description='Prepare et publie une release.')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--version', help='version cible X.Y.Z')
    group.add_argument('--bump', choices=('patch', 'minor', 'major'),
                       default='minor', help='increment (minor par defaut)')
    parser.add_argument('--summary', default='mise a jour',
                        help='resume pour le commit de release')
    parser.add_argument('--notes-file', help='corps de release (UTF-8)')
    parser.add_argument('--branch', default='master', help='branche distante cible')
    parser.add_argument('--dist', default='dist', help='dossier des binaires')
    parser.add_argument('--check', action='store_true', help='verifie sans modifier')
    parser.add_argument('--dry-run', action='store_true', help='affiche le plan')
    parser.add_argument('--skip-tests', action='store_true')
    parser.add_argument('--skip-build', action='store_true')
    parser.add_argument('--skip-publish', action='store_true')
    parser.add_argument('--yes', action='store_true', help='ne pas demander confirmation')
    args = parser.parse_args(argv)

    os.chdir(ROOT)
    current = read_version()
    target = args.version or bump_version(current, args.bump)
    if not re.match(r'^\d+\.\d+\.\d+$', target):
        raise SystemExit('version invalide : %s (format X.Y.Z)' % target)
    if tuple(int(p) for p in target.split('.')) <= tuple(int(p) for p in current.split('.')):
        raise SystemExit('la nouvelle version %s doit etre superieure a %s' % (target, current))
    if tag_exists(target):
        raise SystemExit('le tag v%s existe deja' % target)

    print('version actuelle : %s' % current)
    print('version cible    : %s' % target)

    check_clean()
    check_sync(args.branch)
    if not args.skip_publish:
        check_gh()
    if not args.skip_build:
        check_build_tools()

    with open(os.path.join(ROOT, CHANGELOG), encoding='utf-8') as f:
        section = changelog_section(f.read(), target)
    if section is None and not args.check:
        raise SystemExit('section "## v%s" absente de %s : la rediger avant la release.'
                         % (target, CHANGELOG))
    if section is None:
        print('WARN : section "## v%s" absente de %s' % (target, CHANGELOG))

    if args.check:
        print('OK : environnement pret pour v%s' % target)
        return 0

    body = release_body(section, read_notes(args.notes_file), target)
    print('--- notes de release ---')
    print(safe(body))
    if args.dry_run:
        print('DRY-RUN : aucune modification.')
        return 0

    if not args.yes:
        answer = input('Publier v%s ? [o/N] ' % target).strip().lower()
        if answer not in ('o', 'oui', 'y', 'yes'):
            raise SystemExit('annule')

    # 1. Version + fichiers derives.
    replace_version(target)
    run([sys.executable, 'gen_version.py'])

    # 2. Tests avant commit.
    if not args.skip_tests:
        for test in TESTS:
            if os.path.exists(os.path.join(ROOT, test)):
                run([sys.executable, test])
            else:
                print('INFO : %s absent, ignore.' % test)

    # 3. Commit et tag locaux.
    generated = [HTML, 'version_info.txt', 'extension/manifest.json', 'installer.iss']
    git('add', CHANGELOG, *generated)
    message = 'Release v%s : %s' % (target, args.summary)
    git('commit', '-m', message)
    git('tag', 'v' + target)
    print('OK : commit + tag v%s' % target)

    # 4. test_page compare APP_VERSION au dernier tag : apres le tag.
    if not args.skip_tests and os.path.exists(os.path.join(ROOT, TAG_TEST)):
        run([sys.executable, TAG_TEST])

    # 5. Binaires + empreintes.
    assets = []
    if not args.skip_build:
        assets = build_assets(target, args.dist)
    else:
        print('INFO : build ignore.')

    # 6. Push puis release GitHub.
    if args.skip_publish:
        print('OK : release locale prete (push et publication ignores).')
        return 0
    git('push', 'origin', 'HEAD:' + args.branch)
    git('push', 'origin', 'v' + target)
    publish(target, body, assets)
    print('OK : release v%s publiee.' % target)
    return 0


if __name__ == '__main__':
    sys.exit(main())
