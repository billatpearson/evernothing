"""
test_s3_transfer.py — S3 data transfer tests updated for current evernothing_s3 API.
Uses upload_fileobj (not upload_file) and requires S3_BUCKET_NAME to be set.
"""
import os, sqlite3, sys, tempfile, unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import evernothing_s3

BUCKET = 'test-transfer-bucket'

class TestS3DataTransfer(unittest.TestCase):

    def setUp(self):
        self.test_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.test_db.close()
        self.db_path = self.test_db.name
        with sqlite3.connect(self.db_path) as con:
            con.executescript("""
                CREATE TABLE users(id INTEGER, username TEXT, password TEXT);
                CREATE TABLE notes(id INTEGER, user_id INTEGER, note_key TEXT, note_value TEXT);
                INSERT INTO users VALUES(1, 'testuser', 'hash123');
                INSERT INTO notes VALUES(1, 1, 'Test Note', 'Test Content');
            """)
        evernothing_s3.DB_FILE          = self.db_path
        evernothing_s3.S3_BUCKET_NAME   = BUCKET
        evernothing_s3.AWS_ACCESS_KEY_ID     = 'test_key'
        evernothing_s3.AWS_SECRET_ACCESS_KEY = 'test_secret'

    def tearDown(self):
        try: os.unlink(self.db_path)
        except OSError: pass

    def _mock_s3(self):
        mock_s3 = MagicMock()
        mock_s3.head_bucket.return_value = {}
        mock_s3.get_paginator.return_value.paginate.return_value = []
        return mock_s3

    @patch('evernothing_s3.boto3.client')
    def test_transfer_database_to_s3(self, mock_boto):
        """sync_to_s3 returns True and calls upload_fileobj."""
        mock_boto.return_value = self._mock_s3()
        result = evernothing_s3.sync_to_s3()
        self.assertTrue(result)
        self.assertGreaterEqual(mock_boto.return_value.upload_fileobj.call_count, 1)

    @patch('evernothing_s3.boto3.client')
    def test_transfer_to_correct_bucket(self, mock_boto):
        """Uploads go to the configured bucket."""
        mock_s3 = self._mock_s3()
        mock_boto.return_value = mock_s3
        evernothing_s3.sync_to_s3()
        for c in mock_s3.upload_fileobj.call_args_list:
            self.assertEqual(c[0][1], BUCKET)

    @patch('evernothing_s3.boto3.client')
    def test_transfer_creates_backup_and_latest(self, mock_boto):
        """Creates both a timestamped backup and a latest copy."""
        mock_s3 = self._mock_s3()
        mock_boto.return_value = mock_s3
        evernothing_s3.sync_to_s3()
        keys = [c[0][2] for c in mock_s3.upload_fileobj.call_args_list]
        self.assertTrue(any('backups/' in k for k in keys), "No backup key found")
        self.assertTrue(any('backups/' not in k for k in keys), "No latest key found")

    @patch('evernothing_s3.boto3.client')
    def test_transfer_file_exists(self, mock_boto):
        """sync_to_s3 succeeds when DB file exists and has data."""
        mock_boto.return_value = self._mock_s3()
        self.assertTrue(os.path.exists(self.db_path))
        self.assertGreater(os.path.getsize(self.db_path), 0)
        self.assertTrue(evernothing_s3.sync_to_s3())

    @patch('evernothing_s3.boto3.client')
    def test_transfer_with_data_integrity(self, mock_boto):
        """DB data is unchanged after sync_to_s3."""
        mock_boto.return_value = self._mock_s3()
        with sqlite3.connect(self.db_path) as con:
            before = (
                con.execute("SELECT COUNT(*) FROM users").fetchone()[0],
                con.execute("SELECT COUNT(*) FROM notes").fetchone()[0]
            )
        evernothing_s3.sync_to_s3()
        with sqlite3.connect(self.db_path) as con:
            after = (
                con.execute("SELECT COUNT(*) FROM users").fetchone()[0],
                con.execute("SELECT COUNT(*) FROM notes").fetchone()[0]
            )
        self.assertEqual(before, after)

if __name__ == '__main__':
    unittest.main(verbosity=2)
