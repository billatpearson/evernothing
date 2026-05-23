"""
Evernothing_Connect/s3_pull.py — Phase 3 Option A multi-device delta pull.

Upgrade from the Option B in-memory cursor:

  - Persistent cursor in a `replication_cursor` table (peer_device,
    last_key). Restarts no longer re-list every delta.
  - Version-based last-writer-wins. Each row carries `version` and
    `last_modified_device`. On apply, incoming wins iff its version is
    strictly higher OR the version matches and the incoming device id
    sorts higher lexicographically. This is deterministic regardless
    of clock skew between devices.
  - Receiver writes via raw sqlite3 (no queue_change), so accepted
    incoming rows never get re-published — loop prevention.
  - Receiver stamps the row with the SENDER's device id, so the next
    time we publish locally we'll bump the version and stamp ourselves,
    and the sender then sees a strictly higher version.

What this does NOT do
---------------------
- No attachment sync.
- No transactional batching across delta files. Each file is its own
  unit of work; if one fails to apply we skip it but don't rewind the
  cursor.

Schema dependencies
-------------------
- notes / folders / note_history all have `version INTEGER NOT NULL
  DEFAULT 1` and `last_modified_device TEXT`.
- replication_cursor (peer_device PK, last_key, updated_at).

Both are created by Evernothing_DB.database.init_db() — idempotent.
"""
import datetime
import io
import json
import os
import sqlite3
import threading
import time
import traceback
from datetime import timezone
from typing import Dict, Iterable, Optional, Tuple

from Evernothing_Web.app import app, logger
from Evernothing_Connect.s3_sync import (
    DEVICE_ID, S3_BUCKET_NAME, _is_configured, _s3_client, _sanitize_error,
)

PULL_INTERVAL = max(30, int(os.environ.get('S3_PULL_INTERVAL', '300')))

_pull_status: Dict = {
    'ok':           None,
    'last_pull':    None,
    'deltas_seen':  0,
    'rows_applied': 0,
    'error':        None,
}

_worker_started = False
_worker_lock = threading.Lock()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def get_pull_status() -> Dict:
    return _pull_status.copy()


def start_pull_worker():
    """Start the background pull worker exactly once per process."""
    global _worker_started
    with _worker_lock:
        if _worker_started:
            return
        if app.config.get('TESTING'):
            return
        if not _is_configured():
            logger.info('S3 pull worker not started: S3 not configured')
            return
        t = threading.Thread(target=_worker_loop, name='s3-pull-worker', daemon=True)
        t.start()
        _worker_started = True
        logger.info(f'S3 pull worker started (interval {PULL_INTERVAL}s)')


def pull_once():
    """Run one pull cycle synchronously. Exposed for tests / manual trigger."""
    if not _is_configured():
        _pull_status['error'] = 'S3 not configured'
        return
    _pull_cycle()


# ---------------------------------------------------------------------------
# Cursor (replication_cursor table)
# ---------------------------------------------------------------------------
def _load_cursors() -> Dict[str, str]:
    """Return {peer_device: last_key} for every peer we've seen."""
    from Evernothing_DB.database import DB
    con = sqlite3.connect(DB)
    try:
        cur = con.execute('SELECT peer_device, last_key FROM replication_cursor')
        return {row[0]: row[1] for row in cur.fetchall()}
    finally:
        con.close()


def _save_cursor(peer: str, last_key: str) -> None:
    from Evernothing_DB.database import DB
    now = datetime.datetime.now(timezone.utc).isoformat()
    con = sqlite3.connect(DB)
    try:
        con.execute(
            'INSERT INTO replication_cursor (peer_device, last_key, updated_at) '
            'VALUES (?, ?, ?) ON CONFLICT(peer_device) DO UPDATE SET '
            'last_key = excluded.last_key, updated_at = excluded.updated_at',
            (peer, last_key, now))
        con.commit()
    finally:
        con.close()


# ---------------------------------------------------------------------------
# Worker
# ---------------------------------------------------------------------------
def _worker_loop():
    while True:
        try:
            _pull_cycle()
        except Exception as e:
            _pull_status['ok']    = False
            _pull_status['error'] = _sanitize_error(e)
            logger.error('S3 pull cycle error: %s\n%s', e, traceback.format_exc())
        time.sleep(PULL_INTERVAL)


