# main.py
import streamlit as st
from app.state import initialize_session_state
from app.navigation import render_sidebar, display_page
import streamlit.components.v1 as components

# ============================================================================
# AUTHENTICATION TOGGLE
# ============================================================================
# To ENABLE authentication:
#   1. Install: pip install google-auth google-auth-oauthlib sqlalchemy
#   2. Configure: config/oauth_config.yaml with your Google OAuth credentials
#   3. Set: AUTHENTICATION_ENABLED = True (below)
#
# To DISABLE authentication (development mode):
#   Set: AUTHENTICATION_ENABLED = False
# ============================================================================

AUTHENTICATION_ENABLED = True  # ← CHANGE THIS TO True TO ENABLE AUTH

# ============================================================================

# Import auth modules only if authentication is enabled
if AUTHENTICATION_ENABLED:
    try:
        from auth.session_manager import SessionManager
        from auth.quota_manager import QuotaManager
        from auth.google_oauth import GoogleOAuthManager
        from auth.user_activity import UserActivityLogger
        from database.db_manager import get_database_manager
        from datetime import datetime, timedelta
        AUTH_AVAILABLE = True
    except ImportError as e:
        st.error(f"Authentication modules not available: {e}")
        st.info("Run: pip install google-auth google-auth-oauthlib sqlalchemy")
        AUTH_AVAILABLE = False
        AUTHENTICATION_ENABLED = False
else:
    AUTH_AVAILABLE = False

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
    page_icon="📊"
)

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


def handle_oauth_callback():
    """Handle OAuth callback from Google."""
    if not AUTH_AVAILABLE:
        return
    
    query_params = st.query_params
    
    if 'code' in query_params:
        with st.spinner("🔐 Authenticating..."):
            try:
                oauth_manager = GoogleOAuthManager()
                code = query_params['code']
                authorization_response = f"{oauth_manager.oauth_config['redirect_uri']}?code={code}"
                
                user_info = oauth_manager.handle_callback(authorization_response)
                
                if user_info:
                    db_manager = get_database_manager()
                    user = db_manager.create_or_update_user(user_info)
                    
                    session_id = SessionManager.create_session(user_info)
                    expires_at = datetime.now() + timedelta(hours=2)
                    db_manager.create_session(user_info['email'], session_id, expires_at)
                    
                    UserActivityLogger.log_activity(user_info['email'], 'login')
                    db_manager.log_activity(user_info['email'], 'login', {'method': 'google_oauth'})
                    
                    st.query_params.clear()
                    st.success(f"✅ Welcome, {user_info['name']}!")
                    st.balloons()
                    st.rerun()
                else:
                    st.error("❌ Authentication failed")
                    st.query_params.clear()
            except Exception as e:
                st.error(f"Authentication error: {e}")
                st.query_params.clear()

def render_quota_in_sidebar():
    """Render quota indicator."""
    if not AUTH_AVAILABLE:
        return
        
    user_email = SessionManager.get_user_email()
    if not user_email:
        return
    
    quota_manager = QuotaManager()
    quota_display = quota_manager.get_quota_display_data(user_email)
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("📊 Quotas")
    
    for quota in quota_display['quotas'][:3]:
        st.sidebar.caption(f"{quota['name']}: {quota['usage']}/{quota['limit']}")
        st.sidebar.progress(
            min(quota['percentage'] / 100, 1.0),
            text=f"{quota['remaining']} left"
        )
    
    reset_time = quota_display.get('reset_time', 0)
    st.sidebar.caption(f"⏰ Resets: {reset_time}m")

def main():
    """Main application logic."""
    
    # Handle OAuth callback
    if AUTHENTICATION_ENABLED and AUTH_AVAILABLE:
        handle_oauth_callback()
    
    # Check authentication
    if AUTHENTICATION_ENABLED and AUTH_AVAILABLE:
        is_authenticated = SessionManager.is_authenticated()
        
        if not is_authenticated:
            # Simple, clean login interface
            st.title("🔐 Google Ads Simulator")
            st.markdown("### Welcome! Please sign in to continue")
            
            # Centered login button
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button("🔐 **Sign in with Google**", type="primary", use_container_width=True):
                    if AUTH_AVAILABLE:
                        oauth_manager = GoogleOAuthManager()
                        if oauth_manager.is_configured():
                            auth_url = oauth_manager.get_authorization_url()
                            if auth_url:
                                st.markdown(f'<a href="{auth_url}" target="_blank" style="display:none" id="main_oauth_link"></a>', unsafe_allow_html=True)
                                st.markdown("""
                                <script>
                                    document.getElementById('main_oauth_link').click();
                                </script>
                                """, unsafe_allow_html=True)
                                st.success("🔗 Opening Google login in new tab...")
                        else:
                            st.error("🔧 OAuth not configured. Please contact administrator.")
                    else:
                        st.error("🔧 Authentication system not available.")
            
            # Simple instructions
            st.markdown("""
            **📋 Steps:**
            1. Click "Sign in with Google" above
            2. Sign in with your Google account  
            3. Grant permissions
            4. Return to this tab - you'll be logged in automatically
            """)
            
            return
        
        # Authenticated - update activity
        SessionManager.update_activity()
        
        # Show user in sidebar
        with st.sidebar:
            user_name = SessionManager.get_user_name()
            user_email = SessionManager.get_user_email()
            
            st.markdown(f"### 👤 {user_name}")
            st.caption(user_email)
            
            if st.button("🚪 Logout", use_container_width=True):
                UserActivityLogger.log_activity(user_email, 'logout')
                SessionManager.end_session()
                st.rerun()
            
            render_quota_in_sidebar()
    else:
        # No authentication - dev mode
        if not AUTHENTICATION_ENABLED:
            with st.sidebar:
                st.info("🛠️ **DEV MODE**")
                st.caption("Authentication disabled")
    
    # Main app
    initialize_session_state()
    page = render_sidebar()
    display_page(page)

if __name__ == "__main__":
    main()
