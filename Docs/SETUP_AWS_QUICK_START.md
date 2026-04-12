# AWS S3 Automated Setup - Quick Start

## What This Script Does

Automatically sets up AWS S3 for EverNothing in one command:
- ✅ Creates S3 bucket with encryption & versioning
- ✅ Creates IAM user with minimal permissions
- ✅ Generates access keys
- ✅ Saves credentials to .env file
- ✅ Tests the configuration

## Prerequisites

1. **AWS Account** (free tier works)
2. **AWS CLI installed and configured** with admin credentials:
   ```bash
   aws configure
   ```
3. **boto3 installed**:
   ```bash
   pip install boto3
   ```

## Usage

### Step 1: Run the Script
```bash
python setup_aws_s3.py
```

### Step 2: Review Configuration
The script will show:
- Bucket name: `evernothing03032026`
- Region: `us-east-1`
- IAM user: `evernothing-app`

### Step 3: Confirm
Type `yes` when prompted

### Step 4: Wait for Completion
The script will:
1. Create S3 bucket (5 seconds)
2. Create IAM policy (2 seconds)
3. Create IAM user (2 seconds)
4. Generate access keys (1 second)
5. Save credentials (instant)
6. Test configuration (5 seconds)

**Total time: ~15 seconds**

## Output Files

After successful setup:
- ✅ `.env` - Application configuration (keep secure!)
- ✅ `aws_credentials_TIMESTAMP.txt` - Backup credentials (delete after setup)

## Verify Setup

Test S3 sync:
```bash
python evernothing_s3.py
```

Expected output:
```
==================================================
EverNothing S3 Sync
==================================================
Bucket: evernothing03032026
Region: us-east-1
Database: evernothing.db
--------------------------------------------------
Bucket evernothing03032026 exists
Uploading evernothing.db to s3://evernothing03032026/backups/...
Successfully uploaded to S3
```

## Customization

Set environment variables before running:
```bash
# Windows
set S3_BUCKET_NAME=my-custom-bucket
set AWS_REGION=us-west-2

# Linux/Mac
export S3_BUCKET_NAME=my-custom-bucket
export AWS_REGION=us-west-2

# Then run
python setup_aws_s3.py
```

## Troubleshooting

### "Access Denied"
**Cause:** AWS CLI not configured with admin credentials  
**Fix:**
```bash
aws configure
# Enter credentials with IAM permissions
```

### "Bucket name already exists"
**Cause:** Bucket name taken globally  
**Fix:**
```bash
set S3_BUCKET_NAME=evernothing-yourname-2026
python setup_aws_s3.py
```

### "User already has 2 access keys"
**Cause:** IAM user limit reached  
**Fix:**
```bash
# List keys
aws iam list-access-keys --user-name evernothing-app

# Delete old key
aws iam delete-access-key --user-name evernothing-app --access-key-id AKIAXXXXX

# Run script again
python setup_aws_s3.py
```

### "boto3 not installed"
**Fix:**
```bash
pip install boto3
```

## Security Notes

1. ✅ Script creates IAM user with **minimal permissions** (only your bucket)
2. ✅ Bucket has **public access blocked**
3. ✅ **Encryption enabled** by default
4. ✅ **Versioning enabled** for backup recovery
5. ⚠️ **Delete credentials file** after confirming setup works
6. ⚠️ **Never commit .env** to git (already in .gitignore)

## Manual Setup Alternative

If you prefer manual setup, follow:
```
AWS_S3_SETUP_GUIDE.md
```

## What Gets Created

### S3 Bucket
- Name: `evernothing03032026`
- Region: `us-east-1`
- Encryption: AES256 (SSE-S3)
- Versioning: Enabled
- Public Access: Blocked
- Lifecycle: Infinite retention (no auto-delete)

### IAM User
- Username: `evernothing-app`
- Policy: `EverNothingS3Policy`
- Permissions: S3 read/write to specific bucket only

### Cost
- **Free tier**: 5 GB storage, 20K GET, 2K PUT per month
- **After free tier**: ~$0.01-$0.05 per month for typical usage

## Cleanup (If Needed)

To remove everything:
```bash
# Delete S3 bucket
aws s3 rb s3://evernothing03032026 --force

# Detach policy from user
aws iam detach-user-policy --user-name evernothing-app --policy-arn arn:aws:iam::ACCOUNT:policy/EverNothingS3Policy

# Delete access keys
aws iam delete-access-key --user-name evernothing-app --access-key-id AKIAXXXXX

# Delete user
aws iam delete-user --user-name evernothing-app

# Delete policy
aws iam delete-policy --policy-arn arn:aws:iam::ACCOUNT:policy/EverNothingS3Policy
```

## Support

- Full manual guide: `AWS_S3_SETUP_GUIDE.md`
- Credentials guide: `AWS_CREDENTIALS_GUIDE.md`
- AWS Documentation: https://docs.aws.amazon.com/s3/

---

**Ready to go! Run `python setup_aws_s3.py` to get started.** 🚀
