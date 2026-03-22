"""
Permanently deletes ALL objects in s3://evernothing-backup-2026.
WARNING: This is irreversible.
"""
import boto3, os

BUCKET = "evernothing-backup-2026"

def main():
    s3 = boto3.resource(
        "s3",
        region_name=os.environ.get("AWS_REGION", "us-east-1"),
        aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
    )
    bucket = s3.Bucket(BUCKET)

    confirm = input(f"Type 'yes' to permanently delete ALL objects in s3://{BUCKET}: ")
    if confirm.strip().lower() != "yes":
        print("Aborted.")
        return

    deleted = bucket.object_versions.delete()
    count = sum(len(r.get("Deleted", [])) for r in (deleted if isinstance(deleted, list) else [deleted]))
    print(f"Done. {count} object version(s) deleted from s3://{BUCKET}.")

if __name__ == "__main__":
    main()
