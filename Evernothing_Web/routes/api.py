"""Evernothing_Web/routes/api.py — REST API routes for mobile/Android client."""
import datetime, os
from datetime import timezone
from flask import jsonify, request, session
from flask_login import login_required, login_user, logout_user, current_user
from werkzeug.security import check_password_hash

from Evernothing_Web.app import app, csrf
from Evernothing_DB.database import get_db
from Evernothing_Security.security import encrypt, decrypt, User, api_login_required
from Evernothing_Connect.s3_sync import sync_s3_async, queue_change
from Evernothing_Web.routes.helpers import format_date, log_change


def _delete_recursive(cur, fid, uid):
    cur.execute('SELECT id FROM folders WHERE parent_id=? AND user_id=?', (fid, uid))
    for sub in cur.fetchall():
        _delete_recursive(cur, sub[0], uid)
    cur.execute('DELETE FROM notes WHERE folder_id=? AND user_id=?', (fid, uid))
    cur.execute('DELETE FROM folders WHERE id=? AND user_id=?', (fid, uid))


@app.route('/api/login', methods=['POST'])
@csrf.exempt
def api_login():
    data = request.get_json()
    if not data: return jsonify({'error': 'Invalid request'}), 400
    con = get_db(); cur = con.cursor()
    r = cur.execute('SELECT id,password FROM users WHERE username=?',
                    (data.get('username', ''),)).fetchone()
    if r and check_password_hash(r[1], data.get('password', '')):
        sid = os.urandom(16).hex()
        now = datetime.datetime.now(timezone.utc).isoformat()
        session.update({'session_id': sid, 'last_activity': now,
                        'remember_me': False})
        session.permanent = True
        cur.execute('UPDATE users SET last_login=? WHERE id=?', (now, r[0]))
        cur.execute('INSERT INTO user_sessions (user_id,session_id,login_time,ip_address,user_agent) VALUES(?,?,?,?,?)',
                    (r[0], sid, now, request.remote_addr, request.user_agent.string))
        con.commit(); con.close()
        login_user(User(r[0], data['username']))
        return jsonify({'ok': True, 'username': data['username']})
    con.close()
    return jsonify({'error': 'Invalid username or password'}), 401


@app.route('/api/logout', methods=['POST'])
@csrf.exempt
def api_logout():
    if 'session_id' in session:
        con = get_db(); cur = con.cursor()
        cur.execute('UPDATE user_sessions SET logout_time=? WHERE session_id=?',
                    (datetime.datetime.now(timezone.utc).isoformat(), session['session_id']))
        con.commit(); con.close()
    logout_user(); session.clear()
    return jsonify({'ok': True})


@app.route('/api/folders')
@api_login_required
def api_folders():
    con = get_db(); cur = con.cursor()
    cur.execute('SELECT id,name,parent_id FROM folders WHERE user_id=? ORDER BY name',
                (current_user.id,))
    folders = [{'id': r[0], 'name': decrypt(r[1]), 'parent_id': r[2]}
               for r in cur.fetchall()]
    con.close(); return jsonify(folders)


@app.route('/api/folders', methods=['POST'])
@csrf.exempt
@api_login_required
def api_create_folder():
    data = request.get_json() or {}
    name = data.get('name', '').strip()
    if not name: return jsonify({'error': 'Name required'}), 400
    con = get_db(); cur = con.cursor()
    cur.execute('INSERT INTO folders (user_id,name,parent_id) VALUES(?,?,?)',
                (current_user.id, encrypt(name), data.get('parent_id')))
    fid = cur.lastrowid; con.commit(); con.close(); sync_s3_async()
    return jsonify({'ok': True, 'id': fid})


@app.route('/api/folders/<int:fid>', methods=['DELETE'])
@csrf.exempt
@api_login_required
def api_delete_folder(fid):
    con = get_db(); cur = con.cursor()
    _delete_recursive(cur, fid, current_user.id)
    con.commit(); con.close(); sync_s3_async()
    return jsonify({'ok': True})


@app.route('/api/folders/<int:fid>/notes')
@api_login_required
def api_folder_notes(fid):
    con = get_db(); cur = con.cursor()
    cur.execute('SELECT id,note_key,description,updated_at FROM notes WHERE user_id=? AND folder_id=? ORDER BY note_key',
                (current_user.id, fid))
    notes = [{'id': r[0], 'key': decrypt(r[1]),
              'description': decrypt(r[2]) if r[2] else '',
              'updated_at': format_date(r[3])} for r in cur.fetchall()]
    con.close(); return jsonify(notes)


