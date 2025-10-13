"""
Admin Module
Secure administrative functionality isolated from frontend
"""

from .admin_controller import (
    is_admin_user,
    require_admin,
    show_admin_access_denied,
    get_admin_emails,
    is_admin_enabled,
    initialize_admin_state
)

__all__ = [
    'is_admin_user',
    'require_admin',
    'show_admin_access_denied',
    'get_admin_emails',
    'is_admin_enabled',
    'initialize_admin_state'
]
