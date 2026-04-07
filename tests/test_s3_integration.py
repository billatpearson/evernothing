import unittest
import sys
import os
import json
import tempfile
import sqlite3
from unittest.mock import patch

import boto3
from moto import mock_aws

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import evernothing
from evernothing import app
from werkzeug.security import generate_password_hash

BUCKET = 'test-evernothing-bucket'


def _make_s3():
    return boto3.client('s3', region_name='us-east-1')


def _create_bucket(s3):
    s3.create_bucket(Bucket=BUCKET)


class S3IntegrationTestCase(unittest.TestCase):

    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp()
        evernothing.DB = self.db_path
        evernothing.S3_BUCKET_NAME = BUCKET
        evernothing.AWS_ACCESS_KEY_ID = 'testing'
        evernothing.AWS_SECRET_ACCESS_KEY = 'testing'
        evernothing.AWS_REGION = 'us-east-1'
        evernothing.KMS_KEY_ID = None

        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        evernothing.login_manager.session_protection = None
        self.client = app.test_client()

        with sqlite3.connect(self.db_path) as con:
            con.executescript("""
            CREATE TABLE users(id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT, last_login TEXT, email TEXT);
            CREATE TABLE folders(id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, name TEXT, parent_id INTEGER);
            CREATE TABLE notes(id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, folder_id INTEGER, note_key TEXT, note_value TEXT, description TEXT, updated_at TEXT);
            CREATE TABLE note_history(id INTEGER PRIMARY KEY AUTOINCREMENT, note_id INTEGER, user_id INTEGER, note_key TEXT, note_value TEXT, description TEXT, folder_id INTEGER, updated_at TEXT);
            CREATE TABLE user_sessions(id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, session_id TEXT, login_time TEXT, logout_time TEXT, ip_address TEXT, user_agent TEXT);
            CREATE TABLE attachments(id INTEGER PRIMARY KEY AUTOINCREMENT, note_id INTEGER, user_id INTEGER, filename TEXT, file_data BLOB, file_size INTEGER, uploaded_at TEXT);
            CREATE TABLE audit_log(id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, action TEXT, entity_type TEXT, entity_id INTEGER, old_values TEXT, new_values TEXT, timestamp TEXT, ip_address TEXT);
            CREATE TABLE sync_queue(id INTEGER PRIMARY KEY AUTOINCREMENT, entity_type TEXT, entity_id INTEGER, operation TEXT, payload TEXT, changed_at TEXT, synced_at TEXT);
            """)
            con.execute(
                "INSERT INTO users (username, password, email) VALUES (?,?,?)",
                ("testuser", generate_password_hash("Password1"), "test@example.com")
            )

        import rate_limiter
        rate_limiter.rate_limit_store.clear()

    def tearDown(self):
        evernothing.login_manager.session_protection = "basic"
        try:
            os.close(self.db_fd)
            os.unlink(self.db_path)
        except OSError:
            pass

    def _login(self):
        return self.client.post('/login', data={
            'username': 'testuser', 'password': 'Password1'
        }, follow_redirects=True)

    # --- 1. sync_s3: uploads full DB to root and backups/ ---

    @mock_aws
    def test_sync_s3_uploads_db_to_root(self):
        s3 = _make_s3()
        _create_bucket(s3)
        evernothing.sync_s3()
        keys = [o['Key'] for o in s3.list_objects_v2(Bucket=BUCKET).get('Contents', [])]
        # DB is uploaded encrypted — key is either DB or DB.enc
        db_keys = [k for k in keys if k == evernothing.DB or k == evernothing.DB + '.enc']
        self.assertTrue(db_keys, f"No DB key found in bucket. Keys: {keys}")

    @mock_aws
    def test_sync_s3_uploads_timestamped_backup(self):
        s3 = _make_s3()
        _create_bucket(s3)
        evernothing.sync_s3()
        keys = [o['Key'] for o in s3.list_objects_v2(Bucket=BUCKET).get('Contents', [])]
        backup_keys = [k for k in keys if k.startswith('backups/')]
        self.assertEqual(len(backup_keys), 1)
        self.assertIn(evernothing.DB, backup_keys[0])

    @mock_aws
    def test_sync_s3_db_content_matches_local(self):
        """DB uploaded to S3 must decrypt back to the local DB bytes."""
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        s3 = _make_s3()
        _create_bucket(s3)
        evernothing.sync_s3()
        keys = [o['Key'] for o in s3.list_objects_v2(Bucket=BUCKET).get('Contents', [])]

        with open(self.db_path, 'rb') as f:
            local_bytes = f.read()

        enc_key = evernothing.DB + '.enc'
        if enc_key in keys:
            # Encrypted upload — decrypt and compare
            remote_bytes = s3.get_object(Bucket=BUCKET, Key=enc_key)['Body'].read()
            aesgcm = AESGCM(evernothing.KEY)
            decrypted = aesgcm.decrypt(remote_bytes[:12], remote_bytes[12:], None)
            self.assertEqual(decrypted, local_bytes)
        else:
            # Fallback: encryption unavailable, raw bytes uploaded
            obj = s3.get_object(Bucket=BUCKET, Key=evernothing.DB)
            self.assertEqual(obj['Body'].read(), local_bytes)

    # --- 2. sync_s3: delta upload ---

    @mock_aws
    def test_sync_s3_uploads_delta_for_queued_changes(self):
        s3 = _make_s3()
        _create_bucket(s3)
        self._login()
        self.client.post('/folder/add', data={'name': 'F1'}, follow_redirects=True)
        with sqlite3.connect(self.db_path) as con:
            fid = con.execute("SELECT id FROM folders").fetchone()[0]
        self.client.post(f'/add/{fid}', data={'note': 'DeltaNote', 'content': 'DeltaVal', 'description': ''})
        evernothing.sync_s3()
        keys = [o['Key'] for o in s3.list_objects_v2(Bucket=BUCKET).get('Contents', [])]
        delta_keys = [k for k in keys if k.startswith('changes/')]
        self.assertEqual(len(delta_keys), 1)

    @mock_aws
    def test_sync_s3_delta_contains_note_value(self):
        s3 = _make_s3()
        _create_bucket(s3)
        self._login()
        with patch('evernothing.sync_s3'):
            self.client.post('/folder/add', data={'name': 'F2'}, follow_redirects=True)
            with sqlite3.connect(self.db_path) as con:
                fid = con.execute("SELECT id FROM folders").fetchone()[0]
            self.client.post(f'/add/{fid}', data={'note': 'PayloadNote', 'content': 'PayloadVal', 'description': 'desc1'})
        evernothing.sync_s3()
        keys = [o['Key'] for o in s3.list_objects_v2(Bucket=BUCKET).get('Contents', [])]
        delta_key = next(k for k in keys if k.startswith('changes/'))
        data = json.loads(s3.get_object(Bucket=BUCKET, Key=delta_key)['Body'].read())
        note_change = next((c for c in data if c['entity'] == 'note'), None)
        self.assertIsNotNone(note_change)
        self.assertIn('note_value', note_change['data'])
        self.assertIn('note_key', note_change['data'])

    @mock_aws
    def test_sync_s3_delta_marks_rows_synced(self):
        s3 = _make_s3()
        _create_bucket(s3)
        self._login()
        with patch('evernothing.sync_s3'):
            self.client.post('/folder/add', data={'name': 'F3'}, follow_redirects=True)
            with sqlite3.connect(self.db_path) as con:
                fid = con.execute("SELECT id FROM folders").fetchone()[0]
            self.client.post(f'/add/{fid}', data={'note': 'SyncedNote', 'content': 'v', 'description': ''})
        evernothing.sync_s3()
        with sqlite3.connect(self.db_path) as con:
            unsynced = con.execute("SELECT COUNT(*) FROM sync_queue WHERE synced_at IS NULL").fetchone()[0]
        self.assertEqual(unsynced, 0)

    @mock_aws
    def test_sync_s3_no_delta_uploaded_when_queue_empty(self):
        s3 = _make_s3()
        _create_bucket(s3)
        evernothing.sync_s3()
        keys = [o['Key'] for o in s3.list_objects_v2(Bucket=BUCKET).get('Contents', [])]
        delta_keys = [k for k in keys if k.startswith('changes/')]
        self.assertEqual(len(delta_keys), 0)

    @mock_aws
    def test_sync_s3_second_call_only_uploads_new_changes(self):
        import datetime
        from datetime import timezone
        s3 = _make_s3()
        _create_bucket(s3)
        # First batch: folder + Note1
        with patch('evernothing.sync_s3'):
            self._login()
            self.client.post('/folder/add', data={'name': 'F4'}, follow_redirects=True)
            with sqlite3.connect(self.db_path) as con:
                fid = con.execute("SELECT id FROM folders").fetchone()[0]
            self.client.post(f'/add/{fid}', data={'note': 'Note1', 'content': 'v1', 'description': ''})
        evernothing.sync_s3()  # uploads delta 1, marks rows synced
        with sqlite3.connect(self.db_path) as con:
            synced_after_first = con.execute(
                "SELECT COUNT(*) FROM sync_queue WHERE synced_at IS NOT NULL"
            ).fetchone()[0]
        # Second batch: insert a new unsynced queue row
        with sqlite3.connect(self.db_path) as con:
            con.execute(
                "INSERT INTO sync_queue (entity_type, entity_id, operation, payload, changed_at) VALUES (?,?,?,?,?)",
                ('note', 999, 'INSERT', '{"note_key": "Note2"}',
                 datetime.datetime.now(timezone.utc).isoformat())
            )
        evernothing.sync_s3()  # uploads delta 2, marks new row synced
        with sqlite3.connect(self.db_path) as con:
            synced_after_second = con.execute(
                "SELECT COUNT(*) FROM sync_queue WHERE synced_at IS NOT NULL"
            ).fetchone()[0]
        # All rows should now be synced, and second sync added one more
        self.assertGreater(synced_after_second, synced_after_first)

    # --- 3. restore_from_s3 ---

    @mock_aws
    def test_restore_from_s3_downloads_db_when_missing(self):
        s3 = _make_s3()
        _create_bucket(s3)
        restore_path = self.db_path + '_restore'
        orig_db = evernothing.DB
        evernothing.DB = restore_path
        # S3 key must match evernothing.DB exactly
        s3.put_object(Bucket=BUCKET, Key=restore_path, Body=b'SQLite fake content')
        try:
            evernothing.restore_from_s3()
            self.assertTrue(os.path.exists(restore_path))
            with open(restore_path, 'rb') as f:
                self.assertEqual(f.read(), b'SQLite fake content')
        finally:
            evernothing.DB = orig_db
            if os.path.exists(restore_path):
                os.unlink(restore_path)

    @mock_aws
    def test_restore_from_s3_skips_when_db_exists(self):
        s3 = _make_s3()
        _create_bucket(s3)
        s3.put_object(Bucket=BUCKET, Key=evernothing.DB, Body=b'remote content')
        # DB already exists locally — restore should not overwrite
        with open(self.db_path, 'rb') as f:
            original = f.read()
        evernothing.restore_from_s3()
        with open(self.db_path, 'rb') as f:
            after = f.read()
        self.assertEqual(original, after)

    @mock_aws
    def test_restore_from_s3_handles_missing_bucket_gracefully(self):
        # Bucket does not exist — should not raise
        try:
            evernothing.restore_from_s3()
        except Exception as e:
            self.fail(f"restore_from_s3 raised unexpectedly: {e}")

    # --- 4. sync_s3 failure handling ---

    def test_sync_s3_continues_on_boto3_error(self):
        with patch('evernothing._s3_client', side_effect=Exception("connection refused")):
            try:
                evernothing.sync_s3()
            except Exception as e:
                self.fail(f"sync_s3 raised unexpectedly: {e}")

    # --- 5. queue_change payload completeness ---

    @mock_aws
    def test_queue_change_payload_has_note_value_after_commit(self):
        """Payload must contain note_value — queue_change runs after commit."""
        with patch('evernothing.sync_s3'):
            self._login()
            self.client.post('/folder/add', data={'name': 'QF'}, follow_redirects=True)
            with sqlite3.connect(self.db_path) as con:
                fid = con.execute("SELECT id FROM folders").fetchone()[0]
            self.client.post(f'/add/{fid}', data={'note': 'QNote', 'content': 'QValue', 'description': ''})
        with sqlite3.connect(self.db_path) as con:
            row = con.execute(
                "SELECT payload FROM sync_queue WHERE entity_type='note' AND operation='INSERT'"
            ).fetchone()
        self.assertIsNotNone(row)
        payload = json.loads(row[0])
        self.assertIn('note_value', payload)
        self.assertNotEqual(payload['note_value'], '')
        self.assertNotEqual(payload.get('note_key', ''), '')

    @mock_aws
    def test_queue_change_update_payload_has_note_value(self):
        with patch('evernothing.sync_s3'):
            self._login()
            self.client.post('/folder/add', data={'name': 'QF2'}, follow_redirects=True)
            with sqlite3.connect(self.db_path) as con:
                fid = con.execute("SELECT id FROM folders").fetchone()[0]
            self.client.post(f'/add/{fid}', data={'note': 'QNote2', 'content': 'original', 'description': ''})
            with sqlite3.connect(self.db_path) as con:
                nid = con.execute("SELECT id FROM notes WHERE note_key='QNote2'").fetchone()[0]
            self.client.post(f'/edit/{nid}', data={
                'note': 'QNote2', 'content': 'updated', 'folder_id': fid,
                'description': '', 'confirm': 'yes'
            })
        with sqlite3.connect(self.db_path) as con:
            row = con.execute(
                "SELECT payload FROM sync_queue WHERE entity_type='note' AND operation='UPDATE' AND entity_id=?",
                (nid,)
            ).fetchone()
        self.assertIsNotNone(row)
        payload = json.loads(row[0])
        self.assertIn('note_value', payload)
        self.assertNotEqual(payload['note_value'], '')


if __name__ == '__main__':
    unittest.main()
