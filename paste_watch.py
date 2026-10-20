# -*- coding: utf-8 -*-
r"""Guetteur de presse-papiers : intercepte Ctrl+V et propose la conversion
avant de coller (Windows uniquement, 100 % local).

Le processus vit dans la zone de notification (icone) et demarre avec Windows
si l'option est cochee dans le Setup. Il ne modifie jamais le presse-papiers
sans un choix explicite.

Usage :
  python app.py --paste-watch   (demarre la surveillance)
  python app.py --paste-stop    (arrete la surveillance en cours)
"""
import base64
import ctypes
import json
import os
import queue
import re
import subprocess
import sys
import threading
import time

APP_NAME = 'Convertisseur Clavier'
MUTEX_NAME = 'Local\\ConvertisseurClavierPaste'
STOP_EVENT = 'Local\\ConvertisseurClavierPasteStop'
WINDOW_CLASS = 'ConvertisseurClavierPasteWnd'
TRAY_ID = 1
WM_APP = 0x8000
WM_TRAY = WM_APP + 1
WM_STOP = WM_APP + 2
WM_CLIPBOARDUPDATE = 0x031D
WM_COMMAND = 0x0111
WM_DESTROY = 0x0002
WM_CLOSE = 0x0010
WM_RBUTTONUP = 0x0205
WM_LBUTTONDBLCLK = 0x0203
WM_KEYDOWN = 0x0100
WM_KEYUP = 0x0101
WM_SYSKEYDOWN = 0x0104
WM_SYSKEYUP = 0x0105
WH_KEYBOARD_LL = 13
VK_CONTROL = 0x11
VK_SHIFT = 0x10
VK_MENU = 0x12
VK_LWIN = 0x5B
VK_RWIN = 0x5C
VK_V = 0x56
VK_RETURN = 0x0D
VK_ESCAPE = 0x1B
MAGIC = 0x434C5650  # "CLVP" : identifie nos propres evenements injectes

# La detection reste volontairement prudente : un texte ambigu ne doit pas
# declencher de proposition.
MAX_TEXT = 4000
MIN_LETTERS = 4
MIN_TARGET = -3.5
MARGIN = 0.8
SHORT_MARGIN = 1.0
SHORT_LETTERS = 8
LAYOUT_MARGIN = 0.8
LAYOUT_PENALTY = 2.5
LAYOUTS = ('azerty', 'qwerty')
DEFAULT_LAYOUT = 'azerty'
SETTINGS_ENV = 'CONVERTISSEUR_PASTE_SETTINGS'
SYMBOL_RE = re.compile(r'[@\\/<>{}[\]|~^_=#$%&*+]')
HEB_RE = re.compile(r'[\u0590-\u05ff]')

# <he_model:generated>
# Modele de bigrammes hebreu genere par : python gen_ngrams.py --hebrew
# Source (domaine public) :
#   pg5139.txt <- https://www.gutenberg.org/cache/epub/5139/pg5139.txt (sha256 d105307feb42da01)
HE_ALPHA = "\u05d0\u05d1\u05d2\u05d3\u05d4\u05d5\u05d6\u05d7\u05d8\u05d9\u05db\u05dc\u05de\u05e0\u05e1\u05e2\u05e4\u05e6\u05e7\u05e8\u05e9\u05ea\u05da\u05dd\u05df\u05e3\u05e5 '.,:;!?"
HE_SCALE = 8
HE_OFFSET = 16
HE_B64 = 'PWdYZGRtYmlPbFtma2tVTV1XSmNjblRfUFg7cixUVT07TkZnXFlga21cYVxwZGxjYVtoWFtgbWRlU0xaLkFtN15cQUBRSltoTW9hbWNNOG84bGVfVWhMODhkYllFbF84OGg4WFNBQUVBXmdUVmduM1YzcEVgZ108aE9AY2pfX05iTkwzdTNiX0NFUU1nYGBaUmhhZFZtYFtiYFxkXmBgY2RkKGRXKCh3O2djTExZVmlnXWhnWFpiWF9ka2RkWWFdX2JqZHBcYmJbVnA8X1xERU9LZ2JNWXdqRl03aV9iaF83XkM3aWs3TDdOQ0s3bTdUUDdDRkZKX1FsZXJiUlFvW2hiZVszXlpebWRrRlZYTkZsM1tXPztNTFRnOkxocUdfWG9DXVVoVWNiOkppUVk6UGdZOm9DYV06R1lDYmNTZGdsVV5aZWJmXWVWYmNdXWVlZ15xYlBTcjVeWjpDVE5ga0ZeaG9bXTprYHRpZFJcWUM/ZGpdaGBoSzI/MjIyMjIyMm1hXWFua1ZeWG9iYGReV2FeWFxaYWFiXk9QSHUrXVhDPkxKZWBYZG9tYGRdbV9mYGRdaV1iYm9qaVVUYC5IOy4uLi4uLi5gYF1abnFPZVN3XUtjX19lZU1hYmViU1tXUkVBMTExMTExMVNpWmFkcDtRWnBkZ2RbUmNqO2JeO2lSWFFYO2c7WFRDSFQ7QmJXZWJvWTBgamhxZGdXSFNnW2xlZ0BlUFNiazlbVT09T0ZbNllTbXFRZmBvSWZDamBnVl9gb2hnUkNbWFJJNjY2NjZDNmpkTGBtbTdiXXE3ZWxdN2loVklsN2JAXVlQU0lANzc3Nzc3UWI1XmRwPl1obzVgU2ZOX1xhVG5jXEdQZk5WcjVeW0c+UUtqZ2Jda29XYlNvV0xUU1JhWF5kVV1kXE5aWVt0OmZgSkpTUWxqVlptbVhgWW5hbWlkTGFdUF1mW2RXZFVCL2svXVZAPk9IWllYUWtrTGRHbltdXWJMXF9IWmlUVl1hWEUueDtoY0NOVlY7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozt8O2ppTFBgYDExMTExMTExMTExMTExMTExMTExMTExMTExMX06bmtNVl5cODg4ODg4ODg4OEE4ODg4ODg4ODg4ODg4ODg4fEVva0pUXFlAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEB6SWlkSVJcWEFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQXlKaWdKSlVBcGtcWnJqYmBWZWhta2JZaF1bXWBrXCEuISEhIUc8Xi4hNi5hV0ZOWldVWUZOWVdVRk5TTkZOVVNVRkZGRkZqTldbRk5GRjQ0NDQ0NDQ0NDQ0NDw0NDQ0NDQ0NDQ0NDQ0NH9MQzQ0NDQ0NTU1NTU1PjU1NTU1NTU1NTU1NTU1NTU1NTU1fzU1NTU1NTVFRUVFRUVFRUVFRUVFRUVFRUVFRUVFRUVFRUVzRUVFRUVFRUVFRUVFRUVFRUVFRUVFRUVFRUVFRUVFRUVFRXVFRUVFRUVFPz8/Pz8/Pz8/Pz8/Pz8/Pz8/Pz8/Pz8/Pz8/fF8/Pz8/Pz9BQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUF7UUFBQUFBQQ=='
# </he_model:generated>


# --- modeles et detection (testables sans Windows) ---

def parse_page_models(html_text):
    """Extrait MODEL_ALPHA / MODEL_B64 de convertisseur.html."""
    m = re.search(r'const MODEL_ALPHA = "([^"]*)"', html_text)
    if not m:
        raise ValueError('MODEL_ALPHA introuvable')
    alpha = m.group(1)
    m = re.search(r'MODEL_SCALE\s*=\s*(\d+)', html_text)
    if not m:
        raise ValueError('MODEL_SCALE introuvable')
    scale = int(m.group(1))
    m = re.search(r'MODEL_OFFSET\s*=\s*(\d+)', html_text)
    if not m:
        raise ValueError('MODEL_OFFSET introuvable')
    offset = int(m.group(1))
    m = re.search(r'const MODEL_B64 = \{(.*?)\n\};', html_text, re.S)
    if not m:
        raise ValueError('MODEL_B64 introuvable')
    models = {}
    for code, b64 in re.findall(r"(\w+):\s*'([^']+)'", m.group(1)):
        raw = base64.b64decode(b64)
        if len(raw) != len(alpha) ** 2:
            raise ValueError('modele %s de taille inattendue' % code)
        models[code] = raw
    if not models:
        raise ValueError('aucun modele latin')
    return {'alpha': alpha, 'scale': scale, 'offset': offset,
            'latin': models}


