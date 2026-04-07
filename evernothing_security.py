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

    def encrypt_payload(data: bytes) -> bytes:
        """
        Encrypt raw bytes for S3 storage.
        Format: nonce(12) + AES-GCM ciphertext
        Plaintext format: SHA-256(data)(32) + data
        The prepended hash allows integrity verification on recovery
        without a separate manifest file.
        """
        import hashlib
        digest = hashlib.sha256(data).digest()  # 32 bytes
        nonce = os.urandom(12)
        ciphertext = aesgcm.encrypt(nonce, digest + data, None)
        return nonce + ciphertext

    def decrypt_payload(data: bytes) -> bytes:
        """
        Decrypt bytes produced by encrypt_payload.
        Raises ValueError if SHA-256 integrity check fails.
        """
        import hashlib
        nonce, ciphertext = data[:12], data[12:]
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)
        stored_digest, original = plaintext[:32], plaintext[32:]
        actual_digest = hashlib.sha256(original).digest()
        if stored_digest != actual_digest:
            raise ValueError("SHA-256 integrity check failed — payload may be corrupted or tampered")
        return original

else:
    def encrypt(t): return t
    def decrypt(t): return t
    def encrypt_payload(data: bytes) -> bytes: return data
    def decrypt_payload(data: bytes) -> bytes: return data


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
_SESSION_CHECK_INTERVAL = 60  # seconds between DB session validity checks (#19)

@app.before_request
def validate_session():
    if not current_user.is_authenticated:
        return
    if not session:
        return
    # #20: test bypass — set by test setUp to avoid user_sessions DB dependency
    if session.get('_test_bypass'):
        return

    now_utc = datetime.datetime.now(timezone.utc)
    remember_me = session.get('remember_me', False)  # #21: safe default

    if not remember_me:
        session.permanent = True
        last_activity = session.get('last_activity')
        if last_activity:
            last = datetime.datetime.fromisoformat(last_activity)
            timeout = int(os.environ.get('SESSION_TIMEOUT_HOURS', '2'))
            if now_utc - last > datetime.timedelta(hours=timeout):
                logout_user()
                session.clear()
                return redirect('/login?timeout=1')
        # #21: always set last_activity so new sessions are tracked immediately
        session['last_activity'] = now_utc.isoformat()

    if 'session_id' in session:
        # #19: only hit the DB once per _SESSION_CHECK_INTERVAL seconds
        last_check = session.get('_session_checked')
        if last_check:
            elapsed = (now_utc - datetime.datetime.fromisoformat(last_check)).total_seconds()
            if elapsed < _SESSION_CHECK_INTERVAL:
                return
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
        session['_session_checked'] = now_utc.isoformat()


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


def allowed_file(filename, stream=None):
    """Check file extension and optionally MIME type against allowlist."""
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'zip'}
    ALLOWED_MIMES = {
        'text/plain', 'application/pdf',
        'image/png', 'image/jpeg', 'image/gif',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/zip',
    }
    if not ('.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS):
        return False
    if stream is not None:
        import mimetypes
        header = stream.read(261)
        stream.seek(0)
        try:
            import magic
            mime = magic.from_buffer(header, mime=True)
        except ImportError:
            ext = filename.rsplit('.', 1)[1].lower()
            mime = mimetypes.types_map.get('.' + ext, '')
        if mime and mime not in ALLOWED_MIMES:
            return False
    return True


# --- Access control decorators ---
_ADMIN_TIMEOUT_HOURS = int(os.environ.get('ADMIN_SESSION_TIMEOUT_HOURS', '2'))

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect("/admin")
        # #10/#11: enforce admin session timeout
        login_time = session.get('admin_login_time')
        if login_time:
            age = datetime.datetime.now(timezone.utc) - datetime.datetime.fromisoformat(login_time)
            if age > datetime.timedelta(hours=_ADMIN_TIMEOUT_HOURS):
                session.pop('admin_logged_in', None)
                session.pop('admin_login_time', None)
                return redirect("/admin?timeout=1")
        return f(*args, **kwargs)
    return decorated


def api_login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated
