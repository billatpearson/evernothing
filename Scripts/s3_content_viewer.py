"""
s3_content_viewer.py — S3 Bucket Content Viewer
=================================================
Lists all S3 buckets and displays the actual contents of each file.
Encrypted .enc / .bin files are decrypted using secret.key.
JSON files are pretty-printed. SQLite DB files show table/row counts.
Binary files show a hex dump preview.

Usage:
    python s3_content_viewer.py                        # all buckets, all files
    python s3_content_viewer.py --bucket NAME          # one bucket
    python s3_content_viewer.py --prefix backups/      # filter by prefix
    python s3_content_viewer.py --key path/to/file.enc # single file
    python s3_content_viewer.py --no-content           # listing only, no content
    python s3_content_viewer.py --max-size 512         # skip files larger than N KB

Reads from .env:
    AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION
    SECRET_KEY_FILE  (path to secret.key, default: secret.key)
"""

import os, sys, json, hashlib, argparse, tempfile, sqlite3

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError
except ImportError:
    print("ERROR: boto3 not installed.  pip install boto3")
    sys.exit(1)

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    _HAVE_CRYPTO = True
except ImportError:
    _HAVE_CRYPTO = False

# ── credentials ──────────────────────────────────────────────────────────────
AWS_ACCESS_KEY_ID     = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
AWS_REGION            = os.environ.get('AWS_REGION', 'us-east-1')
AWS_PROFILE           = os.environ.get('AWS_PROFILE', 'billspeiser2')
KEY_FILE              = os.environ.get('SECRET_KEY_FILE', 'secret.key')

# ── helpers ───────────────────────────────────────────────────────────────────
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


def _load_aesgcm():
    if not _HAVE_CRYPTO:
        return None
    if not os.path.exists(KEY_FILE):
        return None
    with open(KEY_FILE, 'rb') as f:
        return AESGCM(f.read())


def _fmt_size(n):
    for unit in ('B', 'KB', 'MB', 'GB'):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"


def _decrypt(aesgcm, data: bytes) -> bytes:
    """AES-256-GCM decrypt with embedded SHA-256 integrity check."""
    nonce, ct = data[:12], data[12:]
    plain = aesgcm.decrypt(nonce, ct, None)
    stored, original = plain[:32], plain[32:]
    if hashlib.sha256(original).digest() != stored:
        raise ValueError("SHA-256 integrity check FAILED")
    return original


def _hex_preview(data: bytes, width=16, rows=8) -> str:
    lines = []
    for i in range(0, min(len(data), width * rows), width):
        chunk = data[i:i+width]
        hex_part = ' '.join(f'{b:02x}' for b in chunk)
        asc_part = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
        lines.append(f"  {i:06x}  {hex_part:<{width*3}}  {asc_part}")
    if len(data) > width * rows:
        lines.append(f"  ... ({len(data):,} bytes total)")
    return '\n'.join(lines)


def _sqlite_summary(data: bytes) -> str:
    """Write bytes to a temp file, open as SQLite, return table/row summary."""
    lines = []
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        tmp.write(data)
        tmp_path = tmp.name
    try:
        con = sqlite3.connect(tmp_path)
        cur = con.cursor()
        tables = [r[0] for r in cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()]
        lines.append(f"  SQLite database - {len(tables)} table(s)")
        for tbl in tables:
            try:
                count = cur.execute(f"SELECT COUNT(*) FROM [{tbl}]").fetchone()[0]
                cols  = [d[0] for d in cur.execute(f"SELECT * FROM [{tbl}] LIMIT 0").description or []]
                lines.append(f"    {tbl:<30} {count:>6} row(s)   cols: {', '.join(cols)}")
            except Exception as e:
                lines.append(f"    {tbl:<30} (error: {e})")
        con.close()
    except Exception as e:
        lines.append(f"  (could not open as SQLite: {e})")
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
    return '\n'.join(lines)


def _render_content(key: str, data: bytes, aesgcm) -> str:
    """Return a human-readable string for the contents of an S3 object."""
    ext = key.rsplit('.', 1)[-1].lower() if '.' in key else ''

    # ── encrypted payloads ────────────────────────────────────────────────────
    if ext in ('enc', 'bin'):
        if not aesgcm:
            return "  [encrypted — secret.key not available for decryption]"
        try:
            plain = _decrypt(aesgcm, data)
            tag   = "SHA-256 integrity: VERIFIED ✓"
        except Exception as e:
            return f"  [decryption failed: {e}]"

        # DB backup (.enc)
        if ext == 'enc' or plain[:16] == b'SQLite format 3\x00':
            return f"  {tag}\n" + _sqlite_summary(plain)

        # Delta JSON (.bin)
        try:
            changes = json.loads(plain.decode('utf-8'))
            out = [f"  {tag}  --  {len(changes)} change record(s)"]
            for i, c in enumerate(changes[:20]):   # cap at 20 records
                out.append(f"\n  [{i+1}] op={c.get('op')}  entity={c.get('entity')}  "
                            f"id={c.get('id')}  at={c.get('at')}")
                data_preview = c.get('data', {})
                for k, v in list(data_preview.items())[:6]:
                    val = str(v)[:80] + ('...' if len(str(v)) > 80 else '')
                    out.append(f"       {k}: {val}")
            if len(changes) > 20:
                out.append(f"\n  ... {len(changes)-20} more record(s) not shown")
            return '\n'.join(out)
        except Exception:
            return f"  {tag}\n" + _hex_preview(plain)

    # ── plain JSON ────────────────────────────────────────────────────────────
    if ext == 'json' or data[:1] in (b'{', b'['):
        try:
            parsed = json.loads(data.decode('utf-8'))
            pretty = json.dumps(parsed, indent=2)
            lines  = pretty.splitlines()
            cap    = 60
            out    = '\n'.join('  ' + l for l in lines[:cap])
            if len(lines) > cap:
                out += f"\n  ... ({len(lines)-cap} more lines)"
            return out
        except Exception:
            pass

    # ── SQLite DB (unencrypted) ───────────────────────────────────────────────
    if data[:16] == b'SQLite format 3\x00':
        return _sqlite_summary(data)

    # ── plain text ────────────────────────────────────────────────────────────
    if ext in ('txt', 'log', 'csv', 'md', 'sh', 'py', 'ini', 'cfg'):
        try:
            text  = data.decode('utf-8', errors='replace')
            lines = text.splitlines()
            cap   = 40
            out   = '\n'.join('  ' + l for l in lines[:cap])
            if len(lines) > cap:
                out += f"\n  ... ({len(lines)-cap} more lines)"
            return out
        except Exception:
            pass

    # ── fallback: hex preview ─────────────────────────────────────────────────
    return _hex_preview(data)


