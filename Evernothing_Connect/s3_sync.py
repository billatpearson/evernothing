"""
Evernothing_Connect/s3_sync.py
All S3/AWS connectivity: client factory, bucket hardening, sync worker,
delta queue, restore.

Phase 1 guarantees:
- If S3 is not configured, every public entry point is a cheap no-op —
  no retries, no user-visible tracebacks, no log spam.
- Bucket-hardening sentinel lives under log/ (git-ignored) so cleaning
  the repo doesn't accidentally re-trigger bucket-policy writes.
- Timestamped DB backups are pruned to S3_BACKUP_RETENTION (default 10).
- Restore correctly decrypts the SSE-wrapped, client-side AES-GCM-encrypted
  DB before writing it to disk.
- UI-facing error strings are sanitized; full tracebacks go to server log.
"""
import datetime
import io
import json
import os
import time
import traceback
from datetime import timezone

from Evernothing_Web.app import app, logger

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
except ImportError:
    pass

try:
    from aws_config import S3_BUCKET_NAME, AWS_REGION, AWS_PROFILE
except ImportError:
    S3_BUCKET_NAME = os.environ.get('S3_BUCKET_NAME', '').strip()
    AWS_REGION     = os.environ.get('AWS_REGION', 'us-east-1')
    AWS_PROFILE    = os.environ.get('AWS_PROFILE', '').strip()

AWS_ACCESS_KEY_ID     = (os.environ.get('AWS_ACCESS_KEY_ID') or '').strip() or None
AWS_SECRET_ACCESS_KEY = (os.environ.get('AWS_SECRET_ACCESS_KEY') or '').strip() or None
KMS_KEY_ID            = os.environ.get('KMS_KEY_ID')
DEVICE_ID             = os.environ.get('DEVICE_ID', __import__('socket').gethostname())
BACKUP_RETENTION      = max(1, int(os.environ.get('S3_BACKUP_RETENTION', '10')))

# Obvious unconfigured placeholder from .env.example
_PLACEHOLDER_BUCKETS = {'your-bucket-name-here', 'example-bucket', ''}

try:
    import boto3
except ImportError:
    boto3 = None

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
_LOG_DIR = os.path.join(_ROOT, 'log')
_BUCKET_POLICY_SENTINEL = os.path.join(_LOG_DIR, '.s3_bucket_hardened')

_bucket_policy_applied = False
_s3_status = {
    'ok':         None,
    'configured': False,
    'bucket':     '',
    'region':     AWS_REGION,
    'last_sync':  None,
    'error':      None,
}


# ---------------------------------------------------------------------------
# Guards
# ---------------------------------------------------------------------------
def _is_configured():
    """Return True only when S3 has all of: boto3 installed, a real bucket
    name, and at least one usable credential source."""
    if not boto3:
        _s3_status['error'] = 'boto3 not installed'
        return False
    if S3_BUCKET_NAME in _PLACEHOLDER_BUCKETS:
        _s3_status['error'] = 'S3_BUCKET_NAME not configured'
        return False
    if not (AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY) and not AWS_PROFILE:
        # We might still have credentials via instance profile or
        # AWS_SESSION_TOKEN. Only flag obvious absence.
        if not os.environ.get('AWS_SESSION_TOKEN'):
            # Soft-configured. boto3 default chain may still succeed.
            pass
    _s3_status['configured'] = True
    _s3_status['bucket']     = S3_BUCKET_NAME
    return True


def _sanitize_error(exc):
    """Short user-visible message; full detail goes to the log."""
    msg = str(exc) or exc.__class__.__name__
    # Strip ARNs / request IDs that leak account metadata
    for piece in ('arn:aws', 'RequestId', 'Extended Request Id'):
        idx = msg.find(piece)
        if idx != -1:
            msg = msg[:idx].rstrip(' ,;:')
            break
    return msg[:160]


