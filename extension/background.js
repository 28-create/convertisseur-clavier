// Service worker : menu clic droit + raccourci clavier. La conversion
// elle-meme est faite par content.js (page active), jamais ici.
'use strict';

const DIRECTION_BY_MENU = {
  'conv-auto': 'auto',
  'conv-he': 'toHe',
  'conv-fr': 'toFr',
};

function createMenus() {
  const ignoreErr = () => { void chrome.runtime.lastError; };
  chrome.contextMenus.removeAll(() => {
    void chrome.runtime.lastError;
    chrome.contextMenus.create({
      id: 'conv-auto',
      title: 'Convertir la sélection',
      contexts: ['selection'],
    }, ignoreErr);
    chrome.contextMenus.create({
      id: 'conv-he',
      title: 'Convertir en hébreu',
      contexts: ['selection'],
    }, ignoreErr);
    chrome.contextMenus.create({
      id: 'conv-fr',
      title: 'Convertir en latin',
      contexts: ['selection'],
    }, ignoreErr);
  });
}

chrome.runtime.onInstalled.addListener(createMenus);
chrome.runtime.onStartup.addListener(createMenus);

async function sendToTab(tabId, direction, frameId) {
  const stored = await chrome.storage.local.get('settings');
  const overrides = (direction === 'toHe' || direction === 'toFr')
    ? { mode: 'hebrew', direction }
    : { direction };
  const opts = Object.assign(
    { layout: 'azerty', mode: 'hebrew', direction: 'auto', latinDir: 'toAz' },
    stored.settings || {},
    overrides
  );
  const msg = { type: 'conv-selection', opts };
  const done = () => {
    // Onglet sans content script (chrome://, Web Store, PDF...) : rien a faire.
    void chrome.runtime.lastError;
  };
  if (typeof frameId === 'number') {
    chrome.tabs.sendMessage(tabId, msg, { frameId }, done);
  } else {
    chrome.tabs.sendMessage(tabId, msg, done);
  }
}

chrome.contextMenus.onClicked.addListener((info, tab) => {
  if (!tab || tab.id == null) return;
  const direction = DIRECTION_BY_MENU[info.menuItemId];
  if (!direction) return;
  sendToTab(tab.id, direction, info.frameId);
});

chrome.commands.onCommand.addListener((command, tab) => {
  if (command !== 'convert-selection') return;
  if (tab && tab.id != null) {
    sendToTab(tab.id, 'auto');
    return;
  }
  if (chrome.tabs && chrome.tabs.query) {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      void chrome.runtime.lastError;
      if (tabs && tabs[0] && tabs[0].id != null) {
        sendToTab(tabs[0].id, 'auto');
      }
    });
  }
});
