# (Full single-file EverNothing application with all prompt instructions included as comments)
# ---------------------------------------------------------
"""
0. Include all prompt instructions as comment.
0.1 Document instructions for installing all packages and runtimes required.
0.2 Document instructions for accessing the web application.

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
10.1 include instructions for restart of application in comments.
10.2 include python command script for database backup in comments.
10.3 include python command for database export in comments.
10.3.1 Export file will contain user name, note key, note value as a comma separated text file in comments. 
10.4 include instructions for running as a background process in comments. 
13. Security
13.1 logout function will expire all login_required data
INSTALLATION (0.1):
 pip install flask flask-login werkzeug boto3

ACCESS (0.2):
 python evernothing.py
 http://127.0.0.1:5000

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

from flask import Flask, request, redirect, render_template_string, make_response

from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3, datetime, json
try:
    import boto3
except ImportError:
    boto3 = None

app = Flask("EverNothing")
app.secret_key = "Keystone1!"
DB = "evernothing.db"

login_manager = LoginManager(app)
login_manager.login_view = "login"

# --- DATABASE ---
def db():
    return sqlite3.connect(DB, check_same_thread=False)

def init_db():
    c = db(); cur = c.cursor()
    cur.executescript("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
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
    """);
    c.commit()

init_db()

# --- AWS SYNC ---
def sync_s3():
    print("S3 ASynch")
    if boto3:
        try:
            # Try to use the specific profile if configured, else default
            try: s3 = boto3.Session(profile_name='billspeiser2').client('s3')
            except: s3 = boto3.client('s3')
            
            s3.upload_file(DB, "evernothing011126", DB)
        except Exception as e:
            print(f"S3 Sync Error: {e}")

# --- AUTH ---
class User(UserMixin):
    def __init__(self, id, username):
        self.id = id
        self.username = username

@login_manager.user_loader
def load_user(uid):
    r = db().cursor().execute(
        "SELECT id,username FROM users WHERE id=?", (uid,)
    ).fetchone()
    return User(*r) if r else None

def format_date(iso_str):
    try:
        print( "formatting date")
        return datetime.datetime.fromisoformat(iso_str).strftime("%m/%d/%Y %H:%M")
    except:
        return iso_str 

def get_breadcrumbs(cur, fid, uid):
    crumbs = []
    while fid:
        f = cur.execute("SELECT id,name,parent_id FROM folders WHERE id=? AND user_id=?", (fid, uid)).fetchone()
        if not f: break
        crumbs.insert(0, (f[0], f[1]))
        fid = f[2]
    return crumbs

# --- ROUTES ---
@app.route("/")
@login_required
def index():
    cur = db().cursor()
    cur.execute("SELECT id,name FROM folders WHERE user_id=? AND parent_id IS NULL ORDER BY name", (current_user.id,))
    folders = cur.fetchall()
    cur.execute("SELECT id,note_key,updated_at FROM notes WHERE user_id=? ORDER BY updated_at DESC LIMIT 10", (current_user.id,))
    recent = [(r[0], r[1], format_date(r[2])) for r in cur.fetchall()]
    return render_template_string(T_FOLDERS, folders=folders, recent=recent)

@app.route("/folder/add", methods=["GET","POST"])
@login_required
def add_folder():
    if request.method == "POST":
        con = db(); cur = con.cursor()
        cur.execute(
            "INSERT INTO folders VALUES(NULL,?,?,NULL)",
            (current_user.id, request.form['name'])
        )
        con.commit()
        sync_s3()
        con.close()        
        return redirect("/")
    return render_template_string(T_ADD_FOLDER)

