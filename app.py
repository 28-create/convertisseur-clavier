# -*- coding: utf-8 -*-
r"""Application Windows : la page convertisseur dans une fenetre native.

Dev (fenetre) :  python app.py [fichier.txt]
Build (.exe)   :  python build_exe.py  (nom versionne : dist\ConvertisseurClavier-X.Y.Z.exe)
Necessite le runtime WebView2 (present par defaut sur Windows 11
et la plupart des Windows 10 a jour).

Verbes pour le menu contextuel et les touches globales :
  app.py fichier.txt           ouvre la fenetre avec le contenu precharge
  app.py --convert-clipboard   convertit le presse-papiers, sans fenetre
                               (selectionnez dans Word/navigateur : Ctrl+C,
                               touche globale, Ctrl+V)
  app.py --convert-file f.txt  convertit un fichier texte vers
                               f.converti.txt, sans fenetre
  app.py --paste-watch         surveille le presse-papiers et propose la
                               conversion avant Ctrl+V (zone de notification)
  app.py --paste-stop          arrete la surveillance en cours

La logique de conversion vient de fix-presse-papiers.py (lui-meme
genere depuis convertisseur.html) : aucune table dupliquee ici.
"""
import argparse
import os
import sys

from win32_clip import win32_clip as _win32_clip

APP_TITLE = 'Convertisseur Clavier Latin ⇄ Hébreu'
HTML_NAME = 'convertisseur.html'
FIX_NAME = 'fix-presse-papiers.py'
# Limite de prechargement (texte injecte dans la fenetre apres chargement).
MAX_PRELOAD = 100000

# Page de chargement minimale : s'affiche instantanement pour que la fenetre
# soit visible sans attendre l'initialisation complete de WebView2 (~2-3 s).
# Une fois visible, cmd_gui navigue vers convertisseur.html.
LOADING_HTML = ('<!DOCTYPE html><html lang="fr"><head><meta charset="utf-8">'
                '<title>Convertisseur Clavier</title></head>'
                '<body style="font-family:system-ui,sans-serif;'
                'display:flex;flex-direction:column;align-items:center;'
                'justify-content:center;height:100vh;margin:0;'
                'background:#f4f6fb;color:#0b1f3a;">'
                '<div style="font-size:1.2rem;font-weight:600;">'
                'Convertisseur Clavier</div>'
                '<div style="margin-top:.75rem;color:#475569;">Chargement...</div>'
                '</body></html>')


def bundle_dir():
    # PyInstaller (onefile et onedir) : fichiers embarques sous sys._MEIPASS
    # (_internal pour un build --onedir) ; sinon : dossier de ce script.
    if getattr(sys, '_MEIPASS', None):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))


def page_path():
    return os.path.join(bundle_dir(), HTML_NAME)


def load_fix():
    # Charge fix-presse-papiers.py malgre le tiret (import classique
    # impossible) : la conversion reste definie a un seul endroit.
    import importlib.util
    path = os.path.join(bundle_dir(), FIX_NAME)
    if not os.path.exists(path):
        here = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(here, FIX_NAME)
    spec = importlib.util.spec_from_file_location('fix_presse_papiers', path)
    if spec is None or spec.loader is None:
        raise SystemExit('Introuvable : %s' % path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def read_text_file(path):
    # Fichiers Windows : UTF-8 d'abord (avec ou sans BOM), sinon ANSI.
    # ANSI : cp1255 (hebreu Windows) uniquement si le decodage donne un
    # texte majoritairement hebreu, sinon un fichier cp1252 accentue
    # serait pris a tort pour de l'hebreu ; repli cp1252 sans plantage.
    with open(path, 'rb') as f:
        raw = f.read()
    for enc in ('utf-8-sig', 'utf-8'):
        try:
            return raw.decode(enc)
        except (UnicodeDecodeError, ValueError):
            continue
    try:
        he = raw.decode('cp1255')
    except (UnicodeDecodeError, ValueError):
        he = ''
    heb = sum(1 for ch in he if '\u0590' <= ch <= '\u05ff')
    lat = sum(1 for ch in he if ch.isascii() and ch.isalpha())
    if heb and heb > lat:
        return he
    return raw.decode('cp1252', errors='replace')


def convert_text(mod, text, layout, direction, mode, latin_dir):
    if mode == 'latin':
        out = mod.convert(text, mod.LATIN_MAPS[latin_dir])
        return out, 'latin %s' % latin_dir
    to_he, to_fr = mod.MAPS[layout]
    direction = mod.autodir(text) if direction == 'auto' else direction
    to_french = direction == 'toFr'
    full = to_fr if to_french else to_he
    swap = mod.CAPS_SWAP if layout == 'azerty' else None
    out = mod.convert_smart(text, full, swap, to_french)
    langue = {'azerty': 'francais', 'qwerty': 'anglais'}[layout]
    return out, '%s %s' % (langue, direction)


def show_msg(text, error=False):
    # Exe --noconsole : aucun affichage console possible. Un message
    # bloquant (MessageBox) n'est ouvert que pour une ERREUR : une
    # conversion reussie depuis le menu clic droit reste silencieuse
    # (le fichier .converti.txt apparait a cote de l'original) et ne
    # bloque jamais le processus.
    # En dev (console), simple print avec repli ASCII.
    if getattr(sys, 'frozen', False) and sys.platform == 'win32':
        if not error:
            return
        try:
            import ctypes
            ctypes.windll.user32.MessageBoxW(None, text, APP_TITLE, 0x30)
        except Exception:
            pass
        return
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode('ascii', 'backslashreplace').decode('ascii'))


