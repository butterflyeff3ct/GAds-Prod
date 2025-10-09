diff --git a/app/login_page.py b/app/login_page.py
index 0e6df4c4709148117353ce930066bfdf51989c25..cdc5a298fb07a2ca67619ceb1729361c037b0a14 100644
--- a/app/login_page.py
+++ b/app/login_page.py
@@ -1,37 +1,40 @@
 # app/login_page.py
 """
 Login Page
 First page users see - handles Google OAuth login flow.
 """
 
 import streamlit as st
 from datetime import datetime, timedelta

 from auth.google_oauth import GoogleOAuthManager
 from auth.session_manager import SessionManager
 from auth.quota_manager import QuotaManager
 from auth.user_activity import UserActivityLogger
 from database.db_manager import get_database_manager
 from app.utils import clear_query_params, get_query_params
 
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
diff --git a/app/login_page.py b/app/login_page.py
index 0e6df4c4709148117353ce930066bfdf51989c25..cdc5a298fb07a2ca67619ceb1729361c037b0a14 100644
--- a/app/login_page.py
+++ b/app/login_page.py
@@ -86,87 +89,89 @@ def render_login_page():
         st.info("Please try again in a few minutes when capacity is available.")
     else:
         # Google Sign-In button
         if st.button("🔐 Sign in with Google", type="primary", use_container_width=True):
             # Check if OAuth is configured
             if not oauth_manager.is_configured():
                 st.error("🔧 OAuth not configured. Please contact administrator.")
                 return
                 
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
         query_params = get_query_params()
         code_values = query_params.get('code')
         if code_values:
             with st.spinner("🔐 Authenticating..."):
                 # Build callback URL
                 code = query_params['code']
                 code = code_values[0]
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
                    
                     clear_query_params()

                     # Success
                     st.success(f"✅ Welcome, {user_info['name']}!")
                     st.balloons()
                     
                     # Redirect to main app
                     st.rerun()
                 else:
                     st.error("❌ Authentication failed. Please try again.")
                     clear_query_params()
     
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