@app.route("/folder/<int:pid>/add_folder", methods=["GET","POST"])
@login_required
def add_subfolder(pid):
    if request.method == "POST":
        con = db(); cur = con.cursor()
        cur.execute(
            "INSERT INTO folders VALUES(NULL,?,?,?)",
            (current_user.id, request.form['name'], pid)
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
    if not f: return redirect("/")

    if request.method == "POST":
        delete_recursive(cur, fid, current_user.id)
        con.commit()
        sync_s3()
        return redirect(f"/folder/{f[1]}" if f[1] else "/")

    return render_template_string(T_DELETE_FOLDER, f=f) if f else redirect("/")

@app.route("/folder/rename/<int:fid>", methods=["GET","POST"])
@login_required
def rename_folder(fid):
    con = db(); cur = con.cursor()
    f = cur.execute("SELECT name,parent_id FROM folders WHERE id=? AND user_id=?", (fid, current_user.id)).fetchone()
    if not f: return redirect("/")
    if request.method == "POST":
        cur.execute("UPDATE folders SET name=? WHERE id=? AND user_id=?", (request.form['name'], fid, current_user.id))
        con.commit()
        sync_s3()
        return redirect(f"/folder/{fid}")
    return render_template_string(T_RENAME_FOLDER, f=f, fid=fid)

@app.route("/note/delete/<int:nid>", methods=["GET","POST"])
@login_required
def delete_note(nid):
    con = db(); cur = con.cursor()
    n = cur.execute("SELECT folder_id, note_key FROM notes WHERE id=? AND user_id=?", (nid, current_user.id)).fetchone()
    if not n: return redirect("/")
    if request.method == "POST":
        cur.execute("DELETE FROM notes WHERE id=? AND user_id=?", (nid, current_user.id))
        con.commit()
        sync_s3()
        return redirect(f"/folder/{n[0]}" if n[0] else "/")
    return render_template_string(T_DELETE_NOTE, n=n)

@app.route("/change_password", methods=["GET","POST"])
@login_required
def change_password():
    error = None
    if request.method == "POST":
        cur = db().cursor()
        r = cur.execute("SELECT password FROM users WHERE id=?", (current_user.id,)).fetchone()
        if r and check_password_hash(r[0], request.form['old_password']):
            cur.execute("UPDATE users SET password=? WHERE id=?", (generate_password_hash(request.form['new_password']), current_user.id))
            cur.connection.commit()
            sync_s3()
            return redirect("/")
        error = "Invalid old password"
    return render_template_string(T_CHANGE_PASSWORD, error=error)

@app.route("/search")
@login_required
def search():
    q = request.args.get('q','')
    cur = db().cursor()
    cur.execute("SELECT id,note_key FROM notes WHERE user_id=? AND (note_key LIKE ? OR note_value LIKE ?) ORDER BY note_key", (current_user.id, f'%{q}%', f'%{q}%'))
    return render_template_string(T_SEARCH, notes=cur.fetchall(), q=q)

@app.route("/export")
@login_required
def export_json():
    cur = db().cursor()
    cur.execute("""
        SELECT n.note_key, n.note_value, n.updated_at, f.name
        FROM notes n
        LEFT JOIN folders f ON n.folder_id = f.id
        WHERE n.user_id=?
    """, (current_user.id,))
    data = [{"note": r[0], "content": r[1], "updated_at": r[2], "folder": r[3]} for r in cur.fetchall()]
    resp = make_response(json.dumps(data, indent=2))
    resp.headers['Content-Disposition'] = 'attachment; filename=notes.json'
    resp.headers['Content-Type'] = 'application/json'
    return resp

@app.route("/folder/<int:fid>")
@login_required
def view_folder(fid):
    cur = db().cursor()
    folder = cur.execute("SELECT id,name,parent_id FROM folders WHERE id=? AND user_id=?", (fid, current_user.id)).fetchone()
    if not folder: return redirect("/")

    cur.execute("SELECT id,name FROM folders WHERE user_id=? AND parent_id=? ORDER BY name", (current_user.id, fid))
    subfolders = cur.fetchall()
    cur.execute(
        "SELECT id,note_key FROM notes WHERE user_id=? AND folder_id=? ORDER BY note_key",
        (current_user.id, fid)
    )
    return render_template_string(T_NOTES, notes=cur.fetchall(), subfolders=subfolders, folder=folder)

@app.route("/add/<int:fid>", methods=["GET","POST"])
@login_required
def add(fid):
    error = None
    note_val = ""
    content_val = ""
    if request.method == "POST":
        note_val = request.form['note']
        content_val = request.form['content']
        con = db(); cur = con.cursor()
        
        if not note_val.strip() or not content_val.strip():
            error = "Note and content cannot be empty"
        elif cur.execute("SELECT 1 FROM notes WHERE user_id=? AND note_key=?", (current_user.id, note_val)).fetchone():
            error = "Note name already exists"
        else:
            cur.execute(
                "INSERT INTO notes VALUES(NULL,?,?,?,?,?)",
                (current_user.id, fid, note_val, content_val, datetime.datetime.utcnow().isoformat())
            )
            nid = cur.lastrowid
            cur.execute(
                "INSERT INTO note_history VALUES(NULL,?,?,?,?,?,?)",
                (nid, current_user.id, note_val, content_val, fid, datetime.datetime.utcnow().isoformat())
            )
            con.commit()
            sync_s3()
            return redirect(f"/folder/{fid}")
    return render_template_string(T_ADD, fid=fid, error=error, note=note_val, content=content_val)

@app.route("/edit/<int:id>", methods=["GET","POST"])
@login_required
def edit(id):
    cur = db().cursor()
    folders = cur.execute(
        "SELECT id,name FROM folders WHERE user_id=? ORDER BY name",
        (current_user.id,)
    ).fetchall()

    cur.execute(
        "SELECT note_key,note_value,folder_id,updated_at FROM notes WHERE id=? AND user_id=?",
        (id, current_user.id),
    )
    row = cur.fetchone()
    if not row: return redirect("/")
    note = list(row)
    note[3] = format_date(note[3])

    if request.method == "POST":
        if note[0] == request.form['note'] and note[1] == request.form['content'] and str(note[2]) == str(request.form.get('folder_id')):
            return redirect("/")

        if request.form.get('confirm') == 'yes':
            now = datetime.datetime.utcnow().isoformat()
            cur.execute(
                "UPDATE notes SET note_key=?,note_value=?,folder_id=?,updated_at=? WHERE id=? AND user_id=?",
                (
                    request.form['note'],
                    request.form['content'],
                    request.form.get('folder_id'),
                    now,
                    id,
                    current_user.id,
                ),
            )
            cur.execute(
                "INSERT INTO note_history VALUES(NULL,?,?,?,?,?,?)",
                (id, current_user.id, request.form['note'], request.form['content'], request.form.get('folder_id'), now)
            )
            cur.connection.commit()
            sync_s3()
            return redirect("/")
        else:
            return render_template_string(T_EDIT_CONFIRM, note=[request.form['note'], request.form['content'], request.form.get('folder_id')], id=id)

    breadcrumbs = get_breadcrumbs(cur, note[2], current_user.id)
    return render_template_string(T_EDIT, note=note, folders=folders, breadcrumbs=breadcrumbs, id=id)

@app.route("/history/<int:nid>")
@login_required
def history(nid):
    cur = db().cursor()
    cur.execute("SELECT id,note_key,updated_at FROM note_history WHERE note_id=? AND user_id=? ORDER BY updated_at DESC", (nid, current_user.id))
    history = [(h[0], h[1], format_date(h[2])) for h in cur.fetchall()]
    return render_template_string(T_HISTORY, history=history, nid=nid)

@app.route("/history/restore/<int:hid>")
@login_required
def restore_history(hid):
    con = db(); cur = con.cursor()
    h = cur.execute("SELECT note_id,note_key,note_value,folder_id FROM note_history WHERE id=? AND user_id=?", (hid, current_user.id)).fetchone()
    if h:
        now = datetime.datetime.utcnow().isoformat()
        cur.execute(
            "UPDATE notes SET note_key=?,note_value=?,folder_id=?,updated_at=? WHERE id=? AND user_id=?",
            (h[1], h[2], h[3], now, h[0], current_user.id)
        )
        cur.execute(
            "INSERT INTO note_history VALUES(NULL,?,?,?,?,?,?)",
            (h[0], current_user.id, h[1], h[2], h[3], now)
        )
        con.commit()
        sync_s3()
        return redirect(f"/edit/{h[0]}")
    return redirect("/")

# --- LOGIN ---
@app.route("/login", methods=["GET","POST"])
def login():
    cur = db().cursor()
    error = None
    if request.method == "POST":
        print("username",request.form['username'])
        r = cur.execute(
            "SELECT id,password FROM users WHERE username=?",
            (request.form['username'],)
        ).fetchone()
        if r and check_password_hash(r[1], request.form['password']):
            login_user(User(r[0], request.form['username']))
            return redirect("/")
        error = "Invalid username or password"
    return render_template_string(T_LOGIN, error=error)

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        print("register",request.form['username'])
        print("pass", generate_password_hash(request.form['password']))
        con = db()
        cursor=con.cursor()
        cursor.execute(
            "INSERT INTO users VALUES(NULL,?,?)",
            (request.form['username'], generate_password_hash(request.form['password']))
        )
        con.commit()
        sync_s3()
        con.close()
        return redirect("/login")
    return render_template_string(T_REGISTER)

@app.route("/logout")
def logout():
    logout_user(); return redirect("/login")

# --- TEMPLATES ---
STYLE = """
<style>
body { background-color: black; color: gold; font-family: sans-serif; }
a { color: gold; text-decoration: none; }
a:hover { color: red; text-decoration: underline; }
input, textarea, select, button { background-color: #111; color: gold; border: 1px solid red; margin: 2px; }
.cancel { border: 1px solid red; }
</style>
"""

T_FOLDERS = STYLE + """
<h3>EverNothing - Folders</h3>
<form action="/search" method="get">
<input name="q" placeholder="Search..."> <button>Go</button>
</form>
<a href=/folder/add>Create Folder</a> | <a href=/export>Export JSON</a> | <a href=/change_password>Change Password</a> | <a href=/logout>Logout</a>
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
<form method=post>
<b>Folder name:</b> <input name=name><br>
<button>Create</button> <a href=/ class=cancel>Cancel</a>
</form>
"""

T_ADD_SUBFOLDER = STYLE + """
<form method=post>
<b>Subfolder name:</b> <input name=name><br>
<button>Create</button> <a href=/folder/{{pid}} class=cancel>Cancel</a>
</form>
"""

T_RENAME_FOLDER = STYLE + """
<form method=post>
<button>Rename</button> <a href=/folder/{{fid}} class=cancel>Cancel</a>
</form>
"""

T_CHANGE_PASSWORD = STYLE + """
<h3>Change Password</h3>
{% if error %}<p style="color:red">{{error}}</p>{% endif %}
<form method=post>
<b>Old Password:</b> <input type=password name=old_password><br>
<b>New Password:</b> <input type=password name=new_password><br>
<button>Change</button> <a href=/ class=cancel>Cancel</a>
</form>
"""

T_DELETE_NOTE = STYLE + """
<h3>Delete Note</h3>
<p>Are you sure you want to delete note <b>{{n[1]}}</b>?</p>
<form method=post><button>Yes, Delete</button> <a href=javascript:history.back() class=cancel>Cancel</a></form>
"""

T_EDIT_CONFIRM = STYLE + """
<h3>Confirm Changes</h3>
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
{% if error %}<p style="color:red">{{error}}</p>{% endif %}
<form method=post>
<b>Note:</b> <input name=note value="{{note}}"><br>
<b>Contents:</b> <textarea name=content rows=40 cols=120>{{content}}</textarea><br>
<button>Add</button> <a href=/folder/{{fid}} class=cancel>Cancel</a>
</form>
"""

T_EDIT = STYLE + """
<a href=/>Home</a>
{% for b in breadcrumbs %}
 &gt; <a href=/folder/{{b[0]}}>{{b[1]}}</a>
{% endfor %}
 | <a href=/history/{{id}}>Edited: {{note[3]}}</a> | <a href=/note/delete/{{id}} style="color:red">[Delete]</a> | <a href=/logout>Logout</a>
<form method=post>
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
"""

T_LOGIN = STYLE + """
<h3>Login</h3>
{% if error %}<p style="color:red">{{error}}</p>{% endif %}
<form method=post>
<input name=username placeholder='Username'><br>
<input type=password name=password placeholder='Password'><br>
<button>Login</button> <a href=/register>Register</a>
</form>
"""

T_REGISTER = STYLE + """
<form method=post>
<input name=username placeholder='Username'><br>
<input type=password name=password placeholder='Password'><br>
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
