"""
Evernothing_UI/templates.py
All HTML template strings and CSS theme constants.
Extracted from evernothing.py as part of separation-of-concerns refactor.

Import with:
    from Evernothing_UI.templates import T_LOGIN, T_FOLDERS, STYLE_STELLAR, ...
"""
# STYLE is an alias for STYLE_STELLAR used by templates
# It is set after STYLE_STELLAR is defined below.


# L1863 in evernothing.py
STYLE_UNICORN = """
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800&display=swap');
:root {
  --rose:    #ff6eb4;
  --violet:  #c084fc;
  --sky:     #67e8f9;
  --mint:    #6ee7b7;
  --sun:     #fde68a;
  --peach:   #fdba74;
  --danger:  #f87171;
  --bg:      #1a0a2e;
  --bg2:     #2d1b4e;
  --bg3:     #3d2560;
  --border:  #6b3fa0;
  --text:    #f0e6ff;
  --radius:  14px;
  --rainbow: linear-gradient(90deg,#ff6eb4,#c084fc,#67e8f9,#6ee7b7,#fde68a,#fdba74,#ff6eb4);
}
* { box-sizing: border-box; margin: 0; padding: 0; }
html { font-size: 17px; }
body {
  background: var(--bg);
  background-image: radial-gradient(ellipse at 20% 20%, #3b1f6a 0%, transparent 60%),
                    radial-gradient(ellipse at 80% 80%, #1a3a5c 0%, transparent 60%);
  color: var(--text);
  font-family: 'Nunito', 'Segoe UI', system-ui, sans-serif;
  min-height: 100vh;
  padding-bottom: 44px;
}
a { color: var(--rose); text-decoration: none; transition: color .15s; }
a:hover { color: var(--sky); }
body::before {
  content: '';
  display: block;
  height: 3px;
  background: var(--rainbow);
  background-size: 200% 100%;
  animation: shimmer 4s linear infinite;
  position: fixed; top: 0; left: 0; width: 100%; z-index: 200;
}
@keyframes shimmer { 0%{background-position:0% 0%} 100%{background-position:200% 0%} }
@keyframes bounce { 0%,100%{transform:translateY(0)} 50%{transform:translateY(-6px)} }
@keyframes spin { from{transform:rotate(0deg)} to{transform:rotate(360deg)} }
.nav {
  background: linear-gradient(135deg, #2d1b4e 0%, #1e1040 100%);
  border-bottom: 2px solid transparent;
  border-image: var(--rainbow) 1;
  padding: 10px 20px;
  display: flex; align-items: center; gap: 6px; flex-wrap: wrap;
  position: sticky; top: 3px; z-index: 100;
}
.nav-brand {
  font-size: 1.15rem; font-weight: 800;
  background: var(--rainbow); background-size: 200% 100%;
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  background-clip: text; animation: shimmer 4s linear infinite;
  letter-spacing: 1px; margin-right: 10px;
  display: flex; align-items: center; gap: 6px;
}
.unicorn-img { width:28px;height:28px;display:inline-block;animation:bounce 2s ease-in-out infinite;filter:drop-shadow(0 0 6px var(--rose)); }
.sparkle-img { width:18px;height:18px;display:inline-block;animation:spin 3s linear infinite;filter:drop-shadow(0 0 4px var(--sun)); }
.page-unicorn { display:block;margin:0 auto 16px;width:72px;height:72px;filter:drop-shadow(0 0 12px var(--rose));animation:bounce 2s ease-in-out infinite; }
.nav a { font-size:.85rem;padding:4px 12px;border-radius:20px;border:1px solid transparent;color:var(--violet);transition:all .15s; }
.nav a:hover { background:var(--bg3);border-color:var(--violet);color:var(--sky);text-decoration:none; }
.nav .sep { color:var(--border); }
.nav .nav-logout { margin-left:auto;color:var(--danger);border-color:var(--danger);border-radius:20px;border:1px solid;padding:4px 12px; }
.nav .nav-logout:hover { background:var(--danger);color:#fff; }
.theme-select { background:var(--bg3);color:var(--violet);border:1px solid var(--border);border-radius:20px;padding:3px 8px;font-size:.8rem;cursor:pointer;font-family:inherit; }
.theme-select:focus { outline:none;border-color:var(--rose); }
.container { max-width:1100px;margin:0;padding:24px 20px; }
h2,h3 { color:var(--sun);margin-bottom:16px;font-weight:700;letter-spacing:.5px; }
h4 { color:var(--violet);margin:20px 0 10px;font-size:.9rem;text-transform:uppercase;letter-spacing:1.5px; }
.card { background:var(--bg2);border:1px solid var(--border);border-radius:var(--radius);padding:20px;margin-bottom:16px;box-shadow:0 4px 24px rgba(192,132,252,.08); }
.item-list { list-style:none; }
.item-list li { display:flex;align-items:center;gap:8px;padding:5px 12px;margin-bottom:2px;border-radius:10px;border:1px solid transparent;transition:all .15s; }
.item-list li:hover { background:var(--bg3);border-color:var(--border); }
.item-list li a { flex:1;font-size:.95rem;color:var(--mint); }
.item-list li a:hover { color:var(--sky); }
.item-list .actions { display:flex;gap:6px;opacity:0;transition:opacity .15s; }
.item-list li:hover .actions { opacity:1; }
.item-list .actions a { font-size:.75rem;padding:2px 8px;border-radius:10px;border:1px solid var(--border);flex:none;color:var(--violet); }
.item-list .actions a:hover { border-color:var(--rose);color:var(--rose); }
.item-list .del { color:var(--danger)!important; }
.empty { color:var(--border);font-style:italic;padding:12px; }
label { display:block;font-size:.85rem;color:var(--violet);margin-bottom:4px;margin-top:12px; }
input[type=text],input[type=password],input[type=email],input[type=date],input:not([type]),textarea,select { background:var(--bg3);color:var(--text);border:1px solid var(--border);border-radius:10px;padding:8px 14px;font-size:.9rem;font-family:inherit;width:100%;transition:border-color .15s,box-shadow .15s;outline:none; }
input:focus,textarea:focus,select:focus { border-color:var(--rose);box-shadow:0 0 0 3px rgba(255,110,180,.15); }
textarea { resize:vertical;font-family:'Consolas','Courier New',monospace;font-size:.85rem; }
select option { background:var(--bg2); }
.form-row { display:flex;gap:12px;flex-wrap:wrap; }
.form-row > * { flex:1;min-width:200px; }
.btn { display:inline-flex;align-items:center;gap:6px;padding:8px 22px;border-radius:20px;border:1px solid var(--violet);background:transparent;color:var(--violet);font-size:.9rem;font-family:inherit;font-weight:600;cursor:pointer;transition:all .15s;text-decoration:none; }
.btn:hover { background:var(--bg3);border-color:var(--sky);color:var(--sky);text-decoration:none; }
.btn-primary { background:linear-gradient(135deg,var(--rose),var(--violet));color:#fff;border:none;font-weight:700; }
.btn-primary:hover { background:linear-gradient(135deg,var(--violet),var(--sky));color:#fff; }
.btn-danger { border-color:var(--danger);color:var(--danger); }
.btn-danger:hover { background:var(--danger);color:#fff;border-color:var(--danger); }
.btn-sm { padding:4px 14px;font-size:.8rem; }
.btn-group { display:flex;gap:10px;margin-top:20px;flex-wrap:wrap;align-items:center; }
err { display:block;color:var(--danger);background:rgba(248,113,113,.1);border:1px solid var(--danger);border-radius:10px;padding:8px 14px;margin:10px 0;font-size:.9rem; }
.breadcrumb { font-size:.85rem;color:var(--border);margin-bottom:16px;display:flex;align-items:center;gap:6px;flex-wrap:wrap; }
.breadcrumb a { color:var(--violet); }
.breadcrumb a:hover { color:var(--rose); }
.breadcrumb .sep { color:var(--border); }
.badge { font-size:.75rem;background:var(--bg3);border:1px solid var(--border);border-radius:10px;padding:1px 8px;color:var(--violet); }
.timestamp { font-size:.8rem;color:var(--border); }
table { width:100%;border-collapse:collapse;font-size:.9rem; }
th { text-align:left;padding:10px 12px;border-bottom:2px solid var(--violet);color:var(--violet);font-size:.8rem;text-transform:uppercase;letter-spacing:.5px; }
td { padding:5px 12px;vertical-align:top;border-bottom:1px solid var(--bg3); }
tr:hover td { background:var(--bg3); }
.search-box { display:flex;gap:8px;margin-bottom:20px; }
.search-box input { flex:1; }
.tag-create { color:var(--mint);font-weight:700; }
.tag-update { color:var(--sun);font-weight:700; }
.tag-delete { color:var(--danger);font-weight:700; }
.footer { position:fixed;bottom:0;left:0;width:100%;background:var(--bg2);border-top:2px solid transparent;border-image:var(--rainbow) 1;color:var(--border);text-align:center;font-size:.75rem;padding:5px;z-index:99; }
.two-col { display:grid;grid-template-columns:1fr 1fr;gap:20px; }
@media (max-width:600px) { .two-col{grid-template-columns:1fr} .nav{gap:4px} textarea{cols:unset;width:100%} }
.confirm-box { background:var(--bg2);border:1px solid var(--rose);border-radius:var(--radius);padding:24px;max-width:600px;box-shadow:0 4px 32px rgba(255,110,180,.12); }
.confirm-box p { margin-bottom:12px;line-height:1.6; }
.confirm-box .field { margin:8px 0;font-size:.9rem; }
.confirm-box .field b { color:var(--sun); }
</style>
<div class="footer">&#x1F984; built on {{ build_date }}</div>
"""

