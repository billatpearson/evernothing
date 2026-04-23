import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env'))

from evernothing_logic import _sync_s3_worker
print("Pushing encrypted backup to S3...")
_sync_s3_worker()
print("Done.")