# ── core display ──────────────────────────────────────────────────────────────
def show_object(s3, bucket: str, key: str, aesgcm, show_content: bool, max_bytes: int):
    obj      = s3.get_object(Bucket=bucket, Key=key)
    size     = obj['ContentLength']
    modified = obj['LastModified'].strftime('%Y-%m-%d %H:%M:%S UTC')
    sc       = obj.get('StorageClass', 'STANDARD')

    print(f"\n  +- {key}")
    print(f"  |  Size: {_fmt_size(size)}   Modified: {modified}   Storage: {sc}")

    if not show_content:
        print(f"  +- (content display disabled)")
        return

    if size > max_bytes:
        print(f"  +- (skipped -- {_fmt_size(size)} exceeds --max-size limit)")
        return

    data    = obj['Body'].read()
    content = _render_content(key, data, aesgcm)
    print(f"  |")
    for line in content.splitlines():
        print(f"  |  {line}")
    print(f"  +- end of {os.path.basename(key)}")


def inspect_bucket(s3, name: str, aesgcm, prefix: str,
                   show_content: bool, max_bytes: int):
    print(f"\n{'='*70}")
    print(f"  Bucket: s3://{name}")
    print(f"{'='*70}")

    paginator = s3.get_paginator('list_objects_v2')
    kwargs    = {'Bucket': name}
    if prefix:
        kwargs['Prefix'] = prefix

    total_count = total_size = 0
    for page in paginator.paginate(**kwargs):
        for obj in page.get('Contents', []):
            total_count += 1
            total_size  += obj['Size']
            try:
                show_object(s3, name, obj['Key'], aesgcm, show_content, max_bytes)
            except ClientError as e:
                print(f"\n  [error reading {obj['Key']}]: {e}")

    if total_count == 0:
        print("  (empty)")
    else:
        print(f"\n  BUCKET TOTAL: {total_count} object(s)  {_fmt_size(total_size)}")

    return total_count, total_size


# ── entry point ───────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="S3 Bucket Content Viewer")
    parser.add_argument('--bucket',     help='Inspect a single bucket')
    parser.add_argument('--prefix',     default='', help='Filter by key prefix')
    parser.add_argument('--key',        help='Display a single object by full key')
    parser.add_argument('--no-content', action='store_true', help='List only, no content')
    parser.add_argument('--max-size',   type=int, default=10240,
                        help='Skip files larger than N KB (default: 10240 = 10 MB)')
    args = parser.parse_args()

    max_bytes = args.max_size * 1024

    try:
        s3      = _s3()
        aesgcm  = _load_aesgcm()
        buckets = s3.list_buckets().get('Buckets', [])
    except NoCredentialsError:
        print("ERROR: No AWS credentials found. Set AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY.")
        sys.exit(1)
    except ClientError as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    if not aesgcm:
        print(f"  NOTE: {KEY_FILE} not found — encrypted files will not be decrypted.\n")

    # Single object mode
    if args.key:
        bucket = args.bucket or buckets[0]['Name']
        show_object(s3, bucket, args.key, aesgcm, show_content=True, max_bytes=max_bytes)
        return

    if args.bucket:
        buckets = [b for b in buckets if b['Name'] == args.bucket]
        if not buckets:
            print(f"Bucket '{args.bucket}' not found.")
            sys.exit(1)

    print(f"\n{'='*70}")
    print(f"  AWS S3 Content Viewer  --  {len(buckets)} bucket(s) found")
    print(f"{'='*70}")
    for b in sorted(buckets, key=lambda x: x['Name']):
        print(f"  {b['Name']:<50} created {b['CreationDate'].strftime('%Y-%m-%d')}")

    grand_count = grand_size = 0
    for b in sorted(buckets, key=lambda x: x['Name']):
        try:
            c, s = inspect_bucket(s3, b['Name'], aesgcm,
                                  prefix=args.prefix,
                                  show_content=not args.no_content,
                                  max_bytes=max_bytes)
            grand_count += c
            grand_size  += s
        except ClientError as e:
            print(f"\n  s3://{b['Name']} -- access error: {e}")

    print(f"\n{'='*70}")
    print(f"  GRAND TOTAL: {grand_count} object(s)  {_fmt_size(grand_size)}"
          f"  across {len(buckets)} bucket(s)")
    print(f"{'='*70}\n")


if __name__ == '__main__':
    main()