# L1991 in evernothing.py
STYLE_STELLAR = """
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;600;700&family=Exo+2:wght@300;400;600&display=swap');
:root {
  --star:      #e8f4fd;
  --nebula:    #7eb8f7;
  --pulsar:    #00d4ff;
  --aurora:    #39ff8f;
  --supernova: #ff6b35;
  --danger:    #ff3d3d;
  --bg:        #020510;
  --bg2:       #060d1f;
  --bg3:       #0d1a35;
  --border:    #1a3060;
  --radius:    8px;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
html { font-size: 16px; }
body {
  background: #00010a;
  /* Andromeda galaxy — real photograph */
  background-image:
    /* Dark overlay so UI text stays readable */
    linear-gradient(rgba(0,1,10,.55), rgba(0,1,10,.55)),
    url('/static/andromeda.jpg');
  background-size: cover;
  background-position: center center;
  background-attachment: fixed;
  background-repeat: no-repeat;
  color: var(--star);
  font-family: 'Exo 2', 'Segoe UI', system-ui, sans-serif;
  min-height: 100vh;
  padding-bottom: 40px;
  position: relative;
}
body::before {
  content: '';
  position: fixed;
  inset: 0;
  background-image:
    radial-gradient(1px 1px at 10% 15%, rgba(255,255,255,.7) 0%, transparent 100%),
    radial-gradient(1px 1px at 25% 40%, rgba(200,210,255,.5) 0%, transparent 100%),
    radial-gradient(1px 1px at 40%  8%, rgba(255,255,255,.6) 0%, transparent 100%),
    radial-gradient(1px 1px at 55% 60%, rgba(180,210,255,.5) 0%, transparent 100%),
    radial-gradient(1px 1px at 70% 25%, rgba(255,255,255,.7) 0%, transparent 100%),
    radial-gradient(1px 1px at 85% 75%, rgba(200,210,255,.5) 0%, transparent 100%),
    radial-gradient(1px 1px at 15% 80%, rgba(255,255,255,.6) 0%, transparent 100%),
    radial-gradient(1px 1px at 90% 45%, rgba(180,210,255,.5) 0%, transparent 100%),
    radial-gradient(1px 1px at 35% 90%, rgba(255,255,255,.6) 0%, transparent 100%),
    radial-gradient(1px 1px at 65%  5%, rgba(200,210,255,.5) 0%, transparent 100%),
    radial-gradient(1.5px 1.5px at 48% 35%, rgba(126,184,247,.8) 0%, transparent 100%),
    radial-gradient(1.5px 1.5px at 78% 88%, rgba(126,184,247,.7) 0%, transparent 100%),
    radial-gradient(1px 1px at  5% 55%, rgba(255,255,255,.6) 0%, transparent 100%),
    radial-gradient(1px 1px at 92% 12%, rgba(255,255,255,.7) 0%, transparent 100%),
    radial-gradient(1px 1px at 30% 70%, rgba(180,210,255,.5) 0%, transparent 100%);
  pointer-events: none;
  z-index: 0;
  animation: twinkle 8s ease-in-out infinite alternate;
}
@keyframes twinkle { 0% { opacity:.5; } 50% { opacity:.9; } 100% { opacity:.6; } }
body > * { position: relative; z-index: 1; }
a { color: var(--nebula); text-decoration: none; transition: color .2s; }
a:hover { color: var(--pulsar); text-shadow: 0 0 8px var(--pulsar); }
.nav {
  background: linear-gradient(135deg, #060d1f 0%, #0a1628 100%);
  border-bottom: 1px solid var(--pulsar);
  box-shadow: 0 2px 20px rgba(0,212,255,.15);
  padding: 10px 20px;
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
  position: sticky;
  top: 0;
  z-index: 100;
}
.nav-brand {
  font-family: 'Orbitron', monospace;
  font-size: 1rem;
  font-weight: 700;
  color: var(--pulsar);
  letter-spacing: 2px;
  margin-right: 10px;
  text-shadow: 0 0 12px var(--pulsar);
}
.nav a {
  font-size: .82rem;
  padding: 4px 10px;
  border-radius: 20px;
  border: 1px solid transparent;
  color: var(--nebula);
  transition: all .2s;
}
.nav a:hover { border-color: var(--pulsar); color: var(--pulsar); background: rgba(0,212,255,.08); text-shadow: 0 0 6px var(--pulsar); text-decoration: none; }
.nav .sep { color: var(--border); }
.nav .nav-logout { margin-left: auto; color: var(--supernova); border-color: var(--supernova); border-radius: 20px; border: 1px solid; padding: 4px 12px; }
.nav .nav-logout:hover { background: var(--supernova); color: #000; text-shadow: none; }
.container { max-width: 1100px; margin: 0; padding: 24px 20px; }
h2, h3 { font-family: 'Orbitron', monospace; color: var(--pulsar); margin-bottom: 16px; font-weight: 600; letter-spacing: 1px; text-shadow: 0 0 10px rgba(0,212,255,.4); }
h4 { color: var(--nebula); margin: 20px 0 10px; font-size: .9rem; text-transform: uppercase; letter-spacing: 2px; }
.card {
  background: linear-gradient(135deg, var(--bg2) 0%, var(--bg3) 100%);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 20px;
  margin-bottom: 16px;
  box-shadow: 0 4px 24px rgba(0,212,255,.06);
}
.item-list { list-style: none; }
.item-list li {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 5px 12px;
  margin-bottom: 2px;
  border-radius: var(--radius);
  border: 1px solid transparent;
  transition: all .2s;
}
.item-list li:hover { background: rgba(0,212,255,.06); border-color: var(--border); box-shadow: inset 0 0 12px rgba(0,212,255,.04); }
.item-list li a { flex: 1; font-size: .95rem; color: var(--aurora); }
.item-list li a:hover { color: var(--pulsar); text-shadow: 0 0 6px var(--pulsar); }
.item-list .actions { display: flex; gap: 6px; opacity: 0; transition: opacity .15s; }
.item-list li:hover .actions { opacity: 1; }
.item-list .actions a { font-size: .75rem; padding: 2px 8px; border-radius: 12px; border: 1px solid var(--border); flex: none; color: var(--nebula); }
.item-list .actions a:hover { border-color: var(--pulsar); color: var(--pulsar); }
.item-list .del { color: var(--danger) !important; }
.empty { color: #3a5080; font-style: italic; padding: 12px; }
label { display: block; font-size: .85rem; color: var(--nebula); margin-bottom: 4px; margin-top: 12px; }
input[type=text], input[type=password], input[type=email], input[type=date], input:not([type]), textarea, select {
  background: var(--bg3);
  color: var(--star);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 8px 12px;
  font-size: .9rem;
  font-family: inherit;
  width: 100%;
  transition: border-color .2s, box-shadow .2s;
  outline: none;
}
input:focus, textarea:focus, select:focus {
  border-color: var(--pulsar);
  box-shadow: 0 0 0 3px rgba(0,212,255,.15);
}
textarea { resize: vertical; font-family: 'Consolas', 'Courier New', monospace; font-size: .85rem; }
select option { background: var(--bg2); }
.form-row { display: flex; gap: 12px; flex-wrap: wrap; }
.form-row > * { flex: 1; min-width: 200px; }
.btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 22px;
  border-radius: 20px;
  border: 1px solid var(--nebula);
  background: transparent;
  color: var(--nebula);
  font-size: .9rem;
  font-family: inherit;
  cursor: pointer;
  transition: all .2s;
  text-decoration: none;
  letter-spacing: .5px;
}
.btn:hover { background: rgba(126,184,247,.12); border-color: var(--pulsar); color: var(--pulsar); box-shadow: 0 0 14px rgba(0,212,255,.25); text-decoration: none; text-shadow: 0 0 6px var(--pulsar); }
.btn-primary {
  background: linear-gradient(135deg, #003d6b 0%, #005a9e 100%);
  color: var(--pulsar);
  border-color: var(--pulsar);
  font-weight: 600;
  box-shadow: 0 0 10px rgba(0,212,255,.2);
}
.btn-primary:hover { background: linear-gradient(135deg, #005a9e 0%, #0078d4 100%); box-shadow: 0 0 20px rgba(0,212,255,.4); color: #fff; }
.btn-danger { border-color: var(--danger); color: var(--danger); }
.btn-danger:hover { background: var(--danger); color: #fff; box-shadow: 0 0 14px rgba(255,61,61,.35); text-shadow: none; }
.btn-sm { padding: 4px 14px; font-size: .8rem; }
.btn-group { display: flex; gap: 10px; margin-top: 20px; flex-wrap: wrap; align-items: center; }
err { display: block; color: var(--danger); background: rgba(255,61,61,.08); border: 1px solid var(--danger); border-radius: var(--radius); padding: 8px 12px; margin: 10px 0; font-size: .9rem; }
.breadcrumb { font-size: .85rem; color: #3a5080; margin-bottom: 16px; display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }
.breadcrumb a { color: var(--nebula); }
.breadcrumb a:hover { color: var(--pulsar); }
.breadcrumb .sep { color: var(--border); }
.badge { font-size: .75rem; background: var(--bg3); border: 1px solid var(--border); border-radius: 10px; padding: 1px 8px; color: var(--nebula); }
.timestamp { font-size: .8rem; color: #3a5080; }
table { width: 100%; border-collapse: collapse; font-size: .9rem; }
th { text-align: left; padding: 10px 12px; border-bottom: 1px solid var(--pulsar); color: var(--nebula); font-size: .8rem; text-transform: uppercase; letter-spacing: 1px; }
td { padding: 6px 12px; vertical-align: top; border-bottom: 1px solid var(--bg3); }
tr:hover td { background: rgba(0,212,255,.04); }
.search-box { display: flex; gap: 8px; margin-bottom: 20px; }
.search-box input { flex: 1; }
.tag-create { color: var(--aurora); font-weight: 600; }
.tag-update { color: var(--nebula); font-weight: 600; }
.tag-delete { color: var(--danger); font-weight: 600; }
.footer {
  position: fixed; bottom: 0; left: 0; width: 100%;
  background: var(--bg2);
  border-top: 1px solid var(--border);
  color: #3a5080; text-align: center; font-size: .75rem; padding: 5px;
  z-index: 99;
  font-family: 'Orbitron', monospace;
  letter-spacing: 1px;
}
.two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
@media (max-width: 600px) {
  .two-col { grid-template-columns: 1fr; }
  .nav { gap: 4px; }
  textarea { cols: unset; width: 100%; }
}
.confirm-box {
  background: linear-gradient(135deg, var(--bg2) 0%, var(--bg3) 100%);
  border: 1px solid var(--supernova);
  border-radius: var(--radius);
  padding: 24px;
  max-width: 600px;
  box-shadow: 0 4px 24px rgba(255,107,53,.12);
}
.confirm-box p { margin-bottom: 12px; line-height: 1.6; }
.confirm-box .field { margin: 8px 0; font-size: .9rem; }
.confirm-box .field b { color: var(--aurora); }
.nav .theme-btn { color: var(--nebula); border: 1px solid var(--nebula); padding: 3px 9px; border-radius: 12px; font-size: .8rem; }
.nav .theme-btn:hover { background: rgba(0,212,255,.12); border-color: var(--pulsar); color: var(--pulsar); }
.theme-select { background:var(--bg3);color:var(--nebula);border:1px solid var(--border);border-radius:20px;padding:3px 8px;font-size:.8rem;cursor:pointer;font-family:inherit; }
.theme-select:focus { outline:none;border-color:var(--pulsar); }</style>
<div class="footer">&#11088; {{ build_date }} &#11088;</div>
"""

