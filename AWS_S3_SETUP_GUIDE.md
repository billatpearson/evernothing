# AWS S3 Bucket Setup Guide for EverNothing

## Overview
This guide walks you through creating and configuring an AWS S3 bucket for EverNothing database backups.

---

## Prerequisites

- AWS Account (create at https://aws.amazon.com if you don't have one)
- Credit card for AWS billing (free tier available)
- Basic understanding of AWS console

---

## Step 1: Create AWS Account (If Needed)

1. Go to https://aws.amazon.com
2. Click "Create an AWS Account"
3. Follow the registration process
4. Verify your email and phone number
5. Add payment method (required even for free tier)

**Free Tier Benefits:**
- 5 GB of S3 storage
- 20,000 GET requests
- 2,000 PUT requests
- Perfect for EverNothing backups!

---

## Step 2: Log into AWS Console

1. Go to https://console.aws.amazon.com
2. Sign in with your AWS account credentials
3. You'll see the AWS Management Console dashboard

---

## Step 3: Navigate to S3

**Option A: Search Bar**
1. Click the search bar at the top
2. Type "S3"
3. Click "S3" under Services

**Option B: Services Menu**
1. Click "Services" in the top menu
2. Under "Storage", click "S3"

---

## Step 4: Create S3 Bucket

### 4.1 Start Bucket Creation
1. Click the orange "Create bucket" button
2. You'll see the "Create bucket" configuration page

### 4.2 General Configuration

**Bucket Name:**
- Enter: `evernothing03032026` (or your preferred unique name)
- Must be globally unique across all AWS accounts
- Use lowercase letters, numbers, and hyphens only
- If name is taken, try: `evernothing-yourname-2026`

**AWS Region:**
- Select: `US East (N. Virginia) us-east-1` (recommended)
- Or choose region closest to you:
  - `US West (Oregon) us-west-2`
  - `EU (Ireland) eu-west-1`
  - `Asia Pacific (Tokyo) ap-northeast-1`

### 4.3 Object Ownership
- Select: **ACLs disabled (recommended)**
- This is the default and most secure option

### 4.4 Block Public Access Settings
- **Keep all boxes CHECKED** ✅
- Block all public access (recommended for security)
- Your application will use credentials for private access

Settings should be:
- ✅ Block all public access
- ✅ Block public access to buckets and objects granted through new access control lists (ACLs)
- ✅ Block public access to buckets and objects granted through any access control lists (ACLs)
- ✅ Block public access to buckets and objects granted through new public bucket or access point policies
- ✅ Block public access to buckets and objects granted through any public bucket or access point policies

### 4.5 Bucket Versioning
- Select: **Enable** (recommended)
- This keeps multiple versions of your database backups
- Allows recovery from accidental deletions

### 4.6 Tags (Optional)
Add tags for organization:
- Key: `Application`, Value: `EverNothing`
- Key: `Environment`, Value: `Production`
- Key: `Purpose`, Value: `Database Backup`

### 4.7 Default Encryption
- Select: **Enable**
- Encryption type: **Server-side encryption with Amazon S3 managed keys (SSE-S3)**
- This is free and automatic

### 4.8 Advanced Settings
- **Object Lock**: Leave disabled (not needed)
- **Bucket Key**: Enable (reduces encryption costs)

### 4.9 Create Bucket
1. Review all settings
2. Click the orange "Create bucket" button at the bottom
3. You should see a success message: "Successfully created bucket 'evernothing03032026'"

---

## Step 5: Configure Bucket Lifecycle (Optional but Recommended)

This automatically deletes old backups to save storage costs.

1. Click on your bucket name (`evernothing03032026`)
2. Go to the "Management" tab
3. Click "Create lifecycle rule"

**Rule Configuration:**
- **Rule name**: `Delete old backups`
- **Choose rule scope**: Apply to all objects in the bucket
- **Lifecycle rule actions**: Check "Expire current versions of objects"
- **Days after object creation**: `30` (keeps last 30 days)
- Click "Create rule"

---

## Step 6: Create IAM User for Application

### 6.1 Navigate to IAM
1. Click "Services" → "Security, Identity, & Compliance" → "IAM"
2. Or search for "IAM" in the search bar

### 6.2 Create User
1. Click "Users" in the left sidebar
2. Click "Add users" button
3. **User name**: `evernothing-app`
4. **Access type**: Check "Access key - Programmatic access"
5. Click "Next: Permissions"

### 6.3 Set Permissions
1. Select "Attach existing policies directly"
2. Click "Create policy" (opens new tab)

**In the new tab:**
1. Click "JSON" tab
2. Paste this policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "EverNothingS3Access",
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:ListBucket",
        "s3:DeleteObject"
      ],
      "Resource": [
        "arn:aws:s3:::evernothing03032026",
        "arn:aws:s3:::evernothing03032026/*"
      ]
    }
  ]
}
```

3. Click "Next: Tags" (optional)
4. Click "Next: Review"
5. **Name**: `EverNothingS3Policy`
6. **Description**: `Allows EverNothing app to backup to S3`
7. Click "Create policy"

**Back to the user creation tab:**
1. Click the refresh button
2. Search for `EverNothingS3Policy`
3. Check the box next to it
4. Click "Next: Tags" (optional)
5. Click "Next: Review"
6. Click "Create user"

### 6.4 Save Credentials
**⚠️ CRITICAL: This is your only chance to see the secret key!**

1. You'll see:
   - **Access key ID**: `AKIAIOSFODNN7EXAMPLE` (example)
   - **Secret access key**: Click "Show" to reveal

2. **Download .csv file** (recommended)
3. Or copy both values to a secure location

**Example credentials (yours will be different):**
```
Access key ID: AKIAIOSFODNN7EXAMPLE
Secret access key: wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
```

---

## Step 7: Configure Application

### Option 1: Environment Variables (Recommended for Production)

**Windows (Command Prompt):**
```cmd
set AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
set AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
set AWS_REGION=us-east-1
set S3_BUCKET_NAME=evernothing03032026
```

**Windows (PowerShell):**
```powershell
$env:AWS_ACCESS_KEY_ID="AKIAIOSFODNN7EXAMPLE"
$env:AWS_SECRET_ACCESS_KEY="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
$env:AWS_REGION="us-east-1"
$env:S3_BUCKET_NAME="evernothing03032026"
```

**Linux/Mac:**
```bash
export AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
export AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
export AWS_REGION=us-east-1
export S3_BUCKET_NAME=evernothing03032026
```

### Option 2: AWS CLI Configuration (Recommended for Development)

1. Install AWS CLI:
   - Windows: Download from https://aws.amazon.com/cli/
   - Mac: `brew install awscli`
   - Linux: `sudo apt install awscli` or `sudo yum install awscli`

2. Configure credentials:
```bash
aws configure --profile billspeiser2
```

3. Enter when prompted:
   - AWS Access Key ID: `AKIAIOSFODNN7EXAMPLE`
   - AWS Secret Access Key: `wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY`
   - Default region name: `us-east-1`
   - Default output format: `json`

### Option 3: .env File (For Local Development)

1. Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

2. Edit `.env` file:
```bash
S3_BUCKET_NAME=evernothing03032026
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
AWS_PROFILE=billspeiser2
```

3. **IMPORTANT**: Ensure `.env` is in `.gitignore`!

---

## Step 8: Test S3 Connection

### Test with AWS CLI
```bash
# List buckets
aws s3 ls --profile billspeiser2

