# AWS Configuration Guide

## Overview
AWS parameters have been externalized to support flexible configuration across different environments.

## Configuration Methods

### Method 1: Using aws_config.py (Recommended)
The `aws_config.py` module centralizes all AWS parameters. It reads from environment variables with sensible defaults.

**Default values:**
- `S3_BUCKET_NAME`: evernothing03032026
- `AWS_REGION`: us-east-1
- `AWS_PROFILE`: billspeiser2
- `DB_FILE`: evernothing.db

### Method 2: Environment Variables
Set environment variables before running the application:

**Windows:**
```cmd
set S3_BUCKET_NAME=your-bucket-name
set AWS_REGION=us-west-2
set AWS_ACCESS_KEY_ID=your-access-key
set AWS_SECRET_ACCESS_KEY=your-secret-key
python evernothing.py
```

**Linux/Mac:**
```bash
export S3_BUCKET_NAME=your-bucket-name
export AWS_REGION=us-west-2
export AWS_ACCESS_KEY_ID=your-access-key
export AWS_SECRET_ACCESS_KEY=your-secret-key
python evernothing.py
```

### Method 3: .env File
1. Copy `.env.example` to `.env`
2. Edit `.env` with your values
3. Use a library like `python-dotenv` to load variables:

```bash
pip install python-dotenv
```

Add to your code:
```python
from dotenv import load_dotenv
load_dotenv()
```

### Method 4: AWS CLI Profile
Use existing AWS CLI profiles:

```bash
export AWS_PROFILE=your-profile-name
python evernothing.py
```

## Configuration Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `S3_BUCKET_NAME` | S3 bucket for database backups | evernothing03032026 |
| `AWS_REGION` | AWS region for S3 bucket | us-east-1 |
| `AWS_ACCESS_KEY_ID` | AWS access key | TBD |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key | TBD |
| `AWS_PROFILE` | AWS CLI profile name | billspeiser2 |
| `DB_FILE` | Database filename | evernothing.db |

## Security Best Practices

1. **Never commit credentials** to version control
2. **Use IAM roles** when running on AWS (EC2, Lambda, etc.)
3. **Use AWS profiles** for local development
4. **Rotate credentials** regularly
5. **Use least privilege** IAM policies

## Testing Configuration

Test S3 sync with:
```bash
python evernothing_s3.py
```

This will validate your configuration and attempt to upload the database to S3.

## Troubleshooting

### "AWS credentials not configured"
- Set `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` environment variables
- Or configure AWS CLI profile with `aws configure --profile your-profile`

### "Bucket does not exist"
- The application will attempt to create the bucket automatically
- Ensure your AWS credentials have `s3:CreateBucket` permission

### "Access Denied"
- Verify your IAM user/role has S3 permissions:
  - `s3:PutObject`
  - `s3:GetObject`
  - `s3:CreateBucket` (if bucket doesn't exist)
