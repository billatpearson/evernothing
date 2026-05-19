"""Tests for Batch 1 auth hardening:

- C1+H8: admin password hash support, constant-time check, rate limit
- C4   : /api/login rate limit + lockout
- M2   : session_protection = 'strong'
- M6   : per-username account lockout
- M11  : /logout?forget=1 clears last_user cookie

These tests exercise the monolith (which is the actual runtime entry
point) so they cover the same code paths a real client hits.
"""
import os
import sqlite3
import tempfile
import unittest
from werkzeug.security import generate_password_hash


class _Base(unittest.TestCase):
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
        evernothing.login_manager.session_protection = None  # avoid invalidating client logins
        self.app = evernothing.app
        self.client = self.app.test_client()
        self.en = evernothing

        # Reset rate-limit + lockout state every test
        from rate_limiter import rate_limit_store
        rate_limit_store.clear()
        from Evernothing_Security.login_lockout import reset_all
        reset_all()

    def tearDown(self):
        os.close(self.db_fd)
        try:
            os.unlink(self.db_path)
        except OSError:
            pass

    def _register(self, username, password='TestPass123', email=None):
        return self.client.post('/register', data={
            'username': username, 'password': password,
            'email': email or f'{username}@example.com',
        }, follow_redirects=True)

    def _login(self, username, password='TestPass123'):
        return self.client.post('/login', data={
            'username': username, 'password': password,
        }, follow_redirects=False)


# ---------------------------------------------------------------------------
# Login lockout (M6)
# ---------------------------------------------------------------------------
class LoginLockoutTests(_Base):
    def test_lockout_module_register_and_clear(self):
        from Evernothing_Security.login_lockout import (
            register_failure, is_locked, clear_failures, reset_all,
            LOGIN_LOCKOUT_THRESHOLD,
        )
        reset_all()
        u = 'lockoutuser'
        for _ in range(LOGIN_LOCKOUT_THRESHOLD - 1):
            self.assertFalse(register_failure(u))
            self.assertFalse(is_locked(u))
        self.assertTrue(register_failure(u))
        self.assertTrue(is_locked(u))
        clear_failures(u)
        self.assertFalse(is_locked(u))

    def test_lockout_disabled_via_env(self):
        from Evernothing_Security import login_lockout
        original = login_lockout.LOGIN_LOCKOUT_ENABLED
        login_lockout.LOGIN_LOCKOUT_ENABLED = False
        try:
            for _ in range(20):
                login_lockout.register_failure('x')
            self.assertFalse(login_lockout.is_locked('x'))
        finally:
            login_lockout.LOGIN_LOCKOUT_ENABLED = original

    def test_form_login_locks_after_threshold(self):
        from Evernothing_Security.login_lockout import LOGIN_LOCKOUT_THRESHOLD
        self._register('lockuser')
        # First fail enough to lock
        for _ in range(LOGIN_LOCKOUT_THRESHOLD):
            self.client.post('/login', data={'username': 'lockuser', 'password': 'wrong'})
        # Even the correct password should be refused now
        rv = self.client.post('/login', data={'username': 'lockuser', 'password': 'TestPass123'},
                              follow_redirects=False)
        self.assertEqual(rv.status_code, 200)
        self.assertIn(b'Account locked', rv.data)

    def test_successful_login_clears_failures(self):
        from Evernothing_Security.login_lockout import _failed
        self._register('clearuser')
        # Three bad attempts (under threshold)
        for _ in range(3):
            self.client.post('/login', data={'username': 'clearuser', 'password': 'wrong'})
        self.assertIn('clearuser', _failed)
        rv = self._login('clearuser')
        self.assertEqual(rv.status_code, 302)
        self.assertNotIn('clearuser', _failed)

    def test_api_login_locks_after_threshold(self):
        from Evernothing_Security.login_lockout import LOGIN_LOCKOUT_THRESHOLD
        self._register('apilock')
        for _ in range(LOGIN_LOCKOUT_THRESHOLD):
            self.client.post('/api/login',
                             json={'username': 'apilock', 'password': 'wrong'})
        rv = self.client.post('/api/login',
                              json={'username': 'apilock', 'password': 'TestPass123'})
        self.assertEqual(rv.status_code, 423)


