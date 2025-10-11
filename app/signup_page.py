"""
User Signup Page - Request Access to Google Ads Simulator
FIXED: Buttons are now properly separated from forms
"""

import streamlit as st
from utils.user_management_sheets import get_user_manager, UserManagementSheets
from utils.recaptcha import get_recaptcha_manager
import re


def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def show_signup_form(user_mgr):
    """Show the signup form"""
    
    with st.form("signup_form", clear_on_submit=False):
        st.subheader("📋 Access Request Form")
        
        col1, col2 = st.columns(2)
        
        with col1:
            email = st.text_input(
                "Email Address *",
                placeholder="your.email@example.com",
                help="Use your primary email address"
            )
        
        with col2:
            full_name = st.text_input(
                "Full Name *",
                placeholder="John Doe",
                help="Your first and last name"
            )
        
        # Optional fields
        with st.expander("📝 Additional Information (Optional)"):
            organization = st.text_input(
                "Organization/Company",
                placeholder="Company name or 'Individual'"
            )
            
            use_case = st.text_area(
                "Why do you need access?",
                placeholder="e.g., Learning Google Ads for my business, Academic research, Professional development",
                height=100
            )
        
        st.markdown("---")
        
        # Terms and conditions
        agree_terms = st.checkbox(
            "I agree to use this platform for educational purposes only",
            value=False
        )
        
        # reCAPTCHA widget
        recaptcha_mgr = get_recaptcha_manager()
        if recaptcha_mgr.enabled:
            st.markdown("")
            st.markdown("**Verify you're human:**")
            recaptcha_response = recaptcha_mgr.render_recaptcha(key="signup_recaptcha")
        
        # Submit button
        submitted = st.form_submit_button(
            "🚀 Request Access",
            type="primary",
            use_container_width=True
        )
        
        if submitted:
            # Validation
            errors = []
            
            if not email:
                errors.append("Email address is required")
            elif not validate_email(email):
                errors.append("Please enter a valid email address")
            
            if not full_name:
                errors.append("Full name is required")
            elif len(full_name.split()) < 2:
                errors.append("Please enter your full name (first and last name)")
            
            if not agree_terms:
                errors.append("You must agree to the terms to continue")
            
            # Validate reCAPTCHA if enabled
            recaptcha_mgr = get_recaptcha_manager()
            if recaptcha_mgr.enabled:
                recaptcha_token = st.session_state.get('signup_recaptcha', '')
                is_valid, error_msg = recaptcha_mgr.verify_recaptcha(recaptcha_token)
                
                if not is_valid:
                    errors.append(error_msg or "Please complete the reCAPTCHA verification")
            
            # Show errors
            if errors:
                for error in errors:
                    st.error(f"❌ {error}")
            else:
                # Store in session state for processing outside form
                st.session_state.signup_data = {
                    'email': email.strip().lower(),
                    'full_name': full_name.strip(),
                    'organization': organization.strip() if organization else "",
                    'use_case': use_case.strip() if use_case else ""
                }
                st.rerun()


def show_signup_success(user_id, email):
    """Show success message after signup"""
    
    st.success(f"""
    🎉 **Access request submitted successfully!**
    
    **Your User ID:** `{user_id}`  
    **Status:** Pending Review
    
    ✅ Your request has been sent to the administrator  
    ✅ You will be notified once your request is reviewed  
    ✅ Keep your User ID for reference
    
    **What happens next?**
    1. An administrator will review your request
    2. Once approved, you can log in with your Google account
    3. You'll see a success message when you try to log in
    
    **Please bookmark this page and check back later!**
    """)
    
    st.balloons()
    
    st.divider()
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔐 Try Logging In", type="primary", use_container_width=True):
            st.switch_page("main.py")
    
    with col2:
        if st.button("📧 Contact Administrator", use_container_width=True):
            st.info("Contact: admin@yourdomain.com")