# List contents of your bucket
aws s3 ls s3://evernothing03032026/ --profile billspeiser2

# Upload test file
echo "test" > test.txt
aws s3 cp test.txt s3://evernothing03032026/test.txt --profile billspeiser2

# Download test file
aws s3 cp s3://evernothing03032026/test.txt test-download.txt --profile billspeiser2

# Delete test file
aws s3 rm s3://evernothing03032026/test.txt --profile billspeiser2
```

### Test with Python Script
```bash
python test_s3_config.py
```

### Test with Application
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
Uploading evernothing.db to s3://evernothing03032026/backups/evernothing.db.20260305_120000
Successfully uploaded to S3
  Bucket: evernothing03032026
  Region: us-east-1
  Backup: backups/evernothing.db.20260305_120000
  Latest: evernothing.db
```

---

## Step 9: Verify Backup in S3 Console

1. Go back to S3 console
2. Click on your bucket: `evernothing03032026`
3. You should see:
   - `evernothing.db` (latest version)
   - `backups/` folder with timestamped backups

---

## Troubleshooting

### Error: "Bucket name already exists"
**Solution:** Choose a different bucket name (must be globally unique)
```
evernothing-yourname-2026
evernothing-company-prod
```

### Error: "Access Denied"
**Solution:** Check IAM policy includes your bucket name
1. Go to IAM → Policies → EverNothingS3Policy
2. Verify bucket name matches in the Resource section

