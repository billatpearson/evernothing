"""Tests for the Option B multi-device pull worker.

Covers:
- Skipping our own device's prefix.
- Idempotent re-application (applying the same delta twice is a no-op).
- Last-writer-wins: an older incoming update does not overwrite a newer local one.
- UPSERT on CREATE when the id doesn't exist yet.
- DELETE removes the row.
- Unknown entity types are ignored, not fatal.
"""
import json
import os
import sqlite3
import tempfile
import unittest
from unittest import mock


class PullApplyTests(unittest.TestCase):
    def setUp(self):
        os.environ['TESTING'] = 'true'
        self.tmp = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.tmp.close()
        self.db_path = self.tmp.name

        self._db_env_patch = mock.patch.dict(os.environ, {'DB_FILE': self.db_path})
        self._db_env_patch.start()

        # Force the DB module to re-resolve DB path
        import importlib
        import Evernothing_DB.database as db
        importlib.reload(db)
        db.init_db()
        self.db = db

        from Evernothing_Connect import s3_pull
        importlib.reload(s3_pull)
        self.s3_pull = s3_pull

    def tearDown(self):
        self._db_env_patch.stop()
        try:
            os.unlink(self.db_path)
        except OSError:
            pass

    def _row(self, table, rid):
        con = sqlite3.connect(self.db_path)
        con.row_factory = sqlite3.Row
        r = con.execute(f'SELECT * FROM {table} WHERE id=?', (rid,)).fetchone()
        con.close()
        return dict(r) if r else None

    # ---- UPSERT / CREATE --------------------------------------------
    def test_create_note_upserts_when_missing(self):
        changes = [{'op': 'CREATE', 'entity': 'note', 'id': 100,
                    'data': {'id': 100, 'user_id': 1, 'folder_id': 0,
                             'note_key': 'k', 'note_value': 'v',
                             'description': 'd', 'updated_at': '2026-05-10T00:00:00+00:00'}}]
        touched = self.s3_pull._apply_changes(changes)
        self.assertEqual(touched, 1)
        row = self._row('notes', 100)
        self.assertEqual(row['note_key'], 'k')
        self.assertEqual(row['note_value'], 'v')

    # ---- IDEMPOTENCY ------------------------------------------------
    def test_apply_same_delta_twice_is_noop(self):
        changes = [{'op': 'CREATE', 'entity': 'note', 'id': 101,
                    'data': {'id': 101, 'user_id': 1,
                             'note_key': 'k', 'note_value': 'v',
                             'updated_at': '2026-05-10T00:00:00+00:00'}}]
        self.assertEqual(self.s3_pull._apply_changes(changes), 1)
        # Same delta again — LWW skip path kicks in, nothing touched.
        self.assertEqual(self.s3_pull._apply_changes(changes), 0)

    # ---- LAST-WRITER-WINS -------------------------------------------
    def test_older_incoming_does_not_overwrite_newer_local(self):
        # Seed: local row is from 2026-05-10T10:00
        con = sqlite3.connect(self.db_path)
        con.execute(
            'INSERT INTO notes (id, user_id, folder_id, note_key, note_value, '
            'description, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)',
            (200, 1, 0, 'k', 'local-wins', '', '2026-05-10T10:00:00+00:00'))
        con.commit(); con.close()

        # Incoming: older timestamp — should be skipped.
        older = [{'op': 'UPDATE', 'entity': 'note', 'id': 200,
                  'data': {'id': 200, 'user_id': 1, 'note_key': 'k',
                           'note_value': 'should-be-ignored',
                           'updated_at': '2026-05-10T09:00:00+00:00'}}]
        self.assertEqual(self.s3_pull._apply_changes(older), 0)
        self.assertEqual(self._row('notes', 200)['note_value'], 'local-wins')

    def test_newer_incoming_overwrites_older_local(self):
        con = sqlite3.connect(self.db_path)
        con.execute(
            'INSERT INTO notes (id, user_id, note_key, note_value, updated_at) '
            'VALUES (?, ?, ?, ?, ?)',
            (201, 1, 'k', 'old', '2026-05-10T09:00:00+00:00'))
        con.commit(); con.close()
        newer = [{'op': 'UPDATE', 'entity': 'note', 'id': 201,
                  'data': {'id': 201, 'user_id': 1, 'note_key': 'k',
                           'note_value': 'new',
                           'updated_at': '2026-05-10T10:00:00+00:00'}}]
        self.assertEqual(self.s3_pull._apply_changes(newer), 1)
        self.assertEqual(self._row('notes', 201)['note_value'], 'new')

    # ---- DELETE -----------------------------------------------------
    def test_delete_removes_row(self):
        con = sqlite3.connect(self.db_path)
        con.execute(
            'INSERT INTO notes (id, user_id, note_key, note_value, updated_at) '
            'VALUES (?, ?, ?, ?, ?)',
            (300, 1, 'k', 'v', '2026-05-10T00:00:00+00:00'))
        con.commit(); con.close()
        deletes = [{'op': 'DELETE', 'entity': 'note', 'id': 300, 'data': {}}]
        self.assertEqual(self.s3_pull._apply_changes(deletes), 1)
        self.assertIsNone(self._row('notes', 300))

    def test_delete_on_missing_row_is_noop(self):
        deletes = [{'op': 'DELETE', 'entity': 'note', 'id': 9999, 'data': {}}]
        self.assertEqual(self.s3_pull._apply_changes(deletes), 0)

    # ---- FOLDERS ----------------------------------------------------
    def test_folder_upsert(self):
        changes = [{'op': 'CREATE', 'entity': 'folder', 'id': 400,
                    'data': {'id': 400, 'user_id': 1, 'name': 'F', 'parent_id': 0}}]
        self.assertEqual(self.s3_pull._apply_changes(changes), 1)
        self.assertEqual(self._row('folders', 400)['name'], 'F')

    # ---- UNKNOWN ENTITIES -------------------------------------------
    def test_unknown_entity_is_ignored(self):
        changes = [{'op': 'CREATE', 'entity': 'widget', 'id': 1, 'data': {}}]
        # Should not raise.
        self.assertEqual(self.s3_pull._apply_changes(changes), 0)


