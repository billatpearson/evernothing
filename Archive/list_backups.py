import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from evernothing import _s3_client, S3_BUCKET_NAME

s3 = _s3_client()
response = s3.list_objects_v2(Bucket=S3_BUCKET_NAME, Prefix='backups/')
if 'Contents' in response:
    backups = [c['Key'] for c in response['Contents'] if '.db' in c['Key']]
    print(f'Found {len(backups)} backups:')
    for b in sorted(backups, reverse=True)[:10]:
        print(f'  {b}')
else:
    print('No backups found')
