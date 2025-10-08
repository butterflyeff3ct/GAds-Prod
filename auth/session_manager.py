# auth/session_manager.py
"""
Session Management
Handles user sessions, authentication state, and session persistence.
"""

import streamlit as st
from datetime import datetime, timedelta
from typing import Optional, Dict
import hashlib
import secrets

class SessionManager:
    """Manages user sessions and authentication state."""
    
    SESSION_TIMEOUT_MINUTES = 120  # 2 hours
    
    @staticmethod
    def create_session(user_info: Dict) -> str:
        """
        Create a new session for authenticated user.
        
        Args:
            user_info: User profile from Google OAuth
            
        Returns:
            Session ID
        """
        # Generate session ID
        session_id = secrets.token_urlsafe(32)
        
        # Store session data
        session_data = {
            'session_id': session_id,
            'user_email': user_info['email'],
            'user_name': user_info['name'],
            'user_picture': user_info.get('picture'),
            'google_id': user_info['google_id'],
            'created_at': datetime.now().isoformat(),
            'last_activity': datetime.now().isoformat(),
            'expires_at': (datetime.now() + timedelta(minutes=SessionManager.SESSION_TIMEOUT_MINUTES)).isoformat()
        }
        
        # Store in Streamlit session state
        st.session_state['user_session'] = session_data
        st.session_state['user_email'] = user_info['email']
        st.session_state['user_name'] = user_info['name']
        st.session_state['is_authenticated'] = True
        
        return session_id
    
    @staticmethod
    def get_current_session() -> Optional[Dict]:
        """Get current session data if valid."""
        session = st.session_state.get('user_session')
        
        if not session:
            return None
        
        # Check if session expired
        try:
            expires_at = datetime.fromisoformat(session['expires_at'])
            if datetime.now() > expires_at:
                # Session expired
                SessionManager.end_session()
                return None
        except:
            return None
        
        return session
    
    @staticmethod
    def update_activity():
        """Update last activity timestamp for current session."""
        session = st.session_state.get('user_session')
        if session:
            session['last_activity'] = datetime.now().isoformat()
            # Extend expiry
            session['expires_at'] = (datetime.now() + timedelta(minutes=SessionManager.SESSION_TIMEOUT_MINUTES)).isoformat()
            st.session_state['user_session'] = session
    
    @staticmethod
    def is_authenticated() -> bool:
        """Check if user is authenticated with valid session."""
        session = SessionManager.get_current_session()
        return session is not None and st.session_state.get('is_authenticated', False)
    
    @staticmethod
    def get_user_email() -> Optional[str]:
        """Get current user's email."""
        session = SessionManager.get_current_session()
        return session['user_email'] if session else None
    
    @staticmethod
    def get_user_name() -> Optional[str]:
        """Get current user's name."""
        session = SessionManager.get_current_session()
        return session['user_name'] if session else None
    
    @staticmethod
    def end_session():
        """End current session and clear authentication state."""
        keys_to_clear = [
            'user_session',
            'user_email',
            'user_name',
            'is_authenticated',
            'oauth_credentials',
            'oauth_state'
        ]
        
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
    
    @staticmethod
    def get_session_time_remaining() -> int:
        """Get minutes remaining in current session."""
        session = SessionManager.get_current_session()
        if not session:
            return 0
        
        try:
            expires_at = datetime.fromisoformat(session['expires_at'])
            remaining = expires_at - datetime.now()
            return max(0, int(remaining.total_seconds() / 60))
        except:
            return 0
