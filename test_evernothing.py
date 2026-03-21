py import unittest
import tempfile
import os
import sqlite3
from unittest.mock import patch

# Test credentials read from environment with safe defaults for CI
TEST_PASSWORD = os.environ.get('TEST_PASSWORD', 'TestPass123')
TEST_EMAIL = os.environ.get('TEST_EMAIL', 'test@example.com')
ADMIN_USER = os.environ.get('ADMIN_USER', 'admin')
ADMIN_PASS = os.environ.get('ADMIN_PASS', 'admin')


class EvernothingTestCase(unittest.TestCase):

    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp()
        # CWE-400 fix: use context manager so connection always closes
        with sqlite3.connect(self.db_path) as con:
            cur = con.cursor()
            cur.execute('CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT, email TEXT, last_login TEXT)')
            cur.execute('CREATE TABLE notes (id INTEGER PRIMARY KEY, user_id INTEGER, note_key TEXT, note_value TEXT, description TEXT, folder_id INTEGER, updated_at TEXT)')
            cur.execute('CREATE TABLE folders (id INTEGER PRIMARY KEY, user_id INTEGER, name TEXT, parent_id INTEGER)')
            cur.execute('CREATE TABLE note_history (id INTEGER PRIMARY KEY, note_id INTEGER, user_id INTEGER, note_key TEXT, note_value TEXT, description TEXT, folder_id INTEGER, updated_at TEXT)')
            cur.execute('CREATE TABLE attachments (id INTEGER PRIMARY KEY, note_id INTEGER, user_id INTEGER, filename TEXT, file_data BLOB, file_size INTEGER, uploaded_at TEXT)')
            cur.execute('CREATE TABLE audit_log (id INTEGER PRIMARY KEY, user_id INTEGER, action TEXT, entity_type TEXT, entity_id INTEGER, old_values TEXT, new_values TEXT, timestamp TEXT, ip_address TEXT)')
            cur.execute('CREATE TABLE user_sessions (id INTEGER PRIMARY KEY, user_id INTEGER, session_id TEXT, login_time TEXT, logout_time TEXT, ip_address TEXT, user_agent TEXT)')
            cur.execute('CREATE INDEX idx_notes_user ON notes(user_id)')
            cur.execute('CREATE INDEX idx_folders_user ON folders(user_id)')
            cur.execute('CREATE INDEX idx_attachments_note ON attachments(note_id)')
            cur.execute('CREATE INDEX idx_audit_user ON audit_log(user_id)')
            cur.execute('CREATE INDEX idx_audit_entity ON audit_log(entity_type, entity_id)')
            con.commit()

        import evernothing
        evernothing.DB = self.db_path
        evernothing.app.config['TESTING'] = True
        evernothing.app.config['WTF_CSRF_ENABLED'] = False
        evernothing.app.config['SECRET_KEY'] = 'test_key'
        # Disable DB-backed session validation so test logins aren't invalidated
        evernothing.login_manager.session_protection = None
        self.app = evernothing.app
        self.client = self.app.test_client()
        self.encrypt = evernothing.encrypt
        self.decrypt = evernothing.decrypt

    def tearDown(self):
        # Clear rate limiter state so tests don't bleed into each other
        try:
            from rate_limiter import rate_limit_store
            rate_limit_store.clear()
        except Exception:
            pass
        os.close(self.db_fd)
        # CWE-703 fix: use specific exception
        try:
            os.unlink(self.db_path)
        except OSError:
            pass

    # --- helpers ---

    def register(self, username, password=None, email=None):
        return self.client.post('/register', data={
            'username': username,
            'password': password or TEST_PASSWORD,
            'email': email or TEST_EMAIL
        }, follow_redirects=True)

    def login(self, username, password=None):
        return self.client.post('/login', data={
            'username': username,
            'password': password or TEST_PASSWORD
        }, follow_redirects=True)

    def logout(self):
        return self.client.get('/logout', follow_redirects=True)

    def admin_login(self):
        os.environ['ADMIN_USER'] = ADMIN_USER
        os.environ['ADMIN_PASS'] = ADMIN_PASS
        return self.client.post('/admin', data={
            'username': ADMIN_USER,
            'password': ADMIN_PASS
        }, follow_redirects=True)

    # ------------------------------------------------------------------ #
    # 1. Encryption
    # ------------------------------------------------------------------ #

    def test_encryption_roundtrip(self):
        """Decryption always returns the original plaintext."""
        import evernothing
        text = "secret note content"
        encrypted = self.encrypt(text)
        self.assertEqual(text, self.decrypt(encrypted))

    def test_encryption_produces_different_ciphertext(self):
        """Each encryption call produces a unique ciphertext (random nonce)."""
        import evernothing
        if not evernothing.ENCRYPTION_ENABLED:
            self.skipTest("Encryption not enabled")
        text = "same text"
        self.assertNotEqual(self.encrypt(text), self.encrypt(text))

    def test_decrypt_empty_string(self):
        """Decrypting empty string returns empty string without error."""
        self.assertEqual("", self.decrypt(""))

    def test_decrypt_plaintext_passthrough(self):
        """Decrypting unencrypted text returns it unchanged (backward compat)."""
        self.assertEqual("plain", self.decrypt("plain"))

    # ------------------------------------------------------------------ #
    # 2. Registration & Login
    # ------------------------------------------------------------------ #

    @patch('evernothing.sync_s3')
    def test_register_and_login(self, mock_sync):
        self.register('user_reg1')
        rv = self.login('user_reg1')
        self.assertIn(b'EverNothing', rv.data)
        self.assertEqual(rv.status_code, 200)

    @patch('evernothing.sync_s3')
    def test_register_redirects_to_login(self, mock_sync):
        rv = self.client.post('/register', data={
            'username': 'user_redir',
            'password': TEST_PASSWORD,
            'email': TEST_EMAIL
        })
        self.assertEqual(rv.status_code, 302)
        self.assertIn('/login', rv.headers['Location'])

    @patch('evernothing.sync_s3')
    def test_duplicate_username_rejected(self, mock_sync):
        self.register('user_dup')
        rv = self.register('user_dup')
        self.assertIn(b'exists', rv.data.lower())

    def test_invalid_login_shows_error(self):
        rv = self.login('nobody', 'WrongPass1')
        self.assertIn(b'Invalid', rv.data)
        self.assertEqual(rv.status_code, 200)

    def test_weak_password_rejected(self):
        rv = self.register('user_weak', password='short')
        # Should not redirect to login — stays on register with error
        self.assertNotIn(b'EverNothing - Folders', rv.data)

    @patch('evernothing.sync_s3')
    def test_logout_clears_session(self, mock_sync):
        self.register('user_logout')
        self.login('user_logout')
        self.logout()
        rv = self.client.get('/')
        self.assertEqual(rv.status_code, 302)

    # ------------------------------------------------------------------ #
    # 3. Authorization — unauthenticated access
    # ------------------------------------------------------------------ #

    def test_index_requires_login(self):
        rv = self.client.get('/')
        self.assertEqual(rv.status_code, 302)

    def test_folder_requires_login(self):
        rv = self.client.get('/folder/1')
        self.assertEqual(rv.status_code, 302)

    def test_add_note_requires_login(self):
        rv = self.client.get('/add/1')
        self.assertEqual(rv.status_code, 302)

    def test_edit_note_requires_login(self):
        rv = self.client.get('/edit/1')
        self.assertEqual(rv.status_code, 302)

    def test_search_requires_login(self):
        rv = self.client.get('/search?q=test')
        self.assertEqual(rv.status_code, 302)

    def test_export_requires_login(self):
        rv = self.client.get('/export')
        self.assertEqual(rv.status_code, 302)

    def test_audit_report_requires_login(self):
        rv = self.client.get('/audit_report')
        self.assertEqual(rv.status_code, 302)

    # ------------------------------------------------------------------ #
    # 4. Admin authorization
    # ------------------------------------------------------------------ #

    def test_admin_dashboard_requires_admin_session(self):
        rv = self.client.get('/admin/dashboard')
        self.assertEqual(rv.status_code, 302)

    def test_admin_edit_user_requires_admin_session(self):
        rv = self.client.get('/admin/user/1')
        self.assertEqual(rv.status_code, 302)

    def test_admin_delete_user_requires_admin_session(self):
        rv = self.client.get('/admin/user/delete/1')
        self.assertEqual(rv.status_code, 302)

    def test_admin_audit_logs_requires_admin_session(self):
        rv = self.client.get('/admin/audit_logs')
        self.assertEqual(rv.status_code, 302)

    def test_admin_login_success(self):
        rv = self.admin_login()
        self.assertIn(b'Admin Dashboard', rv.data)

    def test_admin_login_wrong_password(self):
        os.environ['ADMIN_USER'] = ADMIN_USER
        os.environ['ADMIN_PASS'] = ADMIN_PASS
        rv = self.client.post('/admin', data={
            'username': ADMIN_USER,
            'password': 'wrongpassword'
        }, follow_redirects=True)
        self.assertIn(b'Invalid', rv.data)

    # ------------------------------------------------------------------ #
    # 5. Folder operations
    # ------------------------------------------------------------------ #

    @patch('evernothing.sync_s3')
    def test_create_folder(self, mock_sync):
        self.register('user_folder1')
        self.login('user_folder1')
        rv = self.client.post('/folder/add', data={'name': 'MyFolder'}, follow_redirects=True)
        self.assertIn(b'MyFolder', rv.data)

    @patch('evernothing.sync_s3')
    def test_rename_folder(self, mock_sync):
        self.register('user_folder2')
        self.login('user_folder2')
        self.client.post('/folder/add', data={'name': 'OldName'}, follow_redirects=True)
        rv = self.client.post('/folder/rename/1', data={'name': 'NewName'}, follow_redirects=True)
        self.assertIn(b'NewName', rv.data)

    @patch('evernothing.sync_s3')
    def test_delete_folder(self, mock_sync):
        self.register('user_folder3')
        self.login('user_folder3')
        self.client.post('/folder/add', data={'name': 'ToDelete'}, follow_redirects=True)
        rv = self.client.post('/folder/delete/1', follow_redirects=True)
        self.assertNotIn(b'ToDelete', rv.data)

    @patch('evernothing.sync_s3')
    def test_create_subfolder(self, mock_sync):
        self.register('user_folder4')
        self.login('user_folder4')
        self.client.post('/folder/add', data={'name': 'Parent'}, follow_redirects=True)
        rv = self.client.post('/folder/1/add_folder', data={'name': 'Child'}, follow_redirects=True)
        self.assertIn(b'Child', rv.data)

    @patch('evernothing.sync_s3')
    def test_empty_folder_name_rejected(self, mock_sync):
        self.register('user_folder5')
        self.login('user_folder5')
        rv = self.client.post('/folder/add', data={'name': ''}, follow_redirects=True)
        self.assertNotIn(b'EverNothing - Folders', rv.data)

    # ------------------------------------------------------------------ #
    # 6. Note CRUD
    # ------------------------------------------------------------------ #

    @patch('evernothing.sync_s3')
    def test_create_note(self, mock_sync):
        self.register('user_note1')
        self.login('user_note1')
        self.client.post('/folder/add', data={'name': 'F'}, follow_redirects=True)
        rv = self.client.post('/add/1', data={'note': 'MyNote', 'content': 'MyContent'}, follow_redirects=True)
        self.assertIn(b'MyNote', rv.data)

    @patch('evernothing.sync_s3')
    def test_empty_note_rejected(self, mock_sync):
        self.register('user_note2')
        self.login('user_note2')
        self.client.post('/folder/add', data={'name': 'F'}, follow_redirects=True)
        rv = self.client.post('/add/1', data={'note': '', 'content': ''}, follow_redirects=True)
        self.assertIn(b'empty', rv.data.lower())

    @patch('evernothing.sync_s3')
    def test_duplicate_note_name_rejected(self, mock_sync):
        self.register('user_note3')
        self.login('user_note3')
        self.client.post('/folder/add', data={'name': 'F'}, follow_redirects=True)
        self.client.post('/add/1', data={'note': 'Dupe', 'content': 'Content'}, follow_redirects=True)
        rv = self.client.post('/add/1', data={'note': 'Dupe', 'content': 'Content2'}, follow_redirects=True)
        self.assertIn(b'exists', rv.data.lower())

    @patch('evernothing.sync_s3')
    def test_edit_note(self, mock_sync):
        self.register('user_note4')
        self.login('user_note4')
        self.client.post('/folder/add', data={'name': 'F'}, follow_redirects=True)
        self.client.post('/add/1', data={'note': 'Original', 'content': 'Content'}, follow_redirects=True)
        rv = self.client.post('/edit/1', data={
            'note': 'Updated', 'content': 'New Content', 'folder_id': '1', 'confirm': 'yes'
        }, follow_redirects=True)
        self.assertIn(b'Updated', rv.data)

    @patch('evernothing.sync_s3')
    def test_identical_edit_skips_confirmation(self, mock_sync):
        self.register('user_note5')
        self.login('user_note5')
        self.client.post('/folder/add', data={'name': 'F'}, follow_redirects=True)
        self.client.post('/add/1', data={'note': 'Same', 'content': 'Same'}, follow_redirects=True)
        rv = self.client.post('/edit/1', data={
            'note': 'Same', 'content': 'Same', 'folder_id': '1'
        }, follow_redirects=True)
        # Should redirect home without confirmation prompt
        self.assertIn(b'EverNothing', rv.data)

    @patch('evernothing.sync_s3')
    def test_delete_note(self, mock_sync):
        self.register('user_note6')
        self.login('user_note6')
        self.client.post('/folder/add', data={'name': 'F'}, follow_redirects=True)
        self.client.post('/add/1', data={'note': 'GoneNote', 'content': 'Content'}, follow_redirects=True)
        rv = self.client.post('/note/delete/1', follow_redirects=True)
        self.assertNotIn(b'GoneNote', rv.data)

    # ------------------------------------------------------------------ #
    # 7. Note history & rollback
    # ------------------------------------------------------------------ #

    @patch('evernothing.sync_s3')
    def test_note_history_recorded(self, mock_sync):
        self.register('user_hist1')
        self.login('user_hist1')
        self.client.post('/folder/add', data={'name': 'F'}, follow_redirects=True)
        self.client.post('/add/1', data={'note': 'HistNote', 'content': 'v1'}, follow_redirects=True)
        self.client.post('/edit/1', data={
            'note': 'HistNote', 'content': 'v2', 'folder_id': '1', 'confirm': 'yes'
        }, follow_redirects=True)
        rv = self.client.get('/history/1')
        self.assertIn(b'HistNote', rv.data)

    @patch('evernothing.sync_s3')
    def test_history_rollback_requires_post(self, mock_sync):
        """GET to restore_history must show confirmation, not silently restore."""
        self.register('user_hist2')
        self.login('user_hist2')
        self.client.post('/folder/add', data={'name': 'F'}, follow_redirects=True)
        self.client.post('/add/1', data={'note': 'RollNote', 'content': 'v1'}, follow_redirects=True)
        rv = self.client.get('/history/restore/1')
        # Should show confirmation page, not redirect to edit
        self.assertEqual(rv.status_code, 200)
        self.assertIn(b'Confirm', rv.data)

    # ------------------------------------------------------------------ #
    # 8. Search
    # ------------------------------------------------------------------ #

    @patch('evernothing.sync_s3')
    def test_search_finds_by_key(self, mock_sync):
        self.register('user_search1')
        self.login('user_search1')
        self.client.post('/folder/add', data={'name': 'F'}, follow_redirects=True)
        self.client.post('/add/1', data={'note': 'UniqueKey', 'content': 'SomeContent'}, follow_redirects=True)
        rv = self.client.get('/search?q=UniqueKey')
        self.assertIn(b'UniqueKey', rv.data)

    @patch('evernothing.sync_s3')
    def test_search_finds_by_value(self, mock_sync):
        self.register('user_search2')
        self.login('user_search2')
        self.client.post('/folder/add', data={'name': 'F'}, follow_redirects=True)
        self.client.post('/add/1', data={'note': 'AKey', 'content': 'UniqueValue'}, follow_redirects=True)
        rv = self.client.get('/search?q=UniqueValue')
        self.assertIn(b'AKey', rv.data)

    @patch('evernothing.sync_s3')
    def test_search_no_results(self, mock_sync):
        self.register('user_search3')
        self.login('user_search3')
        rv = self.client.get('/search?q=xyznotexist')
        self.assertIn(b'No matches', rv.data)

    def test_search_empty_query_returns_empty(self):
        self.register('user_search4')
        self.login('user_search4')
        rv = self.client.get('/search?q=')
        self.assertEqual(rv.status_code, 200)

    # ------------------------------------------------------------------ #
    # 9. Data isolation between users
    # ------------------------------------------------------------------ #

    @patch('evernothing.sync_s3')
    def test_user_cannot_see_other_users_notes(self, mock_sync):
        self.register('user_iso1')
        self.login('user_iso1')
        self.client.post('/folder/add', data={'name': 'F'}, follow_redirects=True)
        self.client.post('/add/1', data={'note': 'PrivateNote', 'content': 'Secret'}, follow_redirects=True)
        self.logout()

        self.register('user_iso2')
        self.login('user_iso2')
        rv = self.client.get('/search?q=PrivateNote')
        # "PrivateNote" appears in the search form echo — check results list is empty
        self.assertIn(b'No matches', rv.data)

    @patch('evernothing.sync_s3')
    def test_user_cannot_edit_other_users_note(self, mock_sync):
        self.register('user_iso3')
        self.login('user_iso3')
        self.client.post('/folder/add', data={'name': 'F'}, follow_redirects=True)
        self.client.post('/add/1', data={'note': 'OtherNote', 'content': 'Content'}, follow_redirects=True)
        self.logout()

        self.register('user_iso4')
        self.login('user_iso4')
        rv = self.client.get('/edit/1', follow_redirects=True)
        # Should redirect away — note belongs to user_iso3
        self.assertNotIn(b'OtherNote', rv.data)

    # ------------------------------------------------------------------ #
    # 10. Password change
    # ------------------------------------------------------------------ #

    @patch('evernothing.sync_s3')
    def test_change_password_success(self, mock_sync):
        self.register('user_pw1')
        self.login('user_pw1')
        rv = self.client.post('/change_password', data={
            'old_password': TEST_PASSWORD,
            'new_password': 'NewPass456'
        }, follow_redirects=True)
        self.assertEqual(rv.status_code, 200)

    @patch('evernothing.sync_s3')
    def test_change_password_wrong_old(self, mock_sync):
        self.register('user_pw2')
        self.login('user_pw2')
        rv = self.client.post('/change_password', data={
            'old_password': 'WrongOld1',
            'new_password': 'NewPass456'
        }, follow_redirects=True)
        self.assertIn(b'Invalid', rv.data)

    # ------------------------------------------------------------------ #
    # 11. Audit log
    # ------------------------------------------------------------------ #

    @patch('evernothing.sync_s3')
    def test_audit_log_records_create(self, mock_sync):
        self.register('user_audit1')
        self.login('user_audit1')
        self.client.post('/folder/add', data={'name': 'F'}, follow_redirects=True)
        self.client.post('/add/1', data={'note': 'AuditNote', 'content': 'Content'}, follow_redirects=True)
        rv = self.client.get('/audit_report')
        self.assertIn(b'CREATE', rv.data)

    @patch('evernothing.sync_s3')
    def test_audit_log_records_update(self, mock_sync):
        self.register('user_audit2')
        self.login('user_audit2')
        self.client.post('/folder/add', data={'name': 'F'}, follow_redirects=True)
        self.client.post('/add/1', data={'note': 'AuditNote2', 'content': 'v1'}, follow_redirects=True)
        self.client.post('/edit/1', data={
            'note': 'AuditNote2', 'content': 'v2', 'folder_id': '1', 'confirm': 'yes'
        }, follow_redirects=True)
        rv = self.client.get('/audit_report')
        self.assertIn(b'UPDATE', rv.data)

    # ------------------------------------------------------------------ #
    # 11b. Description field
    # ------------------------------------------------------------------ #

    @patch('evernothing.sync_s3')
    def test_description_saved_on_create(self, mock_sync):
        self.register('user_desc1')
        self.login('user_desc1')
        self.client.post('/folder/add', data={'name': 'F'}, follow_redirects=True)
        self.client.post('/add/1', data={'note': 'DescNote', 'content': 'Content', 'description': 'My short desc'}, follow_redirects=True)
        with sqlite3.connect(self.db_path) as con:
            row = con.execute("SELECT description FROM notes WHERE id=1").fetchone()
        self.assertIsNotNone(row)
        self.assertIn('My short desc', row[0])

    @patch('evernothing.sync_s3')
    def test_description_truncated_at_255(self, mock_sync):
        self.register('user_desc2')
        self.login('user_desc2')
        self.client.post('/folder/add', data={'name': 'F'}, follow_redirects=True)
        long_desc = 'x' * 300
        self.client.post('/add/1', data={'note': 'DescNote2', 'content': 'Content', 'description': long_desc}, follow_redirects=True)
        with sqlite3.connect(self.db_path) as con:
            row = con.execute("SELECT description FROM notes WHERE id=1").fetchone()
        self.assertIsNotNone(row)
        self.assertLessEqual(len(row[0]), 255)

    @patch('evernothing.sync_s3')
    def test_description_empty_allowed(self, mock_sync):
        self.register('user_desc3')
        self.login('user_desc3')
        self.client.post('/folder/add', data={'name': 'F'}, follow_redirects=True)
        rv = self.client.post('/add/1', data={'note': 'NoDesc', 'content': 'Content', 'description': ''}, follow_redirects=True)
        self.assertIn(b'NoDesc', rv.data)

    @patch('evernothing.sync_s3')
    def test_description_shown_on_edit_page(self, mock_sync):
        self.register('user_desc4')
        self.login('user_desc4')
        self.client.post('/folder/add', data={'name': 'F'}, follow_redirects=True)
        self.client.post('/add/1', data={'note': 'EditDesc', 'content': 'Content', 'description': 'Visible desc'}, follow_redirects=True)
        rv = self.client.get('/edit/1')
        self.assertIn(b'Visible desc', rv.data)

    @patch('evernothing.sync_s3')
    def test_description_updated_on_edit(self, mock_sync):
        self.register('user_desc5')
        self.login('user_desc5')
        self.client.post('/folder/add', data={'name': 'F'}, follow_redirects=True)
        self.client.post('/add/1', data={'note': 'UpdDesc', 'content': 'Content', 'description': 'Old desc'}, follow_redirects=True)
        self.client.post('/edit/1', data={
            'note': 'UpdDesc', 'content': 'Content', 'folder_id': '1',
            'description': 'New desc', 'confirm': 'yes'
        }, follow_redirects=True)
        with sqlite3.connect(self.db_path) as con:
            row = con.execute("SELECT description FROM notes WHERE id=1").fetchone()
        self.assertIn('New desc', row[0])

    @patch('evernothing.sync_s3')
    def test_description_in_export(self, mock_sync):
        self.register('user_desc6')
        self.login('user_desc6')
        self.client.post('/folder/add', data={'name': 'F'}, follow_redirects=True)
        self.client.post('/add/1', data={'note': 'ExpDesc', 'content': 'Content', 'description': 'Export me'}, follow_redirects=True)
        rv = self.client.get('/export')
        self.assertIn(b'Export me', rv.data)

    # ------------------------------------------------------------------ #
    # 12. Export
    # ------------------------------------------------------------------ #

    @patch('evernothing.sync_s3')
    def test_export_json(self, mock_sync):
        self.register('user_exp1')
        self.login('user_exp1')
        self.client.post('/folder/add', data={'name': 'F'}, follow_redirects=True)
        self.client.post('/add/1', data={'note': 'ExportNote', 'content': 'ExportContent'}, follow_redirects=True)
        rv = self.client.get('/export')
        self.assertEqual(rv.status_code, 200)
        self.assertIn(b'ExportNote', rv.data)
        self.assertIn(b'application/json', rv.content_type.encode())

    # ------------------------------------------------------------------ #
    # 13. Admin user management
    # ------------------------------------------------------------------ #

    @patch('evernothing.sync_s3')
    def test_admin_can_see_users(self, mock_sync):
        self.register('user_adm1')
        self.admin_login()
        rv = self.client.get('/admin/dashboard')
        self.assertIn(b'user_adm1', rv.data)

    @patch('evernothing.sync_s3')
    def test_admin_delete_user(self, mock_sync):
        self.register('user_adm2')
        self.admin_login()
        rv = self.client.post('/admin/user/delete/1', follow_redirects=True)
        self.assertEqual(rv.status_code, 200)

    # ------------------------------------------------------------------ #
    # 14. Rate limiting
    # ------------------------------------------------------------------ #

    def test_rate_limit_login(self):
        import evernothing
        from rate_limiter import clear_rate_limit
        clear_rate_limit('127.0.0.1', 'login')

        import rate_limiter
        original = rate_limiter.RATE_LIMIT_LOGIN
        rate_limiter.RATE_LIMIT_LOGIN = 3
        try:
            for _ in range(3):
                self.client.post('/login', data={'username': 'x', 'password': 'WrongPass1'})
            rv = self.client.post('/login', data={
                'username': 'x', 'password': 'WrongPass1'
            }, follow_redirects=True)
            self.assertIn(b'Too many', rv.data)
        finally:
            rate_limiter.RATE_LIMIT_LOGIN = original
            clear_rate_limit('127.0.0.1', 'login')

    # ------------------------------------------------------------------ #
    # 15. Input validation
    # ------------------------------------------------------------------ #

    @patch('evernothing.sync_s3')
    def test_register_invalid_email(self, mock_sync):
        rv = self.register('user_val1', email='not-an-email')
        self.assertNotIn(b'EverNothing - Folders', rv.data)

    @patch('evernothing.sync_s3')
    def test_register_username_too_long(self, mock_sync):
        rv = self.register('u' * 60)
        self.assertNotIn(b'EverNothing - Folders', rv.data)

    # ------------------------------------------------------------------ #
    # 16. 404 handler
    # ------------------------------------------------------------------ #

    def test_404_returns_correct_status(self):
        rv = self.client.get('/nonexistent_route_xyz')
        self.assertEqual(rv.status_code, 404)


if __name__ == '__main__':
    unittest.main()
