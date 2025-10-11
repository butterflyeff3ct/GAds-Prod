"""
Login Gate - User Status Check and Access Control
Integrates with Google OAuth to enforce approval workflow
"""

import streamlit as st
from utils.user_management_sheets import get_user_manager, UserManagementSheets
from typing import Dict, Tuple, Optional


def check_user_access(email: str, name: str = "", user_info: Dict = None) -> Tuple[bool, str, Optional[Dict]]:
    """
    Check if user has access to the application
    
    Args:
        email: User email from OAuth
        name: User name from OAuth (optional)
        user_info: Full OAuth user info (optional)
    
    Returns:
        Tuple of (has_access: bool, message: str, user_data: dict or None)
    """
    
    user_mgr = get_user_manager()
    
    if not user_mgr.enabled:
        # User management not available - allow access (backward compatibility)
        return True, "User management not enabled", None
    
    # Get user from database
    user = user_mgr.get_user_by_email(email)
    
    # New user - needs to sign up
    if not user:
        return False, "new_user", None
    
    status = user.get("status", "")
    
    # Check status and return appropriate response
    if status == UserManagementSheets.STATUS_PENDING:
        return False, "pending", user
    
    elif status == UserManagementSheets.STATUS_DENIED:
        return False, "denied", user
    
    elif status == UserManagementSheets.STATUS_SUSPENDED:
        return False, "suspended", user
    
    elif status in [UserManagementSheets.STATUS_APPROVED, UserManagementSheets.STATUS_ACTIVE]:
        # Update login timestamp
        is_first = (status == UserManagementSheets.STATUS_APPROVED)
        user_mgr.update_user_login(email=email, is_first_login=is_first)
        
        # Store user info in session
        st.session_state.user_id = user.get("user_id")
        st.session_state.user_email = email
        st.session_state.user_name = name or user.get("name", "")
        st.session_state.user_status = UserManagementSheets.STATUS_ACTIVE
        
        return True, "approved", user
    
    else:
        # Unknown status - deny access
        return False, "unknown", user


def show_access_denied_message(message_type: str, user_data: Optional[Dict] = None, email: str = ""):
    """
    Display appropriate access denied message based on user status
    
    Args:
        message_type: Type of message (new_user, pending, denied, suspended, unknown)
        user_data: User data from database (if available)
        email: User email for new users
    """
    
    if message_type == "new_user":
        show_new_user_message(email)
    
    elif message_type == "pending":
        show_pending_message(user_data)
    
    elif message_type == "denied":
        show_denied_message(user_data)
    
    elif message_type == "suspended":
        show_suspended_message(user_data)
    
    elif message_type == "unknown":
        show_unknown_status_message(user_data)


