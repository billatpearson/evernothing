"""
Evernothing_Connect/s3_pull.py — Minimal multi-device delta pull (Option B).

What this does
--------------
Every S3_PULL_INTERVAL seconds the worker:
  1. Lists all objects under `changes/<device_id>/` for every device that
     isn't us.
  2. Skips any key it has already processed this process-lifetime.
  3. Downloads each new delta file, applies its CREATE / UPDATE / DELETE
     operations against the local DB using UPSERT semantics.
  4. Resolves conflicts with last-writer-wins by `updated_at`.

What this intentionally does NOT do
-----------------------------------
- No schema changes. No version counter column. Conflict resolution is
  best-effort based on the `updated_at` we already record.
- No persistent cursor. Seen-key state lives in memory — on restart the
  worker re-reads existing deltas. Apply operations are idempotent
  (UPSERT / DELETE-IF-EXISTS) so this is safe but wasteful.
- No loop prevention column — relies on the applier writing directly
  with sqlite3 instead of going through queue_change, so applied rows
  don't get re-queued for re-upload.
- No attachment sync. Notes + folders only.

When to upgrade to Option A (full Phase 3)
------------------------------------------
- If conflicts get painful (same note edited on two devices within seconds
  of each other — whichever clock is ahead wins silently).
- If you outgrow a single user and need per-user cursor tracking.
- If restart-thrash of re-processing deltas becomes a measurable cost.
"""
import io
import json
import os
import sqlite3
import threading
import time
import traceback
from typing import Dict, Iterable, Optional

from Evernothing_Web.app import app, logger
from Evernothing_Connect.s3_sync import (
    DEVICE_ID, S3_BUCKET_NAME, _is_configured, _s3_client, _sanitize_error,
)

PULL_INTERVAL = max(30, int(os.environ.get('S3_PULL_INTERVAL', '300')))  # 5 min default, min 30s

# In-memory set of keys we've already applied. Survives for the lifetime
# of this Python process; resets on restart.
_applied_keys: set = set()
_applied_keys_lock = threading.Lock()

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

    # Enumerate every changes/<device>/ prefix and skip our own.
    # Using the top-level `changes/` prefix + client-side filter is simpler
    # than per-device ListObjects calls and usually cheaper at this scale.
    for page in paginator.paginate(Bucket=S3_BUCKET_NAME, Prefix='changes/'):
        for obj in page.get('Contents', []) or []:
            key = obj['Key']
            # key looks like: changes/<device>/<ts>.json
            parts = key.split('/', 2)
            if len(parts) < 3:
                continue
            device = parts[1]
            if device == DEVICE_ID:
                continue  # our own uploads, not a peer's changes
            with _applied_keys_lock:
                if key in _applied_keys:
                    continue
            try:
                buf = io.BytesIO()
                s3.download_fileobj(S3_BUCKET_NAME, key, buf)
                changes = json.loads(buf.getvalue().decode('utf-8'))
            except Exception as e:
                logger.warning(f'pull: could not fetch/parse {key}: {e}')
                continue

            try:
                applied = _apply_changes(changes)
                rows_applied += applied
                deltas_seen += 1
                with _applied_keys_lock:
                    _applied_keys.add(key)
                logger.info(f'pull: applied {applied} rows from {key}')
            except Exception as e:
                logger.error(f'pull: failed to apply {key}: {e}')

    _pull_status['ok']           = True
    _pull_status['deltas_seen'] += deltas_seen
    _pull_status['rows_applied']+= rows_applied
    _pull_status['last_pull']    = _utc_now_iso()
    _pull_status['error']        = None


# ---------------------------------------------------------------------------
# Delta application
# ---------------------------------------------------------------------------
def _apply_changes(changes: Iterable[dict]) -> int:
    """Apply a list of change records. Writes with a fresh sqlite3
    connection, bypassing queue_change, so applied rows aren't re-queued.
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

            if entity == 'note':
                touched += _apply_note(cur, op, eid, data)
            elif entity == 'folder':
                touched += _apply_folder(cur, op, eid, data)
            else:
                # Unknown entity types are ignored so a newer sender
                # doesn't break an older receiver.
                continue
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()
    return touched


def _apply_note(cur, op, nid, data) -> int:
    if op == 'DELETE':
        cur.execute('DELETE FROM notes WHERE id=?', (nid,))
        return cur.rowcount

    # CREATE and UPDATE both go through an upsert with LWW by updated_at.
    incoming_ts = data.get('updated_at') or ''
    existing = cur.execute(
        'SELECT id, updated_at FROM notes WHERE id=?', (nid,)).fetchone()

    if existing:
        if (existing['updated_at'] or '') >= incoming_ts:
            # We already have the same or newer version — skip.
            return 0
        cur.execute(
            'UPDATE notes SET user_id=?, folder_id=?, note_key=?, note_value=?, '
            'description=?, updated_at=? WHERE id=?',
            (data.get('user_id'), data.get('folder_id'), data.get('note_key'),
             data.get('note_value'), data.get('description'), incoming_ts, nid))
    else:
        cur.execute(
            'INSERT INTO notes (id, user_id, folder_id, note_key, note_value, '
            'description, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)',
            (nid, data.get('user_id'), data.get('folder_id'), data.get('note_key'),
             data.get('note_value'), data.get('description'), incoming_ts))
    return cur.rowcount


def _apply_folder(cur, op, fid, data) -> int:
    if op == 'DELETE':
        cur.execute('DELETE FROM folders WHERE id=?', (fid,))
        return cur.rowcount
    # Folders have no updated_at column in the schema — fallback to
    # replace-on-insert idempotency.
    existing = cur.execute('SELECT id FROM folders WHERE id=?', (fid,)).fetchone()
    if existing:
        cur.execute(
            'UPDATE folders SET user_id=?, name=?, parent_id=? WHERE id=?',
            (data.get('user_id'), data.get('name'), data.get('parent_id'), fid))
    else:
        cur.execute(
            'INSERT INTO folders (id, user_id, name, parent_id) VALUES (?, ?, ?, ?)',
            (fid, data.get('user_id'), data.get('name'), data.get('parent_id')))
    return cur.rowcount


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------
def _utc_now_iso() -> str:
    import datetime
    from datetime import timezone
    return datetime.datetime.now(timezone.utc).isoformat()
