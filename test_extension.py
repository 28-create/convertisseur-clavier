# -*- coding: utf-8 -*-
"""Test de l'extension navigateur (Manifest V3, Chrome/Edge) : manifeste,
fichiers, icones, absence de code distant ou inline, syntaxe JS, synchronisation
des blocs generes et conversions connues.

Usage : python test_extension.py   (exit 0 = OK, exit 1 = derive detectee)
"""
import json
import os
import re
import shutil
import subprocess
import sys

import gen_maps
from gen_version import read_version

EXT = 'extension'
MANIFEST = os.path.join(EXT, 'manifest.json')
CORE = os.path.join(EXT, 'js', 'core.js')
PERMISSIONS = ['clipboardWrite', 'contextMenus', 'storage']

results = []


def check(name, cond, detail=''):
    results.append(bool(cond))
    print('%s %s %s' % ('PASS' if cond else 'FAIL', name, detail))


def read(path):
    with open(path, encoding='utf-8') as f:
        return f.read()


def png_size(path):
    with open(path, 'rb') as f:
        head = f.read(24)
    if len(head) < 24 or head[:8] != b'\x89PNG\r\n\x1a\n' \
            or head[12:16] != b'IHDR':
        return None
    return (int.from_bytes(head[16:20], 'big'),
            int.from_bytes(head[20:24], 'big'))


def js_files():
    out = []
    for root, _dirs, files in os.walk(EXT):
        for name in files:
            if name.endswith('.js'):
                out.append(os.path.join(root, name))
    return sorted(out)


