"""Tests for the Phase 3 Option A multi-device pull worker.

Covers:
- Skipping our own device's prefix.
- Idempotent re-application (applying the same delta twice is a no-op).
- Version-based last-writer-wins (higher version wins).
- Tie break on equal version: lexicographically higher device id wins.
- UPSERT on CREATE when the id doesn't exist yet.
- DELETE removes the row.
- Unknown entity types are ignored, not fatal.
- Persistent cursor: re-pull skips keys recorded in replication_cursor.
- queue_change bumps version + stamps DEVICE_ID for local writes.
"""
import json
import os
import sqlite3
import tempfile
import unittest
from unittest import mock


class _Base(unittest.TestCase):
    def setUp(self):
        os.environ['TESTING'] = 'true'
        self.tmp = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.tmp.close()
        self.db_path = self.tmp.name

        self._db_env_patch = mock.patch.dict(os.environ, {'DB_FILE': self.db_path})
        self._db_env_patch.start()

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
        try: os.unlink(self.db_path)
        except OSError: pass

    def _row(self, table, rid):
        con = sqlite3.connect(self.db_path)
        con.row_factory = sqlite3.Row
        r = con.execute(f'SELECT * FROM {table} WHERE id=?', (rid,)).fetchone()
        con.close()
        return dict(r) if r else None


