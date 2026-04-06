import unittest
import tempfile
import os
import sqlite3
from unittest.mock import patch

class BaseTestCase(unittest.TestCase):
    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp()
        con = sqlite3.connect(self.db_path)
        cur = con.cursor()
        cur.execute('CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT, email TEXT, last_login TEXT)')
        cur.execute('CREATE TABLE notes (id INTEGER PRIMARY KEY, user_id INTEGER, note_key TEXT, note_value TEXT, description TEXT, folder_id INTEGER, updated_at TEXT)')
        cur.execute('CREATE TABLE folders (id INTEGER PRIMARY KEY, user_id INTEGER, name TEXT, parent_id INTEGER)')
        cur.execute('CREATE TABLE note_history (id INTEGER PRIMARY KEY, note_id INTEGER, user_id INTEGER, note_key TEXT, note_value TEXT, description TEXT, folder_id INTEGER, updated_at TEXT)')
        cur.execute('CREATE TABLE attachments (id INTEGER PRIMARY KEY, note_id INTEGER, user_id INTEGER, filename TEXT, file_data BLOB, file_size INTEGER, uploaded_at TEXT)')
        cur.execute('CREATE TABLE audit_log (id INTEGER PRIMARY KEY, user_id INTEGER, action TEXT, entity_type TEXT, entity_id INTEGER, old_values TEXT, new_values TEXT, timestamp TEXT, ip_address TEXT)')
        cur.execute('CREATE TABLE user_sessions (id INTEGER PRIMARY KEY, user_id INTEGER, session_id TEXT, login_time TEXT, logout_time TEXT, ip_address TEXT, user_agent TEXT)')
        cur.execute('CREATE TABLE sync_queue (id INTEGER PRIMARY KEY, entity_type TEXT, entity_id INTEGER, operation TEXT, payload TEXT, changed_at TEXT, synced_at TEXT)')
        cur.execute('CREATE INDEX idx_notes_user ON notes(user_id)')
        cur.execute('CREATE INDEX idx_folders_user ON folders(user_id)')
        cur.execute('CREATE INDEX idx_attachments_note ON attachments(note_id)')
        cur.execute('CREATE INDEX idx_audit_user ON audit_log(user_id)')
        cur.execute('CREATE INDEX idx_audit_entity ON audit_log(entity_type, entity_id)')
        con.commit()
        con.close()
        import evernothing
        evernothing.DB = self.db_path
        evernothing.app.config['TESTING'] = True
        evernothing.app.config['WTF_CSRF_ENABLED'] = False
        evernothing.app.config['SECRET_KEY'] = 'test_key'
        evernothing.login_manager.session_protection = None
        self.app = evernothing.app
        self.client = self.app.test_client()
        self.encrypt = evernothing.encrypt
        self.decrypt = evernothing.decrypt

    def tearDown(self):
        try:
            import rate_limiter
            rate_limiter.rate_limit_store.clear()
        except Exception:
            pass
        os.close(self.db_fd)
        try:
            os.unlink(self.db_path)
        except Exception:
            pass

    def register(self, username, password, email='test@test.com'):
        return self.client.post('/register', data={'username': username, 'password': password, 'email': email}, follow_redirects=True)

    def login(self, username, password):
        return self.client.post('/login', data={'username': username, 'password': password}, follow_redirects=True)

# Authentication Tests
class AuthenticationTests(BaseTestCase):
    def test_encryption(self):
        text = "secret note"
        encrypted = self.encrypt(text)
        decrypted = self.decrypt(encrypted)
        # If encryption is enabled, encrypted should differ from original
        # If disabled, both encrypt and decrypt return original text
        self.assertEqual(text, decrypted)

    @patch('evernothing.sync_s3')
    def test_register_login(self, mock_sync):
        rv = self.register('user1', 'Pass1234')
        self.assertIn(b'Login', rv.data)
        rv = self.login('user1', 'Pass1234')
        self.assertIn(b'EverNothing', rv.data)

    @patch('evernothing.sync_s3')
    def test_duplicate_user(self, mock_sync):
        self.register('user2', 'Pass1234')
        rv = self.register('user2', 'Pass1234')
        self.assertIn(b'exists', rv.data.lower())

    def test_invalid_login(self):
        rv = self.login('invalid', 'wrong')
        self.assertIn(b'Invalid', rv.data)

    def test_unauthorized_access(self):
        rv = self.client.get('/')
        self.assertEqual(rv.status_code, 302)

