"""
Rate Limiting for EverNothing
Prevents brute force attacks on authentication endpoints

Configuration (environment variables):
- RATE_LIMIT_ENABLED: Enable rate limiting (default: true)
- RATE_LIMIT_LOGIN: Max login attempts per IP per hour (default: 10)
- RATE_LIMIT_REGISTER: Max registrations per IP per hour (default: 5)
"""

import os
import time
from collections import defaultdict
from datetime import datetime, timedelta

RATE_LIMIT_ENABLED = os.environ.get('RATE_LIMIT_ENABLED', 'true').lower() == 'true'
RATE_LIMIT_LOGIN = int(os.environ.get('RATE_LIMIT_LOGIN', '10'))
RATE_LIMIT_REGISTER = int(os.environ.get('RATE_LIMIT_REGISTER', '5'))

# In-memory storage: {ip_address: [(timestamp, endpoint), ...]}
rate_limit_store = defaultdict(list)

def check_rate_limit(ip_address, endpoint, limit):
    """Check if IP has exceeded rate limit for endpoint"""
    if not RATE_LIMIT_ENABLED:
        return True
    
    now = datetime.now()
    one_hour_ago = now - timedelta(hours=1)
    
    # Clean old entries
    rate_limit_store[ip_address] = [
        (ts, ep) for ts, ep in rate_limit_store[ip_address]
        if ts > one_hour_ago
    ]
    
    # Count requests for this endpoint
    count = sum(1 for ts, ep in rate_limit_store[ip_address] if ep == endpoint)
    
    if count >= limit:
        return False
    
    # Record this request
    rate_limit_store[ip_address].append((now, endpoint))
    return True

def get_remaining_attempts(ip_address, endpoint, limit):
    """Get remaining attempts for IP on endpoint"""
    if not RATE_LIMIT_ENABLED:
        return limit
    
    now = datetime.now()
    one_hour_ago = now - timedelta(hours=1)
    
    # Count recent requests
    count = sum(
        1 for ts, ep in rate_limit_store.get(ip_address, [])
        if ts > one_hour_ago and ep == endpoint
    )
    
    return max(0, limit - count)

def clear_rate_limit(ip_address, endpoint=None):
    """Clear rate limit for IP (admin function)"""
    if endpoint:
        rate_limit_store[ip_address] = [
            (ts, ep) for ts, ep in rate_limit_store.get(ip_address, [])
            if ep != endpoint
        ]
    else:
        rate_limit_store.pop(ip_address, None)
