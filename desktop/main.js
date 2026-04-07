/**
 * EverNothing Desktop — Electron Main Process
 *
 * Spawns the bundled Python/Flask server as a child process,
 * waits for it to be ready, then opens it in a native BrowserWindow.
 * On quit, the Flask process is cleanly terminated.
 */

const { app, BrowserWindow, shell, Menu, Tray, dialog, nativeImage } = require('electron');
const { spawn, execSync }  = require('child_process');
const path   = require('path');
const http   = require('http');
const fs     = require('fs');

// ── Configuration ─────────────────────────────────────────────────────────────
const PORT        = 5000;
const HOST        = '127.0.0.1';
const BASE_URL    = `http://${HOST}:${PORT}`;
const READY_POLL  = 300;   // ms between readiness checks
const READY_TRIES = 40;    // max attempts (~12 seconds)

// ── Paths ─────────────────────────────────────────────────────────────────────
const IS_PACKAGED  = app.isPackaged;
const RESOURCES    = IS_PACKAGED ? process.resourcesPath : path.join(__dirname, '..');
const APP_DIR      = IS_PACKAGED ? path.join(RESOURCES, 'app') : RESOURCES;
const DATA_DIR     = path.join(app.getPath('userData'), 'evernothing');
const DB_PATH      = path.join(DATA_DIR, 'evernothing.db');
const KEY_PATH     = path.join(DATA_DIR, 'secret.key');
const LOG_PATH     = path.join(DATA_DIR, 'server.log');
const ENTRY_SCRIPT = path.join(APP_DIR, 'evernothing.py');

// ── Globals ───────────────────────────────────────────────────────────────────
let mainWindow  = null;
let tray        = null;
let flaskProc   = null;
let serverReady = false;

// ── Ensure data directory ─────────────────────────────────────────────────────
if (!fs.existsSync(DATA_DIR)) fs.mkdirSync(DATA_DIR, { recursive: true });

// ── Find Python ───────────────────────────────────────────────────────────────
function findPython() {
    const candidates = process.platform === 'win32'
        ? ['python', 'python3', 'py']
        : ['python3', 'python'];
    for (const cmd of candidates) {
        try {
            const out = execSync(`${cmd} --version 2>&1`).toString();
            if (out.match(/Python 3\./)) return cmd;
        } catch (_) {}
    }
    return null;
}

// ── Start Flask server ────────────────────────────────────────────────────────
function startFlask() {
    const python = findPython();
    if (!python) {
        dialog.showErrorBox('Python Not Found',
            'Python 3 is required but was not found.\n\n' +
            'Please install Python 3.8+ from https://python.org and try again.');
        app.quit();
        return;
    }

    const env = Object.assign({}, process.env, {
        DB_FILE:        DB_PATH,
        SECRET_KEY_FILE: KEY_PATH,
        FLASK_ENV:      'production',
        PYTHONUNBUFFERED: '1',
    });

    const logStream = fs.createWriteStream(LOG_PATH, { flags: 'a' });
    logStream.write(`\n--- EverNothing started ${new Date().toISOString()} ---\n`);

    flaskProc = spawn(python, [ENTRY_SCRIPT], { cwd: APP_DIR, env });
    flaskProc.stdout.pipe(logStream);
    flaskProc.stderr.pipe(logStream);

    flaskProc.on('error', err => {
        dialog.showErrorBox('Server Error', `Failed to start Flask server:\n${err.message}`);
        app.quit();
    });

    flaskProc.on('exit', (code) => {
        if (code !== 0 && mainWindow) {
            mainWindow.webContents.loadFile(path.join(__dirname, 'splash.html'),
                { query: { error: `Server exited with code ${code}. Check ${LOG_PATH}` } });
        }
    });
}

// ── Poll until Flask is ready ─────────────────────────────────────────────────
function waitForFlask(tries, resolve, reject) {
    http.get(BASE_URL + '/login', res => {
        serverReady = true;
        resolve();
    }).on('error', () => {
        if (tries <= 0) return reject(new Error('Flask server did not start in time'));
        setTimeout(() => waitForFlask(tries - 1, resolve, reject), READY_POLL);
    });
}

