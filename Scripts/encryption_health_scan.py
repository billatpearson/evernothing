"""
encryption_health_scan.py — Read-only audit of encrypted columns.

Scans every encrypted column in `notes`, `folders`, and `note_history` and
classifies each cell into one of:

  ok            — decrypts under the current SECRET_KEY to readable text
  plaintext     — value is not AES-GCM ciphertext at all (legacy plaintext)
  empty         — column is NULL or '' (skipped)
  bad-decrypt   — looks like ciphertext, but decryption fails (wrong key,
                  truncation, tampering, or stored under an old key)
  double-wrap   — decrypts once and the plaintext IS itself valid base64
                  ciphertext under the same key. This is the bug that
                  produced the corrupted note in the Develop folder.

Exit code:
  0  no problems
  1  one or more rows in bad-decrypt or double-wrap

Usage:
    python Scripts/encryption_health_scan.py            # human-readable
    python Scripts/encryption_health_scan.py --json     # machine-readable
"""
import argparse
import base64
import hashlib
import json
import os
import sqlite3
import sys

# Project root is the parent of Scripts/
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(_ROOT, '.env'))
except ImportError:
    pass

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
except ImportError:
    print('ERROR: cryptography not installed', file=sys.stderr)
    sys.exit(2)

DB_PATH = os.environ.get('DB_FILE', os.path.join(_ROOT, 'DB', 'evernothing.db'))
SECRET = os.environ.get('SECRET_KEY', '')
if not SECRET:
    print('ERROR: SECRET_KEY not set in environment', file=sys.stderr)
    sys.exit(2)

KEY = hashlib.pbkdf2_hmac('sha256', SECRET.encode('utf-8'),
                          b'evernothing-aes-key-v1', iterations=100_000, dklen=32)
aesgcm = AESGCM(KEY)


def looks_like_ciphertext(value):
    """Cheap structural check — value is base64 of >=28 bytes (12 nonce + 16 tag)."""
    if not value:
        return False
    try:
        data = base64.b64decode(value, validate=True)
    except Exception:
        return False
    return len(data) >= 28


def try_decrypt(value):
    """Return (plaintext, error). plaintext is None on failure."""
    try:
        data = base64.b64decode(value)
        return aesgcm.decrypt(data[:12], data[12:], None).decode('utf-8'), None
    except Exception as e:
        return None, type(e).__name__


def classify(value):
    """Return (status, plaintext_or_None, detail_or_None)."""
    if not value:
        return 'empty', None, None
    if not looks_like_ciphertext(value):
        return 'plaintext', value, None
    plain, err = try_decrypt(value)
    if err:
        return 'bad-decrypt', None, err
    # Decrypt succeeded — check if the plaintext is itself ciphertext.
    if looks_like_ciphertext(plain):
        plain2, err2 = try_decrypt(plain)
        if not err2:
            # Double-wrapped under the same key — this is the bug.
            return 'double-wrap', plain2, None
        # Plaintext just looks base64-ish but isn't real inner ciphertext.
        # That's fine — many real strings are coincidentally valid base64.
    return 'ok', plain, None


def scan_table(con, table, id_col, columns):
    """Return list of (table, id, column, status, detail) for non-ok cells."""
    cur = con.cursor()
    select_cols = ', '.join([id_col] + list(columns))
    cur.execute(f'SELECT {select_cols} FROM {table}')
    rows = cur.fetchall()
    findings = []
    counts = {k: 0 for k in ('ok', 'empty', 'plaintext', 'bad-decrypt', 'double-wrap')}
    for row in rows:
        rid = row[0]
        for i, col in enumerate(columns):
            value = row[i + 1]
            status, _, detail = classify(value)
            counts[status] = counts.get(status, 0) + 1
            if status in ('bad-decrypt', 'double-wrap', 'plaintext'):
                findings.append({
                    'table': table, 'id': rid, 'column': col,
                    'status': status, 'detail': detail,
                })
    return findings, counts


def main():
    ap = argparse.ArgumentParser(description='Encryption health scan')
    ap.add_argument('--json', action='store_true', help='Emit JSON output')
    ap.add_argument('--db', default=DB_PATH, help=f'DB path (default: {DB_PATH})')
    args = ap.parse_args()

    if not os.path.exists(args.db):
        print(f'ERROR: DB not found at {args.db}', file=sys.stderr)
        sys.exit(2)

    con = sqlite3.connect(args.db)
    try:
        targets = [
            ('notes',        'id', ('note_key', 'note_value', 'description')),
            ('folders',      'id', ('name',)),
            ('note_history', 'id', ('note_key', 'note_value', 'description')),
        ]
        all_findings = []
        all_counts = {}
        for table, id_col, cols in targets:
            findings, counts = scan_table(con, table, id_col, cols)
            all_findings.extend(findings)
            all_counts[table] = counts
    finally:
        con.close()

    if args.json:
        print(json.dumps({
            'db':       args.db,
            'counts':   all_counts,
            'findings': all_findings,
        }, indent=2, default=str))
    else:
        print('=' * 70)
        print(f'Encryption health scan: {args.db}')
        print('=' * 70)
        for table, counts in all_counts.items():
            total = sum(counts.values())
            ok = counts.get('ok', 0)
            print(f"{table:>14}  {total:>4} cells  "
                  f"ok={ok}  "
                  f"plain={counts.get('plaintext', 0)}  "
                  f"bad-decrypt={counts.get('bad-decrypt', 0)}  "
                  f"double-wrap={counts.get('double-wrap', 0)}  "
                  f"empty={counts.get('empty', 0)}")
        print()
        if not all_findings:
            print('No issues found.')
        else:
            print(f'Found {len(all_findings)} cell(s) needing attention:')
            print()
            for f in all_findings:
                detail = f' ({f["detail"]})' if f['detail'] else ''
                print(f"  [{f['status']:>11}] {f['table']}#{f['id']} {f['column']}{detail}")

    bad = [f for f in all_findings if f['status'] in ('bad-decrypt', 'double-wrap')]
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