# L2219 in evernothing.py
STYLE_STARTREK = """
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
@import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@400;600;700&family=Share+Tech+Mono&display=swap');
:root {
  --lcars-gold:   #ff9900;
  --lcars-blue:   #9999ff;
  --lcars-red:    #cc4444;
  --lcars-teal:   #66cccc;
  --lcars-purple: #cc88ff;
  --text:         #e8e8ff;
  --bg:           #000008;
  --bg2:          rgba(0,0,20,.75);
  --bg3:          rgba(0,0,40,.80);
  --border:       #334466;
  --radius:       4px;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
html { font-size: 16px; }
body {
  background: #000008;
  background-image:
    linear-gradient(rgba(0,0,8,.60), rgba(0,0,8,.60)),
    url('/static/startrek.jpg');
  background-size: cover;
  background-position: center center;
  background-attachment: fixed;
  background-repeat: no-repeat;
  color: var(--text);
  font-family: 'Rajdhani', 'Segoe UI', system-ui, sans-serif;
  min-height: 100vh;
  padding-bottom: 40px;
}
a { color: var(--lcars-blue); text-decoration: none; transition: color .2s; }
a:hover { color: var(--lcars-gold); text-shadow: 0 0 8px var(--lcars-gold); }
/* LCARS-style top bar */
body::before {
  content: '';
  display: block;
  height: 3px;
  background: linear-gradient(90deg, var(--lcars-red) 0%, var(--lcars-gold) 30%, var(--lcars-blue) 60%, var(--lcars-teal) 100%);
  position: fixed; top: 0; left: 0; width: 100%; z-index: 200;
}
.nav {
  background: rgba(0,0,20,.88);
  border-bottom: 2px solid var(--lcars-gold);
  padding: 10px 20px;
  display: flex; align-items: center; gap: 6px; flex-wrap: wrap;
  position: sticky; top: 3px; z-index: 100;
  font-family: 'Share Tech Mono', monospace;
}
.nav-brand {
  font-size: 1rem; font-weight: 700; letter-spacing: 3px;
  color: var(--lcars-gold); text-shadow: 0 0 10px var(--lcars-gold);
  margin-right: 10px; text-transform: uppercase;
}
.nav a { font-size:.82rem;padding:4px 10px;border-radius:2px;border:1px solid transparent;color:var(--lcars-blue);transition:all .2s;letter-spacing:.5px; }
.nav a:hover { border-color:var(--lcars-gold);color:var(--lcars-gold);background:rgba(255,153,0,.08);text-shadow:0 0 6px var(--lcars-gold);text-decoration:none; }
.nav .sep { color: var(--border); }
.nav .nav-logout { margin-left:auto;color:var(--lcars-red);border-color:var(--lcars-red);border-radius:2px;border:1px solid;padding:4px 12px; }
.nav .nav-logout:hover { background:var(--lcars-red);color:#fff;text-shadow:none; }
.container { max-width:1100px;margin:0;padding:24px 20px; }
h2,h3 { font-family:'Share Tech Mono',monospace;color:var(--lcars-gold);margin-bottom:16px;font-weight:600;letter-spacing:2px;text-transform:uppercase;text-shadow:0 0 10px rgba(255,153,0,.4); }
h4 { color:var(--lcars-teal);margin:20px 0 10px;font-size:.9rem;text-transform:uppercase;letter-spacing:2px; }
.card { background:var(--bg2);border:1px solid var(--lcars-gold);border-left:4px solid var(--lcars-gold);border-radius:var(--radius);padding:20px;margin-bottom:16px;box-shadow:0 4px 24px rgba(255,153,0,.08); }
.item-list { list-style:none; }
.item-list li { display:flex;align-items:center;gap:8px;padding:5px 12px;margin-bottom:2px;border-radius:var(--radius);border:1px solid transparent;transition:all .2s; }
.item-list li:hover { background:rgba(255,153,0,.06);border-color:var(--border); }
.item-list li a { flex:1;font-size:.95rem;color:var(--lcars-teal); }
.item-list li a:hover { color:var(--lcars-gold);text-shadow:0 0 6px var(--lcars-gold); }
.item-list .actions { display:flex;gap:6px;opacity:0;transition:opacity .15s; }
.item-list li:hover .actions { opacity:1; }
.item-list .actions a { font-size:.75rem;padding:2px 8px;border-radius:2px;border:1px solid var(--border);flex:none;color:var(--lcars-blue); }
.item-list .actions a:hover { border-color:var(--lcars-gold);color:var(--lcars-gold); }
.item-list .del { color:var(--lcars-red)!important; }
.empty { color:var(--border);font-style:italic;padding:12px; }
label { display:block;font-size:.85rem;color:var(--lcars-teal);margin-bottom:4px;margin-top:12px;letter-spacing:.5px;text-transform:uppercase; }
input[type=text],input[type=password],input[type=email],input[type=date],input:not([type]),textarea,select { background:var(--bg3);color:var(--text);border:1px solid var(--border);border-radius:var(--radius);padding:8px 12px;font-size:.9rem;font-family:inherit;width:100%;transition:border-color .2s,box-shadow .2s;outline:none; }
input:focus,textarea:focus,select:focus { border-color:var(--lcars-gold);box-shadow:0 0 0 3px rgba(255,153,0,.15); }
textarea { resize:vertical;font-family:'Share Tech Mono',monospace;font-size:.85rem; }
select option { background:var(--bg); }
.form-row { display:flex;gap:12px;flex-wrap:wrap; }
.form-row > * { flex:1;min-width:200px; }
.btn { display:inline-flex;align-items:center;gap:6px;padding:8px 22px;border-radius:2px;border:1px solid var(--lcars-blue);background:transparent;color:var(--lcars-blue);font-size:.9rem;font-family:inherit;cursor:pointer;transition:all .2s;text-decoration:none;letter-spacing:1px;text-transform:uppercase; }
.btn:hover { background:rgba(153,153,255,.12);border-color:var(--lcars-gold);color:var(--lcars-gold);box-shadow:0 0 14px rgba(255,153,0,.25);text-decoration:none;text-shadow:0 0 6px var(--lcars-gold); }
.btn-primary { background:rgba(255,153,0,.15);color:var(--lcars-gold);border-color:var(--lcars-gold);font-weight:600;box-shadow:0 0 10px rgba(255,153,0,.2); }
.btn-primary:hover { background:rgba(255,153,0,.28);box-shadow:0 0 20px rgba(255,153,0,.4);color:#fff; }
.btn-danger { border-color:var(--lcars-red);color:var(--lcars-red); }
.btn-danger:hover { background:var(--lcars-red);color:#fff;box-shadow:0 0 14px rgba(204,68,68,.35);text-shadow:none; }
.btn-sm { padding:4px 14px;font-size:.8rem; }
.btn-group { display:flex;gap:10px;margin-top:20px;flex-wrap:wrap;align-items:center; }
err { display:block;color:var(--lcars-red);background:rgba(204,68,68,.08);border:1px solid var(--lcars-red);border-radius:var(--radius);padding:8px 12px;margin:10px 0;font-size:.9rem; }
.breadcrumb { font-size:.85rem;color:var(--border);margin-bottom:16px;display:flex;align-items:center;gap:6px;flex-wrap:wrap; }
.breadcrumb a { color:var(--lcars-blue); }
.breadcrumb a:hover { color:var(--lcars-gold); }
.breadcrumb .sep { color:var(--border); }
.badge { font-size:.75rem;background:var(--bg3);border:1px solid var(--border);border-radius:2px;padding:1px 8px;color:var(--lcars-teal); }
.timestamp { font-size:.8rem;color:var(--border); }
table { width:100%;border-collapse:collapse;font-size:.9rem; }
th { text-align:left;padding:10px 12px;border-bottom:1px solid var(--lcars-gold);color:var(--lcars-teal);font-size:.8rem;text-transform:uppercase;letter-spacing:1px;font-family:'Share Tech Mono',monospace; }
td { padding:6px 12px;vertical-align:top;border-bottom:1px solid var(--bg3); }
tr:hover td { background:rgba(255,153,0,.04); }
.search-box { display:flex;gap:8px;margin-bottom:20px; }
.search-box input { flex:1; }
.tag-create { color:var(--lcars-teal);font-weight:600; }
.tag-update { color:var(--lcars-blue);font-weight:600; }
.tag-delete { color:var(--lcars-red);font-weight:600; }
.footer { position:fixed;bottom:0;left:0;width:100%;background:rgba(0,0,20,.90);border-top:1px solid var(--lcars-gold);color:var(--lcars-gold);text-align:center;font-size:.75rem;padding:5px;z-index:99;font-family:'Share Tech Mono',monospace;letter-spacing:2px; }
.two-col { display:grid;grid-template-columns:1fr 1fr;gap:20px; }
@media (max-width:600px) { .two-col { grid-template-columns:1fr; } .nav { gap:4px; } textarea { width:100%; } }
.confirm-box { background:var(--bg2);border:1px solid var(--lcars-gold);border-radius:var(--radius);padding:24px;max-width:600px;box-shadow:0 4px 24px rgba(255,153,0,.12); }
.confirm-box p { margin-bottom:12px;line-height:1.6; }
.confirm-box .field { margin:8px 0;font-size:.9rem; }
.confirm-box .field b { color:var(--lcars-teal); }
.theme-select { background:var(--bg3);color:var(--lcars-blue);border:1px solid var(--border);border-radius:2px;padding:3px 8px;font-size:.8rem;cursor:pointer;font-family:inherit; }
.theme-select:focus { outline:none;border-color:var(--lcars-gold); }</style>
<div class="footer">&#9650; {{ build_date }} &#9650;</div>
"""

# L2339 in evernothing.py
STYLE = STYLE_STELLAR

# L2341 in evernothing.py
STYLE_LOTR = """
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
@import url('https://fonts.googleapis.com/css2?family=IM+Fell+English:ital@0;1&family=Cinzel+Decorative:wght@400;700&family=Uncial+Antiqua&display=swap');
:root {
  --gold:     #c9a84c;
  --gold2:    #e8c97a;
  --silver:   #a8b8c8;
  --shadow:   #1a0a00;
  --ember:    #8b2500;
  --mithril:  #d4e0ec;
  --shire:    #4a7c3f;
  --danger:   #8b0000;
  --bg:       #0a0500;
  --bg2:      #120a02;
  --bg3:      #1a1005;
  --border:   #3a2a10;
  --radius:   2px;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
html { font-size: 16px; }
body {
  background: var(--bg);
  background-image:
    linear-gradient(rgba(10,5,0,.65), rgba(10,5,0,.65)),
    url('/static/lotr.jpg');
  background-size: cover;
  background-position: center center;
  background-attachment: fixed;
  background-repeat: no-repeat;
  color: var(--mithril);
  font-family: 'IM Fell English', Georgia, serif;
  min-height: 100vh;
  padding-bottom: 40px;
}
a { color: var(--gold); text-decoration: none; transition: color .2s; }
a:hover { color: var(--gold2); text-shadow: 0 0 8px rgba(201,168,76,.6); }
.nav {
  background: linear-gradient(135deg, rgba(10,5,0,.95) 0%, rgba(26,16,5,.95) 100%);
  border-bottom: 2px solid var(--gold);
  box-shadow: 0 2px 20px rgba(201,168,76,.2);
  padding: 10px 20px;
  display: flex; align-items: center; gap: 6px; flex-wrap: wrap;
  position: sticky; top: 0; z-index: 100;
}
.nav-brand {
  font-family: 'Cinzel Decorative', serif;
  font-size: .9rem; font-weight: 700;
  color: var(--gold);
  text-shadow: 0 0 14px rgba(201,168,76,.7), 0 2px 4px rgba(0,0,0,.9);
  letter-spacing: 2px; margin-right: 10px;
}
.nav a { font-size:.82rem;padding:4px 10px;border-radius:1px;border:1px solid transparent;color:var(--silver);transition:all .2s;font-family:'IM Fell English',serif; }
.nav a:hover { border-color:var(--gold);color:var(--gold);background:rgba(201,168,76,.08);text-shadow:0 0 6px rgba(201,168,76,.4);text-decoration:none; }
.nav .sep { color:var(--border); }
.nav .nav-logout { margin-left:auto;color:var(--danger);border-color:var(--danger);border-radius:1px;border:1px solid;padding:4px 12px; }
.nav .nav-logout:hover { background:var(--danger);color:var(--mithril);text-shadow:none; }
.container { max-width:1100px;margin:0;padding:24px 20px; }
h2,h3 { font-family:'Cinzel Decorative',serif;color:var(--gold);margin-bottom:16px;font-weight:700;letter-spacing:1px;text-shadow:0 0 12px rgba(201,168,76,.4); }
h4 { color:var(--silver);margin:20px 0 10px;font-size:.85rem;text-transform:uppercase;letter-spacing:2px;font-family:'Cinzel Decorative',serif; }
.card {
  background: linear-gradient(135deg, rgba(18,10,2,.88) 0%, rgba(26,16,5,.88) 100%);
  border: 1px solid var(--border);
  border-top: 2px solid var(--gold);
  border-radius: var(--radius);
  padding: 20px; margin-bottom: 16px;
  box-shadow: 0 4px 24px rgba(0,0,0,.6), inset 0 1px 0 rgba(201,168,76,.1);
}
.item-list { list-style:none; }
.item-list li { display:flex;align-items:center;gap:8px;padding:6px 12px;margin-bottom:2px;border-radius:var(--radius);border:1px solid transparent;transition:all .2s; }
.item-list li:hover { background:rgba(201,168,76,.06);border-color:var(--border); }
.item-list li a { flex:1;font-size:.95rem;color:var(--gold2); }
.item-list li a:hover { color:var(--gold);text-shadow:0 0 6px rgba(201,168,76,.4); }
.item-list .actions { display:flex;gap:6px;opacity:0;transition:opacity .15s; }
.item-list li:hover .actions { opacity:1; }
.item-list .actions a { font-size:.75rem;padding:2px 8px;border-radius:1px;border:1px solid var(--border);flex:none;color:var(--silver); }
.item-list .actions a:hover { border-color:var(--gold);color:var(--gold); }
.item-list .del { color:var(--danger)!important; }
.empty { color:var(--border);font-style:italic;padding:12px; }
label { display:block;font-size:.82rem;color:var(--silver);margin-bottom:4px;margin-top:12px;letter-spacing:.5px;text-transform:uppercase;font-family:'Cinzel Decorative',serif; }
input[type=text],input[type=password],input[type=email],input[type=date],input:not([type]),textarea,select {
  background:rgba(18,10,2,.9);color:var(--mithril);border:1px solid var(--border);
  border-radius:var(--radius);padding:8px 12px;font-size:.9rem;font-family:'IM Fell English',serif;
  width:100%;transition:border-color .2s,box-shadow .2s;outline:none;
}
input:focus,textarea:focus,select:focus { border-color:var(--gold);box-shadow:0 0 0 3px rgba(201,168,76,.15); }
textarea { resize:vertical;font-family:'IM Fell English',serif;font-size:.9rem; }
select option { background:var(--bg2); }
.form-row { display:flex;gap:12px;flex-wrap:wrap; }
.form-row > * { flex:1;min-width:200px; }
.btn { display:inline-flex;align-items:center;gap:6px;padding:8px 22px;border-radius:1px;border:1px solid var(--gold);background:transparent;color:var(--gold);font-size:.9rem;font-family:'IM Fell English',serif;cursor:pointer;transition:all .2s;text-decoration:none;letter-spacing:.5px; }
.btn:hover { background:rgba(201,168,76,.1);border-color:var(--gold2);color:var(--gold2);box-shadow:0 0 14px rgba(201,168,76,.2);text-decoration:none; }
.btn-primary { background:rgba(201,168,76,.15);color:var(--gold2);border-color:var(--gold);font-weight:600;box-shadow:0 0 10px rgba(201,168,76,.15); }
.btn-primary:hover { background:rgba(201,168,76,.28);box-shadow:0 0 20px rgba(201,168,76,.35);color:#fff; }
.btn-danger { border-color:var(--danger);color:var(--danger); }
.btn-danger:hover { background:var(--danger);color:var(--mithril);box-shadow:0 0 14px rgba(139,0,0,.4);text-shadow:none; }
.btn-sm { padding:4px 14px;font-size:.8rem; }
.btn-group { display:flex;gap:10px;margin-top:20px;flex-wrap:wrap;align-items:center; }
err { display:block;color:var(--danger);background:rgba(139,0,0,.08);border:1px solid var(--danger);border-radius:var(--radius);padding:8px 12px;margin:10px 0;font-size:.9rem; }
.breadcrumb { font-size:.85rem;color:var(--border);margin-bottom:16px;display:flex;align-items:center;gap:6px;flex-wrap:wrap; }
.breadcrumb a { color:var(--silver); }
.breadcrumb a:hover { color:var(--gold); }
.breadcrumb .sep { color:var(--border); }
.badge { font-size:.75rem;background:var(--bg3);border:1px solid var(--border);border-radius:1px;padding:1px 8px;color:var(--silver); }
.timestamp { font-size:.8rem;color:var(--border); }
table { width:100%;border-collapse:collapse;font-size:.9rem; }
th { text-align:left;padding:10px 12px;border-bottom:1px solid var(--gold);color:var(--silver);font-size:.8rem;text-transform:uppercase;letter-spacing:1px;font-family:'Cinzel Decorative',serif; }
td { padding:6px 12px;vertical-align:top;border-bottom:1px solid var(--bg3); }
tr:hover td { background:rgba(201,168,76,.04); }
.search-box { display:flex;gap:8px;margin-bottom:20px; }
.search-box input { flex:1; }
.tag-create { color:var(--shire);font-weight:600; }
.tag-update { color:var(--silver);font-weight:600; }
.tag-delete { color:var(--danger);font-weight:600; }
.footer { position:fixed;bottom:0;left:0;width:100%;background:rgba(10,5,0,.95);border-top:1px solid var(--gold);color:var(--gold);text-align:center;font-size:.75rem;padding:5px;z-index:99;font-family:'Cinzel Decorative',serif;letter-spacing:2px; }
.two-col { display:grid;grid-template-columns:1fr 1fr;gap:20px; }
@media (max-width:600px) { .two-col { grid-template-columns:1fr; } .nav { gap:4px; } textarea { width:100%; } }
.confirm-box { background:rgba(18,10,2,.92);border:1px solid var(--gold);border-radius:var(--radius);padding:24px;max-width:600px;box-shadow:0 4px 24px rgba(0,0,0,.7); }
.confirm-box p { margin-bottom:12px;line-height:1.6; }
.confirm-box .field { margin:8px 0;font-size:.9rem; }
.confirm-box .field b { color:var(--gold2); }
.theme-select { background:rgba(18,10,2,.9);color:var(--gold);border:1px solid var(--border);border-radius:1px;padding:3px 8px;font-size:.8rem;cursor:pointer;font-family:'IM Fell English',serif; }
.theme-select:focus { outline:none;border-color:var(--gold); }</style>
<div class="footer">&#9770; {{ build_date }} &#9770;</div>
"""

