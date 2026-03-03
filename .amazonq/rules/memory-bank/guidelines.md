# EverNothing - Development Guidelines

## Code Quality Standards

### 1. Code Formatting Patterns

#### Python Style
- **Indentation**: 4 spaces (no tabs)
- **Line Length**: No strict limit, but typically 80-120 characters for readability
- **String Quotes**: Double quotes for strings (`"text"`), single quotes for dict keys when convenient
- **Docstrings**: Triple-quoted strings at module/function level for documentation
- **Comments**: Inline comments for complex logic, block comments for sections

#### Naming Conventions
- **Variables**: `snake_case` (e.g., `db_path`, `user_id`, `note_key`)
- **Functions**: `snake_case` (e.g., `init_db()`, `sync_s3()`, `log_change()`)
- **Classes**: `PascalCase` (e.g., `User`, `LoginManager`, `AESGCM`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `DB`, `BUILD_DATE`, `KEY_FILE`, `STYLE`)
- **Private/Internal**: Prefix with underscore (e.g., `_transform()`, `__init__()`)

#### Import Organization
```python
# Standard library imports first
from flask import Flask, request, redirect, render_template_string
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3, datetime, json, os, base64

# Third-party imports second
try:
    import boto3
except ImportError:
    boto3 = None

# Local imports last (if any)
```

### 2. Structural Conventions

#### Single-File Architecture
- All application code in one file (`evernothing.py`)
- Templates embedded as string constants (e.g., `T_LOGIN`, `T_FOLDERS`)
- Configuration via environment variables with defaults
- No external template files or static assets

#### Database Access Pattern
```python
def db():
    con = sqlite3.connect(DB, check_same_thread=False)
    con.row_factory = sqlite3.Row  # Dict-like access
    return con

# Usage pattern:
con = db()
cur = con.cursor()
# ... queries ...
con.commit()
con.close()
```

#### Route Handler Structure
```python
@app.route("/path/<int:id>", methods=["GET", "POST"])
@login_required  # Decorator for authentication
def handler(id):
    con = db()
    cur = con.cursor()
    
    # GET logic
    if request.method == "POST":
        # POST logic
        # ... database operations ...
        con.commit()
        con.close()
        sync_s3()  # Always sync after changes
        return redirect("/")
    
    # ... fetch data ...
    con.close()
    return render_template_string(TEMPLATE, **data)
```

### 3. Textual Standards

#### Date/Time Formatting
- **Display Format**: `MM/dd/yyyy HH:MM` (e.g., "03/02/2026 14:30")
- **Storage Format**: ISO 8601 with timezone (`datetime.datetime.now(timezone.utc).isoformat()`)
- **Conversion Function**: `format_date(iso_str)` for display

#### Error Messages
- **User-Facing**: Clear, actionable messages (e.g., "Invalid username or password")
- **Console Errors**: Descriptive with context (e.g., `f"S3 Sync Error: {e}"`)
- **Validation**: Specific feedback (e.g., "Note and content cannot be empty")

#### UI Text Conventions
- **Buttons**: Imperative verbs (e.g., "Login", "Create", "Delete", "Commit")
- **Links**: Descriptive actions (e.g., "Add Note", "Change Password", "Logout")
- **Confirmations**: Question format (e.g., "Are you sure you want to delete...?")

## Practices Followed Throughout Codebase

### 1. Security Practices

#### Password Handling
```python
# Always hash passwords before storage
from werkzeug.security import generate_password_hash, check_password_hash

# Registration
password_hash = generate_password_hash(request.form['password'])

# Login verification
if check_password_hash(stored_hash, provided_password):
    # Authenticate
```

#### SQL Injection Prevention
```python
# ALWAYS use parameterized queries
cur.execute("SELECT * FROM users WHERE username=?", (username,))

# NEVER use string formatting
# BAD: cur.execute(f"SELECT * FROM users WHERE username='{username}'")
```

#### Session Management
```python
# Use Flask-Login for authentication
@login_required  # Decorator on protected routes
current_user.id  # Access authenticated user

# Track sessions in database
session['session_id'] = os.urandom(16).hex()
```

### 2. Error Handling Patterns

