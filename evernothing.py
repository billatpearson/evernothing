# (Full single-file EverNothing application with all prompt instructions included as comments)
# ---------------------------------------------------------
"""
Unit test:
python test_evernothing.py -v
Prompt: 
 0. Include all prompt instructions as comment.
0.1 Document instructions for installing all packages and runtimes required.
0.2 Document instructions for accessing the web application.
0.3 Document instructions for accessing the web application fron amazon playstore.
0.4 build date will be appear as a footer to the all pages with the format (MM/DD/YY:HH:MM)
1. Python web application
2. Python web application that can be run on android phones
3. Web application will store notes in a database in a searchable key-value pair.
3.2 Users can search on key or value
3.2.1 Organize all key value pairs alphabetically by key.
3.3 Requires username and password login
3.3.0 If login fails display error message
3.3.1 After login user is redirected to a list of folders
3.3.2 If the user has zero folders the user will be able to create one.
3.4 Users see recently edited notes with timestamp with the format "MM/dd/yyyy HH:MM"
3.5 Per-user data isolation
3.6 Display matching key or value
3.6.1 Edit page with commit / cancel / choose folder select control/ delete with confirmation.
3.6.2 Note page will provide bread crumb links to root, folder, subfolder at the top page. 
3.6.2.1 If the note was edited, "Edited: MM/dd/yyyy HH:MM" which will link to a list of recently edits of this note notes.
3.6.3 On commit edit page will display confirmation message. Yes,no buttons. If contents are identical do not prompt.
3.7 Link to add note
3.7.1 Note = single-line, Contents = multiline (120w 40h) text area
3.7.2 Do not allow empty note or content or duplicate note name
3.7.2 Add or cancel
3.8 Subfolders
3.8.1 Create subfolder
3.8.1.1 List notes in folder above subfolder list
3.8.1.1.1 List subfolders in folder
3.8.1.2 Nest notes in subfolder
3.8.1.3 Delete with warning
3.8.1.4 rename folder
3.8.1.5 add note
3.9 Change password
3.10 Cancel button on register page
4. Security
5. AWS integration
6. Continuty
6.1 All record changes will be logged and maintained in separate tables.
6.2 User will be able to review changes in the log and have UI capabilities to roll back to previous change. Roll back dates should have the format of "MM/dd/yyyy HH:MM"

7. UI
7.01 All list and selects are sorted alphabetically.
7.1 background color "black"
7.2 text color "gold"
7.3 Link colar "gold"
7.4 Link hovor "red"
7.5 Text Inputs borders "red"
7.6 Text Inputs area borders "red"
7.8 Select inputs "red"
7.9 Delete link text "red"
7.10 Cancel link 1px border "red"
7.11 Input, text area, select horizontal spacing 2px
7.20 All pages shall provide a log out option on the main menu
8 Input position
8.1 "Add note" should appear in th folder options. 
9 S3 Buckets
9.1 sycrhronize all tables with an Aws S3 bucket  "evernothing011126" uesername "billspeiser2" continue on synch falure with warning
9.2 all AWS  data will be stored with AES-256 encryption.
9.2.1 include decryiption function to retrieve data using JSON and JWT.
9.2 all data will be stored with AES-256.
9.3 Include instructions for generating and installing keys. 
10.1 include instructions for restart of application in comments.
10.2 include python command script for database backup in comments.
10.3 include python command for database export in comments.
10.3.1 Export file will contain user name, note key, note value as a comma separated text file in comments. 
10.4 include instructions for running as a background process in comments. 
13. Security
13.1 logout function will expire all login_required data
14. ADMINISTRATION
14.1 System administrator.
14.1.1 login ( http://127.0.0.1:5000/admin)
14.1.2 administrator login user: "admin" password: "admin"
14.1.3 admin can search and provided a list of current user.
14.1.4 list will contain: user name, sorted alphabetically, number of notes in thier user space.
14.1.5 clicking on user name link will allow admin to change users Dialogs "new username," new user name" and  "new password", with verication.  
14.1.6 A Conformation dialog will bee displayed when the new user name will be commited.
14.1.7 all notes and note folder hierarcy will remain attached to the user selected. 
14.2 delete user
14.2.1 list of user to be selected with name, number of folders, number of folders, and last accessed date. 
15.2.2 provide UI to delete user, folder, and notes associated with the user.
14.2.3 admin privileges.
14.2.3.1 admin user can view all users in a list, user name, clear text password, and last accessed date.
14.2.3.2 admin can modify users user name, clear text password, and last accessed date.
16. Adnriod access.
16.1 include instructions for accessing application as android phone in comments.)
14.1.2 administrator login user: "admin" password: "admin"
14.1.3 admin can search and provided a list of current user.
14.1.4 list will contain: user name, sorted alphabetically, number of notes in thier user space.
14.1.5 clicking on user name link will allow admin to change users Dialogs "new username," new user name" with verication. 
14.1.6 A Conformation dialog will bee displayed when the new user name will be commited.
14.1.7 all notes and note folder hierarcy will remain attached to the user selected. 
14.2 delete user
14.2.1 list of user to be selected with name, number of folders, number of folders, and last accessed date. 
15.2.2 provide UI to delete user, folder, and notes associated with the user.
16. Android access
16.1 include instructions for accessing application as android phone in comments.
17. Deprecation.
17.1 Do not install libraries that have been deprecated.
17.2 Install libraries that are comptibile and safe.
17.3 Provide a script to install all required libries in the comments.
18. Change Control
18.1 All user changes will be logged in the following format:
18.2 JSON USERID current record and updated record. 
18.3 Store changes in a table named "note_history" with the following fields:
18.3.1 id
18.3.2 note_id
18.3.3 user_id
18.3.4 note_key (encrypted)
18.3.5 note_value (encrypted)
18.3.6 folder_id
18.3.7 updated_at (timestamp)
18.4 All user login sessions will be logged in a table named "user_sessions" with the following fields:
18.4.1 id
18.4.2 user_id
18.4.3 session_id
18.4.4 login_time
18.4.5 logout_time
18.4.6 ip_address
18.4.7 user_agent
INSTALLATION (0.1):
 pip install flask flask-login werkzeug boto3 cryptography itsdangerous pyjwt

ACCESS (0.2):
 python evernothing.py
 http://127.0.0.1:5000

ANDROID ACCESS (16.1):
 1. Install Termux from F-Droid.
 2. pkg install python
 3. pip install flask flask-login werkzeug boto3 cryptography
 3. pip install flask flask-login werkzeug boto3 cryptography itsdangerous pyjwt
 4. python evernothing.py
 5. Open Chrome/Browser and go to http://127.0.0.1:5000

RESTART:
 Ctrl+C then python evernothing.py

BACKGROUND:
 Linux/Mac: nohup python evernothing.py &
 Windows: start /B python evernothing.py
 Android (Termux): nohup python evernothing.py &

BACKUP:
 python - <<EOF
 import shutil
 shutil.copy('evernothing.db','evernothing_backup.db')
 EOF

DECRYPTION (9.2.1):
 python - <<EOF
 import sqlite3,json,base64,os,jwt
 from cryptography.hazmat.primitives.ciphers.aead import AESGCM
 with open('secret.key','rb') as f: key=f.read()
 aes=AESGCM(key)
 def dec(t):
  try: return aes.decrypt(base64.b64decode(t)[:12], base64.b64decode(t)[12:], None).decode('utf-8')
  except: return t
 c=sqlite3.connect('evernothing.db');cur=c.cursor()
 cur.execute('SELECT users.username,notes.note_key,notes.note_value FROM notes JOIN users ON users.id=notes.user_id')
 data = [{'user':r[0],'key':dec(r[1]),'value':dec(r[2])} for r in cur.fetchall()]
 print(json.dumps(data, indent=2))
 print("\nJWT Token:\n" + jwt.encode({"data": data}, key.hex(), algorithm="HS256"))
 c.close()
 EOF

EXPORT:
 python - <<EOF
 import sqlite3,csv
 c=sqlite3.connect('evernothing.db');cur=c.cursor()
 cur.execute('SELECT users.username,notes.note_key,notes.note_value FROM notes JOIN users ON users.id=notes.user_id')
 with open('evernothing_export.csv','w',newline='',encoding='utf-8') as f:
  w=csv.writer(f);w.writerow(['username','note_key','note_value']);w.writerows(cur.fetchall())
 c.close()
 EOF
"""

try:
    import os as _os
    from dotenv import load_dotenv
    load_dotenv(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '.env'))
except ImportError:
    pass

from flask import Flask, request, redirect, render_template_string, make_response, session
from flask_wtf.csrf import CSRFProtect
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer
from datetime import timezone
import sqlite3, datetime, json, os, base64, shutil, logging, re
try:
    import boto3
except ImportError:
    boto3 = None
try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
except ImportError:
    AESGCM = None
try:
    from aws_config import S3_BUCKET_NAME, AWS_REGION, AWS_PROFILE
except ImportError:
    S3_BUCKET_NAME = os.environ.get('S3_BUCKET_NAME', 'evernothing-backup-2026')
    AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')
    AWS_PROFILE = os.environ.get('AWS_PROFILE', 'billspeiser2')
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
KMS_KEY_ID = os.environ.get('KMS_KEY_ID')

# Configure logging
os.makedirs('log', exist_ok=True)
logging.basicConfig(
    filename='log/evernothing.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask("EverNothing")
_secret_key = os.environ.get('SECRET_KEY', '')
if not _secret_key:
    import secrets
    _secret_key = secrets.token_hex(32)
    logger.warning("SECRET_KEY not set — using a random key. Sessions will not persist across restarts.")
app.secret_key = _secret_key
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['WTF_CSRF_ENABLED'] = True
csrf = CSRFProtect(app)
_remember_days = int(os.environ.get('REMEMBER_COOKIE_DAYS', '30'))
app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(days=_remember_days)
app.config['REMEMBER_COOKIE_DURATION'] = datetime.timedelta(days=_remember_days)
app.config['SESSION_COOKIE_SECURE'] = os.environ.get('SESSION_COOKIE_SECURE', 'false').lower() == 'true'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['REMEMBER_COOKIE_SECURE'] = os.environ.get('SESSION_COOKIE_SECURE', 'false').lower() == 'true'
app.config['REMEMBER_COOKIE_HTTPONLY'] = True
app.config['REMEMBER_COOKIE_SAMESITE'] = 'Lax'
app.config['REMEMBER_COOKIE_NAME'] = 'remember_token'
DB = "evernothing.db"
BUILD_DATE = datetime.datetime.now().strftime("%m/%d/%y:%H:%M")

@app.context_processor
def inject_build_date():
    return dict(build_date=BUILD_DATE)

# --- ENCRYPTION ---
ENCRYPTION_ENABLED = os.environ.get('ENCRYPTION_ENABLED', 'false').lower() == 'true'
KEY_FILE = "secret.key"
if AESGCM:
    # Always load key for decryption, even if encryption is disabled
    if os.path.exists(KEY_FILE):
        with open(KEY_FILE, 'rb') as f: KEY = f.read()
        aesgcm = AESGCM(KEY)
    else:
        KEY = AESGCM.generate_key(bit_length=256)
        with open(KEY_FILE, 'wb') as f: f.write(KEY)
        aesgcm = AESGCM(KEY)

    def encrypt(txt):
        if not ENCRYPTION_ENABLED or not txt: return txt if txt else ""
        try:
            nonce = os.urandom(12)
            return base64.b64encode(nonce + aesgcm.encrypt(nonce, txt.encode('utf-8'), None)).decode('utf-8')
        except Exception as e:
            print(f"Enc Error: {e}")
            return txt

    def decrypt(txt):
        if not txt: return ""
        try:
            data = base64.b64decode(txt)
            return aesgcm.decrypt(data[:12], data[12:], None).decode('utf-8')
        except Exception:
            return txt
else:
    def encrypt(t): return t
    def decrypt(t): return t

login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.session_protection = "basic"

# Session validation
@app.before_request
def validate_session():
    if current_user.is_authenticated:
        # Empty session = user restored via remember-me cookie after browser restart
        if not session:
            return

        remember_me = session.get('remember_me', False)

        if not remember_me:
            session.permanent = True
            if 'last_activity' in session:
                last_activity = datetime.datetime.fromisoformat(session['last_activity'])
                timeout_hours = int(os.environ.get('SESSION_TIMEOUT_HOURS', '2'))
                if datetime.datetime.now(timezone.utc) - last_activity > datetime.timedelta(hours=timeout_hours):
                    logout_user()
                    session.clear()
                    return redirect('/login?timeout=1')
            session['last_activity'] = datetime.datetime.now(timezone.utc).isoformat()

        if 'session_id' in session:
            con = db()
            cur = con.cursor()
            valid = cur.execute(
                "SELECT id FROM user_sessions WHERE session_id=? AND user_id=? AND logout_time IS NULL",
                (session['session_id'], current_user.id)
            ).fetchone()
            con.close()
            if not valid:
                logout_user()
                session.clear()
                return redirect('/login?invalid=1')

# --- DATABASE ---
def db():
    con = sqlite3.connect(DB, check_same_thread=False, timeout=10)
    con.row_factory = sqlite3.Row
    return con
def init_db():
    c = db(); cur = c.cursor()
    cur.executescript("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        last_login TEXT,
        email TEXT
    );
    CREATE TABLE IF NOT EXISTS folders(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        name TEXT,
        parent_id INTEGER
    );
    CREATE TABLE IF NOT EXISTS notes(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        folder_id INTEGER,
        note_key TEXT,
        note_value TEXT,
        description TEXT,
        updated_at TEXT
    );
    CREATE TABLE IF NOT EXISTS note_history(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        note_id INTEGER,
        user_id INTEGER,
        note_key TEXT,
        note_value TEXT,
        description TEXT,
        folder_id INTEGER,
        updated_at TEXT
    );
    CREATE TABLE IF NOT EXISTS user_sessions(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        session_id TEXT,
        login_time TEXT,
        logout_time TEXT,
        ip_address TEXT,
        user_agent TEXT
    );
    CREATE TABLE IF NOT EXISTS attachments(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        note_id INTEGER,
        user_id INTEGER,
        filename TEXT,
        file_data BLOB,
        file_size INTEGER,
        uploaded_at TEXT
    );
    CREATE TABLE IF NOT EXISTS audit_log(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        action TEXT,
        entity_type TEXT,
        entity_id INTEGER,
        old_values TEXT,
        new_values TEXT,
        timestamp TEXT,
        ip_address TEXT
    );
    CREATE TABLE IF NOT EXISTS sync_queue(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        entity_type TEXT,
        entity_id INTEGER,
        operation TEXT,
        payload TEXT,
        changed_at TEXT,
        synced_at TEXT
    );
    """)
    for _col_sql in [
        "ALTER TABLE notes ADD COLUMN description TEXT",
        "ALTER TABLE note_history ADD COLUMN description TEXT",
    ]:
        try:
            cur.execute(_col_sql)
        except sqlite3.OperationalError:
            pass
    try: 
        cur.execute("ALTER TABLE users ADD COLUMN last_login TEXT")
    except sqlite3.OperationalError:
        pass  # Column already exists
    except Exception as e:
        print(f"Warning: Failed to add last_login column: {e}")
    try: 
        cur.execute("ALTER TABLE users ADD COLUMN email TEXT")
    except sqlite3.OperationalError:
        pass  # Column already exists
    except Exception as e:
        print(f"Warning: Failed to add email column: {e}")
    try:
        cur.execute("SELECT file_data FROM attachments LIMIT 1")
    except sqlite3.OperationalError:
        cur.execute("DROP TABLE IF EXISTS attachments")
        cur.execute("""
            CREATE TABLE attachments(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                note_id INTEGER,
                user_id INTEGER,
                filename TEXT,
                file_data BLOB,
                file_size INTEGER,
                uploaded_at TEXT
            )
        """)
    except Exception as e:
        print(f"Warning: Attachments table check failed: {e}")
    try:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS sync_queue(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_type TEXT,
                entity_id INTEGER,
                operation TEXT,
                payload TEXT,
                changed_at TEXT,
                synced_at TEXT
            )
        """)
    except Exception as e:
        print(f"Warning: sync_queue migration failed: {e}")
    try:
        cur.execute("CREATE INDEX IF NOT EXISTS idx_notes_user ON notes(user_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_folders_user ON folders(user_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_attachments_note ON attachments(note_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_log(user_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_audit_entity ON audit_log(entity_type, entity_id)")
    except Exception as e:
        print(f"Warning: Failed to create indexes: {e}")
    c.commit()
    c.close()