// ── Create main window ────────────────────────────────────────────────────────
function createWindow() {
    mainWindow = new BrowserWindow({
        width:  1280,
        height: 860,
        minWidth:  800,
        minHeight: 600,
        title: 'EverNothing',
        icon: path.join(__dirname, 'assets', 'icon.png'),
        webPreferences: {
            preload:          path.join(__dirname, 'preload.js'),
            contextIsolation: true,
            nodeIntegration:  false,
        },
        show: false,   // shown after server is ready
        backgroundColor: '#1a0a2e',
    });

    // Show splash while server starts
    mainWindow.loadFile(path.join(__dirname, 'splash.html'));
    mainWindow.show();

    // Open external links in the system browser, not Electron
    mainWindow.webContents.setWindowOpenHandler(({ url }) => {
        if (!url.startsWith(BASE_URL)) shell.openExternal(url);
        return { action: 'deny' };
    });

    // Build application menu
    const menu = Menu.buildFromTemplate([
        {
            label: 'EverNothing',
            submenu: [
                { label: 'Home',     click: () => mainWindow.loadURL(BASE_URL) },
                { label: 'Search',   click: () => mainWindow.loadURL(BASE_URL + '/search') },
                { type: 'separator' },
                { label: 'Reload',   role: 'reload' },
                { type: 'separator' },
                { label: 'Open Log', click: () => shell.openPath(LOG_PATH) },
                { label: 'Data Folder', click: () => shell.openPath(DATA_DIR) },
                { type: 'separator' },
                { label: 'Quit',     role: 'quit' },
            ]
        },
        {
            label: 'View',
            submenu: [
                { role: 'zoomIn' }, { role: 'zoomOut' }, { role: 'resetZoom' },
                { type: 'separator' },
                { role: 'togglefullscreen' },
                { role: 'toggleDevTools' },
            ]
        },
        {
            label: 'Account',
            submenu: [
                { label: 'Change Password', click: () => mainWindow.loadURL(BASE_URL + '/change_password') },
                { label: 'Sessions',        click: () => mainWindow.loadURL(BASE_URL + '/sessions') },
                { label: 'Audit Log',       click: () => mainWindow.loadURL(BASE_URL + '/audit_report') },
                { label: 'Export Notes',    click: () => mainWindow.loadURL(BASE_URL + '/export') },
                { type: 'separator' },
                { label: 'Logout',          click: () => mainWindow.loadURL(BASE_URL + '/logout') },
            ]
        }
    ]);
    Menu.setApplicationMenu(menu);

    // Wait for Flask then navigate
    new Promise((resolve, reject) => waitForFlask(READY_TRIES, resolve, reject))
        .then(() => mainWindow.loadURL(BASE_URL))
        .catch(err => {
            mainWindow.webContents.loadFile(path.join(__dirname, 'splash.html'),
                { query: { error: err.message + `\n\nCheck log: ${LOG_PATH}` } });
        });
}

// ── System tray ───────────────────────────────────────────────────────────────
function createTray() {
    const iconPath = path.join(__dirname, 'assets', 'icon-tray.png');
    if (!fs.existsSync(iconPath)) return;
    tray = new Tray(nativeImage.createFromPath(iconPath));
    tray.setToolTip('EverNothing');
    tray.setContextMenu(Menu.buildFromTemplate([
        { label: 'Open',  click: () => { mainWindow.show(); mainWindow.focus(); } },
        { label: 'Quit',  click: () => app.quit() },
    ]));
    tray.on('double-click', () => { mainWindow.show(); mainWindow.focus(); });
}

// ── App lifecycle ─────────────────────────────────────────────────────────────
app.whenReady().then(() => {
    startFlask();
    createWindow();
    createTray();

    app.on('activate', () => {
        if (BrowserWindow.getAllWindows().length === 0) createWindow();
    });
});

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') app.quit();
});

app.on('before-quit', () => {
    if (flaskProc) {
        flaskProc.kill();
        flaskProc = null;
    }
});
