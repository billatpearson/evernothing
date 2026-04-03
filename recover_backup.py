"""
recover_backup.py — Secure Device Recovery Tool
================================================
Downloads, decrypts, and SHA-256 verifies encrypted backups and
delta change files from S3.

All files in S3 are AES-256-GCM encrypted with a prepended SHA-256
integrity hash. This tool requires the original secret.key file.

Usage:
    # List available backups
    python recover_backup.py list

    # Recover latest DB backup to a local file
    python recover_backup.py recover-db

    # Recover a specific DB backup
    python recover_backup.py recover-db --key backups/evernothing.db.20260402_120000.enc

    # Recover and print all delta change files as JSON
    python recover_backup.py recover-deltas

    # Recover deltas from a specific device
    python recover_backup.py recover-deltas --device myhostname

Configuration (env vars or .env file):
    SECRET_KEY_FILE   path to secret.key  (default: secret.key)
    S3_BUCKET_NAME    S3 bucket           (default: evernothing-backup-2026)
    AWS_REGION        AWS region          (default: us-east-1)
    AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY
"""

import os, sys, json, hashlib, argparse
from datetime import timezone

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    import boto3
except ImportError:
    print("ERROR: boto3 not installed. Run: pip install boto3")
    sys.exit(1)

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
except ImportError:
    print("ERROR: cryptography not installed. Run: pip install cryptography")
    sys.exit(1)


# --- Configuration ---
KEY_FILE      = os.environ.get('SECRET_KEY_FILE', 'secret.key')
BUCKET        = os.environ.get('S3_BUCKET_NAME', 'evernothing-backup-2026')
REGION        = os.environ.get('AWS_REGION', 'us-east-1')
ACCESS_KEY    = os.environ.get('AWS_ACCESS_KEY_ID')
SECRET_KEY    = os.environ.get('AWS_SECRET_ACCESS_KEY')
DB_FILE       = os.environ.get('DB_FILE', 'evernothing.db')


def _load_key() -> AESGCM:
    if not os.path.exists(KEY_FILE):
        print(f"ERROR: Key file '{KEY_FILE}' not found. Copy it from the server.")
        sys.exit(1)
    with open(KEY_FILE, 'rb') as f:
        return AESGCM(f.read())


def _s3():
    kwargs = {'region_name': REGION}
    if ACCESS_KEY and SECRET_KEY:
        kwargs['aws_access_key_id']     = ACCESS_KEY
        kwargs['aws_secret_access_key'] = SECRET_KEY
    return boto3.client('s3', **kwargs)


def decrypt_payload(aesgcm: AESGCM, data: bytes) -> bytes:
    """
    Decrypt AES-256-GCM payload and verify embedded SHA-256 hash.
    Format on disk: nonce(12) | AES-GCM( sha256(plaintext)(32) | plaintext )
    Raises ValueError if integrity check fails.
    """
    nonce, ciphertext = data[:12], data[12:]
    plaintext = aesgcm.decrypt(nonce, ciphertext, None)
    stored_digest, original = plaintext[:32], plaintext[32:]
    actual_digest = hashlib.sha256(original).digest()
    if stored_digest != actual_digest:
        raise ValueError("SHA-256 integrity check FAILED — file may be corrupted or tampered.")
    return original


def cmd_list(args):
    s3 = _s3()
    print(f"\nBucket: s3://{BUCKET}\n")

    print("=== DB Backups ===")
    resp = s3.list_objects_v2(Bucket=BUCKET, Prefix='backups/')
    backups = sorted(resp.get('Contents', []), key=lambda o: o['LastModified'], reverse=True)
    for obj in backups:
        size_kb = obj['Size'] / 1024
        print(f"  {obj['Key']:<60} {size_kb:>8.1f} KB  {obj['LastModified'].strftime('%Y-%m-%d %H:%M:%S UTC')}")
    if not backups:
        print("  (none)")

    print("\n=== Delta Changes ===")
    resp = s3.list_objects_v2(Bucket=BUCKET, Prefix='changes/')
    deltas = sorted(resp.get('Contents', []), key=lambda o: o['LastModified'], reverse=True)
    for obj in deltas:
        size_kb = obj['Size'] / 1024
        print(f"  {obj['Key']:<60} {size_kb:>8.1f} KB  {obj['LastModified'].strftime('%Y-%m-%d %H:%M:%S UTC')}")
    if not deltas:
        print("  (none)")