class PullApplyTests(_Base):
    # ---- UPSERT / CREATE --------------------------------------------
    def test_create_note_upserts_when_missing(self):
        changes = [{'op': 'CREATE', 'entity': 'note', 'id': 100,
                    'data': {'id': 100, 'user_id': 1, 'folder_id': 0,
                             'note_key': 'k', 'note_value': 'v',
                             'description': 'd',
                             'updated_at': '2026-05-10T00:00:00+00:00',
                             'version': 1,
                             'last_modified_device': 'peer-A'}}]
        touched = self.s3_pull._apply_changes(changes, sender_device='peer-A')
        self.assertEqual(touched, 1)
        row = self._row('notes', 100)
        self.assertEqual(row['note_key'], 'k')
        self.assertEqual(row['note_value'], 'v')
        self.assertEqual(row['version'], 1)
        self.assertEqual(row['last_modified_device'], 'peer-A')

    # ---- IDEMPOTENCY ------------------------------------------------
    def test_apply_same_delta_twice_is_noop(self):
        changes = [{'op': 'CREATE', 'entity': 'note', 'id': 101,
                    'data': {'id': 101, 'user_id': 1,
                             'note_key': 'k', 'note_value': 'v',
                             'updated_at': '2026-05-10T00:00:00+00:00',
                             'version': 1,
                             'last_modified_device': 'peer-A'}}]
        self.assertEqual(self.s3_pull._apply_changes(changes, 'peer-A'), 1)
        self.assertEqual(self.s3_pull._apply_changes(changes, 'peer-A'), 0)

    # ---- VERSION-BASED LWW ------------------------------------------
    def test_higher_version_overwrites_lower(self):
        con = sqlite3.connect(self.db_path)
        con.execute(
            'INSERT INTO notes (id, user_id, note_key, note_value, '
            'updated_at, version, last_modified_device) '
            'VALUES (?, ?, ?, ?, ?, ?, ?)',
            (200, 1, 'k', 'old', '2026-05-10T09:00:00+00:00', 1, 'self'))
        con.commit(); con.close()
        newer = [{'op': 'UPDATE', 'entity': 'note', 'id': 200,
                  'data': {'id': 200, 'user_id': 1, 'note_key': 'k',
                           'note_value': 'new',
                           'updated_at': '2026-05-10T10:00:00+00:00',
                           'version': 2,
                           'last_modified_device': 'peer-A'}}]
        self.assertEqual(self.s3_pull._apply_changes(newer, 'peer-A'), 1)
        row = self._row('notes', 200)
        self.assertEqual(row['note_value'], 'new')
        self.assertEqual(row['version'], 2)
        self.assertEqual(row['last_modified_device'], 'peer-A')

    def test_lower_version_does_not_overwrite_higher(self):
        con = sqlite3.connect(self.db_path)
        con.execute(
            'INSERT INTO notes (id, user_id, note_key, note_value, '
            'updated_at, version, last_modified_device) '
            'VALUES (?, ?, ?, ?, ?, ?, ?)',
            (201, 1, 'k', 'high', '2026-05-10T10:00:00+00:00', 5, 'self'))
        con.commit(); con.close()
        older = [{'op': 'UPDATE', 'entity': 'note', 'id': 201,
                  'data': {'id': 201, 'user_id': 1, 'note_key': 'k',
                           'note_value': 'low',
                           'updated_at': '2026-05-10T11:00:00+00:00',
                           'version': 3,
                           'last_modified_device': 'peer-A'}}]
        self.assertEqual(self.s3_pull._apply_changes(older, 'peer-A'), 0)
        self.assertEqual(self._row('notes', 201)['note_value'], 'high')

    def test_equal_version_higher_device_id_wins(self):
        # Local stamped 'aaa', incoming stamped 'zzz' at the same version.
        # Lexicographically 'zzz' > 'aaa' so incoming should win.
        con = sqlite3.connect(self.db_path)
        con.execute(
            'INSERT INTO notes (id, user_id, note_key, note_value, '
            'updated_at, version, last_modified_device) '
            'VALUES (?, ?, ?, ?, ?, ?, ?)',
            (202, 1, 'k', 'aaa-wrote', '2026-05-10T10:00:00+00:00', 3, 'aaa'))
        con.commit(); con.close()
        tie = [{'op': 'UPDATE', 'entity': 'note', 'id': 202,
                'data': {'id': 202, 'user_id': 1, 'note_key': 'k',
                         'note_value': 'zzz-wrote',
                         'updated_at': '2026-05-10T10:00:00+00:00',
                         'version': 3,
                         'last_modified_device': 'zzz'}}]
        self.assertEqual(self.s3_pull._apply_changes(tie, 'zzz'), 1)
        self.assertEqual(self._row('notes', 202)['note_value'], 'zzz-wrote')
        self.assertEqual(self._row('notes', 202)['last_modified_device'], 'zzz')

    def test_equal_version_lower_device_id_loses(self):
        con = sqlite3.connect(self.db_path)
        con.execute(
            'INSERT INTO notes (id, user_id, note_key, note_value, '
            'updated_at, version, last_modified_device) '
            'VALUES (?, ?, ?, ?, ?, ?, ?)',
            (203, 1, 'k', 'zzz-wrote', '2026-05-10T10:00:00+00:00', 3, 'zzz'))
        con.commit(); con.close()
        tie = [{'op': 'UPDATE', 'entity': 'note', 'id': 203,
                'data': {'id': 203, 'user_id': 1, 'note_key': 'k',
                         'note_value': 'aaa-wrote',
                         'updated_at': '2026-05-10T10:00:00+00:00',
                         'version': 3,
                         'last_modified_device': 'aaa'}}]
        self.assertEqual(self.s3_pull._apply_changes(tie, 'aaa'), 0)
        self.assertEqual(self._row('notes', 203)['note_value'], 'zzz-wrote')

    # ---- DELETE -----------------------------------------------------
    def test_delete_removes_row(self):
        con = sqlite3.connect(self.db_path)
        con.execute(
            'INSERT INTO notes (id, user_id, note_key, note_value, updated_at) '
            'VALUES (?, ?, ?, ?, ?)',
            (300, 1, 'k', 'v', '2026-05-10T00:00:00+00:00'))
        con.commit(); con.close()
        deletes = [{'op': 'DELETE', 'entity': 'note', 'id': 300, 'data': {}}]
        self.assertEqual(self.s3_pull._apply_changes(deletes, 'peer-A'), 1)
        self.assertIsNone(self._row('notes', 300))

    def test_delete_on_missing_row_is_noop(self):
        deletes = [{'op': 'DELETE', 'entity': 'note', 'id': 9999, 'data': {}}]
        self.assertEqual(self.s3_pull._apply_changes(deletes, 'peer-A'), 0)

    # ---- FOLDERS ----------------------------------------------------
    def test_folder_upsert_with_version(self):
        changes = [{'op': 'CREATE', 'entity': 'folder', 'id': 400,
                    'data': {'id': 400, 'user_id': 1, 'name': 'F',
                             'parent_id': 0, 'version': 1,
                             'last_modified_device': 'peer-A'}}]
        self.assertEqual(self.s3_pull._apply_changes(changes, 'peer-A'), 1)
        row = self._row('folders', 400)
        self.assertEqual(row['name'], 'F')
        self.assertEqual(row['version'], 1)
        self.assertEqual(row['last_modified_device'], 'peer-A')

    # ---- UNKNOWN ENTITIES -------------------------------------------
    def test_unknown_entity_is_ignored(self):
        changes = [{'op': 'CREATE', 'entity': 'widget', 'id': 1, 'data': {}}]
        self.assertEqual(self.s3_pull._apply_changes(changes, 'peer-A'), 0)


