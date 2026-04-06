"""
AWS Configuration Module
Centralizes all AWS-related parameters for EverNothing application

Configuration Priority:
1. Environment variables (highest priority)
2. Default values defined here

Environment Variables:
- S3_BUCKET_NAME: S3 bucket name for database backups
- AWS_REGION: AWS region for S3 bucket
- AWS_ACCESS_KEY_ID: AWS access key
- AWS_SECRET_ACCESS_KEY: AWS secret key
- AWS_PROFILE: AWS CLI profile name (optional)
- DB_FILE: Database filename to sync
"""

import os

# S3 Configuration
S3_BUCKET_NAME = os.environ.get('S3_BUCKET_NAME', '')
AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')

# AWS Credentials — prefer IAM roles; only use keys if no role is available
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID', '')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY', '')
AWS_PROFILE = os.environ.get('AWS_PROFILE', '')

# Database Configuration
DB_FILE = os.environ.get('DB_FILE', 'evernothing.db')
