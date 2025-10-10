"""
Diagnostic script to check OAuth and Google Sheets configuration
"""
import streamlit as st
import os
from pathlib import Path

print("=" * 60)
print("🔍 CONFIGURATION DIAGNOSTICS")
print("=" * 60)

# Check if secrets.toml exists
secrets_path = Path(".streamlit/secrets.toml")
if secrets_path.exists():
    print("✅ secrets.toml found")
    
    # Try to load secrets
    try:
        # Check OAuth config
        if "google_oauth" in st.secrets:
            oauth_config = st.secrets["google_oauth"]
            print("\n📋 OAuth Configuration:")
            print(f"  ✅ client_id: {oauth_config.get('client_id', 'MISSING')[:50]}...")
            print(f"  ✅ client_secret: {'*' * 10} (present)")
            print(f"  ✅ redirect_uri_local: {oauth_config.get('redirect_uri_local', 'MISSING')}")
            print(f"  ✅ redirect_uri_deployed: {oauth_config.get('redirect_uri_deployed', 'MISSING')}")
        else:
            print("\n❌ google_oauth section missing in secrets.toml")
        
        # Check Google Sheets config
        if "google_sheets" in st.secrets:
            sheets_config = st.secrets["google_sheets"]
            print("\n📊 Google Sheets Configuration:")
            print(f"  ✅ sheet_id: {sheets_config.get('sheet_id', 'MISSING')}")
            
            if "credentials" in sheets_config:
                creds = sheets_config["credentials"]
                print(f"  ✅ credentials.type: {creds.get('type', 'MISSING')}")
                print(f"  ✅ credentials.project_id: {creds.get('project_id', 'MISSING')}")
                print(f"  ✅ credentials.client_email: {creds.get('client_email', 'MISSING')}")
                print(f"  ✅ credentials.private_key: {'*' * 10} (present)" if creds.get('private_key') else "  ❌ private_key MISSING")
            else:
                print("  ❌ credentials section missing")
        else:
            print("\n❌ google_sheets section missing in secrets.toml")
            
    except Exception as e:
        print(f"\n❌ Error reading secrets: {e}")
else:
    print("❌ secrets.toml NOT FOUND")
    print(f"   Expected location: {secrets_path.absolute()}")

# Check environment
print("\n🌍 Environment:")
print(f"  Server Port: {os.getenv('STREAMLIT_SERVER_PORT', 'Not set')}")
print(f"  Server Address: {os.getenv('STREAMLIT_SERVER_ADDRESS', 'Not set')}")
print(f"  Hostname: {os.getenv('HOSTNAME', 'Not set')}")
print(f"  Current Directory: {os.getcwd()}")

# Check if running locally or deployed
is_local = "localhost" in os.getenv('STREAMLIT_SERVER_ADDRESS', '') or os.getenv('STREAMLIT_SERVER_PORT') == '8501'
print(f"\n🎯 Detected Environment: {'LOCAL' if is_local else 'DEPLOYED'}")

print("\n" + "=" * 60)
print("Run this script with: python fix_redirect_uri.py")
print("=" * 60)
