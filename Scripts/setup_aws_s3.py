#!/usr/bin/env python3
"""
Automated AWS S3 Setup for EverNothing
Creates S3 bucket, IAM user, and configures permissions

Usage:
    python setup_aws_s3.py

Requirements:
    pip install boto3
    aws configure (with admin credentials)
"""

import boto3
import json
import sys
import os
from datetime import datetime

# Configuration
BUCKET_NAME = os.environ.get('S3_BUCKET_NAME', 'evernothing-backup-2026')
REGION = os.environ.get('AWS_REGION', 'us-east-1')
IAM_USER = 'evernothing-app'
POLICY_NAME = 'EverNothingS3Policy'
# Optional: comma-separated CIDRs to restrict bucket access by IP (e.g. "203.0.113.0/24,10.0.0.0/8")
# Leave empty to skip IP restriction (HTTPS-only policy still applies).
ALLOWED_IPS = [ip.strip() for ip in os.environ.get('S3_ALLOWED_IPS', '').split(',') if ip.strip()]


def _apply_bucket_policy(s3_client, bucket_name):
    """Apply bucket policy that:
      - Denies all requests over plain HTTP (fix #11)
      - Optionally restricts access to ALLOWED_IPS CIDRs (fix #12)
    """
    statements = [
        {
            "Sid": "DenyInsecureTransport",
            "Effect": "Deny",
            "Principal": "*",
            "Action": "s3:*",
            "Resource": [
                f"arn:aws:s3:::{bucket_name}",
                f"arn:aws:s3:::{bucket_name}/*"
            ],
            "Condition": {"Bool": {"aws:SecureTransport": "false"}}
        }
    ]
    if ALLOWED_IPS:
        statements.append({
            "Sid": "DenyNonAllowedIPs",
            "Effect": "Deny",
            "Principal": "*",
            "Action": "s3:*",
            "Resource": [
                f"arn:aws:s3:::{bucket_name}",
                f"arn:aws:s3:::{bucket_name}/*"
            ],
            "Condition": {"NotIpAddress": {"aws:SourceIp": ALLOWED_IPS}}
        })
    policy = {"Version": "2012-10-17", "Statement": statements}
    try:
        s3_client.put_bucket_policy(Bucket=bucket_name, Policy=json.dumps(policy))
        print(f"✅ Bucket policy applied (HTTPS-only{', IP restriction' if ALLOWED_IPS else ''})")
    except Exception as e:
        print(f"⚠️  Could not apply bucket policy: {e}")

def print_header(text):
    print("\n" + "=" * 60)
    print(text)
    print("=" * 60)

def print_step(step, text):
    print(f"\n[Step {step}] {text}")

