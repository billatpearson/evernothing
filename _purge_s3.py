import boto3, os, sys
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env'))

s3 = boto3.client('s3',
    region_name=os.environ.get('AWS_REGION', 'us-east-1'),
    aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'))

BUCKET = os.environ.get('S3_BUCKET_NAME', 'evernothing-backup-2026')

paginator = s3.get_paginator('list_objects_v2')
objects = [obj for page in paginator.paginate(Bucket=BUCKET)
           for obj in page.get('Contents', [])]

if not objects:
    print('Bucket already empty.')
    sys.exit(0)

print(f'Deleting {len(objects)} unencrypted object(s) from s3://{BUCKET}...')
for obj in objects:
    print(f'  DELETE {obj["Key"]}')

result  = s3.delete_objects(Bucket=BUCKET,
              Delete={'Objects': [{'Key': o['Key']} for o in objects]})
deleted = result.get('Deleted', [])
errors  = result.get('Errors', [])
print(f'Done. Deleted: {len(deleted)}  Errors: {len(errors)}')
for e in errors:
    print(f'  ERROR: {e}')