# L2467 in evernothing.py
STYLE_SHREK = """
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
@import url('https://fonts.googleapis.com/css2?family=MedievalSharp&family=Cinzel:wght@400;600&family=Lora:wght@400;600&display=swap');
:root {
  --swamp:    #4a7c3f;
  --mud:      #8b6914;
  --onion:    #c8a84b;
  --slime:    #7ec850;
  --mist:     #a8c878;
  --parchment:#f5e6c8;
  --dark:     #1a2e0a;
  --bark:     #3d2b1f;
  --danger:   #c0392b;
  --bg:       #0d1a08;
  --bg2:      #162410;
  --bg3:      #1e3015;
  --border:   #3a5a2a;
  --radius:   4px;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
html { font-size: 16px; }
body {
  background: var(--bg);
  background-image:
    /* Swamp mist layers */
    radial-gradient(ellipse 120% 40% at 50% 100%, rgba(74,124,63,.25) 0%, transparent 70%),
    radial-gradient(ellipse 80% 30% at 20% 80%, rgba(126,200,80,.12) 0%, transparent 60%),
    radial-gradient(ellipse 60% 20% at 80% 90%, rgba(74,124,63,.15) 0%, transparent 50%),
    /* Night sky */
    radial-gradient(ellipse 200% 60% at 50% 0%, #0a1505 0%, #0d1a08 100%);
  color: var(--parchment);
  font-family: 'Lora', Georgia, serif;
  min-height: 100vh;
  padding-bottom: 40px;
  position: relative;
  overflow-x: hidden;
}
/* Fireflies */
body::before {
  content: '✦ ✧ ✦ ✧ ✦ ✧ ✦ ✧ ✦ ✧ ✦';
  position: fixed;
  top: 15%;
  left: 0;
  width: 100%;
  color: rgba(200,168,75,.4);
  font-size: .6rem;
  letter-spacing: 3rem;
  pointer-events: none;
  z-index: 0;
  animation: fireflies 8s ease-in-out infinite alternate;
}
body::after {
  content: '✧ ✦ ✧ ✦ ✧ ✦ ✧ ✦ ✧';
  position: fixed;
  top: 60%;
  left: 5%;
  width: 100%;
  color: rgba(126,200,80,.3);
  font-size: .5rem;
  letter-spacing: 4rem;
  pointer-events: none;
  z-index: 0;
  animation: fireflies 6s ease-in-out infinite alternate-reverse;
}
@keyframes fireflies {
  0%   { opacity: .2; transform: translateY(0px); }
  50%  { opacity: .8; transform: translateY(-8px); }
  100% { opacity: .3; transform: translateY(4px); }
}
body > * { position: relative; z-index: 1; }
a { color: var(--slime); text-decoration: none; transition: color .2s; }
a:hover { color: var(--onion); text-shadow: 0 0 8px rgba(200,168,75,.5); }
/* Swamp mud top border */
.nav {
  background: linear-gradient(135deg, #0d1a08 0%, #162410 100%);
  border-bottom: 3px solid var(--mud);
  box-shadow: 0 3px 20px rgba(74,124,63,.3), inset 0 -1px 0 var(--swamp);
  padding: 10px 20px;
  display: flex; align-items: center; gap: 6px; flex-wrap: wrap;
  position: sticky; top: 0; z-index: 100;
}
.nav-brand {
  font-family: 'Cinzel', serif;
  font-size: 1rem; font-weight: 600;
  color: var(--onion);
  text-shadow: 0 0 12px rgba(200,168,75,.6), 0 2px 4px rgba(0,0,0,.8);
  letter-spacing: 2px; margin-right: 10px;
  text-transform: uppercase;
}
.nav a { font-size:.82rem;padding:4px 10px;border-radius:2px;border:1px solid transparent;color:var(--mist);transition:all .2s;font-family:'Lora',serif; }
.nav a:hover { border-color:var(--swamp);color:var(--onion);background:rgba(74,124,63,.15);text-shadow:0 0 6px rgba(200,168,75,.4);text-decoration:none; }
.nav .sep { color:var(--border); }
.nav .nav-logout { margin-left:auto;color:var(--danger);border-color:var(--danger);border-radius:2px;border:1px solid;padding:4px 12px; }
.nav .nav-logout:hover { background:var(--danger);color:#fff;text-shadow:none; }
.container { max-width:1100px;margin:0;padding:24px 20px; }
h2,h3 { font-family:'Cinzel',serif;color:var(--onion);margin-bottom:16px;font-weight:600;letter-spacing:1px;text-shadow:0 0 10px rgba(200,168,75,.3); }
h4 { color:var(--mist);margin:20px 0 10px;font-size:.9rem;text-transform:uppercase;letter-spacing:2px;font-family:'Cinzel',serif; }
.card {
  background: linear-gradient(135deg, var(--bg2) 0%, var(--bg3) 100%);
  border: 1px solid var(--border);
  border-left: 4px solid var(--swamp);
  border-radius: var(--radius);
  padding: 20px; margin-bottom: 16px;
  box-shadow: 0 4px 24px rgba(74,124,63,.1);
}
.item-list { list-style:none; }
.item-list li { display:flex;align-items:center;gap:8px;padding:6px 12px;margin-bottom:2px;border-radius:var(--radius);border:1px solid transparent;transition:all .2s; }
.item-list li:hover { background:rgba(74,124,63,.1);border-color:var(--border); }
.item-list li a { flex:1;font-size:.95rem;color:var(--slime); }
.item-list li a:hover { color:var(--onion); }
.item-list .actions { display:flex;gap:6px;opacity:0;transition:opacity .15s; }
.item-list li:hover .actions { opacity:1; }
.item-list .actions a { font-size:.75rem;padding:2px 8px;border-radius:2px;border:1px solid var(--border);flex:none;color:var(--mist); }
.item-list .actions a:hover { border-color:var(--onion);color:var(--onion); }
.item-list .del { color:var(--danger)!important; }
.empty { color:var(--border);font-style:italic;padding:12px;font-family:'Lora',serif; }
label { display:block;font-size:.82rem;color:var(--mist);margin-bottom:4px;margin-top:12px;letter-spacing:.5px;text-transform:uppercase;font-family:'Cinzel',serif; }
input[type=text],input[type=password],input[type=email],input[type=date],input:not([type]),textarea,select {
  background:var(--bg3);color:var(--parchment);border:1px solid var(--border);
  border-radius:var(--radius);padding:8px 12px;font-size:.9rem;font-family:'Lora',serif;
  width:100%;transition:border-color .2s,box-shadow .2s;outline:none;
}
input:focus,textarea:focus,select:focus { border-color:var(--swamp);box-shadow:0 0 0 3px rgba(74,124,63,.2); }
textarea { resize:vertical;font-family:'Lora',serif;font-size:.9rem; }
select option { background:var(--bg2); }
.form-row { display:flex;gap:12px;flex-wrap:wrap; }
.form-row > * { flex:1;min-width:200px; }
.btn { display:inline-flex;align-items:center;gap:6px;padding:8px 22px;border-radius:2px;border:1px solid var(--swamp);background:transparent;color:var(--mist);font-size:.9rem;font-family:'Lora',serif;cursor:pointer;transition:all .2s;text-decoration:none;letter-spacing:.5px; }
.btn:hover { background:rgba(74,124,63,.15);border-color:var(--onion);color:var(--onion);box-shadow:0 0 14px rgba(200,168,75,.2);text-decoration:none; }
.btn-primary { background:rgba(74,124,63,.2);color:var(--onion);border-color:var(--mud);font-weight:600;box-shadow:0 0 10px rgba(74,124,63,.15); }
.btn-primary:hover { background:rgba(74,124,63,.35);box-shadow:0 0 20px rgba(200,168,75,.3);color:var(--parchment); }
.btn-danger { border-color:var(--danger);color:var(--danger); }
.btn-danger:hover { background:var(--danger);color:#fff;box-shadow:0 0 14px rgba(192,57,43,.35);text-shadow:none; }
.btn-sm { padding:4px 14px;font-size:.8rem; }
.btn-group { display:flex;gap:10px;margin-top:20px;flex-wrap:wrap;align-items:center; }
err { display:block;color:var(--danger);background:rgba(192,57,43,.08);border:1px solid var(--danger);border-radius:var(--radius);padding:8px 12px;margin:10px 0;font-size:.9rem; }
.breadcrumb { font-size:.85rem;color:var(--border);margin-bottom:16px;display:flex;align-items:center;gap:6px;flex-wrap:wrap; }
.breadcrumb a { color:var(--mist); }
.breadcrumb a:hover { color:var(--onion); }
.breadcrumb .sep { color:var(--border); }
.badge { font-size:.75rem;background:var(--bg3);border:1px solid var(--border);border-radius:2px;padding:1px 8px;color:var(--mist); }
.timestamp { font-size:.8rem;color:var(--border); }
table { width:100%;border-collapse:collapse;font-size:.9rem; }
th { text-align:left;padding:10px 12px;border-bottom:1px solid var(--mud);color:var(--mist);font-size:.8rem;text-transform:uppercase;letter-spacing:1px;font-family:'Cinzel',serif; }
td { padding:6px 12px;vertical-align:top;border-bottom:1px solid var(--bg3); }
tr:hover td { background:rgba(74,124,63,.06); }
.search-box { display:flex;gap:8px;margin-bottom:20px; }
.search-box input { flex:1; }
.tag-create { color:var(--slime);font-weight:600; }
.tag-update { color:var(--mist);font-weight:600; }
.tag-delete { color:var(--danger);font-weight:600; }
.footer { position:fixed;bottom:0;left:0;width:100%;background:var(--bg2);border-top:2px solid var(--mud);color:var(--border);text-align:center;font-size:.75rem;padding:5px;z-index:99;font-family:'Cinzel',serif;letter-spacing:1px; }
.two-col { display:grid;grid-template-columns:1fr 1fr;gap:20px; }
@media (max-width:600px) { .two-col { grid-template-columns:1fr; } .nav { gap:4px; } textarea { width:100%; } }
.confirm-box { background:var(--bg2);border:1px solid var(--mud);border-radius:var(--radius);padding:24px;max-width:600px;box-shadow:0 4px 24px rgba(74,124,63,.12); }
.confirm-box p { margin-bottom:12px;line-height:1.6; }
.confirm-box .field { margin:8px 0;font-size:.9rem; }
.confirm-box .field b { color:var(--slime); }
.theme-select { background:var(--bg3);color:var(--mist);border:1px solid var(--border);border-radius:2px;padding:3px 8px;font-size:.8rem;cursor:pointer;font-family:'Lora',serif; }
.theme-select:focus { outline:none;border-color:var(--swamp); }</style>
<div class="footer">&#127807; {{ build_date }} &#127807;</div>
"""

