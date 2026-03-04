import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Mock Kivy before importing main
sys.modules['kivy'] = MagicMock()
sys.modules['kivy.app'] = MagicMock()
sys.modules['kivy.uix'] = MagicMock()
sys.modules['kivy.uix.screenmanager'] = MagicMock()
sys.modules['kivy.uix.boxlayout'] = MagicMock()
sys.modules['kivy.uix.gridlayout'] = MagicMock()
sys.modules['kivy.uix.scrollview'] = MagicMock()
sys.modules['kivy.uix.label'] = MagicMock()
sys.modules['kivy.uix.textinput'] = MagicMock()
sys.modules['kivy.uix.button'] = MagicMock()
sys.modules['kivy.core'] = MagicMock()
sys.modules['kivy.core.window'] = MagicMock()

from main import APIClient

class AndroidAppTestCase(unittest.TestCase):
    def setUp(self):
        self.api = APIClient()
        self.api.base_url = 'http://test.local:5000'
    
    def tearDown(self):
        pass
    
    @patch('requests.Session.post')
    def test_login_success(self, mock_post):
        mock_post.return_value.status_code = 302
        result = self.api.login('testuser', 'testpass')
        self.assertTrue(result)
        mock_post.assert_called_once_with(
            'http://test.local:5000/login',
            data={'username': 'testuser', 'password': 'testpass'},
            allow_redirects=False
        )
    
    @patch('requests.Session.post')
    def test_login_failure(self, mock_post):
        mock_post.return_value.status_code = 200
        result = self.api.login('baduser', 'badpass')
        self.assertFalse(result)
    
    @patch('requests.Session.post')
    def test_login_network_error(self, mock_post):
        mock_post.side_effect = Exception('Network error')
        result = self.api.login('user', 'pass')
        self.assertFalse(result)
    
    @patch('requests.Session.post')
    def test_register_success(self, mock_post):
        mock_post.return_value.status_code = 302
        result = self.api.register('newuser', 'newpass', 'test@test.com')
        self.assertTrue(result)
        mock_post.assert_called_once_with(
            'http://test.local:5000/register',
            data={'username': 'newuser', 'password': 'newpass', 'email': 'test@test.com'},
            allow_redirects=False
        )
    
    @patch('requests.Session.post')
    def test_register_duplicate(self, mock_post):
        mock_post.return_value.status_code = 200
        result = self.api.register('existing', 'pass', 'test@test.com')
        self.assertFalse(result)
    
    @patch('requests.Session.get')
    def test_get_folders_success(self, mock_get):
        mock_get.return_value.text = '''
        <a href=/folder/1>Folder1</a>
        <a href=/folder/2>Folder2</a>
        '''
        folders = self.api.get_folders()
        self.assertIsNotNone(folders)
        self.assertEqual(len(folders), 2)
        self.assertEqual(folders[0]['id'], '1')
        self.assertEqual(folders[0]['name'], 'Folder1')
    
    @patch('requests.Session.get')
    def test_get_folders_not_logged_in(self, mock_get):
        mock_get.return_value.text = '<h3>Login</h3>'
        folders = self.api.get_folders()
        self.assertIsNone(folders)
    
    @patch('requests.Session.get')
    def test_get_folders_network_error(self, mock_get):
        mock_get.side_effect = Exception('Network error')
        folders = self.api.get_folders()
        self.assertIsNone(folders)
    
    @patch('requests.Session.get')
    def test_get_folder_contents(self, mock_get):
        mock_get.return_value.text = '''
        <a href=/edit/1>Note1</a>
        <a href=/edit/2>Note2</a>
        <a href=/folder/3>Subfolder1</a>
        '''
        contents = self.api.get_folder_contents('1')
        self.assertEqual(len(contents['notes']), 2)
        self.assertEqual(len(contents['subfolders']), 1)
        self.assertEqual(contents['notes'][0]['name'], 'Note1')
        self.assertEqual(contents['subfolders'][0]['name'], 'Subfolder1')
    
    @patch('requests.Session.get')
    def test_get_folder_contents_empty(self, mock_get):
        mock_get.return_value.text = '<h3>Folder</h3>'
        contents = self.api.get_folder_contents('1')
        self.assertEqual(len(contents['notes']), 0)
        self.assertEqual(len(contents['subfolders']), 0)
    
    @patch('requests.Session.post')
    def test_create_folder_root(self, mock_post):
        mock_post.return_value.status_code = 302
        result = self.api.create_folder('NewFolder')
        self.assertTrue(result)
        mock_post.assert_called_once_with(
            'http://test.local:5000/folder/add',
            data={'name': 'NewFolder'},
            allow_redirects=False
        )
    
    @patch('requests.Session.post')
    def test_create_folder_subfolder(self, mock_post):
        mock_post.return_value.status_code = 302
        result = self.api.create_folder('SubFolder', parent_id='5')
        self.assertTrue(result)
        mock_post.assert_called_once_with(
            'http://test.local:5000/folder/5/add_folder',
            data={'name': 'SubFolder'},
            allow_redirects=False
        )
    
    @patch('requests.Session.post')
    def test_create_folder_failure(self, mock_post):
        mock_post.return_value.status_code = 200
        result = self.api.create_folder('Folder')
        self.assertFalse(result)
    
    @patch('requests.Session.post')
    def test_create_note_success(self, mock_post):
        mock_post.return_value.status_code = 302
        result = self.api.create_note('1', 'TestNote', 'TestContent')
        self.assertTrue(result)
        mock_post.assert_called_once_with(
            'http://test.local:5000/add/1',
            data={'note': 'TestNote', 'content': 'TestContent'},
            allow_redirects=False
        )
    
    @patch('requests.Session.post')
    def test_create_note_failure(self, mock_post):
        mock_post.return_value.status_code = 200
        result = self.api.create_note('1', 'Note', 'Content')
        self.assertFalse(result)
    
    @patch('requests.Session.post')
    def test_create_note_network_error(self, mock_post):
        mock_post.side_effect = Exception('Network error')
        result = self.api.create_note('1', 'Note', 'Content')
        self.assertFalse(result)
    
    @patch('requests.Session.get')
    def test_logout(self, mock_get):
        self.api.logout()
        mock_get.assert_called_once_with('http://test.local:5000/logout')
    
    @patch('requests.Session.get')
    def test_logout_network_error(self, mock_get):
        mock_get.side_effect = Exception('Network error')
        # Should not raise exception
        self.api.logout()
    
    def test_api_client_initialization(self):
        api = APIClient()
        self.assertIsNotNone(api.session)
        self.assertEqual(api.base_url, 'http://127.0.0.1:5000')
    
    def test_api_client_custom_server(self):
        os.environ['EVERNOTHING_SERVER'] = 'http://custom.server:8000'
        api = APIClient()
        self.assertEqual(api.base_url, 'http://custom.server:8000')
        del os.environ['EVERNOTHING_SERVER']
    
    @patch('requests.Session.get')
    def test_get_folders_html_parsing_edge_cases(self, mock_get):
        mock_get.return_value.text = '''
        <a href=/folder/1>Folder with spaces</a>
        <a href=/folder/2>Folder<span>Extra</span></a>
        <a href=/other/3>NotAFolder</a>
        '''
        folders = self.api.get_folders()
        self.assertEqual(len(folders), 2)
        self.assertEqual(folders[0]['name'], 'Folder with spaces')
    
    @patch('requests.Session.get')
    def test_get_folder_contents_filters_parent(self, mock_get):
        mock_get.return_value.text = '''
        <a href=/folder/1>CurrentFolder</a>
        <a href=/folder/2>Subfolder</a>
        '''
        contents = self.api.get_folder_contents('1')
        # Should not include current folder in subfolders
        self.assertEqual(len(contents['subfolders']), 1)
        self.assertEqual(contents['subfolders'][0]['id'], '2')
    
    @patch('requests.Session.post')
    def test_create_note_empty_values(self, mock_post):
        mock_post.return_value.status_code = 302
        result = self.api.create_note('1', '', '')
        self.assertTrue(result)  # API client doesn't validate, server does
    
    @patch('requests.Session.post')
    def test_create_folder_empty_name(self, mock_post):
        mock_post.return_value.status_code = 302
        result = self.api.create_folder('')
        self.assertTrue(result)  # API client doesn't validate, server does
    
    @patch('requests.Session')
    def test_session_persistence(self, mock_session_class):
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        
        api = APIClient()
        api.session = mock_session
        
        # Multiple calls should use same session
        mock_session.post.return_value.status_code = 302
        api.login('user1', 'pass1')
        api.login('user2', 'pass2')
        
        self.assertEqual(mock_session.post.call_count, 2)

class AndroidAppIntegrationTestCase(unittest.TestCase):
    """Integration tests requiring actual Flask backend"""
    
    def setUp(self):
        self.api = APIClient()
        # These tests require Flask backend running
        self.skip_if_no_backend()
    
    def skip_if_no_backend(self):
        try:
            import requests
            requests.get('http://127.0.0.1:5000', timeout=1)
        except:
            self.skipTest('Flask backend not running')
    
    def test_full_workflow(self):
        # Register
        result = self.api.register('testuser123', 'testpass123', 'test@test.com')
        self.assertTrue(result)
        
        # Login
        result = self.api.login('testuser123', 'testpass123')
        self.assertTrue(result)
        
        # Get folders
        folders = self.api.get_folders()
        self.assertIsNotNone(folders)
        
        # Create folder
        result = self.api.create_folder('TestFolder')
        self.assertTrue(result)
        
        # Logout
        self.api.logout()

if __name__ == '__main__':
    unittest.main()
