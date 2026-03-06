import unittest
import tempfile
import os
import sqlite3
from unittest.mock import patch

class EvernothingTestCase(unittest.TestCase):
    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp()
        
        con = sqlite3.connect(self.db_path)
        cur = con.cursor()
        cur.execute('CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT, email TEXT, last_login TEXT)')
        cur.execute('CREATE TABLE notes (id INTEGER PRIMARY KEY, user_id INTEGER, note_key TEXT, note_value TEXT, folder_id INTEGER, updated_at TEXT)')
        cur.execute('CREATE TABLE folders (id INTEGER PRIMARY KEY, user_id INTEGER, name TEXT, parent_id INTEGER)')
        cur.execute('CREATE TABLE note_history (id INTEGER PRIMARY KEY, note_id INTEGER, user_id INTEGER, note_key TEXT, note_value TEXT, folder_id INTEGER, updated_at TEXT)')
        cur.execute('CREATE TABLE attachments (id INTEGER PRIMARY KEY, note_id INTEGER, user_id INTEGER, filename TEXT, file_data BLOB, file_size INTEGER, uploaded_at TEXT)')
        cur.execute('CREATE TABLE audit_log (id INTEGER PRIMARY KEY, user_id INTEGER, action TEXT, entity_type TEXT, entity_id INTEGER, old_values TEXT, new_values TEXT, timestamp TEXT, ip_address TEXT)')
        cur.execute('CREATE TABLE user_sessions (id INTEGER PRIMARY KEY, user_id INTEGER, session_id TEXT, login_time TEXT, logout_time TEXT, ip_address TEXT, user_agent TEXT)')
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
        evernothing.app.config['SECRET_KEY'] = 'test_key'
        self.app = evernothing.app
        self.client = self.app.test_client()
        self.encrypt = evernothing.encrypt
        self.decrypt = evernothing.decrypt

    def tearDown(self):
        os.close(self.db_fd)
        try:
            os.unlink(self.db_path)
        except:
            pass

    def register(self, username, password='TestPass123', email='test@test.com'):
        return self.client.post('/register', data={'username': username, 'password': password, 'email': email}, follow_redirects=True)

    def login(self, username, password='TestPass123'):
        return self.client.post('/login', data={'username': username, 'password': password}, follow_redirects=True)

    def logout(self):
        return self.client.get('/logout', follow_redirects=True)

    def test_encryption(self):
        """Test encryption/decryption when enabled"""
        import evernothing
        text = "secret note"
        encrypted = self.encrypt(text)
        decrypted = self.decrypt(encrypted)
        
        # If encryption is enabled, encrypted should differ from original
        # If disabled, they should be the same
        if evernothing.ENCRYPTION_ENABLED:
            self.assertNotEqual(text, encrypted)
        
        # Decryption should always return original text
        self.assertEqual(text, decrypted)

    @patch('evernothing.sync_s3')
    def test_register_login(self, mock_sync):
        rv = self.register('user1')
        self.assertIn(b'Login', rv.data)
        rv = self.login('user1')
        self.assertIn(b'EverNothing', rv.data)

    @patch('evernothing.sync_s3')
    def test_duplicate_user(self, mock_sync):
        self.register('user2')
        rv = self.register('user2')
        self.assertIn(b'exists', rv.data.lower())

    def test_invalid_login(self):
        rv = self.login('invalid', 'wrong')
        self.assertIn(b'Invalid', rv.data)

    @patch('evernothing.sync_s3')
    def test_create_note(self, mock_sync):
        self.register('user3')
        self.login('user3')
        self.client.post('/folder/add', data={'name': 'TestFolder'}, follow_redirects=True)
        rv = self.client.post('/add/1', data={'note': 'Test Note', 'content': 'Test Content'}, follow_redirects=True)
        self.assertIn(b'Test Note', rv.data)

    @patch('evernothing.sync_s3')
    def test_edit_note(self, mock_sync):
        self.register('user4')
        self.login('user4')
        self.client.post('/folder/add', data={'name': 'TestFolder'}, follow_redirects=True)
        self.client.post('/add/1', data={'note': 'Original', 'content': 'Content'}, follow_redirects=True)
        rv = self.client.post('/edit/1', data={'note': 'Updated', 'content': 'New Content', 'folder_id': '1', 'confirm': 'yes'}, follow_redirects=True)
        self.assertIn(b'Updated', rv.data)

    @patch('evernothing.sync_s3')
    def test_delete_note(self, mock_sync):
        self.register('user5')
        self.login('user5')
        self.client.post('/folder/add', data={'name': 'TestFolder'}, follow_redirects=True)
        self.client.post('/add/1', data={'note': 'Delete Me', 'content': 'Content'}, follow_redirects=True)
        rv = self.client.post('/note/delete/1', follow_redirects=True)
        self.assertNotIn(b'Delete Me', rv.data)

    @patch('evernothing.sync_s3')
    def test_folder_operations(self, mock_sync):
        self.register('folderuser')
        self.login('folderuser')
        rv = self.client.post('/folder/add', data={'name': 'TestFolder'}, follow_redirects=True)
        self.assertIn(b'TestFolder', rv.data)

    def test_admin_login(self):
        os.environ['ADMIN_USER'] = 'admin'
        os.environ['ADMIN_PASS'] = 'admin'
        rv = self.client.post('/admin', data={'username': 'admin', 'password': 'admin'}, follow_redirects=True)
        self.assertIn(b'Admin Dashboard', rv.data)

    @patch('evernothing.sync_s3')
    def test_audit_log(self, mock_sync):
        self.register('user7')
        self.login('user7')
        self.client.post('/folder/add', data={'name': 'TestFolder'}, follow_redirects=True)
        self.client.post('/add/1', data={'note': 'Audit Test', 'content': 'Content'}, follow_redirects=True)
        rv = self.client.get('/audit_report')
        self.assertIn(b'CREATE', rv.data)

    def test_unauthorized_access(self):
        rv = self.client.get('/')
        self.assertEqual(rv.status_code, 302)

if __name__ == '__main__':
    unittest.main()