# ---------------------------------------------------------------------------
# /api/login rate limit (C4)
# ---------------------------------------------------------------------------
class ApiLoginRateLimitTests(_Base):
    def test_api_login_returns_429_when_rate_limited(self):
        import rate_limiter
        original = rate_limiter.RATE_LIMIT_LOGIN
        rate_limiter.RATE_LIMIT_LOGIN = 3
        try:
            self._register('apirl')
            # Three legit attempts (each succeeds and counts toward the bucket)
            for _ in range(3):
                self.client.post('/api/login',
                                 json={'username': 'apirl', 'password': 'wrong'})
            # Fourth — over the limit
            rv = self.client.post('/api/login',
                                  json={'username': 'apirl', 'password': 'TestPass123'})
            self.assertEqual(rv.status_code, 429)
        finally:
            rate_limiter.RATE_LIMIT_LOGIN = original


# ---------------------------------------------------------------------------
# Admin auth (C1, H8, admin rate limit)
# ---------------------------------------------------------------------------
class AdminAuthTests(_Base):
    def test_verify_admin_with_plaintext(self):
        from Evernothing_Security.admin_auth import verify_admin
        os.environ['ADMIN_USER'] = 'root'
        os.environ['ADMIN_PASS'] = 'Pa55word!'
        os.environ.pop('ADMIN_PASS_HASH', None)
        try:
            self.assertTrue(verify_admin('root', 'Pa55word!'))
            self.assertFalse(verify_admin('root', 'wrong'))
            self.assertFalse(verify_admin('rooT', 'Pa55word!'))  # constant-time, but case-sensitive
        finally:
            os.environ.pop('ADMIN_USER', None)
            os.environ.pop('ADMIN_PASS', None)

    def test_verify_admin_with_hash_preferred_over_plaintext(self):
        from Evernothing_Security.admin_auth import verify_admin
        os.environ['ADMIN_USER'] = 'root'
        os.environ['ADMIN_PASS_HASH'] = generate_password_hash('hashed-pass')
        os.environ['ADMIN_PASS'] = 'plaintext-ignored'
        try:
            self.assertTrue(verify_admin('root', 'hashed-pass'))
            self.assertFalse(verify_admin('root', 'plaintext-ignored'))
        finally:
            os.environ.pop('ADMIN_USER', None)
            os.environ.pop('ADMIN_PASS', None)
            os.environ.pop('ADMIN_PASS_HASH', None)

    def test_verify_admin_default_used_when_no_env(self):
        from Evernothing_Security.admin_auth import verify_admin, using_default_credentials
        os.environ.pop('ADMIN_USER', None)
        os.environ.pop('ADMIN_PASS', None)
        os.environ.pop('ADMIN_PASS_HASH', None)
        self.assertTrue(verify_admin('admin', 'admin'))
        self.assertTrue(using_default_credentials())

    def test_admin_login_route_rejects_wrong_password(self):
        os.environ['ADMIN_USER'] = 'root'
        os.environ['ADMIN_PASS'] = 'rightpass'
        os.environ.pop('ADMIN_PASS_HASH', None)
        try:
            rv = self.client.post('/admin', data={'username': 'root', 'password': 'wrongpass'},
                                  follow_redirects=True)
            self.assertIn(b'Invalid credentials', rv.data)
        finally:
            os.environ.pop('ADMIN_USER', None)
            os.environ.pop('ADMIN_PASS', None)

    def test_admin_login_route_accepts_hash(self):
        os.environ['ADMIN_USER'] = 'root'
        os.environ['ADMIN_PASS_HASH'] = generate_password_hash('h@shed')
        os.environ.pop('ADMIN_PASS', None)
        try:
            rv = self.client.post('/admin', data={'username': 'root', 'password': 'h@shed'},
                                  follow_redirects=False)
            # Successful admin login redirects to the dashboard
            self.assertEqual(rv.status_code, 302)
            self.assertIn('/admin/dashboard', rv.headers.get('Location', ''))
        finally:
            os.environ.pop('ADMIN_USER', None)
            os.environ.pop('ADMIN_PASS_HASH', None)

    def test_admin_login_rate_limited(self):
        import rate_limiter
        original = rate_limiter.RATE_LIMIT_LOGIN
        rate_limiter.RATE_LIMIT_LOGIN = 2
        try:
            os.environ['ADMIN_USER'] = 'root'
            os.environ['ADMIN_PASS'] = 'rightpass'
            os.environ.pop('ADMIN_PASS_HASH', None)
            for _ in range(2):
                self.client.post('/admin', data={'username': 'root', 'password': 'wrong'})
            rv = self.client.post('/admin', data={'username': 'root', 'password': 'rightpass'},
                                  follow_redirects=True)
            self.assertIn(b'Too many', rv.data)
        finally:
            rate_limiter.RATE_LIMIT_LOGIN = original
            os.environ.pop('ADMIN_USER', None)
            os.environ.pop('ADMIN_PASS', None)


