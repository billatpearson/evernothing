"""
One-time setup: creates a KMS CMK and configures the S3 bucket with:
  - SSE-KMS default encryption (your CMK)
  - Versioning enabled
  - Bucket policy denying uploads without SSE-KMS

Run once:
  python setup_kms_s3.py

The KMS_KEY_ID printed at the end must be added to .env.
"""
import boto3, json, os, sys

S3_BUCKET_NAME = os.environ.get('S3_BUCKET_NAME', 'evernothing-backup-2026')
AWS_REGION     = os.environ.get('AWS_REGION', 'us-east-1')
AWS_ACCESS_KEY_ID     = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
AWS_PROFILE    = os.environ.get('AWS_PROFILE', 'billspeiser2')

def get_clients():
    if AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY:
        session = boto3.Session(
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            region_name=AWS_REGION
        )
    else:
        session = boto3.Session(profile_name=AWS_PROFILE, region_name=AWS_REGION)
    return session.client('kms'), session.client('s3')

def main():
    kms, s3 = get_clients()

    # 1. Create CMK
    print("Creating KMS CMK...")
    key = kms.create_key(
        Description='EverNothing database encryption key',
        KeyUsage='ENCRYPT_DECRYPT',
        Tags=[{'TagKey': 'Application', 'TagValue': 'EverNothing'}]
    )
    key_id  = key['KeyMetadata']['KeyId']
    key_arn = key['KeyMetadata']['Arn']
    print(f"  KeyId:  {key_id}")
    print(f"  KeyArn: {key_arn}")

    kms.create_alias(AliasName='alias/evernothing', TargetKeyId=key_id)
    print("  Alias:  alias/evernothing")

    # 2. Enable versioning
    print(f"\nEnabling versioning on s3://{S3_BUCKET_NAME}...")
    s3.put_bucket_versioning(
        Bucket=S3_BUCKET_NAME,
        VersioningConfiguration={'Status': 'Enabled'}
    )

    # 3. Set SSE-KMS as default encryption
    print("Setting SSE-KMS default encryption...")
    s3.put_bucket_encryption(
        Bucket=S3_BUCKET_NAME,
        ServerSideEncryptionConfiguration={
            'Rules': [{
                'ApplyServerSideEncryptionByDefault': {
                    'SSEAlgorithm': 'aws:kms',
                    'KMSMasterKeyID': key_arn
                },
                'BucketKeyEnabled': True
            }]
        }
    )

    # 4. Deny unencrypted uploads
    print("Applying deny-unencrypted bucket policy...")
    policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "DenyUnencryptedUploads",
                "Effect": "Deny",
                "Principal": "*",
                "Action": "s3:PutObject",
                "Resource": f"arn:aws:s3:::{S3_BUCKET_NAME}/*",
                "Condition": {
                    "StringNotEquals": {
                        "s3:x-amz-server-side-encryption": "aws:kms"
                    }
                }
            }
        ]
    }
    s3.put_bucket_policy(Bucket=S3_BUCKET_NAME, Policy=json.dumps(policy))

    print(f"""
Setup complete.

Add this to your .env file:
  KMS_KEY_ID={key_id}

To decrypt/download the DB locally:
  aws s3 cp s3://{S3_BUCKET_NAME}/evernothing.db ./evernothing.db
  (KMS decryption is transparent via AWS CLI / boto3)
""")

if __name__ == '__main__':
    main()
