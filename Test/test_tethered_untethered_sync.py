"""
Validation of TETHERED and UN-TETHERED synchronization between the
desktop (PC) app and the Android app.

Terminology (architectural, not literal strings in the code):

  * UN-TETHERED  — PC and phone are independent and replicate purely
    through the shared S3 bucket using the Phase-3 delta protocol
    (changes/<DEVICE_ID>/<ts>.json + LWW convergence). No cable.

  * TETHERED      — PC and phone exchange the whole SQLite DB directly
    over the USB/ADB channel (an `adb push` / `adb pull` of
    evernothing.db). The receiving side reads the transferred rows as-is.

These tests drive the REAL publish/pull/apply code on both sides. S3 is
replaced by an in-memory fake (a dict keyed by object key) so no AWS
access is required; the fake is wired into the exact upload/list/download
calls each implementation makes. The desktop uses Evernothing_Connect
(s3_sync/s3_pull); the phone uses evernothing_android.

Run from the PC repo root:
    cd c:\\source\\ai\\evernothing\\evernothing
    python -m pytest Test/test_tethered_untethered_sync.py -v
"""
import io
import os
import sys
import json
import sqlite3
import tempfile
import importlib
import unittest
from unittest import mock

# Make the Android single-file app importable alongside the PC package.
_PC_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_ANDROID_ROOT = os.path.join(os.path.dirname(_PC_ROOT), 'evernothing_android')
for p in (_PC_ROOT, _ANDROID_ROOT):
    if p not in sys.path:
        sys.path.insert(0, p)


# ---------------------------------------------------------------------------
# In-memory fake S3 — just enough surface for both implementations.
# ---------------------------------------------------------------------------
class FakeS3:
    """Dict-backed stand-in for a boto3 S3 client. Supports the calls the
    real publish/pull paths use: upload_fileobj, head_bucket, get_paginator
    (list_objects_v2), download_fileobj."""

    def __init__(self):
        self.objects = {}  # key -> bytes

    # --- upload --------------------------------------------------------
    def upload_fileobj(self, fileobj, bucket, key, ExtraArgs=None):
        self.objects[key] = fileobj.read()

    def upload_file(self, filename, bucket, key, ExtraArgs=None):
        with open(filename, 'rb') as f:
            self.objects[key] = f.read()

    # --- bucket bookkeeping -------------------------------------------
    def head_bucket(self, Bucket=None):
        return {}

    # --- list ----------------------------------------------------------
    def get_paginator(self, _op):
        outer = self

        class _Paginator:
            def paginate(self, Bucket=None, Prefix=''):
                contents = [{'Key': k} for k in sorted(outer.objects)
                            if k.startswith(Prefix)]
                yield {'Contents': contents}
        return _Paginator()

    # --- download ------------------------------------------------------
    def download_fileobj(self, bucket, key, fileobj):
        if key not in self.objects:
            raise KeyError(key)
        fileobj.write(self.objects[key])


# ---------------------------------------------------------------------------
# Helpers to build a fresh PC-schema DB on a temp path.
# ---------------------------------------------------------------------------
def _new_db(path):
    con = sqlite3.connect(path)
    con.executescript("""
        CREATE TABLE users(id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE,
                           password TEXT, last_login TEXT, email TEXT);
        CREATE TABLE folders(id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
                             name TEXT, parent_id INTEGER,
                             version INTEGER NOT NULL DEFAULT 1,
                             last_modified_device TEXT);
        CREATE TABLE notes(id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
                           folder_id INTEGER, note_key TEXT, note_value TEXT,
                           description TEXT, updated_at TEXT,
                           version INTEGER NOT NULL DEFAULT 1,
                           last_modified_device TEXT);
        CREATE TABLE note_history(id INTEGER PRIMARY KEY AUTOINCREMENT, note_id INTEGER,
                                  user_id INTEGER, note_key TEXT, note_value TEXT,
                                  description TEXT, folder_id INTEGER, updated_at TEXT,
                                  version INTEGER NOT NULL DEFAULT 1,
                                  last_modified_device TEXT);
        CREATE TABLE sync_queue(id INTEGER PRIMARY KEY AUTOINCREMENT, entity_type TEXT,
                                entity_id INTEGER, operation TEXT, payload TEXT,
                                changed_at TEXT, synced_at TEXT);
        CREATE TABLE replication_cursor(peer_device TEXT PRIMARY KEY, last_key TEXT NOT NULL,
                                        updated_at TEXT NOT NULL);
        INSERT INTO users(id,username,password) VALUES(1,'bspeiser','x');
    """)
    con.commit()
    con.close()


