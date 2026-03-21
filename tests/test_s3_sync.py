import unittest
import sys
import os
import tempfile
import sqlite3
import json
import datetime
from unittest.mock import patch, MagicMock, call

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import evernothing
from evernothing import queue_change, sync_s3, db as get_db


SCHEMA = """
CREATE TABLE IF NOT EXISTS sync_queue(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_type TEXT,
    entity_id INTEGER,
    operation TEXT,
    payload TEXT,
    changed_at TEXT,
    synced_at TEXT
);
"""


class S3SyncTestCase(unittest.TestCase):

    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp()
        evernothing.DB = self.db_path
        with sqlite3.connect(self.db_path) as con:
            con.executescript(SCHEMA)

    def tearDown(self):
        try:
            os.close(self.db_fd)
            os.unlink(self.db_path)
        except OSError:
            pass

    def _insert_queue_row(self, entity_type, entity_id, operation, payload, synced_at=None):
        with sqlite3.connect(self.db_path) as con:
            con.execute(
                "INSERT INTO sync_queue (entity_type, entity_id, operation, payload, changed_at, synced_at) VALUES(?,?,?,?,?,?)",
                (entity_type, entity_id, operation, json.dumps(payload),
                 datetime.datetime.utcnow().isoformat(), synced_at)
            )

    def _unsynced_rows(self):
        with sqlite3.connect(self.db_path) as con:
            return con.execute(
                "SELECT id, operation, entity_type, synced_at FROM sync_queue WHERE synced_at IS NULL"
            ).fetchall()

    def _synced_rows(self):
        with sqlite3.connect(self.db_path) as con:
            return con.execute(
                "SELECT id FROM sync_queue WHERE synced_at IS NOT NULL"
            ).fetchall()

    # --- 1. queue_change writes correct rows ---

    def test_queue_change_insert(self):
        with sqlite3.connect(self.db_path) as con:
            cur = con.cursor()
            queue_change(cur, 'note', 42, 'INSERT', {'key': 'MyNote', 'folder_id': 1})
            con.commit()
        rows = self._unsynced_rows()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][1], 'INSERT')
        self.assertEqual(rows[0][2], 'note')
        self.assertIsNone(rows[0][3])

    def test_queue_change_update(self):
        with sqlite3.connect(self.db_path) as con:
            cur = con.cursor()
            queue_change(cur, 'note', 42, 'UPDATE', {'key': 'UpdatedNote', 'folder_id': 1})
            con.commit()
        rows = self._unsynced_rows()
        self.assertEqual(rows[0][1], 'UPDATE')

    def test_queue_change_delete(self):
        with sqlite3.connect(self.db_path) as con:
            cur = con.cursor()
            queue_change(cur, 'note', 42, 'DELETE', {'user_id': 1})
            con.commit()
        rows = self._unsynced_rows()
        self.assertEqual(rows[0][1], 'DELETE')

    def test_queue_change_payload_serialized(self):
        payload = {'key': 'TestNote', 'folder_id': 5, 'description': 'desc'}
        with sqlite3.connect(self.db_path) as con:
            cur = con.cursor()
            queue_change(cur, 'note', 99, 'INSERT', payload)
            con.commit()
        with sqlite3.connect(self.db_path) as con:
            row = con.execute("SELECT payload FROM sync_queue").fetchone()
        self.assertEqual(json.loads(row[0]), payload)

    # --- 2. sync_s3 uploads only unsynced rows ---

    @patch('evernothing._s3_client')
    @patch('evernothing.boto3', new_callable=lambda: type('boto3', (), {'__bool__': lambda s: True}))
    def test_sync_s3_uploads_unsynced(self, mock_boto3, mock_s3_client):
        mock_s3 = MagicMock()
        mock_s3_client.return_value = mock_s3

        self._insert_queue_row('note', 1, 'INSERT', {'key': 'NoteA'})
        self._insert_queue_row('note', 2, 'UPDATE', {'key': 'NoteB'})

        with patch('evernothing.boto3', True):
            sync_s3()

        mock_s3.upload_fileobj.assert_called_once()
        args, kwargs = mock_s3.upload_fileobj.call_args
        uploaded = json.loads(args[0].read().decode())
        self.assertEqual(len(uploaded), 2)
        ops = {r['op'] for r in uploaded}
        self.assertIn('INSERT', ops)
        self.assertIn('UPDATE', ops)

    @patch('evernothing._s3_client')
    def test_sync_s3_marks_rows_synced(self, mock_s3_client):
        mock_s3_client.return_value = MagicMock()

        self._insert_queue_row('note', 1, 'INSERT', {'key': 'NoteA'})
        self._insert_queue_row('folder', 3, 'DELETE', {'user_id': 1})

        with patch('evernothing.boto3', True):
            sync_s3()

        self.assertEqual(len(self._unsynced_rows()), 0)
        self.assertEqual(len(self._synced_rows()), 2)

    @patch('evernothing._s3_client')
    def test_sync_s3_skips_already_synced(self, mock_s3_client):
        mock_s3 = MagicMock()
        mock_s3_client.return_value = mock_s3

        # One already synced, one not
        self._insert_queue_row('note', 1, 'INSERT', {'key': 'Old'}, synced_at='2026-01-01T00:00:00')
        self._insert_queue_row('note', 2, 'UPDATE', {'key': 'New'})

        with patch('evernothing.boto3', True):
            sync_s3()

        args, _ = mock_s3.upload_fileobj.call_args
        uploaded = json.loads(args[0].read().decode())
        self.assertEqual(len(uploaded), 1)
        self.assertEqual(uploaded[0]['op'], 'UPDATE')

    @patch('evernothing._s3_client')
    def test_sync_s3_no_upload_when_queue_empty(self, mock_s3_client):
        mock_s3 = MagicMock()
        mock_s3_client.return_value = mock_s3

        with patch('evernothing.boto3', True):
            sync_s3()

        mock_s3.upload_fileobj.assert_not_called()

    # --- 3. S3 key format ---

    @patch('evernothing._s3_client')
    def test_sync_s3_key_format(self, mock_s3_client):
        mock_s3 = MagicMock()
        mock_s3_client.return_value = mock_s3

        self._insert_queue_row('note', 1, 'INSERT', {'key': 'K'})

        with patch('evernothing.boto3', True):
            sync_s3()

        _, kwargs = mock_s3.upload_fileobj.call_args
        s3_key = mock_s3.upload_fileobj.call_args[0][2]
        self.assertTrue(s3_key.startswith('changes/'))
        self.assertTrue(s3_key.endswith('.json'))

    # --- 4. S3 payload structure ---

    @patch('evernothing._s3_client')
    def test_sync_s3_payload_structure(self, mock_s3_client):
        mock_s3 = MagicMock()
        mock_s3_client.return_value = mock_s3

        self._insert_queue_row('note', 7, 'DELETE', {'user_id': 2})

        with patch('evernothing.boto3', True):
            sync_s3()

        args, _ = mock_s3.upload_fileobj.call_args
        uploaded = json.loads(args[0].read().decode())
        record = uploaded[0]
        self.assertIn('op', record)
        self.assertIn('entity', record)
        self.assertIn('id', record)
        self.assertIn('data', record)
        self.assertIn('at', record)
        self.assertEqual(record['op'], 'DELETE')
        self.assertEqual(record['entity'], 'note')
        self.assertEqual(record['id'], 7)

    # --- 5. SSE-KMS header applied ---

    @patch('evernothing._s3_client')
    def test_sync_s3_sse_kms_header(self, mock_s3_client):
        mock_s3 = MagicMock()
        mock_s3_client.return_value = mock_s3

        self._insert_queue_row('note', 1, 'INSERT', {'key': 'K'})

        with patch('evernothing.boto3', True):
            with patch('evernothing.KMS_KEY_ID', 'arn:aws:kms:us-east-1:123:key/abc'):
                sync_s3()

        _, kwargs = mock_s3.upload_fileobj.call_args
        extra = kwargs.get('ExtraArgs', {})
        self.assertEqual(extra.get('ServerSideEncryption'), 'aws:kms')
        self.assertEqual(extra.get('SSEKMSKeyId'), 'arn:aws:kms:us-east-1:123:key/abc')

    # --- 6. boto3 unavailable ---

    def test_sync_s3_no_boto3(self):
        self._insert_queue_row('note', 1, 'INSERT', {'key': 'K'})
        with patch('evernothing.boto3', None):
            sync_s3()  # should not raise
        # rows remain unsynced
        self.assertEqual(len(self._unsynced_rows()), 1)


if __name__ == '__main__':
    unittest.main()
