"""Tracking Test Page - Verify User Logging and MS Clarity Integration"""

import streamlit as st
import time
from datetime import datetime
from core.auth import GoogleAuthManager
from utils.gsheet_writer import GSheetLogger


def render_tracking_test():
    """Render tracking test page with diagnostic information"""
    
    st.title("🔍 Tracking Integration Test")
    st.markdown("This page helps verify that user logging and MS Clarity are working correctly.")
    
    # Get current user
    auth = GoogleAuthManager()
    user = auth.get_user()
    
    if not user:
        st.error("❌ No user logged in. Please sign in first.")
        return
    
    st.success(f"✅ User logged in: **{user.get('name')}** ({user.get('email')})")
    
    # Test sections
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Google Sheets Integration")
        test_google_sheets_integration()
    
    with col2:
        st.subheader("🎯 MS Clarity Integration")
        test_ms_clarity_integration()
    
    # Session tracking info
    st.subheader("📈 Current Session Information")
    display_session_info(auth)


def test_google_sheets_integration():
    """Test Google Sheets logging functionality"""
    
    try:
        # Check if sheets logger is available
        auth = GoogleAuthManager()
        sheets_logger = auth.gsheet_logger_safe
        
        if not sheets_logger:
            st.error("❌ Google Sheets logger not initialized")
            return
        
        if not sheets_logger.enabled:
            st.error("❌ Google Sheets logging is disabled")
            st.info("Check your secrets configuration for `google_sheets` section")
            return
        
        st.success("✅ Google Sheets logger initialized")
        
        # Test user storage
        user = auth.get_user()
        if user:
            user_data = {
                "email": user.get("email", ""),
                "first_name": user.get("given_name", ""),
                "last_name": user.get("family_name", ""),
                "locale": user.get("locale", ""),
                "user_id": user.get("sub", ""),
                "picture": user.get("picture", "")
            }
            
            # Try to store user (will only store if new)
            if st.button("🧪 Test User Storage"):
                with st.spinner("Testing user storage..."):
                    result = sheets_logger.store_user_if_new(user_data)
                    if result:
                        st.success("✅ User data stored successfully (new user)")
                    else:
                        st.info("ℹ️ User already exists in sheets")
        
        # Test session logging
        session_tracker = auth.get_session_tracker()
        if session_tracker:
            st.success("✅ Session tracker active")
            
            if st.button("🧪 Test Session Logging"):
                with st.spinner("Testing session logging..."):
                    # Log a test session start
                    sheets_logger.log_session_start(
                        email=user.get("email"),
                        session_id=f"test-{int(time.time())}",
                        trace_id=f"test-trace-{int(time.time())}"
                    )
                    st.success("✅ Test session logged successfully")
        else:
            st.warning("⚠️ No session tracker found")
    
    except Exception as e:
        st.error(f"❌ Google Sheets test failed: {str(e)}")
        st.code(str(e))


def test_ms_clarity_integration():
    """Test MS Clarity integration"""
    
    try:
        # Check if Clarity project ID is configured
        clarity_config = st.secrets.get("clarity", {})
        project_id = clarity_config.get("project_id")
        
        if not project_id:
            st.error("❌ MS Clarity project ID not configured")
            st.info("Add `[clarity]` section with `project_id` to your secrets")
            return
        
        st.success(f"✅ MS Clarity configured (Project ID: {project_id})")
        
        # Check if Clarity script is loaded
        st.info("🔍 **How to verify MS Clarity is working:**")
        st.markdown("""
        1. **Open Browser Developer Tools** (F12)
        2. **Go to Network tab**
        3. **Refresh this page**
        4. **Look for requests to `clarity.ms`**
        5. **Or check your [Clarity Dashboard](https://clarity.microsoft.com/)
        """)
        
        # JavaScript test
        st.markdown("**JavaScript Test:**")
        if st.button("🧪 Test Clarity JavaScript"):
            st.components.v1.html("""
            <script>
                if (typeof clarity !== 'undefined') {
                    document.getElementById('clarity-result').innerHTML = '✅ Clarity JavaScript loaded successfully';
                    clarity('event', 'test_event');
                } else {
                    document.getElementById('clarity-result').innerHTML = '❌ Clarity JavaScript not loaded';
                }
            </script>
            <div id="clarity-result">Testing...</div>
            """, height=50)
    
    except Exception as e:
        st.error(f"❌ MS Clarity test failed: {str(e)}")


def display_session_info(auth):
    """Display current session information"""
    
    session_tracker = auth.get_session_tracker()
    user = auth.get_user()
    
    if not session_tracker or not user:
        st.warning("⚠️ Session information not available")
        return
    
    session_data = session_tracker.get_session_data()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Session ID", session_data["session_id"][:8] + "...")
        st.metric("Trace ID", session_data["trace_id"][:12] + "...")
    
    with col2:
        st.metric("Operations", session_data["operations"])
        st.metric("Tokens Used", session_data["tokens_used"])
    
    with col3:
        duration_minutes = session_data["duration_ms"] / 60000
        st.metric("Duration", f"{duration_minutes:.1f} min")
        st.metric("Status", "Active")
    
    # Session details
    with st.expander("📋 Detailed Session Data"):
        st.json(session_data)
    
    # Test session metrics update
    if st.button("🧪 Test Metrics Update"):
        auth.increment_operations(1)
        auth.increment_tokens(10)
        st.success("✅ Metrics updated - check the values above")
        st.rerun()


def render_tracking_status():
    """Render a simple tracking status widget for other pages"""
    
    with st.expander("🔍 Tracking Status", expanded=False):
        # Quick status check
        try:
            # Check MS Clarity
            clarity_config = st.secrets.get("clarity", {})
            clarity_status = "✅" if clarity_config.get("project_id") else "❌"
            
            # Check Google Sheets
            auth = GoogleAuthManager()
            sheets_status = "✅" if auth.gsheet_logger_safe and auth.gsheet_logger_safe.enabled else "❌"
            
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"MS Clarity: {clarity_status}")
            with col2:
                st.write(f"Google Sheets: {sheets_status}")
                
        except Exception:
            st.write("❌ Tracking status unavailable")
