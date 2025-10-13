"""
Admin Controller - Secure admin access management
Only accessible programmatically, NOT through Streamlit pages/

This module provides:
- Admin user identification
- Access control decorators
- Admin-only functionality protection

SECURITY: Admin emails are now stored in .streamlit/secrets.toml
"""

import streamlit as st
from typing import Optional, List
from functools import wraps

# ============================================
# ADMIN CONFIGURATION - READ FROM SECRETS
# ============================================

def get_admin_emails() -> List[str]:
    """
    Get admin emails from secrets.toml
    
    Returns:
        List of authorized admin email addresses
    """
    try:
        # Try to get from secrets.toml
        if "admin" in st.secrets and "admin_emails" in st.secrets["admin"]:
            admin_emails = st.secrets["admin"]["admin_emails"]
            
            # Handle both list and single string
            if isinstance(admin_emails, list):
                return [email.strip().lower() for email in admin_emails]
            else:
                return [admin_emails.strip().lower()]
        
        # Fallback if not configured
        st.warning("""
        ⚠️ **Admin configuration not found in secrets.toml**
        
        Please add the following to `.streamlit/secrets.toml`:
        
        ```toml
        [admin]
        enabled = true
        admin_emails = [
            "your.email@example.com",
        ]
        ```
        """)
        return []
        
    except Exception as e:
        st.error(f"❌ Error loading admin configuration: {e}")
        return []


def is_admin_enabled() -> bool:
    """
    Check if admin functionality is enabled
    
    Returns:
        True if admin is enabled in config
    """
    try:
        return st.secrets.get("admin", {}).get("enabled", False)
    except:
        return False


# ============================================
# ADMIN IDENTIFICATION
# ============================================

def is_admin_user(email: Optional[str] = None) -> bool:
    """
    Check if user has admin privileges
    
    Args:
        email: User email. If None, gets from current session
        
    Returns:
        True if user is admin, False otherwise
    """
    # Check if admin is enabled
    if not is_admin_enabled():
        return False
    
    if email is None:
        # Try to get email from session state first
        email = st.session_state.get('user_email')
        
        # If not in session, try to get from OAuth
        if not email:
            try:
                from core.auth import GoogleAuthManager
                auth = GoogleAuthManager()
                user = auth.get_user()
                if not user:
                    return False
                email = user.get('email', '')
            except Exception:
                return False
    
    if not email:
        return False
    
    # Get admin emails from secrets
    admin_emails = get_admin_emails()
    
    # Case-insensitive email matching
    return email.lower().strip() in admin_emails


def get_admin_level(email: Optional[str] = None) -> str:
    """
    Get admin privilege level
    
    Returns:
        'super_admin', 'admin', or 'user'
    """
    if not is_admin_user(email):
        return 'user'
    
    # For now, all admins are treated equally
    # In future, implement role-based access
    return 'admin'


# ============================================
# ACCESS CONTROL
# ============================================