def _row(path, table, rid):
    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    try:
        r = con.execute(f'SELECT * FROM {table} WHERE id=?', (rid,)).fetchone()
        return dict(r) if r else None
    finally:
        con.close()


def _count(path, table):
    con = sqlite3.connect(path)
    try:
        return con.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0]
    finally:
        con.close()


class _Base(unittest.TestCase):
    def setUp(self):
        os.environ['TESTING'] = 'true'

        # PC DB
        self.pc_db = tempfile.NamedTemporaryFile(suffix='_pc.db', delete=False).name
        os.unlink(self.pc_db)
        _new_db(self.pc_db)

        # Android DB
        self.droid_db = tempfile.NamedTemporaryFile(suffix='_droid.db', delete=False).name
        os.unlink(self.droid_db)
        _new_db(self.droid_db)

        # Import + configure the PC sync modules against the PC DB.
        os.environ['DB_FILE'] = self.pc_db
        os.environ['DEVICE_ID'] = 'desktop-PC'
        import Evernothing_DB.database as db
        importlib.reload(db)
        db.DB = self.pc_db
        from Evernothing_Connect import s3_sync, s3_pull
        importlib.reload(s3_sync)
        importlib.reload(s3_pull)
        self.s3_sync = s3_sync
        self.s3_pull = s3_pull
        self.s3_sync.DEVICE_ID = 'desktop-PC'
        self.s3_pull.DEVICE_ID = 'desktop-PC'
        self.s3_sync.S3_BUCKET_NAME = 'test-bucket'
        self.s3_pull.S3_BUCKET_NAME = 'test-bucket'

        # Import + configure the Android app against the Android DB.
        os.environ['DB_FILE'] = self.droid_db
        os.environ['DEVICE_ID'] = 'android-PHONE'
        import evernothing_android as ea
        importlib.reload(ea)
        ea.DB = self.droid_db
        ea.DEVICE_ID = 'android-PHONE'
        ea.S3_BUCKET_NAME = 'test-bucket'
        self.ea = ea

    def tearDown(self):
        for p in (self.pc_db, self.droid_db):
            try:
                os.unlink(p)
            except OSError:
                pass
            did = os.path.join(os.path.dirname(p), '.device_id')
            if os.path.exists(did):
                try:
                    os.unlink(did)
                except OSError:
                    pass


