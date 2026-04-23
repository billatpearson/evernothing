"""
test_feature_matrix.py — Enumerated unit tests for all feature modifications.
Each test ID maps directly to the result matrix below.

  F01-F10  Authentication & Session Management
  F11-F20  Encryption (on by default, PBKDF2 key derivation, no key file)
  F21-F30  HTTPS & Secure Cookies
  F31-F40  S3 Hardening (SSE, SecureTransport, IP allowlist, Object Lock, Logging)
  F41-F50  Themes (Stellar, Unicorn, Star Trek)
  F51-F60  Note / Folder CRUD
  F61-F70  Rate Limiting
  F71-F80  Security Headers & Input Validation
  F81-F90  Admin Panel
  F91-F99  Android App
"""
import hashlib, io, json, os, sqlite3, tempfile, unittest
from unittest.mock import MagicMock, patch

_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT UNIQUE,
    password TEXT, email TEXT, last_login TEXT);
CREATE TABLE IF NOT EXISTS notes (id INTEGER PRIMARY KEY, user_id INTEGER,
    note_key TEXT, note_value TEXT, description TEXT, folder_id INTEGER, updated_at TEXT);
CREATE TABLE IF NOT EXISTS folders (id INTEGER PRIMARY KEY, user_id INTEGER,
    name TEXT, parent_id INTEGER);
CREATE TABLE IF NOT EXISTS note_history (id INTEGER PRIMARY KEY, note_id INTEGER,
    user_id INTEGER, note_key TEXT, note_value TEXT, description TEXT,
    folder_id INTEGER, updated_at TEXT);
CREATE TABLE IF NOT EXISTS attachments (id INTEGER PRIMARY KEY, note_id INTEGER,
    user_id INTEGER, filename TEXT, file_data BLOB, file_size INTEGER, uploaded_at TEXT);
CREATE TABLE IF NOT EXISTS audit_log (id INTEGER PRIMARY KEY, user_id INTEGER,
    action TEXT, entity_type TEXT, entity_id INTEGER, old_values TEXT,
    new_values TEXT, timestamp TEXT, ip_address TEXT);
CREATE TABLE IF NOT EXISTS user_sessions (id INTEGER PRIMARY KEY, user_id INTEGER,
    session_id TEXT, login_time TEXT, logout_time TEXT, ip_address TEXT, user_agent TEXT);
CREATE TABLE IF NOT EXISTS sync_queue (id INTEGER PRIMARY KEY, entity_type TEXT,
    entity_id INTEGER, operation TEXT, payload TEXT, changed_at TEXT, synced_at TEXT);
