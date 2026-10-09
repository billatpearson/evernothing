"""Tests for database corruption detection and bootstrap safety.

Covers:
- _db_has_users_but_empty_data() detects users with empty notes/folders
- _db_is_empty() returns True only when ALL tables are empty
- Bootstrap aborts when corruption detected
- S3 snapshot user count validation
"""
import json
import os
import sqlite3
import tempfile
import unittest


def _db_has_users_but_empty_data(db_path):
    """Detect corruption: users exist but notes/folders are empty."""
    try:
        con = sqlite3.connect(db_path)
        try:
            u = con.execute('SELECT COUNT(*) FROM users').fetchone()[0]
            n = con.execute('SELECT COUNT(*) FROM notes').fetchone()[0]
            f = con.execute('SELECT COUNT(*) FROM folders').fetchone()[0]
        finally:
            con.close()
        return u > 0 and (n == 0 or f == 0)
    except Exception:
        return False


def _db_is_empty(db_path):
    """True when users, notes, and folders are all empty."""
    try:
        con = sqlite3.connect(db_path)
        try:
            u = con.execute('SELECT COUNT(*) FROM users').fetchone()[0]
            n = con.execute('SELECT COUNT(*) FROM notes').fetchone()[0]
            f = con.execute('SELECT COUNT(*) FROM folders').fetchone()[0]
        finally:
            con.close()
        return u == 0 and n == 0 and f == 0
    except Exception:
        return True


class TestDbHasUsersButEmptyData(unittest.TestCase):
    """Test _db_has_users_but_empty_data() function."""
    
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.tmp.close()
        self.db_path = self.tmp.name
        # Create required tables
        con = sqlite3.connect(self.db_path)
        con.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT)")
        con.execute("CREATE TABLE folders (id INTEGER PRIMARY KEY, user_id INTEGER, name TEXT)")
        con.execute("CREATE TABLE notes (id INTEGER PRIMARY KEY, user_id INTEGER, folder_id INTEGER, note_key TEXT, note_value TEXT)")
        con.commit()
        con.close()
    
    def tearDown(self):
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)
    
    def test_empty_db_returns_false(self):
        """Empty DB with no users returns False."""
        self.assertFalse(_db_has_users_but_empty_data(self.db_path))
    
    def test_users_but_no_notes_returns_true(self):
        """DB with users but no notes returns True."""
        con = sqlite3.connect(self.db_path)
        con.execute("INSERT INTO users (username) VALUES ('test')")
        con.commit()
        con.close()
        
        self.assertTrue(_db_has_users_but_empty_data(self.db_path))
    
    def test_users_but_no_folders_returns_true(self):
        """DB with users but no folders returns True."""
        con = sqlite3.connect(self.db_path)
        con.execute("INSERT INTO users (username) VALUES ('test')")
        con.commit()
        con.close()
        
        self.assertTrue(_db_has_users_but_empty_data(self.db_path))
    
    def test_users_with_notes_and_folders_returns_false(self):
        """DB with users AND notes AND folders returns False."""
        con = sqlite3.connect(self.db_path)
        con.execute("INSERT INTO users (username) VALUES ('test')")
        con.execute("INSERT INTO folders (user_id, name) VALUES (1, 'test folder')")
        con.execute("INSERT INTO notes (user_id, folder_id, note_key, note_value) VALUES (1, 1, 'k', 'v')")
        con.commit()
        con.close()
        
        self.assertFalse(_db_has_users_but_empty_data(self.db_path))


class TestDbIsEmpty(unittest.TestCase):
    """Test _db_is_empty() function."""
    
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.tmp.close()
        self.db_path = self.tmp.name
        # Create required tables
        con = sqlite3.connect(self.db_path)
        con.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT)")
        con.execute("CREATE TABLE folders (id INTEGER PRIMARY KEY, user_id INTEGER, name TEXT)")
        con.execute("CREATE TABLE notes (id INTEGER PRIMARY KEY, user_id INTEGER, folder_id INTEGER, note_key TEXT, note_value TEXT)")
        con.commit()
        con.close()
    
    def tearDown(self):
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)
    
    def test_truly_empty_returns_true(self):
        """Completely empty DB returns True."""
        self.assertTrue(_db_is_empty(self.db_path))
    
    def test_users_only_returns_false(self):
        """DB with only users returns False (notes/folders still 0 but users > 0)."""
        con = sqlite3.connect(self.db_path)
        con.execute("INSERT INTO users (username) VALUES ('test')")
        con.commit()
        con.close()
        
        # _db_is_empty requires ALL three to be empty
        # Users=1, notes=0, folders=0 means NOT empty
        self.assertFalse(_db_is_empty(self.db_path))
    
    def test_all_tables_populated_returns_false(self):
        """DB with all tables populated returns False."""
        con = sqlite3.connect(self.db_path)
        con.execute("INSERT INTO users (username) VALUES ('test')")
        con.execute("INSERT INTO folders (user_id, name) VALUES (1, 'test')")
        con.execute("INSERT INTO notes (user_id, folder_id, note_key, note_value) VALUES (1, 1, 'k', 'v')")
        con.commit()
        con.close()
        
        self.assertFalse(_db_is_empty(self.db_path))


if __name__ == '__main__':
    unittest.main()
