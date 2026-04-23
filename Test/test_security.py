"""
test_security.py — Tests for all security changes made to EverNothing.

Covers:
  #1  IAM role credential chain (no hard-coded key fallback)
  #7  SSE on every S3 upload (AES256 default, KMS when configured)
  #8  DB file-level encryption before upload
  #9  TLS verification on boto3 clients
  #10 Auto-created bucket gets full hardening (encryption, versioning, public-access-block, policy)
  #11 Bucket policy enforces aws:SecureTransport
  #12 Bucket policy enforces IP allowlist when S3_ALLOWED_IPS is set
  #13 Server access logging enabled on bucket
  #14 Object Lock GOVERNANCE retention enabled on bucket
  HTTPS redirect (enforce_https before_request hook)
  Secure cookie defaults
"""
import sys, os
# Add Scripts/ to path so setup_aws_s3 is importable after reorganization
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'Scripts'))

import io
import json
import os
import sqlite3
import tempfile
import unittest
from unittest.mock import MagicMock, call, patch


# ---------------------------------------------------------------------------
# Shared DB setup helper
# ---------------------------------------------------------------------------

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

def _make_db():
    fd, path = tempfile.mkstemp()
    with sqlite3.connect(path) as con:
        con.executescript(_SCHEMA)
    return fd, path


# ---------------------------------------------------------------------------
# Base test case with Flask app wired to a temp DB
# ---------------------------------------------------------------------------

class _Base(unittest.TestCase):

    def setUp(self):
        self.db_fd, self.db_path = _make_db()
        import evernothing
        evernothing.DB = self.db_path
        evernothing.app.config['TESTING'] = True
        evernothing.app.config['WTF_CSRF_ENABLED'] = False
        evernothing.app.config['SECRET_KEY'] = 'test_key'
        evernothing.login_manager.session_protection = None
        self.app = evernothing.app
        self.client = self.app.test_client()
        self.en = evernothing

    def tearDown(self):
        os.close(self.db_fd)
        try:
            os.unlink(self.db_path)
        except OSError:
            pass


# ===========================================================================
# 1. IAM role credential chain — no hard-coded empty-string fallback
# ===========================================================================

class TestCredentialChain(_Base):

    def test_no_keys_uses_default_chain(self):
        """_s3_client() must not pass explicit keys when env vars are absent."""
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop('AWS_ACCESS_KEY_ID', None)
            os.environ.pop('AWS_SECRET_ACCESS_KEY', None)
            with patch('evernothing.boto3') as mock_boto3:
                mock_boto3.client.return_value = MagicMock()
                mock_boto3.Session.return_value.client.return_value = MagicMock()
                self.en.AWS_ACCESS_KEY_ID = None
                self.en.AWS_SECRET_ACCESS_KEY = None
                self.en.AWS_PROFILE = ''
                self.en._s3_client()
                call_kwargs = mock_boto3.client.call_args[1]
                self.assertNotIn('aws_access_key_id', call_kwargs)
                self.assertNotIn('aws_secret_access_key', call_kwargs)

    def test_explicit_keys_passed_when_set(self):
        """_s3_client() passes explicit keys when both env vars are present."""
        with patch('evernothing.boto3') as mock_boto3:
            mock_boto3.client.return_value = MagicMock()
            self.en.AWS_ACCESS_KEY_ID = 'AKIATEST'
            self.en.AWS_SECRET_ACCESS_KEY = 'secret'
            self.en.AWS_PROFILE = ''
            self.en._s3_client()
            call_kwargs = mock_boto3.client.call_args[1]
            self.assertEqual(call_kwargs.get('aws_access_key_id'), 'AKIATEST')
            self.assertEqual(call_kwargs.get('aws_secret_access_key'), 'secret')


# ===========================================================================
# 7. SSE on every upload — AES256 default, KMS when KMS_KEY_ID is set
# ===========================================================================