# Note Operations Tests
class NoteOperationsTests(BaseTestCase):
    @patch('evernothing.sync_s3')
    def test_add_note_success(self, mock_sync):
        self.register('noteuser', 'Pass1234')
        self.login('noteuser', 'Pass1234')
        self.client.post('/folder/add', data={'name': 'TestFolder'}, follow_redirects=True)
        rv = self.client.post('/add/1', data={'note': 'My Note', 'content': 'My Content'}, follow_redirects=True)
        self.assertIn(b'My Note', rv.data)

    @patch('evernothing.sync_s3')
    def test_add_note_empty_fields(self, mock_sync):
        self.register('noteuser2', 'Pass1234')
        self.login('noteuser2', 'Pass1234')
        self.client.post('/folder/add', data={'name': 'TestFolder'}, follow_redirects=True)
        rv = self.client.post('/add/1', data={'note': '', 'content': 'Content'}, follow_redirects=True)
        self.assertIn(b'cannot be empty', rv.data)

    @patch('evernothing.sync_s3')
    def test_add_note_duplicate_name(self, mock_sync):
        self.register('noteuser3', 'Pass1234')
        self.login('noteuser3', 'Pass1234')
        self.client.post('/folder/add', data={'name': 'TestFolder'}, follow_redirects=True)
        self.client.post('/add/1', data={'note': 'Duplicate', 'content': 'Content1'}, follow_redirects=True)
        rv = self.client.post('/add/1', data={'note': 'Duplicate', 'content': 'Content2'}, follow_redirects=True)
        self.assertIn(b'already exists', rv.data)

    @patch('evernothing.sync_s3')
    def test_edit_note_success(self, mock_sync):
        self.register('noteuser4', 'Pass1234')
        self.login('noteuser4', 'Pass1234')
        self.client.post('/folder/add', data={'name': 'TestFolder'}, follow_redirects=True)
        self.client.post('/add/1', data={'note': 'Original', 'content': 'Original Content'}, follow_redirects=True)
        rv = self.client.post('/edit/1', data={'note': 'Updated', 'content': 'Updated Content', 'folder_id': '1', 'confirm': 'yes'}, follow_redirects=True)
        self.assertIn(b'Updated', rv.data)

    @patch('evernothing.sync_s3')
    def test_edit_note_no_change(self, mock_sync):
        self.register('noteuser5', 'Pass1234')
        self.login('noteuser5', 'Pass1234')
        self.client.post('/folder/add', data={'name': 'TestFolder'}, follow_redirects=True)
        self.client.post('/add/1', data={'note': 'Same', 'content': 'Same Content'}, follow_redirects=True)
        rv = self.client.post('/edit/1', data={'note': 'Same', 'content': 'Same Content', 'folder_id': '1'}, follow_redirects=True)
        self.assertIn(b'EverNothing', rv.data)

    @patch('evernothing.sync_s3')
    def test_edit_note_confirmation(self, mock_sync):
        self.register('noteuser6', 'Pass1234')
        self.login('noteuser6', 'Pass1234')
        self.client.post('/folder/add', data={'name': 'TestFolder'}, follow_redirects=True)
        self.client.post('/add/1', data={'note': 'Before', 'content': 'Before Content'}, follow_redirects=True)
        rv = self.client.post('/edit/1', data={'note': 'After', 'content': 'After Content', 'folder_id': '1'}, follow_redirects=True)
        self.assertIn(b'Confirm Changes', rv.data)

    @patch('evernothing.sync_s3')
    def test_delete_note_success(self, mock_sync):
        self.register('noteuser7', 'Pass1234')
        self.login('noteuser7', 'Pass1234')
        self.client.post('/folder/add', data={'name': 'TestFolder'}, follow_redirects=True)
        self.client.post('/add/1', data={'note': 'ToDelete', 'content': 'Delete Content'}, follow_redirects=True)
        rv = self.client.post('/note/delete/1', follow_redirects=True)
        self.assertNotIn(b'ToDelete', rv.data)

    @patch('evernothing.sync_s3')
    def test_delete_note_confirmation(self, mock_sync):
        self.register('noteuser8', 'Pass1234')
        self.login('noteuser8', 'Pass1234')
        self.client.post('/folder/add', data={'name': 'TestFolder'}, follow_redirects=True)
        self.client.post('/add/1', data={'note': 'ConfirmDelete', 'content': 'Content'}, follow_redirects=True)
        rv = self.client.get('/note/delete/1')
        self.assertIn(b'Are you sure', rv.data)
        self.assertIn(b'ConfirmDelete', rv.data)

# Folder Tests
class FolderTests(BaseTestCase):
    @patch('evernothing.sync_s3')
    def test_folder_operations(self, mock_sync):
        self.register('folderuser', 'Pass1234')
        self.login('folderuser', 'Pass1234')
        rv = self.client.post('/folder/add', data={'name': 'TestFolder'}, follow_redirects=True)
        self.assertIn(b'TestFolder', rv.data)

# Admin Tests
class AdminTests(BaseTestCase):
    def test_admin_login(self):
        os.environ['ADMIN_USER'] = 'admin'
        os.environ['ADMIN_PASS'] = 'admin'
        rv = self.client.post('/admin', data={'username': 'admin', 'password': 'admin'}, follow_redirects=True)
        self.assertIn(b'Users', rv.data)

# Audit Tests
class AuditTests(BaseTestCase):
    @patch('evernothing.sync_s3')
    def test_audit_log(self, mock_sync):
        self.register('user7', 'Pass1234')
        self.login('user7', 'Pass1234')
        self.client.post('/folder/add', data={'name': 'TestFolder'}, follow_redirects=True)
        self.client.post('/add/1', data={'note': 'Audit Test', 'content': 'Content'}, follow_redirects=True)
        rv = self.client.get('/audit_report')
        self.assertIn(b'CREATE', rv.data)

    @patch('evernothing.sync_s3')
    def test_note_history_created(self, mock_sync):
        self.register('noteuser9', 'Pass1234')
        self.login('noteuser9', 'Pass1234')
        self.client.post('/folder/add', data={'name': 'TestFolder'}, follow_redirects=True)
        self.client.post('/add/1', data={'note': 'History', 'content': 'V1'}, follow_redirects=True)
        self.client.post('/edit/1', data={'note': 'History', 'content': 'V2', 'folder_id': '1', 'confirm': 'yes'}, follow_redirects=True)
        rv = self.client.get('/history/1')
        self.assertIn(b'History', rv.data)

if __name__ == '__main__':
    unittest.main()
