"""
evernothing_config.py — Basic Configuration
Environment variables, constants, Flask app object, CSRF, logging.
"""
import os, datetime, logging, secrets
from flask import Flask
from flask_wtf.csrf import CSRFProtect

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env'))
except ImportError:
    pass

# --- AWS / S3 ---
try:
    from aws_config import S3_BUCKET_NAME, AWS_REGION, AWS_PROFILE
except ImportError:
    S3_BUCKET_NAME = os.environ.get('S3_BUCKET_NAME', 'evernothing-backup-2026')
    AWS_REGION     = os.environ.get('AWS_REGION', 'us-east-1')
    AWS_PROFILE    = os.environ.get('AWS_PROFILE', 'billspeiser2')

AWS_ACCESS_KEY_ID     = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
KMS_KEY_ID            = os.environ.get('KMS_KEY_ID')
NUM_BACKUPS           = int(os.environ.get('NUM_BACKUPS', '10'))
DEVICE_ID             = os.environ.get('DEVICE_ID', __import__('socket').gethostname())

# --- Database ---
DB = os.environ.get('DB_FILE', 'evernothing.db')

# --- Build date ---
BUILD_DATE = datetime.datetime.now().strftime("%m/%d/%y:%H:%M")

# --- Logging ---
os.makedirs('log', exist_ok=True)
logging.basicConfig(
    filename='log/evernothing.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# --- Flask app ---
app = Flask("EverNothing")

_secret_key = os.environ.get('SECRET_KEY', '')
if not _secret_key:
    _secret_key = secrets.token_hex(32)
    logger.warning("SECRET_KEY not set — using a random key. Sessions will not persist across restarts.")
app.secret_key = _secret_key

app.config['MAX_CONTENT_LENGTH']    = 16 * 1024 * 1024
app.config['WTF_CSRF_ENABLED']      = True
app.config['PERMANENT_SESSION_LIFETIME']  = datetime.timedelta(days=int(os.environ.get('REMEMBER_COOKIE_DAYS', '30')))
app.config['REMEMBER_COOKIE_DURATION']    = datetime.timedelta(days=int(os.environ.get('REMEMBER_COOKIE_DAYS', '30')))
app.config['SESSION_COOKIE_SECURE']       = os.environ.get('SESSION_COOKIE_SECURE', 'false').lower() == 'true'
app.config['SESSION_COOKIE_HTTPONLY']     = True
app.config['SESSION_COOKIE_SAMESITE']     = 'Lax'
app.config['REMEMBER_COOKIE_SECURE']      = os.environ.get('SESSION_COOKIE_SECURE', 'false').lower() == 'true'
app.config['REMEMBER_COOKIE_HTTPONLY']    = True
app.config['REMEMBER_COOKIE_SAMESITE']    = 'Lax'
app.config['REMEMBER_COOKIE_NAME']        = 'remember_token'

csrf = CSRFProtect(app)

@app.context_processor
def inject_build_date():
    return dict(build_date=BUILD_DATE)
