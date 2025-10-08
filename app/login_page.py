# app/login_page.py
"""
Login Page
First page users see - handles Google OAuth login flow.
"""

import streamlit as st
from auth.google_oauth import GoogleOAuthManager
from auth.session_manager import SessionManager
from auth.quota_manager import QuotaManager
from auth.user_activity import UserActivityLogger
from database.db_manager import get_database_manager

def render_login_page():
    """
    Render the login page with Google OAuth button.
    This is the first page users see before accessing the simulator.
    """
    
    # Custom CSS for login page
    st.markdown("""
    <style>
        .login-container {
            max-width: 500px;
            margin: 100px auto;
            padding: 40px;
            background: white;
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            text-align: center;
        }
        .app-logo {
            font-size: 48px;
            margin-bottom: 20px;
        }
        .app-title {
            font-size: 32px;
            font-weight: 700;
            color: #202124;
            margin-bottom: 10px;
        }
        .app-subtitle {
            font-size: 16px;
            color: #5f6368;
            margin-bottom: 40px;
        }
        .login-button {
            background: #4285F4;
            color: white;
            padding: 12px 24px;
            border-radius: 4px;
            border: none;
            font-size: 16px;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            gap: 10px;
        }
        .features-list {
            text-align: left;
            margin-top: 40px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 8px;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Main login container
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    
    # Logo and title
    st.markdown('<div class="app-logo">📊</div>', unsafe_allow_html=True)
    st.markdown('<div class="app-title">Google Ads Simulator</div>', unsafe_allow_html=True)
    st.markdown('<div class="app-subtitle">Educational platform for mastering Google Ads Search campaigns</div>', unsafe_allow_html=True)
    
    # Initialize managers
    oauth_manager = GoogleOAuthManager()
    quota_manager = QuotaManager()
    
    # Check global quota (10 users/hour limit)
    can_login, global_message = quota_manager.check_global_limit('concurrent_users')
    
    if not can_login:
        st.error(f"⚠️ {global_message}")
        st.info("Please try again in a few minutes when capacity is available.")
    else:
        # Google Sign-In button
        if st.button("🔐 Sign in with Google", type="primary", use_container_width=True):
            # Get authorization URL
            auth_url = oauth_manager.get_authorization_url()
            
            if auth_url:
                st.markdown(f'<a href="{auth_url}" target="_blank" style="display:none" id="oauth_link"></a>', unsafe_allow_html=True)
                st.markdown("""
                <script>
                    document.getElementById('oauth_link').click();
                </script>
                """, unsafe_allow_html=True)
                
                st.info("🔄 Redirecting to Google login...")
            else:
                st.error("OAuth configuration error. Please contact administrator.")
        
        # Handle OAuth callback
        query_params = st.query_params
        if 'code' in query_params:
            with st.spinner("🔐 Authenticating..."):
                # Build callback URL
                code = query_params['code']
                authorization_response = f"{oauth_manager.oauth_config['redirect_uri']}?code={code}"
                
                # Handle callback
                user_info = oauth_manager.handle_callback(authorization_response)
                
                if user_info:
                    # Create/update user in database
                    db_manager = get_database_manager()
                    user = db_manager.create_or_update_user(user_info)
                    
                    # Create session
                    session_id = SessionManager.create_session(user_info)
                    
                    # Save to database
                    expires_at = datetime.now() + timedelta(hours=2)
                    db_manager.create_session(user_info['email'], session_id, expires_at)
                    
                    # Log activity
                    UserActivityLogger.log_activity(user_info['email'], 'login')
                    db_manager.log_activity(user_info['email'], 'login', {'method': 'google_oauth'})
                    
                    # Clear query params
                    st.query_params.clear()
                    
                    # Success
                    st.success(f"✅ Welcome, {user_info['name']}!")
                    st.balloons()
                    
                    # Redirect to main app
                    st.rerun()
                else:
                    st.error("❌ Authentication failed. Please try again.")
    
    # Features section
    st.markdown("""
    <div class="features-list">
        <h3 style="margin-top: 0;">🎓 What you'll learn:</h3>
        <ul style="line-height: 2;">
            <li>✅ Complete Google Ads campaign setup</li>
            <li>✅ Auction mechanics and bidding strategies</li>
            <li>✅ Quality Score optimization</li>
            <li>✅ Keyword research and targeting</li>
            <li>✅ Budget management and pacing</li>
            <li>✅ Performance analysis and reporting</li>
        </ul>
        
        <h3>🔒 Secure & Private:</h3>
        <ul style="line-height: 2;">
            <li>✅ Secure Google OAuth login</li>
            <li>✅ Your data stays private</li>
            <li>✅ No credit card required</li>
            <li>✅ Free educational access</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Footer
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.caption("🔐 Secure Login")
    with col2:
        st.caption("📚 Educational Use")
    with col3:
        st.caption("🆓 Free Access")