class PersistentCursorTests(_Base):
    """The cursor in replication_cursor table survives a fresh _pull_cycle
    so already-applied keys are not re-fetched even after process restart."""

    def _make_cycle(self, list_returns):
        from Evernothing_Connect import s3_pull
        mock_s3 = mock.MagicMock()
        paginator = mock.MagicMock()
        paginator.paginate.return_value = list_returns
        mock_s3.get_paginator.return_value = paginator

        def fake_download(bucket, key, buf):
            payload = [{'op': 'CREATE', 'entity': 'note', 'id': 500,
                        'data': {'id': 500, 'user_id': 1,
                                 'note_key': 'k', 'note_value': key,
                                 'updated_at': '2026-05-10T00:00:00+00:00',
                                 'version': 1,
                                 'last_modified_device': 'peer-B'}}]
            buf.write(json.dumps(payload).encode())
        mock_s3.download_fileobj.side_effect = fake_download
        return mock_s3

    def test_cursor_persists_across_cycles(self):
        os.environ['DEVICE_ID'] = 'peer-A'  # also patched via reload below
        from Evernothing_Connect import s3_sync, s3_pull
        # DEVICE_ID is module-level; reload to pick up new env
        import importlib
        importlib.reload(s3_sync)
        importlib.reload(s3_pull)

        list_returns_first = [{'Contents': [
            {'Key': 'changes/peer-B/001.json'},
            {'Key': 'changes/peer-B/002.json'},
        ]}]
        list_returns_second = [{'Contents': [
            {'Key': 'changes/peer-B/001.json'},
            {'Key': 'changes/peer-B/002.json'},
            {'Key': 'changes/peer-B/003.json'},
        ]}]

        mock_s3 = self._make_cycle(list_returns_first)
        with mock.patch('Evernothing_Connect.s3_pull._s3_client', return_value=mock_s3), \
             mock.patch('Evernothing_Connect.s3_pull._is_configured', return_value=True):
            s3_pull._pull_cycle()
        # First cycle downloaded both new keys.
        self.assertEqual(mock_s3.download_fileobj.call_count, 2)

        # Second cycle: cursor should skip 001 and 002, fetch only 003.
        mock_s3 = self._make_cycle(list_returns_second)
        with mock.patch('Evernothing_Connect.s3_pull._s3_client', return_value=mock_s3), \
             mock.patch('Evernothing_Connect.s3_pull._is_configured', return_value=True):
            s3_pull._pull_cycle()
        self.assertEqual(mock_s3.download_fileobj.call_count, 1)
        called_key = mock_s3.download_fileobj.call_args[0][1]
        self.assertEqual(called_key, 'changes/peer-B/003.json')

    def test_cursor_skips_own_device(self):
        os.environ['DEVICE_ID'] = 'peer-A'
        import importlib
        from Evernothing_Connect import s3_sync, s3_pull
        importlib.reload(s3_sync)
        importlib.reload(s3_pull)

        list_returns = [{'Contents': [
            {'Key': 'changes/peer-A/own1.json'},
            {'Key': 'changes/peer-A/own2.json'},
        ]}]
        mock_s3 = self._make_cycle(list_returns)
        with mock.patch('Evernothing_Connect.s3_pull._s3_client', return_value=mock_s3), \
             mock.patch('Evernothing_Connect.s3_pull._is_configured', return_value=True):
            s3_pull._pull_cycle()
        self.assertEqual(mock_s3.download_fileobj.call_count, 0)


