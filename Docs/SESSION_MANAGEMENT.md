# Session Management - Implementation Details

## Overview
Enhanced session management with security features including timeout, concurrent session limits, and session validation.

## Features Implemented

### 1. Remember Me (30 Days)
- **Persistent login** checkbox on login page
- **30-day cookie** keeps user logged in
- **No timeout** when "Remember Me" is active
- **Configurable** via `REMEMBER_COOKIE_DAYS` environment variable
- **Secure** uses Flask-Login's built-in remember me functionality

### 2. Session Timeout (2 Hours Inactivity)
- **Automatic logout** after 2 hours of inactivity
- **Last activity tracking** updates on every request
- **User-friendly message** when session expires
- **Configurable** via `SESSION_TIMEOUT_HOURS` environment variable

### 2. Concurrent Session Limit (Max 3)
- **Maximum 3 active sessions** per user
- **Automatic termination** of oldest session when limit reached
- **Prevents session hijacking** by limiting concurrent access

### 3. Session Validation
- **Database verification** on every request
- **Automatic logout** if session invalidated
- **Protection against** session fixation attacks

### 4. Session Management UI
- **View active sessions** at `/sessions`
- **See login details**: time, IP address, device
- **Revoke sessions** remotely
- **Current session highlighted** in green

### 5. Security Enhancements
- **HTTPOnly cookies** (prevents XSS access)
- **SameSite=Lax** (CSRF protection)
- **Secure flag** (HTTPS only, configurable)
- **Strong session protection** (Flask-Login)

## Configuration

### Environment Variables

```bash
# Session timeout in hours (default: 2)
SESSION_TIMEOUT_HOURS=2

# Remember Me cookie duration in days (default: 30)
REMEMBER_COOKIE_DAYS=30

# Enable secure cookies (HTTPS only)
SESSION_COOKIE_SECURE=true

# Secret key for session encryption
SECRET_KEY=your-random-secret-key-here
```

### Production Settings

```bash
# Generate strong secret key
python -c "import os; print(os.urandom(32).hex())"

# Set in environment
export SECRET_KEY=<generated-key>
export SESSION_COOKIE_SECURE=true
export SESSION_TIMEOUT_HOURS=1
```

## Usage

### Remember Me Feature

1. **Enable Remember Me**
   - Check "Remember me on this device" on login
   - Stay logged in for 30 days
   - No 2-hour timeout applies

2. **Disable Remember Me**
   - Uncheck the box on login
   - Standard 2-hour inactivity timeout applies
   - Must re-login after timeout

3. **Security Notes**
   - Only use on trusted devices
   - Logout manually on shared computers
   - Cookie is HTTPOnly and encrypted

### User Session Management

1. **View Active Sessions**
   - Navigate to: Home → Sessions
   - See all active and recent sessions

2. **Revoke Session**
   - Click `[Revoke]` next to any active session
   - Session immediately invalidated
   - User logged out on next request

3. **Session Expiry**
   - Automatic logout after 2 hours of inactivity
   - Warning message: "Session expired due to inactivity"

### Admin Session Management

Admins can view user sessions via audit logs:
- `/admin/audit_logs` shows all login/logout events
- Filter by user to see session history

## Database Schema

### user_sessions Table
```sql
CREATE TABLE user_sessions(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    session_id TEXT,
    login_time TEXT,
    logout_time TEXT,
    ip_address TEXT,
    user_agent TEXT
);
```

### Session Lifecycle

1. **Login**: New session created with unique ID
2. **Activity**: `last_activity` updated on each request
3. **Validation**: Session checked against database
4. **Timeout**: Auto-logout after 2 hours inactivity
5. **Logout**: Session marked with `logout_time`

## Security Benefits

### Before
- ❌ No session timeout
- ❌ Unlimited concurrent sessions
- ❌ No session validation
- ❌ Vulnerable to session hijacking

### After
- ✅ 2-hour inactivity timeout
- ✅ Max 3 concurrent sessions
- ✅ Database-backed validation
- ✅ HTTPOnly + SameSite cookies
- ✅ Session revocation capability
- ✅ Strong session protection

## Testing

### Test Session Timeout
```python
# Login and wait 2+ hours
# Next request should redirect to login with timeout message
```

### Test Concurrent Sessions
```python
# Login from 4 different browsers/devices
# 4th login should terminate 1st session
```

### Test Session Revocation
```python
# Login from 2 devices
# Revoke session from device 1
# Device 2 should be logged out on next request
```

## Troubleshooting

### "Session expired" on every request
- Check `SECRET_KEY` is consistent across restarts
- Verify system time is correct
- Check database permissions

### Sessions not expiring
- Verify `SESSION_TIMEOUT_HOURS` is set
- Check `last_activity` is being updated
- Ensure `@app.before_request` is executing

### Can't login (concurrent limit)
- Check active sessions at `/sessions`
- Revoke old sessions
- Or wait for timeout (2 hours)

## Migration Notes

### Existing Users
- Existing sessions remain valid
- Will be validated on next request
- May need to re-login if session invalid

### Database
- No migration needed
- `user_sessions` table already exists
- New columns added automatically

## Performance Impact

- **Minimal overhead**: 1 extra DB query per request
- **Optimized**: Uses indexed queries
- **Cached**: Session data in Flask session
- **Async**: No blocking operations

## Future Enhancements

1. **Remember Me** functionality
2. **Session analytics** dashboard
3. **Suspicious activity** detection
4. **Email notifications** for new logins
5. **Device fingerprinting**
6. **Geographic session limits**