### Error: "Credentials not configured"
**Solution:** Set environment variables or configure AWS CLI
```bash
aws configure --profile billspeiser2
```

### Error: "Region not found"
**Solution:** Verify region code is correct
- Use `us-east-1` not `us-east-1a`
- Check available regions: https://docs.aws.amazon.com/general/latest/gr/s3.html

### Error: "Database file not found"
**Solution:** Run the application first to create the database
```bash
python evernothing.py
```

---

## Cost Estimation

### Free Tier (First 12 Months)
- **Storage**: 5 GB free
- **Requests**: 20,000 GET, 2,000 PUT per month
- **Data Transfer**: 15 GB out per month

### After Free Tier
- **Storage**: $0.023 per GB/month
- **PUT requests**: $0.005 per 1,000 requests
- **GET requests**: $0.0004 per 1,000 requests

### Example Cost for EverNothing
- Database size: 10 MB
- Daily backups: 30 per month
- Monthly storage: ~300 MB
- **Estimated cost**: $0.01 - $0.05 per month

**Essentially free for typical usage!**

---

## Security Best Practices

1. ✅ **Never commit credentials to git**
   - Add `.env` to `.gitignore`
   - Use environment variables in production

2. ✅ **Use IAM user with minimal permissions**
   - Only S3 access, not full admin
   - Specific to one bucket

3. ✅ **Enable bucket versioning**
   - Recover from accidental deletions
   - Keep backup history

4. ✅ **Enable encryption**
   - SSE-S3 is free and automatic
   - Protects data at rest

5. ✅ **Block public access**
   - Keep all public access blocks enabled
   - Use credentials for private access

6. ✅ **Rotate credentials regularly**
   - Every 90 days recommended
   - Create new key, test, delete old key

7. ✅ **Monitor usage**
   - Set up billing alerts
   - Review S3 access logs

---

## Maintenance

### Monthly Tasks
- Review S3 storage usage
- Check backup success in logs
- Verify latest backup exists

### Quarterly Tasks
- Rotate AWS credentials
- Review and update IAM policies
- Test backup restoration

### Annual Tasks
- Review lifecycle policies
- Optimize storage costs
- Update documentation

---

## Additional Resources

- **AWS S3 Documentation**: https://docs.aws.amazon.com/s3/
- **AWS Free Tier**: https://aws.amazon.com/free/
- **AWS Pricing Calculator**: https://calculator.aws/
- **IAM Best Practices**: https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html
- **S3 Security**: https://docs.aws.amazon.com/AmazonS3/latest/userguide/security-best-practices.html

---

## Quick Reference

### Bucket Details
- **Name**: `evernothing03032026`
- **Region**: `us-east-1`
- **Purpose**: Database backups
- **Encryption**: SSE-S3 enabled
- **Versioning**: Enabled
- **Public Access**: Blocked

### IAM User
- **Username**: `evernothing-app`
- **Policy**: `EverNothingS3Policy`
- **Permissions**: S3 read/write to specific bucket

### Application Configuration
```bash
S3_BUCKET_NAME=evernothing03032026
AWS_REGION=us-east-1
AWS_PROFILE=billspeiser2
```

---

## Support

If you encounter issues:
1. Check the troubleshooting section above
2. Review AWS CloudTrail logs for detailed errors
3. Consult AWS documentation
4. Contact AWS Support (if you have a support plan)

---

**Setup Complete! 🎉**

Your EverNothing application is now configured to automatically backup to AWS S3!
