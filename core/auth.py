"""Google OAuth Authentication Module"""
import streamlit as st
import requests
import secrets as python_secrets
import os
from urllib.parse import urlencode
from typing import Optional, Dict, Any


class GoogleAuthManager:
    """Manages Google OAuth authentication flow"""
    
    def __init__(self):
        """Initialize authentication manager with secrets"""
        try:
            auth_config = st.secrets["google_oauth"]
            self.client_id = auth_config["client_id"]
            self.client_secret = auth_config["client_secret"]
            
            # Dynamically determine redirect URI based on environment
            self.redirect_uri = self._get_redirect_uri(auth_config)
            
            # Debug info (show environment detection)
            debug_info = []
            debug_info.append(f"🔧 Using redirect URI: {self.redirect_uri}")
            debug_info.append(f"Environment variables:")
            debug_info.append(f"  STREAMLIT_CLOUD: {os.getenv('STREAMLIT_CLOUD')}")
            debug_info.append(f"  STREAMLIT_CLOUD_DOMAIN: {os.getenv('STREAMLIT_CLOUD_DOMAIN')}")
            debug_info.append(f"  STREAMLIT_SERVER_PORT: {os.getenv('STREAMLIT_SERVER_PORT')}")
            debug_info.append(f"  STREAMLIT_SERVER_ADDRESS: {os.getenv('STREAMLIT_SERVER_ADDRESS')}")
            debug_info.append(f"  STREAMLIT_SHARING_MODE: {os.getenv('STREAMLIT_SHARING_MODE')}")
            debug_info.append(f"  HOSTNAME: {os.getenv('HOSTNAME')}")
            debug_info.append(f"  PWD: {os.getenv('PWD')}")
            
            # Always show debug info for now to troubleshoot
            for info in debug_info:
                st.caption(info)
            
            # Check if placeholder values are still being used
            if (self.client_id == "YOUR_CLIENT_ID_HERE" or 
                self.client_secret == "YOUR_CLIENT_SECRET_HERE"):
                st.error("🔧 **OAuth Configuration Required**")
                st.error("❌ Please replace placeholder values with your actual OAuth credentials")
                st.markdown("---")
                st.markdown("### 📋 **Setup Instructions:**")
                st.markdown("""
                1. **Create Google OAuth Client:**
                   - Go to [Google Cloud Console](https://console.cloud.google.com/)
                   - Navigate to "APIs & Services" > "Credentials"
                   - Click "Create Credentials" > "OAuth client ID"
                   - Choose "Web application"
                   - Set authorized redirect URIs:
                     - `http://localhost:8501/` (for local development)
                     - `https://butterflyeff3ct-gads-prod-main-qnzzei.streamlit.app/` (for deployed app)

                2. **Update Configuration:**
                   - Edit `.streamlit/secrets.toml`
                   - Replace the placeholder values with your actual credentials:
                   ```toml
                   [google_oauth]
                   client_id = "your-actual-client-id"
                   client_secret = "your-actual-client-secret"
                   redirect_uri_local = "http://localhost:8501/"
                   redirect_uri_deployed = "https://butterflyeff3ct-gads-prod-main-qnzzei.streamlit.app/"
                   ```

                3. **Restart the Application:**
                   - Stop the current app (Ctrl+C)
                   - Run `streamlit run main.py` again
                """)
                st.stop()
            
            self.oauth_enabled = True
        except Exception as e:
            # OAuth not configured - show configuration error
            st.error("🔧 **OAuth Configuration Required**")
            st.error(f"❌ Error loading OAuth configuration: {e}")
            st.markdown("---")
            st.markdown("### 📋 **Setup Instructions:**")
            st.markdown("""
            1. **Create Google OAuth Client:**
               - Go to [Google Cloud Console](https://console.cloud.google.com/)
               - Navigate to "APIs & Services" > "Credentials"
               - Click "Create Credentials" > "OAuth client ID"
               - Choose "Web application"
               - Set authorized redirect URIs:
                 - `http://localhost:8501/` (for local development)
                 - `https://butterflyeff3ct-gads-prod-main-qnzzei.streamlit.app/` (for deployed app)

            2. **Update Configuration:**
               - Edit `.streamlit/secrets.toml`
               - Add your OAuth credentials:
               ```toml
               [google_oauth]
               client_id = "YOUR_CLIENT_ID"
               client_secret = "YOUR_CLIENT_SECRET"
               redirect_uri_local = "http://localhost:8501/"
               redirect_uri_deployed = "https://butterflyeff3ct-gads-prod-main-qnzzei.streamlit.app/"
               ```

            3. **Restart the Application:**
               - Stop the current app (Ctrl+C)
               - Run `streamlit run main.py` again
            """)
            st.stop()
        
        # Google OAuth endpoints
        self.auth_url = "https://accounts.google.com/o/oauth2/v2/auth"
        self.token_url = "https://oauth2.googleapis.com/token"
        self.userinfo_url = "https://www.googleapis.com/oauth2/v2/userinfo"
        
        # Initialize session state
        self._init_session_state()
    
    def _get_redirect_uri(self, auth_config):
        """Dynamically determine the correct redirect URI based on environment"""
        import os
        
        # Get all environment variables for debugging
        env_vars = {
            "STREAMLIT_CLOUD": os.getenv("STREAMLIT_CLOUD"),
            "STREAMLIT_CLOUD_DOMAIN": os.getenv("STREAMLIT_CLOUD_DOMAIN"),
            "STREAMLIT_SHARING_MODE": os.getenv("STREAMLIT_SHARING_MODE"),
            "STREAMLIT_SERVER_PORT": os.getenv("STREAMLIT_SERVER_PORT"),
            "STREAMLIT_SERVER_ADDRESS": os.getenv("STREAMLIT_SERVER_ADDRESS"),
            "HOSTNAME": os.getenv("HOSTNAME"),
            "PWD": os.getenv("PWD"),
        }
        
        # Multiple detection methods for Streamlit Cloud
        is_streamlit_cloud = (
            os.getenv("STREAMLIT_CLOUD") == "true" or
            os.getenv("STREAMLIT_CLOUD_DOMAIN") or
            os.getenv("STREAMLIT_SHARING_MODE") == "true" or
            "streamlit.app" in str(os.getenv("STREAMLIT_SERVER_PORT", "")) or
            "streamlit.app" in str(os.getenv("STREAMLIT_SERVER_ADDRESS", "")) or
            "streamlit.app" in str(os.getenv("HOSTNAME", "")) or
            "/app" in str(os.getenv("PWD", ""))  # Streamlit Cloud apps run in /app directory
        )
        
        # Additional check: if we're not running on localhost, assume Streamlit Cloud
        try:
            server_port = os.getenv("STREAMLIT_SERVER_PORT", "")
            if server_port and "8501" not in str(server_port):
                is_streamlit_cloud = True
        except:
            pass
        
        # Force deployed URI if we detect Streamlit Cloud OR if we're not on localhost
        # Also check if we're not running on the default Streamlit port
        server_port = os.getenv("STREAMLIT_SERVER_PORT", "")
        is_localhost = (
            server_port.endswith("8501") and 
            "localhost" in str(os.getenv("STREAMLIT_SERVER_ADDRESS", ""))
        )
        
        if is_streamlit_cloud or not is_localhost:
            # Running on Streamlit Cloud - use deployed URI
            deployed_uri = "https://butterflyeff3ct-gads-prod-main-qnzzei.streamlit.app/"
            return deployed_uri
        else:
            # Running locally - use localhost URI
            local_uri = auth_config.get("redirect_uri_local", "http://localhost:8501/")
            return local_uri
    
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
                    # Only display image if picture exists and is not None
                    if user.get('picture'):
                        st.image(user['picture'], width=50)
                    else:
                        # Show a placeholder avatar
                        st.markdown("👤")
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
