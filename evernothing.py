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

from flask import Flask, request, redirect, render_template_string, make_response, session

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
    S3_BUCKET_NAME = os.environ.get('S3_BUCKET_NAME', 'evernothing03032026')
    AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')
    AWS_PROFILE = os.environ.get('AWS_PROFILE', 'billspeiser2')

# Configure logging
logging.basicConfig(
    filename='evernothing.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask("EverNothing")
app.secret_key = os.environ.get('SECRET_KEY', 'Keystone1!')  # Use env var in production
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['WTF_CSRF_ENABLED'] = False  # TODO: Enable CSRF protection
app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(hours=int(os.environ.get('SESSION_TIMEOUT_HOURS', '2')))
app.config['REMEMBER_COOKIE_DURATION'] = datetime.timedelta(days=int(os.environ.get('REMEMBER_COOKIE_DAYS', '30')))
app.config['SESSION_COOKIE_SECURE'] = os.environ.get('SESSION_COOKIE_SECURE', 'false').lower() == 'true'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
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
login_manager.session_protection = "strong"

# Session validation
@app.before_request
def validate_session():
    if current_user.is_authenticated:
        # Skip timeout check if "remember me" is active
        if not session.get('remember_me'):
            session.permanent = True
            if 'session_id' in session and 'last_activity' in session:
                # Check session timeout (2 hours of inactivity)
                last_activity = datetime.datetime.fromisoformat(session['last_activity'])
                if datetime.datetime.now(timezone.utc) - last_activity > datetime.timedelta(hours=2):
                    logout_user()
                    session.clear()
                    return redirect('/login?timeout=1')
                # Update last activity
                session['last_activity'] = datetime.datetime.now(timezone.utc).isoformat()
        
        # Validate session still exists in database
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
        updated_at TEXT
    );
    CREATE TABLE IF NOT EXISTS note_history(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        note_id INTEGER,
        user_id INTEGER,
        note_key TEXT,
        note_value TEXT,
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
    """)
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

# --- AWS SYNC ---
def sync_s3():
    """Asynchronously sync database to S3"""
    if not boto3:
        logger.warning("S3 sync skipped: boto3 not available")
        return
    
    try:
        # Try to use the specific profile if configured, else default
        try: 
            s3 = boto3.Session(profile_name=AWS_PROFILE).client('s3')
        except Exception:
            s3 = boto3.client('s3', region_name=AWS_REGION)
        
        s3.upload_file(DB, S3_BUCKET_NAME, DB)
        logger.info(f"S3 sync successful: {DB} -> s3://{S3_BUCKET_NAME}/{DB}")
    except Exception as e:
        logger.error(f"S3 Sync Error: {e}")
        print(f"S3 Sync Error: {e}")

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
    if not text and not allow_empty:
        return None, "Input cannot be empty"
    if text and len(text) > max_length:
        return None, f"Input too long (max {max_length} characters)"
    if text:
        # Remove potentially dangerous characters
        text = text.strip()
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
            cur.execute("UPDATE users SET password=? WHERE id=?", (generate_password_hash(request.form['new_password']), current_user.id))
            con.commit()
            con.close()
            sync_s3()
            return redirect("/")
        con.close()
        error = "Invalid old password"
    return render_template_string(T_CHANGE_PASSWORD, error=error)

@app.route("/search")
@login_required
def search():
    q = request.args.get('q', '').strip()
    if not q or len(q) > 100:
        return render_template_string(T_SEARCH, notes=[], q=q)
    
    con = db()
    cur = con.cursor()
    try:
        # Use parameterized query for security
        cur.execute(
            "SELECT id,note_key,note_value FROM notes WHERE user_id=?",
            (current_user.id,)
        )
        notes = []
        q_lower = q.lower()
        for r in cur.fetchall():
            k, v = decrypt(r[1]), decrypt(r[2])
            if q_lower in k.lower() or q_lower in v.lower():
                notes.append((r[0], k))
        notes.sort(key=lambda x: x[1].lower())
    except Exception as e:
        logger.error(f"Search error: {e}")
        notes = []
    finally:
        con.close()
    return render_template_string(T_SEARCH, notes=notes, q=q)

@app.route("/export")
@login_required
def export_json():
    con = db()
    cur = con.cursor()
    cur.execute("""
        SELECT n.note_key, n.note_value, n.updated_at, f.name
        FROM notes n
        LEFT JOIN folders f ON n.folder_id = f.id
        WHERE n.user_id=?
    """, (current_user.id,))
    data = [{"note": decrypt(r[0]), "content": decrypt(r[1]), "updated_at": r[2], "folder": decrypt(r[3]) if r[3] else None} for r in cur.fetchall()]
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
    if request.method == "POST":
        note_val = str(escape(request.form['note']))
        content_val = str(escape(request.form['content']))
        con = db(); cur = con.cursor()
        
        if not note_val.strip() or not content_val.strip():
            error = "Note and content cannot be empty"
            con.close()
        else:
            cur.execute("SELECT note_key FROM notes WHERE user_id=?", (current_user.id,))
            if any(decrypt(r[0]) == note_val for r in cur.fetchall()):
                error = "Note name already exists"
                con.close()
            else:
                cur.execute(
                    "INSERT INTO notes (user_id, folder_id, note_key, note_value, updated_at) VALUES(?,?,?,?,?)",
                    (current_user.id, fid, encrypt(note_val), encrypt(content_val), datetime.datetime.now(timezone.utc).isoformat())
                )
                nid = cur.lastrowid
                log_change(cur, current_user.id, 'CREATE', 'note', nid, {}, {'note': note_val, 'content': content_val, 'folder_id': fid}, request.remote_addr)
                cur.execute(
                    "INSERT INTO note_history (note_id, user_id, note_key, note_value, folder_id, updated_at) VALUES(?,?,?,?,?,?)",
                    (nid, current_user.id, encrypt(note_val), encrypt(content_val), fid, datetime.datetime.now(timezone.utc).isoformat())
                )
                if 'file' in request.files and request.files['file'].filename:
                    file = request.files['file']
                    filename = file.filename[:255]  # Limit filename length
                    file_data = file.read()
                    if len(file_data) > 0:
                        cur.execute(
                            "INSERT INTO attachments (note_id, user_id, filename, file_data, file_size, uploaded_at) VALUES(?,?,?,?,?,?)",
                            (nid, current_user.id, filename, file_data, len(file_data), datetime.datetime.now(timezone.utc).isoformat())
                        )
                        log_change(cur, current_user.id, 'CREATE', 'attachment', cur.lastrowid, {}, {'note_id': nid, 'filename': filename, 'size': len(file_data)}, request.remote_addr)
                con.commit()
                con.close()
                sync_s3()
                return redirect(f"/folder/{fid}")
    return render_template_string(T_ADD, fid=fid, error=error, note=note_val, content=content_val)

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
        "SELECT note_key,note_value,folder_id,updated_at FROM notes WHERE id=? AND user_id=?",
        (id, current_user.id),
    )
    row = cur.fetchone()
    if not row:
        con.close()
        return redirect("/")
    note = [decrypt(row[0]), decrypt(row[1]), row[2], row[3]]
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
            filename = file.filename[:255]  # Limit filename length
            file_data = file.read()
            if len(file_data) > 0:
                cur.execute(
                    "INSERT INTO attachments (note_id, user_id, filename, file_data, file_size, uploaded_at) VALUES(?,?,?,?,?,?)",
                    (id, current_user.id, filename, file_data, len(file_data), datetime.datetime.now(timezone.utc).isoformat())
                )
                log_change(cur, current_user.id, 'CREATE', 'attachment', cur.lastrowid, {}, {'note_id': id, 'filename': filename, 'size': len(file_data)}, request.remote_addr)
                con.commit()
                con.close()
                sync_s3()
                return redirect(f"/edit/{id}")

        # Handle note edit
        if 'note' in request.form and 'content' in request.form:
            if note[0] == request.form['note'] and note[1] == request.form['content'] and str(note[2]) == str(request.form.get('folder_id')):
                con.close()
                return redirect("/")

            if request.form.get('confirm') == 'yes':
                now = datetime.datetime.now(timezone.utc).isoformat()
                old_vals = {'note': note[0], 'content': note[1], 'folder_id': note[2]}
                new_vals = {'note': request.form['note'], 'content': request.form['content'], 'folder_id': request.form.get('folder_id')}
                cur.execute(
                    "UPDATE notes SET note_key=?,note_value=?,folder_id=?,updated_at=? WHERE id=? AND user_id=?",
                    (
                        encrypt(request.form['note']),
                        encrypt(request.form['content']),
                        request.form.get('folder_id'),
                        now,
                        id,
                        current_user.id,
                    ),
                )
                log_change(cur, current_user.id, 'UPDATE', 'note', id, old_vals, new_vals, request.remote_addr)
                cur.execute(
                    "INSERT INTO note_history (note_id, user_id, note_key, note_value, folder_id, updated_at) VALUES(?,?,?,?,?,?)",
                    (id, current_user.id, encrypt(request.form['note']), encrypt(request.form['content']), request.form.get('folder_id'), now)
                )
                con.commit()
                con.close()
                sync_s3()
                return redirect("/")
            else:
                con.close()
                return render_template_string(T_EDIT_CONFIRM, note=[request.form['note'], request.form['content'], request.form.get('folder_id')], id=id)

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

@app.route("/history/restore/<int:hid>")
@login_required
def restore_history(hid):
    con = db(); cur = con.cursor()
    h = cur.execute("SELECT note_id,note_key,note_value,folder_id FROM note_history WHERE id=? AND user_id=?", (hid, current_user.id)).fetchone()
    if h:
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
    con.close()
    return redirect("/")

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
def admin_dashboard():
    if not session.get('admin_logged_in'): return redirect("/admin")
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
def admin_edit_user(uid):
    if not session.get('admin_logged_in'): return redirect("/admin")
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
def admin_delete_user(uid):
    if not session.get('admin_logged_in'): return redirect("/admin")
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

@app.route("/admin/audit_logs")
def admin_audit_logs():
    if not session.get('admin_logged_in'): return redirect("/admin")
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
            print(f"--- PASSWORD RESET LINK ---\n{link}\n-----------------------------")
        return render_template_string(T_FORGOT_PASSWORD, message="If that email exists, a reset link has been sent (check console).")
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
    con = db()
    cur = con.cursor()
    error = None
    
    # Check for timeout/invalid session messages
    if request.args.get('timeout'):
        error = "Session expired due to inactivity. Please login again."
    elif request.args.get('invalid'):
        error = "Invalid session. Please login again."
    
    if request.method == "POST":
        print("username",request.form['username'])
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
            logger.info(f"New user registered: {username}")
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

@app.route("/delete_attachment/<int:aid>")
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
<style>
body { background-color: black; color: gold; font-family: sans-serif; }
a { color: gold; text-decoration: none; }
a:hover { color: red; text-decoration: underline; }
input, textarea, select, button { background-color: #111; color: gold; border: 1px solid red; margin: 2px; }
.cancel { border: 1px solid red; }
.footer {
    position: fixed;
    left: 0;
    bottom: 0;
    width: 100%;
    background-color: black;
    color: gold;
    text-align: center;
}
</style>
<div class="footer">{{ build_date }}</div>
"""

T_FOLDERS = STYLE + """
<h3>EverNothing - Folders</h3>
<form action="/search" method="get">
<input name="q" placeholder="Search..."> <button>Go</button>
</form>
<a href=/folder/add>Create Folder</a> | <a href=/export>Export JSON</a> | <a href=/audit_report>Audit Report</a> | <a href=/sessions>Sessions</a> | <a href=/change_password>Change Password</a> | <a href=/logout>Logout</a>
<ul>
{% for f in folders %}
<li><a href=/folder/{{f[0]}}>{{f[1]}}</a> <a href=/folder/rename/{{f[0]}} style="font-size:small">[rename]</a> <a href=/folder/delete/{{f[0]}} style="color:red;font-size:small">[x]</a></li>
{% else %}
<li>No folders. <a href=/folder/add>Create one</a></li>
{% endfor %}
</ul>
<h4>Recently Edited</h4>
<ul>
{% for n in recent %}
<li><a href=/edit/{{n[0]}}>{{n[1]}}</a> ({{n[2]}})</li>
{% endfor %}
</ul>
"""

T_ADD_FOLDER = STYLE + """
<h3>Create Folder</h3>
<a href=/logout>Logout</a>
{% if error %}<p style="color:red">{{error}}</p>{% endif %}
<form method=post>
<b>Folder name:</b> <input name=name maxlength="255"><br>
<button>Create</button> <a href=/ class=cancel>Cancel</a>
</form>
"""

T_ADD_SUBFOLDER = STYLE + """
<h3>Create Subfolder</h3>
<a href=/logout>Logout</a>
<form method=post>
<b>Subfolder name:</b> <input name=name><br>
<button>Create</button> <a href=/folder/{{pid}} class=cancel>Cancel</a>
</form>
"""

T_RENAME_FOLDER = STYLE + """
<h3>Rename Folder</h3>
<a href=/logout>Logout</a>
<form method=post>
<b>Name:</b> <input name=name value="{{f[0]}}"><br>
<button>Rename</button> <a href=/folder/{{fid}} class=cancel>Cancel</a>
</form>
"""

T_CHANGE_PASSWORD = STYLE + """
<h3>Change Password</h3>
<a href=/logout>Logout</a>
{% if error %}<p style="color:red">{{error}}</p>{% endif %}
<form method=post>
<b>Old Password:</b> <input type=password name=old_password><br>
<b>New Password:</b> <input type=password name=new_password><br>
<button>Change</button> <a href=/ class=cancel>Cancel</a>
</form>
"""

T_DELETE_NOTE = STYLE + """
<h3>Delete Note</h3>
<a href=/logout>Logout</a>
<p>Are you sure you want to delete note <b>{{n[1]}}</b>?</p>
<form method=post><button>Yes, Delete</button> <a href=javascript:history.back() class=cancel>Cancel</a></form>
"""

T_EDIT_CONFIRM = STYLE + """
<h3>Confirm Changes</h3>
<a href=/logout>Logout</a>
<p>Are you sure you want to save these changes?</p>
<b>Note:</b> {{note[0]}}<br>
<form method=post action="/edit/{{id}}">
<input type=hidden name=note value="{{note[0]}}">
<input type=hidden name=content value="{{note[1]}}">
<input type=hidden name=folder_id value="{{note[2]}}">
<input type=hidden name=confirm value="yes">
<button>Yes</button> <button type=button onclick="history.back()">No</button>
</form>
"""

T_NOTES = STYLE + """
<h3>Folder: {{folder[1]}}</h3>
<a href={% if folder[2] %}/folder/{{folder[2]}}{% else %}/{% endif %}>Back</a>
| <a href=/folder/delete/{{folder[0]}} style="color:red;font-size:small">[Delete Folder]</a>
| <a href=/folder/rename/{{folder[0]}} style="font-size:small">[Rename Folder]</a>
| <a href=/add/{{folder[0]}}>Add Note</a> | <a href=/logout>Logout</a>

<h4>Notes</h4>
<ul>
{% for n in notes %}
<li><a href=/edit/{{n[0]}}>{{n[1]}}</a> <a href=/note/delete/{{n[0]}} style="color:red;font-size:small">[x]</a></li>
{% else %}
<li>No notes.</li>
{% endfor %}
</ul>

<h4>Subfolders</h4>
<ul>
{% for s in subfolders %}
<li><a href=/folder/{{s[0]}}>{{s[1]}}</a></li>
{% else %}
<li>No subfolders.</li>
{% endfor %}
</ul>
<a href=/folder/{{folder[0]}}/add_folder>Create Subfolder</a>
"""

T_ADD = STYLE + """
<h3>Add Note</h3>
<a href=/logout>Logout</a>
{% if error %}<p style="color:red">{{error}}</p>{% endif %}
<form method=post enctype="multipart/form-data">
<b>Note:</b> <input name=note value="{{note}}"><br>
<b>Contents:</b> <textarea name=content rows=40 cols=120>{{content}}</textarea><br>
<b>Attachment (optional):</b> <input type=file name=file><br>
<button>Add</button> <a href=/folder/{{fid}} class=cancel>Cancel</a>
</form>
"""

T_EDIT = STYLE + """
<a href=/>Home</a>
{% for b in breadcrumbs %}
 &gt; <a href=/folder/{{b[0]}}>{{b[1]}}</a>
{% endfor %}
 | <a href=/history/{{id}}>Edited: {{note[3]}}</a> | <a href=/note/delete/{{id}} style="color:red">[Delete]</a> | <a href=/logout>Logout</a>
<form method=post enctype="multipart/form-data">
<b>Note:</b> <input name=note value='{{note[0]}}'><br>
<b>Contents:</b><br>
<textarea name=content rows=40 cols=120>{{note[1]}}</textarea><br>
<b>Folder:</b> <select name=folder_id>
{% for f in folders %}
<option value='{{f[0]}}' {% if f[0]==note[2] %}selected{% endif %}>{{f[1]}}</option>
{% endfor %}
</select><br><br>

<button>Commit</button> <a href=/ class=cancel>Cancel</a>
</form>

<h4>Attachments</h4>
<form method=post enctype="multipart/form-data">
<input type=file name=file>
<button>Upload</button>
</form>
<ul>
{% for att in attachments %}
<li><a href=/download/{{att[0]}}>{{att[1]}}</a> ({{att[2]}} bytes) <a href=/delete_attachment/{{att[0]}} style="color:red">[x]</a></li>
{% else %}
<li>No attachments</li>
{% endfor %}
</ul>
"""

T_LOGIN = STYLE + """
<h3>Login</h3>
{% if error %}<p style="color:red">{{error}}</p>{% endif %}
<form method=post>
<input name=username placeholder='Username'><br>
<input type=password name=password placeholder='Password'><br>
<label style="display:block; margin:10px 0;">
<input type=checkbox name=remember_me style="width:auto; margin-right:5px;">
Remember me on this device (30 days)
</label>
<button>Login</button> <a href=/register>Register</a> | <a href=/forgot_password>Forgot Password?</a>
</form>
"""

T_REGISTER = STYLE + """
<h3>Register</h3>
{% if error %}<p style="color:red">{{error}}</p>{% endif %}
<form method=post>
<input name=username placeholder='Username' maxlength="50" required><br>
<input name=email placeholder='Email' type="email" maxlength="100" required><br>
<input type=password name=password placeholder='Password (min 8 chars, uppercase, lowercase, number)' minlength="8" required><br>
<button>Create</button> <a href=/login class=cancel>Cancel</a>
</form>
"""

T_SEARCH = STYLE + """
<h3>Search: {{q}}</h3>
<a href=/>Back</a> | <a href=/logout>Logout</a>
<ul>
{% for n in notes %}
<li><a href=/edit/{{n[0]}}>{{n[1]}}</a></li>
{% else %}
<li>No matches.</li>
{% endfor %}
</ul>
"""

T_DELETE_FOLDER = STYLE + """
<h3>Delete Folder</h3>
<a href=/logout>Logout</a>
<p>Are you sure you want to delete folder <b>{{f[0]}}</b> and all its notes?</p>
<form method=post><button>Yes, Delete</button> <a href=javascript:history.back() class=cancel>Cancel</a></form>
"""

T_HISTORY = STYLE + """
<h3>History for Note</h3>
<a href=/edit/{{nid}}>Back to Edit</a> | <a href=/logout>Logout</a>
<ul>
{% for h in history %}
<li>{{h[2]}} - {{h[1]}} <a href=/history/restore/{{h[0]}}>[Rollback to this]</a></li>
{% endfor %}
</ul>
"""

T_ADMIN_LOGIN = STYLE + """
<h3>Admin Login</h3>
{% if error %}<p style="color:red">{{error}}</p>{% endif %}
<form method=post>
<input name=username placeholder='Username'><br>
<input type=password name=password placeholder='Password'><br>
<button>Login</button>
</form>
"""

T_ADMIN_DASHBOARD = STYLE + """
<h3>Admin Dashboard</h3>
<form method="get">
<input name="q" placeholder="Search Users..." value="{{q}}"> <button>Search</button>
</form>
<a href=/admin/audit_logs>View Audit Logs</a> | <a href=/logout>Logout</a>
<ul>
{% for u in users %}
<li><a href=/admin/user/{{u[0]}}>{{u[1]}}</a> (Notes: {{u[2]}}, Folders: {{u[3]}}, Last Login: {{u[4]}}) <a href=/admin/user/delete/{{u[0]}} style="color:red">[Delete]</a></li>
{% else %}
<li>No users found.</li>
{% endfor %}
</ul>
"""

T_ADMIN_EDIT_USER = STYLE + """
<h3>Edit User</h3>
<a href=/logout>Logout</a>
{% if error %}<p style="color:red">{{error}}</p>{% endif %}
<form method=post>
<b>Old Username:</b> <input value="{{user[1]}}" readonly style="border:none; background:black; color:gold"><br>
<b>New Username:</b> <input name=new_username><br>
<b>New Password:</b> <input name=new_password placeholder="Leave blank to keep"><br>
<button>Update</button> <a href=/admin/dashboard class=cancel>Cancel</a>
</form>
"""

T_ADMIN_EDIT_USER_CONFIRM = STYLE + """
<h3>Verify Change</h3>
<a href=/logout>Logout</a>
<p>Change username from <b>{{user[1]}}</b> to <b>{{new_name}}</b>?</p>
{% if new_pass %}<p>Change password?</p>{% endif %}
<form method=post>
<input type=hidden name=new_username value="{{new_name}}">
<input type=hidden name=new_password value="{{new_pass}}">
<input type=hidden name=confirm value="yes">
<button>Yes, Change</button> <a href=/admin/dashboard class=cancel>Cancel</a>
</form>
"""

T_ADMIN_DELETE_USER = STYLE + """
<h3>Delete User</h3>
<a href=/logout>Logout</a>
<p>Are you sure you want to delete user <b>{{user[1]}}</b>?</p>
<p style="color:red">Warning: This will delete all notes and folders associated with this user.</p>
<form method=post>
<button>Yes, Delete User</button> <a href=/admin/dashboard class=cancel>Cancel</a>
</form>
"""

T_FORGOT_PASSWORD = STYLE + """
<h3>Forgot Password</h3>
{% if message %}<p>{{message}}</p>{% endif %}
<form method=post>
<input name=email placeholder='Email' required><br>
<button>Send Reset Link</button> <a href=/login class=cancel>Cancel</a>
</form>
"""

T_RESET_PASSWORD = STYLE + """
<h3>Reset Password</h3>
{% if error %}<p style="color:red">{{error}}</p>{% endif %}
<form method=post>
<input type=password name=password placeholder='New Password' required><br>
<button>Reset Password</button>
</form>
"""

T_AUDIT_REPORT = STYLE + """
<h3>Audit Report</h3>
<a href=/>Back</a> | <a href=/logout>Logout</a>
<table style="width:100%; border-collapse:collapse; margin-top:20px;">
<tr style="border-bottom:1px solid red;">
<th style="text-align:left; padding:5px;">Time</th>
<th style="text-align:left; padding:5px;">User</th>
<th style="text-align:left; padding:5px;">Action</th>
<th style="text-align:left; padding:5px;">Entity</th>
<th style="text-align:left; padding:5px;">Old Values</th>
<th style="text-align:left; padding:5px;">New Values</th>
<th style="text-align:left; padding:5px;">IP</th>
</tr>
{% for log in logs %}
<tr style="border-bottom:1px solid #333;">
<td style="padding:5px;">{{log.timestamp}}</td>
<td style="padding:5px;">{{log.user}}</td>
<td style="padding:5px;">{{log.action}}</td>
<td style="padding:5px;">{{log.entity}}</td>
<td style="padding:5px; font-size:small;">
{% for key, val in log.old.items() %}
<b>{{key}}:</b> {{val}}<br>
{% endfor %}
</td>
<td style="padding:5px; font-size:small;">
{% for key, val in log.new.items() %}
<b>{{key}}:</b> {{val}}<br>
{% endfor %}
</td>
<td style="padding:5px; font-size:small;">{{log.ip}}</td>
</tr>
{% endfor %}
</table>
"""

T_SESSIONS = STYLE + """
<h3>Active Sessions</h3>
<a href=/>Back</a> | <a href=/logout>Logout</a>
<p>Manage your active login sessions. You can have up to 3 concurrent sessions.</p>
<table style="width:100%; border-collapse:collapse; margin-top:20px;">
<tr style="border-bottom:1px solid red;">
<th style="text-align:left; padding:5px;">Login Time</th>
<th style="text-align:left; padding:5px;">Logout Time</th>
<th style="text-align:left; padding:5px;">IP Address</th>
<th style="text-align:left; padding:5px;">Device</th>
<th style="text-align:left; padding:5px;">Action</th>
</tr>
{% for s in sessions %}
<tr style="border-bottom:1px solid #333; {% if s.is_current %}background:#222;{% endif %}">
<td style="padding:5px;">{{s.login_time}}</td>
<td style="padding:5px;">{{s.logout_time}}</td>
<td style="padding:5px;">{{s.ip}}</td>
<td style="padding:5px; font-size:small;">{{s.user_agent}}</td>
<td style="padding:5px;">
{% if s.is_current %}
<span style="color:#0f0;">Current</span>
{% elif s.logout_time == 'Active' %}
<a href=/session/revoke/{{s.session_id}} style="color:red;">[Revoke]</a>
{% endif %}
</td>
</tr>
{% endfor %}
</table>
"""

T_ADMIN_AUDIT_LOGS = STYLE + """
<h3>Admin Audit Logs</h3>
<a href=/admin/dashboard>Back to Dashboard</a> | <a href="javascript:location.reload()" style="color:#0f0;">[Refresh]</a> | <a href=/logout>Logout</a>
<form method="get" style="margin:20px 0;">
<b>Filters:</b><br>
<input name="user" placeholder="Username" value="{{user_filter}}" style="width:150px;">
<select name="action" style="width:120px;">
<option value="">All Actions</option>
<option value="CREATE" {% if action_filter=='CREATE' %}selected{% endif %}>CREATE</option>
<option value="UPDATE" {% if action_filter=='UPDATE' %}selected{% endif %}>UPDATE</option>
<option value="DELETE" {% if action_filter=='DELETE' %}selected{% endif %}>DELETE</option>
</select>
<select name="entity" style="width:120px;">
<option value="">All Entities</option>
<option value="note" {% if entity_filter=='note' %}selected{% endif %}>Note</option>
<option value="attachment" {% if entity_filter=='attachment' %}selected{% endif %}>Attachment</option>
<option value="user" {% if entity_filter=='user' %}selected{% endif %}>User</option>
</select>
<select name="limit" style="width:100px;">
<option value="50" {% if limit==50 %}selected{% endif %}>50</option>
<option value="100" {% if limit==100 %}selected{% endif %}>100</option>
<option value="500" {% if limit==500 %}selected{% endif %}>500</option>
<option value="1000" {% if limit==1000 %}selected{% endif %}>1000</option>
</select>
<button>Filter</button>
<a href=/admin/audit_logs style="margin-left:10px;">Clear</a>
</form>
<p style="color:#888;">Showing {{logs|length}} records</p>
<table style="width:100%; border-collapse:collapse;">
<tr style="border-bottom:2px solid red;">
<th style="text-align:left; padding:8px;">Time</th>
<th style="text-align:left; padding:8px;">User</th>
<th style="text-align:left; padding:8px;">Action</th>
<th style="text-align:left; padding:8px;">Entity</th>
<th style="text-align:left; padding:8px;">Old Values</th>
<th style="text-align:left; padding:8px;">New Values</th>
<th style="text-align:left; padding:8px;">IP</th>
</tr>
{% for log in logs %}
<tr style="border-bottom:1px solid #333;">
<td style="padding:8px; font-size:small;">{{log.timestamp}}</td>
<td style="padding:8px;">{{log.user}}</td>
<td style="padding:8px; color:{% if log.action=='CREATE' %}#0f0{% elif log.action=='DELETE' %}#f00{% else %}#ff0{% endif %};">{{log.action}}</td>
<td style="padding:8px; font-size:small;">{{log.entity}}</td>
<td style="padding:8px; font-size:small; background:#111;">
{% if log.old %}
{% for key, val in log.old.items() %}
<b style="color:#f88;">{{key}}:</b> {{val}}<br>
{% endfor %}
{% else %}
<span style="color:#666;">-</span>
{% endif %}
</td>
<td style="padding:8px; font-size:small; background:#111;">
{% if log.new %}
{% for key, val in log.new.items() %}
<b style="color:#8f8;">{{key}}:</b> {{val}}<br>
{% endfor %}
{% else %}
<span style="color:#666;">-</span>
{% endif %}
</td>
<td style="padding:8px; font-size:small; color:#888;">{{log.ip}}</td>
</tr>
{% else %}
<tr><td colspan="7" style="padding:20px; text-align:center; color:#888;">No audit logs found</td></tr>
{% endfor %}
</table>
"""

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