def show_new_user_message(email: str):
    """Show message for new users who need to sign up"""
    
    st.warning("""
    🆕 **Welcome! You're new here.**
    
    To access the Google Ads Simulator, you need to request access first.
    """)
    
    st.info(f"""
    **Your Email:** {email}
    
    Click the button below to submit an access request.
    You'll receive a User ID and be notified once approved.
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📝 Request Access", type="primary", use_container_width=True):
            st.switch_page("pages/1_📝_Request_Access.py")
    
    with col2:
        if st.button("❓ Learn More", use_container_width=True):
            with st.expander("About Access Requests", expanded=True):
                st.markdown("""
                ### Why do I need approval?
                
                This platform is designed for serious learners and professionals.
                Our approval process ensures quality and prevents abuse.
                
                ### What happens next?
                
                1. Submit your access request
                2. Get a unique User ID
                3. Admin reviews your request (24-48 hours)
                4. Once approved, log in and start learning!
                
                ### Questions?
                Contact: me3tpatil@gmail.com
                """)


def show_pending_message(user_data: Dict):
    """Show message for users with pending approval"""
    
    user_id = user_data.get("user_id", "N/A")
    signup_time = user_data.get("signup_timestamp", "Unknown")
    
    st.info(f"""
    ⏳ **Your access request is pending review**
    
    **User ID:** `{user_id}`  
    **Submitted:** {signup_time}  
    **Status:** Awaiting administrator approval
    """)
    
    st.markdown("""
    ### What's happening?
    
    Your request is in the queue for administrator review.
    This typically takes 24-48 hours.
    
    ### What can I do?
    
    - ✅ **Check back later** - Try logging in again to see if you've been approved
    - 📧 **Contact admin** - If it's urgent, reach out with your User ID
    - 🔄 **Be patient** - All requests are reviewed carefully
    
    **You'll be able to access the platform immediately once approved!**
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 Refresh Status", type="primary", use_container_width=True):
            st.rerun()
    
    with col2:
        if st.button("📧 Contact Admin", use_container_width=True):
            st.info("Email: me3tpatil@gmail.com")  # Update this


def show_denied_message(user_data: Dict):
    """Show message for denied users with reapplication option"""
    
    user_id = user_data.get("user_id", "N/A")
    denial_reason = user_data.get("denial_reason", "Not specified")
    reapply_count = user_data.get("reapply_count", 0)
    
    user_mgr = get_user_manager()
    max_reapply = int(user_mgr.get_config_value("max_reapply_count", "3"))
    remaining_attempts = max_reapply - reapply_count
    
    st.error(f"""
    ❌ **Your access request was denied**
    
    **User ID:** `{user_id}`  
    **Reason:** {denial_reason}  
    **Reapplication attempts remaining:** {remaining_attempts}
    """)
    
    if remaining_attempts > 0:
        st.warning("""
        ### You can reapply!
        
        If you believe the issue has been resolved or you can provide
        additional context, you're welcome to submit a new request.
        """)
        
        if st.button("🔄 Submit Reapplication", type="primary"):
            st.switch_page("pages/1_📝_Request_Access.py")
    else:
        st.error(f"""
        ### Maximum reapplication attempts reached
        
        You have used all {max_reapply} reapplication attempts.
        Please contact the administrator directly if you need access.
        
        **Contact:** me3tpatil@gmail.com
        """)


def show_suspended_message(user_data: Dict):
    """Show message for suspended users"""
    
    user_id = user_data.get("user_id", "N/A")
    suspension_reason = user_data.get("denial_reason", "Policy violation")
    
    st.error(f"""
    🚫 **Your account has been suspended**
    
    **User ID:** `{user_id}`  
    **Reason:** {suspension_reason}
    
    Your access to the platform has been suspended by an administrator.
    """)
    
    st.warning("""
    ### What does this mean?
    
    Account suspension means your access has been revoked due to:
    - Policy violations
    - Terms of service breach
    - Administrative action
    
    ### What can I do?
    
    If you believe this is an error, please contact the administrator
    with your User ID to appeal this decision.
    
    **Contact:** me3tpatil@gmail.com
    """)


def show_unknown_status_message(user_data: Dict):
    """Show message for users with unknown status"""
    
    user_id = user_data.get("user_id", "N/A") if user_data else "Unknown"
    
    st.error(f"""
    ⚠️ **Account status unknown**
    
    **User ID:** `{user_id}`
    
    There's an issue with your account status.
    Please contact the administrator for assistance.
    
    **Contact:** me3tpatil@gmail.com
    """)


def require_approval(email: str, name: str = "", user_info: Dict = None):
    """
    Decorator-style function to protect pages that require approval
    Call this at the top of any protected page
    
    Args:
        email: User email from OAuth
        name: User name from OAuth
        user_info: Full OAuth user info
    
    Returns:
        True if user has access, False otherwise (and stops execution)
    """
    
    has_access, message, user_data = check_user_access(email, name, user_info)
    
    if not has_access:
        show_access_denied_message(message, user_data, email)
        st.stop()
    
    return True


def get_user_display_info() -> Dict[str, str]:
    """
    Get user display information from session
    
    Returns:
        Dict with user_id, email, name, status
    """
    return {
        "user_id": st.session_state.get("user_id", ""),
        "email": st.session_state.get("user_email", ""),
        "name": st.session_state.get("user_name", ""),
        "status": st.session_state.get("user_status", "")
    }


# Integration helper functions

def integrate_with_oauth_login(user_info: Dict) -> bool:
    """
    Helper function to integrate with your existing OAuth login
    
    Usage in your auth code:
        user_info = google_oauth.get_user_info()
        if integrate_with_oauth_login(user_info):
            # User has access - proceed with login
            show_main_app()
        else:
            # Access denied message already shown
            # No need to do anything else
    
    Args:
        user_info: Dictionary with 'email' and 'name' from OAuth
    
    Returns:
        True if user has access, False otherwise
    """
    
    email = user_info.get("email", "")
    name = user_info.get("name", "")
    
    has_access, message, user_data = check_user_access(email, name, user_info)
    
    if not has_access:
        show_access_denied_message(message, user_data, email)
        return False
    
    return True


# Example integration code for your main.py

def example_main_integration():
    """
    Example of how to integrate login gate into your main.py
    Copy this pattern into your actual main.py
    """
    
    # Your existing OAuth code
    # user_info = perform_google_oauth()  # Your existing function
    
    # Add this check after OAuth
    user_info = {
        "email": "user@example.com",
        "name": "John Doe"
    }
    
    if not integrate_with_oauth_login(user_info):
        # User doesn't have access
        # Access denied message is already shown
        st.stop()
    
    # If we reach here, user has access
    # Continue with your normal app flow
    st.success("✅ Welcome! You have access to the simulator.")
    # show_your_main_app()
