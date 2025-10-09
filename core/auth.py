"""Google OAuth Authentication Module"""
import streamlit as st
import requests
import secrets as python_secrets
from urllib.parse import urlencode
from typing import Optional, Dict, Any


class GoogleAuthManager:
    """Manages Google OAuth authentication flow"""
    
    def __init__(self):
        """Initialize authentication manager with secrets"""
        try:
            auth_config = st.secrets["auth"]
            self.client_id = auth_config["client_id"]
            self.client_secret = auth_config["client_secret"]
            self.redirect_uri = auth_config["redirect_uri"]
        except Exception as e:
            st.error(f"❌ Error loading auth configuration: {e}")
            st.stop()
        
        # Google OAuth endpoints
        self.auth_url = "https://accounts.google.com/o/oauth2/v2/auth"
        self.token_url = "https://oauth2.googleapis.com/token"
        self.userinfo_url = "https://www.googleapis.com/oauth2/v2/userinfo"
        
        # Initialize session state
        self._init_session_state()
    
    def _init_session_state(self):
        """Initialize authentication session state"""
        if "user" not in st.session_state:
            st.session_state.user = None
        if "oauth_state" not in st.session_state:
            st.session_state.oauth_state = None
        if "auth_code_processed" not in st.session_state:
            st.session_state.auth_code_processed = False
    
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
            "access_type": "online",
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
            raise Exception(f"Token exchange failed: {response.text}")
    
    def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """Get user information from Google"""
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(self.userinfo_url, headers=headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to get user info: {response.text}")
    
    def handle_oauth_callback(self):
        """Handle OAuth callback from Google"""
        query_params = st.query_params
        
        if "code" in query_params and not st.session_state.auth_code_processed:
            code = query_params["code"]
            
            with st.spinner("🔄 Authenticating with Google..."):
                try:
                    # Exchange code for token
                    token_data = self.exchange_code_for_token(code)
                    access_token = token_data.get("access_token")
                    
                    # Get user info
                    user_info = self.get_user_info(access_token)
                    
                    st.session_state.user = user_info
                    st.session_state.auth_code_processed = True
                    
                    # Clear query params
                    st.query_params.clear()
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Authentication failed: {e}")
                    st.session_state.user = None
                    st.session_state.auth_code_processed = False
                    st.query_params.clear()
    
    def is_authenticated(self) -> bool:
        """Check if user is authenticated"""
        return st.session_state.user is not None
    
    def get_user(self) -> Optional[Dict[str, Any]]:
        """Get current authenticated user"""
        return st.session_state.user
    
    def logout(self):
        """Log out current user"""
        st.session_state.user = None
        st.session_state.oauth_state = None
        st.session_state.auth_code_processed = False
        st.query_params.clear()
        st.rerun()
    
    def show_login_screen(self):
        """Display login screen"""
        st.markdown("## 🔐 Google Ads Campaign Simulator")
        st.markdown("### Please log in to continue")
        st.write("")
        
        auth_url = self.get_authorization_url()
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.link_button(
                "🔑 Log in with Google",
                auth_url,
                type="primary",
                use_container_width=True
            )
        
        st.markdown("---")
        st.info("💡 You need a Google account to access this application")
    
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
                    if 'picture' in user:
                        st.image(user['picture'], width=50)
                with col2:
                    st.write(f"**{user.get('name')}**")
                    st.caption(user.get('email'))
                
                if st.button("🚪 Logout", use_container_width=True):
                    self.logout()
        else:
            col1, col2, col3 = st.columns([1, 3, 1])
            with col2:
                st.info(f"👤 Logged in as: **{user.get('name')}** ({user.get('email')})")


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