def load_models(html_text):
    """Modeles de la page (fr/en) + modele hebreu genere ci-dessous."""
    out = parse_page_models(html_text)
    raw = base64.b64decode(HE_B64)
    if len(raw) != len(HE_ALPHA) ** 2:
        raise ValueError('modele hebreu de taille inattendue '
                         '(python gen_ngrams.py --hebrew)')
    out.update({'he_alpha': HE_ALPHA, 'he_scale': HE_SCALE,
                'he_offset': HE_OFFSET, 'he': raw})
    return out


def normalize_latin(text, alpha):
    # Miroir exact de normalize() (gen_ngrams.py) et de normalizeForModel().
    s = str(text).lower().replace('\u2019', "'").replace('\u0153', 'oe')
    return re.sub(r'\s+', ' ',
                  ''.join(ch if ch in alpha else ' ' for ch in s)).strip()


def normalize_hebrew(text, alpha):
    s = str(text).lower().replace('\u05f3', "'").replace('\u05f4', '"')
    return re.sub(r'\s+', ' ',
                  ''.join(ch if ch in alpha else ' ' for ch in s)).strip()


def _score(raw, alpha, scale, offset, text, normalize):
    t = normalize(text, alpha)
    if len(t) < 2:
        return None
    idx = {ch: i for i, ch in enumerate(alpha)}
    acc = 0.0
    for a, b in zip(t, t[1:]):
        acc += raw[idx[a] * len(alpha) + idx[b]] / scale - offset
    return acc / (len(t) - 1)


def score_latin(models, text):
    vals = [_score(raw, models['alpha'], models['scale'], models['offset'],
                   text, normalize_latin)
            for raw in models['latin'].values()]
    vals = [v for v in vals if v is not None]
    return max(vals) if vals else None


def score_hebrew(models, text):
    return _score(models['he'], models['he_alpha'], models['he_scale'],
                  models['he_offset'], text, normalize_hebrew)


def count_scripts(text):
    heb = sum(1 for ch in text if HEB_RE.match(ch) and ch.isalpha())
    lat = sum(1 for ch in text
              if ch.isalpha() and not ('\u0590' <= ch <= '\u05ff'))
    return lat, heb


def normalize_layout(layout):
    """Rend une disposition connue ; AZERTY par defaut."""
    return layout if layout in LAYOUTS else DEFAULT_LAYOUT


def convert_for_layout(text, layout, direction, fix_mod):
    """Convertit un texte pour une disposition imposee (popup)."""
    layout = normalize_layout(layout)
    if direction == 'toHe':
        table, _to_fr = fix_mod.MAPS[layout]
        swap = fix_mod.CAPS_SWAP if layout == 'azerty' else None
        return fix_mod.convert_smart(text, table, swap, False)
    _to_he, table = fix_mod.MAPS[layout]
    swap = fix_mod.CAPS_SWAP if layout == 'azerty' else None
    return fix_mod.convert_smart(text, table, swap, True)


def _layout_penalty(text, direction):
    """Penalise les restes de l'ecriture source et les symboles de code.

    Une disposition erronee laisse souvent une lettre latine dans la sortie
    hebraique (ou l'inverse), ou transforme une touche en / \\ etc. Le modele
    de bigrammes ne voit pas ces caracteres : on les compte a part.
    """
    penalty = 0
    for ch in text:
        if ch.isalpha():
            if direction == 'toHe' and not HEB_RE.match(ch):
                penalty += LAYOUT_PENALTY
            elif direction == 'toFr' and HEB_RE.match(ch):
                penalty += LAYOUT_PENALTY
        elif SYMBOL_RE.match(ch):
            penalty += LAYOUT_PENALTY
    return penalty


def _layout_candidates(text, direction, models, fix_mod):
    """Note les deux dispositions : score modele et score effectif."""
    out = {}
    for layout in LAYOUTS:
        converted = convert_for_layout(text, layout, direction, fix_mod)
        if direction == 'toHe':
            score = score_hebrew(models, converted)
        else:
            score = score_latin(models, converted)
        if score is None:
            continue
        penalty = _layout_penalty(converted, direction)
        out[layout] = {'layout': layout, 'text': converted,
                       'score': score, 'penalty': penalty,
                       'effective': score - penalty}
    return out


def detect_text(text, models, fix_mod, default_layout=DEFAULT_LAYOUT):
    """Rend None ou {direction, layout, text, source_text, score, ...}.

    Compare la lecture actuelle (modele de sa langue) aux deux dispositions
    possibles, et ne propose que si l'ecart avec la source est net. Si les
    deux dispositions restent plausibles et proches (peu de lettres pour les
    distinguer), la disposition par defaut de l'utilisateur est utilisee.
    """
    text = '' if text is None else str(text)
    default_layout = normalize_layout(default_layout)
    if not text.strip() or len(text) > MAX_TEXT:
        return None
    lat, heb = count_scripts(text)
    if lat + heb < MIN_LETTERS:
        return None
    if lat and heb:  # texte mixte : trop ambigu
        return None
    if SYMBOL_RE.search(text):  # URL, chemin, code, adresse...
        return None

    direction = 'toHe' if lat else 'toFr'
    source_score = (score_latin(models, text) if lat
                    else score_hebrew(models, text))
    candidates = _layout_candidates(text, direction, models, fix_mod)
    if source_score is None or not candidates:
        return None
    ranked = sorted(candidates.values(),
                    key=lambda item: item['effective'], reverse=True)
    best = ranked[0]
    detected_layout = best['layout']
    ambiguous = False
    if len(ranked) > 1:
        second = ranked[1]
        close = (best['effective'] - second['effective'] < LAYOUT_MARGIN
                 and best['text'] != second['text'])
        if (close and second['effective'] >= MIN_TARGET
                and candidates.get(default_layout) is not None
                and candidates[default_layout]['effective'] >= MIN_TARGET):
            best = candidates[default_layout]
            ambiguous = True

    if not best['text'].strip() or best['text'] == text:
        return None
    if best['effective'] < MIN_TARGET:
        return None
    need = MARGIN if lat + heb >= SHORT_LETTERS else SHORT_MARGIN
    margin = best['effective'] - source_score
    if margin < need:
        return None
    return {'direction': direction, 'layout': best['layout'],
            'detected_layout': detected_layout,
            'text': best['text'], 'source_text': text,
            'source_score': source_score, 'score': best['score'],
            'effective_score': best['effective'],
            'margin': margin, 'layout_ambiguous': ambiguous,
            'layout_default': default_layout,
            'layout_scores': {layout: candidate['effective']
                              for layout, candidate in candidates.items()}}


def truncate(text, limit=160):
    text = str(text).strip()
    if len(text) <= limit:
        return text
    return text[:limit].rstrip() + '\u2026'


def layout_label(layout):
    return 'AZERTY' if layout == 'azerty' else 'QWERTY'


def settings_path():
    """Fichier de reglages du guetteur (surchargeable pour les tests)."""
    override = os.environ.get(SETTINGS_ENV)
    if override:
        return os.path.abspath(os.path.expanduser(override))
    base = os.environ.get('LOCALAPPDATA') or os.environ.get('APPDATA')
    if not base:
        base = (os.environ.get('XDG_CONFIG_HOME')
                or os.path.join(os.path.expanduser('~'), '.config'))
    return os.path.join(base, 'ConvertisseurClavier', 'paste_watch.json')


