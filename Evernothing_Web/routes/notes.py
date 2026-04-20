"""Evernothing_Web/routes/notes.py — Note and folder CRUD routes."""
import datetime, json
from datetime import timezone
from flask import make_response, redirect, request, render_template_string
from flask_login import login_required, current_user
from markupsafe import escape

from Evernothing_Web.app import app, logger
from Evernothing_DB.database import get_db
from Evernothing_Security.security import encrypt, decrypt, allowed_file
from Evernothing_Connect.s3_sync import queue_change, sync_s3_async
from Evernothing_Web.routes.helpers import (
    _render, format_date, get_breadcrumbs, log_change)

import evernothing as _en


def _delete_recursive(cur, fid, uid):
    cur.execute('SELECT id FROM folders WHERE parent_id=? AND user_id=?', (fid, uid))
    for sub in cur.fetchall():
        _delete_recursive(cur, sub[0], uid)
    cur.execute('DELETE FROM notes WHERE folder_id=? AND user_id=?', (fid, uid))
    cur.execute('DELETE FROM folders WHERE id=? AND user_id=?', (fid, uid))


@app.route('/')
@login_required
def index():
    con = get_db(); cur = con.cursor()
    cur.execute('SELECT id,name FROM folders WHERE user_id=? AND parent_id IS NULL', (current_user.id,))
    folders = sorted([(r[0], decrypt(r[1])) for r in cur.fetchall()], key=lambda x: x[1].lower())
    cur.execute('SELECT id,note_key,updated_at FROM notes WHERE user_id=? ORDER BY updated_at DESC LIMIT 10', (current_user.id,))
    recent = [(r[0], decrypt(r[1]), format_date(r[2])) for r in cur.fetchall()]
    con.close()
    return _render(_en.T_FOLDERS, folders=folders, recent=recent)


@app.route('/folder/add', methods=['GET', 'POST'])
@login_required
def add_folder():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        if not name:
            return _render(_en.T_ADD_FOLDER, error='Folder name cannot be empty')
        con = get_db(); cur = con.cursor()
        try:
            cur.execute('INSERT INTO folders (user_id,name,parent_id) VALUES(?,?,NULL)',
                        (current_user.id, encrypt(name)))
            queue_change(cur, 'folder', cur.lastrowid, 'INSERT')
            con.commit(); sync_s3_async()
        except Exception as e:
            con.rollback(); logger.error(f'Error creating folder: {e}')
            return _render(_en.T_ADD_FOLDER, error='Failed to create folder')
        finally:
            con.close()
        return redirect('/')
    return _render(_en.T_ADD_FOLDER)


@app.route('/folder/<int:pid>/add_folder', methods=['GET', 'POST'])
@login_required
def add_subfolder(pid):
    if request.method == 'POST':
        con = get_db(); cur = con.cursor()
        cur.execute('INSERT INTO folders (user_id,name,parent_id) VALUES(?,?,?)',
                    (current_user.id, encrypt(request.form['name']), pid))
        queue_change(cur, 'folder', cur.lastrowid, 'INSERT')
        con.commit(); sync_s3_async(); con.close()
        return redirect(f'/folder/{pid}')
    return _render(_en.T_ADD_SUBFOLDER, pid=pid)


@app.route('/folder/delete/<int:fid>', methods=['GET', 'POST'])
@login_required
def delete_folder(fid):
    con = get_db(); cur = con.cursor()
    f = cur.execute('SELECT name,parent_id FROM folders WHERE id=? AND user_id=?',
                    (fid, current_user.id)).fetchone()
    if not f: con.close(); return redirect('/')
    if request.method == 'POST':
        _delete_recursive(cur, fid, current_user.id)
        queue_change(cur, 'folder', fid, 'DELETE')
        con.commit(); con.close(); sync_s3_async()
        return redirect(f'/folder/{f[1]}' if f[1] else '/')
    result = _render(_en.T_DELETE_FOLDER, f=(decrypt(f[0]), f[1]))
    con.close(); return result