#### Graceful Degradation
```python
# Optional dependencies with fallback
try:
    import boto3
except ImportError:
    boto3 = None

# Check before use
if boto3:
    # Use boto3
else:
    print("Warning: boto3 not available")
```

#### Database Error Handling
```python
try:
    cur.execute("INSERT INTO users ...")
    con.commit()
except sqlite3.IntegrityError:
    # Handle duplicate username
    return render_template_string(T_REGISTER, error="Username already exists")
except Exception as e:
    print(f"Database error: {e}")
    # Rollback or cleanup
```

#### Encryption Error Handling
```python
def decrypt(txt):
    if not txt: return ""
    try:
        data = base64.b64decode(txt)
        return aesgcm.decrypt(data[:12], data[12:], None).decode('utf-8')
    except Exception:
        return txt  # Return as-is if decryption fails (backward compatibility)
```

### 3. Data Validation

#### Input Validation
```python
# Check for empty inputs
if not note_val.strip() or not content_val.strip():
    error = "Note and content cannot be empty"

# Check for duplicates
cur.execute("SELECT note_key FROM notes WHERE user_id=?", (current_user.id,))
if any(decrypt(r[0]) == note_val for r in cur.fetchall()):
    error = "Note name already exists"
```

#### Type Validation
```python
# Use type hints in function signatures (optional but recommended)
def log_change(cur, user_id: int, action: str, entity_type: str, 
               entity_id: int, old_values: dict, new_values: dict, ip_addr: str):
    # Implementation
```

### 4. Audit Logging Pattern

#### Always Log Changes
```python
# Before any UPDATE/DELETE operation
old_vals = {'username': user[1], 'last_login': user[2]}
new_vals = {'username': new_name, 'last_login': new_last_login}

log_change(cur, current_user.id, 'UPDATE', 'user', uid, 
           old_vals, new_vals, request.remote_addr)

# Then perform the operation
cur.execute("UPDATE users SET username=?, last_login=? WHERE id=?", ...)
```

#### Audit Log Structure
```python
# Store as JSON for flexibility
cur.execute(
    "INSERT INTO audit_log (user_id, action, entity_type, entity_id, "
    "old_values, new_values, timestamp, ip_address) VALUES(?,?,?,?,?,?,?,?)",
    (user_id, action, entity_type, entity_id, 
     json.dumps(old_values), json.dumps(new_values), 
     datetime.datetime.now(timezone.utc).isoformat(), ip_addr)
)
```

## Semantic Patterns Overview

### 1. Recurring Implementation Patterns

#### Encryption Wrapper Pattern
```python
# Transparent encryption/decryption
def encrypt(txt):
    if not ENCRYPTION_ENABLED or not txt: return txt if txt else ""
    try:
        nonce = os.urandom(12)
        return base64.b64encode(
            nonce + aesgcm.encrypt(nonce, txt.encode('utf-8'), None)
        ).decode('utf-8')
    except Exception as e:
        print(f"Enc Error: {e}")
        return txt

# Use everywhere data is stored
cur.execute("INSERT INTO notes ... VALUES(?,?,?,?,?)",
            (user_id, folder_id, encrypt(note_key), encrypt(note_value), timestamp))

# Use everywhere data is retrieved
note_key = decrypt(row[1])
```

#### Sync-After-Write Pattern
```python
# After every database commit
con.commit()
con.close()
sync_s3()  # Non-blocking, continues on failure
return redirect("/")
```

#### Breadcrumb Navigation Pattern
```python
def get_breadcrumbs(cur, fid, uid):
    crumbs = []
    while fid:
        f = cur.execute("SELECT id,name,parent_id FROM folders WHERE id=? AND user_id=?", 
                       (fid, uid)).fetchone()
        if not f: break
        crumbs.insert(0, (f[0], decrypt(f[1])))
        fid = f[2]
    return crumbs

# Display in template
# Home > Folder1 > Folder2 > Current
```

### 2. Common Architectural Approaches

#### Template String Pattern
```python
# Define style once, reuse everywhere
STYLE = """
<style>
body { background-color: black; color: gold; }
a { color: gold; }
a:hover { color: red; }
</style>
"""

# Concatenate with page templates
T_LOGIN = STYLE + """
<h3>Login</h3>
<form method=post>
...
</form>
"""
```