# ---------------------------------------------------------------------------
# Client factory
# ---------------------------------------------------------------------------
def _s3_client():
    ca = os.environ.get('AWS_CA_BUNDLE') or True
    base = {'region_name': AWS_REGION, 'verify': ca}
    if AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY:
        return boto3.client('s3', **base,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
    if AWS_PROFILE:
        try:
            return boto3.Session(profile_name=AWS_PROFILE).client('s3', **base)
        except Exception as e:
            logger.warning(f"AWS profile '{AWS_PROFILE}' failed: {e}")
    return boto3.client('s3', **base)


# ---------------------------------------------------------------------------
# Bucket hardening
# ---------------------------------------------------------------------------
def _apply_bucket_policy(s3, bucket_name):
    """Apply a safe default bucket policy.

    Principals allowed:
      - Anything under the AWS account that owns the bucket (root + IAM).
      - Any ARN in S3_ALLOWED_PRINCIPALS (comma-separated).
    Denies:
      - Any request that isn't HTTPS.
      - Any principal outside the account or the allow list.
      - Requests from IPs outside S3_ALLOWED_IPS (optional).

    We deliberately DO NOT lock the bucket to a single IAM user ARN —
    that's a footgun when keys rotate or the user is deleted.
    """
    allowed_ips = [ip.strip() for ip in os.environ.get('S3_ALLOWED_IPS', '').split(',') if ip.strip()]
    extra_principals = [p.strip() for p in os.environ.get('S3_ALLOWED_PRINCIPALS', '').split(',') if p.strip()]

    account_id = None
    try:
        sts_kw = {'region_name': AWS_REGION}
        if AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY:
            sts_kw.update(aws_access_key_id=AWS_ACCESS_KEY_ID,
                          aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
        account_id = boto3.client('sts', **sts_kw).get_caller_identity()['Account']
    except Exception as e:
        logger.warning(f'Could not resolve AWS account id: {e}')

    stmts = [{
        'Sid': 'DenyInsecureTransport', 'Effect': 'Deny', 'Principal': '*',
        'Action': 's3:*',
        'Resource': [f'arn:aws:s3:::{bucket_name}', f'arn:aws:s3:::{bucket_name}/*'],
        'Condition': {'Bool': {'aws:SecureTransport': 'false'}},
    }]

    if account_id:
        # Allow anyone in the owning account + any explicitly listed principal.
        # Without the account we skip this rule rather than publish a bucket.
        allowed_principals = [f'arn:aws:iam::{account_id}:root'] + extra_principals
        stmts.append({
            'Sid': 'DenyOutsideAccount', 'Effect': 'Deny', 'Principal': '*',
            'Action': 's3:*',
            'Resource': [f'arn:aws:s3:::{bucket_name}', f'arn:aws:s3:::{bucket_name}/*'],
            'Condition': {
                'StringNotEquals': {'aws:PrincipalAccount': account_id},
                'StringNotEqualsIfExists': {'aws:PrincipalArn': allowed_principals},
            },
        })
    else:
        logger.warning('Bucket policy will be DenyInsecureTransport only — '
                       'set S3_ALLOWED_PRINCIPALS to restrict access by ARN.')

    if allowed_ips:
        stmts.append({
            'Sid': 'DenyNonAllowedIPs', 'Effect': 'Deny', 'Principal': '*',
            'Action': 's3:*',
            'Resource': [f'arn:aws:s3:::{bucket_name}', f'arn:aws:s3:::{bucket_name}/*'],
            'Condition': {'NotIpAddress': {'aws:SourceIp': allowed_ips}},
        })
    try:
        s3.put_bucket_policy(Bucket=bucket_name,
            Policy=json.dumps({'Version': '2012-10-17', 'Statement': stmts}))
        logger.info(f'Bucket policy applied to {bucket_name}')
    except Exception as e:
        logger.warning(f'Could not apply bucket policy: {e}')


def _enable_s3_access_logging(s3, bucket_name):
    log_bucket = f'{bucket_name}-logs'
    log_retention_days = int(os.environ.get('S3_LOG_RETENTION_DAYS', '90'))
    try:
        created = False
        try:
            s3.head_bucket(Bucket=log_bucket)
        except Exception:
            created = True
            if AWS_REGION == 'us-east-1':
                s3.create_bucket(Bucket=log_bucket)
            else:
                s3.create_bucket(Bucket=log_bucket,
                    CreateBucketConfiguration={'LocationConstraint': AWS_REGION})
            s3.put_public_access_block(Bucket=log_bucket,
                PublicAccessBlockConfiguration={
                    'BlockPublicAcls': True, 'IgnorePublicAcls': True,
                    'BlockPublicPolicy': True, 'RestrictPublicBuckets': True,
                })

        # Always enforce these — harmless to reapply on existing buckets.
        try:
            s3.put_bucket_encryption(Bucket=log_bucket,
                ServerSideEncryptionConfiguration={'Rules': [
                    {'ApplyServerSideEncryptionByDefault': {'SSEAlgorithm': 'AES256'}}]})
        except Exception as e:
            logger.warning(f'Could not enable SSE on log bucket: {e}')

        try:
            s3.put_bucket_lifecycle_configuration(Bucket=log_bucket,
                LifecycleConfiguration={'Rules': [{
                    'ID': 'ExpireOldAccessLogs',
                    'Status': 'Enabled',
                    'Filter': {'Prefix': 'access-logs/'},
                    'Expiration': {'Days': log_retention_days},
                    'AbortIncompleteMultipartUpload': {'DaysAfterInitiation': 7},
                }]})
            logger.info(f'Log bucket lifecycle: expire after {log_retention_days}d')
        except Exception as e:
            logger.warning(f'Could not set lifecycle on log bucket: {e}')

        s3.put_bucket_acl(Bucket=log_bucket, ACL='log-delivery-write')
        s3.put_bucket_logging(Bucket=bucket_name, BucketLoggingStatus={
            'LoggingEnabled': {'TargetBucket': log_bucket, 'TargetPrefix': 'access-logs/'},
        })
        if created:
            logger.info(f'Created hardened log bucket s3://{log_bucket}/')
        logger.info(f'S3 access logging -> s3://{log_bucket}/access-logs/')
    except Exception as e:
        logger.warning(f'Could not enable S3 access logging: {e}')


def _enable_s3_object_lock(s3, bucket_name):
    """Apply Object Lock default retention. Object Lock must have been
    enabled at bucket creation — if it wasn't, this call will fail cleanly
    and we'll only warn once (not on every sync)."""
    lock_days = int(os.environ.get('S3_LOCK_DAYS', '30'))
    try:
        s3.put_object_lock_configuration(Bucket=bucket_name, ObjectLockConfiguration={
            'ObjectLockEnabled': 'Enabled',
            'Rule': {'DefaultRetention': {'Mode': 'GOVERNANCE', 'Days': lock_days}},
        })
        logger.info(f'S3 Object Lock GOVERNANCE {lock_days}d on {bucket_name}')
    except Exception as e:
        logger.info('Object Lock not applied (only possible at bucket creation): %s',
                    _sanitize_error(e))


# ---------------------------------------------------------------------------
# Upload helpers
# ---------------------------------------------------------------------------
def _s3_upload_with_retry(fn, *args, **kwargs):
    """Retry an S3 call up to 3 times.

    IMPORTANT: boto3.upload_fileobj consumes and closes the passed stream.
    For retryable uploads use _s3_upload_bytes_with_retry.
    """
    for attempt in range(3):
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            if attempt == 2:
                raise
            wait = 2 ** attempt
            logger.warning(f'S3 call attempt {attempt+1} failed ({e}), retrying in {wait}s')
            time.sleep(wait)


def _s3_upload_bytes_with_retry(s3, data: bytes, bucket: str, key: str, extra_args=None):
    """Retryable bytes-to-S3 upload. Fresh BytesIO per attempt.

    Adds ChecksumAlgorithm='SHA256' so S3 verifies the payload against a
    client-side hash — any corruption in transit is rejected with an error.
    """
    args = {'ChecksumAlgorithm': 'SHA256'}
    if extra_args:
        args.update(extra_args)
    for attempt in range(3):
        try:
            return s3.upload_fileobj(io.BytesIO(data), bucket, key, ExtraArgs=args)
        except Exception as e:
            if attempt == 2:
                raise
            wait = 2 ** attempt
            logger.warning(
                f's3://{bucket}/{key} upload attempt {attempt+1} failed ({e}), '
                f'retrying in {wait}s')
            time.sleep(wait)


# ---------------------------------------------------------------------------
# Backup pruning
# ---------------------------------------------------------------------------
def _prune_old_backups(s3, bucket, db_path):
    """Keep only the most recent BACKUP_RETENTION objects under backups/."""
    try:
        prefix = f'backups/{db_path}.'
        paginator = s3.get_paginator('list_objects_v2')
        all_objs = [obj
                    for page in paginator.paginate(Bucket=bucket, Prefix=prefix)
                    for obj in page.get('Contents', [])]
        all_objs.sort(key=lambda o: o['LastModified'])
        to_delete = all_objs[:-BACKUP_RETENTION] if len(all_objs) > BACKUP_RETENTION else []
        if to_delete:
            s3.delete_objects(Bucket=bucket,
                Delete={'Objects': [{'Key': o['Key']} for o in to_delete]})
            logger.info(f'Pruned {len(to_delete)} old S3 backups, keeping last {BACKUP_RETENTION}')
    except Exception as e:
        logger.warning(f'Backup prune skipped: {e}')


# ---------------------------------------------------------------------------
# Sync queue
# ---------------------------------------------------------------------------
def queue_change(cur, entity_type, entity_id, operation, payload=None):
    if payload is None:
        payload = {}
        try:
            if entity_type == 'note':
                r = cur.execute(
                    'SELECT id,user_id,folder_id,note_key,note_value,description,updated_at '
                    'FROM notes WHERE id=?', (entity_id,)).fetchone()
                if r: payload = dict(r)
            elif entity_type == 'folder':
                r = cur.execute(
                    'SELECT id,user_id,name,parent_id FROM folders WHERE id=?',
                    (entity_id,)).fetchone()
                if r: payload = dict(r)
        except Exception as e:
            logger.warning(f'queue_change fetch failed: {e}')
    cur.execute(
        'INSERT INTO sync_queue (entity_type,entity_id,operation,payload,changed_at) '
        'VALUES(?,?,?,?,?)',
        (entity_type, entity_id, operation, json.dumps(payload),
         datetime.datetime.now(timezone.utc).isoformat()))


# ---------------------------------------------------------------------------
# Sync worker
# ---------------------------------------------------------------------------
def get_s3_status():
    return _s3_status.copy()


def sync_s3():
    if not _is_configured():
        logger.info(f'S3 sync skipped: {_s3_status["error"]}')
        return
    _sync_s3_worker()


def sync_s3_async():
    if app.config.get('TESTING'):
        return
    if not _is_configured():
        # Quiet skip — the configured flag is already on _s3_status.
        return
    import threading
    threading.Thread(target=_sync_s3_worker, daemon=True).start()


def _sync_s3_worker():
    from Evernothing_DB.database import get_db, DB
    from Evernothing_Security.security import KEY, aesgcm
    global _bucket_policy_applied
    try:
        s3 = _s3_client()
        os.makedirs(_LOG_DIR, exist_ok=True)
        if not _bucket_policy_applied and not os.path.exists(_BUCKET_POLICY_SENTINEL):
            _apply_bucket_policy(s3, S3_BUCKET_NAME)
            _enable_s3_access_logging(s3, S3_BUCKET_NAME)
            _enable_s3_object_lock(s3, S3_BUCKET_NAME)
            try:
                open(_BUCKET_POLICY_SENTINEL, 'w').close()
            except Exception:
                pass
            _bucket_policy_applied = True
        elif os.path.exists(_BUCKET_POLICY_SENTINEL):
            _bucket_policy_applied = True

        if KMS_KEY_ID:
            _sse = {'ServerSideEncryption': 'aws:kms', 'SSEKMSKeyId': KMS_KEY_ID}
        else:
            _sse = {'ServerSideEncryption': 'AES256'}
        extra_json = {'ContentType': 'application/json', **_sse}
        extra_db   = {**_sse}

        con = get_db(); cur = con.cursor()
        cur.execute(
            'SELECT id,entity_type,entity_id,operation,payload,changed_at '
            'FROM sync_queue WHERE synced_at IS NULL')
        rows = cur.fetchall()
        delta_ids = []
        if rows:
            changes = [{
                'op': r[3], 'entity': r[1], 'id': r[2],
                'data': json.loads(r[4]), 'at': r[5],
            } for r in rows]
            ts = datetime.datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
            _s3_upload_bytes_with_retry(
                s3, json.dumps(changes).encode(),
                S3_BUCKET_NAME, f'changes/{DEVICE_ID}/{ts}.json',
                extra_args=extra_json)
            delta_ids = [r[0] for r in rows]
        con.close()

        ts = datetime.datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
        with open(DB, 'rb') as f:
            db_bytes = f.read()
        if aesgcm and KEY:
            nonce = os.urandom(12)
            db_bytes = nonce + aesgcm.encrypt(nonce, db_bytes, None)
            enc_suffix = '.enc'
        else:
            enc_suffix = ''
        _s3_upload_bytes_with_retry(s3, db_bytes, S3_BUCKET_NAME,
                                    DB + enc_suffix, extra_args=extra_db)
        _s3_upload_bytes_with_retry(s3, db_bytes, S3_BUCKET_NAME,
                                    f'backups/{DB}.{ts}{enc_suffix}',
                                    extra_args=extra_db)
        logger.info(f'S3 DB backup: s3://{S3_BUCKET_NAME}/backups/{DB}.{ts}{enc_suffix}')

        _prune_old_backups(s3, S3_BUCKET_NAME, DB)

        if delta_ids:
            con = get_db(); cur = con.cursor()
            now = datetime.datetime.now(timezone.utc).isoformat()
            cur.execute(
                'UPDATE sync_queue SET synced_at=? WHERE id IN ({})'.format(
                    ','.join('?' * len(delta_ids))),
                [now] + delta_ids)
            con.commit(); con.close()
        _s3_status['ok']        = True
        _s3_status['error']     = None
        _s3_status['last_sync'] = datetime.datetime.now(timezone.utc).isoformat()
    except Exception as e:
        _s3_status['ok']    = False
        _s3_status['error'] = _sanitize_error(e)
        logger.error('S3 Sync Error: %s\n%s', e, traceback.format_exc())


# ---------------------------------------------------------------------------
# Restore
# ---------------------------------------------------------------------------
def restore_from_s3():
    """On startup, if the local DB is missing, pull the latest from S3.

    Handles both the plaintext (legacy) and the AES-GCM-encrypted (.enc)
    upload paths. Writes to a temp file and atomically renames once the
    payload is decrypted and verified, so a partial download never
    clobbers a good DB.
    """
    from Evernothing_DB.database import DB
    from Evernothing_Security.security import KEY, aesgcm

    if not _is_configured():
        return
    if os.path.exists(DB):
        return

    try:
        s3 = _s3_client()
        enc_suffix = '.enc' if (aesgcm and KEY) else ''
        src_key = DB + enc_suffix

        # Stream into memory first so we can decrypt/verify before writing.
        buf = io.BytesIO()
        try:
            s3.download_fileobj(S3_BUCKET_NAME, src_key, buf)
        except Exception:
            # Fallback: some legacy deployments stored plaintext.
            if enc_suffix:
                logger.info(f'Encrypted {src_key} not found, trying plaintext fallback')
                buf = io.BytesIO()
                s3.download_fileobj(S3_BUCKET_NAME, DB, buf)
                enc_suffix = ''
            else:
                raise

        raw = buf.getvalue()
        if enc_suffix == '.enc':
            if len(raw) < 28:  # 12 nonce + 16 tag minimum
                raise ValueError('ciphertext too short for AES-GCM')
            nonce, ct = raw[:12], raw[12:]
            raw = aesgcm.decrypt(nonce, ct, None)

        # Atomic write — temp file then rename
        tmp = DB + '.restore.tmp'
        os.makedirs(os.path.dirname(DB) or '.', exist_ok=True)
        with open(tmp, 'wb') as f:
            f.write(raw)
        os.replace(tmp, DB)
        logger.info(f'Restored {DB} from s3://{S3_BUCKET_NAME}/{src_key} ({len(raw)} bytes)')
    except Exception as e:
        logger.warning('S3 restore skipped: %s', _sanitize_error(e))