# L2677 in evernothing.py
T_FOLDERS = STYLE + """
<nav class="nav">
  <span class="nav-brand">&#11088; EverNothing</span>
  <a href=/folder/add>+ Folder</a>
  <a href=/export>Export</a>
  <a href=/audit_report>Audit</a>
  <a href=/sessions>Sessions</a>
  <a href=/change_password>Password</a>
  <form action="/set_theme" method="get" style="display:inline">
    <select name="t" class="theme-select" onchange="this.form.submit()" title="Switch theme">
      <option value="stellar" {% if theme != "unicorn" %}selected="selected"{% endif %}>&#11088; Stellar</option>
      <option value="unicorn" {% if theme == "unicorn" %}selected="selected"{% endif %}>&#x1F984; Unicorn</option>
      <option value="startrek" {% if theme == "startrek" %}selected="selected"{% endif %}>&#x1F596; Star Trek</option>
      <option value="shrek" {% if theme == "shrek" %}selected="selected"{% endif %}>&#127807; Shrek</option>
      <option value="lotr" {% if theme == "lotr" %}selected="selected"{% endif %}>&#9770; LOTR</option>
    </select>
  </form>
  <a href=/logout class="nav-logout">Logout</a>
</nav>
<div class="container">
  <div class="search-box">
    <form action="/search" method="get" style="display:flex;gap:8px;width:100%">
      <input name="q" placeholder="Search notes..." style="flex:1">
      <button class="btn btn-primary">Search</button>
    </form>
  </div>
  <div class="two-col">
    <div>
      <h4>Folders</h4>
      <ul class="item-list">
      {% for f in folders %}
      <li>
        <a href=/folder/{{f[0]}}>&#128193; {{f[1]}}</a>
        <span class="actions">
          <a href=/folder/rename/{{f[0]}}>rename</a>
          <a href=/folder/delete/{{f[0]}} class="del">delete</a>
        </span>
      </li>
      {% else %}
      <li class="empty">No folders yet. <a href=/folder/add>Create one</a></li>
      {% endfor %}
      </ul>
    </div>
    <div>
      <h4>Recently Edited</h4>
      <ul class="item-list">
      {% for n in recent %}
      <li>
        <a href=/edit/{{n[0]}}>{{n[1]}}</a>
        <span class="timestamp">{{n[2]}}</span>
      </li>
      {% else %}
      <li class="empty">No notes yet.</li>
      {% endfor %}
      </ul>
    </div>
  </div>
</div>
"""

# L2737 in evernothing.py
T_ADD_FOLDER = STYLE + """
<nav class="nav">
  <span class="nav-brand">&#11088; EverNothing</span>
  <a href=/>Home</a>
  <form action="/set_theme" method="get" style="display:inline">
    <select name="t" class="theme-select" onchange="this.form.submit()" title="Switch theme">
      <option value="stellar" {% if theme != "unicorn" %}selected="selected"{% endif %}>&#11088; Stellar</option>
      <option value="unicorn" {% if theme == "unicorn" %}selected="selected"{% endif %}>&#x1F984; Unicorn</option>
      <option value="startrek" {% if theme == "startrek" %}selected="selected"{% endif %}>&#x1F596; Star Trek</option>
      <option value="shrek" {% if theme == "shrek" %}selected="selected"{% endif %}>&#127807; Shrek</option>
      <option value="lotr" {% if theme == "lotr" %}selected="selected"{% endif %}>&#9770; LOTR</option>
    </select>
  </form>
  <a href=/logout class="nav-logout">Logout</a>
</nav>
<div class="container">
  <h3>Create Folder</h3>
  {% if error %}<err>{{error}}</err>{% endif %}
  <div class="card" style="max-width:480px">
    <form method=post>
      <input type=hidden name=csrf_token value="{{ csrf_token() }}">
      <label>Folder Name</label>
      <input name=name maxlength="255" autofocus>
      <div class="btn-group">
        <button class="btn btn-primary">Create</button>
        <a href=/ class="btn">Cancel</a>
      </div>
    </form>
  </div>
</div>
"""

# L2769 in evernothing.py
T_ADD_SUBFOLDER = STYLE + """
<nav class="nav">
  <span class="nav-brand">&#11088; EverNothing</span>
  <a href=/folder/{{pid}}>Back</a>
  <form action="/set_theme" method="get" style="display:inline">
    <select name="t" class="theme-select" onchange="this.form.submit()" title="Switch theme">
      <option value="stellar" {% if theme != "unicorn" %}selected="selected"{% endif %}>&#11088; Stellar</option>
      <option value="unicorn" {% if theme == "unicorn" %}selected="selected"{% endif %}>&#x1F984; Unicorn</option>
      <option value="startrek" {% if theme == "startrek" %}selected="selected"{% endif %}>&#x1F596; Star Trek</option>
      <option value="shrek" {% if theme == "shrek" %}selected="selected"{% endif %}>&#127807; Shrek</option>
      <option value="lotr" {% if theme == "lotr" %}selected="selected"{% endif %}>&#9770; LOTR</option>
    </select>
  </form>
  <a href=/logout class="nav-logout">Logout</a>
</nav>
<div class="container">
  <h3>Create Subfolder</h3>
  <div class="card" style="max-width:480px">
    <form method=post>
      <input type=hidden name=csrf_token value="{{ csrf_token() }}">
      <label>Subfolder Name</label>
      <input name=name autofocus>
      <div class="btn-group">
        <button class="btn btn-primary">Create</button>
        <a href=/folder/{{pid}} class="btn">Cancel</a>
      </div>
    </form>
  </div>
</div>
"""

# L2800 in evernothing.py
T_RENAME_FOLDER = STYLE + """
<nav class="nav">
  <span class="nav-brand">&#11088; EverNothing</span>
  <a href=/folder/{{fid}}>Back</a>
  <form action="/set_theme" method="get" style="display:inline">
    <select name="t" class="theme-select" onchange="this.form.submit()" title="Switch theme">
      <option value="stellar" {% if theme != "unicorn" %}selected="selected"{% endif %}>&#11088; Stellar</option>
      <option value="unicorn" {% if theme == "unicorn" %}selected="selected"{% endif %}>&#x1F984; Unicorn</option>
      <option value="startrek" {% if theme == "startrek" %}selected="selected"{% endif %}>&#x1F596; Star Trek</option>
      <option value="shrek" {% if theme == "shrek" %}selected="selected"{% endif %}>&#127807; Shrek</option>
      <option value="lotr" {% if theme == "lotr" %}selected="selected"{% endif %}>&#9770; LOTR</option>
    </select>
  </form>
  <a href=/logout class="nav-logout">Logout</a>
</nav>
<div class="container">
  <h3>Rename Folder</h3>
  <div class="card" style="max-width:480px">
    <form method=post>
      <input type=hidden name=csrf_token value="{{ csrf_token() }}">
      <label>New Name</label>
      <input name=name value="{{f[0]}}" autofocus>
      <div class="btn-group">
        <button class="btn btn-primary">Rename</button>
        <a href=/folder/{{fid}} class="btn">Cancel</a>
      </div>
    </form>
  </div>
</div>
"""

# L2831 in evernothing.py
T_CHANGE_PASSWORD = STYLE + """
<nav class="nav">
  <span class="nav-brand">&#11088; EverNothing</span>
  <a href=/>Home</a>
  <form action="/set_theme" method="get" style="display:inline">
    <select name="t" class="theme-select" onchange="this.form.submit()" title="Switch theme">
      <option value="stellar" {% if theme != "unicorn" %}selected="selected"{% endif %}>&#11088; Stellar</option>
      <option value="unicorn" {% if theme == "unicorn" %}selected="selected"{% endif %}>&#x1F984; Unicorn</option>
      <option value="startrek" {% if theme == "startrek" %}selected="selected"{% endif %}>&#x1F596; Star Trek</option>
      <option value="shrek" {% if theme == "shrek" %}selected="selected"{% endif %}>&#127807; Shrek</option>
      <option value="lotr" {% if theme == "lotr" %}selected="selected"{% endif %}>&#9770; LOTR</option>
    </select>
  </form>
  <a href=/logout class="nav-logout">Logout</a>
</nav>
<div class="container">
  <h3>Change Password</h3>
  {% if error %}<err>{{error}}</err>{% endif %}
  <div class="card" style="max-width:480px">
    <form method=post>
      <input type=hidden name=csrf_token value="{{ csrf_token() }}">
      <label>Current Password</label>
      <div style="position:relative">
        <input type=password name=old_password id=old_password autofocus style="padding-right:70px">
        <a href="#" onclick="toggleVis('old_password',this);return false;" style="position:absolute;right:10px;top:50%;transform:translateY(-50%);font-size:.8rem;color:var(--gold-dim)">Show</a>
      </div>
      <label>New Password</label>
      <div style="position:relative">
        <input type=password name=new_password id=new_password style="padding-right:70px">
        <a href="#" onclick="toggleVis('new_password',this);return false;" style="position:absolute;right:10px;top:50%;transform:translateY(-50%);font-size:.8rem;color:var(--gold-dim)">Show</a>
      </div>
      <label>Verify New Password</label>
      <div style="position:relative">
        <input type=password name=verify_password id=verify_password style="padding-right:70px">
        <a href="#" onclick="toggleVis('verify_password',this);return false;" style="position:absolute;right:10px;top:50%;transform:translateY(-50%);font-size:.8rem;color:var(--gold-dim)">Show</a>
      </div>
      <div class="btn-group">
        <button class="btn btn-primary">Change Password</button>
        <a href=/ class="btn">Cancel</a>
      </div>
    </form>
  </div>
</div>
<script>
function toggleVis(id, link) {
  var el = document.getElementById(id);
  if (el.type === 'password') { el.type = 'text'; link.textContent = 'Hide'; }
  else { el.type = 'password'; link.textContent = 'Show'; }
}
</script>
"""

# L2883 in evernothing.py
T_DELETE_NOTE = STYLE + """
<nav class="nav">
  <span class="nav-brand">&#11088; EverNothing</span>
  <a href=/>Home</a>
  <form action="/set_theme" method="get" style="display:inline">
    <select name="t" class="theme-select" onchange="this.form.submit()" title="Switch theme">
      <option value="stellar" {% if theme != "unicorn" %}selected="selected"{% endif %}>&#11088; Stellar</option>
      <option value="unicorn" {% if theme == "unicorn" %}selected="selected"{% endif %}>&#x1F984; Unicorn</option>
      <option value="startrek" {% if theme == "startrek" %}selected="selected"{% endif %}>&#x1F596; Star Trek</option>
      <option value="shrek" {% if theme == "shrek" %}selected="selected"{% endif %}>&#127807; Shrek</option>
      <option value="lotr" {% if theme == "lotr" %}selected="selected"{% endif %}>&#9770; LOTR</option>
    </select>
  </form>
  <a href=/logout class="nav-logout">Logout</a>
</nav>
<div class="container">
  <div class="confirm-box">
    <h3>Delete Note</h3>
    <p>Are you sure you want to permanently delete <b>{{n[1]}}</b>?</p>
    <p style="color:#888;font-size:.85rem">This action cannot be undone.</p>
    <form method=post>
      <input type=hidden name=csrf_token value="{{ csrf_token() }}">
      <div class="btn-group">
        <button class="btn btn-danger">Yes, Delete</button>
        <a href=javascript:history.back() class="btn">Cancel</a>
      </div>
    </form>
  </div>
</div>
"""

# L2914 in evernothing.py
T_EDIT_CONFIRM = STYLE + """
<nav class="nav">
  <span class="nav-brand">&#11088; EverNothing</span>
  <a href=/>Home</a>
  <form action="/set_theme" method="get" style="display:inline">
    <select name="t" class="theme-select" onchange="this.form.submit()" title="Switch theme">
      <option value="stellar" {% if theme != "unicorn" %}selected="selected"{% endif %}>&#11088; Stellar</option>
      <option value="unicorn" {% if theme == "unicorn" %}selected="selected"{% endif %}>&#x1F984; Unicorn</option>
      <option value="startrek" {% if theme == "startrek" %}selected="selected"{% endif %}>&#x1F596; Star Trek</option>
      <option value="shrek" {% if theme == "shrek" %}selected="selected"{% endif %}>&#127807; Shrek</option>
      <option value="lotr" {% if theme == "lotr" %}selected="selected"{% endif %}>&#9770; LOTR</option>
    </select>
  </form>
  <a href=/logout class="nav-logout">Logout</a>
</nav>
<div class="container">
  <div class="confirm-box">
    <h3>Confirm Changes</h3>
    <p>Save the following changes?</p>
    <div class="field"><b>Note:</b> {{note[0]}}</div>
    <div class="field"><b>Description:</b> {{note[4]}}</div>
    <form method=post action="/edit/{{id}}">
      <input type=hidden name=csrf_token value="{{ csrf_token() }}">
      <input type=hidden name=note value="{{note[0]}}">
      <input type=hidden name=content value="{{note[1]}}">
      <input type=hidden name=folder_id value="{{note[2]}}">
      <input type=hidden name=description value="{{note[4]}}">
      <input type=hidden name=confirm value="yes">
      <div class="btn-group">
        <button class="btn btn-primary">Yes, Save</button>
        <button type=button class="btn" onclick="history.back()">Cancel</button>
      </div>
    </form>
  </div>
</div>
"""

