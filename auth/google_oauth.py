# auth/google_oauth.py
"""
Google OAuth 2.0 Authentication Manager
Handles login flow, token management, and user profile retrieval.
"""

import streamlit as st
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
import google.auth.transport.requests
import requests
import yaml
from typing import Optional, Dict
import os
from datetime import datetime, timedelta

# Allow insecure transport for localhost development
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

class GoogleOAuthManager:
    """Manages Google OAuth 2.0 authentication flow."""
    
    def __init__(self, config_path: str = None):
        # Use local config for development, production config for deployment
        if config_path is None:
            import os
            if os.path.exists("config/oauth_config_local.yaml"):
                config_path = "config/oauth_config_local.yaml"
            elif os.path.exists("config/oauth_config.yaml"):
                config_path = "config/oauth_config.yaml"
            elif os.path.exists("config/oauth_config_template.yaml"):
                config_path = "config/oauth_config_template.yaml"
            else:
                config_path = None
        """Initialize OAuth manager with configuration."""
        self.oauth_config = None
        
        if config_path:
            try:
                with open(config_path, 'r') as f:
                    config = yaml.safe_load(f)
                    self.oauth_config = config['google_oauth']
            except Exception as e:
                self.oauth_config = None
        
        if not self.oauth_config:
            # Fallback: try to load from Streamlit secrets
            try:
                secrets = st.secrets
                if hasattr(secrets, 'get') and secrets.get("google_oauth"):
                    self.oauth_config = secrets["google_oauth"]
                elif hasattr(secrets, 'google_oauth'):
                    self.oauth_config = secrets.google_oauth
                else:
                    # Try alternative access methods
                    try:
                        self.oauth_config = dict(st.secrets["google_oauth"])
                    except:
                        self.oauth_config = None
                
                if not self.oauth_config:
                    st.warning("⚠️ OAuth configuration not found. Authentication will be disabled.")
                    self.oauth_config = None
            except Exception as secrets_error:
                st.warning("⚠️ OAuth configuration not available. Authentication will be disabled.")
                self.oauth_config = None
        
        self.scopes = self.oauth_config.get('scopes', [
            'openid',
            'https://www.googleapis.com/auth/userinfo.email',
            'https://www.googleapis.com/auth/userinfo.profile'
        ]) if self.oauth_config else [
            'openid',
            'https://www.googleapis.com/auth/userinfo.email',
            'https://www.googleapis.com/auth/userinfo.profile'
        ]
    
    def is_configured(self) -> bool:
        """Check if OAuth is properly configured."""
        if self.oauth_config is None:
            return False
        
        required_fields = ['client_id', 'client_secret', 'redirect_uri']
        for field in required_fields:
            if not self.oauth_config.get(field):
                return False
        
        return True
    
    def get_debug_info(self) -> dict:
        """Get debug information about OAuth configuration."""
        return {
            'has_config': self.oauth_config is not None,
            'config_keys': list(self.oauth_config.keys()) if self.oauth_config else [],
            'client_id_present': bool(self.oauth_config.get('client_id')) if self.oauth_config else False,
            'client_secret_present': bool(self.oauth_config.get('client_secret')) if self.oauth_config else False,
            'redirect_uri_present': bool(self.oauth_config.get('redirect_uri')) if self.oauth_config else False,
            'is_configured': self.is_configured()
        }
    
    def get_authorization_url(self) -> str:
        """
        Generate Google OAuth authorization URL.
        
        Returns:
            Authorization URL for user to visit
        """
        if not self.is_configured():
            return None
        
        # Create flow
        flow = Flow.from_client_config(
            client_config={
                "web": {
                    "client_id": self.oauth_config['client_id'],
                    "client_secret": self.oauth_config['client_secret'],
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [self.oauth_config['redirect_uri']]
                }
            },
            scopes=self.scopes
        )
        
        flow.redirect_uri = self.oauth_config['redirect_uri']
        
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'
        )
        
        # Store state in session for verification
        st.session_state['oauth_state'] = state
        
        return authorization_url
    
    def handle_callback(self, authorization_response: str) -> Optional[Dict]:
        """
        Handle OAuth callback and exchange code for tokens.
        
        Args:
            authorization_response: Full callback URL with code
            
        Returns:
            User info dictionary or None if failed
        """
        if not self.oauth_config:
            return None
        
        try:
            # Create flow
            flow = Flow.from_client_config(
                client_config={
                    "web": {
                        "client_id": self.oauth_config['client_id'],
                        "client_secret": self.oauth_config['client_secret'],
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "redirect_uris": [self.oauth_config['redirect_uri']]
                    }
                },
                scopes=self.scopes,
                state=st.session_state.get('oauth_state')
            )
            
            flow.redirect_uri = self.oauth_config['redirect_uri']
            
            # Fetch tokens
            flow.fetch_token(authorization_response=authorization_response)
            
            # Get credentials
            credentials = flow.credentials
            
            # Get user info
            user_info = self._get_user_info(credentials)
            
            if user_info:
                # Store credentials in session
                st.session_state['oauth_credentials'] = {
                    'token': credentials.token,
                    'refresh_token': credentials.refresh_token,
                    'token_expiry': (datetime.now() + timedelta(hours=1)).isoformat()
                }
                
                return user_info
            
            return None
            
        except Exception as e:
            st.error(f"OAuth callback error: {e}")
            return None
    
    def _get_user_info(self, credentials: Credentials) -> Optional[Dict]:
        """
        Fetch user profile information from Google.
        
        Returns:
            Dictionary with email, name, picture
        """
        try:
            # Use credentials to get user info
            response = requests.get(
                'https://www.googleapis.com/oauth2/v2/userinfo',
                headers={'Authorization': f'Bearer {credentials.token}'}
            )
            
            if response.status_code == 200:
                user_data = response.json()
                return {
                    'email': user_data.get('email'),
                    'name': user_data.get('name'),
                    'picture': user_data.get('picture'),
                    'google_id': user_data.get('id'),
                    'verified_email': user_data.get('verified_email', False)
                }
            
            return None
            
        except Exception as e:
            st.error(f"Failed to get user info: {e}")
            return None
    
    def refresh_token_if_needed(self, credentials_dict: Dict) -> bool:
        """
        Refresh OAuth token if expired.
        
        Returns:
            True if token is valid (refreshed if needed)
        """
        try:
            token_expiry = datetime.fromisoformat(credentials_dict.get('token_expiry'))
            
            # Check if token expired
            if datetime.now() >= token_expiry:
                # Need to refresh
                credentials = Credentials(
                    token=credentials_dict['token'],
                    refresh_token=credentials_dict.get('refresh_token')
                )
                
                # Refresh
                request = google.auth.transport.requests.Request()
                credentials.refresh(request)
                
                # Update session
                st.session_state['oauth_credentials'] = {
                    'token': credentials.token,
                    'refresh_token': credentials.refresh_token,
                    'token_expiry': (datetime.now() + timedelta(hours=1)).isoformat()
                }
                
                return True
            
            return True
            
        except Exception as e:
            st.error(f"Token refresh failed: {e}")
            return False
    
    def logout(self):
        """Clear session and logout user."""
        keys_to_clear = [
            'oauth_credentials',
            'oauth_state',
            'user_session',
            'user_email',
            'user_name'
        ]
        
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
