# main_with_auth.py
"""
Main Application Entry Point with Authentication
This version includes Google OAuth login and quota management.
"""

import streamlit as st
from app.login_page import render_login_page
from app.state import initialize_session_state
from app.navigation import render_sidebar, display_page
from auth.session_manager import SessionManager
from auth.quota_manager import QuotaManager
from auth.user_activity import UserActivityLogger
import streamlit.components.v1 as components

# Disable cache clearing popup
def disabled_cache_clear(*args, **kwargs):
    pass

if hasattr(st, 'cache_data'):
    st.cache_data.clear = disabled_cache_clear
if hasattr(st, 'cache_resource'):  
    st.cache_resource.clear = disabled_cache_clear

# Page Configuration
st.set_page_config(
    layout="wide",
    page_title="Google Ads Simulator",
    page_icon="📊",
    initial_sidebar_state="collapsed"
)

# Disable cache popup
components.html("""
<script>
document.addEventListener('keydown', function(event) {
    if (event.key === 'c' || event.key === 'C') {
        event.preventDefault();
        event.stopPropagation();
        return false;
    }
}, true);
</script>
""", height=0)

def render_quota_indicator():
    """Render quota indicator in sidebar."""
    user_email = SessionManager.get_user_email()
    if not user_email:
        return
    
    quota_manager = QuotaManager()
    quota_display = quota_manager.get_quota_display_data(user_email)
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("📊 Your Quotas")
    
    status_colors = {
        'healthy': '🟢',
        'warning': '🟡',
        'critical': '🔴'
    }
    status_icon = status_colors.get(quota_display['overall_status'], '⚪')
    
    st.sidebar.write(f"{status_icon} Status: {quota_display['overall_status'].title()}")
    
    for quota in quota_display['quotas']:
        st.sidebar.caption(f"{quota['name']}: {quota['usage']}/{quota['limit']}")
        st.sidebar.progress(
            min(quota['percentage'] / 100, 1.0),
            text=f"{quota['remaining']} remaining"
        )
    
    reset_time = quota_display.get('reset_time', 0)
    st.sidebar.caption(f"⏰ Resets in {reset_time} minutes")
    
    if st.sidebar.button("📈 View Detailed Usage", use_container_width=True):
        st.session_state.page_selection = "Quota Dashboard"
        st.rerun()

def main():
    """Main application logic with authentication."""
    
    # ========== AUTHENTICATION CHECK ==========
    if not SessionManager.is_authenticated():
        render_login_page()
        return
    
    # Update activity
    SessionManager.update_activity()
    
    # ========== SIDEBAR USER INFO ==========
    with st.sidebar:
        user_name = SessionManager.get_user_name()
        user_email = SessionManager.get_user_email()
        
        st.write(f"👤 **{user_name}**")
        st.caption(user_email)
        
        if st.button("🚪 Logout", use_container_width=True):
            UserActivityLogger.log_activity(user_email, 'logout')
            SessionManager.end_session()
            st.rerun()
        
        render_quota_indicator()
    
    # ========== MAIN APP ==========
    initialize_session_state()
    page = render_sidebar()
    display_page(page)

if __name__ == "__main__":
    main()
