# EverNothing - Session Log

## Session: Full UI Redesign

### Changes Made

- **`STYLE` constant**: Complete rewrite with CSS variables (`--gold`, `--red`, `--bg`, etc.), sticky nav bar, card layouts, responsive grid, button classes (`.btn`, `.btn-primary`, `.btn-danger`, `.btn-sm`), item lists with hover-reveal actions, table styles, breadcrumb styles, confirm-box styles, mobile viewport meta tag
- **All templates redesigned**: `T_FOLDERS`, `T_ADD_FOLDER`, `T_ADD_SUBFOLDER`, `T_RENAME_FOLDER`, `T_CHANGE_PASSWORD`, `T_DELETE_NOTE`, `T_EDIT_CONFIRM`, `T_NOTES`, `T_ADD`, `T_EDIT`, `T_LOGIN`, `T_REGISTER`, `T_SEARCH`, `T_DELETE_FOLDER`, `T_HISTORY`, `T_ADMIN_LOGIN`, `T_ADMIN_DASHBOARD`, `T_ADMIN_EDIT_USER`, `T_ADMIN_EDIT_USER_CONFIRM`, `T_ADMIN_DELETE_USER`, `T_FORGOT_PASSWORD`, `T_RESET_PASSWORD`, `T_AUDIT_REPORT`, `T_SESSIONS`, `T_ADMIN_AUDIT_LOGS`
- **Inline rollback confirm**: Updated to match new style
- **Duplicate note fix**: Deleted duplicate `Bash Setup` row (id 84); hardened duplicate check in `add()` to use case-insensitive stripped comparison

### Key Design Decisions

- Sticky top nav bar on every page; logout always top-right in red
- Login/Register/Forgot/Reset: centered card layout (no nav)
- Home + Folder view: two-column responsive grid
- Hover-reveal action buttons on list items
- Confirm/delete pages use `.confirm-box` card style
- Color-coded audit action tags: green=CREATE, gold=UPDATE, red=DELETE
- CSS variables make theme changes trivial
- Mobile: grid collapses to single column at 600px

---

## Session: Module Refactor (IN PROGRESS)

### Goal
Split monolithic `evernothing.py` into 5 focused files:
1. `evernothing_db.py` — DB, encryption, utilities ✅ DONE
2. `evernothing_templates.py` — `STYLE` + all `T_*` constants ❌ TODO
3. `evernothing_routes.py` — all web + admin routes, `User` class, `load_user`, `sync_s3` ❌ TODO
4. `evernothing_api.py` — all `/api/*` JSON routes, `api_login_required` decorator ❌ TODO
5. `evernothing.py` — thin entry point: imports all modules, calls `init_db()`, `backup_database()`, runs app ❌ TODO

### Completed: `evernothing_db.py`
Contains: `encrypt()`/`decrypt()` (AES-GCM), `db()`, `init_db()`, `backup_database()`, `format_date()`, `get_breadcrumbs()`, `log_change()`, `delete_recursive()`, `validate_input()`, `validate_email()`, `validate_password()`, `allowed_file()`.
Uses `DB = os.environ.get('DB_FILE', 'evernothing.db')`.

### Key Refactor Decisions
- `evernothing.py` remains the single run target (Termux compatibility)
- `test_evernothing.py` imports `evernothing` — thin entry point must re-export all names tests depend on
- `/api/*` routes use `@csrf.exempt` + custom `api_login_required` (returns JSON 401, not redirect)
- `T_ADMIN_S3_BACKUPS` is currently defined AFTER `if __name__ == '__main__'` in original file — fix positioning during refactor
- `sync_s3()` belongs in `evernothing_routes.py` (uses boto3, called after every DB commit)
- `User` class and `load_user` belong in `evernothing_routes.py`
- Flask `app` object created in thin `evernothing.py`, passed to routes/api modules (or use blueprints)

### Names Tests Depend On (must be importable from `evernothing`)
`app`, `login_manager`, `db`, `encrypt`, `decrypt`, `init_db`, `sync_s3`, `rate_limiter` (module with `rate_limit_store`)

