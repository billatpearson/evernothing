"""
evernothing_logic.py — Core Logic
S3 sync, delta queue, audit logging, breadcrumbs, date formatting,
recursive folder deletion, IAM policy generation.
"""
import os, json, datetime, io
from datetime import timezone
from evernothing_config import (
    app, logger, DB, S3_BUCKET_NAME, AWS_REGION, AWS_PROFILE,
    AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, KMS_KEY_ID,
    NUM_BACKUPS, DEVICE_ID
)
from evernothing_db import db  # safe: evernothing_db only imports evernothing_config

try:
    import boto3
except ImportError:
    boto3 = None

_bucket_policy_applied = False
_BUCKET_POLICY_SENTINEL = ".bucket_policy_applied"  # #17: file sentinel survives worker restarts
_S3_RETRY_ATTEMPTS = 3


def _s3_upload_with_retry(fn, *args, **kwargs):
    """#16: retry S3 uploads with exponential backoff."""
    import time
    for attempt in range(_S3_RETRY_ATTEMPTS):
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            if attempt == _S3_RETRY_ATTEMPTS - 1:
                raise
            wait = 2 ** attempt
            logger.warning(f"S3 upload attempt {attempt+1} failed ({e}), retrying in {wait}s")
            time.sleep(wait)


# --- Utilities ---
def format_date(iso_str):
    try:
        return datetime.datetime.fromisoformat(iso_str).strftime("%m/%d/%Y %H:%M")
    except Exception:
        return iso_str


def get_breadcrumbs(cur, fid, uid):
    from evernothing_security import decrypt
    crumbs = []
    while fid:
        f = cur.execute(
            "SELECT id,name,parent_id FROM folders WHERE id=? AND user_id=?", (fid, uid)
        ).fetchone()
        if not f:
            break
        crumbs.insert(0, (f[0], decrypt(f[1])))
        fid = f[2]
    return crumbs


def log_change(cur, user_id, action, entity_type, entity_id, old_values, new_values, ip_addr):
    cur.execute(
        "INSERT INTO audit_log (user_id, action, entity_type, entity_id, old_values, new_values, timestamp, ip_address) "
        "VALUES(?,?,?,?,?,?,?,?)",
        (user_id, action, entity_type, entity_id,
         json.dumps(old_values), json.dumps(new_values),
         datetime.datetime.now(timezone.utc).isoformat(), ip_addr)
    )


def delete_recursive(cur, fid, uid):
    cur.execute("SELECT id FROM folders WHERE parent_id=? AND user_id=?", (fid, uid))
    for sub in cur.fetchall():
        delete_recursive(cur, sub[0], uid)
    cur.execute("DELETE FROM notes WHERE folder_id=? AND user_id=?", (fid, uid))
    cur.execute("DELETE FROM folders WHERE id=? AND user_id=?", (fid, uid))


def queue_change(cur, entity_type, entity_id, operation):
    payload = {}
    try:
        if entity_type == 'note':
            r = cur.execute(
                "SELECT id,user_id,folder_id,note_key,note_value,description,updated_at FROM notes WHERE id=?",
                (entity_id,)
            ).fetchone()
            if r:
                payload = {'id': r[0], 'user_id': r[1], 'folder_id': r[2],
                           'note_key': r[3], 'note_value': r[4], 'description': r[5], 'updated_at': r[6]}
        elif entity_type == 'folder':
            r = cur.execute(
                "SELECT id,user_id,name,parent_id FROM folders WHERE id=?", (entity_id,)
            ).fetchone()
            if r:
                payload = {'id': r[0], 'user_id': r[1], 'name': r[2], 'parent_id': r[3]}
    except Exception as e:
        logger.warning(f"queue_change fetch failed: {e}")
    cur.execute(
        "INSERT INTO sync_queue (entity_type, entity_id, operation, payload, changed_at) VALUES(?,?,?,?,?)",
        (entity_type, entity_id, operation, json.dumps(payload),
         datetime.datetime.now(timezone.utc).isoformat())
    )


# --- S3 ---
def _s3_client():
    if AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY:
        return boto3.client('s3', region_name=AWS_REGION,
                            aws_access_key_id=AWS_ACCESS_KEY_ID,
                            aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
    try:
        return boto3.Session(profile_name=AWS_PROFILE).client('s3')
    except Exception:
        return boto3.client('s3', region_name=AWS_REGION)


def get_iam_policy():
    return {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "EverNothingObjectAccess",
                "Effect": "Allow",
                "Action": ["s3:PutObject", "s3:GetObject"],
                "Resource": f"arn:aws:s3:::{S3_BUCKET_NAME}/*"
            },
            {
                "Sid": "EverNothingBucketAccess",
                "Effect": "Allow",
                "Action": ["s3:ListBucket", "s3:HeadBucket", "s3:CreateBucket",
                           "s3:PutBucketPolicy", "s3:PutBucketVersioning", "s3:PutPublicAccessBlock"],
                "Resource": f"arn:aws:s3:::{S3_BUCKET_NAME}"
            }
        ]
    }


