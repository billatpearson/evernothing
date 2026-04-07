# EverNothing Desktop App

Downloadable desktop application for Windows, macOS, and Linux.
Wraps the EverNothing Flask server in a native Electron window —
no browser required, one double-click to launch.

## Prerequisites

- **Node.js 18+**: https://nodejs.org
- **Python 3.8+**: https://python.org
- Python packages: `pip install flask flask-login werkzeug boto3 cryptography itsdangerous flask-wtf python-dotenv`

## Quick Start (Development)

```bash
cd desktop
npm install
npm start
```

## Build Installers

```bash
cd desktop
npm install

# Windows (.exe installer)
npm run build:win

# macOS (.dmg)
npm run build:mac

# Linux (.AppImage)
npm run build:linux

# All platforms
npm run build:all
```

Installers are output to `desktop/dist/`.

## What Gets Bundled

The build copies these files from the parent directory into the installer:

| File | Purpose |
|---|---|
| `evernothing.py` | Main Flask application |
| `evernothing_config.py` | Configuration |
| `evernothing_db.py` | Database layer |
| `evernothing_security.py` | Encryption & auth |
| `evernothing_logic.py` | S3 sync & business logic |
| `evernothing_templates.py` | HTML templates |
| `rate_limiter.py` | Rate limiting |
| `email_utils.py` | Password reset emails |

## Data Storage

All user data is stored in the OS user data directory:

| Platform | Path |
|---|---|
| Windows | `%APPDATA%\evernothing\` |
| macOS | `~/Library/Application Support/evernothing/` |
| Linux | `~/.config/evernothing/` |

Files stored there:
- `evernothing.db` — SQLite database
- `secret.key` — AES-256 encryption key
- `server.log` — Flask server log

## Adding App Icons

Place icon files in `desktop/assets/`:
- `icon.ico` — Windows (256x256)
- `icon.icns` — macOS
- `icon.png` — Linux + splash screen (512x512)
- `icon-tray.png` — System tray (16x16 or 32x32)

## Architecture

```
EverNothing Desktop
├── Electron (main.js)          ← Native window, menu, tray
│   ├── Spawns Python process   ← Flask server on localhost:5000
│   ├── Polls until ready       ← HTTP check on /login
│   └── BrowserWindow           ← Loads http://127.0.0.1:5000
└── Flask (evernothing.py)      ← Full web app, unchanged
    ├── SQLite DB               ← Stored in user data dir
    └── S3 sync                 ← Encrypted backups to AWS
```

## Troubleshooting

**"Python Not Found"**: Install Python 3.8+ and ensure it's on your PATH.

**Server doesn't start**: Open the log via menu → EverNothing → Open Log.

**Port 5000 in use**: Another process is using port 5000. Stop it or change
`PORT` in `main.js`.

**Windows Defender warning**: The installer is unsigned. Click "More info" →
"Run anyway". To remove the warning, sign the installer with a code signing
certificate.