---

## Session: Description Field + Test Infrastructure

### Changes Made

- **`notes` and `note_history` tables**: Added `description TEXT` column (max 255 chars)
- **`init_db()`**: Added `ALTER TABLE notes/note_history ADD COLUMN description TEXT` migrations for existing DBs
- **`add()` route**: Reads `description` from form (capped at 255), inserts into both tables
- **`edit()` route**: Selects `description` as `note[4]`, includes in identical-check, UPDATE, history INSERT, confirm page
- **`export_json()`**: SELECT includes `n.description`, exported as `"description"` key
- **`T_ADD`**: Has `<input name=description maxlength="255">`
- **`T_EDIT`**: Has `<input name=description value='{{note[4]}}' maxlength="255">`
- **`T_EDIT_CONFIRM`**: Shows description, passes as hidden field, has CSRF token `<input type=hidden name=csrf_token value="{{ csrf_token() }}">`

### Test Infrastructure Fixes

- `setUp`: `notes` and `note_history` CREATE TABLE include `description TEXT` column
- `setUp`: Sets `evernothing.login_manager.session_protection = None` (prevents `validate_session` before_request from invalidating test logins)
- `tearDown`: Clears `rate_limit_store` from `rate_limiter` module; uses `except OSError`
- 6 description tests added (section 11b), all using `with sqlite3.connect(...) as con:` context managers
- `test_user_cannot_see_other_users_notes`: Asserts `b'No matches'` instead of `assertNotIn(b'PrivateNote')`

### Key Insights

- `T_EDIT_CONFIRM` form posts to `/edit/{{id}}` — must include CSRF token or Flask-WTF rejects with 400 Bad Request
- `validate_session` before_request checks `user_sessions` DB table — test logins don't insert rows there, so sessions get invalidated. Fix: `evernothing.login_manager.session_protection = None` in setUp
- Rate limiter uses module-level `rate_limit_store = defaultdict(list)` — persists across tests. Must call `rate_limit_store.clear()` in tearDown
- Search page echoes the query string in the form `value=` attribute — `assertNotIn(b'query')` will always fail. Use `assertIn(b'No matches')` for data isolation tests
- All sqlite3 connections in tests must use `with sqlite3.connect(...) as con:` context managers (CWE-400/664)
- flask-wtf must be installed in the same Python environment used to run tests
- Kivy 2.3.1 installed under Python 3.9.13 at `C:\Users\bills\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.9_qbz5n2kfra8p0\python.exe`

---

## Session: Android Login, On-Device Decryption, Startup Race & Sync Validation

### Context
Native Android app (`evernothing_android/android-app/`) is a Kotlin + Jetpack Compose
WebView host that runs the Flask app (`evernothing_android.py`) via Chaquopy embedded
Python. It replicates with the PC through a shared S3 bucket. Physical test device:
`ZD222TQWQH`. Admin creds: `admin`/`admin`.

### Changes Made (evernothing_android.py)

- **S3 bootstrap wired into `start_server()`**: previously only `__main__` called
  `_bootstrap_from_s3()`, which Android never runs (the foreground service enters via
  `start_server()`), so a fresh install never hydrated the PC DB. Now `start_server()`
  runs bootstrap, then `_ensure_admin_user()`.
- **Fixed `NameError` in `_bootstrap_from_s3()`**: referenced an undefined `con` in the
  user-count validation block, which silently aborted the restore. Reads the local count
  via its own connection now.
- **`_ensure_admin_user()`**: idempotent admin seed that runs AFTER bootstrap so it never
  blocks the empty-DB hydrate trigger (old import-time seed poisoned bootstrap by making
  the DB non-empty).
- **Optional `flask_wtf`**: Chaquopy has no wheel; import now falls back to a no-op
  CSRFProtect shim (CSRF is disabled on the loopback server anyway).
- **`_resolve_db_path()`**: relative `evernothing.db` was unopenable under Chaquopy's
  non-writable CWD. Resolves to the app files dir via `$HOME` / known Android path.
