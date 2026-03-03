# EverNothing - Technology Stack

## Programming Languages

### Python 3.x
**Primary language for all components**
- Main application: Python 3.7+ (uses f-strings, type hints optional)
- No specific version pinned (compatible with 3.7-3.11+)
- Standard library modules: `sqlite3`, `datetime`, `json`, `os`, `base64`

## Core Dependencies

### Web Framework
- **Flask**: Lightweight WSGI web application framework
- **flask-login**: User session management and authentication
- **werkzeug**: WSGI utilities (password hashing via `generate_password_hash`, `check_password_hash`)
- **itsdangerous**: Secure token generation for password reset (`URLSafeTimedSerializer`)

### Database
- **sqlite3**: Built-in Python module (no external dependency)
- Database file: `evernothing.db` (SQLite 3.x format)
- No ORM - direct SQL queries

### Security & Encryption
- **cryptography**: AES-256 encryption via `AESGCM` (Galois/Counter Mode)
- **pyjwt**: JWT token generation for data export

### Cloud Integration
- **boto3**: AWS SDK for Python (S3 operations)
- Optional dependency (app runs without it, prints warning)

### Mobile (Android)
- **kivy**: Python framework for mobile apps (in development)
- Requires separate installation on Android via Termux

## Installation

### Standard Installation
```bash
pip install flask flask-login werkzeug boto3 cryptography itsdangerous pyjwt
```

### Android (Termux) Installation
```bash
# Install Termux from F-Droid
pkg install python
pip install flask flask-login werkzeug boto3 cryptography itsdangerous pyjwt
```

### Development Dependencies
```bash
# For testing
pip install unittest  # Built-in, no install needed
```

## Build System

### No Build Process Required
- Single-file application (no compilation)
- No bundling or minification
- No frontend build tools (no npm, webpack, etc.)

### Deployment
```bash
# Direct execution
python evernothing.py

# Background process (Linux/Mac)
nohup python evernothing.py &

# Background process (Windows)
start /B python evernothing.py

# Background process (Android/Termux)
nohup python evernothing.py &
```

## Development Commands

### Running the Application
```bash
# Start web server (default: http://127.0.0.1:5000)
python evernothing.py

# Access application
# Browser: http://127.0.0.1:5000
# Admin: http://127.0.0.1:5000/admin
```

### Testing
```bash
# Run all tests
python test_evernothing.py

# Run with verbose output
python test_evernothing.py -v

# Run specific test
python test_evernothing.py EvernothingTestCase.test_encryption
```

### Database Operations

#### Backup
```bash
# Manual backup
python -c "import shutil; shutil.copy('evernothing.db', 'evernothing_backup.db')"

# S3 backup
python evernothing_s3.py
```

#### Export
```bash
# CSV export
python -c "
import sqlite3, csv
c = sqlite3.connect('evernothing.db')
cur = c.cursor()
cur.execute('SELECT users.username, notes.note_key, notes.note_value FROM notes JOIN users ON users.id=notes.user_id')
with open('evernothing_export.csv', 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    w.writerow(['username', 'note_key', 'note_value'])
    w.writerows(cur.fetchall())
c.close()
"
```

#### Decryption
```bash
# Decrypt and export as JSON with JWT
python decrypt_db.py

# Or inline:
python -c "
import sqlite3, json, base64, os, jwt
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

with open('secret.key', 'rb') as f: 
    key = f.read()
aes = AESGCM(key)

def dec(t):
    try: 
        return aes.decrypt(base64.b64decode(t)[:12], base64.b64decode(t)[12:], None).decode('utf-8')
    except: 
        return t

c = sqlite3.connect('evernothing.db')
cur = c.cursor()
cur.execute('SELECT users.username, notes.note_key, notes.note_value FROM notes JOIN users ON users.id=notes.user_id')
data = [{'user': r[0], 'key': dec(r[1]), 'value': dec(r[2])} for r in cur.fetchall()]
print(json.dumps(data, indent=2))
print('JWT Token:', jwt.encode({'data': data}, key.hex(), algorithm='HS256'))
c.close()
"
```

### AWS S3 Configuration
```bash
# Set environment variables
export S3_BUCKET_NAME="evernothing03032026"
export AWS_REGION="us-east-1"
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"

# Or use AWS CLI profile
aws configure --profile billspeiser2
```

### Encryption Key Management
```bash
# Generate new key (auto-generated on first run)
python -c "
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
key = AESGCM.generate_key(bit_length=256)
with open('secret.key', 'wb') as f:
    f.write(key)
print('Key generated: secret.key')
"

# Enable encryption
export ENCRYPTION_ENABLED=true
```

## Runtime Configuration

### Flask Configuration
```python
app.secret_key = os.environ.get('SECRET_KEY', 'Keystone1!')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload
app.config['WTF_CSRF_ENABLED'] = False  # TODO: Enable in production
```

### Server Configuration
```python
# Development server (default)
app.run(host='0.0.0.0', port=5000)

# Production (use WSGI server)
# gunicorn evernothing:app
# uwsgi --http :5000 --wsgi-file evernothing.py --callable app
```

## Version Control

### Git Configuration (`.gitignore`)
```
evernothing.db      # Database file (contains user data)
*.db                # All SQLite databases
secret.key          # Encryption key (sensitive)
.env                # Environment variables (credentials)
```

## Platform Support

### Supported Platforms
- **Linux**: Full support (tested)
- **macOS**: Full support (Unix-like)
- **Windows**: Full support (tested on Windows 11)
- **Android**: Via Termux (requires manual setup)

### Browser Compatibility
- Chrome/Chromium (primary)
- Firefox
- Safari
- Edge
- Any modern browser with JavaScript enabled

## Performance Characteristics

### Database
- SQLite: Single-file, serverless, zero-configuration
- Indexes on foreign keys for query optimization
- Row-level locking (may cause "database is locked" under high concurrency)

### Encryption
- AES-256-GCM: ~1-2ms per encrypt/decrypt operation
- Nonce generation: `os.urandom(12)` (cryptographically secure)
- Base64 encoding: ~10% storage overhead

### S3 Sync
- Asynchronous (non-blocking)
- Uploads entire database file (~KB to MB range)
- Continues on failure (prints warning, doesn't crash)

## Security Considerations

### Enabled by Default
- Password hashing (Werkzeug's `generate_password_hash`)
- Session management (Flask-Login)
- Audit logging (all modifications tracked)

### Optional (Requires Configuration)
- AES-256 encryption (`ENCRYPTION_ENABLED=true`)
- CSRF protection (`WTF_CSRF_ENABLED=False` by default - TODO)
- HTTPS (requires reverse proxy like nginx)

### Credentials Management
- Admin credentials: Environment variables (`ADMIN_USER`, `ADMIN_PASS`)
- AWS credentials: Environment variables or AWS CLI profiles
- Secret key: Environment variable (`SECRET_KEY`) or default (change in production!)

## Monitoring & Logging

### Application Logs
- Console output (stdout/stderr)
- S3 sync status: "S3 ASynch" or "S3 Sync Error: {error}"
- Encryption errors: "Enc Error: {error}"

### Audit Logs
- Database table: `audit_log`
- Captured: user_id, action, entity_type, entity_id, old_values, new_values, timestamp, ip_address
- Accessible via: `/audit_report` (users), `/admin/audit_logs` (admin)

### Session Logs
- Database table: `user_sessions`
- Captured: user_id, session_id, login_time, logout_time, ip_address, user_agent

## Development Tools

### IDE Support
- VS Code workspace: `workspace.code-workspace`
- Python extension recommended
- SQLite viewer extension recommended

### Debugging
```python
# Enable Flask debug mode (development only)
app.run(debug=True, host='0.0.0.0', port=5000)
```

### Database Inspection
```bash
# SQLite CLI
sqlite3 evernothing.db

# List tables
.tables

# Schema
.schema users

# Query
SELECT * FROM users;
```