def load_settings(path=None):
    """Lit le clavier par defaut ; un fichier absent/casse rend AZERTY."""
    path = path or settings_path()
    raw = None
    try:
        with open(path, encoding='utf-8') as f:
            raw = json.load(f)
    except (OSError, ValueError, TypeError):
        raw = None
    if not isinstance(raw, dict):
        raw = {}
    return {'default_layout': normalize_layout(raw.get('default_layout'))}


def save_settings(settings, path=None):
    """Ecrit les reglages de facon atomique ; ne leve jamais d'exception."""
    path = path or settings_path()
    layout = normalize_layout((settings or {}).get('default_layout'))
    tmp = path + '.tmp'
    try:
        folder = os.path.dirname(path)
        if folder:
            os.makedirs(folder, exist_ok=True)
        with open(tmp, 'w', encoding='utf-8', newline='\n') as f:
            json.dump({'default_layout': layout}, f,
                      ensure_ascii=True, indent=2)
            f.write('\n')
        os.replace(tmp, path)
        return True
    except Exception:
        try:
            if os.path.exists(tmp):
                os.remove(tmp)
        except Exception:
            pass
        return False


# --- Win32 : crochet clavier, icone de notification, collage ---

class POINT(ctypes.Structure):
    _fields_ = [('x', ctypes.c_long), ('y', ctypes.c_long)]


class RECT(ctypes.Structure):
    _fields_ = [('left', ctypes.c_long), ('top', ctypes.c_long),
                ('right', ctypes.c_long), ('bottom', ctypes.c_long)]


class GUITHREADINFO(ctypes.Structure):
    _fields_ = [('cbSize', ctypes.c_uint), ('flags', ctypes.c_uint),
                ('hwndActive', ctypes.c_void_p), ('hwndFocus', ctypes.c_void_p),
                ('hwndCapture', ctypes.c_void_p),
                ('hwndMenuOwner', ctypes.c_void_p),
                ('hwndMoveSize', ctypes.c_void_p),
                ('hwndCaret', ctypes.c_void_p), ('rcCaret', RECT)]


class KBDLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [('vkCode', ctypes.c_ulong), ('scanCode', ctypes.c_ulong),
                ('flags', ctypes.c_ulong), ('time', ctypes.c_ulong),
                ('dwExtraInfo', ctypes.c_size_t)]


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [('dx', ctypes.c_long), ('dy', ctypes.c_long),
                ('mouseData', ctypes.c_ulong), ('dwFlags', ctypes.c_ulong),
                ('time', ctypes.c_ulong), ('dwExtraInfo', ctypes.c_size_t)]


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [('wVk', ctypes.c_ushort), ('wScan', ctypes.c_ushort),
                ('dwFlags', ctypes.c_ulong), ('time', ctypes.c_ulong),
                ('dwExtraInfo', ctypes.c_size_t)]


class HARDWAREINPUT(ctypes.Structure):
    _fields_ = [('uMsg', ctypes.c_ulong), ('wParamL', ctypes.c_ushort),
                ('wParamH', ctypes.c_ushort)]


class _INPUTUNION(ctypes.Union):
    _fields_ = [('mi', MOUSEINPUT), ('ki', KEYBDINPUT), ('hi', HARDWAREINPUT)]


class INPUT(ctypes.Structure):
    _fields_ = [('type', ctypes.c_ulong), ('u', _INPUTUNION)]


class WNDCLASSW(ctypes.Structure):
    _fields_ = [('style', ctypes.c_uint), ('lpfnWndProc', ctypes.c_void_p),
                ('cbClsExtra', ctypes.c_int), ('cbWndExtra', ctypes.c_int),
                ('hInstance', ctypes.c_void_p), ('hIcon', ctypes.c_void_p),
                ('hCursor', ctypes.c_void_p), ('hbrBackground', ctypes.c_void_p),
                ('lpszMenuName', ctypes.c_wchar_p),
                ('lpszClassName', ctypes.c_wchar_p)]


class MSG(ctypes.Structure):
    _fields_ = [('hwnd', ctypes.c_void_p), ('message', ctypes.c_uint),
                ('wParam', ctypes.c_size_t), ('lParam', ctypes.c_size_t),
                ('time', ctypes.c_ulong), ('pt', POINT)]


class GUID(ctypes.Structure):
    _fields_ = [('Data1', ctypes.c_ulong), ('Data2', ctypes.c_ushort),
                ('Data3', ctypes.c_ushort), ('Data4', ctypes.c_ubyte * 8)]


class NOTIFYICONDATAW(ctypes.Structure):
    _fields_ = [('cbSize', ctypes.c_ulong), ('hWnd', ctypes.c_void_p),
                ('uID', ctypes.c_uint), ('uFlags', ctypes.c_uint),
                ('uCallbackMessage', ctypes.c_uint), ('hIcon', ctypes.c_void_p),
                ('szTip', ctypes.c_wchar * 128), ('dwState', ctypes.c_ulong),
                ('dwStateMask', ctypes.c_ulong),
                ('szInfo', ctypes.c_wchar * 256),
                ('uTimeoutOrVersion', ctypes.c_uint),
                ('szInfoTitle', ctypes.c_wchar * 64),
                ('dwInfoFlags', ctypes.c_ulong), ('guidItem', GUID),
                ('hBalloonIcon', ctypes.c_void_p)]


class MONITORINFO(ctypes.Structure):
    _fields_ = [('cbSize', ctypes.c_ulong), ('rcMonitor', RECT),
                ('rcWork', RECT), ('dwFlags', ctypes.c_ulong)]


if sys.platform == 'win32':
    WNDPROC = ctypes.WINFUNCTYPE(ctypes.c_ssize_t, ctypes.c_void_p,
                                 ctypes.c_uint, ctypes.c_size_t,
                                 ctypes.c_size_t)
    HOOKPROC = ctypes.WINFUNCTYPE(ctypes.c_ssize_t, ctypes.c_int,
                                  ctypes.c_size_t, ctypes.c_size_t)
else:
    WNDPROC = None
    HOOKPROC = None

_U32 = None
_K32 = None
_S32 = None