@app.route('/folder/rename/<int:fid>', methods=['GET', 'POST'])
@login_required
def rename_folder(fid):
    con = get_db(); cur = con.cursor()
    f = cur.execute('SELECT name,parent_id FROM folders WHERE id=? AND user_id=?',
                    (fid, current_user.id)).fetchone()
    if not f: con.close(); return redirect('/')
    if request.method == 'POST':
        cur.execute('UPDATE folders SET name=? WHERE id=? AND user_id=?',
                    (encrypt(request.form['name']), fid, current_user.id))
        queue_change(cur, 'folder', fid, 'UPDATE')
        con.commit(); con.close(); sync_s3_async()
        return redirect(f'/folder/{fid}')
    con.close()
    return _render(_en.T_RENAME_FOLDER, f=(decrypt(f[0]), f[1]), fid=fid)


@app.route('/folder/<int:fid>')
@login_required
def view_folder(fid):
    con = get_db(); cur = con.cursor()
    folder = cur.execute('SELECT id,name,parent_id FROM folders WHERE id=? AND user_id=?',
                         (fid, current_user.id)).fetchone()
    if not folder: con.close(); return redirect('/')
    breadcrumb = [(folder[0], decrypt(folder[1]))]
    pid = folder[2]
    while pid:
        p = cur.execute('SELECT id,name,parent_id FROM folders WHERE id=? AND user_id=?',
                        (pid, current_user.id)).fetchone()
        if not p: break
        breadcrumb.insert(0, (p[0], decrypt(p[1]))); pid = p[2]
    cur.execute('SELECT id,name FROM folders WHERE user_id=? AND parent_id=?', (current_user.id, fid))
    subfolders = sorted([(r[0], decrypt(r[1])) for r in cur.fetchall()], key=lambda x: x[1].lower())
    cur.execute('SELECT id,note_key FROM notes WHERE user_id=? AND folder_id=?', (current_user.id, fid))
    notes = sorted([(r[0], decrypt(r[1])) for r in cur.fetchall()], key=lambda x: x[1].lower())
    con.close()
    return _render(_en.T_NOTES, notes=notes, subfolders=subfolders,
                   folder=(folder[0], decrypt(folder[1]), folder[2]), breadcrumb=breadcrumb)


@app.route('/add/<int:fid>', methods=['GET', 'POST'])
@login_required
def add(fid):
    error = note_val = content_val = desc_val = ''
    if request.method == 'POST':
        note_val    = str(escape(request.form['note']))
        content_val = str(escape(request.form['content']))
        desc_val    = request.form.get('description', '')[:255]
        if not note_val.strip() or not content_val.strip():
            error = 'Note and content cannot be empty'
        else:
            con = get_db(); cur = con.cursor()
            cur.execute('SELECT note_key FROM notes WHERE user_id=?', (current_user.id,))
            if any(decrypt(r[0]).strip().lower() == note_val.strip().lower() for r in cur.fetchall()):
                error = 'Note name already exists'; con.close()
            else:
                now = datetime.datetime.now(timezone.utc).isoformat()
                cur.execute('INSERT INTO notes (user_id,folder_id,note_key,note_value,description,updated_at) VALUES(?,?,?,?,?,?)',
                            (current_user.id, fid, encrypt(note_val), encrypt(content_val), encrypt(desc_val), now))
                nid = cur.lastrowid
                log_change(cur, current_user.id, 'CREATE', 'note', nid, {},
                           {'note': note_val, 'folder_id': fid}, request.remote_addr)
                cur.execute('INSERT INTO note_history (note_id,user_id,note_key,note_value,description,folder_id,updated_at) VALUES(?,?,?,?,?,?,?)',
                            (nid, current_user.id, encrypt(note_val), encrypt(content_val), encrypt(desc_val), fid, now))
                queue_change(cur, 'note', nid, 'INSERT')
                con.commit(); con.close(); sync_s3_async()
                return redirect(f'/folder/{fid}')
    return _render(_en.T_ADD, fid=fid, error=error, note=note_val, content=content_val, description=desc_val)


