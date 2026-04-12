"""
EverNothing Android Application
Runs a local Flask server on the device (via Termux) and periodically
checkpoints the SQLite database to S3.

Quick install on Android (Termux):
  curl -fsSL https://raw.githubusercontent.com/YOUR_REPO/main/evernothing_android/install_android.sh | bash

Manual install:
  pkg install python git -y
  pip install flask flask-login werkzeug boto3 cryptography python-dotenv
  python evernothing_android.py

Access: http://127.0.0.1:5000
"""

import datetime, logging, os, sqlite3, threading, time
from typing import Optional
from flask import Flask, redirect, render_template_string, request, session
from flask_login import (LoginManager, UserMixin, current_user,
                         login_required, login_user, logout_user)
from werkzeug.security import check_password_hash, generate_password_hash
from config_loader import load_config

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
config = load_config()

DB              = config['DB_FILE']
S3_BUCKET_NAME  = config['S3_BUCKET_NAME']
AWS_REGION      = config['AWS_REGION']
AWS_ACCESS_KEY_ID     = config.get('AWS_ACCESS_KEY_ID') or None
AWS_SECRET_ACCESS_KEY = config.get('AWS_SECRET_ACCESS_KEY') or None
ENCRYPTION_ENABLED    = config.get('ENCRYPTION_ENABLED', 'true').lower() == 'true'
# How often (seconds) the background thread checkpoints to S3. Default 15 min.
CHECKPOINT_INTERVAL = int(os.environ.get('CHECKPOINT_INTERVAL', str(15 * 60)))

# Derive AES-256 key from SECRET_KEY — no separate key file needed.
# WARNING: changing SECRET_KEY makes existing encrypted notes unreadable.
try:
    import hashlib
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM as _AESGCM
    _aes_key = hashlib.pbkdf2_hmac(
        'sha256',
        config['SECRET_KEY'].encode('utf-8'),
        b'evernothing-aes-key-v1',
        iterations=100_000,
        dklen=32
    )
    _aesgcm = _AESGCM(_aes_key)
    _encryption_available = True
except Exception:
    _aesgcm = None
    _encryption_available = False

def _encrypt(txt: str) -> str:
    if not ENCRYPTION_ENABLED or not _encryption_available or not txt:
        return txt or ''
    import base64
    nonce = os.urandom(12)
    return base64.b64encode(nonce + _aesgcm.encrypt(nonce, txt.encode(), None)).decode()

def _decrypt(txt: str) -> str:
    if not txt:
        return ''
    try:
        import base64
        data = base64.b64decode(txt)
        return _aesgcm.decrypt(data[:12], data[12:], None).decode()
    except Exception:
        return txt  # plaintext passthrough for unencrypted legacy data

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[logging.StreamHandler()]
)
log = logging.getLogger('evernothing')

# ---------------------------------------------------------------------------
# Flask app
# ---------------------------------------------------------------------------
app = Flask("EverNothingAndroid")
app.secret_key = config['SECRET_KEY']
app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(days=30)

login_manager = LoginManager(app)
login_manager.login_view = "login"

class User(UserMixin):
    def __init__(self, id, username):
        self.id = id
        self.username = username

@login_manager.user_loader
def load_user(uid):
    con = sqlite3.connect(DB)
    try:
        r = con.cursor().execute(
            "SELECT id,username FROM users WHERE id=?", (uid,)).fetchone()
    finally:
        con.close()
    return User(*r) if r else None

# ---------------------------------------------------------------------------
# S3 checkpoint
# ---------------------------------------------------------------------------
_last_checkpoint: Optional[datetime.datetime] = None
_checkpoint_lock = threading.Lock()

def _s3_client():
    try:
        import boto3
    except ImportError:
        return None
    kwargs = {'region_name': AWS_REGION, 'verify': True}
    if AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY:
        kwargs['aws_access_key_id']     = AWS_ACCESS_KEY_ID
        kwargs['aws_secret_access_key'] = AWS_SECRET_ACCESS_KEY
    return boto3.client('s3', **kwargs)