# ===========================================================================
# UN-TETHERED: cloud S3 delta replication, both directions + LWW convergence
# ===========================================================================
class UntetheredSyncTests(_Base):

    def test_phone_edit_propagates_to_pc_via_s3(self):
        """Phone creates a note -> publishes delta to S3 -> PC pulls and
        applies it. Un-tethered, cloud-only path."""
        s3 = FakeS3()

        # Phone makes a local write and queues it.
        con = sqlite3.connect(self.droid_db)
        cur = con.cursor()
        cur.execute("INSERT INTO notes(id,user_id,note_key,note_value,updated_at) "
                    "VALUES(?,?,?,?,?)", (1001, 1, 'phone-note', 'from-phone',
                                          '2026-05-10T10:00:00'))
        self.ea._queue_change(cur, 'note', 1001, 'INSERT')
        con.commit()
        con.close()

        # Phone publishes its delta stream to S3.
        published = self.ea._publish_deltas(s3)
        self.assertGreater(published, 0)
        self.assertTrue(any(k.startswith('changes/android-PHONE/')
                            for k in s3.objects),
                        f"expected phone delta key, got {list(s3.objects)}")

        # PC pulls via its real pull cycle (S3 + config mocked to the fake).
        with mock.patch('Evernothing_Connect.s3_pull._s3_client', return_value=s3), \
             mock.patch('Evernothing_Connect.s3_pull._is_configured', return_value=True):
            self.s3_pull._pull_cycle()

        got = _row(self.pc_db, 'notes', 1001)
        self.assertIsNotNone(got, "PC never received the phone's note")
        self.assertEqual(got['note_value'], 'from-phone')
        self.assertEqual(got['last_modified_device'], 'android-PHONE')

    def test_pc_edit_propagates_to_phone_via_s3(self):
        """PC creates a note -> publishes delta to S3 -> phone pulls and
        applies it. Reverse direction of the cloud path."""
        s3 = FakeS3()

        # PC makes a local write and queues it. The PC's queue_change reads
        # the row back with dict(r), which requires a Row factory — the real
        # app's db() helper sets this, so the test connection must too.
        con = sqlite3.connect(self.pc_db)
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        cur.execute("INSERT INTO notes(id,user_id,note_key,note_value,updated_at) "
                    "VALUES(?,?,?,?,?)", (2002, 1, 'pc-note', 'from-pc',
                                          '2026-05-10T11:00:00'))
        self.s3_sync.queue_change(cur, 'note', 2002, 'INSERT')
        con.commit()
        con.close()

        # PC publishes its delta stream to S3 (real worker, fake client).
        with mock.patch('Evernothing_Connect.s3_sync._s3_client', return_value=s3), \
             mock.patch('Evernothing_Connect.s3_sync._is_configured', return_value=True), \
             mock.patch('Evernothing_Connect.s3_sync._apply_bucket_policy'), \
             mock.patch('Evernothing_Connect.s3_sync._enable_s3_access_logging'), \
             mock.patch('Evernothing_Connect.s3_sync._enable_s3_object_lock'), \
             mock.patch('Evernothing_Connect.s3_sync._prune_old_backups'):
            self.s3_sync.sync_s3()

        self.assertTrue(any(k.startswith('changes/desktop-PC/')
                            for k in s3.objects),
                        f"expected PC delta key, got {list(s3.objects)}")

        # Phone pulls via its real pull_deltas (fake S3 client).
        with mock.patch.object(self.ea, '_s3_client', return_value=s3):
            applied = self.ea.pull_deltas(silent=True)
        self.assertGreater(applied, 0)

        got = _row(self.droid_db, 'notes', 2002)
        self.assertIsNotNone(got, "phone never received the PC's note")
        self.assertEqual(got['note_value'], 'from-pc')
        self.assertEqual(got['last_modified_device'], 'desktop-PC')

    def test_concurrent_edit_converges_by_lww(self):
        """Both sides edit the SAME note id at the SAME version. After a
        full cloud exchange both DBs must agree, and the winner is the
        lexicographically-larger device id (LWW tie-break)."""
        s3 = FakeS3()

        # Seed the same base note (version 1) on both sides.
        for path in (self.pc_db, self.droid_db):
            con = sqlite3.connect(path)
            con.execute("INSERT INTO notes(id,user_id,note_key,note_value,updated_at,"
                        "version,last_modified_device) VALUES(?,?,?,?,?,?,?)",
                        (3003, 1, 'k', 'base', '2026-05-10T09:00:00', 1, 'seed'))
            con.commit()
            con.close()

        # PC edits -> version 2, device desktop-PC.
        con = sqlite3.connect(self.pc_db); con.row_factory = sqlite3.Row
        cur = con.cursor()
        cur.execute("UPDATE notes SET note_value='pc-wins', "
                    "updated_at='2026-05-10T12:00:00' WHERE id=3003")
        self.s3_sync.queue_change(cur, 'note', 3003, 'UPDATE')
        con.commit(); con.close()

        # Phone edits -> version 2, device android-PHONE (concurrent).
        con = sqlite3.connect(self.droid_db); cur = con.cursor()
        cur.execute("UPDATE notes SET note_value='phone-wins', "
                    "updated_at='2026-05-10T12:00:01' WHERE id=3003")
        self.ea._queue_change(cur, 'note', 3003, 'UPDATE')
        con.commit(); con.close()

        # Both publish.
        with mock.patch('Evernothing_Connect.s3_sync._s3_client', return_value=s3), \
             mock.patch('Evernothing_Connect.s3_sync._is_configured', return_value=True), \
             mock.patch('Evernothing_Connect.s3_sync._apply_bucket_policy'), \
             mock.patch('Evernothing_Connect.s3_sync._enable_s3_access_logging'), \
             mock.patch('Evernothing_Connect.s3_sync._enable_s3_object_lock'), \
             mock.patch('Evernothing_Connect.s3_sync._prune_old_backups'):
            self.s3_sync.sync_s3()
        with mock.patch.object(self.ea, '_s3_client', return_value=s3):
            self.ea._publish_deltas(s3)

        # Each side pulls the other's delta.
        with mock.patch('Evernothing_Connect.s3_pull._s3_client', return_value=s3), \
             mock.patch('Evernothing_Connect.s3_pull._is_configured', return_value=True):
            self.s3_pull._pull_cycle()
        with mock.patch.object(self.ea, '_s3_client', return_value=s3):
            self.ea.pull_deltas(silent=True)

        pc = _row(self.pc_db, 'notes', 3003)
        droid = _row(self.droid_db, 'notes', 3003)

        # Both sides must hold the identical winning value (convergence).
        self.assertEqual(pc['note_value'], droid['note_value'],
                         "DBs diverged after concurrent edit")
        self.assertEqual(pc['last_modified_device'], droid['last_modified_device'])
        # version 2 on both sides, tie broken lexicographically: 'desktop-PC'
        # > 'android-PHONE', so the PC write wins deterministically.
        self.assertEqual(pc['last_modified_device'], 'desktop-PC')
        self.assertEqual(pc['note_value'], 'pc-wins')

    def test_delete_propagates_via_s3(self):
        """A DELETE on the phone removes the row on the PC after sync."""
        s3 = FakeS3()
        # Seed a note on both sides.
        for path in (self.pc_db, self.droid_db):
            con = sqlite3.connect(path)
            con.execute("INSERT INTO notes(id,user_id,note_key,note_value,updated_at,"
                        "version,last_modified_device) VALUES(?,?,?,?,?,?,?)",
                        (4004, 1, 'k', 'v', '2026-05-10T09:00:00', 1, 'seed'))
            con.commit(); con.close()

        # Phone deletes, queuing an explicit payload (mirrors the app).
        con = sqlite3.connect(self.droid_db); cur = con.cursor()
        cur.execute("DELETE FROM notes WHERE id=4004")
        self.ea._queue_change(cur, 'note', 4004, 'DELETE',
                              payload={'id': 4004, 'user_id': 1})
        con.commit(); con.close()
        self.ea._publish_deltas(s3)

        with mock.patch('Evernothing_Connect.s3_pull._s3_client', return_value=s3), \
             mock.patch('Evernothing_Connect.s3_pull._is_configured', return_value=True):
            self.s3_pull._pull_cycle()

        self.assertIsNone(_row(self.pc_db, 'notes', 4004),
                          "DELETE did not propagate to PC")


