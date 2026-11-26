// Content script : convertit la selection dans le champ actif (input,
// textarea, contenteditable) ou copie le resultat pour du texte de page.
// Aucune donnee ne quitte la machine.
'use strict';

const TOAST_MAX = 120;
let lastEditable = null;
let internalCopy = false;
let toastHost = null;
let toastBox = null;
let toastText = null;
let toastSub = null;
let toastTimer = 0;

document.addEventListener('focusin', (e) => {
  if (internalCopy) return;
  if (textInputLike(e.target)) lastEditable = e.target;
}, true);

function textInputLike(el) {
  if (!el || el.nodeType !== 1 || !el.isConnected) return false;
  if (el.readOnly || el.disabled) return false;
  if (el.tagName === 'TEXTAREA') return true;
  if (el.tagName !== 'INPUT') return false;
  const type = (el.type || 'text').toLowerCase();
  return type === 'text' || type === 'search' || type === 'url' ||
    type === 'tel';
}

function editableRoot(node) {
  if (!node) return null;
  const el = node.nodeType === 1 ? node : node.parentElement;
  if (!el) return null;
  if (document.designMode === 'on') return document.body || el;
  if (el.isContentEditable) return el;
  return null;
}

function inputSelection(el) {
  if (!textInputLike(el)) return null;
  const start = el.selectionStart;
  const end = el.selectionEnd;
  if (typeof start === 'number' && typeof end === 'number' && end > start) {
    return { kind: 'input', el, start, end, text: el.value.slice(start, end) };
  }
  return null;
}

function resolveTarget() {
  const active = inputSelection(document.activeElement);
  if (active) return active;
  const sel = window.getSelection();
  if (sel && sel.rangeCount > 0 && !sel.isCollapsed) {
    const text = sel.toString();
    if (text) {
      if (editableRoot(sel.anchorNode) &&
          (!sel.focusNode || editableRoot(sel.focusNode))) {
        return { kind: 'editable', sel, text };
      }
      return { kind: 'page', text };
    }
  }
  if (lastEditable && !lastEditable.isConnected) lastEditable = null;
  return inputSelection(lastEditable);
}

function replaceInput(target, out) {
  const el = target.el;
  if (!textInputLike(el)) return false;
  el.focus();
  try {
    el.setSelectionRange(target.start, target.end);
  } catch {
    // certains champs refusent setSelectionRange : on tentera setRangeText
  }
  const before = el.value;
  let ok = false;
  try {
    ok = document.execCommand('insertText', false, out);
  } catch {
    ok = false;
  }
  if (ok && el.value !== before) {
    return true;
  }
  el.setRangeText(out, target.start, target.end, 'end');
  if (el.value !== before) {
    el.dispatchEvent(new InputEvent('input', {
      bubbles: true, inputType: 'insertText', data: out,
    }));
  }
  return el.value !== before;
}

function replaceEditable(target, out) {
  const root = editableRoot(target.sel && target.sel.anchorNode);
  if (root && typeof root.focus === 'function') {
    try { root.focus(); } catch {}
  }
  let ok = false;
  try {
    ok = document.execCommand('insertText', false, out);
  } catch {
    ok = false;
  }
  if (ok) return true;
  try {
    const range = target.sel.rangeCount ? target.sel.getRangeAt(0) : null;
    if (!range) return false;
    range.deleteContents();
    range.insertNode(document.createTextNode(out));
    return true;
  } catch {
    return false;
  }
}

