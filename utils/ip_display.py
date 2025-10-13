"""IP Address Display Utilities for Admin Dashboard"""
import streamlit as st
from typing import Optional, List, Dict
import re


def display_ip_info():
    """Display current session's IP information in sidebar or admin panel"""
    ip = st.session_state.get("client_ip", "Not captured")
    user_agent = st.session_state.get("user_agent", "Not captured")
    
    with st.expander("🌐 Session Info", expanded=False):
        st.text(f"IP Address: {ip}")
        st.caption(f"User Agent: {user_agent[:50]}..." if len(user_agent) > 50 else f"User Agent: {user_agent}")


def format_ip_column(ip: str) -> str:
    """Format IP for display in tables"""
    if not ip or ip == "Unknown":
        return "🔒 Unknown"
    
    # Anonymize last octet for privacy
    if re.match(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", ip):
        parts = ip.split(".")
        return f"{parts[0]}.{parts[1]}.{parts[2]}.***"
    
    return ip


def get_unique_ips_from_sessions(sessions: List[Dict]) -> List[str]:
    """
    Extract unique IP addresses from session data
    
    Args:
        sessions: List of session dictionaries with 'ip_address' field
        
    Returns:
        List of unique IP addresses
    """
    ips = set()
    for session in sessions:
        ip = session.get("ip_address", "")
        if ip and ip != "Unknown":
            ips.add(ip)
    
    return sorted(list(ips))


def detect_suspicious_logins(sessions: List[Dict], threshold: int = 3) -> Dict[str, List[Dict]]:
    """
    Detect potential suspicious activity based on IP patterns
    
    Args:
        sessions: List of session dictionaries
        threshold: Number of different IPs that triggers alert
        
    Returns:
        Dictionary with 'suspicious' flag and details
    """
    unique_ips = get_unique_ips_from_sessions(sessions)
    
    result = {
        "is_suspicious": len(unique_ips) >= threshold,
        "unique_ip_count": len(unique_ips),
        "unique_ips": unique_ips,
        "threshold": threshold
    }
    
    return result


def show_ip_analytics(sessions: List[Dict]):
    """
    Display IP analytics in admin dashboard
    
    Args:
        sessions: List of session dictionaries
    """
    if not sessions:
        st.info("No session data available")
        return
    
    unique_ips = get_unique_ips_from_sessions(sessions)
    suspicious = detect_suspicious_logins(sessions)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Sessions", len(sessions))
    
    with col2:
        st.metric("Unique IPs", len(unique_ips))
    
    with col3:
        status = "⚠️ Review" if suspicious["is_suspicious"] else "✅ Normal"
        st.metric("Security Status", status)
    
    if suspicious["is_suspicious"]:
        st.warning(f"""
        **Suspicious Activity Detected**
        
        This user has logged in from {len(unique_ips)} different IP addresses,
        which exceeds the threshold of {suspicious['threshold']}.
        
        This could indicate:
        - Account sharing
        - VPN/proxy usage
        - Legitimate travel/multiple locations
        - Potential security concern
        """)
    
    # Show recent IPs
    st.subheader("Recent Login IPs")
    for i, session in enumerate(sessions[-5:][::-1]):  # Last 5 sessions, reversed
        ip = session.get("ip_address", "Unknown")
        login_time = session.get("login_time", "Unknown")
        status = session.get("status", "unknown")
        
        status_emoji = "🟢" if status == "active" else "⚪"
        st.text(f"{status_emoji} {format_ip_column(ip)} - {login_time}")


def get_ip_stats_for_user(email: str) -> Optional[Dict]:
    """
    Get IP statistics for a specific user (requires GSheet access)
    
    Args:
        email: User's email address
        
    Returns:
        Dictionary with IP statistics or None
    """
    try:
        from utils.gsheet_writer import GSheetLogger
        
        logger = GSheetLogger(show_warnings=False)
        if not logger.enabled:
            return None
        
        sessions = logger.get_user_sessions(email, limit=50)
        unique_ips = get_unique_ips_from_sessions(sessions)
        
        return {
            "total_sessions": len(sessions),
            "unique_ips": len(unique_ips),
            "ips": unique_ips,
            "sessions": sessions
        }
        
    except Exception:
        return None
