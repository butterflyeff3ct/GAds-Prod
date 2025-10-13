"""Google OAuth Authentication Module - Production Ready"""
import streamlit as st
import requests
import secrets as python_secrets
import os
from urllib.parse import urlencode
from typing import Optional, Dict, Any
from utils.gsheet_writer import GSheetLogger, SessionTracker


class GoogleAuthManager:
    """Manages Google OAuth 2.0 authentication flow"""
    
    def __init__(self):
        """Initialize authentication manager with secrets"""
        # Initialize gsheet_logger as None first to prevent AttributeError
        self.gsheet_logger = None
        
        # Wrap entire initialization in try-catch to ensure gsheet_logger is always set
        try:
            auth_config = st.secrets["google_oauth"]
            self.client_id = auth_config["client_id"]
            self.client_secret = auth_config["client_secret"]
            
            # Dynamically determine redirect URI based on environment
            self.redirect_uri = self._get_redirect_uri(auth_config)
            
            # Check if placeholder values are still being used
            if (self.client_id == "YOUR_CLIENT_ID_HERE" or 
                self.client_secret == "YOUR_CLIENT_SECRET_HERE"):
                st.error("🔧 **OAuth Configuration Required**")
                st.error("❌ Please configure your OAuth credentials")
                st.stop()
            
            self.oauth_enabled = True
        except Exception as e:
            st.error("🔧 **OAuth Configuration Required**")
            st.error(f"❌ Error loading OAuth configuration")
            # Initialize sheets logger without showing warnings during OAuth errors
            try:
                self.gsheet_logger = GSheetLogger(show_warnings=False)
            except Exception:
                self.gsheet_logger = None
            st.stop()
        
        # Google OAuth endpoints
        self.auth_url = "https://accounts.google.com/o/oauth2/v2/auth"
        self.token_url = "https://oauth2.googleapis.com/token"
        self.userinfo_url = "https://www.googleapis.com/oauth2/v2/userinfo"
        
        # Initialize session state
        self._init_session_state()
        
        # Initialize Google Sheets logger
        self._initialize_google_sheets_logger()
        
        # Final safety check - ensure gsheet_logger attribute always exists
        if not hasattr(self, 'gsheet_logger'):
            self.gsheet_logger = None
    
    def _initialize_google_sheets_logger(self):
        """Initialize Google Sheets logger with error handling"""
        try:
            self.gsheet_logger = GSheetLogger(show_warnings=False)
        except Exception:
            self.gsheet_logger = None
    
    @property
    def gsheet_logger_safe(self):
        """Safe access to gsheet_logger attribute"""
        if not hasattr(self, 'gsheet_logger'):
            self.gsheet_logger = None
        return self.gsheet_logger
    
    def _get_redirect_uri(self, auth_config):
        """Dynamically determine the correct redirect URI based on environment"""
        import socket
        
        # Check if running on Streamlit Cloud
        is_streamlit_cloud = (
            "streamlit.app" in os.getenv("HOSTNAME", "") or
            os.getenv("STREAMLIT_SHARING_MODE") == "true" or
            "/mount/src" in os.getcwd()
        )
        
        # If definitely on Streamlit Cloud, use deployed URI
        if is_streamlit_cloud:
            return auth_config.get("redirect_uri_deployed", "http://localhost:8501")
        
        # Otherwise, assume localhost (safer default for development)
        return auth_config.get("redirect_uri_local", "http://localhost:8501")
    
    def _init_session_state(self):
        """Initialize authentication session state"""
        if "user" not in st.session_state:
            st.session_state.user = None
        if "oauth_state" not in st.session_state:
            st.session_state.oauth_state = None
        if "auth_code_processed" not in st.session_state:
            st.session_state.auth_code_processed = False
        if "session_tracker" not in st.session_state:
            st.session_state.session_tracker = None
        if "session_id" not in st.session_state:
            st.session_state.session_id = None
        if "auth_in_progress" not in st.session_state:
            st.session_state.auth_in_progress = False
    
    def get_authorization_url(self) -> str:
        """Generate Google OAuth authorization URL"""
        state = python_secrets.token_urlsafe(32)
        st.session_state.oauth_state = state
        
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": "openid email profile",
            "state": state,
            "access_type": "offline",
            "prompt": "consent"
        }
        
        return f"{self.auth_url}?{urlencode(params)}"
    
    def exchange_code_for_token(self, code: str) -> Dict[str, Any]:
        """Exchange authorization code for access token"""
        data = {
            "code": code,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri": self.redirect_uri,
            "grant_type": "authorization_code",
        }
        
        response = requests.post(self.token_url, data=data)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Token exchange failed")
    
    def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """Get user information from Google"""
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(self.userinfo_url, headers=headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to get user info")
    
    def handle_oauth_callback(self):
        """Handle OAuth callback from Google"""
        query_params = st.query_params
        
        if "code" in query_params and not st.session_state.auth_code_processed:
            code = query_params["code"]
            
            # Clear query params IMMEDIATELY to prevent reuse
            st.query_params.clear()
            
            with st.spinner("🔄 Authenticating with Google..."):
                try:
                    # Exchange code for token
                    token_data = self.exchange_code_for_token(code)
                    access_token = token_data.get("access_token")
                    
                    # Get user info
                    user_info = self.get_user_info(access_token)
                    
                    # ✅ STEP 3: CHECK USER ACCESS WITH LOGIN GATE
                    from app.login_gate import integrate_with_oauth_login
                    
                    if not integrate_with_oauth_login(user_info):
                        # User doesn't have access - message already shown
                        # Clear auth state and stop
                        st.session_state.auth_code_processed = True
                        st.stop()
                    
                    # User approved! Continue with login
                    st.session_state.user = user_info
                    st.session_state.auth_code_processed = True
                    
                    # Initialize session tracking
                    self._initialize_session_tracking(user_info)
                    
                    st.rerun()
                    
                except Exception as e:
                    error_msg = str(e)
                    if "invalid_grant" in error_msg.lower():
                        st.error("🔄 **Authentication expired.** Please try signing in again.")
                    else:
                        st.error(f"❌ Authentication failed. Please try again.")
                    
                    st.session_state.user = None
                    st.session_state.auth_code_processed = False
                    st.stop()
    
    def is_authenticated(self) -> bool:
        """Check if user is authenticated"""
        return st.session_state.user is not None
    
    def get_user(self) -> Optional[Dict[str, Any]]:
        """Get current authenticated user"""
        return st.session_state.user
    
    def _initialize_session_tracking(self, user_info: Dict[str, Any]):
        """Initialize session tracking and Google Sheets logging with IP capture"""
        try:
            # Create session tracker with trace ID
            session_tracker = SessionTracker()
            
            # Generate trace ID from session ID
            trace_id = f"trace-{session_tracker.session_id[:8]}"
            session_tracker.set_trace_id(trace_id)
            
            st.session_state.session_tracker = session_tracker
            st.session_state.session_id = session_tracker.session_id
            
            # Capture IP address and user agent
            from utils.ip_utils import get_client_ip, get_user_agent, format_ip_for_logging
            
            ip_address = get_client_ip()
            user_agent = get_user_agent()
            
            # Format IP for logging (handles IPv6 length)
            ip_address = format_ip_for_logging(ip_address)
            
            # Store in session for later use
            st.session_state.client_ip = ip_address
            st.session_state.user_agent = user_agent
            
            # NEW: Initialize quota system with user context
            from app.quota_system import get_quota_manager
            quota_mgr = get_quota_manager()
            
            # Set user context in quota manager
            quota_mgr.set_user_context(
                user_id=user_info.get("sub"),
                email=user_info.get("email"),
                session_id=session_tracker.session_id
            )
            
            # Load user's existing quota usage from sheets
            quota_mgr.load_quotas_from_sheets(user_info.get("email"))
            
            # Store user data in Google Sheets (if new user)
            user_data = {
                "email": user_info.get("email", ""),
                "first_name": user_info.get("given_name", ""),
                "last_name": user_info.get("family_name", ""),
                "locale": user_info.get("locale", ""),
                "user_id": user_info.get("sub", ""),
                "picture": user_info.get("picture", "")
            }
            
            if self.gsheet_logger_safe and self.gsheet_logger_safe.enabled:
                # Close any orphaned sessions from previous browser sessions
                user_email = user_info.get("email")
                closed_count = self.gsheet_logger_safe.close_orphaned_sessions(user_email)
                
                # Store user if new (creates User ID)
                is_new_user = self.gsheet_logger_safe.store_user_if_new(user_data)
                
                # Update First Login and Last Login timestamps
                self.gsheet_logger_safe.update_user_login_timestamps(
                    email=user_email,
                    is_first_login=is_new_user  # Only update First Login if new user
                )
                
                # Get the 6-digit User ID for this user (now that we're sure they exist)
                user_id_6digit = self.gsheet_logger_safe.get_user_id_by_email(user_email)
                
                # Log session start with 6-digit User ID, IP address, and user agent
                self.gsheet_logger_safe.log_session_start(
                    email=user_email,
                    session_id=session_tracker.session_id,
                    trace_id=trace_id,
                    user_id=user_id_6digit,  # FIXED: Use 6-digit ID from Users sheet
                    ip_address=ip_address,    # NEW: IP address tracking
                    user_agent=user_agent     # NEW: User agent tracking
                )
            
        except Exception:
            # Don't fail authentication if logging fails
            pass
    
    def get_session_tracker(self) -> Optional[SessionTracker]:
        """Get current session tracker"""
        return st.session_state.get("session_tracker")
    
    def increment_tokens(self, count: int):
        """Increment token usage in session tracker"""
        tracker = self.get_session_tracker()
        if tracker:
            tracker.increment_tokens(count)
    
    def increment_operations(self, count: int = 1):
        """Increment operations count in session tracker"""
        tracker = self.get_session_tracker()
        if tracker:
            tracker.increment_operations(count)
    
    def logout(self):
        """Log out current user and log session end"""
        try:
            # Log session end before clearing session state
            user = self.get_user()
            session_tracker = self.get_session_tracker()
            
            if user and session_tracker and self.gsheet_logger_safe and self.gsheet_logger_safe.enabled:
                session_data = session_tracker.get_session_data()
                duration_ms = session_tracker.get_duration_ms()
                
                self.gsheet_logger_safe.log_session_end(
                    email=user.get("email"),
                    session_id=session_data["session_id"],
                    tokens_used=session_data["tokens_used"],
                    operations=session_data["operations"],
                    duration_ms=duration_ms,
                    status="logged_out"
                )
        except Exception:
            # Don't fail logout if logging fails
            pass
        
        # Clear session state
        st.session_state.user = None
        st.session_state.oauth_state = None
        st.session_state.auth_code_processed = False
        st.session_state.session_tracker = None
        st.session_state.session_id = None
        st.session_state.auth_in_progress = False
        st.query_params.clear()
        st.rerun()
    
    def show_login_screen(self):
        """Display login screen"""
        st.markdown("## 🔐 Google Ads Campaign Simulator")
        st.markdown("### Please log in to continue")
        st.write("")
        
        auth_url = self.get_authorization_url()
        
        # ✅ STEP 4: ADD SIGNUP AND LOGIN BUTTONS
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            # Signup button
            if st.button(
                "📝 Request Access",
                use_container_width=True,
                help="New users need to request access first"
            ):
                st.switch_page("pages/1_📝_Request_Access.py")
            
            st.write("")  # Spacing
            
            # Login button
            st.link_button(
                "🔑 Sign in with Google",
                auth_url,
                type="primary",
                use_container_width=True
            )
        
        st.markdown("---")
        st.info("💡 New users: Request access first, then log in once approved")
    
    def show_user_info(self, sidebar: bool = True):
        """Display logged-in user information"""
        user = self.get_user()
        if not user:
            return
        
        if sidebar:
            with st.sidebar:
                st.markdown("---")
                st.markdown("### 👤 Logged in as:")
                
                col1, col2 = st.columns([1, 3])
                with col1:
                    if user.get('picture'):
                        st.image(user['picture'], width=50)
                    else:
                        st.markdown("👤")
                with col2:
                    st.write(f"**{user.get('name')}**")
                    st.caption(user.get('email'))
                
                if st.button("🚪 Logout", use_container_width=True):
                    self.logout()


def require_auth(func):
    """Decorator to require authentication for a function"""
    def wrapper(*args, **kwargs):
        auth = GoogleAuthManager()
        
        # Handle OAuth callback
        if "code" in st.query_params:
            auth.handle_oauth_callback()
        
        # Check authentication
        if not auth.is_authenticated():
            auth.show_login_screen()
            st.stop()

        # Show user info in sidebar
        auth.show_user_info(sidebar=True)
        
        # Execute the protected function
        return func(*args, **kwargs)
    
    return wrapper
