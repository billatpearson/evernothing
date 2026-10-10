"""Custom scrypt password verification for Android (where hashlib.scrypt is not available)."""

import re
import base64
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from cryptography.hazmat.backends import default_backend


def _parse_scrypt_hash(hash_string):
    """Parse a scrypt hash string into its components.
    
    Format: scrypt:N:r:p$salt$hash
    Note: salt is base64-encoded, hash is hex-encoded
    Returns (n, r, p, salt_bytes, expected_hash_bytes) or None if parsing fails.
    """
    pattern = r'^scrypt:(\d+):(\d+):(\d+)\$([a-zA-Z0-9+/=]+)\$([a-fA-F0-9]+)$'
    match = re.match(pattern, hash_string)
    if not match:
        return None
    
    n = int(match.group(1))
    r = int(match.group(2))
    p = int(match.group(3))
    salt_b64 = match.group(4)
    hash_hex = match.group(5)
    
    try:
        salt_bytes = base64.b64decode(salt_b64)
        expected_hash_bytes = bytes.fromhex(hash_hex)
        return (n, r, p, salt_bytes, expected_hash_bytes)
    except Exception:
        return None


def verify_scrypt_password(password, hash_string):
    """Verify a password against a scrypt hash using cryptography library.
    
    This implements scrypt verification compatible with the scrypt hashes in the database.
    The hash format is: scrypt:N:r:p$salt$hash
    - salt is base64-encoded
    - hash is hex-encoded
    
    Args:
        password: The plain text password to verify
        hash_string: The scrypt hash string
    
    Returns:
        True if password matches, False otherwise
    """
    parsed = _parse_scrypt_hash(hash_string)
    if parsed is None:
        return False
    
    n, r, p, salt_bytes, expected_hash_bytes = parsed
    
    try:
        # Derive key using scrypt with the provided password
        kdf = Scrypt(
            salt=salt_bytes,
            length=len(expected_hash_bytes),
            n=n,
            r=r,
            p=p,
            backend=default_backend()
        )
        
        # Derive the key and compare
        derived = kdf.derive(password.encode('utf-8'))
        
        # Constant-time comparison
        if len(derived) != len(expected_hash_bytes):
            return False
        
        # Secure comparison using XOR
        result = 0
        for x, y in zip(derived, expected_hash_bytes):
            result |= x ^ y
        
        return result == 0
        
    except Exception:
        return False


def check_password_hash(password_hash, password):
    """Drop-in replacement for werkzeug.security.check_password_hash.
    
    This handles scrypt hashes using our custom implementation,
    and falls back to werkzeug for other hash types.
    
    Args:
        password_hash: The stored password hash
        password: The plain text password to verify
    
    Returns:
        True if password matches, False otherwise
    """
    # Handle scrypt hashes with our custom implementation
    if password_hash and password_hash.startswith('scrypt:'):
        return verify_scrypt_password(password, password_hash)
    
    # For other hash types or empty inputs
    if not password_hash or not password:
        return False
        
    try:
        from werkzeug.security import check_password_hash as werkzeug_check
        return werkzeug_check(password_hash, password)
    except Exception:
        return False