@app.route('/note/delete/<int:nid>', methods=['GET', 'POST'])
@login_required
def delete_note(nid):
    con = get_db(); cur = con.cursor()
    n = cur.execute('SELECT folder_id,note_key FROM notes WHERE id=? AND user_id=?',
                    (nid, current_user.id)).fetchone()
    if not n: con.close(); return redirect('/')
    if request.method == 'POST':
        cur.execute('DELETE FROM notes WHERE id=? AND user_id=?', (nid, current_user.id))
        queue_change(cur, 'note', nid, 'DELETE')
        con.commit(); con.close(); sync_s3_async()
        return redirect(f'/folder/{n[0]}' if n[0] else '/')
    con.close()
    return _render(_en.T_DELETE_NOTE, n=(n[0], decrypt(n[1])))


@app.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    con = get_db(); cur = con.cursor()
    folders = sorted([(f[0], decrypt(f[1])) for f in
                      cur.execute('SELECT id,name FROM folders WHERE user_id=?', (current_user.id,)).fetchall()],
                     key=lambda x: x[1].lower())
    row = cur.execute('SELECT note_key,note_value,folder_id,updated_at,description FROM notes WHERE id=? AND user_id=?',
                      (id, current_user.id)).fetchone()
    if not row: con.close(); return redirect('/')
    note = [decrypt(row[0]), decrypt(row[1]), row[2], format_date(row[3]), decrypt(row[4]) if row[4] else '']
    attachments = cur.execute('SELECT id,filename,file_size FROM attachments WHERE note_id=? AND user_id=?',
                              (id, current_user.id)).fetchall()
    if request.method == 'POST':
        if 'note' in request.form:
            new_desc = request.form.get('description', '')[:255]
            if (note[0] == request.form['note'] and note[1] == request.form['content']
                    and str(note[2]) == str(request.form.get('folder_id')) and note[4] == new_desc):
                con.close(); return redirect('/')
            if request.form.get('confirm') == 'yes':
                now = datetime.datetime.now(timezone.utc).isoformat()
                old = {'note': note[0], 'content': note[1], 'description': note[4], 'folder_id': note[2]}
                new = {'note': request.form['note'], 'content': request.form['content'],
                       'description': new_desc, 'folder_id': request.form.get('folder_id')}
                cur.execute('UPDATE notes SET note_key=?,note_value=?,description=?,folder_id=?,updated_at=? WHERE id=? AND user_id=?',
                            (encrypt(request.form['note']), encrypt(request.form['content']),
                             encrypt(new_desc), request.form.get('folder_id'), now, id, current_user.id))
                log_change(cur, current_user.id, 'UPDATE', 'note', id, old, new, request.remote_addr)
                cur.execute('INSERT INTO note_history (note_id,user_id,note_key,note_value,description,folder_id,updated_at) VALUES(?,?,?,?,?,?,?)',
                            (id, current_user.id, encrypt(request.form['note']), encrypt(request.form['content']),
                             encrypt(new_desc), request.form.get('folder_id'), now))
                queue_change(cur, 'note', id, 'UPDATE')
                con.commit(); con.close(); sync_s3_async()
                return redirect('/')
            else:
                con.close()
                return _render(_en.T_EDIT_CONFIRM,
                               note=[request.form['note'], request.form['content'],
                                     request.form.get('folder_id'), None, new_desc], id=id)
    breadcrumbs = get_breadcrumbs(cur, note[2], current_user.id)
    con.close()
    return _render(_en.T_EDIT, note=note, folders=folders, breadcrumbs=breadcrumbs, id=id, attachments=attachments)