init_db()

# --- BACKUP ON STARTUP ---
def backup_database():
    """Backup database with timestamp on application launch"""
    if os.path.exists(DB):
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"Backups/evernothing_backup_{timestamp}.db"
        os.makedirs("Backups", exist_ok=True)
        shutil.copy(DB, backup_file)
        print(f"Database backed up to: {backup_file}")

backup_database()

def compress_old_backups(days=5, backup_dir="Backups"):
    """Compress .db backup files older than `days` days into .gz archives."""
    import gzip
    cutoff = datetime.datetime.now() - datetime.timedelta(days=days)
    if not os.path.isdir(backup_dir):
        return
    for fname in os.listdir(backup_dir):
        if not fname.endswith(".db"):
            continue
        fpath = os.path.join(backup_dir, fname)
        if datetime.datetime.fromtimestamp(os.path.getmtime(fpath)) < cutoff:
            gz_path = fpath + ".gz"
            try:
                with open(fpath, "rb") as f_in, gzip.open(gz_path, "wb") as f_out:
                    shutil.copyfileobj(f_in, f_out)
                os.remove(fpath)
                print(f"Compressed backup: {gz_path}")
            except Exception as e:
                print(f"Compress error ({fname}): {e}")

compress_old_backups()

# --- AWS SYNC ---
def _s3_client():
    """Return a boto3 S3 client using env vars or profile."""
    if AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY:
        return boto3.client('s3', region_name=AWS_REGION,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
    try:
        return boto3.Session(profile_name=AWS_PROFILE).client('s3')
    except Exception:
        return boto3.client('s3', region_name=AWS_REGION)

DEVICE_ID = os.environ.get('DEVICE_ID', __import__('socket').gethostname())
_bucket_policy_applied = False

def queue_change(cur, entity_type, entity_id, operation):
    """Record a change in sync_queue with the complete row as payload."""
    payload = {}
    try:
        if entity_type == 'note':
            r = cur.execute("SELECT id,user_id,folder_id,note_key,note_value,description,updated_at FROM notes WHERE id=?", (entity_id,)).fetchone()
            if r:
                payload = {'id': r[0], 'user_id': r[1], 'folder_id': r[2], 'note_key': r[3], 'note_value': r[4], 'description': r[5], 'updated_at': r[6]}
        elif entity_type == 'folder':
            r = cur.execute("SELECT id,user_id,name,parent_id FROM folders WHERE id=?", (entity_id,)).fetchone()
            if r:
                payload = {'id': r[0], 'user_id': r[1], 'name': r[2], 'parent_id': r[3]}
    except Exception as e:
        logger.warning(f"queue_change fetch failed: {e}")
    cur.execute(
        "INSERT INTO sync_queue (entity_type, entity_id, operation, payload, changed_at) VALUES(?,?,?,?,?)",
        (entity_type, entity_id, operation, json.dumps(payload),
         datetime.datetime.now(timezone.utc).isoformat())
    )

# Minimum required S3 actions for this application
_REQUIRED_S3_ACTIONS = [
    "s3:PutObject",
    "s3:GetObject",
    "s3:ListBucket",
    "s3:HeadBucket",
    "s3:CreateBucket",
    "s3:PutBucketPolicy",
    "s3:PutBucketVersioning",
    "s3:PutPublicAccessBlock"
]

def get_iam_policy():
    """Return the least-privilege IAM policy document scoped to the configured bucket."""
    return {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "EverNothingObjectAccess",
                "Effect": "Allow",
                "Action": ["s3:PutObject", "s3:GetObject"],
                "Resource": f"arn:aws:s3:::{S3_BUCKET_NAME}/*"
            },
            {
                "Sid": "EverNothingBucketAccess",
                "Effect": "Allow",
                "Action": [
                    "s3:ListBucket",
                    "s3:HeadBucket",
                    "s3:CreateBucket",
                    "s3:PutBucketPolicy",
                    "s3:PutBucketVersioning",
                    "s3:PutPublicAccessBlock"
                ],
                "Resource": f"arn:aws:s3:::{S3_BUCKET_NAME}"
            }
        ]
    }


def _apply_bucket_policy(s3, bucket_name):
    """Apply a least-privilege bucket policy scoped to the calling IAM principal."""
    try:
        sts_kwargs = {'region_name': AWS_REGION}
        if AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY:
            sts_kwargs['aws_access_key_id'] = AWS_ACCESS_KEY_ID
            sts_kwargs['aws_secret_access_key'] = AWS_SECRET_ACCESS_KEY
        caller_arn = boto3.client('sts', **sts_kwargs).get_caller_identity()['Arn']
    except Exception as e:
        logger.warning(f"Could not determine caller ARN for bucket policy: {e}")
        return

    policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "DenyAllExceptCallerPrincipal",
                "Effect": "Deny",
                "Principal": "*",
                "Action": "s3:*",
                "Resource": [
                    f"arn:aws:s3:::{bucket_name}",
                    f"arn:aws:s3:::{bucket_name}/*"
                ],
                "Condition": {
                    "StringNotEquals": {
                        "aws:PrincipalArn": caller_arn
                    }
                }
            },
            {
                "Sid": "DenyInsecureTransport",
                "Effect": "Deny",
                "Principal": "*",
                "Action": "s3:*",
                "Resource": [
                    f"arn:aws:s3:::{bucket_name}",
                    f"arn:aws:s3:::{bucket_name}/*"
                ],
                "Condition": {
                    "Bool": {"aws:SecureTransport": "false"}
                }
            }
        ]
    }
    try:
        s3.put_bucket_policy(Bucket=bucket_name, Policy=json.dumps(policy))
        logger.info(f"Bucket policy applied to {bucket_name}")
    except Exception as e:
        logger.warning(f"Could not apply bucket policy: {e}")


def sync_s3():
    """Upload unsynced delta changes and full DB backup to S3."""
    if not boto3:
        logger.warning("S3 sync skipped: boto3 not available")
        return
    try:
        import io
        s3 = _s3_client()
        global _bucket_policy_applied
        if not _bucket_policy_applied:
            _apply_bucket_policy(s3, S3_BUCKET_NAME)
            _bucket_policy_applied = True
        extra_json = {"ServerSideEncryption": "aws:kms", "ContentType": "application/json"}
        extra_db = {"ServerSideEncryption": "aws:kms"}
        if KMS_KEY_ID:
            extra_json["SSEKMSKeyId"] = KMS_KEY_ID
            extra_db["SSEKMSKeyId"] = KMS_KEY_ID

        # --- delta changes ---
        con = db()
        cur = con.cursor()
        cur.execute("SELECT id, entity_type, entity_id, operation, payload, changed_at FROM sync_queue WHERE synced_at IS NULL")
        rows = cur.fetchall()
        if rows:
            changes = [
                {"op": r[3], "entity": r[1], "id": r[2], "data": json.loads(r[4]), "at": r[5]}
                for r in rows
            ]
            ts = datetime.datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            s3_key = f"changes/{DEVICE_ID}/{ts}.json"
            s3.upload_fileobj(io.BytesIO(json.dumps(changes).encode("utf-8")), S3_BUCKET_NAME, s3_key, ExtraArgs=extra_json)
            ids = [r[0] for r in rows]
            now = datetime.datetime.now(timezone.utc).isoformat()
            cur.execute(
                f"UPDATE sync_queue SET synced_at=? WHERE id IN ({','.join('?'*len(ids))})",
                [now] + ids
            )
            con.commit()
            logger.info(f"S3 delta sync: {len(changes)} change(s) -> s3://{S3_BUCKET_NAME}/{s3_key}")
        con.close()

        # --- full DB backup ---
        ts = datetime.datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        with open(DB, 'rb') as f:
            db_bytes = f.read()
        s3.upload_fileobj(io.BytesIO(db_bytes), S3_BUCKET_NAME, DB, ExtraArgs=extra_db)
        s3.upload_fileobj(io.BytesIO(db_bytes), S3_BUCKET_NAME, f"backups/{DB}.{ts}", ExtraArgs=extra_db)
        logger.info(f"S3 DB backup: s3://{S3_BUCKET_NAME}/{DB} + backups/{DB}.{ts}")
        print("S3 ASynch")
    except Exception as e:
        logger.error(f"S3 Sync Error: {e}")
        print(f"S3 Sync Error: {e}")

def restore_from_s3():
    """Download DB from S3 if local file is missing (recovery on startup)."""
    if not boto3 or os.path.exists(DB):
        return
    try:
        s3 = _s3_client()
        s3.download_file(S3_BUCKET_NAME, DB, DB)
        logger.info(f"Restored {DB} from s3://{S3_BUCKET_NAME}/{DB}")
        print(f"Restored database from S3: {DB}")
    except Exception as e:
        logger.warning(f"S3 restore skipped: {e}")

# --- AUTH ---
class User(UserMixin):
    def __init__(self, id, username):
        self.id = id
        self.username = username

@login_manager.user_loader
def load_user(uid):
    con = db()
    r = con.cursor().execute(
        "SELECT id,username FROM users WHERE id=?", (uid,)
    ).fetchone()
    con.close()
    return User(*r) if r else None

def validate_input(text, max_length=255, allow_empty=False):
    """Validate and sanitize user input"""
    if text:
        text = text.strip()
    if not text and not allow_empty:
        return None, "Input cannot be empty"
    if text and len(text) > max_length:
        return None, f"Input too long (max {max_length} characters)"
    return text, None

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        return None, "Invalid email format"
    return email, None

def validate_password(password):
    """Validate password strength"""
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
    """Check if file extension is allowed"""
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'zip'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def format_date(iso_str):
    try:
        return datetime.datetime.fromisoformat(iso_str).strftime("%m/%d/%Y %H:%M")
    except Exception:
        return iso_str 

def get_breadcrumbs(cur, fid, uid):
    crumbs = []
    while fid:
        f = cur.execute("SELECT id,name,parent_id FROM folders WHERE id=? AND user_id=?", (fid, uid)).fetchone()
        if not f: break
        crumbs.insert(0, (f[0], decrypt(f[1])))
        fid = f[2]
    return crumbs

def log_change(cur, user_id, action, entity_type, entity_id, old_values, new_values, ip_addr):
    cur.execute(
        "INSERT INTO audit_log (user_id, action, entity_type, entity_id, old_values, new_values, timestamp, ip_address) VALUES(?,?,?,?,?,?,?,?)",
        (user_id, action, entity_type, entity_id, json.dumps(old_values), json.dumps(new_values), datetime.datetime.now(timezone.utc).isoformat(), ip_addr)
    )

@app.errorhandler(404)
def not_found(error):
    logger.warning(f"404 error: {request.url}")
    return render_template_string(STYLE + "<h3>404 - Page Not Found</h3><a href=/>Home</a>"), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"500 error: {error}")
    return render_template_string(STYLE + "<h3>500 - Internal Server Error</h3><a href=/>Home</a>"), 500

# --- ROUTES ---
@app.route("/")
@login_required
def index():
    con = db()
    cur = con.cursor()
    cur.execute("SELECT id,name FROM folders WHERE user_id=? AND parent_id IS NULL", (current_user.id,))
    folders = sorted([(r[0], decrypt(r[1])) for r in cur.fetchall()], key=lambda x: x[1].lower())
    
    cur.execute("SELECT id,note_key,updated_at FROM notes WHERE user_id=? ORDER BY updated_at DESC LIMIT 10", (current_user.id,))
    recent = [(r[0], decrypt(r[1]), format_date(r[2])) for r in cur.fetchall()]
    con.close()
    
    return render_template_string(T_FOLDERS, folders=folders, recent=recent)

@app.route("/folder/add", methods=["GET","POST"])
@login_required
def add_folder():
    if request.method == "POST":
        name, error = validate_input(request.form.get('name', ''))
        if error:
            return render_template_string(T_ADD_FOLDER, error=error)
        
        con = db(); cur = con.cursor()
        try:
            cur.execute(
                "INSERT INTO folders (user_id, name, parent_id) VALUES(?,?,NULL)",
                (current_user.id, encrypt(name))
            )
            queue_change(cur, 'folder', cur.lastrowid, 'INSERT')
            con.commit()
            sync_s3()
            logger.info(f"User {current_user.id} created folder: {name}")
        except Exception as e:
            logger.error(f"Error creating folder: {e}")
            con.rollback()
            return render_template_string(T_ADD_FOLDER, error="Failed to create folder")
        finally:
            con.close()
        return redirect("/")
    return render_template_string(T_ADD_FOLDER)

