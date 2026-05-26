"""Evernothing_Web/routes/auth.py — Authentication routes."""
import datetime, os, sqlite3
from datetime import timezone
from flask import make_response, redirect, request, session
from flask_login import login_user, logout_user, login_required
from werkzeug.security import check_password_hash, generate_password_hash
from itsdangerous import URLSafeTimedSerializer

from Evernothing_Web.app import app, logger
from Evernothing_DB.database import get_db
from Evernothing_Security.security import User, validate_input, validate_email, validate_password
from Evernothing_Connect.s3_sync import sync_s3_async
from Evernothing_Web.routes.helpers import _render

# Import templates from monolith during transition
import evernothing as _en


def _serializer():
    return URLSafeTimedSerializer(app.secret_key)


@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        con = get_db(); cur = con.cursor()
        user = cur.execute('SELECT username FROM users WHERE email=?', (email,)).fetchone()
        con.close()
        if user:
            token = _serializer().dumps(email, salt='recover-key')
            link = request.url_root + 'reset_password/' + token
            try:
                from email_utils import send_password_reset_email
                send_password_reset_email(email, link)
            except ImportError:
                logger.warning('email_utils not available')
        return _render(_en.T_FORGOT_PASSWORD, message='If that email exists, a reset link has been sent.')
    return _render(_en.T_FORGOT_PASSWORD)


@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        email = _serializer().loads(token, salt='recover-key', max_age=3600)
    except Exception:
        return _render(_en.T_RESET_PASSWORD, error='Invalid or expired token.')
    if request.method == 'POST':
        con = get_db(); cur = con.cursor()
        cur.execute('UPDATE users SET password=? WHERE email=?',
                    (generate_password_hash(request.form['password']), email))
        con.commit(); con.close()
        sync_s3_async()
        return redirect('/login')
    return _render(_en.T_RESET_PASSWORD)


@app.route('/login', methods=['GET', 'POST'])
def login():
    from rate_limiter import check_rate_limit, get_remaining_attempts, RATE_LIMIT_LOGIN
    from Evernothing_Security.login_lockout import (
        is_locked, register_failure, clear_failures, lockout_seconds_remaining,
    )
    error = None
    if request.args.get('timeout'):
        error = 'Session expired due to inactivity. Please login again.'
    elif request.args.get('invalid'):
        error = 'Invalid session. Please login again.'
    elif request.args.get('csrf'):
        error = 'Your session has expired. Please log in again.'

    if request.method == 'POST':
        username = request.form.get('username', '')
        if not check_rate_limit(request.remote_addr, 'login', RATE_LIMIT_LOGIN):
            logger.warning(f'Rate limit exceeded for login from {request.remote_addr}')
            return _render(_en.T_LOGIN, error='Too many login attempts. Please try again later.',
                           last_user=request.cookies.get('last_user', ''))
        if is_locked(username):
            secs = lockout_seconds_remaining(username)
            mins = max(1, secs // 60)
            return _render(_en.T_LOGIN,
                           error=f'Account locked due to repeated failed logins. Try again in ~{mins} min.',
                           last_user=request.cookies.get('last_user', ''))

        con = get_db(); cur = con.cursor()
        r = cur.execute('SELECT id,password FROM users WHERE username=?',
                        (username,)).fetchone()
        if r and check_password_hash(r['password'], request.form['password']):
            clear_failures(username)
            # Enforce max 3 concurrent sessions
            active = cur.execute(
                'SELECT COUNT(*) FROM user_sessions WHERE user_id=? AND logout_time IS NULL', (r['id'],)
            ).fetchone()[0]
            if active >= 3:
                oldest = cur.execute(
                    'SELECT session_id FROM user_sessions WHERE user_id=? AND logout_time IS NULL ORDER BY login_time ASC LIMIT 1',
                    (r['id'],)).fetchone()
                if oldest:
                    cur.execute('UPDATE user_sessions SET logout_time=? WHERE session_id=?',
                                (datetime.datetime.now(timezone.utc).isoformat(), oldest[0]))
            remember_me = request.form.get('remember_me') == 'on'
            sid = os.urandom(16).hex()
            session.update({'session_id': sid,
                            'last_activity': datetime.datetime.now(timezone.utc).isoformat(),
                            'remember_me': remember_me})
            session.permanent = True
            now = datetime.datetime.now(timezone.utc).isoformat()
            cur.execute('UPDATE users SET last_login=? WHERE id=?', (now, r['id']))
            cur.execute('INSERT INTO user_sessions (user_id,session_id,login_time,ip_address,user_agent) VALUES(?,?,?,?,?)',
                        (r['id'], sid, now, request.remote_addr, request.user_agent.string))
            con.commit(); con.close()
            login_user(User(r['id'], username), remember=remember_me)
            resp = make_response(redirect('/'))
            resp.set_cookie(
                'last_user', username,
                max_age=60 * 60 * 24 * 365,
                httponly=True,
                secure=app.config.get('SESSION_COOKIE_SECURE', True),
                samesite='Lax',
            )
            return resp
        con.close()
        if register_failure(username):
            logger.warning(f'Account locked for {username!r} after repeated failed logins from {request.remote_addr}')
        error = 'Invalid username or password'
    return _render(_en.T_LOGIN, error=error,
                   last_user=request.cookies.get('last_user', ''))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        from rate_limiter import check_rate_limit, RATE_LIMIT_REGISTER
        if not check_rate_limit(request.remote_addr, 'register', RATE_LIMIT_REGISTER):
            return _render(_en.T_REGISTER, error='Too many registration attempts.')
        username, err = validate_input(request.form.get('username', ''), max_length=50)
        if err: return _render(_en.T_REGISTER, error=err)
        email, err = validate_email(request.form.get('email', ''))
        if err: return _render(_en.T_REGISTER, error=err)
        password, err = validate_password(request.form.get('password', ''))
        if err: return _render(_en.T_REGISTER, error=err)
        con = get_db(); cur = con.cursor()
        try:
            cur.execute('INSERT INTO users (username,password,email) VALUES(?,?,?)',
                        (username, generate_password_hash(password), email))
            con.commit(); sync_s3_async()
            return redirect('/login')
        except sqlite3.IntegrityError:
            return _render(_en.T_REGISTER, error='Username already exists')
        finally:
            con.close()
    return _render(_en.T_REGISTER)


@app.route('/logout')
def logout():
    if 'session_id' in session:
        con = get_db(); cur = con.cursor()
        cur.execute('UPDATE user_sessions SET logout_time=? WHERE session_id=?',
                    (datetime.datetime.now(timezone.utc).isoformat(), session['session_id']))
        con.commit(); con.close()
    forget_device = request.args.get('forget') == '1'
    logout_user(); session.clear()
    resp = make_response(redirect('/login'))
    if forget_device:
        resp.set_cookie('last_user', '', max_age=0, expires=0,
                        httponly=True,
                        secure=app.config.get('SESSION_COOKIE_SECURE', True),
                        samesite='Lax')
    return resp
