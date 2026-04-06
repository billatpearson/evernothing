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

import gzip, io, os, sys
import boto3
from datetime import datetime

try:
    from aws_config import S3_BUCKET_NAME, AWS_REGION, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, DB_FILE
except ImportError:
    # Fallback to environment variables if aws_config not available
    S3_BUCKET_NAME = os.environ.get('S3_BUCKET_NAME', '')
    AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')
    AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID', '')
    AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY', '')
    DB_FILE = os.environ.get('DB_FILE', 'evernothing.db')

NUM_BACKUPS = int(os.environ.get('NUM_BACKUPS', '10'))

def sync_to_s3():
    """Upload evernothing.db to S3 bucket"""
    
    # Validate configuration
    if not AWS_ACCESS_KEY_ID or not AWS_SECRET_ACCESS_KEY:
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
        
        # Compress and upload timestamped backup
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        s3_key = f"backups/{DB_FILE}.{timestamp}.gz"

        with open(DB_FILE, 'rb') as f:
            buf = io.BytesIO()
            with gzip.GzipFile(fileobj=buf, mode='wb') as gz:
                gz.write(f.read())
            buf.seek(0)

        print(f"Uploading compressed backup to s3://{S3_BUCKET_NAME}/{s3_key}")
        s3.upload_fileobj(buf, S3_BUCKET_NAME, s3_key)

        # Also upload uncompressed latest
        s3.upload_file(DB_FILE, S3_BUCKET_NAME, DB_FILE)

        # Prune old backups, keep only the last NUM_BACKUPS
        paginator = s3.get_paginator('list_objects_v2')
        all_backups = sorted(
            [obj for page in paginator.paginate(Bucket=S3_BUCKET_NAME, Prefix=f"backups/{DB_FILE}.")
             for obj in page.get('Contents', [])],
            key=lambda o: o['LastModified']
        )
        to_delete = all_backups[:-NUM_BACKUPS] if len(all_backups) > NUM_BACKUPS else []
        if to_delete:
            s3.delete_objects(Bucket=S3_BUCKET_NAME,
                              Delete={'Objects': [{'Key': o['Key']} for o in to_delete]})
            print(f"  Pruned {len(to_delete)} old backup(s), keeping {NUM_BACKUPS}")

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