def create_s3_bucket(s3_client):
    """Create S3 bucket with proper configuration"""
    print_step(1, "Creating S3 Bucket")
    
    try:
        # Check if bucket exists
        try:
            s3_client.head_bucket(Bucket=BUCKET_NAME)
            print(f"✅ Bucket '{BUCKET_NAME}' already exists")
            return True
        except:
            pass
        
        # Create bucket
        if REGION == 'us-east-1':
            s3_client.create_bucket(Bucket=BUCKET_NAME)
        else:
            s3_client.create_bucket(
                Bucket=BUCKET_NAME,
                CreateBucketConfiguration={'LocationConstraint': REGION}
            )
        print(f"✅ Created bucket: {BUCKET_NAME}")
        
        # Enable versioning
        s3_client.put_bucket_versioning(
            Bucket=BUCKET_NAME,
            VersioningConfiguration={'Status': 'Enabled'}
        )
        print(f"✅ Enabled versioning")
        
        # Enable encryption
        s3_client.put_bucket_encryption(
            Bucket=BUCKET_NAME,
            ServerSideEncryptionConfiguration={
                'Rules': [{'ApplyServerSideEncryptionByDefault': {'SSEAlgorithm': 'AES256'}}]
            }
        )
        print(f"✅ Enabled encryption")
        
        # Block public access
        s3_client.put_public_access_block(
            Bucket=BUCKET_NAME,
            PublicAccessBlockConfiguration={
                'BlockPublicAcls': True,
                'IgnorePublicAcls': True,
                'BlockPublicPolicy': True,
                'RestrictPublicBuckets': True
            }
        )
        print(f"✅ Blocked public access")
        
        # Add lifecycle rule (optional - commented out for infinite retention)
        # Uncomment to enable 30-day retention:
        # s3_client.put_bucket_lifecycle_configuration(
        #     Bucket=BUCKET_NAME,
        #     LifecycleConfiguration={
        #         'Rules': [{
        #             'Id': 'DeleteOldBackups',
        #             'Status': 'Enabled',
        #             'Prefix': 'backups/',
        #             'Expiration': {'Days': 30}
        #         }]
        #     }
        # )
        # print(f"✅ Configured lifecycle (30-day retention)")
        print(f"✅ Lifecycle: Infinite retention (no auto-delete)")

        # fix #14: Object Lock — GOVERNANCE mode protects against accidental/malicious deletes.
        # Note: Object Lock must be enabled at bucket creation time via CreateBucket; since we
        # can't retroactively enable it here, we set the default retention rule which applies
        # to all new objects. To enable Object Lock on a brand-new bucket, delete and recreate
        # with ObjectLockEnabledForBucket=True, or use setup_aws_s3.py from scratch.
        lock_days = int(os.environ.get('S3_LOCK_DAYS', '30'))
        try:
            s3_client.put_object_lock_configuration(
                Bucket=BUCKET_NAME,
                ObjectLockConfiguration={
                    'ObjectLockEnabled': 'Enabled',
                    'Rule': {
                        'DefaultRetention': {
                            'Mode': 'GOVERNANCE',
                            'Days': lock_days
                        }
                    }
                }
            )
            print(f"✅ Object Lock enabled (GOVERNANCE, {lock_days} days)")
        except Exception as e:
            print(f"⚠️  Object Lock not applied (bucket may need to be recreated with ObjectLockEnabledForBucket=True): {e}")

        # fix #13: server access logging — logs go to <bucket>-logs
        log_bucket = f"{BUCKET_NAME}-logs"
        try:
            try:
                s3_client.head_bucket(Bucket=log_bucket)
            except Exception:
                if REGION == 'us-east-1':
                    s3_client.create_bucket(Bucket=log_bucket)
                else:
                    s3_client.create_bucket(Bucket=log_bucket,
                        CreateBucketConfiguration={'LocationConstraint': REGION})
                s3_client.put_public_access_block(Bucket=log_bucket,
                    PublicAccessBlockConfiguration={
                        'BlockPublicAcls': True, 'IgnorePublicAcls': True,
                        'BlockPublicPolicy': True, 'RestrictPublicBuckets': True})
                print(f"✅ Log bucket created: {log_bucket}")
            s3_client.put_bucket_acl(Bucket=log_bucket, ACL='log-delivery-write')
            s3_client.put_bucket_logging(
                Bucket=BUCKET_NAME,
                BucketLoggingStatus={
                    'LoggingEnabled': {
                        'TargetBucket': log_bucket,
                        'TargetPrefix': 'access-logs/'
                    }
                }
            )
            print(f"✅ Access logging enabled → s3://{log_bucket}/access-logs/")
        except Exception as e:
            print(f"⚠️  Could not enable access logging: {e}")

        # Enforce HTTPS-only and optionally restrict to known IPs
        _apply_bucket_policy(s3_client, BUCKET_NAME)

        return True
    except Exception as e:
        print(f"❌ Error creating bucket: {e}")
        return False

def create_iam_policy(iam_client):
    """Create IAM policy for S3 access"""
    print_step(2, "Creating IAM Policy")
    
    policy_document = {
        "Version": "2012-10-17",
        "Statement": [{
            "Sid": "EverNothingS3Access",
            "Effect": "Allow",
            "Action": [
                "s3:PutObject",
                "s3:GetObject",
                "s3:ListBucket",
                "s3:DeleteObject"
            ],
            "Resource": [
                f"arn:aws:s3:::{BUCKET_NAME}",
                f"arn:aws:s3:::{BUCKET_NAME}/*"
            ]
        }]
    }
    
    try:
        # Check if policy exists
        try:
            response = iam_client.list_policies(Scope='Local', MaxItems=1000)
            for policy in response['Policies']:
                if policy['PolicyName'] == POLICY_NAME:
                    print(f"✅ Policy '{POLICY_NAME}' already exists")
                    return policy['Arn']
        except:
            pass
        
        # Create policy
        response = iam_client.create_policy(
            PolicyName=POLICY_NAME,
            PolicyDocument=json.dumps(policy_document),
            Description='Allows EverNothing app to backup to S3'
        )
        policy_arn = response['Policy']['Arn']
        print(f"✅ Created policy: {POLICY_NAME}")
        print(f"   ARN: {policy_arn}")
        return policy_arn
    except Exception as e:
        print(f"❌ Error creating policy: {e}")
        return None