def _win32():
    """Configure les prototypes une seule fois et rend (user32, kernel32)."""
    global _U32, _K32, _S32
    if _U32 is not None:
        return _U32, _K32
    u32 = ctypes.windll.user32
    k32 = ctypes.windll.kernel32
    s32 = ctypes.windll.shell32
    vp, sz, ui, ul = (ctypes.c_void_p, ctypes.c_size_t, ctypes.c_uint,
                      ctypes.c_ulong)
    u32.SetWindowsHookExW.restype = vp
    u32.SetWindowsHookExW.argtypes = [ctypes.c_int, HOOKPROC, vp, ui]
    u32.CallNextHookEx.restype = ctypes.c_ssize_t
    u32.CallNextHookEx.argtypes = [vp, ctypes.c_int, sz, sz]
    u32.UnhookWindowsHookEx.restype = ctypes.c_int
    u32.UnhookWindowsHookEx.argtypes = [vp]
    u32.GetMessageW.restype = ctypes.c_int
    u32.GetMessageW.argtypes = [ctypes.POINTER(MSG), vp, ui, ui]
    u32.TranslateMessage.argtypes = [ctypes.POINTER(MSG)]
    u32.DispatchMessageW.restype = ctypes.c_ssize_t
    u32.DispatchMessageW.argtypes = [ctypes.POINTER(MSG)]
    u32.RegisterClassW.restype = ctypes.c_ushort
    u32.RegisterClassW.argtypes = [ctypes.POINTER(WNDCLASSW)]
    u32.CreateWindowExW.restype = vp
    u32.CreateWindowExW.argtypes = [ul, ctypes.c_wchar_p, ctypes.c_wchar_p,
                                    ul, ctypes.c_int, ctypes.c_int,
                                    ctypes.c_int, ctypes.c_int,
                                    vp, vp, vp, vp]
    u32.DefWindowProcW.restype = ctypes.c_ssize_t
    u32.DefWindowProcW.argtypes = [vp, ui, sz, sz]
    u32.DestroyWindow.argtypes = [vp]
    u32.PostQuitMessage.argtypes = [ctypes.c_int]
    u32.PostMessageW.argtypes = [vp, ui, sz, sz]
    u32.AddClipboardFormatListener.argtypes = [vp]
    u32.RemoveClipboardFormatListener.argtypes = [vp]
    u32.GetClipboardSequenceNumber.restype = ui
    u32.GetForegroundWindow.restype = vp
    u32.SetForegroundWindow.restype = ctypes.c_int
    u32.SetForegroundWindow.argtypes = [vp]
    u32.BringWindowToTop.restype = ctypes.c_int
    u32.BringWindowToTop.argtypes = [vp]
    u32.IsWindow.restype = ctypes.c_int
    u32.IsWindow.argtypes = [vp]
    u32.ShowWindow.argtypes = [vp, ctypes.c_int]
    u32.GetCursorPos.argtypes = [ctypes.POINTER(POINT)]
    u32.ClientToScreen.argtypes = [vp, ctypes.POINTER(POINT)]
    u32.WindowFromPoint.restype = vp
    u32.WindowFromPoint.argtypes = [POINT]
    u32.GetWindowThreadProcessId.restype = ul
    u32.GetWindowThreadProcessId.argtypes = [vp, vp]
    u32.GetGUIThreadInfo.restype = ctypes.c_int
    u32.GetGUIThreadInfo.argtypes = [ul, ctypes.POINTER(GUITHREADINFO)]
    u32.GetAsyncKeyState.restype = ctypes.c_short
    u32.GetAsyncKeyState.argtypes = [ctypes.c_int]
    u32.SendInput.restype = ui
    u32.SendInput.argtypes = [ui, ctypes.POINTER(INPUT), ctypes.c_int]
    u32.AttachThreadInput.restype = ctypes.c_int
    u32.AttachThreadInput.argtypes = [ul, ul, ctypes.c_int]
    u32.LoadImageW.restype = vp
    u32.LoadImageW.argtypes = [vp, ctypes.c_wchar_p, ui, ctypes.c_int,
                               ctypes.c_int, ui]
    u32.LoadIconW.restype = vp
    u32.LoadIconW.argtypes = [vp, vp]
    u32.CreatePopupMenu.restype = vp
    u32.AppendMenuW.restype = ctypes.c_int
    u32.AppendMenuW.argtypes = [vp, ui, sz, ctypes.c_wchar_p]
    u32.TrackPopupMenu.restype = ctypes.c_int
    u32.TrackPopupMenu.argtypes = [vp, ui, ctypes.c_int, ctypes.c_int,
                                   ctypes.c_int, vp, vp]
    u32.DestroyMenu.argtypes = [vp]
    s32.Shell_NotifyIconW.restype = ctypes.c_int
    s32.Shell_NotifyIconW.argtypes = [ul, ctypes.POINTER(NOTIFYICONDATAW)]
    u32.MonitorFromPoint.restype = vp
    u32.MonitorFromPoint.argtypes = [POINT, ul]
    u32.GetMonitorInfoW.restype = ctypes.c_int
    u32.GetMonitorInfoW.argtypes = [vp, ctypes.POINTER(MONITORINFO)]
    u32.GetSystemMetrics.restype = ctypes.c_int
    u32.GetSystemMetrics.argtypes = [ctypes.c_int]
    u32.MessageBoxW.restype = ctypes.c_int
    u32.MessageBoxW.argtypes = [vp, ctypes.c_wchar_p, ctypes.c_wchar_p, ui]
    u32.FindWindowW.restype = vp
    u32.FindWindowW.argtypes = [ctypes.c_wchar_p, ctypes.c_wchar_p]
    k32.GetModuleHandleW.restype = vp
    k32.GetModuleHandleW.argtypes = [ctypes.c_wchar_p]
    k32.CreateMutexW.restype = vp
    k32.CreateMutexW.argtypes = [vp, ctypes.c_int, ctypes.c_wchar_p]
    k32.GetLastError.restype = ui
    k32.CreateEventW.restype = vp
    k32.CreateEventW.argtypes = [vp, ctypes.c_int, ctypes.c_int,
                                 ctypes.c_wchar_p]
    k32.OpenEventW.restype = vp
    k32.OpenEventW.argtypes = [ui, ctypes.c_int, ctypes.c_wchar_p]
    k32.SetEvent.restype = ctypes.c_int
    k32.SetEvent.argtypes = [vp]
    k32.WaitForSingleObject.restype = ui
    k32.WaitForSingleObject.argtypes = [vp, ui]
    k32.CloseHandle.restype = ctypes.c_int
    k32.CloseHandle.argtypes = [vp]
    k32.GetCurrentThreadId.restype = ul
    _U32, _K32, _S32 = u32, k32, s32
    return u32, k32


def _msg(text, error=True):
    if sys.platform != 'win32':
        print(text)
        return
    try:
        u32, _ = _win32()
        u32.MessageBoxW(None, text, APP_NAME, 0x10 if error else 0x40)
    except Exception:
        pass


def work_area(x, y):
    """Zone de travail du moniteur contenant (x, y)."""
    try:
        u32, _ = _win32()
        hmon = u32.MonitorFromPoint(POINT(x, y), 2)  # MONITOR_DEFAULTTONEAREST
        mi = MONITORINFO()
        mi.cbSize = ctypes.sizeof(MONITORINFO)
        if hmon and u32.GetMonitorInfoW(hmon, ctypes.byref(mi)):
            return (mi.rcWork.left, mi.rcWork.top,
                    mi.rcWork.right, mi.rcWork.bottom)
        return (0, 0, u32.GetSystemMetrics(0), u32.GetSystemMetrics(1))
    except Exception:
        return (0, 0, 1280, 720)


def _key_down(vk):
    try:
        u32, _ = _win32()
        return bool(u32.GetAsyncKeyState(vk) & 0x8000)
    except Exception:
        return False