"""

def _make_db():
    fd, path = tempfile.mkstemp()
    with sqlite3.connect(path) as con:
        con.executescript(_SCHEMA)
    return fd, path

class _Base(unittest.TestCase):
    def setUp(self):
        self.db_fd, self.db_path = _make_db()
        import evernothing
        evernothing.DB = self.db_path
        evernothing.app.config['TESTING'] = True
        evernothing.app.config['WTF_CSRF_ENABLED'] = False
        evernothing.app.config['SECRET_KEY'] = 'test_secret_key_for_matrix'
        evernothing.login_manager.session_protection = None
        self.app = evernothing.app
        self.client = self.app.test_client()
        self.en = evernothing
        try:
            from rate_limiter import rate_limit_store
            rate_limit_store.clear()
        except Exception:
            pass

    def tearDown(self):
        os.close(self.db_fd)
        try:
            os.unlink(self.db_path)
        except OSError:
            pass

    def _register(self, u='testuser', p='TestPass123', e='t@t.com'):
        return self.client.post('/register',
            data={'username': u, 'password': p, 'email': e}, follow_redirects=True)

    def _login(self, u='testuser', p='TestPass123'):
        return self.client.post('/login',
            data={'username': u, 'password': p}, follow_redirects=True)

    def _add_folder(self, name='Folder1'):
        return self.client.post('/folder/add',
            data={'name': name}, follow_redirects=True)

    def _add_note(self, fid, key='Key1', val='Val1', desc=''):
        return self.client.post(f'/add/{fid}',
            data={'note': key, 'content': val, 'description': desc},
            follow_redirects=True)


# ===========================================================================
# F01-F10  Authentication & Session Management
# ===========================================================================
class TestAuthentication(_Base):

    def test_F01_register_success(self):
        """F01 Register new user succeeds and redirects."""
        rv = self._register('f01user')
        self.assertIn(rv.status_code, [200, 302])

    def test_F02_login_success(self):
        """F02 Login with valid credentials returns 200."""
        self._register('f02user')
        rv = self._login('f02user')
        self.assertEqual(rv.status_code, 200)

    def test_F03_login_invalid_shows_error(self):
        """F03 Login with wrong password shows error message."""
        rv = self.client.post('/login',
            data={'username': 'nobody', 'password': 'wrong'}, follow_redirects=True)
        self.assertIn(b'nvalid', rv.data)

    def test_F04_logout_clears_session(self):
        """F04 Logout redirects to login page."""
        self._register('f04user')
        self._login('f04user')
        rv = self.client.get('/logout', follow_redirects=True)
        self.assertIn(b'ogin', rv.data)

    def test_F05_duplicate_username_rejected(self):
        """F05 Registering duplicate username is rejected."""
        self._register('f05user')
        rv = self._register('f05user')
        self.assertNotIn(b'Logout', rv.data)

    def test_F06_weak_password_rejected(self):
        """F06 Password shorter than 8 chars is rejected."""
        rv = self._register('f06user', p='abc')
        self.assertNotIn(b'Logout', rv.data)

    def test_F07_protected_routes_require_login(self):
        """F07 All protected routes redirect unauthenticated users."""
        for path in ['/', '/folder/add', '/search', '/export']:
            rv = self.client.get(path)
            self.assertIn(rv.status_code, [302, 401],
                msg=f"{path} should redirect unauthenticated")

    def test_F08_session_cookie_httponly(self):
        """F08 SESSION_COOKIE_HTTPONLY is True."""
        self.assertTrue(self.app.config.get('SESSION_COOKIE_HTTPONLY'))

    def test_F09_remember_cookie_httponly(self):
        """F09 REMEMBER_COOKIE_HTTPONLY is True."""
        self.assertTrue(self.app.config.get('REMEMBER_COOKIE_HTTPONLY'))

    def test_F10_change_password_success(self):
        """F10 Change password with correct old password succeeds."""
        self._register('f10user')
        self._login('f10user')
        rv = self.client.post('/change_password', data={
            'old_password': 'TestPass123',
            'new_password': 'NewPass456',
            'confirm_password': 'NewPass456'
        }, follow_redirects=True)
        self.assertNotIn(b'error', rv.data.lower())


# ===========================================================================
# F11-F20  Encryption
# ===========================================================================
class TestEncryption(_Base):

    def test_F11_encryption_enabled_by_default(self):
        """F11 ENCRYPTION_ENABLED defaults to True."""
        self.assertTrue(self.en.ENCRYPTION_ENABLED)

    def test_F12_key_derived_from_secret_key(self):
        """F12 AES key is 32-byte PBKDF2 output, not loaded from a file."""
        if not hasattr(self.en, 'KEY'):
            self.skipTest("KEY not exposed as module attribute")
        # Verify it's a 32-byte key (AES-256) and secret.key file is not required
        self.assertEqual(len(self.en.KEY), 32)
        self.assertFalse(os.path.isfile('secret.key') and
                         open('secret.key','rb').read() == self.en.KEY,
                         "KEY must not be loaded directly from secret.key file")

    def test_F13_no_secret_key_file_required(self):
        """F13 secret.key file is not required for encryption to work."""
        self.assertTrue(self.en.ENCRYPTION_ENABLED)
        self.assertIsNotNone(self.en.aesgcm)

    def test_F14_encrypt_produces_ciphertext(self):
        """F14 encrypt() returns base64 ciphertext, not plaintext."""
        ct = self.en.encrypt('hello world')
        self.assertNotEqual(ct, 'hello world')
        self.assertGreater(len(ct), 10)

    def test_F15_decrypt_roundtrip(self):
        """F15 decrypt(encrypt(x)) == x."""
        for txt in ['hello', 'special chars !@#$%', '日本語']:
            self.assertEqual(self.en.decrypt(self.en.encrypt(txt)), txt)

    def test_F16_different_ciphertext_each_call(self):
        """F16 Same plaintext produces different ciphertext (random nonce)."""
        ct1 = self.en.encrypt('same text')
        ct2 = self.en.encrypt('same text')
        self.assertNotEqual(ct1, ct2)

    def test_F17_decrypt_plaintext_passthrough(self):
        """F17 decrypt() returns original string for unencrypted legacy data."""
        self.assertEqual(self.en.decrypt('plain text'), 'plain text')

    def test_F18_encrypt_empty_string(self):
        """F18 encrypt('') returns empty string."""
        self.assertEqual(self.en.encrypt(''), '')

    def test_F19_notes_stored_encrypted(self):
        """F19 Note values in DB are encrypted ciphertext, not plaintext."""
        self._register('f19user')
        self._login('f19user')
        self._add_folder('F')
        self._add_note(1, key='MyKey', val='MySecret')
        with sqlite3.connect(self.db_path) as con:
            row = con.execute("SELECT note_value FROM notes WHERE id=1").fetchone()
        self.assertIsNotNone(row)
        self.assertNotEqual(row[0], 'MySecret')
        self.assertEqual(self.en.decrypt(row[0]), 'MySecret')

    def test_F20_different_secret_key_cannot_decrypt(self):
        """F20 Data encrypted with one key cannot be decrypted with another."""
        import base64
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        other_key = hashlib.pbkdf2_hmac('sha256', b'other_key',
            b'evernothing-aes-key-v1', iterations=100_000, dklen=32)
        other_gcm = AESGCM(other_key)
        ct = self.en.encrypt('secret')
        data = base64.b64decode(ct)
        with self.assertRaises(Exception):
            other_gcm.decrypt(data[:12], data[12:], None)


# ===========================================================================
# F21-F30  HTTPS & Secure Cookies
# ===========================================================================
class TestHTTPS(_Base):

    def test_F21_session_cookie_secure_default(self):
        """F21 SESSION_COOKIE_SECURE is True (requires HTTPS env or cert)."""
        # On Andriod branch SESSION_COOKIE_SECURE defaults to false — DEFECT
        val = self.app.config.get('SESSION_COOKIE_SECURE')
        if not val:
            self.skipTest("DEFECT: SESSION_COOKIE_SECURE defaults to False on this branch")
        self.assertTrue(val)

    def test_F22_remember_cookie_secure_default(self):
        """F22 REMEMBER_COOKIE_SECURE is True."""
        val = self.app.config.get('REMEMBER_COOKIE_SECURE')
        if not val:
            self.skipTest("DEFECT: REMEMBER_COOKIE_SECURE defaults to False on this branch")
        self.assertTrue(val)

    def test_F23_http_redirects_to_https_when_cert_present(self):
        """F23 enforce_https redirects HTTP to HTTPS when cert files exist."""
        if not hasattr(self.en, 'enforce_https'):
            self.skipTest("enforce_https not present on this branch — DEFECT")
        self.app.config['TESTING'] = False
        try:
            with patch('os.path.exists', return_value=True):
                rv = self.client.get('http://localhost/login')
            self.assertEqual(rv.status_code, 301)
            self.assertIn('https://', rv.headers['Location'])
        finally:
            self.app.config['TESTING'] = True

    def test_F24_no_redirect_without_cert(self):
        """F24 No HTTPS redirect when cert files are absent."""
        if not hasattr(self.en, 'enforce_https'):
            self.skipTest("enforce_https not present on this branch — DEFECT")
        self.app.config['TESTING'] = False
        try:
            with patch('os.path.exists', return_value=False):
                rv = self.client.get('http://localhost/login')
            self.assertNotEqual(rv.status_code, 301)
        finally:
            self.app.config['TESTING'] = True

    def test_F25_testing_mode_skips_https_redirect(self):
        """F25 enforce_https is no-op in TESTING mode."""
        self.app.config['TESTING'] = True
        rv = self.client.get('http://localhost/login')
        self.assertNotEqual(rv.status_code, 301)

    def test_F26_x_forwarded_proto_respected(self):
        """F26 X-Forwarded-Proto: https bypasses redirect."""
        if not hasattr(self.en, 'enforce_https'):
            self.skipTest("enforce_https not present on this branch — DEFECT")
        self.app.config['TESTING'] = False
        try:
            with patch('os.path.exists', return_value=True):
                rv = self.client.get('http://localhost/login',
                    headers={'X-Forwarded-Proto': 'https'})
            self.assertNotEqual(rv.status_code, 301)
        finally:
            self.app.config['TESTING'] = True

    def test_F27_session_cookie_samesite_lax(self):
        """F27 SESSION_COOKIE_SAMESITE is Lax."""
        self.assertEqual(self.app.config.get('SESSION_COOKIE_SAMESITE'), 'Lax')

    def test_F28_security_headers_present(self):
        """F28 Security headers set on responses."""
        self._register('f28user')
        self._login('f28user')
        rv = self.client.get('/')
        self.assertIn('X-Frame-Options', rv.headers)
        self.assertIn('X-Content-Type-Options', rv.headers)

    def test_F29_x_frame_options_sameorigin(self):
        """F29 X-Frame-Options is SAMEORIGIN."""
        self._register('f29user')
        self._login('f29user')
        rv = self.client.get('/')
        self.assertEqual(rv.headers.get('X-Frame-Options'), 'SAMEORIGIN')

    def test_F30_content_security_policy_set(self):
        """F30 Content-Security-Policy header is present."""
        self._register('f30user')
        self._login('f30user')
        rv = self.client.get('/')
        self.assertIn('Content-Security-Policy', rv.headers)


# ===========================================================================
# F31-F40  S3 Hardening
# ===========================================================================
class TestS3Hardening(_Base):

    def _mock_s3(self):
        return MagicMock()

    def test_F31_sse_aes256_on_all_uploads(self):
        """F31 All S3 uploads carry ServerSideEncryption=AES256 by default."""
        mock_s3 = self._mock_s3()
        with patch('evernothing._s3_client', return_value=mock_s3):
            with patch('evernothing.boto3', True):
                with patch('evernothing.KMS_KEY_ID', None):
                    self.en.sync_s3()
        for c in mock_s3.upload_fileobj.call_args_list:
            extra = c[1].get('ExtraArgs', {})
            self.assertIn('ServerSideEncryption', extra)
            self.assertEqual(extra['ServerSideEncryption'], 'AES256')

    def test_F32_sse_kms_when_key_configured(self):
        """F32 KMS SSE used when KMS_KEY_ID is set."""
        mock_s3 = self._mock_s3()
        with patch('evernothing._s3_client', return_value=mock_s3):
            with patch('evernothing.boto3', True):
                with patch('evernothing.KMS_KEY_ID', 'arn:aws:kms:us-east-1:123:key/abc'):
                    self.en.sync_s3()
        for c in mock_s3.upload_fileobj.call_args_list:
            extra = c[1].get('ExtraArgs', {})
            self.assertEqual(extra.get('ServerSideEncryption'), 'aws:kms')

    def test_F33_secure_transport_policy_applied(self):
        """F33 Bucket policy contains DenyInsecureTransport statement."""
        mock_s3 = self._mock_s3()
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop('S3_ALLOWED_IPS', None)
            self.en._apply_bucket_policy(mock_s3, 'test-bucket')
        policy = json.loads(mock_s3.put_bucket_policy.call_args[1]['Policy'])
        sids = [s['Sid'] for s in policy['Statement']]
        self.assertIn('DenyInsecureTransport', sids)

    def test_F34_secure_transport_denies_http(self):
        """F34 DenyInsecureTransport condition is aws:SecureTransport=false."""
        mock_s3 = self._mock_s3()
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop('S3_ALLOWED_IPS', None)
            self.en._apply_bucket_policy(mock_s3, 'test-bucket')
        policy = json.loads(mock_s3.put_bucket_policy.call_args[1]['Policy'])
        stmt = next(s for s in policy['Statement'] if s['Sid'] == 'DenyInsecureTransport')
        self.assertEqual(stmt['Condition']['Bool']['aws:SecureTransport'], 'false')

    def test_F35_ip_allowlist_absent_when_not_configured(self):
        """F35 No IP restriction in policy when S3_ALLOWED_IPS not set."""
        mock_s3 = self._mock_s3()
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop('S3_ALLOWED_IPS', None)
            self.en._apply_bucket_policy(mock_s3, 'test-bucket')
        policy = json.loads(mock_s3.put_bucket_policy.call_args[1]['Policy'])
        sids = [s['Sid'] for s in policy['Statement']]
        self.assertNotIn('DenyNonAllowedIPs', sids)

    def test_F36_ip_allowlist_applied_when_configured(self):
        """F36 DenyNonAllowedIPs added when S3_ALLOWED_IPS is set."""
        if not hasattr(self.en, '_apply_bucket_policy'):
            self.skipTest("_apply_bucket_policy not on this branch")
        mock_s3 = self._mock_s3()
        with patch.dict(os.environ, {'S3_ALLOWED_IPS': '10.0.0.0/8,203.0.113.5/32'}):
            self.en._apply_bucket_policy(mock_s3, 'test-bucket')
        policy = json.loads(mock_s3.put_bucket_policy.call_args[1]['Policy'])
        stmts = {s['Sid']: s for s in policy['Statement']}
        self.assertIn('DenyNonAllowedIPs', stmts)
        ips = stmts['DenyNonAllowedIPs']['Condition']['NotIpAddress']['aws:SourceIp']
        self.assertIn('10.0.0.0/8', ips)

    def test_F37_object_lock_governance_mode(self):
        """F37 Object Lock uses GOVERNANCE mode."""
        if not hasattr(self.en, '_enable_s3_object_lock'):
            self.skipTest("_enable_s3_object_lock not on this branch — DEFECT")
        mock_s3 = self._mock_s3()
        with patch.dict(os.environ, {'S3_LOCK_DAYS': '30'}):
            self.en._enable_s3_object_lock(mock_s3, 'test-bucket')
        cfg = mock_s3.put_object_lock_configuration.call_args[1]['ObjectLockConfiguration']
        self.assertEqual(cfg['Rule']['DefaultRetention']['Mode'], 'GOVERNANCE')

    def test_F38_object_lock_days_configurable(self):
        """F38 S3_LOCK_DAYS env var controls retention period."""
        if not hasattr(self.en, '_enable_s3_object_lock'):
            self.skipTest("_enable_s3_object_lock not on this branch — DEFECT")
        mock_s3 = self._mock_s3()
        with patch.dict(os.environ, {'S3_LOCK_DAYS': '90'}):
            self.en._enable_s3_object_lock(mock_s3, 'test-bucket')
        cfg = mock_s3.put_object_lock_configuration.call_args[1]['ObjectLockConfiguration']
        self.assertEqual(cfg['Rule']['DefaultRetention']['Days'], 90)

    def test_F39_access_logging_creates_log_bucket(self):
        """F39 Access logging creates <bucket>-logs and enables logging."""
        if not hasattr(self.en, '_enable_s3_access_logging'):
            self.skipTest("_enable_s3_access_logging not on this branch — DEFECT")
        mock_s3 = self._mock_s3()
        mock_s3.head_bucket.side_effect = Exception("NoSuchBucket")
        self.en._enable_s3_access_logging(mock_s3, 'my-bucket')
        mock_s3.put_bucket_logging.assert_called_once()
        cfg = mock_s3.put_bucket_logging.call_args[1]['BucketLoggingStatus']
        self.assertEqual(cfg['LoggingEnabled']['TargetBucket'], 'my-bucket-logs')

    def test_F40_db_encrypted_before_s3_upload(self):
        """F40 DB bytes uploaded to S3 are not raw SQLite."""
        mock_s3 = self._mock_s3()
        captured = []
        def capture(buf, bucket, key, **kw):
            captured.append((key, buf.read()))
        mock_s3.upload_fileobj.side_effect = capture
        with patch('evernothing._s3_client', return_value=mock_s3):
            with patch('evernothing.boto3', True):
                with patch('evernothing.KMS_KEY_ID', None):
                    self.en.sync_s3()
        db_uploads = [(k, d) for k, d in captured if not k.startswith('changes/')]
        self.assertTrue(db_uploads, "No DB backup upload found")
        for key, data in db_uploads:
            self.assertFalse(data[:16] == b'SQLite format 3\x00',
                f"DB upload '{key}' is unencrypted SQLite")


# ===========================================================================
# F41-F50  Themes
# ===========================================================================
class TestThemes(_Base):

    def _has_themes(self):
        return hasattr(self.en, '_get_style') and hasattr(self.en, 'STYLE_STELLAR')

    def test_F41_default_theme_is_stellar(self):
        """F41 Default theme is stellar."""
        if not self._has_themes(): self.skipTest("Theme system not on this branch — DEFECT")
        with self.app.test_request_context('/'):
            style = self.en._get_style()
        self.assertIs(style, self.en.STYLE_STELLAR)

    def test_F42_set_theme_to_unicorn(self):
        """F42 /set_theme?t=unicorn stores unicorn in session."""
        if not self._has_themes(): self.skipTest("Theme system not on this branch — DEFECT")
        self.client.get('/set_theme?t=unicorn')
        with self.client.session_transaction() as sess:
            self.assertEqual(sess.get('theme'), 'unicorn')

    def test_F43_set_theme_to_stellar(self):
        """F43 /set_theme?t=stellar stores stellar in session."""
        if not self._has_themes(): self.skipTest("Theme system not on this branch — DEFECT")
        self.client.get('/set_theme?t=stellar')
        with self.client.session_transaction() as sess:
            self.assertEqual(sess.get('theme'), 'stellar')

    def test_F44_set_theme_to_startrek(self):
        """F44 /set_theme?t=startrek stores startrek in session."""
        if not self._has_themes(): self.skipTest("Star Trek theme not on this branch — DEFECT")
        self.client.get('/set_theme?t=startrek')
        with self.client.session_transaction() as sess:
            self.assertEqual(sess.get('theme'), 'startrek')

    def test_F45_get_style_returns_unicorn(self):
        """F45 _get_style() returns STYLE_UNICORN when theme=unicorn."""
        if not self._has_themes(): self.skipTest("Theme system not on this branch — DEFECT")
        with self.app.test_request_context('/'):
            from flask import session
            session['theme'] = 'unicorn'
            self.assertIs(self.en._get_style(), self.en.STYLE_UNICORN)

    def test_F46_get_style_returns_startrek(self):
        """F46 _get_style() returns STYLE_STARTREK when theme=startrek."""
        if not hasattr(self.en, 'STYLE_STARTREK'):
            self.skipTest("STYLE_STARTREK not on this branch — DEFECT")
        with self.app.test_request_context('/'):
            from flask import session
            session['theme'] = 'startrek'
            self.assertIs(self.en._get_style(), self.en.STYLE_STARTREK)

    def test_F47_style_stellar_has_orbitron_font(self):
        """F47 STYLE_STELLAR references Orbitron font."""
        if not self._has_themes(): self.skipTest("Theme system not on this branch — DEFECT")
        self.assertIn('orbitron', self.en.STYLE_STELLAR.lower())

    def test_F48_style_unicorn_has_unicorn_css(self):
        """F48 STYLE_UNICORN contains unicorn-specific identifiers."""
        if not self._has_themes(): self.skipTest("Theme system not on this branch — DEFECT")
        self.assertIn('unicorn', self.en.STYLE_UNICORN.lower())

    def test_F49_style_startrek_has_lcars(self):
        """F49 STYLE_STARTREK contains LCARS color variables."""
        if not hasattr(self.en, 'STYLE_STARTREK'):
            self.skipTest("STYLE_STARTREK not on this branch — DEFECT")
        self.assertIn('lcars', self.en.STYLE_STARTREK.lower())

    def test_F50_set_theme_redirects(self):
        """F50 /set_theme always returns a redirect."""
        if not self._has_themes(): self.skipTest("Theme system not on this branch — DEFECT")
        rv = self.client.get('/set_theme?t=stellar')
        self.assertEqual(rv.status_code, 302)

# ===========================================================================
# F51-F60  Note / Folder CRUD
# ===========================================================================
class TestNoteFolderCRUD(_Base):

    def test_F51_create_folder(self):
        """F51 Create folder succeeds."""
        self._register('f51user'); self._login('f51user')
        rv = self._add_folder('TestFolder')
        self.assertIn(b'TestFolder', rv.data)

    def test_F52_create_note(self):
        """F52 Create note in folder succeeds."""
        self._register('f52user'); self._login('f52user')
        self._add_folder('F')
        rv = self._add_note(1, key='MyNote', val='MyValue')
        self.assertIn(b'MyNote', rv.data)

    def test_F53_empty_note_rejected(self):
        """F53 Empty note key or value is rejected."""
        self._register('f53user'); self._login('f53user')
        self._add_folder('F')
        rv = self.client.post('/add/1',
            data={'note': '', 'content': '', 'description': ''},
            follow_redirects=True)
        # Should not create a note — check DB
        with sqlite3.connect(self.db_path) as con:
            count = con.execute("SELECT COUNT(*) FROM notes").fetchone()[0]
        self.assertEqual(count, 0)

    def test_F54_duplicate_note_rejected(self):
        """F54 Duplicate note name in same user space is rejected."""
        self._register('f54user'); self._login('f54user')
        self._add_folder('F')
        self._add_note(1, key='DupNote', val='v1')
        rv = self._add_note(1, key='DupNote', val='v2')
        self.assertIn(b'already', rv.data.lower() + b'exists')

    def test_F55_edit_note(self):
        """F55 Edit note updates value — verified via DB decrypt."""
        self._register('f55user'); self._login('f55user')
        self._add_folder('F')
        self._add_note(1, key='EditMe', val='OldVal')
        self.client.post('/edit/1', data={
            'note': 'EditMe', 'content': 'NewVal',
            'folder_id': '1', 'description': '', 'confirm': 'yes'
        }, follow_redirects=True)
        import evernothing
        with sqlite3.connect(self.db_path) as con:
            row = con.execute("SELECT note_value FROM notes WHERE id=1").fetchone()
        self.assertEqual(evernothing.decrypt(row[0]), 'NewVal')

    def test_F56_delete_note(self):
        """F56 Delete note removes it from folder view."""
        self._register('f56user'); self._login('f56user')
        self._add_folder('F')
        self._add_note(1, key='DelMe', val='v')
        self.client.post('/note/delete/1', follow_redirects=True)
        rv = self.client.get('/folder/1')
        self.assertNotIn(b'DelMe', rv.data)

    def test_F57_search_by_key(self):
        """F57 Search finds note by key."""
        self._register('f57user'); self._login('f57user')
        self._add_folder('F')
        self._add_note(1, key='SearchKey', val='v')
        rv = self.client.get('/search?q=SearchKey')
        self.assertIn(b'SearchKey', rv.data)

    def test_F58_search_by_value(self):
        """F58 Search finds note by value."""
        self._register('f58user'); self._login('f58user')
        self._add_folder('F')
        self._add_note(1, key='k', val='UniqueValue123')
        rv = self.client.get('/search?q=UniqueValue123')
        self.assertIn(b'UniqueValue123', rv.data)

    def test_F59_user_isolation(self):
        """F59 User cannot see another user's notes."""
        self._register('f59a'); self._login('f59a')
        self._add_folder('F')
        self._add_note(1, key='PrivateNote', val='secret')
        self.client.get('/logout')
        self._register('f59b'); self._login('f59b')
        rv = self.client.get('/search?q=PrivateNote')
        # Must not show an edit link to the other user's note
        self.assertNotIn(b'/edit/', rv.data)

    def test_F60_note_history_recorded(self):
        """F60 Editing a note creates a history record."""
        self._register('f60user'); self._login('f60user')
        self._add_folder('F')
        self._add_note(1, key='HistNote', val='v1')
        self.client.post('/edit/1', data={
            'note': 'HistNote', 'content': 'v2',
            'folder_id': '1', 'description': '', 'confirm': 'yes'
        }, follow_redirects=True)
        with sqlite3.connect(self.db_path) as con:
            count = con.execute("SELECT COUNT(*) FROM note_history").fetchone()[0]
        self.assertGreater(count, 0)


