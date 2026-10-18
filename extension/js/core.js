// Coeur de conversion de l'extension : tables et fonctions GENEREES depuis
// convertisseur.html par gen_maps.py (source unique). Ne pas editer les blocs
// marques. Le reste (glue) est ecrit a la main.
'use strict';

// <maps:generated>
const FR_TO_HE = {
  "a": "/", "A": "/", "z": "'", "Z": "'",
  "e": "\u05e7", "E": "\u05e7", "r": "\u05e8", "R": "\u05e8",
  "t": "\u05d0", "T": "\u05d0", "y": "\u05d8", "Y": "\u05d8",
  "u": "\u05d5", "U": "\u05d5", "i": "\u05df", "I": "\u05df",
  "o": "\u05dd", "O": "\u05dd", "p": "\u05e4", "P": "\u05e4",
  "^": "]", "\u00a8": "}", "$": "[", "\u00a3": "{",
  "\u00a4": "{", "q": "\u05e9", "Q": "\u05e9", "s": "\u05d3",
  "S": "\u05d3", "d": "\u05d2", "D": "\u05d2", "f": "\u05db",
  "F": "\u05db", "g": "\u05e2", "G": "\u05e2", "h": "\u05d9",
  "H": "\u05d9", "j": "\u05d7", "J": "\u05d7", "k": "\u05dc",
  "K": "\u05dc", "l": "\u05da", "L": "\u05da", "m": "\u05e3",
  "M": "\u05e3", "\u00f9": ",", "\u00d9": ",", "%": ",",
  "*": "\\", "w": "\u05d6", "W": "\u05d6", "x": "\u05e1",
  "X": "\u05e1", "c": "\u05d1", "C": "\u05d1", "v": "\u05d4",
  "V": "\u05d4", "b": "\u05e0", "B": "\u05e0", "n": "\u05de",
  "N": "\u05de", ",": "\u05e6", "?": "\u05e6", ";": "\u05ea",
  ".": "\u05ea", ":": "\u05e5", "/": "\u05e5", "!": ".",
  "\u00a7": ".", "\u00b2": ";", "&": "1", "1": "1",
  "\u00e9": "2", "2": "2", "~": "2", "\"": "3",
  "3": "3", "#": "3", "'": "4", "4": "4",
  "{": "4", "(": "5", "5": "5", "[": "5",
  "-": "6", "6": "6", "|": "6", "\u00e8": "7",
  "7": "7", "`": "7", "_": "8", "8": "8",
  "\\": "8", "\u00e7": "9", "9": "9", "\u00e0": "0",
  "0": "0", "@": "0", ")": "-", "\u00b0": "_",
  "]": "-", "=": "=", "+": "+", "}": "=",
};

const HE_TO_FR = {
  "/": "a", "'": "z", "\u05e7": "e", "\u05e8": "r",
  "\u05d0": "t", "\u05d8": "y", "\u05d5": "u", "\u05df": "i",
  "\u05dd": "o", "\u05e4": "p", "]": "^", "[": "$",
  "\u05e9": "q", "\u05d3": "s", "\u05d2": "d", "\u05db": "f",
  "\u05e2": "g", "\u05d9": "h", "\u05d7": "j", "\u05dc": "k",
  "\u05da": "l", "\u05e3": "m", ",": "\u00f9", "\u05d6": "w",
  "\u05e1": "x", "\u05d1": "c", "\u05d4": "v", "\u05e0": "b",
  "\u05de": "n", "\u05e6": ",", "\u05ea": ";", "\u05e5": ":",
  ".": "!", ";": "\u00b2", "1": "&", "2": "\u00e9",
  "3": "\"", "4": "'", "5": "(", "6": "-",
  "7": "\u00e8", "8": "_", "9": "\u00e7", "0": "\u00e0",
  "-": ")", "=": "=", "Q": "A", "W": "Z",
  "E": "E", "R": "R", "T": "T", "Y": "Y",
  "U": "U", "I": "I", "O": "O", "P": "P",
  "A": "Q", "S": "S", "D": "D", "F": "F",
  "G": "G", "H": "H", "J": "J", "K": "K",
  "L": "L", "Z": "W", "X": "X", "C": "C",
  "V": "V", "B": "B", "N": "N", "M": ",",
  ":": "M", "\"": "\u00f9", ")": "\u00e7", "(": "\u00e0",
};

