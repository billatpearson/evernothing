"""
S3 Configuration Test
Tests S3 sync configuration without requiring actual AWS credentials
"""

import os
import sys

def test_s3_config():
    """Test S3 configuration and setup"""
    print("=" * 60)
    print("EverNothing S3 Configuration Test")
    print("=" * 60)
    
    results = []
    
    # Test 1: Check if aws_config module exists
    print("\n[Test 1] Checking aws_config module...")
    try:
        from aws_config import S3_BUCKET_NAME, AWS_REGION, AWS_PROFILE
        print(f"✅ aws_config.py found")
        print(f"   - S3_BUCKET_NAME: {S3_BUCKET_NAME}")
        print(f"   - AWS_REGION: {AWS_REGION}")
        print(f"   - AWS_PROFILE: {AWS_PROFILE}")
        results.append(("aws_config module", True))
    except ImportError as e:
        print(f"⚠️  aws_config.py not found, using environment variables")
        S3_BUCKET_NAME = os.environ.get('S3_BUCKET_NAME', 'evernothing03032026')
        AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')
        AWS_PROFILE = os.environ.get('AWS_PROFILE', 'billspeiser2')
        print(f"   - S3_BUCKET_NAME: {S3_BUCKET_NAME}")
        print(f"   - AWS_REGION: {AWS_REGION}")
        print(f"   - AWS_PROFILE: {AWS_PROFILE}")
        results.append(("aws_config module", False))
    
    # Test 2: Check if boto3 is installed
    print("\n[Test 2] Checking boto3 installation...")
    try:
        import boto3
        print(f"✅ boto3 installed (version: {boto3.__version__})")
        results.append(("boto3 installed", True))
    except ImportError:
        print("❌ boto3 not installed")
        print("   Install with: pip install boto3")
        results.append(("boto3 installed", False))
        return results
    
    # Test 3: Check if database file exists
    print("\n[Test 3] Checking database file...")
    db_file = 'evernothing.db'
    if os.path.exists(db_file):
        size = os.path.getsize(db_file)
        print(f"✅ Database file exists: {db_file} ({size:,} bytes)")
        results.append(("database file exists", True))
    else:
        print(f"⚠️  Database file not found: {db_file}")
        print("   Run the application first to create the database")
        results.append(("database file exists", False))
    
    # Test 4: Check AWS credentials configuration
    print("\n[Test 4] Checking AWS credentials...")
    aws_access_key = os.environ.get('AWS_ACCESS_KEY_ID', 'TBD')
    aws_secret_key = os.environ.get('AWS_SECRET_ACCESS_KEY', 'TBD')
    
    if aws_access_key != 'TBD' and aws_secret_key != 'TBD':
        print(f"✅ AWS credentials configured")
        print(f"   - AWS_ACCESS_KEY_ID: {aws_access_key[:8]}...")
        print(f"   - AWS_SECRET_ACCESS_KEY: ***hidden***")
        results.append(("AWS credentials", True))
    else:
        print("⚠️  AWS credentials not configured")
        print("   Option 1: Set environment variables:")
        print("     export AWS_ACCESS_KEY_ID=your-key")
        print("     export AWS_SECRET_ACCESS_KEY=your-secret")
        print("   Option 2: Use AWS CLI profile:")
        print("     aws configure --profile billspeiser2")
        results.append(("AWS credentials", False))
    
    # Test 5: Check AWS CLI profile
    print("\n[Test 5] Checking AWS CLI profile...")
    aws_config_file = os.path.expanduser('~/.aws/credentials')
    if os.path.exists(aws_config_file):
        print(f"✅ AWS credentials file exists: {aws_config_file}")
        try:
            with open(aws_config_file, 'r') as f:
                content = f.read()
                if 'billspeiser2' in content:
                    print(f"✅ Profile 'billspeiser2' found")
                    results.append(("AWS CLI profile", True))
                else:
                    print(f"⚠️  Profile 'billspeiser2' not found")
                    results.append(("AWS CLI profile", False))
        except Exception as e:
            print(f"⚠️  Could not read credentials file: {e}")
            results.append(("AWS CLI profile", False))
    else:
        print(f"⚠️  AWS credentials file not found")
        print("   Configure with: aws configure")
        results.append(("AWS CLI profile", False))
    
    # Test 6: Test S3 connection (if credentials available)
    print("\n[Test 6] Testing S3 connection...")
    if aws_access_key != 'TBD' or os.path.exists(os.path.expanduser('~/.aws/credentials')):
        try:
            if aws_access_key != 'TBD':
                s3 = boto3.client(
                    's3',
                    region_name=AWS_REGION,
                    aws_access_key_id=aws_access_key,
                    aws_secret_access_key=aws_secret_key
                )
            else:
                s3 = boto3.Session(profile_name=AWS_PROFILE).client('s3')
            
            # Try to list buckets
            response = s3.list_buckets()
            print(f"✅ S3 connection successful")
            print(f"   Found {len(response['Buckets'])} buckets")
            
            # Check if our bucket exists
            bucket_names = [b['Name'] for b in response['Buckets']]
            if S3_BUCKET_NAME in bucket_names:
                print(f"✅ Target bucket exists: {S3_BUCKET_NAME}")
            else:
                print(f"⚠️  Target bucket not found: {S3_BUCKET_NAME}")
                print(f"   Will be created on first sync")
            
            results.append(("S3 connection", True))
        except Exception as e:
            print(f"❌ S3 connection failed: {e}")
            results.append(("S3 connection", False))
    else:
        print("⚠️  Skipped (no credentials configured)")
        results.append(("S3 connection", None))
    
    # Test 7: Check .env.example file
    print("\n[Test 7] Checking configuration template...")
    if os.path.exists('.env.example'):
        print(f"✅ .env.example file exists")
        print("   Copy to .env and configure your settings")
        results.append(("config template", True))
    else:
        print(f"⚠️  .env.example not found")
        results.append(("config template", False))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result is True)
    failed = sum(1 for _, result in results if result is False)
    skipped = sum(1 for _, result in results if result is None)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result is True else "⚠️  WARN" if result is False else "⏭️  SKIP"
        print(f"{status} - {test_name}")
    
    print(f"\nTotal: {total} tests")
    print(f"Passed: {passed}")
    print(f"Warnings: {failed}")
    print(f"Skipped: {skipped}")
    
    # Recommendations
    print("\n" + "=" * 60)
    print("Recommendations")
    print("=" * 60)
    
    if not results[1][1]:  # boto3 not installed
        print("❗ Install boto3: pip install boto3")
    
    if not results[3][1] and not results[4][1]:  # No credentials
        print("❗ Configure AWS credentials:")
        print("   aws configure --profile billspeiser2")
        print("   OR set environment variables")
    
    if results[1][1] and (results[3][1] or results[4][1]):
        print("✅ Ready for S3 sync!")
        print("   Run: python evernothing_s3.py")
    
    return results

if __name__ == '__main__':
    results = test_s3_config()
    
    # Exit with appropriate code
    has_critical_failure = not results[1][1]  # boto3 not installed
    sys.exit(1 if has_critical_failure else 0)