def show_existing_user_status(user):
    """Show status for existing users"""
    
    status = user.get("status", "")
    user_id = user.get("user_id", "")
    
    if status == UserManagementSheets.STATUS_PENDING:
        st.info(f"""
        ⏳ **Your access request is already pending review**
        
        **User ID:** `{user_id}`  
        **Status:** Awaiting administrator approval
        
        You'll be able to log in once your request is approved.
        Please check back later or contact the administrator if you have questions.
        """)
    
    elif status == UserManagementSheets.STATUS_APPROVED:
        st.success(f"""
        ✅ **Your access has been approved!**
        
        **User ID:** `{user_id}`  
        **Status:** Approved
        
        You can now log in using your Google account.
        Click the "Login with Google" button to get started!
        """)
        
        if st.button("🔐 Go to Login", type="primary"):
            st.switch_page("main.py")
    
    elif status == UserManagementSheets.STATUS_ACTIVE:
        st.success(f"""
        ✅ **You already have an active account!**
        
        **User ID:** `{user_id}`  
        **Status:** Active
        
        Simply log in using your Google account to continue.
        """)
        
        if st.button("🔐 Go to Login", type="primary"):
            st.switch_page("main.py")
    
    elif status == UserManagementSheets.STATUS_DENIED:
        show_denied_user_reapply(user)
    
    elif status == UserManagementSheets.STATUS_SUSPENDED:
        st.error(f"""
        🚫 **Your account has been suspended**
        
        **User ID:** `{user_id}`  
        **Reason:** {user.get('denial_reason', 'Not specified')}
        
        Please contact the administrator if you believe this is an error.
        """)


def show_denied_user_reapply(user):
    """Show reapplication form for denied users"""
    
    user_id = user.get("user_id", "")
    denial_reason = user.get("denial_reason", "Not specified")
    reapply_count = user.get("reapply_count", 0)
    
    user_mgr = get_user_manager()
    max_reapply = int(user_mgr.get_config_value("max_reapply_count", "3"))
    remaining_attempts = max_reapply - reapply_count
    
    if remaining_attempts > 0:
        st.warning(f"""
        ⚠️ **Your previous access request was denied**
        
        **User ID:** `{user_id}`  
        **Reason for denial:** {denial_reason}  
        **Reapplications remaining:** {remaining_attempts}
        
        You can submit a new request if you believe the issue has been resolved.
        """)
        
        st.divider()
        
        st.subheader("🔄 Reapply for Access")
        
        with st.form("reapply_form"):
            st.text_input("Email", value=user.get("email", ""), disabled=True)
            st.text_input("Name", value=user.get("name", ""), disabled=True)
            
            explanation = st.text_area(
                "Why should we reconsider your application? *",
                placeholder="Explain what has changed or why you believe you should be approved",
                height=100
            )
            
            # reCAPTCHA for reapplication
            recaptcha_mgr = get_recaptcha_manager()
            if recaptcha_mgr.enabled:
                st.markdown("")
                st.markdown("**Verify you're human:**")
                recaptcha_response = recaptcha_mgr.render_recaptcha(key="reapply_recaptcha")
            
            reapply_submitted = st.form_submit_button(
                "🔄 Submit Reapplication",
                type="primary"
            )
            
            if reapply_submitted:
                errors = []
                
                if not explanation:
                    errors.append("Please provide an explanation for your reapplication")
                
                # Validate reCAPTCHA if enabled
                if recaptcha_mgr.enabled:
                    recaptcha_token = st.session_state.get('reapply_recaptcha', '')
                    is_valid, error_msg = recaptcha_mgr.verify_recaptcha(recaptcha_token)
                    
                    if not is_valid:
                        errors.append(error_msg or "Please complete the reCAPTCHA verification")
                
                if errors:
                    for error in errors:
                        st.error(f"❌ {error}")
                else:
                    # Store in session state
                    st.session_state.reapply_data = {
                        'email': user.get("email"),
                        'explanation': explanation,
                        'reapply_count': reapply_count
                    }
                    st.rerun()
    else:
        st.error(f"""
        ❌ **Maximum reapplication attempts reached**
        
        **User ID:** `{user_id}`  
        **Original denial reason:** {denial_reason}  
        **Reapplication attempts used:** {reapply_count}/{max_reapply}
        
        You have reached the maximum number of reapplication attempts.
        Please contact the administrator directly if you need further assistance.
        """)