def create_iam_user(iam_client, policy_arn):
    """Create IAM user and attach policy"""
    print_step(3, "Creating IAM User")
    
    try:
        # Check if user exists
        try:
            iam_client.get_user(UserName=IAM_USER)
            print(f"✅ User '{IAM_USER}' already exists")
        except iam_client.exceptions.NoSuchEntityException:
            # Create user
            iam_client.create_user(
                UserName=IAM_USER,
                Tags=[
                    {'Key': 'Application', 'Value': 'EverNothing'},
                    {'Key': 'Purpose', 'Value': 'S3 Backup'}
                ]
            )
            print(f"✅ Created user: {IAM_USER}")
        
        # Attach policy
        iam_client.attach_user_policy(
            UserName=IAM_USER,
            PolicyArn=policy_arn
        )
        print(f"✅ Attached policy to user")
        
        return True
    except Exception as e:
        print(f"❌ Error creating user: {e}")
        return False

def create_access_key(iam_client):
    """Create access key for IAM user"""
    print_step(4, "Creating Access Key")
    
    try:
        # List existing keys
        response = iam_client.list_access_keys(UserName=IAM_USER)
        if len(response['AccessKeyMetadata']) >= 2:
            print(f"⚠️  User already has 2 access keys (maximum)")
            print(f"   Delete an old key first with:")
            print(f"   aws iam delete-access-key --user-name {IAM_USER} --access-key-id <KEY_ID>")
            return None
        
        # Create new access key
        response = iam_client.create_access_key(UserName=IAM_USER)
        access_key = response['AccessKey']
        
        print(f"✅ Created access key")
        return access_key
    except Exception as e:
        print(f"❌ Error creating access key: {e}")
        return None