def _apply_bucket_policy(s3, bucket_name):
    try:
        sts_kwargs = {'region_name': AWS_REGION}
        if AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY:
            sts_kwargs['aws_access_key_id'] = AWS_ACCESS_KEY_ID
            sts_kwargs['aws_secret_access_key'] = AWS_SECRET_ACCESS_KEY
        caller_arn = boto3.client('sts', **sts_kwargs).get_caller_identity()['Arn']
    except Exception as e:
        logger.warning(f"Could not determine caller ARN: {e}")
        return

    policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "DenyAllExceptCallerPrincipal",
                "Effect": "Deny", "Principal": "*", "Action": "s3:*",
                "Resource": [f"arn:aws:s3:::{bucket_name}", f"arn:aws:s3:::{bucket_name}/*"],
                "Condition": {"StringNotEquals": {"aws:PrincipalArn": caller_arn}}
            },
            {
                "Sid": "DenyInsecureTransport",
                "Effect": "Deny", "Principal": "*", "Action": "s3:*",
                "Resource": [f"arn:aws:s3:::{bucket_name}", f"arn:aws:s3:::{bucket_name}/*"],
                "Condition": {"Bool": {"aws:SecureTransport": "false"}}
            }
        ]
    }
    try:
        s3.put_bucket_policy(Bucket=bucket_name, Policy=json.dumps(policy))
        logger.info(f"Bucket policy applied to {bucket_name}")
    except Exception as e:
        logger.warning(f"Could not apply bucket policy: {e}")


def sync_s3():
    """#15: run in background thread so writes don't block HTTP responses."""
    if not boto3:
        logger.warning("S3 sync skipped: boto3 not available")
        return
    import threading
    threading.Thread(target=_sync_s3_worker, daemon=True).start()


def _sync_s3_worker():
    """Actual S3 sync logic — runs off the request thread."""
    try:
        global _bucket_policy_applied
        s3 = _s3_client()

        # #17: use file sentinel so policy is applied once per host, not per worker
        if not _bucket_policy_applied and not os.path.exists(_BUCKET_POLICY_SENTINEL):
            _apply_bucket_policy(s3, S3_BUCKET_NAME)
            try:
                open(_BUCKET_POLICY_SENTINEL, 'w').close()
            except Exception:
                pass
            _bucket_policy_applied = True
        elif os.path.exists(_BUCKET_POLICY_SENTINEL):
            _bucket_policy_applied = True

        extra_json = {"ServerSideEncryption": "aws:kms", "ContentType": "application/json"}
        extra_db   = {"ServerSideEncryption": "aws:kms"}
        if KMS_KEY_ID:
            extra_json["SSEKMSKeyId"] = KMS_KEY_ID
            extra_db["SSEKMSKeyId"]   = KMS_KEY_ID

        # Delta changes
        con = db(); cur = con.cursor()
        cur.execute("SELECT id, entity_type, entity_id, operation, payload, changed_at FROM sync_queue WHERE synced_at IS NULL")
        rows = cur.fetchall()
        delta_ids = []
        if rows:
            changes = [{"op": r[3], "entity": r[1], "id": r[2], "data": json.loads(r[4]), "at": r[5]} for r in rows]
            ts = datetime.datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            _s3_upload_with_retry(
                s3.upload_fileobj,
                io.BytesIO(json.dumps(changes).encode()), S3_BUCKET_NAME,
                f"changes/{DEVICE_ID}/{ts}.json", ExtraArgs=extra_json
            )
            delta_ids = [r[0] for r in rows]
            logger.info(f"S3 delta: {len(changes)} change(s)")
        con.close()

        # #18: full DB backup — mark delta synced only after backup succeeds
        ts = datetime.datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        with open(DB, 'rb') as f:
            db_bytes = f.read()
        _s3_upload_with_retry(s3.upload_fileobj, io.BytesIO(db_bytes), S3_BUCKET_NAME, DB, ExtraArgs=extra_db)
        _s3_upload_with_retry(s3.upload_fileobj, io.BytesIO(db_bytes), S3_BUCKET_NAME, f"backups/{DB}.{ts}", ExtraArgs=extra_db)
        logger.info(f"S3 DB backup: s3://{S3_BUCKET_NAME}/backups/{DB}.{ts}")

        # #18: only mark synced after both delta upload AND DB backup succeed
        if delta_ids:
            con = db(); cur = con.cursor()
            now = datetime.datetime.now(timezone.utc).isoformat()
            cur.execute(
                f"UPDATE sync_queue SET synced_at=? WHERE id IN ({','.join('?'*len(delta_ids))})",
                [now] + delta_ids
            )
            con.commit()
            con.close()

        print("S3 ASynch")
    except Exception as e:
        logger.error(f"S3 Sync Error: {e}")
        print(f"S3 Sync Error: {e}")


def restore_from_s3():
    if not boto3 or os.path.exists(DB):
        return
    try:
        _s3_client().download_file(S3_BUCKET_NAME, DB, DB)
        logger.info(f"Restored {DB} from S3")
        print(f"Restored database from S3: {DB}")
    except Exception as e:
        logger.warning(f"S3 restore skipped: {e}")


# --- Error handlers ---
# Minimal inline styles avoid any import dependency on evernothing_templates
_ERR_STYLE = "<style>body{background:#0a0a0a;color:#ffd700;font-family:sans-serif;padding:40px}a{color:#ffd700}</style>"

from flask import render_template_string, request as _request

@app.errorhandler(404)
def not_found(error):
    logger.warning(f"404: {_request.url}")
    return render_template_string(_ERR_STYLE + "<h3>404 - Page Not Found</h3><a href=/>Home</a>"), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"500: {error}")
    return render_template_string(_ERR_STYLE + "<h3>500 - Internal Server Error</h3><a href=/>Home</a>"), 500
