"""
Admin Dashboard - User Management and Approval System
Allows administrators to review, approve, and manage user access requests
"""

import streamlit as st
from utils.user_management_sheets import get_user_manager, UserManagementSheets
from utils.email_notifications import get_email_notifier
import pandas as pd
from datetime import datetime


def is_admin(email: str) -> bool:
    """
    Check if user is an administrator
    
    Update this function with your admin emails or implement
    a more sophisticated admin check
    """
    # TODO: Update this list with your admin emails
    admin_emails = [
        "me3tpatil@gmail.com",
    ]
    
    return email.lower() in [e.lower() for e in admin_emails]


def show_admin_dashboard():
    """Main admin dashboard interface"""
    
    # Check if user is logged in
    user = st.session_state.get("user")
    if not user:
        st.error("🔐 Please log in to access the admin dashboard")
        st.info("Please return to the main page and log in with Google.")
        return
    
    user_email = user.get("email", "")
    
    # Check if user is admin
    if not is_admin(user_email):
        st.error("⛔ Access Denied: Admin privileges required")
        st.info(f"Your email: {user_email}")
        return
    
    # Initialize user manager
    user_mgr = get_user_manager()
    
    if not user_mgr.enabled:
        st.error("❌ User management system is not available")
        return
    
    # Dashboard header
    st.title("👨‍💼 Admin Dashboard")
    st.caption(f"Logged in as: {user_email}")
    
    # Dashboard tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "⏳ Pending Approvals",
        "👥 All Users",
        "➕ Add User Manually",
        "⚙️ Settings"
    ])
    
    with tab1:
        show_pending_approvals_tab(user_mgr, user_email)
    
    with tab2:
        show_all_users_tab(user_mgr)
    
    with tab3:
        show_add_user_tab(user_mgr, user_email)
    
    with tab4:
        show_settings_tab(user_mgr)


def show_pending_approvals_tab(user_mgr, admin_email: str):
    """Show pending user approval requests"""
    
    st.header("⏳ Pending User Approvals")
    
    # Get pending users
    pending_users = user_mgr.get_pending_users()
    
    if not pending_users:
        st.success("✅ No pending approvals! All caught up.")
        st.info("New signup requests will appear here for your review.")
        return
    
    # Show count
    st.info(f"📊 **{len(pending_users)} user(s)** awaiting approval")
    
    # Bulk actions
    with st.expander("🔧 Bulk Actions"):
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("✅ Approve All", type="primary", use_container_width=True):
                if st.session_state.get("confirm_bulk_approve"):
                    success_count = 0
                    for user in pending_users:
                        if user_mgr.update_user_status(
                            email=user['email'],
                            new_status='approved',
                            notes=f"Bulk approved by {admin_email}"
                        ):
                            success_count += 1
                    
                    st.success(f"✅ Approved {success_count} users!")
                    st.session_state.confirm_bulk_approve = False
                    st.rerun()
                else:
                    st.session_state.confirm_bulk_approve = True
                    st.warning("⚠️ Click again to confirm bulk approval")
        
        with col2:
            if st.button("❌ Deny All", use_container_width=True):
                st.warning("Use individual denial to provide specific reasons")
    
    st.divider()
    
    # Show each pending user
    for idx, user in enumerate(pending_users):
        show_user_approval_card(user_mgr, user, admin_email, idx)


