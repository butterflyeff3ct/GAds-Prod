import streamlit as st
import streamlit.components.v1 as components
from datetime import datetime, timedelta

from app.state import initialize_session_state
from app.navigation import render_sidebar, display_page

# === AUTHENTICATION TOGGLE =============================================
# To ENABLE authentication:
# 1. pip install google-auth google-auth-oauthlib sqlalchemy
# 2. Configure: config/oauth_config.yaml with your Google OAuth credentials
# 3. Set AUTHENTICATION_ENABLED = True
#
# To DISABLE authentication (development mode):
# Set AUTHENTICATION_ENABLED = False
# ======================================================================

AUTHENTICATION_ENABLED = True  # ← Set to False for testing

# === AUTHENTICATION MODULE IMPORTS ====================================
if AUTHENTICATION_ENABLED:
    try:
        from auth.session_manager import SessionManager
        from auth.quota_manager import QuotaManager
        from auth.google_oauth import GoogleOAuthManager
        from auth.user_activity import UserActivityLogger
        from database.db_manager import get_database_manager
        from app.utils import clear_query_params, get_query_params

        AUTH_AVAILABLE = True
    except ImportError as e:
        st.error(f"Authentication modules not available: {e}")
        st.info("Run: pip install google-auth google-auth-oauthlib sqlalchemy")
        AUTH_AVAILABLE = False
        AUTHENTICATION_ENABLED = False
else:
    AUTH_AVAILABLE = False

# === DISABLE STREAMLIT CACHE CLEAR POPUP ===============================
def disabled_cache_clear(*args, **kwargs):
    pass


if hasattr(st, "cache_data"):
    st.cache_data.clear = disabled_cache_clear
if hasattr(st, "cache_resource"):
    st.cache_resource.clear = disabled_cache_clear

# === PAGE CONFIGURATION ===============================================
st.set_page_config(
    layout="wide",
    page_title="Google Ads Simulator",
    page_icon="📊"
)

# Disable Ctrl/C to prevent accidental cache clearing
components.html(
    """
    <script>
    document.addEventListener('keydown', function(event) {
        if (event.key === 'c' || event.key === 'C') {
            event.preventDefault();
            event.stopPropagation();
            return false;
        }
    }, true);
    </script>
    """,
    height=0,
)

# === HANDLE GOOGLE OAUTH CALLBACK =====================================
def handle_oauth_callback():
    """Handle OAuth callback from Google."""
    if not AUTH_AVAILABLE:
        return

    query_params = get_query_params()

    # Handle OAuth success callback
    if 'code' in query_params:
        code_values = query_params.get('code')
        if code_values:
            with st.spinner("🔐 Authenticating..."):
                try:
                    oauth_manager = GoogleOAuthManager()
                    if not oauth_manager.is_configured():
                        st.error("❌ OAuth not configured")
                        st.query_params.clear()
                        clear_query_params()
                        return

                    code = code_values[0]
                    authorization_response = f"{oauth_manager.oauth_config['redirect_uri']}?code={code}"

                    user_info = oauth_manager.handle_callback(authorization_response)
                    if user_info:
                        db_manager = get_database_manager()
                        db_manager.create_or_update_user(user_info)

                        # Create session
                        session_id = SessionManager.create_session(user_info)
                        expires_at = datetime.now() + timedelta(hours=2)
                        db_manager.create_session(user_info['email'], session_id, expires_at)

                        # Log activity
                        UserActivityLogger.log_activity(user_info['email'], 'login')
                        db_manager.log_activity(user_info['email'], 'login', {'method': 'google_oauth'})

                        clear_query_params()
                        st.success(f"✅ Welcome, {user_info['name']}!")
                        st.balloons()
                        import time
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ Authentication failed. Please try again.")
                        clear_query_params()
                except Exception as e:
                    st.error(f"❌ Authentication error: {str(e)}")
                    clear_query_params()

    # Handle OAuth error callback
    elif 'error' in query_params:
        error_values = query_params.get('error', [])
        error_description_values = query_params.get('error_description', [])
        st.error(f"❌ OAuth Error: {error_values[0] if error_values else 'Unknown error'}")
        if error_description_values:
            st.error(f"Details: {error_description_values[0]}")
        clear_query_params()


# === SIDEBAR QUOTA DISPLAY ============================================
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

    for quota in quota_display["quotas"][:3]:
        st.sidebar.caption(f"{quota['name']}: {quota['usage']}/{quota['limit']}")
        st.sidebar.progress(
            min(quota["percentage"] / 100, 1.0),
            text=f"{quota['remaining']} left",
        )

    reset_time = quota_display.get("reset_time", 0)
    st.sidebar.caption(f"⏰ Resets: {reset_time}m")


# === MAIN APPLICATION LOGIC ===========================================
def main():
    """Main application logic."""
    # Handle OAuth callback
    if AUTHENTICATION_ENABLED and AUTH_AVAILABLE:
        handle_oauth_callback()

    # Authentication logic
    if AUTHENTICATION_ENABLED and AUTH_AVAILABLE:
        is_authenticated = SessionManager.is_authenticated()

        if not is_authenticated:
            st.title("🔐 Google Ads Simulator")
            st.markdown("### Welcome! Please sign in to continue")

            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button("🔐 **Sign in with Google**", type="primary", use_container_width=True):
                    if AUTH_AVAILABLE:
                        oauth_manager = GoogleOAuthManager()
                        if oauth_manager.is_configured():
                            auth_url = oauth_manager.get_authorization_url()
                            if auth_url:
                                st.markdown(
                                    f'<a href="{auth_url}" style="display:none" id="main_oauth_link"></a>',
                                    unsafe_allow_html=True,
                                )
                                st.markdown(
                                    """
                                    <script>
                                    document.getElementById('main_oauth_link').click();
                                    </script>
                                    """,
                                    unsafe_allow_html=True,
                                )
                                st.info("🔄 Redirecting to Google login...")
                            else:
                                st.error("🔧 OAuth not configured. Please contact administrator.")
                        else:
                            st.error("🔧 Authentication system not available.")

            st.markdown(
                """
                **📋 Steps:**
                1. Click "Sign in with Google" above  
                2. Sign in with your Google account  
                3. Grant permissions  
                4. You’ll be redirected back and logged in automatically
                """
            )
            return

        # Authenticated user
        SessionManager.update_activity()
        with st.sidebar:
            user_name = SessionManager.get_user_name()
            user_email = SessionManager.get_user_email()
            st.markdown(f"### 👤 {user_name}")
            st.caption(user_email)
            if st.button("🚪 Logout", use_container_width=True):
                UserActivityLogger.log_activity(user_email, "logout")
                SessionManager.end_session()
                st.rerun()

        render_quota_in_sidebar()

    else:
        # Dev Mode
        if not AUTHENTICATION_ENABLED:
            with st.sidebar:
                st.info("🛠️ **DEV MODE**")
                st.caption("Authentication disabled")

        initialize_session_state()
        page = render_sidebar()
        display_page(page)


# === ENTRY POINT ======================================================
if __name__ == "__main__":
    main()
