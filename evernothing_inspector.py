"""
EverNothing S3 Inspector
Standalone read-only web app for browsing S3 bucket contents.

Usage:
    python evernothing_inspector.py

Access:
    http://127.0.0.1:5001

Configuration (env vars or .env):
    S3_BUCKET_NAME, AWS_REGION, AWS_PROFILE, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY
"""

try:
    import os as _os
    from dotenv import load_dotenv
    load_dotenv(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '.env'))
except ImportError:
    pass

from flask import Flask, request, redirect, render_template_string, send_file
import os, json, datetime, io

try:
    import boto3
except ImportError:
    boto3 = None

try:
    from aws_config import S3_BUCKET_NAME, AWS_REGION, AWS_PROFILE
except ImportError:
    S3_BUCKET_NAME = os.environ.get('S3_BUCKET_NAME', 'evernothing-backup-2026')
    AWS_REGION     = os.environ.get('AWS_REGION', 'us-east-1')
    AWS_PROFILE    = os.environ.get('AWS_PROFILE', 'billspeiser2')

AWS_ACCESS_KEY_ID     = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')

app = Flask('EverNothingInspector')
app.secret_key = os.urandom(24).hex()

BUILD_DATE = datetime.datetime.now().strftime("%m/%d/%y:%H:%M")

@app.context_processor
def inject_build_date():
    return dict(build_date=BUILD_DATE)

