// Content script : convertit la selection dans le champ actif (input,
// textarea, contenteditable) ou copie le resultat pour du texte de page.
// Aucune donnee ne quitte la machine.
'use strict';

const TOAST_ID = 'conv-clavier-toast';
const HEBREW = /[\u0590-\u05FF]/;
let lastEditable = null;
let toastTimer = 0;

document.addEventListener('focusin', (e) => {
  if (textInputLike(e.target)) lastEditable = e.target;
}, true);

function textInputLike(el) {
  if (!el || el.nodeType !== 1) return false;
  if (el.tagName === 'TEXTAREA') return true;
  if (el.tagName !== 'INPUT') return false;
  const type = (el.type || 'text').toLowerCase();
  return type === 'text' || type === 'search' || type === 'url' ||
    type === 'tel' || type === 'email';
}

function editableRoot(node) {
  const el = node && (node.nodeType === 1 ? node : node.parentElement);
  if (!el || !el.closest) return null;
  return el.closest('[contenteditable=""], [contenteditable="true"], ' +
    '[contenteditable="plaintext-only"]');
}

function resolveTarget() {
  const candidates = [];
  if (document.activeElement) candidates.push(document.activeElement);
  if (lastEditable) candidates.push(lastEditable);
  for (const el of candidates) {
    if (!textInputLike(el)) continue;
    const start = el.selectionStart;
    const end = el.selectionEnd;
    if (typeof start === 'number' && typeof end === 'number' && end > start) {
      return { kind: 'input', el, start, end, text: el.value.slice(start, end) };
    }
  }
  const sel = window.getSelection();
  if (sel && sel.rangeCount > 0 && !sel.isCollapsed) {
    const text = sel.toString();
    if (text) {
      if (editableRoot(sel.anchorNode)) {
        return { kind: 'editable', sel, text };
      }
      return { kind: 'page', text };
    }
  }
  return null;
}

function replaceInput(target, out) {
  const el = target.el;
  el.focus();
  try {
    el.setSelectionRange(target.start, target.end);
  } catch {
    // certains champs refusent setSelectionRange : on tentera setRangeText
  }
  let ok = false;
  try {
    ok = document.execCommand('insertText', false, out);
  } catch {
    ok = false;
  }
  if (ok && el.value.slice(target.start, target.start + out.length) === out) {
    return true;
  }
  const before = el.value;
  el.setRangeText(out, target.start, target.end, 'end');
  if (el.value !== before) {
    el.dispatchEvent(new InputEvent('input', {
      bubbles: true, inputType: 'insertText', data: out,
    }));
  }
  return el.value !== before;
}

function replaceEditable(target, out) {
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
  }
}

function showToast(text, sub) {
  let host = document.getElementById(TOAST_ID);
  if (!host) {
    host = document.createElement('div');
    host.id = TOAST_ID;
    host.setAttribute('role', 'status');
    host.style.cssText = 'position:fixed;z-index:2147483647;right:16px;' +
      'bottom:16px;max-width:min(460px,82vw);';
    const root = host.attachShadow({ mode: 'open' });
    const style = document.createElement('style');
    style.textContent =
      '.box{font:13px/1.35 system-ui,-apple-system,Segoe UI,sans-serif;' +
      'background:#1f2430;color:#fff;border-radius:10px;padding:10px 12px;' +
      'box-shadow:0 6px 24px rgba(0,0,0,.35);border-inline-start:4px solid #6c8cff;' +
      'cursor:pointer}' +
      '.t{font-size:15px;white-space:pre-wrap;word-break:break-word;' +
      'unicode-bidi:plaintext}' +
      '.s{opacity:.75;margin-top:4px;font-size:11px}';
    const box = document.createElement('div');
    box.className = 'box';
    const t = document.createElement('div');
    t.className = 't';
    const s = document.createElement('div');
    s.className = 's';
    box.append(t, s);
    root.append(style, box);
    host.addEventListener('click', () => host.remove());
    (document.body || document.documentElement).appendChild(host);
  }
  const box = host.shadowRoot.querySelector('.box');
  const t = host.shadowRoot.querySelector('.t');
  const s = host.shadowRoot.querySelector('.s');
  box.dir = HEBREW.test(text || '') ? 'rtl' : 'ltr';
  t.textContent = text || '';
  t.hidden = !text;
  s.textContent = sub || '';
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => host.remove(), 6500);
}

chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
  if (!msg || msg.type !== 'conv-selection') return undefined;
  const target = resolveTarget();
  if (!target || !target.text) {
    if (document.hasFocus()) {
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
