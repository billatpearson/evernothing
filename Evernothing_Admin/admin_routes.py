"""Evernothing_Admin/admin_routes.py — All /admin/* routes."""
import datetime, json, os, sqlite3
from datetime import timezone
from flask import redirect, request, session
from flask_login import current_user
from werkzeug.security import generate_password_hash

from Evernothing_Web.app import app, logger
from Evernothing_DB.database import get_db
from Evernothing_Security.security import admin_required
from Evernothing_Connect.s3_sync import sync_s3_async, S3_BUCKET_NAME
from Evernothing_Web.routes.helpers import _render, format_date, log_change

import evernothing as _en


@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        from rate_limiter import check_rate_limit, RATE_LIMIT_LOGIN
        from Evernothing_Security.admin_auth import verify_admin
        if not check_rate_limit(request.remote_addr, 'admin', RATE_LIMIT_LOGIN):
            logger.warning(f'Rate limit exceeded for admin login from {request.remote_addr}')
            return _render(_en.T_ADMIN_LOGIN, error='Too many attempts. Please try again later.')
        if verify_admin(request.form.get('username', ''), request.form.get('password', '')):
            session['admin_logged_in'] = True
            session['admin_login_time'] = datetime.datetime.now(timezone.utc).isoformat()
            con = get_db(); cur = con.cursor()
            log_change(cur, 0, 'CREATE', 'admin_session', 0, {},
                       {'admin': os.environ.get('ADMIN_USER') or 'admin',
                        'ip': request.remote_addr}, request.remote_addr)
            con.commit(); con.close()
            return redirect('/admin/dashboard')
        return _render(_en.T_ADMIN_LOGIN, error='Invalid credentials')
    timeout = request.args.get('timeout')
    return _render(_en.T_ADMIN_LOGIN,
                   error='Admin session expired. Please log in again.' if timeout else None)


@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    q = request.args.get('q', '')
    con = get_db(); cur = con.cursor()
    cur.execute('''SELECT u.id,u.username,COUNT(DISTINCT n.id),COUNT(DISTINCT f.id),u.last_login
                   FROM users u
                   LEFT JOIN notes n ON u.id=n.user_id
                   LEFT JOIN folders f ON u.id=f.user_id
                   WHERE u.username LIKE ? GROUP BY u.id ORDER BY u.username''', (f'%{q}%',))
    users = [(r[0], r[1], r[2], r[3], format_date(r[4]) if r[4] else 'Never')
             for r in cur.fetchall()]
    con.close()
    return _render(_en.T_ADMIN_DASHBOARD, users=users, q=q)


@app.route('/admin/user/<int:uid>', methods=['GET', 'POST'])
@admin_required
def admin_edit_user(uid):
    con = get_db(); cur = con.cursor()
    user = cur.execute('SELECT id,username,last_login FROM users WHERE id=?', (uid,)).fetchone()
    if not user: con.close(); return redirect('/admin/dashboard')
    if request.method == 'POST':
        new_name = request.form.get('new_username')
        new_pass = request.form.get('new_password')
        new_ll   = request.form.get('last_login')
        if request.form.get('confirm') == 'yes':
            try:
                old = {'username': user[1], 'last_login': user[2]}
                new = {'username': new_name, 'last_login': new_ll}
                if new_pass: new['password'] = '***changed***'
                cur.execute('UPDATE users SET username=?,last_login=? WHERE id=?', (new_name, new_ll, uid))
                if new_pass:
                    cur.execute('UPDATE users SET password=? WHERE id=?',
                                (generate_password_hash(new_pass), uid))
                log_change(cur, 0, 'UPDATE', 'user', uid, old, new, request.remote_addr)
                con.commit(); con.close(); sync_s3_async()
                return redirect('/admin/dashboard')
            except sqlite3.IntegrityError:
                con.close()
                return _render(_en.T_ADMIN_EDIT_USER, user=user, error='Username already exists')
        else:
            con.close()
            return _render(_en.T_ADMIN_EDIT_USER_CONFIRM, user=user,
                           new_name=new_name, new_pass=new_pass, new_last_login=new_ll)
    con.close()
    return _render(_en.T_ADMIN_EDIT_USER, user=user)


