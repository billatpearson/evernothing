"""evernothing_templates.py — User Experience
STYLE constant and all T_* HTML template strings.
"""
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
th { text-align: left; padding: 10px 12px; border: 1px solid var(--red); color: var(--gold-dim); font-size: .8rem; text-transform: uppercase; letter-spacing: .5px; }
td { padding: 3px 12px; vertical-align: top; }
tr { border: 1px solid #cc2200; }
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
<div class="footer">built on {{ build_date }}</div>
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


T_ADMIN_S3_BACKUPS = STYLE + """
<nav class="nav">
  <span class="nav-brand">&#9670; Admin</span>
  <a href=/admin/dashboard>&#8592; Dashboard</a>
  <a href=/logout class="nav-logout">Logout</a>
</nav>
<div class="container">
  <h3>S3 Backups</h3>
  {% if message %}<p style="color:#0c0;">{{message}}</p>{% endif %}
  {% if error %}<err>{{error}}</err>{% endif %}
  {% if confirm_key %}
  <div class="confirm-box">
    <p>Restore backup <b>{{confirm_key}}</b> to local file?</p>
    <form method=post action="/admin/s3_restore/{{confirm_key}}">
      <input type=hidden name=csrf_token value="{{ csrf_token() }}">
      <div class="btn-group">
        <button class="btn btn-primary">Yes, Restore</button>
        <a href=/admin/s3_backups class="btn">Cancel</a>
      </div>
    </form>
  </div>
  {% else %}
  <table>
    <tr><th>Backup File</th><th>Size</th><th>Last Modified</th><th>Action</th></tr>
    {% for backup in backups %}
    <tr>
      <td style="font-size:.8rem">{{backup.key}}</td>
      <td>{{backup.size}}</td>
      <td class="timestamp">{{backup.modified}}</td>
      <td><a href="/admin/s3_restore/{{backup.key}}" style="color:#0c0">[Restore]</a></td>
    </tr>
    {% else %}
    <tr><td colspan="4" class="empty">No backups found or S3 not configured.</td></tr>
    {% endfor %}
  </table>
  {% endif %}
</div>
"""
