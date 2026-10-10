#!/usr/bin/env python
"""Test bootstrap with corrupted database (users but no notes/folders)."""
import os
import sqlite3
import tempfile

# Set up test environment
tmp = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
tmp.close()
db_path = tmp.name
os.environ['DB_FILE'] = db_path

# Create corrupted database (users exist but notes/folders are empty)
con = sqlite3.connect(db_path)
con.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT)")
con.execute("INSERT INTO users (username) VALUES ('testuser')")
con.execute("CREATE TABLE folders (id INTEGER PRIMARY KEY, user_id INTEGER, name TEXT)")
con.execute("CREATE TABLE notes (id INTEGER PRIMARY KEY, user_id INTEGER, folder_id INTEGER, note_key TEXT, note_value TEXT)")
con.commit()
con.close()

print(f"Created corrupted DB at: {db_path}")
print("Contents: 1 user, 0 notes, 0 folders")

# Import evernothing after setting DB_FILE
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Check corruption detection
from evernothing import _db_has_users_but_empty_data, _db_is_empty

print(f"\n_db_is_empty(): {_db_is_empty()}")
print(f"_db_has_users_but_empty_data(): {_db_has_users_but_empty_data()}")

# Test bootstrap
from evernothing import _bootstrap_from_s3
print(f"\n_bootstrap_from_s3() returned: {_bootstrap_from_s3()}")
print("Expected: False (bootstrap should be aborted due to corruption)")

# Cleanup
os.unlink(db_path)
print("\nTest completed!")
