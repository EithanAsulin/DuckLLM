const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  checkDependencies: () => ipcRenderer.invoke('check-dependencies'),
  installOllama: (mode) => ipcRenderer.invoke('install-ollama', mode),
  getOllamaModels: () => ipcRenderer.invoke('get-ollama-models'),
  createModel: (type) => ipcRenderer.invoke('create-model', type),
  uninstallApp: (models) => ipcRenderer.invoke('uninstall-app', models),
  launchApp: () => ipcRenderer.send('launch-app'),
  closeApp: () => ipcRenderer.send('close-app'),
  onProgress: (callback) => ipcRenderer.on('setup-progress', (event, value) => callback(value)),
});