@app.route('/api/notes/<int:nid>')
@api_login_required
def api_get_note(nid):
    con = get_db(); cur = con.cursor()
    r = cur.execute('SELECT id,note_key,note_value,description,folder_id,updated_at FROM notes WHERE id=? AND user_id=?',
                    (nid, current_user.id)).fetchone()
    con.close()
    if not r: return jsonify({'error': 'Not found'}), 404
    return jsonify({'id': r[0], 'key': decrypt(r[1]), 'value': decrypt(r[2]),
                    'description': decrypt(r[3]) if r[3] else '',
                    'folder_id': r[4], 'updated_at': format_date(r[5])})


@app.route('/api/notes', methods=['POST'])
@csrf.exempt
@api_login_required
def api_create_note():
    data = request.get_json() or {}
    key = data.get('key', '').strip(); value = data.get('value', '').strip()
    if not key or not value: return jsonify({'error': 'Key and value required'}), 400
    con = get_db(); cur = con.cursor()
    cur.execute('SELECT note_key FROM notes WHERE user_id=?', (current_user.id,))
    if any(decrypt(r[0]).strip().lower() == key.lower() for r in cur.fetchall()):
        con.close(); return jsonify({'error': 'Note name already exists'}), 409
    now = datetime.datetime.now(timezone.utc).isoformat()
    fid = data.get('folder_id'); desc = data.get('description', '')[:255]
    cur.execute('INSERT INTO notes (user_id,folder_id,note_key,note_value,description,updated_at) VALUES(?,?,?,?,?,?)',
                (current_user.id, fid, encrypt(key), encrypt(value), encrypt(desc), now))
    nid = cur.lastrowid
    cur.execute('INSERT INTO note_history (note_id,user_id,note_key,note_value,description,folder_id,updated_at) VALUES(?,?,?,?,?,?,?)',
                (nid, current_user.id, encrypt(key), encrypt(value), encrypt(desc), fid, now))
    log_change(cur, current_user.id, 'CREATE', 'note', nid, {}, {'key': key, 'folder_id': fid}, request.remote_addr)
    con.commit(); con.close(); sync_s3_async()
    return jsonify({'ok': True, 'id': nid})


@app.route('/api/notes/<int:nid>', methods=['PUT'])
@csrf.exempt
@api_login_required
def api_update_note(nid):
    data = request.get_json() or {}
    key = data.get('key', '').strip(); value = data.get('value', '').strip()
    if not key or not value: return jsonify({'error': 'Key and value required'}), 400
    con = get_db(); cur = con.cursor()
    now = datetime.datetime.now(timezone.utc).isoformat()
    fid = data.get('folder_id'); desc = data.get('description', '')[:255]
    cur.execute('UPDATE notes SET note_key=?,note_value=?,description=?,folder_id=?,updated_at=? WHERE id=? AND user_id=?',
                (encrypt(key), encrypt(value), encrypt(desc), fid, now, nid, current_user.id))
    cur.execute('INSERT INTO note_history (note_id,user_id,note_key,note_value,description,folder_id,updated_at) VALUES(?,?,?,?,?,?,?)',
                (nid, current_user.id, encrypt(key), encrypt(value), encrypt(desc), fid, now))
    log_change(cur, current_user.id, 'UPDATE', 'note', nid, {}, {'key': key, 'folder_id': fid}, request.remote_addr)
    con.commit(); con.close(); sync_s3_async()
    return jsonify({'ok': True})


@app.route('/api/notes/<int:nid>', methods=['DELETE'])
@csrf.exempt
@api_login_required
def api_delete_note(nid):
    con = get_db(); cur = con.cursor()
    cur.execute('DELETE FROM notes WHERE id=? AND user_id=?', (nid, current_user.id))
    con.commit(); con.close(); sync_s3_async()
    return jsonify({'ok': True})


@app.route('/api/search')
@api_login_required
def api_search():
    q = request.args.get('q', '').strip().lower()
    if not q: return jsonify([])
    con = get_db(); cur = con.cursor()
    cur.execute('SELECT id,note_key,note_value,updated_at FROM notes WHERE user_id=?',
                (current_user.id,))
    results = []
    for r in cur.fetchall():
        k, v = decrypt(r[1]), decrypt(r[2])
        if q in k.lower() or q in v.lower():
            results.append({'id': r[0], 'key': k, 'updated_at': format_date(r[3])})
    con.close()
    return jsonify(sorted(results, key=lambda x: x['key'].lower()))