def sync_to_s3(silent=False) -> bool:
    """Checkpoint the local DB to S3. Returns True on success."""
    if not S3_BUCKET_NAME:
        if not silent:
            log.warning("S3_BUCKET_NAME not configured — skipping checkpoint")
        return False
    if not os.path.exists(DB):
        log.warning(f"DB file '{DB}' not found — skipping checkpoint")
        return False
    s3 = _s3_client()
    if s3 is None:
        log.warning("boto3 not installed — skipping checkpoint")
        return False
    try:
        import gzip, io
        # Ensure bucket exists
        try:
            s3.head_bucket(Bucket=S3_BUCKET_NAME)
        except Exception:
            if AWS_REGION == 'us-east-1':
                s3.create_bucket(Bucket=S3_BUCKET_NAME)
            else:
                s3.create_bucket(Bucket=S3_BUCKET_NAME,
                    CreateBucketConfiguration={'LocationConstraint': AWS_REGION})
            s3.put_public_access_block(Bucket=S3_BUCKET_NAME,
                PublicAccessBlockConfiguration={
                    'BlockPublicAcls': True, 'IgnorePublicAcls': True,
                    'BlockPublicPolicy': True, 'RestrictPublicBuckets': True})
            log.info(f"Created S3 bucket: {S3_BUCKET_NAME}")

        sse = {'ServerSideEncryption': 'AES256'}
        ts  = datetime.datetime.utcnow().strftime('%Y%m%d_%H%M%S')

        with open(DB, 'rb') as f:
            raw = f.read()

        # Compressed timestamped backup
        buf = io.BytesIO()
        with gzip.GzipFile(fileobj=buf, mode='wb') as gz:
            gz.write(raw)
        buf.seek(0)
        s3.upload_fileobj(buf, S3_BUCKET_NAME,
                          f"backups/android/{DB}.{ts}.gz", ExtraArgs=sse)

        # Latest copy (uncompressed for easy restore)
        s3.upload_fileobj(io.BytesIO(raw), S3_BUCKET_NAME,
                          f"android/{DB}", ExtraArgs=sse)

        global _last_checkpoint
        _last_checkpoint = datetime.datetime.utcnow()
        log.info(f"S3 checkpoint OK → s3://{S3_BUCKET_NAME}/backups/android/{DB}.{ts}.gz")
        return True

    except Exception as e:
        log.error(f"S3 checkpoint failed: {e}")
        return False

def _checkpoint_loop():
    """Background thread: checkpoint every CHECKPOINT_INTERVAL seconds."""
    log.info(f"S3 checkpoint thread started (every {CHECKPOINT_INTERVAL}s)")
    # Initial delay so the app is fully up before first sync
    time.sleep(30)
    while True:
        with _checkpoint_lock:
            sync_to_s3(silent=True)
        time.sleep(CHECKPOINT_INTERVAL)

# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------
_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    email TEXT,
    last_login TEXT
);
CREATE TABLE IF NOT EXISTS folders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    parent_id INTEGER
);
CREATE TABLE IF NOT EXISTS notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    folder_id INTEGER,
    note_key TEXT NOT NULL,
    note_value TEXT NOT NULL,
    description TEXT,
    updated_at TEXT
);
CREATE TABLE IF NOT EXISTS note_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    note_id INTEGER, user_id INTEGER,
    note_key TEXT, note_value TEXT,
    description TEXT, folder_id INTEGER, updated_at TEXT
);
CREATE TABLE IF NOT EXISTS user_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER, session_id TEXT,
    login_time TEXT, logout_time TEXT,
    ip_address TEXT, user_agent TEXT
);
"""

def init_db():
    with sqlite3.connect(DB) as con:
        con.executescript(_SCHEMA)

def _now():
    return datetime.datetime.utcnow().isoformat()

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.route("/")
@login_required
def index():
    con = sqlite3.connect(DB)
    try:
        cur = con.cursor()
        notes   = cur.execute("SELECT COUNT(*) FROM notes   WHERE user_id=?", (current_user.id,)).fetchone()[0]
        folders = cur.execute("SELECT COUNT(*) FROM folders WHERE user_id=?", (current_user.id,)).fetchone()[0]
        folder_list = cur.execute(
            "SELECT id,name FROM folders WHERE user_id=? AND parent_id IS NULL ORDER BY name",
            (current_user.id,)).fetchall()
    finally:
        con.close()
    next_cp = ""
    if _last_checkpoint:
        elapsed = (datetime.datetime.utcnow() - _last_checkpoint).seconds
        remaining = max(0, CHECKPOINT_INTERVAL - elapsed)
        next_cp = f"{remaining // 60}m {remaining % 60}s"
    return render_template_string(T_HOME,
        note_count=notes, folder_count=folders,
        folders=folder_list,
        last_checkpoint=_last_checkpoint.strftime('%H:%M:%S UTC') if _last_checkpoint else 'Never',
        next_checkpoint=next_cp,
        bucket=S3_BUCKET_NAME)

@app.route("/folder/<int:fid>")
@login_required
def folder(fid):
    con = sqlite3.connect(DB)
    try:
        cur = con.cursor()
        fname = cur.execute("SELECT name FROM folders WHERE id=? AND user_id=?",
                            (fid, current_user.id)).fetchone()
        if not fname:
            return redirect("/")
        notes = cur.execute(
            "SELECT id,note_key,updated_at FROM notes WHERE user_id=? AND folder_id=? ORDER BY note_key",
            (current_user.id, fid)).fetchall()
        notes = [(r[0], _decrypt(r[1]), r[2]) for r in notes]
        subfolders = cur.execute(
            "SELECT id,name FROM folders WHERE user_id=? AND parent_id=? ORDER BY name",
            (current_user.id, fid)).fetchall()
    finally:
        con.close()
    return render_template_string(T_FOLDER,
        fname=fname[0], fid=fid, notes=notes, subfolders=subfolders)

@app.route("/note/<int:nid>")
@login_required
def view_note(nid):
    con = sqlite3.connect(DB)
    try:
        r = con.cursor().execute(
            "SELECT note_key,note_value,description,updated_at,folder_id FROM notes WHERE id=? AND user_id=?",
            (nid, current_user.id)).fetchone()
    finally:
        con.close()
    if not r:
        return redirect("/")
    return render_template_string(T_NOTE, nid=nid,
        key=_decrypt(r[0]), value=_decrypt(r[1]),
        desc=_decrypt(r[2]) if r[2] else '',
        updated=r[3] or '', fid=r[4])

@app.route("/note/add/<int:fid>", methods=["GET","POST"])
@login_required
def add_note(fid):
    error = None
    if request.method == "POST":
        key   = request.form.get('key','').strip()
        value = request.form.get('value','').strip()
        desc  = request.form.get('desc','').strip()[:255]
        if not key or not value:
            error = "Key and value are required."
        else:
            con = sqlite3.connect(DB)
            try:
                cur = con.cursor()
                exists = cur.execute(
                    "SELECT 1 FROM notes WHERE user_id=? AND note_key=?",
                    (current_user.id, key)).fetchone()
                if exists:
                    error = "A note with that name already exists."
                else:
                    cur.execute(
                        "INSERT INTO notes (user_id,folder_id,note_key,note_value,description,updated_at) VALUES(?,?,?,?,?,?)",
                        (current_user.id, fid, _encrypt(key), _encrypt(value), _encrypt(desc), _now()))
                    con.commit()
                    return redirect(f"/folder/{fid}")
            finally:
                con.close()
    return render_template_string(T_ADD_NOTE, fid=fid, error=error)

@app.route("/note/edit/<int:nid>", methods=["GET","POST"])
@login_required
def edit_note(nid):
    con = sqlite3.connect(DB)
    try:
        r = con.cursor().execute(
            "SELECT note_key,note_value,description,folder_id FROM notes WHERE id=? AND user_id=?",
            (nid, current_user.id)).fetchone()
    finally:
        con.close()
    if not r:
        return redirect("/")
    error = None
    if request.method == "POST":
        key   = request.form.get('key','').strip()
        value = request.form.get('value','').strip()
        desc  = request.form.get('desc','').strip()[:255]
        if not key or not value:
            error = "Key and value are required."
        else:
            con = sqlite3.connect(DB)
            try:
                cur = con.cursor()
                cur.execute(
                    "UPDATE notes SET note_key=?,note_value=?,description=?,updated_at=? WHERE id=? AND user_id=?",
                    (_encrypt(key), _encrypt(value), _encrypt(desc), _now(), nid, current_user.id))
                con.commit()
            finally:
                con.close()
            return redirect(f"/note/{nid}")
    return render_template_string(T_EDIT_NOTE, nid=nid,
        key=_decrypt(r[0]), value=_decrypt(r[1]),
        desc=_decrypt(r[2]) if r[2] else '', fid=r[3], error=error)

@app.route("/note/delete/<int:nid>", methods=["POST"])
@login_required
def delete_note(nid):
    con = sqlite3.connect(DB)
    try:
        fid = con.cursor().execute(
            "SELECT folder_id FROM notes WHERE id=? AND user_id=?",
            (nid, current_user.id)).fetchone()
        con.cursor().execute("DELETE FROM notes WHERE id=? AND user_id=?",
                             (nid, current_user.id))
        con.commit()
    finally:
        con.close()
    return redirect(f"/folder/{fid[0]}" if fid else "/")

@app.route("/folder/add", methods=["GET","POST"])
@login_required
def add_folder():
    error = None
    if request.method == "POST":
        name = request.form.get('name','').strip()
        parent_id = request.form.get('parent_id') or None
        if not name:
            error = "Folder name is required."
        else:
            con = sqlite3.connect(DB)
            try:
                con.cursor().execute(
                    "INSERT INTO folders (user_id,name,parent_id) VALUES(?,?,?)",
                    (current_user.id, name, parent_id))
                con.commit()
            finally:
                con.close()
            return redirect("/")
    return render_template_string(T_ADD_FOLDER, error=error)

@app.route("/search")
@login_required
def search():
    q = request.args.get('q','').strip().lower()
    results = []
    if q:
        con = sqlite3.connect(DB)
        try:
            rows = con.cursor().execute(
                "SELECT id,note_key,note_value,folder_id FROM notes WHERE user_id=?",
                (current_user.id,)).fetchall()
        finally:
            con.close()
        results = [(r[0], _decrypt(r[1]), _decrypt(r[2]), r[3]) for r in rows
                   if q in _decrypt(r[1]).lower() or q in _decrypt(r[2]).lower()]
    return render_template_string(T_SEARCH, q=q, results=results)

@app.route("/checkpoint", methods=["POST"])
@login_required
def manual_checkpoint():
    with _checkpoint_lock:
        ok = sync_to_s3()
    return render_template_string(T_CHECKPOINT, success=ok,
        bucket=S3_BUCKET_NAME,
        ts=_last_checkpoint.strftime('%H:%M:%S UTC') if _last_checkpoint else 'N/A')

@app.route("/login", methods=["GET","POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get('username','').strip()
        password = request.form.get('password','')
        con = sqlite3.connect(DB)
        try:
            r = con.cursor().execute(
                "SELECT id,password FROM users WHERE username=?", (username,)).fetchone()
        finally:
            con.close()
        if r and check_password_hash(r[1], password):
            login_user(User(r[0], username), remember=True)
            return redirect("/")
        error = "Invalid username or password."
    return render_template_string(T_LOGIN, error=error)

@app.route("/register", methods=["GET","POST"])
def register():
    error = None
    if request.method == "POST":
        username = request.form.get('username','').strip()
        password = request.form.get('password','')
        if not username or not password:
            error = "Username and password required."
        elif len(password) < 8:
            error = "Password must be at least 8 characters."
        else:
            con = sqlite3.connect(DB)
            try:
                try:
                    con.cursor().execute(
                        "INSERT INTO users (username,password) VALUES(?,?)",
                        (username, generate_password_hash(password)))
                    con.commit()
                    return redirect("/login")
                except sqlite3.IntegrityError:
                    error = "Username already taken."
            finally:
                con.close()
    return render_template_string(T_REGISTER, error=error)

@app.route("/logout")
def logout():
    logout_user()
    session.clear()
    return redirect("/login")

# ---------------------------------------------------------------------------
# Templates — mobile-optimised, touch-friendly
# ---------------------------------------------------------------------------
_CSS = """
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{background:#0a0a0a;color:#e8e8e8;font-family:'Segoe UI',system-ui,sans-serif;padding-bottom:60px}
a{color:#4af;text-decoration:none}
a:hover{color:#7cf}
.nav{background:#111;border-bottom:2px solid #f90;padding:12px 16px;display:flex;align-items:center;gap:10px;flex-wrap:wrap;position:sticky;top:0;z-index:99}
.nav-brand{color:#f90;font-weight:700;font-size:1.1rem;letter-spacing:1px;flex:1}
.nav a{color:#aaa;font-size:.85rem;padding:4px 10px;border:1px solid #333;border-radius:4px}
.nav a:hover{border-color:#f90;color:#f90}
.container{max-width:700px;margin:0 auto;padding:16px}
.card{background:#161616;border:1px solid #2a2a2a;border-radius:8px;padding:16px;margin-bottom:12px}
.card h3{color:#f90;margin-bottom:10px;font-size:1rem}
.stat{display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid #222;font-size:.95rem}
.stat:last-child{border:none}
.stat b{color:#f90}
.list-item{display:flex;align-items:center;padding:10px 12px;border-bottom:1px solid #1e1e1e;gap:8px}
.list-item:last-child{border:none}
.list-item a{flex:1;color:#4af;font-size:.95rem}
.list-item .del{color:#c44;font-size:.8rem;padding:3px 8px;border:1px solid #c44;border-radius:4px}
input,textarea{background:#1a1a1a;color:#e8e8e8;border:1px solid #333;border-radius:6px;padding:10px 12px;font-size:.95rem;width:100%;margin-bottom:10px;font-family:inherit}
input:focus,textarea:focus{border-color:#f90;outline:none}
textarea{resize:vertical;min-height:120px;font-family:monospace}
.btn{display:inline-block;padding:10px 22px;border-radius:6px;border:1px solid #f90;background:transparent;color:#f90;font-size:.95rem;cursor:pointer;font-family:inherit;text-align:center;width:100%;margin-bottom:8px}
.btn:hover{background:rgba(255,153,0,.12)}
.btn-primary{background:rgba(255,153,0,.15);font-weight:600}
.btn-danger{border-color:#c44;color:#c44}
.btn-danger:hover{background:rgba(204,68,68,.15)}
.btn-sm{width:auto;padding:5px 14px;font-size:.82rem;margin:0}
.err{color:#f66;background:rgba(255,80,80,.08);border:1px solid #c44;border-radius:6px;padding:8px 12px;margin-bottom:10px;font-size:.9rem}
.ok{color:#4f4;background:rgba(0,200,0,.08);border:1px solid #4a4;border-radius:6px;padding:8px 12px;margin-bottom:10px;font-size:.9rem}
.cp-bar{background:#161616;border:1px solid #2a2a2a;border-radius:8px;padding:10px 14px;margin-bottom:12px;font-size:.82rem;color:#888;display:flex;justify-content:space-between;flex-wrap:wrap;gap:6px}
.cp-bar span{color:#f90}
label{display:block;font-size:.82rem;color:#888;margin-bottom:4px;text-transform:uppercase;letter-spacing:.5px}
.search-row{display:flex;gap:8px;margin-bottom:16px}
.search-row input{margin:0;flex:1}
.search-row button{width:auto;padding:10px 16px;margin:0}
h2{color:#f90;margin-bottom:16px;font-size:1.1rem;letter-spacing:.5px}
.note-value{background:#111;border:1px solid #222;border-radius:6px;padding:12px;white-space:pre-wrap;font-family:monospace;font-size:.9rem;line-height:1.5;margin-bottom:12px}
.ts{font-size:.78rem;color:#555}
</style>
"""

T_HOME = _CSS + """
<div class="nav"><span class="nav-brand">&#9733; EverNothing</span>
  <a href="/search">Search</a>
  <a href="/folder/add">+ Folder</a>
  <a href="/logout">Logout</a>
</div>
<div class="container">
  <div class="cp-bar">
    <span>Last checkpoint: <span>{{last_checkpoint}}</span></span>
    {% if next_checkpoint %}<span>Next in: <span>{{next_checkpoint}}</span></span>{% endif %}
    <form method="post" action="/checkpoint" style="margin:0">
      <button class="btn btn-sm" style="padding:3px 10px;font-size:.78rem">Sync Now</button>
    </form>
  </div>
  <div class="card">
    <h3>Your Stats</h3>
    <div class="stat"><span>Notes</span><b>{{note_count}}</b></div>
    <div class="stat"><span>Folders</span><b>{{folder_count}}</b></div>
    {% if bucket %}<div class="stat"><span>S3 Bucket</span><b>{{bucket}}</b></div>{% endif %}
  </div>
  <div class="card">
    <h3>Folders</h3>
    {% for fid,fname in folders %}
    <div class="list-item"><a href="/folder/{{fid}}">&#128193; {{fname}}</a></div>
    {% else %}<p style="color:#555;padding:8px">No folders yet. <a href="/folder/add">Create one</a>.</p>
    {% endfor %}
  </div>
</div>
"""

T_FOLDER = _CSS + """
<div class="nav"><span class="nav-brand">&#128193; {{fname}}</span>
  <a href="/">Home</a>
  <a href="/note/add/{{fid}}">+ Note</a>
</div>
<div class="container">
  {% if notes %}
  <div class="card">
    <h3>Notes</h3>
    {% for nid,key,ts in notes %}
    <div class="list-item">
      <a href="/note/{{nid}}">{{key}}</a>
      <span class="ts">{{ts}}</span>
    </div>
    {% endfor %}
  </div>
  {% endif %}
  {% if subfolders %}
  <div class="card">
    <h3>Subfolders</h3>
    {% for sfid,sfname in subfolders %}
    <div class="list-item"><a href="/folder/{{sfid}}">&#128193; {{sfname}}</a></div>
    {% endfor %}
  </div>
  {% endif %}
  {% if not notes and not subfolders %}
  <p style="color:#555;padding:16px">Empty folder. <a href="/note/add/{{fid}}">Add a note</a>.</p>
  {% endif %}
</div>
"""

T_NOTE = _CSS + """
<div class="nav"><span class="nav-brand">{{key}}</span>
  <a href="/folder/{{fid}}">&#8592; Back</a>
  <a href="/note/edit/{{nid}}">Edit</a>
</div>
<div class="container">
  {% if desc %}<p style="color:#888;margin-bottom:12px;font-size:.9rem">{{desc}}</p>{% endif %}
  <div class="note-value">{{value}}</div>
  <p class="ts">Updated: {{updated}}</p>
  <form method="post" action="/note/delete/{{nid}}" style="margin-top:16px"
        onsubmit="return confirm('Delete this note?')">
    <button class="btn btn-danger btn-sm">Delete</button>
  </form>
</div>
"""

T_ADD_NOTE = _CSS + """
<div class="nav"><span class="nav-brand">New Note</span><a href="/folder/{{fid}}">Cancel</a></div>
<div class="container">
  {% if error %}<div class="err">{{error}}</div>{% endif %}
  <form method="post">
    <label>Note name</label>
    <input name="key" placeholder="e.g. WiFi Password" required autofocus>
    <label>Content</label>
    <textarea name="value" placeholder="Note content..." required></textarea>
    <label>Description (optional)</label>
    <input name="desc" placeholder="Short description">
    <button class="btn btn-primary">Save Note</button>
  </form>
</div>
"""

T_EDIT_NOTE = _CSS + """
<div class="nav"><span class="nav-brand">Edit Note</span><a href="/note/{{nid}}">Cancel</a></div>
<div class="container">
  {% if error %}<div class="err">{{error}}</div>{% endif %}
  <form method="post">
    <label>Note name</label>
    <input name="key" value="{{key}}" required>
    <label>Content</label>
    <textarea name="value" required>{{value}}</textarea>
    <label>Description</label>
    <input name="desc" value="{{desc}}">
    <button class="btn btn-primary">Save Changes</button>
  </form>
</div>
"""

T_ADD_FOLDER = _CSS + """
<div class="nav"><span class="nav-brand">New Folder</span><a href="/">Cancel</a></div>
<div class="container">
  {% if error %}<div class="err">{{error}}</div>{% endif %}
  <form method="post">
    <label>Folder name</label>
    <input name="name" placeholder="e.g. Work" required autofocus>
    <button class="btn btn-primary">Create Folder</button>
  </form>
</div>
"""

T_SEARCH = _CSS + """
<div class="nav"><span class="nav-brand">Search</span><a href="/">Home</a></div>
<div class="container">
  <form method="get" action="/search">
    <div class="search-row">
      <input name="q" value="{{q}}" placeholder="Search notes..." autofocus>
      <button class="btn btn-sm">Go</button>
    </div>
  </form>
  {% if q %}
    {% if results %}
    <div class="card">
      {% for nid,key,value,fid in results %}
      <div class="list-item">
        <a href="/note/{{nid}}">{{key}}</a>
        <span style="color:#555;font-size:.82rem">{{value[:40]}}{% if value|length > 40 %}…{% endif %}</span>
      </div>
      {% endfor %}
    </div>
    {% else %}
    <p style="color:#555;padding:16px">No results for "{{q}}".</p>
    {% endif %}
  {% endif %}
</div>
"""

T_CHECKPOINT = _CSS + """
<div class="nav"><span class="nav-brand">S3 Checkpoint</span><a href="/">Home</a></div>
<div class="container">
  {% if success %}
  <div class="ok">&#10003; Checkpoint complete at {{ts}}</div>
  <p style="color:#888;font-size:.9rem">Bucket: {{bucket}}</p>
  {% else %}
  <div class="err">&#10007; Checkpoint failed. Check AWS credentials and S3 bucket name in config.ini.</div>
  {% endif %}
  <a href="/" class="btn" style="margin-top:16px">Back</a>
</div>
"""

T_LOGIN = _CSS + """
<div class="container" style="max-width:380px;padding-top:60px">
  <h2 style="text-align:center;margin-bottom:24px">&#9733; EverNothing</h2>
  {% if error %}<div class="err">{{error}}</div>{% endif %}
  <form method="post">
    <label>Username</label>
    <input name="username" autocomplete="username" required autofocus>
    <label>Password</label>
    <input type="password" name="password" autocomplete="current-password" required>
    <button class="btn btn-primary">Login</button>
  </form>
  <p style="text-align:center;margin-top:16px;color:#555;font-size:.9rem">
    New user? <a href="/register">Register</a>
  </p>
</div>
"""

T_REGISTER = _CSS + """
<div class="container" style="max-width:380px;padding-top:60px">
  <h2 style="text-align:center;margin-bottom:24px">Create Account</h2>
  {% if error %}<div class="err">{{error}}</div>{% endif %}
  <form method="post">
    <label>Username</label>
    <input name="username" autocomplete="username" required autofocus>
    <label>Password (min 8 chars)</label>
    <input type="password" name="password" autocomplete="new-password" required>
    <button class="btn btn-primary">Register</button>
  </form>
  <p style="text-align:center;margin-top:16px;color:#555;font-size:.9rem">
    <a href="/login">Back to login</a>
  </p>
</div>
"""

# ---------------------------------------------------------------------------
# Startup
# ---------------------------------------------------------------------------
if __name__ == '__main__':
    init_db()

    # Start background S3 checkpoint thread
    if S3_BUCKET_NAME:
        t = threading.Thread(target=_checkpoint_loop, daemon=True)
        t.start()
        log.info(f"S3 checkpointing every {CHECKPOINT_INTERVAL}s to s3://{S3_BUCKET_NAME}")
    else:
        log.warning("S3_BUCKET_NAME not set — checkpointing disabled. Edit config.ini to enable.")

    log.info(f"Starting EverNothing on http://{config['HOST']}:{config['PORT']}")
    log.info("Open your browser and go to http://127.0.0.1:5000")
    app.run(host=config['HOST'], port=config['PORT'], debug=False)
