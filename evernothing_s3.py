"""
EverNothing S3 Synchronization Application
Synchronizes evernothing.db to Amazon S3 bucket

Usage:
  python evernothing_s3.py

Configuration:
  Preferred: attach an IAM role to the host (EC2 instance profile, ECS task role, etc.)
  and set only S3_BUCKET_NAME + AWS_REGION.  Long-lived access keys are supported as a
  fallback but are discouraged — use IAM roles wherever possible.

  Environment variables:
  - S3_BUCKET_NAME        (required)
  - AWS_REGION            (default: us-east-1)
  - AWS_ACCESS_KEY_ID     (optional — omit when using an IAM role)
  - AWS_SECRET_ACCESS_KEY (optional — omit when using an IAM role)
"""

import gzip, io, os, sys
import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError
from datetime import datetime

# Load .env before importing aws_config so S3_BUCKET_NAME and friends are populated
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env'))
except ImportError:
    pass

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM as _AESGCM
except ImportError:
    _AESGCM = None

try:
    from aws_config import S3_BUCKET_NAME, AWS_REGION, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, DB_FILE
except ImportError:
    S3_BUCKET_NAME        = os.environ.get('S3_BUCKET_NAME', '')
    AWS_REGION            = os.environ.get('AWS_REGION', 'us-east-1')
    # Leave as None when not set so boto3 falls through to IAM role / instance profile
    AWS_ACCESS_KEY_ID     = os.environ.get('AWS_ACCESS_KEY_ID') or None
    AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY') or None
    DB_FILE               = os.environ.get('DB_FILE', 'evernothing.db')

NUM_BACKUPS = int(os.environ.get('NUM_BACKUPS', '10'))
_SSE = {'ServerSideEncryption': 'AES256'}   # applied to every S3 put
_KEY_FILE = os.environ.get('KEY_FILE', 'secret.key')

def _encrypt_db_bytes(data: bytes) -> tuple:
    """Encrypt raw DB bytes with AES-GCM using the app's secret.key.
    Returns (ciphertext_bytes, suffix) where suffix is '.enc' on success
    or '' if encryption is unavailable (key file missing / cryptography not installed).
    Format: 12-byte nonce || AES-GCM ciphertext — matches the app's note encryption scheme.
    """
    if not _AESGCM:
        print("WARNING: cryptography not installed — uploading DB without file-level encryption")
        return data, ''
    if not os.path.exists(_KEY_FILE):
        print(f"WARNING: {_KEY_FILE} not found — uploading DB without file-level encryption")
        return data, ''
    with open(_KEY_FILE, 'rb') as f:
        key = f.read()
    aesgcm = _AESGCM(key)
    nonce = os.urandom(12)
    return nonce + aesgcm.encrypt(nonce, data, None), '.enc'

def _ensure_log_bucket(s3, log_bucket):
    """Create the logging bucket if it doesn't exist and grant log delivery."""
    try:
        s3.head_bucket(Bucket=log_bucket)
    except Exception:
        try:
            if AWS_REGION == 'us-east-1':
                s3.create_bucket(Bucket=log_bucket)
            else:
                s3.create_bucket(Bucket=log_bucket,
                    CreateBucketConfiguration={'LocationConstraint': AWS_REGION})
            s3.put_public_access_block(Bucket=log_bucket,
                PublicAccessBlockConfiguration={
                    'BlockPublicAcls': True, 'IgnorePublicAcls': True,
                    'BlockPublicPolicy': True, 'RestrictPublicBuckets': True})
        except Exception as e:
            print(f"WARNING: Could not create log bucket {log_bucket}: {e}")
            return False
    # Grant S3 log delivery write permission via bucket ACL
    try:
        s3.put_bucket_acl(Bucket=log_bucket, ACL='log-delivery-write')
    except Exception as e:
        print(f"WARNING: Could not set log-delivery-write ACL on {log_bucket}: {e}")
    return True