# L2951 in evernothing.py
T_NOTES = STYLE + """
<nav class="nav">
  <span class="nav-brand">&#11088; EverNothing</span>
  <a href={% if folder[2] %}/folder/{{folder[2]}}{% else %}/{% endif %}>&#8592; Back</a>
  <a href=/add/{{folder[0]}}>+ Add Note</a>
  <a href=/folder/{{folder[0]}}/add_folder>+ Subfolder</a>
  <a href=/folder/rename/{{folder[0]}}>Rename</a>
  <a href=/folder/delete/{{folder[0]}} class="btn-danger" style="color:var(--red)">Delete Folder</a>
  <form action="/set_theme" method="get" style="display:inline">
    <select name="t" class="theme-select" onchange="this.form.submit()" title="Switch theme">
      <option value="stellar" {% if theme != "unicorn" %}selected="selected"{% endif %}>&#11088; Stellar</option>
      <option value="unicorn" {% if theme == "unicorn" %}selected="selected"{% endif %}>&#x1F984; Unicorn</option>
      <option value="startrek" {% if theme == "startrek" %}selected="selected"{% endif %}>&#x1F596; Star Trek</option>
      <option value="shrek" {% if theme == "shrek" %}selected="selected"{% endif %}>&#127807; Shrek</option>
      <option value="lotr" {% if theme == "lotr" %}selected="selected"{% endif %}>&#9770; LOTR</option>
    </select>
  </form>
  <a href=/logout class="nav-logout">Logout</a>
</nav>
<div class="container">
  <div class="breadcrumb">
    <a href="/">&#127968; Home</a>
    {% for bc_id, bc_name in breadcrumb %}
      <span class="sep">&#8250;</span>
      {% if bc_id == folder[0] %}
        <span>{{bc_name}}</span>
      {% else %}
        <a href="/folder/{{bc_id}}">{{bc_name}}</a>
      {% endif %}
    {% endfor %}
  </div>
  <div class="two-col">
    <div>
      <h4>Notes</h4>
      <ul class="item-list">
      {% for n in notes %}
      <li>
        <a href=/edit/{{n[0]}}>{{n[1]}}</a>
        <span class="actions">
          <a href=/note/delete/{{n[0]}} class="del">delete</a>
        </span>
      </li>
      {% else %}
      <li class="empty">No notes. <a href=/add/{{folder[0]}}>Add one</a></li>
      {% endfor %}
      </ul>
    </div>
    <div>
      <h4>Subfolders</h4>
      <ul class="item-list">
      {% for s in subfolders %}
      <li><a href=/folder/{{s[0]}}>&#128193; {{s[1]}}</a></li>
      {% else %}
      <li class="empty">No subfolders.</li>
      {% endfor %}
      </ul>
    </div>
  </div>
</div>
"""

# L3012 in evernothing.py
T_ADD = STYLE + """
<nav class="nav">
  <span class="nav-brand">&#11088; EverNothing</span>
  <a href=/folder/{{fid}}>&#8592; Back</a>
  <form action="/set_theme" method="get" style="display:inline">
    <select name="t" class="theme-select" onchange="this.form.submit()" title="Switch theme">
      <option value="stellar" {% if theme != "unicorn" %}selected="selected"{% endif %}>&#11088; Stellar</option>
      <option value="unicorn" {% if theme == "unicorn" %}selected="selected"{% endif %}>&#x1F984; Unicorn</option>
      <option value="startrek" {% if theme == "startrek" %}selected="selected"{% endif %}>&#x1F596; Star Trek</option>
      <option value="shrek" {% if theme == "shrek" %}selected="selected"{% endif %}>&#127807; Shrek</option>
      <option value="lotr" {% if theme == "lotr" %}selected="selected"{% endif %}>&#9770; LOTR</option>
    </select>
  </form>
  <a href=/logout class="nav-logout">Logout</a>
</nav>
<div class="container">
  <h3>Add Note</h3>
  {% if error %}<err>{{error}}</err>{% endif %}
  <form method=post enctype="multipart/form-data">
    <input type=hidden name=csrf_token value="{{ csrf_token() }}">
    <div class="form-row">
      <div>
        <label>Note Title</label>
        <input name=note value="{{note}}" autofocus>
      </div>
      <div>
        <label>Description <span style="color:#555">(optional, max 255)</span></label>
        <input name=description value="{{description}}" maxlength="255">
      </div>
    </div>
    <label>Contents</label>
    <textarea name=content rows=30 cols=120>{{content}}</textarea>
    <label>Attachment <span style="color:#555">(optional)</span></label>
    <input type=file name=file style="width:auto">
    <div class="btn-group">
      <button class="btn btn-primary">Add Note</button>
      <a href=/folder/{{fid}} class="btn">Cancel</a>
    </div>
  </form>
</div>
"""

# L3054 in evernothing.py
T_EDIT = STYLE + """
<nav class="nav">
  <span class="nav-brand">&#11088; EverNothing</span>
  <a href=/>Home</a>
  {% for b in breadcrumbs %}
  <span class="sep">&#8250;</span> <a href=/folder/{{b[0]}}>{{b[1]}}</a>
  {% endfor %}
  <span style="margin-left:auto;display:flex;gap:8px;align-items:center">
    <a href=/history/{{id}} class="btn btn-sm" style="color:var(--gold-dim)">History: {{note[3]}}</a>
    <a href=/note/delete/{{id}} class="btn btn-sm btn-danger">Delete</a>
    <a href=/logout class="btn btn-sm nav-logout">Logout</a>
  </span>
</nav>
<div class="container">
  {% if error %}<err>{{error}}</err>{% endif %}
  <form method=post enctype="multipart/form-data">
    <input type=hidden name=csrf_token value="{{ csrf_token() }}">
    <div class="form-row">
      <div>
        <label>Note Title</label>
        <input name=note value='{{note[0]}}'>
      </div>
      <div>
        <label>Description <span style="color:#555">(optional)</span></label>
        <input name=description value='{{note[4]}}' maxlength="255">
      </div>
    </div>
    <label>Folder</label>
    <select name=folder_id style="width:auto;min-width:200px">
    {% for f in folders %}
    <option value='{{f[0]}}' {% if f[0]==note[2] %}selected{% endif %}>{{f[1]}}</option>
    {% endfor %}
    </select>
    <label>Contents</label>
    <textarea name=content rows=30 cols=120>{{note[1]}}</textarea>
    <div class="btn-group">
      <button class="btn btn-primary">Commit</button>
      <a href=/ class="btn">Cancel</a>
    </div>
  </form>

  <h4>Attachments</h4>
  <form method=post enctype="multipart/form-data" style="display:flex;gap:8px;align-items:center;margin-bottom:12px">
    <input type=hidden name=csrf_token value="{{ csrf_token() }}">
    <input type=file name=file style="width:auto">
    <button class="btn btn-sm">Upload</button>
  </form>
  <ul class="item-list">
  {% for att in attachments %}
  <li>
    <a href=/download/{{att[0]}}>&#128206; {{att[1]}}</a>
    <span class="badge">{{att[2]}} bytes</span>
    <span class="actions" style="opacity:1">
      <form method=post action="/delete_attachment/{{att[0]}}" style="display:inline">
        <input type=hidden name=csrf_token value="{{ csrf_token() }}">
        <button class="btn btn-sm btn-danger" style="border:none;background:none;cursor:pointer;color:var(--red)">remove</button>
      </form>
    </span>
  </li>
  {% else %}
  <li class="empty">No attachments.</li>
  {% endfor %}
  </ul>
</div>
"""

# L3120 in evernothing.py
T_LOGIN = STYLE + """
<div style="min-height:100vh;display:flex;align-items:center;justify-content:center">
  <div class="card" style="width:100%;max-width:400px">
    <h2 style="text-align:center;margin-bottom:4px">&#127775;EverNothing</h2>
    <p style="text-align:center;color:#666;font-size:.85rem;margin-bottom:20px">Sign in to your notes</p>
    {% if error %}<err>{{error}}</err>{% endif %}
    <form method=post>
      <input type=hidden name=csrf_token value="{{ csrf_token() }}">
      <label>Username</label>
      <input name=username autofocus>
      <label>Password</label>
      <input type=password name=password>
      <label style="flex-direction:row;display:flex;align-items:center;gap:8px;margin-top:12px;cursor:pointer">
        <input type=checkbox name=remember_me style="width:auto;margin:0"> Remember me for 30 days
      </label>
      <div class="btn-group" style="margin-top:16px">
        <button class="btn btn-primary" style="flex:1;justify-content:center">Login</button>
      </div>
    </form>
    <p style="text-align:center;margin-top:16px;font-size:.85rem">
      <a href=/register>Create account</a> &nbsp;|&nbsp; <a href=/forgot_password>Forgot password?</a>
    </p>
  </div>
</div>
"""

# L3146 in evernothing.py
T_REGISTER = STYLE + """
<div style="min-height:100vh;display:flex;align-items:center;justify-content:center">
  <div class="card" style="width:100%;max-width:420px">
    <h2 style="text-align:center;margin-bottom:4px">&#127775;EverNothing</h2>
    <p style="text-align:center;color:#666;font-size:.85rem;margin-bottom:20px">Create your account</p>
    {% if error %}<err>{{error}}</err>{% endif %}
    <form method=post>
      <input type=hidden name=csrf_token value="{{ csrf_token() }}">
      <label>Username</label>
      <input name=username maxlength="50" required autofocus>
      <label>Email</label>
      <input name=email type="email" maxlength="100" required>
      <label>Password <span style="color:#555">(min 8 chars, upper, lower, number)</span></label>
      <input type=password name=password minlength="8" required>
      <div class="btn-group" style="margin-top:16px">
        <button class="btn btn-primary" style="flex:1;justify-content:center">Create Account</button>
      </div>
    </form>
    <p style="text-align:center;margin-top:16px;font-size:.85rem"><a href=/login>Already have an account?</a></p>
  </div>
</div>
"""

# L3169 in evernothing.py
T_SEARCH = STYLE + """
<nav class="nav">
  <span class="nav-brand">&#11088; EverNothing</span>
  <a href=/>Home</a>
  <form action="/set_theme" method="get" style="display:inline">
    <select name="t" class="theme-select" onchange="this.form.submit()" title="Switch theme">
      <option value="stellar" {% if theme != "unicorn" %}selected="selected"{% endif %}>&#11088; Stellar</option>
      <option value="unicorn" {% if theme == "unicorn" %}selected="selected"{% endif %}>&#x1F984; Unicorn</option>
      <option value="startrek" {% if theme == "startrek" %}selected="selected"{% endif %}>&#x1F596; Star Trek</option>
      <option value="shrek" {% if theme == "shrek" %}selected="selected"{% endif %}>&#127807; Shrek</option>
      <option value="lotr" {% if theme == "lotr" %}selected="selected"{% endif %}>&#9770; LOTR</option>
    </select>
  </form>
  <a href=/logout class="nav-logout">Logout</a>
</nav>
<div class="container">
  <form method="get" class="card">
    <div class="search-box">
      <input name="q" value="{{q}}" placeholder="Search notes..." autofocus style="flex:1">
      <button class="btn btn-primary">Search</button>
    </div>
    <div class="form-row" style="margin-top:8px">
      <div>
        <label>Folder</label>
        <select name="folder">
          <option value="">All Folders</option>
          {% for f in folders %}
          <option value="{{f[0]}}" {% if folder_filter==f[0]|string %}selected{% endif %}>{{f[1]}}</option>
          {% endfor %}
        </select>
      </div>
      <div>
        <label>Date From</label>
        <input type="date" name="date_from" value="{{date_from}}">
      </div>
      <div>
        <label>Date To</label>
        <input type="date" name="date_to" value="{{date_to}}">
      </div>
    </div>
    <div style="margin-top:10px;display:flex;gap:16px;font-size:.85rem">
      <label style="display:flex;align-items:center;gap:6px;margin:0;cursor:pointer">
        <input type="checkbox" name="regex" {% if use_regex %}checked{% endif %} style="width:auto"> Regex
      </label>
      <label style="display:flex;align-items:center;gap:6px;margin:0;cursor:pointer">
        <input type="checkbox" name="history" {% if search_history %}checked{% endif %} style="width:auto"> Search History
      </label>
    </div>
  </form>
  {% if folder_results %}
  <h4>Folders <span class="badge">{{folder_results|length}}</span></h4>
  <ul class="item-list">
  {% for f in folder_results %}
  <li><a href=/folder/{{f[0]}}>&#128193; {{f[1]}}</a></li>
  {% endfor %}
  </ul>
  {% endif %}
  <h4>Notes {% if notes %}<span class="badge">{{notes|length}}</span>{% endif %}</h4>
  <ul class="item-list">
  {% for n in notes %}
  <li>
    <a href=/edit/{{n[0]}}>{{n[1]}}</a>
    <span class="timestamp">{{n[2]}}</span>
  </li>
  {% else %}
  <li class="empty">No matches.</li>
  {% endfor %}
  </ul>
</div>
"""