class TestSSEOnUploads(_Base):

    def _run_sync(self, mock_s3):
        with patch('evernothing._s3_client', return_value=mock_s3):
            with patch('evernothing.boto3', True):
                self.en.sync_s3()

    def test_db_backup_has_sse_aes256_by_default(self):
        """DB backup uploads must carry ServerSideEncryption=AES256 when no KMS key."""
        mock_s3 = MagicMock()
        with patch('evernothing.KMS_KEY_ID', None):
            self._run_sync(mock_s3)
        for c in mock_s3.upload_fileobj.call_args_list:
            extra = c[1].get('ExtraArgs', {})
            self.assertIn('ServerSideEncryption', extra,
                          f"Missing SSE on upload call: {c}")
            self.assertEqual(extra['ServerSideEncryption'], 'AES256')

    def test_db_backup_has_sse_kms_when_configured(self):
        """DB backup uploads must use aws:kms when KMS_KEY_ID is set."""
        mock_s3 = MagicMock()
        with patch('evernothing.KMS_KEY_ID', 'arn:aws:kms:us-east-1:123:key/abc'):
            self._run_sync(mock_s3)
        for c in mock_s3.upload_fileobj.call_args_list:
            extra = c[1].get('ExtraArgs', {})
            self.assertEqual(extra.get('ServerSideEncryption'), 'aws:kms')
            self.assertEqual(extra.get('SSEKMSKeyId'), 'arn:aws:kms:us-east-1:123:key/abc')

    def test_evernothing_s3_sse_on_upload(self):
        """evernothing_s3.sync_to_s3() must pass SSE ExtraArgs on both upload calls."""
        import evernothing_s3
        mock_s3 = MagicMock()
        mock_s3.head_bucket.return_value = {}
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as f:
            f.write(b'SQLite format 3\x00' + b'\x00' * 84)
            db_path = f.name
        try:
            with patch('evernothing_s3.boto3') as mock_boto3:
                mock_boto3.client.return_value = mock_s3
                orig = evernothing_s3.DB_FILE
                evernothing_s3.DB_FILE = db_path
                evernothing_s3.S3_BUCKET_NAME = 'test-bucket'
                evernothing_s3.sync_to_s3()
                evernothing_s3.DB_FILE = orig
            for c in mock_s3.upload_fileobj.call_args_list + mock_s3.upload_file.call_args_list:
                extra = c[1].get('ExtraArgs', {})
                self.assertIn('ServerSideEncryption', extra,
                              f"Missing SSE ExtraArgs on: {c}")
        finally:
            os.unlink(db_path)


# ===========================================================================
# 8. DB file-level encryption before upload
# ===========================================================================

class TestDBFileEncryption(_Base):

    def test_db_bytes_encrypted_before_upload(self):
        """Bytes sent to S3 for DB backup must not be a raw SQLite file."""
        mock_s3 = MagicMock()
        captured = []

        def capture_upload(buf, bucket, key, **kwargs):
            captured.append((key, buf.read()))

        mock_s3.upload_fileobj.side_effect = capture_upload

        with patch('evernothing._s3_client', return_value=mock_s3):
            with patch('evernothing.boto3', True):
                with patch('evernothing.KMS_KEY_ID', None):
                    self.en.sync_s3()

        db_uploads = [(k, d) for k, d in captured if not k.startswith('changes/')]
        self.assertTrue(db_uploads, "No DB backup upload found")
        for key, data in db_uploads:
            # Raw SQLite files start with "SQLite format 3\x00"
            self.assertFalse(
                data[:16] == b'SQLite format 3\x00',
                f"DB upload '{key}' appears to be unencrypted SQLite"
            )

    def test_db_encryption_roundtrip(self):
        """Encrypted DB bytes can be decrypted back to the original content."""
        import evernothing_s3
        original = b'SQLite format 3\x00' + b'\xAB' * 100

        # Write a temp key file
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        key = AESGCM.generate_key(bit_length=256)
        fd, key_path = tempfile.mkstemp()
        os.write(fd, key)
        os.close(fd)

        orig_key_file = evernothing_s3._KEY_FILE
        evernothing_s3._KEY_FILE = key_path
        try:
            enc, suffix = evernothing_s3._encrypt_db_bytes(original)
            self.assertEqual(suffix, '.enc')
            self.assertNotEqual(enc, original)
            # Decrypt and verify
            aesgcm = AESGCM(key)
            decrypted = aesgcm.decrypt(enc[:12], enc[12:], None)
            self.assertEqual(decrypted, original)
        finally:
            evernothing_s3._KEY_FILE = orig_key_file
            os.unlink(key_path)

    def test_db_encryption_falls_back_gracefully_without_key_file(self):
        """_encrypt_db_bytes returns original data with empty suffix when key file missing."""
        import evernothing_s3
        orig_key_file = evernothing_s3._KEY_FILE
        evernothing_s3._KEY_FILE = '/nonexistent/secret.key'
        try:
            data = b'raw data'
            result, suffix = evernothing_s3._encrypt_db_bytes(data)
            self.assertEqual(result, data)
            self.assertEqual(suffix, '')
        finally:
            evernothing_s3._KEY_FILE = orig_key_file