@app.route("/folder/<int:pid>/add_folder", methods=["GET","POST"])
@login_required
def add_subfolder(pid):
    if request.method == "POST":
        con = db(); cur = con.cursor()
        cur.execute(
            "INSERT INTO folders (user_id, name, parent_id) VALUES(?,?,?)",
            (current_user.id, encrypt(request.form['name']), pid)
        )
        queue_change(cur, 'folder', cur.lastrowid, 'INSERT')
        con.commit()
        sync_s3()
        con.close()        
        return redirect(f"/folder/{pid}")
    return render_template_string(T_ADD_SUBFOLDER, pid=pid)

def delete_recursive(cur, fid, uid):
    cur.execute("SELECT id FROM folders WHERE parent_id=? AND user_id=?", (fid, uid))
    for sub in cur.fetchall():
        delete_recursive(cur, sub[0], uid)
    cur.execute("DELETE FROM notes WHERE folder_id=? AND user_id=?", (fid, uid))
    cur.execute("DELETE FROM folders WHERE id=? AND user_id=?", (fid, uid))

@app.route("/folder/delete/<int:fid>", methods=["GET","POST"])
@login_required
def delete_folder(fid):
    con = db(); cur = con.cursor() 
    f = cur.execute("SELECT name,parent_id FROM folders WHERE id=? AND user_id=?", (fid, current_user.id)).fetchone()
    if not f:
        con.close()
        return redirect("/")

    if request.method == "POST":
        delete_recursive(cur, fid, current_user.id)
        queue_change(cur, 'folder', fid, 'DELETE')
        con.commit()
        con.close()
        sync_s3()
        return redirect(f"/folder/{f[1]}" if f[1] else "/")

    result = render_template_string(T_DELETE_FOLDER, f=(decrypt(f[0]), f[1])) if f else redirect("/")
    con.close()
    return result

@app.route("/folder/rename/<int:fid>", methods=["GET","POST"])
@login_required
def rename_folder(fid):
    con = db(); cur = con.cursor()
    f = cur.execute("SELECT name,parent_id FROM folders WHERE id=? AND user_id=?", (fid, current_user.id)).fetchone()
    if not f:
        con.close()
        return redirect("/")
    if request.method == "POST":
        cur.execute("UPDATE folders SET name=? WHERE id=? AND user_id=?", (encrypt(request.form['name']), fid, current_user.id))
        queue_change(cur, 'folder', fid, 'UPDATE')
        con.commit()
        con.close()
        sync_s3()
        return redirect(f"/folder/{fid}")
    con.close()
    return render_template_string(T_RENAME_FOLDER, f=(decrypt(f[0]), f[1]), fid=fid)

@app.route("/note/delete/<int:nid>", methods=["GET","POST"])
@login_required
def delete_note(nid):
    con = db(); cur = con.cursor()
    n = cur.execute("SELECT folder_id, note_key FROM notes WHERE id=? AND user_id=?", (nid, current_user.id)).fetchone()
    if not n:
        con.close()
        return redirect("/")
    if request.method == "POST":
        cur.execute("DELETE FROM notes WHERE id=? AND user_id=?", (nid, current_user.id))
        queue_change(cur, 'note', nid, 'DELETE')
        con.commit()
        con.close()
        sync_s3()
        return redirect(f"/folder/{n[0]}" if n[0] else "/")
    con.close()
    return render_template_string(T_DELETE_NOTE, n=(n[0], decrypt(n[1])))

@app.route("/change_password", methods=["GET","POST"])
@login_required
def change_password():
    error = None
    if request.method == "POST":
        con = db()
        cur = con.cursor()
        r = cur.execute("SELECT password FROM users WHERE id=?", (current_user.id,)).fetchone()
        if r and check_password_hash(r[0], request.form['old_password']):
            new_password = request.form['new_password']
            if new_password != request.form.get('verify_password', ''):
                con.close()
                error = "New passwords do not match"
            else:
                cur.execute("UPDATE users SET password=? WHERE id=?", (generate_password_hash(new_password), current_user.id))
                con.commit()
                con.close()
                sync_s3()
                return redirect("/")
        else:
            con.close()
            error = "Invalid old password"
    return render_template_string(T_CHANGE_PASSWORD, error=error)