# L3240 in evernothing.py
T_DELETE_FOLDER = STYLE + """
<nav class="nav">
  <span class="nav-brand">&#11088; EverNothing</span>
  <a href=/>Home</a>
  <form action="/set_theme" method="get" style="display:inline">
    <select name="t" class="theme-select" onchange="this.form.submit()" title="Switch theme">
      <option value="stellar" {% if theme != "unicorn" %}selected="selected"{% endif %}>&#11088; Stellar</option>
      <option value="unicorn" {% if theme == "unicorn" %}selected="selected"{% endif %}>&#x1F984; Unicorn</option>
      <option value="startrek" {% if theme == "startrek" %}selected="selected"{% endif %}>&#x1F596; Star Trek</option>
      <option value="shrek" {% if theme == "shrek" %}selected="selected"{% endif %}>&#127807; Shrek</option>
      <option value="lotr" {% if theme == "lotr" %}selected="selected"{% endif %}>&#9770; LOTR</option>
    </select>
  </form>
  <a href=/logout class="nav-logout">Logout</a>
</nav>
<div class="container">
  <div class="confirm-box">
    <h3>Delete Folder</h3>
    <p>Are you sure you want to delete <b>{{f[0]}}</b> and all its notes and subfolders?</p>
    <p style="color:#888;font-size:.85rem">This action cannot be undone.</p>
    <form method=post>
      <input type=hidden name=csrf_token value="{{ csrf_token() }}">
      <div class="btn-group">
        <button class="btn btn-danger">Yes, Delete</button>
        <a href=javascript:history.back() class="btn">Cancel</a>
      </div>
    </form>
  </div>
</div>
"""

# L3271 in evernothing.py
T_HISTORY = STYLE + """
<nav class="nav">
  <span class="nav-brand">&#11088; EverNothing</span>
  <a href=/edit/{{nid}}>&#8592; Back to Note</a>
  <form action="/set_theme" method="get" style="display:inline">
    <select name="t" class="theme-select" onchange="this.form.submit()" title="Switch theme">
      <option value="stellar" {% if theme != "unicorn" %}selected="selected"{% endif %}>&#11088; Stellar</option>
      <option value="unicorn" {% if theme == "unicorn" %}selected="selected"{% endif %}>&#x1F984; Unicorn</option>
      <option value="startrek" {% if theme == "startrek" %}selected="selected"{% endif %}>&#x1F596; Star Trek</option>
      <option value="shrek" {% if theme == "shrek" %}selected="selected"{% endif %}>&#127807; Shrek</option>
      <option value="lotr" {% if theme == "lotr" %}selected="selected"{% endif %}>&#9770; LOTR</option>
    </select>
  </form>
  <a href=/logout class="nav-logout">Logout</a>
</nav>
<div class="container">
  <h3>Note History</h3>
  <ul class="item-list">
  {% for h in history %}
  <li>
    <span style="font-size:.85rem;color:#888;min-width:140px">{{h[2]}}</span>
    <span style="flex:1">{{h[1]}}</span>
    <span class="actions" style="opacity:1">
      <a href=/history/restore/{{h[0]}} class="btn btn-sm">Rollback</a>
    </span>
  </li>
  {% else %}
  <li class="empty">No history.</li>
  {% endfor %}
  </ul>
</div>
"""

# L3304 in evernothing.py
T_ADMIN_LOGIN = STYLE + """
<div style="min-height:100vh;display:flex;align-items:center;justify-content:center">
  <div class="card" style="width:100%;max-width:380px">
    <h2 style="text-align:center;margin-bottom:4px">&#127775;Admin</h2>
    <p style="text-align:center;color:#666;font-size:.85rem;margin-bottom:20px">EverNothing Administration</p>
    {% if error %}<err>{{error}}</err>{% endif %}
    <form method=post>
      <input type=hidden name=csrf_token value="{{ csrf_token() }}">
      <label>Username</label>
      <input name=username autofocus>
      <label>Password</label>
      <input type=password name=password>
      <div class="btn-group" style="margin-top:16px">
        <button class="btn btn-primary" style="flex:1;justify-content:center">Login</button>
      </div>
    </form>
  </div>
</div>
"""

# L3324 in evernothing.py
T_ADMIN_SESSIONS = STYLE + """
<nav class="nav">
  <span class="nav-brand">&#11088; Admin</span>
  <a href=/admin/dashboard>&#8592; Dashboard</a>
  <form action="/set_theme" method="get" style="display:inline">
    <select name="t" class="theme-select" onchange="this.form.submit()" title="Switch theme">
      <option value="stellar" {% if theme != "unicorn" %}selected="selected"{% endif %}>&#11088; Stellar</option>
      <option value="unicorn" {% if theme == "unicorn" %}selected="selected"{% endif %}>&#x1F984; Unicorn</option>
      <option value="startrek" {% if theme == "startrek" %}selected="selected"{% endif %}>&#x1F596; Star Trek</option>
      <option value="shrek" {% if theme == "shrek" %}selected="selected"{% endif %}>&#127807; Shrek</option>
      <option value="lotr" {% if theme == "lotr" %}selected="selected"{% endif %}>&#9770; LOTR</option>
    </select>
  </form>
  <a href=/logout class="nav-logout">Logout</a>
</nav>
<div class="container">
  <h3>All Sessions</h3>
  <table>
    <tr><th>Username</th><th>Login Time</th><th>Status</th><th>IP Address</th><th>Device</th></tr>
    {% for s in sessions %}
    <tr>
      <td>{{s.username}}</td>
      <td class="timestamp">{{s.login_time}}</td>
      <td>
        {% if s.logout_time == 'Active' %}<span style="color:var(--gold-dim)">Active</span>
        {% else %}<span style="color:#555">{{s.logout_time}}</span>{% endif %}
      </td>
      <td style="font-size:.85rem">{{s.ip}}</td>
      <td style="font-size:.8rem;color:#888">{{s.user_agent}}</td>
    </tr>
    {% else %}
    <tr><td colspan=5 class="empty">No sessions found.</td></tr>
    {% endfor %}
  </table>
</div>
"""

# L3361 in evernothing.py
T_ADMIN_DASHBOARD = STYLE + """
<nav class="nav">
  <span class="nav-brand">&#11088; Admin</span>
  <a href=/admin/audit_logs>Audit Logs</a>
  <a href=/admin/sessions>Sessions</a>
  <a href=/admin/s3_backups>S3 Backups</a>
  <a href=/admin/iam_policy>IAM Policy</a>
  <form action="/set_theme" method="get" style="display:inline">
    <select name="t" class="theme-select" onchange="this.form.submit()" title="Switch theme">
      <option value="stellar" {% if theme != "unicorn" %}selected="selected"{% endif %}>&#11088; Stellar</option>
      <option value="unicorn" {% if theme == "unicorn" %}selected="selected"{% endif %}>&#x1F984; Unicorn</option>
      <option value="startrek" {% if theme == "startrek" %}selected="selected"{% endif %}>&#x1F596; Star Trek</option>
      <option value="shrek" {% if theme == "shrek" %}selected="selected"{% endif %}>&#127807; Shrek</option>
      <option value="lotr" {% if theme == "lotr" %}selected="selected"{% endif %}>&#9770; LOTR</option>
    </select>
  </form>
  <a href=/logout class="nav-logout">Logout</a>
</nav>
<div class="container">
  <h3>Users</h3>
  <form method="get" style="margin-bottom:16px">
    <div class="search-box">
      <input name="q" placeholder="Search users..." value="{{q}}" style="flex:1">
      <button class="btn btn-primary">Search</button>
    </div>
  </form>
  <table>
    <tr>
      <th>Username</th><th>Notes</th><th>Folders</th><th>Last Login</th><th>Actions</th>
    </tr>
    {% for u in users %}
    <tr>
      <td><a href=/admin/user/{{u[0]}}>{{u[1]}}</a></td>
      <td><span class="badge">{{u[2]}}</span></td>
      <td><span class="badge">{{u[3]}}</span></td>
      <td class="timestamp">{{u[4]}}</td>
      <td><a href=/admin/user/delete/{{u[0]}} style="color:var(--red);font-size:.8rem">delete</a></td>
    </tr>
    {% else %}
    <tr><td colspan=5 class="empty">No users found.</td></tr>
    {% endfor %}
  </table>
</div>
"""

# L3406 in evernothing.py
T_ADMIN_EDIT_USER = STYLE + """
<nav class="nav">
  <span class="nav-brand">&#11088; Admin</span>
  <a href=/admin/dashboard>&#8592; Dashboard</a>
  <form action="/set_theme" method="get" style="display:inline">
    <select name="t" class="theme-select" onchange="this.form.submit()" title="Switch theme">
      <option value="stellar" {% if theme != "unicorn" %}selected="selected"{% endif %}>&#11088; Stellar</option>
      <option value="unicorn" {% if theme == "unicorn" %}selected="selected"{% endif %}>&#x1F984; Unicorn</option>
      <option value="startrek" {% if theme == "startrek" %}selected="selected"{% endif %}>&#x1F596; Star Trek</option>
      <option value="shrek" {% if theme == "shrek" %}selected="selected"{% endif %}>&#127807; Shrek</option>
      <option value="lotr" {% if theme == "lotr" %}selected="selected"{% endif %}>&#9770; LOTR</option>
    </select>
  </form>
  <a href=/logout class="nav-logout">Logout</a>
</nav>
<div class="container">
  <h3>Edit User</h3>
  {% if error %}<err>{{error}}</err>{% endif %}
  <p style="color:#666;font-size:.85rem">Passwords are hashed and cannot be displayed. You can only reset them.</p>
  <div class="card" style="max-width:500px">
    <form method=post>
      <input type=hidden name=csrf_token value="{{ csrf_token() }}">
      <label>Current Username</label>
      <input value="{{user[1]}}" readonly style="opacity:.6">
      <label>New Username</label>
      <input name=new_username autofocus>
      <label>New Password <span style="color:#555">(leave blank to keep)</span></label>
      <input name=new_password type=password>
      <label>Last Login</label>
      <input name=last_login value="{{user[2] if user[2] else 'Never'}}" readonly style="opacity:.6">
      <div class="btn-group">
        <button class="btn btn-primary">Update</button>
        <a href=/admin/dashboard class="btn">Cancel</a>
      </div>
    </form>
  </div>
</div>
"""

# L3445 in evernothing.py
T_ADMIN_EDIT_USER_CONFIRM = STYLE + """
<nav class="nav">
  <span class="nav-brand">&#11088; Admin</span>
  <a href=/admin/dashboard>Dashboard</a>
  <form action="/set_theme" method="get" style="display:inline">
    <select name="t" class="theme-select" onchange="this.form.submit()" title="Switch theme">
      <option value="stellar" {% if theme != "unicorn" %}selected="selected"{% endif %}>&#11088; Stellar</option>
      <option value="unicorn" {% if theme == "unicorn" %}selected="selected"{% endif %}>&#x1F984; Unicorn</option>
      <option value="startrek" {% if theme == "startrek" %}selected="selected"{% endif %}>&#x1F596; Star Trek</option>
      <option value="shrek" {% if theme == "shrek" %}selected="selected"{% endif %}>&#127807; Shrek</option>
      <option value="lotr" {% if theme == "lotr" %}selected="selected"{% endif %}>&#9770; LOTR</option>
    </select>
  </form>
  <a href=/logout class="nav-logout">Logout</a>
</nav>
<div class="container">
  <div class="confirm-box">
    <h3>Confirm User Change</h3>
    <p>Change username from <b>{{user[1]}}</b> to <b>{{new_name}}</b>?</p>
    {% if new_pass %}<p>Password will also be changed.</p>{% endif %}
    <form method=post>
      <input type=hidden name=csrf_token value="{{ csrf_token() }}">
      <input type=hidden name=new_username value="{{new_name}}">
      <input type=hidden name=new_password value="{{new_pass}}">
      <input type=hidden name=confirm value="yes">
      <div class="btn-group">
        <button class="btn btn-primary">Yes, Change</button>
        <a href=/admin/dashboard class="btn">Cancel</a>
      </div>
    </form>
  </div>
</div>
"""

# L3479 in evernothing.py
T_ADMIN_DELETE_USER = STYLE + """
<nav class="nav">
  <span class="nav-brand">&#11088; Admin</span>
  <a href=/admin/dashboard>&#8592; Dashboard</a>
  <form action="/set_theme" method="get" style="display:inline">
    <select name="t" class="theme-select" onchange="this.form.submit()" title="Switch theme">
      <option value="stellar" {% if theme != "unicorn" %}selected="selected"{% endif %}>&#11088; Stellar</option>
      <option value="unicorn" {% if theme == "unicorn" %}selected="selected"{% endif %}>&#x1F984; Unicorn</option>
      <option value="startrek" {% if theme == "startrek" %}selected="selected"{% endif %}>&#x1F596; Star Trek</option>
      <option value="shrek" {% if theme == "shrek" %}selected="selected"{% endif %}>&#127807; Shrek</option>
      <option value="lotr" {% if theme == "lotr" %}selected="selected"{% endif %}>&#9770; LOTR</option>
    </select>
  </form>
  <a href=/logout class="nav-logout">Logout</a>
</nav>
<div class="container">
  <div class="confirm-box">
    <h3>Delete User</h3>
    <p>Are you sure you want to delete <b>{{user[1]}}</b>?</p>
    <p style="color:var(--red);font-size:.85rem">All notes, folders, and history for this user will be permanently deleted.</p>
    <form method=post>
      <input type=hidden name=csrf_token value="{{ csrf_token() }}">
      <div class="btn-group">
        <button class="btn btn-danger">Yes, Delete User</button>
        <a href=/admin/dashboard class="btn">Cancel</a>
      </div>
    </form>
  </div>
</div>
"""

