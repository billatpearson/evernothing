import unittest
import os
import tempfile
import sqlite3
from unittest.mock import patch, MagicMock, call
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import evernothing_s3

class TestS3DataTransfer(unittest.TestCase):
    
    def setUp(self):
        # Create test database with actual data
        self.test_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.test_db.close()
        self.db_path = self.test_db.name
        
        # Populate with test data
        con = sqlite3.connect(self.db_path)
        cur = con.cursor()
        cur.executescript("""
            CREATE TABLE users(id INTEGER, username TEXT, password TEXT);
            CREATE TABLE notes(id INTEGER, user_id INTEGER, note_key TEXT, note_value TEXT);
            INSERT INTO users VALUES(1, 'testuser', 'hash123');
            INSERT INTO notes VALUES(1, 1, 'Test Note', 'Test Content');
        """)
        con.commit()
        con.close()
        
        os.environ['DB_FILE'] = self.db_path
        os.environ['AWS_ACCESS_KEY_ID'] = 'test_key'
        os.environ['AWS_SECRET_ACCESS_KEY'] = 'test_secret'
        evernothing_s3.DB_FILE = self.db_path
        evernothing_s3.AWS_ACCESS_KEY_ID = 'test_key'
        evernothing_s3.AWS_SECRET_ACCESS_KEY = 'test_secret'
    
    def tearDown(self):
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)
    
    @patch('evernothing_s3.boto3.client')
    def test_transfer_database_to_s3(self, mock_boto):
        """Test actual database file is transferred to S3"""
        mock_s3 = MagicMock()
        mock_boto.return_value = mock_s3
        
        result = evernothing_s3.sync_to_s3()
        
        # Verify success
        self.assertTrue(result)
        
        # Verify S3 client created with correct credentials
        mock_boto.assert_called_once_with(
            's3',
            region_name='us-east-1',
            aws_access_key_id='test_key',
            aws_secret_access_key='test_secret'
        )
        
        # Verify upload_file called twice (backup + latest)
        self.assertEqual(mock_s3.upload_file.call_count, 2)
        
        # Verify correct file path used
        calls = mock_s3.upload_file.call_args_list
        self.assertEqual(calls[0][0][0], self.db_path)  # First arg is local file
        self.assertEqual(calls[1][0][0], self.db_path)  # Second upload also uses same file
    
    @patch('evernothing_s3.boto3.client')
    def test_transfer_to_correct_bucket(self, mock_boto):
        """Test data transferred to correct S3 bucket"""
        mock_s3 = MagicMock()
        mock_boto.return_value = mock_s3
        
        result = evernothing_s3.sync_to_s3()
        
        # Verify bucket name
        calls = mock_s3.upload_file.call_args_list
        self.assertEqual(calls[0][0][1], 'evernothing03032026')  # Backup upload
        self.assertEqual(calls[1][0][1], 'evernothing03032026')  # Latest upload
    
    @patch('evernothing_s3.boto3.client')
    def test_transfer_creates_backup_and_latest(self, mock_boto):
        """Test transfer creates both timestamped backup and latest copy"""
        mock_s3 = MagicMock()
        mock_boto.return_value = mock_s3
        
        result = evernothing_s3.sync_to_s3()
        
        calls = mock_s3.upload_file.call_args_list
        
        # First call should be backup with timestamp
        backup_key = calls[0][0][2]
        self.assertTrue(backup_key.startswith('backups/'))
        self.assertIn('.db.', backup_key)
        
        # Second call should be latest
        latest_key = calls[1][0][2]
        self.assertEqual(latest_key, self.db_path)
    
    @patch('evernothing_s3.boto3.client')
    def test_transfer_file_exists(self, mock_boto):
        """Test transfer verifies file exists before upload"""
        mock_s3 = MagicMock()
        mock_boto.return_value = mock_s3
        
        # Verify file exists
        self.assertTrue(os.path.exists(self.db_path))
        
        # Verify file has data
        file_size = os.path.getsize(self.db_path)
        self.assertGreater(file_size, 0)
        
        result = evernothing_s3.sync_to_s3()
        self.assertTrue(result)
    
    @patch('evernothing_s3.boto3.client')
    def test_transfer_with_data_integrity(self, mock_boto):
        """Test database data integrity during transfer"""
        mock_s3 = MagicMock()
        mock_boto.return_value = mock_s3
        
        # Read data before transfer
        con = sqlite3.connect(self.db_path)
        cur = con.cursor()
        cur.execute("SELECT COUNT(*) FROM users")
        user_count_before = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM notes")
        note_count_before = cur.fetchone()[0]
        con.close()
        
        # Transfer
        result = evernothing_s3.sync_to_s3()
        self.assertTrue(result)
        
        # Verify data unchanged after transfer
        con = sqlite3.connect(self.db_path)
        cur = con.cursor()
        cur.execute("SELECT COUNT(*) FROM users")
        user_count_after = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM notes")
        note_count_after = cur.fetchone()[0]
        con.close()
        
        self.assertEqual(user_count_before, user_count_after)
        self.assertEqual(note_count_before, note_count_after)

if __name__ == '__main__':
    print("Running S3 Data Transfer Tests...")
    unittest.main(verbosity=2)
