"""
s3_inspector.py — S3 Account Inspector
=======================================
Lists all S3 buckets on the account and displays their contents,
sizes, storage classes, and totals.

Usage:
    python s3_inspector.py                  # all buckets
    python s3_inspector.py --bucket NAME    # one bucket
    python s3_inspector.py --prefix backups/# filter by prefix
    python s3_inspector.py --summary        # totals only, no file listing

Reads credentials from .env or environment variables:
    AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION, AWS_PROFILE
"""

import os, sys, argparse
from datetime import timezone

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError
except ImportError:
    print("ERROR: boto3 not installed. Run: pip install boto3")
    sys.exit(1)

# --- Credentials ---
AWS_ACCESS_KEY_ID     = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
AWS_REGION            = os.environ.get('AWS_REGION', 'us-east-1')
AWS_PROFILE           = os.environ.get('AWS_PROFILE', 'billspeiser2')


def _s3():
    if AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY:
        return boto3.client('s3',
            region_name=AWS_REGION,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
    try:
        return boto3.Session(profile_name=AWS_PROFILE).client('s3')
    except Exception:
        return boto3.client('s3', region_name=AWS_REGION)


def _fmt_size(n):
    for unit in ('B', 'KB', 'MB', 'GB', 'TB'):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} PB"


def _bucket_region(s3, name):
    try:
        r = s3.get_bucket_location(Bucket=name)
        return r['LocationConstraint'] or 'us-east-1'
    except ClientError:
        return 'unknown'


def _list_objects(s3, bucket, prefix=''):
    """Paginate through all objects in a bucket, yielding each object dict."""
    paginator = s3.get_paginator('list_objects_v2')
    kwargs = {'Bucket': bucket}
    if prefix:
        kwargs['Prefix'] = prefix
    for page in paginator.paginate(**kwargs):
        for obj in page.get('Contents', []):
            yield obj


def inspect_bucket(s3, name, prefix='', summary_only=False):
    print(f"\n{'='*70}")
    print(f"  Bucket : s3://{name}")
    print(f"  Region : {_bucket_region(s3, name)}")
    print(f"{'='*70}")

    objects = list(_list_objects(s3, name, prefix))

    if not objects:
        print("  (empty)")
        return 0, 0

    total_size  = sum(o['Size'] for o in objects)
    total_count = len(objects)

    if not summary_only:
        # Group by top-level prefix (folder)
        groups = {}
        for obj in objects:
            key   = obj['Key']
            parts = key.split('/', 1)
            grp   = parts[0] + '/' if len(parts) > 1 else '(root)'
            groups.setdefault(grp, []).append(obj)

        for grp in sorted(groups):
            grp_objects = groups[grp]
            grp_size    = sum(o['Size'] for o in grp_objects)
            print(f"\n  [{grp}]  {len(grp_objects)} object(s)  {_fmt_size(grp_size)}")
            print(f"  {'Key':<55} {'Size':>10}  {'Modified (UTC)':<20}  Storage")
            print(f"  {'-'*55} {'-'*10}  {'-'*20}  -------")
            for obj in sorted(grp_objects, key=lambda o: o['LastModified'], reverse=True):
                mod = obj['LastModified'].strftime('%Y-%m-%d %H:%M:%S')
                sc  = obj.get('StorageClass', 'STANDARD')
                print(f"  {obj['Key']:<55} {_fmt_size(obj['Size']):>10}  {mod:<20}  {sc}")

    print(f"\n  TOTAL: {total_count} object(s)  {_fmt_size(total_size)}")
    return total_count, total_size


def main():
    parser = argparse.ArgumentParser(description="S3 Account Inspector")
    parser.add_argument('--bucket',  help='Inspect a single bucket by name')
    parser.add_argument('--prefix',  default='', help='Filter objects by key prefix')
    parser.add_argument('--summary', action='store_true', help='Show totals only, no file listing')
    args = parser.parse_args()

    try:
        s3 = _s3()
        buckets = s3.list_buckets().get('Buckets', [])
    except NoCredentialsError:
        print("ERROR: No AWS credentials found.")
        print("Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY in your .env file.")
        sys.exit(1)
    except ClientError as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    if not buckets:
        print("No buckets found on this account.")
        sys.exit(0)

    # Filter to single bucket if requested
    if args.bucket:
        buckets = [b for b in buckets if b['Name'] == args.bucket]
        if not buckets:
            print(f"Bucket '{args.bucket}' not found on this account.")
            sys.exit(1)

    print(f"\n{'='*70}")
    print(f"  AWS S3 Account Inspector")
    print(f"  Account buckets found: {len(buckets)}")
    print(f"{'='*70}")
    for b in sorted(buckets, key=lambda x: x['Name']):
        created = b['CreationDate'].strftime('%Y-%m-%d')
        print(f"  {b['Name']:<45} created {created}")

    grand_count = 0
    grand_size  = 0
    for b in sorted(buckets, key=lambda x: x['Name']):
        try:
            c, s = inspect_bucket(s3, b['Name'], prefix=args.prefix, summary_only=args.summary)
            grand_count += c
            grand_size  += s
        except ClientError as e:
            print(f"\n  s3://{b['Name']} — access error: {e}")

    print(f"\n{'='*70}")
    print(f"  GRAND TOTAL: {grand_count} object(s)  {_fmt_size(grand_size)}  across {len(buckets)} bucket(s)")
    print(f"{'='*70}\n")


if __name__ == '__main__':
    main()