def require_admin(func):
    """
    Decorator to protect admin-only functions
    Stops execution if user is not admin
    
    Usage:
        @require_admin
        def admin_function():
            # Only accessible by admins
            pass
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not is_admin_user():
            show_admin_access_denied()
            st.stop()
        return func(*args, **kwargs)
    return wrapper


def check_admin_access(silent: bool = False) -> bool:
    """
    Check admin access without stopping execution
    
    Args:
        silent: If True, don't show error message
        
    Returns:
        True if user is admin, False otherwise
    """
    is_admin = is_admin_user()
    
    if not is_admin and not silent:
        st.error("🚫 Admin access required")
    
    return is_admin


# ============================================
# USER FEEDBACK
# ============================================

def show_admin_access_denied():
    """Show access denied message for admin features"""
    st.error("🚫 **Access Denied**")
    st.warning("""
    ### Administrative Access Required
    
    You don't have permission to access administrative features.
    
    This area is restricted to authorized administrators only.
    """)
    
    with st.expander("ℹ️ Why am I seeing this?"):
        st.write("""
        **Admin features are restricted to:**
        - System administrators
        - Authorized staff members
        - Designated moderators
        
        **If you believe you should have admin access:**
        1. Verify you're logged in with the correct account
        2. Contact the system administrator
        3. Provide your email address for verification
        
        **Contact Information:**
        - Email: me3tpatil@gmail.com
        - Subject: "Admin Access Request"
        """)


def show_admin_badge():
    """Display admin badge in UI"""
    st.sidebar.markdown("---")
    st.sidebar.success("👨‍💼 **Admin Mode Active**")


def show_admin_config_status():
    """
    Display admin configuration status
    For debugging/setup purposes
    """
    try:
        enabled = is_admin_enabled()
        admin_emails = get_admin_emails()
        
        st.subheader("🔐 Admin Configuration Status")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if enabled:
                st.success("✅ Admin system enabled")
            else:
                st.error("❌ Admin system disabled")
        
        with col2:
            st.metric("Authorized Admins", len(admin_emails))
        
        if admin_emails:
            with st.expander("👥 View Admin List"):
                for email in admin_emails:
                    st.write(f"• {email}")
        else:
            st.warning("⚠️ No admin emails configured")
            
    except Exception as e:
        st.error(f"Error checking admin config: {e}")


# ============================================
# ADMIN UTILITIES
# ============================================

def log_admin_action(action: str, details: dict = None):
    """
    Log admin actions for audit trail
    
    Args:
        action: Description of action taken
        details: Additional details about the action
    """
    try:
        from utils.tracking import log_user_activity
        
        user_email = st.session_state.get('user_email', 'unknown')
        
        log_data = {
            'user': user_email,
            'action': f"ADMIN: {action}",
            'timestamp': st.session_state.get('session_start_time'),
            'details': details or {}
        }
        
        log_user_activity(log_data)
        
    except Exception as e:
        # Don't fail on logging errors
        print(f"Failed to log admin action: {e}")


def get_admin_menu_items() -> List[str]:
    """
    Get list of admin menu items based on user permissions
    
    Returns:
        List of admin menu options
    """
    base_items = [
        "📊 Dashboard",
        "👥 User Management",
        "📝 Activity Logs",
        "⚙️ System Settings"
    ]
    
    # Super admins get additional options
    admin_level = get_admin_level()
    if admin_level == 'super_admin':
        base_items.extend([
            "🔒 Access Control",
            "🗄️ Database Admin",
            "🔧 Advanced Settings"
        ])
    
    return base_items


# ============================================
# ADMIN DASHBOARD TRIGGER
# ============================================

def trigger_admin_dashboard():
    """
    Set session state to show admin dashboard
    Called when admin clicks admin dashboard button
    """
    if not is_admin_user():
        show_admin_access_denied()
        st.stop()
    
    st.session_state.show_admin_dashboard = True
    # Don't modify page_selection - it's widget-bound
    
    # Log the access
    log_admin_action("Accessed Admin Dashboard")


def hide_admin_dashboard():
    """Return to normal user view"""
    st.session_state.show_admin_dashboard = False
    # Don't modify page_selection - it's widget-bound


# ============================================
# SESSION STATE HELPERS
# ============================================

def initialize_admin_state():
    """Initialize admin-related session state variables"""
    if 'show_admin_dashboard' not in st.session_state:
        st.session_state.show_admin_dashboard = False
    
    if 'admin_current_view' not in st.session_state:
        st.session_state.admin_current_view = "dashboard"


def is_in_admin_mode() -> bool:
    """Check if currently in admin mode"""
    return st.session_state.get('show_admin_dashboard', False) and is_admin_user()


# ============================================
# SECURITY ENHANCEMENTS
# ============================================

def get_session_timeout() -> int:
    """
    Get admin session timeout in minutes
    
    Returns:
        Timeout in minutes (default: 60)
    """
    try:
        return int(st.secrets.get("admin", {}).get("session_timeout_minutes", 60))
    except:
        return 60


def is_2fa_required() -> bool:
    """
    Check if 2FA is required for admin access
    
    Returns:
        True if 2FA is required
    """
    try:
        return st.secrets.get("admin", {}).get("require_2fa", False)
    except:
        return False
