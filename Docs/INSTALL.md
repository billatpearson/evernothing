# EverNothing - Installation Guide

Complete installation instructions for EverNothing application.

---

## Quick Install (Automated)

```bash
python install.py
```

This script automatically:
- ✅ Checks Python version
- ✅ Installs all dependencies
- ✅ Generates encryption key
- ✅ Creates configuration files
- ✅ Initializes database
- ✅ Creates directories
- ✅ Runs tests

**Time:** ~2 minutes

---

## Manual Installation

### Prerequisites

- Python 3.7 or higher
- pip (Python package manager)
- Internet connection

### Step 1: Install Dependencies

```bash
pip install flask flask-login werkzeug boto3 cryptography itsdangerous pyjwt
```

### Step 2: Generate Encryption Key

```bash
python -c "from cryptography.hazmat.primitives.ciphers.aead import AESGCM; import os; key=AESGCM.generate_key(bit_length=256); open('secret.key','wb').write(key); print('Key generated')"
```

### Step 3: Create Configuration

```bash
cp .env.example .env
```

Edit `.env` with your settings (optional for basic usage).

### Step 4: Initialize Database

```bash
python evernothing.py
# Press Ctrl+C after it starts
```

The database will be created automatically on first run.

### Step 5: Start Application

```bash
python evernothing.py
```

Access at: http://127.0.0.1:5000

---

## AWS S3 Setup (Optional)

For automatic cloud backups:

### Option 1: Automated Setup

```bash
python setup_aws_s3.py
```

Requires AWS CLI configured with admin credentials.

### Option 2: Manual Setup

1. Create S3 bucket in AWS Console
2. Create IAM user with S3 permissions
3. Configure credentials:

```bash
# Environment variables
export AWS_ACCESS_KEY_ID=your-key
export AWS_SECRET_ACCESS_KEY=your-secret
export S3_BUCKET_NAME=evernothing-backup-2026
export AWS_REGION=us-east-1

# OR use AWS CLI
aws configure --profile billspeiser2
```

See `AWS_S3_SETUP_GUIDE.md` for detailed instructions.

---

## Platform-Specific Instructions

### Windows

```cmd
# Install
python install.py

# Start application
python evernothing.py

# Background process
start /B python evernothing.py
```

### Linux/Mac

```bash
# Install
python3 install.py

# Start application
python3 evernothing.py

# Background process
nohup python3 evernothing.py &
```

### Android (Termux)

```bash
# Install Termux from F-Droid
pkg install python
pip install flask flask-login werkzeug boto3 cryptography itsdangerous pyjwt

# Run application
python evernothing.py

# Access in browser
# http://127.0.0.1:5000
```

---

## Configuration

### Environment Variables

Edit `.env` file or set environment variables:

```bash
# Application
SECRET_KEY=change-this-in-production
ENCRYPTION_ENABLED=false
ADMIN_USER=admin
ADMIN_PASS=admin

# Session
SESSION_TIMEOUT_HOURS=2
REMEMBER_COOKIE_DAYS=30
SESSION_COOKIE_SECURE=false

# AWS S3
S3_BUCKET_NAME=evernothing-backup-2026
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
AWS_PROFILE=billspeiser2

# Database
DB_FILE=evernothing.db
```

### Production Settings

For production deployment:

1. Change `SECRET_KEY` to random value
2. Change `ADMIN_USER` and `ADMIN_PASS`
3. Set `ENCRYPTION_ENABLED=true`
4. Set `SESSION_COOKIE_SECURE=true` (requires HTTPS)
5. Use strong passwords (8+ chars, uppercase, lowercase, number)

---

## Verification

### Test Installation

```bash
python test_evernothing.py -v
```

Expected: All 11 tests pass

### Test S3 Configuration

```bash
python test_s3_config.py
```

### Test S3 Sync

```bash
python evernothing_s3.py
```

---

## Access Points

### User Interface
- **URL:** http://127.0.0.1:5000
- **Register:** Create new account
- **Login:** Use your credentials

### Admin Interface
- **URL:** http://127.0.0.1:5000/admin
- **Default:** admin/admin (change in production!)

---

## Directory Structure

After installation:

```
evernothing/
├── evernothing.py          # Main application
├── evernothing.db          # SQLite database
├── secret.key              # Encryption key
├── .env                    # Configuration
├── evernothing.log         # Application logs
├── Backups/                # Database backups
├── blob_storage/           # File attachments
└── logs/                   # Additional logs
```

---

## Troubleshooting

### Port Already in Use

```bash
# Windows
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# Linux/Mac
lsof -i :5000
kill -9 <PID>
```

### Dependencies Failed to Install

```bash
# Upgrade pip
python -m pip install --upgrade pip

# Install individually
pip install flask
pip install flask-login
pip install werkzeug
pip install boto3
pip install cryptography
pip install itsdangerous
pip install pyjwt
```

### Database Locked

```bash
# Close all connections
# Delete evernothing.db
# Restart application (will recreate)
```

### AWS Credentials Not Working

```bash
# Test credentials
aws sts get-caller-identity --profile billspeiser2

# Reconfigure
aws configure --profile billspeiser2
```

### Permission Denied

```bash
# Windows: Run as Administrator
# Linux/Mac: Use sudo or fix permissions
chmod +x install.py
```

---

## Upgrading

### From Previous Version

```bash
# Backup database
cp evernothing.db evernothing.db.backup

# Pull latest code
git pull

# Install new dependencies
pip install -r requirements.txt

# Restart application
python evernothing.py
```

---

## Uninstallation

### Remove Application

```bash
# Stop application (Ctrl+C)

# Remove files
rm -rf evernothing/

# Remove AWS resources (optional)
python cleanup_aws.py
```

### Keep Data

To keep your data but remove the application:

```bash
# Backup database
cp evernothing.db ~/evernothing_backup.db

# Remove application
rm -rf evernothing/
```

---

## Additional Resources

- **AWS Setup:** `AWS_S3_SETUP_GUIDE.md`
- **Security:** `RECOMMENDATIONS.md`
- **Session Management:** `SESSION_MANAGEMENT.md`
- **High Priority Fixes:** `HIGH_PRIORITY_FIXES.md`
- **Test Results:** `TEST_RESULTS.md`

---

## Support

### Common Issues

1. **Import errors:** Install missing dependencies
2. **Port conflicts:** Change port or kill process
3. **AWS errors:** Check credentials and permissions
4. **Database errors:** Check file permissions

### Getting Help

1. Check `evernothing.log` for errors
2. Review documentation files
3. Run tests: `python test_evernothing.py`
4. Check AWS configuration: `python test_s3_config.py`

---

## Quick Reference

### Start Application
```bash
python evernothing.py
```

### Stop Application
```
Ctrl+C
```

### Run Tests
```bash
python test_evernothing.py
```

### Backup Database
```bash
cp evernothing.db backup_$(date +%Y%m%d).db
```

### Sync to S3
```bash
python evernothing_s3.py
```

---

**Installation complete! Start with: `python evernothing.py`** 🚀