class Watcher:
    """Crochet clavier + presse-papiers + icone de notification."""

    def __init__(self, html_path, icon_path, fix_mod):
        self.html_path = html_path
        self.icon_path = icon_path
        self.fix = fix_mod
        self.models = None
        self.default_layout = load_settings()['default_layout']
        self.queue = queue.Queue()
        self.paused = False
        self.proposal = None
        self.pending_seq = 0
        self.update_seq = 0
        self.handled_seq = 0
        self.self_set_text = None
        self.overlay_open = False
        self.block_v = False
        self.hwnd = None
        self.hook = None
        self.icon = None
        self.stop_handle = None
        self.worker_event = threading.Event()
        self.worker_stop = threading.Event()
        self.ready = threading.Event()
        self.start_error = None
        self._thread = None
        self._worker_thread = None
        self._clip_get = None
        self._clip_set = None
        self._wndproc_ref = None
        self._hook_ref = None

    # -- cycle de vie --

    def start(self):
        with open(self.html_path, encoding='utf-8') as f:
            self.models = load_models(f.read())
        from win32_clip import win32_clip
        self._clip_get, self._clip_set = win32_clip()
        self._worker_thread = threading.Thread(target=self._worker, daemon=True)
        self._worker_thread.start()
        self._thread = threading.Thread(target=self._win_main, daemon=True)
        self._thread.start()
        if not self.ready.wait(8):
            self.start_error = 'delai depasse au demarrage'
        if self.start_error:
            raise RuntimeError(self.start_error)

    def stop(self):
        if sys.platform == 'win32':
            try:
                if self.hwnd:
                    _U32.PostMessageW(self.hwnd, WM_STOP, 0, 0)
                elif self.stop_handle:
                    _K32.SetEvent(self.stop_handle)
            except Exception:
                pass
        self.worker_stop.set()
        self.worker_event.set()

    def wait(self):
        for t in (self._worker_thread, self._thread):
            if t is not None:
                t.join(3)

    # -- detection au fil du presse-papiers --

    def _on_update(self):
        try:
            u32, _ = _win32()
            self.update_seq = u32.GetClipboardSequenceNumber()
            self.worker_event.set()
        except Exception:
            pass

    def _worker(self):
        while not self.worker_stop.is_set():
            self.worker_event.wait(0.5)
            self.worker_event.clear()
            if self.worker_stop.is_set():
                break
            try:
                u32, _ = _win32()
                seq = self.update_seq
                if seq == self.handled_seq:
                    self.proposal = None
                    self.pending_seq = seq
                    continue
                try:
                    text = self._clip_get() if self._clip_get else ''
                except Exception:
                    text = ''
                if u32.GetClipboardSequenceNumber() != seq:
                    self.worker_event.set()
                    continue
                if self.self_set_text is not None and text == self.self_set_text:
                    self.self_set_text = None
                    self.proposal = None
                    self.pending_seq = seq
                    self.handled_seq = seq
                    continue
                self.proposal = (detect_text(text, self.models, self.fix,
                                             self.default_layout)
                                 if text else None)
                self.pending_seq = seq
            except Exception:
                self.proposal = None

    # -- boucle Win32 --

    def _win_main(self):
        u32 = k32 = None
        try:
            u32, k32 = _win32()
            hinst = k32.GetModuleHandleW(None)
            self._wndproc_ref = WNDPROC(self._wndproc)
            wc = WNDCLASSW()
            wc.lpfnWndProc = ctypes.cast(self._wndproc_ref, ctypes.c_void_p)
            wc.hInstance = hinst
            wc.lpszClassName = WINDOW_CLASS
            if not u32.RegisterClassW(ctypes.byref(wc)):
                err = k32.GetLastError()
                if err != 1410:  # ERROR_CLASS_ALREADY_EXISTS
                    raise OSError('RegisterClassW: %d' % err)
            self.hwnd = u32.CreateWindowExW(
                0, WINDOW_CLASS, APP_NAME, 0, 0, 0, 0, 0,
                None, None, hinst, None)
            if not self.hwnd:
                raise OSError('CreateWindowExW: %d' % k32.GetLastError())
            u32.AddClipboardFormatListener(self.hwnd)
            self._add_tray()
            self.stop_handle = k32.CreateEventW(None, False, False, STOP_EVENT)
            if self.stop_handle:
                threading.Thread(target=self._wait_stop,
                                 args=(self.stop_handle,), daemon=True).start()
            self._hook_ref = HOOKPROC(self._hook)
            self.hook = u32.SetWindowsHookExW(WH_KEYBOARD_LL, self._hook_ref,
                                              hinst, 0)
            if not self.hook:
                raise OSError('SetWindowsHookExW: %d' % k32.GetLastError())
            # Le presse-papiers peut deja contenir un texte : premiere analyse.
            self._on_update()
            self.ready.set()
            msg = MSG()
            while u32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
                u32.TranslateMessage(ctypes.byref(msg))
                u32.DispatchMessageW(ctypes.byref(msg))
        except Exception as e:
            self.start_error = str(e)
            self.ready.set()
            self.queue.put(('error', 'Surveillance impossible : %s' % e))
        finally:
            try:
                if u32:
                    if self.hook:
                        u32.UnhookWindowsHookEx(self.hook)
                        self.hook = None
                    if self.icon is not None:
                        _S32.Shell_NotifyIconW(2, ctypes.byref(self.icon))
                        self.icon = None
                    if self.hwnd:
                        u32.RemoveClipboardFormatListener(self.hwnd)
                        u32.DestroyWindow(self.hwnd)
                        self.hwnd = None
                if k32 and self.stop_handle:
                    k32.SetEvent(self.stop_handle)
                    k32.CloseHandle(self.stop_handle)
                    self.stop_handle = None
            except Exception:
                pass
            self.worker_stop.set()
            self.worker_event.set()
            self.queue.put(('stop',))

    def _wait_stop(self, handle):
        try:
            if _K32.WaitForSingleObject(handle, 0xFFFFFFFF) == 0 and self.hwnd:
                _U32.PostMessageW(self.hwnd, WM_STOP, 0, 0)
        except Exception:
            pass

    # -- fenetre cachee, icone, menu --

    def _wndproc(self, hwnd, msg, wparam, lparam):
        u32 = _U32
        try:
            if msg == WM_CLIPBOARDUPDATE:
                self._on_update()
                return 0
            if msg == WM_TRAY:
                code = lparam & 0xFFFF
                if code in (WM_RBUTTONUP, 0x007B):  # WM_CONTEXTMENU
                    self._menu()
                elif code == WM_LBUTTONDBLCLK:
                    self._open_app()
                return 0
            if msg == WM_COMMAND:
                cmd = wparam & 0xFFFF
                if cmd == 1:
                    self._toggle_pause()
                elif cmd == 2:
                    self._open_app()
                elif cmd == 3:
                    u32.DestroyWindow(hwnd)
                return 0
            if msg in (WM_STOP, WM_CLOSE):
                u32.DestroyWindow(hwnd)
                return 0
            if msg == WM_DESTROY:
                u32.PostQuitMessage(0)
                return 0
            return u32.DefWindowProcW(hwnd, msg, wparam, lparam)
        except Exception:
            return 0

    def _load_icon(self):
        u32, _ = _win32()
        try:
            if self.icon_path and os.path.isfile(self.icon_path):
                h = u32.LoadImageW(None, self.icon_path, 1, 0, 0,
                                   0x10 | 0x40)  # ICON, FROMFILE, DEFAULTSIZE
                if h:
                    return h
        except Exception:
            pass
        return u32.LoadIconW(None, ctypes.c_void_p(32512))  # IDI_APPLICATION

    def _add_tray(self):
        u32, _ = _win32()
        nid = NOTIFYICONDATAW()
        nid.cbSize = ctypes.sizeof(NOTIFYICONDATAW)
        nid.hWnd = self.hwnd
        nid.uID = TRAY_ID
        nid.uFlags = 0x1 | 0x2 | 0x4  # MESSAGE | ICON | TIP
        nid.uCallbackMessage = WM_TRAY
        nid.hIcon = self._load_icon()
        nid.szTip = APP_NAME + ' - surveillance du presse-papiers'
        if _S32.Shell_NotifyIconW(0, ctypes.byref(nid)):  # NIM_ADD
            self.icon = nid

    def _set_tip(self, text):
        if self.icon is None:
            return
        u32, _ = _win32()
        nid = NOTIFYICONDATAW()
        nid.cbSize = ctypes.sizeof(NOTIFYICONDATAW)
        nid.hWnd = self.hwnd
        nid.uID = TRAY_ID
        nid.uFlags = 0x4  # NIF_TIP
        nid.szTip = text[:127]
        _S32.Shell_NotifyIconW(1, ctypes.byref(nid))  # NIM_MODIFY

    def _balloon(self, title, text):
        if self.icon is None:
            return
        u32, _ = _win32()
        nid = NOTIFYICONDATAW()
        nid.cbSize = ctypes.sizeof(NOTIFYICONDATAW)
        nid.hWnd = self.hwnd
        nid.uID = TRAY_ID
        nid.uFlags = 0x10  # NIF_INFO
        nid.szInfoTitle = title[:63]
        nid.szInfo = text[:255]
        nid.dwInfoFlags = 0x1  # NIIF_INFO
        _S32.Shell_NotifyIconW(1, ctypes.byref(nid))

    def _toggle_pause(self):
        self.paused = not self.paused
        if self.paused:
            self._set_tip(APP_NAME + ' - surveillance suspendue')
            self._balloon(APP_NAME, 'Surveillance du presse-papiers suspendue. '
                                    'Ctrl+V colle normalement.')
        else:
            self._set_tip(APP_NAME + ' - surveillance du presse-papiers')
            self._balloon(APP_NAME, 'Surveillance du presse-papiers reprise.')

    def set_default_layout(self, layout):
        """Memorise le clavier utilise quand la detection est ambigue."""
        layout = normalize_layout(layout)
        if save_settings({'default_layout': layout}):
            self.default_layout = layout
            return True
        return False

    def _change_default_layout(self, layout):
        if self.set_default_layout(layout):
            self._balloon(APP_NAME, 'Clavier par défaut si ambiguïté : %s.'
                          % layout_label(layout))
        else:
            self._balloon(APP_NAME, 'Impossible d’enregistrer le clavier '
                                    'par défaut.')

    def _menu(self):
        u32, _ = _win32()
        menu = u32.CreatePopupMenu()
        if not menu:
            return
        label = ('Reprendre la surveillance' if self.paused
                 else 'Suspendre la surveillance')
        u32.AppendMenuW(menu, 0, 1, label)
        u32.AppendMenuW(menu, 0, 2, 'Ouvrir le convertisseur')
        u32.AppendMenuW(menu, 0x800, 0, None)  # MF_SEPARATOR
        checked = 0x8  # MF_CHECKED
        u32.AppendMenuW(menu, checked if self.default_layout == 'azerty' else 0,
                        4, 'Défaut si ambigu : AZERTY')
        u32.AppendMenuW(menu, checked if self.default_layout == 'qwerty' else 0,
                        5, 'Défaut si ambigu : QWERTY')
        u32.AppendMenuW(menu, 0x800, 0, None)
        u32.AppendMenuW(menu, 0, 3, 'Quitter')
        pt = POINT()
        u32.GetCursorPos(ctypes.byref(pt))
        u32.SetForegroundWindow(self.hwnd)
        cmd = u32.TrackPopupMenu(menu, 0x100 | 0x2 | 0x80, pt.x, pt.y, 0,
                                 self.hwnd, None)
        u32.PostMessageW(self.hwnd, 0, 0, 0)  # WM_NULL
        u32.DestroyMenu(menu)
        if cmd == 1:
            self._toggle_pause()
        elif cmd == 2:
            self._open_app()
        elif cmd == 4:
            self._change_default_layout('azerty')
        elif cmd == 5:
            self._change_default_layout('qwerty')
        elif cmd == 3:
            u32.DestroyWindow(self.hwnd)

    def _open_app(self):
        if getattr(sys, 'frozen', False):
            subprocess.Popen([sys.executable])
        else:
            here = os.path.dirname(os.path.abspath(__file__))
            subprocess.Popen([sys.executable, os.path.join(here, 'app.py')])

    # -- crochet clavier --

    def _hook(self, ncode, wparam, lparam):
        if ncode < 0:
            return _U32.CallNextHookEx(None, ncode, wparam, lparam)
        try:
            kb = ctypes.cast(lparam,
                             ctypes.POINTER(KBDLLHOOKSTRUCT)).contents
            if kb.dwExtraInfo == MAGIC:
                return _U32.CallNextHookEx(None, ncode, wparam, lparam)
            # Pendant la proposition : Entree = convertir, Maj+Entree =
            # coller tel quel, Echap = annuler.
            if self.overlay_open and kb.vkCode in (VK_RETURN, VK_ESCAPE):
                if wparam in (WM_KEYDOWN, WM_SYSKEYDOWN):
                    if kb.vkCode == VK_ESCAPE:
                        choice = 'cancel'
                    elif _key_down(VK_SHIFT):
                        choice = 'keep'
                    else:
                        choice = 'convert'
                    self.queue.put(('choice', choice))
                return 1
            if kb.vkCode != VK_V:
                return _U32.CallNextHookEx(None, ncode, wparam, lparam)
            if wparam in (WM_KEYUP, WM_SYSKEYUP):
                if self.block_v:
                    self.block_v = False
                    return 1
                return _U32.CallNextHookEx(None, ncode, wparam, lparam)
            if wparam not in (WM_KEYDOWN, WM_SYSKEYDOWN):
                return _U32.CallNextHookEx(None, ncode, wparam, lparam)
            if (not _key_down(VK_CONTROL) or _key_down(VK_SHIFT)
                    or _key_down(VK_MENU) or _key_down(VK_LWIN)
                    or _key_down(VK_RWIN)):
                return _U32.CallNextHookEx(None, ncode, wparam, lparam)
            if self.paused:
                return _U32.CallNextHookEx(None, ncode, wparam, lparam)
            if self.overlay_open or self.block_v:
                self.block_v = True
                return 1
            seq = _U32.GetClipboardSequenceNumber()
            prop = self.proposal
            if (not prop or self.pending_seq != seq
                    or self.handled_seq == seq):
                return _U32.CallNextHookEx(None, ncode, wparam, lparam)
            self.block_v = True
            self.overlay_open = True
            target = _U32.GetForegroundWindow()
            anchor = self._anchor(target)
            self.queue.put(('propose', prop, target, anchor))
            return 1
        except Exception:
            return _U32.CallNextHookEx(None, ncode, wparam, lparam)

    def _anchor(self, hwnd):
        try:
            u32, _ = _win32()
            if hwnd:
                tid = u32.GetWindowThreadProcessId(hwnd, None)
                gti = GUITHREADINFO()
                gti.cbSize = ctypes.sizeof(GUITHREADINFO)
                if u32.GetGUIThreadInfo(tid, ctypes.byref(gti)) and gti.hwndCaret:
                    pt = POINT(gti.rcCaret.left, gti.rcCaret.bottom)
                    if u32.ClientToScreen(gti.hwndCaret, ctypes.byref(pt)):
                        return (pt.x, pt.y)
        except Exception:
            pass
        try:
            pt = POINT()
            _U32.GetCursorPos(ctypes.byref(pt))
            return (pt.x, pt.y)
        except Exception:
            return (200, 200)

    # -- choix de l'utilisateur, collage --

    def resolve(self, choice, prop, target):
        err = None
        try:
            if choice == 'convert':
                try:
                    self.self_set_text = prop['text']
                    self._clip_set(prop['text'])
                    self.handled_seq = _U32.GetClipboardSequenceNumber()
                except Exception as e:
                    err = 'Ecriture du presse-papiers impossible : %s' % e
            elif choice in ('keep', 'cancel'):
                self.handled_seq = self.pending_seq
            # choice == 'dismiss' : proposition conservee pour le prochain
            # Ctrl+V (l'utilisateur a seulement clique ailleurs).
            self.overlay_open = False
            self.block_v = False
            if choice in ('convert', 'keep') and err is None:
                if self._focus(target):
                    time.sleep(0.06)
                    self._send_ctrl_v()
        finally:
            self.overlay_open = False
            self.block_v = False
        return err

    def _focus(self, hwnd):
        try:
            u32, k32 = _win32()
            if not hwnd or not u32.IsWindow(hwnd):
                return False
            fg = u32.GetForegroundWindow()
            tid_me = k32.GetCurrentThreadId()
            tid_fg = u32.GetWindowThreadProcessId(fg, None) if fg else 0
            attached = False
            if tid_fg and tid_fg != tid_me:
                attached = bool(u32.AttachThreadInput(tid_me, tid_fg, True))
            try:
                u32.ShowWindow(hwnd, 9)  # SW_RESTORE
                u32.BringWindowToTop(hwnd)
                u32.SetForegroundWindow(hwnd)
            finally:
                if attached:
                    u32.AttachThreadInput(tid_me, tid_fg, False)
            return u32.GetForegroundWindow() == hwnd
        except Exception:
            return False

    def _send_ctrl_v(self):
        try:
            u32, _ = _win32()
            events = (INPUT * 4)()
            for i, (vk, up) in enumerate(((VK_CONTROL, False), (VK_V, False),
                                          (VK_V, True), (VK_CONTROL, True))):
                events[i].type = 1  # INPUT_KEYBOARD
                events[i].u.ki.wVk = vk
                events[i].u.ki.wScan = 0
                events[i].u.ki.dwFlags = 0x2 if up else 0
                events[i].u.ki.time = 0
                events[i].u.ki.dwExtraInfo = MAGIC
            u32.SendInput(4, events, ctypes.sizeof(INPUT))
        except Exception:
            pass