# ---------------------------------------------------------------------------
# Logout / forget-device (M11)
# ---------------------------------------------------------------------------
class LogoutForgetDeviceTests(_Base):
    def test_logout_without_forget_keeps_last_user_cookie(self):
        self._register('keepme')
        self._login('keepme')
        rv = self.client.get('/logout')
        # Without ?forget=1 we should NOT see a Set-Cookie clearing last_user
        clears = [c for c in rv.headers.getlist('Set-Cookie')
                  if 'last_user=' in c and ('Max-Age=0' in c or 'expires=Thu, 01 Jan 1970' in c.lower())]
        self.assertEqual(clears, [],
                         f'expected no clear-cookie for last_user, got {clears}')

    def test_logout_with_forget_clears_last_user_cookie(self):
        self._register('forgetme')
        self._login('forgetme')
        rv = self.client.get('/logout?forget=1')
        # Cookie is cleared via Set-Cookie max-age=0; check the response header
        cookies = rv.headers.getlist('Set-Cookie')
        self.assertTrue(any('last_user=' in c and ('Max-Age=0' in c or 'expires=Thu, 01 Jan 1970' in c.lower())
                            for c in cookies),
                        f'expected last_user clear in Set-Cookie; got: {cookies}')


# ---------------------------------------------------------------------------
# session_protection (M2)
# ---------------------------------------------------------------------------
class SessionProtectionTests(_Base):
    def test_default_session_protection_is_strong(self):
        # The module-level default in Evernothing_Web/app.py should be 'strong'.
        # We can't reload that module here (other modules import the same app),
        # so we read the source line directly to assert the configured value.
        import os, re
        path = os.path.join(os.path.dirname(__file__), '..',
                            'Evernothing_Web', 'app.py')
        with open(path, 'r', encoding='utf-8') as f:
            src = f.read()
        m = re.search(r"login_manager\.session_protection\s*=\s*'([^']+)'", src)
        self.assertIsNotNone(m, 'session_protection assignment not found')
        self.assertEqual(m.group(1), 'strong')

    def test_monolith_default_session_protection_is_strong(self):
        import os, re
        path = os.path.join(os.path.dirname(__file__), '..', 'evernothing.py')
        with open(path, 'r', encoding='utf-8') as f:
            src = f.read()
        m = re.search(r"login_manager\.session_protection\s*=\s*\"([^\"]+)\"", src)
        self.assertIsNotNone(m, 'session_protection assignment not found in monolith')
        self.assertEqual(m.group(1), 'strong')


if __name__ == '__main__':
    unittest.main()
