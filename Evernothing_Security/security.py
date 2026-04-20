"""
Evernothing_Security/security.py
Encryption, password validation, session management, rate limiting,
CSRF, security headers, HTTPS enforcement.
"""
import base64, hashlib, os, re
from datetime import timezone
from functools import wraps
import datetime

from flask import redirect, request, session, jsonify
from flask_login import UserMixin, current_user, logout_user

from Evernothing_Web.app import app, login_manager, logger

# ---------------------------------------------------------------------------
# Encryption
# ---------------------------------------------------------------------------
try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
except ImportError:
    AESGCM = None

ENCRYPTION_ENABLED = os.environ.get('ENCRYPTION_ENABLED', 'true').lower() == 'true'

if AESGCM:
    _secret = app.secret_key
    if isinstance(_secret, bytes):
        _secret = _secret.decode('utf-8', errors='replace')
    KEY = hashlib.pbkdf2_hmac(
        'sha256', _secret.encode('utf-8'),
        b'evernothing-aes-key-v1', iterations=100_000, dklen=32)
    aesgcm = AESGCM(KEY)

    def encrypt(txt: str) -> str:
        if not ENCRYPTION_ENABLED or not txt:
            return txt or ''
        try:
            nonce = os.urandom(12)
            return base64.b64encode(nonce + aesgcm.encrypt(nonce, txt.encode('utf-8'), None)).decode()
        except Exception as e:
            logger.error(f'Enc Error: {e}')
            return txt

    def decrypt(txt: str) -> str:
        if not txt:
            return ''
        try:
            data = base64.b64decode(txt)
            return aesgcm.decrypt(data[:12], data[12:], None).decode('utf-8')
        except Exception:
            return txt
else:
    KEY = b''
    aesgcm = None
    def encrypt(t): return t
    def decrypt(t): return t

# ---------------------------------------------------------------------------
# User model
# ---------------------------------------------------------------------------
class User(UserMixin):
    def __init__(self, id, username):
        self.id = id
        self.username = username

@login_manager.user_loader
def load_user(uid):
    from Evernothing_DB.database import get_db
    con = get_db()
    try:
        r = con.execute('SELECT id,username FROM users WHERE id=?', (uid,)).fetchone()
    finally:
        con.close()
    return User(r['id'], r['username']) if r else None

# ---------------------------------------------------------------------------
# Input validation
# ---------------------------------------------------------------------------
def validate_input(text, max_length=10000):
    if text is None:
        return None, None
    if len(text) > max_length:
        return None, f'Input too long (max {max_length} characters)'
    return text, None

def validate_email(email):
    if not re.match(r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$', email):
        return None, 'Invalid email format'
    return email, None

def validate_password(password):
    if len(password) < 8:
        return None, 'Password must be at least 8 characters'
    if not any(c.isupper() for c in password):
        return None, 'Password must contain at least one uppercase letter'
    if not any(c.islower() for c in password):
        return None, 'Password must contain at least one lowercase letter'
    if not any(c.isdigit() for c in password):
        return None, 'Password must contain at least one number'
    return password, None

ALLOWED_EXTENSIONS = {'txt','pdf','png','jpg','jpeg','gif','doc','docx','zip'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ---------------------------------------------------------------------------
# Access control decorators
# ---------------------------------------------------------------------------
def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect('/admin')
        login_time = session.get('admin_login_time')
        if login_time:
            elapsed = (datetime.datetime.now(timezone.utc) -
                       datetime.datetime.fromisoformat(login_time)).total_seconds()
            if elapsed > 7200:
                session.pop('admin_logged_in', None)
                return redirect('/admin?timeout=1')
        return f(*args, **kwargs)
    return decorated

def api_login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated

# ---------------------------------------------------------------------------
# Security hooks
# ---------------------------------------------------------------------------
@app.before_request
def enforce_https():
    if app.config.get('TESTING') or app.debug:
        return
    _root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ssl_cert = os.environ.get('SSL_CERT', os.path.join(_root, 'Startup', 'cert.pem'))
    ssl_key  = os.environ.get('SSL_KEY',  os.path.join(_root, 'Startup', 'key.pem'))
    if not (os.path.exists(ssl_cert) and os.path.exists(ssl_key)):
        return
    if request.is_secure:
        return
    if request.headers.get('X-Forwarded-Proto', 'http') == 'https':
        return
    return redirect(request.url.replace('http://', 'https://', 1), code=301)

@app.before_request
def validate_session():
    if current_user.is_authenticated:
        if not session:
            return
        remember_me = session.get('remember_me', False)
        if not remember_me:
            session.permanent = True
            if 'last_activity' in session:
                last = datetime.datetime.fromisoformat(session['last_activity'])
                timeout = int(os.environ.get('SESSION_TIMEOUT_HOURS', '2'))
                if datetime.datetime.now(timezone.utc) - last > datetime.timedelta(hours=timeout):
                    logout_user(); session.clear()
                    return redirect('/login?timeout=1')
            session['last_activity'] = datetime.datetime.now(timezone.utc).isoformat()

@app.after_request
def set_security_headers(response):
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; img-src 'self' data:;")
    return response
