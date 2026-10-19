# -*- coding: utf-8 -*-
"""Presse-papiers Unicode via l'API Win32 (ctypes), sans tkinter.

Utilise par app.py (verbes CLI) et paste_watch.py (surveillance Ctrl+V).
Rend (get, set_text), avec des reessais si une autre application verrouille
le presse-papiers.
"""


def win32_clip():
    import ctypes
    import time

    u32 = ctypes.windll.user32
    k32 = ctypes.windll.kernel32
    CF_UNICODETEXT = 13
    GHND = 0x0042
    # Prototypes : sans restype c_void_p, les handles 64 bits seraient
    # tronques en int 32 bits (access violation a la dereference).
    u32.OpenClipboard.argtypes = [ctypes.c_void_p]
    u32.CloseClipboard.argtypes = []
    u32.EmptyClipboard.argtypes = []
    u32.GetClipboardData.restype = ctypes.c_void_p
    u32.GetClipboardData.argtypes = [ctypes.c_uint]
    u32.SetClipboardData.restype = ctypes.c_void_p
    u32.SetClipboardData.argtypes = [ctypes.c_uint, ctypes.c_void_p]
    k32.GlobalAlloc.restype = ctypes.c_void_p
    k32.GlobalAlloc.argtypes = [ctypes.c_uint, ctypes.c_size_t]
    k32.GlobalLock.restype = ctypes.c_void_p
    k32.GlobalLock.argtypes = [ctypes.c_void_p]
    k32.GlobalUnlock.argtypes = [ctypes.c_void_p]
    k32.GlobalFree.argtypes = [ctypes.c_void_p]

    def _open():
        for _i in range(10):
            if u32.OpenClipboard(None):
                return True
            time.sleep(0.05)
        return False

    def get():
        if not _open():
            raise OSError('ouverture impossible (presse-papiers verrouille)')
        try:
            h = u32.GetClipboardData(CF_UNICODETEXT)
            if not h:
                return ''
            p = k32.GlobalLock(h)
            if not p:
                return ''
            try:
                return ctypes.wstring_at(p)
            finally:
                k32.GlobalUnlock(h)
        finally:
            u32.CloseClipboard()

    def set_text(text):
        buf = ctypes.create_unicode_buffer(text)
        size = ctypes.sizeof(buf)
        if not _open():
            raise OSError('ouverture impossible (presse-papiers verrouille)')
        try:
            u32.EmptyClipboard()
            h = k32.GlobalAlloc(GHND, size)
            if not h:
                raise OSError('allocation impossible')
            p = k32.GlobalLock(h)
            if not p:
                k32.GlobalFree(h)
                raise OSError('verrouillage impossible')
            try:
                ctypes.memmove(p, buf, size)
            finally:
                k32.GlobalUnlock(h)
            # Le systeme devient proprietaire du bloc en cas de succes.
            if not u32.SetClipboardData(CF_UNICODETEXT, h):
                k32.GlobalFree(h)
                raise OSError('ecriture refusee')
        finally:
            u32.CloseClipboard()

    return get, set_text
