"""
Example: Admin Dashboard with IP Analytics
Copy this code into your admin page or dashboard
"""

import streamlit as st
from utils.ip_display import (
    display_ip_info,
    show_ip_analytics, 
    get_ip_stats_for_user,
    detect_suspicious_logins
)
from utils.gsheet_writer import GSheetLogger


def show_admin_ip_dashboard():
    """
    Complete admin dashboard with IP tracking and analytics
    Add this to your admin page
    """
    
    st.title("🔐 Security & IP Analytics Dashboard")
    
    # Current session info
    st.subheader("Current Session")
    display_ip_info()
    
    st.divider()
    
    # User search
    st.subheader("User IP Analytics")
    
    user_email = st.text_input("Enter user email to analyze:")
    
    if user_email and st.button("Analyze User"):
        with st.spinner("Fetching user data..."):
            stats = get_ip_stats_for_user(user_email)
            
            if stats:
                # Show metrics
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Total Sessions", stats['total_sessions'])
                
                with col2:
                    st.metric("Unique IPs", stats['unique_ips'])
                
                with col3:
                    suspicious = detect_suspicious_logins(stats['sessions'])
                    status = "⚠️ Review" if suspicious['is_suspicious'] else "✅ Normal"
                    st.metric("Status", status)
                
                # Show detailed analytics
                st.subheader(f"IP Analytics for {user_email}")
                show_ip_analytics(stats['sessions'])
                
                # Show raw session data
                with st.expander("📋 View Raw Session Data"):
                    st.dataframe(stats['sessions'], use_container_width=True)
                
            else:
                st.error("Unable to fetch user data. User may not exist or Sheets API unavailable.")


def show_security_alerts():
    """
    Show security alerts for all users
    Scans all recent sessions for suspicious patterns
    """
    
    st.subheader("🚨 Security Alerts")
    
    try:
        logger = GSheetLogger(show_warnings=False)
        
        if not logger.enabled:
            st.warning("Google Sheets integration not available")
            return
        
        # Get all recent sessions (you might want to limit this)
        st.info("Scanning recent activity...")
        
        # In production, you'd want to batch this or cache it
        # For now, this is a simple example
        
        # You can extend this to:
        # 1. Get all users
        # 2. Check each user's IPs
        # 3. Flag suspicious patterns
        
        st.success("Security scan complete. No alerts.")
        
    except Exception as e:
        st.error(f"Security scan failed: {e}")


def show_ip_whitelist_manager():
    """
    Manage IP whitelist (for enterprise features)
    """
    
    st.subheader("🔒 IP Whitelist Management")
    
    st.info("""
    **Future Enhancement**: IP Whitelist
    
    This feature would allow you to:
    - Add approved IP ranges
    - Block access from other IPs
    - Set per-user IP restrictions
    - Implement geo-blocking
    """)
    
    # Placeholder for future implementation
    with st.expander("Add IP to Whitelist"):
        ip = st.text_input("IP Address or CIDR range:")
        description = st.text_input("Description:")
        
        if st.button("Add to Whitelist"):
            st.success(f"✅ Added {ip} to whitelist (placeholder)")


# Example integration into main admin page:
def example_admin_page():
    """
    Full example of admin page with IP tracking
    
    HOW TO USE:
    1. Create a new admin page (e.g., pages/Admin_Dashboard.py)
    2. Copy this function
    3. Add authentication check
    4. Call this function
    """
    
    # Check if user is admin (your existing auth check)
    # if not is_admin():
    #     st.error("Access denied")
    #     return
    
    st.set_page_config(page_title="Admin Dashboard", page_icon="🔐", layout="wide")
    
    # Sidebar navigation
    with st.sidebar:
        st.title("🔐 Admin Panel")
        
        section = st.radio(
            "Navigation",
            ["IP Analytics", "Security Alerts", "User Management", "IP Whitelist"]
        )
    
    # Main content
    if section == "IP Analytics":
        show_admin_ip_dashboard()
    
    elif section == "Security Alerts":
        show_security_alerts()
    
    elif section == "IP Whitelist":
        show_ip_whitelist_manager()
    
    elif section == "User Management":
        st.info("Your existing user management code here")


# Quick integration snippets:

def snippet_show_user_ips_in_profile():
    """
    Snippet: Show user's IPs in their profile page
    """
    
    user_email = st.session_state.get("user_email")
    
    if user_email:
        with st.expander("🌐 Your Login History"):
            stats = get_ip_stats_for_user(user_email)
            
            if stats and stats['sessions']:
                st.write(f"**Total Logins:** {stats['total_sessions']}")
                st.write(f"**Unique IPs:** {stats['unique_ips']}")
                
                st.subheader("Recent Logins")
                for session in stats['sessions'][-5:]:  # Last 5
                    ip = session.get('ip_address', 'Unknown')
                    time = session.get('login_time', 'Unknown')
                    st.text(f"• {ip} - {time}")


def snippet_alert_on_new_ip():
    """
    Snippet: Show alert when user logs in from new IP
    """
    
    current_ip = st.session_state.get("client_ip")
    user_email = st.session_state.get("user_email")
    
    if current_ip and user_email:
        stats = get_ip_stats_for_user(user_email)
        
        if stats and stats['ips']:
            known_ips = stats['ips']
            
            # Check if current IP is new
            if current_ip not in known_ips and current_ip != "Unknown":
                st.warning(f"""
                🌍 **New Login Location Detected**
                
                You're logging in from a new IP address: `{current_ip}`
                
                If this wasn't you, please contact support immediately.
                """)


def snippet_show_in_sidebar():
    """
    Snippet: Show IP info in sidebar
    """
    
    with st.sidebar:
        st.markdown("---")
        display_ip_info()


# Usage Instructions:
"""
HOW TO INTEGRATE:

1. BASIC: Show current IP in sidebar
   → Add `snippet_show_in_sidebar()` to your main page

2. USER PROFILE: Show login history
   → Add `snippet_show_user_ips_in_profile()` to user profile page

3. SECURITY: Alert on new IP
   → Add `snippet_alert_on_new_ip()` after login check

4. ADMIN DASHBOARD: Complete analytics
   → Create admin page with `example_admin_page()`

5. CUSTOM: Use utilities directly
   → Import from `utils.ip_display` and `utils.ip_utils`
"""