# ===========================================================================
# 9. TLS verification on boto3 clients
# ===========================================================================

class TestTLSVerification(_Base):

    def test_s3_client_has_verify_true(self):
        """_s3_client() must pass verify=True (or a CA bundle path)."""
        with patch('evernothing.boto3') as mock_boto3:
            mock_boto3.client.return_value = MagicMock()
            self.en.AWS_ACCESS_KEY_ID = 'KEY'
            self.en.AWS_SECRET_ACCESS_KEY = 'SECRET'
            self.en.AWS_PROFILE = ''
            with patch.dict(os.environ, {'AWS_CA_BUNDLE': ''}, clear=False):
                os.environ.pop('AWS_CA_BUNDLE', None)
                self.en._s3_client()
            call_kwargs = mock_boto3.client.call_args[1]
            verify = call_kwargs.get('verify')
            # True or a non-empty path string are both acceptable
            self.assertTrue(verify, "verify must be True or a CA bundle path")

    def test_evernothing_s3_client_has_verify(self):
        """evernothing_s3 boto3.client() call must include verify."""
        import evernothing_s3
        with patch('evernothing_s3.boto3') as mock_boto3:
            mock_s3 = MagicMock()
            mock_s3.head_bucket.return_value = {}
            mock_boto3.client.return_value = mock_s3
            with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as f:
                f.write(b'\x00' * 100)
                db_path = f.name
            try:
                orig = evernothing_s3.DB_FILE
                evernothing_s3.DB_FILE = db_path
                evernothing_s3.S3_BUCKET_NAME = 'test-bucket'
                evernothing_s3.sync_to_s3()
                evernothing_s3.DB_FILE = orig
            finally:
                os.unlink(db_path)
            call_kwargs = mock_boto3.client.call_args[1]
            self.assertIn('verify', call_kwargs)
            self.assertTrue(call_kwargs['verify'])


# ===========================================================================
# 10. Auto-created bucket hardening
# ===========================================================================

class TestBucketHardening(_Base):

    def _run_sync_with_no_bucket(self):
        """Run sync_to_s3 simulating a missing bucket (head_bucket raises)."""
        import evernothing_s3
        mock_s3 = MagicMock()
        mock_s3.head_bucket.side_effect = Exception("NoSuchBucket")
        mock_s3.get_paginator.return_value.paginate.return_value = []

        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as f:
            f.write(b'\x00' * 100)
            db_path = f.name

        orig_db = evernothing_s3.DB_FILE
        orig_bucket = evernothing_s3.S3_BUCKET_NAME
        evernothing_s3.DB_FILE = db_path
        evernothing_s3.S3_BUCKET_NAME = 'new-bucket'

        with patch('evernothing_s3.boto3') as mock_boto3:
            mock_boto3.client.return_value = mock_s3
            evernothing_s3.sync_to_s3()

        evernothing_s3.DB_FILE = orig_db
        evernothing_s3.S3_BUCKET_NAME = orig_bucket
        os.unlink(db_path)
        return mock_s3

    def test_auto_create_blocks_public_access(self):
        mock_s3 = self._run_sync_with_no_bucket()
        mock_s3.put_public_access_block.assert_called()
        # Called at least once for the main bucket
        main_call = mock_s3.put_public_access_block.call_args_list[0]
        cfg = main_call[1]['PublicAccessBlockConfiguration']
        self.assertTrue(cfg['BlockPublicAcls'])
        self.assertTrue(cfg['RestrictPublicBuckets'])

    def test_auto_create_enables_encryption(self):
        mock_s3 = self._run_sync_with_no_bucket()
        mock_s3.put_bucket_encryption.assert_called_once()

    def test_auto_create_enables_versioning(self):
        mock_s3 = self._run_sync_with_no_bucket()
        mock_s3.put_bucket_versioning.assert_called_once()
        cfg = mock_s3.put_bucket_versioning.call_args[1]['VersioningConfiguration']
        self.assertEqual(cfg['Status'], 'Enabled')

    def test_auto_create_applies_bucket_policy(self):
        mock_s3 = self._run_sync_with_no_bucket()
        mock_s3.put_bucket_policy.assert_called()


