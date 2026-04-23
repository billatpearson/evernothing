"""
Evernothing_Test
Test infrastructure and shared fixtures.
All test files live in Test/ and tests/ directories.
This module provides shared setUp helpers.
"""
import os, sqlite3, tempfile

_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT, email TEXT, last_login TEXT);
CREATE TABLE IF NOT EXISTS notes (id INTEGER PRIMARY KEY, user_id INTEGER, note_key TEXT, note_value TEXT, description TEXT, folder_id INTEGER, updated_at TEXT);
CREATE TABLE IF NOT EXISTS folders (id INTEGER PRIMARY KEY, user_id INTEGER, name TEXT, parent_id INTEGER);
CREATE TABLE IF NOT EXISTS note_history (id INTEGER PRIMARY KEY, note_id INTEGER, user_id INTEGER, note_key TEXT, note_value TEXT, description TEXT, folder_id INTEGER, updated_at TEXT);
CREATE TABLE IF NOT EXISTS attachments (id INTEGER PRIMARY KEY, note_id INTEGER, user_id INTEGER, filename TEXT, file_data BLOB, file_size INTEGER, uploaded_at TEXT);
CREATE TABLE IF NOT EXISTS audit_log (id INTEGER PRIMARY KEY, user_id INTEGER, action TEXT, entity_type TEXT, entity_id INTEGER, old_values TEXT, new_values TEXT, timestamp TEXT, ip_address TEXT);
CREATE TABLE IF NOT EXISTS user_sessions (id INTEGER PRIMARY KEY, user_id INTEGER, session_id TEXT, login_time TEXT, logout_time TEXT, ip_address TEXT, user_agent TEXT);
CREATE TABLE IF NOT EXISTS sync_queue (id INTEGER PRIMARY KEY, entity_type TEXT, entity_id INTEGER, operation TEXT, payload TEXT, changed_at TEXT, synced_at TEXT);
"""

def make_test_db():
    """Create a temporary SQLite DB with the full schema. Returns (fd, path)."""
    fd, path = tempfile.mkstemp()
    with sqlite3.connect(path) as con:
        con.executescript(_SCHEMA)
    return fd, path

def configure_test_app(app, db_path):
    """Apply standard test configuration to a Flask app."""
    import evernothing
    evernothing.DB = db_path
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['SECRET_KEY'] = 'test_key'
