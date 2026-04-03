"""
evernothing_security.py — Security
Encryption/decryption, Flask-Login setup, session validation,
input validation, rate limiting helpers, access control decorators.
"""
import os, re, base64, datetime
from datetime import timezone
from functools import wraps
from flask import session, redirect, request, jsonify
from flask_login import LoginManager, UserMixin, logout_user, current_user
from evernothing_config import app, logger
from evernothing_db import db  # safe: evernothing_db only imports evernothing_config

# --- Encryption ---
try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
except ImportError:
    AESGCM = None

ENCRYPTION_ENABLED = os.environ.get('ENCRYPTION_ENABLED', 'false').lower() == 'true'
KEY_FILE = "secret.key"

if AESGCM:
    if os.path.exists(KEY_FILE):
        with open(KEY_FILE, 'rb') as f:
            KEY = f.read()
    else:
        KEY = AESGCM.generate_key(bit_length=256)
        with open(KEY_FILE, 'wb') as f:
            f.write(KEY)
    aesgcm = AESGCM(KEY)

    def encrypt(txt):
        if not ENCRYPTION_ENABLED or not txt:
            return txt if txt else ""
        try:
            nonce = os.urandom(12)
            return base64.b64encode(nonce + aesgcm.encrypt(nonce, txt.encode('utf-8'), None)).decode('utf-8')
        except Exception as e:
            logger.error(f"Enc Error: {e}")
            return txt

    def decrypt(txt):
        if not txt:
            return ""
        try:
            data = base64.b64decode(txt)
            return aesgcm.decrypt(data[:12], data[12:], None).decode('utf-8')
        except Exception:
            return txt
else:
    def encrypt(t): return t
    def decrypt(t): return t


# --- Flask-Login ---
login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.session_protection = "basic"


class User(UserMixin):
    def __init__(self, id, username):
        self.id = id
        self.username = username


@login_manager.user_loader
def load_user(uid):
    con = db()
    r = con.cursor().execute("SELECT id,username FROM users WHERE id=?", (uid,)).fetchone()
    con.close()
    return User(*r) if r else None


# --- Session validation ---
@app.before_request
def validate_session():
    if not current_user.is_authenticated:
        return
    if not session:
        return

    if not session.get('remember_me', False):
        session.permanent = True
        if 'last_activity' in session:
            last = datetime.datetime.fromisoformat(session['last_activity'])
            timeout = int(os.environ.get('SESSION_TIMEOUT_HOURS', '2'))
            if datetime.datetime.now(timezone.utc) - last > datetime.timedelta(hours=timeout):
                logout_user()
                session.clear()
                return redirect('/login?timeout=1')
        session['last_activity'] = datetime.datetime.now(timezone.utc).isoformat()

    if 'session_id' in session:
        con = db()
        valid = con.cursor().execute(
            "SELECT id FROM user_sessions WHERE session_id=? AND user_id=? AND logout_time IS NULL",
            (session['session_id'], current_user.id)
        ).fetchone()
        con.close()
        if not valid:
            logout_user()
            session.clear()
            return redirect('/login?invalid=1')


# --- Input validation ---
def validate_input(text, max_length=255, allow_empty=False):
    if text:
        text = text.strip()
    if not text and not allow_empty:
        return None, "Input cannot be empty"
    if text and len(text) > max_length:
        return None, f"Input too long (max {max_length} characters)"
    return text, None


def validate_email(email):
    if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
        return None, "Invalid email format"
    return email, None


def validate_password(password):
    if len(password) < 8:
        return None, "Password must be at least 8 characters"
    if not any(c.isupper() for c in password):
        return None, "Password must contain at least one uppercase letter"
    if not any(c.islower() for c in password):
        return None, "Password must contain at least one lowercase letter"
    if not any(c.isdigit() for c in password):
        return None, "Password must contain at least one number"
    return password, None


def allowed_file(filename):
    ALLOWED = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'zip'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED


# --- Access control decorators ---
def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect("/admin")
        return f(*args, **kwargs)
    return decorated


def api_login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated
