"""
main.py — EverNothing application entry point (separation-of-concerns architecture).

Module responsibilities:
  Evernothing_Web/      Flask app object, config, hooks, routes
  Evernothing_DB/       Database connection, schema, backup
  Evernothing_Security/ Encryption, auth, validation, headers
  Evernothing_Connect/  S3 sync, bucket hardening, delta queue
  Evernothing_Theme/    CSS themes, theme switching
  Evernothing_Admin/    Admin routes
  Evernothing_Android/  Android/Termux app
  Evernothing_Test/     Test infrastructure
  Evernothing_UI/       Templates (HTML/CSS)
"""
import os, sys

_ROOT = os.path.dirname(os.path.abspath(__file__))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

# 1. Bootstrap DB
from Evernothing_DB.database import init_db, backup_database, compress_old_backups, prune_old_backups, DB
os.makedirs(os.path.dirname(DB), exist_ok=True)
init_db()
backup_database()
compress_old_backups()
prune_old_backups()

# 2. Bootstrap security hooks (before_request / after_request)
import Evernothing_Security.security  # noqa

# 3. S3 restore on startup
from Evernothing_Connect.s3_sync import restore_from_s3
restore_from_s3()

# 3a. Start the S3 pull worker (Option B multi-device replication).
#     Safe no-op when S3 isn't configured or app is in TESTING mode.
from Evernothing_Connect.s3_pull import start_pull_worker
start_pull_worker()

# 4. Register all route modules (each imports app and decorates routes)
import Evernothing_Web.routes.auth      # noqa
import Evernothing_Web.routes.notes     # noqa
import Evernothing_Web.routes.sessions  # noqa
import Evernothing_Web.routes.api       # noqa
import Evernothing_Admin.admin_routes   # noqa

# 5. Import templates from monolith (still needed during transition)
import evernothing  # noqa — registers error handlers and template constants

from Evernothing_Web.app import app

if __name__ == '__main__':
    import os as _os
    from Evernothing_Web.app import logger
    ssl_cert = _os.environ.get('SSL_CERT', _os.path.join(_ROOT, 'Startup', 'cert.pem'))
    ssl_key  = _os.environ.get('SSL_KEY',  _os.path.join(_ROOT, 'Startup', 'key.pem'))
    use_ssl  = _os.path.exists(ssl_cert) and _os.path.exists(ssl_key)
    ssl_ctx  = (ssl_cert, ssl_key) if use_ssl else None
    if not use_ssl:
        logger.warning('SSL cert/key not found — running without HTTPS.')
    app.run(host='0.0.0.0', port=5443 if use_ssl else 5000, ssl_context=ssl_ctx)
