# -*- coding: utf-8 -*-
"""Ecran de lancement minimal (Win32 pur, ctypes).

WebView2 met plusieurs secondes a creer sa fenetre : on affiche tout de
suite une petite fenetre native, remplacee par la fenetre reelle des qu'elle
apparait. Aucune dependance (ni tkinter, ni .NET, ni fichier externe), donc
quelques millisecondes seulement.

Hors Windows (CI Linux), Splash.show() ne fait rien et renvoie False.
"""
import sys
import threading

IS_WINDOWS = sys.platform == 'win32'

WIDTH = 380
HEIGHT = 150
COLOR_BG = 0x00F5F4F2      # COLORREF : 0x00BBGGRR (fond clair de la page)
COLOR_TITLE = 0x00202020
COLOR_SUB = 0x008A8A8A
CLASS_NAME = 'ConvertisseurClavierSplash'

WS_EX_TOOLWINDOW = 0x00000080
WS_EX_TOPMOST = 0x00000008
WS_POPUP = 0x80000000
WS_BORDER = 0x00800000
SW_SHOWNOACTIVATE = 4
WM_DESTROY = 0x0002
WM_CLOSE = 0x0010
WM_PAINT = 0x000F
WM_ERASEBKGND = 0x0014
ERROR_CLASS_ALREADY_EXISTS = 1410
IDC_ARROW = 32512
DT_CENTER = 0x0001
DT_VCENTER = 0x0004
DT_SINGLELINE = 0x0020
DT_NOPREFIX = 0x0800
TRANSPARENT = 1
DEFAULT_CHARSET = 1
FW_SEMIBOLD = 600
FW_NORMAL = 400

_api = None