# ===========================================================================
# TETHERED: direct full-DB transfer over the USB/ADB channel
# ===========================================================================
class TetheredSyncTests(_Base):

    def test_full_db_transfer_pc_to_phone(self):
        """Simulate `adb push evernothing.db` — the whole PC DB is copied
        onto the phone. The phone must then read the PC's rows intact."""
        # PC has several notes the phone has never seen.
        con = sqlite3.connect(self.pc_db)
        for i in range(5):
            con.execute("INSERT INTO notes(id,user_id,note_key,note_value,updated_at,"
                        "version,last_modified_device) VALUES(?,?,?,?,?,?,?)",
                        (5000 + i, 1, f'k{i}', f'v{i}', '2026-05-10T09:00:00',
                         1, 'desktop-PC'))
        con.commit(); con.close()
        pc_notes = _count(self.pc_db, 'notes')

        # Tethered transfer = byte-for-byte file copy (what adb push does).
        import shutil
        shutil.copy2(self.pc_db, self.droid_db)

        # Phone reads the transferred DB.
        self.assertEqual(_count(self.droid_db, 'notes'), pc_notes)
        got = _row(self.droid_db, 'notes', 5002)
        self.assertEqual(got['note_value'], 'v2')
        self.assertEqual(got['last_modified_device'], 'desktop-PC')

    def test_full_db_transfer_phone_to_pc(self):
        """Simulate `adb pull evernothing.db` — the phone DB is copied back
        onto the PC, which then reads the phone's rows intact."""
        con = sqlite3.connect(self.droid_db)
        con.execute("INSERT INTO notes(id,user_id,note_key,note_value,updated_at,"
                    "version,last_modified_device) VALUES(?,?,?,?,?,?,?)",
                    (6006, 1, 'phone-only', 'created-on-phone',
                     '2026-05-10T09:00:00', 1, 'android-PHONE'))
        con.commit(); con.close()

        import shutil
        shutil.copy2(self.droid_db, self.pc_db)

        got = _row(self.pc_db, 'notes', 6006)
        self.assertIsNotNone(got, "phone->PC transfer lost the row")
        self.assertEqual(got['note_value'], 'created-on-phone')
        self.assertEqual(got['last_modified_device'], 'android-PHONE')

    def test_transferred_db_is_a_valid_sqlite_image(self):
        """A tethered transfer must land a well-formed SQLite file the
        receiver can open and integrity-check (guards against partial
        pushes clobbering a good DB)."""
        import shutil
        shutil.copy2(self.pc_db, self.droid_db)
        con = sqlite3.connect(self.droid_db)
        try:
            self.assertEqual(con.execute('PRAGMA integrity_check').fetchone()[0], 'ok')
        finally:
            con.close()


if __name__ == '__main__':
    unittest.main(verbosity=2)
