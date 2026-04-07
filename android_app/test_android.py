import unittest
import os
import sys
import tempfile
import sqlite3
from unittest.mock import patch, MagicMock

# Add both the android dir and the parent evernothing dir to path
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
sys.path.insert(0, os.path.join(_HERE, '..', 'evernothing'))

class TestEverNothingAndroid(unittest.TestCase):
    
    def setUp(self):
        self.test_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.test_db.close()
        self.db_path = self.test_db.name
        
        con = sqlite3.connect(self.db_path)
        cur = con.cursor()
        cur.executescript("""
            CREATE TABLE users(id INTEGER PRIMARY KEY, username TEXT, password TEXT);
            CREATE TABLE notes(id INTEGER PRIMARY KEY, user_id INTEGER, note_key TEXT, note_value TEXT);
            CREATE TABLE folders(id INTEGER PRIMARY KEY, user_id INTEGER, name TEXT);
            INSERT INTO users VALUES(1, 'testuser', 'scrypt:32768:8:1$test$hash');
            INSERT INTO notes VALUES(1, 1, 'Test Note', 'Test Content');
            INSERT INTO folders VALUES(1, 1, 'Test Folder');
        """)
        con.commit()
        con.close()
        
        os.environ['DB_FILE'] = self.db_path
        os.environ['AWS_ACCESS_KEY_ID'] = 'test_key'
        os.environ['AWS_SECRET_ACCESS_KEY'] = 'test_secret'
        
        import evernothing_android
        self.app = evernothing_android.app
        self.app.config['TESTING'] = True
        evernothing_android.DB = self.db_path
        self.client = self.app.test_client()
    
    def tearDown(self):
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)
    
    def test_login_page_loads(self):
        response = self.client.get('/login')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Login', response.data)
    
    def test_home_requires_login(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 302)
    
    @patch('evernothing_android.sync_to_s3')
    def test_upload_db_success(self, mock_sync):
        mock_sync.return_value = True
        with self.client.session_transaction() as sess:
            sess['_user_id'] = '1'
        response = self.client.post('/checkpoint')
        self.assertEqual(response.status_code, 200)
        mock_sync.assert_called_once()
    
    def test_database_stats(self):
        con = sqlite3.connect(self.db_path)
        cur = con.cursor()
        cur.execute("SELECT COUNT(*) FROM notes WHERE user_id=1")
        note_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM folders WHERE user_id=1")
        folder_count = cur.fetchone()[0]
        con.close()
        self.assertEqual(note_count, 1)
        self.assertEqual(folder_count, 1)

class TestS3Sync(unittest.TestCase):
    
    def setUp(self):
        self.test_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.test_db.write(b'test')
        self.test_db.close()
        self.db_path = self.test_db.name
        
        os.environ['DB_FILE'] = self.db_path
        os.environ['AWS_ACCESS_KEY_ID'] = 'test_key'
        os.environ['AWS_SECRET_ACCESS_KEY'] = 'test_secret'

        # Import from parent evernothing directory (path already set at module top)
        import evernothing_s3
        self.s3_module = evernothing_s3
        self.s3_module.DB_FILE = self.db_path
        self.s3_module.S3_BUCKET_NAME = 'test-bucket'
    
    def tearDown(self):
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)
    
    def test_missing_credentials(self):
        os.environ['AWS_ACCESS_KEY_ID'] = 'TBD'
        self.s3_module.AWS_ACCESS_KEY_ID = 'TBD'
        result = self.s3_module.sync_to_s3()
        self.assertFalse(result)
    
    def test_missing_database(self):
        os.unlink(self.db_path)
        result = self.s3_module.sync_to_s3()
        self.assertFalse(result)
    
    @patch('evernothing_s3.boto3.client')
    def test_successful_upload(self, mock_boto):
        mock_s3 = MagicMock()
        mock_boto.return_value = mock_s3
        self.s3_module.AWS_ACCESS_KEY_ID = 'test_key'
        self.s3_module.AWS_SECRET_ACCESS_KEY = 'test_secret'
        result = self.s3_module.sync_to_s3()
        self.assertTrue(result)
        # upload_fileobj used for compressed backup, upload_file for latest copy
        total_uploads = mock_s3.upload_file.call_count + mock_s3.upload_fileobj.call_count
        self.assertGreaterEqual(total_uploads, 2)

if __name__ == '__main__':
    print("Running EverNothing Android Tests...")
    unittest.main(verbosity=2)
