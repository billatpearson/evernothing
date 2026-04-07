"""Unit tests for unicorn and stellar theme switching."""
import unittest
import tempfile
import os
import sqlite3


class ThemeTestCase(unittest.TestCase):

    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp()
        with sqlite3.connect(self.db_path) as con:
            cur = con.cursor()
            cur.execute('CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT, email TEXT, last_login TEXT)')
            cur.execute('CREATE TABLE notes (id INTEGER PRIMARY KEY, user_id INTEGER, note_key TEXT, note_value TEXT, description TEXT, folder_id INTEGER, updated_at TEXT)')
            cur.execute('CREATE TABLE folders (id INTEGER PRIMARY KEY, user_id INTEGER, name TEXT, parent_id INTEGER)')
            cur.execute('CREATE TABLE note_history (id INTEGER PRIMARY KEY, note_id INTEGER, user_id INTEGER, note_key TEXT, note_value TEXT, description TEXT, folder_id INTEGER, updated_at TEXT)')
            cur.execute('CREATE TABLE attachments (id INTEGER PRIMARY KEY, note_id INTEGER, user_id INTEGER, filename TEXT, file_data BLOB, file_size INTEGER, uploaded_at TEXT)')
            cur.execute('CREATE TABLE audit_log (id INTEGER PRIMARY KEY, user_id INTEGER, action TEXT, entity_type TEXT, entity_id INTEGER, old_values TEXT, new_values TEXT, timestamp TEXT, ip_address TEXT)')
            cur.execute('CREATE TABLE user_sessions (id INTEGER PRIMARY KEY, user_id INTEGER, session_id TEXT, login_time TEXT, logout_time TEXT, ip_address TEXT, user_agent TEXT)')
            cur.execute('CREATE TABLE sync_queue (id INTEGER PRIMARY KEY, entity_type TEXT, entity_id INTEGER, operation TEXT, payload TEXT, changed_at TEXT, synced_at TEXT)')
            con.commit()

        import evernothing
        evernothing.DB = self.db_path
        evernothing.app.config['TESTING'] = True
        evernothing.app.config['WTF_CSRF_ENABLED'] = False
        evernothing.app.config['SECRET_KEY'] = 'test_key'
        evernothing.login_manager.session_protection = None
        self.app = evernothing.app
        self.client = self.app.test_client()
        self.evernothing = evernothing

    def tearDown(self):
        os.close(self.db_fd)
        try:
            os.unlink(self.db_path)
        except OSError:
            pass

    # --- helpers ---

    def _set_theme(self, theme):
        return self.client.get(f'/set_theme?t={theme}', follow_redirects=False)

    # --- tests ---

    def test_default_theme_is_stellar(self):
        """_get_style() returns STYLE_STELLAR when no theme is set in session."""
        with self.app.test_request_context('/'):
            style = self.evernothing._get_style()
        self.assertIs(style, self.evernothing.STYLE_STELLAR)

    def test_set_theme_to_unicorn(self):
        """GET /set_theme?t=unicorn stores 'unicorn' in session."""
        with self.client.session_transaction() as sess:
            sess['theme'] = 'stellar'
        self.client.get('/set_theme?t=unicorn', follow_redirects=False)
        with self.client.session_transaction() as sess:
            self.assertEqual(sess.get('theme'), 'unicorn')

    def test_set_theme_to_stellar(self):
        """GET /set_theme?t=stellar stores 'stellar' in session."""
        with self.client.session_transaction() as sess:
            sess['theme'] = 'unicorn'
        self.client.get('/set_theme?t=stellar', follow_redirects=False)
        with self.client.session_transaction() as sess:
            self.assertEqual(sess.get('theme'), 'stellar')

    def test_invalid_theme_toggles(self):
        """An unrecognised theme value cycles through stellar -> unicorn -> startrek."""
        with self.client.session_transaction() as sess:
            sess['theme'] = 'stellar'
        self.client.get('/set_theme?t=invalid', follow_redirects=False)
        with self.client.session_transaction() as sess:
            self.assertEqual(sess.get('theme'), 'unicorn')

    def test_get_style_returns_unicorn_when_session_set(self):
        """_get_style() returns STYLE_UNICORN when session theme is 'unicorn'."""
        with self.app.test_request_context('/'):
            from flask import session
            session['theme'] = 'unicorn'
            style = self.evernothing._get_style()
        self.assertIs(style, self.evernothing.STYLE_UNICORN)

    def test_get_style_returns_stellar_when_session_set(self):
        """_get_style() returns STYLE_STELLAR when session theme is 'stellar'."""
        with self.app.test_request_context('/'):
            from flask import session
            session['theme'] = 'stellar'
            style = self.evernothing._get_style()
        self.assertIs(style, self.evernothing.STYLE_STELLAR)

    def test_style_unicorn_contains_unicorn_css(self):
        """STYLE_UNICORN contains unicorn-specific CSS identifiers."""
        self.assertIn('unicorn', self.evernothing.STYLE_UNICORN.lower())

    def test_style_stellar_contains_stellar_css(self):
        """STYLE_STELLAR contains stellar-specific CSS identifiers."""
        self.assertIn('orbitron', self.evernothing.STYLE_STELLAR.lower())

    def test_set_theme_redirects(self):
        """set_theme always redirects (302)."""
        resp = self.client.get('/set_theme?t=unicorn')
        self.assertEqual(resp.status_code, 302)

    def test_toggle_from_unicorn_to_stellar(self):
        """Fallback cycle: unicorn -> startrek when no valid t param."""
        with self.client.session_transaction() as sess:
            sess['theme'] = 'unicorn'
        self.client.get('/set_theme', follow_redirects=False)
        with self.client.session_transaction() as sess:
            self.assertEqual(sess.get('theme'), 'startrek')

    def test_set_theme_to_startrek(self):
        """GET /set_theme?t=startrek stores 'startrek' in session."""
        with self.client.session_transaction() as sess:
            sess['theme'] = 'stellar'
        self.client.get('/set_theme?t=startrek', follow_redirects=False)
        with self.client.session_transaction() as sess:
            self.assertEqual(sess.get('theme'), 'startrek')

    def test_get_style_returns_startrek_when_session_set(self):
        """_get_style() returns STYLE_STARTREK when session theme is 'startrek'."""
        with self.app.test_request_context('/'):
            from flask import session
            session['theme'] = 'startrek'
            style = self.evernothing._get_style()
        self.assertIs(style, self.evernothing.STYLE_STARTREK)

    def test_style_startrek_contains_lcars_css(self):
        """STYLE_STARTREK contains LCARS-specific identifiers."""
        self.assertIn('lcars', self.evernothing.STYLE_STARTREK.lower())


if __name__ == '__main__':
    unittest.main()
