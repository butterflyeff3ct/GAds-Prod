# auth/quota_manager.py
"""
Quota Management System
Tracks and enforces API usage limits per user and globally.
"""

import streamlit as st
from datetime import datetime, timedelta
from typing import Dict, Optional
import yaml
from collections import defaultdict

class QuotaManager:
    """Manages API quotas and rate limiting."""
    
    def __init__(self, config_path: str = None):
        # Use local config for development, production config for deployment
        if config_path is None:
            import os
            if os.path.exists("config/oauth_config_local.yaml"):
                config_path = "config/oauth_config_local.yaml"
            else:
                config_path = "config/oauth_config.yaml"
        """Initialize quota manager with limits from config."""
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                self.quota_limits = config.get('quota_limits', {})
        except:
            # Default limits if config not found
            self.quota_limits = {
                'google_ads_api': 10,
                'gemini_api': 20,
                'keyword_planner': 15,
                'max_concurrent_users': 10,
                'max_hourly_logins': 50,
                'simulations_per_hour': 5,
                'campaigns_per_day': 10
            }
        
        # Initialize usage tracking in session state
        if 'api_usage' not in st.session_state:
            st.session_state['api_usage'] = {}
        
        if 'hourly_reset_time' not in st.session_state:
            st.session_state['hourly_reset_time'] = datetime.now() + timedelta(hours=1)
    
    def check_quota(self, user_email: str, api_name: str) -> tuple[bool, str]:
        """
        Check if user has quota remaining for an API.
        
        Args:
            user_email: User's email
            api_name: API identifier (google_ads_api, gemini_api, etc.)
            
        Returns:
            (has_quota: bool, message: str)
        """
        # Check if hourly period has reset
        if datetime.now() >= st.session_state['hourly_reset_time']:
            self._reset_hourly_quotas()
        
        # Get user's current usage
        user_usage = st.session_state['api_usage'].get(user_email, {})
        current_usage = user_usage.get(api_name, 0)
        limit = self.quota_limits.get(api_name, 10)
        
        if current_usage >= limit:
            reset_in = self._get_time_until_reset()
            return False, f"Quota exceeded for {api_name}. Limit: {limit}/hour. Resets in {reset_in} minutes."
        
        remaining = limit - current_usage
        return True, f"{remaining}/{limit} remaining"
    
    def increment_usage(self, user_email: str, api_name: str, amount: int = 1):
        """
        Increment API usage counter for user.
        
        Args:
            user_email: User's email
            api_name: API identifier
            amount: Number of calls to increment
        """
        if user_email not in st.session_state['api_usage']:
            st.session_state['api_usage'][user_email] = {}
        
        current = st.session_state['api_usage'][user_email].get(api_name, 0)
        st.session_state['api_usage'][user_email][api_name] = current + amount
    
    def get_user_quota_status(self, user_email: str) -> Dict:
        """
        Get complete quota status for a user.
        
        Returns:
            Dictionary with usage and limits for all APIs
        """
        user_usage = st.session_state['api_usage'].get(user_email, {})
        
        status = {}
        for api_name, limit in self.quota_limits.items():
            if api_name.startswith('max_'):  # Skip global limits
                continue
            
            usage = user_usage.get(api_name, 0)
            percentage = (usage / limit * 100) if limit > 0 else 0
            
            status[api_name] = {
                'usage': usage,
                'limit': limit,
                'remaining': limit - usage,
                'percentage': round(percentage, 1),
                'status': 'ok' if usage < limit * 0.8 else 'warning' if usage < limit else 'exceeded'
            }
        
        status['reset_in_minutes'] = self._get_time_until_reset()
        
        return status
    
    def check_global_limit(self, limit_type: str) -> tuple[bool, str]:
        """
        Check global limits (e.g., concurrent users, hourly logins).
        
        Args:
            limit_type: Type of global limit to check
            
        Returns:
            (allowed: bool, message: str)
        """
        if limit_type == 'concurrent_users':
            # Count active sessions
            active_users = len(st.session_state.get('api_usage', {}))
            limit = self.quota_limits.get('max_concurrent_users', 10)
            
            if active_users >= limit:
                return False, f"Maximum concurrent users ({limit}) reached. Please try again later."
            
            return True, f"{active_users}/{limit} users active"
        
        return True, "OK"
    
    def _reset_hourly_quotas(self):
        """Reset all hourly quotas."""
        st.session_state['api_usage'] = {}
        st.session_state['hourly_reset_time'] = datetime.now() + timedelta(hours=1)
    
    def _get_time_until_reset(self) -> int:
        """Get minutes until hourly quota reset."""
        reset_time = st.session_state.get('hourly_reset_time', datetime.now())
        remaining = reset_time - datetime.now()
        return max(0, int(remaining.total_seconds() / 60))
    
    def get_quota_display_data(self, user_email: str) -> Dict:
        """
        Get formatted quota data for UI display.
        
        Returns:
            Dictionary with formatted strings for UI
        """
        status = self.get_user_quota_status(user_email)
        
        display_data = {
            'quotas': [],
            'reset_time': status.get('reset_in_minutes', 0),
            'overall_status': 'healthy'
        }
        
        for api_name, api_status in status.items():
            if api_name == 'reset_in_minutes':
                continue
            
            # Format API name
            display_name = api_name.replace('_', ' ').title()
            
            display_data['quotas'].append({
                'name': display_name,
                'usage': api_status['usage'],
                'limit': api_status['limit'],
                'percentage': api_status['percentage'],
                'status': api_status['status'],
                'remaining': api_status['remaining']
            })
            
            # Update overall status
            if api_status['status'] == 'exceeded':
                display_data['overall_status'] = 'critical'
            elif api_status['status'] == 'warning' and display_data['overall_status'] == 'healthy':
                display_data['overall_status'] = 'warning'
        
        return display_data