# --- interface de proposition ---

BG = '#1e2430'
CARD = '#262e3d'
PREVIEW = '#1b2536'
BORDER = '#405477'
SHADOW = '#0b1019'
TEXT = '#f2f5fa'
MUTED = '#9aa6b8'
ACCENT = '#7aa2ff'
ACCENT_TEXT = '#0b1020'
SECONDARY = '#39445a'


def show_proposal(root, watcher, data, target, anchor, current):
    import tkinter as tk
    from tkinter import messagebox

    if current.get('win') is not None:
        try:
            current['win'].destroy()
        except Exception:
            pass
        current['win'] = None
        current['choose'] = None

    win = tk.Toplevel(root)
    win.withdraw()
    win.overrideredirect(True)
    win.attributes('-topmost', True)
    try:
        win.attributes('-toolwindow', True)
    except Exception:
        pass
    win.configure(bg=SHADOW)
    win.resizable(False, False)

    shell = tk.Frame(win, bg=SHADOW)
    shell.pack(fill='both', expand=True)
    card = tk.Frame(shell, bg=CARD, highlightbackground=BORDER,
                    highlightthickness=1)
    card.pack(fill='both', expand=True, padx=2, pady=2)
    tk.Frame(card, bg=ACCENT, height=4).pack(fill='x')
    outer = tk.Frame(card, bg=CARD, padx=18, pady=14)
    outer.pack(fill='both', expand=True)

    header = tk.Frame(outer, bg=CARD)
    header.pack(fill='x')
    badge = tk.Canvas(header, width=44, height=44, bg=CARD,
                      highlightthickness=0)
    badge.create_oval(2, 2, 42, 42, fill=ACCENT, outline='')
    badge.create_text(22, 22, text='A\u05d0', fill=ACCENT_TEXT,
                      font=('Segoe UI', 10, 'bold'))
    badge.pack(side='left', padx=(0, 12))

    titles = tk.Frame(header, bg=CARD)
    titles.pack(side='left', fill='x', expand=True)
    tk.Label(titles, text='Convertir avant de coller ?', bg=CARD, fg=TEXT,
             font=('Segoe UI', 13, 'bold'), anchor='w').pack(fill='x')
    tk.Label(titles, text='Vérifiez l’aperçu, puis choisissez.', bg=CARD,
             fg=MUTED, font=('Segoe UI', 9), anchor='w').pack(
        fill='x', pady=(2, 0))

    close_btn = tk.Button(header, text='\u2715',
                          command=lambda: choose('cancel'),
                          bg=CARD, fg=MUTED, activebackground=SECONDARY,
                          activeforeground=TEXT, relief='flat', bd=0,
                          highlightthickness=0, padx=6, pady=1,
                          cursor='hand2', font=('Segoe UI', 11))
    close_btn.pack(side='right', anchor='n')

    rtl = data['direction'] == 'toHe'
    state = {'layout': normalize_layout(data['layout']),
             'text': data['text'], 'manual': False,
             'convert_button': None}
    selected_var = tk.StringVar(value=state['layout'])
    default_var = tk.StringVar(value=normalize_layout(
        data.get('layout_default', data['layout'])))

    preview_box = tk.Frame(outer, bg=PREVIEW, padx=14, pady=10,
                           highlightbackground=BORDER, highlightthickness=1)
    preview_box.pack(fill='x', pady=(14, 0))
    tk.Label(preview_box, text='APERÇU', bg=PREVIEW, fg=ACCENT,
             font=('Segoe UI', 7, 'bold'), anchor='w').pack(fill='x')
    preview_label = tk.Label(preview_box, text=truncate(data['text'], 220),
                             bg=PREVIEW, fg=TEXT, font=('Segoe UI', 16),
                             wraplength=470,
                             justify=('right' if rtl else 'left'),
                             anchor=('e' if rtl else 'w'))
    preview_label.pack(fill='x', pady=(4, 0))
    source_one = ' '.join(data['source_text'].split())
    tk.Label(outer, text='Original : ' + truncate(source_one, 110),
             bg=CARD, fg=MUTED, font=('Segoe UI', 8),
             justify=('right' if rtl else 'left'),
             anchor=('e' if rtl else 'w')).pack(fill='x', pady=(8, 0))

    layout_line = tk.Frame(outer, bg=CARD)
    layout_line.pack(fill='x', pady=(12, 0))
    tk.Label(layout_line, text='Clavier :', bg=CARD, fg=MUTED,
             font=('Segoe UI', 9), anchor='w').pack(side='left')
    layout_btn = tk.Menubutton(
        layout_line, text=layout_label(state['layout']) + '  \u25be',
        bg=SECONDARY, fg=TEXT, activebackground='#4a5874',
        activeforeground=TEXT, relief='flat', bd=0,
        highlightthickness=0, padx=10, pady=3, cursor='hand2',
        font=('Segoe UI', 10), indicatoron=False, justify='center')
    layout_btn.pack(side='left', padx=(6, 0))
    note_label = tk.Label(layout_line, text='', bg=CARD, fg=MUTED,
                          font=('Segoe UI', 8), anchor='w')
    note_label.pack(side='left', padx=(8, 0))

    row = tk.Frame(outer, bg=CARD)
    row.pack(fill='x', pady=(14, 0))

    def note_text():
        if state['manual']:
            return 'Choix manuel'
        if data.get('layout_ambiguous'):
            return 'Détection ambiguë'
        return 'Détection automatique'

    def apply_layout(layout, manual=True):
        layout = normalize_layout(layout)
        if manual:
            state['manual'] = True
        state['layout'] = layout
        state['text'] = convert_for_layout(
            data['source_text'], layout, data['direction'], watcher.fix)
        preview_label.configure(text=truncate(state['text'], 220)
                                or '(aucun texte)')
        selected_var.set(layout)
        layout_btn.configure(text=layout_label(layout) + '  \u25be')
        note_label.configure(text=note_text())
        convert_button = state.get('convert_button')
        if convert_button is not None:
            convert_button.configure(
                state='normal' if state['text'].strip() else 'disabled')

    def select_layout(layout):
        apply_layout(layout, manual=True)
        try:
            b1.focus_set()
        except Exception:
            pass

    def set_default(layout):
        layout = normalize_layout(layout)
        old = normalize_layout(data.get('layout_default', state['layout']))
        if layout == old:
            return
        if not watcher.set_default_layout(layout):
            default_var.set(old)
            try:
                messagebox.showerror(
                    APP_NAME, 'Impossible d’enregistrer le clavier par '
                              'défaut.')
            except Exception:
                pass
            return
        data['layout_default'] = layout
        if data.get('layout_ambiguous') and not state['manual']:
            apply_layout(layout, manual=False)
        else:
            note_label.configure(text=note_text())
        try:
            b1.focus_set()
        except Exception:
            pass

    menu = tk.Menu(layout_btn, tearoff=0, bg=CARD, fg=TEXT,
                   activebackground=ACCENT, activeforeground=ACCENT_TEXT,
                   font=('Segoe UI', 9))
    menu.add_radiobutton(label='Utiliser AZERTY', variable=selected_var,
                         value='azerty',
                         command=lambda: select_layout('azerty'))
    menu.add_radiobutton(label='Utiliser QWERTY', variable=selected_var,
                         value='qwerty',
                         command=lambda: select_layout('qwerty'))
    menu.add_separator()
    menu.add_radiobutton(label='Défaut si ambigu : AZERTY',
                         variable=default_var, value='azerty',
                         command=lambda: set_default('azerty'))
    menu.add_radiobutton(label='Défaut si ambigu : QWERTY',
                         variable=default_var, value='qwerty',
                         command=lambda: set_default('qwerty'))
    layout_btn.configure(menu=menu)
    note_label.configure(text=note_text())

    def choose(choice):
        if current.get('win') is not win or current.get('choose') is None:
            return
        if choice == 'convert' and not state['text'].strip():
            return
        current['choose'] = None
        current['win'] = None
        try:
            win.destroy()
        except Exception:
            pass
        selected = dict(data)
        selected['layout'] = state['layout']
        selected['text'] = state['text']
        err = watcher.resolve(choice, selected, target)
        if err:
            try:
                messagebox.showerror(APP_NAME, err)
            except Exception:
                pass

    b1 = tk.Button(row, text='Convertir et coller',
                   command=lambda: choose('convert'),
                   bg=ACCENT, fg=ACCENT_TEXT, activebackground='#9ab8ff',
                   activeforeground=ACCENT_TEXT, relief='flat', bd=0,
                   highlightthickness=0, padx=16, pady=8, cursor='hand2',
                   font=('Segoe UI', 10, 'bold'))
    b1.pack(side='left')
    state['convert_button'] = b1
    b2 = tk.Button(row, text='Coller tel quel',
                   command=lambda: choose('keep'),
                   bg=SECONDARY, fg=TEXT, activebackground='#4a5874',
                   activeforeground=TEXT, relief='flat', bd=0,
                   highlightthickness=0, padx=14, pady=8, cursor='hand2',
                   font=('Segoe UI', 9))
    b2.pack(side='left', padx=(10, 0))
    b3 = tk.Button(row, text='Annuler', command=lambda: choose('cancel'),
                   bg=SECONDARY, fg=TEXT, activebackground='#4a5874',
                   activeforeground=TEXT, relief='flat', bd=0,
                   highlightthickness=0, padx=14, pady=8, cursor='hand2',
                   font=('Segoe UI', 9))
    b3.pack(side='right')

    footer = tk.Frame(outer, bg=CARD)
    footer.pack(fill='x', pady=(10, 0))
    tk.Label(footer, text='Entrée : convertir  ·  Maj+Entrée : original  ·  '
                          'Échap : annuler', bg=CARD, fg=MUTED,
             font=('Segoe UI', 8), anchor='w').pack(fill='x')
    tk.Label(footer, text='La fenêtre reste ouverte ; clique ailleurs pour '
                          'la fermer.', bg=CARD, fg=ACCENT,
             font=('Segoe UI', 8), anchor='w').pack(fill='x', pady=(2, 0))

    win.bind('<Return>', lambda _e: choose('convert'))
    win.bind('<Shift-Return>', lambda _e: choose('keep'))
    win.bind('<Escape>', lambda _e: choose('cancel'))
    win.protocol('WM_DELETE_WINDOW', lambda: choose('cancel'))

    win.update_idletasks()
    w = max(560, win.winfo_reqwidth())
    h = win.winfo_reqheight()
    left, top, right, bottom = work_area(anchor[0], anchor[1])
    w = min(w, max(320, right - left - 16))
    x = min(max(left + 8, anchor[0] - w // 2), right - w - 8)
    y = anchor[1] + 20
    if y + h > bottom - 8:
        y = anchor[1] - h - 28
    y = max(top + 8, y)
    win.geometry('%dx%d+%d+%d' % (w, h, x, y))
    win.deiconify()
    win.lift()
    try:
        win.focus_force()
    except Exception:
        pass
    b1.focus_set()

    mouse_buttons = (0x01, 0x02, 0x04)
    try:
        u32, _ = _win32()
        for vk in mouse_buttons:
            u32.GetAsyncKeyState(vk)
    except Exception:
        pass

    def click_outside():
        # Aucune minuterie de fermeture. On surveille le clic hors de la
        # fenetre (ou de son menu), sans dependre du focus : un simple clic
        # ailleurs ferme la proposition. Le bit 0x0001 attrape aussi un clic
        # tres bref, relache avant le passage suivant.
        if current.get('win') is not win:
            return
        try:
            u32, _ = _win32()
            states = [u32.GetAsyncKeyState(vk) for vk in mouse_buttons]
            if any(state & 0x8001 for state in states):
                pt = POINT()
                u32.GetCursorPos(ctypes.byref(pt))
                hit = u32.WindowFromPoint(pt)
                if not hit:
                    choose('dismiss')
                    return
                pid = ctypes.c_ulong()
                u32.GetWindowThreadProcessId(hit, ctypes.byref(pid))
                if pid.value != os.getpid():
                    choose('dismiss')
                    return
        except Exception:
            pass
        try:
            win.after(50, click_outside)
        except Exception:
            pass

    current['win'] = win
    current['choose'] = choose
    win.after(30, click_outside)


def _run_tk(watcher):
    import tkinter as tk
    from tkinter import messagebox

    root = tk.Tk()
    root.withdraw()
    root.title(APP_NAME)
    current = {'win': None, 'choose': None}

    def poll():
        try:
            while True:
                item = watcher.queue.get_nowait()
                kind = item[0]
                if kind == 'propose':
                    show_proposal(root, watcher, item[1], item[2], item[3],
                                  current)
                elif kind == 'choice':
                    cb = current.get('choose')
                    if cb:
                        cb(item[1])
                elif kind == 'error':
                    try:
                        messagebox.showerror(APP_NAME, item[1])
                    except Exception:
                        pass
                elif kind == 'stop':
                    try:
                        root.destroy()
                    except Exception:
                        pass
                    return
        except queue.Empty:
            pass
        try:
            root.after(40, poll)
        except Exception:
            pass

    root.after(40, poll)
    root.mainloop()


_MUTEX = None


def _single_instance():
    global _MUTEX
    if sys.platform != 'win32':
        return True
    _, k32 = _win32()
    if _MUTEX:
        return True
    h = k32.CreateMutexW(None, False, MUTEX_NAME)
    err = k32.GetLastError()
    if not h:
        return True
    if err == 183:  # ERROR_ALREADY_EXISTS
        k32.CloseHandle(h)
        return False
    _MUTEX = h
    return True


def run(html_path=None, icon_path=None, fix_mod=None):
    if sys.platform != 'win32':
        _msg('La surveillance du presse-papiers est reservee a Windows.')
        return 1
    if fix_mod is None:
        _msg('Module de conversion manquant.')
        return 1
    here = os.path.dirname(os.path.abspath(__file__))
    html_path = html_path or os.path.join(here, 'convertisseur.html')
    icon_path = icon_path or os.path.join(here, 'app.ico')
    if not os.path.isfile(html_path):
        _msg('Introuvable : %s' % html_path)
        return 1
    if not _single_instance():
        return 0
    watcher = Watcher(html_path, icon_path, fix_mod)
    try:
        watcher.start()
    except Exception as e:
        _msg('Surveillance impossible : %s' % e)
        watcher.stop()
        return 1
    try:
        _run_tk(watcher)
    except Exception as e:
        _msg('Interface impossible : %s' % e)
        return 1
    finally:
        watcher.stop()
        watcher.wait()
    return 0


def run_stop():
    if sys.platform != 'win32':
        return 0
    signaled = False
    try:
        u32, k32 = _win32()
        h = k32.OpenEventW(0x0002, False, STOP_EVENT)
        if h:
            k32.SetEvent(h)
            k32.CloseHandle(h)
            signaled = True
    except Exception:
        return 0
    if not signaled:
        return 0
    # L'installeur remplace ou supprime l'exe juste apres : on attend que la
    # fenetre cachee du guetteur disparaisse (sinon fichier verrouille).
    try:
        u32, _ = _win32()
        for _i in range(100):
            if not u32.FindWindowW(WINDOW_CLASS, APP_NAME):
                break
            time.sleep(0.05)
    except Exception:
        pass
    return 0
