import unittest
import os
import tempfile
from unittest.mock import patch, MagicMock
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import evernothing_s3

class TestS3Sync(unittest.TestCase):
    
    def setUp(self):
        self.test_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.test_db.write(b'test data')
        self.test_db.close()
        self.db_path = self.test_db.name
        
        os.environ['DB_FILE'] = self.db_path
        os.environ['AWS_ACCESS_KEY_ID'] = 'test_key'
        os.environ['AWS_SECRET_ACCESS_KEY'] = 'test_secret'
        evernothing_s3.DB_FILE = self.db_path
        evernothing_s3.AWS_ACCESS_KEY_ID = 'test_key'
        evernothing_s3.AWS_SECRET_ACCESS_KEY = 'test_secret'
    
    def tearDown(self):
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)
    
    def test_missing_credentials(self):
        evernothing_s3.AWS_ACCESS_KEY_ID = 'TBD'
        result = evernothing_s3.sync_to_s3()
        self.assertFalse(result)
    
    def test_missing_database(self):
        os.unlink(self.db_path)
        result = evernothing_s3.sync_to_s3()
        self.assertFalse(result)
    
    @patch('evernothing_s3.boto3.client')
    def test_successful_upload(self, mock_boto):
        mock_s3 = MagicMock()
        mock_boto.return_value = mock_s3
        result = evernothing_s3.sync_to_s3()
        self.assertTrue(result)
        self.assertEqual(mock_s3.upload_file.call_count, 2)
    
    @patch('evernothing_s3.boto3.client')
    def test_upload_exception(self, mock_boto):
        mock_s3 = MagicMock()
        mock_s3.upload_file.side_effect = Exception("S3 error")
        mock_boto.return_value = mock_s3
        result = evernothing_s3.sync_to_s3()
        self.assertFalse(result)

if __name__ == '__main__':
    print("Running EverNothing S3 Tests...")
    unittest.main(verbosity=2)