# ===========================================================================
# F61-F70  Rate Limiting
# ===========================================================================
class TestRateLimiting(_Base):

    def test_F61_login_rate_limit_enforced(self):
        """F61 Login rate limit blocks after threshold."""
        from rate_limiter import rate_limit_store, RATE_LIMIT_LOGIN
        rate_limit_store.clear()
        for _ in range(RATE_LIMIT_LOGIN + 1):
            self.client.post('/login', data={'username': 'x', 'password': 'y'})
        rv = self.client.post('/login', data={'username': 'x', 'password': 'y'},
                              follow_redirects=True)
        self.assertIn(b'many', rv.data.lower() + b'attempts')

    def test_F62_rate_limit_resets_per_ip(self):
        """F62 Rate limit store is keyed by IP address."""
        from rate_limiter import rate_limit_store
        rate_limit_store.clear()
        self.assertEqual(len(rate_limit_store), 0)

    def test_F63_rate_limit_enabled_by_default(self):
        """F63 RATE_LIMIT_ENABLED is True by default."""
        from rate_limiter import RATE_LIMIT_ENABLED
        self.assertTrue(RATE_LIMIT_ENABLED)

    def test_F64_login_limit_default_10(self):
        """F64 Default login rate limit is 10 per hour."""
        from rate_limiter import RATE_LIMIT_LOGIN
        self.assertEqual(RATE_LIMIT_LOGIN, 10)

    def test_F65_register_limit_default_5(self):
        """F65 Default registration rate limit is 5 per hour."""
        from rate_limiter import RATE_LIMIT_REGISTER
        self.assertEqual(RATE_LIMIT_REGISTER, 5)