#### Context Processor Pattern
```python
# Inject variables into all templates
@app.context_processor
def inject_build_date():
    return dict(build_date=BUILD_DATE)

# Access in any template
# {{ build_date }}
```

#### Recursive Deletion Pattern
```python
def delete_recursive(cur, fid, uid):
    # Delete all subfolders first
    cur.execute("SELECT id FROM folders WHERE parent_id=? AND user_id=?", (fid, uid))
    for sub in cur.fetchall():
        delete_recursive(cur, sub[0], uid)
    
    # Then delete notes in this folder
    cur.execute("DELETE FROM notes WHERE folder_id=? AND user_id=?", (fid, uid))
    
    # Finally delete the folder itself
    cur.execute("DELETE FROM folders WHERE id=? AND user_id=?", (fid, uid))
```

### 3. Frequent Design Patterns

#### Factory Pattern (Database Connection)
```python
def db():
    con = sqlite3.connect(DB, check_same_thread=False)
    con.row_factory = sqlite3.Row
    return con

# Create new connection for each request
con = db()
```

#### Decorator Pattern (Authentication)
```python
from flask_login import login_required

@app.route("/")
@login_required  # Automatically redirects to login if not authenticated
def index():
    # Only authenticated users reach here
```

#### Strategy Pattern (Encryption)
```python
# Different encryption strategies based on configuration
if AESGCM:
    # Use AES-256 encryption
    def encrypt(txt): ...
    def decrypt(txt): ...
else:
    # No-op encryption (passthrough)
    def encrypt(t): return t
    def decrypt(t): return t
```

### 4. Proper Internal API Usage

#### Flask Route Registration
```python
# Standard route with multiple methods
@app.route("/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit(id):
    # GET: Display form
    # POST: Process form
    pass

# Redirect after POST
return redirect("/")

# Render template with data
return render_template_string(T_EDIT, note=note, folders=folders)
```

#### Flask-Login Integration
```python
# User class
class User(UserMixin):
    def __init__(self, id, username):
        self.id = id
        self.username = username

# User loader
@login_manager.user_loader
def load_user(uid):
    con = db()
    r = con.cursor().execute("SELECT id,username FROM users WHERE id=?", (uid,)).fetchone()
    con.close()
    return User(*r) if r else None

# Login user
login_user(User(user_id, username))

# Logout user
logout_user()
session.clear()
```

#### SQLite Row Factory
```python
# Enable dict-like access
con.row_factory = sqlite3.Row

# Access by column name
row = cur.execute("SELECT id, username FROM users WHERE id=?", (1,)).fetchone()
user_id = row['id']  # or row[0]
username = row['username']  # or row[1]
```

### 5. Frequently Used Code Idioms

#### Ternary Expressions
```python
# Conditional assignment
value = expr if condition else default

# Examples from codebase
t = n if n else ""
o = \"\\\\\" if b else \"/\"
result = User(*r) if r else None
```

#### List Comprehensions
```python
# Transform and filter data
folders = sorted([(r[0], decrypt(r[1])) for r in cur.fetchall()], 
                 key=lambda x: x[1].lower())

# Decrypt all results
notes = [(r[0], decrypt(r[1]), format_date(r[2])) for r in cur.fetchall()]
```

#### Context Managers (Implicit)
```python
# File operations
with open('secret.key', 'rb') as f:
    key = f.read()

# Database connections (manual close pattern used instead)
con = db()
try:
    # ... operations ...
    con.commit()
finally:
    con.close()
```

#### String Formatting
```python
# f-strings for interpolation
print(f"S3 Sync Error: {e}")
print(f"Bucket: {S3_BUCKET_NAME}")

# Format method for templates
result = "{command_finished}{prompt_started}".format(
    command_finished=f"\\x1b]633;D;{exit_code}\\x07",
    prompt_started="\\x1b]633;A\\x07"
)
```

### 6. Popular Annotations

