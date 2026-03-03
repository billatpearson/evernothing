"""
EverNothing S3 Synchronization Application
Synchronizes evernothing.db to Amazon S3 bucket

Usage:
  python evernothing_s3.py

Configuration:
  Set environment variables or edit defaults below:
  - S3_BUCKET_NAME
  - AWS_REGION
  - AWS_ACCESS_KEY_ID
  - AWS_SECRET_ACCESS_KEY
"""

import os
import sys
import boto3
from datetime import datetime

# Configuration - externalized via environment variables
S3_BUCKET_NAME = os.environ.get('S3_BUCKET_NAME', 'evernothing03032026')
AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID', 'TBD')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY', 'TBD')
DB_FILE = os.environ.get('DB_FILE', 'evernothing.db')

def sync_to_s3():
    """Upload evernothing.db to S3 bucket"""
    
    # Validate configuration
    if AWS_ACCESS_KEY_ID == 'TBD' or AWS_SECRET_ACCESS_KEY == 'TBD':
        print("ERROR: AWS credentials not configured")
        print("Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables")
        return False
    
    if not os.path.exists(DB_FILE):
        print(f"ERROR: Database file '{DB_FILE}' not found")
        return False
    
    try:
        # Create S3 client
        s3 = boto3.client(
            's3',
            region_name=AWS_REGION,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY
        )
        
        # Check if bucket exists, create if not
        try:
            s3.head_bucket(Bucket=S3_BUCKET_NAME)
            print(f"Bucket {S3_BUCKET_NAME} exists")
        except:
            print(f"Creating bucket {S3_BUCKET_NAME}...")
            if AWS_REGION == 'us-east-1':
                s3.create_bucket(Bucket=S3_BUCKET_NAME)
            else:
                s3.create_bucket(
                    Bucket=S3_BUCKET_NAME,
                    CreateBucketConfiguration={'LocationConstraint': AWS_REGION}
                )
            print(f"Bucket created successfully")
        
        # Upload file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        s3_key = f"backups/{DB_FILE}.{timestamp}"
        
        print(f"Uploading {DB_FILE} to s3://{S3_BUCKET_NAME}/{s3_key}")
        s3.upload_file(DB_FILE, S3_BUCKET_NAME, s3_key)
        
        # Also upload as latest
        s3.upload_file(DB_FILE, S3_BUCKET_NAME, DB_FILE)
        
        print(f"Successfully uploaded to S3")
        print(f"  Bucket: {S3_BUCKET_NAME}")
        print(f"  Region: {AWS_REGION}")
        print(f"  Backup: {s3_key}")
        print(f"  Latest: {DB_FILE}")
        return True
        
    except Exception as e:
        print(f"ERROR: S3 sync failed: {e}")
        return False

if __name__ == '__main__':
    print("=" * 50)
    print("EverNothing S3 Sync")
    print("=" * 50)
    print(f"Bucket: {S3_BUCKET_NAME}")
    print(f"Region: {AWS_REGION}")
    print(f"Database: {DB_FILE}")
    print("-" * 50)
    
    success = sync_to_s3()
    sys.exit(0 if success else 1)
