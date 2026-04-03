"""
evernothing_db.py — Database Operations
Connection factory, schema init, backup, compression.
"""
import sqlite3, datetime, os, shutil
from evernothing_config import DB, logger


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
    """)

    # Migrations
    for sql in [
        "ALTER TABLE notes ADD COLUMN description TEXT",
        "ALTER TABLE note_history ADD COLUMN description TEXT",
        "ALTER TABLE users ADD COLUMN last_login TEXT",
        "ALTER TABLE users ADD COLUMN email TEXT",
    ]:
        try:
            cur.execute(sql)
        except sqlite3.OperationalError:
            pass

    # Verify attachments has file_data column
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

    # Indexes
    for idx in [
        "CREATE INDEX IF NOT EXISTS idx_notes_user ON notes(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_folders_user ON folders(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_attachments_note ON attachments(note_id)",
        "CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_log(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_audit_entity ON audit_log(entity_type, entity_id)",
    ]:
        try:
            cur.execute(idx)
        except Exception as e:
            logger.warning(f"Index creation warning: {e}")

    c.commit()
    c.close()


def backup_database():
    """Timestamped local backup on startup."""
    if not os.path.exists(DB):
        return
    os.makedirs("Backups", exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    shutil.copy(DB, f"Backups/evernothing_backup_{ts}.db")
    logger.info(f"Database backed up: Backups/evernothing_backup_{ts}.db")


def compress_old_backups(days=5, backup_dir="Backups"):
    """Compress .db backup files older than `days` days."""
    import gzip
    if not os.path.isdir(backup_dir):
        return
    cutoff = datetime.datetime.now() - datetime.timedelta(days=days)
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
                logger.info(f"Compressed backup: {gz_path}")
            except Exception as e:
                logger.warning(f"Compress error ({fname}): {e}")
