// Service worker : menu clic droit + raccourci clavier. La conversion
// elle-meme est faite par content.js (page active), jamais ici.
'use strict';

const DIRECTION_BY_MENU = {
  'conv-auto': 'auto',
  'conv-he': 'toHe',
  'conv-fr': 'toFr',
};

function createMenus() {
  chrome.contextMenus.removeAll(() => {
    chrome.contextMenus.create({
      id: 'conv-auto',
      title: 'Convertir la sélection',
      contexts: ['selection'],
    });
    chrome.contextMenus.create({
      id: 'conv-he',
      title: 'Convertir en hébreu',
      contexts: ['selection'],
    });
    chrome.contextMenus.create({
      id: 'conv-fr',
      title: 'Convertir en latin',
      contexts: ['selection'],
    });
  });
}

chrome.runtime.onInstalled.addListener(createMenus);
chrome.runtime.onStartup.addListener(createMenus);

async function sendToTab(tabId, direction) {
  const stored = await chrome.storage.local.get('settings');
  const opts = Object.assign(
    { layout: 'azerty', mode: 'hebrew', direction: 'auto', latinDir: 'toAz' },
    stored.settings || {},
    { direction }
  );
  chrome.tabs.sendMessage(tabId, { type: 'conv-selection', opts }, () => {
    // Onglet sans content script (chrome://, Web Store, PDF...) : rien a faire.
    void chrome.runtime.lastError;
  });
}

chrome.contextMenus.onClicked.addListener((info, tab) => {
  if (!tab || tab.id == null) return;
  const direction = DIRECTION_BY_MENU[info.menuItemId];
  if (!direction) return;
  sendToTab(tab.id, direction);
});

chrome.commands.onCommand.addListener((command, tab) => {
  if (command !== 'convert-selection' || !tab || tab.id == null) return;
  sendToTab(tab.id, 'auto');
});
