"""
Debug Page
Helps troubleshoot OAuth and authentication issues.
"""

import streamlit as st
import sys
import os

def render_debug_page():
    """Render debug information page."""
    st.title("🔧 Debug Information")
    
    st.markdown("This page helps troubleshoot OAuth and authentication issues.")
    
    # OAuth Debug Info
    st.subheader("🔐 OAuth Configuration")
    
    try:
        from auth.google_oauth import GoogleOAuthManager
        
        oauth_manager = GoogleOAuthManager()
        debug_info = oauth_manager.get_debug_info()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Configuration Status:**")
            st.json(debug_info)
        
        with col2:
            st.markdown("**OAuth Manager Details:**")
            if oauth_manager.oauth_config:
                # Show partial config (hide secrets)
                safe_config = {
                    'client_id': oauth_manager.oauth_config.get('client_id', 'Not set')[:20] + '...' if oauth_manager.oauth_config.get('client_id') else 'Not set',
                    'redirect_uri': oauth_manager.oauth_config.get('redirect_uri', 'Not set'),
                    'scopes': oauth_manager.oauth_config.get('scopes', 'Not set')
                }
                st.json(safe_config)
            else:
                st.error("No OAuth configuration found")
        
        # Test authorization URL
        st.markdown("**Authorization URL Test:**")
        auth_url = oauth_manager.get_authorization_url()
        if auth_url:
            st.success("✅ Authorization URL generated successfully!")
            st.code(auth_url[:100] + "..." if len(auth_url) > 100 else auth_url)
        else:
            st.error("❌ Failed to generate authorization URL")
            
    except Exception as e:
        st.error(f"Error loading OAuth manager: {e}")
    
    # Streamlit Secrets Debug
    st.subheader("🔑 Streamlit Secrets")
    
    try:
        secrets_available = hasattr(st, 'secrets')
        st.write(f"Secrets available: {secrets_available}")
        
        if secrets_available:
            try:
                # Try to access google_oauth secrets
                oauth_secrets = st.secrets.get("google_oauth", {})
                if oauth_secrets:
                    st.success("✅ Google OAuth secrets found!")
                    # Show safe version
                    safe_secrets = {
                        'client_id': str(oauth_secrets.get('client_id', 'Not set'))[:20] + '...' if oauth_secrets.get('client_id') else 'Not set',
                        'redirect_uri': oauth_secrets.get('redirect_uri', 'Not set')
                    }
                    st.json(safe_secrets)
                else:
                    st.warning("⚠️ No Google OAuth secrets found")
                    
            except Exception as e:
                st.error(f"Error accessing secrets: {e}")
        else:
            st.warning("⚠️ Streamlit secrets not available")
            
    except Exception as e:
        st.error(f"Error checking secrets: {e}")
    
    # Environment Info
    st.subheader("🌐 Environment Information")
    
    env_info = {
        'Python version': sys.version,
        'Streamlit version': st.__version__,
        'Current directory': os.getcwd(),
        'Environment variables': {
            'STREAMLIT_SERVER_HEADLESS': os.environ.get('STREAMLIT_SERVER_HEADLESS', 'Not set'),
            'STREAMLIT_SERVER_PORT': os.environ.get('STREAMLIT_SERVER_PORT', 'Not set'),
        }
    }
    
    st.json(env_info)
    
    # File System Check
    st.subheader("📁 Configuration Files")
    
    config_files = [
        'config/oauth_config.yaml',
        'config/oauth_config_local.yaml', 
        'config/oauth_config_template.yaml',
        '.streamlit/secrets.toml'
    ]
    
    for file_path in config_files:
        exists = os.path.exists(file_path)
        status = "✅" if exists else "❌"
        st.write(f"{status} {file_path}")
    
    # Instructions
    st.subheader("📋 Troubleshooting Steps")
    
    if not debug_info.get('is_configured'):
        st.markdown("""
        **To fix OAuth configuration:**
        
        1. **For Streamlit Cloud:**
           - Go to your app settings
           - Add OAuth secrets:
           ```toml
           [google_oauth]
           client_id = "your-client-id"
           client_secret = "your-client-secret"
           redirect_uri = "https://butterflyeff3ct-gads-prod-main-qnzzei.streamlit.app/oauth2callback"
           ```
        
        2. **For Local Development:**
           - Copy `config/oauth_config_template.yaml` to `config/oauth_config.yaml`
           - Add your OAuth credentials
           - Or add to `.streamlit/secrets.toml`
        """)
    else:
        st.success("✅ OAuth is properly configured!")
