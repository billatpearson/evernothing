"""
Evernothing_Android
Android/Termux Flask application with periodic S3 checkpointing.
Source lives in android_app/ — this module provides the package boundary.
"""
import os, sys
_android_app = os.path.join(os.path.dirname(__file__), '..', 'android_app')
if _android_app not in sys.path:
    sys.path.insert(0, _android_app)