def _load():
    """Charge user32/gdi32 et fixe les prototypes (une seule fois)."""
    global _api
    if _api is not None:
        return _api
    import ctypes

    DWORD = ctypes.c_ulong
    UINT = ctypes.c_uint
    INT = ctypes.c_int
    BOOL = ctypes.c_int
    HWND = ctypes.c_void_p
    HDC = ctypes.c_void_p
    HBRUSH = ctypes.c_void_p
    HFONT = ctypes.c_void_p
    HGDIOBJ = ctypes.c_void_p
    HICON = ctypes.c_void_p
    HMODULE = ctypes.c_void_p
    HMENU = ctypes.c_void_p
    HINSTANCE = ctypes.c_void_p
    LPVOID = ctypes.c_void_p
    COLORREF = ctypes.c_ulong
    LPCWSTR = ctypes.c_wchar_p
    WPARAM = ctypes.c_size_t
    LPARAM = ctypes.c_ssize_t
    LRESULT = ctypes.c_ssize_t
    WNDPROC = ctypes.WINFUNCTYPE(LRESULT, HWND, UINT, WPARAM, LPARAM)

    class POINT(ctypes.Structure):
        _fields_ = [('x', ctypes.c_long), ('y', ctypes.c_long)]

    class RECT(ctypes.Structure):
        _fields_ = [('left', ctypes.c_long), ('top', ctypes.c_long),
                    ('right', ctypes.c_long), ('bottom', ctypes.c_long)]

    class PAINTSTRUCT(ctypes.Structure):
        _fields_ = [('hdc', HDC), ('fErase', BOOL), ('rcPaint', RECT),
                    ('fRestore', BOOL), ('fIncUpdate', BOOL),
                    ('rgbReserved', ctypes.c_byte * 32)]

    class MSG(ctypes.Structure):
        _fields_ = [('hwnd', HWND), ('message', UINT),
                    ('wParam', WPARAM), ('lParam', LPARAM),
                    ('time', DWORD), ('pt', POINT)]

    class WNDCLASSW(ctypes.Structure):
        _fields_ = [('style', UINT), ('lpfnWndProc', LPVOID),
                    ('cbClsExtra', INT), ('cbWndExtra', INT),
                    ('hInstance', HINSTANCE), ('hIcon', HICON),
                    ('hCursor', HGDIOBJ), ('hbrBackground', HBRUSH),
                    ('lpszMenuName', LPCWSTR), ('lpszClassName', LPCWSTR)]

    u32 = ctypes.WinDLL('user32', use_last_error=True)
    g32 = ctypes.WinDLL('gdi32', use_last_error=True)
    k32 = ctypes.WinDLL('kernel32', use_last_error=True)

    u32.RegisterClassW.argtypes = [ctypes.POINTER(WNDCLASSW)]
    u32.RegisterClassW.restype = ctypes.c_ushort
    u32.CreateWindowExW.argtypes = [DWORD, LPCWSTR, LPCWSTR, DWORD, INT, INT,
                                    INT, INT, HWND, HMENU, HINSTANCE, LPVOID]
    u32.CreateWindowExW.restype = HWND
    u32.DefWindowProcW.argtypes = [HWND, UINT, WPARAM, LPARAM]
    u32.DefWindowProcW.restype = LRESULT
    u32.ShowWindow.argtypes = [HWND, INT]
    u32.UpdateWindow.argtypes = [HWND]
    u32.DestroyWindow.argtypes = [HWND]
    u32.PostMessageW.argtypes = [HWND, UINT, WPARAM, LPARAM]
    u32.PostQuitMessage.argtypes = [INT]
    u32.GetMessageW.argtypes = [ctypes.POINTER(MSG), HWND, UINT, UINT]
    u32.GetMessageW.restype = BOOL
    u32.TranslateMessage.argtypes = [ctypes.POINTER(MSG)]
    u32.DispatchMessageW.argtypes = [ctypes.POINTER(MSG)]
    u32.DispatchMessageW.restype = LRESULT
    u32.BeginPaint.argtypes = [HWND, ctypes.POINTER(PAINTSTRUCT)]
    u32.BeginPaint.restype = HDC
    u32.EndPaint.argtypes = [HWND, ctypes.POINTER(PAINTSTRUCT)]
    u32.FillRect.argtypes = [HDC, ctypes.POINTER(RECT), HBRUSH]
    u32.DrawTextW.argtypes = [HDC, LPCWSTR, INT, ctypes.POINTER(RECT), UINT]
    g32.SetTextColor.argtypes = [HDC, COLORREF]
    g32.SetBkMode.argtypes = [HDC, INT]
    u32.GetSystemMetrics.argtypes = [INT]
    u32.GetSystemMetrics.restype = INT
    k32.GetModuleHandleW.argtypes = [LPCWSTR]
    k32.GetModuleHandleW.restype = HMODULE
    u32.LoadCursorW.argtypes = [HINSTANCE, LPVOID]
    u32.LoadCursorW.restype = HGDIOBJ
    g32.CreateSolidBrush.argtypes = [COLORREF]
    g32.CreateSolidBrush.restype = HBRUSH
    g32.CreateFontW.argtypes = [INT, INT, INT, INT, INT, DWORD, DWORD, DWORD,
                               DWORD, DWORD, DWORD, DWORD, DWORD, LPCWSTR]
    g32.CreateFontW.restype = HFONT
    g32.SelectObject.argtypes = [HDC, HGDIOBJ]
    g32.SelectObject.restype = HGDIOBJ
    g32.DeleteObject.argtypes = [HGDIOBJ]

    _api = {
        'ctypes': ctypes, 'u32': u32, 'g32': g32, 'k32': k32,
        'WNDPROC': WNDPROC,
        'WNDCLASSW': WNDCLASSW, 'PAINTSTRUCT': PAINTSTRUCT, 'MSG': MSG,
        'RECT': RECT, 'HWND': HWND, 'HGDIOBJ': HGDIOBJ,
    }
    return _api


