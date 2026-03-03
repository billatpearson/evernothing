# EverNothing - Product Overview

## Purpose
EverNothing is a secure, hierarchical note-taking web application designed for personal knowledge management with enterprise-grade features including encryption, audit logging, and cloud synchronization.

## Value Proposition
- **Cross-Platform Access**: Web-based application accessible from desktop browsers and Android devices (via Termux)
- **Security First**: AES-256 encryption for sensitive data, comprehensive audit logging, and user session tracking
- **Cloud Backup**: Automatic synchronization to AWS S3 with versioned backups
- **Complete History**: Full change tracking with rollback capabilities for all notes
- **Multi-User Support**: Per-user data isolation with admin management capabilities

## Key Features

### Core Note Management
- Hierarchical folder/subfolder organization with unlimited nesting
- Key-value pair note storage with full-text search on both keys and values
- Rich text content support with multi-line text areas (120 columns × 40 rows)
- File attachments (up to 16MB) with upload/download/delete capabilities
- Alphabetical sorting of all lists and selects

### Security & Compliance
- Username/password authentication with secure password hashing (Werkzeug)
- Optional AES-256 encryption for note keys and values
- Comprehensive audit logging (user actions, timestamps, IP addresses, old/new values)
- Session management with login/logout tracking
- Password reset functionality via email tokens

### Change Management
- Complete note history with timestamps (MM/dd/yyyy HH:MM format)
- Rollback to any previous version
- Confirmation dialogs for destructive operations
- Audit trail for all CREATE/UPDATE/DELETE operations

### Administration
- Dedicated admin portal at `/admin`
- User management (search, edit username/password, view last login)
- User deletion with cascade (removes all associated notes/folders)
- Audit log viewer with filtering (user, action, entity type, limit)
- User statistics (note count, folder count, last access date)

### AWS Integration
- Automatic S3 synchronization after every database change
- Timestamped backups (format: `backups/evernothing.db.YYYYMMDD_HHMMSS`)
- Latest version always available at root (`evernothing.db`)
- Configurable bucket name and region via environment variables

### Data Export
- JSON export of all user notes with metadata
- CSV export capability (username, note_key, note_value)
- Decryption utilities for encrypted data retrieval

## Target Users

### Primary Users
- **Knowledge Workers**: Individuals managing personal notes, research, and documentation
- **Developers**: Technical users comfortable with command-line deployment and configuration
- **Privacy-Conscious Users**: Those requiring encryption and self-hosted solutions

### Secondary Users
- **System Administrators**: Managing multi-user deployments with admin tools
- **Mobile Users**: Android users accessing via Termux for on-the-go note access

## Use Cases

1. **Personal Knowledge Base**: Organize notes hierarchically by topic/project with full-text search
2. **Secure Documentation**: Store sensitive information with encryption and audit trails
3. **Collaborative Note-Taking**: Multi-user environment with per-user isolation
4. **Version Control for Notes**: Track changes over time with rollback capabilities
5. **Cross-Device Synchronization**: Access notes from multiple devices via S3 sync
6. **Compliance Tracking**: Audit logs for regulatory requirements (who changed what, when)

## Technical Highlights
- **Single-File Application**: Entire web app in one Python file (~1500 lines)
- **Embedded Templates**: HTML templates included as strings (no external files)
- **Minimal Dependencies**: Flask, SQLite, boto3, cryptography, werkzeug
- **Zero Configuration**: Works out-of-box with sensible defaults
- **Build Date Footer**: All pages display build timestamp (MM/DD/YY:HH:MM)

## UI/UX Design
- **Color Scheme**: Black background, gold text, red accents for links/borders
- **Responsive Forms**: 2px horizontal spacing for inputs
- **Breadcrumb Navigation**: Hierarchical path display on note edit pages
- **Recently Edited**: Dashboard shows last 10 edited notes with timestamps
- **Confirmation Dialogs**: Prevents accidental data loss on edits/deletes
