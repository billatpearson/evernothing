import unittest
import sys
import os

# Add the parent directory to the path to allow importing 'evernothing'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from evernothing import app

class EvernothingTestCase(unittest.TestCase):
    """This class represents the test case for the Evernothing application."""

    def setUp(self):
        """Define test variables and initialize app."""
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    def test_index_page(self):
        """Test that the index page loads correctly."""
        response = self.client.get('/', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Welcome to Evernothing!", response.data)

if __name__ == "__main__":
    unittest.main()