# ===========================================================================
# 11. Bucket policy enforces aws:SecureTransport
# ===========================================================================

class TestSecureTransportPolicy(_Base):

    def _get_policy_statements(self, bucket_name='test-bucket', allowed_ips=None):
        mock_s3 = MagicMock()
        env = {}
        if allowed_ips:
            env['S3_ALLOWED_IPS'] = ','.join(allowed_ips)
        with patch.dict(os.environ, env):
            self.en._apply_bucket_policy(mock_s3, bucket_name)
        policy = json.loads(mock_s3.put_bucket_policy.call_args[1]['Policy'])
        return policy['Statement']

    def test_deny_insecure_transport_present(self):
        stmts = self._get_policy_statements()
        sids = [s['Sid'] for s in stmts]
        self.assertIn('DenyInsecureTransport', sids)

    def test_deny_insecure_transport_condition(self):
        stmts = {s['Sid']: s for s in self._get_policy_statements()}
        stmt = stmts['DenyInsecureTransport']
        self.assertEqual(stmt['Effect'], 'Deny')
        self.assertEqual(stmt['Condition']['Bool']['aws:SecureTransport'], 'false')

    def test_deny_insecure_transport_covers_bucket_and_objects(self):
        stmts = {s['Sid']: s for s in self._get_policy_statements('my-bucket')}
        resources = stmts['DenyInsecureTransport']['Resource']
        self.assertIn('arn:aws:s3:::my-bucket', resources)
        self.assertIn('arn:aws:s3:::my-bucket/*', resources)

    def test_setup_s3_policy_has_secure_transport(self):
        """setup_aws_s3._apply_bucket_policy also enforces SecureTransport."""
        import setup_aws_s3
        mock_s3 = MagicMock()
        orig = setup_aws_s3.ALLOWED_IPS
        setup_aws_s3.ALLOWED_IPS = []
        setup_aws_s3._apply_bucket_policy(mock_s3, 'setup-bucket')
        setup_aws_s3.ALLOWED_IPS = orig
        policy = json.loads(mock_s3.put_bucket_policy.call_args[1]['Policy'])
        sids = [s['Sid'] for s in policy['Statement']]
        self.assertIn('DenyInsecureTransport', sids)


# ===========================================================================
# 12. Bucket policy IP allowlist
# ===========================================================================

class TestIPAllowlistPolicy(_Base):

    def test_ip_restriction_absent_when_no_env(self):
        mock_s3 = MagicMock()
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop('S3_ALLOWED_IPS', None)
            self.en._apply_bucket_policy(mock_s3, 'bucket')
        policy = json.loads(mock_s3.put_bucket_policy.call_args[1]['Policy'])
        sids = [s['Sid'] for s in policy['Statement']]
        self.assertNotIn('DenyNonAllowedIPs', sids)

    def test_ip_restriction_present_when_env_set(self):
        mock_s3 = MagicMock()
        with patch.dict(os.environ, {'S3_ALLOWED_IPS': '10.0.0.0/8,203.0.113.5/32'}):
            self.en._apply_bucket_policy(mock_s3, 'bucket')
        policy = json.loads(mock_s3.put_bucket_policy.call_args[1]['Policy'])
        stmts = {s['Sid']: s for s in policy['Statement']}
        self.assertIn('DenyNonAllowedIPs', stmts)
        ips = stmts['DenyNonAllowedIPs']['Condition']['NotIpAddress']['aws:SourceIp']
        self.assertIn('10.0.0.0/8', ips)
        self.assertIn('203.0.113.5/32', ips)

    def test_setup_s3_ip_restriction(self):
        import setup_aws_s3
        mock_s3 = MagicMock()
        orig = setup_aws_s3.ALLOWED_IPS
        setup_aws_s3.ALLOWED_IPS = ['192.168.1.0/24']
        setup_aws_s3._apply_bucket_policy(mock_s3, 'bucket')
        setup_aws_s3.ALLOWED_IPS = orig
        policy = json.loads(mock_s3.put_bucket_policy.call_args[1]['Policy'])
        sids = [s['Sid'] for s in policy['Statement']]
        self.assertIn('DenyNonAllowedIPs', sids)


