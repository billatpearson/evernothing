#!/usr/bin/env python
import boto3

s3 = boto3.client('s3', region_name='us-east-1')
bucket = 'evernothing-backup-2026'
resp = s3.list_objects_v2(Bucket=bucket, Prefix='')

print(f"Objects in s3://{bucket}/:")
for obj in resp.get('Contents', []):
    print(f"  {obj['Key']} ({obj['Size']} bytes)")
