# EverNothing Android

Simplified EverNothing application for Android devices with S3 database upload capability.

## Installation on Android

### Prerequisites
1. Install **Termux** from F-Droid (https://f-droid.org/en/packages/com.termux/)
2. Open Termux

### Setup Steps

```bash
# 1. Update Termux
pkg update && pkg upgrade -y

# 2. Install Python
pkg install python -y

# 3. Install dependencies
pip install flask flask-login werkzeug boto3 cryptography

# 4. Create app directory
mkdir ~/evernothing
cd ~/evernothing

# 5. Copy files
# Copy evernothing_android.py to this directory
# Copy evernothing.db to this directory

# 6. Configure AWS credentials
# Edit config.ini with your AWS credentials

# 7. Run application
python evernothing_android.py
```

### Access Application
1. Open Chrome or any browser on your Android device
2. Navigate to: `http://127.0.0.1:5000`
3. Login with your EverNothing credentials

## Features

- **View Statistics**: See your note and folder counts
- **Upload to S3**: One-click database backup to AWS S3
- **Lightweight**: Minimal UI optimized for mobile
- **Secure**: Uses same authentication as desktop version

## Configuration

Edit `config.ini` before running:

```ini
[AWS]
S3_BUCKET_NAME = evernothing03032026
AWS_REGION = us-east-1
AWS_ACCESS_KEY_ID = your_access_key_here
AWS_SECRET_ACCESS_KEY = your_secret_key_here

[APP]
SECRET_KEY = Keystone1!
DB_FILE = evernothing.db
HOST = 0.0.0.0
PORT = 5000
```

Alternatively, set environment variables (overrides config.ini):

```bash
export S3_BUCKET_NAME="evernothing03032026"
export AWS_REGION="us-east-1"
export AWS_ACCESS_KEY_ID="your_key_here"
export AWS_SECRET_ACCESS_KEY="your_secret_here"
```

## File Structure

```
evernothing_android/
├── evernothing_android.py    # Main application
├── config_loader.py          # Configuration loader
├── config.ini                # Configuration file (edit this!)
├── requirements.txt          # Python dependencies
├── install_android.sh        # Installation script
├── build_package.sh          # Package builder (Linux/Mac)
├── build_package.bat         # Package builder (Windows)
├── README.md                 # This file
└── evernothing.db           # Database (copy from desktop)
```

## Building Deployment Package

**On Windows:**
```cmd
build_package.bat
```

**On Linux/Mac:**
```bash
bash build_package.sh
```

This creates a `.zip` or `.tar.gz` file ready for deployment.

## Troubleshooting

**Port already in use:**
```bash
pkill python
python evernothing_android.py
```

**Database not found:**
- Ensure `evernothing.db` is in the same directory as the app
- Check file permissions: `chmod 644 evernothing.db`

**AWS upload fails:**
- Verify AWS credentials are set correctly
- Check internet connection
- Ensure S3 bucket exists and you have write permissions

## Running in Background

```bash
# Start in background
nohup python evernothing_android.py > app.log 2>&1 &

# Stop background process
pkill -f evernothing_android.py
```

## Security Notes

- Keep AWS credentials secure
- Use environment variables, not hardcoded values
- Consider using AWS IAM roles with limited S3 permissions
- Database is stored unencrypted on device