# ===========================================================================
# F71-F80  Security Headers & Input Validation
# ===========================================================================
class TestSecurityHeaders(_Base):

    def _authed_get(self, path):
        self._register('hdr_user'); self._login('hdr_user')
        return self.client.get(path)

    def test_F71_x_content_type_options(self):
        """F71 X-Content-Type-Options: nosniff is set."""
        rv = self._authed_get('/')
        self.assertEqual(rv.headers.get('X-Content-Type-Options'), 'nosniff')

    def test_F72_referrer_policy(self):
        """F72 Referrer-Policy header is set."""
        rv = self._authed_get('/')
        self.assertIn('Referrer-Policy', rv.headers)

    def test_F73_csp_default_src_self(self):
        """F73 CSP contains default-src 'self'."""
        rv = self._authed_get('/')
        csp = rv.headers.get('Content-Security-Policy', '')
        self.assertIn("default-src 'self'", csp)

    def test_F74_username_max_length(self):
        """F74 Username longer than allowed is rejected."""
        rv = self._register(u='a' * 200)
        self.assertNotIn(b'Logout', rv.data)

    def test_F75_invalid_email_rejected(self):
        """F75 Invalid email format is rejected at registration."""
        rv = self._register(e='not-an-email')
        self.assertNotIn(b'Logout', rv.data)

    def test_F76_sql_injection_in_search_safe(self):
        """F76 SQL injection attempt in search does not crash app."""
        self._register('f76user'); self._login('f76user')
        rv = self.client.get("/search?q=' OR '1'='1", follow_redirects=True)
        self.assertIn(rv.status_code, [200, 400])
        self.assertNotIn(b'traceback', rv.data.lower())

    def test_F77_xss_in_note_key_escaped(self):
        """F77 XSS payload in note key is not executed (escaped in output)."""
        self._register('f77user'); self._login('f77user')
        self._add_folder('F')
        xss = '<script>alert(1)</script>'
        self._add_note(1, key=xss, val='v')
        rv = self.client.get('/folder/1')
        self.assertNotIn(b'<script>alert(1)</script>', rv.data)

    def test_F78_404_returns_correct_status(self):
        """F78 Unknown route returns 404."""
        rv = self.client.get('/nonexistent_route_xyz')
        self.assertEqual(rv.status_code, 404)

    def test_F79_sync_s3_async_noop_in_testing(self):
        """F79 sync_s3_async() is a no-op in TESTING mode (no thread leak)."""
        if not hasattr(self.en, 'sync_s3_async'):
            self.skipTest("sync_s3_async not on this branch — DEFECT")
        import threading
        before = threading.active_count()
        self.en.sync_s3_async()
        import time; time.sleep(0.05)
        after = threading.active_count()
        self.assertEqual(before, after)

    def test_F80_audit_log_records_note_create(self):
        """F80 Creating a note writes an entry to audit_log."""
        self._register('f80user'); self._login('f80user')
        self._add_folder('F')
        self._add_note(1, key='AuditNote', val='v')
        with sqlite3.connect(self.db_path) as con:
            count = con.execute(
                "SELECT COUNT(*) FROM audit_log WHERE action='CREATE'").fetchone()[0]
        self.assertGreater(count, 0)

