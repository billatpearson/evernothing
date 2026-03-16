"""
EverNothing - Database, Encryption, and Core Utilities
"""
import sqlite3, datetime, json, os, base64, shutil, logging
from datetime import timezone

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
except ImportError:
    AESGCM = None

logger = logging.getLogger(__name__)

DB = os.environ.get('DB_FILE', 'evernothing.db')

# --- ENCRYPTION ---
ENCRYPTION_ENABLED = os.environ.get('ENCRYPTION_ENABLED', 'false').lower() == 'true'
KEY_FILE = 'secret.key'

if AESGCM:
    if os.path.exists(KEY_FILE):
        with open(KEY_FILE, 'rb') as f:
            KEY = f.read()
    else:
        KEY = AESGCM.generate_key(bit_length=256)
        with open(KEY_FILE, 'wb') as f:
            f.write(KEY)
    aesgcm = AESGCM(KEY)

    def encrypt(txt):
        if not ENCRYPTION_ENABLED or not txt: return txt if txt else ''
        try:
            nonce = os.urandom(12)
            return base64.b64encode(nonce + aesgcm.encrypt(nonce, txt.encode('utf-8'), None)).decode('utf-8')
        except Exception as e:
            print(f'Enc Error: {e}')
            return txt

    def decrypt(txt):
        if not txt: return ''
        try:
            data = base64.b64decode(txt)
            return aesgcm.decrypt(data[:12], data[12:], None).decode('utf-8')
        except Exception:
            return txt
else:
    def encrypt(t): return t
    def decrypt(t): return t


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
    """)
    for _sql in [
        "ALTER TABLE notes ADD COLUMN description TEXT",
        "ALTER TABLE note_history ADD COLUMN description TEXT",
        "ALTER TABLE users ADD COLUMN last_login TEXT",
        "ALTER TABLE users ADD COLUMN email TEXT",
    ]:
        try:
            cur.execute(_sql)
        except sqlite3.OperationalError:
            pass
    try:
        cur.execute("SELECT file_data FROM attachments LIMIT 1")
    except sqlite3.OperationalError:
        cur.execute("DROP TABLE IF EXISTS attachments")
        cur.execute("""
            CREATE TABLE attachments(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                note_id INTEGER, user_id INTEGER, filename TEXT,
                file_data BLOB, file_size INTEGER, uploaded_at TEXT
            )
        """)
    for idx in [
        "CREATE INDEX IF NOT EXISTS idx_notes_user ON notes(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_folders_user ON folders(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_attachments_note ON attachments(note_id)",
        "CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_log(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_audit_entity ON audit_log(entity_type, entity_id)",
    ]:
        try:
            cur.execute(idx)
        except Exception:
            pass
    c.commit(); c.close()


def backup_database():
    """Backup database with timestamp on application launch."""
    if os.path.exists(DB):
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        os.makedirs('Backups', exist_ok=True)
        backup_file = f'Backups/evernothing_backup_{timestamp}.db'
        shutil.copy(DB, backup_file)
        print(f'Database backed up to: {backup_file}')


# --- UTILITIES ---
def format_date(iso_str):
    try:
        return datetime.datetime.fromisoformat(iso_str).strftime('%m/%d/%Y %H:%M')
    except Exception:
        return iso_str


def get_breadcrumbs(cur, fid, uid):
    crumbs = []
    while fid:
        f = cur.execute(
            "SELECT id,name,parent_id FROM folders WHERE id=? AND user_id=?", (fid, uid)
        ).fetchone()
        if not f: break
        crumbs.insert(0, (f[0], decrypt(f[1])))
        fid = f[2]
    return crumbs


def log_change(cur, user_id, action, entity_type, entity_id, old_values, new_values, ip_addr):
    cur.execute(
        "INSERT INTO audit_log (user_id, action, entity_type, entity_id, old_values, new_values, timestamp, ip_address) VALUES(?,?,?,?,?,?,?,?)",
        (user_id, action, entity_type, entity_id,
         json.dumps(old_values), json.dumps(new_values),
         datetime.datetime.now(timezone.utc).isoformat(), ip_addr)
    )


def delete_recursive(cur, fid, uid):
    cur.execute("SELECT id FROM folders WHERE parent_id=? AND user_id=?", (fid, uid))
    for sub in cur.fetchall():
        delete_recursive(cur, sub[0], uid)
    cur.execute("DELETE FROM notes WHERE folder_id=? AND user_id=?", (fid, uid))
    cur.execute("DELETE FROM folders WHERE id=? AND user_id=?", (fid, uid))


def validate_input(text, max_length=255, allow_empty=False):
    if not text and not allow_empty:
        return None, 'Input cannot be empty'
    if text and len(text) > max_length:
        return None, f'Input too long (max {max_length} characters)'
    return text.strip() if text else text, None


def validate_email(email):
    import re
    if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
        return None, 'Invalid email format'
    return email, None


def validate_password(password):
    if len(password) < 8:
        return None, 'Password must be at least 8 characters'
    if not any(c.isupper() for c in password):
        return None, 'Password must contain at least one uppercase letter'
    if not any(c.islower() for c in password):
        return None, 'Password must contain at least one lowercase letter'
    if not any(c.isdigit() for c in password):
        return None, 'Password must contain at least one number'
    return password, None


def allowed_file(filename):
    ALLOWED = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'zip'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED
