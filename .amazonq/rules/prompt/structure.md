# EverNothing - Project Structure

## Directory Organization

```
evernothing/
├── .amazonq/rules/memory-bank/     # AI assistant context documentation
├── android/                         # Android/Kivy mobile app (in development)
│   └── main.py                     # Kivy-based mobile UI
├── tests/                          # Unit tests
│   └── test_evernothing.py        # Comprehensive test suite
├── User/                           # VS Code user data (IDE artifacts)
│   └── globalStorage/             # Extension storage
├── blob_storage/                   # File attachment storage
├── Backups/                        # Manual database backups
├── Cache/                          # Browser cache data
├── logs/                           # Application logs
├── evernothing.py                  # Main application (single-file Flask app)
├── evernothing_s3.py              # S3 synchronization utility
├── evernothing.db                  # SQLite database (gitignored)
├── secret.key                      # AES-256 encryption key (gitignored)
├── decrypt_db.py                   # Database decryption utility
├── test_*.py                       # Additional test files
├── TEST_REPORT.md                  # Test execution documentation
├── .env                            # Environment variables
├── .gitignore                      # Git exclusions
└── workspace.code-workspace        # VS Code workspace config
```

## Core Components

### 1. Main Application (`evernothing.py`)
**Single-file Flask application containing:**
- **Database Layer**: SQLite with 7 tables (users, notes, folders, note_history, attachments, audit_log, user_sessions)
- **Authentication**: Flask-Login integration with session management
- **Encryption**: Optional AES-256 encryption for note data
- **Routes**: 30+ endpoints for CRUD operations, admin, and utilities
- **Templates**: Embedded HTML templates as Python strings (15+ templates)
- **AWS Integration**: S3 sync function called after every database change

**Key Functions:**
- `init_db()`: Creates schema with indexes
- `encrypt(txt)` / `decrypt(txt)`: AES-256 encryption/decryption
- `sync_s3()`: Uploads database to S3 bucket
- `log_change()`: Audit logging for all modifications
- `get_breadcrumbs()`: Hierarchical folder path generation
- `format_date()`: Timestamp formatting (MM/dd/yyyy HH:MM)