class Splash:
    """Fenetre de lancement : show() puis close(). Ne leve jamais."""

    def __init__(self, title, subtitle=''):
        self.title = title
        self.subtitle = subtitle
        self._thread = None
        self._ready = threading.Event()
        self._hwnd = None
        self._fonts = []
        self._brush = None

    def show(self):
        if not IS_WINDOWS:
            return False
        try:
            self._thread = threading.Thread(target=self._run, name='splash',
                                            daemon=True)
            self._thread.start()
            self._ready.wait(3.0)
        except Exception:
            return False
        return self._hwnd is not None

    def close(self):
        # PostMessage : DestroyWindow doit etre appele par le thread qui a
        # cree la fenetre, celui de la boucle de messages.
        hwnd = self._hwnd
        if not hwnd:
            return
        try:
            _load()['u32'].PostMessageW(hwnd, WM_CLOSE, 0, 0)
        except Exception:
            pass
        if self._thread is not None:
            self._thread.join(2.0)

    # -- thread de la fenetre --

    def _run(self):
        try:
            api = _load()
        except Exception:
            return
        ctypes = api['ctypes']
        u32, g32, k32 = api['u32'], api['g32'], api['k32']
        proc = api['WNDPROC'](self._wndproc)
        self._brush = g32.CreateSolidBrush(COLOR_BG)
        self._fonts = [
            g32.CreateFontW(-22, 0, 0, 0, FW_SEMIBOLD, 0, 0, 0,
                            DEFAULT_CHARSET, 0, 0, 0, 0, 'Segoe UI'),
            g32.CreateFontW(-14, 0, 0, 0, FW_NORMAL, 0, 0, 0,
                            DEFAULT_CHARSET, 0, 0, 0, 0, 'Segoe UI'),
        ]
        wc = api['WNDCLASSW']()
        wc.lpfnWndProc = ctypes.cast(proc, ctypes.c_void_p)
        wc.hInstance = k32.GetModuleHandleW(None)
        wc.hCursor = u32.LoadCursorW(None, IDC_ARROW)
        wc.hbrBackground = self._brush
        wc.lpszClassName = CLASS_NAME
        ctypes.set_last_error(0)
        if not u32.RegisterClassW(ctypes.byref(wc)):
            if ctypes.get_last_error() != ERROR_CLASS_ALREADY_EXISTS:
                self._ready.set()
                return
        x = (u32.GetSystemMetrics(0) - WIDTH) // 2
        y = (u32.GetSystemMetrics(1) - HEIGHT) // 3
        hwnd = u32.CreateWindowExW(WS_EX_TOOLWINDOW | WS_EX_TOPMOST, CLASS_NAME,
                                   self.title, WS_POPUP | WS_BORDER,
                                   x, y, WIDTH, HEIGHT, None, None,
                                   wc.hInstance, None)
        if not hwnd:
            self._ready.set()
            return
        self._hwnd = hwnd
        u32.ShowWindow(hwnd, SW_SHOWNOACTIVATE)
        u32.UpdateWindow(hwnd)
        self._ready.set()
        msg = api['MSG']()
        while u32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
            u32.TranslateMessage(ctypes.byref(msg))
            u32.DispatchMessageW(ctypes.byref(msg))
        self._hwnd = None

    def _wndproc(self, hwnd, msg, wparam, lparam):
        api = _api
        if api is None:
            return 0
        ctypes = api['ctypes']
        u32, g32 = api['u32'], api['g32']
        if msg == WM_PAINT:
            ps = api['PAINTSTRUCT']()
            hdc = u32.BeginPaint(hwnd, ctypes.byref(ps))
            rect = api['RECT'](0, 0, WIDTH, HEIGHT)
            u32.FillRect(hdc, ctypes.byref(rect), self._brush)
            g32.SetBkMode(hdc, TRANSPARENT)
            g32.SetTextColor(hdc, COLOR_TITLE)
            old = g32.SelectObject(hdc, self._fonts[0]) if self._fonts else None
            title_rect = api['RECT'](16, 38, WIDTH - 16, HEIGHT - 46)
            u32.DrawTextW(hdc, self.title, -1, ctypes.byref(title_rect),
                          DT_CENTER | DT_SINGLELINE | DT_VCENTER | DT_NOPREFIX)
            if self.subtitle:
                g32.SetTextColor(hdc, COLOR_SUB)
                if len(self._fonts) > 1:
                    g32.SelectObject(hdc, self._fonts[1])
                sub_rect = api['RECT'](16, HEIGHT - 52, WIDTH - 16, HEIGHT - 22)
                u32.DrawTextW(hdc, self.subtitle, -1, ctypes.byref(sub_rect),
                              DT_CENTER | DT_SINGLELINE | DT_NOPREFIX)
            if old:
                g32.SelectObject(hdc, old)
            u32.EndPaint(hwnd, ctypes.byref(ps))
            return 0
        if msg == WM_ERASEBKGND:
            return 1
        if msg == WM_CLOSE:
            u32.DestroyWindow(hwnd)
            return 0
        if msg == WM_DESTROY:
            u32.PostQuitMessage(0)
            return 0
        return u32.DefWindowProcW(hwnd, msg, wparam, lparam)


def show(title, subtitle=''):
    """Raccourci : renvoie un Splash deja affiche (ou None)."""
    splash = Splash(title, subtitle)
    return splash if splash.show() else None
