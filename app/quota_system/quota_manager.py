"""
Quota Management System
Tracks and enforces usage limits for Gemini tokens and Google Ads operations

Features:
- Real-time quota tracking
- Batched Google Sheets synchronization (prevents rate limit errors)
- Automatic fallback to mock data
- User-specific quota management
"""

import streamlit as st
from typing import Dict, Tuple, Optional
from datetime import datetime
import time


class QuotaManager:
    """Manages user quotas for API usage"""
    
    # Default quota limits
    DEFAULT_GEMINI_TOKEN_LIMIT = 7000
    DEFAULT_GOOGLE_ADS_OP_LIMIT = 10
    
    # Sync thresholds - only sync to sheets at these intervals
    GEMINI_SYNC_THRESHOLD = 500  # Sync every 500 tokens
    GOOGLE_ADS_SYNC_THRESHOLD = 1  # Sync every operation (low frequency)
    
    def __init__(self):
        """Initialize quota manager"""
        self.initialize_session_state()
        self.gsheet_logger = self._get_gsheet_logger()
        
        # User context tracking
        self.current_user_id = None
        self.current_session_id = None
        self.current_user_email = None
    
    def _get_gsheet_logger(self):
        """Get Google Sheets logger instance"""
        try:
            from utils.gsheet_writer import GSheetLogger
            return GSheetLogger(show_warnings=False)
        except Exception:
            return None
    
    def initialize_session_state(self):
        """Initialize quota tracking in session state"""
        if 'quota_gemini_tokens' not in st.session_state:
            st.session_state.quota_gemini_tokens = 0
        
        if 'quota_google_ads_ops' not in st.session_state:
            st.session_state.quota_google_ads_ops = 0
        
        if 'quota_limits' not in st.session_state:
            st.session_state.quota_limits = {
                'gemini_tokens': self.DEFAULT_GEMINI_TOKEN_LIMIT,
                'google_ads_ops': self.DEFAULT_GOOGLE_ADS_OP_LIMIT
            }
        
        if 'quota_last_reset' not in st.session_state:
            st.session_state.quota_last_reset = datetime.now().isoformat()
        
        # Track last synced values to sheets
        if 'quota_last_synced_gemini' not in st.session_state:
            st.session_state.quota_last_synced_gemini = 0
        
        if 'quota_last_synced_ads' not in st.session_state:
            st.session_state.quota_last_synced_ads = 0
        
        # User context initialization
        if 'quota_user_id' not in st.session_state:
            st.session_state.quota_user_id = None
        if 'quota_user_email' not in st.session_state:
            st.session_state.quota_user_email = None
        if 'quota_session_id' not in st.session_state:
            st.session_state.quota_session_id = None
    
    # ============================================
    # USER CONTEXT MANAGEMENT
    # ============================================
    
    def set_user_context(self, user_id: str, email: str, session_id: str):
        """Set current user context for quota tracking"""
        self.current_user_id = user_id
        self.current_user_email = email
        self.current_session_id = session_id
        
        # Update session state with user context
        st.session_state['quota_user_id'] = user_id
        st.session_state['quota_user_email'] = email
        st.session_state['quota_session_id'] = session_id
    
    def get_user_context(self) -> Dict[str, str]:
        """Get current user context"""
        return {
            'user_id': self.current_user_id or st.session_state.get('quota_user_id'),
            'email': self.current_user_email or st.session_state.get('quota_user_email'),
            'session_id': self.current_session_id or st.session_state.get('quota_session_id')
        }
    
    def _log_gemini_usage_to_user_tracking(self, user_id: str, session_id: str, 
                                          tokens_used: int, operation_type: str):
        """Log individual Gemini API usage to user tracking"""
        try:
            if self.gsheet_logger and self.gsheet_logger.enabled:
                self.gsheet_logger.log_gemini_usage(
                    user_id=user_id,
                    session_id=session_id,
                    tokens_used=tokens_used,
                    operation_type=operation_type
                )
        except Exception as e:
            # Silently fail - don't disrupt user experience
            print(f"Failed to log Gemini usage to user tracking: {e}")
    
    # ============================================
    # QUOTA TRACKING
    # ============================================
    
    def get_gemini_usage(self) -> Tuple[int, int]:
        """
        Get Gemini token usage
        
        Returns:
            Tuple of (used, limit)
        """
        used = st.session_state.get('quota_gemini_tokens', 0)
        limit = st.session_state.get('quota_limits', {}).get('gemini_tokens', self.DEFAULT_GEMINI_TOKEN_LIMIT)
        return (used, limit)
    
    def get_google_ads_usage(self) -> Tuple[int, int]:
        """
        Get Google Ads operation usage
        
        Returns:
            Tuple of (used, limit)
        """
        used = st.session_state.get('quota_google_ads_ops', 0)
        limit = st.session_state.get('quota_limits', {}).get('google_ads_ops', self.DEFAULT_GOOGLE_ADS_OP_LIMIT)
        return (used, limit)
    
    def increment_gemini_tokens(self, count: int, operation_type: str = "gemini_api_call") -> bool:
        """
        Increment Gemini token usage with user context logging
        
        Args:
            count: Number of tokens to add
            operation_type: Type of operation (e.g., "keyword_generation", "ad_generation")
            
        Returns:
            True if within quota, False if quota exceeded
        """
        current = st.session_state.quota_gemini_tokens
        limit = st.session_state.quota_limits['gemini_tokens']
        
        # Update usage
        st.session_state.quota_gemini_tokens = current + count
        
        # NEW: Log to user-specific tracking
        user_context = self.get_user_context()
        if user_context['user_id']:
            self._log_gemini_usage_to_user_tracking(
                user_id=user_context['user_id'],
                session_id=user_context['session_id'],
                tokens_used=count,
                operation_type=operation_type
            )
        
        # BATCHED SYNC: Only sync to sheets at threshold intervals
        last_synced = st.session_state.quota_last_synced_gemini
        new_value = st.session_state.quota_gemini_tokens
        
        # Sync if we've crossed a threshold OR if quota exceeded
        if (new_value - last_synced >= self.GEMINI_SYNC_THRESHOLD) or (new_value >= limit):
            self._sync_to_sheets('gemini_tokens', new_value)
            st.session_state.quota_last_synced_gemini = new_value
        
        # Check if exceeded
        return st.session_state.quota_gemini_tokens <= limit
    
    def increment_google_ads_ops(self, count: int = 1) -> bool:
        """
        Increment Google Ads operation usage
        
        Args:
            count: Number of operations to add
            
        Returns:
            True if within quota, False if quota exceeded
        """
        current = st.session_state.quota_google_ads_ops
        limit = st.session_state.quota_limits['google_ads_ops']
        
        # Update usage
        st.session_state.quota_google_ads_ops = current + count
        
        # BATCHED SYNC: Only sync at threshold
        last_synced = st.session_state.quota_last_synced_ads
        new_value = st.session_state.quota_google_ads_ops
        
        # Sync if threshold reached OR quota exceeded
        if (new_value - last_synced >= self.GOOGLE_ADS_SYNC_THRESHOLD) or (new_value >= limit):
            self._sync_to_sheets('google_ads_ops', new_value)
            st.session_state.quota_last_synced_ads = new_value
        
        # Check if exceeded
        return st.session_state.quota_google_ads_ops <= limit
    
    # ============================================
    # QUOTA CHECKS
    # ============================================
    
    def can_use_gemini(self) -> bool:
        """Check if Gemini API can be used (within quota)"""
        used, limit = self.get_gemini_usage()
        return used < limit
    
    def can_use_google_ads(self) -> bool:
        """Check if Google Ads API can be used (within quota)"""
        used, limit = self.get_google_ads_usage()
        return used < limit
    
    def get_gemini_remaining(self) -> int:
        """Get remaining Gemini tokens"""
        used, limit = self.get_gemini_usage()
        return max(0, limit - used)
    
    def get_google_ads_remaining(self) -> int:
        """Get remaining Google Ads operations"""
        used, limit = self.get_google_ads_usage()
        return max(0, limit - used)
    
    # ============================================
    # GOOGLE SHEETS SYNC (BATCHED)
    # ============================================
    
    def _sync_to_sheets(self, quota_type: str, value: int):
        """
        Sync quota usage to Google Sheets (BATCHED - reduces API calls)
        
        Args:
            quota_type: 'gemini_tokens' or 'google_ads_ops'
            value: Current usage value
        """
        try:
            # Skip if sheets not available
            if not self.gsheet_logger or not self.gsheet_logger.enabled:
                return
            
            user_email = st.session_state.get('user_email')
            session_id = st.session_state.get('session_id')
            
            # Skip if no user info
            if not user_email or not session_id:
                return
            
            # Log quota update (with built-in rate limiting)
            self.gsheet_logger.log_quota_update(
                email=user_email,
                session_id=session_id,
                quota_type=quota_type,
                used=value,
                timestamp=datetime.now().isoformat()
            )
        except Exception as e:
            # Silently fail - don't disrupt user experience
            # Just log to console
            print(f"Quota sync to sheets failed (non-critical): {e}")
    
    def sync_all_quotas(self):
        """Sync all quota values to Google Sheets (called at session end)"""
        try:
            self._sync_to_sheets('gemini_tokens', st.session_state.quota_gemini_tokens)
            self._sync_to_sheets('google_ads_ops', st.session_state.quota_google_ads_ops)
        except Exception:
            pass  # Non-critical failure
    
    def load_quotas_from_sheets(self, user_email: str) -> bool:
        """
        Load user's quota usage from Google Sheets
        
        Args:
            user_email: User's email address
            
        Returns:
            True if loaded successfully
        """
        try:
            if self.gsheet_logger and self.gsheet_logger.enabled:
                quota_data = self.gsheet_logger.get_user_quotas(user_email)
                
                if quota_data:
                    st.session_state.quota_gemini_tokens = quota_data.get('gemini_tokens', 0)
                    st.session_state.quota_google_ads_ops = quota_data.get('google_ads_ops', 0)
                    
                    # Update sync trackers
                    st.session_state.quota_last_synced_gemini = quota_data.get('gemini_tokens', 0)
                    st.session_state.quota_last_synced_ads = quota_data.get('google_ads_ops', 0)
                    return True
        except Exception as e:
            print(f"Failed to load quotas from sheets: {e}")
        
        return False
    
    # ============================================
    # QUOTA RESET
    # ============================================
    
    def reset_quotas(self):
        """Reset all quotas to zero (admin only)"""
        st.session_state.quota_gemini_tokens = 0
        st.session_state.quota_google_ads_ops = 0
        st.session_state.quota_last_reset = datetime.now().isoformat()
        
        # Reset sync trackers
        st.session_state.quota_last_synced_gemini = 0
        st.session_state.quota_last_synced_ads = 0
        
        # Sync to sheets
        self.sync_all_quotas()
    
    def reset_user_quotas(self, user_email: str):
        """Reset quotas for specific user (admin only)"""
        if self.gsheet_logger and self.gsheet_logger.enabled:
            self.gsheet_logger.reset_user_quotas(user_email)
    
    # ============================================
    # QUOTA DISPLAY
    # ============================================
    
    def get_quota_summary(self) -> Dict:
        """
        Get summary of all quota usage
        
        Returns:
            Dictionary with quota information
        """
        gemini_used, gemini_limit = self.get_gemini_usage()
        ads_used, ads_limit = self.get_google_ads_usage()
        
        return {
            'gemini': {
                'used': gemini_used,
                'limit': gemini_limit,
                'remaining': max(0, gemini_limit - gemini_used),
                'percentage': (gemini_used / gemini_limit * 100) if gemini_limit > 0 else 0,
                'exceeded': gemini_used >= gemini_limit
            },
            'google_ads': {
                'used': ads_used,
                'limit': ads_limit,
                'remaining': max(0, ads_limit - ads_used),
                'percentage': (ads_used / ads_limit * 100) if ads_limit > 0 else 0,
                'exceeded': ads_used >= ads_limit
            }
        }


# ============================================
# GLOBAL INSTANCE
# ============================================

_quota_manager = None

def get_quota_manager() -> QuotaManager:
    """Get quota manager singleton"""
    global _quota_manager
    if _quota_manager is None:
        _quota_manager = QuotaManager()
    return _quota_manager