- **On-device decryption via Kotlin bridge**: `cryptography` has no arm64 Chaquopy wheel,
  so `_decrypt()` silently returned ciphertext and the whole UI showed base64 blobs.
  `_encrypt`/`_decrypt` now fall back to the Kotlin AES-GCM bridge (`_aes.py` ->
  `AesGcmBridge.kt`) when `cryptography` is absent. Same PBKDF2-SHA256 derivation
  (salt `evernothing-aes-key-v1`, 100k iters, 32 bytes) and `nonce||ct||tag` wire format
  as the PC, so PC-encrypted notes round-trip. Logs `crypto backend: kotlin-bridge`.
- **Register password minimum** lowered 8 -> 4 chars (per explicit test-user requirement
  `test99`/`test99`).
- **`ADMIN_USER`/`ADMIN_PASS`** config support added to `config_loader.py` + `config.ini`.

### Changes Made (MainActivity.kt) — startup race fix
- WebView loaded `http://127.0.0.1:5000` before the server finished its ~20-40s cold-start
  bootstrap -> dead-end "Cannot reach Evernothing" screen. Added auto-retry: on main-frame
  load error, reload every 2s for up to 20 attempts (~40s grace) before showing the error
  screen. `onLoaded` (clean `onPageFinished`) resets the budget; a `mainFrameFailed` flag
  avoids mistaking WebView's internal error page for a successful load.

### Verified on device ZD222TQWQH
- Fresh install bootstraps current PC DB from S3; `admin`/`admin` login, logout,
  register `test99`, create `folder99`, create note `title99`/`contents99` — all pass.
- Decryption confirmed: folder names (`Bank`, `Git`, ...) and note bodies render as
  plaintext, not base64.
- Startup-race fix confirmed in logcat: WebView start 16:48:57 -> server bound :5000 at
  16:49:10; app rode through the gap and loaded with no error screen (uiautomator dump:
  error screen absent, WebView present).

### S3 / data operations
- `bspeiser` password set to `Password123!` (hash updated in PC DB, re-uploaded to S3
  keys `evernothing.db` + `android/evernothing.db`).
- Ran `Scripts/migrate_encrypt.py`: encrypted 5 remaining plaintext notes + 2 folders;
  re-uploaded fully-encrypted DB to S3.

### Sync validation test (NEW: Test/test_tethered_untethered_sync.py)
- "Tethered" = PC<->phone full-DB transfer over USB/ADB. "Un-tethered" = independent
  S3 cloud delta replication with LWW convergence. (Terms are architectural; not literal
  strings in the repo.)
- 7 tests driving the REAL PC (`Evernothing_Connect`) and Android (`evernothing_android`)
  publish/pull/apply code through an in-memory fake S3 (no AWS). Covers both directions,
  concurrent-edit LWW convergence, DELETE propagation, and full-DB transfer + integrity.
- Full sync regression: 15 (test_s3_pull) + 23 (test_android replication) + 7 (new) = all pass.

### Git
- Android repo on branch `alpha` (pushed to origin earlier this session). Commits:
  `11abf65` (Alpha: login/bootstrap/decryption fixes) + `6047f09` (startup-race fix).
- PC repo on `main`: commit `955d3f8` (sync validation test).

### Key Insights
- Android native app never executes `__main__`; one-time startup work must live in
  `start_server()`.
- Seeding users at import time poisons the empty-DB S3 bootstrap trigger — seed AFTER
  bootstrap and make it idempotent.
- Chaquopy lacks arm64 wheels for `cryptography` and `flask_wtf`; both must degrade
  gracefully (Kotlin AES bridge; no-op CSRF shim).
- PC `queue_change` reads rows back with `dict(row)` — test connections must set
  `con.row_factory = sqlite3.Row` or the payload serializes empty.
- USB/ADB to ZD222TQWQH is flaky; large (~77-110MB) APK installs often drop mid-stream
  and need retries. No WiFi on the device, so wireless adb wasn't an option.
