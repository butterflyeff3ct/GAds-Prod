"""IP Address Utilities for Session Tracking"""
import streamlit as st
from typing import Optional


def get_client_ip() -> str:
    """
    Get the client's IP address from Streamlit headers
    
    Handles cases where app is behind proxies/load balancers
    by checking X-Forwarded-For and X-Real-IP headers first
    
    Returns:
        IP address string or 'Unknown' if unable to determine
    """
    try:
        # Try to get headers from Streamlit context
        from streamlit.web.server.websocket_headers import _get_websocket_headers
        
        headers = _get_websocket_headers()
        
        # Check for IP in common proxy headers (handles load balancers)
        # X-Forwarded-For can contain multiple IPs (client, proxy1, proxy2, ...)
        # We want the leftmost (original client IP)
        if "X-Forwarded-For" in headers:
            forwarded_ips = headers["X-Forwarded-For"].split(",")
            if forwarded_ips:
                return forwarded_ips[0].strip()
        
        # Fallback to X-Real-IP header
        if "X-Real-Ip" in headers:
            return headers["X-Real-Ip"].strip()
        
        # Fallback to Remote-Addr
        if "Remote-Addr" in headers:
            return headers["Remote-Addr"].strip()
        
        # If no headers available, return unknown
        return "Unknown"
        
    except Exception as e:
        # Silently fail and return unknown - IP tracking shouldn't break login
        return "Unknown"


def get_user_agent() -> str:
    """
    Get the user's browser/device information
    
    Returns:
        User agent string or 'Unknown'
    """
    try:
        from streamlit.web.server.websocket_headers import _get_websocket_headers
        
        headers = _get_websocket_headers()
        
        if "User-Agent" in headers:
            return headers["User-Agent"]
        
        return "Unknown"
        
    except Exception:
        return "Unknown"


def format_ip_for_logging(ip: str) -> str:
    """
    Format IP address for logging
    Truncates if too long, handles IPv6
    
    Returns:
        Formatted IP string (max 45 chars for IPv6)
    """
    if not ip or ip == "Unknown":
        return "Unknown"
    
    # IPv6 addresses can be up to 45 characters
    # IPv4 addresses are much shorter
    return ip[:45]


def get_location_from_ip(ip: str) -> Optional[str]:
    """
    Get approximate location from IP address
    Note: This requires external API and is not implemented
    
    For future enhancement - could integrate with ipapi.co or similar
    
    Returns:
        Location string or None
    """
    # Placeholder for future enhancement
    # Could integrate with:
    # - ipapi.co (free tier: 1000 requests/day)
    # - ip-api.com (free tier: 45 requests/minute)
    # - ipgeolocation.io
    return None