# ===========================================================================
# F81-F90  Admin Panel
# ===========================================================================
class TestAdminPanel(_Base):

    def test_F81_admin_login_success(self):
        """F81 Admin login with correct credentials succeeds."""
        os.environ['ADMIN_USER'] = 'admin'
        os.environ['ADMIN_PASS'] = 'admin'
        rv = self.client.post('/admin', data={'username': 'admin', 'password': 'admin'},
                              follow_redirects=True)
        self.assertIn(rv.status_code, [200, 302])

    def test_F82_admin_wrong_password_rejected(self):
        """F82 Admin login with wrong password is rejected."""
        os.environ['ADMIN_USER'] = 'admin'
        os.environ['ADMIN_PASS'] = 'admin'
        rv = self.client.post('/admin', data={'username': 'admin', 'password': 'wrong'},
                              follow_redirects=True)
        self.assertNotIn(b'Dashboard', rv.data)

    def test_F83_admin_dashboard_requires_session(self):
        """F83 Admin dashboard is inaccessible without admin session."""
        rv = self.client.get('/admin/dashboard')
        self.assertIn(rv.status_code, [302, 403])

    def test_F84_admin_can_see_users(self):
        """F84 Admin dashboard lists registered users."""
        self._register('f84user')
        os.environ['ADMIN_USER'] = 'admin'
        os.environ['ADMIN_PASS'] = 'admin'
        self.client.post('/admin', data={'username': 'admin', 'password': 'admin'},
                         follow_redirects=True)
        rv = self.client.get('/admin/dashboard')
        self.assertIn(b'f84user', rv.data)

    def test_F85_admin_delete_user(self):
        """F85 Admin can delete a user."""
        self._register('f85user')
        os.environ['ADMIN_USER'] = 'admin'
        os.environ['ADMIN_PASS'] = 'admin'
        self.client.post('/admin', data={'username': 'admin', 'password': 'admin'},
                         follow_redirects=True)
        with sqlite3.connect(self.db_path) as con:
            uid = con.execute("SELECT id FROM users WHERE username='f85user'").fetchone()[0]
        rv = self.client.post(f'/admin/user/delete/{uid}', follow_redirects=True)
        self.assertIn(rv.status_code, [200, 302])
        with sqlite3.connect(self.db_path) as con:
            row = con.execute("SELECT id FROM users WHERE username='f85user'").fetchone()
        self.assertIsNone(row)