### 2. S3 Synchronization (`evernothing_s3.py`)
**Standalone utility for database backup:**
- Validates AWS credentials from environment variables
- Creates S3 bucket if not exists (region-aware)
- Uploads timestamped backups (`backups/evernothing.db.YYYYMMDD_HHMMSS`)
- Maintains latest version at root (`evernothing.db`)
- Configurable via environment: `S3_BUCKET_NAME`, `AWS_REGION`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`

### 3. Android Application (`android/main.py`)
**Kivy-based mobile interface (in development):**
- `LoginScreen`: User authentication UI
- `ScreenManager`: Navigation between app screens
- Planned screens: Main, Folder, Note, Add/Edit, Admin
- Communicates with Flask backend via HTTP

### 4. Test Suite (`test_evernothing.py`)
**Comprehensive unit tests with 11 test cases:**
- Isolated test databases using `tempfile.mkstemp()`
- Mocked S3 sync to prevent real AWS calls
- Coverage: encryption, auth, CRUD, folders, admin, audit logs
- Unique usernames per test to avoid constraint violations

### 5. Database Decryption (`decrypt_db.py`)
**Utility for encrypted data retrieval:**
- Reads `secret.key` for AES-256 decryption
- Exports decrypted notes as JSON
- Generates JWT tokens for secure data transfer

## Database Schema

### Tables
1. **users**: id, username (UNIQUE), password (hashed), email, last_login
2. **folders**: id, user_id, name (encrypted), parent_id (self-referencing)
3. **notes**: id, user_id, folder_id, note_key (encrypted), note_value (encrypted), updated_at
4. **note_history**: id, note_id, user_id, note_key, note_value, folder_id, updated_at
5. **attachments**: id, note_id, user_id, filename, file_data (BLOB), file_size, uploaded_at
6. **audit_log**: id, user_id, action, entity_type, entity_id, old_values (JSON), new_values (JSON), timestamp, ip_address
7. **user_sessions**: id, user_id, session_id, login_time, logout_time, ip_address, user_agent

### Indexes
- `idx_notes_user`: notes(user_id)
- `idx_folders_user`: folders(user_id)
- `idx_attachments_note`: attachments(note_id)
- `idx_audit_user`: audit_log(user_id)
- `idx_audit_entity`: audit_log(entity_type, entity_id)

## Architectural Patterns

### 1. Single-File Monolith
- All code in one file for simplicity and portability
- Templates embedded as strings (no external template files)
- Configuration via environment variables with sensible defaults

### 2. Database-Centric Design
- SQLite as primary data store (no ORM)
- Direct SQL queries using `sqlite3` module
- Row factory for dict-like access: `con.row_factory = sqlite3.Row`

### 3. Encryption Layer
- Transparent encryption/decryption via wrapper functions
- Nonce-based AES-GCM mode (12-byte nonce + ciphertext)
- Base64 encoding for storage compatibility
- Graceful fallback for unencrypted data

### 4. Audit-First Approach
- `log_change()` called before every database modification
- Stores old/new values as JSON for diff tracking
- IP address and timestamp captured for compliance

### 5. Sync-After-Write Pattern
- `sync_s3()` invoked after every commit
- Continues on failure with console warning
- Asynchronous design (prints "S3 ASynch")

### 6. Hierarchical Data Model
- Self-referencing `parent_id` in folders table
- Recursive deletion via `delete_recursive()` function
- Breadcrumb generation via recursive `get_breadcrumbs()`

### 7. Session-Based Authentication
- Flask-Login for user session management
- Custom session tracking in `user_sessions` table
- Session ID stored in Flask session and database

### 8. Template Inheritance via String Concatenation
- `STYLE` constant prepended to all templates
- Consistent UI (black/gold/red theme) across all pages
- Footer with build date injected via `@app.context_processor`

## Component Relationships

```
┌─────────────────┐
│  Flask Routes   │ ← HTTP Requests
└────────┬────────┘
         │
         ├─→ Authentication (Flask-Login)
         ├─→ Database Layer (SQLite)
         │   ├─→ Encryption (AES-256)
         │   └─→ Audit Logging
         ├─→ S3 Sync (boto3)
         └─→ Templates (render_template_string)
```

## Data Flow

1. **User Request** → Flask Route Handler
2. **Authentication Check** → Flask-Login (@login_required)
3. **Database Query** → SQLite (with encryption if enabled)
4. **Audit Logging** → audit_log table (for modifications)
5. **Database Commit** → SQLite transaction
6. **S3 Sync** → boto3 upload (async, non-blocking)
7. **Response Rendering** → Jinja2 template (embedded string)
8. **HTTP Response** → User's browser

## Configuration Management

### Environment Variables
- `SECRET_KEY`: Flask session encryption key (default: "Keystone1!")
- `ENCRYPTION_ENABLED`: Enable AES-256 encryption (default: false)
- `S3_BUCKET_NAME`: AWS S3 bucket (default: "evernothing03032026")
- `AWS_REGION`: AWS region (default: "us-east-1")
- `AWS_ACCESS_KEY_ID`: AWS credentials (default: "TBD")
- `AWS_SECRET_ACCESS_KEY`: AWS credentials (default: "TBD")
- `ADMIN_USER`: Admin username (default: "admin")
- `ADMIN_PASS`: Admin password (default: "admin")
- `DB_FILE`: Database filename (default: "evernothing.db")

### File-Based Configuration
- `secret.key`: AES-256 encryption key (auto-generated if missing)
- `.env`: Environment variable definitions
- `workspace.code-workspace`: VS Code workspace settings
