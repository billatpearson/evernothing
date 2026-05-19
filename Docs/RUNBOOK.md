# EverNothing Runbook

Operational procedures for day-to-day running, maintenance, and recovery of
EverNothing. For first-time install see [`INSTALL.md`](INSTALL.md).

Paths below assume the app root is `C:\source\ai\evernothing\evernothing`.

---

## Contents

1. [Start the server](#start-the-server)
2. [Stop the server](#stop-the-server)
3. [Run the test suite](#run-the-test-suite)
4. [Back up the database](#back-up-the-database)
5. [Restore from a backup](#restore-from-a-backup)
6. [Rotate `SECRET_KEY` and re-encrypt data](#rotate-secret_key-and-re-encrypt-data)
7. [Encrypt plaintext rows (migration)](#encrypt-plaintext-rows-migration)
8. [Configure S3 sync](#configure-s3-sync)
9. [Run the Android app (Termux)](#run-the-android-app-termux)
10. [Run the SMS receive service](#run-the-sms-receive-service)
11. [Troubleshooting](#troubleshooting)

---

## Start the server

Preferred path — runs the full test suite first, then relaunches:

```cmd
Startup\test_and_restart.bat
```

What it does:

- Kills the process tracked by `server.pid`, plus any orphan listeners on
  ports 5000 and 5443.
- Runs `pytest` against the `Test/` and `tests/` directories.
- Relaunches `python evernothing.py` detached (stdout → `log\server.log`,
  stderr → `log\server_err.log`).
- Writes the new PID to `server.pid`.

Port selection is automatic:

| Condition | Port | URL |
|---|---|---|
| `Startup\cert.pem` **and** `Startup\key.pem` exist | 5443 | `https://127.0.0.1:5443` |
| Either cert file missing | 5000 | `http://127.0.0.1:5000` |

Note: `SESSION_COOKIE_SECURE=true` in `.env` requires HTTPS. If you run on
port 5000 with that setting on, login will silently fail because the session
cookie will not be sent back.

For a quick foreground launch (no tests, no detachment):

```cmd
python main.py
```

---

## Stop the server

```cmd
for /f %p in (server.pid) do taskkill /F /PID %p
del server.pid
```

Or kill whatever is on the port:

```cmd
for /f "tokens=5" %p in ('netstat -ano ^| findstr ":5443 " ^| findstr LISTENING') do taskkill /F /PID %p
```

---

## Run the test suite

Full suite used by `test_and_restart.bat`:

```cmd
python -m pytest Test\ tests\ -v --tb=short
```

Focused runs:

```cmd
python -m pytest Test\test_security.py -v
python -m pytest tests\test_s3_sync.py -v
python -m pytest Test\test_themes.py -v
```

Android module tests live in the sibling repo:

```cmd
cd ..\evernothing_android
python -m pytest test_android.py -v
```

---

## Back up the database

Backups are automatic. On every startup `main.py` calls
`backup_database()` and `compress_old_backups()` from
`Evernothing_DB/database.py`. Output lands in `DB\Backups\`.

Manual on-demand backup:

```cmd
copy DB\evernothing.db DB\Backups\evernothing_manual_%date:~-4%%date:~4,2%%date:~7,2%.db
```

The `Scripts\migrate_encrypt.py` helper also writes a
`DB\evernothing.db.premigration_YYYYMMDD_HHMMSS.bak` next to the live DB
before it touches any rows.

---

## Restore from a backup

1. Stop the server (see above).
2. Confirm which backup you want — `dir DB\Backups\`.
3. Swap the file:

```cmd
copy DB\evernothing.db DB\evernothing.db.bad
copy DB\Backups\evernothing_YYYYMMDD_HHMMSS.db DB\evernothing.db
```

4. Restart with `Startup\test_and_restart.bat`.

The restored DB must have been encrypted with the current `SECRET_KEY`. If
you are restoring across a key rotation, either restore the matching
`.env` too or re-run the re-encryption flow below.

---

## Rotate `SECRET_KEY` and re-encrypt data

`SECRET_KEY` is the PBKDF2 input for the AES-256-GCM data key. Changing it
without re-encrypting will render every note, folder name, and history
entry unreadable.

Safe rotation:

1. Stop the server.
2. Take a manual backup of `DB\evernothing.db` (see above).
3. Generate a new key:

   ```cmd
   python -c "import secrets; print(secrets.token_hex(32))"
   ```

4. Decrypt everything with the **old** key and re-encrypt with the **new**
   key in a single script. The pattern used during the May 2026 rotation:

   - Load old `SECRET_KEY` from `.env`.
   - Iterate `notes`, `folders`, `note_history` — `decrypt(row)` each
     encrypted column.
   - Update `.env` with the new `SECRET_KEY`.
   - Reload the crypto module so it picks up the new key.
   - Iterate again and `encrypt(row)` each value, writing back.
   - Commit in a single transaction.

5. Restart and smoke-test: log in, open a note, check the history pane.

If anything fails, restore the pre-rotation backup and the old `.env`.
Never overwrite the old `.env` until the re-encrypt step succeeds.

---

## Encrypt plaintext rows (migration)

Use when the mixed-encryption banner appears, or the first time you flip
`ENCRYPTION_ENABLED=true`:

```cmd
python Scripts\migrate_encrypt.py
```

Behaviour:

- Refuses to run unless `ENCRYPTION_ENABLED=true`.
- Writes a `.premigration_*.bak` alongside `DB\evernothing.db`.
- Skips rows that are already AES-GCM ciphertext (safe to re-run).
- Encrypts `notes`, `folders`, and `note_history`.
- Rolls back on any error; on success prints `Migration complete`.

---

## Configure S3 sync

S3 settings live in `.env`:

```
S3_BUCKET_NAME=your-bucket
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
# or
AWS_PROFILE=your-cli-profile
```

Verification:

```cmd
python Scripts\s3_inspector.py
python Scripts\s3_content_viewer.py
```

First-time bucket bootstrap:

```cmd
python Scripts\setup_aws_s3.py
```

The server is resilient to S3 failure. If `restore_from_s3()` or a sync
call fails, the UI shows an "S3 sync unavailable" banner and the app
continues against the local SQLite DB. See
[`AWS_S3_SETUP_GUIDE.md`](AWS_S3_SETUP_GUIDE.md) for IAM and bucket-policy
detail.

---

## Run the Android app (Termux)

The Android build lives in the sibling repo at
`C:\source\ai\evernothing\evernothing_android`. On the device:

```bash
pkg install python git
pip install flask flask-login werkzeug boto3 cryptography itsdangerous pyjwt
git clone https://github.com/billatpearson/evernothing_android
cd evernothing_android
python main.py
```

Open `http://127.0.0.1:5000` in the phone browser. The Android app
checkpoints its local DB to S3 on an interval when credentials are
configured in its own `.env`.

---

## Run the SMS receive service

The SMS service is a standalone Flask app at
`C:\source\ai\evernothing\sms_service\` that receives inbound SMS via
Twilio + ngrok.

One-time setup:

1. Sign up at twilio.com (trial, no card required).
2. Put credentials in `sms_service\.env` — copy from `.env.example`.
3. Ensure `sms_service\ngrok.exe` is present (already bundled).

Run:

```cmd
cd ..\sms_service
start_with_tunnel.bat
```

That script starts Flask and ngrok, prints the public HTTPS URL, and
tails the log. Paste the `https://<random>.ngrok-free.app/sms` URL into
the Twilio phone-number webhook and send a test SMS to the configured
number (+1 602 769 4235 for this account).

Tests:

```cmd
cd ..\sms_service
python -m pytest test_sms.py -v
```

See `sms_service\README.md` for the full interface and test matrix.

---

## Troubleshooting

### Encryption health check

To audit every encrypted column for rows that look like ciphertext but
won't decrypt under the current `SECRET_KEY`:

```cmd
python Scripts\encryption_health_scan.py
```

Reports counts per table (`notes`, `folders`, `note_history`) and lists
any cell flagged `plaintext`, `bad-decrypt`, or `double-wrap`. Exit code
is non-zero if `bad-decrypt` or `double-wrap` rows exist.

`bad-decrypt` rows are typically history snapshots that were written
under an older `SECRET_KEY` and not re-encrypted during a key rotation.
They cannot be recovered without the old key.

`double-wrap` is a rotation-time bug where ciphertext got treated as
plaintext and re-wrapped. Newly-detected double-wrap rows mean the
rotation script didn't preserve the original ciphertext correctly.



### Mixed-encryption banner on dashboard

Some rows were written before encryption was enabled. Run:

```cmd
python Scripts\migrate_encrypt.py
```

### All notes show as ciphertext after a restart

The current `SECRET_KEY` no longer matches the one the data was
encrypted with. Either restore the matching `.env`, or restore a backup
from before the key change and re-run the rotation procedure.

### `ERR_SSL_PROTOCOL_ERROR` hitting `https://127.0.0.1:5443`

Either the cert files are missing, or the browser is hitting the HTTPS
URL while the server fell back to port 5000. Check
`log\server.log` for the actual `Running on ...` line.

### `ERR_CONNECTION_REFUSED`

The server didn't start. Check `log\server_err.log`. Most common cause:
port 5443/5000 already held by a dead python.exe that
`test_and_restart.bat` didn't catch. Kill it with:

```cmd
for /f "tokens=5" %p in ('netstat -ano ^| findstr ":5443 " ^| findstr LISTENING') do taskkill /F /PID %p
```

### `[FAILED] Main app tests failed. Server NOT restarted.`

`test_and_restart.bat` will not launch the server when tests are red.
Run the failing module directly to see the traceback:

```cmd
python -m pytest Test\test_security.py -v --tb=long
```

### S3 sync banner stays up

S3 credentials or bucket policy are wrong. Verify with:

```cmd
python Scripts\s3_inspector.py
```

Then check the last few lines of `log\server.log` for the boto3 error
message — it is usually an `AccessDenied` or `NoSuchBucket`.

### Login rate-limited

The security module throttles repeated failed logins per IP. Wait out
the window or restart the server to clear the in-memory counter.

### Port already in use after a crash

```cmd
netstat -ano | findstr ":5443 "
taskkill /F /PID <pid>
del server.pid
```

---

## Related documents

- [`INSTALL.md`](INSTALL.md) — first-time setup
- [`AWS_S3_SETUP_GUIDE.md`](AWS_S3_SETUP_GUIDE.md) — bucket + IAM detail
- [`SESSION_MANAGEMENT.md`](SESSION_MANAGEMENT.md) — cookie/session policy
- [`RECOMMENDATIONS.md`](RECOMMENDATIONS.md) — hardening backlog
