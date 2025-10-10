"""
Quick fix for redirect URI issue
Run this to update core/auth.py
"""

# Read the file
with open('core/auth.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find and replace the _get_redirect_uri method
old_method = '''    def _get_redirect_uri(self, auth_config):
        """Dynamically determine the correct redirect URI based on environment"""
        server_port = os.getenv("STREAMLIT_SERVER_PORT", "")
        server_address = os.getenv("STREAMLIT_SERVER_ADDRESS", "")
        
        # Check if running locally
        is_localhost = (
            server_port == "8501" or
            server_address == "localhost" or 
            server_address == "127.0.0.1" or
            "localhost" in str(server_address) or
            "127.0.0.1" in str(server_address)
        )
        
        if is_localhost:
            return auth_config.get("redirect_uri_local", "http://localhost:8501")
        else:
            # For deployed app, use configured URI
            return auth_config.get("redirect_uri_deployed", "http://localhost:8501")'''

new_method = '''    def _get_redirect_uri(self, auth_config):
        """Dynamically determine the correct redirect URI based on environment"""
        import socket
        
        # Multiple detection methods for localhost
        server_port = os.getenv("STREAMLIT_SERVER_PORT", "")
        server_address = os.getenv("STREAMLIT_SERVER_ADDRESS", "")
        hostname = socket.gethostname()
        
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
        return auth_config.get("redirect_uri_local", "http://localhost:8501")'''

if old_method in content:
    content = content.replace(old_method, new_method)
    print("✅ Found and updated _get_redirect_uri method")
else:
    print("⚠️ Could not find exact match for _get_redirect_uri method")
    print("You may need to update manually")

# Write back
with open('core/auth.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ File updated! Restart your Streamlit app.")
