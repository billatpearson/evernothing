"""
Evernothing_Security/admin_auth.py — Admin credential check.

Two sources for the expected admin password:

1. ADMIN_PASS_HASH  (preferred) — Werkzeug-compatible hash string from
   `werkzeug.security.generate_password_hash`. Verified in constant time.

2. ADMIN_PASS       (back-compat) — plaintext. Compared in constant time
   via hmac.compare_digest. Logs a loud warning when default 'admin' is
   used so it doesn't silently ship to production.

A boot-time call to log_admin_security_warnings() emits one-time warnings
about insecure defaults so operators see them in the log.
"""
import hmac
import os
import threading

from werkzeug.security import check_password_hash

_warned_lock = threading.Lock()
_warned = False


def _expected_user() -> str:
    return os.environ.get('ADMIN_USER') or 'admin'


def verify_admin(submitted_user: str, submitted_pass: str) -> bool:
    """Constant-time admin credential check."""
    expected_user = _expected_user()
    # Compare username in constant time too — leaks length but not content.
    if not hmac.compare_digest(
            (submitted_user or '').encode('utf-8'),
            expected_user.encode('utf-8')):
        return False

    pass_hash = os.environ.get('ADMIN_PASS_HASH', '').strip()
    if pass_hash:
        try:
            return check_password_hash(pass_hash, submitted_pass or '')
        except Exception:
            return False

    expected_plain = os.environ.get('ADMIN_PASS') or 'admin'
    return hmac.compare_digest(
        (submitted_pass or '').encode('utf-8'),
        expected_plain.encode('utf-8'))


def using_default_credentials() -> bool:
    """True iff admin is left at admin/admin with no hash configured."""
    if os.environ.get('ADMIN_PASS_HASH', '').strip():
        return False
    return _expected_user() == 'admin' and (os.environ.get('ADMIN_PASS') or 'admin') == 'admin'


def log_admin_security_warnings(logger):
    """Emit one-time warnings about admin auth posture. Call at app boot."""
    global _warned
    with _warned_lock:
        if _warned:
            return
        _warned = True
    if using_default_credentials():
        logger.warning(
            'ADMIN credentials are at default (admin/admin). Set ADMIN_PASS_HASH '
            '(preferred) or a strong ADMIN_PASS in .env. Generate a hash with: '
            'python -c "from werkzeug.security import generate_password_hash; '
            'import getpass; print(generate_password_hash(getpass.getpass()))"')
    elif not os.environ.get('ADMIN_PASS_HASH', '').strip():
        logger.info(
            'ADMIN_PASS is plaintext in .env. Consider switching to '
            'ADMIN_PASS_HASH for safer storage.')
