"""
Evernothing_Connect/s3_sync.py
All S3/AWS connectivity: client factory, bucket hardening,
sync worker, delta queue, restore.
"""
import io, json, os, time
from datetime import timezone
import datetime

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
    S3_BUCKET_NAME = os.environ.get('S3_BUCKET_NAME', '')
    AWS_REGION     = os.environ.get('AWS_REGION', 'us-east-1')
    AWS_PROFILE    = os.environ.get('AWS_PROFILE', '')

AWS_ACCESS_KEY_ID     = os.environ.get('AWS_ACCESS_KEY_ID') or None
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY') or None
KMS_KEY_ID            = os.environ.get('KMS_KEY_ID')
DEVICE_ID             = os.environ.get('DEVICE_ID', __import__('socket').gethostname())

try:
    import boto3
except ImportError:
    boto3 = None

_bucket_policy_applied = False
_BUCKET_POLICY_SENTINEL = os.path.join(os.path.dirname(__file__), '..', '.bucket_policy_applied')
_s3_status = {'ok': None, 'error': None}

# ---------------------------------------------------------------------------
# Client factory
# ---------------------------------------------------------------------------
def _s3_client():
    from botocore.exceptions import NoCredentialsError, PartialCredentialsError
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
    allowed_ips = [ip.strip() for ip in os.environ.get('S3_ALLOWED_IPS','').split(',') if ip.strip()]
    try:
        sts_kw = {'region_name': AWS_REGION}
        if AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY:
            sts_kw.update(aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
        caller_arn = boto3.client('sts', **sts_kw).get_caller_identity()['Arn']
    except Exception as e:
        logger.warning(f'Could not get caller ARN: {e}'); caller_arn = None

    stmts = [{'Sid':'DenyInsecureTransport','Effect':'Deny','Principal':'*','Action':'s3:*',
               'Resource':[f'arn:aws:s3:::{bucket_name}',f'arn:aws:s3:::{bucket_name}/*'],
               'Condition':{'Bool':{'aws:SecureTransport':'false'}}}]
    if caller_arn:
        stmts.append({'Sid':'DenyAllExceptCaller','Effect':'Deny','Principal':'*','Action':'s3:*',
                       'Resource':[f'arn:aws:s3:::{bucket_name}',f'arn:aws:s3:::{bucket_name}/*'],
                       'Condition':{'StringNotEquals':{'aws:PrincipalArn':caller_arn}}})
    if allowed_ips:
        stmts.append({'Sid':'DenyNonAllowedIPs','Effect':'Deny','Principal':'*','Action':'s3:*',
                       'Resource':[f'arn:aws:s3:::{bucket_name}',f'arn:aws:s3:::{bucket_name}/*'],
                       'Condition':{'NotIpAddress':{'aws:SourceIp':allowed_ips}}})
    try:
        s3.put_bucket_policy(Bucket=bucket_name, Policy=json.dumps({'Version':'2012-10-17','Statement':stmts}))
        logger.info(f'Bucket policy applied to {bucket_name}')
    except Exception as e:
        logger.warning(f'Could not apply bucket policy: {e}')

def _enable_s3_access_logging(s3, bucket_name):
    log_bucket = f'{bucket_name}-logs'
    try:
        try: s3.head_bucket(Bucket=log_bucket)
        except Exception:
            if AWS_REGION == 'us-east-1': s3.create_bucket(Bucket=log_bucket)
            else: s3.create_bucket(Bucket=log_bucket, CreateBucketConfiguration={'LocationConstraint':AWS_REGION})
            s3.put_public_access_block(Bucket=log_bucket, PublicAccessBlockConfiguration={
                'BlockPublicAcls':True,'IgnorePublicAcls':True,'BlockPublicPolicy':True,'RestrictPublicBuckets':True})
        s3.put_bucket_acl(Bucket=log_bucket, ACL='log-delivery-write')
        s3.put_bucket_logging(Bucket=bucket_name, BucketLoggingStatus={
            'LoggingEnabled':{'TargetBucket':log_bucket,'TargetPrefix':'access-logs/'}})
        logger.info(f'S3 access logging → s3://{log_bucket}/access-logs/')
    except Exception as e:
        logger.warning(f'Could not enable S3 access logging: {e}')

def _enable_s3_object_lock(s3, bucket_name):
    lock_days = int(os.environ.get('S3_LOCK_DAYS','30'))
    try:
        s3.put_object_lock_configuration(Bucket=bucket_name, ObjectLockConfiguration={
            'ObjectLockEnabled':'Enabled',
            'Rule':{'DefaultRetention':{'Mode':'GOVERNANCE','Days':lock_days}}})
        logger.info(f'S3 Object Lock GOVERNANCE {lock_days}d on {bucket_name}')
    except Exception as e:
        logger.warning(f'Object Lock not applied: {e}')

# ---------------------------------------------------------------------------
# Upload with retry
# ---------------------------------------------------------------------------
def _s3_upload_with_retry(fn, *args, **kwargs):
    """Retry an S3 call up to 3 times.

    IMPORTANT: boto3.upload_fileobj consumes and closes the passed stream.
    If you need to retry an upload, use _s3_upload_bytes_with_retry instead —
    it rebuilds the BytesIO on every attempt so retry #2 doesn't fail with
    "I/O operation on closed file."
    """
    for attempt in range(3):
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            if attempt == 2: raise
            wait = 2 ** attempt
            logger.warning(f'S3 upload attempt {attempt+1} failed ({e}), retrying in {wait}s')
            time.sleep(wait)


def _s3_upload_bytes_with_retry(s3, data: bytes, bucket: str, key: str, extra_args=None):
    """Retryable bytes-to-S3 upload. Fresh BytesIO per attempt."""
    for attempt in range(3):
        try:
            return s3.upload_fileobj(io.BytesIO(data), bucket, key,
                                     ExtraArgs=extra_args or {})
        except Exception as e:
            if attempt == 2: raise
            wait = 2 ** attempt
            logger.warning(
                f's3://{bucket}/{key} upload attempt {attempt+1} failed ({e}), '
                f'retrying in {wait}s')
            time.sleep(wait)

# ---------------------------------------------------------------------------
# Sync queue
# ---------------------------------------------------------------------------
def queue_change(cur, entity_type, entity_id, operation, payload=None):
    if payload is None:
        payload = {}
        try:
            if entity_type == 'note':
                r = cur.execute('SELECT id,user_id,folder_id,note_key,note_value,description,updated_at FROM notes WHERE id=?',(entity_id,)).fetchone()
                if r: payload = dict(r)
            elif entity_type == 'folder':
                r = cur.execute('SELECT id,user_id,name,parent_id FROM folders WHERE id=?',(entity_id,)).fetchone()
                if r: payload = dict(r)
        except Exception as e:
            logger.warning(f'queue_change fetch failed: {e}')
    cur.execute('INSERT INTO sync_queue (entity_type,entity_id,operation,payload,changed_at) VALUES(?,?,?,?,?)',
        (entity_type, entity_id, operation, json.dumps(payload),
         datetime.datetime.now(timezone.utc).isoformat()))

# ---------------------------------------------------------------------------
# Sync worker
# ---------------------------------------------------------------------------
def get_s3_status():
    return _s3_status.copy()

def sync_s3():
    if not boto3: logger.warning('S3 sync skipped: boto3 not available'); return
    _sync_s3_worker()

def sync_s3_async():
    if not boto3: logger.warning('S3 sync skipped: boto3 not available'); return
    if app.config.get('TESTING'): return
    import threading
    threading.Thread(target=_sync_s3_worker, daemon=True).start()

def _sync_s3_worker():
    from Evernothing_DB.database import get_db, DB
    from Evernothing_Security.security import KEY, aesgcm
    global _bucket_policy_applied
    try:
        s3 = _s3_client()
        if not _bucket_policy_applied and not os.path.exists(_BUCKET_POLICY_SENTINEL):
            _apply_bucket_policy(s3, S3_BUCKET_NAME)
            _enable_s3_access_logging(s3, S3_BUCKET_NAME)
            _enable_s3_object_lock(s3, S3_BUCKET_NAME)
            try: open(_BUCKET_POLICY_SENTINEL, 'w').close()
            except Exception: pass
            _bucket_policy_applied = True
        elif os.path.exists(_BUCKET_POLICY_SENTINEL):
            _bucket_policy_applied = True

        if KMS_KEY_ID:
            _sse = {'ServerSideEncryption':'aws:kms','SSEKMSKeyId':KMS_KEY_ID}
        else:
            _sse = {'ServerSideEncryption':'AES256'}
        extra_json = {'ContentType':'application/json',**_sse}
        extra_db   = {**_sse}

        con = get_db(); cur = con.cursor()
        cur.execute('SELECT id,entity_type,entity_id,operation,payload,changed_at FROM sync_queue WHERE synced_at IS NULL')
        rows = cur.fetchall()
        delta_ids = []
        if rows:
            changes = [{'op':r[3],'entity':r[1],'id':r[2],'data':json.loads(r[4]),'at':r[5]} for r in rows]
            ts = datetime.datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
            _s3_upload_bytes_with_retry(
                s3, json.dumps(changes).encode(),
                S3_BUCKET_NAME, f'changes/{DEVICE_ID}/{ts}.json',
                extra_args=extra_json)
            delta_ids = [r[0] for r in rows]
        con.close()

        ts = datetime.datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
        with open(DB,'rb') as f: db_bytes = f.read()
        if aesgcm and KEY:
            import os as _os
            nonce = _os.urandom(12)
            db_bytes = nonce + aesgcm.encrypt(nonce, db_bytes, None)
            enc_suffix = '.enc'
        else:
            enc_suffix = ''
        _s3_upload_bytes_with_retry(s3, db_bytes, S3_BUCKET_NAME, DB+enc_suffix, extra_args=extra_db)
        _s3_upload_bytes_with_retry(s3, db_bytes, S3_BUCKET_NAME, f'backups/{DB}.{ts}{enc_suffix}', extra_args=extra_db)
        logger.info(f'S3 DB backup: s3://{S3_BUCKET_NAME}/backups/{DB}.{ts}{enc_suffix}')

        if delta_ids:
            con = get_db(); cur = con.cursor()
            now = datetime.datetime.now(timezone.utc).isoformat()
            cur.execute(f"UPDATE sync_queue SET synced_at=? WHERE id IN ({','.join('?'*len(delta_ids))})", [now]+delta_ids)
            con.commit(); con.close()
        _s3_status['ok'] = True; _s3_status['error'] = None
    except Exception as e:
        _s3_status['ok'] = False; _s3_status['error'] = str(e)
        logger.error(f'S3 Sync Error: {e}')

def restore_from_s3():
    from Evernothing_DB.database import DB
    if not boto3 or os.path.exists(DB): return
    try:
        s3 = _s3_client()
        s3.download_file(S3_BUCKET_NAME, DB, DB)
        logger.info(f'Restored {DB} from S3')
    except Exception as e:
        logger.warning(f'S3 restore skipped: {e}')
