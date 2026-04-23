"""
Evernothing_Theme/themes.py
All CSS theme constants and theme switching logic.
Imports STYLE_STELLAR, STYLE_UNICORN, STYLE_STARTREK, STYLE_SHREK, STYLE_LOTR.
"""
from flask import session
# Import all theme CSS from the monolith during transition
# Once fully migrated, the CSS strings will live here directly.
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Evernothing_Web.app import app

# Re-export theme constants (sourced from evernothing.py during transition)
def _load_themes():
    """Lazy-load theme constants from the monolith to avoid circular imports."""
    import evernothing as _en
    return {
        'stellar':  _en.STYLE_STELLAR,
        'unicorn':  _en.STYLE_UNICORN,
        'startrek': _en.STYLE_STARTREK,
        'shrek':    _en.STYLE_SHREK,
        'lotr':     _en.STYLE_LOTR,
    }

VALID_THEMES = ('stellar', 'unicorn', 'startrek', 'shrek', 'lotr')
_CYCLE = {'stellar':'unicorn','unicorn':'startrek','startrek':'shrek','shrek':'lotr','lotr':'stellar'}

def get_style():
    """Return the CSS block for the current session theme."""
    themes = _load_themes()
    t = session.get('theme', 'stellar')
    return themes.get(t, themes['stellar'])

def cycle_theme(current: str) -> str:
    return _CYCLE.get(current, 'stellar')