# L3510 in evernothing.py
T_FORGOT_PASSWORD = STYLE + """
<div style="min-height:100vh;display:flex;align-items:center;justify-content:center">
  <div class="card" style="width:100%;max-width:400px">
    <h2 style="text-align:center;margin-bottom:4px">&#127775;EverNothing</h2>
    <p style="text-align:center;color:#666;font-size:.85rem;margin-bottom:20px">Reset your password</p>
    {% if message %}<p style="color:#0c0;text-align:center">{{message}}</p>{% endif %}
    <form method=post>
      <input type=hidden name=csrf_token value="{{ csrf_token() }}">
      <label>Email Address</label>
      <input name=email type=email required autofocus>
      <div class="btn-group" style="margin-top:16px">
        <button class="btn btn-primary" style="flex:1;justify-content:center">Send Reset Link</button>
      </div>
    </form>
    <p style="text-align:center;margin-top:16px;font-size:.85rem"><a href=/login>Back to login</a></p>
  </div>
</div>
"""

# L3529 in evernothing.py
T_RESET_PASSWORD = STYLE + """
<div style="min-height:100vh;display:flex;align-items:center;justify-content:center">
  <div class="card" style="width:100%;max-width:400px">
    <h2 style="text-align:center;margin-bottom:20px">&#127775;Reset Password</h2>
    {% if error %}<err>{{error}}</err>{% endif %}
    <form method=post>
      <input type=hidden name=csrf_token value="{{ csrf_token() }}">
      <label>New Password</label>
      <input type=password name=password required autofocus>
      <div class="btn-group" style="margin-top:16px">
        <button class="btn btn-primary" style="flex:1;justify-content:center">Reset Password</button>
      </div>
    </form>
  </div>
</div>
"""

# L3546 in evernothing.py
T_AUDIT_REPORT = STYLE + """
<nav class="nav">
  <span class="nav-brand">&#11088; EverNothing</span>
  <a href=/>&#8592; Home</a>
  <form action="/set_theme" method="get" style="display:inline">
    <select name="t" class="theme-select" onchange="this.form.submit()" title="Switch theme">
      <option value="stellar" {% if theme != "unicorn" %}selected="selected"{% endif %}>&#11088; Stellar</option>
      <option value="unicorn" {% if theme == "unicorn" %}selected="selected"{% endif %}>&#x1F984; Unicorn</option>
      <option value="startrek" {% if theme == "startrek" %}selected="selected"{% endif %}>&#x1F596; Star Trek</option>
      <option value="shrek" {% if theme == "shrek" %}selected="selected"{% endif %}>&#127807; Shrek</option>
      <option value="lotr" {% if theme == "lotr" %}selected="selected"{% endif %}>&#9770; LOTR</option>
    </select>
  </form>
  <a href=/logout class="nav-logout">Logout</a>
</nav>
<div class="container">
  <h3>Audit Report</h3>
  <table>
    <tr><th>Time</th><th>Action</th><th>Entity</th><th>Old Values</th><th>New Values</th><th>IP</th></tr>
    {% for log in logs %}
    <tr>
      <td class="timestamp">{{log.timestamp}}</td>
      <td><span class="tag-{{log.action|lower}}">{{log.action}}</span></td>
      <td style="font-size:.8rem">{{log.entity}}</td>
      <td style="font-size:.8rem">{% for k,v in log.old.items() %}<b>{{k}}:</b> {{v}}<br>{% endfor %}</td>
      <td style="font-size:.8rem">{% for k,v in log.new.items() %}<b>{{k}}:</b> {{v}}<br>{% endfor %}</td>
      <td style="font-size:.75rem;color:#666">{{log.ip}}</td>
    </tr>
    {% else %}
    <tr><td colspan=6 class="empty">No audit records.</td></tr>
    {% endfor %}
  </table>
</div>
"""

# L3581 in evernothing.py
T_SESSIONS = STYLE + """
<nav class="nav">
  <span class="nav-brand">&#11088; EverNothing</span>
  <a href=/>&#8592; Home</a>
  <form action="/set_theme" method="get" style="display:inline">
    <select name="t" class="theme-select" onchange="this.form.submit()" title="Switch theme">
      <option value="stellar" {% if theme != "unicorn" %}selected="selected"{% endif %}>&#11088; Stellar</option>
      <option value="unicorn" {% if theme == "unicorn" %}selected="selected"{% endif %}>&#x1F984; Unicorn</option>
      <option value="startrek" {% if theme == "startrek" %}selected="selected"{% endif %}>&#x1F596; Star Trek</option>
      <option value="shrek" {% if theme == "shrek" %}selected="selected"{% endif %}>&#127807; Shrek</option>
      <option value="lotr" {% if theme == "lotr" %}selected="selected"{% endif %}>&#9770; LOTR</option>
    </select>
  </form>
  <a href=/logout class="nav-logout">Logout</a>
</nav>
<div class="container">
  <h3>Login Sessions</h3>
  <p style="color:#666;font-size:.85rem;margin-bottom:16px">Up to 3 concurrent sessions allowed. Revoke any you don't recognize.</p>
  <table>
    <tr><th>Login Time</th><th>Status</th><th>IP Address</th><th>Device</th><th></th></tr>
    {% for s in sessions %}
    <tr {% if s.is_current %}style="background:var(--bg3)"{% endif %}>
      <td class="timestamp">{{s.login_time}}</td>
      <td>
        {% if s.is_current %}<span style="color:#0c0">&#9679; Current</span>
        {% elif s.logout_time == 'Active' %}<span style="color:var(--gold-dim)">Active</span>
        {% else %}<span style="color:#555">{{s.logout_time}}</span>{% endif %}
      </td>
      <td style="font-size:.85rem">{{s.ip}}</td>
      <td style="font-size:.8rem;color:#888">{{s.user_agent}}</td>
      <td>
        {% if not s.is_current and s.logout_time == 'Active' %}
        <a href=/session/revoke/{{s.session_id}} class="btn btn-sm btn-danger">Revoke</a>
        {% endif %}
      </td>
    </tr>
    {% endfor %}
  </table>
</div>
"""

# L3622 in evernothing.py
T_ADMIN_AUDIT_LOGS = STYLE + """
<nav class="nav">
  <span class="nav-brand">&#11088; Admin</span>
  <a href=/admin/dashboard>&#8592; Dashboard</a>
  <a href="javascript:location.reload()" style="color:#0c0">Refresh</a>
  <form action="/set_theme" method="get" style="display:inline">
    <select name="t" class="theme-select" onchange="this.form.submit()" title="Switch theme">
      <option value="stellar" {% if theme != "unicorn" %}selected="selected"{% endif %}>&#11088; Stellar</option>
      <option value="unicorn" {% if theme == "unicorn" %}selected="selected"{% endif %}>&#x1F984; Unicorn</option>
      <option value="startrek" {% if theme == "startrek" %}selected="selected"{% endif %}>&#x1F596; Star Trek</option>
      <option value="shrek" {% if theme == "shrek" %}selected="selected"{% endif %}>&#127807; Shrek</option>
      <option value="lotr" {% if theme == "lotr" %}selected="selected"{% endif %}>&#9770; LOTR</option>
    </select>
  </form>
  <a href=/logout class="nav-logout">Logout</a>
</nav>
<div class="container">
  <h3>Audit Logs</h3>
  <form method="get" class="card" style="margin-bottom:16px">
    <div class="form-row">
      <div>
        <label>Username</label>
        <input name="user" value="{{user_filter}}" placeholder="Filter by user">
      </div>
      <div>
        <label>Action</label>
        <select name="action">
          <option value="">All Actions</option>
          <option value="CREATE" {% if action_filter=='CREATE' %}selected{% endif %}>CREATE</option>
          <option value="UPDATE" {% if action_filter=='UPDATE' %}selected{% endif %}>UPDATE</option>
          <option value="DELETE" {% if action_filter=='DELETE' %}selected{% endif %}>DELETE</option>
        </select>
      </div>
      <div>
        <label>Entity</label>
        <select name="entity">
          <option value="">All Entities</option>
          <option value="note" {% if entity_filter=='note' %}selected{% endif %}>Note</option>
          <option value="attachment" {% if entity_filter=='attachment' %}selected{% endif %}>Attachment</option>
          <option value="user" {% if entity_filter=='user' %}selected{% endif %}>User</option>
        </select>
      </div>
      <div>
        <label>Limit</label>
        <select name="limit">
          <option value="50" {% if limit==50 %}selected{% endif %}>50</option>
          <option value="100" {% if limit==100 %}selected{% endif %}>100</option>
          <option value="500" {% if limit==500 %}selected{% endif %}>500</option>
          <option value="1000" {% if limit==1000 %}selected{% endif %}>1000</option>
        </select>
      </div>
    </div>
    <div class="btn-group">
      <button class="btn btn-primary">Filter</button>
      <a href=/admin/audit_logs class="btn">Clear</a>
      <span style="margin-left:auto;color:#666;font-size:.85rem">{{logs|length}} records</span>
    </div>
  </form>
  <table>
    <tr><th>Time</th><th>User</th><th>Action</th><th>Entity</th><th>Old</th><th>New</th><th>IP</th></tr>
    {% for log in logs %}
    <tr>
      <td class="timestamp">{{log.timestamp}}</td>
      <td>{{log.user}}</td>
      <td><span class="tag-{{log.action|lower}}">{{log.action}}</span></td>
      <td style="font-size:.8rem">{{log.entity}}</td>
      <td style="font-size:.8rem">{% for k,v in log.old.items() %}<b>{{k}}:</b> {{v}}<br>{% endfor %}</td>
      <td style="font-size:.8rem">{% for k,v in log.new.items() %}<b>{{k}}:</b> {{v}}<br>{% endfor %}</td>
      <td style="font-size:.75rem;color:#666">{{log.ip}}</td>
    </tr>
    {% else %}
    <tr><td colspan=7 class="empty">No audit logs found.</td></tr>
    {% endfor %}
  </table>
</div>
"""

# L3873 in evernothing.py
T_ADMIN_S3_BACKUPS = STYLE + """
<h3>S3 Backups</h3>
<a href=/admin/dashboard>Back to Dashboard</a> | <a href=/logout>Logout</a>
{% if message %}<p style="color:#0f0;">{{message}}</p>{% endif %}
{% if error %}<p style="color:red;">{{error}}</p>{% endif %}
<p>Database backups stored in S3 bucket: <b>{{ config.get('S3_BUCKET_NAME', 'N/A') }}</b></p>
<table style="width:100%; border-collapse:collapse; margin-top:20px;">
<tr style="border-bottom:2px solid red;">
<th style="text-align:left; padding:8px;">Backup File</th>
<th style="text-align:left; padding:8px;">Size (bytes)</th>
<th style="text-align:left; padding:8px;">Last Modified</th>
<th style="text-align:left; padding:8px;">Action</th>
</tr>
{% if confirm_key %}
<p>Restore backup <b>{{confirm_key}}</b> to local file?</p>
<form method=post action="/admin/s3_restore/{{confirm_key}}">
<input type=hidden name=csrf_token value="{{ csrf_token() }}">
<button>Yes, Restore</button> <a href=/admin/s3_backups class=cancel>Cancel</a>
</form>
{% else %}
<table style="width:100%; border-collapse:collapse; margin-top:20px;">
<tr style="border-bottom:2px solid red;">
<th style="text-align:left; padding:8px;">Backup File</th>
<th style="text-align:left; padding:8px;">Size (bytes)</th>
<th style="text-align:left; padding:8px;">Last Modified</th>
<th style="text-align:left; padding:8px;">Action</th>
</tr>
{% for backup in backups %}
<tr style="border-bottom:1px solid #333;">
<td style="padding:8px; font-size:small;">{{backup.key}}</td>
<td style="padding:8px;">{{backup.size}}</td>
<td style="padding:8px;">{{backup.modified}}</td>
<td style="padding:8px;"><a href="/admin/s3_restore/{{backup.key}}" style="color:#0f0;">[Restore]</a></td>
</tr>
{% else %}
<tr><td colspan="4" style="padding:20px; text-align:center; color:#888;">No backups found or S3 not configured</td></tr>
{% endfor %}
</table>
{% endif %}
"""