@app.route('/history/<int:nid>')
@login_required
def history(nid):
    con = get_db(); cur = con.cursor()
    cur.execute('SELECT id,note_key,updated_at FROM note_history WHERE note_id=? AND user_id=? ORDER BY updated_at DESC',
                (nid, current_user.id))
    hist = [(h[0], decrypt(h[1]), format_date(h[2])) for h in cur.fetchall()]
    con.close()
    return _render(_en.T_HISTORY, history=hist, nid=nid)


@app.route('/history/restore/<int:hid>', methods=['GET', 'POST'])
@login_required
def restore_history(hid):
    con = get_db(); cur = con.cursor()
    h = cur.execute('SELECT note_id,note_key,note_value,folder_id FROM note_history WHERE id=? AND user_id=?',
                    (hid, current_user.id)).fetchone()
    if not h: con.close(); return redirect('/')
    if request.method == 'GET':
        key_preview = decrypt(h[1]); con.close()
        return render_template_string(
            _en.STYLE + """<nav class="nav"><span class="nav-brand">&#11088; EverNothing</span>
<a href=/history/{{nid}}>&#8592; Back</a></nav>
<div class="container"><div class="confirm-box"><h3>Confirm Rollback</h3>
<p>Restore note to version: <b>{{key}}</b>?</p>
<form method=post><input type=hidden name=csrf_token value="{{ csrf_token() }}">
<div class="btn-group"><button class="btn btn-primary">Yes, Restore</button>
<a href=/history/{{nid}} class="btn">Cancel</a></div></form></div></div>""",
            key=key_preview, nid=h[0])
    now = datetime.datetime.now(timezone.utc).isoformat()
    cur.execute('UPDATE notes SET note_key=?,note_value=?,folder_id=?,updated_at=? WHERE id=? AND user_id=?',
                (h[1], h[2], h[3], now, h[0], current_user.id))
    cur.execute('INSERT INTO note_history (note_id,user_id,note_key,note_value,folder_id,updated_at) VALUES(?,?,?,?,?,?)',
                (h[0], current_user.id, h[1], h[2], h[3], now))
    con.commit(); con.close(); sync_s3_async()
    return redirect(f'/edit/{h[0]}')


@app.route('/search')
@login_required
def search():
    import re as _re
    q = request.args.get('q', '').strip()
    folder_filter = request.args.get('folder', '')
    date_from = request.args.get('date_from', '')
    date_to   = request.args.get('date_to', '')
    use_regex = request.args.get('regex', '') == 'on'
    search_history = request.args.get('history', '') == 'on'
    if not q or len(q) > 100:
        return _render(_en.T_SEARCH, notes=[], q=q, folders=[], folder_filter=folder_filter, folder_results=[])
    con = get_db(); cur = con.cursor()
    try:
        cur.execute('SELECT id,name FROM folders WHERE user_id=?', (current_user.id,))
        folders = [(f[0], decrypt(f[1])) for f in cur.fetchall()]
        table = 'note_history' if search_history else 'notes'
        sql = f'SELECT id,note_key,note_value,updated_at,folder_id FROM {table} WHERE user_id=?'
        params = [current_user.id]
        if folder_filter: sql += ' AND folder_id=?'; params.append(folder_filter)
        if date_from:     sql += ' AND updated_at >= ?'; params.append(date_from)
        if date_to:       sql += ' AND updated_at <= ?'; params.append(date_to)
        cur.execute(sql, params)
        notes = []
        if use_regex:
            try:
                pat = _re.compile(q, _re.IGNORECASE)
                for r in cur.fetchall():
                    k, v = decrypt(r[1]), decrypt(r[2])
                    if pat.search(k) or pat.search(v): notes.append((r[0], k, format_date(r[3])))
            except _re.error: pass
        else:
            ql = q.lower()
            for r in cur.fetchall():
                k, v = decrypt(r[1]), decrypt(r[2])
                if ql in k.lower() or ql in v.lower(): notes.append((r[0], k, format_date(r[3])))
        folder_results = []
        if not search_history:
            cur.execute('SELECT id,name FROM folders WHERE user_id=?', (current_user.id,))
            if use_regex:
                try:
                    pat = _re.compile(q, _re.IGNORECASE)
                    folder_results = [(r[0], decrypt(r[1])) for r in cur.fetchall() if pat.search(decrypt(r[1]))]
                except _re.error: pass
            else:
                folder_results = [(r[0], decrypt(r[1])) for r in cur.fetchall() if q.lower() in decrypt(r[1]).lower()]
            folder_results.sort(key=lambda x: x[1].lower())
        notes.sort(key=lambda x: x[1].lower())
    except Exception as e:
        logger.error(f'Search error: {e}'); notes = folders = folder_results = []
    finally:
        con.close()
    return _render(_en.T_SEARCH, notes=notes, q=q, folders=folders, folder_results=folder_results,
                   folder_filter=folder_filter, date_from=date_from, date_to=date_to,
                   use_regex=use_regex, search_history=search_history)


