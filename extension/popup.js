// Popup : convertit a la volee et memorise les reglages (stockage local).
'use strict';

const els = {
  mode: document.getElementById('mode'),
  layout: document.getElementById('layout'),
  layoutRow: document.getElementById('layoutRow'),
  input: document.getElementById('input'),
  output: document.getElementById('output'),
  copy: document.getElementById('copy'),
  status: document.getElementById('status'),
};

let settings = Object.assign({}, Conv.DEFAULTS);
let statusTimer = 0;

function modeValue(s) {
  if (s.mode === 'latin') {
    return s.latinDir === 'toQw' ? 'latin/toQw' : 'latin/toAz';
  }
  if (s.direction === 'toHe' || s.direction === 'toFr') {
    return 'hebrew/' + s.direction;
  }
  return 'hebrew/auto';
}

function optsFromUI() {
  const parts = els.mode.value.split('/');
  const mode = parts[0] === 'latin' ? 'latin' : 'hebrew';
  const dir = parts[1];
  return {
    layout: els.layout.value === 'qwerty' ? 'qwerty' : 'azerty',
    mode,
    direction: mode === 'hebrew' ? dir : 'auto',
    latinDir: mode === 'latin' ? dir : 'toAz',
  };
}

function convert() {
  const out = Conv.convertText(els.input.value, optsFromUI());
  els.output.textContent = out;
  els.output.dir = /[\u0590-\u05FF]/.test(out) ? 'rtl' : 'ltr';
  els.output.classList.toggle('empty', !out);
}

function save() {
  chrome.storage.local.set({ settings: optsFromUI() });
}

function flash(msg) {
  els.status.textContent = msg;
  clearTimeout(statusTimer);
  statusTimer = setTimeout(() => { els.status.textContent = ''; }, 1600);
}

async function copy() {
  const text = els.output.textContent;
  if (!text) return;
  try {
    await navigator.clipboard.writeText(text);
    flash('Copié !');
  } catch {
    flash('Copie impossible.');
  }
}

function syncLayoutRow() {
  els.layoutRow.hidden = optsFromUI().mode === 'latin';
}

els.mode.addEventListener('change', () => {
  syncLayoutRow();
  convert();
  save();
});

els.layout.addEventListener('change', () => {
  convert();
  save();
});

els.input.addEventListener('input', convert);
els.copy.addEventListener('click', copy);

els.input.addEventListener('keydown', (e) => {
  if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
    e.preventDefault();
    copy();
  }
});

chrome.storage.local.get('settings').then((stored) => {
  settings = Conv.normalizeOptions(stored.settings || {});
  els.mode.value = modeValue(settings);
  els.layout.value = settings.layout;
  syncLayoutRow();
  convert();
  els.input.focus();
});