def _pull_cycle():
    s3 = _s3_client()
    paginator = s3.get_paginator('list_objects_v2')
    deltas_seen = 0
    rows_applied = 0
    cursors = _load_cursors()
    # Group new keys by peer so we advance the cursor exactly once per peer.
    new_keys_by_peer: Dict[str, list] = {}

    for page in paginator.paginate(Bucket=S3_BUCKET_NAME, Prefix='changes/'):
        for obj in page.get('Contents', []) or []:
            key = obj['Key']
            parts = key.split('/', 2)
            if len(parts) < 3:
                continue
            peer = parts[1]
            if peer == DEVICE_ID:
                continue
            last_seen = cursors.get(peer)
            if last_seen is not None and key <= last_seen:
                continue
            new_keys_by_peer.setdefault(peer, []).append(key)

    for peer, keys in new_keys_by_peer.items():
        keys.sort()
        for key in keys:
            try:
                buf = io.BytesIO()
                s3.download_fileobj(S3_BUCKET_NAME, key, buf)
                changes = json.loads(buf.getvalue().decode('utf-8'))
            except Exception as e:
                logger.warning(f'pull: could not fetch/parse {key}: {e}')
                # Don't advance cursor past a key we couldn't read.
                break
            try:
                applied = _apply_changes(changes, sender_device=peer)
                rows_applied += applied
                deltas_seen += 1
                _save_cursor(peer, key)
                logger.info(f'pull: applied {applied} rows from {key}')
            except Exception as e:
                logger.error(f'pull: failed to apply {key}: {e}')
                break

    _pull_status['ok']           = True
    _pull_status['deltas_seen'] += deltas_seen
    _pull_status['rows_applied']+= rows_applied
    _pull_status['last_pull']    = datetime.datetime.now(timezone.utc).isoformat()
    _pull_status['error']        = None


# ---------------------------------------------------------------------------
# Conflict resolution
# ---------------------------------------------------------------------------
def _incoming_wins(local_version: int, local_device: Optional[str],
                   incoming_version: int, incoming_device: Optional[str]) -> bool:
    """Deterministic last-writer-wins: higher version wins; tie broken
    lexicographically by device id (so two peers that race converge to
    the same answer)."""
    if incoming_version > local_version:
        return True
    if incoming_version < local_version:
        return False
    return (incoming_device or '') > (local_device or '')


# ---------------------------------------------------------------------------
# Delta application
# ---------------------------------------------------------------------------
def _apply_changes(changes: Iterable[dict], sender_device: str) -> int:
    """Apply a list of change records from `sender_device`. Writes via
    raw sqlite3, bypassing queue_change, so applied rows aren't re-queued.
    Returns the number of rows actually touched."""
    from Evernothing_DB.database import DB
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    touched = 0
    try:
        for ch in changes:
            op     = (ch.get('op') or '').upper()
            entity = ch.get('entity')
            data   = ch.get('data') or {}
            eid    = ch.get('id') or data.get('id')

            # Trust the row's own device stamp first; fall back to the
            # bucket prefix sender_device only if missing.
            incoming_device  = data.get('last_modified_device') or sender_device
            incoming_version = int(data.get('version') or 1)

            if entity == 'note':
                touched += _apply_note(cur, op, eid, data,
                                       incoming_version, incoming_device)
            elif entity == 'folder':
                touched += _apply_folder(cur, op, eid, data,
                                         incoming_version, incoming_device)
            else:
                continue
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()
    return touched


def _apply_note(cur, op, nid, data, incoming_version, incoming_device) -> int:
    if op == 'DELETE':
        # DELETE always wins — there's no row to compare versions against.
        cur.execute('DELETE FROM notes WHERE id=?', (nid,))
        return cur.rowcount

    incoming_ts = data.get('updated_at') or ''
    existing = cur.execute(
        'SELECT id, version, last_modified_device FROM notes WHERE id=?',
        (nid,)).fetchone()

    if existing:
        local_version = int(existing['version'] or 1)
        local_device  = existing['last_modified_device']
        if not _incoming_wins(local_version, local_device,
                              incoming_version, incoming_device):
            return 0
        cur.execute(
            'UPDATE notes SET user_id=?, folder_id=?, note_key=?, note_value=?, '
            'description=?, updated_at=?, version=?, last_modified_device=? '
            'WHERE id=?',
            (data.get('user_id'), data.get('folder_id'), data.get('note_key'),
             data.get('note_value'), data.get('description'), incoming_ts,
             incoming_version, incoming_device, nid))
    else:
        cur.execute(
            'INSERT INTO notes (id, user_id, folder_id, note_key, note_value, '
            'description, updated_at, version, last_modified_device) '
            'VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
            (nid, data.get('user_id'), data.get('folder_id'),
             data.get('note_key'), data.get('note_value'),
             data.get('description'), incoming_ts,
             incoming_version, incoming_device))
    return cur.rowcount


def _apply_folder(cur, op, fid, data, incoming_version, incoming_device) -> int:
    if op == 'DELETE':
        cur.execute('DELETE FROM folders WHERE id=?', (fid,))
        return cur.rowcount
    existing = cur.execute(
        'SELECT id, version, last_modified_device FROM folders WHERE id=?',
        (fid,)).fetchone()
    if existing:
        local_version = int(existing['version'] or 1)
        local_device  = existing['last_modified_device']
        if not _incoming_wins(local_version, local_device,
                              incoming_version, incoming_device):
            return 0
        cur.execute(
            'UPDATE folders SET user_id=?, name=?, parent_id=?, version=?, '
            'last_modified_device=? WHERE id=?',
            (data.get('user_id'), data.get('name'), data.get('parent_id'),
             incoming_version, incoming_device, fid))
    else:
        cur.execute(
            'INSERT INTO folders (id, user_id, name, parent_id, version, '
            'last_modified_device) VALUES (?, ?, ?, ?, ?, ?)',
            (fid, data.get('user_id'), data.get('name'), data.get('parent_id'),
             incoming_version, incoming_device))
    return cur.rowcount