class PullCycleTests(unittest.TestCase):
    """End-to-end cycle with a mocked S3 client."""

    def setUp(self):
        os.environ['TESTING'] = 'true'
        self.tmp = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.tmp.close()
        self.db_path = self.tmp.name
        self._db_env_patch = mock.patch.dict(os.environ, {
            'DB_FILE': self.db_path,
            'S3_BUCKET_NAME': 'test-bucket',
            'DEVICE_ID': 'device-a',
        })
        self._db_env_patch.start()
        import importlib
        import Evernothing_DB.database as db
        importlib.reload(db); db.init_db()
        from Evernothing_Connect import s3_sync, s3_pull
        importlib.reload(s3_sync); importlib.reload(s3_pull)
        self.s3_pull = s3_pull

    def tearDown(self):
        self._db_env_patch.stop()
        try: os.unlink(self.db_path)
        except OSError: pass

    def test_cycle_skips_our_own_device_prefix(self):
        mock_s3 = mock.MagicMock()
        # Our device-a has 1 object, peer device-b has 1 object.
        paginator = mock.MagicMock()
        paginator.paginate.return_value = [{'Contents': [
            {'Key': 'changes/device-a/own.json'},
            {'Key': 'changes/device-b/peer.json'},
        ]}]
        mock_s3.get_paginator.return_value = paginator

        def fake_download(bucket, key, buf):
            payload = [{'op': 'CREATE', 'entity': 'note', 'id': 500,
                        'data': {'id': 500, 'user_id': 1, 'note_key': 'k',
                                 'note_value': 'peer-sent',
                                 'updated_at': '2026-05-10T00:00:00+00:00'}}]
            buf.write(json.dumps(payload).encode())
        mock_s3.download_fileobj.side_effect = fake_download

        with mock.patch('Evernothing_Connect.s3_pull._s3_client', return_value=mock_s3), \
             mock.patch('Evernothing_Connect.s3_pull._is_configured', return_value=True):
            self.s3_pull._pull_cycle()

        # Only the peer file was fetched
        self.assertEqual(mock_s3.download_fileobj.call_count, 1)
        (_, called_key, _) = mock_s3.download_fileobj.call_args[0]
        self.assertEqual(called_key, 'changes/device-b/peer.json')

        # And its row landed
        con = sqlite3.connect(self.db_path)
        row = con.execute('SELECT note_value FROM notes WHERE id=500').fetchone()
        con.close()
        self.assertEqual(row[0], 'peer-sent')

    def test_cycle_skips_keys_already_applied(self):
        mock_s3 = mock.MagicMock()
        paginator = mock.MagicMock()
        paginator.paginate.return_value = [{'Contents': [
            {'Key': 'changes/device-b/seen.json'},
        ]}]
        mock_s3.get_paginator.return_value = paginator

        def fake_download(bucket, key, buf):
            buf.write(b'[]')
        mock_s3.download_fileobj.side_effect = fake_download

        with mock.patch('Evernothing_Connect.s3_pull._s3_client', return_value=mock_s3), \
             mock.patch('Evernothing_Connect.s3_pull._is_configured', return_value=True):
            self.s3_pull._pull_cycle()
            self.s3_pull._pull_cycle()

        # Second cycle shouldn't re-download.
        self.assertEqual(mock_s3.download_fileobj.call_count, 1)


if __name__ == '__main__':
    unittest.main()