@app.route('/export')
@login_required
def export_json():
    con = get_db(); cur = con.cursor()
    cur.execute('''SELECT n.note_key,n.note_value,n.updated_at,f.name,n.description
                   FROM notes n LEFT JOIN folders f ON n.folder_id=f.id WHERE n.user_id=?''',
                (current_user.id,))
    data = [{'note': decrypt(r[0]), 'content': decrypt(r[1]), 'description': decrypt(r[4]) if r[4] else '',
             'updated_at': r[2], 'folder': decrypt(r[3]) if r[3] else None} for r in cur.fetchall()]
    con.close()
    resp = make_response(json.dumps(data, indent=2))
    resp.headers['Content-Disposition'] = 'attachment; filename=notes.json'
    resp.headers['Content-Type'] = 'application/json'
    return resp


@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    error = None
    if request.method == 'POST':
        con = get_db(); cur = con.cursor()
        r = cur.execute('SELECT password FROM users WHERE id=?', (current_user.id,)).fetchone()
        from werkzeug.security import check_password_hash as _chk
        if r and _chk(r[0], request.form['old_password']):
            if request.form['new_password'] != request.form.get('verify_password', ''):
                error = 'New passwords do not match'
            else:
                cur.execute('UPDATE users SET password=? WHERE id=?',
                            (generate_password_hash(request.form['new_password']), current_user.id))
                con.commit(); con.close(); sync_s3_async()
                return redirect('/')
        else:
            error = 'Invalid old password'
        if error: con.close()
    return _render(_en.T_CHANGE_PASSWORD, error=error)


@app.route('/download/<int:aid>')
@login_required
def download_attachment(aid):
    con = get_db(); cur = con.cursor()
    a = cur.execute('SELECT filename,file_data FROM attachments WHERE id=? AND user_id=?',
                    (aid, current_user.id)).fetchone()
    con.close()
    if a:
        resp = make_response(a[1])
        resp.headers['Content-Disposition'] = f'attachment; filename={a[0]}'
        return resp
    return redirect('/')


@app.route('/delete_attachment/<int:aid>', methods=['POST'])
@login_required
def delete_attachment(aid):
    con = get_db(); cur = con.cursor()
    a = cur.execute('SELECT note_id,filename FROM attachments WHERE id=? AND user_id=?',
                    (aid, current_user.id)).fetchone()
    if a:
        log_change(cur, current_user.id, 'DELETE', 'attachment', aid,
                   {'note_id': a[0], 'filename': a[1]}, {}, request.remote_addr)
        cur.execute('DELETE FROM attachments WHERE id=? AND user_id=?', (aid, current_user.id))
        con.commit(); con.close(); sync_s3_async()
        return redirect(f'/edit/{a[0]}')
    con.close(); return redirect('/')
