#!/usr/bin/env python3
"""
Add S3 Permissions to Existing IAM User
Grants billspeiser2 user the ability to create and manage S3 buckets
"""

import boto3
import json
import sys

IAM_USER = 'billspeiser2'
POLICY_NAME = 'S3FullAccessPolicy'

policy_document = {
    "Version": "2012-10-17",
    "Statement": [{
        "Effect": "Allow",
        "Action": [
            "s3:CreateBucket",
            "s3:DeleteBucket",
            "s3:ListBucket",
            "s3:ListAllMyBuckets",
            "s3:PutObject",
            "s3:GetObject",
            "s3:DeleteObject",
            "s3:PutBucketVersioning",
            "s3:PutBucketEncryption",
            "s3:PutPublicAccessBlock",
            "s3:PutLifecycleConfiguration",
            "s3:GetBucketLocation"
        ],
        "Resource": "*"
    }]
}

try:
    iam = boto3.client('iam')
    
    # Create inline policy for user
    iam.put_user_policy(
        UserName=IAM_USER,
        PolicyName=POLICY_NAME,
        PolicyDocument=json.dumps(policy_document)
    )
    
    print(f"✅ Added S3 permissions to user: {IAM_USER}")
    print(f"✅ Policy: {POLICY_NAME}")
    print("\nYou can now run: python setup_aws_s3.py")
    
except iam.exceptions.NoSuchEntityException:
    print(f"❌ User '{IAM_USER}' not found")
    print("Create the user first or use a different AWS profile")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    print("\nNote: You need admin permissions to modify IAM policies")
    print("Run this with AWS credentials that have IAM permissions")
    sys.exit(1)