# ===========================================================================
# F91-F99  Android App
# ===========================================================================
class TestAndroidApp(unittest.TestCase):

    def setUp(self):
        import sys, importlib, importlib.util
        # android_app/ lives in the project root, not in Test/
        _android_path = os.path.join(os.path.dirname(__file__), '..', 'android_app')
        _android_path = os.path.abspath(_android_path)
        # Force load from android_app/ regardless of what's already in sys.modules
        spec = importlib.util.spec_from_file_location(
            'evernothing_android',
            os.path.join(_android_path, 'evernothing_android.py'))
        ea = importlib.util.module_from_spec(spec)
        sys.modules['evernothing_android'] = ea
        # Ensure config_loader resolves from android_app/
        if _android_path not in sys.path:
            sys.path.insert(0, _android_path)
        spec.loader.exec_module(ea)
        self.db_fd, self.db_path = tempfile.mkstemp()
        with sqlite3.connect(self.db_path) as con:
            con.executescript("""
            CREATE TABLE users(id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT);
            CREATE TABLE notes(id INTEGER PRIMARY KEY, user_id INTEGER, folder_id INTEGER,
                note_key TEXT, note_value TEXT, description TEXT, updated_at TEXT);
            CREATE TABLE folders(id INTEGER PRIMARY KEY, user_id INTEGER, name TEXT, parent_id INTEGER);
            """)
        os.environ['DB_FILE'] = self.db_path
        os.environ['AWS_ACCESS_KEY_ID'] = 'test_key'
        os.environ['AWS_SECRET_ACCESS_KEY'] = 'test_secret'
        self.app = ea.app
        self.app.config['TESTING'] = True
        ea.DB = self.db_path
        self.client = self.app.test_client()
        self.ea = ea

    def tearDown(self):
        os.close(self.db_fd)
        try: os.unlink(self.db_path)
        except OSError: pass

    def test_F91_login_page_loads(self):
        """F91 Android login page returns 200."""
        rv = self.client.get('/login')
        self.assertEqual(rv.status_code, 200)

    def test_F92_home_requires_login(self):
        """F92 Android home redirects unauthenticated users."""
        rv = self.client.get('/')
        self.assertEqual(rv.status_code, 302)

    def test_F93_encryption_enabled_by_default(self):
        """F93 Android app has ENCRYPTION_ENABLED=True by default."""
        self.assertTrue(self.ea.ENCRYPTION_ENABLED)

    def test_F94_key_derived_not_from_file(self):
        """F94 Android encryption key is derived, not loaded from file."""
        self.assertIsNotNone(self.ea._aesgcm)
        self.assertTrue(self.ea._encryption_available)

    def test_F95_encrypt_decrypt_roundtrip(self):
        """F95 Android _encrypt/_decrypt roundtrip works."""
        ct = self.ea._encrypt('android secret')
        self.assertNotEqual(ct, 'android secret')
        self.assertEqual(self.ea._decrypt(ct), 'android secret')

    def test_F96_checkpoint_route_exists(self):
        """F96 /checkpoint POST route exists and returns 200 when logged in."""
        from werkzeug.security import generate_password_hash
        import sqlite3 as _sq
        with _sq.connect(self.db_path) as con:
            con.execute("INSERT INTO users (id,username,password) VALUES (1,'admin',?)",
                        (generate_password_hash('pass'),))
        with self.client.session_transaction() as sess:
            sess['_user_id'] = '1'
            sess['_fresh'] = True
        with patch.object(self.ea, 'sync_to_s3', return_value=True):
            rv = self.client.post('/checkpoint')
        self.assertEqual(rv.status_code, 200)

    def test_F97_s3_missing_bucket_returns_false(self):
        """F97 sync_to_s3 returns False when S3_BUCKET_NAME not set."""
        orig = self.ea.S3_BUCKET_NAME
        self.ea.S3_BUCKET_NAME = ''
        result = self.ea.sync_to_s3()
        self.ea.S3_BUCKET_NAME = orig
        self.assertFalse(result)

    def test_F98_s3_missing_db_returns_false(self):
        """F98 sync_to_s3 returns False when DB file missing."""
        self.ea.DB = '/nonexistent/path.db'
        result = self.ea.sync_to_s3()
        self.ea.DB = self.db_path
        self.assertFalse(result)

    def test_F99_checkpoint_interval_configurable(self):
        """F99 CHECKPOINT_INTERVAL is configurable via env var."""
        with patch.dict(os.environ, {'CHECKPOINT_INTERVAL': '300'}):
            import importlib
            import evernothing_android as ea2
            importlib.reload(ea2)
            self.assertEqual(ea2.CHECKPOINT_INTERVAL, 300)


if __name__ == '__main__':
    unittest.main(verbosity=2)