@app.route("/search")
@login_required
def search():
    q = request.args.get('q', '').strip()
    folder_filter = request.args.get('folder', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    use_regex = request.args.get('regex', '') == 'on'
    search_history = request.args.get('history', '') == 'on'
    
    if not q or len(q) > 100:
        return render_template_string(T_SEARCH, notes=[], q=q, folders=[], folder_filter=folder_filter, folder_results=[])
    
    con = db()
    cur = con.cursor()
    try:
        # Get folders for filter dropdown
        cur.execute("SELECT id, name FROM folders WHERE user_id=?", (current_user.id,))
        folders = [(f[0], decrypt(f[1])) for f in cur.fetchall()]
        
        # Build query
        table = "note_history" if search_history else "notes"
        query = f"SELECT id, note_key, note_value, updated_at, folder_id FROM {table} WHERE user_id=?"
        params = [current_user.id]
        
        if folder_filter:
            query += " AND folder_id=?"
            params.append(folder_filter)
        
        if date_from:
            query += " AND updated_at >= ?"
            params.append(date_from)
        
        if date_to:
            query += " AND updated_at <= ?"
            params.append(date_to)
        
        cur.execute(query, params)
        notes = []
        
        if use_regex:
            import re
            try:
                pattern = re.compile(q, re.IGNORECASE)
                for r in cur.fetchall():
                    k, v = decrypt(r[1]), decrypt(r[2])
                    if pattern.search(k) or pattern.search(v):
                        notes.append((r[0], k, format_date(r[3])))
            except re.error:
                notes = []
        else:
            q_lower = q.lower()
            for r in cur.fetchall():
                k, v = decrypt(r[1]), decrypt(r[2])
                if q_lower in k.lower() or q_lower in v.lower():
                    notes.append((r[0], k, format_date(r[3])))

        # Search folder names (case-insensitive)
        folder_results = []
        if not search_history:
            cur.execute("SELECT id, name FROM folders WHERE user_id=?", (current_user.id,))
            if use_regex:
                try:
                    pattern = re.compile(q, re.IGNORECASE)
                    folder_results = [(r[0], decrypt(r[1])) for r in cur.fetchall() if pattern.search(decrypt(r[1]))]
                except re.error:
                    folder_results = []
            else:
                folder_results = [(r[0], decrypt(r[1])) for r in cur.fetchall() if q_lower in decrypt(r[1]).lower()]
            folder_results.sort(key=lambda x: x[1].lower())

        notes.sort(key=lambda x: x[1].lower())
    except Exception as e:
        logger.error(f"Search error: {e}")
        notes = []
        folders = []
        folder_results = []
    finally:
        con.close()
    
    return render_template_string(T_SEARCH, notes=notes, q=q, folders=folders,
                                 folder_results=folder_results,
                                 folder_filter=folder_filter, date_from=date_from, 
                                 date_to=date_to, use_regex=use_regex, search_history=search_history)

@app.route("/export")
@login_required
def export_json():
    con = db()
    cur = con.cursor()
    cur.execute("""
        SELECT n.note_key, n.note_value, n.updated_at, f.name, n.description
        FROM notes n
        LEFT JOIN folders f ON n.folder_id = f.id
        WHERE n.user_id=?
    """, (current_user.id,))
    data = [{"note": decrypt(r[0]), "content": decrypt(r[1]), "description": decrypt(r[4]) if r[4] else "", "updated_at": r[2], "folder": decrypt(r[3]) if r[3] else None} for r in cur.fetchall()]
    con.close()
    resp = make_response(json.dumps(data, indent=2))
    resp.headers['Content-Disposition'] = 'attachment; filename=notes.json'
    resp.headers['Content-Type'] = 'application/json'
    return resp

@app.route("/folder/<int:fid>")
@login_required
def view_folder(fid):
    con = db()
    cur = con.cursor()
    folder = cur.execute("SELECT id,name,parent_id FROM folders WHERE id=? AND user_id=?", (fid, current_user.id)).fetchone()
    if not folder:
        con.close()
        return redirect("/")

    cur.execute("SELECT id,name FROM folders WHERE user_id=? AND parent_id=?", (current_user.id, fid))
    subfolders = sorted([(r[0], decrypt(r[1])) for r in cur.fetchall()], key=lambda x: x[1].lower())
    
    cur.execute("SELECT id,note_key FROM notes WHERE user_id=? AND folder_id=?", (current_user.id, fid))
    notes = sorted([(r[0], decrypt(r[1])) for r in cur.fetchall()], key=lambda x: x[1].lower())
    con.close()
    
    return render_template_string(T_NOTES, notes=notes, subfolders=subfolders, folder=(folder[0], decrypt(folder[1]), folder[2]))

@app.route("/add/<int:fid>", methods=["GET","POST"])
@login_required
def add(fid):
    from markupsafe import escape
    error = None
    note_val = ""
    content_val = ""
    desc_val = ""
    if request.method == "POST":
        note_val = str(escape(request.form['note']))
        content_val = str(escape(request.form['content']))
        con = db(); cur = con.cursor()
        
        desc_val = request.form.get('description', '')[:255]
        if not note_val.strip() or not content_val.strip():
            error = "Note and content cannot be empty"
            con.close()
        else:
            cur.execute("SELECT note_key FROM notes WHERE user_id=?", (current_user.id,))
            if any(decrypt(r[0]).strip().lower() == str(note_val).strip().lower() for r in cur.fetchall()):
                error = "Note name already exists"
                con.close()
            else:
                cur.execute(
                    "INSERT INTO notes (user_id, folder_id, note_key, note_value, description, updated_at) VALUES(?,?,?,?,?,?)",
                    (current_user.id, fid, encrypt(note_val), encrypt(content_val), encrypt(desc_val), datetime.datetime.now(timezone.utc).isoformat())
                )
                nid = cur.lastrowid
                log_change(cur, current_user.id, 'CREATE', 'note', nid, {}, {'note': note_val, 'content': content_val, 'description': desc_val, 'folder_id': fid}, request.remote_addr)
                cur.execute(
                    "INSERT INTO note_history (note_id, user_id, note_key, note_value, description, folder_id, updated_at) VALUES(?,?,?,?,?,?,?)",
                    (nid, current_user.id, encrypt(note_val), encrypt(content_val), encrypt(desc_val), fid, datetime.datetime.now(timezone.utc).isoformat())
                )
                if 'file' in request.files and request.files['file'].filename:
                    file = request.files['file']
                    if not allowed_file(file.filename):
                        error = "File type not allowed"
                        con.close()
                    else:
                        filename = file.filename[:255]  # Limit filename length
                        file_data = file.read()
                        if len(file_data) > 0 and len(file_data) <= app.config['MAX_CONTENT_LENGTH']:
                            cur.execute(
                                "INSERT INTO attachments (note_id, user_id, filename, file_data, file_size, uploaded_at) VALUES(?,?,?,?,?,?)",
                                (nid, current_user.id, filename, file_data, len(file_data), datetime.datetime.now(timezone.utc).isoformat())
                            )
                            log_change(cur, current_user.id, 'CREATE', 'attachment', cur.lastrowid, {}, {'note_id': nid, 'filename': filename, 'size': len(file_data)}, request.remote_addr)
                        else:
                            error = "File too large or empty"
                            con.close()
                con.commit()
                queue_change(cur, 'note', nid, 'INSERT')
                con.commit()
                con.close()
                sync_s3()
                return redirect(f"/folder/{fid}")
    return render_template_string(T_ADD, fid=fid, error=error, note=note_val, content=content_val, description=desc_val)

@app.route("/edit/<int:id>", methods=["GET","POST"])
@login_required
def edit(id):
    con = db()
    cur = con.cursor()
    folders = cur.execute(
        "SELECT id,name FROM folders WHERE user_id=?",
        (current_user.id,)
    ).fetchall()
    folders = sorted([(f[0], decrypt(f[1])) for f in folders], key=lambda x: x[1].lower())

    cur.execute(
        "SELECT note_key,note_value,folder_id,updated_at,description FROM notes WHERE id=? AND user_id=?",
        (id, current_user.id),
    )
    row = cur.fetchone()
    if not row:
        con.close()
        return redirect("/")
    note = [decrypt(row[0]), decrypt(row[1]), row[2], row[3], decrypt(row[4]) if row[4] else ""]
    note[3] = format_date(note[3])

    try:
        cur.execute("SELECT id,filename,file_size FROM attachments WHERE note_id=? AND user_id=?", (id, current_user.id))
        attachments = cur.fetchall()
    except:
        attachments = []

    if request.method == "POST":
        # Check if this is a file upload (has file and no note/content fields)
        if 'file' in request.files and request.files['file'].filename and 'note' not in request.form:
            file = request.files['file']
            if not allowed_file(file.filename):
                con.close()
                return render_template_string(T_EDIT, note=note, folders=folders, breadcrumbs=[], id=id, attachments=[], error="File type not allowed")
            
            filename = file.filename[:255]  # Limit filename length
            file_data = file.read()
            if len(file_data) > 0 and len(file_data) <= app.config['MAX_CONTENT_LENGTH']:
                cur.execute(
                    "INSERT INTO attachments (note_id, user_id, filename, file_data, file_size, uploaded_at) VALUES(?,?,?,?,?,?)",
                    (id, current_user.id, filename, file_data, len(file_data), datetime.datetime.now(timezone.utc).isoformat())
                )
                log_change(cur, current_user.id, 'CREATE', 'attachment', cur.lastrowid, {}, {'note_id': id, 'filename': filename, 'size': len(file_data)}, request.remote_addr)
                con.commit()
                con.close()
                sync_s3()
                return redirect(f"/edit/{id}")
            else:
                con.close()
                return render_template_string(T_EDIT, note=note, folders=folders, breadcrumbs=[], id=id, attachments=[], error="File too large or empty")

        # Handle note edit
        if 'note' in request.form and 'content' in request.form:
            new_desc = request.form.get('description', '')[:255]
            if note[0] == request.form['note'] and note[1] == request.form['content'] and str(note[2]) == str(request.form.get('folder_id')) and note[4] == new_desc:
                con.close()
                return redirect("/")

            if request.form.get('confirm') == 'yes':
                now = datetime.datetime.now(timezone.utc).isoformat()
                old_vals = {'note': note[0], 'content': note[1], 'description': note[4], 'folder_id': note[2]}
                new_vals = {'note': request.form['note'], 'content': request.form['content'], 'description': new_desc, 'folder_id': request.form.get('folder_id')}
                cur.execute(
                    "UPDATE notes SET note_key=?,note_value=?,description=?,folder_id=?,updated_at=? WHERE id=? AND user_id=?",
                    (
                        encrypt(request.form['note']),
                        encrypt(request.form['content']),
                        encrypt(new_desc),
                        request.form.get('folder_id'),
                        now,
                        id,
                        current_user.id,
                    ),
                )
                log_change(cur, current_user.id, 'UPDATE', 'note', id, old_vals, new_vals, request.remote_addr)
                cur.execute(
                    "INSERT INTO note_history (note_id, user_id, note_key, note_value, description, folder_id, updated_at) VALUES(?,?,?,?,?,?,?)",
                    (id, current_user.id, encrypt(request.form['note']), encrypt(request.form['content']), encrypt(new_desc), request.form.get('folder_id'), now)
                )
                con.commit()
                queue_change(cur, 'note', id, 'UPDATE')
                con.commit()
                con.close()
                sync_s3()
                return redirect("/")
            else:
                con.close()
                return render_template_string(T_EDIT_CONFIRM, note=[request.form['note'], request.form['content'], request.form.get('folder_id'), None, new_desc], id=id)

    breadcrumbs = get_breadcrumbs(cur, note[2], current_user.id)
    con.close()
    return render_template_string(T_EDIT, note=note, folders=folders, breadcrumbs=breadcrumbs, id=id, attachments=attachments)

@app.route("/history/<int:nid>")
@login_required
def history(nid):
    con = db()
    cur = con.cursor()
    cur.execute("SELECT id,note_key,updated_at FROM note_history WHERE note_id=? AND user_id=? ORDER BY updated_at DESC", (nid, current_user.id))
    history = [(h[0], decrypt(h[1]), format_date(h[2])) for h in cur.fetchall()]
    con.close()
    return render_template_string(T_HISTORY, history=history, nid=nid)

@app.route("/history/restore/<int:hid>", methods=["GET","POST"])
@login_required
def restore_history(hid):
    con = db(); cur = con.cursor()
    h = cur.execute("SELECT note_id,note_key,note_value,folder_id FROM note_history WHERE id=? AND user_id=?", (hid, current_user.id)).fetchone()
    if not h:
        con.close()
        return redirect("/")
    if request.method == "GET":
        note_key_preview = decrypt(h[1])
        con.close()
        return render_template_string(
            STYLE + """
<nav class="nav">
  <span class="nav-brand">&#9670; EverNothing</span>
  <a href=/history/{{nid}}>&#8592; Back</a>
  <a href=/logout class="nav-logout">Logout</a>
</nav>
<div class="container">
  <div class="confirm-box">
    <h3>Confirm Rollback</h3>
    <p>Restore note to version: <b>{{key}}</b>?</p>
    <form method=post>
      <input type=hidden name=csrf_token value="{{ csrf_token() }}">
      <div class="btn-group">
        <button class="btn btn-primary">Yes, Restore</button>
        <a href=/history/{{nid}} class="btn">Cancel</a>
      </div>
    </form>
  </div>
</div>""",
            key=note_key_preview, nid=h[0]
        )
    now = datetime.datetime.now(timezone.utc).isoformat()
    cur.execute(
        "UPDATE notes SET note_key=?,note_value=?,folder_id=?,updated_at=? WHERE id=? AND user_id=?",
        (h[1], h[2], h[3], now, h[0], current_user.id)
    )
    cur.execute(
        "INSERT INTO note_history (note_id, user_id, note_key, note_value, folder_id, updated_at) VALUES(?,?,?,?,?,?)",
        (h[0], current_user.id, h[1], h[2], h[3], now)
    )
    con.commit()
    con.close()
    sync_s3()
    return redirect(f"/edit/{h[0]}")

# --- ADMIN AUTH HELPER ---
def admin_required(f):
    """Decorator to enforce admin session on every admin route."""
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect("/admin")
        return f(*args, **kwargs)
    return decorated

# --- ADMIN ---
@app.route("/admin", methods=["GET","POST"])
def admin_login():
    if request.method == "POST":
        admin_user = os.environ.get('ADMIN_USER', 'admin')
        admin_pass = os.environ.get('ADMIN_PASS', 'admin')
        if request.form.get("username") == admin_user and request.form.get("password") == admin_pass:
            session['admin_logged_in'] = True
            return redirect("/admin/dashboard")
        return render_template_string(T_ADMIN_LOGIN, error="Invalid credentials")
    return render_template_string(T_ADMIN_LOGIN)

@app.route("/admin/dashboard")
@admin_required
def admin_dashboard():
    q = request.args.get('q', '')
    con = db()
    cur = con.cursor()
    sql = """
        SELECT u.id, u.username, COUNT(DISTINCT n.id), COUNT(DISTINCT f.id), u.last_login
        FROM users u 
        LEFT JOIN notes n ON u.id = n.user_id 
        LEFT JOIN folders f ON u.id = f.user_id
        WHERE u.username LIKE ?
        GROUP BY u.id 
        ORDER BY u.username
    """
    cur.execute(sql, (f'%{q}%',))
    users = [(r[0], r[1], r[2], r[3], format_date(r[4]) if r[4] else "Never") for r in cur.fetchall()]
    con.close()
    return render_template_string(T_ADMIN_DASHBOARD, users=users, q=q)

@app.route("/admin/user/<int:uid>", methods=["GET","POST"])
@admin_required
def admin_edit_user(uid):
    con = db()
    cur = con.cursor()
    user = cur.execute("SELECT id, username, last_login FROM users WHERE id=?", (uid,)).fetchone()
    if not user:
        con.close()
        return redirect("/admin/dashboard")
    
    if request.method == "POST":
        new_name = request.form.get('new_username')
        new_pass = request.form.get('new_password')
        new_last_login = request.form.get('last_login')
        if request.form.get('confirm') == 'yes':
            try:
                old_vals = {'username': user[1], 'last_login': user[2]}
                new_vals = {'username': new_name, 'last_login': new_last_login}
                if new_pass:
                    new_vals['password'] = '***changed***'
                cur.execute("UPDATE users SET username=?, last_login=? WHERE id=?", (new_name, new_last_login, uid))
                if new_pass:
                    cur.execute("UPDATE users SET password=? WHERE id=?", (generate_password_hash(new_pass), uid))
                log_change(cur, current_user.id if hasattr(current_user, 'id') else 0, 'UPDATE', 'user', uid, old_vals, new_vals, request.remote_addr)
                con.commit()
                con.close()
                sync_s3()
                return redirect("/admin/dashboard")
            except sqlite3.IntegrityError:
                con.close()
                return render_template_string(T_ADMIN_EDIT_USER, user=user, error="Username already exists")
        else:
            con.close()
            return render_template_string(T_ADMIN_EDIT_USER_CONFIRM, user=user, new_name=new_name, new_pass=new_pass, new_last_login=new_last_login)

    con.close()
    return render_template_string(T_ADMIN_EDIT_USER, user=user)

@app.route("/admin/user/delete/<int:uid>", methods=["GET","POST"])
@admin_required
def admin_delete_user(uid):
    con = db()
    cur = con.cursor()
    user = cur.execute("SELECT id, username FROM users WHERE id=?", (uid,)).fetchone()
    if not user:
        con.close()
        return redirect("/admin/dashboard")
    
    if request.method == "POST":
        cur.execute("DELETE FROM notes WHERE user_id=?", (uid,))
        cur.execute("DELETE FROM folders WHERE user_id=?", (uid,))
        cur.execute("DELETE FROM note_history WHERE user_id=?", (uid,))
        cur.execute("DELETE FROM users WHERE id=?", (uid,))
        con.commit()
        con.close()
        sync_s3()
        return redirect("/admin/dashboard")

    con.close()
    return render_template_string(T_ADMIN_DELETE_USER, user=user)

@app.route("/admin/iam_policy")
@admin_required
def admin_iam_policy():
    policy = json.dumps(get_iam_policy(), indent=2)
    return render_template_string(STYLE + """
<nav class="nav">
  <span class="nav-brand">&#9670; Admin</span>
  <a href=/admin/dashboard>&#8592; Dashboard</a>
  <a href=/logout class="nav-logout">Logout</a>
</nav>
<div class="container">
  <h3>Least-Privilege IAM Policy</h3>
  <p style="color:#888;font-size:.85rem;margin-bottom:16px">
    Apply this policy to the IAM user or role used by EverNothing.
    It grants only the minimum S3 actions required, scoped to
    <b>arn:aws:s3:::{{ bucket }}</b> only.
  </p>
  <div class="card">
    <pre style="white-space:pre-wrap;font-size:.85rem;color:var(--gold)">{{ policy }}</pre>
  </div>
  <p style="color:#555;font-size:.8rem;margin-top:12px">
    CLI equivalent: <code>python evernothing_s3.py --iam-policy</code>
  </p>
</div>
""", policy=policy, bucket=S3_BUCKET_NAME)


@app.route("/admin/s3_backups")
@admin_required
def admin_s3_backups():
    
    backups = []
    try:
        if boto3:
            s3 = _s3_client()
            response = s3.list_objects_v2(Bucket=S3_BUCKET_NAME, Prefix='backups/')
            if 'Contents' in response:
                for obj in response['Contents']:
                    backups.append({
                        'key': obj['Key'],
                        'size': obj['Size'],
                        'modified': obj['LastModified'].strftime('%m/%d/%Y %H:%M')
                    })
                backups.sort(key=lambda x: x['modified'], reverse=True)
    except Exception as e:
        logger.error(f"Failed to list S3 backups: {e}")
    
    return render_template_string(T_ADMIN_S3_BACKUPS, backups=backups)

@app.route("/admin/s3_restore/<path:key>", methods=["GET","POST"])
@admin_required
def admin_s3_restore(key):
    if request.method == "GET":
        return render_template_string(T_ADMIN_S3_BACKUPS, backups=[], confirm_key=key)
    
    try:
        if boto3:
            s3 = _s3_client()
            # Download backup
            backup_file = f"restore_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            s3.download_file(S3_BUCKET_NAME, key, backup_file)
            logger.info(f"Restored backup from S3: {key} to {backup_file}")
            return render_template_string(T_ADMIN_S3_BACKUPS, backups=[], message=f"Backup restored to {backup_file}. Restart app to use it.")
    except Exception as e:
        logger.error(f"Failed to restore S3 backup: {e}")
        return render_template_string(T_ADMIN_S3_BACKUPS, backups=[], error=f"Restore failed: {e}")
    
    return redirect("/admin/s3_backups")

@app.route("/admin/sessions")
@admin_required
def admin_sessions():
    con = db()
    cur = con.cursor()
    cur.execute("""
        SELECT u.username, s.session_id, s.login_time, s.logout_time, s.ip_address, s.user_agent
        FROM user_sessions s
        JOIN users u ON s.user_id = u.id
        ORDER BY s.login_time DESC
        LIMIT 200
    """)
    sessions = [{
        'username': r[0],
        'session_id': r[1],
        'login_time': format_date(r[2]),
        'logout_time': format_date(r[3]) if r[3] else 'Active',
        'ip': r[4],
        'user_agent': (r[5] or '')[:50] + ('...' if r[5] and len(r[5]) > 50 else '')
    } for r in cur.fetchall()]
    con.close()
    return render_template_string(T_ADMIN_SESSIONS, sessions=sessions)

@app.route("/admin/audit_logs")
@admin_required
def admin_audit_logs():
    user_filter = request.args.get('user', '')
    action_filter = request.args.get('action', '')
    entity_filter = request.args.get('entity', '')
    limit = int(request.args.get('limit', 100))
    
    con = db()
    cur = con.cursor()
    
    query = """
        SELECT a.id, u.username, a.action, a.entity_type, a.entity_id, a.old_values, a.new_values, a.timestamp, a.ip_address
        FROM audit_log a
        LEFT JOIN users u ON a.user_id = u.id
        WHERE 1=1
    """
    params = []
    
    if user_filter:
        query += " AND u.username LIKE ?"
        params.append(f'%{user_filter}%')
    if action_filter:
        query += " AND a.action = ?"
        params.append(action_filter)
    if entity_filter:
        query += " AND a.entity_type = ?"
        params.append(entity_filter)
    
    query += " ORDER BY a.timestamp DESC LIMIT ?"
    params.append(limit)
    
    cur.execute(query, params)
    logs = []
    for r in cur.fetchall():
        old_vals = json.loads(r[5]) if r[5] else {}
        new_vals = json.loads(r[6]) if r[6] else {}
        logs.append({
            'id': r[0],
            'user': r[1] or 'System',
            'action': r[2],
            'entity': f"{r[3]} #{r[4]}",
            'old': old_vals,
            'new': new_vals,
            'timestamp': format_date(r[7]),
            'ip': r[8]
        })
    con.close()
    return render_template_string(T_ADMIN_AUDIT_LOGS, logs=logs, user_filter=user_filter, action_filter=action_filter, entity_filter=entity_filter, limit=limit)

# --- PASSWORD RESET ---
def get_serializer():
    return URLSafeTimedSerializer(app.secret_key)

@app.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form['email']
        con = db()
        cur = con.cursor()
        user = cur.execute("SELECT username FROM users WHERE email=?", (email,)).fetchone()
        con.close()
        if user:
            token = get_serializer().dumps(email, salt='recover-key')
            link = request.url_root + "reset_password/" + token
            
            # Try to send email
            try:
                from email_utils import send_password_reset_email
                if send_password_reset_email(email, link):
                    logger.info(f"Password reset email sent to {email}")
                else:
                    logger.warning(f"Failed to send password reset email to {email}")
            except ImportError:
                logger.warning("email_utils not available; password reset link was not sent")
        return render_template_string(T_FORGOT_PASSWORD, message="If that email exists, a reset link has been sent.")
    return render_template_string(T_FORGOT_PASSWORD)

@app.route("/reset_password/<token>", methods=["GET", "POST"])
def reset_password(token):
    try: email = get_serializer().loads(token, salt='recover-key', max_age=3600)
    except: return render_template_string(T_RESET_PASSWORD, error="Invalid or expired token.")
    if request.method == "POST":
        con = db()
        cur = con.cursor()
        cur.execute("UPDATE users SET password=? WHERE email=?", (generate_password_hash(request.form['password']), email))
        con.commit()
        con.close()
        sync_s3()
        return redirect("/login")
    return render_template_string(T_RESET_PASSWORD)

# --- LOGIN ---
@app.route("/login", methods=["GET","POST"])
def login():
    from rate_limiter import check_rate_limit, get_remaining_attempts, RATE_LIMIT_LOGIN
    
    con = db()
    cur = con.cursor()
    error = None
    
    # Check for timeout/invalid session messages
    if request.args.get('timeout'):
        error = "Session expired due to inactivity. Please login again."
    elif request.args.get('invalid'):
        error = "Invalid session. Please login again."
    
    if request.method == "POST":
        # Check rate limit
        if not check_rate_limit(request.remote_addr, 'login', RATE_LIMIT_LOGIN):
            remaining = get_remaining_attempts(request.remote_addr, 'login', RATE_LIMIT_LOGIN)
            error = f"Too many login attempts. Please try again later."
            logger.warning(f"Rate limit exceeded for login from {request.remote_addr}")
            con.close()
            return render_template_string(T_LOGIN, error=error)
        
        r = cur.execute(
            "SELECT id,password FROM users WHERE username=?",
            (request.form['username'],)
        ).fetchone()
        if r and check_password_hash(r[1], request.form['password']):
            # Check concurrent session limit (max 3 active sessions)
            active_sessions = cur.execute(
                "SELECT COUNT(*) FROM user_sessions WHERE user_id=? AND logout_time IS NULL",
                (r[0],)
            ).fetchone()[0]
            
            if active_sessions >= 3:
                # Terminate oldest session
                oldest = cur.execute(
                    "SELECT session_id FROM user_sessions WHERE user_id=? AND logout_time IS NULL ORDER BY login_time ASC LIMIT 1",
                    (r[0],)
                ).fetchone()
                if oldest:
                    cur.execute(
                        "UPDATE user_sessions SET logout_time=? WHERE session_id=?",
                        (datetime.datetime.now(timezone.utc).isoformat(), oldest[0])
                    )
            
            # Check if "Remember Me" is checked
            remember_me = request.form.get('remember_me') == 'on'
            
            session_id = os.urandom(16).hex()
            session['session_id'] = session_id
            session['last_activity'] = datetime.datetime.now(timezone.utc).isoformat()
            session['remember_me'] = remember_me
            session.permanent = True
            
            cur.execute("UPDATE users SET last_login=? WHERE id=?", (datetime.datetime.now(timezone.utc).isoformat(), r[0]))
            cur.execute(
                "INSERT INTO user_sessions (user_id, session_id, login_time, ip_address, user_agent) VALUES (?, ?, ?, ?, ?)",
                (r[0], session_id, datetime.datetime.now(timezone.utc).isoformat(), request.remote_addr, request.user_agent.string)
            )
            con.commit()
            con.close()
            login_user(User(r[0], request.form['username']), remember=remember_me)
            return redirect("/")
        error = "Invalid username or password"
    con.close()
    return render_template_string(T_LOGIN, error=error)

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        from rate_limiter import check_rate_limit, RATE_LIMIT_REGISTER
        
        # Check rate limit
        if not check_rate_limit(request.remote_addr, 'register', RATE_LIMIT_REGISTER):
            error = "Too many registration attempts. Please try again later."
            logger.warning(f"Rate limit exceeded for registration from {request.remote_addr}")
            return render_template_string(T_REGISTER, error=error)
        
        username, error = validate_input(request.form.get('username', ''), max_length=50)
        if error:
            return render_template_string(T_REGISTER, error=error)
        
        email, error = validate_email(request.form.get('email', ''))
        if error:
            return render_template_string(T_REGISTER, error=error)
        
        password, error = validate_password(request.form.get('password', ''))
        if error:
            return render_template_string(T_REGISTER, error=error)
        
        con = db()
        cursor=con.cursor()
        try:
            cursor.execute(
                "INSERT INTO users (username, password, email) VALUES(?,?,?)",
                (username, generate_password_hash(password), email)
            )
            con.commit()
            sync_s3()
            logger.info(f"New user registered: {username!r}")
            return redirect("/login")
        except sqlite3.IntegrityError:
            logger.warning(f"Duplicate registration attempt: {username}")
            return render_template_string(T_REGISTER, error="Username already exists")
        except Exception as e:
            logger.error(f"Registration error: {e}")
            return render_template_string(T_REGISTER, error="Registration failed")
        finally:
            con.close()
    return render_template_string(T_REGISTER)

@app.route("/logout")
def logout():
    if 'session_id' in session:
        con = db()
        cur = con.cursor()
        cur.execute(
            "UPDATE user_sessions SET logout_time=? WHERE session_id=?",
            (datetime.datetime.now(timezone.utc).isoformat(), session['session_id'])
        )
        con.commit()
        con.close()
    logout_user(); session.clear(); return redirect("/login")

@app.route("/sessions")
@login_required
def view_sessions():
    con = db()
    cur = con.cursor()
    cur.execute(
        "SELECT session_id, login_time, logout_time, ip_address, user_agent FROM user_sessions WHERE user_id=? ORDER BY login_time DESC LIMIT 10",
        (current_user.id,)
    )
    sessions = []
    for s in cur.fetchall():
        sessions.append({
            'session_id': s[0],
            'login_time': format_date(s[1]),
            'logout_time': format_date(s[2]) if s[2] else 'Active',
            'ip': s[3],
            'user_agent': s[4][:50] + '...' if len(s[4]) > 50 else s[4],
            'is_current': s[0] == session.get('session_id')
        })
    con.close()
    return render_template_string(T_SESSIONS, sessions=sessions)

@app.route("/session/revoke/<session_id>")
@login_required
def revoke_session(session_id):
    con = db()
    cur = con.cursor()
    # Only allow revoking own sessions
    cur.execute(
        "UPDATE user_sessions SET logout_time=? WHERE session_id=? AND user_id=?",
        (datetime.datetime.now(timezone.utc).isoformat(), session_id, current_user.id)
    )
    con.commit()
    con.close()
    return redirect("/sessions")

@app.route("/audit_report")
@login_required
def audit_report():
    con = db()
    cur = con.cursor()
    cur.execute("""
        SELECT a.id, u.username, a.action, a.entity_type, a.entity_id, a.old_values, a.new_values, a.timestamp, a.ip_address
        FROM audit_log a
        LEFT JOIN users u ON a.user_id = u.id
        WHERE a.user_id = ? OR ? = 0
        ORDER BY a.timestamp DESC
        LIMIT 100
    """, (current_user.id, 1 if session.get('admin_logged_in') else 0))
    logs = []
    for r in cur.fetchall():
        old_vals = json.loads(r[5]) if r[5] else {}
        new_vals = json.loads(r[6]) if r[6] else {}
        logs.append({
            'id': r[0],
            'user': r[1],
            'action': r[2],
            'entity': f"{r[3]} #{r[4]}",
            'old': old_vals,
            'new': new_vals,
            'timestamp': format_date(r[7]),
            'ip': r[8]
        })
    con.close()
    return render_template_string(T_AUDIT_REPORT, logs=logs)

@app.route("/download/<int:aid>")
@login_required
def download_attachment(aid):
    con = db()
    cur = con.cursor()
    a = cur.execute("SELECT filename,file_data FROM attachments WHERE id=? AND user_id=?", (aid, current_user.id)).fetchone()
    con.close()
    if a:
        resp = make_response(a[1])
        resp.headers['Content-Disposition'] = f'attachment; filename={a[0]}'
        return resp
    return redirect("/")

@app.route("/delete_attachment/<int:aid>", methods=["POST"])
@login_required
def delete_attachment(aid):
    con = db()
    cur = con.cursor()
    a = cur.execute("SELECT note_id, filename FROM attachments WHERE id=? AND user_id=?", (aid, current_user.id)).fetchone()
    if a:
        log_change(cur, current_user.id, 'DELETE', 'attachment', aid, {'note_id': a[0], 'filename': a[1]}, {}, request.remote_addr)
        cur.execute("DELETE FROM attachments WHERE id=? AND user_id=?", (aid, current_user.id))
        con.commit()
        con.close()
        sync_s3()
        return redirect(f"/edit/{a[0]}")
    con.close()
    return redirect("/")

# --- TEMPLATES ---
STYLE = """
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
:root {
  --gold: #ffd700;
  --gold-dim: #b8960c;
  --red: #cc2200;
  --red-bright: #ff3300;
  --bg: #0a0a0a;
  --bg2: #111;
  --bg3: #1a1a1a;
  --border: #2a2a2a;
  --radius: 6px;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
html { font-size: 17px; }
body {
  background: var(--bg);
  color: var(--gold);
  font-family: 'Segoe UI', system-ui, sans-serif;
  min-height: 100vh;
  padding-bottom: 40px;
}
a { color: var(--gold); text-decoration: none; transition: color .15s; }
a:hover { color: var(--red-bright); }
.nav {
  background: var(--bg2);
  border-bottom: 1px solid var(--red);
  padding: 10px 20px;
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
  position: sticky;
  top: 0;
  z-index: 100;
}
.nav-brand {
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--gold);
  letter-spacing: 1px;
  margin-right: 10px;
}
.nav a {
  font-size: .85rem;
  padding: 4px 10px;
  border-radius: var(--radius);
  border: 1px solid transparent;
  transition: all .15s;
}
.nav a:hover { border-color: var(--red); color: var(--red-bright); text-decoration: none; }
.nav .sep { color: #444; }
.nav .nav-logout { margin-left: auto; color: var(--red); border-color: var(--red); }
.nav .nav-logout:hover { background: var(--red); color: #000; }
.container { max-width: 1100px; margin: 0; padding: 24px 20px; }
h2, h3 { color: var(--gold); margin-bottom: 16px; font-weight: 600; letter-spacing: .5px; }
h4 { color: var(--gold-dim); margin: 20px 0 10px; font-size: .95rem; text-transform: uppercase; letter-spacing: 1px; }
.card {
  background: var(--bg2);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 20px;
  margin-bottom: 16px;
}
.item-list { list-style: none; }
.item-list li {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 3px 12px;
  margin-bottom: 1px;
  border-radius: var(--radius);
  border: 1px solid transparent;
  transition: all .15s;
}
.item-list li:hover { background: var(--bg3); border-color: var(--border); }
.item-list li a { flex: 1; font-size: .95rem; }
.item-list .actions { display: flex; gap: 6px; opacity: 0; transition: opacity .15s; }
.item-list li:hover .actions { opacity: 1; }
.item-list .actions a { font-size: .75rem; padding: 2px 7px; border-radius: 3px; border: 1px solid #333; flex: none; }
.item-list .actions a:hover { border-color: var(--red); color: var(--red-bright); }
.item-list .del { color: var(--red) !important; }
.empty { color: #555; font-style: italic; padding: 12px; }
label { display: block; font-size: .85rem; color: var(--gold-dim); margin-bottom: 4px; margin-top: 12px; }
input[type=text], input[type=password], input[type=email], input[type=date], input:not([type]), textarea, select {
  background: var(--bg2);
  color: var(--gold);
  border: 1px solid #444;
  border-radius: var(--radius);
  padding: 8px 12px;
  font-size: .9rem;
  font-family: inherit;
  width: 100%;
  transition: border-color .15s;
  outline: none;
}
input[type=text]:focus, input[type=password]:focus, input[type=email]:focus,
input:not([type]):focus, textarea:focus, select:focus {
  border-color: var(--gold-dim);
}
textarea { resize: vertical; font-family: 'Consolas', 'Courier New', monospace; font-size: .85rem; }
select option { background: var(--bg2); }
.form-row { display: flex; gap: 12px; flex-wrap: wrap; }
.form-row > * { flex: 1; min-width: 200px; }
.btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 20px;
  border-radius: var(--radius);
  border: 1px solid var(--gold-dim);
  background: transparent;
  color: var(--gold);
  font-size: .9rem;
  font-family: inherit;
  cursor: pointer;
  transition: all .15s;
  text-decoration: none;
}
.btn:hover { background: var(--gold-dim); color: #000; border-color: var(--gold-dim); text-decoration: none; }
.btn-primary { background: var(--gold-dim); color: #000; border-color: var(--gold-dim); font-weight: 600; }
.btn-primary:hover { background: var(--gold); border-color: var(--gold); color: #000; }
.btn-danger { border-color: var(--red); color: var(--red); }
.btn-danger:hover { background: var(--red); color: #fff; }
.btn-sm { padding: 4px 12px; font-size: .8rem; }
.btn-group { display: flex; gap: 10px; margin-top: 20px; flex-wrap: wrap; align-items: center; }
err { display: block; color: var(--red-bright); background: #1a0000; border: 1px solid var(--red); border-radius: var(--radius); padding: 8px 12px; margin: 10px 0; font-size: .9rem; }
.breadcrumb { font-size: .85rem; color: #666; margin-bottom: 16px; display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }
.breadcrumb a { color: var(--gold-dim); }
.breadcrumb a:hover { color: var(--gold); }
.breadcrumb .sep { color: #444; }
.badge { font-size: .75rem; background: var(--bg3); border: 1px solid var(--border); border-radius: 10px; padding: 1px 8px; color: #888; }
.timestamp { font-size: .8rem; color: #666; }
table { width: 100%; border-collapse: collapse; font-size: .9rem; }
th { text-align: left; padding: 10px 12px; border-bottom: 2px solid var(--red); color: var(--gold-dim); font-size: .8rem; text-transform: uppercase; letter-spacing: .5px; }
td { padding: 3px 12px; border-bottom: 1px solid var(--border); vertical-align: top; }
tr:hover td { background: var(--bg3); }
.search-box { display: flex; gap: 8px; margin-bottom: 20px; }
.search-box input { flex: 1; }
.tag-create { color: #0c0; }
.tag-update { color: var(--gold-dim); }
.tag-delete { color: var(--red); }
.footer {
  position: fixed; bottom: 0; left: 0; width: 100%;
  background: var(--bg2); border-top: 1px solid var(--border);
  color: #555; text-align: center; font-size: .75rem; padding: 5px;
  z-index: 99;
}
.two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
@media (max-width: 600px) {
  .two-col { grid-template-columns: 1fr; }
  .nav { gap: 4px; }
  textarea { cols: unset; width: 100%; }
}
.confirm-box {
  background: var(--bg2); border: 1px solid var(--red);
  border-radius: var(--radius); padding: 24px; max-width: 600px;
}
.confirm-box p { margin-bottom: 12px; line-height: 1.6; }
.confirm-box .field { margin: 8px 0; font-size: .9rem; }
.confirm-box .field b { color: var(--gold-dim); }
</style>
<div class="footer">{{ build_date }}</div>
"""

T_FOLDERS = STYLE + """
<nav class="nav">
  <span class="nav-brand">&#9670; EverNothing</span>
  <a href=/folder/add>+ Folder</a>
  <a href=/export>Export</a>
  <a href=/audit_report>Audit</a>
  <a href=/sessions>Sessions</a>
  <a href=/change_password>Password</a>
  <a href=/logout class="nav-logout">Logout</a>
</nav>
<div class="container">
  <div class="search-box">
    <form action="/search" method="get" style="display:flex;gap:8px;width:100%">
      <input name="q" placeholder="Search notes..." style="flex:1">
      <button class="btn btn-primary">Search</button>
    </form>
  </div>
  <div class="two-col">
    <div>
      <h4>Folders</h4>
      <ul class="item-list">
      {% for f in folders %}
      <li>
        <a href=/folder/{{f[0]}}>&#128193; {{f[1]}}</a>
        <span class="actions">
          <a href=/folder/rename/{{f[0]}}>rename</a>
          <a href=/folder/delete/{{f[0]}} class="del">delete</a>
        </span>
      </li>
      {% else %}
      <li class="empty">No folders yet. <a href=/folder/add>Create one</a></li>
      {% endfor %}
      </ul>
    </div>
    <div>
      <h4>Recently Edited</h4>
      <ul class="item-list">
      {% for n in recent %}
      <li>
        <a href=/edit/{{n[0]}}>{{n[1]}}</a>
        <span class="timestamp">{{n[2]}}</span>
      </li>
      {% else %}
      <li class="empty">No notes yet.</li>
      {% endfor %}
      </ul>
    </div>
  </div>
</div>
"""

T_ADD_FOLDER = STYLE + """
<nav class="nav">
  <span class="nav-brand">&#9670; EverNothing</span>
  <a href=/>Home</a>
  <a href=/logout class="nav-logout">Logout</a>
</nav>
<div class="container">
  <h3>Create Folder</h3>
  {% if error %}<err>{{error}}</err>{% endif %}
  <div class="card" style="max-width:480px">
    <form method=post>
      <input type=hidden name=csrf_token value="{{ csrf_token() }}">
      <label>Folder Name</label>
      <input name=name maxlength="255" autofocus>
      <div class="btn-group">
        <button class="btn btn-primary">Create</button>
        <a href=/ class="btn">Cancel</a>
      </div>
    </form>
  </div>
</div>
"""

T_ADD_SUBFOLDER = STYLE + """
<nav class="nav">
  <span class="nav-brand">&#9670; EverNothing</span>
  <a href=/folder/{{pid}}>Back</a>
  <a href=/logout class="nav-logout">Logout</a>
</nav>
<div class="container">
  <h3>Create Subfolder</h3>
  <div class="card" style="max-width:480px">
    <form method=post>
      <input type=hidden name=csrf_token value="{{ csrf_token() }}">
      <label>Subfolder Name</label>
      <input name=name autofocus>
      <div class="btn-group">
        <button class="btn btn-primary">Create</button>
        <a href=/folder/{{pid}} class="btn">Cancel</a>
      </div>
    </form>
  </div>
</div>
"""

T_RENAME_FOLDER = STYLE + """
<nav class="nav">
  <span class="nav-brand">&#9670; EverNothing</span>
  <a href=/folder/{{fid}}>Back</a>
  <a href=/logout class="nav-logout">Logout</a>
</nav>
<div class="container">
  <h3>Rename Folder</h3>
  <div class="card" style="max-width:480px">
    <form method=post>
      <input type=hidden name=csrf_token value="{{ csrf_token() }}">
      <label>New Name</label>
      <input name=name value="{{f[0]}}" autofocus>
      <div class="btn-group">
        <button class="btn btn-primary">Rename</button>
        <a href=/folder/{{fid}} class="btn">Cancel</a>
      </div>
    </form>
  </div>
</div>
"""

T_CHANGE_PASSWORD = STYLE + """
<nav class="nav">
  <span class="nav-brand">&#9670; EverNothing</span>
  <a href=/>Home</a>
  <a href=/logout class="nav-logout">Logout</a>
</nav>
<div class="container">
  <h3>Change Password</h3>
  {% if error %}<err>{{error}}</err>{% endif %}
  <div class="card" style="max-width:480px">
    <form method=post>
      <input type=hidden name=csrf_token value="{{ csrf_token() }}">
      <label>Current Password</label>
      <div style="position:relative">
        <input type=password name=old_password id=old_password autofocus style="padding-right:70px">
        <a href="#" onclick="toggleVis('old_password',this);return false;" style="position:absolute;right:10px;top:50%;transform:translateY(-50%);font-size:.8rem;color:var(--gold-dim)">Show</a>
      </div>
      <label>New Password</label>
      <div style="position:relative">
        <input type=password name=new_password id=new_password style="padding-right:70px">
        <a href="#" onclick="toggleVis('new_password',this);return false;" style="position:absolute;right:10px;top:50%;transform:translateY(-50%);font-size:.8rem;color:var(--gold-dim)">Show</a>
      </div>
      <label>Verify New Password</label>
      <div style="position:relative">
        <input type=password name=verify_password id=verify_password style="padding-right:70px">
        <a href="#" onclick="toggleVis('verify_password',this);return false;" style="position:absolute;right:10px;top:50%;transform:translateY(-50%);font-size:.8rem;color:var(--gold-dim)">Show</a>
      </div>
      <div class="btn-group">
        <button class="btn btn-primary">Change Password</button>
        <a href=/ class="btn">Cancel</a>
      </div>
    </form>
  </div>
</div>
<script>
function toggleVis(id, link) {
  var el = document.getElementById(id);
  if (el.type === 'password') { el.type = 'text'; link.textContent = 'Hide'; }
  else { el.type = 'password'; link.textContent = 'Show'; }
}
</script>
"""

T_DELETE_NOTE = STYLE + """
<nav class="nav">
  <span class="nav-brand">&#9670; EverNothing</span>
  <a href=/>Home</a>
  <a href=/logout class="nav-logout">Logout</a>
</nav>
<div class="container">
  <div class="confirm-box">
    <h3>Delete Note</h3>
    <p>Are you sure you want to permanently delete <b>{{n[1]}}</b>?</p>
    <p style="color:#888;font-size:.85rem">This action cannot be undone.</p>
    <form method=post>
      <input type=hidden name=csrf_token value="{{ csrf_token() }}">
      <div class="btn-group">
        <button class="btn btn-danger">Yes, Delete</button>
        <a href=javascript:history.back() class="btn">Cancel</a>
      </div>
    </form>
  </div>
</div>
"""

T_EDIT_CONFIRM = STYLE + """
<nav class="nav">
  <span class="nav-brand">&#9670; EverNothing</span>
  <a href=/>Home</a>
  <a href=/logout class="nav-logout">Logout</a>
</nav>
<div class="container">
  <div class="confirm-box">
    <h3>Confirm Changes</h3>
    <p>Save the following changes?</p>
    <div class="field"><b>Note:</b> {{note[0]}}</div>
    <div class="field"><b>Description:</b> {{note[4]}}</div>
    <form method=post action="/edit/{{id}}">
      <input type=hidden name=csrf_token value="{{ csrf_token() }}">
      <input type=hidden name=note value="{{note[0]}}">
      <input type=hidden name=content value="{{note[1]}}">
      <input type=hidden name=folder_id value="{{note[2]}}">
      <input type=hidden name=description value="{{note[4]}}">
      <input type=hidden name=confirm value="yes">
      <div class="btn-group">
        <button class="btn btn-primary">Yes, Save</button>
        <button type=button class="btn" onclick="history.back()">Cancel</button>
      </div>
    </form>
  </div>
</div>
"""

T_NOTES = STYLE + """
<nav class="nav">
  <span class="nav-brand">&#9670; EverNothing</span>
  <a href={% if folder[2] %}/folder/{{folder[2]}}{% else %}/{% endif %}>&#8592; Back</a>
  <a href=/add/{{folder[0]}}>+ Add Note</a>
  <a href=/folder/{{folder[0]}}/add_folder>+ Subfolder</a>
  <a href=/folder/rename/{{folder[0]}}>Rename</a>
  <a href=/folder/delete/{{folder[0]}} class="btn-danger" style="color:var(--red)">Delete Folder</a>
  <a href=/logout class="nav-logout">Logout</a>
</nav>
<div class="container">
  <h3>&#128193; {{folder[1]}}</h3>
  <div class="two-col">
    <div>
      <h4>Notes</h4>
      <ul class="item-list">
      {% for n in notes %}
      <li>
        <a href=/edit/{{n[0]}}>{{n[1]}}</a>
        <span class="actions">
          <a href=/note/delete/{{n[0]}} class="del">delete</a>
        </span>
      </li>
      {% else %}
      <li class="empty">No notes. <a href=/add/{{folder[0]}}>Add one</a></li>
      {% endfor %}
      </ul>
    </div>
    <div>
      <h4>Subfolders</h4>
      <ul class="item-list">
      {% for s in subfolders %}
      <li><a href=/folder/{{s[0]}}>&#128193; {{s[1]}}</a></li>
      {% else %}
      <li class="empty">No subfolders.</li>
      {% endfor %}
      </ul>
    </div>
  </div>
</div>
"""

T_ADD = STYLE + """
<nav class="nav">
  <span class="nav-brand">&#9670; EverNothing</span>
  <a href=/folder/{{fid}}>&#8592; Back</a>
  <a href=/logout class="nav-logout">Logout</a>
</nav>
<div class="container">
  <h3>Add Note</h3>
  {% if error %}<err>{{error}}</err>{% endif %}
  <form method=post enctype="multipart/form-data">
    <input type=hidden name=csrf_token value="{{ csrf_token() }}">
    <div class="form-row">
      <div>
        <label>Note Title</label>
        <input name=note value="{{note}}" autofocus>
      </div>
      <div>
        <label>Description <span style="color:#555">(optional, max 255)</span></label>
        <input name=description value="{{description}}" maxlength="255">
      </div>
    </div>
    <label>Contents</label>
    <textarea name=content rows=30 cols=120>{{content}}</textarea>
    <label>Attachment <span style="color:#555">(optional)</span></label>
    <input type=file name=file style="width:auto">
    <div class="btn-group">
      <button class="btn btn-primary">Add Note</button>
      <a href=/folder/{{fid}} class="btn">Cancel</a>
    </div>
  </form>
</div>
"""

T_EDIT = STYLE + """
<nav class="nav">
  <span class="nav-brand">&#9670; EverNothing</span>
  <a href=/>Home</a>
  {% for b in breadcrumbs %}
  <span class="sep">&#8250;</span> <a href=/folder/{{b[0]}}>{{b[1]}}</a>
  {% endfor %}
  <span style="margin-left:auto;display:flex;gap:8px;align-items:center">
    <a href=/history/{{id}} class="btn btn-sm" style="color:var(--gold-dim)">History: {{note[3]}}</a>
    <a href=/note/delete/{{id}} class="btn btn-sm btn-danger">Delete</a>
    <a href=/logout class="btn btn-sm nav-logout">Logout</a>
  </span>
</nav>
<div class="container">
  {% if error %}<err>{{error}}</err>{% endif %}
  <form method=post enctype="multipart/form-data">
    <input type=hidden name=csrf_token value="{{ csrf_token() }}">
    <div class="form-row">
      <div>
        <label>Note Title</label>
        <input name=note value='{{note[0]}}'>
      </div>
      <div>
        <label>Description <span style="color:#555">(optional)</span></label>
        <input name=description value='{{note[4]}}' maxlength="255">
      </div>
    </div>
    <label>Folder</label>
    <select name=folder_id style="width:auto;min-width:200px">
    {% for f in folders %}
    <option value='{{f[0]}}' {% if f[0]==note[2] %}selected{% endif %}>{{f[1]}}</option>
    {% endfor %}
    </select>
    <label>Contents</label>
    <textarea name=content rows=30 cols=120>{{note[1]}}</textarea>
    <div class="btn-group">
      <button class="btn btn-primary">Commit</button>
      <a href=/ class="btn">Cancel</a>
    </div>
  </form>

  <h4>Attachments</h4>
  <form method=post enctype="multipart/form-data" style="display:flex;gap:8px;align-items:center;margin-bottom:12px">
    <input type=hidden name=csrf_token value="{{ csrf_token() }}">
    <input type=file name=file style="width:auto">
    <button class="btn btn-sm">Upload</button>
  </form>
  <ul class="item-list">
  {% for att in attachments %}
  <li>
    <a href=/download/{{att[0]}}>&#128206; {{att[1]}}</a>
    <span class="badge">{{att[2]}} bytes</span>
    <span class="actions" style="opacity:1">
      <form method=post action="/delete_attachment/{{att[0]}}" style="display:inline">
        <input type=hidden name=csrf_token value="{{ csrf_token() }}">
        <button class="btn btn-sm btn-danger" style="border:none;background:none;cursor:pointer;color:var(--red)">remove</button>
      </form>
    </span>
  </li>
  {% else %}
  <li class="empty">No attachments.</li>
  {% endfor %}
  </ul>
</div>
"""

T_LOGIN = STYLE + """
<div style="min-height:100vh;display:flex;align-items:center;justify-content:center">
  <div class="card" style="width:100%;max-width:400px">
    <h2 style="text-align:center;margin-bottom:4px">&#9670; EverNothing</h2>
    <p style="text-align:center;color:#666;font-size:.85rem;margin-bottom:20px">Sign in to your notes</p>
    {% if error %}<err>{{error}}</err>{% endif %}
    <form method=post>
      <input type=hidden name=csrf_token value="{{ csrf_token() }}">
      <label>Username</label>
      <input name=username autofocus>
      <label>Password</label>
      <input type=password name=password>
      <label style="flex-direction:row;display:flex;align-items:center;gap:8px;margin-top:12px;cursor:pointer">
        <input type=checkbox name=remember_me style="width:auto;margin:0"> Remember me for 30 days
      </label>
      <div class="btn-group" style="margin-top:16px">
        <button class="btn btn-primary" style="flex:1;justify-content:center">Login</button>
      </div>
    </form>
    <p style="text-align:center;margin-top:16px;font-size:.85rem">
      <a href=/register>Create account</a> &nbsp;|&nbsp; <a href=/forgot_password>Forgot password?</a>
    </p>
  </div>
</div>
"""

T_REGISTER = STYLE + """
<div style="min-height:100vh;display:flex;align-items:center;justify-content:center">
  <div class="card" style="width:100%;max-width:420px">
    <h2 style="text-align:center;margin-bottom:4px">&#9670; EverNothing</h2>
    <p style="text-align:center;color:#666;font-size:.85rem;margin-bottom:20px">Create your account</p>
    {% if error %}<err>{{error}}</err>{% endif %}
    <form method=post>
      <input type=hidden name=csrf_token value="{{ csrf_token() }}">
      <label>Username</label>
      <input name=username maxlength="50" required autofocus>
      <label>Email</label>
      <input name=email type="email" maxlength="100" required>
      <label>Password <span style="color:#555">(min 8 chars, upper, lower, number)</span></label>
      <input type=password name=password minlength="8" required>
      <div class="btn-group" style="margin-top:16px">
        <button class="btn btn-primary" style="flex:1;justify-content:center">Create Account</button>
      </div>
    </form>
    <p style="text-align:center;margin-top:16px;font-size:.85rem"><a href=/login>Already have an account?</a></p>
  </div>
</div>
"""

T_SEARCH = STYLE + """
<nav class="nav">
  <span class="nav-brand">&#9670; EverNothing</span>
  <a href=/>Home</a>
  <a href=/logout class="nav-logout">Logout</a>
</nav>
<div class="container">
  <form method="get" class="card">
    <div class="search-box">
      <input name="q" value="{{q}}" placeholder="Search notes..." autofocus style="flex:1">
      <button class="btn btn-primary">Search</button>
    </div>
    <div class="form-row" style="margin-top:8px">
      <div>
        <label>Folder</label>
        <select name="folder">
          <option value="">All Folders</option>
          {% for f in folders %}
          <option value="{{f[0]}}" {% if folder_filter==f[0]|string %}selected{% endif %}>{{f[1]}}</option>
          {% endfor %}
        </select>
      </div>
      <div>
        <label>Date From</label>
        <input type="date" name="date_from" value="{{date_from}}">
      </div>
      <div>
        <label>Date To</label>
        <input type="date" name="date_to" value="{{date_to}}">
      </div>
    </div>
    <div style="margin-top:10px;display:flex;gap:16px;font-size:.85rem">
      <label style="display:flex;align-items:center;gap:6px;margin:0;cursor:pointer">
        <input type="checkbox" name="regex" {% if use_regex %}checked{% endif %} style="width:auto"> Regex
      </label>
      <label style="display:flex;align-items:center;gap:6px;margin:0;cursor:pointer">
        <input type="checkbox" name="history" {% if search_history %}checked{% endif %} style="width:auto"> Search History
      </label>
    </div>
  </form>
  {% if folder_results %}
  <h4>Folders <span class="badge">{{folder_results|length}}</span></h4>
  <ul class="item-list">
  {% for f in folder_results %}
  <li><a href=/folder/{{f[0]}}>&#128193; {{f[1]}}</a></li>
  {% endfor %}
  </ul>
  {% endif %}
  <h4>Notes {% if notes %}<span class="badge">{{notes|length}}</span>{% endif %}</h4>
  <ul class="item-list">
  {% for n in notes %}
  <li>
    <a href=/edit/{{n[0]}}>{{n[1]}}</a>
    <span class="timestamp">{{n[2]}}</span>
  </li>
  {% else %}
  <li class="empty">No matches.</li>
  {% endfor %}
  </ul>
</div>
"""

T_DELETE_FOLDER = STYLE + """
<nav class="nav">
  <span class="nav-brand">&#9670; EverNothing</span>
  <a href=/>Home</a>
  <a href=/logout class="nav-logout">Logout</a>
</nav>
<div class="container">
  <div class="confirm-box">
    <h3>Delete Folder</h3>
    <p>Are you sure you want to delete <b>{{f[0]}}</b> and all its notes and subfolders?</p>
    <p style="color:#888;font-size:.85rem">This action cannot be undone.</p>
    <form method=post>
      <input type=hidden name=csrf_token value="{{ csrf_token() }}">
      <div class="btn-group">
        <button class="btn btn-danger">Yes, Delete</button>
        <a href=javascript:history.back() class="btn">Cancel</a>
      </div>
    </form>
  </div>
</div>
"""

T_HISTORY = STYLE + """
<nav class="nav">
  <span class="nav-brand">&#9670; EverNothing</span>
  <a href=/edit/{{nid}}>&#8592; Back to Note</a>
  <a href=/logout class="nav-logout">Logout</a>
</nav>
<div class="container">
  <h3>Note History</h3>
  <ul class="item-list">
  {% for h in history %}
  <li>
    <span style="font-size:.85rem;color:#888;min-width:140px">{{h[2]}}</span>
    <span style="flex:1">{{h[1]}}</span>
    <span class="actions" style="opacity:1">
      <a href=/history/restore/{{h[0]}} class="btn btn-sm">Rollback</a>
    </span>
  </li>
  {% else %}
  <li class="empty">No history.</li>
  {% endfor %}
  </ul>
</div>
"""

T_ADMIN_LOGIN = STYLE + """
<div style="min-height:100vh;display:flex;align-items:center;justify-content:center">
  <div class="card" style="width:100%;max-width:380px">
    <h2 style="text-align:center;margin-bottom:4px">&#9670; Admin</h2>
    <p style="text-align:center;color:#666;font-size:.85rem;margin-bottom:20px">EverNothing Administration</p>
    {% if error %}<err>{{error}}</err>{% endif %}
    <form method=post>
      <input type=hidden name=csrf_token value="{{ csrf_token() }}">
      <label>Username</label>
      <input name=username autofocus>
      <label>Password</label>
      <input type=password name=password>
      <div class="btn-group" style="margin-top:16px">
        <button class="btn btn-primary" style="flex:1;justify-content:center">Login</button>
      </div>
    </form>
  </div>
</div>
"""

T_ADMIN_SESSIONS = STYLE + """
<nav class="nav">
  <span class="nav-brand">&#9670; Admin</span>
  <a href=/admin/dashboard>&#8592; Dashboard</a>
  <a href=/logout class="nav-logout">Logout</a>
</nav>
<div class="container">
  <h3>All Sessions</h3>
  <table>
    <tr><th>Username</th><th>Login Time</th><th>Status</th><th>IP Address</th><th>Device</th></tr>
    {% for s in sessions %}
    <tr>
      <td>{{s.username}}</td>
      <td class="timestamp">{{s.login_time}}</td>
      <td>
        {% if s.logout_time == 'Active' %}<span style="color:var(--gold-dim)">Active</span>
        {% else %}<span style="color:#555">{{s.logout_time}}</span>{% endif %}
      </td>
      <td style="font-size:.85rem">{{s.ip}}</td>
      <td style="font-size:.8rem;color:#888">{{s.user_agent}}</td>
    </tr>
    {% else %}
    <tr><td colspan=5 class="empty">No sessions found.</td></tr>
    {% endfor %}
  </table>
</div>
"""

T_ADMIN_DASHBOARD = STYLE + """
<nav class="nav">
  <span class="nav-brand">&#9670; Admin</span>
  <a href=/admin/audit_logs>Audit Logs</a>
  <a href=/admin/sessions>Sessions</a>
  <a href=/admin/s3_backups>S3 Backups</a>
  <a href=/admin/iam_policy>IAM Policy</a>
  <a href=/logout class="nav-logout">Logout</a>
</nav>
<div class="container">
  <h3>Users</h3>
  <form method="get" style="margin-bottom:16px">
    <div class="search-box">
      <input name="q" placeholder="Search users..." value="{{q}}" style="flex:1">
      <button class="btn btn-primary">Search</button>
    </div>
  </form>
  <table>
    <tr>
      <th>Username</th><th>Notes</th><th>Folders</th><th>Last Login</th><th>Actions</th>
    </tr>
    {% for u in users %}
    <tr>
      <td><a href=/admin/user/{{u[0]}}>{{u[1]}}</a></td>
      <td><span class="badge">{{u[2]}}</span></td>
      <td><span class="badge">{{u[3]}}</span></td>
      <td class="timestamp">{{u[4]}}</td>
      <td><a href=/admin/user/delete/{{u[0]}} style="color:var(--red);font-size:.8rem">delete</a></td>
    </tr>
    {% else %}
    <tr><td colspan=5 class="empty">No users found.</td></tr>
    {% endfor %}
  </table>
</div>
"""

T_ADMIN_EDIT_USER = STYLE + """
<nav class="nav">
  <span class="nav-brand">&#9670; Admin</span>
  <a href=/admin/dashboard>&#8592; Dashboard</a>
  <a href=/logout class="nav-logout">Logout</a>
</nav>
<div class="container">
  <h3>Edit User</h3>
  {% if error %}<err>{{error}}</err>{% endif %}
  <p style="color:#666;font-size:.85rem">Passwords are hashed and cannot be displayed. You can only reset them.</p>
  <div class="card" style="max-width:500px">
    <form method=post>
      <input type=hidden name=csrf_token value="{{ csrf_token() }}">
      <label>Current Username</label>
      <input value="{{user[1]}}" readonly style="opacity:.6">
      <label>New Username</label>
      <input name=new_username autofocus>
      <label>New Password <span style="color:#555">(leave blank to keep)</span></label>
      <input name=new_password type=password>
      <label>Last Login</label>
      <input name=last_login value="{{user[2] if user[2] else 'Never'}}" readonly style="opacity:.6">
      <div class="btn-group">
        <button class="btn btn-primary">Update</button>
        <a href=/admin/dashboard class="btn">Cancel</a>
      </div>
    </form>
  </div>
</div>
"""

T_ADMIN_EDIT_USER_CONFIRM = STYLE + """
<nav class="nav">
  <span class="nav-brand">&#9670; Admin</span>
  <a href=/admin/dashboard>Dashboard</a>
  <a href=/logout class="nav-logout">Logout</a>
</nav>
<div class="container">
  <div class="confirm-box">
    <h3>Confirm User Change</h3>
    <p>Change username from <b>{{user[1]}}</b> to <b>{{new_name}}</b>?</p>
    {% if new_pass %}<p>Password will also be changed.</p>{% endif %}
    <form method=post>
      <input type=hidden name=csrf_token value="{{ csrf_token() }}">
      <input type=hidden name=new_username value="{{new_name}}">
      <input type=hidden name=new_password value="{{new_pass}}">
      <input type=hidden name=confirm value="yes">
      <div class="btn-group">
        <button class="btn btn-primary">Yes, Change</button>
        <a href=/admin/dashboard class="btn">Cancel</a>
      </div>
    </form>
  </div>
</div>
"""

T_ADMIN_DELETE_USER = STYLE + """
<nav class="nav">
  <span class="nav-brand">&#9670; Admin</span>
  <a href=/admin/dashboard>&#8592; Dashboard</a>
  <a href=/logout class="nav-logout">Logout</a>
</nav>
<div class="container">
  <div class="confirm-box">
    <h3>Delete User</h3>
    <p>Are you sure you want to delete <b>{{user[1]}}</b>?</p>
    <p style="color:var(--red);font-size:.85rem">All notes, folders, and history for this user will be permanently deleted.</p>
    <form method=post>
      <input type=hidden name=csrf_token value="{{ csrf_token() }}">
      <div class="btn-group">
        <button class="btn btn-danger">Yes, Delete User</button>
        <a href=/admin/dashboard class="btn">Cancel</a>
      </div>
    </form>
  </div>
</div>
"""

T_FORGOT_PASSWORD = STYLE + """
<div style="min-height:100vh;display:flex;align-items:center;justify-content:center">
  <div class="card" style="width:100%;max-width:400px">
    <h2 style="text-align:center;margin-bottom:4px">&#9670; EverNothing</h2>
    <p style="text-align:center;color:#666;font-size:.85rem;margin-bottom:20px">Reset your password</p>
    {% if message %}<p style="color:#0c0;text-align:center">{{message}}</p>{% endif %}
    <form method=post>
      <input type=hidden name=csrf_token value="{{ csrf_token() }}">
      <label>Email Address</label>
      <input name=email type=email required autofocus>
      <div class="btn-group" style="margin-top:16px">
        <button class="btn btn-primary" style="flex:1;justify-content:center">Send Reset Link</button>
      </div>
    </form>
    <p style="text-align:center;margin-top:16px;font-size:.85rem"><a href=/login>Back to login</a></p>
  </div>
</div>
"""

T_RESET_PASSWORD = STYLE + """
<div style="min-height:100vh;display:flex;align-items:center;justify-content:center">
  <div class="card" style="width:100%;max-width:400px">
    <h2 style="text-align:center;margin-bottom:20px">&#9670; Reset Password</h2>
    {% if error %}<err>{{error}}</err>{% endif %}
    <form method=post>
      <input type=hidden name=csrf_token value="{{ csrf_token() }}">
      <label>New Password</label>
      <input type=password name=password required autofocus>
      <div class="btn-group" style="margin-top:16px">
        <button class="btn btn-primary" style="flex:1;justify-content:center">Reset Password</button>
      </div>
    </form>
  </div>
</div>
"""

T_AUDIT_REPORT = STYLE + """
<nav class="nav">
  <span class="nav-brand">&#9670; EverNothing</span>
  <a href=/>&#8592; Home</a>
  <a href=/logout class="nav-logout">Logout</a>
</nav>
<div class="container">
  <h3>Audit Report</h3>
  <table>
    <tr><th>Time</th><th>Action</th><th>Entity</th><th>Old Values</th><th>New Values</th><th>IP</th></tr>
    {% for log in logs %}
    <tr>
      <td class="timestamp">{{log.timestamp}}</td>
      <td><span class="tag-{{log.action|lower}}">{{log.action}}</span></td>
      <td style="font-size:.8rem">{{log.entity}}</td>
      <td style="font-size:.8rem">{% for k,v in log.old.items() %}<b>{{k}}:</b> {{v}}<br>{% endfor %}</td>
      <td style="font-size:.8rem">{% for k,v in log.new.items() %}<b>{{k}}:</b> {{v}}<br>{% endfor %}</td>
      <td style="font-size:.75rem;color:#666">{{log.ip}}</td>
    </tr>
    {% else %}
    <tr><td colspan=6 class="empty">No audit records.</td></tr>
    {% endfor %}
  </table>
</div>
"""

T_SESSIONS = STYLE + """
<nav class="nav">
  <span class="nav-brand">&#9670; EverNothing</span>
  <a href=/>&#8592; Home</a>
  <a href=/logout class="nav-logout">Logout</a>
</nav>
<div class="container">
  <h3>Login Sessions</h3>
  <p style="color:#666;font-size:.85rem;margin-bottom:16px">Up to 3 concurrent sessions allowed. Revoke any you don't recognize.</p>
  <table>
    <tr><th>Login Time</th><th>Status</th><th>IP Address</th><th>Device</th><th></th></tr>
    {% for s in sessions %}
    <tr {% if s.is_current %}style="background:var(--bg3)"{% endif %}>
      <td class="timestamp">{{s.login_time}}</td>
      <td>
        {% if s.is_current %}<span style="color:#0c0">&#9679; Current</span>
        {% elif s.logout_time == 'Active' %}<span style="color:var(--gold-dim)">Active</span>
        {% else %}<span style="color:#555">{{s.logout_time}}</span>{% endif %}
      </td>
      <td style="font-size:.85rem">{{s.ip}}</td>
      <td style="font-size:.8rem;color:#888">{{s.user_agent}}</td>
      <td>
        {% if not s.is_current and s.logout_time == 'Active' %}
        <a href=/session/revoke/{{s.session_id}} class="btn btn-sm btn-danger">Revoke</a>
        {% endif %}
      </td>
    </tr>
    {% endfor %}
  </table>
</div>
"""

T_ADMIN_AUDIT_LOGS = STYLE + """
<nav class="nav">
  <span class="nav-brand">&#9670; Admin</span>
  <a href=/admin/dashboard>&#8592; Dashboard</a>
  <a href="javascript:location.reload()" style="color:#0c0">Refresh</a>
  <a href=/logout class="nav-logout">Logout</a>
</nav>
<div class="container">
  <h3>Audit Logs</h3>
  <form method="get" class="card" style="margin-bottom:16px">
    <div class="form-row">
      <div>
        <label>Username</label>
        <input name="user" value="{{user_filter}}" placeholder="Filter by user">
      </div>
      <div>
        <label>Action</label>
        <select name="action">
          <option value="">All Actions</option>
          <option value="CREATE" {% if action_filter=='CREATE' %}selected{% endif %}>CREATE</option>
          <option value="UPDATE" {% if action_filter=='UPDATE' %}selected{% endif %}>UPDATE</option>
          <option value="DELETE" {% if action_filter=='DELETE' %}selected{% endif %}>DELETE</option>
        </select>
      </div>
      <div>
        <label>Entity</label>
        <select name="entity">
          <option value="">All Entities</option>
          <option value="note" {% if entity_filter=='note' %}selected{% endif %}>Note</option>
          <option value="attachment" {% if entity_filter=='attachment' %}selected{% endif %}>Attachment</option>
          <option value="user" {% if entity_filter=='user' %}selected{% endif %}>User</option>
        </select>
      </div>
      <div>
        <label>Limit</label>
        <select name="limit">
          <option value="50" {% if limit==50 %}selected{% endif %}>50</option>
          <option value="100" {% if limit==100 %}selected{% endif %}>100</option>
          <option value="500" {% if limit==500 %}selected{% endif %}>500</option>
          <option value="1000" {% if limit==1000 %}selected{% endif %}>1000</option>
        </select>
      </div>
    </div>
    <div class="btn-group">
      <button class="btn btn-primary">Filter</button>
      <a href=/admin/audit_logs class="btn">Clear</a>
      <span style="margin-left:auto;color:#666;font-size:.85rem">{{logs|length}} records</span>
    </div>
  </form>
  <table>
    <tr><th>Time</th><th>User</th><th>Action</th><th>Entity</th><th>Old</th><th>New</th><th>IP</th></tr>
    {% for log in logs %}
    <tr>
      <td class="timestamp">{{log.timestamp}}</td>
      <td>{{log.user}}</td>
      <td><span class="tag-{{log.action|lower}}">{{log.action}}</span></td>
      <td style="font-size:.8rem">{{log.entity}}</td>
      <td style="font-size:.8rem">{% for k,v in log.old.items() %}<b>{{k}}:</b> {{v}}<br>{% endfor %}</td>
      <td style="font-size:.8rem">{% for k,v in log.new.items() %}<b>{{k}}:</b> {{v}}<br>{% endfor %}</td>
      <td style="font-size:.75rem;color:#666">{{log.ip}}</td>
    </tr>
    {% else %}
    <tr><td colspan=7 class="empty">No audit logs found.</td></tr>
    {% endfor %}
  </table>
</div>
"""

# --- JSON API (for Android app) ---
from flask import jsonify

def api_login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated

@app.route("/api/login", methods=["POST"])
@csrf.exempt
def api_login():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid request'}), 400
    con = db(); cur = con.cursor()
    r = cur.execute("SELECT id,password FROM users WHERE username=?", (data.get('username',''),)).fetchone()
    if r and check_password_hash(r[1], data.get('password','')):
        session_id = os.urandom(16).hex()
        session['session_id'] = session_id
        session['last_activity'] = datetime.datetime.now(timezone.utc).isoformat()
        session['remember_me'] = False
        session.permanent = True
        cur.execute("UPDATE users SET last_login=? WHERE id=?", (datetime.datetime.now(timezone.utc).isoformat(), r[0]))
        cur.execute("INSERT INTO user_sessions (user_id, session_id, login_time, ip_address, user_agent) VALUES (?,?,?,?,?)",
            (r[0], session_id, datetime.datetime.now(timezone.utc).isoformat(), request.remote_addr, request.user_agent.string))
        con.commit(); con.close()
        login_user(User(r[0], data['username']))
        return jsonify({'ok': True, 'username': data['username']})
    con.close()
    return jsonify({'error': 'Invalid username or password'}), 401

@app.route("/api/logout", methods=["POST"])
@csrf.exempt
def api_logout():
    if 'session_id' in session:
        con = db(); cur = con.cursor()
        cur.execute("UPDATE user_sessions SET logout_time=? WHERE session_id=?",
            (datetime.datetime.now(timezone.utc).isoformat(), session['session_id']))
        con.commit(); con.close()
    logout_user(); session.clear()
    return jsonify({'ok': True})

@app.route("/api/folders")
@api_login_required
def api_folders():
    con = db(); cur = con.cursor()
    cur.execute("SELECT id,name,parent_id FROM folders WHERE user_id=? ORDER BY name", (current_user.id,))
    folders = [{'id': r[0], 'name': decrypt(r[1]), 'parent_id': r[2]} for r in cur.fetchall()]
    con.close()
    return jsonify(folders)

@app.route("/api/folders", methods=["POST"])
@csrf.exempt
@api_login_required
def api_create_folder():
    data = request.get_json()
    name = (data or {}).get('name', '').strip()
    parent_id = (data or {}).get('parent_id')
    if not name:
        return jsonify({'error': 'Name required'}), 400
    con = db(); cur = con.cursor()
    cur.execute("INSERT INTO folders (user_id, name, parent_id) VALUES(?,?,?)", (current_user.id, encrypt(name), parent_id))
    fid = cur.lastrowid
    con.commit(); con.close(); sync_s3()
    return jsonify({'ok': True, 'id': fid})

@app.route("/api/folders/<int:fid>", methods=["DELETE"])
@csrf.exempt
@api_login_required
def api_delete_folder(fid):
    con = db(); cur = con.cursor()
    delete_recursive(cur, fid, current_user.id)
    con.commit(); con.close(); sync_s3()
    return jsonify({'ok': True})

@app.route("/api/folders/<int:fid>/notes")
@api_login_required
def api_folder_notes(fid):
    con = db(); cur = con.cursor()
    cur.execute("SELECT id,note_key,description,updated_at FROM notes WHERE user_id=? AND folder_id=? ORDER BY note_key", (current_user.id, fid))
    notes = [{'id': r[0], 'key': decrypt(r[1]), 'description': decrypt(r[2]) if r[2] else '', 'updated_at': format_date(r[3])} for r in cur.fetchall()]
    con.close()
    return jsonify(notes)

@app.route("/api/notes/<int:nid>")
@api_login_required
def api_get_note(nid):
    con = db(); cur = con.cursor()
    r = cur.execute("SELECT id,note_key,note_value,description,folder_id,updated_at FROM notes WHERE id=? AND user_id=?", (nid, current_user.id)).fetchone()
    con.close()
    if not r:
        return jsonify({'error': 'Not found'}), 404
    return jsonify({'id': r[0], 'key': decrypt(r[1]), 'value': decrypt(r[2]), 'description': decrypt(r[3]) if r[3] else '', 'folder_id': r[4], 'updated_at': format_date(r[5])})

@app.route("/api/notes", methods=["POST"])
@csrf.exempt
@api_login_required
def api_create_note():
    data = request.get_json() or {}
    key = data.get('key', '').strip()
    value = data.get('value', '').strip()
    fid = data.get('folder_id')
    desc = data.get('description', '')[:255]
    if not key or not value:
        return jsonify({'error': 'Key and value required'}), 400
    con = db(); cur = con.cursor()
    cur.execute("SELECT note_key FROM notes WHERE user_id=?", (current_user.id,))
    if any(decrypt(r[0]).strip().lower() == key.lower() for r in cur.fetchall()):
        con.close()
        return jsonify({'error': 'Note name already exists'}), 409
    now = datetime.datetime.now(timezone.utc).isoformat()
    cur.execute("INSERT INTO notes (user_id, folder_id, note_key, note_value, description, updated_at) VALUES(?,?,?,?,?,?)",
        (current_user.id, fid, encrypt(key), encrypt(value), encrypt(desc), now))
    nid = cur.lastrowid
    cur.execute("INSERT INTO note_history (note_id, user_id, note_key, note_value, description, folder_id, updated_at) VALUES(?,?,?,?,?,?,?)",
        (nid, current_user.id, encrypt(key), encrypt(value), encrypt(desc), fid, now))
    log_change(cur, current_user.id, 'CREATE', 'note', nid, {}, {'key': key, 'folder_id': fid}, request.remote_addr)
    con.commit(); con.close(); sync_s3()
    return jsonify({'ok': True, 'id': nid})

@app.route("/api/notes/<int:nid>", methods=["PUT"])
@csrf.exempt
@api_login_required
def api_update_note(nid):
    data = request.get_json() or {}
    key = data.get('key', '').strip()
    value = data.get('value', '').strip()
    fid = data.get('folder_id')
    desc = data.get('description', '')[:255]
    if not key or not value:
        return jsonify({'error': 'Key and value required'}), 400
    con = db(); cur = con.cursor()
    now = datetime.datetime.now(timezone.utc).isoformat()
    cur.execute("UPDATE notes SET note_key=?,note_value=?,description=?,folder_id=?,updated_at=? WHERE id=? AND user_id=?",
        (encrypt(key), encrypt(value), encrypt(desc), fid, now, nid, current_user.id))
    cur.execute("INSERT INTO note_history (note_id, user_id, note_key, note_value, description, folder_id, updated_at) VALUES(?,?,?,?,?,?,?)",
        (nid, current_user.id, encrypt(key), encrypt(value), encrypt(desc), fid, now))
    log_change(cur, current_user.id, 'UPDATE', 'note', nid, {}, {'key': key, 'folder_id': fid}, request.remote_addr)
    con.commit(); con.close(); sync_s3()
    return jsonify({'ok': True})

@app.route("/api/notes/<int:nid>", methods=["DELETE"])
@csrf.exempt
@api_login_required
def api_delete_note(nid):
    con = db(); cur = con.cursor()
    cur.execute("DELETE FROM notes WHERE id=? AND user_id=?", (nid, current_user.id))
    con.commit(); con.close(); sync_s3()
    return jsonify({'ok': True})

@app.route("/api/search")
@api_login_required
def api_search():
    q = request.args.get('q', '').strip().lower()
    if not q:
        return jsonify([])
    con = db(); cur = con.cursor()
    cur.execute("SELECT id,note_key,note_value,updated_at FROM notes WHERE user_id=?", (current_user.id,))
    results = []
    for r in cur.fetchall():
        k, v = decrypt(r[1]), decrypt(r[2])
        if q in k.lower() or q in v.lower():
            results.append({'id': r[0], 'key': k, 'updated_at': format_date(r[3])})
    con.close()
    return jsonify(sorted(results, key=lambda x: x['key'].lower()))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)