def _enable_access_logging(s3, bucket):
    """Enable S3 server access logging (fix #13). Logs go to <bucket>-logs."""
    log_bucket = f"{bucket}-logs"
    if not _ensure_log_bucket(s3, log_bucket):
        return
    try:
        s3.put_bucket_logging(
            Bucket=bucket,
            BucketLoggingStatus={
                'LoggingEnabled': {
                    'TargetBucket': log_bucket,
                    'TargetPrefix': 'access-logs/'
                }
            }
        )
        print(f"Access logging enabled → s3://{log_bucket}/access-logs/")
    except Exception as e:
        print(f"WARNING: Could not enable access logging: {e}")

def _apply_bucket_policy_s3(s3, bucket_name):
    """HTTPS-only + optional IP restriction bucket policy (fixes #11/#12)."""
    import json as _json
    allowed_ips = [ip.strip() for ip in os.environ.get('S3_ALLOWED_IPS', '').split(',') if ip.strip()]
    statements = [{
        "Sid": "DenyInsecureTransport",
        "Effect": "Deny", "Principal": "*", "Action": "s3:*",
        "Resource": [f"arn:aws:s3:::{bucket_name}", f"arn:aws:s3:::{bucket_name}/*"],
        "Condition": {"Bool": {"aws:SecureTransport": "false"}}
    }]
    if allowed_ips:
        statements.append({
            "Sid": "DenyNonAllowedIPs",
            "Effect": "Deny", "Principal": "*", "Action": "s3:*",
            "Resource": [f"arn:aws:s3:::{bucket_name}", f"arn:aws:s3:::{bucket_name}/*"],
            "Condition": {"NotIpAddress": {"aws:SourceIp": allowed_ips}}
        })
    try:
        s3.put_bucket_policy(Bucket=bucket_name, Policy=_json.dumps({"Version": "2012-10-17", "Statement": statements}))
    except Exception as e:
        print(f"WARNING: Could not apply bucket policy: {e}")

def sync_to_s3():
    """Upload evernothing.db to S3 bucket"""

    if not S3_BUCKET_NAME:
        print("ERROR: S3_BUCKET_NAME is not configured")
        return False

    if not os.path.exists(DB_FILE):
        print(f"ERROR: Database file '{DB_FILE}' not found")
        return False

    try:
        # Build client kwargs — only pass explicit keys when provided.
        # When omitted boto3 automatically uses the IAM role / instance profile
        # credential chain, which is the preferred approach.
        client_kwargs = {'region_name': AWS_REGION}
        if AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY:
            client_kwargs['aws_access_key_id']     = AWS_ACCESS_KEY_ID
            client_kwargs['aws_secret_access_key'] = AWS_SECRET_ACCESS_KEY
        else:
            print("INFO: No explicit AWS keys — using IAM role / instance profile credentials")
        # fix #9: explicit TLS verification; set AWS_CA_BUNDLE for custom CA bundles
        client_kwargs['verify'] = os.environ.get('AWS_CA_BUNDLE') or True

        s3 = boto3.client('s3', **client_kwargs)
        
        # Check if bucket exists, create if not
        try:
            s3.head_bucket(Bucket=S3_BUCKET_NAME)
            print(f"Bucket {S3_BUCKET_NAME} exists")
        except:
            print(f"Creating bucket {S3_BUCKET_NAME}...")
            if AWS_REGION == 'us-east-1':
                s3.create_bucket(Bucket=S3_BUCKET_NAME)
            else:
                s3.create_bucket(
                    Bucket=S3_BUCKET_NAME,
                    CreateBucketConfiguration={'LocationConstraint': AWS_REGION}
                )
            # --- fix #10: apply the same hardening as setup_aws_s3.py ---
            # Block public access
            s3.put_public_access_block(
                Bucket=S3_BUCKET_NAME,
                PublicAccessBlockConfiguration={
                    'BlockPublicAcls': True, 'IgnorePublicAcls': True,
                    'BlockPublicPolicy': True, 'RestrictPublicBuckets': True
                }
            )
            # Default encryption
            s3.put_bucket_encryption(
                Bucket=S3_BUCKET_NAME,
                ServerSideEncryptionConfiguration={
                    'Rules': [{'ApplyServerSideEncryptionByDefault': {'SSEAlgorithm': 'AES256'}}]
                }
            )
            # Versioning must be enabled before Object Lock can be used
            s3.put_bucket_versioning(
                Bucket=S3_BUCKET_NAME,
                VersioningConfiguration={'Status': 'Enabled'}
            )
            # --- fix #14: Object Lock — GOVERNANCE mode so admins can still
            #     delete if needed, but accidental/malicious deletes are blocked ---
            try:
                s3.put_object_lock_configuration(
                    Bucket=S3_BUCKET_NAME,
                    ObjectLockConfiguration={
                        'ObjectLockEnabled': 'Enabled',
                        'Rule': {
                            'DefaultRetention': {
                                'Mode': 'GOVERNANCE',
                                'Days': int(os.environ.get('S3_LOCK_DAYS', '30'))
                            }
                        }
                    }
                )
                print(f"Object Lock enabled (GOVERNANCE, {os.environ.get('S3_LOCK_DAYS', '30')} days)")
            except Exception as e:
                print(f"WARNING: Could not enable Object Lock: {e}")
            # --- fix #13: server access logging ---
            _enable_access_logging(s3, S3_BUCKET_NAME)
            # HTTPS-only + optional IP restriction bucket policy
            _apply_bucket_policy_s3(s3, S3_BUCKET_NAME)
            print(f"Bucket created and hardened successfully")
        
        # Compress and upload timestamped backup
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # fix #8: encrypt DB bytes before upload so plaintext SQLite structure
        # (including unencrypted keys/metadata) is never stored in S3.
        with open(DB_FILE, 'rb') as f:
            raw_db = f.read()
        enc_db, enc_suffix = _encrypt_db_bytes(raw_db)

        # Compressed + encrypted timestamped backup
        s3_key = f"backups/{DB_FILE}.{timestamp}.gz{enc_suffix}"
        buf = io.BytesIO()
        with gzip.GzipFile(fileobj=buf, mode='wb') as gz:
            gz.write(enc_db)
        buf.seek(0)

        print(f"Uploading compressed backup to s3://{S3_BUCKET_NAME}/{s3_key}")
        s3.upload_fileobj(buf, S3_BUCKET_NAME, s3_key,
                          ExtraArgs=_SSE)

        # Also upload encrypted latest (no compression for fast restore)
        latest_key = DB_FILE + enc_suffix
        s3.upload_fileobj(io.BytesIO(enc_db), S3_BUCKET_NAME, latest_key,
                          ExtraArgs=_SSE)

        # Prune old backups, keep only the last NUM_BACKUPS
        paginator = s3.get_paginator('list_objects_v2')
        all_backups = sorted(
            [obj for page in paginator.paginate(Bucket=S3_BUCKET_NAME, Prefix=f"backups/{DB_FILE}.")
             for obj in page.get('Contents', [])],
            key=lambda o: o['LastModified']
        )
        to_delete = all_backups[:-NUM_BACKUPS] if len(all_backups) > NUM_BACKUPS else []
        if to_delete:
            s3.delete_objects(Bucket=S3_BUCKET_NAME,
                              Delete={'Objects': [{'Key': o['Key']} for o in to_delete]})
            print(f"  Pruned {len(to_delete)} old backup(s), keeping {NUM_BACKUPS}")

        print(f"Successfully uploaded to S3")
        print(f"  Bucket: {S3_BUCKET_NAME}")
        print(f"  Region: {AWS_REGION}")
        print(f"  Backup: {s3_key}")
        print(f"  Latest: {latest_key}")
        return True
        
    except (NoCredentialsError, PartialCredentialsError) as e:
        print(f"ERROR: AWS credentials not found or incomplete: {e}")
        print("Either set AWS_ACCESS_KEY_ID + AWS_SECRET_ACCESS_KEY, or attach an IAM role to this host.")
        return False
    except Exception as e:
        print(f"ERROR: S3 sync failed: {e}")
        return False

if __name__ == '__main__':
    print("=" * 50)
    print("EverNothing S3 Sync")
    print("=" * 50)
    print(f"Bucket: {S3_BUCKET_NAME}")
    print(f"Region: {AWS_REGION}")
    print(f"Database: {DB_FILE}")
    print("-" * 50)
    
    success = sync_to_s3()
    sys.exit(0 if success else 1)
