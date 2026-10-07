# -*- coding: utf-8 -*-
r"""Application Windows : la page convertisseur dans une fenetre native.

Dev (fenetre) :  python app.py
Build (.exe)   :  python build_exe.py  (nom versionne : dist\ConvertisseurClavier-X.Y.Z.exe)
Le .exe se trouve ensuite dans dist\\ConvertisseurClavier.exe.
Necessite le runtime WebView2 (present par defaut sur Windows 11
et la plupart des Windows 10 a jour).
"""
import os
import sys

APP_TITLE = 'Convertisseur Clavier Latin ⇄ Hébreu'


def page_path():
    # PyInstaller (onefile) : fichiers embarques sous sys._MEIPASS ;
    # sinon : meme dossier que ce script.
    base = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, 'convertisseur.html')


def main():
    try:
        import webview
    except ImportError:
        print('pywebview manquant : pip install pywebview')
        return 1
    page = page_path()
    if not os.path.exists(page):
        print('Introuvable : %s' % page)
        return 1
    webview.create_window(APP_TITLE, url=page, width=980, height=780,
                          min_size=(640, 520))
    try:
        webview.start()
    except Exception as e:  # ex. WebView2 absent de la machine
        print('Demarrage impossible (WebView2 requis sur Windows) : %s' % e)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
