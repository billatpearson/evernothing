"""
migrate_encrypt.py — One-time migration to encrypt all plaintext notes.

Run this ONCE after enabling ENCRYPTION_ENABLED=true to bring existing
plaintext data into the encrypted state.

Usage:
    cd C:\\source\\ai\\evernothing\\evernothing
    python Scripts/migrate_encrypt.py

Safe to re-run — already-encrypted rows are detected and skipped.
All changes are committed in a single transaction; on any error the
DB is left unchanged.
"""
import os, sys, sqlite3, base64

# Ensure app root is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from evernothing import encrypt, decrypt, ENCRYPTION_ENABLED

# Always use DB/evernothing.db relative to the project root
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.environ.get('DB_FILE',
     os.path.join(_project_root, 'DB', 'evernothing.db'))

def is_encrypted(value: str) -> bool:
    """Return True if value looks like AES-GCM base64 ciphertext."""
    if not value:
        return True  # empty — nothing to do
    try:
        data = base64.b64decode(value)
        # AES-GCM nonce is 12 bytes; minimum ciphertext is nonce + 16-byte tag
        return len(data) >= 28
    except Exception:
        return False  # not valid base64 → plaintext

def migrate_column(cur, table, id_col, *value_cols):
    """Encrypt all plaintext values in the given columns of a table."""
    cols = ', '.join([id_col] + list(value_cols))
    cur.execute(f"SELECT {cols} FROM {table}")
    rows = cur.fetchall()
    updated = 0
    for row in rows:
        row_id = row[0]
        new_vals = {}
        for i, col in enumerate(value_cols):
            val = row[i + 1]
            if val and not is_encrypted(val):
                new_vals[col] = encrypt(val)
        if new_vals:
            set_clause = ', '.join(f"{c}=?" for c in new_vals)
            cur.execute(
                f"UPDATE {table} SET {set_clause} WHERE {id_col}=?",
                list(new_vals.values()) + [row_id]
            )
            updated += 1
    return updated, len(rows)

def main():
    if not ENCRYPTION_ENABLED:
        print("ERROR: ENCRYPTION_ENABLED is False — set it to true in .env first.")
        sys.exit(1)

    db_path = DB
    if not os.path.exists(db_path):
        print(f"ERROR: Database not found at {db_path}")
        sys.exit(1)

    print(f"Migrating: {db_path}")
    print("Creating backup before migration...")
    import shutil, datetime
    backup = db_path + f".premigration_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.bak"
    shutil.copy2(db_path, backup)
    print(f"  Backup: {backup}")

    con = sqlite3.connect(db_path)
    try:
        cur = con.cursor()

        print("\nMigrating notes...")
        u, t = migrate_column(cur, 'notes', 'id', 'note_key', 'note_value', 'description')
        print(f"  {u} of {t} rows updated")

        print("Migrating folders...")
        u, t = migrate_column(cur, 'folders', 'id', 'name')
        print(f"  {u} of {t} rows updated")

        print("Migrating note_history...")
        u, t = migrate_column(cur, 'note_history', 'id', 'note_key', 'note_value', 'description')
        print(f"  {u} of {t} rows updated")

        con.commit()
        print("\nMigration complete. All plaintext data is now encrypted.")
        print(f"Backup retained at: {backup}")
        print("You may delete the backup once you have verified the app works correctly.")

    except Exception as e:
        con.rollback()
        print(f"\nERROR: Migration failed — database unchanged. Error: {e}")
        sys.exit(1)
    finally:
        con.close()

if __name__ == '__main__':
    main()
