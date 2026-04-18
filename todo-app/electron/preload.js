const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  getAllIPs: () => ipcRenderer.invoke('get-all-ips'),
  copyToClipboard: (text) => ipcRenderer.invoke('copy-to-clipboard', text)
});