def cmd_clipboard(mod, args):
    if sys.platform == 'win32':
        try:
            clip_get, clip_set = _win32_clip()
        except Exception:
            clip_get, clip_set = mod.get_clipboard, mod.set_clipboard
    else:
        clip_get, clip_set = mod.get_clipboard, mod.set_clipboard
    try:
        src = clip_get()
    except Exception as e:
        show_msg('Lecture du presse-papiers impossible : %s' % e, error=True)
        return 1
    if not src:
        show_msg('Presse-papiers vide (ou texte manquant).', error=True)
        return 1
    out, tag = convert_text(mod, src, args.layout, args.direction,
                            args.mode, args.latin_dir)
    try:
        clip_set(out)
    except Exception as e:
        show_msg('Ecriture du presse-papiers impossible : %s' % e, error=True)
        return 1
    if not getattr(sys, 'frozen', False):
        show_msg('[%s] %s' % (tag, out))
    return 0


def cmd_file(mod, args):
    src_path = args.convert_file
    if not os.path.isfile(src_path):
        show_msg('Introuvable : %s' % src_path, error=True)
        return 1
    try:
        text = read_text_file(src_path)
    except OSError as e:
        show_msg('Lecture impossible : %s' % e, error=True)
        return 1
    if not text:
        show_msg('Fichier vide : %s' % src_path, error=True)
        return 1
    out, _tag = convert_text(mod, text, args.layout, args.direction,
                             args.mode, args.latin_dir)
    root, ext = os.path.splitext(src_path)
    if root.endswith('.converti'):
        dst_path = src_path
    else:
        dst_path = root + '.converti' + (ext or '.txt')
    try:
        with open(dst_path, 'w', encoding='utf-8') as f:
            f.write(out)
    except OSError as e:
        show_msg('Ecriture impossible : %s' % e, error=True)
        return 1
    show_msg('Converti : %s' % dst_path)
    return 0


def preload_js(text):
    # Texte injecte APRES chargement de la page. On ne peut pas passer par
    # une URL : WebView2 refuse file://...?text=... (page d'erreur
    # chrome-error). json.dumps (ensure_ascii) rend un litteral JS sur et
    # supprime toute limite de longueur d'URL. doConvert() couvre aussi le
    # mode "sans conversion en direct" (l'evenement input ne suffit pas).
    import json
    return ("(() => { const i = document.getElementById('input');"
            " if (!i) return; i.value = %s;"
            " if (typeof doConvert === 'function') doConvert();"
            " else i.dispatchEvent(new Event('input', { bubbles: true })); })()"
            % json.dumps(text))


def start_splash():
    # Ecran de lancement Win32 (win32_splash) : purement visuel. Hors
    # Windows, ou si le module echoue, on renvoie None et rien ne change.
    try:
        import win32_splash
        return win32_splash.show(APP_TITLE, 'Chargement de la page...')
    except Exception:
        return None


def close_splash(splash):
    if splash is None:
        return
    try:
        splash.close()
    except Exception:
        pass


