"""
Evernothing_DB/database.py
Database connection, schema init, backup, and compression.
"""
import gzip, os, shutil, sqlite3, datetime
from datetime import timezone

# DB path resolved relative to project root
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.environ.get('DB_FILE',
     os.path.join(_ROOT, 'DB', 'evernothing.db'))

_SCHEMA = """
CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE,
    password TEXT, last_login TEXT, email TEXT);
CREATE TABLE IF NOT EXISTS folders(
    id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
    name TEXT, parent_id INTEGER);
CREATE TABLE IF NOT EXISTS notes(
    id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
    folder_id INTEGER, note_key TEXT, note_value TEXT,
    description TEXT, updated_at TEXT);
CREATE TABLE IF NOT EXISTS note_history(
    id INTEGER PRIMARY KEY AUTOINCREMENT, note_id INTEGER,
    user_id INTEGER, note_key TEXT, note_value TEXT,
    description TEXT, folder_id INTEGER, updated_at TEXT);
CREATE TABLE IF NOT EXISTS user_sessions(
    id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
    session_id TEXT, login_time TEXT, logout_time TEXT,
    ip_address TEXT, user_agent TEXT);
CREATE TABLE IF NOT EXISTS attachments(
    id INTEGER PRIMARY KEY AUTOINCREMENT, note_id INTEGER,
    user_id INTEGER, filename TEXT, file_data BLOB,
    file_size INTEGER, uploaded_at TEXT);
CREATE TABLE IF NOT EXISTS audit_log(
    id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
    action TEXT, entity_type TEXT, entity_id INTEGER,
    old_values TEXT, new_values TEXT, timestamp TEXT, ip_address TEXT);
CREATE TABLE IF NOT EXISTS sync_queue(
    id INTEGER PRIMARY KEY AUTOINCREMENT, entity_type TEXT,
    entity_id INTEGER, operation TEXT, payload TEXT,
    changed_at TEXT, synced_at TEXT);
CREATE INDEX IF NOT EXISTS idx_notes_user    ON notes(user_id);
CREATE INDEX IF NOT EXISTS idx_folders_user  ON folders(user_id);
CREATE INDEX IF NOT EXISTS idx_attachments   ON attachments(note_id);
CREATE INDEX IF NOT EXISTS idx_audit_user    ON audit_log(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_entity  ON audit_log(entity_type, entity_id);
"""

def get_db():
    """Return a new SQLite connection to the configured DB."""
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con

def init_db():
    """Create all tables if they don't exist."""
    con = get_db()
    con.executescript(_SCHEMA)
    con.commit()
    con.close()

def backup_database():
    """Create a timestamped backup of the DB file."""
    if not os.path.exists(DB):
        return
    backup_dir = os.path.join(_ROOT, 'DB', 'Backups')
    os.makedirs(backup_dir, exist_ok=True)
    ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    dest = os.path.join(backup_dir, f'evernothing_backup_{ts}.db')
    shutil.copy2(DB, dest)
    print(f'Database backed up to: {dest}')

def compress_old_backups(days: int = 5):
    """Gzip backup files older than `days` days."""
    backup_dir = os.path.join(_ROOT, 'DB', 'Backups')
    if not os.path.isdir(backup_dir):
        return
    cutoff = datetime.datetime.now() - datetime.timedelta(days=days)
    for fname in os.listdir(backup_dir):
        if not fname.endswith('.db'):
            continue
        fpath = os.path.join(backup_dir, fname)
        if datetime.datetime.fromtimestamp(os.path.getmtime(fpath)) < cutoff:
            gz_path = fpath + '.gz'
            try:
                with open(fpath, 'rb') as f_in, gzip.open(gz_path, 'wb') as f_out:
                    f_out.write(f_in.read())
                os.remove(fpath)
            except Exception as e:
                print(f'Compress error ({fname}): {e}')