def cmd_recover_db(args):
    aesgcm = _load_key()
    s3 = _s3()

    key = args.key
    if not key:
        # Find latest backup
        resp = s3.list_objects_v2(Bucket=BUCKET, Prefix='backups/')
        backups = sorted(resp.get('Contents', []), key=lambda o: o['LastModified'], reverse=True)
        if not backups:
            print("No backups found in S3.")
            sys.exit(1)
        key = backups[0]['Key']

    print(f"Downloading: s3://{BUCKET}/{key}")
    obj = s3.get_object(Bucket=BUCKET, Key=key)
    encrypted = obj['Body'].read()
    print(f"  Downloaded {len(encrypted):,} bytes (encrypted)")

    plaintext = decrypt_payload(aesgcm, encrypted)
    print(f"  Decrypted  {len(plaintext):,} bytes")
    print(f"  SHA-256 integrity: VERIFIED ✓")

    out_file = args.output or f"recovered_{os.path.basename(key).replace('.enc', '')}"
    with open(out_file, 'wb') as f:
        f.write(plaintext)
    print(f"  Saved to: {out_file}")
    print(f"\nTo use: set DB_FILE={out_file} and restart the app.")


def cmd_recover_deltas(args):
    aesgcm = _load_key()
    s3 = _s3()

    prefix = f"changes/{args.device}/" if args.device else "changes/"
    resp = s3.list_objects_v2(Bucket=BUCKET, Prefix=prefix)
    deltas = sorted(resp.get('Contents', []), key=lambda o: o['LastModified'])

    if not deltas:
        print(f"No delta files found under s3://{BUCKET}/{prefix}")
        sys.exit(0)

    all_changes = []
    for obj in deltas:
        print(f"Processing: {obj['Key']}")
        encrypted = s3.get_object(Bucket=BUCKET, Key=obj['Key'])['Body'].read()
        try:
            plaintext = decrypt_payload(aesgcm, encrypted)
            changes = json.loads(plaintext.decode('utf-8'))
            all_changes.extend(changes)
            print(f"  {len(changes)} change(s) — SHA-256 integrity: VERIFIED ✓")
        except ValueError as e:
            print(f"  ERROR: {e}")
        except Exception as e:
            print(f"  ERROR decrypting {obj['Key']}: {e}")

    out_file = args.output or "recovered_deltas.json"
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump(all_changes, f, indent=2)
    print(f"\nTotal: {len(all_changes)} change(s) written to {out_file}")


def main():
    parser = argparse.ArgumentParser(description="EverNothing Secure Backup Recovery Tool")
    sub = parser.add_subparsers(dest='cmd', required=True)

    sub.add_parser('list', help='List all backups and deltas in S3')

    p_db = sub.add_parser('recover-db', help='Download and decrypt a DB backup')
    p_db.add_argument('--key', help='S3 key of backup to recover (default: latest)')
    p_db.add_argument('--output', '-o', help='Output filename')

    p_delta = sub.add_parser('recover-deltas', help='Download and decrypt all delta change files')
    p_delta.add_argument('--device', help='Filter by device/hostname prefix')
    p_delta.add_argument('--output', '-o', help='Output JSON filename (default: recovered_deltas.json)')

    args = parser.parse_args()
    {'list': cmd_list, 'recover-db': cmd_recover_db, 'recover-deltas': cmd_recover_deltas}[args.cmd](args)


if __name__ == '__main__':
    main()