async function copyText(text) {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch {
    // repli pour les pages sans API Clipboard
  }
  const prevActive = document.activeElement;
  const sel = window.getSelection();
  const prevRanges = [];
  if (sel) {
    for (let i = 0; i < sel.rangeCount; i++) {
      prevRanges.push(sel.getRangeAt(i).cloneRange());
    }
  }
  internalCopy = true;
  try {
    const ta = document.createElement('textarea');
    ta.value = text;
    ta.setAttribute('readonly', '');
    ta.style.cssText = 'position:fixed;top:0;left:-9999px;opacity:0;';
    (document.body || document.documentElement).appendChild(ta);
    ta.select();
    const ok = document.execCommand('copy');
    ta.remove();
    return ok;
  } catch {
    return false;
  } finally {
    internalCopy = false;
    try {
      if (prevActive && prevActive.isConnected &&
          typeof prevActive.focus === 'function') {
        prevActive.focus({ preventScroll: true });
      }
      if (sel && prevRanges.length) {
        sel.removeAllRanges();
        for (const r of prevRanges) sel.addRange(r);
      }
    } catch {}
  }
}

function showToast(text, sub) {
  if (!toastHost || !toastHost.isConnected) {
    toastHost = document.createElement('div');
    toastHost.setAttribute('role', 'status');
    toastHost.style.cssText = 'all:initial;position:fixed;z-index:2147483647;' +
      'right:16px;bottom:16px;max-width:min(460px,82vw);';
    const root = toastHost.attachShadow({ mode: 'closed' });
    const style = document.createElement('style');
    style.textContent =
      ':host{all:initial!important}' +
      '.box{font:13px/1.35 system-ui,-apple-system,Segoe UI,sans-serif;' +
      'background:#1f2430;color:#fff;border-radius:10px;padding:10px 12px;' +
      'box-shadow:0 6px 24px rgba(0,0,0,.35);border-inline-start:4px solid #6c8cff;' +
      'cursor:pointer;box-sizing:border-box}' +
      '.t{font-size:15px;white-space:pre-wrap;word-break:break-word;' +
      'unicode-bidi:plaintext;max-height:140px;overflow:hidden}' +
      '.s{opacity:.75;margin-top:4px;font-size:11px}';
    toastBox = document.createElement('div');
    toastBox.className = 'box';
    toastText = document.createElement('div');
    toastText.className = 't';
    toastSub = document.createElement('div');
    toastSub.className = 's';
    toastBox.append(toastText, toastSub);
    root.append(style, toastBox);
    toastHost.addEventListener('click', () => {
      if (toastHost) toastHost.remove();
    });
    (document.body || document.documentElement).appendChild(toastHost);
  }
  const raw = text || '';
  const preview = raw.length > TOAST_MAX ? raw.slice(0, TOAST_MAX) + '\u2026' : raw;
  toastBox.dir = 'auto';
  toastText.textContent = preview;
  toastText.hidden = !preview;
  toastSub.textContent = sub || '';
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => {
    if (toastHost) toastHost.remove();
  }, 6500);
}

chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
  if (!msg || msg.type !== 'conv-selection') return undefined;
  const target = resolveTarget();
  if (!target || !target.text) {
    const active = document.activeElement;
    if (document.hasFocus() && (!active || active.tagName !== 'IFRAME')) {
      showToast('', 'Sélectionnez d’abord du texte à convertir.');
      sendResponse({ ok: false, empty: true });
    }
    return undefined;
  }
  const out = Conv.convertText(target.text, msg.opts || {});
  if (out === target.text) {
    showToast(out, 'Aucun changement (texte déjà converti ?).');
    sendResponse({ ok: true, changed: false });
    return undefined;
  }
  if (target.kind === 'input' && replaceInput(target, out)) {
    showToast(out, 'Converti dans le champ.');
    sendResponse({ ok: true, changed: true });
    return undefined;
  }
  if (target.kind === 'editable' && replaceEditable(target, out)) {
    showToast(out, 'Converti dans le champ.');
    sendResponse({ ok: true, changed: true });
    return undefined;
  }
  copyText(out).then((copied) => {
    showToast(out, copied ? 'Copié dans le presse-papiers.'
      : 'Copie impossible dans cette page.');
    sendResponse({ ok: copied, changed: false });
  });
  return true; // reponse asynchrone
});
