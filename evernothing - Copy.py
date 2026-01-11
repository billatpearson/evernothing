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
3.3 Requires username and password login
3.3.0 If login fails display error message
3.3.1 After login user is redirected to a list of folders
3.3.2 If the user has zero folder the user will be able to create one.
3.4 Users see recently edited notes
3.5 Per-user data isolation
3.6 Display matching key or value
3.6.1 Edit page with commit / cancel / choose folder select control
3.7 Link to add note
3.7.1 Note = single-line, Contents = multiline
3.7.2 Add or cancel
3.8 Subfolders
3.8.1 Create subfolder
3.8.1.1 Nest notes in subfolder
3.8.1.2 List contents
3.8.1.3 Delete with warning

INSTALLATION (0.1):
 pip install flask flask-login werkzeug

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
    """);
    c.commit()

init_db()

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

# --- ROUTES ---
@app.route("/")
@login_required
def index():
    cur = db().cursor()
    cur.execute("SELECT id,name FROM folders WHERE user_id=? AND parent_id IS NULL", (current_user.id,))
    folders = cur.fetchall()
    cur.execute("SELECT id,note_key FROM notes WHERE user_id=? ORDER BY updated_at DESC LIMIT 10", (current_user.id,))
    recent = cur.fetchall()
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
        cur.execute("DELETE FROM notes WHERE folder_id=? AND user_id=?", (fid, current_user.id))
        cur.execute("DELETE FROM folders WHERE id=? AND user_id=?", (fid, current_user.id))
        delete_recursive(cur, fid, current_user.id)
        con.commit()
        return redirect("/")
    f = cur.execute("SELECT name FROM folders WHERE id=? AND user_id=?", (fid, current_user.id)).fetchone()
        return redirect(f"/folder/{f[1]}" if f[1] else "/")

    return render_template_string(T_DELETE_FOLDER, f=f) if f else redirect("/")

@app.route("/search")
@login_required
def search():
    q = request.args.get('q','')
    cur = db().cursor()
    cur.execute("SELECT id,note_key FROM notes WHERE user_id=? AND (note_key LIKE ? OR note_value LIKE ?)", (current_user.id, f'%{q}%', f'%{q}%'))
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

    cur.execute("SELECT id,name FROM folders WHERE user_id=? AND parent_id=?", (current_user.id, fid))
    subfolders = cur.fetchall()

    cur.execute(
        "SELECT id,note_key FROM notes WHERE user_id=? AND folder_id=? ORDER BY updated_at DESC",
        (current_user.id, fid)
    )
    return render_template_string(T_NOTES, notes=cur.fetchall(), fid=fid)
    return render_template_string(T_NOTES, notes=cur.fetchall(), subfolders=subfolders, folder=folder)

@app.route("/add/<int:fid>", methods=["GET","POST"])
@login_required
def add(fid):
    if request.method == "POST":
        con = db(); cur = con.cursor()
        cur.execute(
            "INSERT INTO notes VALUES(NULL,?,?,?,?,?)",
            (current_user.id, fid, request.form['note'], request.form['content'], datetime.datetime.utcnow().isoformat())
        )
        con.commit()
        return redirect(f"/folder/{fid}")
    return render_template_string(T_ADD, fid=fid)

@app.route("/edit/<int:id>", methods=["GET","POST"])
@login_required
def edit(id):
    cur = db().cursor()
    folders = cur.execute(
        "SELECT id,name FROM folders WHERE user_id=?",
        (current_user.id,)
    ).fetchall()

    if request.method == "POST":
        cur.execute(
            "UPDATE notes SET note_key=?,note_value=?,folder_id=?,updated_at=? WHERE id=? AND user_id=?",
            (
                request.form['note'],
                request.form['content'],
                request.form.get('folder_id'),
                datetime.datetime.utcnow().isoformat(),
                id,
                current_user.id,
            ),
        )
        cur.connection.commit()
        return redirect("/")

    cur.execute(
        "SELECT note_key,note_value,folder_id FROM notes WHERE id=? AND user_id=?",
        (id, current_user.id),
    )
    note = cur.fetchone()
    return render_template_string(T_EDIT, note=note, folders=folders)

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
        con.close()
        return redirect("/login")
    return render_template_string(T_REGISTER)

@app.route("/logout")
def logout():
    logout_user(); return redirect("/login")

# --- TEMPLATES ---
T_FOLDERS = """
<h3>EverNothing - Folders</h3>
<form action="/search" method="get">
<input name="q" placeholder="Search..."> <button>Go</button>
</form>
<a href=/folder/add>Create Folder</a> | <a href=/export>Export JSON</a> | <a href=/logout>Logout</a>
<ul>
{% for f in folders %}
<li><a href=/folder/{{f[0]}}>{{f[1]}}</a> <a href=/folder/delete/{{f[0]}} style="color:red;font-size:small">[x]</a></li>
{% else %}
<li>No folders. <a href=/folder/add>Create one</a></li>
{% endfor %}
</ul>
<h4>Recently Edited</h4>
<ul>
{% for n in recent %}
<li><a href=/edit/{{n[0]}}>{{n[1]}}</a></li>
{% endfor %}
</ul>
"""

T_ADD_FOLDER = """
<form method=post>
Folder name:<br><input name=name><br>
<button>Create</button> <a href=/>Cancel</a>
</form>
"""

T_ADD_SUBFOLDER = """
<form method=post>
Subfolder name:<br><input name=name><br>
<button>Create</button> <a href=/folder/{{pid}}>Cancel</a>
</form>
"""

T_NOTES = """
<a href=/>Back to folders</a>
<h3>Folder: {{folder[1]}}</h3>
<a href={% if folder[2] %}/folder/{{folder[2]}}{% else %}/{% endif %}>Back</a>
| <a href=/folder/delete/{{folder[0]}} style="color:red;font-size:small">[Delete Folder]</a>

