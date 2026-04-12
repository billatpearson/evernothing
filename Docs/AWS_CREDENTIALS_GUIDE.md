# AWS Credentials Configuration Guide

## Where AWS Credentials Are Stored

### Option 1: Environment Variables
```bash
# Windows (Command Prompt)
set AWS_ACCESS_KEY_ID=your-access-key-here
set AWS_SECRET_ACCESS_KEY=your-secret-key-here
set AWS_REGION=us-east-1

# Windows (PowerShell)
$env:AWS_ACCESS_KEY_ID="your-access-key-here"
$env:AWS_SECRET_ACCESS_KEY="your-secret-key-here"
$env:AWS_REGION="us-east-1"

# Linux/Mac
export AWS_ACCESS_KEY_ID=your-access-key-here
export AWS_SECRET_ACCESS_KEY=your-secret-key-here
export AWS_REGION=us-east-1
```

### Option 2: AWS CLI Configuration Files
**Location:** `~/.aws/credentials` (or `C:\Users\YourUsername\.aws\credentials` on Windows)

**Format:**
```ini
[default]
aws_access_key_id = YOUR_ACCESS_KEY
aws_secret_access_key = YOUR_SECRET_KEY

[billspeiser2]
aws_access_key_id = YOUR_ACCESS_KEY
aws_secret_access_key = YOUR_SECRET_KEY
```

**Config file:** `~/.aws/config`
```ini
[default]
region = us-east-1

[profile billspeiser2]
region = us-east-1
```

### Option 3: .env File (Application-Specific)
**Location:** `evernothing/.env`

**Format:**
```bash
# Copy from .env.example
S3_BUCKET_NAME=evernothing03032026
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your-access-key-here
AWS_SECRET_ACCESS_KEY=your-secret-key-here
AWS_PROFILE=billspeiser2
```

## How to Check if Credentials Are Configured

### Check Environment Variables (Safe)
```bash
# Windows
echo %AWS_ACCESS_KEY_ID%
echo %AWS_REGION%

# Linux/Mac
echo $AWS_ACCESS_KEY_ID
echo $AWS_REGION
```

### Check AWS CLI Configuration
```bash
# List configured profiles
aws configure list-profiles

# Show configuration (masks credentials)
aws configure list

# Test credentials (safe - doesn't show keys)
aws sts get-caller-identity
```

### Check in Python (Safe - Masked)
```python
import os

# Check if credentials are set (shows only first 4 chars)
access_key = os.environ.get('AWS_ACCESS_KEY_ID', 'NOT_SET')
if access_key != 'NOT_SET':
    print(f"AWS_ACCESS_KEY_ID: {access_key[:4]}...{access_key[-4:]}")
else:
    print("AWS_ACCESS_KEY_ID: Not configured")

# Check region
region = os.environ.get('AWS_REGION', 'NOT_SET')
print(f"AWS_REGION: {region}")

# Check if AWS config file exists
import os.path
aws_creds = os.path.expanduser('~/.aws/credentials')
print(f"AWS credentials file exists: {os.path.exists(aws_creds)}")
```

## Current Configuration Status

Run this safe check:
```bash
python -c "import os; print('Access Key:', 'SET' if os.environ.get('AWS_ACCESS_KEY_ID', 'TBD') != 'TBD' else 'NOT SET'); print('Secret Key:', 'SET' if os.environ.get('AWS_SECRET_ACCESS_KEY', 'TBD') != 'TBD' else 'NOT SET'); print('Region:', os.environ.get('AWS_REGION', 'us-east-1'))"
```

## How to Get AWS Credentials

1. **Log into AWS Console**: https://console.aws.amazon.com
2. **Navigate to IAM**: Services → IAM
3. **Create/Select User**: Users → Your username
4. **Security Credentials Tab**
5. **Create Access Key**: Click "Create access key"
6. **Download/Copy**: Save the Access Key ID and Secret Access Key

⚠️ **IMPORTANT**: Never commit credentials to git or share them publicly!

## Configure AWS CLI (Recommended)
```bash
# Interactive configuration
aws configure --profile billspeiser2

# It will prompt for:
# AWS Access Key ID: [enter your key]
# AWS Secret Access Key: [enter your secret]
# Default region name: us-east-1
# Default output format: json
```

## Test Configuration
```bash
# Test with AWS CLI
aws s3 ls --profile billspeiser2

# Test with Python script
python test_s3_config.py
```

## Security Best Practices

1. ✅ Use AWS CLI profiles instead of environment variables
2. ✅ Never commit credentials to version control
3. ✅ Add `.env` to `.gitignore`
4. ✅ Rotate credentials regularly
5. ✅ Use IAM roles when running on AWS (EC2, Lambda)
6. ✅ Set minimal required permissions (least privilege)

## Required IAM Permissions

Your AWS user needs these S3 permissions:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:ListBucket",
        "s3:CreateBucket"
      ],
      "Resource": [
        "arn:aws:s3:::evernothing03032026",
        "arn:aws:s3:::evernothing03032026/*"
      ]
    }
  ]
}
```
