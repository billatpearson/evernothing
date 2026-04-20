"""
main.py — EverNothing application entry point (separation-of-concerns architecture).

Module responsibilities:
  Evernothing_Web/      Flask app object, config, hooks
  Evernothing_DB/       Database connection, schema, backup
  Evernothing_Security/ Encryption, auth, validation, headers
  Evernothing_Connect/  S3 sync, bucket hardening, delta queue
  Evernothing_Theme/    CSS themes, theme switching
  Evernothing_Admin/    Admin routes
  Evernothing_Android/  Android/Termux app
  Evernothing_Test/     Test infrastructure
  Evernothing_UI/       Templates (HTML/CSS)

During the transition period, routes are still registered in evernothing.py.
This file bootstraps the new module structure and delegates to the monolith.
"""
import os, sys

# Ensure project root is on path
_ROOT = os.path.dirname(os.path.abspath(__file__))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

# 1. Bootstrap DB
from Evernothing_DB.database import init_db, backup_database, compress_old_backups, DB
os.makedirs(os.path.dirname(DB), exist_ok=True)
init_db()
backup_database()
compress_old_backups()

# 2. Bootstrap security (registers before_request / after_request hooks)
import Evernothing_Security.security  # noqa: side-effect registration

# 3. Bootstrap S3 connectivity
from Evernothing_Connect.s3_sync import restore_from_s3
restore_from_s3()

# 4. Import the monolith (registers all routes on the shared app object)
#    This will be replaced module-by-module as routes are extracted.
import evernothing  # noqa

# 5. Get the app for gunicorn / direct run
from Evernothing_Web.app import app

if __name__ == '__main__':
    from Evernothing_Web.app import logger
    import os as _os
    ssl_cert = _os.environ.get('SSL_CERT', _os.path.join(_ROOT, 'Startup', 'cert.pem'))
    ssl_key  = _os.environ.get('SSL_KEY',  _os.path.join(_ROOT, 'Startup', 'key.pem'))
    use_ssl  = _os.path.exists(ssl_cert) and _os.path.exists(ssl_key)
    ssl_ctx  = (ssl_cert, ssl_key) if use_ssl else None
    if not use_ssl:
        logger.warning('SSL cert/key not found — running without HTTPS.')
    app.run(host='0.0.0.0', port=5443 if use_ssl else 5000, ssl_context=ssl_ctx)