T_ADMIN_S3_BACKUPS = STYLE + """
<h3>S3 Backups</h3>
<a href=/admin/dashboard>Back to Dashboard</a> | <a href=/logout>Logout</a>
{% if message %}<p style="color:#0f0;">{{message}}</p>{% endif %}
{% if error %}<p style="color:red;">{{error}}</p>{% endif %}
<p>Database backups stored in S3 bucket: <b>{{ config.get('S3_BUCKET_NAME', 'N/A') }}</b></p>
<table style="width:100%; border-collapse:collapse; margin-top:20px;">
<tr style="border-bottom:2px solid red;">
<th style="text-align:left; padding:8px;">Backup File</th>
<th style="text-align:left; padding:8px;">Size (bytes)</th>
<th style="text-align:left; padding:8px;">Last Modified</th>
<th style="text-align:left; padding:8px;">Action</th>
</tr>
{% if confirm_key %}
<p>Restore backup <b>{{confirm_key}}</b> to local file?</p>
<form method=post action="/admin/s3_restore/{{confirm_key}}">
<input type=hidden name=csrf_token value="{{ csrf_token() }}">
<button>Yes, Restore</button> <a href=/admin/s3_backups class=cancel>Cancel</a>
</form>
{% else %}
<table style="width:100%; border-collapse:collapse; margin-top:20px;">
<tr style="border-bottom:2px solid red;">
<th style="text-align:left; padding:8px;">Backup File</th>
<th style="text-align:left; padding:8px;">Size (bytes)</th>
<th style="text-align:left; padding:8px;">Last Modified</th>
<th style="text-align:left; padding:8px;">Action</th>
</tr>
{% for backup in backups %}
<tr style="border-bottom:1px solid #333;">
<td style="padding:8px; font-size:small;">{{backup.key}}</td>
<td style="padding:8px;">{{backup.size}}</td>
<td style="padding:8px;">{{backup.modified}}</td>
<td style="padding:8px;"><a href="/admin/s3_restore/{{backup.key}}" style="color:#0f0;">[Restore]</a></td>
</tr>
{% else %}
<tr><td colspan="4" style="padding:20px; text-align:center; color:#888;">No backups found or S3 not configured</td></tr>
{% endfor %}
</table>
{% endif %}
"""