#### Flask Route Decorators
```python
@app.route("/path")           # GET only
@app.route("/path", methods=["GET", "POST"])  # Multiple methods
@login_required               # Authentication required
@app.context_processor        # Inject template variables
```

#### Type Hints (Optional)
```python
# Function signatures
def format_date(iso_str: str) -> str:
    try:
        return datetime.datetime.fromisoformat(iso_str).strftime("%m/%d/%Y %H:%M")
    except Exception:
        return iso_str
```

## Testing Standards

### Test Structure
```python
class EvernothingTestCase(unittest.TestCase):
    def setUp(self):
        # Create isolated test database
        self.db_fd, self.db_path = tempfile.mkstemp()
        # ... initialize schema ...
        
    def tearDown(self):
        # Cleanup
        os.close(self.db_fd)
        os.unlink(self.db_path)
    
    @patch('evernothing.sync_s3')  # Mock external dependencies
    def test_feature(self, mock_sync):
        # Test implementation
```

### Test Naming
- Prefix with `test_`
- Descriptive names (e.g., `test_register_login`, `test_duplicate_user`)
- One test per feature/scenario

### Test Isolation
- Unique usernames per test (e.g., `user1`, `user2`, `user3`)
- Separate database per test run
- Mock external services (S3, email)

## Configuration Management

### Environment Variables
```python
# Always provide defaults
S3_BUCKET_NAME = os.environ.get('S3_BUCKET_NAME', 'evernothing03032026')
AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')
ENCRYPTION_ENABLED = os.environ.get('ENCRYPTION_ENABLED', 'false').lower() == 'true'

# Sensitive defaults should be obvious
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID', 'TBD')
```

### Feature Flags
```python
# Boolean flags for optional features
ENCRYPTION_ENABLED = os.environ.get('ENCRYPTION_ENABLED', 'false').lower() == 'true'

# Use throughout code
if ENCRYPTION_ENABLED:
    # Encrypt data
else:
    # Store plaintext
```

## Documentation Standards

### Module-Level Docstrings
```python
"""
EverNothing S3 Synchronization Application
Synchronizes evernothing.db to Amazon S3 bucket

Usage:
  python evernothing_s3.py

Configuration:
  Set environment variables or edit defaults below:
  - S3_BUCKET_NAME
  - AWS_REGION
"""
```

### Function Docstrings
```python
def sync_to_s3():
    """Upload evernothing.db to S3 bucket"""
    # Implementation
```

### Inline Comments
```python
# Validate configuration
if AWS_ACCESS_KEY_ID == 'TBD':
    print("ERROR: AWS credentials not configured")
    return False

# Create S3 client
s3 = boto3.client('s3', region_name=AWS_REGION, ...)
```

## Performance Considerations

### Database Indexes
```python
# Always create indexes on foreign keys
cur.execute("CREATE INDEX IF NOT EXISTS idx_notes_user ON notes(user_id)")
cur.execute("CREATE INDEX IF NOT EXISTS idx_folders_user ON folders(user_id)")
```

### Query Optimization
```python
# Fetch only needed columns
cur.execute("SELECT id, username FROM users WHERE id=?", (uid,))

# Use LIMIT for large result sets
cur.execute("SELECT ... ORDER BY updated_at DESC LIMIT 10")
```

### Connection Management
```python
# Close connections promptly
con = db()
# ... operations ...
con.close()

# Don't hold connections across redirects
con.commit()
con.close()
return redirect("/")
```

## Deployment Best Practices

### Production Checklist
1. Change `SECRET_KEY` from default
2. Set `ADMIN_USER` and `ADMIN_PASS` to secure values
3. Configure AWS credentials properly
4. Enable `ENCRYPTION_ENABLED=true`
5. Use WSGI server (gunicorn/uwsgi) instead of Flask dev server
6. Set up HTTPS with reverse proxy (nginx)
7. Enable CSRF protection (`WTF_CSRF_ENABLED=True`)
8. Regular database backups to S3

### Security Hardening
```python
# TODO items in code
app.config['WTF_CSRF_ENABLED'] = False  # TODO: Enable CSRF protection

# Use environment variables for secrets
app.secret_key = os.environ.get('SECRET_KEY', 'Keystone1!')  # Change in production!
```