const EN_TO_HE = {
  "q": "/", "Q": "/", "w": "'", "W": "'",
  "e": "\u05e7", "E": "\u05e7", "r": "\u05e8", "R": "\u05e8",
  "t": "\u05d0", "T": "\u05d0", "y": "\u05d8", "Y": "\u05d8",
  "u": "\u05d5", "U": "\u05d5", "i": "\u05df", "I": "\u05df",
  "o": "\u05dd", "O": "\u05dd", "p": "\u05e4", "P": "\u05e4",
  "[": "]", "{": "}", "]": "[", "}": "{",
  "\\": "\\", "|": "|", "a": "\u05e9", "A": "\u05e9",
  "s": "\u05d3", "S": "\u05d3", "d": "\u05d2", "D": "\u05d2",
  "f": "\u05db", "F": "\u05db", "g": "\u05e2", "G": "\u05e2",
  "h": "\u05d9", "H": "\u05d9", "j": "\u05d7", "J": "\u05d7",
  "k": "\u05dc", "K": "\u05dc", "l": "\u05da", "L": "\u05da",
  ";": "\u05e3", ":": "\u05e3", "'": ",", "\"": ",",
  "z": "\u05d6", "Z": "\u05d6", "x": "\u05e1", "X": "\u05e1",
  "c": "\u05d1", "C": "\u05d1", "v": "\u05d4", "V": "\u05d4",
  "b": "\u05e0", "B": "\u05e0", "n": "\u05de", "N": "\u05de",
  "m": "\u05e6", "M": "\u05e6", ",": "\u05ea", "<": ">",
  ".": "\u05e5", ">": "<", "/": ".", "?": ".",
  "`": ";", "~": ";", "1": "1", "!": "!",
  "2": "2", "@": "@", "3": "3", "#": "#",
  "4": "4", "$": "$", "5": "5", "%": "%",
  "6": "6", "^": "^", "7": "7", "&": "&",
  "8": "8", "*": "*", "9": "9", "(": ")",
  "0": "0", ")": "(", "-": "-", "_": "_",
  "=": "=", "+": "+",
};

const HE_TO_EN = {
  "/": "q", "'": "w", "\u05e7": "e", "\u05e8": "r",
  "\u05d0": "t", "\u05d8": "y", "\u05d5": "u", "\u05df": "i",
  "\u05dd": "o", "\u05e4": "p", "]": "[", "[": "]",
  "}": "{", "{": "}", "\u05e9": "a", "\u05d3": "s",
  "\u05d2": "d", "\u05db": "f", "\u05e2": "g", "\u05d9": "h",
  "\u05d7": "j", "\u05dc": "k", "\u05da": "l", "\u05e3": ";",
  ",": "'", "\u05d6": "z", "\u05e1": "x", "\u05d1": "c",
  "\u05d4": "v", "\u05e0": "b", "\u05de": "n", "\u05e6": "m",
  "\u05ea": ",", "\u05e5": ".", ".": "/", ";": "`",
  ")": "(", "(": ")", ">": "<", "<": ">",
};

const QW_TO_AZ = {
  "q": "a", "Q": "A", "w": "z", "W": "Z",
  "a": "q", "A": "Q", "z": "w", "Z": "W",
  "m": ",", "M": "?", ";": "m", ":": "M",
  "'": "\u00f9", "\"": "%", ",": ";", "<": ".",
  ".": ":", ">": "/", "/": "!", "?": "\u00a7",
  "[": "^", "{": "\u00a8", "]": "$", "}": "\u00a3",
  "\\": "*", "|": "\u03bc", "`": "\u00b2", "1": "&",
  "2": "\u00e9", "3": "\"", "4": "'", "5": "(",
  "6": "-", "7": "\u00e8", "8": "_", "9": "\u00e7",
  "0": "\u00e0", "-": ")", "!": "1", "@": "2",
  "#": "3", "$": "4", "%": "5", "^": "6",
  "&": "7", "*": "8", "(": "9", ")": "0",
  "_": "\u00b0",
};

const AZ_TO_QW = {
  "a": "q", "A": "Q", "z": "w", "Z": "W",
  "q": "a", "Q": "A", "w": "z", "W": "Z",
  ",": "m", "?": "M", "m": ";", "M": ":",
  "\u00f9": "'", "%": "\"", ";": ",", ".": "<",
  ":": ".", "/": ">", "!": "/", "\u00a7": "?",
  "^": "[", "\u00a8": "{", "$": "]", "\u00a3": "}",
  "*": "\\", "\u03bc": "|", "\u00b2": "`", "&": "1",
  "\u00e9": "2", "\"": "3", "'": "4", "(": "5",
  "-": "6", "\u00e8": "7", "_": "8", "\u00e7": "9",
  "\u00e0": "0", ")": "-", "1": "!", "2": "@",
  "3": "#", "4": "$", "5": "%", "6": "^",
  "7": "&", "8": "*", "9": "(", "0": ")",
  "\u00b0": "_",
};

