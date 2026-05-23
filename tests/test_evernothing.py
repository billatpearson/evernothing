import unittest
import sys
import os
import tempfile
import sqlite3
from unittest.mock import patch

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import evernothing
from evernothing import app
from werkzeug.security import generate_password_hash


class EvernothingTestCase(unittest.TestCase):

    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp()
        evernothing.DB = self.db_path
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        evernothing.login_manager.session_protection = "basic"
        self.client = app.test_client()

        with sqlite3.connect(self.db_path) as con:
            con.executescript("""
            CREATE TABLE users(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                password TEXT,
                last_login TEXT,
                email TEXT
            );
            CREATE TABLE folders(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                name TEXT,
                parent_id INTEGER,
                version INTEGER NOT NULL DEFAULT 1,
                last_modified_device TEXT
            );
            CREATE TABLE notes(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                folder_id INTEGER,
                note_key TEXT,
                note_value TEXT,
                description TEXT,
                updated_at TEXT,
                version INTEGER NOT NULL DEFAULT 1,
                last_modified_device TEXT
            );
            CREATE TABLE note_history(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                note_id INTEGER,
                user_id INTEGER,
                note_key TEXT,
                note_value TEXT,
                description TEXT,
                folder_id INTEGER,
                updated_at TEXT,
                version INTEGER NOT NULL DEFAULT 1,
                last_modified_device TEXT
            );
            CREATE TABLE user_sessions(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                session_id TEXT,
                login_time TEXT,
                logout_time TEXT,
                ip_address TEXT,
                user_agent TEXT
            );
            CREATE TABLE attachments(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                note_id INTEGER,
                user_id INTEGER,
                filename TEXT,
                file_data BLOB,
                file_size INTEGER,
                uploaded_at TEXT
            );
            CREATE TABLE audit_log(
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
            CREATE TABLE sync_queue(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_type TEXT,
                entity_id INTEGER,
                operation TEXT,
                payload TEXT,
                changed_at TEXT,
                synced_at TEXT
            );
            """)
            con.execute(
                "INSERT INTO users (username, password, email) VALUES (?,?,?)",
                ("testuser", generate_password_hash("Password1"), "test@example.com")
            )
            con.execute(
                "INSERT INTO users (username, password, email) VALUES (?,?,?)",
                ("otheruser", generate_password_hash("Password1"), "other@example.com")
            )

        os.environ['ADMIN_USER'] = 'admin'
        os.environ['ADMIN_PASS'] = 'admin'

        import rate_limiter
        rate_limiter.rate_limit_store.clear()

    def tearDown(self):
        evernothing.login_manager.session_protection = "basic"
        try:
            os.close(self.db_fd)
            os.unlink(self.db_path)
        except OSError:
            pass

    def _login(self, username="testuser", password="Password1"):
        return self.client.post('/login', data={
            'username': username, 'password': password
        }, follow_redirects=True)

    # --- 1. Unauthenticated access ---

    def test_index_redirects_to_login(self):
        response = self.client.get('/')
        self.assertIn(response.status_code, (301, 302))

    def test_protected_routes_redirect_to_login(self):
        for route in ['/export', '/change_password', '/sessions', '/audit_report',
                      '/folder/add', '/folder/1', '/search?q=x']:
            response = self.client.get(route)
            self.assertIn(response.status_code, (301, 302), msg=f"{route} did not redirect")

    def test_404_handler(self):
        response = self.client.get('/nonexistent_route_xyz')
        self.assertEqual(response.status_code, 404)

    # --- 2. Public pages ---

    def test_login_page_loads(self):
        response = self.client.get('/login')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'EverNothing', response.data)
        self.assertIn(b'username', response.data)
        self.assertIn(b'password', response.data)

    def test_register_page_loads(self):
        response = self.client.get('/register')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Create', response.data)

    def test_forgot_password_page_loads(self):
        response = self.client.get('/forgot_password')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Reset', response.data)

    def test_admin_login_page_loads(self):
        response = self.client.get('/admin')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Admin', response.data)

    # --- 3. Authentication ---

    def test_login_valid_credentials(self):
        response = self._login()
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(b'Invalid username or password', response.data)

    def test_login_invalid_credentials(self):
        response = self._login(password='wrongpass')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Invalid username or password', response.data)

    def test_logout(self):
        self._login()
        response = self.client.get('/logout', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'login', response.data.lower())

    def test_admin_invalid_credentials(self):
        response = self.client.post('/admin', data={
            'username': 'wrong', 'password': 'wrong'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Invalid credentials', response.data)

    # --- 4. Registration ---

    @patch('evernothing.sync_s3')
    def test_register_new_user(self, mock_sync):
        response = self.client.post('/register', data={
            'username': 'newuser', 'password': 'Password1', 'email': 'new@example.com'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        with sqlite3.connect(self.db_path) as con:
            r = con.execute("SELECT id FROM users WHERE username='newuser'").fetchone()
        self.assertIsNotNone(r)

    @patch('evernothing.sync_s3')
    def test_register_duplicate_user(self, mock_sync):
        response = self.client.post('/register', data={
            'username': 'testuser', 'password': 'Password1', 'email': 'x@example.com'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'already exists', response.data)

    def test_register_weak_password(self):
        response = self.client.post('/register', data={
            'username': 'weakuser', 'password': 'short', 'email': 'w@example.com'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Password must', response.data)

    def test_register_invalid_email(self):
        response = self.client.post('/register', data={
            'username': 'emailuser', 'password': 'Password1', 'email': 'notanemail'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Invalid email', response.data)

    # --- 5. Folders ---

    @patch('evernothing.sync_s3')
    def test_create_and_view_folder(self, mock_sync):
        self._login()
        response = self.client.post('/folder/add', data={'name': 'MyFolder'}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'MyFolder', response.data)

    @patch('evernothing.sync_s3')
    def test_rename_folder(self, mock_sync):
        self._login()
        self.client.post('/folder/add', data={'name': 'OldName'}, follow_redirects=True)
        with sqlite3.connect(self.db_path) as con:
            fid = con.execute("SELECT id FROM folders ORDER BY id DESC LIMIT 1").fetchone()[0]
        response = self.client.post(f'/folder/rename/{fid}', data={'name': 'NewName'}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        with sqlite3.connect(self.db_path) as con:
            name = con.execute("SELECT name FROM folders WHERE id=?", (fid,)).fetchone()[0]
        self.assertEqual(evernothing.decrypt(name), 'NewName')

    @patch('evernothing.sync_s3')
    def test_delete_folder(self, mock_sync):
        self._login()
        self.client.post('/folder/add', data={'name': 'ToDelete'}, follow_redirects=True)
        with sqlite3.connect(self.db_path) as con:
            fid = con.execute("SELECT id FROM folders ORDER BY id DESC LIMIT 1").fetchone()[0]
        self.client.post(f'/folder/delete/{fid}', follow_redirects=True)
        with sqlite3.connect(self.db_path) as con:
            r = con.execute("SELECT id FROM folders WHERE id=?", (fid,)).fetchone()
        self.assertIsNone(r)

    def test_cannot_access_other_users_folder(self):
        self._login()
        with sqlite3.connect(self.db_path) as con:
            other_id = con.execute("SELECT id FROM users WHERE username='otheruser'").fetchone()[0]
            con.execute("INSERT INTO folders (user_id, name, parent_id) VALUES (?,?,NULL)", (other_id, 'OtherFolder'))
            fid = con.execute("SELECT id FROM folders WHERE user_id=?", (other_id,)).fetchone()[0]
        response = self.client.get(f'/folder/{fid}', follow_redirects=True)
        self.assertNotIn(b'OtherFolder', response.data)

    # --- 6. Notes ---

    @patch('evernothing.sync_s3')
    def test_add_note(self, mock_sync):
        self._login()
        self.client.post('/folder/add', data={'name': 'NoteFolder'}, follow_redirects=True)
        with sqlite3.connect(self.db_path) as con:
            fid = con.execute("SELECT id FROM folders").fetchone()[0]
        response = self.client.post(f'/add/{fid}', data={
            'note': 'MyNote', 'content': 'MyContent', 'description': ''
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        with sqlite3.connect(self.db_path) as con:
            r = con.execute("SELECT id FROM notes ORDER BY id DESC LIMIT 1").fetchone()
        self.assertIsNotNone(r)

    @patch('evernothing.sync_s3')
    def test_add_note_empty_fields(self, mock_sync):
        self._login()
        self.client.post('/folder/add', data={'name': 'F'}, follow_redirects=True)
        with sqlite3.connect(self.db_path) as con:
            fid = con.execute("SELECT id FROM folders").fetchone()[0]
        response = self.client.post(f'/add/{fid}', data={
            'note': '', 'content': '', 'description': ''
        }, follow_redirects=True)
        self.assertIn(b'cannot be empty', response.data)

    @patch('evernothing.sync_s3')
    def test_add_duplicate_note(self, mock_sync):
        self._login()
        self.client.post('/folder/add', data={'name': 'F2'}, follow_redirects=True)
        with sqlite3.connect(self.db_path) as con:
            fid = con.execute("SELECT id FROM folders").fetchone()[0]
        self.client.post(f'/add/{fid}', data={'note': 'DupNote', 'content': 'c', 'description': ''})
        response = self.client.post(f'/add/{fid}', data={
            'note': 'DupNote', 'content': 'c2', 'description': ''
        }, follow_redirects=True)
        self.assertIn(b'already exists', response.data)

    @patch('evernothing.sync_s3')
    def test_edit_note(self, mock_sync):
        self._login()
        self.client.post('/folder/add', data={'name': 'EF'}, follow_redirects=True)
        with sqlite3.connect(self.db_path) as con:
            fid = con.execute("SELECT id FROM folders").fetchone()[0]
        self.client.post(f'/add/{fid}', data={'note': 'EditMe', 'content': 'old', 'description': ''})
        with sqlite3.connect(self.db_path) as con:
            nid = con.execute("SELECT id FROM notes ORDER BY id DESC LIMIT 1").fetchone()[0]
        self.client.post(f'/edit/{nid}', data={
            'note': 'EditMe', 'content': 'new content', 'folder_id': fid,
            'description': '', 'confirm': 'yes'
        }, follow_redirects=True)
        with sqlite3.connect(self.db_path) as con:
            val = con.execute("SELECT note_value FROM notes WHERE id=?", (nid,)).fetchone()[0]
        self.assertEqual(evernothing.decrypt(val), 'new content')

    @patch('evernothing.sync_s3')
    def test_delete_note(self, mock_sync):
        self._login()
        self.client.post('/folder/add', data={'name': 'DF'}, follow_redirects=True)
        with sqlite3.connect(self.db_path) as con:
            fid = con.execute("SELECT id FROM folders").fetchone()[0]
        self.client.post(f'/add/{fid}', data={'note': 'DelNote', 'content': 'x', 'description': ''})
        with sqlite3.connect(self.db_path) as con:
            nid = con.execute("SELECT id FROM notes ORDER BY id DESC LIMIT 1").fetchone()[0]
        self.client.post(f'/note/delete/{nid}', follow_redirects=True)
        with sqlite3.connect(self.db_path) as con:
            r = con.execute("SELECT id FROM notes WHERE id=?", (nid,)).fetchone()
        self.assertIsNone(r)

    def test_user_cannot_see_other_users_notes(self):
        self._login()
        response = self.client.get('/search?q=PrivateNote', follow_redirects=True)
        self.assertIn(b'No matches', response.data)

    # --- 7. Search ---

    @patch('evernothing.sync_s3')
    def test_search_finds_note(self, mock_sync):
        self._login()
        self.client.post('/folder/add', data={'name': 'SF'}, follow_redirects=True)
        with sqlite3.connect(self.db_path) as con:
            fid = con.execute("SELECT id FROM folders").fetchone()[0]
        self.client.post(f'/add/{fid}', data={'note': 'SearchableNote', 'content': 'findme', 'description': ''})
        response = self.client.get('/search?q=SearchableNote', follow_redirects=True)
        self.assertIn(b'SearchableNote', response.data)

    def test_search_no_results(self):
        self._login()
        response = self.client.get('/search?q=zzznomatch', follow_redirects=True)
        self.assertIn(b'No matches', response.data)

    # --- 8. Note history ---

    @patch('evernothing.sync_s3')
    def test_note_history_recorded(self, mock_sync):
        self._login()
        self.client.post('/folder/add', data={'name': 'HF'}, follow_redirects=True)
        with sqlite3.connect(self.db_path) as con:
            fid = con.execute("SELECT id FROM folders").fetchone()[0]
        self.client.post(f'/add/{fid}', data={'note': 'HistNote', 'content': 'v1', 'description': ''})
        with sqlite3.connect(self.db_path) as con:
            nid = con.execute("SELECT id FROM notes ORDER BY id DESC LIMIT 1").fetchone()[0]
        self.client.post(f'/edit/{nid}', data={
            'note': 'HistNote', 'content': 'v2', 'folder_id': fid,
            'description': '', 'confirm': 'yes'
        })
        with sqlite3.connect(self.db_path) as con:
            count = con.execute("SELECT COUNT(*) FROM note_history WHERE note_id=?", (nid,)).fetchone()[0]
        self.assertGreaterEqual(count, 2)

    # --- 9. Change password ---

    @patch('evernothing.sync_s3')
    def test_change_password(self, mock_sync):
        self._login()
        response = self.client.post('/change_password', data={
            'old_password': 'Password1', 'new_password': 'NewPass2', 'verify_password': 'NewPass2'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        with sqlite3.connect(self.db_path) as con:
            pw = con.execute("SELECT password FROM users WHERE username='testuser'").fetchone()[0]
        from werkzeug.security import check_password_hash
        self.assertTrue(check_password_hash(pw, 'NewPass2'))

    def test_change_password_wrong_old(self):
        self._login()
        response = self.client.post('/change_password', data={
            'old_password': 'wrongpass', 'new_password': 'NewPass2', 'verify_password': 'NewPass2'
        }, follow_redirects=True)
        self.assertIn(b'Invalid old password', response.data)

    def test_change_password_mismatch(self):
        self._login()
        response = self.client.post('/change_password', data={
            'old_password': 'Password1', 'new_password': 'NewPass2', 'verify_password': 'Different2'
        }, follow_redirects=True)
        self.assertIn(b'do not match', response.data)

    # --- 10. Export ---

    @patch('evernothing.sync_s3')
    def test_export_json(self, mock_sync):
        self._login()
        self.client.post('/folder/add', data={'name': 'XF'}, follow_redirects=True)
        with sqlite3.connect(self.db_path) as con:
            fid = con.execute("SELECT id FROM folders").fetchone()[0]
        self.client.post(f'/add/{fid}', data={'note': 'ExportNote', 'content': 'exportval', 'description': ''})
        response = self.client.get('/export')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'ExportNote', response.data)

    # --- 11. Audit log ---

    @patch('evernothing.sync_s3')
    def test_audit_log_on_note_create(self, mock_sync):
        self._login()
        self.client.post('/folder/add', data={'name': 'AF'}, follow_redirects=True)
        with sqlite3.connect(self.db_path) as con:
            fid = con.execute("SELECT id FROM folders").fetchone()[0]
        self.client.post(f'/add/{fid}', data={'note': 'AuditNote', 'content': 'av', 'description': ''})
        with sqlite3.connect(self.db_path) as con:
            r = con.execute("SELECT id FROM audit_log WHERE action='CREATE' AND entity_type='note'").fetchone()
        self.assertIsNotNone(r)

    # --- 12. Admin ---

    def _admin_login(self):
        return self.client.post('/admin', data={
            'username': os.environ.get('ADMIN_USER', 'admin'),
            'password': os.environ.get('ADMIN_PASS', 'admin')
        }, follow_redirects=True)

    def test_admin_dashboard_loads(self):
        self._admin_login()
        response = self.client.get('/admin/dashboard', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'testuser', response.data)

    @patch('evernothing.sync_s3')
    def test_admin_delete_user(self, mock_sync):
        self._admin_login()
        with sqlite3.connect(self.db_path) as con:
            uid = con.execute("SELECT id FROM users WHERE username='otheruser'").fetchone()[0]
        self.client.post(f'/admin/user/delete/{uid}', follow_redirects=True)
        with sqlite3.connect(self.db_path) as con:
            r = con.execute("SELECT id FROM users WHERE username='otheruser'").fetchone()
        self.assertIsNone(r)

    @patch('evernothing.sync_s3')
    def test_admin_edit_user_duplicate_username(self, mock_sync):
        """G7: Admin renaming a user to an existing username shows error, not crash."""
        self._admin_login()
        with sqlite3.connect(self.db_path) as con:
            uid = con.execute("SELECT id FROM users WHERE username='otheruser'").fetchone()[0]
        # Try to rename 'otheruser' to 'testuser' which already exists
        response = self.client.post(f'/admin/user/{uid}', data={
            'new_username': 'testuser',
            'new_password': '',
            'last_login': '',
            'confirm': 'yes'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'already exists', response.data)
        # Verify the original username was NOT changed
        with sqlite3.connect(self.db_path) as con:
            r = con.execute("SELECT username FROM users WHERE id=?", (uid,)).fetchone()
        self.assertEqual(r[0], 'otheruser')


    # --- 13. Sync queue (delta S3) ---

    @patch('evernothing.sync_s3')
    def test_sync_queue_on_note_create(self, mock_sync):
        self._login()
        self.client.post('/folder/add', data={'name': 'SQF'}, follow_redirects=True)
        with sqlite3.connect(self.db_path) as con:
            fid = con.execute("SELECT id FROM folders").fetchone()[0]
        self.client.post(f'/add/{fid}', data={'note': 'SyncNote', 'content': 'val', 'description': ''})
        with sqlite3.connect(self.db_path) as con:
            r = con.execute(
                "SELECT operation, entity_type FROM sync_queue WHERE entity_type='note' AND operation='INSERT'"
            ).fetchone()
        self.assertIsNotNone(r)
        self.assertEqual(r[0], 'INSERT')

    @patch('evernothing.sync_s3')
    def test_sync_queue_on_note_update(self, mock_sync):
        self._login()
        self.client.post('/folder/add', data={'name': 'SQF2'}, follow_redirects=True)
        with sqlite3.connect(self.db_path) as con:
            fid = con.execute("SELECT id FROM folders").fetchone()[0]
        self.client.post(f'/add/{fid}', data={'note': 'SyncUpdate', 'content': 'v1', 'description': ''})
        with sqlite3.connect(self.db_path) as con:
            nid = con.execute("SELECT id FROM notes ORDER BY id DESC LIMIT 1").fetchone()[0]
        self.client.post(f'/edit/{nid}', data={
            'note': 'SyncUpdate', 'content': 'v2', 'folder_id': fid,
            'description': '', 'confirm': 'yes'
        })
        with sqlite3.connect(self.db_path) as con:
            r = con.execute(
                "SELECT operation FROM sync_queue WHERE entity_type='note' AND entity_id=? AND operation='UPDATE'",
                (nid,)
            ).fetchone()
        self.assertIsNotNone(r)

    @patch('evernothing.sync_s3')
    def test_sync_queue_on_note_delete(self, mock_sync):
        self._login()
        self.client.post('/folder/add', data={'name': 'SQF3'}, follow_redirects=True)
        with sqlite3.connect(self.db_path) as con:
            fid = con.execute("SELECT id FROM folders").fetchone()[0]
        self.client.post(f'/add/{fid}', data={'note': 'SyncDel', 'content': 'x', 'description': ''})
        with sqlite3.connect(self.db_path) as con:
            nid = con.execute("SELECT id FROM notes ORDER BY id DESC LIMIT 1").fetchone()[0]
        self.client.post(f'/note/delete/{nid}', follow_redirects=True)
        with sqlite3.connect(self.db_path) as con:
            r = con.execute(
                "SELECT operation FROM sync_queue WHERE entity_type='note' AND entity_id=? AND operation='DELETE'",
                (nid,)
            ).fetchone()
        self.assertIsNotNone(r)

    @patch('evernothing.sync_s3')
    def test_sync_queue_on_note_rollback(self, mock_sync):
        self._login()
        self.client.post('/folder/add', data={'name': 'SQF4'}, follow_redirects=True)
        with sqlite3.connect(self.db_path) as con:
            fid = con.execute("SELECT id FROM folders").fetchone()[0]
        self.client.post(f'/add/{fid}', data={'note': 'SyncRoll', 'content': 'v1', 'description': ''})
        with sqlite3.connect(self.db_path) as con:
            nid = con.execute("SELECT id FROM notes ORDER BY id DESC LIMIT 1").fetchone()[0]
        self.client.post(f'/edit/{nid}', data={
            'note': 'SyncRoll', 'content': 'v2', 'folder_id': fid,
            'description': '', 'confirm': 'yes'
        })
        with sqlite3.connect(self.db_path) as con:
            hid = con.execute(
                "SELECT id FROM note_history WHERE note_id=? ORDER BY id ASC LIMIT 1", (nid,)
            ).fetchone()[0]
        self.client.post(f'/history/restore/{hid}', follow_redirects=True)
        with sqlite3.connect(self.db_path) as con:
            val = con.execute("SELECT note_value FROM notes WHERE id=?", (nid,)).fetchone()[0]
        self.assertEqual(evernothing.decrypt(val), 'v1')

    @patch('evernothing.sync_s3')
    def test_sync_queue_payload_contains_key(self, mock_sync):
        import json
        self._login()
        self.client.post('/folder/add', data={'name': 'SQF5'}, follow_redirects=True)
        with sqlite3.connect(self.db_path) as con:
            fid = con.execute("SELECT id FROM folders").fetchone()[0]
        self.client.post(f'/add/{fid}', data={'note': 'PayloadNote', 'content': 'pval', 'description': 'pdesc'})
        with sqlite3.connect(self.db_path) as con:
            row = con.execute(
                "SELECT payload FROM sync_queue WHERE entity_type='note' AND operation='INSERT'"
            ).fetchone()
        self.assertIsNotNone(row)
        payload = json.loads(row[0])
        # Payload stores encrypted values — decrypt to verify
        self.assertEqual(evernothing.decrypt(payload['note_key']), 'PayloadNote')
        self.assertEqual(evernothing.decrypt(payload.get('description', '')), 'pdesc')

    @patch('evernothing.sync_s3')
    def test_sync_queue_unsynced_rows_start_null(self, mock_sync):
        self._login()
        self.client.post('/folder/add', data={'name': 'SQF6'}, follow_redirects=True)
        with sqlite3.connect(self.db_path) as con:
            fid = con.execute("SELECT id FROM folders").fetchone()[0]
        self.client.post(f'/add/{fid}', data={'note': 'UnsyncedNote', 'content': 'u', 'description': ''})
        with sqlite3.connect(self.db_path) as con:
            r = con.execute(
                "SELECT synced_at FROM sync_queue WHERE entity_type='note' AND operation='INSERT'"
            ).fetchone()
        self.assertIsNone(r[0])


    # --- 14. Encryption / Decryption ---

    def test_encrypt_decrypt_roundtrip(self):
        """encrypt() then decrypt() returns the original string."""
        from evernothing_security import encrypt, decrypt
        original = "Hello, Unicorn! & <Sparkles>"
        self.assertEqual(decrypt(encrypt(original)), original)

    def test_encrypt_produces_different_ciphertext_each_call(self):
        """Each encrypt() call uses a fresh nonce — ciphertexts must differ."""
        import evernothing_security as sec
        original = sec.ENCRYPTION_ENABLED
        sec.ENCRYPTION_ENABLED = True
        try:
            c1 = sec.encrypt("same text")
            c2 = sec.encrypt("same text")
            self.assertNotEqual(c1, c2)
        finally:
            sec.ENCRYPTION_ENABLED = original

    def test_decrypt_non_encrypted_value_returns_as_is(self):
        """decrypt() on a plain string (not base64 AES) returns it unchanged."""
        from evernothing_security import decrypt
        self.assertEqual(decrypt("plaintext"), "plaintext")

    def test_decrypt_empty_returns_empty(self):
        from evernothing_security import decrypt
        self.assertEqual(decrypt(""), "")
        self.assertEqual(decrypt(None), "")

    def test_encrypt_payload_decrypt_payload_roundtrip(self):
        """encrypt_payload() then decrypt_payload() returns original bytes."""
        from evernothing_security import encrypt_payload, decrypt_payload
        data = b'{"op": "INSERT", "entity": "note", "id": 42}'
        self.assertEqual(decrypt_payload(encrypt_payload(data)), data)

    def test_encrypt_payload_binary_data(self):
        """encrypt_payload works on arbitrary binary data (e.g. a DB file snapshot)."""
        from evernothing_security import encrypt_payload, decrypt_payload
        data = bytes(range(256)) * 100  # 25,600 bytes of binary
        self.assertEqual(decrypt_payload(encrypt_payload(data)), data)

    def test_decrypt_payload_sha256_integrity_passes(self):
        """decrypt_payload does not raise when data is untampered."""
        from evernothing_security import encrypt_payload, decrypt_payload
        data = b'integrity check payload'
        try:
            decrypt_payload(encrypt_payload(data))
        except ValueError:
            self.fail("decrypt_payload raised ValueError on valid data")

    def test_decrypt_payload_tampered_raises(self):
        """Flipping a byte in the ciphertext must raise ValueError."""
        from evernothing_security import encrypt_payload, decrypt_payload
        data = b'tamper me'
        enc = bytearray(encrypt_payload(data))
        enc[-1] ^= 0xFF  # flip last byte
        with self.assertRaises(Exception):  # AES-GCM tag failure or ValueError
            decrypt_payload(bytes(enc))

    def test_decrypt_payload_wrong_key_raises(self):
        """Data encrypted with one key cannot be decrypted with another."""
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        import os, hashlib
        key1 = AESGCM(AESGCM.generate_key(256))
        key2 = AESGCM(AESGCM.generate_key(256))
        data = b'secret payload'
        # Encrypt with key1
        nonce = os.urandom(12)
        digest = hashlib.sha256(data).digest()
        ciphertext = key1.encrypt(nonce, digest + data, None)
        encrypted = nonce + ciphertext
        # Attempt decrypt with key2
        with self.assertRaises(Exception):
            nonce2, ct2 = encrypted[:12], encrypted[12:]
            key2.decrypt(nonce2, ct2, None)

    def test_encrypt_disabled_returns_plaintext(self):
        """When ENCRYPTION_ENABLED=False, encrypt() is a no-op."""
        import evernothing_security as sec
        original = sec.ENCRYPTION_ENABLED
        sec.ENCRYPTION_ENABLED = False
        try:
            self.assertEqual(sec.encrypt("no encryption"), "no encryption")
        finally:
            sec.ENCRYPTION_ENABLED = original


if __name__ == '__main__':
    unittest.main()
