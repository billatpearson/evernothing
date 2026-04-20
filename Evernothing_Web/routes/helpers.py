"""Shared helpers used across route modules."""
import datetime, json
from datetime import timezone
from flask import make_response, render_template_string, session
from flask_login import current_user
from Evernothing_Web.app import app, logger, BUILD_DATE
from Evernothing_DB.database import get_db
from Evernothing_Security.security import decrypt, encrypt
from Evernothing_Connect.s3_sync import queue_change, sync_s3_async, get_s3_status
from Evernothing_Connect.s3_sync import S3_BUCKET_NAME

_MIXED_ENCRYPTION_WARNING = False

def format_date(ts):
    if not ts: return ''
    try:
        dt = datetime.datetime.fromisoformat(ts)
        return dt.strftime('%m/%d/%Y %H:%M')
    except Exception:
        return ts

def get_breadcrumbs(cur, folder_id, user_id):
    crumbs = []
    fid = folder_id
    while fid:
        row = cur.execute('SELECT id,name,parent_id FROM folders WHERE id=? AND user_id=?', (fid, user_id)).fetchone()
        if not row: break
        crumbs.insert(0, (row[0], decrypt(row[1])))
        fid = row[2]
    return crumbs

def log_change(cur, user_id, action, entity_type, entity_id, old_vals, new_vals, ip):
    cur.execute(
        'INSERT INTO audit_log (user_id,action,entity_type,entity_id,old_values,new_values,timestamp,ip_address) VALUES(?,?,?,?,?,?,?,?)',
        (user_id, action, entity_type, entity_id,
         json.dumps(old_vals), json.dumps(new_vals),
         datetime.datetime.now(timezone.utc).isoformat(), ip))

def _get_style():
    from Evernothing_Theme.themes import get_style
    return get_style()

def _render(template, **kwargs):
    """Render a template string with theme, S3 status, and build_date injected."""
    # Import theme CSS from monolith during transition
    import evernothing as _en
    theme = session.get('theme', 'stellar')
    themed = template.replace(_en.STYLE_STELLAR, _get_style())
    kwargs.setdefault('theme', theme)
    kwargs.setdefault('build_date', BUILD_DATE)
    s3 = get_s3_status()
    kwargs.setdefault('s3_ok', s3['ok'])
    kwargs.setdefault('s3_error', s3['error'])
    if s3['ok'] is False:
        banner = ('<div style="background:#7f1d1d;color:#fca5a5;padding:8px 20px;'
                  'font-size:.85rem;text-align:center;position:sticky;top:0;z-index:999;">'
                  f'&#9888; S3 Sync unavailable — local DB only. Error: {s3["error"]}</div>')
        themed = themed.replace('<nav ', banner + '<nav ', 1)
    elif s3['ok'] is None and not S3_BUCKET_NAME:
        banner = ('<div style="background:#1e3a5f;color:#93c5fd;padding:8px 20px;'
                  'font-size:.85rem;text-align:center;position:sticky;top:0;z-index:999;">'
                  '&#8505; S3 sync not configured — set S3_BUCKET_NAME in .env.</div>')
        themed = themed.replace('<nav ', banner + '<nav ', 1)
    if _MIXED_ENCRYPTION_WARNING:
        enc_banner = ('<div style="background:#78350f;color:#fde68a;padding:8px 20px;'
                      'font-size:.85rem;text-align:center;position:sticky;top:0;z-index:998;">'
                      '&#9888; Mixed encryption state. Run: <code>python Scripts/migrate_encrypt.py</code></div>')
        themed = themed.replace('<nav ', enc_banner + '<nav ', 1)
    return render_template_string(themed, **kwargs)