class QueueChangeVersioningTests(_Base):
    """queue_change should bump the row's version and stamp DEVICE_ID
    so subsequent uploads carry up-to-date metadata."""

    def test_queue_change_bumps_version_and_stamps_device(self):
        os.environ['DEVICE_ID'] = 'peer-X'
        import importlib
        import Evernothing_Connect.s3_sync as s3_sync
        importlib.reload(s3_sync)

        con = sqlite3.connect(self.db_path)
        con.row_factory = sqlite3.Row
        con.execute(
            'INSERT INTO notes (id, user_id, note_key, note_value, '
            'updated_at, version, last_modified_device) '
            'VALUES (?, ?, ?, ?, ?, ?, ?)',
            (700, 1, 'k', 'v', '2026-05-10T00:00:00+00:00', 4, 'peer-Y'))
        con.commit()
        cur = con.cursor()
        s3_sync.queue_change(cur, 'note', 700, 'UPDATE')
        con.commit()

        # Row should now be version=5, stamped peer-X.
        row = self._row('notes', 700)
        self.assertEqual(row['version'], 5)
        self.assertEqual(row['last_modified_device'], 'peer-X')
        # The published payload (in sync_queue.payload) should reflect that.
        q = con.execute(
            'SELECT payload FROM sync_queue WHERE entity_id=700 ORDER BY id DESC LIMIT 1'
        ).fetchone()
        payload = json.loads(q['payload'])
        self.assertEqual(payload['version'], 5)
        self.assertEqual(payload['last_modified_device'], 'peer-X')
        con.close()

    def test_queue_change_delete_does_not_bump(self):
        os.environ['DEVICE_ID'] = 'peer-X'
        import importlib
        import Evernothing_Connect.s3_sync as s3_sync
        importlib.reload(s3_sync)

        con = sqlite3.connect(self.db_path)
        con.row_factory = sqlite3.Row
        con.execute(
            'INSERT INTO notes (id, user_id, note_key, note_value, '
            'updated_at, version, last_modified_device) '
            'VALUES (?, ?, ?, ?, ?, ?, ?)',
            (701, 1, 'k', 'v', '2026-05-10T00:00:00+00:00', 4, 'peer-Y'))
        con.commit()
        cur = con.cursor()
        s3_sync.queue_change(cur, 'note', 701, 'DELETE')
        con.commit()

        # DELETE should leave the existing row's version alone (we'll delete it after).
        row = self._row('notes', 701)
        self.assertEqual(row['version'], 4)
        self.assertEqual(row['last_modified_device'], 'peer-Y')
        con.close()


class TwoDeviceConvergenceTests(_Base):
    """Simulate two devices trading deltas; both converge to the same state."""

    def test_round_trip_convergence(self):
        os.environ['DEVICE_ID'] = 'A'
        import importlib
        import Evernothing_Connect.s3_sync as s3_sync
        importlib.reload(s3_sync)
        from Evernothing_Connect import s3_pull
        importlib.reload(s3_pull)

        # Device A creates a note locally — version=1, device=A.
        con = sqlite3.connect(self.db_path)
        con.row_factory = sqlite3.Row
        con.execute(
            'INSERT INTO notes (id, user_id, note_key, note_value, '
            'updated_at, version, last_modified_device) '
            'VALUES (?, ?, ?, ?, ?, ?, ?)',
            (800, 1, 'k', 'A wrote', '2026-05-10T10:00:00+00:00', 1, 'A'))
        con.commit(); con.close()

        # Device B sends a newer version (simulating what arrives via S3).
        b_change = [{'op': 'UPDATE', 'entity': 'note', 'id': 800,
                     'data': {'id': 800, 'user_id': 1, 'note_key': 'k',
                              'note_value': 'B wrote',
                              'updated_at': '2026-05-10T10:01:00+00:00',
                              'version': 2,
                              'last_modified_device': 'B'}}]
        s3_pull._apply_changes(b_change, sender_device='B')

        # A should now reflect B's write
        row = self._row('notes', 800)
        self.assertEqual(row['note_value'], 'B wrote')
        self.assertEqual(row['version'], 2)
        self.assertEqual(row['last_modified_device'], 'B')

        # Now A makes a local edit through queue_change
        con = sqlite3.connect(self.db_path)
        con.row_factory = sqlite3.Row
        con.execute(
            'UPDATE notes SET note_value=?, updated_at=? WHERE id=?',
            ('A overwrote', '2026-05-10T10:02:00+00:00', 800))
        cur = con.cursor()
        s3_sync.queue_change(cur, 'note', 800, 'UPDATE')
        con.commit(); con.close()

        # version should be 3, device A
        row = self._row('notes', 800)
        self.assertEqual(row['version'], 3)
        self.assertEqual(row['last_modified_device'], 'A')


if __name__ == '__main__':
    unittest.main()
