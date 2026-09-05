# (Full single-file EverNothing application with all prompt instructions included as comments)
# see evernothing initscripts.txt  ---------------------------------------------------------


try:
    import os as _os
    from dotenv import load_dotenv
    load_dotenv(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '.env'))
except ImportError:
    pass

from flask import Flask, request, redirect, render_template_string, make_response, session
from flask_wtf.csrf import CSRFProtect, CSRFError
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer
from datetime import timezone
import sqlite3, datetime, json, os, base64, shutil, logging, re
try:
    import boto3
except ImportError:
    boto3 = None
try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
except ImportError:
    AESGCM = None
try:
    from aws_config import S3_BUCKET_NAME, AWS_REGION, AWS_PROFILE
except ImportError:
    S3_BUCKET_NAME = os.environ.get('S3_BUCKET_NAME', 'evernothing-backup-2026')
    AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')
    AWS_PROFILE = os.environ.get('AWS_PROFILE', 'billspeiser2')
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
KMS_KEY_ID = os.environ.get('KMS_KEY_ID')

# Configure logging
os.makedirs('log', exist_ok=True)
logging.basicConfig(
    filename='log/evernothing.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask("EverNothing")
_secret_key = os.environ.get('SECRET_KEY', '')
if not _secret_key:
    import secrets
    _secret_key = secrets.token_hex(32)
    logger.warning("SECRET_KEY not set — using a random key. Sessions will not persist across restarts.")
app.secret_key = _secret_key
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['WTF_CSRF_ENABLED'] = True
csrf = CSRFProtect(app)


# CSRF token expiry / invalid token handler:
# Flask-WTF raises CSRFError for missing-or-stale tokens. By default this
# returns a 400 page. Instead, log out any current session and redirect to
# /login?csrf=1 so the user sees "Your session has expired."
@app.errorhandler(CSRFError)
def _handle_csrf_error(e):
    try:
        logout_user()
    except Exception:
        pass
    session.clear()
    return redirect('/login?csrf=1')
_remember_days = int(os.environ.get('REMEMBER_COOKIE_DAYS', '30'))
app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(days=_remember_days)
app.config['REMEMBER_COOKIE_DURATION'] = datetime.timedelta(days=_remember_days)
app.config['SESSION_COOKIE_SECURE'] = os.environ.get('SESSION_COOKIE_SECURE', 'true').lower() == 'true'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['REMEMBER_COOKIE_SECURE'] = os.environ.get('SESSION_COOKIE_SECURE', 'true').lower() == 'true'
app.config['REMEMBER_COOKIE_HTTPONLY'] = True
app.config['REMEMBER_COOKIE_SAMESITE'] = 'Lax'
app.config['REMEMBER_COOKIE_NAME'] = 'remember_token'
# DB path: always use DB/evernothing.db relative to this file's directory.
# DB_FILE env var overrides for tests and custom deployments.
_db_default = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'DB', 'evernothing.db')
DB = os.environ.get('DB_FILE', _db_default)
BUILD_DATE = datetime.datetime.now().strftime("%m/%d/%y:%H:%M")

@app.before_request
def enforce_https():
    """Redirect all plain HTTP requests to HTTPS."""
    # Skip in testing/debug mode so unit tests still work over HTTP
    if app.config.get('TESTING') or app.debug:
        return
    # Skip if the app itself is not running with SSL (no cert configured)
    # — redirecting to https:// when the server only speaks HTTP causes ERR_SSL_PROTOCOL_ERROR
    ssl_cert = os.environ.get('SSL_CERT', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Startup', 'cert.pem'))
    ssl_key  = os.environ.get('SSL_KEY',  os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Startup', 'key.pem'))
    if not (os.path.exists(ssl_cert) and os.path.exists(ssl_key)):
        return
    if request.is_secure:
        return
    # Honour reverse-proxy header (e.g. nginx / AWS ALB)
    if request.headers.get('X-Forwarded-Proto', 'http') == 'https':
        return
    url = request.url.replace('http://', 'https://', 1)
    return redirect(url, code=301)

@app.context_processor
def inject_build_date():
    return dict(build_date=BUILD_DATE)

@app.after_request
def set_security_headers(response):
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "img-src 'self' data:;"
    )
    return response
ENCRYPTION_ENABLED = os.environ.get('ENCRYPTION_ENABLED', 'true').lower() == 'true'
if AESGCM:
    # Derive the AES-256 key from SECRET_KEY using PBKDF2-SHA256.
    # This eliminates the separate secret.key file — the DB can only be
    # decrypted by someone who knows SECRET_KEY, even if they have the DB file.
    import hashlib
    KEY = hashlib.pbkdf2_hmac(
        'sha256',
        _secret_key.encode('utf-8'),
        b'evernothing-aes-key-v1',  # fixed app-specific salt
        iterations=100_000,
        dklen=32
    )
    aesgcm = AESGCM(KEY)

    def encrypt(txt):
        if not ENCRYPTION_ENABLED or not txt: return txt if txt else ""
        try:
            nonce = os.urandom(12)
            return base64.b64encode(nonce + aesgcm.encrypt(nonce, txt.encode('utf-8'), None)).decode('utf-8')
        except Exception as e:
            print(f"Enc Error: {e}")
            return txt

    def decrypt(txt):
        if not txt: return ""
        try:
            data = base64.b64decode(txt)
            return aesgcm.decrypt(data[:12], data[12:], None).decode('utf-8')
        except Exception:
            return txt
else:
    def encrypt(t): return t
    def decrypt(t): return t

login_manager = LoginManager(app)
login_manager.login_view = "login"
# 'strong' rotates the session id when remote_addr or user_agent changes
# coarsely. 'basic' was a meaningful gap.
login_manager.session_protection = "strong"

# One-time boot-time warning if admin creds are still defaults.
try:
    from Evernothing_Security.admin_auth import log_admin_security_warnings
    log_admin_security_warnings(logger)
except Exception:
    pass

# Session validation
@app.before_request
def validate_session():
    if current_user.is_authenticated:
        # Empty session = user restored via remember-me cookie after browser restart
        if not session:
            return

        remember_me = session.get('remember_me', False)

        if not remember_me:
            session.permanent = True
            if 'last_activity' in session:
                last_activity = datetime.datetime.fromisoformat(session['last_activity'])
                timeout_hours = int(os.environ.get('SESSION_TIMEOUT_HOURS', '2'))
                if datetime.datetime.now(timezone.utc) - last_activity > datetime.timedelta(hours=timeout_hours):
                    logout_user()
                    session.clear()
                    return redirect('/login?timeout=1')
            session['last_activity'] = datetime.datetime.now(timezone.utc).isoformat()

        if 'session_id' in session:
            con = db()
            cur = con.cursor()
            valid = cur.execute(
                "SELECT id FROM user_sessions WHERE session_id=? AND user_id=? AND logout_time IS NULL",
                (session['session_id'], current_user.id)
            ).fetchone()
            con.close()
            if not valid:
                logout_user()
                session.clear()
                return redirect('/login?invalid=1')

# --- DATABASE ---
def db():
    con = sqlite3.connect(DB, check_same_thread=False, timeout=10)
    con.row_factory = sqlite3.Row
    return con
def init_db():
    c = db(); cur = c.cursor()
    cur.executescript("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        last_login TEXT,
        email TEXT
    );
    CREATE TABLE IF NOT EXISTS folders(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        name TEXT,
        parent_id INTEGER
    );
    CREATE TABLE IF NOT EXISTS notes(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        folder_id INTEGER,
        note_key TEXT,
        note_value TEXT,
        description TEXT,
        updated_at TEXT
    );
    CREATE TABLE IF NOT EXISTS note_history(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        note_id INTEGER,
        user_id INTEGER,
        note_key TEXT,
        note_value TEXT,
        description TEXT,
        folder_id INTEGER,
        updated_at TEXT
    );
    CREATE TABLE IF NOT EXISTS user_sessions(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        session_id TEXT,
        login_time TEXT,
        logout_time TEXT,
        ip_address TEXT,
        user_agent TEXT
    );
    CREATE TABLE IF NOT EXISTS attachments(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        note_id INTEGER,
        user_id INTEGER,
        filename TEXT,
        file_data BLOB,
        file_size INTEGER,
        uploaded_at TEXT
    );
    CREATE TABLE IF NOT EXISTS audit_log(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        action TEXT,
        entity_type TEXT,
        entity_id INTEGER,
        old_values TEXT,
        new_values TEXT,
        timestamp TEXT,
        ip_address TEXT
    );
    CREATE TABLE IF NOT EXISTS sync_queue(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        entity_type TEXT,
        entity_id INTEGER,
        operation TEXT,
        payload TEXT,
        changed_at TEXT,
        synced_at TEXT
    );
    CREATE TABLE IF NOT EXISTS replication_cursor(
        peer_device TEXT PRIMARY KEY,
        last_key    TEXT NOT NULL,
        updated_at  TEXT NOT NULL
    );
    """)
    for _col_sql in [
        "ALTER TABLE notes ADD COLUMN description TEXT",
        "ALTER TABLE note_history ADD COLUMN description TEXT",
    ]:
        try:
            cur.execute(_col_sql)
        except sqlite3.OperationalError:
            pass
    try: 
        cur.execute("ALTER TABLE users ADD COLUMN last_login TEXT")
    except sqlite3.OperationalError:
        pass  # Column already exists
    except Exception as e:
        print(f"Warning: Failed to add last_login column: {e}")
    try: 
        cur.execute("ALTER TABLE users ADD COLUMN email TEXT")
    except sqlite3.OperationalError:
        pass  # Column already exists
    except Exception as e:
        print(f"Warning: Failed to add email column: {e}")
    try:
        cur.execute("SELECT file_data FROM attachments LIMIT 1")
    except sqlite3.OperationalError:
        cur.execute("DROP TABLE IF EXISTS attachments")
        cur.execute("""
            CREATE TABLE attachments(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                note_id INTEGER,
                user_id INTEGER,
                filename TEXT,
                file_data BLOB,
                file_size INTEGER,
                uploaded_at TEXT
            )
        """)
    except Exception as e:
        print(f"Warning: Attachments table check failed: {e}")
    try:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS sync_queue(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_type TEXT,
                entity_id INTEGER,
                operation TEXT,
                payload TEXT,
                changed_at TEXT,
                synced_at TEXT
            )
        """)
    except Exception as e:
        print(f"Warning: sync_queue migration failed: {e}")
    try:
        cur.execute("CREATE INDEX IF NOT EXISTS idx_notes_user ON notes(user_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_folders_user ON folders(user_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_attachments_note ON attachments(note_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_log(user_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_audit_entity ON audit_log(entity_type, entity_id)")
    except Exception as e:
        print(f"Warning: Failed to create indexes: {e}")

    # Phase 3 replication columns (idempotent). Without these, queue_change's
    # `UPDATE ... SET version = ..., last_modified_device = ...` silently
    # fails in its try/except and publishes empty-data deltas to S3, which
    # peer devices then either apply as NULLs (constraint failure) or
    # skip (harmless with REQ-09 receiver guard, but wrong regardless).
    for _tbl, _col, _def in [
        ('notes',        'version',              'INTEGER NOT NULL DEFAULT 1'),
        ('notes',        'last_modified_device', 'TEXT'),
        ('folders',      'version',              'INTEGER NOT NULL DEFAULT 1'),
        ('folders',      'last_modified_device', 'TEXT'),
        ('note_history', 'version',              'INTEGER NOT NULL DEFAULT 1'),
        ('note_history', 'last_modified_device', 'TEXT'),
    ]:
        existing = cur.execute(f"PRAGMA table_info({_tbl})").fetchall()
        if any(row[1] == _col for row in existing):
            continue
        try:
            cur.execute(f"ALTER TABLE {_tbl} ADD COLUMN {_col} {_def}")
            logger.info(f"schema: added {_tbl}.{_col}")
        except Exception as e:
            logger.warning(f"schema: could not add {_tbl}.{_col}: {e}")

    c.commit()
    c.close()

init_db()

# --- BACKUP ON STARTUP ---
def backup_database():
    """Backup database with timestamp on application launch"""
    if os.path.exists(DB):
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"Backups/evernothing_backup_{timestamp}.db"
        os.makedirs("Backups", exist_ok=True)
        shutil.copy(DB, backup_file)
        print(f"Database backed up to: {backup_file}")


def compress_old_backups(days=5, backup_dir="Backups"):
    """Compress .db backup files older than `days` days into .gz archives."""
    import gzip
    cutoff = datetime.datetime.now() - datetime.timedelta(days=days)
    if not os.path.isdir(backup_dir):
        return
    for fname in os.listdir(backup_dir):
        if not fname.endswith(".db"):
            continue
        fpath = os.path.join(backup_dir, fname)
        if datetime.datetime.fromtimestamp(os.path.getmtime(fpath)) < cutoff:
            gz_path = fpath + ".gz"
            try:
                with open(fpath, "rb") as f_in, gzip.open(gz_path, "wb") as f_out:
                    shutil.copyfileobj(f_in, f_out)
                os.remove(fpath)
                print(f"Compressed backup: {gz_path}")
            except Exception as e:
                print(f"Compress error ({fname}): {e}")


def prune_old_backups(days=5):
    """Delete backup files (.db and .db.gz) older than `days` days from
    both the legacy repo-root 'Backups/' and 'DB/Backups/'."""
    cutoff = datetime.datetime.now() - datetime.timedelta(days=days)
    deleted = 0
    for backup_dir in ('Backups', os.path.join('DB', 'Backups')):
        if not os.path.isdir(backup_dir):
            continue
        for fname in os.listdir(backup_dir):
            if not (fname.endswith('.db') or fname.endswith('.db.gz')):
                continue
            fpath = os.path.join(backup_dir, fname)
            try:
                if datetime.datetime.fromtimestamp(os.path.getmtime(fpath)) < cutoff:
                    os.remove(fpath)
                    deleted += 1
            except OSError as e:
                print(f'Prune error ({fname}): {e}')
    if deleted:
        print(f'Pruned {deleted} backup file(s) older than {days} days.')


def _run_startup_tasks():
    """Filesystem-touching startup work — only called from __main__ so
    that test imports don't race on the same Backups directory under
    pytest -n auto."""
    backup_database()
    compress_old_backups()
    prune_old_backups()

# --- Encryption migration check ---
# Detects mixed plaintext/encrypted state and warns the operator.
# Run Scripts/migrate_encrypt.py to resolve.
_MIXED_ENCRYPTION_WARNING = False

def _check_encryption_state():
    """Sample notes table to detect plaintext rows when encryption is enabled."""
    global _MIXED_ENCRYPTION_WARNING
    if not ENCRYPTION_ENABLED:
        return
    try:
        con = db(); cur = con.cursor()
        rows = cur.execute(
            "SELECT note_key FROM notes ORDER BY RANDOM() LIMIT 20"
        ).fetchall()
        con.close()
        plaintext_count = 0
        for (val,) in rows:
            if val:
                try:
                    base64.b64decode(val)
                    decoded_len = len(base64.b64decode(val))
                    if decoded_len < 28:   # too short to be AES-GCM
                        plaintext_count += 1
                except Exception:
                    plaintext_count += 1   # not base64 → plaintext
        if plaintext_count > 0:
            _MIXED_ENCRYPTION_WARNING = True
            logger.warning(
                f"MIXED ENCRYPTION STATE: {plaintext_count} of {len(rows)} sampled notes "
                "appear to be stored as plaintext. Run Scripts/migrate_encrypt.py to "
                "encrypt all existing data."
            )
    except Exception:
        pass  # table may not exist yet on first run

_check_encryption_state()

# --- AWS SYNC ---
def _s3_client():
    """Return a boto3 S3 client.

    Credential resolution order (most to least preferred):
      1. IAM role / instance profile (no keys needed — preferred)
      2. Explicit AWS_ACCESS_KEY_ID + AWS_SECRET_ACCESS_KEY env vars
      3. Named AWS CLI profile (AWS_PROFILE)

    Raises NoCredentialsError if boto3 cannot find any credentials so the
    caller gets a loud failure instead of a silent no-op.
    """
    from botocore.exceptions import NoCredentialsError, PartialCredentialsError
    # fix #9: always verify TLS — rejects self-signed / MITM certs including
    # corporate proxies doing TLS inspection unless a custom CA bundle is provided.
    ca_bundle = os.environ.get('AWS_CA_BUNDLE') or True  # True = use certifi default
    base = {'region_name': AWS_REGION, 'verify': ca_bundle}
    if AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY:
        return boto3.client('s3', **base,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
    if AWS_PROFILE:
        try:
            return boto3.Session(profile_name=AWS_PROFILE).client('s3', **base)
        except Exception as e:
            logger.warning(f"AWS profile '{AWS_PROFILE}' failed ({e}), falling back to default credential chain")
    # Let boto3 use the default chain (instance profile, ECS task role, env, ~/.aws)
    # This will raise NoCredentialsError loudly if nothing is available
    return boto3.client('s3', **base)

DEVICE_ID = os.environ.get('DEVICE_ID', __import__('socket').gethostname())
_bucket_policy_applied = False

def queue_change(cur, entity_type, entity_id, operation, payload=None):
    """Record a change in sync_queue. Phase 3 Option A semantics:
    bumps the row's version and stamps DEVICE_ID before reading it back,
    so the published payload reflects the local write. Skip the bump on
    DELETE (no row left to stamp). Receiver-applied changes don't call
    queue_change (s3_pull writes via raw sqlite3) — that's the loop guard.
    """
    op = (operation or '').upper()
    if payload is None:
        payload = {}
        try:
            if entity_type == 'note':
                if op != 'DELETE':
                    cur.execute(
                        "UPDATE notes SET version = COALESCE(version, 0) + 1, "
                        "last_modified_device = ? WHERE id = ?",
                        (DEVICE_ID, entity_id))
                r = cur.execute(
                    "SELECT id,user_id,folder_id,note_key,note_value,description,"
                    "updated_at,version,last_modified_device "
                    "FROM notes WHERE id=?", (entity_id,)).fetchone()
                if r:
                    payload = {'id': r[0], 'user_id': r[1], 'folder_id': r[2],
                               'note_key': r[3], 'note_value': r[4],
                               'description': r[5], 'updated_at': r[6],
                               'version': r[7], 'last_modified_device': r[8]}
            elif entity_type == 'folder':
                if op != 'DELETE':
                    cur.execute(
                        "UPDATE folders SET version = COALESCE(version, 0) + 1, "
                        "last_modified_device = ? WHERE id = ?",
                        (DEVICE_ID, entity_id))
                r = cur.execute(
                    "SELECT id,user_id,name,parent_id,version,last_modified_device "
                    "FROM folders WHERE id=?", (entity_id,)).fetchone()
                if r:
                    payload = {'id': r[0], 'user_id': r[1], 'name': r[2],
                               'parent_id': r[3], 'version': r[4],
                               'last_modified_device': r[5]}
        except Exception as e:
            logger.warning(f"queue_change fetch failed: {e}")
    cur.execute(
        "INSERT INTO sync_queue (entity_type, entity_id, operation, payload, changed_at) VALUES(?,?,?,?,?)",
        (entity_type, entity_id, operation, json.dumps(payload),
         datetime.datetime.now(timezone.utc).isoformat())
    )


# ---------------------------------------------------------------------------
# Pull path (REQ-10). Mirrors evernothing_android.py; PC ingests deltas
# published by peer devices under changes/<peer>/<ts>.json. Per-peer
# cursor lives in replication_cursor so restarts don't re-apply.
# Defensive guard (REQ-09 mirror) skips incomplete payloads instead of
# halting the whole cursor on NOT NULL constraint failures.
# ---------------------------------------------------------------------------
def _incoming_wins(local_version, local_device, incoming_version, incoming_device):
    """Deterministic LWW: higher version wins; tie broken by larger device
    id lexicographically."""
    if incoming_version > local_version:
        return True
    if incoming_version < local_version:
        return False
    return (incoming_device or '') > (local_device or '')


def _apply_remote_note(cur, op, nid, data, version, device):
    if op == 'DELETE':
        cur.execute('DELETE FROM notes WHERE id=?', (nid,))
        return cur.rowcount

    # Defensive: empty/incomplete payloads (e.g. from a sender whose
    # schema was missing version/last_modified_device columns) skip
    # cleanly instead of halting the cursor on NULL user_id.
    if (not data
            or data.get('user_id') is None
            or data.get('note_key') is None
            or data.get('note_value') is None):
        keys = list(data.keys()) if isinstance(data, dict) else type(data).__name__
        logger.warning(f'apply note {op} id={nid} from {device} skipped: incomplete payload (keys={keys})')
        return 0

    incoming_ts = data.get('updated_at') or ''
    existing = cur.execute(
        'SELECT id, version, last_modified_device FROM notes WHERE id=?',
        (nid,)).fetchone()

    if existing:
        local_v = int(existing[1] or 1)
        local_d = existing[2]
        if not _incoming_wins(local_v, local_d, version, device):
            return 0
        cur.execute(
            'UPDATE notes SET user_id=?, folder_id=?, note_key=?, note_value=?, '
            'description=?, updated_at=?, version=?, last_modified_device=? '
            'WHERE id=?',
            (data.get('user_id'), data.get('folder_id'), data.get('note_key'),
             data.get('note_value'), data.get('description'), incoming_ts,
             version, device, nid))
    else:
        cur.execute(
            'INSERT INTO notes (id, user_id, folder_id, note_key, note_value, '
            'description, updated_at, version, last_modified_device) '
            'VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
            (nid, data.get('user_id'), data.get('folder_id'),
             data.get('note_key'), data.get('note_value'),
             data.get('description'), incoming_ts, version, device))
    return cur.rowcount


def _apply_remote_folder(cur, op, fid, data, version, device):
    if op == 'DELETE':
        cur.execute('DELETE FROM folders WHERE id=?', (fid,))
        return cur.rowcount

    if (not data
            or data.get('user_id') is None
            or data.get('name') is None):
        keys = list(data.keys()) if isinstance(data, dict) else type(data).__name__
        logger.warning(f'apply folder {op} id={fid} from {device} skipped: incomplete payload (keys={keys})')
        return 0

    existing = cur.execute(
        'SELECT id, version, last_modified_device FROM folders WHERE id=?',
        (fid,)).fetchone()
    if existing:
        local_v = int(existing[1] or 1)
        local_d = existing[2]
        if not _incoming_wins(local_v, local_d, version, device):
            return 0
        cur.execute(
            'UPDATE folders SET user_id=?, name=?, parent_id=?, version=?, '
            'last_modified_device=? WHERE id=?',
            (data.get('user_id'), data.get('name'), data.get('parent_id'),
             version, device, fid))
    else:
        cur.execute(
            'INSERT INTO folders (id, user_id, name, parent_id, version, '
            'last_modified_device) VALUES (?, ?, ?, ?, ?, ?)',
            (fid, data.get('user_id'), data.get('name'), data.get('parent_id'),
             version, device))
    return cur.rowcount


def _apply_remote_changes(changes, sender_device):
    """Apply a batch of remote change entries to the local DB via raw
    sqlite3 (bypassing queue_change so applied rows aren't re-published).
    Returns count of rows touched."""
    con = sqlite3.connect(DB)
    cur = con.cursor()
    touched = 0
    try:
        for ch in changes:
            op       = (ch.get('op') or '').upper()
            entity   = ch.get('entity')
            data     = ch.get('data') or {}
            eid      = ch.get('id') or data.get('id')
            in_dev   = data.get('last_modified_device') or sender_device
            in_ver   = int(data.get('version') or 1)
            if entity == 'note':
                touched += _apply_remote_note(cur, op, eid, data, in_ver, in_dev)
            elif entity == 'folder':
                touched += _apply_remote_folder(cur, op, eid, data, in_ver, in_dev)
            # (other entity types intentionally ignored until REQ-11 lands users)
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()
    return touched


def _load_pull_cursors():
    """Return {peer_device: last_key} from replication_cursor."""
    con = sqlite3.connect(DB)
    try:
        return {row[0]: row[1] for row in
                con.execute('SELECT peer_device, last_key FROM replication_cursor')}
    finally:
        con.close()


def _save_pull_cursor(peer, last_key):
    now = datetime.datetime.now(timezone.utc).isoformat()
    con = sqlite3.connect(DB)
    try:
        con.execute(
            'INSERT INTO replication_cursor (peer_device, last_key, updated_at) '
            'VALUES (?, ?, ?) ON CONFLICT(peer_device) DO UPDATE SET '
            'last_key = excluded.last_key, updated_at = excluded.updated_at',
            (peer, last_key, now))
        con.commit()
    finally:
        con.close()


def pull_deltas(silent=False):
    """Pull pending deltas from peer devices' changes/<peer>/ prefixes.
    Returns total rows applied. Per-peer cursor in replication_cursor
    makes restart-safe; we never re-apply a key we've already processed."""
    if not boto3:
        if not silent:
            logger.warning('S3 pull skipped: boto3 unavailable')
        return 0
    if not S3_BUCKET_NAME:
        if not silent:
            logger.warning('S3 pull skipped: S3_BUCKET_NAME empty')
        return 0

    import io
    s3 = _s3_client()
    cursors = _load_pull_cursors()
    new_keys_by_peer = {}
    try:
        paginator = s3.get_paginator('list_objects_v2')
        for page in paginator.paginate(Bucket=S3_BUCKET_NAME, Prefix='changes/'):
            for obj in page.get('Contents', []) or []:
                key = obj['Key']
                parts = key.split('/', 2)
                if len(parts) < 3:
                    continue
                peer = parts[1]
                if peer == DEVICE_ID:
                    continue
                if cursors.get(peer) and key <= cursors[peer]:
                    continue
                new_keys_by_peer.setdefault(peer, []).append(key)
    except Exception as e:
        logger.warning(f'S3 pull list failed: {e}')
        return 0

    total = 0
    for peer, keys in new_keys_by_peer.items():
        keys.sort()
        for key in keys:
            try:
                buf = io.BytesIO()
                s3.download_fileobj(S3_BUCKET_NAME, key, buf)
                changes = json.loads(buf.getvalue().decode('utf-8'))
            except Exception as e:
                logger.warning(f'S3 pull fetch {key} failed: {e}')
                break
            try:
                applied = _apply_remote_changes(changes, sender_device=peer)
                total += applied
                _save_pull_cursor(peer, key)
                logger.info(f'S3 pull: applied {applied} row(s) from {key}')
            except Exception as e:
                logger.error(f'S3 pull apply {key} failed: {e}')
                break
    return total


# ---------------------------------------------------------------------------
# Phase 0 — bootstrap. A fresh device (empty DB) hydrates from the best
# available S3 snapshot and seeds its per-peer pull cursors at each
# peer's latest key, so the next pull cycle only fetches deltas newer
# than the snapshot instead of replaying months of history.
# ---------------------------------------------------------------------------
def _db_is_empty() -> bool:
    """True when users, notes, and folders are all empty. sync_queue
    and replication_cursor are not counted; a bootstrapped-but-aborted
    state may leave leftovers there and we still want to retry."""
    try:
        con = sqlite3.connect(DB)
        try:
            u = con.execute('SELECT COUNT(*) FROM users').fetchone()[0]
            n = con.execute('SELECT COUNT(*) FROM notes').fetchone()[0]
            f = con.execute('SELECT COUNT(*) FROM folders').fetchone()[0]
        finally:
            con.close()
        return u == 0 and n == 0 and f == 0
    except Exception:
        return True


# S3 keys to try in priority order when bootstrapping the PC. First
# candidate is the PC's own last plaintext snapshot; second is the phone's
# snapshot as a fallback for a fresh PC hydrating from a phone.
_PC_BOOTSTRAP_KEY_CANDIDATES = [
    '{db_basename}',
    'DB/{db_basename}',
    'android/{db_basename}',
]


def _bootstrap_from_s3() -> bool:
    """If the DB is empty, hydrate from the best available S3 snapshot
    and seed replication_cursor at each peer's latest key. Returns True
    if bootstrap ran to completion. Idempotent: a populated DB no-ops."""
    if not _db_is_empty():
        return False
    if not boto3:
        logger.info('bootstrap: skipped (boto3 unavailable)')
        return False
    if not S3_BUCKET_NAME:
        logger.info('bootstrap: skipped (S3_BUCKET_NAME not configured)')
        return False

    import io
    try:
        s3 = _s3_client()
    except Exception as e:
        logger.warning(f'bootstrap: S3 client init failed: {e}')
        return False

    db_basename = os.path.basename(DB)
    restored = False
    for template in _PC_BOOTSTRAP_KEY_CANDIDATES:
        key = template.format(db_basename=db_basename)
        try:
            buf = io.BytesIO()
            s3.download_fileobj(S3_BUCKET_NAME, key, buf)
            data = buf.getvalue()
            if not data:
                continue
            # SQLite header sanity: reject anything else (e.g. gzipped or
            # encrypted). Bootstrap only handles plaintext SQLite files.
            if not data.startswith(b'SQLite format 3\x00'):
                logger.info(f'bootstrap: {key} not a SQLite file, skipping')
                continue
            os.makedirs(os.path.dirname(DB) or '.', exist_ok=True)
            with open(DB, 'wb') as f:
                f.write(data)
            logger.info(f'bootstrap: restored {DB} from s3://{S3_BUCKET_NAME}/{key} ({len(data)} bytes)')
            restored = True
            break
        except Exception as e:
            logger.info(f'bootstrap: {key} not usable ({e})')

    if not restored:
        logger.warning('bootstrap: no S3 snapshot available; starting with empty DB')
        return False

    # Re-run migrations to ensure replication columns are present on the
    # restored snapshot (may predate the Phase 3 schema).
    init_db()

    # Seed cursors so pull_deltas() starts fresh from each peer's latest key.
    _seed_pull_cursors_from_s3(s3)
    return True


def _seed_pull_cursors_from_s3(s3) -> int:
    """List every changes/<peer>/*.json and mark each peer's cursor at
    the LATEST key. Skips our own DEVICE_ID's prefix. Returns count of
    peers seeded."""
    latest_by_peer: dict = {}
    try:
        paginator = s3.get_paginator('list_objects_v2')
        for page in paginator.paginate(Bucket=S3_BUCKET_NAME, Prefix='changes/'):
            for obj in page.get('Contents', []) or []:
                key = obj['Key']
                parts = key.split('/', 2)
                if len(parts) < 3:
                    continue
                peer = parts[1]
                if peer == DEVICE_ID:
                    continue
                if peer not in latest_by_peer or key > latest_by_peer[peer]:
                    latest_by_peer[peer] = key
    except Exception as e:
        logger.warning(f'bootstrap: list changes/ failed: {e}')
        return 0

    for peer, key in latest_by_peer.items():
        _save_pull_cursor(peer, key)
        logger.info(f'bootstrap: cursor[{peer}] = {key}')
    return len(latest_by_peer)


# Minimum required S3 actions for this application
_REQUIRED_S3_ACTIONS = [
    "s3:PutObject",
    "s3:GetObject",
    "s3:ListBucket",
    "s3:HeadBucket",
    "s3:CreateBucket",
    "s3:PutBucketPolicy",
    "s3:PutBucketVersioning",
    "s3:PutPublicAccessBlock"
]

def get_iam_policy():
    """Return the least-privilege IAM policy document scoped to the configured bucket."""
    return {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "EverNothingObjectAccess",
                "Effect": "Allow",
                "Action": ["s3:PutObject", "s3:GetObject"],
                "Resource": f"arn:aws:s3:::{S3_BUCKET_NAME}/*"
            },
            {
                "Sid": "EverNothingBucketAccess",
                "Effect": "Allow",
                "Action": [
                    "s3:ListBucket",
                    "s3:HeadBucket",
                    "s3:CreateBucket",
                    "s3:PutBucketPolicy",
                    "s3:PutBucketVersioning",
                    "s3:PutPublicAccessBlock"
                ],
                "Resource": f"arn:aws:s3:::{S3_BUCKET_NAME}"
            }
        ]
    }


