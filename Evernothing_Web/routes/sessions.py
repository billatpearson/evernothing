"""Evernothing_Web/routes/sessions.py — Session management, theme, audit."""
import datetime
from datetime import timezone
from flask import redirect, request, session
from flask_login import login_required, current_user

from Evernothing_Web.app import app
from Evernothing_DB.database import get_db
from Evernothing_Web.routes.helpers import _render, format_date, log_change

import evernothing as _en


@app.route('/set_theme')
def set_theme():
    t = request.args.get('t', '')
    if t in ('stellar', 'unicorn', 'startrek', 'shrek', 'lotr'):
        session['theme'] = t
    else:
        cycle = {'stellar': 'unicorn', 'unicorn': 'startrek',
                 'startrek': 'shrek', 'shrek': 'lotr', 'lotr': 'stellar'}
        session['theme'] = cycle.get(session.get('theme', 'stellar'), 'stellar')
    return redirect(request.referrer or '/')


@app.route('/sessions')
@login_required
def view_sessions():
    con = get_db(); cur = con.cursor()
    cur.execute('''SELECT session_id,login_time,logout_time,ip_address,user_agent
                   FROM user_sessions WHERE user_id=? ORDER BY login_time DESC LIMIT 20''',
                (current_user.id,))
    sessions = [{'session_id': r[0], 'login_time': format_date(r[1]),
                 'logout_time': format_date(r[2]) if r[2] else 'Active',
                 'ip': r[3], 'user_agent': (r[4] or '')[:60]}
                for r in cur.fetchall()]
    con.close()
    return _render(_en.T_SESSIONS, sessions=sessions)


@app.route('/session/revoke/<session_id>')
@login_required
def revoke_session(session_id):
    con = get_db(); cur = con.cursor()
    cur.execute('UPDATE user_sessions SET logout_time=? WHERE session_id=? AND user_id=?',
                (datetime.datetime.now(timezone.utc).isoformat(), session_id, current_user.id))
    con.commit(); con.close()
    return redirect('/sessions')


@app.route('/audit_report')
@login_required
def audit_report():
    import json
    con = get_db(); cur = con.cursor()
    cur.execute('''SELECT a.id,u.username,a.action,a.entity_type,a.entity_id,
                          a.old_values,a.new_values,a.timestamp,a.ip_address
                   FROM audit_log a LEFT JOIN users u ON a.user_id=u.id
                   WHERE a.user_id=? ORDER BY a.timestamp DESC LIMIT 100''',
                (current_user.id,))
    logs = [{'id': r[0], 'user': r[1], 'action': r[2],
             'entity': f'{r[3]} #{r[4]}',
             'old': json.loads(r[5]) if r[5] else {},
             'new': json.loads(r[6]) if r[6] else {},
             'timestamp': format_date(r[7]), 'ip': r[8]}
            for r in cur.fetchall()]
    con.close()
    return _render(_en.T_AUDIT_REPORT, logs=logs)