def show_user_approval_card(user_mgr, user: dict, admin_email: str, idx: int):
    """Display individual user approval card"""
    
    with st.container(border=True):
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.subheader(f"📧 {user['email']}")
            
            col_info1, col_info2 = st.columns(2)
            
            with col_info1:
                st.write(f"**Name:** {user.get('name', 'N/A')}")
                st.write(f"**User ID:** `{user['user_id']}`")
            
            with col_info2:
                st.write(f"**Submitted:** {user.get('signup_timestamp', 'Unknown')}")
                st.write(f"**Source:** {user.get('added_by', 'N/A')}")
            
            # Show notes if available
            notes = user.get('notes', '')
            if notes:
                with st.expander("📝 Additional Information"):
                    st.info(notes)
        
        with col2:
            st.write("")  # Spacing
            
            # Approve button
            if st.button(
                "✅ Approve",
                key=f"approve_{idx}",
                type="primary",
                use_container_width=True
            ):
                success = user_mgr.update_user_status(
                    email=user['email'],
                    new_status='approved',
                    notes=f"Approved by {admin_email}"
                )
                
                if success:
                    st.success(f"✅ Approved {user['email']}")
                    
                    # Send approval email
                    email_notifier = get_email_notifier()
                    if email_notifier.enabled:
                        with st.spinner("Sending approval email..."):
                            email_sent = email_notifier.send_approval_email(
                                to_email=user['email'],
                                user_name=user.get('name', 'User'),
                                user_id=user['user_id']
                            )
                            if email_sent:
                                st.info("✉️ Approval email sent successfully")
                            else:
                                st.warning("⚠️ User approved but email failed to send")
                    
                    st.rerun()
                else:
                    st.error("❌ Failed to approve user")
            
            # Deny section - using expander instead of popover
            with st.expander("❌ Deny with Reason"):
                denial_reason = st.text_area(
                    "Reason for denial *",
                    placeholder="e.g., Invalid email domain, Incomplete information, Policy violation",
                    key=f"reason_{idx}",
                    height=100
                )
                
                col_deny1, col_deny2 = st.columns(2)
                with col_deny1:
                    if st.button("Confirm Denial", key=f"deny_confirm_{idx}", type="secondary", use_container_width=True):
                        if not denial_reason:
                            st.error("Please provide a reason")
                        else:
                            success = user_mgr.update_user_status(
                                email=user['email'],
                                new_status='denied',
                                denial_reason=denial_reason,
                                notes=f"Denied by {admin_email}: {denial_reason}"
                            )
                            
                            if success:
                                st.success(f"❌ Denied {user['email']}")
                                
                                # Send denial email
                                email_notifier = get_email_notifier()
                                if email_notifier.enabled:
                                    with st.spinner("Sending denial email..."):
                                        # Check if user can reapply
                                        reapply_count = user.get('reapply_count', 0)
                                        max_reapply = int(user_mgr.get_config_value('max_reapply_count', '3'))
                                        can_reapply = reapply_count < max_reapply
                                        
                                        email_sent = email_notifier.send_denial_email(
                                            to_email=user['email'],
                                            user_name=user.get('name', 'User'),
                                            user_id=user['user_id'],
                                            denial_reason=denial_reason,
                                            can_reapply=can_reapply
                                        )
                                        if email_sent:
                                            st.info("✉️ Denial email sent successfully")
                                        else:
                                            st.warning("⚠️ User denied but email failed to send")
                                
                                st.rerun()
                            else:
                                st.error("Failed to deny user")
                
                with col_deny2:
                    if st.button("Cancel", key=f"deny_cancel_{idx}", use_container_width=True):
                        st.info("Cancelled")
        
        st.divider()


def show_all_users_tab(user_mgr):
    """Show all users with filtering and search"""
    
    st.header("👥 All Users")
    
    # Note: This requires additional method in user_management_sheets.py
    # For now, show a message
    st.info("""
    **User List View - Coming Soon**
    
    This section will display:
    - All users with status filters
    - Search by email/name/User ID
    - Quick status change actions
    - User activity history
    
    For now, you can view user data directly in Google Sheets.
    """)
    
    # Quick stats
    col1, col2, col3, col4 = st.columns(4)
    
    # These would come from actual queries
    with col1:
        st.metric("Total Users", "—")
    with col2:
        st.metric("Active", "—")
    with col3:
        st.metric("Pending", "—")
    with col4:
        st.metric("Denied", "—")


def show_add_user_tab(user_mgr, admin_email: str):
    """Manually add users (pre-approved)"""
    
    st.header("➕ Add User Manually")
    
    st.info("""
    **Pre-approve users without requiring signup**
    
    Use this to manually add:
    - Beta testers
    - VIP users
    - Team members
    - Special access users
    
    These users will be immediately approved and can log in right away.
    """)
    
    with st.form("add_user_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            email = st.text_input(
                "Email Address *",
                placeholder="user@example.com"
            )
        
        with col2:
            name = st.text_input(
                "Full Name *",
                placeholder="John Doe"
            )
        
        notes = st.text_area(
            "Admin Notes (Optional)",
            placeholder="e.g., Beta tester, Team member, VIP access",
            help="Internal notes visible only to admins"
        )
        
        submitted = st.form_submit_button("➕ Add User", type="primary")
        
        if submitted:
            if not email or not name:
                st.error("❌ Email and name are required")
            else:
                # Add user with admin as added_by (pre-approved)
                result = user_mgr.add_user_signup(
                    email=email.strip().lower(),
                    name=name.strip(),
                    added_by=admin_email
                )
                
                if result.get("success"):
                    user_id = result.get("user_id")
                    
                    # Add notes if provided
                    if notes:
                        user_mgr.update_user_status(
                            email=email.strip().lower(),
                            new_status='approved',
                            notes=notes
                        )
                    
                    st.success(f"""
                    ✅ **User added successfully!**
                    
                    **Email:** {email}  
                    **User ID:** `{user_id}`  
                    **Status:** Approved (can log in immediately)
                    """)
                    
                    st.balloons()
                else:
                    error = result.get("error", "Unknown error")
                    if "already exists" in error:
                        st.warning(f"⚠️ User already exists: {email}")
                    else:
                        st.error(f"❌ Failed to add user: {error}")


