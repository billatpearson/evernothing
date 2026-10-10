#!/usr/bin/env python
"""Analyze login hash verification between PC and Android."""
import sqlite3
from werkzeug.security import check_password_hash as werkzeug_check
import base64
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from cryptography.hazmat.backends import default_backend

# Get the password hash from the database
con = sqlite3.connect(r'DB\evernothing.db')
r = con.cursor().execute('SELECT id, username, password FROM users WHERE username="bspeiser"').fetchone()
con.close()

user_id, username, password_hash = r

print(f"Username: {username}")
print(f"Password hash: {password_hash}")
print()

# Parse the hash
parts = password_hash.split('$')
print("Hash parts:")
print(f"  Part 0 (params): {parts[0]}")
print(f"  Part 1 (salt b64): {parts[1]}")
print(f"  Part 2 (hash hex): {parts[2][:32]}...")
print()

# Decode the components
salt_b64 = parts[1]
hash_hex = parts[2]

salt_bytes = base64.b64decode(salt_b64)
expected_hash_bytes = bytes.fromhex(hash_hex)

print(f"Salt (hex): {salt_bytes.hex()}")
print(f"Expected hash length: {len(expected_hash_bytes)}")
print()

# Test with werkzeug
print("Testing with werkzeug.check_password_hash:")
for pwd in ['TestPassword123!', 'password123', 'password', 'admin', 'bspeiser', 'Evernothing1!']:
    try:
        result = werkzeug_check(password_hash, pwd)
        print(f"  '{pwd}': {result}")
    except Exception as e:
        print(f"  '{pwd}': ERROR - {e}")
print()

# Test with cryptography library (Android approach)
print("Testing with cryptography Scrypt (Android):")
n, r, p = 32768, 8, 1

test_passwords = ['TestPassword123!', 'password123', 'password', 'admin', 'bspeiser', 'Evernothing1!']
for pwd in test_passwords:
    kdf = Scrypt(salt=salt_bytes, length=len(expected_hash_bytes), n=n, r=r, p=p, backend=default_backend())
    derived = kdf.derive(pwd.encode('utf-8'))
    
    # Constant-time comparison
    result = 0
    for x, y in zip(derived, expected_hash_bytes):
        result |= x ^ y
    
    is_match = result == 0
    print(f"  '{pwd}': {is_match}")
