/**
 * preload.js — Electron Preload Script
 * Runs in the renderer context before page scripts.
 * Exposes only what the renderer needs via contextBridge.
 */
const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
    // Renderer can request the server base URL
    getBaseUrl: () => 'http://127.0.0.1:5000',
});