<h4>Subfolders</h4>
<ul>
{% for s in subfolders %}
<li><a href=/folder/{{s[0]}}>{{s[1]}}</a></li>
{% else %}
<li>No subfolders.</li>
{% endfor %}
</ul>
<a href=/folder/{{folder[0]}}/add_folder>Create Subfolder</a>

<h4>Notes</h4>
<ul>
{% for n in notes %}
<li><a href=/edit/{{n[0]}}>{{n[1]}}</a></li>
{% else %}
<li>No notes.</li>
{% endfor %}
</ul>
<a href=/add/{{fid}}>Add Note</a>
<a href=/add/{{folder[0]}}>Add Note</a>
"""

T_ADD = """
<form method=post>
Note:<br><input name=note><br>
Contents:<br><textarea name=content></textarea><br>
<button>Add</button> <a href=/folder/{{fid}}>Cancel</a>
</form>
"""

T_EDIT = """
<form method=post>
Note:<br>
<input name=note value='{{note[0]}}'><br>

Contents:<br>
<textarea name=content>{{note[1]}}</textarea><br>

Folder:<br>
<select name=folder_id>
{% for f in folders %}
<option value='{{f[0]}}' {% if f[0]==note[2] %}selected{% endif %}>{{f[1]}}</option>
{% endfor %}
</select><br><br>

<button>Commit</button> <a href=/>Cancel</a>
</form>
"""

T_LOGIN = """
<h3>Login</h3>
{% if error %}<p style="color:red">{{error}}</p>{% endif %}
<form method=post>
<input name=username placeholder='Username'><br>
<input type=password name=password placeholder='Password'><br>
<button>Login</button> <a href=/register>Register</a>
</form>
"""

T_REGISTER = """
<form method=post>
<input name=username placeholder='Username'><br>
<input type=password name=password placeholder='Password'><br>
<button>Create</button>
</form>
"""

T_SEARCH = """
<h3>Search: {{q}}</h3>
<a href=/>Back</a>
<ul>
{% for n in notes %}
<li><a href=/edit/{{n[0]}}>{{n[1]}}</a></li>
{% else %}
<li>No matches.</li>
{% endfor %}
</ul>
"""

T_DELETE_FOLDER = """
<h3>Delete Folder</h3>
<p>Are you sure you want to delete folder <b>{{f[0]}}</b> and all its notes?</p>
<form method=post><button>Yes, Delete</button> <a href=/>Cancel</a></form>
<form method=post><button>Yes, Delete</button> <a href=javascript:history.back()>Cancel</a></form>
"""

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
