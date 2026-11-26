# -*- coding: utf-8 -*-
"""Presse-papiers Unicode via l'API Win32 (ctypes), sans tkinter.

Utilise par app.py (verbes CLI) et paste_watch.py (surveillance Ctrl+V).
Rend (get, set_text), avec des reessais si une autre application verrouille
le presse-papiers.
"""


# Formats standards utilises par les gestionnaires de mots de passe (KeePass,
# Bitwarden, 1Password) et l'historique Windows pour marquer un contenu secret.
SENSITIVE_FORMATS = (
    'ExcludeClipboardContentFromMonitorProcessing',
    'Clipboard Viewer Ignore',
    'org.nspasteboard.ConcealedType',
)
HISTORY_FORMAT = 'CanIncludeInClipboardHistory'


def win32_clip(skip_sensitive=False, max_chars=0):
    import ctypes
    import time

    u32 = ctypes.WinDLL('user32', use_last_error=True)
    k32 = ctypes.WinDLL('kernel32', use_last_error=True)
    CF_UNICODETEXT = 13
    GHND = 0x0042
    # Prototypes : sans restype c_void_p, les handles 64 bits seraient
    # tronques en int 32 bits (access violation a la dereference).
    u32.OpenClipboard.argtypes = [ctypes.c_void_p]
    u32.OpenClipboard.restype = ctypes.c_int
    u32.CloseClipboard.argtypes = []
    u32.CloseClipboard.restype = ctypes.c_int
    u32.EmptyClipboard.argtypes = []
    u32.EmptyClipboard.restype = ctypes.c_int
    u32.GetClipboardData.restype = ctypes.c_void_p
    u32.GetClipboardData.argtypes = [ctypes.c_uint]
    u32.SetClipboardData.restype = ctypes.c_void_p
    u32.SetClipboardData.argtypes = [ctypes.c_uint, ctypes.c_void_p]
    u32.RegisterClipboardFormatW.argtypes = [ctypes.c_wchar_p]
    u32.RegisterClipboardFormatW.restype = ctypes.c_uint
    u32.IsClipboardFormatAvailable.argtypes = [ctypes.c_uint]
    u32.IsClipboardFormatAvailable.restype = ctypes.c_int
    k32.GlobalAlloc.restype = ctypes.c_void_p
    k32.GlobalAlloc.argtypes = [ctypes.c_uint, ctypes.c_size_t]
    k32.GlobalSize.restype = ctypes.c_size_t
    k32.GlobalSize.argtypes = [ctypes.c_void_p]
    k32.GlobalLock.restype = ctypes.c_void_p
    k32.GlobalLock.argtypes = [ctypes.c_void_p]
    k32.GlobalUnlock.argtypes = [ctypes.c_void_p]
    k32.GlobalFree.argtypes = [ctypes.c_void_p]

    sensitive_ids = [
        fmt for fmt in (u32.RegisterClipboardFormatW(name)
                        for name in SENSITIVE_FORMATS)
        if fmt
    ]
    history_id = u32.RegisterClipboardFormatW(HISTORY_FORMAT)

    def _is_sensitive():
        for fmt in sensitive_ids:
            if u32.IsClipboardFormatAvailable(fmt):
                return True
        if history_id and u32.IsClipboardFormatAvailable(history_id):
            h = u32.GetClipboardData(history_id)
            if h:
                size = k32.GlobalSize(h)
                if size >= 4:
                    p = k32.GlobalLock(h)
                    if p:
                        try:
                            if ctypes.c_uint32.from_address(p).value == 0:
                                return True
                        finally:
                            k32.GlobalUnlock(h)
        return False

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
            if skip_sensitive and _is_sensitive():
                return ''
            h = u32.GetClipboardData(CF_UNICODETEXT)
            if not h:
                return ''
            nchars = k32.GlobalSize(h) // 2
            if nchars <= 0:
                return ''
            limit = min(nchars, max_chars) if max_chars else nchars
            p = k32.GlobalLock(h)
            if not p:
                return ''
            try:
                return ctypes.wstring_at(p, limit).split('\x00', 1)[0]
            finally:
                k32.GlobalUnlock(h)
        finally:
            u32.CloseClipboard()

    def set_text(text):
        buf = ctypes.create_unicode_buffer(text)
        size = ctypes.sizeof(buf)
        # Allouer et remplir avant EmptyClipboard pour ne jamais detruire le
        # presse-papiers existant en cas d'echec memoire.
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
        if not _open():
            k32.GlobalFree(h)
            raise OSError('ouverture impossible (presse-papiers verrouille)')
        try:
            if not u32.EmptyClipboard():
                k32.GlobalFree(h)
                raise OSError('vidage refuse')
            # Le systeme devient proprietaire du bloc en cas de succes.
            if not u32.SetClipboardData(CF_UNICODETEXT, h):
                k32.GlobalFree(h)
                raise OSError('ecriture refusee')
        finally:
            u32.CloseClipboard()

    return get, set_text