def run_core(cases):
    """Execute extension/js/core.js sous node. None si node absent."""
    if not shutil.which('node'):
        return None
    prog = (
        'const fs=require("fs"),vm=require("vm");'
        'const ctx={};vm.createContext(ctx);'
        'vm.runInContext(fs.readFileSync(%s,"utf8"),ctx);'
        'const cases=%s;'
        'const out=[];'
        'for(const c of cases){try{'
        'out.push({got:ctx.Conv.convertText(c[0],c[1]),dir:ctx.Conv.detectDir(c[0])});'
        '}catch(e){out.push({err:String(e)});}}'
        'console.log(JSON.stringify(out));'
    ) % (json.dumps(CORE, ensure_ascii=True),
         json.dumps([[t, o] for t, o, _e in cases], ensure_ascii=True))
    r = subprocess.run(['node', '-e', prog], capture_output=True, text=True,
                       encoding='utf-8', errors='replace')
    if r.returncode != 0:
        raise RuntimeError('node a echoue : ' + (r.stderr or '').strip()[:200])
    try:
        return json.loads(r.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        raise RuntimeError('sortie node illisible : ' + repr(r.stdout[:200]))


def run_background():
    """Execute background.js avec des API chrome simulees. None si node absent."""
    if not shutil.which('node'):
        return None
    prog = r'''
const fs = require("fs"), vm = require("vm");
const handlers = {}, menus = [], sent = [];
globalThis.chrome = {
  runtime: {
    onInstalled: { addListener: f => { handlers.installed = f; } },
    onStartup: { addListener: f => { handlers.startup = f; } },
    lastError: null,
  },
  contextMenus: {
    removeAll(cb) { cb(); },
    create(o) { menus.push(o); },
    onClicked: { addListener: f => { handlers.click = f; } },
  },
  commands: { onCommand: { addListener: f => { handlers.command = f; } } },
  storage: {
    local: { get: async () => ({ settings: {
      layout: "qwerty", mode: "hebrew", latinDir: "toAz" } }) },
  },
  tabs: {
    sendMessage(id, msg, cb) { sent.push({ id, msg }); if (cb) cb(); },
  },
};
vm.runInThisContext(fs.readFileSync("extension/background.js", "utf8"));
handlers.installed();
if (handlers.click) handlers.click({ menuItemId: "conv-he" }, { id: 7 });
if (handlers.command) handlers.command("convert-selection", { id: 8 });
setTimeout(() => {
  console.log(JSON.stringify({ menus: menus.map(m => m.id), sent }));
}, 30);
'''
    r = subprocess.run(['node', '-e', prog], capture_output=True, text=True,
                       encoding='utf-8', errors='replace')
    if r.returncode != 0:
        raise RuntimeError('node a echoue : ' + (r.stderr or '').strip()[:200])
    try:
        return json.loads(r.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        raise RuntimeError('sortie node illisible : ' + repr(r.stdout[:200]))


def main():
    if not os.path.isfile(MANIFEST):
        check('manifeste present', False, MANIFEST)
        print('ECHEC : voir ci-dessus')
        return 1
    try:
        m = json.loads(read(MANIFEST))
    except ValueError as e:
        check('manifeste JSON valide', False, str(e)[:120])
        print('ECHEC : voir ci-dessus')
        return 1

    check('manifeste JSON valide', True)
    check('Manifest V3', m.get('manifest_version') == 3,
          str(m.get('manifest_version')))
    ver = read_version()
    check('version == APP_VERSION', m.get('version') == ver,
          '%s/%s' % (m.get('version'), ver))
    check('nom et description', bool(m.get('name')) and bool(m.get('description')))

    sw = (m.get('background') or {}).get('service_worker')
    check('service worker present',
          bool(sw) and os.path.isfile(os.path.join(EXT, sw)), str(sw))
    popup = (m.get('action') or {}).get('default_popup')
    check('popup present',
          bool(popup) and os.path.isfile(os.path.join(EXT, popup)), str(popup))

    icons = m.get('icons') or {}
    icons_ok = set(icons) == {'16', '32', '48', '128'}
    for size, rel in sorted(icons.items()):
        path = os.path.join(EXT, rel)
        dim = png_size(path) if os.path.isfile(path) else None
        if not size.isdigit() or dim != (int(size), int(size)):
            icons_ok = False
    check('icones PNG 16/32/48/128', icons_ok)

    scripts = (m.get('content_scripts') or [{}])[0]
    check('content script sur toutes les pages',
          scripts.get('matches') == ['<all_urls>'])
    check('content script : coeur puis logique',
          scripts.get('js') == ['js/core.js', 'content.js'])
    check('content script dans tous les cadres',
          scripts.get('all_frames') is True)
    for rel in scripts.get('js') or []:
        check('fichier %s' % rel, os.path.isfile(os.path.join(EXT, rel)))

    check('permissions minimales',
          sorted(m.get('permissions') or []) == sorted(PERMISSIONS),
          str(m.get('permissions')))
    check('aucune host_permissions superflue', not m.get('host_permissions'),
          str(m.get('host_permissions')))

    cmd = (m.get('commands') or {}).get('convert-selection') or {}
    check('raccourci convert-selection',
          (cmd.get('suggested_key') or {}).get('default') == 'Ctrl+Shift+H')

    texts = {}
    for root, _dirs, files in os.walk(EXT):
        for name in files:
            if name.endswith(('.js', '.html', '.json', '.css')):
                path = os.path.join(root, name)
                texts[path] = read(path)

    remote = [p for p, t in texts.items() if re.search(r'https?://', t)]
    check('aucune ressource distante', not remote, str(remote))

    inline = []
    for path, text in texts.items():
        if not path.endswith('.html'):
            continue
        if re.search(r'<script\b(?![^>]*\bsrc=)[^>]*>', text):
            inline.append(path)
        if re.search(r'\son[a-z]+\s*=', text):
            inline.append(path)
    check('aucun script ni geste inline (CSP)', not inline, str(inline))

    unsafe = []
    for path, text in texts.items():
        if not path.endswith('.js'):
            continue
        if re.search(r'\.(innerHTML|outerHTML)\s*=|insertAdjacentHTML', text):
            unsafe.append(path)
        if re.search(r'\beval\s*\(|new\s+Function\s*\(', text):
            unsafe.append(path)
    check('pas de HTML injecte ni eval', not unsafe, str(unsafe))

    core = read(CORE)
    html = read('convertisseur.html')
    want_maps = gen_maps.emit_js_maps(gen_maps.parse_js_maps(html),
                                      gen_maps.parse_caps_swap(html))
    want_core = gen_maps.extract_core(html)
    got_maps = re.search('^%s$.*?^%s$' % (re.escape(gen_maps.JS_BEGIN),
                                          re.escape(gen_maps.JS_END)),
                         core, re.S | re.M)
    got_core = re.search('^%s$.*?^%s$' % (re.escape(gen_maps.JS_CORE_BEGIN),
                                          re.escape(gen_maps.JS_CORE_END)),
                         core, re.S | re.M)
    check('tables generees a jour',
          bool(got_maps) and got_maps.group(0) ==
          gen_maps.JS_BEGIN + '\n' + want_maps + gen_maps.JS_END)
    check('coeur genere a jour',
          bool(got_core) and got_core.group(0) ==
          gen_maps.JS_CORE_BEGIN + '\n' + want_core + gen_maps.JS_CORE_END)

    if shutil.which('node'):
        bad = None
        for path in js_files():
            r = subprocess.run(['node', '--check', path], capture_output=True,
                               text=True, encoding='utf-8', errors='replace')
            if r.returncode != 0:
                bad = (path, (r.stderr or '').strip()[:160])
                break
        check('syntaxe JS (node --check)', bad is None, str(bad or ''))
    else:
        print('PASS syntaxe JS ignore (node indisponible)')

    cases = [
        ('qkuo', {}, 'שלום'),
        ('שלום', {}, 'qkuo'),
        ('akuo', {'layout': 'qwerty'}, 'שלום'),
        ('Bםמחםור', {}, 'Bonjour'),
        ('Salut, נםמחםור !', {}, 'Salut, bonjour !'),
        ('bonjour', {'direction': 'toHe'}, 'נםמחםור'),
        ('qwerty', {'mode': 'latin'}, 'azerty'),
        ('azerty', {'mode': 'latin', 'latinDir': 'toQw'}, 'qwerty'),
    ]
    try:
        got = run_core(cases)
    except RuntimeError as e:
        got = None
        check('conversions (node)', False, str(e))
    if got is None:
        print('PASS conversions ignore (node indisponible)')
    else:
        for (text, _opts, exp), row in zip(cases, got):
            if row.get('err') or row.get('got') != exp:
                check('conversion %s' % ascii(text), False,
                      '%s (attendu %s)' % (
                          ascii(row.get('got') or row.get('err')),
                          ascii(exp)))
            else:
                check('conversion %s' % ascii(text), True)
        check('detection du sens', all(
            row.get('dir') == want for row, want in zip(
                got, ['toHe', 'toFr', 'toHe', 'toFr', 'toFr', 'toHe', 'toHe', 'toHe'])),
            str([row.get('dir') for row in got]))

    try:
        bg = run_background()
    except RuntimeError as e:
        bg = None
        check('menu clic droit (node)', False, str(e))
    if bg is None:
        print('PASS menu clic droit ignore (node indisponible)')
    else:
        sent = bg.get('sent') or []
        check('3 entrees de menu', bg.get('menus') ==
              ['conv-auto', 'conv-he', 'conv-fr'], str(bg.get('menus')))
        first = ((sent[0] if sent else {}).get('msg') or {}).get('opts') or {}
        check('clic droit vers le champ actif',
              len(sent) == 2 and sent[0].get('id') == 7
              and sent[0]['msg'].get('type') == 'conv-selection'
              and first.get('direction') == 'toHe'
              and first.get('layout') == 'qwerty', str(sent[:1]))
        second = ((sent[1] if len(sent) > 1 else {}).get('msg') or {}).get('opts') or {}
        check('raccourci = auto',
              len(sent) == 2 and sent[1].get('id') == 8
              and second.get('direction') == 'auto', str(sent[1:2]))

    ok = all(results)
    print(('OK : extension (%d verifications)' % len(results)) if ok
          else 'ECHEC : voir ci-dessus')
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