class LoadingFlow:
    """Sequence page de chargement -> vraie page -> injection du texte.

    Le clic droit / la touche globale ouvrent la fenetre avec un fichier a
    precharger : le texte ne peut etre injecte qu'une fois la vraie page
    chargee. La sequence est isolee de pywebview pour rester testable
    (test_app.py) sans ouvrir de fenetre : `window` expose seulement
    `load_url(url)` et `evaluate_js(js)`.

    L'evenement `loaded` de pywebview peut se declencher plusieurs fois et
    sur une page intermediaire (serveur local) : on ne se fie donc pas au
    nombre d'evenements, on verifie que le champ #input existe vraiment.
    """

    def __init__(self, page, preload_text=None):
        self.page = page
        self.preload_text = preload_text
        self.navigated = False
        self.preloaded = False

    def on_loaded(self, window):
        if not self.navigated:
            # Page de chargement affichee : on navigue vers la vraie page.
            self.navigated = True
            window.load_url(self.page)
            return
        if self.preloaded:
            return
        try:
            ready = bool(window.evaluate_js(
                "!!document.getElementById('input')"))
        except Exception:
            ready = False
        if not ready:
            return  # page intermediaire : attendre le vrai document
        self.preloaded = True
        if self.preload_text:
            window.evaluate_js(preload_js(self.preload_text))


def cmd_gui(preload_text=None):
    page = page_path()
    if not os.path.exists(page):
        show_msg('Introuvable : %s' % page, error=True)
        return 1
    # Ecran de lancement : WebView2 met plusieurs secondes a creer sa
    # fenetre. On affiche tout de suite une petite fenetre native (Win32,
    # sans dependance) qu'on ferme des que la fenetre reelle apparait.
    splash = start_splash()
    try:
        import webview
    except ImportError:
        close_splash(splash)
        show_msg('pywebview manquant : pip install pywebview', error=True)
        return 1
    # Page de chargement minimale : la fenetre apparait immediatement sans
    # attendre l'initialisation de WebView2 (~2-3 s). Une fois affichee, on
    # navigue vers convertisseur.html pour charger l'interface complete.
    flow = LoadingFlow(page, preload_text)
    window = webview.create_window(APP_TITLE, html=LOADING_HTML,
                                   width=980, height=780, min_size=(640, 520))
    window.events.loaded += (lambda: flow.on_loaded(window))
    if splash is not None:
        window.events.shown += (lambda: close_splash(splash))
    try:
        webview.start()
    except Exception as e:  # ex. WebView2 absent de la machine
        show_msg('Demarrage impossible (WebView2 requis sur Windows) : %s' % e,
                 error=True)
        return 1
    finally:
        close_splash(splash)
    return 0


def build_parser():
    ap = argparse.ArgumentParser(
        description='Convertisseur Clavier Latin/Hebreu (fenetre ou CLI).')
    ap.add_argument('fichier', nargs='?',
                    help='fichier texte a ouvrir dans la fenetre')
    ap.add_argument('--convert-clipboard', action='store_true',
                    help='convertit le presse-papiers, sans fenetre')
    ap.add_argument('--convert-file', metavar='FICHIER',
                    help='convertit un fichier vers FICHIER.converti.txt')
    ap.add_argument('--layout', default='azerty',
                    choices=['azerty', 'qwerty'])
    ap.add_argument('--direction', default='auto',
                    choices=['auto', 'toHe', 'toFr'])
    ap.add_argument('--mode', default='hebrew', choices=['hebrew', 'latin'],
                    help='hebrew = francais/anglais<->hebreu (defaut), '
                         'latin = QWERTY<->AZERTY')
    ap.add_argument('--latin-dir', default='toAz', choices=['toAz', 'toQw'])
    ap.add_argument('--paste-watch', action='store_true',
                    help='surveille le presse-papiers et propose la '
                         'conversion avant Ctrl+V (icone de notification)')
    ap.add_argument('--paste-stop', action='store_true',
                    help='arrete la surveillance du presse-papiers')
    return ap


def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.paste_stop:
        import paste_watch
        return paste_watch.run_stop()
    if args.paste_watch:
        import paste_watch
        return paste_watch.run(page_path(),
                               os.path.join(bundle_dir(), 'app.ico'),
                               load_fix())
    if args.convert_clipboard:
        return cmd_clipboard(load_fix(), args)
    if args.convert_file:
        return cmd_file(load_fix(), args)
    preload = None
    if args.fichier:
        if os.path.isfile(args.fichier):
            try:
                text = read_text_file(args.fichier)
            except OSError:
                text = ''
            if text and len(text) <= MAX_PRELOAD:
                preload = text
        # Dossier ou fichier illisible : simple ouverture de la fenetre.
    return cmd_gui(preload)


if __name__ == '__main__':
    sys.exit(main())
