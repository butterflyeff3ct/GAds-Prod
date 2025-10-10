"""
Google OAuth Data Inspector Page (No Sheets API calls)
Shows what data Google actually returns for the logged-in user
"""
import streamlit as st
from core.auth import GoogleAuthManager


def render_data_inspector():
    """Render the data inspector page"""
    
    st.title("🔍 Google OAuth Data Inspector")
    
    auth = GoogleAuthManager()
    
    if not auth.is_authenticated():
        st.warning("⚠️ Please log in first!")
        st.info("Go back to Dashboard and log in with Google, then come back here.")
        st.stop()
    
    user = auth.get_user()
    
    st.success("✅ You are logged in!")
    
    # Show session info
    session_tracker = auth.get_session_tracker()
    if session_tracker:
        session_data = session_tracker.get_session_data()
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"**Session ID:** `{session_data['session_id']}`")
        with col2:
            st.info(f"**Trace ID:** `{session_data['trace_id']}`")
    
    st.markdown("---")
    st.markdown("### 📋 All Data Returned by Google:")
    st.json(user)
    
    st.markdown("---")
    st.markdown("### 🔍 Specific Fields Check:")
    
    fields_to_check = [
        ("email", "Email address", "✅ Always provided"),
        ("name", "Full name", "✅ Always provided"),
        ("given_name", "First name", "✅ Always provided"),
        ("family_name", "Last name", "✅ Usually provided"),
        ("picture", "Profile picture URL", "✅ Usually provided"),
        ("locale", "User locale (e.g., en, es)", "⚠️ Sometimes missing"),
        ("sub", "Google User ID (unique)", "✅ Always provided"),
        ("verified_email", "Email verification status", "✅ Usually provided"),
        ("hd", "Hosted domain (G Suite)", "⚠️ Only for G Suite users")
    ]
    
    for field, description, note in fields_to_check:
        value = user.get(field, None)
        
        col1, col2, col3 = st.columns([2, 3, 2])
        
        with col1:
            st.write(f"**{field}**")
        
        with col2:
            if value:
                st.success(f"✅ {value}")
            else:
                st.error(f"❌ NOT PROVIDED")
        
        with col3:
            st.caption(note)
    
    st.markdown("---")
    st.markdown("### 📊 What Gets Stored in Google Sheet:")
    
    st.markdown("**Users Tab:**")
    user_data = {
        "email": user.get("email", ""),
        "first_name": user.get("given_name", ""),
        "last_name": user.get("family_name", ""),
        "locale": user.get("locale", ""),
        "user_id": user.get("sub", ""),
        "picture": user.get("picture", "")
    }
    
    st.json(user_data)
    
    # Check for missing critical fields
    st.markdown("**Field Status:**")
    
    critical_fields = {
        "Email": user.get("email"),
        "First Name": user.get("given_name"),
        "User ID (sub)": user.get("sub")
    }
    
    optional_fields = {
        "Last Name": user.get("family_name"),
        "Locale": user.get("locale"),
        "Profile Picture": user.get("picture")
    }
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Critical Fields:**")
        for field_name, value in critical_fields.items():
            if value:
                st.success(f"✅ {field_name}: Present")
            else:
                st.error(f"❌ {field_name}: MISSING")
    
    with col2:
        st.markdown("**Optional Fields:**")
        for field_name, value in optional_fields.items():
            if value:
                st.info(f"✅ {field_name}: Present")
            else:
                st.warning(f"⚠️ {field_name}: Not provided by Google")
    
    st.markdown("---")
    st.markdown("### 💡 Understanding Missing Fields:")
    
    if st.checkbox("Why is Locale missing?", value=False):
        st.write("""
        **Locale** is the user's language/region setting (e.g., 'en', 'es-MX', 'fr-FR').
        
        Google only returns this if:
        - User has explicitly set a language preference in their Google account
        - User's account is configured with regional settings
        
        **This is normal** - many Google accounts don't have locale set.
        If missing, it will be stored as blank in your Google Sheet.
        """)
    
    if st.checkbox("Why is User ID missing?", value=False):
        st.write("""
        **User ID (sub field)** is Google's unique identifier for the user.
        
        This should **ALWAYS** be present. If it's missing:
        - ❌ This is a serious issue with the OAuth flow
        - Contact support or check your OAuth scopes
        
        The 'sub' field is a core part of the OpenID Connect standard.
        """)
    
    if st.checkbox("Why is Last Name missing?", value=False):
        st.write("""
        **Last Name (family_name)** may be missing if:
        - User only has a single name in their Google account
        - User's account is configured without a last name
        
        This is normal for some users (e.g., single-name cultures).
        """)
    
    st.markdown("---")
    st.info("""
    **Summary:**
    - ✅ **Critical fields** (Email, First Name, User ID) must be present
    - ⚠️ **Optional fields** (Locale, Last Name) may be missing - this is normal
    - Empty fields in Google Sheet = Google didn't provide that data
    
    **Note:** This page doesn't make any Google Sheets API calls to avoid rate limits.
    Your data is already being logged automatically on login/logout.
    """)


if __name__ == "__main__":
    render_data_inspector()