def save_credentials(access_key):
    """Save credentials to file"""
    print_step(5, "Saving Credentials")
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'aws_credentials_{timestamp}.txt'
    
    try:
        with open(filename, 'w') as f:
            f.write("AWS Credentials for EverNothing\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"Access Key ID: {access_key['AccessKeyId']}\n")
            f.write(f"Secret Access Key: {access_key['SecretAccessKey']}\n")
            f.write(f"Region: {REGION}\n")
            f.write(f"Bucket: {BUCKET_NAME}\n\n")
            f.write("=" * 60 + "\n")
            f.write("IMPORTANT: Keep these credentials secure!\n")
            f.write("Add to .env file or configure with:\n")
            f.write(f"aws configure --profile billspeiser2\n")
        
        print(f"✅ Credentials saved to: {filename}")
        print(f"⚠️  IMPORTANT: Keep this file secure and delete after configuring!")
        return filename
    except Exception as e:
        print(f"❌ Error saving credentials: {e}")
        return None

def create_env_file(access_key):
    """Create .env file with credentials"""
    print_step(6, "Creating .env File")
    
    env_content = f"""# EverNothing AWS Configuration
# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

# S3 Configuration
S3_BUCKET_NAME={BUCKET_NAME}
AWS_REGION={REGION}

# AWS Credentials
AWS_ACCESS_KEY_ID={access_key['AccessKeyId']}
AWS_SECRET_ACCESS_KEY={access_key['SecretAccessKey']}
AWS_PROFILE=billspeiser2

# Database Configuration
DB_FILE=evernothing.db

# Application Configuration
SECRET_KEY=change-this-in-production
ENCRYPTION_ENABLED=false
ADMIN_USER=admin
ADMIN_PASS=admin

# Session Configuration
SESSION_TIMEOUT_HOURS=2
REMEMBER_COOKIE_DAYS=30
SESSION_COOKIE_SECURE=false
"""
    
    try:
        # Check if .env exists
        if os.path.exists('.env'):
            backup = f'.env.backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
            os.rename('.env', backup)
            print(f"⚠️  Existing .env backed up to: {backup}")
        
        with open('.env', 'w') as f:
            f.write(env_content)
        
        print(f"✅ Created .env file")
        return True
    except Exception as e:
        print(f"❌ Error creating .env file: {e}")
        return False

def test_configuration(access_key):
    """Test S3 access with new credentials"""
    print_step(7, "Testing Configuration")
    
    try:
        # Create S3 client with new credentials
        s3 = boto3.client(
            's3',
            region_name=REGION,
            aws_access_key_id=access_key['AccessKeyId'],
            aws_secret_access_key=access_key['SecretAccessKey']
        )
        
        # Test bucket access
        s3.head_bucket(Bucket=BUCKET_NAME)
        print(f"✅ Bucket access verified")
        
        # Test upload
        test_content = f"Test file created at {datetime.now()}"
        s3.put_object(
            Bucket=BUCKET_NAME,
            Key='test.txt',
            Body=test_content.encode()
        )
        print(f"✅ Upload test successful")
        
        # Test download
        response = s3.get_object(Bucket=BUCKET_NAME, Key='test.txt')
        content = response['Body'].read().decode()
        print(f"✅ Download test successful")
        
        # Cleanup test file
        s3.delete_object(Bucket=BUCKET_NAME, Key='test.txt')
        print(f"✅ Cleanup successful")
        
        return True
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def main():
    print_header("EverNothing AWS S3 Automated Setup")
    
    print("\nThis script will:")
    print("1. Create S3 bucket with encryption and versioning")
    print("2. Create IAM policy with minimal permissions")
    print("3. Create IAM user and attach policy")
    print("4. Generate access keys")
    print("5. Save credentials to .env file")
    print("6. Test the configuration")
    
    print(f"\nConfiguration:")
    print(f"  Bucket: {BUCKET_NAME}")
    print(f"  Region: {REGION}")
    print(f"  IAM User: {IAM_USER}")
    
    response = input("\nProceed? (yes/no): ").lower()
    if response != 'yes':
        print("Setup cancelled.")
        sys.exit(0)
    
    try:
        # Initialize AWS clients
        s3_client = boto3.client('s3', region_name=REGION)
        iam_client = boto3.client('iam')
        
        # Execute setup steps
        if not create_s3_bucket(s3_client):
            sys.exit(1)
        
        policy_arn = create_iam_policy(iam_client)
        if not policy_arn:
            sys.exit(1)
        
        if not create_iam_user(iam_client, policy_arn):
            sys.exit(1)
        
        access_key = create_access_key(iam_client)
        if not access_key:
            sys.exit(1)
        
        creds_file = save_credentials(access_key)
        if not creds_file:
            sys.exit(1)
        
        if not create_env_file(access_key):
            sys.exit(1)
        
        if not test_configuration(access_key):
            print("\n⚠️  Configuration test failed, but resources were created")
            print("   Check credentials and try manual testing")
        
        # Success summary
        print_header("Setup Complete! 🎉")
        print(f"\n✅ S3 Bucket: {BUCKET_NAME}")
        print(f"✅ IAM User: {IAM_USER}")
        print(f"✅ Credentials saved to: {creds_file}")
        print(f"✅ Configuration saved to: .env")
        
        print("\nNext steps:")
        print("1. Review and secure the credentials file")
        print("2. Test with: python evernothing_s3.py")
        print("3. Delete credentials file after confirming it works")
        print(f"4. Keep .env file secure (already in .gitignore)")
        
        print("\nTo configure AWS CLI:")
        print(f"aws configure --profile billspeiser2")
        print(f"  Access Key ID: {access_key['AccessKeyId']}")
        print(f"  Secret Access Key: {access_key['SecretAccessKey']}")
        print(f"  Region: {REGION}")
        
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        print("\nTroubleshooting:")
        print("1. Ensure AWS CLI is configured with admin credentials")
        print("2. Check you have permissions to create S3 buckets and IAM users")
        print("3. Verify bucket name is globally unique")
        sys.exit(1)

if __name__ == '__main__':
    main()
