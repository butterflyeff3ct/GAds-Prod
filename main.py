import streamlit as st
import os
import time
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
# ✅ set_page_config() is now first Streamlit command

# ---- IMPORTS THAT USE STREAMLIT ----
from app.state import initialize_session_state
from app.navigation import render_sidebar, display_page
from core.auth import require_auth, GoogleAuthManager
from utils.tracking import inject_clarity  # import here, not before set_page_config

# ---- Inject Microsoft Clarity Tracking ----
inject_clarity()

# ---- Disable Cache Clear Popup ----
def disabled_cache_clear(*args, **kwargs):
    pass

if hasattr(st, 'cache_data'):
    st.cache_data.clear = disabled_cache_clear
if hasattr(st, 'cache_resource'):
    st.cache_resource.clear = disabled_cache_clear

components.html("""
<script>
// Disable Streamlit cache clearing popups
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
@require_auth
def main():
    """Main application - protected by authentication"""
    initialize_session_state()

    if TEST_MODE:
        st.warning("🧪 **TEST MODE ACTIVE** - Development & educational version.")

    auth = GoogleAuthManager()
    user = auth.get_user()
    if user:
        st.success(f"👋 Welcome back, **{user.get('name')}**!")

    page = render_sidebar()
    display_page(page)


def cleanup_on_exit():
    """Clean up session data when app exits"""
    try:
        auth = GoogleAuthManager()
        user = auth.get_user()
        session_tracker = auth.get_session_tracker()

        if user and session_tracker and auth.gsheet_logger_safe and auth.gsheet_logger_safe.enabled:
            session_data = session_tracker.get_session_data()
            duration_ms = session_tracker.get_duration_ms()
            
            auth.gsheet_logger_safe.log_session_end(
                email=user.get("email"),
                session_id=session_data["session_id"],
                tokens_used=session_data["tokens_used"],
                operations=session_data["operations"],
                duration_ms=duration_ms,
                status="closed"
            )
    except Exception:
        pass

import atexit
atexit.register(cleanup_on_exit)

if __name__ == "__main__":
    main()
