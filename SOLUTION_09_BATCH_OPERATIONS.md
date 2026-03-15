# Solution 9: Batch Operations

## Implementation Steps

### 1. Add Batch Selection UI to Templates

Update T_NOTES template to include checkboxes:

```python
T_NOTES = STYLE + """
<h3>Folder: {{folder[1]}}</h3>
<a href={% if folder[2] %}/folder/{{folder[2]}}{% else %}/{% endif %}>Back</a>
| <a href=/folder/delete/{{folder[0]}} style="color:red;font-size:small">[Delete Folder]</a>
| <a href=/folder/rename/{{folder[0]}} style="font-size:small">[Rename Folder]</a>
| <a href=/add/{{folder[0]}}>Add Note</a> | <a href=/logout>Logout</a>

<form method="post" action="/batch_action" id="batchForm">
<input type=hidden name=csrf_token value="{{ csrf_token() }}">
<input type=hidden name=folder_id value="{{folder[0]}}">
<select name="action" style="margin:10px 0;">
<option value="">-- Batch Action --</option>
<option value="delete">Delete Selected</option>
<option value="move">Move to Folder</option>
<option value="export">Export Selected</option>
</select>
<select name="target_folder" id="targetFolder" style="display:none;">
{% for f in all_folders %}
<option value="{{f[0]}}">{{f[1]}}</option>
{% endfor %}
</select>
<button type="submit">Apply</button>
<button type="button" onclick="selectAll()">Select All</button>
<button type="button" onclick="deselectAll()">Deselect All</button>

<h4>Notes</h4>
<ul>
{% for n in notes %}
<li>
<input type="checkbox" name="note_ids" value="{{n[0]}}" class="note-checkbox">
<a href=/edit/{{n[0]}}>{{n[1]}}</a> 
<a href=/note/delete/{{n[0]}} style="color:red;font-size:small">[x]</a>
</li>
{% else %}
<li>No notes.</li>
{% endfor %}
</ul>
</form>

<script>
document.querySelector('select[name="action"]').addEventListener('change', function() {
    document.getElementById('targetFolder').style.display = 
        this.value === 'move' ? 'inline' : 'none';
});
function selectAll() {
    document.querySelectorAll('.note-checkbox').forEach(cb => cb.checked = true);
}
function deselectAll() {
    document.querySelectorAll('.note-checkbox').forEach(cb => cb.checked = false);
}
</script>
"""
```

### 2. Add Batch Action Route

```python
@app.route("/batch_action", methods=["POST"])
@login_required
def batch_action():
    action = request.form.get('action')
    note_ids = request.form.getlist('note_ids')
    folder_id = request.form.get('folder_id')
    target_folder = request.form.get('target_folder')
    
    if not note_ids:
        return redirect(f"/folder/{folder_id}")
    
    con = db()
    cur = con.cursor()
    
    try:
        if action == 'delete':
            for nid in note_ids:
                cur.execute("DELETE FROM notes WHERE id=? AND user_id=?", (nid, current_user.id))
                log_change(cur, current_user.id, 'DELETE', 'note', nid, {}, {}, request.remote_addr)
        
        elif action == 'move':
            for nid in note_ids:
                old_folder = cur.execute("SELECT folder_id FROM notes WHERE id=?", (nid,)).fetchone()[0]
                cur.execute("UPDATE notes SET folder_id=? WHERE id=? AND user_id=?", 
                           (target_folder, nid, current_user.id))
                log_change(cur, current_user.id, 'UPDATE', 'note', nid, 
                          {'folder_id': old_folder}, {'folder_id': target_folder}, request.remote_addr)
        
        elif action == 'export':
            cur.execute(f"SELECT note_key, note_value FROM notes WHERE id IN ({','.join('?'*len(note_ids))}) AND user_id=?",
                       (*note_ids, current_user.id))
            data = [{'note': decrypt(r[0]), 'content': decrypt(r[1])} for r in cur.fetchall()]
            con.close()
            resp = make_response(json.dumps(data, indent=2))
            resp.headers['Content-Disposition'] = 'attachment; filename=batch_export.json'
            resp.headers['Content-Type'] = 'application/json'
            return resp
        
        con.commit()
        sync_s3()
    except Exception as e:
        logger.error(f"Batch action error: {e}")
        con.rollback()
    finally:
        con.close()
    
    return redirect(f"/folder/{folder_id}")
```

### 3. Update view_folder to pass all_folders

```python
@app.route("/folder/<int:fid>")
@login_required
def view_folder(fid):
    con = db()
    cur = con.cursor()
    # ... existing code ...
    
    # Get all folders for move dropdown
    cur.execute("SELECT id, name FROM folders WHERE user_id=?", (current_user.id,))
    all_folders = [(f[0], decrypt(f[1])) for f in cur.fetchall()]
    
    con.close()
    return render_template_string(T_NOTES, notes=notes, subfolders=subfolders, 
                                 folder=folder, all_folders=all_folders)
```