const CAPS_SWAP = {"Q": "A", "A": "Q", "W": "Z", "Z": "W"};
// </maps:generated>

// <core:generated>
function convertSmart(text, fullMap, swapCaps, toFrench) {
  const capsTok = tok => {
    const letters = tok.replace(/[^A-Za-z]/g, '');
    return (letters.length && letters === letters.toUpperCase())
      ? [...tok].map(ch => (ch in swapCaps ? swapCaps[ch] : ch)).join('')
      : tok;
  };
  if (!/[\u0590-\u05FF]/.test(text)) {
    // Sans hebreu, pas de segmentation : un seul passage.
    if (!toFrench) return [...text].map(ch => (ch in fullMap ? fullMap[ch] : ch)).join('');
    if (!swapCaps) return text;
    return text.replace(/[^\s]*[A-Z][^\s]*/g, capsTok);
  }
  if (!toFrench) {
    // Sens inverse : seuls les mots 100 % latins sont convertis
    // ("abcש" reste intact : le contexte mot-entier compte).
    return text.split(/(\s+)/).map(tok => {
      if (!tok || /^\s+$/.test(tok) || /[\u0590-\u05FF]/.test(tok)) return tok;
      return [...tok].map(ch => (ch in fullMap ? fullMap[ch] : ch)).join('');
    }).join('');
  }
  let out = text.replace(/[^\s]*[\u0590-\u05FF][^\s]*/g, tok => [...tok].map(ch => (ch in fullMap ? fullMap[ch] : ch)).join(''));
  if (swapCaps) out = out.replace(/[^\s]*[A-Z][^\s]*/g, capsTok);
  return out;
}

function detectDir(text) {
  // Doit rester identique a autodir() dans fix-presse-papiers.py
  // (meme classe latine accentuee, meme seuil 0.2).
  // Heuristique : du francais normal ne contient aucun hebreu ; si au
  // moins 20 % des lettres latines sont en fait de l'hebreu, c'est une
  // frappe en clavier hebreu a reconvertir. En dessous, l'hebreu present
  // est preserve tel quel (melange avec du vrai hebreu).
  const h = (text.match(/[\u0590-\u05FF]/g) || []).length;
  const l = (text.match(/[A-Za-zéèêëàâäçîïôöùûüÉÈÀÇÙ]/g) || []).length;
  return (h > 0 && h >= l * 0.2) ? 'toFr' : 'toHe';
}
// </core:generated>

// --- glue extension ---
// Meme choix de table que doConvert() dans la page.
const MAPS = {
  azerty: { toHe: FR_TO_HE, toFr: HE_TO_FR, label: 'AZERTY', capsSwap: CAPS_SWAP },
  qwerty: { toHe: EN_TO_HE, toFr: HE_TO_EN, label: 'QWERTY', capsSwap: null },
};

const DEFAULTS = {
  layout: 'azerty',
  direction: 'auto',
  mode: 'hebrew',
  latinDir: 'toAz',
};

function normalizeOptions(opts) {
  const o = Object.assign({}, DEFAULTS, opts || {});
  if (!MAPS[o.layout]) o.layout = 'azerty';
  if (o.mode !== 'latin') o.mode = 'hebrew';
  if (o.latinDir !== 'toQw') o.latinDir = 'toAz';
  if (o.direction !== 'toHe' && o.direction !== 'toFr') o.direction = 'auto';
  return o;
}

function convertText(text, opts) {
  const o = normalizeOptions(opts);
  const src = String(text == null ? '' : text);
  if (o.mode === 'latin') {
    const m = o.latinDir === 'toAz' ? QW_TO_AZ : AZ_TO_QW;
    return [...src].map(ch => (ch in m ? m[ch] : ch)).join('');
  }
  const dir = o.direction === 'auto' ? detectDir(src) : o.direction;
  const toFrench = dir === 'toFr';
  const full = toFrench ? MAPS[o.layout].toFr : MAPS[o.layout].toHe;
  return convertSmart(src, full, MAPS[o.layout].capsSwap, toFrench);
}

globalThis.Conv = { convertText, detectDir, normalizeOptions, MAPS, DEFAULTS };
