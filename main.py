# ========================================
# LOGGING CONFIGURATION - MUST BE FIRST
# ========================================
import os
import sys

# Suppress warnings BEFORE any other imports
import warnings
warnings.filterwarnings('ignore')
warnings.simplefilter('ignore')

# Suppress torch/tensorflow warnings AGGRESSIVELY
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['PYTORCH_ENABLE_MPS_FALLBACK'] = '1'

# Configure logging before importing any other modules
try:
    from config.logging_config import setup_logging
except ImportError:
    # Fallback if logging_config not found
    def setup_logging(debug_mode=False):
        import logging
        logging.basicConfig(level=logging.WARNING)

# Enable debug mode via environment variable: DEBUG_MODE=true
DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"
setup_logging(debug_mode=DEBUG_MODE)

# ========================================
# MINIMAL STREAMLIT IMPORTS
# ========================================
import streamlit as st
import streamlit.components.v1 as components

# --- MUST BE FIRST STREAMLIT COMMAND ---
TEST_MODE = os.getenv("TEST_MODE", "false").lower() == "true"

if TEST_MODE:
    page_title = "Google Ads Simulator - TEST MODE"
    page_icon = "🧪"
else:
    page_title = "Google Ads Simulator"
    page_icon = "📊"

st.set_page_config(
    layout="wide",
    page_title=page_title,
    page_icon=page_icon
)

# ========================================
# LAZY IMPORTS - Load only what's needed
# ========================================
def lazy_import_state():
    """Lazy import state management"""
    from app.state import initialize_session_state
    return initialize_session_state

def lazy_import_navigation():
    """Lazy import navigation"""
    from app.navigation import render_sidebar, display_page
    return render_sidebar, display_page

def lazy_import_auth():
    """Lazy import authentication"""
    from core.auth import require_auth, GoogleAuthManager
    return require_auth, GoogleAuthManager

def lazy_import_tracking():
    """Lazy import tracking"""
    from utils.tracking import inject_clarity
    return inject_clarity

def lazy_import_login_gate():
    """Lazy import login gate"""
    from app.login_gate import integrate_with_oauth_login
    return integrate_with_oauth_login

def lazy_import_chatbot():
    """Lazy import chatbot"""
    from app.chatbot import render_dialogflow_chat
    return render_dialogflow_chat

# ========================================
# INITIALIZATION - Deferred until needed
# ========================================

# Initialize state only once
_state_initialized = False

def ensure_state_initialized():
    """Ensure state is initialized only once"""
    global _state_initialized
    if not _state_initialized:
        init_func = lazy_import_state()
        init_func()
        _state_initialized = True

# ---- Inject Microsoft Clarity Tracking (Lazy) ----
def initialize_tracking():
    """Initialize tracking lazily"""
    inject_clarity = lazy_import_tracking()
    inject_clarity()

# Call tracking once
initialize_tracking()

# ---- Disable Cache Clear Popup ----
def disabled_cache_clear(*args, **kwargs):
    pass

if hasattr(st, 'cache_data'):
    st.cache_data.clear = disabled_cache_clear
if hasattr(st, 'cache_resource'):
    st.cache_resource.clear = disabled_cache_clear

components.html("""
<script>
document.addEventListener('keydown', function(event) {
    if (event.key === 'c' || event.key === 'C') {
        event.preventDefault();
        event.stopPropagation();
        return false;
    }
}, true);

window.addEventListener('load', function() {
    const observer = new MutationObserver(() => {
        const dialogs = document.querySelectorAll('[role="dialog"], .stModal, [data-testid*="modal"]');
        dialogs.forEach(dialog => {
            if (dialog.textContent && dialog.textContent.includes('Clear cache')) {
                dialog.remove();
            }
        });
        const menuItems = document.querySelectorAll('li, button, [role="menuitem"]');
        menuItems.forEach(item => {
            if (item.textContent && item.textContent.includes('Clear cache')) {
                item.style.display = 'none';
            }
        });
    });
    observer.observe(document.body, { childList: true, subtree: true });
});
</script>
""", height=0)

# --- Main Application Logic ---
def create_protected_main():
    """Create the main function with authentication decorator"""
    require_auth, GoogleAuthManager = lazy_import_auth()
    
    @require_auth
    def main():
        """Main application - protected by authentication"""
        # Initialize state lazily
        ensure_state_initialized()

        if TEST_MODE:
            st.warning("🧪 **TEST MODE ACTIVE** - Development & educational version.")

        auth = GoogleAuthManager()
        user = auth.get_user()
        if user:
            st.success(f"👋 Welcome back, **{user.get('name')}**!")

        # Lazy load navigation
        render_sidebar, display_page = lazy_import_navigation()
        
        page = render_sidebar()
        display_page(page)
        
        # RESTORED: Render DialogFlow Messenger chatbot (bottom-right corner)
        try:
            dialogflow_config = st.secrets.get("dialogflow", {})
            if dialogflow_config.get("project_id") and dialogflow_config.get("agent_id"):
                render_dialogflow_chat = lazy_import_chatbot()
                render_dialogflow_chat(
                    project_id=dialogflow_config["project_id"],
                    agent_id=dialogflow_config["agent_id"],
                    location=dialogflow_config.get("location", "us-central1")
                )
        except Exception as e:
            pass  # Silently fail if DialogFlow not configured
    
    return main


def cleanup_on_exit():
    """Clean up session data when app exits"""
    try:
        _, GoogleAuthManager = lazy_import_auth()
        auth = GoogleAuthManager()
        user = auth.get_user()
        session_tracker = auth.get_session_tracker()

        if user and session_tracker:
            from app.quota_system import get_quota_manager
            quota_mgr = get_quota_manager()
            quota_mgr.sync_all_quotas()
            
            if auth.gsheet_logger_safe and auth.gsheet_logger_safe.enabled:
                session_data = session_tracker.get_session_data()
                duration_ms = session_tracker.get_duration_ms()
                quota_summary = quota_mgr.get_quota_summary()
                
                auth.gsheet_logger_safe.log_session_end(
                    email=user.get("email"),
                    session_id=session_data["session_id"],
                    tokens_used=quota_summary['gemini']['used'],
                    operations=quota_summary['gemini']['used'],
                    duration_ms=duration_ms,
                    status="closed"
                )
    except Exception:
        pass

import atexit
atexit.register(cleanup_on_exit)

if __name__ == "__main__":
    main_func = create_protected_main()
    main_func()
