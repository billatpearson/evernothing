"""
Evernothing_Security/login_lockout.py — per-username failed-login lockout.

Complements rate_limiter.py (per-IP) by tracking failures per username so
an attacker rotating IPs still hits the same wall.

In-memory state — resets on process restart. Same trade-off as the IP
limiter; documented as M6/M5 in the security audit. Move to DB-backed
state when we go multi-worker.

Configuration (environment variables):
  LOGIN_LOCKOUT_ENABLED    Enable lockout (default true)
  LOGIN_LOCKOUT_THRESHOLD  Failed attempts before lockout (default 5)
  LOGIN_LOCKOUT_MINUTES    Lockout window in minutes (default 15)
"""
import os
import threading
from datetime import datetime, timedelta

LOGIN_LOCKOUT_ENABLED   = os.environ.get('LOGIN_LOCKOUT_ENABLED', 'true').lower() == 'true'
LOGIN_LOCKOUT_THRESHOLD = int(os.environ.get('LOGIN_LOCKOUT_THRESHOLD', '5'))
LOGIN_LOCKOUT_MINUTES   = int(os.environ.get('LOGIN_LOCKOUT_MINUTES', '15'))

# {username_lower: {'count': int, 'first_at': dt, 'locked_until': dt|None}}
_failed: dict = {}
_lock = threading.Lock()


def _key(username: str) -> str:
    return (username or '').strip().lower()


def is_locked(username: str) -> bool:
    """True iff there's an active lockout for this username."""
    if not LOGIN_LOCKOUT_ENABLED:
        return False
    k = _key(username)
    if not k:
        return False
    with _lock:
        rec = _failed.get(k)
        if not rec:
            return False
        until = rec.get('locked_until')
        if until and datetime.utcnow() < until:
            return True
        # lockout window expired — reset state so subsequent attempts start fresh
        if until and datetime.utcnow() >= until:
            _failed.pop(k, None)
        return False


def lockout_seconds_remaining(username: str) -> int:
    """Seconds left on a current lockout. 0 if not locked."""
    k = _key(username)
    with _lock:
        rec = _failed.get(k)
        if not rec:
            return 0
        until = rec.get('locked_until')
        if not until:
            return 0
        delta = (until - datetime.utcnow()).total_seconds()
        return max(0, int(delta))


def register_failure(username: str) -> bool:
    """Record a failed login. Returns True iff this attempt triggered a
    lockout (i.e. we crossed the threshold on this call)."""
    if not LOGIN_LOCKOUT_ENABLED:
        return False
    k = _key(username)
    if not k:
        return False
    with _lock:
        rec = _failed.get(k)
        now = datetime.utcnow()
        if not rec:
            _failed[k] = {'count': 1, 'first_at': now, 'locked_until': None}
            return False
        # If a previous lockout has expired, start counting from zero again.
        if rec.get('locked_until') and now >= rec['locked_until']:
            _failed[k] = {'count': 1, 'first_at': now, 'locked_until': None}
            return False
        rec['count'] += 1
        if rec['count'] >= LOGIN_LOCKOUT_THRESHOLD and not rec.get('locked_until'):
            rec['locked_until'] = now + timedelta(minutes=LOGIN_LOCKOUT_MINUTES)
            return True
        return False


def clear_failures(username: str) -> None:
    """Call on successful login to reset the counter."""
    k = _key(username)
    with _lock:
        _failed.pop(k, None)


def reset_all() -> None:
    """Test helper — wipe all state."""
    with _lock:
        _failed.clear()