# ===========================================================================
# 13. Server access logging
# ===========================================================================

class TestAccessLogging(_Base):

    def test_enable_s3_access_logging_called_on_first_sync(self):
        """_enable_s3_access_logging is called during first sync (sentinel absent)."""
        sentinel = self.en._BUCKET_POLICY_SENTINEL
        if os.path.exists(sentinel):
            os.remove(sentinel)
        self.en._bucket_policy_applied = False

        mock_s3 = MagicMock()
        with patch('evernothing._s3_client', return_value=mock_s3):
            with patch('evernothing.boto3', True):
                with patch.object(self.en, '_enable_s3_access_logging') as mock_log:
                    with patch.object(self.en, '_apply_bucket_policy'):
                        with patch.object(self.en, '_enable_s3_object_lock'):
                            self.en.sync_s3()
                    mock_log.assert_called_once_with(mock_s3, self.en.S3_BUCKET_NAME)

        if os.path.exists(sentinel):
            os.remove(sentinel)

    def test_enable_s3_access_logging_creates_log_bucket(self):
        """_enable_s3_access_logging creates a <bucket>-logs bucket and enables logging."""
        mock_s3 = MagicMock()
        mock_s3.head_bucket.side_effect = Exception("NoSuchBucket")
        self.en._enable_s3_access_logging(mock_s3, 'my-bucket')
        # Should have tried to create the log bucket
        create_calls = [str(c) for c in mock_s3.create_bucket.call_args_list]
        self.assertTrue(any('my-bucket-logs' in c for c in create_calls))
        mock_s3.put_bucket_logging.assert_called_once()
        logging_cfg = mock_s3.put_bucket_logging.call_args[1]['BucketLoggingStatus']
        self.assertEqual(logging_cfg['LoggingEnabled']['TargetBucket'], 'my-bucket-logs')
        self.assertEqual(logging_cfg['LoggingEnabled']['TargetPrefix'], 'access-logs/')

    def test_enable_s3_access_logging_uses_existing_log_bucket(self):
        """_enable_s3_access_logging skips creation when log bucket already exists."""
        mock_s3 = MagicMock()
        mock_s3.head_bucket.return_value = {}   # bucket exists
        self.en._enable_s3_access_logging(mock_s3, 'my-bucket')
        mock_s3.create_bucket.assert_not_called()
        mock_s3.put_bucket_logging.assert_called_once()


# ===========================================================================
# 14. Object Lock
# ===========================================================================

