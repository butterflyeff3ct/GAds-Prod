"""Helper functions for session tracking and metrics collection"""

import streamlit as st
from typing import Optional
from .gsheet_writer import SessionTracker


def get_auth_manager():
    """Get the current authentication manager"""
    try:
        from core.auth import GoogleAuthManager
        return GoogleAuthManager()
    except Exception:
        return None


def track_api_call(operation_name: str, tokens_used: int = 0):
    """Track an API call or operation"""
    auth = get_auth_manager()
    if auth:
        auth.increment_operations(1)
        if tokens_used > 0:
            auth.increment_tokens(tokens_used)
        
        # Optional: Log the operation name for debugging
        if hasattr(st, 'session_state') and 'operations_log' not in st.session_state:
            st.session_state.operations_log = []
        
        if 'operations_log' in st.session_state:
            st.session_state.operations_log.append({
                'operation': operation_name,
                'tokens': tokens_used,
                'timestamp': st.session_state.get('session_tracker', {}).get('start_time')
            })


def track_gemini_call(tokens_used: int):
    """Track a Gemini AI API call"""
    track_api_call("gemini_call", tokens_used)


def track_google_ads_call():
    """Track a Google Ads API call"""
    track_api_call("google_ads_call", 0)  # Google Ads API doesn't use tokens


def track_campaign_creation():
    """Track campaign creation operation"""
    track_api_call("campaign_creation", 0)


def track_simulation_run():
    """Track simulation run operation"""
    track_api_call("simulation_run", 0)


def get_session_summary() -> dict:
    """Get current session summary"""
    auth = get_auth_manager()
    if not auth:
        return {}
    
    session_tracker = auth.get_session_tracker()
    if not session_tracker:
        return {}
    
    session_data = session_tracker.get_session_data()
    operations_log = st.session_state.get('operations_log', [])
    
    return {
        'session_id': session_data.get('session_id'),
        'tokens_used': session_data.get('tokens_used', 0),
        'operations_count': session_data.get('operations', 0),
        'duration_ms': session_data.get('duration_ms', 0),
        'operations_breakdown': operations_log
    }


def show_session_stats():
    """Display session statistics in the sidebar"""
    summary = get_session_summary()
    if not summary:
        return
    
    with st.sidebar:
        st.markdown("---")
        st.markdown("### 📊 Session Stats")
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Tokens Used", summary.get('tokens_used', 0))
        with col2:
            st.metric("Operations", summary.get('operations_count', 0))
        
        duration_minutes = summary.get('duration_ms', 0) / (1000 * 60)
        st.metric("Session Duration", f"{duration_minutes:.1f} min")
        
        # Show operations breakdown if available
        operations_log = summary.get('operations_breakdown', [])
        if operations_log:
            with st.expander("🔍 Operations Breakdown"):
                for op in operations_log[-5:]:  # Show last 5 operations
                    st.caption(f"{op['operation']}: {op['tokens']} tokens")


# Decorator for automatic operation tracking
def track_operation(operation_name: str, tokens_used: int = 0):
    """Decorator to automatically track operations"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Track the operation before execution
            track_api_call(operation_name, tokens_used)
            
            # Execute the function
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                # Track error if needed
                track_api_call(f"{operation_name}_error", 0)
                raise e
        
        return wrapper
    return decorator