def show_settings_tab(user_mgr):
    """Show and manage system settings"""
    
    st.header("⚙️ System Settings")
    
    # Email Configuration Status
    email_notifier = get_email_notifier()
    
    st.subheader("📧 Email Notifications")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if email_notifier.enabled:
            st.success("✅ Email notifications are **ENABLED**")
            st.info(f"📨 Sending from: {email_notifier.sender_email}")
        else:
            st.warning("⚠️ Email notifications are **DISABLED**")
            st.info("Configure in `.streamlit/secrets.toml` to enable")
    
    with col2:
        if email_notifier.enabled:
            st.write("**Test Email Configuration:**")
            test_email = st.text_input(
                "Send test email to:",
                placeholder="your.email@example.com",
                key="test_email_input"
            )
            
            if st.button("🧪 Send Test Email", type="primary"):
                if test_email:
                    with st.spinner("Sending test email..."):
                        success = email_notifier.send_test_email(test_email)
                        if success:
                            st.success(f"✅ Test email sent to {test_email}!")
                            st.balloons()
                        else:
                            st.error("❌ Failed to send test email. Check your SMTP configuration.")
                else:
                    st.error("Please enter an email address")
    
    st.divider()
    
    # reCAPTCHA Configuration Status
    from utils.recaptcha import get_recaptcha_manager
    recaptcha_mgr = get_recaptcha_manager()
    
    st.subheader("🤖 reCAPTCHA Bot Protection")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if recaptcha_mgr.enabled:
            st.success("✅ reCAPTCHA is **ENABLED**")
            st.info(f"🔑 Version: {recaptcha_mgr.version.upper()}")
        else:
            st.warning("⚠️ reCAPTCHA is **DISABLED**")
            st.info("Configure in `.streamlit/secrets.toml` to enable")
    
    with col2:
        if recaptcha_mgr.enabled:
            st.write("**Protection Status:**")
            st.success("✅ Signup form protected")
            st.success("✅ Reapplication form protected")
        else:
            st.write("**When Enabled:**")
            st.info("⚡ Blocks automated bot signups")
            st.info("⚡ Prevents spam submissions")
    
    st.divider()
    
    # System Configuration
    st.subheader("⚙️ System Configuration")
    
    st.info("""
    **Configuration Settings**
    
    These settings are stored in the Admin Config worksheet
    in your Google Sheets. Changes here will update the sheet.
    """)
    
    # Get current settings
    auto_approve = user_mgr.get_config_value("auto_approve_enabled", "false")
    max_reapply = user_mgr.get_config_value("max_reapply_count", "3")
    session_timeout = user_mgr.get_config_value("session_timeout_mins", "30")
    require_review = user_mgr.get_config_value("require_admin_review", "true")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Auto-Approve Enabled", auto_approve.upper())
        st.metric("Max Reapply Count", max_reapply)
    
    with col2:
        st.metric("Session Timeout (mins)", session_timeout)
        st.metric("Require Admin Review", require_review.upper())
    
    st.divider()
    
    st.subheader("Update Settings")
    
    st.warning("""
    ⚠️ **Note:** To update these settings, you need to:
    1. Open your Google Sheets
    2. Go to the "Admin Config" tab
    3. Modify the "Value" column for the setting you want to change
    4. Changes take effect immediately
    
    **Future Enhancement:** Settings editor will be added here.
    """)
    
    # Direct link to Google Sheets
    sheet_id = st.secrets.get("google_sheets", {}).get("sheet_id", "")
    if sheet_id:
        sheet_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit#gid=0"
        st.link_button("📊 Open Google Sheets", sheet_url, type="primary")


def show_admin_stats(user_mgr):
    """Show admin dashboard statistics"""
    
    st.subheader("📊 Quick Stats")
    
    # Get pending count
    pending = user_mgr.get_pending_users()
    pending_count = len(pending)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Pending Approvals", pending_count)
    
    with col2:
        st.metric("Today's Signups", "—")  # Would need date filtering
    
    with col3:
        st.metric("Active Users", "—")  # Would need status filtering
    
    with col4:
        st.metric("Total Users", "—")  # Would need count query


# Main function
def main():
    """Main function for admin dashboard"""
    
    # Set page config
    st.set_page_config(
        page_title="Admin Dashboard",
        page_icon="👨‍💼",
        layout="wide"
    )
    
    # Show dashboard
    show_admin_dashboard()
    
    # Footer
    st.divider()
    st.caption("🎓 Google Ads Simulator - Admin Dashboard")


if __name__ == "__main__":
    main()
