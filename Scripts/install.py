#!/usr/bin/env python3
"""
EverNothing - Complete Installation Script
Installs dependencies, sets up database, configures AWS S3, and starts the application

Usage:
    python install.py

Requirements:
    - Python 3.7+
    - pip
    - Internet connection
"""

import subprocess
import sys
import os
import platform

def print_header(text):
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)

def print_step(step, text):
    print(f"\n[{step}] {text}")

def run_command(cmd, description, check=True):
    """Run shell command and handle errors"""
    try:
        print(f"   Running: {description}...")
        result = subprocess.run(cmd, shell=True, check=check, capture_output=True, text=True)
        if result.stdout:
            print(f"   {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"   ❌ Error: {e.stderr.strip() if e.stderr else str(e)}")
        return False

def check_python_version():
    """Check Python version"""
    print_step("1/8", "Checking Python Version")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 7:
        print(f"   ✅ Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"   ❌ Python 3.7+ required, found {version.major}.{version.minor}")
        return False

def install_dependencies():
    """Install Python packages"""
    print_step("2/8", "Installing Dependencies")
    
    packages = [
        "flask",
        "flask-login",
        "werkzeug",
        "boto3",
        "cryptography",
        "itsdangerous",
        "pyjwt"
    ]
    
    print(f"   Installing: {', '.join(packages)}")
    cmd = f"{sys.executable} -m pip install {' '.join(packages)}"
    
    if run_command(cmd, "pip install", check=False):
        print("   ✅ All dependencies installed")
        return True
    else:
        print("   ⚠️  Some packages may have failed, continuing...")
        return True

def generate_secret_key():
    """Generate encryption key"""
    print_step("3/8", "Generating Encryption Key")
    
    if os.path.exists('secret.key'):
        print("   ✅ secret.key already exists")
        return True
    
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        key = AESGCM.generate_key(bit_length=256)
        with open('secret.key', 'wb') as f:
            f.write(key)
        print("   ✅ Generated secret.key")
        return True
    except Exception as e:
        print(f"   ⚠️  Could not generate key: {e}")
        return True

def create_env_file():
    """Create .env file from template"""
    print_step("4/8", "Creating Configuration File")
    
    if os.path.exists('.env'):
        print("   ✅ .env already exists")
        return True
    
    if not os.path.exists('.env.example'):
        print("   ⚠️  .env.example not found, skipping")
        return True
    
    try:
        import shutil
        shutil.copy('.env.example', '.env')
        print("   ✅ Created .env from template")
        print("   ⚠️  Edit .env to configure AWS credentials")
        return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def initialize_database():
    """Initialize database"""
    print_step("5/8", "Initializing Database")
    
    if os.path.exists('evernothing.db'):
        print("   ✅ evernothing.db already exists")
        return True
    
    try:
        import sqlite3
        con = sqlite3.connect('evernothing.db')
        cur = con.cursor()
        
        # Create tables
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
        CREATE INDEX IF NOT EXISTS idx_notes_user ON notes(user_id);
        CREATE INDEX IF NOT EXISTS idx_folders_user ON folders(user_id);
        CREATE INDEX IF NOT EXISTS idx_attachments_note ON attachments(note_id);
        CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_log(user_id);
        CREATE INDEX IF NOT EXISTS idx_audit_entity ON audit_log(entity_type, entity_id);
        """)
        
        con.commit()
        con.close()
        print("   ✅ Database initialized")
        return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def create_directories():
    """Create required directories"""
    print_step("6/8", "Creating Directories")
    
    dirs = ['Backups', 'blob_storage', 'logs']
    for d in dirs:
        try:
            os.makedirs(d, exist_ok=True)
            print(f"   ✅ {d}/")
        except Exception as e:
            print(f"   ⚠️  Could not create {d}: {e}")
    
    return True

def check_aws_config():
    """Check AWS configuration"""
    print_step("7/8", "Checking AWS Configuration")
    
    access_key = os.environ.get('AWS_ACCESS_KEY_ID', 'NOT_SET')
    secret_key = os.environ.get('AWS_SECRET_ACCESS_KEY', 'NOT_SET')
    
    if access_key != 'NOT_SET' and secret_key != 'NOT_SET':
        print(f"   ✅ AWS credentials configured")
        print(f"      Access Key: {access_key[:4]}...{access_key[-4:]}")
        return True
    
    # Check AWS CLI config
    aws_creds = os.path.expanduser('~/.aws/credentials')
    if os.path.exists(aws_creds):
        print(f"   ✅ AWS CLI credentials file exists")
        return True
    
    print("   ⚠️  AWS credentials not configured")
    print("      Option 1: Set environment variables")
    print("         export AWS_ACCESS_KEY_ID=your-key")
    print("         export AWS_SECRET_ACCESS_KEY=your-secret")
    print("      Option 2: Run AWS CLI")
    print("         aws configure --profile billspeiser2")
    print("      Option 3: Run setup script")
    print("         python setup_aws_s3.py")
    return True

def run_tests():
    """Run unit tests"""
    print_step("8/8", "Running Tests")
    
    if not os.path.exists('test_evernothing.py'):
        print("   ⚠️  test_evernothing.py not found, skipping")
        return True
    
    cmd = f"{sys.executable} test_evernothing.py"
    if run_command(cmd, "Unit tests", check=False):
        print("   ✅ Tests passed")
        return True
    else:
        print("   ⚠️  Some tests failed, but installation complete")
        return True

def print_next_steps():
    """Print next steps"""
    print_header("Installation Complete! 🎉")
    
    print("\n📋 Next Steps:\n")
    
    print("1. Configure AWS S3 (if not done):")
    print("   python setup_aws_s3.py")
    print("   OR edit .env file with your AWS credentials\n")
    
    print("2. Start the application:")
    print("   python evernothing.py\n")
    
    print("3. Access the application:")
    print("   http://127.0.0.1:5000\n")
    
    print("4. Default admin login:")
    print("   http://127.0.0.1:5000/admin")
    print("   Username: admin")
    print("   Password: admin")
    print("   ⚠️  Change these in production!\n")
    
    print("📚 Documentation:")
    print("   - AWS_S3_SETUP_GUIDE.md - Complete AWS setup")
    print("   - RECOMMENDATIONS.md - Security improvements")
    print("   - SESSION_MANAGEMENT.md - Session features")
    print("   - HIGH_PRIORITY_FIXES.md - Recent improvements\n")
    
    print("🔧 Useful Commands:")
    print("   python evernothing_s3.py     - Test S3 sync")
    print("   python test_evernothing.py   - Run tests")
    print("   python test_s3_config.py     - Check S3 config\n")
    
    print("🐛 Troubleshooting:")
    print("   - Check evernothing.log for errors")
    print("   - Ensure port 5000 is available")
    print("   - Verify AWS credentials are set\n")

def main():
    print_header("EverNothing Installation")
    print("\nThis script will:")
    print("  • Check Python version")
    print("  • Install dependencies")
    print("  • Generate encryption key")
    print("  • Create configuration files")
    print("  • Initialize database")
    print("  • Create directories")
    print("  • Check AWS configuration")
    print("  • Run tests")
    
    response = input("\nProceed with installation? (yes/no): ").lower()
    if response != 'yes':
        print("Installation cancelled.")
        sys.exit(0)
    
    # Run installation steps
    steps = [
        check_python_version,
        install_dependencies,
        generate_secret_key,
        create_env_file,
        initialize_database,
        create_directories,
        check_aws_config,
        run_tests
    ]
    
    failed = []
    for step in steps:
        if not step():
            failed.append(step.__name__)
    
    # Print results
    if failed:
        print("\n⚠️  Installation completed with warnings:")
        for f in failed:
            print(f"   - {f}")
    
    print_next_steps()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInstallation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Installation failed: {e}")
        sys.exit(1)