# --- S3 ---
def _s3():
    if not boto3:
        return None
    try:
        if AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY:
            return boto3.client('s3', region_name=AWS_REGION,
                aws_access_key_id=AWS_ACCESS_KEY_ID,
                aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
        if AWS_PROFILE:
            try:
                return boto3.Session(profile_name=AWS_PROFILE).client('s3')
            except Exception:
                pass
        return boto3.client('s3', region_name=AWS_REGION)
    except Exception:
        return None

def list_objects(prefix=''):
    s3 = _s3()
    if not s3:
        return [], "boto3 not available"
    try:
        paginator = s3.get_paginator('list_objects_v2')
        items = []
        for page in paginator.paginate(Bucket=S3_BUCKET_NAME, Prefix=prefix):
            for obj in page.get('Contents', []):
                items.append({
                    'key':          obj['Key'],
                    'size':         obj['Size'],
                    'modified':     obj['LastModified'].strftime('%m/%d/%Y %H:%M'),
                    'modified_raw': obj['LastModified'].isoformat(),
                })
        return items, None
    except Exception as e:
        return [], str(e)

def get_object_bytes(key):
    s3 = _s3()
    if not s3:
        return None, "boto3 not available"
    try:
        resp = s3.get_object(Bucket=S3_BUCKET_NAME, Key=key)
        return resp['Body'].read(), None
    except Exception as e:
        return None, str(e)

# --- Style ---
STYLE = """
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
:root {
  --gold: #ffd700; --gold-dim: #b8960c; --red: #cc2200; --red-bright: #ff3300;
  --bg: #0a0a0a; --bg2: #111; --bg3: #1a1a1a; --border: #2a2a2a; --radius: 6px;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body { background: var(--bg); color: var(--gold); font-family: 'Segoe UI', system-ui, sans-serif; min-height: 100vh; padding-bottom: 40px; }
a { color: var(--gold); text-decoration: none; transition: color .15s; }
a:hover { color: var(--red-bright); }
.nav { background: var(--bg2); border-bottom: 1px solid var(--red); padding: 10px 20px; display: flex; align-items: center; gap: 6px; flex-wrap: wrap; position: sticky; top: 0; z-index: 100; }
.nav-brand { font-size: 1.1rem; font-weight: 700; color: var(--gold); letter-spacing: 1px; margin-right: 10px; }
.nav a { font-size: .85rem; padding: 4px 10px; border-radius: var(--radius); border: 1px solid transparent; }
.nav a:hover { border-color: var(--red); color: var(--red-bright); }
.tab.active { border-color: var(--red) !important; color: var(--gold) !important; background: var(--bg3); }
.container { max-width: 1200px; margin: 0 auto; padding: 24px 20px; }
h3 { color: var(--gold); margin-bottom: 16px; font-weight: 600; }
.card { background: var(--bg2); border: 1px solid var(--border); border-radius: var(--radius); padding: 20px; margin-bottom: 16px; }
table { width: 100%; border-collapse: collapse; font-size: .9rem; }
th { text-align: left; padding: 10px 12px; border-bottom: 2px solid var(--red); color: var(--gold-dim); font-size: .8rem; text-transform: uppercase; letter-spacing: .5px; }
td { padding: 9px 12px; border-bottom: 1px solid var(--border); vertical-align: top; }
tr:hover td { background: var(--bg3); }
.btn { display: inline-flex; align-items: center; gap: 6px; padding: 6px 16px; border-radius: var(--radius); border: 1px solid var(--gold-dim); background: transparent; color: var(--gold); font-size: .85rem; cursor: pointer; text-decoration: none; transition: all .15s; }
.btn:hover { background: var(--gold-dim); color: #000; }
.btn-sm { padding: 3px 10px; font-size: .78rem; }
err { display: block; color: var(--red-bright); background: #1a0000; border: 1px solid var(--red); border-radius: var(--radius); padding: 8px 12px; margin: 10px 0; font-size: .9rem; }
.timestamp { font-size: .8rem; color: #666; }
.tag-insert { color: #0c0; } .tag-update { color: var(--gold-dim); } .tag-delete { color: var(--red); }
pre { background: var(--bg3); border: 1px solid var(--border); border-radius: var(--radius); padding: 16px; font-size: .8rem; overflow-x: auto; white-space: pre-wrap; word-break: break-all; color: var(--gold); }
.footer { position: fixed; bottom: 0; left: 0; width: 100%; background: var(--bg2); border-top: 1px solid var(--border); color: #555; text-align: center; font-size: .75rem; padding: 5px; z-index: 99; }
.info { color: #888; font-size: .85rem; margin-bottom: 12px; }
</style>
<div class="footer">{{ build_date }}</div>
"""

NAV = """
<nav class="nav">
  <span class="nav-brand">&#128269; S3 Inspector</span>
  <a href=/inspector/backups class="tab {b}">&#128190; Backups</a>
  <a href=/inspector/deltas class="tab {d}">&#9889; Deltas</a>
</nav>
"""

T_BACKUPS = STYLE + NAV.format(b='active', d='') + """
<div class="container">
  <h3>Full Database Backups</h3>
  <p class="info">Bucket: <b>{{bucket}}</b> &nbsp;|&nbsp; {{backups|length}} backup(s)</p>
  {% if error %}<err>{{error}}</err>{% endif %}
  <table>
    <tr><th>Key</th><th>Size</th><th>Last Modified</th><th>Actions</th></tr>
    {% for b in backups %}
    <tr>
      <td style="font-size:.82rem;font-family:monospace">{{b.key}}</td>
      <td class="timestamp">{{'{:,}'.format(b.size)}} bytes</td>
      <td class="timestamp">{{b.modified}}</td>
      <td><a href="/inspector/download?key={{b.key|urlencode}}" class="btn btn-sm">&#11123; Download</a></td>
    </tr>
    {% else %}
    <tr><td colspan=4 style="color:#555;padding:20px">No backups found.</td></tr>
    {% endfor %}
  </table>
</div>
"""

T_DELTAS = STYLE + NAV.format(b='', d='active') + """
<div class="container">
  <h3>Delta Change Files</h3>
  <p class="info">Bucket: <b>{{bucket}}</b> &nbsp;|&nbsp; {{deltas|length}} delta file(s)</p>
  {% if error %}<err>{{error}}</err>{% endif %}
  <table>
    <tr><th>Device</th><th>Timestamp</th><th>Size</th><th>Actions</th></tr>
    {% for d in deltas %}
    <tr>
      <td style="font-size:.85rem">{{d.device}}</td>
      <td class="timestamp">{{d.modified}}</td>
      <td class="timestamp">{{'{:,}'.format(d.size)}} bytes</td>
      <td style="display:flex;gap:6px">
        <a href="/inspector/delta?key={{d.key|urlencode}}" class="btn btn-sm">&#128269; Inspect</a>
        <a href="/inspector/download?key={{d.key|urlencode}}" class="btn btn-sm">&#11123; Download</a>
      </td>
    </tr>
    {% else %}
    <tr><td colspan=4 style="color:#555;padding:20px">No delta files found.</td></tr>
    {% endfor %}
  </table>
</div>
"""

T_DELTA_VIEW = STYLE + NAV.format(b='', d='active') + """
<div class="container">
  <h3>Delta: <span style="font-family:monospace;font-size:.9rem;color:var(--gold-dim)">{{key}}</span></h3>
  <div style="margin-bottom:16px">
    <a href=/inspector/deltas class="btn btn-sm">&#8592; Back</a>
    <a href="/inspector/download?key={{key|urlencode}}" class="btn btn-sm" style="margin-left:8px">&#11123; Download</a>
  </div>
  {% if error %}<err>{{error}}</err>{% endif %}
  {% if changes %}
  <p class="info">{{changes|length}} change record(s)</p>
  <table>
    <tr><th>#</th><th>Operation</th><th>Entity</th><th>ID</th><th>Timestamp</th><th>Payload</th></tr>
    {% for c in changes %}
    <tr>
      <td class="timestamp">{{loop.index}}</td>
      <td><span class="tag-{{c.op|lower}}">{{c.op}}</span></td>
      <td>{{c.entity}}</td>
      <td class="timestamp">{{c.id}}</td>
      <td class="timestamp">{{c.at}}</td>
      <td>
        <details>
          <summary style="cursor:pointer;color:var(--gold-dim);font-size:.8rem">View payload</summary>
          <pre>{{c.data_pretty}}</pre>
        </details>
      </td>
    </tr>
    {% endfor %}
  </table>
  {% endif %}
</div>
"""

# --- Routes ---
@app.route('/')
@app.route('/inspector')
def inspector_root():
    return redirect('/inspector/backups')

@app.route('/inspector/backups')
def inspector_backups():
    items, error = list_objects('')
    backups = sorted(
        [i for i in items if i['key'] == 'evernothing.db' or i['key'].startswith('backups/')],
        key=lambda x: x['modified_raw'], reverse=True
    )
    return render_template_string(T_BACKUPS, backups=backups, error=error, bucket=S3_BUCKET_NAME)

@app.route('/inspector/deltas')
def inspector_deltas():
    items, error = list_objects('changes/')
    deltas = sorted(items, key=lambda x: x['modified_raw'], reverse=True)
    for d in deltas:
        parts = d['key'].split('/')
        d['device'] = parts[1] if len(parts) >= 3 else '?'
    return render_template_string(T_DELTAS, deltas=deltas, error=error, bucket=S3_BUCKET_NAME)

@app.route('/inspector/delta')
def inspector_delta():
    key = request.args.get('key', '')
    if not key:
        return redirect('/inspector/deltas')
    data, error = get_object_bytes(key)
    changes = []
    if data and not error:
        try:
            raw = json.loads(data.decode('utf-8'))
            for c in raw:
                c['data_pretty'] = json.dumps(c.get('data', {}), indent=2)
            changes = raw
        except Exception as e:
            error = f"Failed to parse delta: {e}"
    return render_template_string(T_DELTA_VIEW, key=key, changes=changes, error=error)

@app.route('/inspector/download')
def inspector_download():
    key = request.args.get('key', '')
    if not key:
        return redirect('/inspector/backups')
    data, error = get_object_bytes(key)
    if error or not data:
        return f"Download failed: {error}", 500
    filename = key.split('/')[-1]
    return send_file(
        io.BytesIO(data),
        as_attachment=True,
        download_name=filename,
        mimetype='application/octet-stream'
    )

if __name__ == '__main__':
    if not boto3:
        print("WARNING: boto3 not installed. S3 features will not work.")
    print(f"S3 Inspector running at http://127.0.0.1:5001")
    print(f"Bucket: {S3_BUCKET_NAME}")
    app.run(host='0.0.0.0', port=5001, debug=False)
