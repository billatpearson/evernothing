"""
Evernothing_Web/app.py
Flask application factory — single source of truth for the app object.
All other modules import `app`, `csrf`, `login_manager` from here.
"""
import os, datetime, secrets, logging
from flask import Flask
from flask_wtf.csrf import CSRFProtect
from flask_login import LoginManager

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.env'))
except ImportError:
    pass

# --- Logging ---
os.makedirs(os.path.join(os.path.dirname(__file__), '..', 'log'), exist_ok=True)
logging.basicConfig(
    filename=os.path.join(os.path.dirname(__file__), '..', 'log', 'evernothing.log'),
    level=logging.INFO,
    format='%(asctime)s %(name)s %(levelname)s %(message)s'
)
logger = logging.getLogger('evernothing')

# --- Flask app ---
app = Flask('EverNothing',
            template_folder=os.path.join(os.path.dirname(__file__), '..', 'Evernothing_UI'),
            static_folder=os.path.join(os.path.dirname(__file__), '..', 'static'))

_secret_key = os.environ.get('SECRET_KEY', '')
if not _secret_key:
    _secret_key = secrets.token_hex(32)
    logger.warning('SECRET_KEY not set — using random key. Sessions will not persist.')
app.secret_key = _secret_key

_remember_days = int(os.environ.get('REMEMBER_COOKIE_DAYS', '30'))
app.config.update(
    MAX_CONTENT_LENGTH        = 16 * 1024 * 1024,
    WTF_CSRF_ENABLED          = True,
    PERMANENT_SESSION_LIFETIME= datetime.timedelta(days=_remember_days),
    REMEMBER_COOKIE_DURATION  = datetime.timedelta(days=_remember_days),
    SESSION_COOKIE_SECURE     = os.environ.get('SESSION_COOKIE_SECURE', 'true').lower() == 'true',
    SESSION_COOKIE_HTTPONLY   = True,
    SESSION_COOKIE_SAMESITE   = 'Lax',
    REMEMBER_COOKIE_SECURE    = os.environ.get('SESSION_COOKIE_SECURE', 'true').lower() == 'true',
    REMEMBER_COOKIE_HTTPONLY  = True,
    REMEMBER_COOKIE_SAMESITE  = 'Lax',
    REMEMBER_COOKIE_NAME      = 'remember_token',
)

csrf = CSRFProtect(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.session_protection = 'basic'

BUILD_DATE = datetime.datetime.now().strftime('%m/%d/%y:%H:%M')