def _apply_bucket_policy(s3, bucket_name):
    """Apply bucket policy that:
      - Denies all requests over plain HTTP (fix #11)
      - Restricts access to ALLOWED_IPS CIDRs when configured (fix #12)
      - Denies all principals except the calling IAM identity
    """
    # Optional IP allowlist — comma-separated CIDRs in S3_ALLOWED_IPS env var
    allowed_ips = [ip.strip() for ip in os.environ.get('S3_ALLOWED_IPS', '').split(',') if ip.strip()]

    try:
        sts_kwargs = {'region_name': AWS_REGION}
        if AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY:
            sts_kwargs['aws_access_key_id'] = AWS_ACCESS_KEY_ID
            sts_kwargs['aws_secret_access_key'] = AWS_SECRET_ACCESS_KEY
        caller_arn = boto3.client('sts', **sts_kwargs).get_caller_identity()['Arn']
    except Exception as e:
        logger.warning(f"Could not determine caller ARN for bucket policy: {e}")
        caller_arn = None

    statements = [
        {
            "Sid": "DenyInsecureTransport",
            "Effect": "Deny",
            "Principal": "*",
            "Action": "s3:*",
            "Resource": [
                f"arn:aws:s3:::{bucket_name}",
                f"arn:aws:s3:::{bucket_name}/*"
            ],
            "Condition": {"Bool": {"aws:SecureTransport": "false"}}
        }
    ]

    if caller_arn:
        statements.append({
            "Sid": "DenyAllExceptCallerPrincipal",
            "Effect": "Deny",
            "Principal": "*",
            "Action": "s3:*",
            "Resource": [
                f"arn:aws:s3:::{bucket_name}",
                f"arn:aws:s3:::{bucket_name}/*"
            ],
            "Condition": {"StringNotEquals": {"aws:PrincipalArn": caller_arn}}
        })

    if allowed_ips:
        statements.append({
            "Sid": "DenyNonAllowedIPs",
            "Effect": "Deny",
            "Principal": "*",
            "Action": "s3:*",
            "Resource": [
                f"arn:aws:s3:::{bucket_name}",
                f"arn:aws:s3:::{bucket_name}/*"
            ],
            "Condition": {"NotIpAddress": {"aws:SourceIp": allowed_ips}}
        })
        logger.info(f"Bucket policy: IP restriction applied to {len(allowed_ips)} CIDR(s)")

    policy = {"Version": "2012-10-17", "Statement": statements}
    try:
        s3.put_bucket_policy(Bucket=bucket_name, Policy=json.dumps(policy))
        logger.info(f"Bucket policy applied to {bucket_name}")
    except Exception as e:
        logger.warning(f"Could not apply bucket policy: {e}")


_BUCKET_POLICY_SENTINEL = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), 'log', '.s3_bucket_hardened')

def _enable_s3_access_logging(s3, bucket_name):
    """Enable S3 server access logging (fix #13). Logs go to <bucket>-logs."""
    log_bucket = f"{bucket_name}-logs"
    try:
        try:
            s3.head_bucket(Bucket=log_bucket)
        except Exception:
            if AWS_REGION == 'us-east-1':
                s3.create_bucket(Bucket=log_bucket)
            else:
                s3.create_bucket(Bucket=log_bucket,
                    CreateBucketConfiguration={'LocationConstraint': AWS_REGION})
            s3.put_public_access_block(Bucket=log_bucket,
                PublicAccessBlockConfiguration={
                    'BlockPublicAcls': True, 'IgnorePublicAcls': True,
                    'BlockPublicPolicy': True, 'RestrictPublicBuckets': True})
        s3.put_bucket_acl(Bucket=log_bucket, ACL='log-delivery-write')
        s3.put_bucket_logging(
            Bucket=bucket_name,
            BucketLoggingStatus={
                'LoggingEnabled': {
                    'TargetBucket': log_bucket,
                    'TargetPrefix': 'access-logs/'
                }
            }
        )
        logger.info(f"S3 access logging enabled → s3://{log_bucket}/access-logs/")
    except Exception as e:
        logger.warning(f"Could not enable S3 access logging: {e}")

def _enable_s3_object_lock(s3, bucket_name):
    """Enable S3 Object Lock GOVERNANCE retention (fix #14).
    Protects backups from accidental or malicious deletion.
    Requires the bucket to have been created with ObjectLockEnabledForBucket=True.
    """
    lock_days = int(os.environ.get('S3_LOCK_DAYS', '30'))
    try:
        s3.put_object_lock_configuration(
            Bucket=bucket_name,
            ObjectLockConfiguration={
                'ObjectLockEnabled': 'Enabled',
                'Rule': {
                    'DefaultRetention': {
                        'Mode': 'GOVERNANCE',
                        'Days': lock_days
                    }
                }
            }
        )
        logger.info(f"S3 Object Lock enabled (GOVERNANCE, {lock_days} days) on {bucket_name}")
    except Exception as e:
        logger.warning(f"Could not enable S3 Object Lock (bucket may need ObjectLockEnabledForBucket=True at creation): {e}")

def _s3_upload_with_retry(fn, *args, **kwargs):
    import time
    for attempt in range(3):
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            if attempt == 2: raise
            wait = 2 ** attempt
            logger.warning(f"S3 upload attempt {attempt+1} failed ({e}), retrying in {wait}s")
            time.sleep(wait)

def sync_s3():
    """Run S3 sync synchronously (blocking). Used by tests and direct calls."""
    if not boto3:
        logger.warning("S3 sync skipped: boto3 not available")
        return
    _sync_s3_worker()

def sync_s3_async():
    """Non-blocking S3 sync — spawns a background thread. Used by HTTP routes."""
    if not boto3:
        logger.warning("S3 sync skipped: boto3 not available")
        return
    if app.config.get('TESTING'):
        return
    import threading
    threading.Thread(target=_sync_s3_worker, daemon=True).start()

# S3 availability status — updated by _sync_s3_worker on each attempt
_s3_status = {'ok': None, 'error': None}   # None = not yet attempted

def get_s3_status():
    """Return (ok: bool|None, error: str|None) for display in the UI."""
    return _s3_status.copy()

def _sync_s3_worker():
    try:
        import io
        global _bucket_policy_applied
        s3 = _s3_client()
        os.makedirs(os.path.dirname(_BUCKET_POLICY_SENTINEL), exist_ok=True)
        # file sentinel prevents redundant hardening calls across workers
        if not _bucket_policy_applied and not os.path.exists(_BUCKET_POLICY_SENTINEL):
            _apply_bucket_policy(s3, S3_BUCKET_NAME)
            _enable_s3_access_logging(s3, S3_BUCKET_NAME)
            _enable_s3_object_lock(s3, S3_BUCKET_NAME)
            try: open(_BUCKET_POLICY_SENTINEL, 'w').close()
            except Exception: pass
            _bucket_policy_applied = True
        elif os.path.exists(_BUCKET_POLICY_SENTINEL):
            _bucket_policy_applied = True

        # Build ExtraArgs — use KMS if configured, otherwise fall back to AES256.
        # SSE is always applied; no upload should ever land unencrypted.
        if KMS_KEY_ID:
            _sse = {"ServerSideEncryption": "aws:kms", "SSEKMSKeyId": KMS_KEY_ID}
        else:
            _sse = {"ServerSideEncryption": "AES256"}
        extra_json = {"ContentType": "application/json", **_sse}
        extra_db   = {**_sse}

        con = db(); cur = con.cursor()
        cur.execute("SELECT id, entity_type, entity_id, operation, payload, changed_at FROM sync_queue WHERE synced_at IS NULL")
        rows = cur.fetchall()
        delta_ids = []
        if rows:
            changes = [{"op": r[3], "entity": r[1], "id": r[2], "data": json.loads(r[4]), "at": r[5]} for r in rows]
            ts = datetime.datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            upload_kwargs = {"ExtraArgs": extra_json}
            _s3_upload_with_retry(s3.upload_fileobj, io.BytesIO(json.dumps(changes).encode("utf-8")),
                                  S3_BUCKET_NAME, f"changes/{DEVICE_ID}/{ts}.json", **upload_kwargs)
            delta_ids = [r[0] for r in rows]
            logger.info(f"S3 delta: {len(changes)} change(s)")
        con.close()

        # mark delta synced only after DB backup succeeds
        ts = datetime.datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        with open(DB, 'rb') as f:
            db_bytes = f.read()
        # fix #8: encrypt the DB file before uploading so metadata/keys are
        # not exposed as plaintext even if SSE is ever misconfigured.
        # Format: 12-byte nonce || AES-GCM ciphertext (same scheme as note encryption)
        if AESGCM and KEY:
            nonce = os.urandom(12)
            db_bytes = nonce + aesgcm.encrypt(nonce, db_bytes, None)
            enc_suffix = '.enc'
        else:
            enc_suffix = ''
        upload_db_kwargs = {"ExtraArgs": extra_db}
        _s3_upload_with_retry(s3.upload_fileobj, io.BytesIO(db_bytes), S3_BUCKET_NAME, DB + enc_suffix, **upload_db_kwargs)
        _s3_upload_with_retry(s3.upload_fileobj, io.BytesIO(db_bytes), S3_BUCKET_NAME, f"backups/{DB}.{ts}{enc_suffix}", **upload_db_kwargs)
        logger.info(f"S3 DB backup: s3://{S3_BUCKET_NAME}/backups/{DB}.{ts}{enc_suffix}")

        if delta_ids:
            con = db(); cur = con.cursor()
            now = datetime.datetime.now(timezone.utc).isoformat()
            cur.execute(f"UPDATE sync_queue SET synced_at=? WHERE id IN ({','.join('?'*len(delta_ids))})", [now]+delta_ids)
            con.commit(); con.close()
        _s3_status['ok'] = True
        _s3_status['error'] = None
        logger.info("S3 sync OK")

        # After a successful publish + backup, pull any pending deltas
        # from peer devices so the local DB converges. Failures here are
        # logged but don't flip _s3_status to error -- pushing succeeded.
        try:
            n = pull_deltas(silent=True)
            if n:
                logger.info(f"S3 pull: applied {n} row(s) from peers")
        except Exception as e:
            logger.warning(f"S3 pull failed: {e}")
    except Exception as e:
        _s3_status['ok'] = False
        _s3_status['error'] = str(e)
        logger.error(f"S3 Sync Error: {e}")

def restore_from_s3():
    """Download DB from S3 if local file is missing (recovery on startup)."""
    if not boto3 or os.path.exists(DB):
        return
    try:
        s3 = _s3_client()
        s3.download_file(S3_BUCKET_NAME, DB, DB)
        logger.info(f"Restored {DB} from s3://{S3_BUCKET_NAME}/{DB}")
        print(f"Restored database from S3: {DB}")
    except Exception as e:
        logger.warning(f"S3 restore skipped: {e}")

# --- AUTH ---
class User(UserMixin):
    def __init__(self, id, username):
        self.id = id
        self.username = username

@login_manager.user_loader
def load_user(uid):
    con = db()
    r = con.cursor().execute(
        "SELECT id,username FROM users WHERE id=?", (uid,)
    ).fetchone()
    con.close()
    return User(*r) if r else None

def validate_input(text, max_length=255, allow_empty=False):
    """Validate and sanitize user input"""
    if text:
        text = text.strip()
    if not text and not allow_empty:
        return None, "Input cannot be empty"
    if text and len(text) > max_length:
        return None, f"Input too long (max {max_length} characters)"
    return text, None

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        return None, "Invalid email format"
    return email, None

def validate_password(password):
    """Validate password strength"""
    if len(password) < 8:
        return None, "Password must be at least 8 characters"
    if not any(c.isupper() for c in password):
        return None, "Password must contain at least one uppercase letter"
    if not any(c.islower() for c in password):
        return None, "Password must contain at least one lowercase letter"
    if not any(c.isdigit() for c in password):
        return None, "Password must contain at least one number"
    return password, None

def allowed_file(filename, stream=None):
    """Check file extension and optionally MIME type against allowlist."""
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'zip'}
    ALLOWED_MIMES = {
        'text/plain', 'application/pdf',
        'image/png', 'image/jpeg', 'image/gif',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/zip',
    }
    if not ('.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS):
        return False
    if stream is not None:
        import imghdr, mimetypes
        header = stream.read(261)
        stream.seek(0)
        # Use python-magic if available, fall back to imghdr/mimetypes
        try:
            import magic
            mime = magic.from_buffer(header, mime=True)
        except ImportError:
            ext = filename.rsplit('.', 1)[1].lower()
            mime = mimetypes.types_map.get('.' + ext, '')
        if mime and mime not in ALLOWED_MIMES:
            return False
    return True

def format_date(iso_str):
    try:
        return datetime.datetime.fromisoformat(iso_str).strftime("%m/%d/%Y %H:%M")
    except Exception:
        return iso_str 

def get_breadcrumbs(cur, fid, uid):
    crumbs = []
    while fid:
        f = cur.execute("SELECT id,name,parent_id FROM folders WHERE id=? AND user_id=?", (fid, uid)).fetchone()
        if not f: break
        crumbs.insert(0, (f[0], decrypt(f[1])))
        fid = f[2]
    return crumbs

def log_change(cur, user_id, action, entity_type, entity_id, old_values, new_values, ip_addr):
    cur.execute(
        "INSERT INTO audit_log (user_id, action, entity_type, entity_id, old_values, new_values, timestamp, ip_address) VALUES(?,?,?,?,?,?,?,?)",
        (user_id, action, entity_type, entity_id, json.dumps(old_values), json.dumps(new_values), datetime.datetime.now(timezone.utc).isoformat(), ip_addr)
    )

@app.errorhandler(404)
def not_found(error):
    logger.warning(f"404 error: {request.url}")
    return _render(STYLE + "<h3>404 - Page Not Found</h3><a href=/>Home</a>"), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"500 error: {error}")
    return _render(STYLE + "<h3>500 - Internal Server Error</h3><a href=/>Home</a>"), 500

# --- ROUTES ---
@app.route("/")
@login_required
def index():
    con = db()
    cur = con.cursor()
    cur.execute("SELECT id,name FROM folders WHERE user_id=? AND parent_id IS NULL", (current_user.id,))
    folders = sorted([(r[0], decrypt(r[1])) for r in cur.fetchall()], key=lambda x: x[1].lower())
    
    cur.execute("SELECT id,note_key,updated_at FROM notes WHERE user_id=? ORDER BY updated_at DESC LIMIT 10", (current_user.id,))
    recent = [(r[0], decrypt(r[1]), format_date(r[2])) for r in cur.fetchall()]
    con.close()
    
    return _render(T_FOLDERS, folders=folders, recent=recent)

@app.route("/folder/add", methods=["GET","POST"])
@login_required
def add_folder():
    if request.method == "POST":
        name, error = validate_input(request.form.get('name', ''))
        if error:
            return _render(T_ADD_FOLDER, error=error)
        
        con = db(); cur = con.cursor()
        try:
            cur.execute(
                "INSERT INTO folders (user_id, name, parent_id) VALUES(?,?,NULL)",
                (current_user.id, encrypt(name))
            )
            queue_change(cur, 'folder', cur.lastrowid, 'INSERT')
            con.commit()
            sync_s3_async()
            logger.info(f"User {current_user.id} created folder: {name}")
        except Exception as e:
            logger.error(f"Error creating folder: {e}")
            con.rollback()
            return _render(T_ADD_FOLDER, error="Failed to create folder")
        finally:
            con.close()
        return redirect("/")
    return _render(T_ADD_FOLDER)

@app.route("/folder/<int:pid>/add_folder", methods=["GET","POST"])
@login_required
def add_subfolder(pid):
    if request.method == "POST":
        con = db(); cur = con.cursor()
        cur.execute(
            "INSERT INTO folders (user_id, name, parent_id) VALUES(?,?,?)",
            (current_user.id, encrypt(request.form['name']), pid)
        )
        queue_change(cur, 'folder', cur.lastrowid, 'INSERT')
        con.commit()
        sync_s3_async()
        con.close()        
        return redirect(f"/folder/{pid}")
    return _render(T_ADD_SUBFOLDER, pid=pid)

def delete_recursive(cur, fid, uid):
    cur.execute("SELECT id FROM folders WHERE parent_id=? AND user_id=?", (fid, uid))
    for sub in cur.fetchall():
        delete_recursive(cur, sub[0], uid)
    cur.execute("DELETE FROM notes WHERE folder_id=? AND user_id=?", (fid, uid))
    cur.execute("DELETE FROM folders WHERE id=? AND user_id=?", (fid, uid))

@app.route("/folder/delete/<int:fid>", methods=["GET","POST"])
@login_required
def delete_folder(fid):
    con = db(); cur = con.cursor() 
    f = cur.execute("SELECT name,parent_id FROM folders WHERE id=? AND user_id=?", (fid, current_user.id)).fetchone()
    if not f:
        con.close()
        return redirect("/")

    if request.method == "POST":
        delete_recursive(cur, fid, current_user.id)
        queue_change(cur, 'folder', fid, 'DELETE')
        con.commit()
        con.close()
        sync_s3_async()
        return redirect(f"/folder/{f[1]}" if f[1] else "/")

    result = _render(T_DELETE_FOLDER, f=(decrypt(f[0]), f[1])) if f else redirect("/")
    con.close()
    return result

@app.route("/folder/rename/<int:fid>", methods=["GET","POST"])
@login_required
def rename_folder(fid):
    con = db(); cur = con.cursor()
    f = cur.execute("SELECT name,parent_id FROM folders WHERE id=? AND user_id=?", (fid, current_user.id)).fetchone()
    if not f:
        con.close()
        return redirect("/")
    if request.method == "POST":
        cur.execute("UPDATE folders SET name=? WHERE id=? AND user_id=?", (encrypt(request.form['name']), fid, current_user.id))
        queue_change(cur, 'folder', fid, 'UPDATE')
        con.commit()
        con.close()
        sync_s3_async()
        return redirect(f"/folder/{fid}")
    con.close()
    return _render(T_RENAME_FOLDER, f=(decrypt(f[0]), f[1]), fid=fid)

@app.route("/note/delete/<int:nid>", methods=["GET","POST"])
@login_required
def delete_note(nid):
    con = db(); cur = con.cursor()
    n = cur.execute("SELECT folder_id, note_key FROM notes WHERE id=? AND user_id=?", (nid, current_user.id)).fetchone()
    if not n:
        con.close()
        return redirect("/")
    if request.method == "POST":
        cur.execute("DELETE FROM notes WHERE id=? AND user_id=?", (nid, current_user.id))
        queue_change(cur, 'note', nid, 'DELETE')
        con.commit()
        con.close()
        sync_s3_async()
        return redirect(f"/folder/{n[0]}" if n[0] else "/")
    con.close()
    return _render(T_DELETE_NOTE, n=(n[0], decrypt(n[1])))

@app.route("/change_password", methods=["GET","POST"])
@login_required
def change_password():
    error = None
    if request.method == "POST":
        con = db()
        cur = con.cursor()
        r = cur.execute("SELECT password FROM users WHERE id=?", (current_user.id,)).fetchone()
        if r and check_password_hash(r[0], request.form['old_password']):
            new_password = request.form['new_password']
            if new_password != request.form.get('verify_password', ''):
                con.close()
                error = "New passwords do not match"
            else:
                cur.execute("UPDATE users SET password=? WHERE id=?", (generate_password_hash(new_password), current_user.id))
                con.commit()
                con.close()
                sync_s3_async()
                return redirect("/")
        else:
            con.close()
            error = "Invalid old password"
    return _render(T_CHANGE_PASSWORD, error=error)

@app.route("/search")
@login_required
def search():
    q = request.args.get('q', '').strip()
    folder_filter = request.args.get('folder', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    use_regex = request.args.get('regex', '') == 'on'
    search_history = request.args.get('history', '') == 'on'
    
    if not q or len(q) > 100:
        return _render(T_SEARCH, notes=[], q=q, folders=[], folder_filter=folder_filter, folder_results=[])
    
    con = db()
    cur = con.cursor()
    try:
        # Get folders for filter dropdown
        cur.execute("SELECT id, name FROM folders WHERE user_id=?", (current_user.id,))
        folders = [(f[0], decrypt(f[1])) for f in cur.fetchall()]
        
        # Build query
        table = "note_history" if search_history else "notes"
        query = f"SELECT id, note_key, note_value, updated_at, folder_id FROM {table} WHERE user_id=?"
        params = [current_user.id]
        
        if folder_filter:
            query += " AND folder_id=?"
            params.append(folder_filter)
        
        if date_from:
            query += " AND updated_at >= ?"
            params.append(date_from)
        
        if date_to:
            query += " AND updated_at <= ?"
            params.append(date_to)
        
        cur.execute(query, params)
        notes = []
        
        if use_regex:
            import re
            try:
                pattern = re.compile(q, re.IGNORECASE)
                for r in cur.fetchall():
                    k, v = decrypt(r[1]), decrypt(r[2])
                    if pattern.search(k) or pattern.search(v):
                        notes.append((r[0], k, format_date(r[3])))
            except re.error:
                notes = []
        else:
            q_lower = q.lower()
            for r in cur.fetchall():
                k, v = decrypt(r[1]), decrypt(r[2])
                if q_lower in k.lower() or q_lower in v.lower():
                    notes.append((r[0], k, format_date(r[3])))

        # Search folder names (case-insensitive)
        folder_results = []
        if not search_history:
            cur.execute("SELECT id, name FROM folders WHERE user_id=?", (current_user.id,))
            if use_regex:
                try:
                    pattern = re.compile(q, re.IGNORECASE)
                    folder_results = [(r[0], decrypt(r[1])) for r in cur.fetchall() if pattern.search(decrypt(r[1]))]
                except re.error:
                    folder_results = []
            else:
                folder_results = [(r[0], decrypt(r[1])) for r in cur.fetchall() if q_lower in decrypt(r[1]).lower()]
            folder_results.sort(key=lambda x: x[1].lower())

        notes.sort(key=lambda x: x[1].lower())
    except Exception as e:
        logger.error(f"Search error: {e}")
        notes = []
        folders = []
        folder_results = []
    finally:
        con.close()
    
    return _render(T_SEARCH, notes=notes, q=q, folders=folders,
                                 folder_results=folder_results,
                                 folder_filter=folder_filter, date_from=date_from, 
                                 date_to=date_to, use_regex=use_regex, search_history=search_history)

@app.route("/export")
@login_required
def export_json():
    con = db()
    cur = con.cursor()
    cur.execute("""
        SELECT n.note_key, n.note_value, n.updated_at, f.name, n.description
        FROM notes n
        LEFT JOIN folders f ON n.folder_id = f.id
        WHERE n.user_id=?
    """, (current_user.id,))
    data = [{"note": decrypt(r[0]), "content": decrypt(r[1]), "description": decrypt(r[4]) if r[4] else "", "updated_at": r[2], "folder": decrypt(r[3]) if r[3] else None} for r in cur.fetchall()]
    con.close()
    resp = make_response(json.dumps(data, indent=2))
    resp.headers['Content-Disposition'] = 'attachment; filename=notes.json'
    resp.headers['Content-Type'] = 'application/json'
    return resp

@app.route("/folder/<int:fid>")
@login_required
def view_folder(fid):
    con = db()
    cur = con.cursor()
    folder = cur.execute("SELECT id,name,parent_id FROM folders WHERE id=? AND user_id=?", (fid, current_user.id)).fetchone()
    if not folder:
        con.close()
        return redirect("/")

    # Build breadcrumb: walk up parent chain
    breadcrumb = [(folder[0], decrypt(folder[1]))]
    parent_id = folder[2]
    while parent_id:
        parent = cur.execute("SELECT id,name,parent_id FROM folders WHERE id=? AND user_id=?", (parent_id, current_user.id)).fetchone()
        if not parent:
            break
        breadcrumb.insert(0, (parent[0], decrypt(parent[1])))
        parent_id = parent[2]

    cur.execute("SELECT id,name FROM folders WHERE user_id=? AND parent_id=?", (current_user.id, fid))
    subfolders = sorted([(r[0], decrypt(r[1])) for r in cur.fetchall()], key=lambda x: x[1].lower())

    cur.execute("SELECT id,note_key FROM notes WHERE user_id=? AND folder_id=?", (current_user.id, fid))
    notes = sorted([(r[0], decrypt(r[1])) for r in cur.fetchall()], key=lambda x: x[1].lower())
    con.close()

    return _render(T_NOTES, notes=notes, subfolders=subfolders,
                   folder=(folder[0], decrypt(folder[1]), folder[2]),
                   breadcrumb=breadcrumb)

@app.route("/add/<int:fid>", methods=["GET","POST"])
@login_required
def add(fid):
    from markupsafe import escape
    error = None
    note_val = ""
    content_val = ""
    desc_val = ""
    if request.method == "POST":
        note_val = str(escape(request.form['note']))
        content_val = str(escape(request.form['content']))
        con = db(); cur = con.cursor()
        
        desc_val = request.form.get('description', '')[:255]
        if not note_val.strip() or not content_val.strip():
            error = "Note and content cannot be empty"
            con.close()
        else:
            cur.execute("SELECT note_key FROM notes WHERE user_id=?", (current_user.id,))
            if any(decrypt(r[0]).strip().lower() == str(note_val).strip().lower() for r in cur.fetchall()):
                error = "Note name already exists"
                con.close()
            else:
                cur.execute(
                    "INSERT INTO notes (user_id, folder_id, note_key, note_value, description, updated_at) VALUES(?,?,?,?,?,?)",
                    (current_user.id, fid, encrypt(note_val), encrypt(content_val), encrypt(desc_val), datetime.datetime.now(timezone.utc).isoformat())
                )
                nid = cur.lastrowid
                log_change(cur, current_user.id, 'CREATE', 'note', nid, {}, {'note': note_val, 'content': content_val, 'description': desc_val, 'folder_id': fid}, request.remote_addr)
                cur.execute(
                    "INSERT INTO note_history (note_id, user_id, note_key, note_value, description, folder_id, updated_at) VALUES(?,?,?,?,?,?,?)",
                    (nid, current_user.id, encrypt(note_val), encrypt(content_val), encrypt(desc_val), fid, datetime.datetime.now(timezone.utc).isoformat())
                )
                if 'file' in request.files and request.files['file'].filename:
                    file = request.files['file']
                    if not allowed_file(file.filename):
                        error = "File type not allowed"
                        con.close()
                    else:
                        filename = file.filename[:255]  # Limit filename length
                        file_data = file.read()
                        if len(file_data) > 0 and len(file_data) <= app.config['MAX_CONTENT_LENGTH']:
                            cur.execute(
                                "INSERT INTO attachments (note_id, user_id, filename, file_data, file_size, uploaded_at) VALUES(?,?,?,?,?,?)",
                                (nid, current_user.id, filename, file_data, len(file_data), datetime.datetime.now(timezone.utc).isoformat())
                            )
                            log_change(cur, current_user.id, 'CREATE', 'attachment', cur.lastrowid, {}, {'note_id': nid, 'filename': filename, 'size': len(file_data)}, request.remote_addr)
                        else:
                            error = "File too large or empty"
                            con.close()
                con.commit()
                queue_change(cur, 'note', nid, 'INSERT')
                con.commit()
                con.close()
                sync_s3_async()
                return redirect(f"/folder/{fid}")
    return _render(T_ADD, fid=fid, error=error, note=note_val, content=content_val, description=desc_val)

@app.route("/edit/<int:id>", methods=["GET","POST"])
@login_required
def edit(id):
    con = db()
    cur = con.cursor()
    folders = cur.execute(
        "SELECT id,name FROM folders WHERE user_id=?",
        (current_user.id,)
    ).fetchall()
    folders = sorted([(f[0], decrypt(f[1])) for f in folders], key=lambda x: x[1].lower())

    cur.execute(
        "SELECT note_key,note_value,folder_id,updated_at,description FROM notes WHERE id=? AND user_id=?",
        (id, current_user.id),
    )
    row = cur.fetchone()
    if not row:
        con.close()
        return redirect("/")
    note = [decrypt(row[0]), decrypt(row[1]), row[2], row[3], decrypt(row[4]) if row[4] else ""]
    note[3] = format_date(note[3])

    try:
        cur.execute("SELECT id,filename,file_size FROM attachments WHERE note_id=? AND user_id=?", (id, current_user.id))
        attachments = cur.fetchall()
    except:
        attachments = []

    if request.method == "POST":
        # Check if this is a file upload (has file and no note/content fields)
        if 'file' in request.files and request.files['file'].filename and 'note' not in request.form:
            file = request.files['file']
            if not allowed_file(file.filename):
                con.close()
                return _render(T_EDIT, note=note, folders=folders, breadcrumbs=[], id=id, attachments=[], error="File type not allowed")
            
            filename = file.filename[:255]  # Limit filename length
            file_data = file.read()
            if len(file_data) > 0 and len(file_data) <= app.config['MAX_CONTENT_LENGTH']:
                cur.execute(
                    "INSERT INTO attachments (note_id, user_id, filename, file_data, file_size, uploaded_at) VALUES(?,?,?,?,?,?)",
                    (id, current_user.id, filename, file_data, len(file_data), datetime.datetime.now(timezone.utc).isoformat())
                )
                log_change(cur, current_user.id, 'CREATE', 'attachment', cur.lastrowid, {}, {'note_id': id, 'filename': filename, 'size': len(file_data)}, request.remote_addr)
                con.commit()
                con.close()
                sync_s3_async()
                return redirect(f"/edit/{id}")
            else:
                con.close()
                return _render(T_EDIT, note=note, folders=folders, breadcrumbs=[], id=id, attachments=[], error="File too large or empty")

        # Handle note edit
        if 'note' in request.form and 'content' in request.form:
            new_desc = request.form.get('description', '')[:255]
            if note[0] == request.form['note'] and note[1] == request.form['content'] and str(note[2]) == str(request.form.get('folder_id')) and note[4] == new_desc:
                con.close()
                return redirect("/")

            if request.form.get('confirm') == 'yes':
                now = datetime.datetime.now(timezone.utc).isoformat()
                old_vals = {'note': note[0], 'content': note[1], 'description': note[4], 'folder_id': note[2]}
                new_vals = {'note': request.form['note'], 'content': request.form['content'], 'description': new_desc, 'folder_id': request.form.get('folder_id')}
                cur.execute(
                    "UPDATE notes SET note_key=?,note_value=?,description=?,folder_id=?,updated_at=? WHERE id=? AND user_id=?",
                    (
                        encrypt(request.form['note']),
                        encrypt(request.form['content']),
                        encrypt(new_desc),
                        request.form.get('folder_id'),
                        now,
                        id,
                        current_user.id,
                    ),
                )
                log_change(cur, current_user.id, 'UPDATE', 'note', id, old_vals, new_vals, request.remote_addr)
                cur.execute(
                    "INSERT INTO note_history (note_id, user_id, note_key, note_value, description, folder_id, updated_at) VALUES(?,?,?,?,?,?,?)",
                    (id, current_user.id, encrypt(request.form['note']), encrypt(request.form['content']), encrypt(new_desc), request.form.get('folder_id'), now)
                )
                con.commit()
                queue_change(cur, 'note', id, 'UPDATE')
                con.commit()
                con.close()
                sync_s3_async()
                return redirect("/")
            else:
                con.close()
                return _render(T_EDIT_CONFIRM, note=[request.form['note'], request.form['content'], request.form.get('folder_id'), None, new_desc], id=id)

    breadcrumbs = get_breadcrumbs(cur, note[2], current_user.id)
    con.close()
    return _render(T_EDIT, note=note, folders=folders, breadcrumbs=breadcrumbs, id=id, attachments=attachments)

@app.route("/history/<int:nid>")
@login_required
def history(nid):
    con = db()
    cur = con.cursor()
    cur.execute("SELECT id,note_key,updated_at FROM note_history WHERE note_id=? AND user_id=? ORDER BY updated_at DESC", (nid, current_user.id))
    history = [(h[0], decrypt(h[1]), format_date(h[2])) for h in cur.fetchall()]
    con.close()
    return _render(T_HISTORY, history=history, nid=nid)

@app.route("/history/restore/<int:hid>", methods=["GET","POST"])
@login_required
def restore_history(hid):
    con = db(); cur = con.cursor()
    h = cur.execute("SELECT note_id,note_key,note_value,folder_id FROM note_history WHERE id=? AND user_id=?", (hid, current_user.id)).fetchone()
    if not h:
        con.close()
        return redirect("/")
    if request.method == "GET":
        note_key_preview = decrypt(h[1])
        con.close()
        return render_template_string(
            STYLE + """
<nav class="nav">
  <span class="nav-brand">&#11088; EverNothing</span>
  <a href=/history/{{nid}}>&#8592; Back</a>
  <form action="/set_theme" method="get" style="display:inline">
    <select name="t" class="theme-select" onchange="this.form.submit()" title="Switch theme">
      <option value="stellar" {% if theme != "unicorn" %}selected="selected"{% endif %}>&#11088; Stellar</option>
      <option value="unicorn" {% if theme == "unicorn" %}selected="selected"{% endif %}>&#x1F984; Unicorn</option>
      <option value="startrek" {% if theme == "startrek" %}selected="selected"{% endif %}>&#x1F596; Star Trek</option>
      <option value="shrek" {% if theme == "shrek" %}selected="selected"{% endif %}>&#127807; Shrek</option>
      <option value="lotr" {% if theme == "lotr" %}selected="selected"{% endif %}>&#9770; LOTR</option>
    </select>
  </form>
  <a href=/logout class="nav-logout">Logout</a>
</nav>
<div class="container">
  <div class="confirm-box">
    <h3>Confirm Rollback</h3>
    <p>Restore note to version: <b>{{key}}</b>?</p>
    <form method=post>
      <input type=hidden name=csrf_token value="{{ csrf_token() }}">
      <div class="btn-group">
        <button class="btn btn-primary">Yes, Restore</button>
        <a href=/history/{{nid}} class="btn">Cancel</a>
      </div>
    </form>
  </div>
</div>""",
            key=note_key_preview, nid=h[0]
        )
    now = datetime.datetime.now(timezone.utc).isoformat()
    cur.execute(
        "UPDATE notes SET note_key=?,note_value=?,folder_id=?,updated_at=? WHERE id=? AND user_id=?",
        (h[1], h[2], h[3], now, h[0], current_user.id)
    )
    cur.execute(
        "INSERT INTO note_history (note_id, user_id, note_key, note_value, folder_id, updated_at) VALUES(?,?,?,?,?,?)",
        (h[0], current_user.id, h[1], h[2], h[3], now)
    )
    con.commit()
    con.close()
    sync_s3_async()
    return redirect(f"/edit/{h[0]}")

# --- ADMIN AUTH HELPER ---
# #12/#13: decorators imported from evernothing_security — no duplicate definitions
from evernothing_security import admin_required, api_login_required

# --- ADMIN ---
@app.route("/admin", methods=["GET","POST"])
def admin_login():
    if request.method == "POST":
        from rate_limiter import check_rate_limit, RATE_LIMIT_LOGIN
        from Evernothing_Security.admin_auth import verify_admin
        # Rate-limit admin POSTs per IP using the same hourly bucket as user
        # login. Was previously unrestricted.
        if not check_rate_limit(request.remote_addr, 'admin', RATE_LIMIT_LOGIN):
            logger.warning(f"Rate limit exceeded for admin login from {request.remote_addr}")
            return _render(T_ADMIN_LOGIN, error="Too many attempts. Please try again later.")

        if verify_admin(request.form.get("username", ""), request.form.get("password", "")):
            # #10/#11: record login time for timeout; log to audit_log
            session['admin_logged_in'] = True
            session['admin_login_time'] = datetime.datetime.now(timezone.utc).isoformat()
            con = db(); cur = con.cursor()
            log_change(cur, 0, 'CREATE', 'admin_session', 0, {},
                       {'admin': os.environ.get('ADMIN_USER') or 'admin', 'ip': request.remote_addr},
                       request.remote_addr)
            con.commit(); con.close()
            return redirect("/admin/dashboard")
        return _render(T_ADMIN_LOGIN, error="Invalid credentials")
    timeout = request.args.get('timeout')
    return _render(T_ADMIN_LOGIN, error="Admin session expired. Please log in again." if timeout else None)

@app.route("/admin/dashboard")
@admin_required
def admin_dashboard():
    q = request.args.get('q', '')
    con = db()
    cur = con.cursor()
    sql = """
        SELECT u.id, u.username, COUNT(DISTINCT n.id), COUNT(DISTINCT f.id), u.last_login
        FROM users u 
        LEFT JOIN notes n ON u.id = n.user_id 
        LEFT JOIN folders f ON u.id = f.user_id
        WHERE u.username LIKE ?
        GROUP BY u.id 
        ORDER BY u.username
    """
    cur.execute(sql, (f'%{q}%',))
    users = [(r[0], r[1], r[2], r[3], format_date(r[4]) if r[4] else "Never") for r in cur.fetchall()]
    con.close()
    return _render(T_ADMIN_DASHBOARD, users=users, q=q)

@app.route("/admin/user/<int:uid>", methods=["GET","POST"])
@admin_required
def admin_edit_user(uid):
    con = db()
    cur = con.cursor()
    user = cur.execute("SELECT id, username, last_login FROM users WHERE id=?", (uid,)).fetchone()
    if not user:
        con.close()
        return redirect("/admin/dashboard")
    
    if request.method == "POST":
        new_name = request.form.get('new_username')
        new_pass = request.form.get('new_password')
        new_last_login = request.form.get('last_login')
        if request.form.get('confirm') == 'yes':
            try:
                old_vals = {'username': user[1], 'last_login': user[2]}
                new_vals = {'username': new_name, 'last_login': new_last_login}
                if new_pass:
                    new_vals['password'] = '***changed***'
                cur.execute("UPDATE users SET username=?, last_login=? WHERE id=?", (new_name, new_last_login, uid))
                if new_pass:
                    cur.execute("UPDATE users SET password=? WHERE id=?", (generate_password_hash(new_pass), uid))
                log_change(cur, current_user.id if hasattr(current_user, 'id') else 0, 'UPDATE', 'user', uid, old_vals, new_vals, request.remote_addr)
                con.commit()
                con.close()
                sync_s3_async()
                return redirect("/admin/dashboard")
            except sqlite3.IntegrityError:
                con.close()
                return _render(T_ADMIN_EDIT_USER, user=user, error="Username already exists")
        else:
            con.close()
            return _render(T_ADMIN_EDIT_USER_CONFIRM, user=user, new_name=new_name, new_pass=new_pass, new_last_login=new_last_login)

    con.close()
    return _render(T_ADMIN_EDIT_USER, user=user)

@app.route("/admin/user/delete/<int:uid>", methods=["GET","POST"])
@admin_required
def admin_delete_user(uid):
    con = db()
    cur = con.cursor()
    user = cur.execute("SELECT id, username FROM users WHERE id=?", (uid,)).fetchone()
    if not user:
        con.close()
        return redirect("/admin/dashboard")
    
    if request.method == "POST":
        cur.execute("DELETE FROM notes WHERE user_id=?", (uid,))
        cur.execute("DELETE FROM folders WHERE user_id=?", (uid,))
        cur.execute("DELETE FROM note_history WHERE user_id=?", (uid,))
        log_change(cur, 0, 'DELETE', 'user', uid,
                   {'username': user[1]}, {},
                   request.remote_addr)
        cur.execute("DELETE FROM users WHERE id=?", (uid,))
        con.commit()
        con.close()
        sync_s3_async()
        return redirect("/admin/dashboard")

    con.close()
    return _render(T_ADMIN_DELETE_USER, user=user)

@app.route("/admin/iam_policy")
@admin_required
def admin_iam_policy():
    policy = json.dumps(get_iam_policy(), indent=2)
    return _render(STYLE + """
<nav class="nav">
  <span class="nav-brand">&#11088; Admin</span>
  <a href=/admin/dashboard>&#8592; Dashboard</a>
  <form action="/set_theme" method="get" style="display:inline">
    <select name="t" class="theme-select" onchange="this.form.submit()" title="Switch theme">
      <option value="stellar" {% if theme != "unicorn" %}selected="selected"{% endif %}>&#11088; Stellar</option>
      <option value="unicorn" {% if theme == "unicorn" %}selected="selected"{% endif %}>&#x1F984; Unicorn</option>
      <option value="startrek" {% if theme == "startrek" %}selected="selected"{% endif %}>&#x1F596; Star Trek</option>
      <option value="shrek" {% if theme == "shrek" %}selected="selected"{% endif %}>&#127807; Shrek</option>
      <option value="lotr" {% if theme == "lotr" %}selected="selected"{% endif %}>&#9770; LOTR</option>
    </select>
  </form>
  <a href=/logout class="nav-logout">Logout</a>
</nav>
<div class="container">
  <h3>Least-Privilege IAM Policy</h3>
  <p style="color:#888;font-size:.85rem;margin-bottom:16px">
    Apply this policy to the IAM user or role used by EverNothing.
    It grants only the minimum S3 actions required, scoped to
    <b>arn:aws:s3:::{{ bucket }}</b> only.
  </p>
  <div class="card">
    <pre style="white-space:pre-wrap;font-size:.85rem;color:var(--gold)">{{ policy }}</pre>
  </div>
  <p style="color:#555;font-size:.8rem;margin-top:12px">
    CLI equivalent: <code>python evernothing_s3.py --iam-policy</code>
  </p>
</div>
""", policy=policy, bucket=S3_BUCKET_NAME)


@app.route("/admin/s3_backups")
@admin_required
def admin_s3_backups():
    
    backups = []
    try:
        if boto3:
            s3 = _s3_client()
            response = s3.list_objects_v2(Bucket=S3_BUCKET_NAME, Prefix='backups/')
            if 'Contents' in response:
                for obj in response['Contents']:
                    backups.append({
                        'key': obj['Key'],
                        'size': obj['Size'],
                        'modified': obj['LastModified'].strftime('%m/%d/%Y %H:%M')
                    })
                backups.sort(key=lambda x: x['modified'], reverse=True)
    except Exception as e:
        logger.error(f"Failed to list S3 backups: {e}")
    
    return _render(T_ADMIN_S3_BACKUPS, backups=backups)

@app.route("/admin/s3_restore/<path:key>", methods=["GET","POST"])
@admin_required
def admin_s3_restore(key):
    if request.method == "GET":
        return _render(T_ADMIN_S3_BACKUPS, backups=[], confirm_key=key)
    
    try:
        if boto3:
            s3 = _s3_client()
            # Download backup
            backup_file = f"restore_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            s3.download_file(S3_BUCKET_NAME, key, backup_file)
            logger.info(f"Restored backup from S3: {key} to {backup_file}")
            return _render(T_ADMIN_S3_BACKUPS, backups=[], message=f"Backup restored to {backup_file}. Restart app to use it.")
    except Exception as e:
        logger.error(f"Failed to restore S3 backup: {e}")
        return _render(T_ADMIN_S3_BACKUPS, backups=[], error=f"Restore failed: {e}")
    
    return redirect("/admin/s3_backups")

@app.route("/admin/sessions")
@admin_required
def admin_sessions():
    con = db()
    cur = con.cursor()
    cur.execute("""
        SELECT u.username, s.session_id, s.login_time, s.logout_time, s.ip_address, s.user_agent
        FROM user_sessions s
        JOIN users u ON s.user_id = u.id
        ORDER BY s.login_time DESC
        LIMIT 200
    """)
    sessions = [{
        'username': r[0],
        'session_id': r[1],
        'login_time': format_date(r[2]),
        'logout_time': format_date(r[3]) if r[3] else 'Active',
        'ip': r[4],
        'user_agent': (r[5] or '')[:50] + ('...' if r[5] and len(r[5]) > 50 else '')
    } for r in cur.fetchall()]
    con.close()
    return _render(T_ADMIN_SESSIONS, sessions=sessions)

@app.route("/admin/audit_logs")
@admin_required
def admin_audit_logs():
    user_filter = request.args.get('user', '')
    action_filter = request.args.get('action', '')
    entity_filter = request.args.get('entity', '')
    limit = int(request.args.get('limit', 100))
    
    con = db()
    cur = con.cursor()
    
    query = """
        SELECT a.id, u.username, a.action, a.entity_type, a.entity_id, a.old_values, a.new_values, a.timestamp, a.ip_address
        FROM audit_log a
        LEFT JOIN users u ON a.user_id = u.id
        WHERE 1=1
    """
    params = []
    
    if user_filter:
        query += " AND u.username LIKE ?"
        params.append(f'%{user_filter}%')
    if action_filter:
        query += " AND a.action = ?"
        params.append(action_filter)
    if entity_filter:
        query += " AND a.entity_type = ?"
        params.append(entity_filter)
    
    query += " ORDER BY a.timestamp DESC LIMIT ?"
    params.append(limit)
    
    cur.execute(query, params)
    logs = []
    for r in cur.fetchall():
        old_vals = json.loads(r[5]) if r[5] else {}
        new_vals = json.loads(r[6]) if r[6] else {}
        logs.append({
            'id': r[0],
            'user': r[1] or 'System',
            'action': r[2],
            'entity': f"{r[3]} #{r[4]}",
            'old': old_vals,
            'new': new_vals,
            'timestamp': format_date(r[7]),
            'ip': r[8]
        })
    con.close()
    return _render(T_ADMIN_AUDIT_LOGS, logs=logs, user_filter=user_filter, action_filter=action_filter, entity_filter=entity_filter, limit=limit)

# --- PASSWORD RESET ---
def get_serializer():
    return URLSafeTimedSerializer(app.secret_key)

@app.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form['email']
        con = db()
        cur = con.cursor()
        user = cur.execute("SELECT username FROM users WHERE email=?", (email,)).fetchone()
        con.close()
        if user:
            token = get_serializer().dumps(email, salt='recover-key')
            link = request.url_root + "reset_password/" + token
            
            # Try to send email
            try:
                from email_utils import send_password_reset_email
                if send_password_reset_email(email, link):
                    logger.info(f"Password reset email sent to {email}")
                else:
                    logger.warning(f"Failed to send password reset email to {email}")
            except ImportError:
                logger.warning("email_utils not available; password reset link was not sent")
        return _render(T_FORGOT_PASSWORD, message="If that email exists, a reset link has been sent.")
    return _render(T_FORGOT_PASSWORD)

@app.route("/reset_password/<token>", methods=["GET", "POST"])
def reset_password(token):
    try: email = get_serializer().loads(token, salt='recover-key', max_age=3600)
    except: return _render(T_RESET_PASSWORD, error="Invalid or expired token.")
    if request.method == "POST":
        con = db()
        cur = con.cursor()
        cur.execute("UPDATE users SET password=? WHERE email=?", (generate_password_hash(request.form['password']), email))
        con.commit()
        con.close()
        sync_s3_async()
        return redirect("/login")
    return _render(T_RESET_PASSWORD)

# --- LOGIN ---
@app.route("/login", methods=["GET","POST"])
def login():
    from rate_limiter import check_rate_limit, get_remaining_attempts, RATE_LIMIT_LOGIN
    from Evernothing_Security.login_lockout import (
        is_locked, register_failure, clear_failures, lockout_seconds_remaining,
    )

    con = db()
    cur = con.cursor()
    error = None

    # Check for timeout/invalid session messages
    if request.args.get('timeout'):
        error = "Session expired due to inactivity. Please login again."
    elif request.args.get('invalid'):
        error = "Invalid session. Please login again."
    elif request.args.get('csrf'):
        error = "Your session has expired. Please log in again."

    if request.method == "POST":
        username = request.form.get('username', '')

        # Per-IP rate limit
        if not check_rate_limit(request.remote_addr, 'login', RATE_LIMIT_LOGIN):
            logger.warning(f"Rate limit exceeded for login from {request.remote_addr}")
            con.close()
            return _render(T_LOGIN, error="Too many login attempts. Please try again later.",
                           last_user=request.cookies.get('last_user', ''))

        # Per-username lockout
        if is_locked(username):
            secs = lockout_seconds_remaining(username)
            mins = max(1, secs // 60)
            con.close()
            return _render(T_LOGIN,
                           error=f"Account locked due to repeated failed logins. Try again in ~{mins} min.",
                           last_user=request.cookies.get('last_user', ''))

        r = cur.execute(
            "SELECT id,password FROM users WHERE username=?", (username,)
        ).fetchone()
        if r and check_password_hash(r[1], request.form['password']):
            clear_failures(username)
            # Check concurrent session limit (max 3 active sessions)
            active_sessions = cur.execute(
                "SELECT COUNT(*) FROM user_sessions WHERE user_id=? AND logout_time IS NULL",
                (r[0],)
            ).fetchone()[0]
            
            if active_sessions >= 3:
                # Terminate oldest session
                oldest = cur.execute(
                    "SELECT session_id FROM user_sessions WHERE user_id=? AND logout_time IS NULL ORDER BY login_time ASC LIMIT 1",
                    (r[0],)
                ).fetchone()
                if oldest:
                    cur.execute(
                        "UPDATE user_sessions SET logout_time=? WHERE session_id=?",
                        (datetime.datetime.now(timezone.utc).isoformat(), oldest[0])
                    )
            
            # Check if "Remember Me" is checked
            remember_me = request.form.get('remember_me') == 'on'
            
            session_id = os.urandom(16).hex()
            session['session_id'] = session_id
            session['last_activity'] = datetime.datetime.now(timezone.utc).isoformat()
            session['remember_me'] = remember_me
            session.permanent = True
            
            cur.execute("UPDATE users SET last_login=? WHERE id=?", (datetime.datetime.now(timezone.utc).isoformat(), r[0]))
            cur.execute(
                "INSERT INTO user_sessions (user_id, session_id, login_time, ip_address, user_agent) VALUES (?, ?, ?, ?, ?)",
                (r[0], session_id, datetime.datetime.now(timezone.utc).isoformat(), request.remote_addr, request.user_agent.string)
            )
            con.commit()
            con.close()
            login_user(User(r[0], username), remember=remember_me)
            resp = make_response(redirect("/"))
            # Remember username for this device (1 year). Not the password.
            resp.set_cookie(
                'last_user', username,
                max_age=60 * 60 * 24 * 365,
                httponly=True,
                secure=app.config.get('SESSION_COOKIE_SECURE', True),
                samesite='Lax',
            )
            return resp
        # Failed login — register against username (mitigates IP-rotation
        # bypass of the per-IP rate limiter).
        if register_failure(username):
            logger.warning(f"Account locked for {username!r} after repeated failed logins from {request.remote_addr}")
        error = "Invalid username or password"
    con.close()
    return _render(T_LOGIN, error=error, last_user=request.cookies.get('last_user', ''))

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        from rate_limiter import check_rate_limit, RATE_LIMIT_REGISTER
        
        # Check rate limit
        if not check_rate_limit(request.remote_addr, 'register', RATE_LIMIT_REGISTER):
            error = "Too many registration attempts. Please try again later."
            logger.warning(f"Rate limit exceeded for registration from {request.remote_addr}")
            return _render(T_REGISTER, error=error)
        
        username, error = validate_input(request.form.get('username', ''), max_length=50)
        if error:
            return _render(T_REGISTER, error=error)
        
        email, error = validate_email(request.form.get('email', ''))
        if error:
            return _render(T_REGISTER, error=error)
        
        password, error = validate_password(request.form.get('password', ''))
        if error:
            return _render(T_REGISTER, error=error)
        
        con = db()
        cursor=con.cursor()
        try:
            cursor.execute(
                "INSERT INTO users (username, password, email) VALUES(?,?,?)",
                (username, generate_password_hash(password), email)
            )
            con.commit()
            sync_s3_async()
            logger.info(f"New user registered: {username!r}")
            return redirect("/login")
        except sqlite3.IntegrityError:
            logger.warning(f"Duplicate registration attempt: {username}")
            return _render(T_REGISTER, error="Username already exists")
        except Exception as e:
            logger.error(f"Registration error: {e}")
            return _render(T_REGISTER, error="Registration failed")
        finally:
            con.close()
    return _render(T_REGISTER)

@app.route("/logout")
def logout():
    if 'session_id' in session:
        con = db()
        cur = con.cursor()
        cur.execute(
            "UPDATE user_sessions SET logout_time=? WHERE session_id=?",
            (datetime.datetime.now(timezone.utc).isoformat(), session['session_id'])
        )
        con.commit()
        con.close()
    forget_device = request.args.get('forget') == '1'
    logout_user(); session.clear()
    resp = make_response(redirect("/login"))
    if forget_device:
        # Clear the remembered-username cookie. Match the original
        # set_cookie attributes so the browser actually overwrites it.
        resp.set_cookie('last_user', '', max_age=0, expires=0,
                        httponly=True,
                        secure=app.config.get('SESSION_COOKIE_SECURE', True),
                        samesite='Lax')
    return resp

@app.route("/set_theme")
def set_theme():
    t = request.args.get('t', '')
    if t in ('stellar', 'unicorn', 'startrek', 'shrek', 'lotr'):
        session['theme'] = t
    else:
        cycle = {'stellar': 'unicorn', 'unicorn': 'startrek', 'startrek': 'shrek', 'shrek': 'lotr', 'lotr': 'stellar'}
        session['theme'] = cycle.get(session.get('theme', 'stellar'), 'stellar')
    return redirect(request.referrer or '/')

@app.route("/sessions")
@login_required
def view_sessions():
    con = db()
    cur = con.cursor()
    cur.execute(
        "SELECT session_id, login_time, logout_time, ip_address, user_agent FROM user_sessions WHERE user_id=? ORDER BY login_time DESC LIMIT 10",
        (current_user.id,)
    )
    sessions = []
    for s in cur.fetchall():
        sessions.append({
            'session_id': s[0],
            'login_time': format_date(s[1]),
            'logout_time': format_date(s[2]) if s[2] else 'Active',
            'ip': s[3],
            'user_agent': s[4][:50] + '...' if len(s[4]) > 50 else s[4],
            'is_current': s[0] == session.get('session_id')
        })
    con.close()
    return _render(T_SESSIONS, sessions=sessions)

@app.route("/session/revoke/<session_id>")
@login_required
def revoke_session(session_id):
    con = db()
    cur = con.cursor()
    # Only allow revoking own sessions
    cur.execute(
        "UPDATE user_sessions SET logout_time=? WHERE session_id=? AND user_id=?",
        (datetime.datetime.now(timezone.utc).isoformat(), session_id, current_user.id)
    )
    con.commit()
    con.close()
    return redirect("/sessions")

@app.route("/audit_report")
@login_required
def audit_report():
    con = db()
    cur = con.cursor()
    cur.execute("""
        SELECT a.id, u.username, a.action, a.entity_type, a.entity_id, a.old_values, a.new_values, a.timestamp, a.ip_address
        FROM audit_log a
        LEFT JOIN users u ON a.user_id = u.id
        WHERE a.user_id = ? OR ? = 0
        ORDER BY a.timestamp DESC
        LIMIT 100
    """, (current_user.id, 1 if session.get('admin_logged_in') else 0))
    logs = []
    for r in cur.fetchall():
        old_vals = json.loads(r[5]) if r[5] else {}
        new_vals = json.loads(r[6]) if r[6] else {}
        logs.append({
            'id': r[0],
            'user': r[1],
            'action': r[2],
            'entity': f"{r[3]} #{r[4]}",
            'old': old_vals,
            'new': new_vals,
            'timestamp': format_date(r[7]),
            'ip': r[8]
        })
    con.close()
    return _render(T_AUDIT_REPORT, logs=logs)

@app.route("/download/<int:aid>")
@login_required
def download_attachment(aid):
    con = db()
    cur = con.cursor()
    a = cur.execute("SELECT filename,file_data FROM attachments WHERE id=? AND user_id=?", (aid, current_user.id)).fetchone()
    con.close()
    if a:
        resp = make_response(a[1])
        resp.headers['Content-Disposition'] = f'attachment; filename={a[0]}'
        return resp
    return redirect("/")

@app.route("/delete_attachment/<int:aid>", methods=["POST"])
@login_required
def delete_attachment(aid):
    con = db()
    cur = con.cursor()
    a = cur.execute("SELECT note_id, filename FROM attachments WHERE id=? AND user_id=?", (aid, current_user.id)).fetchone()
    if a:
        log_change(cur, current_user.id, 'DELETE', 'attachment', aid, {'note_id': a[0], 'filename': a[1]}, {}, request.remote_addr)
        cur.execute("DELETE FROM attachments WHERE id=? AND user_id=?", (aid, current_user.id))
        con.commit()
        con.close()
        sync_s3_async()
        return redirect(f"/edit/{a[0]}")
    con.close()
    return redirect("/")

# --- TEMPLATES ---
STYLE_UNICORN = """
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800&display=swap');
:root {
  --rose:    #ff6eb4;
  --violet:  #c084fc;
  --sky:     #67e8f9;
  --mint:    #6ee7b7;
  --sun:     #fde68a;
  --peach:   #fdba74;
  --danger:  #f87171;
  --bg:      #1a0a2e;
  --bg2:     #2d1b4e;
  --bg3:     #3d2560;
  --border:  #6b3fa0;
  --text:    #f0e6ff;
  --radius:  14px;
  --rainbow: linear-gradient(90deg,#ff6eb4,#c084fc,#67e8f9,#6ee7b7,#fde68a,#fdba74,#ff6eb4);
}
* { box-sizing: border-box; margin: 0; padding: 0; }
html { font-size: 17px; }
body {
  background: var(--bg);
  background-image: radial-gradient(ellipse at 20% 20%, #3b1f6a 0%, transparent 60%),
                    radial-gradient(ellipse at 80% 80%, #1a3a5c 0%, transparent 60%);
  color: var(--text);
  font-family: 'Nunito', 'Segoe UI', system-ui, sans-serif;
  min-height: 100vh;
  padding-bottom: 44px;
}
a { color: var(--rose); text-decoration: none; transition: color .15s; }
a:hover { color: var(--sky); }
body::before {
  content: '';
  display: block;
  height: 3px;
  background: var(--rainbow);
  background-size: 200% 100%;
  animation: shimmer 4s linear infinite;
  position: fixed; top: 0; left: 0; width: 100%; z-index: 200;
}
@keyframes shimmer { 0%{background-position:0% 0%} 100%{background-position:200% 0%} }
@keyframes bounce { 0%,100%{transform:translateY(0)} 50%{transform:translateY(-6px)} }
@keyframes spin { from{transform:rotate(0deg)} to{transform:rotate(360deg)} }
.nav {
  background: linear-gradient(135deg, #2d1b4e 0%, #1e1040 100%);
  border-bottom: 2px solid transparent;
  border-image: var(--rainbow) 1;
  padding: 10px 20px;
  display: flex; align-items: center; gap: 6px; flex-wrap: wrap;
  position: sticky; top: 3px; z-index: 100;
}
.nav-brand {
  font-size: 1.15rem; font-weight: 800;
  background: var(--rainbow); background-size: 200% 100%;
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  background-clip: text; animation: shimmer 4s linear infinite;
  letter-spacing: 1px; margin-right: 10px;
  display: flex; align-items: center; gap: 6px;
}
.unicorn-img { width:28px;height:28px;display:inline-block;animation:bounce 2s ease-in-out infinite;filter:drop-shadow(0 0 6px var(--rose)); }
.sparkle-img { width:18px;height:18px;display:inline-block;animation:spin 3s linear infinite;filter:drop-shadow(0 0 4px var(--sun)); }
.page-unicorn { display:block;margin:0 auto 16px;width:72px;height:72px;filter:drop-shadow(0 0 12px var(--rose));animation:bounce 2s ease-in-out infinite; }
.nav a { font-size:.85rem;padding:4px 12px;border-radius:20px;border:1px solid transparent;color:var(--violet);transition:all .15s; }
.nav a:hover { background:var(--bg3);border-color:var(--violet);color:var(--sky);text-decoration:none; }
.nav .sep { color:var(--border); }
.nav .nav-logout { margin-left:auto;color:var(--danger);border-color:var(--danger);border-radius:20px;border:1px solid;padding:4px 12px; }
.nav .nav-logout:hover { background:var(--danger);color:#fff; }
.theme-select { background:var(--bg3);color:var(--violet);border:1px solid var(--border);border-radius:20px;padding:3px 8px;font-size:.8rem;cursor:pointer;font-family:inherit; }
.theme-select:focus { outline:none;border-color:var(--rose); }
.container { max-width:1100px;margin:0;padding:24px 20px; }
h2,h3 { color:var(--sun);margin-bottom:16px;font-weight:700;letter-spacing:.5px; }
h4 { color:var(--violet);margin:20px 0 10px;font-size:.9rem;text-transform:uppercase;letter-spacing:1.5px; }
.card { background:var(--bg2);border:1px solid var(--border);border-radius:var(--radius);padding:20px;margin-bottom:16px;box-shadow:0 4px 24px rgba(192,132,252,.08); }
.item-list { list-style:none; }
.item-list li { display:flex;align-items:center;gap:8px;padding:8px 12px;border-bottom:1px solid var(--border);transition:background .15s; }
.item-list li:first-child { border-top:1px solid var(--border); }
.item-list li:hover { background:var(--bg3); }
.item-list li a { flex:1;font-size:.95rem;color:var(--mint); }
.item-list li a:hover { color:var(--sky); }
.item-list .actions { display:flex;gap:6px;opacity:0;transition:opacity .15s; }
.item-list li:hover .actions { opacity:1; }
.item-list .actions a { font-size:.75rem;padding:2px 8px;border-radius:10px;border:1px solid var(--border);flex:none;color:var(--violet); }
.item-list .actions a:hover { border-color:var(--rose);color:var(--rose); }
.item-list .del { color:var(--danger)!important; }
.empty { color:var(--border);font-style:italic;padding:12px; }
label { display:block;font-size:.85rem;color:var(--violet);margin-bottom:4px;margin-top:12px; }
input[type=text],input[type=password],input[type=email],input[type=date],input:not([type]),textarea,select { background:var(--bg3);color:var(--text);border:1px solid var(--border);border-radius:10px;padding:8px 14px;font-size:.9rem;font-family:inherit;width:100%;transition:border-color .15s,box-shadow .15s;outline:none; }
input:focus,textarea:focus,select:focus { border-color:var(--rose);box-shadow:0 0 0 3px rgba(255,110,180,.15); }
textarea { resize:vertical;font-family:'Consolas','Courier New',monospace;font-size:.85rem; }
select option { background:var(--bg2); }
.form-row { display:flex;gap:12px;flex-wrap:wrap; }
.form-row > * { flex:1;min-width:200px; }
.btn { display:inline-flex;align-items:center;gap:6px;padding:8px 22px;border-radius:20px;border:1px solid var(--violet);background:transparent;color:var(--violet);font-size:.9rem;font-family:inherit;font-weight:600;cursor:pointer;transition:all .15s;text-decoration:none; }
.btn:hover { background:var(--bg3);border-color:var(--sky);color:var(--sky);text-decoration:none; }
.btn-primary { background:linear-gradient(135deg,var(--rose),var(--violet));color:#fff;border:none;font-weight:700; }
.btn-primary:hover { background:linear-gradient(135deg,var(--violet),var(--sky));color:#fff; }
.btn-danger { border-color:var(--danger);color:var(--danger); }
.btn-danger:hover { background:var(--danger);color:#fff;border-color:var(--danger); }
.btn-sm { padding:4px 14px;font-size:.8rem; }
.btn-group { display:flex;gap:10px;margin-top:20px;flex-wrap:wrap;align-items:center; }
err { display:block;color:var(--danger);background:rgba(248,113,113,.1);border:1px solid var(--danger);border-radius:10px;padding:8px 14px;margin:10px 0;font-size:.9rem; }
.breadcrumb { font-size:.85rem;color:var(--border);margin-bottom:16px;display:flex;align-items:center;gap:6px;flex-wrap:wrap; }
.breadcrumb a { color:var(--violet); }
.breadcrumb a:hover { color:var(--rose); }
.breadcrumb .sep { color:var(--border); }
.badge { font-size:.75rem;background:var(--bg3);border:1px solid var(--border);border-radius:10px;padding:1px 8px;color:var(--violet); }
.timestamp { font-size:.8rem;color:var(--border); }
table { width:100%;border-collapse:collapse;font-size:.9rem; }
th { text-align:left;padding:10px 12px;border-bottom:2px solid var(--violet);color:var(--violet);font-size:.8rem;text-transform:uppercase;letter-spacing:.5px; }
td { padding:5px 12px;vertical-align:top;border-bottom:1px solid var(--bg3); }
tr:hover td { background:var(--bg3); }
.search-box { display:flex;gap:8px;margin-bottom:20px; }
.search-box input { flex:1; }
.tag-create { color:var(--mint);font-weight:700; }
.tag-update { color:var(--sun);font-weight:700; }
.tag-delete { color:var(--danger);font-weight:700; }
.footer { position:fixed;bottom:0;left:0;width:100%;background:var(--bg2);border-top:2px solid transparent;border-image:var(--rainbow) 1;color:var(--border);text-align:center;font-size:.75rem;padding:5px;z-index:99; }
.two-col { display:grid;grid-template-columns:1fr 1fr;gap:20px; }
@media (max-width:600px) { .two-col{grid-template-columns:1fr} .nav{gap:4px} textarea{cols:unset;width:100%} }
.confirm-box { background:var(--bg2);border:1px solid var(--rose);border-radius:var(--radius);padding:24px;max-width:600px;box-shadow:0 4px 32px rgba(255,110,180,.12); }
.confirm-box p { margin-bottom:12px;line-height:1.6; }
.confirm-box .field { margin:8px 0;font-size:.9rem; }
.confirm-box .field b { color:var(--sun); }
</style>
<div class="footer">&#x1F984; built on {{ build_date }}</div>
"""

STYLE_STELLAR = """
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;600;700&family=Exo+2:wght@300;400;600&display=swap');
:root {
  --star:      #e8f4fd;
  --nebula:    #7eb8f7;
  --pulsar:    #00d4ff;
  --aurora:    #39ff8f;
  --supernova: #ff6b35;
  --danger:    #ff3d3d;
  --bg:        #020510;
  --bg2:       #060d1f;
  --bg3:       #0d1a35;
  --border:    #1a3060;
  --radius:    8px;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
html { font-size: 16px; }
body {
  background: #00010a;
  /* Andromeda galaxy — real photograph */
  background-image:
    /* Dark overlay so UI text stays readable */
    linear-gradient(rgba(0,1,10,.55), rgba(0,1,10,.55)),
    url('/static/andromeda.jpg');
  background-size: cover;
  background-position: center center;
  background-attachment: fixed;
  background-repeat: no-repeat;
  color: var(--star);
  font-family: 'Exo 2', 'Segoe UI', system-ui, sans-serif;
  min-height: 100vh;
  padding-bottom: 40px;
  position: relative;
}
body::before {
  content: '';
  position: fixed;
  inset: 0;
  background-image:
    radial-gradient(1px 1px at 10% 15%, rgba(255,255,255,.7) 0%, transparent 100%),
    radial-gradient(1px 1px at 25% 40%, rgba(200,210,255,.5) 0%, transparent 100%),
    radial-gradient(1px 1px at 40%  8%, rgba(255,255,255,.6) 0%, transparent 100%),
    radial-gradient(1px 1px at 55% 60%, rgba(180,210,255,.5) 0%, transparent 100%),
    radial-gradient(1px 1px at 70% 25%, rgba(255,255,255,.7) 0%, transparent 100%),
    radial-gradient(1px 1px at 85% 75%, rgba(200,210,255,.5) 0%, transparent 100%),
    radial-gradient(1px 1px at 15% 80%, rgba(255,255,255,.6) 0%, transparent 100%),
    radial-gradient(1px 1px at 90% 45%, rgba(180,210,255,.5) 0%, transparent 100%),
    radial-gradient(1px 1px at 35% 90%, rgba(255,255,255,.6) 0%, transparent 100%),
    radial-gradient(1px 1px at 65%  5%, rgba(200,210,255,.5) 0%, transparent 100%),
    radial-gradient(1.5px 1.5px at 48% 35%, rgba(126,184,247,.8) 0%, transparent 100%),
    radial-gradient(1.5px 1.5px at 78% 88%, rgba(126,184,247,.7) 0%, transparent 100%),
    radial-gradient(1px 1px at  5% 55%, rgba(255,255,255,.6) 0%, transparent 100%),
    radial-gradient(1px 1px at 92% 12%, rgba(255,255,255,.7) 0%, transparent 100%),
    radial-gradient(1px 1px at 30% 70%, rgba(180,210,255,.5) 0%, transparent 100%);
  pointer-events: none;
  z-index: 0;
  animation: twinkle 8s ease-in-out infinite alternate;
}
@keyframes twinkle { 0% { opacity:.5; } 50% { opacity:.9; } 100% { opacity:.6; } }
body > * { position: relative; z-index: 1; }
a { color: var(--nebula); text-decoration: none; transition: color .2s; }
a:hover { color: var(--pulsar); text-shadow: 0 0 8px var(--pulsar); }
.nav {
  background: linear-gradient(135deg, #060d1f 0%, #0a1628 100%);
  border-bottom: 1px solid var(--pulsar);
  box-shadow: 0 2px 20px rgba(0,212,255,.15);
  padding: 10px 20px;
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
  position: sticky;
  top: 0;
  z-index: 100;
}
.nav-brand {
  font-family: 'Orbitron', monospace;
  font-size: 1rem;
  font-weight: 700;
  color: var(--pulsar);
  letter-spacing: 2px;
  margin-right: 10px;
  text-shadow: 0 0 12px var(--pulsar);
}
.nav a {
  font-size: .82rem;
  padding: 4px 10px;
  border-radius: 20px;
  border: 1px solid transparent;
  color: var(--nebula);
  transition: all .2s;
}
.nav a:hover { border-color: var(--pulsar); color: var(--pulsar); background: rgba(0,212,255,.08); text-shadow: 0 0 6px var(--pulsar); text-decoration: none; }
.nav .sep { color: var(--border); }
.nav .nav-logout { margin-left: auto; color: var(--supernova); border-color: var(--supernova); border-radius: 20px; border: 1px solid; padding: 4px 12px; }
.nav .nav-logout:hover { background: var(--supernova); color: #000; text-shadow: none; }
.container { max-width: 1100px; margin: 0; padding: 24px 20px; }
h2, h3 { font-family: 'Orbitron', monospace; color: var(--pulsar); margin-bottom: 16px; font-weight: 600; letter-spacing: 1px; text-shadow: 0 0 10px rgba(0,212,255,.4); }
h4 { color: var(--nebula); margin: 20px 0 10px; font-size: .9rem; text-transform: uppercase; letter-spacing: 2px; }
.card {
  background: linear-gradient(135deg, var(--bg2) 0%, var(--bg3) 100%);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 20px;
  margin-bottom: 16px;
  box-shadow: 0 4px 24px rgba(0,212,255,.06);
}
.item-list { list-style: none; }
.item-list li {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-bottom: 1px solid var(--border);
  transition: background .2s;
}
.item-list li:first-child { border-top: 1px solid var(--border); }
.item-list li:hover { background: rgba(0,212,255,.06); box-shadow: inset 0 0 12px rgba(0,212,255,.04); }
.item-list li a { flex: 1; font-size: .95rem; color: var(--aurora); }
.item-list li a:hover { color: var(--pulsar); text-shadow: 0 0 6px var(--pulsar); }
.item-list .actions { display: flex; gap: 6px; opacity: 0; transition: opacity .15s; }
.item-list li:hover .actions { opacity: 1; }
.item-list .actions a { font-size: .75rem; padding: 2px 8px; border-radius: 12px; border: 1px solid var(--border); flex: none; color: var(--nebula); }
.item-list .actions a:hover { border-color: var(--pulsar); color: var(--pulsar); }
.item-list .del { color: var(--danger) !important; }
.empty { color: #3a5080; font-style: italic; padding: 12px; }
label { display: block; font-size: .85rem; color: var(--nebula); margin-bottom: 4px; margin-top: 12px; }
input[type=text], input[type=password], input[type=email], input[type=date], input:not([type]), textarea, select {
  background: var(--bg3);
  color: var(--star);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 8px 12px;
  font-size: .9rem;
  font-family: inherit;
  width: 100%;
  transition: border-color .2s, box-shadow .2s;
  outline: none;
}
input:focus, textarea:focus, select:focus {
  border-color: var(--pulsar);
  box-shadow: 0 0 0 3px rgba(0,212,255,.15);
}
textarea { resize: vertical; font-family: 'Consolas', 'Courier New', monospace; font-size: .85rem; }
select option { background: var(--bg2); }
.form-row { display: flex; gap: 12px; flex-wrap: wrap; }
.form-row > * { flex: 1; min-width: 200px; }
.btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 22px;
  border-radius: 20px;
  border: 1px solid var(--nebula);
  background: transparent;
  color: var(--nebula);
  font-size: .9rem;
  font-family: inherit;
  cursor: pointer;
  transition: all .2s;
  text-decoration: none;
  letter-spacing: .5px;
}
.btn:hover { background: rgba(126,184,247,.12); border-color: var(--pulsar); color: var(--pulsar); box-shadow: 0 0 14px rgba(0,212,255,.25); text-decoration: none; text-shadow: 0 0 6px var(--pulsar); }
.btn-primary {
  background: linear-gradient(135deg, #003d6b 0%, #005a9e 100%);
  color: var(--pulsar);
  border-color: var(--pulsar);
  font-weight: 600;
  box-shadow: 0 0 10px rgba(0,212,255,.2);
}
.btn-primary:hover { background: linear-gradient(135deg, #005a9e 0%, #0078d4 100%); box-shadow: 0 0 20px rgba(0,212,255,.4); color: #fff; }
.btn-danger { border-color: var(--danger); color: var(--danger); }
.btn-danger:hover { background: var(--danger); color: #fff; box-shadow: 0 0 14px rgba(255,61,61,.35); text-shadow: none; }
.btn-sm { padding: 4px 14px; font-size: .8rem; }
.btn-group { display: flex; gap: 10px; margin-top: 20px; flex-wrap: wrap; align-items: center; }
err { display: block; color: var(--danger); background: rgba(255,61,61,.08); border: 1px solid var(--danger); border-radius: var(--radius); padding: 8px 12px; margin: 10px 0; font-size: .9rem; }
.breadcrumb { font-size: .85rem; color: #3a5080; margin-bottom: 16px; display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }
.breadcrumb a { color: var(--nebula); }
.breadcrumb a:hover { color: var(--pulsar); }
.breadcrumb .sep { color: var(--border); }
.badge { font-size: .75rem; background: var(--bg3); border: 1px solid var(--border); border-radius: 10px; padding: 1px 8px; color: var(--nebula); }
.timestamp { font-size: .8rem; color: #3a5080; }
table { width: 100%; border-collapse: collapse; font-size: .9rem; }
th { text-align: left; padding: 10px 12px; border-bottom: 1px solid var(--pulsar); color: var(--nebula); font-size: .8rem; text-transform: uppercase; letter-spacing: 1px; }
td { padding: 6px 12px; vertical-align: top; border-bottom: 1px solid var(--bg3); }
tr:hover td { background: rgba(0,212,255,.04); }
.search-box { display: flex; gap: 8px; margin-bottom: 20px; }
.search-box input { flex: 1; }
.tag-create { color: var(--aurora); font-weight: 600; }
.tag-update { color: var(--nebula); font-weight: 600; }
.tag-delete { color: var(--danger); font-weight: 600; }
.footer {
  position: fixed; bottom: 0; left: 0; width: 100%;
  background: var(--bg2);
  border-top: 1px solid var(--border);
  color: #3a5080; text-align: center; font-size: .75rem; padding: 5px;
  z-index: 99;
  font-family: 'Orbitron', monospace;
  letter-spacing: 1px;
}
.two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
@media (max-width: 600px) {
  .two-col { grid-template-columns: 1fr; }
  .nav { gap: 4px; }
  textarea { cols: unset; width: 100%; }
}
.confirm-box {
  background: linear-gradient(135deg, var(--bg2) 0%, var(--bg3) 100%);
  border: 1px solid var(--supernova);
  border-radius: var(--radius);
  padding: 24px;
  max-width: 600px;
  box-shadow: 0 4px 24px rgba(255,107,53,.12);
}
.confirm-box p { margin-bottom: 12px; line-height: 1.6; }
.confirm-box .field { margin: 8px 0; font-size: .9rem; }
.confirm-box .field b { color: var(--aurora); }
.nav .theme-btn { color: var(--nebula); border: 1px solid var(--nebula); padding: 3px 9px; border-radius: 12px; font-size: .8rem; }
.nav .theme-btn:hover { background: rgba(0,212,255,.12); border-color: var(--pulsar); color: var(--pulsar); }
.theme-select { background:var(--bg3);color:var(--nebula);border:1px solid var(--border);border-radius:20px;padding:3px 8px;font-size:.8rem;cursor:pointer;font-family:inherit; }
.theme-select:focus { outline:none;border-color:var(--pulsar); }</style>
<div class="footer">&#11088; {{ build_date }} &#11088;</div>
"""

STYLE_STARTREK = """
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
@import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@400;600;700&family=Share+Tech+Mono&display=swap');
:root {
  --lcars-gold:   #ff9900;
  --lcars-blue:   #9999ff;
  --lcars-red:    #cc4444;
  --lcars-teal:   #66cccc;
  --lcars-purple: #cc88ff;
  --text:         #e8e8ff;
  --bg:           #000008;
  --bg2:          rgba(0,0,20,.75);
  --bg3:          rgba(0,0,40,.80);
  --border:       #334466;
  --radius:       4px;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
html { font-size: 16px; }
body {
  background: #000008;
  background-image:
    linear-gradient(rgba(0,0,8,.60), rgba(0,0,8,.60)),
    url('/static/startrek.jpg');
  background-size: cover;
  background-position: center center;
  background-attachment: fixed;
  background-repeat: no-repeat;
  color: var(--text);
  font-family: 'Rajdhani', 'Segoe UI', system-ui, sans-serif;
  min-height: 100vh;
  padding-bottom: 40px;
}
a { color: var(--lcars-blue); text-decoration: none; transition: color .2s; }
a:hover { color: var(--lcars-gold); text-shadow: 0 0 8px var(--lcars-gold); }
/* LCARS-style top bar */
body::before {
  content: '';
  display: block;
  height: 3px;
  background: linear-gradient(90deg, var(--lcars-red) 0%, var(--lcars-gold) 30%, var(--lcars-blue) 60%, var(--lcars-teal) 100%);
  position: fixed; top: 0; left: 0; width: 100%; z-index: 200;
}
.nav {
  background: rgba(0,0,20,.88);
  border-bottom: 2px solid var(--lcars-gold);
  padding: 10px 20px;
  display: flex; align-items: center; gap: 6px; flex-wrap: wrap;
  position: sticky; top: 3px; z-index: 100;
  font-family: 'Share Tech Mono', monospace;
}
.nav-brand {
  font-size: 1rem; font-weight: 700; letter-spacing: 3px;
  color: var(--lcars-gold); text-shadow: 0 0 10px var(--lcars-gold);
  margin-right: 10px; text-transform: uppercase;
}
.nav a { font-size:.82rem;padding:4px 10px;border-radius:2px;border:1px solid transparent;color:var(--lcars-blue);transition:all .2s;letter-spacing:.5px; }
.nav a:hover { border-color:var(--lcars-gold);color:var(--lcars-gold);background:rgba(255,153,0,.08);text-shadow:0 0 6px var(--lcars-gold);text-decoration:none; }
.nav .sep { color: var(--border); }
.nav .nav-logout { margin-left:auto;color:var(--lcars-red);border-color:var(--lcars-red);border-radius:2px;border:1px solid;padding:4px 12px; }
.nav .nav-logout:hover { background:var(--lcars-red);color:#fff;text-shadow:none; }
.container { max-width:1100px;margin:0;padding:24px 20px; }
h2,h3 { font-family:'Share Tech Mono',monospace;color:var(--lcars-gold);margin-bottom:16px;font-weight:600;letter-spacing:2px;text-transform:uppercase;text-shadow:0 0 10px rgba(255,153,0,.4); }
h4 { color:var(--lcars-teal);margin:20px 0 10px;font-size:.9rem;text-transform:uppercase;letter-spacing:2px; }
.card { background:var(--bg2);border:1px solid var(--lcars-gold);border-left:4px solid var(--lcars-gold);border-radius:var(--radius);padding:20px;margin-bottom:16px;box-shadow:0 4px 24px rgba(255,153,0,.08); }
.item-list { list-style:none; }
.item-list li { display:flex;align-items:center;gap:8px;padding:8px 12px;border-bottom:1px solid var(--border);transition:background .2s; }
.item-list li:first-child { border-top:1px solid var(--border); }
.item-list li:hover { background:rgba(255,153,0,.06); }
.item-list li a { flex:1;font-size:.95rem;color:var(--lcars-teal); }
.item-list li a:hover { color:var(--lcars-gold);text-shadow:0 0 6px var(--lcars-gold); }
.item-list .actions { display:flex;gap:6px;opacity:0;transition:opacity .15s; }
.item-list li:hover .actions { opacity:1; }
.item-list .actions a { font-size:.75rem;padding:2px 8px;border-radius:2px;border:1px solid var(--border);flex:none;color:var(--lcars-blue); }
.item-list .actions a:hover { border-color:var(--lcars-gold);color:var(--lcars-gold); }
.item-list .del { color:var(--lcars-red)!important; }
.empty { color:var(--border);font-style:italic;padding:12px; }
label { display:block;font-size:.85rem;color:var(--lcars-teal);margin-bottom:4px;margin-top:12px;letter-spacing:.5px;text-transform:uppercase; }
input[type=text],input[type=password],input[type=email],input[type=date],input:not([type]),textarea,select { background:var(--bg3);color:var(--text);border:1px solid var(--border);border-radius:var(--radius);padding:8px 12px;font-size:.9rem;font-family:inherit;width:100%;transition:border-color .2s,box-shadow .2s;outline:none; }
input:focus,textarea:focus,select:focus { border-color:var(--lcars-gold);box-shadow:0 0 0 3px rgba(255,153,0,.15); }
textarea { resize:vertical;font-family:'Share Tech Mono',monospace;font-size:.85rem; }
select option { background:var(--bg); }
.form-row { display:flex;gap:12px;flex-wrap:wrap; }
.form-row > * { flex:1;min-width:200px; }
.btn { display:inline-flex;align-items:center;gap:6px;padding:8px 22px;border-radius:2px;border:1px solid var(--lcars-blue);background:transparent;color:var(--lcars-blue);font-size:.9rem;font-family:inherit;cursor:pointer;transition:all .2s;text-decoration:none;letter-spacing:1px;text-transform:uppercase; }
.btn:hover { background:rgba(153,153,255,.12);border-color:var(--lcars-gold);color:var(--lcars-gold);box-shadow:0 0 14px rgba(255,153,0,.25);text-decoration:none;text-shadow:0 0 6px var(--lcars-gold); }
.btn-primary { background:rgba(255,153,0,.15);color:var(--lcars-gold);border-color:var(--lcars-gold);font-weight:600;box-shadow:0 0 10px rgba(255,153,0,.2); }
.btn-primary:hover { background:rgba(255,153,0,.28);box-shadow:0 0 20px rgba(255,153,0,.4);color:#fff; }
.btn-danger { border-color:var(--lcars-red);color:var(--lcars-red); }
.btn-danger:hover { background:var(--lcars-red);color:#fff;box-shadow:0 0 14px rgba(204,68,68,.35);text-shadow:none; }
.btn-sm { padding:4px 14px;font-size:.8rem; }
.btn-group { display:flex;gap:10px;margin-top:20px;flex-wrap:wrap;align-items:center; }
err { display:block;color:var(--lcars-red);background:rgba(204,68,68,.08);border:1px solid var(--lcars-red);border-radius:var(--radius);padding:8px 12px;margin:10px 0;font-size:.9rem; }
.breadcrumb { font-size:.85rem;color:var(--border);margin-bottom:16px;display:flex;align-items:center;gap:6px;flex-wrap:wrap; }
.breadcrumb a { color:var(--lcars-blue); }
.breadcrumb a:hover { color:var(--lcars-gold); }
.breadcrumb .sep { color:var(--border); }
.badge { font-size:.75rem;background:var(--bg3);border:1px solid var(--border);border-radius:2px;padding:1px 8px;color:var(--lcars-teal); }
.timestamp { font-size:.8rem;color:var(--border); }
table { width:100%;border-collapse:collapse;font-size:.9rem; }
th { text-align:left;padding:10px 12px;border-bottom:1px solid var(--lcars-gold);color:var(--lcars-teal);font-size:.8rem;text-transform:uppercase;letter-spacing:1px;font-family:'Share Tech Mono',monospace; }
td { padding:6px 12px;vertical-align:top;border-bottom:1px solid var(--bg3); }
tr:hover td { background:rgba(255,153,0,.04); }
.search-box { display:flex;gap:8px;margin-bottom:20px; }
.search-box input { flex:1; }
.tag-create { color:var(--lcars-teal);font-weight:600; }
.tag-update { color:var(--lcars-blue);font-weight:600; }
.tag-delete { color:var(--lcars-red);font-weight:600; }
.footer { position:fixed;bottom:0;left:0;width:100%;background:rgba(0,0,20,.90);border-top:1px solid var(--lcars-gold);color:var(--lcars-gold);text-align:center;font-size:.75rem;padding:5px;z-index:99;font-family:'Share Tech Mono',monospace;letter-spacing:2px; }
.two-col { display:grid;grid-template-columns:1fr 1fr;gap:20px; }
@media (max-width:600px) { .two-col { grid-template-columns:1fr; } .nav { gap:4px; } textarea { width:100%; } }
.confirm-box { background:var(--bg2);border:1px solid var(--lcars-gold);border-radius:var(--radius);padding:24px;max-width:600px;box-shadow:0 4px 24px rgba(255,153,0,.12); }
.confirm-box p { margin-bottom:12px;line-height:1.6; }
.confirm-box .field { margin:8px 0;font-size:.9rem; }
.confirm-box .field b { color:var(--lcars-teal); }
.theme-select { background:var(--bg3);color:var(--lcars-blue);border:1px solid var(--border);border-radius:2px;padding:3px 8px;font-size:.8rem;cursor:pointer;font-family:inherit; }
.theme-select:focus { outline:none;border-color:var(--lcars-gold); }</style>
<div class="footer">&#9650; {{ build_date }} &#9650;</div>
"""

# Keep STYLE as an alias so error handlers that reference it still work
STYLE = STYLE_STELLAR

STYLE_LOTR = """
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
@import url('https://fonts.googleapis.com/css2?family=IM+Fell+English:ital@0;1&family=Cinzel+Decorative:wght@400;700&family=Uncial+Antiqua&display=swap');
:root {
  --gold:     #c9a84c;
  --gold2:    #e8c97a;
  --silver:   #a8b8c8;
  --shadow:   #1a0a00;
  --ember:    #8b2500;
  --mithril:  #d4e0ec;
  --shire:    #4a7c3f;
  --danger:   #8b0000;
  --bg:       #0a0500;
  --bg2:      #120a02;
  --bg3:      #1a1005;
  --border:   #3a2a10;
  --radius:   2px;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
html { font-size: 16px; }
body {
  background: var(--bg);
  background-image:
    linear-gradient(rgba(10,5,0,.65), rgba(10,5,0,.65)),
    url('/static/lotr.jpg');
  background-size: cover;
  background-position: center center;
  background-attachment: fixed;
  background-repeat: no-repeat;
  color: var(--mithril);
  font-family: 'IM Fell English', Georgia, serif;
  min-height: 100vh;
  padding-bottom: 40px;
}
a { color: var(--gold); text-decoration: none; transition: color .2s; }
a:hover { color: var(--gold2); text-shadow: 0 0 8px rgba(201,168,76,.6); }
.nav {
  background: linear-gradient(135deg, rgba(10,5,0,.95) 0%, rgba(26,16,5,.95) 100%);
  border-bottom: 2px solid var(--gold);
  box-shadow: 0 2px 20px rgba(201,168,76,.2);
  padding: 10px 20px;
  display: flex; align-items: center; gap: 6px; flex-wrap: wrap;
  position: sticky; top: 0; z-index: 100;
}
.nav-brand {
  font-family: 'Cinzel Decorative', serif;
  font-size: .9rem; font-weight: 700;
  color: var(--gold);
  text-shadow: 0 0 14px rgba(201,168,76,.7), 0 2px 4px rgba(0,0,0,.9);
  letter-spacing: 2px; margin-right: 10px;
}
.nav a { font-size:.82rem;padding:4px 10px;border-radius:1px;border:1px solid transparent;color:var(--silver);transition:all .2s;font-family:'IM Fell English',serif; }
.nav a:hover { border-color:var(--gold);color:var(--gold);background:rgba(201,168,76,.08);text-shadow:0 0 6px rgba(201,168,76,.4);text-decoration:none; }
.nav .sep { color:var(--border); }
.nav .nav-logout { margin-left:auto;color:var(--danger);border-color:var(--danger);border-radius:1px;border:1px solid;padding:4px 12px; }
.nav .nav-logout:hover { background:var(--danger);color:var(--mithril);text-shadow:none; }
.container { max-width:1100px;margin:0;padding:24px 20px; }
h2,h3 { font-family:'Cinzel Decorative',serif;color:var(--gold);margin-bottom:16px;font-weight:700;letter-spacing:1px;text-shadow:0 0 12px rgba(201,168,76,.4); }
h4 { color:var(--silver);margin:20px 0 10px;font-size:.85rem;text-transform:uppercase;letter-spacing:2px;font-family:'Cinzel Decorative',serif; }
.card {
  background: linear-gradient(135deg, rgba(18,10,2,.88) 0%, rgba(26,16,5,.88) 100%);
  border: 1px solid var(--border);
  border-top: 2px solid var(--gold);
  border-radius: var(--radius);
  padding: 20px; margin-bottom: 16px;
  box-shadow: 0 4px 24px rgba(0,0,0,.6), inset 0 1px 0 rgba(201,168,76,.1);
}
.item-list { list-style:none; }
.item-list li { display:flex;align-items:center;gap:8px;padding:8px 12px;border-bottom:1px solid var(--border);transition:background .2s; }
.item-list li:first-child { border-top:1px solid var(--border); }
.item-list li:hover { background:rgba(201,168,76,.06); }
.item-list li a { flex:1;font-size:.95rem;color:var(--gold2); }
.item-list li a:hover { color:var(--gold);text-shadow:0 0 6px rgba(201,168,76,.4); }
.item-list .actions { display:flex;gap:6px;opacity:0;transition:opacity .15s; }
.item-list li:hover .actions { opacity:1; }
.item-list .actions a { font-size:.75rem;padding:2px 8px;border-radius:1px;border:1px solid var(--border);flex:none;color:var(--silver); }
.item-list .actions a:hover { border-color:var(--gold);color:var(--gold); }
.item-list .del { color:var(--danger)!important; }
.empty { color:var(--border);font-style:italic;padding:12px; }
label { display:block;font-size:.82rem;color:var(--silver);margin-bottom:4px;margin-top:12px;letter-spacing:.5px;text-transform:uppercase;font-family:'Cinzel Decorative',serif; }
input[type=text],input[type=password],input[type=email],input[type=date],input:not([type]),textarea,select {
  background:rgba(18,10,2,.9);color:var(--mithril);border:1px solid var(--border);
  border-radius:var(--radius);padding:8px 12px;font-size:.9rem;font-family:'IM Fell English',serif;
  width:100%;transition:border-color .2s,box-shadow .2s;outline:none;
}
input:focus,textarea:focus,select:focus { border-color:var(--gold);box-shadow:0 0 0 3px rgba(201,168,76,.15); }
textarea { resize:vertical;font-family:'IM Fell English',serif;font-size:.9rem; }
select option { background:var(--bg2); }
.form-row { display:flex;gap:12px;flex-wrap:wrap; }
.form-row > * { flex:1;min-width:200px; }
.btn { display:inline-flex;align-items:center;gap:6px;padding:8px 22px;border-radius:1px;border:1px solid var(--gold);background:transparent;color:var(--gold);font-size:.9rem;font-family:'IM Fell English',serif;cursor:pointer;transition:all .2s;text-decoration:none;letter-spacing:.5px; }
.btn:hover { background:rgba(201,168,76,.1);border-color:var(--gold2);color:var(--gold2);box-shadow:0 0 14px rgba(201,168,76,.2);text-decoration:none; }
.btn-primary { background:rgba(201,168,76,.15);color:var(--gold2);border-color:var(--gold);font-weight:600;box-shadow:0 0 10px rgba(201,168,76,.15); }
.btn-primary:hover { background:rgba(201,168,76,.28);box-shadow:0 0 20px rgba(201,168,76,.35);color:#fff; }
.btn-danger { border-color:var(--danger);color:var(--danger); }
.btn-danger:hover { background:var(--danger);color:var(--mithril);box-shadow:0 0 14px rgba(139,0,0,.4);text-shadow:none; }
.btn-sm { padding:4px 14px;font-size:.8rem; }
.btn-group { display:flex;gap:10px;margin-top:20px;flex-wrap:wrap;align-items:center; }
err { display:block;color:var(--danger);background:rgba(139,0,0,.08);border:1px solid var(--danger);border-radius:var(--radius);padding:8px 12px;margin:10px 0;font-size:.9rem; }
.breadcrumb { font-size:.85rem;color:var(--border);margin-bottom:16px;display:flex;align-items:center;gap:6px;flex-wrap:wrap; }
.breadcrumb a { color:var(--silver); }
.breadcrumb a:hover { color:var(--gold); }
.breadcrumb .sep { color:var(--border); }
.badge { font-size:.75rem;background:var(--bg3);border:1px solid var(--border);border-radius:1px;padding:1px 8px;color:var(--silver); }
.timestamp { font-size:.8rem;color:var(--border); }
table { width:100%;border-collapse:collapse;font-size:.9rem; }
th { text-align:left;padding:10px 12px;border-bottom:1px solid var(--gold);color:var(--silver);font-size:.8rem;text-transform:uppercase;letter-spacing:1px;font-family:'Cinzel Decorative',serif; }
td { padding:6px 12px;vertical-align:top;border-bottom:1px solid var(--bg3); }
tr:hover td { background:rgba(201,168,76,.04); }
.search-box { display:flex;gap:8px;margin-bottom:20px; }
.search-box input { flex:1; }
.tag-create { color:var(--shire);font-weight:600; }
.tag-update { color:var(--silver);font-weight:600; }
.tag-delete { color:var(--danger);font-weight:600; }
.footer { position:fixed;bottom:0;left:0;width:100%;background:rgba(10,5,0,.95);border-top:1px solid var(--gold);color:var(--gold);text-align:center;font-size:.75rem;padding:5px;z-index:99;font-family:'Cinzel Decorative',serif;letter-spacing:2px; }
.two-col { display:grid;grid-template-columns:1fr 1fr;gap:20px; }
@media (max-width:600px) { .two-col { grid-template-columns:1fr; } .nav { gap:4px; } textarea { width:100%; } }
.confirm-box { background:rgba(18,10,2,.92);border:1px solid var(--gold);border-radius:var(--radius);padding:24px;max-width:600px;box-shadow:0 4px 24px rgba(0,0,0,.7); }
.confirm-box p { margin-bottom:12px;line-height:1.6; }
.confirm-box .field { margin:8px 0;font-size:.9rem; }
.confirm-box .field b { color:var(--gold2); }
.theme-select { background:rgba(18,10,2,.9);color:var(--gold);border:1px solid var(--border);border-radius:1px;padding:3px 8px;font-size:.8rem;cursor:pointer;font-family:'IM Fell English',serif; }
.theme-select:focus { outline:none;border-color:var(--gold); }</style>
<div class="footer">&#9770; {{ build_date }} &#9770;</div>
"""

STYLE_SHREK = """
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
@import url('https://fonts.googleapis.com/css2?family=MedievalSharp&family=Cinzel:wght@400;600&family=Lora:wght@400;600&display=swap');
:root {
  --swamp:    #4a7c3f;
  --mud:      #8b6914;
  --onion:    #c8a84b;
  --slime:    #7ec850;
  --mist:     #a8c878;
  --parchment:#f5e6c8;
  --dark:     #1a2e0a;
  --bark:     #3d2b1f;
  --danger:   #c0392b;
  --bg:       #0d1a08;
  --bg2:      #162410;
  --bg3:      #1e3015;
  --border:   #3a5a2a;
  --radius:   4px;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
html { font-size: 16px; }
body {
  background: var(--bg);
  background-image:
    /* Swamp mist layers */
    radial-gradient(ellipse 120% 40% at 50% 100%, rgba(74,124,63,.25) 0%, transparent 70%),
    radial-gradient(ellipse 80% 30% at 20% 80%, rgba(126,200,80,.12) 0%, transparent 60%),
    radial-gradient(ellipse 60% 20% at 80% 90%, rgba(74,124,63,.15) 0%, transparent 50%),
    /* Night sky */
    radial-gradient(ellipse 200% 60% at 50% 0%, #0a1505 0%, #0d1a08 100%);
  color: var(--parchment);
  font-family: 'Lora', Georgia, serif;
  min-height: 100vh;
  padding-bottom: 40px;
  position: relative;
  overflow-x: hidden;
}
/* Fireflies */
body::before {
  content: '✦ ✧ ✦ ✧ ✦ ✧ ✦ ✧ ✦ ✧ ✦';
  position: fixed;
  top: 15%;
  left: 0;
  width: 100%;
  color: rgba(200,168,75,.4);
  font-size: .6rem;
  letter-spacing: 3rem;
  pointer-events: none;
  z-index: 0;
  animation: fireflies 8s ease-in-out infinite alternate;
}
body::after {
  content: '✧ ✦ ✧ ✦ ✧ ✦ ✧ ✦ ✧';
  position: fixed;
  top: 60%;
  left: 5%;
  width: 100%;
  color: rgba(126,200,80,.3);
  font-size: .5rem;
  letter-spacing: 4rem;
  pointer-events: none;
  z-index: 0;
  animation: fireflies 6s ease-in-out infinite alternate-reverse;
}
@keyframes fireflies {
  0%   { opacity: .2; transform: translateY(0px); }
  50%  { opacity: .8; transform: translateY(-8px); }
  100% { opacity: .3; transform: translateY(4px); }
}
body > * { position: relative; z-index: 1; }
a { color: var(--slime); text-decoration: none; transition: color .2s; }
a:hover { color: var(--onion); text-shadow: 0 0 8px rgba(200,168,75,.5); }
/* Swamp mud top border */
.nav {
  background: linear-gradient(135deg, #0d1a08 0%, #162410 100%);
  border-bottom: 3px solid var(--mud);
  box-shadow: 0 3px 20px rgba(74,124,63,.3), inset 0 -1px 0 var(--swamp);
  padding: 10px 20px;
  display: flex; align-items: center; gap: 6px; flex-wrap: wrap;
  position: sticky; top: 0; z-index: 100;
}
.nav-brand {
  font-family: 'Cinzel', serif;
  font-size: 1rem; font-weight: 600;
  color: var(--onion);
  text-shadow: 0 0 12px rgba(200,168,75,.6), 0 2px 4px rgba(0,0,0,.8);
  letter-spacing: 2px; margin-right: 10px;
  text-transform: uppercase;
}
.nav a { font-size:.82rem;padding:4px 10px;border-radius:2px;border:1px solid transparent;color:var(--mist);transition:all .2s;font-family:'Lora',serif; }
.nav a:hover { border-color:var(--swamp);color:var(--onion);background:rgba(74,124,63,.15);text-shadow:0 0 6px rgba(200,168,75,.4);text-decoration:none; }
.nav .sep { color:var(--border); }
.nav .nav-logout { margin-left:auto;color:var(--danger);border-color:var(--danger);border-radius:2px;border:1px solid;padding:4px 12px; }
.nav .nav-logout:hover { background:var(--danger);color:#fff;text-shadow:none; }
.container { max-width:1100px;margin:0;padding:24px 20px; }
h2,h3 { font-family:'Cinzel',serif;color:var(--onion);margin-bottom:16px;font-weight:600;letter-spacing:1px;text-shadow:0 0 10px rgba(200,168,75,.3); }
h4 { color:var(--mist);margin:20px 0 10px;font-size:.9rem;text-transform:uppercase;letter-spacing:2px;font-family:'Cinzel',serif; }
.card {
  background: linear-gradient(135deg, var(--bg2) 0%, var(--bg3) 100%);
  border: 1px solid var(--border);
  border-left: 4px solid var(--swamp);
  border-radius: var(--radius);
  padding: 20px; margin-bottom: 16px;
  box-shadow: 0 4px 24px rgba(74,124,63,.1);
}
.item-list { list-style:none; }
.item-list li { display:flex;align-items:center;gap:8px;padding:8px 12px;border-bottom:1px solid var(--border);transition:background .2s; }
.item-list li:first-child { border-top:1px solid var(--border); }
.item-list li:hover { background:rgba(74,124,63,.1); }
.item-list li a { flex:1;font-size:.95rem;color:var(--slime); }
.item-list li a:hover { color:var(--onion); }
.item-list .actions { display:flex;gap:6px;opacity:0;transition:opacity .15s; }
.item-list li:hover .actions { opacity:1; }
.item-list .actions a { font-size:.75rem;padding:2px 8px;border-radius:2px;border:1px solid var(--border);flex:none;color:var(--mist); }
.item-list .actions a:hover { border-color:var(--onion);color:var(--onion); }
.item-list .del { color:var(--danger)!important; }
.empty { color:var(--border);font-style:italic;padding:12px;font-family:'Lora',serif; }
label { display:block;font-size:.82rem;color:var(--mist);margin-bottom:4px;margin-top:12px;letter-spacing:.5px;text-transform:uppercase;font-family:'Cinzel',serif; }
input[type=text],input[type=password],input[type=email],input[type=date],input:not([type]),textarea,select {
  background:var(--bg3);color:var(--parchment);border:1px solid var(--border);
  border-radius:var(--radius);padding:8px 12px;font-size:.9rem;font-family:'Lora',serif;
  width:100%;transition:border-color .2s,box-shadow .2s;outline:none;
}
input:focus,textarea:focus,select:focus { border-color:var(--swamp);box-shadow:0 0 0 3px rgba(74,124,63,.2); }
textarea { resize:vertical;font-family:'Lora',serif;font-size:.9rem; }
select option { background:var(--bg2); }
.form-row { display:flex;gap:12px;flex-wrap:wrap; }
.form-row > * { flex:1;min-width:200px; }
.btn { display:inline-flex;align-items:center;gap:6px;padding:8px 22px;border-radius:2px;border:1px solid var(--swamp);background:transparent;color:var(--mist);font-size:.9rem;font-family:'Lora',serif;cursor:pointer;transition:all .2s;text-decoration:none;letter-spacing:.5px; }
.btn:hover { background:rgba(74,124,63,.15);border-color:var(--onion);color:var(--onion);box-shadow:0 0 14px rgba(200,168,75,.2);text-decoration:none; }
.btn-primary { background:rgba(74,124,63,.2);color:var(--onion);border-color:var(--mud);font-weight:600;box-shadow:0 0 10px rgba(74,124,63,.15); }
.btn-primary:hover { background:rgba(74,124,63,.35);box-shadow:0 0 20px rgba(200,168,75,.3);color:var(--parchment); }
.btn-danger { border-color:var(--danger);color:var(--danger); }
.btn-danger:hover { background:var(--danger);color:#fff;box-shadow:0 0 14px rgba(192,57,43,.35);text-shadow:none; }
.btn-sm { padding:4px 14px;font-size:.8rem; }
.btn-group { display:flex;gap:10px;margin-top:20px;flex-wrap:wrap;align-items:center; }
err { display:block;color:var(--danger);background:rgba(192,57,43,.08);border:1px solid var(--danger);border-radius:var(--radius);padding:8px 12px;margin:10px 0;font-size:.9rem; }
.breadcrumb { font-size:.85rem;color:var(--border);margin-bottom:16px;display:flex;align-items:center;gap:6px;flex-wrap:wrap; }
.breadcrumb a { color:var(--mist); }
.breadcrumb a:hover { color:var(--onion); }
.breadcrumb .sep { color:var(--border); }
.badge { font-size:.75rem;background:var(--bg3);border:1px solid var(--border);border-radius:2px;padding:1px 8px;color:var(--mist); }
.timestamp { font-size:.8rem;color:var(--border); }
table { width:100%;border-collapse:collapse;font-size:.9rem; }
th { text-align:left;padding:10px 12px;border-bottom:1px solid var(--mud);color:var(--mist);font-size:.8rem;text-transform:uppercase;letter-spacing:1px;font-family:'Cinzel',serif; }
td { padding:6px 12px;vertical-align:top;border-bottom:1px solid var(--bg3); }
tr:hover td { background:rgba(74,124,63,.06); }
.search-box { display:flex;gap:8px;margin-bottom:20px; }
.search-box input { flex:1; }
.tag-create { color:var(--slime);font-weight:600; }
.tag-update { color:var(--mist);font-weight:600; }
.tag-delete { color:var(--danger);font-weight:600; }
.footer { position:fixed;bottom:0;left:0;width:100%;background:var(--bg2);border-top:2px solid var(--mud);color:var(--border);text-align:center;font-size:.75rem;padding:5px;z-index:99;font-family:'Cinzel',serif;letter-spacing:1px; }
.two-col { display:grid;grid-template-columns:1fr 1fr;gap:20px; }
@media (max-width:600px) { .two-col { grid-template-columns:1fr; } .nav { gap:4px; } textarea { width:100%; } }
.confirm-box { background:var(--bg2);border:1px solid var(--mud);border-radius:var(--radius);padding:24px;max-width:600px;box-shadow:0 4px 24px rgba(74,124,63,.12); }
.confirm-box p { margin-bottom:12px;line-height:1.6; }
.confirm-box .field { margin:8px 0;font-size:.9rem; }
.confirm-box .field b { color:var(--slime); }
.theme-select { background:var(--bg3);color:var(--mist);border:1px solid var(--border);border-radius:2px;padding:3px 8px;font-size:.8rem;cursor:pointer;font-family:'Lora',serif; }
.theme-select:focus { outline:none;border-color:var(--swamp); }</style>
<div class="footer">&#127807; {{ build_date }} &#127807;</div>
"""

def _get_style():
    """Return the CSS block for the current user's theme (reads Flask session)."""
    t = session.get('theme', 'stellar')
    if t == 'unicorn':   return STYLE_UNICORN
    if t == 'startrek':  return STYLE_STARTREK
    if t == 'shrek':     return STYLE_SHREK
    if t == 'lotr':      return STYLE_LOTR
    return STYLE_STELLAR

def _render(template, **kwargs):
    """Swap STYLE_STELLAR for the user's chosen theme, then render.
    Also injects theme, build_date, and S3 status so Jinja2 variables resolve."""
    theme = session.get('theme', 'stellar')
    themed = template.replace(STYLE_STELLAR, _get_style())
    kwargs.setdefault('theme', theme)
    kwargs.setdefault('build_date', BUILD_DATE)
    # Inject S3 status so every page can show the alert banner
    s3 = get_s3_status()
    kwargs.setdefault('s3_ok', s3['ok'])
    kwargs.setdefault('s3_error', s3['error'])
    # Prepend S3 warning banner when sync has failed
    if s3['ok'] is False:
        banner = (
            '<div style="background:#7f1d1d;color:#fca5a5;padding:8px 20px;'
            'font-size:.85rem;text-align:center;position:sticky;top:0;z-index:999;">'
            '&#9888; S3 Sync unavailable — running on local database only. '
            f'Error: {s3["error"]}</div>'
        )
        themed = themed.replace('<nav ', banner + '<nav ', 1)
    elif s3['ok'] is None and not S3_BUCKET_NAME:
        banner = (
            '<div style="background:#1e3a5f;color:#93c5fd;padding:8px 20px;'
            'font-size:.85rem;text-align:center;position:sticky;top:0;z-index:999;">'
            '&#8505; S3 sync not configured — set S3_BUCKET_NAME in .env to enable cloud backup.</div>'
        )
        themed = themed.replace('<nav ', banner + '<nav ', 1)
    if _MIXED_ENCRYPTION_WARNING:
        enc_banner = (
            '<div style="background:#78350f;color:#fde68a;padding:8px 20px;'
            'font-size:.85rem;text-align:center;position:sticky;top:0;z-index:998;">'
            '&#9888; Mixed encryption state — some notes are plaintext. '
            'Run: <code>python Scripts/migrate_encrypt.py</code></div>'
        )
        themed = themed.replace('<nav ', enc_banner + '<nav ', 1)
    return render_template_string(themed, **kwargs)

T_FOLDERS = STYLE + """
<nav class="nav">
  <span class="nav-brand">&#11088; EverNothing</span>
  <a href=/folder/add>+ Folder</a>
  <a href=/export>Export</a>
  <a href=/audit_report>Audit</a>
  <a href=/sessions>Sessions</a>
  <a href=/change_password>Password</a>
  <form action="/set_theme" method="get" style="display:inline">
    <select name="t" class="theme-select" onchange="this.form.submit()" title="Switch theme">
      <option value="stellar" {% if theme != "unicorn" %}selected="selected"{% endif %}>&#11088; Stellar</option>
      <option value="unicorn" {% if theme == "unicorn" %}selected="selected"{% endif %}>&#x1F984; Unicorn</option>
      <option value="startrek" {% if theme == "startrek" %}selected="selected"{% endif %}>&#x1F596; Star Trek</option>
      <option value="shrek" {% if theme == "shrek" %}selected="selected"{% endif %}>&#127807; Shrek</option>
      <option value="lotr" {% if theme == "lotr" %}selected="selected"{% endif %}>&#9770; LOTR</option>
    </select>
  </form>
  <a href=/logout class="nav-logout">Logout</a>
</nav>
<div class="container">
  <div class="search-box">
    <form action="/search" method="get" style="display:flex;gap:8px;width:100%">
      <input name="q" placeholder="Search notes..." style="flex:1">
      <button class="btn btn-primary">Search</button>
    </form>
  </div>
  <div class="two-col">
    <div>
      <h4>Folders</h4>
      <ul class="item-list">
      {% for f in folders %}
      <li>
        <a href=/folder/{{f[0]}}>&#128193; {{f[1]}}</a>
        <span class="actions">
          <a href=/folder/rename/{{f[0]}}>rename</a>
          <a href=/folder/delete/{{f[0]}} class="del">delete</a>
        </span>
      </li>
      {% else %}
      <li class="empty">No folders yet. <a href=/folder/add>Create one</a></li>
      {% endfor %}
      </ul>
    </div>
    <div>
      <h4>Recently Edited</h4>
      <ul class="item-list">
      {% for n in recent %}
      <li>
        <a href=/edit/{{n[0]}}>{{n[1]}}</a>
        <span class="timestamp">{{n[2]}}</span>
      </li>
      {% else %}
      <li class="empty">No notes yet.</li>
      {% endfor %}
      </ul>
    </div>
  </div>
</div>
"""

T_ADD_FOLDER = STYLE + """
<nav class="nav">
  <span class="nav-brand">&#11088; EverNothing</span>
  <a href=/>Home</a>
  <form action="/set_theme" method="get" style="display:inline">
    <select name="t" class="theme-select" onchange="this.form.submit()" title="Switch theme">
      <option value="stellar" {% if theme != "unicorn" %}selected="selected"{% endif %}>&#11088; Stellar</option>
      <option value="unicorn" {% if theme == "unicorn" %}selected="selected"{% endif %}>&#x1F984; Unicorn</option>
      <option value="startrek" {% if theme == "startrek" %}selected="selected"{% endif %}>&#x1F596; Star Trek</option>
      <option value="shrek" {% if theme == "shrek" %}selected="selected"{% endif %}>&#127807; Shrek</option>
      <option value="lotr" {% if theme == "lotr" %}selected="selected"{% endif %}>&#9770; LOTR</option>
    </select>
  </form>
  <a href=/logout class="nav-logout">Logout</a>
</nav>
<div class="container">
  <h3>Create Folder</h3>
  {% if error %}<err>{{error}}</err>{% endif %}
  <div class="card" style="max-width:480px">
    <form method=post>
      <input type=hidden name=csrf_token value="{{ csrf_token() }}">
      <label>Folder Name</label>
      <input name=name maxlength="255" autofocus>
      <div class="btn-group">
        <button class="btn btn-primary">Create</button>
        <a href=/ class="btn">Cancel</a>
      </div>
    </form>
  </div>
</div>
"""

T_ADD_SUBFOLDER = STYLE + """
<nav class="nav">
  <span class="nav-brand">&#11088; EverNothing</span>
  <a href=/folder/{{pid}}>Back</a>
  <form action="/set_theme" method="get" style="display:inline">
    <select name="t" class="theme-select" onchange="this.form.submit()" title="Switch theme">
      <option value="stellar" {% if theme != "unicorn" %}selected="selected"{% endif %}>&#11088; Stellar</option>
      <option value="unicorn" {% if theme == "unicorn" %}selected="selected"{% endif %}>&#x1F984; Unicorn</option>
      <option value="startrek" {% if theme == "startrek" %}selected="selected"{% endif %}>&#x1F596; Star Trek</option>
      <option value="shrek" {% if theme == "shrek" %}selected="selected"{% endif %}>&#127807; Shrek</option>
      <option value="lotr" {% if theme == "lotr" %}selected="selected"{% endif %}>&#9770; LOTR</option>
    </select>
  </form>
  <a href=/logout class="nav-logout">Logout</a>
</nav>
<div class="container">
  <h3>Create Subfolder</h3>
  <div class="card" style="max-width:480px">
    <form method=post>
      <input type=hidden name=csrf_token value="{{ csrf_token() }}">
      <label>Subfolder Name</label>
      <input name=name autofocus>
      <div class="btn-group">
        <button class="btn btn-primary">Create</button>
        <a href=/folder/{{pid}} class="btn">Cancel</a>
      </div>
    </form>
  </div>
</div>
"""

T_RENAME_FOLDER = STYLE + """
<nav class="nav">
  <span class="nav-brand">&#11088; EverNothing</span>
  <a href=/folder/{{fid}}>Back</a>
  <form action="/set_theme" method="get" style="display:inline">
    <select name="t" class="theme-select" onchange="this.form.submit()" title="Switch theme">
      <option value="stellar" {% if theme != "unicorn" %}selected="selected"{% endif %}>&#11088; Stellar</option>
      <option value="unicorn" {% if theme == "unicorn" %}selected="selected"{% endif %}>&#x1F984; Unicorn</option>
      <option value="startrek" {% if theme == "startrek" %}selected="selected"{% endif %}>&#x1F596; Star Trek</option>
      <option value="shrek" {% if theme == "shrek" %}selected="selected"{% endif %}>&#127807; Shrek</option>
      <option value="lotr" {% if theme == "lotr" %}selected="selected"{% endif %}>&#9770; LOTR</option>
    </select>
  </form>
  <a href=/logout class="nav-logout">Logout</a>
</nav>
<div class="container">
  <h3>Rename Folder</h3>
  <div class="card" style="max-width:480px">
    <form method=post>
      <input type=hidden name=csrf_token value="{{ csrf_token() }}">
      <label>New Name</label>
      <input name=name value="{{f[0]}}" autofocus>
      <div class="btn-group">
        <button class="btn btn-primary">Rename</button>
        <a href=/folder/{{fid}} class="btn">Cancel</a>
      </div>
    </form>
  </div>
</div>
"""

T_CHANGE_PASSWORD = STYLE + """
<nav class="nav">
  <span class="nav-brand">&#11088; EverNothing</span>
  <a href=/>Home</a>
  <form action="/set_theme" method="get" style="display:inline">
    <select name="t" class="theme-select" onchange="this.form.submit()" title="Switch theme">
      <option value="stellar" {% if theme != "unicorn" %}selected="selected"{% endif %}>&#11088; Stellar</option>
      <option value="unicorn" {% if theme == "unicorn" %}selected="selected"{% endif %}>&#x1F984; Unicorn</option>
      <option value="startrek" {% if theme == "startrek" %}selected="selected"{% endif %}>&#x1F596; Star Trek</option>
      <option value="shrek" {% if theme == "shrek" %}selected="selected"{% endif %}>&#127807; Shrek</option>
      <option value="lotr" {% if theme == "lotr" %}selected="selected"{% endif %}>&#9770; LOTR</option>
    </select>
  </form>
  <a href=/logout class="nav-logout">Logout</a>
</nav>
<div class="container">
  <h3>Change Password</h3>
  {% if error %}<err>{{error}}</err>{% endif %}
  <div class="card" style="max-width:480px">
    <form method=post>
      <input type=hidden name=csrf_token value="{{ csrf_token() }}">
      <label>Current Password</label>
      <div style="position:relative">
        <input type=password name=old_password id=old_password autofocus style="padding-right:70px">
        <a href="#" onclick="toggleVis('old_password',this);return false;" style="position:absolute;right:10px;top:50%;transform:translateY(-50%);font-size:.8rem;color:var(--gold-dim)">Show</a>
      </div>
      <label>New Password</label>
      <div style="position:relative">
        <input type=password name=new_password id=new_password style="padding-right:70px">
        <a href="#" onclick="toggleVis('new_password',this);return false;" style="position:absolute;right:10px;top:50%;transform:translateY(-50%);font-size:.8rem;color:var(--gold-dim)">Show</a>
      </div>
      <label>Verify New Password</label>
      <div style="position:relative">
        <input type=password name=verify_password id=verify_password style="padding-right:70px">
        <a href="#" onclick="toggleVis('verify_password',this);return false;" style="position:absolute;right:10px;top:50%;transform:translateY(-50%);font-size:.8rem;color:var(--gold-dim)">Show</a>
      </div>
      <div class="btn-group">
        <button class="btn btn-primary">Change Password</button>
        <a href=/ class="btn">Cancel</a>
      </div>
    </form>
  </div>
</div>
<script>
function toggleVis(id, link) {
  var el = document.getElementById(id);
  if (el.type === 'password') { el.type = 'text'; link.textContent = 'Hide'; }
  else { el.type = 'password'; link.textContent = 'Show'; }
}
</script>
"""

T_DELETE_NOTE = STYLE + """
<nav class="nav">
  <span class="nav-brand">&#11088; EverNothing</span>
  <a href=/>Home</a>
  <form action="/set_theme" method="get" style="display:inline">
    <select name="t" class="theme-select" onchange="this.form.submit()" title="Switch theme">
      <option value="stellar" {% if theme != "unicorn" %}selected="selected"{% endif %}>&#11088; Stellar</option>
      <option value="unicorn" {% if theme == "unicorn" %}selected="selected"{% endif %}>&#x1F984; Unicorn</option>
      <option value="startrek" {% if theme == "startrek" %}selected="selected"{% endif %}>&#x1F596; Star Trek</option>
      <option value="shrek" {% if theme == "shrek" %}selected="selected"{% endif %}>&#127807; Shrek</option>
      <option value="lotr" {% if theme == "lotr" %}selected="selected"{% endif %}>&#9770; LOTR</option>
    </select>
  </form>
  <a href=/logout class="nav-logout">Logout</a>
</nav>
<div class="container">
  <div class="confirm-box">
    <h3>Delete Note</h3>
    <p>Are you sure you want to permanently delete <b>{{n[1]}}</b>?</p>
    <p style="color:#888;font-size:.85rem">This action cannot be undone.</p>
    <form method=post>
      <input type=hidden name=csrf_token value="{{ csrf_token() }}">
      <div class="btn-group">
        <button class="btn btn-danger">Yes, Delete</button>
        <a href=javascript:history.back() class="btn">Cancel</a>
      </div>
    </form>
  </div>
</div>
"""

T_EDIT_CONFIRM = STYLE + """
<nav class="nav">
  <span class="nav-brand">&#11088; EverNothing</span>
  <a href=/>Home</a>
  <form action="/set_theme" method="get" style="display:inline">
    <select name="t" class="theme-select" onchange="this.form.submit()" title="Switch theme">
      <option value="stellar" {% if theme != "unicorn" %}selected="selected"{% endif %}>&#11088; Stellar</option>
      <option value="unicorn" {% if theme == "unicorn" %}selected="selected"{% endif %}>&#x1F984; Unicorn</option>
      <option value="startrek" {% if theme == "startrek" %}selected="selected"{% endif %}>&#x1F596; Star Trek</option>
      <option value="shrek" {% if theme == "shrek" %}selected="selected"{% endif %}>&#127807; Shrek</option>
      <option value="lotr" {% if theme == "lotr" %}selected="selected"{% endif %}>&#9770; LOTR</option>
    </select>
  </form>
  <a href=/logout class="nav-logout">Logout</a>
</nav>
<div class="container">
  <div class="confirm-box">
    <h3>Confirm Changes</h3>
    <p>Save the following changes?</p>
    <div class="field"><b>Note:</b> {{note[0]}}</div>
    <div class="field"><b>Description:</b> {{note[4]}}</div>
    <form method=post action="/edit/{{id}}">
      <input type=hidden name=csrf_token value="{{ csrf_token() }}">
      <input type=hidden name=note value="{{note[0]}}">
      <input type=hidden name=content value="{{note[1]}}">
      <input type=hidden name=folder_id value="{{note[2]}}">
      <input type=hidden name=description value="{{note[4]}}">
      <input type=hidden name=confirm value="yes">
      <div class="btn-group">
        <button class="btn btn-primary">Yes, Save</button>
        <button type=button class="btn" onclick="history.back()">Cancel</button>
      </div>
    </form>
  </div>
</div>
"""

T_NOTES = STYLE + """
<nav class="nav">
  <span class="nav-brand">&#11088; EverNothing</span>
  <a href={% if folder[2] %}/folder/{{folder[2]}}{% else %}/{% endif %}>&#8592; Back</a>
  <a href=/add/{{folder[0]}}>+ Add Note</a>
  <a href=/folder/{{folder[0]}}/add_folder>+ Subfolder</a>
  <a href=/folder/rename/{{folder[0]}}>Rename</a>
  <a href=/folder/delete/{{folder[0]}} class="btn-danger" style="color:var(--red)">Delete Folder</a>
  <form action="/set_theme" method="get" style="display:inline">
    <select name="t" class="theme-select" onchange="this.form.submit()" title="Switch theme">
      <option value="stellar" {% if theme != "unicorn" %}selected="selected"{% endif %}>&#11088; Stellar</option>
      <option value="unicorn" {% if theme == "unicorn" %}selected="selected"{% endif %}>&#x1F984; Unicorn</option>
      <option value="startrek" {% if theme == "startrek" %}selected="selected"{% endif %}>&#x1F596; Star Trek</option>
      <option value="shrek" {% if theme == "shrek" %}selected="selected"{% endif %}>&#127807; Shrek</option>
      <option value="lotr" {% if theme == "lotr" %}selected="selected"{% endif %}>&#9770; LOTR</option>
    </select>
  </form>
  <a href=/logout class="nav-logout">Logout</a>
</nav>
<div class="container">
  <div class="breadcrumb">
    <a href="/">&#127968; Home</a>
    {% for bc_id, bc_name in breadcrumb %}
      <span class="sep">&#8250;</span>
      {% if bc_id == folder[0] %}
        <span>{{bc_name}}</span>
      {% else %}
        <a href="/folder/{{bc_id}}">{{bc_name}}</a>
      {% endif %}
    {% endfor %}
  </div>
  <div class="two-col">
    <div>
      <h4>Notes</h4>
      <ul class="item-list">
      {% for n in notes %}
      <li>
        <a href=/edit/{{n[0]}}>{{n[1]}}</a>
        <span class="actions">
          <a href=/note/delete/{{n[0]}} class="del">delete</a>
        </span>
      </li>
      {% else %}
      <li class="empty">No notes. <a href=/add/{{folder[0]}}>Add one</a></li>
      {% endfor %}
      </ul>
    </div>
    <div>
      <h4>Subfolders</h4>
      <ul class="item-list">
      {% for s in subfolders %}
      <li><a href=/folder/{{s[0]}}>&#128193; {{s[1]}}</a></li>
      {% else %}
      <li class="empty">No subfolders.</li>
      {% endfor %}
      </ul>
    </div>
  </div>
</div>
"""

T_ADD = STYLE + """
<nav class="nav">
  <span class="nav-brand">&#11088; EverNothing</span>
  <a href=/folder/{{fid}}>&#8592; Back</a>
  <form action="/set_theme" method="get" style="display:inline">
    <select name="t" class="theme-select" onchange="this.form.submit()" title="Switch theme">
      <option value="stellar" {% if theme != "unicorn" %}selected="selected"{% endif %}>&#11088; Stellar</option>
      <option value="unicorn" {% if theme == "unicorn" %}selected="selected"{% endif %}>&#x1F984; Unicorn</option>
      <option value="startrek" {% if theme == "startrek" %}selected="selected"{% endif %}>&#x1F596; Star Trek</option>
      <option value="shrek" {% if theme == "shrek" %}selected="selected"{% endif %}>&#127807; Shrek</option>
      <option value="lotr" {% if theme == "lotr" %}selected="selected"{% endif %}>&#9770; LOTR</option>
    </select>
  </form>
  <a href=/logout class="nav-logout">Logout</a>
</nav>
<div class="container">
  <h3>Add Note</h3>
  {% if error %}<err>{{error}}</err>{% endif %}
  <form method=post enctype="multipart/form-data">
    <input type=hidden name=csrf_token value="{{ csrf_token() }}">
    <div class="form-row">
      <div>
        <label>Note Title</label>
        <input name=note value="{{note}}" autofocus>
      </div>
      <div>
        <label>Description <span style="color:#555">(optional, max 255)</span></label>
        <input name=description value="{{description}}" maxlength="255">
      </div>
    </div>
    <label>Contents</label>
    <textarea name=content rows=30 cols=120>{{content}}</textarea>
    <label>Attachment <span style="color:#555">(optional)</span></label>
    <input type=file name=file style="width:auto">
    <div class="btn-group">
      <button class="btn btn-primary">Add Note</button>
      <a href=/folder/{{fid}} class="btn">Cancel</a>
    </div>
  </form>
</div>
"""

T_EDIT = STYLE + """
<nav class="nav">
  <span class="nav-brand">&#11088; EverNothing</span>
  <a href=/>Home</a>
  {% for b in breadcrumbs %}
  <span class="sep">&#8250;</span> <a href=/folder/{{b[0]}}>{{b[1]}}</a>
  {% endfor %}
  <span style="margin-left:auto;display:flex;gap:8px;align-items:center">
    <a href=/history/{{id}} class="btn btn-sm" style="color:var(--gold-dim)">History: {{note[3]}}</a>
    <a href=/note/delete/{{id}} class="btn btn-sm btn-danger">Delete</a>
    <a href=/logout class="btn btn-sm nav-logout">Logout</a>
  </span>
</nav>
<div class="container">
  {% if error %}<err>{{error}}</err>{% endif %}
  <form method=post enctype="multipart/form-data">
    <input type=hidden name=csrf_token value="{{ csrf_token() }}">
    <div class="form-row">
      <div>
        <label>Note Title</label>
        <input name=note value='{{note[0]}}'>
      </div>
      <div>
        <label>Description <span style="color:#555">(optional)</span></label>
        <input name=description value='{{note[4]}}' maxlength="255">
      </div>
    </div>
    <label>Folder</label>
    <select name=folder_id style="width:auto;min-width:200px">
    {% for f in folders %}
    <option value='{{f[0]}}' {% if f[0]==note[2] %}selected{% endif %}>{{f[1]}}</option>
    {% endfor %}
    </select>
    <label>Contents</label>
    <textarea name=content rows=30 cols=120>{{note[1]}}</textarea>
    <div class="btn-group">
      <button class="btn btn-primary">Commit</button>
      <a href=/ class="btn">Cancel</a>
    </div>
  </form>

  <h4>Attachments</h4>
  <form method=post enctype="multipart/form-data" style="display:flex;gap:8px;align-items:center;margin-bottom:12px">
    <input type=hidden name=csrf_token value="{{ csrf_token() }}">
    <input type=file name=file style="width:auto">
    <button class="btn btn-sm">Upload</button>
  </form>
  <ul class="item-list">
  {% for att in attachments %}
  <li>
    <a href=/download/{{att[0]}}>&#128206; {{att[1]}}</a>
    <span class="badge">{{att[2]}} bytes</span>
    <span class="actions" style="opacity:1">
      <form method=post action="/delete_attachment/{{att[0]}}" style="display:inline">
        <input type=hidden name=csrf_token value="{{ csrf_token() }}">
        <button class="btn btn-sm btn-danger" style="border:none;background:none;cursor:pointer;color:var(--red)">remove</button>
      </form>
    </span>
  </li>
  {% else %}
  <li class="empty">No attachments.</li>
  {% endfor %}
  </ul>
</div>
"""

T_LOGIN = STYLE + """
<div style="min-height:100vh;display:flex;align-items:center;justify-content:center">
  <div class="card" style="width:100%;max-width:400px">
    <h2 style="text-align:center;margin-bottom:4px">&#127775;EverNothing</h2>
    <p style="text-align:center;color:#666;font-size:.85rem;margin-bottom:20px">Sign in to your notes</p>
    {% if error %}<err>{{error}}</err>{% endif %}
    <form method=post autocomplete="on">
      <input type=hidden name=csrf_token value="{{ csrf_token() }}">
      <label>Username</label>
      <input name=username value="{{ last_user|default('', true) }}" autocomplete="username" {% if not last_user %}autofocus{% endif %}>
      <label>Password</label>
      <input type=password name=password autocomplete="current-password" {% if last_user %}autofocus{% endif %}>
      <label style="flex-direction:row;display:flex;align-items:center;gap:8px;margin-top:12px;cursor:pointer">
        <input type=checkbox name=remember_me style="width:auto;margin:0"> Remember me for 30 days
      </label>
      <div class="btn-group" style="margin-top:16px">
        <button class="btn btn-primary" style="flex:1;justify-content:center">Login</button>
      </div>
    </form>
    <p style="text-align:center;margin-top:16px;font-size:.85rem">
      <a href=/register>Create account</a> &nbsp;|&nbsp; <a href=/forgot_password>Forgot password?</a>
    </p>
  </div>
</div>
"""

T_REGISTER = STYLE + """
<div style="min-height:100vh;display:flex;align-items:center;justify-content:center">
  <div class="card" style="width:100%;max-width:420px">
    <h2 style="text-align:center;margin-bottom:4px">&#127775;EverNothing</h2>
    <p style="text-align:center;color:#666;font-size:.85rem;margin-bottom:20px">Create your account</p>
    {% if error %}<err>{{error}}</err>{% endif %}
    <form method=post>
      <input type=hidden name=csrf_token value="{{ csrf_token() }}">
      <label>Username</label>
      <input name=username maxlength="50" required autofocus>
      <label>Email</label>
      <input name=email type="email" maxlength="100" required>
      <label>Password <span style="color:#555">(min 8 chars, upper, lower, number)</span></label>
      <input type=password name=password minlength="8" required>
      <div class="btn-group" style="margin-top:16px">
        <button class="btn btn-primary" style="flex:1;justify-content:center">Create Account</button>
      </div>
    </form>
    <p style="text-align:center;margin-top:16px;font-size:.85rem"><a href=/login>Already have an account?</a></p>
  </div>
</div>
"""

T_SEARCH = STYLE + """
<nav class="nav">
  <span class="nav-brand">&#11088; EverNothing</span>
  <a href=/>Home</a>
  <form action="/set_theme" method="get" style="display:inline">
    <select name="t" class="theme-select" onchange="this.form.submit()" title="Switch theme">
      <option value="stellar" {% if theme != "unicorn" %}selected="selected"{% endif %}>&#11088; Stellar</option>
      <option value="unicorn" {% if theme == "unicorn" %}selected="selected"{% endif %}>&#x1F984; Unicorn</option>
      <option value="startrek" {% if theme == "startrek" %}selected="selected"{% endif %}>&#x1F596; Star Trek</option>
      <option value="shrek" {% if theme == "shrek" %}selected="selected"{% endif %}>&#127807; Shrek</option>
      <option value="lotr" {% if theme == "lotr" %}selected="selected"{% endif %}>&#9770; LOTR</option>
    </select>
  </form>
  <a href=/logout class="nav-logout">Logout</a>
</nav>
<div class="container">
  <form method="get" class="card">
    <div class="search-box">
      <input name="q" value="{{q}}" placeholder="Search notes..." autofocus style="flex:1">
      <button class="btn btn-primary">Search</button>
    </div>
    <div class="form-row" style="margin-top:8px">
      <div>
        <label>Folder</label>
        <select name="folder">
          <option value="">All Folders</option>
          {% for f in folders %}
          <option value="{{f[0]}}" {% if folder_filter==f[0]|string %}selected{% endif %}>{{f[1]}}</option>
          {% endfor %}
        </select>
      </div>
      <div>
        <label>Date From</label>
        <input type="date" name="date_from" value="{{date_from}}">
      </div>
      <div>
        <label>Date To</label>
        <input type="date" name="date_to" value="{{date_to}}">
      </div>
    </div>
    <div style="margin-top:10px;display:flex;gap:16px;font-size:.85rem">
      <label style="display:flex;align-items:center;gap:6px;margin:0;cursor:pointer">
        <input type="checkbox" name="regex" {% if use_regex %}checked{% endif %} style="width:auto"> Regex
      </label>
      <label style="display:flex;align-items:center;gap:6px;margin:0;cursor:pointer">
        <input type="checkbox" name="history" {% if search_history %}checked{% endif %} style="width:auto"> Search History
      </label>
    </div>
  </form>
  {% if folder_results %}
  <h4>Folders <span class="badge">{{folder_results|length}}</span></h4>
  <ul class="item-list">
  {% for f in folder_results %}
  <li><a href=/folder/{{f[0]}}>&#128193; {{f[1]}}</a></li>
  {% endfor %}
  </ul>
  {% endif %}
  <h4>Notes {% if notes %}<span class="badge">{{notes|length}}</span>{% endif %}</h4>
  <ul class="item-list">
  {% for n in notes %}
  <li>
    <a href=/edit/{{n[0]}}>{{n[1]}}</a>
    <span class="timestamp">{{n[2]}}</span>
  </li>
  {% else %}
  <li class="empty">No matches.</li>
  {% endfor %}
  </ul>
</div>
"""

T_DELETE_FOLDER = STYLE + """
<nav class="nav">
  <span class="nav-brand">&#11088; EverNothing</span>
  <a href=/>Home</a>
  <form action="/set_theme" method="get" style="display:inline">
    <select name="t" class="theme-select" onchange="this.form.submit()" title="Switch theme">
      <option value="stellar" {% if theme != "unicorn" %}selected="selected"{% endif %}>&#11088; Stellar</option>
      <option value="unicorn" {% if theme == "unicorn" %}selected="selected"{% endif %}>&#x1F984; Unicorn</option>
      <option value="startrek" {% if theme == "startrek" %}selected="selected"{% endif %}>&#x1F596; Star Trek</option>
      <option value="shrek" {% if theme == "shrek" %}selected="selected"{% endif %}>&#127807; Shrek</option>
      <option value="lotr" {% if theme == "lotr" %}selected="selected"{% endif %}>&#9770; LOTR</option>
    </select>
  </form>
  <a href=/logout class="nav-logout">Logout</a>
</nav>
<div class="container">
  <div class="confirm-box">
    <h3>Delete Folder</h3>
    <p>Are you sure you want to delete <b>{{f[0]}}</b> and all its notes and subfolders?</p>
    <p style="color:#888;font-size:.85rem">This action cannot be undone.</p>
    <form method=post>
      <input type=hidden name=csrf_token value="{{ csrf_token() }}">
      <div class="btn-group">
        <button class="btn btn-danger">Yes, Delete</button>
        <a href=javascript:history.back() class="btn">Cancel</a>
      </div>
    </form>
  </div>
</div>
"""

T_HISTORY = STYLE + """
<nav class="nav">
  <span class="nav-brand">&#11088; EverNothing</span>
  <a href=/edit/{{nid}}>&#8592; Back to Note</a>
  <form action="/set_theme" method="get" style="display:inline">
    <select name="t" class="theme-select" onchange="this.form.submit()" title="Switch theme">
      <option value="stellar" {% if theme != "unicorn" %}selected="selected"{% endif %}>&#11088; Stellar</option>
      <option value="unicorn" {% if theme == "unicorn" %}selected="selected"{% endif %}>&#x1F984; Unicorn</option>
      <option value="startrek" {% if theme == "startrek" %}selected="selected"{% endif %}>&#x1F596; Star Trek</option>
      <option value="shrek" {% if theme == "shrek" %}selected="selected"{% endif %}>&#127807; Shrek</option>
      <option value="lotr" {% if theme == "lotr" %}selected="selected"{% endif %}>&#9770; LOTR</option>
    </select>
  </form>
  <a href=/logout class="nav-logout">Logout</a>
</nav>
<div class="container">
  <h3>Note History</h3>
  <ul class="item-list">
  {% for h in history %}
  <li>
    <span style="font-size:.85rem;color:#888;min-width:140px">{{h[2]}}</span>
    <span style="flex:1">{{h[1]}}</span>
    <span class="actions" style="opacity:1">
      <a href=/history/restore/{{h[0]}} class="btn btn-sm">Rollback</a>
    </span>
  </li>
  {% else %}
  <li class="empty">No history.</li>
  {% endfor %}
  </ul>
</div>
"""

T_ADMIN_LOGIN = STYLE + """
<div style="min-height:100vh;display:flex;align-items:center;justify-content:center">
  <div class="card" style="width:100%;max-width:380px">
    <h2 style="text-align:center;margin-bottom:4px">&#127775;Admin</h2>
    <p style="text-align:center;color:#666;font-size:.85rem;margin-bottom:20px">EverNothing Administration</p>
    {% if error %}<err>{{error}}</err>{% endif %}
    <form method=post>
      <input type=hidden name=csrf_token value="{{ csrf_token() }}">
      <label>Username</label>
      <input name=username autofocus>
      <label>Password</label>
      <input type=password name=password>
      <div class="btn-group" style="margin-top:16px">
        <button class="btn btn-primary" style="flex:1;justify-content:center">Login</button>
      </div>
    </form>
  </div>
</div>
"""

T_ADMIN_SESSIONS = STYLE + """
<nav class="nav">
  <span class="nav-brand">&#11088; Admin</span>
  <a href=/admin/dashboard>&#8592; Dashboard</a>
  <form action="/set_theme" method="get" style="display:inline">
    <select name="t" class="theme-select" onchange="this.form.submit()" title="Switch theme">
      <option value="stellar" {% if theme != "unicorn" %}selected="selected"{% endif %}>&#11088; Stellar</option>
      <option value="unicorn" {% if theme == "unicorn" %}selected="selected"{% endif %}>&#x1F984; Unicorn</option>
      <option value="startrek" {% if theme == "startrek" %}selected="selected"{% endif %}>&#x1F596; Star Trek</option>
      <option value="shrek" {% if theme == "shrek" %}selected="selected"{% endif %}>&#127807; Shrek</option>
      <option value="lotr" {% if theme == "lotr" %}selected="selected"{% endif %}>&#9770; LOTR</option>
    </select>
  </form>
  <a href=/logout class="nav-logout">Logout</a>
</nav>
<div class="container">
  <h3>All Sessions</h3>
  <table>
    <tr><th>Username</th><th>Login Time</th><th>Status</th><th>IP Address</th><th>Device</th></tr>
    {% for s in sessions %}
    <tr>
      <td>{{s.username}}</td>
      <td class="timestamp">{{s.login_time}}</td>
      <td>
        {% if s.logout_time == 'Active' %}<span style="color:var(--gold-dim)">Active</span>
        {% else %}<span style="color:#555">{{s.logout_time}}</span>{% endif %}
      </td>
      <td style="font-size:.85rem">{{s.ip}}</td>
      <td style="font-size:.8rem;color:#888">{{s.user_agent}}</td>
    </tr>
    {% else %}
    <tr><td colspan=5 class="empty">No sessions found.</td></tr>
    {% endfor %}
  </table>
</div>
"""

T_ADMIN_DASHBOARD = STYLE + """
<nav class="nav">
  <span class="nav-brand">&#11088; Admin</span>
  <a href=/admin/audit_logs>Audit Logs</a>
  <a href=/admin/sessions>Sessions</a>
  <a href=/admin/s3_backups>S3 Backups</a>
  <a href=/admin/iam_policy>IAM Policy</a>
  <form action="/set_theme" method="get" style="display:inline">
    <select name="t" class="theme-select" onchange="this.form.submit()" title="Switch theme">
      <option value="stellar" {% if theme != "unicorn" %}selected="selected"{% endif %}>&#11088; Stellar</option>
      <option value="unicorn" {% if theme == "unicorn" %}selected="selected"{% endif %}>&#x1F984; Unicorn</option>
      <option value="startrek" {% if theme == "startrek" %}selected="selected"{% endif %}>&#x1F596; Star Trek</option>
      <option value="shrek" {% if theme == "shrek" %}selected="selected"{% endif %}>&#127807; Shrek</option>
      <option value="lotr" {% if theme == "lotr" %}selected="selected"{% endif %}>&#9770; LOTR</option>
    </select>
  </form>
  <a href=/logout class="nav-logout">Logout</a>
</nav>
<div class="container">
  <h3>Users</h3>
  <form method="get" style="margin-bottom:16px">
    <div class="search-box">
      <input name="q" placeholder="Search users..." value="{{q}}" style="flex:1">
      <button class="btn btn-primary">Search</button>
    </div>
  </form>
  <table>
    <tr>
      <th>Username</th><th>Notes</th><th>Folders</th><th>Last Login</th><th>Actions</th>
    </tr>
    {% for u in users %}
    <tr>
      <td><a href=/admin/user/{{u[0]}}>{{u[1]}}</a></td>
      <td><span class="badge">{{u[2]}}</span></td>
      <td><span class="badge">{{u[3]}}</span></td>
      <td class="timestamp">{{u[4]}}</td>
      <td><a href=/admin/user/delete/{{u[0]}} style="color:var(--red);font-size:.8rem">delete</a></td>
    </tr>
    {% else %}
    <tr><td colspan=5 class="empty">No users found.</td></tr>
    {% endfor %}
  </table>
</div>
"""

T_ADMIN_EDIT_USER = STYLE + """
<nav class="nav">
  <span class="nav-brand">&#11088; Admin</span>
  <a href=/admin/dashboard>&#8592; Dashboard</a>
  <form action="/set_theme" method="get" style="display:inline">
    <select name="t" class="theme-select" onchange="this.form.submit()" title="Switch theme">
      <option value="stellar" {% if theme != "unicorn" %}selected="selected"{% endif %}>&#11088; Stellar</option>
      <option value="unicorn" {% if theme == "unicorn" %}selected="selected"{% endif %}>&#x1F984; Unicorn</option>
      <option value="startrek" {% if theme == "startrek" %}selected="selected"{% endif %}>&#x1F596; Star Trek</option>
      <option value="shrek" {% if theme == "shrek" %}selected="selected"{% endif %}>&#127807; Shrek</option>
      <option value="lotr" {% if theme == "lotr" %}selected="selected"{% endif %}>&#9770; LOTR</option>
    </select>
  </form>
  <a href=/logout class="nav-logout">Logout</a>
</nav>
<div class="container">
  <h3>Edit User</h3>
  {% if error %}<err>{{error}}</err>{% endif %}
  <p style="color:#666;font-size:.85rem">Passwords are hashed and cannot be displayed. You can only reset them.</p>
  <div class="card" style="max-width:500px">
    <form method=post>
      <input type=hidden name=csrf_token value="{{ csrf_token() }}">
      <label>Current Username</label>
      <input value="{{user[1]}}" readonly style="opacity:.6">
      <label>New Username</label>
      <input name=new_username autofocus>
      <label>New Password <span style="color:#555">(leave blank to keep)</span></label>
      <input name=new_password type=password>
      <label>Last Login</label>
      <input name=last_login value="{{user[2] if user[2] else 'Never'}}" readonly style="opacity:.6">
      <div class="btn-group">
        <button class="btn btn-primary">Update</button>
        <a href=/admin/dashboard class="btn">Cancel</a>
      </div>
    </form>
  </div>
</div>
"""

T_ADMIN_EDIT_USER_CONFIRM = STYLE + """
<nav class="nav">
  <span class="nav-brand">&#11088; Admin</span>
  <a href=/admin/dashboard>Dashboard</a>
  <form action="/set_theme" method="get" style="display:inline">
    <select name="t" class="theme-select" onchange="this.form.submit()" title="Switch theme">
      <option value="stellar" {% if theme != "unicorn" %}selected="selected"{% endif %}>&#11088; Stellar</option>
      <option value="unicorn" {% if theme == "unicorn" %}selected="selected"{% endif %}>&#x1F984; Unicorn</option>
      <option value="startrek" {% if theme == "startrek" %}selected="selected"{% endif %}>&#x1F596; Star Trek</option>
      <option value="shrek" {% if theme == "shrek" %}selected="selected"{% endif %}>&#127807; Shrek</option>
      <option value="lotr" {% if theme == "lotr" %}selected="selected"{% endif %}>&#9770; LOTR</option>
    </select>
  </form>
  <a href=/logout class="nav-logout">Logout</a>
</nav>
<div class="container">
  <div class="confirm-box">
    <h3>Confirm User Change</h3>
    <p>Change username from <b>{{user[1]}}</b> to <b>{{new_name}}</b>?</p>
    {% if new_pass %}<p>Password will also be changed.</p>{% endif %}
    <form method=post>
      <input type=hidden name=csrf_token value="{{ csrf_token() }}">
      <input type=hidden name=new_username value="{{new_name}}">
      <input type=hidden name=new_password value="{{new_pass}}">
      <input type=hidden name=confirm value="yes">
      <div class="btn-group">
        <button class="btn btn-primary">Yes, Change</button>
        <a href=/admin/dashboard class="btn">Cancel</a>
      </div>
    </form>
  </div>
</div>
"""

T_ADMIN_DELETE_USER = STYLE + """
<nav class="nav">
  <span class="nav-brand">&#11088; Admin</span>
  <a href=/admin/dashboard>&#8592; Dashboard</a>
  <form action="/set_theme" method="get" style="display:inline">
    <select name="t" class="theme-select" onchange="this.form.submit()" title="Switch theme">
      <option value="stellar" {% if theme != "unicorn" %}selected="selected"{% endif %}>&#11088; Stellar</option>
      <option value="unicorn" {% if theme == "unicorn" %}selected="selected"{% endif %}>&#x1F984; Unicorn</option>
      <option value="startrek" {% if theme == "startrek" %}selected="selected"{% endif %}>&#x1F596; Star Trek</option>
      <option value="shrek" {% if theme == "shrek" %}selected="selected"{% endif %}>&#127807; Shrek</option>
      <option value="lotr" {% if theme == "lotr" %}selected="selected"{% endif %}>&#9770; LOTR</option>
    </select>
  </form>
  <a href=/logout class="nav-logout">Logout</a>
</nav>
<div class="container">
  <div class="confirm-box">
    <h3>Delete User</h3>
    <p>Are you sure you want to delete <b>{{user[1]}}</b>?</p>
    <p style="color:var(--red);font-size:.85rem">All notes, folders, and history for this user will be permanently deleted.</p>
    <form method=post>
      <input type=hidden name=csrf_token value="{{ csrf_token() }}">
      <div class="btn-group">
        <button class="btn btn-danger">Yes, Delete User</button>
        <a href=/admin/dashboard class="btn">Cancel</a>
      </div>
    </form>
  </div>
</div>
"""

T_FORGOT_PASSWORD = STYLE + """
<div style="min-height:100vh;display:flex;align-items:center;justify-content:center">
  <div class="card" style="width:100%;max-width:400px">
    <h2 style="text-align:center;margin-bottom:4px">&#127775;EverNothing</h2>
    <p style="text-align:center;color:#666;font-size:.85rem;margin-bottom:20px">Reset your password</p>
    {% if message %}<p style="color:#0c0;text-align:center">{{message}}</p>{% endif %}
    <form method=post>
      <input type=hidden name=csrf_token value="{{ csrf_token() }}">
      <label>Email Address</label>
      <input name=email type=email required autofocus>
      <div class="btn-group" style="margin-top:16px">
        <button class="btn btn-primary" style="flex:1;justify-content:center">Send Reset Link</button>
      </div>
    </form>
    <p style="text-align:center;margin-top:16px;font-size:.85rem"><a href=/login>Back to login</a></p>
  </div>
</div>
"""

T_RESET_PASSWORD = STYLE + """
<div style="min-height:100vh;display:flex;align-items:center;justify-content:center">
  <div class="card" style="width:100%;max-width:400px">
    <h2 style="text-align:center;margin-bottom:20px">&#127775;Reset Password</h2>
    {% if error %}<err>{{error}}</err>{% endif %}
    <form method=post>
      <input type=hidden name=csrf_token value="{{ csrf_token() }}">
      <label>New Password</label>
      <input type=password name=password required autofocus>
      <div class="btn-group" style="margin-top:16px">
        <button class="btn btn-primary" style="flex:1;justify-content:center">Reset Password</button>
      </div>
    </form>
  </div>
</div>
"""

T_AUDIT_REPORT = STYLE + """
<nav class="nav">
  <span class="nav-brand">&#11088; EverNothing</span>
  <a href=/>&#8592; Home</a>
  <form action="/set_theme" method="get" style="display:inline">
    <select name="t" class="theme-select" onchange="this.form.submit()" title="Switch theme">
      <option value="stellar" {% if theme != "unicorn" %}selected="selected"{% endif %}>&#11088; Stellar</option>
      <option value="unicorn" {% if theme == "unicorn" %}selected="selected"{% endif %}>&#x1F984; Unicorn</option>
      <option value="startrek" {% if theme == "startrek" %}selected="selected"{% endif %}>&#x1F596; Star Trek</option>
      <option value="shrek" {% if theme == "shrek" %}selected="selected"{% endif %}>&#127807; Shrek</option>
      <option value="lotr" {% if theme == "lotr" %}selected="selected"{% endif %}>&#9770; LOTR</option>
    </select>
  </form>
  <a href=/logout class="nav-logout">Logout</a>
</nav>
<div class="container">
  <h3>Audit Report</h3>
  <table>
    <tr><th>Time</th><th>Action</th><th>Entity</th><th>Old Values</th><th>New Values</th><th>IP</th></tr>
    {% for log in logs %}
    <tr>
      <td class="timestamp">{{log.timestamp}}</td>
      <td><span class="tag-{{log.action|lower}}">{{log.action}}</span></td>
      <td style="font-size:.8rem">{{log.entity}}</td>
      <td style="font-size:.8rem">{% for k,v in log.old.items() %}<b>{{k}}:</b> {{v}}<br>{% endfor %}</td>
      <td style="font-size:.8rem">{% for k,v in log.new.items() %}<b>{{k}}:</b> {{v}}<br>{% endfor %}</td>
      <td style="font-size:.75rem;color:#666">{{log.ip}}</td>
    </tr>
    {% else %}
    <tr><td colspan=6 class="empty">No audit records.</td></tr>
    {% endfor %}
  </table>
</div>
"""

T_SESSIONS = STYLE + """
<nav class="nav">
  <span class="nav-brand">&#11088; EverNothing</span>
  <a href=/>&#8592; Home</a>
  <form action="/set_theme" method="get" style="display:inline">
    <select name="t" class="theme-select" onchange="this.form.submit()" title="Switch theme">
      <option value="stellar" {% if theme != "unicorn" %}selected="selected"{% endif %}>&#11088; Stellar</option>
      <option value="unicorn" {% if theme == "unicorn" %}selected="selected"{% endif %}>&#x1F984; Unicorn</option>
      <option value="startrek" {% if theme == "startrek" %}selected="selected"{% endif %}>&#x1F596; Star Trek</option>
      <option value="shrek" {% if theme == "shrek" %}selected="selected"{% endif %}>&#127807; Shrek</option>
      <option value="lotr" {% if theme == "lotr" %}selected="selected"{% endif %}>&#9770; LOTR</option>
    </select>
  </form>
  <a href=/logout class="nav-logout">Logout</a>
</nav>
<div class="container">
  <h3>Login Sessions</h3>
  <p style="color:#666;font-size:.85rem;margin-bottom:16px">Up to 3 concurrent sessions allowed. Revoke any you don't recognize.</p>
  <table>
    <tr><th>Login Time</th><th>Status</th><th>IP Address</th><th>Device</th><th></th></tr>
    {% for s in sessions %}
    <tr {% if s.is_current %}style="background:var(--bg3)"{% endif %}>
      <td class="timestamp">{{s.login_time}}</td>
      <td>
        {% if s.is_current %}<span style="color:#0c0">&#9679; Current</span>
        {% elif s.logout_time == 'Active' %}<span style="color:var(--gold-dim)">Active</span>
        {% else %}<span style="color:#555">{{s.logout_time}}</span>{% endif %}
      </td>
      <td style="font-size:.85rem">{{s.ip}}</td>
      <td style="font-size:.8rem;color:#888">{{s.user_agent}}</td>
      <td>
        {% if not s.is_current and s.logout_time == 'Active' %}
        <a href=/session/revoke/{{s.session_id}} class="btn btn-sm btn-danger">Revoke</a>
        {% endif %}
      </td>
    </tr>
    {% endfor %}
  </table>
</div>
"""

T_ADMIN_AUDIT_LOGS = STYLE + """
<nav class="nav">
  <span class="nav-brand">&#11088; Admin</span>
  <a href=/admin/dashboard>&#8592; Dashboard</a>
  <a href="javascript:location.reload()" style="color:#0c0">Refresh</a>
  <form action="/set_theme" method="get" style="display:inline">
    <select name="t" class="theme-select" onchange="this.form.submit()" title="Switch theme">
      <option value="stellar" {% if theme != "unicorn" %}selected="selected"{% endif %}>&#11088; Stellar</option>
      <option value="unicorn" {% if theme == "unicorn" %}selected="selected"{% endif %}>&#x1F984; Unicorn</option>
      <option value="startrek" {% if theme == "startrek" %}selected="selected"{% endif %}>&#x1F596; Star Trek</option>
      <option value="shrek" {% if theme == "shrek" %}selected="selected"{% endif %}>&#127807; Shrek</option>
      <option value="lotr" {% if theme == "lotr" %}selected="selected"{% endif %}>&#9770; LOTR</option>
    </select>
  </form>
  <a href=/logout class="nav-logout">Logout</a>
</nav>
<div class="container">
  <h3>Audit Logs</h3>
  <form method="get" class="card" style="margin-bottom:16px">
    <div class="form-row">
      <div>
        <label>Username</label>
        <input name="user" value="{{user_filter}}" placeholder="Filter by user">
      </div>
      <div>
        <label>Action</label>
        <select name="action">
          <option value="">All Actions</option>
          <option value="CREATE" {% if action_filter=='CREATE' %}selected{% endif %}>CREATE</option>
          <option value="UPDATE" {% if action_filter=='UPDATE' %}selected{% endif %}>UPDATE</option>
          <option value="DELETE" {% if action_filter=='DELETE' %}selected{% endif %}>DELETE</option>
        </select>
      </div>
      <div>
        <label>Entity</label>
        <select name="entity">
          <option value="">All Entities</option>
          <option value="note" {% if entity_filter=='note' %}selected{% endif %}>Note</option>
          <option value="attachment" {% if entity_filter=='attachment' %}selected{% endif %}>Attachment</option>
          <option value="user" {% if entity_filter=='user' %}selected{% endif %}>User</option>
        </select>
      </div>
      <div>
        <label>Limit</label>
        <select name="limit">
          <option value="50" {% if limit==50 %}selected{% endif %}>50</option>
          <option value="100" {% if limit==100 %}selected{% endif %}>100</option>
          <option value="500" {% if limit==500 %}selected{% endif %}>500</option>
          <option value="1000" {% if limit==1000 %}selected{% endif %}>1000</option>
        </select>
      </div>
    </div>
    <div class="btn-group">
      <button class="btn btn-primary">Filter</button>
      <a href=/admin/audit_logs class="btn">Clear</a>
      <span style="margin-left:auto;color:#666;font-size:.85rem">{{logs|length}} records</span>
    </div>
  </form>
  <table>
    <tr><th>Time</th><th>User</th><th>Action</th><th>Entity</th><th>Old</th><th>New</th><th>IP</th></tr>
    {% for log in logs %}
    <tr>
      <td class="timestamp">{{log.timestamp}}</td>
      <td>{{log.user}}</td>
      <td><span class="tag-{{log.action|lower}}">{{log.action}}</span></td>
      <td style="font-size:.8rem">{{log.entity}}</td>
      <td style="font-size:.8rem">{% for k,v in log.old.items() %}<b>{{k}}:</b> {{v}}<br>{% endfor %}</td>
      <td style="font-size:.8rem">{% for k,v in log.new.items() %}<b>{{k}}:</b> {{v}}<br>{% endfor %}</td>
      <td style="font-size:.75rem;color:#666">{{log.ip}}</td>
    </tr>
    {% else %}
    <tr><td colspan=7 class="empty">No audit logs found.</td></tr>
    {% endfor %}
  </table>
</div>
"""

# --- JSON API (for Android app) ---
from flask import jsonify
# api_login_required imported above from evernothing_security (#13)

@app.route("/api/login", methods=["POST"])
@csrf.exempt
def api_login():
    from rate_limiter import check_rate_limit, RATE_LIMIT_LOGIN
    from Evernothing_Security.login_lockout import (
        is_locked, register_failure, clear_failures,
    )
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid request'}), 400
    username = data.get('username', '')

    # Per-IP rate limit. Same hourly bucket as the form login.
    if not check_rate_limit(request.remote_addr, 'login', RATE_LIMIT_LOGIN):
        logger.warning(f"Rate limit exceeded for /api/login from {request.remote_addr}")
        return jsonify({'error': 'Too many login attempts'}), 429

    # Per-username lockout
    if is_locked(username):
        return jsonify({'error': 'Account temporarily locked'}), 423

    con = db(); cur = con.cursor()
    r = cur.execute("SELECT id,password FROM users WHERE username=?", (username,)).fetchone()
    if r and check_password_hash(r[1], data.get('password','')):
        clear_failures(username)
        session_id = os.urandom(16).hex()
        session['session_id'] = session_id
        session['last_activity'] = datetime.datetime.now(timezone.utc).isoformat()
        session['remember_me'] = False
        session.permanent = True
        cur.execute("UPDATE users SET last_login=? WHERE id=?", (datetime.datetime.now(timezone.utc).isoformat(), r[0]))
        cur.execute("INSERT INTO user_sessions (user_id, session_id, login_time, ip_address, user_agent) VALUES (?,?,?,?,?)",
            (r[0], session_id, datetime.datetime.now(timezone.utc).isoformat(), request.remote_addr, request.user_agent.string))
        con.commit(); con.close()
        login_user(User(r[0], username))
        return jsonify({'ok': True, 'username': username})
    con.close()
    if register_failure(username):
        logger.warning(f"Account locked for {username!r} via /api/login from {request.remote_addr}")
    return jsonify({'error': 'Invalid username or password'}), 401

@app.route("/api/logout", methods=["POST"])
@csrf.exempt
def api_logout():
    if 'session_id' in session:
        con = db(); cur = con.cursor()
        cur.execute("UPDATE user_sessions SET logout_time=? WHERE session_id=?",
            (datetime.datetime.now(timezone.utc).isoformat(), session['session_id']))
        con.commit(); con.close()
    logout_user(); session.clear()
    return jsonify({'ok': True})

@app.route("/api/folders")
@api_login_required
def api_folders():
    con = db(); cur = con.cursor()
    cur.execute("SELECT id,name,parent_id FROM folders WHERE user_id=? ORDER BY name", (current_user.id,))
    folders = [{'id': r[0], 'name': decrypt(r[1]), 'parent_id': r[2]} for r in cur.fetchall()]
    con.close()
    return jsonify(folders)

@app.route("/api/folders", methods=["POST"])
@csrf.exempt
@api_login_required
def api_create_folder():
    data = request.get_json()
    name = (data or {}).get('name', '').strip()
    parent_id = (data or {}).get('parent_id')
    if not name:
        return jsonify({'error': 'Name required'}), 400
    con = db(); cur = con.cursor()
    cur.execute("INSERT INTO folders (user_id, name, parent_id) VALUES(?,?,?)", (current_user.id, encrypt(name), parent_id))
    fid = cur.lastrowid
    con.commit(); con.close(); sync_s3_async()
    return jsonify({'ok': True, 'id': fid})

@app.route("/api/folders/<int:fid>", methods=["DELETE"])
@csrf.exempt
@api_login_required
def api_delete_folder(fid):
    con = db(); cur = con.cursor()
    delete_recursive(cur, fid, current_user.id)
    con.commit(); con.close(); sync_s3_async()
    return jsonify({'ok': True})

@app.route("/api/folders/<int:fid>/notes")
@api_login_required
def api_folder_notes(fid):
    con = db(); cur = con.cursor()
    cur.execute("SELECT id,note_key,description,updated_at FROM notes WHERE user_id=? AND folder_id=? ORDER BY note_key", (current_user.id, fid))
    notes = [{'id': r[0], 'key': decrypt(r[1]), 'description': decrypt(r[2]) if r[2] else '', 'updated_at': format_date(r[3])} for r in cur.fetchall()]
    con.close()
    return jsonify(notes)

@app.route("/api/notes/<int:nid>")
@api_login_required
def api_get_note(nid):
    con = db(); cur = con.cursor()
    r = cur.execute("SELECT id,note_key,note_value,description,folder_id,updated_at FROM notes WHERE id=? AND user_id=?", (nid, current_user.id)).fetchone()
    con.close()
    if not r:
        return jsonify({'error': 'Not found'}), 404
    return jsonify({'id': r[0], 'key': decrypt(r[1]), 'value': decrypt(r[2]), 'description': decrypt(r[3]) if r[3] else '', 'folder_id': r[4], 'updated_at': format_date(r[5])})

@app.route("/api/notes", methods=["POST"])
@csrf.exempt
@api_login_required
def api_create_note():
    data = request.get_json() or {}
    key = data.get('key', '').strip()
    value = data.get('value', '').strip()
    fid = data.get('folder_id')
    desc = data.get('description', '')[:255]
    if not key or not value:
        return jsonify({'error': 'Key and value required'}), 400
    con = db(); cur = con.cursor()
    cur.execute("SELECT note_key FROM notes WHERE user_id=?", (current_user.id,))
    if any(decrypt(r[0]).strip().lower() == key.lower() for r in cur.fetchall()):
        con.close()
        return jsonify({'error': 'Note name already exists'}), 409
    now = datetime.datetime.now(timezone.utc).isoformat()
    cur.execute("INSERT INTO notes (user_id, folder_id, note_key, note_value, description, updated_at) VALUES(?,?,?,?,?,?)",
        (current_user.id, fid, encrypt(key), encrypt(value), encrypt(desc), now))
    nid = cur.lastrowid
    cur.execute("INSERT INTO note_history (note_id, user_id, note_key, note_value, description, folder_id, updated_at) VALUES(?,?,?,?,?,?,?)",
        (nid, current_user.id, encrypt(key), encrypt(value), encrypt(desc), fid, now))
    log_change(cur, current_user.id, 'CREATE', 'note', nid, {}, {'key': key, 'folder_id': fid}, request.remote_addr)
    con.commit(); con.close(); sync_s3_async()
    return jsonify({'ok': True, 'id': nid})

@app.route("/api/notes/<int:nid>", methods=["PUT"])
@csrf.exempt
@api_login_required
def api_update_note(nid):
    data = request.get_json() or {}
    key = data.get('key', '').strip()
    value = data.get('value', '').strip()
    fid = data.get('folder_id')
    desc = data.get('description', '')[:255]
    if not key or not value:
        return jsonify({'error': 'Key and value required'}), 400
    con = db(); cur = con.cursor()
    now = datetime.datetime.now(timezone.utc).isoformat()
    cur.execute("UPDATE notes SET note_key=?,note_value=?,description=?,folder_id=?,updated_at=? WHERE id=? AND user_id=?",
        (encrypt(key), encrypt(value), encrypt(desc), fid, now, nid, current_user.id))
    cur.execute("INSERT INTO note_history (note_id, user_id, note_key, note_value, description, folder_id, updated_at) VALUES(?,?,?,?,?,?,?)",
        (nid, current_user.id, encrypt(key), encrypt(value), encrypt(desc), fid, now))
    log_change(cur, current_user.id, 'UPDATE', 'note', nid, {}, {'key': key, 'folder_id': fid}, request.remote_addr)
    con.commit(); con.close(); sync_s3_async()
    return jsonify({'ok': True})

@app.route("/api/notes/<int:nid>", methods=["DELETE"])
@csrf.exempt
@api_login_required
def api_delete_note(nid):
    con = db(); cur = con.cursor()
    cur.execute("DELETE FROM notes WHERE id=? AND user_id=?", (nid, current_user.id))
    con.commit(); con.close(); sync_s3_async()
    return jsonify({'ok': True})

@app.route("/api/search")
@api_login_required
def api_search():
    q = request.args.get('q', '').strip().lower()
    if not q:
        return jsonify([])
    con = db(); cur = con.cursor()
    cur.execute("SELECT id,note_key,note_value,updated_at FROM notes WHERE user_id=?", (current_user.id,))
    results = []
    for r in cur.fetchall():
        k, v = decrypt(r[1]), decrypt(r[2])
        if q in k.lower() or q in v.lower():
            results.append({'id': r[0], 'key': k, 'updated_at': format_date(r[3])})
    con.close()
    return jsonify(sorted(results, key=lambda x: x['key'].lower()))

if __name__ == '__main__':
    # Filesystem-side-effect startup tasks. Moved out of module-scope so
    # parallel test runs don't race on the same Backups directory.
    _run_startup_tasks()

    # Phase 0: bootstrap from S3 if the local DB is empty. No-op on a
    # populated DB, which is the steady state for a long-running PC.
    if _bootstrap_from_s3():
        logger.info('bootstrap: complete; entering steady-state delta mode')

    # SSL cert/key paths — override via env vars or generate a self-signed cert for dev:
    #   openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes
    ssl_cert = os.environ.get('SSL_CERT', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Startup', 'cert.pem'))
    ssl_key  = os.environ.get('SSL_KEY',  os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Startup', 'key.pem'))
    use_ssl  = os.path.exists(ssl_cert) and os.path.exists(ssl_key)
    ssl_ctx  = (ssl_cert, ssl_key) if use_ssl else None
    if not use_ssl:
        logger.warning("SSL cert/key not found — running without HTTPS. Set SSL_CERT and SSL_KEY env vars.")

    # Start the S3 pull worker (multi-device replication). No-op when S3
    # isn't configured or app.config['TESTING'] is True.
    try:
        from Evernothing_Connect.s3_pull import start_pull_worker
        start_pull_worker()
    except Exception as _e:
        logger.warning(f'S3 pull worker not started: {_e}')

    app.run(host='0.0.0.0', port=5443 if use_ssl else 5000, ssl_context=ssl_ctx)


T_ADMIN_S3_BACKUPS = STYLE + """
<h3>S3 Backups</h3>
<a href=/admin/dashboard>Back to Dashboard</a> | <a href=/logout>Logout</a>
{% if message %}<p style="color:#0f0;">{{message}}</p>{% endif %}
{% if error %}<p style="color:red;">{{error}}</p>{% endif %}
<p>Database backups stored in S3 bucket: <b>{{ config.get('S3_BUCKET_NAME', 'N/A') }}</b></p>
<table style="width:100%; border-collapse:collapse; margin-top:20px;">
<tr style="border-bottom:2px solid red;">
<th style="text-align:left; padding:8px;">Backup File</th>
<th style="text-align:left; padding:8px;">Size (bytes)</th>
<th style="text-align:left; padding:8px;">Last Modified</th>
<th style="text-align:left; padding:8px;">Action</th>
</tr>
{% if confirm_key %}
<p>Restore backup <b>{{confirm_key}}</b> to local file?</p>
<form method=post action="/admin/s3_restore/{{confirm_key}}">
<input type=hidden name=csrf_token value="{{ csrf_token() }}">
<button>Yes, Restore</button> <a href=/admin/s3_backups class=cancel>Cancel</a>
</form>
{% else %}
<table style="width:100%; border-collapse:collapse; margin-top:20px;">
<tr style="border-bottom:2px solid red;">
<th style="text-align:left; padding:8px;">Backup File</th>
<th style="text-align:left; padding:8px;">Size (bytes)</th>
<th style="text-align:left; padding:8px;">Last Modified</th>
<th style="text-align:left; padding:8px;">Action</th>
</tr>
{% for backup in backups %}
<tr style="border-bottom:1px solid #333;">
<td style="padding:8px; font-size:small;">{{backup.key}}</td>
<td style="padding:8px;">{{backup.size}}</td>
<td style="padding:8px;">{{backup.modified}}</td>
<td style="padding:8px;"><a href="/admin/s3_restore/{{backup.key}}" style="color:#0f0;">[Restore]</a></td>
</tr>
{% else %}
<tr><td colspan="4" style="padding:20px; text-align:center; color:#888;">No backups found or S3 not configured</td></tr>
{% endfor %}
</table>
{% endif %}
"""

