class TestObjectLock(_Base):

    def test_enable_s3_object_lock_called_on_first_sync(self):
        sentinel = self.en._BUCKET_POLICY_SENTINEL
        if os.path.exists(sentinel):
            os.remove(sentinel)
        self.en._bucket_policy_applied = False

        mock_s3 = MagicMock()
        with patch('evernothing._s3_client', return_value=mock_s3):
            with patch('evernothing.boto3', True):
                with patch.object(self.en, '_enable_s3_object_lock') as mock_lock:
                    with patch.object(self.en, '_apply_bucket_policy'):
                        with patch.object(self.en, '_enable_s3_access_logging'):
                            self.en.sync_s3()
                    mock_lock.assert_called_once_with(mock_s3, self.en.S3_BUCKET_NAME)

        if os.path.exists(sentinel):
            os.remove(sentinel)

    def test_object_lock_governance_mode(self):
        """_enable_s3_object_lock sets GOVERNANCE mode."""
        mock_s3 = MagicMock()
        with patch.dict(os.environ, {'S3_LOCK_DAYS': '30'}):
            self.en._enable_s3_object_lock(mock_s3, 'my-bucket')
        cfg = mock_s3.put_object_lock_configuration.call_args[1]['ObjectLockConfiguration']
        self.assertEqual(cfg['Rule']['DefaultRetention']['Mode'], 'GOVERNANCE')
        self.assertEqual(cfg['Rule']['DefaultRetention']['Days'], 30)

    def test_object_lock_respects_s3_lock_days_env(self):
        mock_s3 = MagicMock()
        with patch.dict(os.environ, {'S3_LOCK_DAYS': '90'}):
            self.en._enable_s3_object_lock(mock_s3, 'my-bucket')
        cfg = mock_s3.put_object_lock_configuration.call_args[1]['ObjectLockConfiguration']
        self.assertEqual(cfg['Rule']['DefaultRetention']['Days'], 90)

    def test_object_lock_failure_does_not_raise(self):
        """A bucket that doesn't support Object Lock logs a warning but doesn't crash."""
        mock_s3 = MagicMock()
        mock_s3.put_object_lock_configuration.side_effect = Exception("ObjectLockConfigurationNotFoundError")
        try:
            self.en._enable_s3_object_lock(mock_s3, 'my-bucket')
        except Exception:
            self.fail("_enable_s3_object_lock raised unexpectedly")


# ===========================================================================
# HTTPS redirect
# ===========================================================================

class TestHTTPSRedirect(_Base):

    def test_http_redirects_to_https(self):
        """Plain HTTP requests are redirected to HTTPS (301) when SSL cert is present."""
        self.app.config['TESTING'] = False
        try:
            with patch('os.path.exists', return_value=True):
                resp = self.client.get('http://localhost/login')
            self.assertEqual(resp.status_code, 301)
            self.assertIn('https://', resp.headers['Location'])
        finally:
            self.app.config['TESTING'] = True

    def test_https_not_redirected(self):
        """Requests already on HTTPS are not redirected."""
        self.app.config['TESTING'] = False
        try:
            with patch('os.path.exists', return_value=True):
                resp = self.client.get('https://localhost/login')
            self.assertNotEqual(resp.status_code, 301)
        finally:
            self.app.config['TESTING'] = True

    def test_x_forwarded_proto_https_not_redirected(self):
        """Requests with X-Forwarded-Proto: https (reverse proxy) are not redirected."""
        self.app.config['TESTING'] = False
        try:
            with patch('os.path.exists', return_value=True):
                resp = self.client.get('http://localhost/login',
                                       headers={'X-Forwarded-Proto': 'https'})
            self.assertNotEqual(resp.status_code, 301)
        finally:
            self.app.config['TESTING'] = True

    def test_no_redirect_without_cert(self):
        """No redirect when cert/key files are absent — avoids ERR_SSL_PROTOCOL_ERROR."""
        self.app.config['TESTING'] = False
        try:
            with patch('os.path.exists', return_value=False):
                resp = self.client.get('http://localhost/login')
            self.assertNotEqual(resp.status_code, 301)
        finally:
            self.app.config['TESTING'] = True

    def test_testing_mode_skips_redirect(self):
        """enforce_https is a no-op in TESTING mode so unit tests work over HTTP."""
        self.app.config['TESTING'] = True
        resp = self.client.get('http://localhost/login')
        self.assertNotEqual(resp.status_code, 301)


# ===========================================================================
# Secure cookie defaults
# ===========================================================================

class TestSecureCookieDefaults(_Base):

    def test_session_cookie_secure_default_true(self):
        self.assertTrue(self.app.config.get('SESSION_COOKIE_SECURE'))

    def test_session_cookie_httponly(self):
        self.assertTrue(self.app.config.get('SESSION_COOKIE_HTTPONLY'))

    def test_remember_cookie_secure_default_true(self):
        self.assertTrue(self.app.config.get('REMEMBER_COOKIE_SECURE'))

    def test_remember_cookie_httponly(self):
        self.assertTrue(self.app.config.get('REMEMBER_COOKIE_HTTPONLY'))


if __name__ == '__main__':
    unittest.main()