@app.route('/admin/user/delete/<int:uid>', methods=['GET', 'POST'])
@admin_required
def admin_delete_user(uid):
    con = get_db(); cur = con.cursor()
    user = cur.execute('SELECT id,username FROM users WHERE id=?', (uid,)).fetchone()
    if not user: con.close(); return redirect('/admin/dashboard')
    if request.method == 'POST':
        cur.execute('DELETE FROM notes WHERE user_id=?', (uid,))
        cur.execute('DELETE FROM folders WHERE user_id=?', (uid,))
        cur.execute('DELETE FROM note_history WHERE user_id=?', (uid,))
        log_change(cur, 0, 'DELETE', 'user', uid, {'username': user[1]}, {}, request.remote_addr)
        cur.execute('DELETE FROM users WHERE id=?', (uid,))
        con.commit(); con.close(); sync_s3_async()
        return redirect('/admin/dashboard')
    con.close()
    return _render(_en.T_ADMIN_DELETE_USER, user=user)


@app.route('/admin/sessions')
@admin_required
def admin_sessions():
    con = get_db(); cur = con.cursor()
    cur.execute('''SELECT u.username,s.session_id,s.login_time,s.logout_time,s.ip_address,s.user_agent
                   FROM user_sessions s JOIN users u ON s.user_id=u.id
                   ORDER BY s.login_time DESC LIMIT 200''')
    sessions = [{'username': r[0], 'session_id': r[1],
                 'login_time': format_date(r[2]),
                 'logout_time': format_date(r[3]) if r[3] else 'Active',
                 'ip': r[4], 'user_agent': (r[5] or '')[:50]}
                for r in cur.fetchall()]
    con.close()
    return _render(_en.T_ADMIN_SESSIONS, sessions=sessions)


@app.route('/admin/audit_logs')
@admin_required
def admin_audit_logs():
    user_filter   = request.args.get('user', '')
    action_filter = request.args.get('action', '')
    entity_filter = request.args.get('entity', '')
    limit = int(request.args.get('limit', 100))
    con = get_db(); cur = con.cursor()
    sql = '''SELECT a.id,u.username,a.action,a.entity_type,a.entity_id,
                    a.old_values,a.new_values,a.timestamp,a.ip_address
             FROM audit_log a LEFT JOIN users u ON a.user_id=u.id WHERE 1=1'''
    params = []
    if user_filter:   sql += ' AND u.username LIKE ?'; params.append(f'%{user_filter}%')
    if action_filter: sql += ' AND a.action=?';        params.append(action_filter)
    if entity_filter: sql += ' AND a.entity_type=?';   params.append(entity_filter)
    sql += ' ORDER BY a.timestamp DESC LIMIT ?'; params.append(limit)
    cur.execute(sql, params)
    logs = [{'id': r[0], 'user': r[1] or 'System', 'action': r[2],
             'entity': f'{r[3]} #{r[4]}',
             'old': json.loads(r[5]) if r[5] else {},
             'new': json.loads(r[6]) if r[6] else {},
             'timestamp': format_date(r[7]), 'ip': r[8]}
            for r in cur.fetchall()]
    con.close()
    return _render(_en.T_ADMIN_AUDIT_LOGS, logs=logs,
                   user_filter=user_filter, action_filter=action_filter,
                   entity_filter=entity_filter, limit=limit)


@app.route('/admin/iam_policy')
@admin_required
def admin_iam_policy():
    from Evernothing_Connect.s3_sync import S3_BUCKET_NAME as _bucket
    policy = json.dumps(_en.get_iam_policy(), indent=2)
    return _render(_en.STYLE + '''
<nav class="nav"><span class="nav-brand">&#11088; Admin</span>
<a href=/admin/dashboard>&#8592; Dashboard</a></nav>
<div class="container"><h3>Least-Privilege IAM Policy</h3>
<div class="card"><pre style="white-space:pre-wrap;font-size:.85rem">{{ policy }}</pre></div>
</div>''', policy=policy, bucket=_bucket)


@app.route('/admin/s3_backups')
@admin_required
def admin_s3_backups():
    backups = []
    try:
        import boto3 as _b3
        from Evernothing_Connect.s3_sync import _s3_client
        s3 = _s3_client()
        resp = s3.list_objects_v2(Bucket=S3_BUCKET_NAME, Prefix='backups/')
        for obj in resp.get('Contents', []):
            backups.append({'key': obj['Key'], 'size': obj['Size'],
                            'modified': obj['LastModified'].strftime('%m/%d/%Y %H:%M')})
        backups.sort(key=lambda x: x['modified'], reverse=True)
    except Exception as e:
        logger.error(f'Failed to list S3 backups: {e}')
    return _render(_en.T_ADMIN_S3_BACKUPS, backups=backups)