def process_signup(user_mgr, signup_data):
    """Process signup request"""
    
    email = signup_data['email']
    full_name = signup_data['full_name']
    organization = signup_data.get('organization', '')
    use_case = signup_data.get('use_case', '')
    
    # Check if user already exists
    existing_user = user_mgr.get_user_by_email(email)
    
    if existing_user:
        # Store user data for display
        st.session_state.existing_user = existing_user
        return
    
    # Build notes for admin
    notes = []
    if organization:
        notes.append(f"Organization: {organization}")
    if use_case:
        notes.append(f"Use case: {use_case}")
    
    notes_str = " | ".join(notes) if notes else ""
    
    # Add user signup
    result = user_mgr.add_user_signup(
        email=email,
        name=full_name,
        added_by="self"
    )
    
    if result.get("success"):
        user_id = result.get("user_id")
        
        # Add notes if provided
        if notes_str:
            user_mgr.update_user_status(
                email=email,
                new_status=UserManagementSheets.STATUS_PENDING,
                notes=notes_str
            )
        
        # Store success data
        st.session_state.signup_success = {
            'user_id': user_id,
            'email': email
        }
    else:
        st.error(f"""
        ❌ **Failed to submit access request**
        
        Error: {result.get('error', 'Unknown error')}
        
        Please try again or contact the administrator for assistance.
        """)


def process_reapply(user_mgr, reapply_data):
    """Process reapplication"""
    
    email = reapply_data['email']
    explanation = reapply_data['explanation']
    reapply_count = reapply_data['reapply_count']
    
    notes = f"Reapplication #{reapply_count + 1}: {explanation}"
    
    success = user_mgr.update_user_status(
        email=email,
        new_status=UserManagementSheets.STATUS_PENDING,
        notes=notes
    )
    
    if success:
        user = user_mgr.get_user_by_email(email)
        st.session_state.reapply_success = True
        st.session_state.existing_user = user
    else:
        st.error("❌ Failed to submit reapplication. Please try again or contact support.")


def show_signup_help():
    """Show help information"""
    
    with st.expander("❓ Frequently Asked Questions"):
        st.markdown("""
        ### How long does approval take?
        Typically within 24-48 hours. Check back by trying to log in.
        
        ### What email should I use?
        Use your primary email address. This will be linked to your Google account for login.
        
        ### What if I made a mistake?
        Contact the administrator with your User ID to update your information.
        
        ### Why was my request denied?
        Common reasons include: invalid email domain, incomplete information, or policy violations.
        You can reapply up to 3 times with additional explanation.
        
        ### Can I check my status?
        Yes! Simply try to log in with Google. You'll see your current status.
        
        ### Who can I contact for help?
        Email: admin@yourdomain.com
        """)


def main():
    """Main function for signup page"""
    
    # Check if user is already logged in
    user = st.session_state.get("user")
    if user:
        st.info("✅ You're already logged in!")
        if st.button("Go to Dashboard"):
            st.switch_page("main.py")
        return
    
    # Page header
    st.title("🎯 Request Access to Google Ads Simulator")
    
    st.markdown("""
    Welcome! This is an educational platform for learning Google Ads campaign management.
    
    **To get started:**
    1. Fill out the form below
    2. You'll receive a unique User ID
    3. An administrator will review your request
    4. Once approved, you can log in and start learning!
    """)
    
    st.divider()
    
    # Initialize user manager
    user_mgr = get_user_manager()
    
    if not user_mgr.enabled:
        st.error("""
        ❌ **User management system is not available.**
        
        Please contact the administrator to enable access management.
        """)
        return
    
    # Process signup data if it exists
    if 'signup_data' in st.session_state:
        signup_data = st.session_state.signup_data
        del st.session_state.signup_data
        process_signup(user_mgr, signup_data)
        st.rerun()
    
    # Process reapply data if it exists
    if 'reapply_data' in st.session_state:
        reapply_data = st.session_state.reapply_data
        del st.session_state.reapply_data
        process_reapply(user_mgr, reapply_data)
        st.rerun()
    
    # Show success message if signup was successful
    if 'signup_success' in st.session_state:
        success_data = st.session_state.signup_success
        del st.session_state.signup_success
        show_signup_success(success_data['user_id'], success_data['email'])
        return
    
    # Show reapply success message
    if 'reapply_success' in st.session_state:
        del st.session_state.reapply_success
        st.success("""
        ✅ **Reapplication submitted successfully!**
        
        An administrator will review your request again.
        You'll be able to log in once approved.
        """)
        st.balloons()
    
    # Show existing user status if applicable
    if 'existing_user' in st.session_state:
        user = st.session_state.existing_user
        del st.session_state.existing_user
        show_existing_user_status(user)
        return
    
    # Show signup form
    show_signup_form(user_mgr)
    
    # Show help section
    st.divider()
    show_signup_help()
    
    # Footer
    st.markdown("---")
    st.caption("🎓 Google Ads Simulator - Educational Platform")


if __name__ == "__main__":
    main()
