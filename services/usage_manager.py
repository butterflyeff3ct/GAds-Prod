# /services/usage_manager.py
"""
Centralized Usage Manager for API Quota Control
Tracks and enforces limits across Gemini, Google Ads, and Dialogflow APIs
"""

import streamlit as st
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
import json
import os

class UsageManager:
    """Centralized usage tracking and quota enforcement"""
    
    # Default limits per service
    DEFAULT_LIMITS = {
        "gemini": {"hourly": 1500, "daily": 5000},
        "google_ads": {"hourly": 300, "daily": 1000},
        "dialogflow": {"hourly": 100, "daily": 300}
    }
    
    # Behavior when limits exceeded
    EXCEED_BEHAVIOR = {
        "gemini": "fallback_to_mock",
        "google_ads": "stop_and_alert",
        "dialogflow": "disable_chatbot"
    }
    
    def __init__(self):
        self.session_key = "api_usage_tracking"
        
    def _get_usage_data(self) -> Dict:
        """Get current usage data from session state"""
        if self.session_key not in st.session_state:
            st.session_state[self.session_key] = {
                "services": {},
                "last_daily_reset": datetime.now().date().isoformat()
            }
        return st.session_state[self.session_key]
    
    def _check_daily_reset(self) -> bool:
        """Check if daily reset is needed and perform it"""
        usage_data = self._get_usage_data()
        current_date = datetime.now().date().isoformat()
        
        if usage_data["last_daily_reset"] != current_date:
            # Reset daily counters
            for service in usage_data["services"]:
                usage_data["services"][service]["daily_tokens"] = 0
            usage_data["last_daily_reset"] = current_date
            
            # Show reset notification
            if any(usage_data["services"].values()):
                st.info("🔄 Daily API token counters have been reset!")
            return True
        return False
    
    def _check_hourly_reset(self) -> bool:
        """Check if hourly reset is needed and perform it"""
        usage_data = self._get_usage_data()
        
        # Check if we need to reset hourly counters
        # Since we removed user tracking, we'll reset hourly counters daily
        current_date = datetime.now().date().isoformat()
        if usage_data["last_daily_reset"] != current_date:
            # Reset hourly counters
            for service in usage_data["services"]:
                usage_data["services"][service]["hourly_tokens"] = 0
            usage_data["last_daily_reset"] = current_date
            return True
        return False
    
    def _initialize_service_data(self, service: str) -> Dict:
        """Initialize tracking data for a service"""
        return {
            "hourly_tokens": 0,
            "daily_tokens": 0,
            "last_used": datetime.now().isoformat(),
            "total_requests": 0
        }
    
    def check_limit(self, service: str) -> Tuple[bool, str]:
        """
        Check if service is within limits
        
        Returns:
            Tuple[bool, str]: (is_within_limit, reason_if_exceeded)
        """
        # Check for resets
        self._check_daily_reset()
        self._check_hourly_reset()
        
        usage_data = self._get_usage_data()
        
        # Initialize service if not exists
        if service not in usage_data["services"]:
            usage_data["services"][service] = self._initialize_service_data(service)
        
        service_data = usage_data["services"][service]
        limits = self.DEFAULT_LIMITS.get(service, {"hourly": 1000, "daily": 3000})
        
        # Check hourly limit
        if service_data["hourly_tokens"] >= limits["hourly"]:
            return False, f"Hourly limit reached ({service_data['hourly_tokens']}/{limits['hourly']})"
        
        # Check daily limit
        if service_data["daily_tokens"] >= limits["daily"]:
            return False, f"Daily limit reached ({service_data['daily_tokens']}/{limits['daily']})"
        
        return True, "Within limits"
    
    def record_usage(self, service: str, tokens_used: int) -> None:
        """Record token usage for a service"""
        usage_data = self._get_usage_data()
        
        # Initialize service if not exists
        if service not in usage_data["services"]:
            usage_data["services"][service] = self._initialize_service_data(service)
        
        service_data = usage_data["services"][service]
        
        # Update counters
        service_data["hourly_tokens"] += tokens_used
        service_data["daily_tokens"] += tokens_used
        service_data["total_requests"] += 1
        service_data["last_used"] = datetime.now().isoformat()
        
        # Update session state
        st.session_state[self.session_key] = usage_data
    
# Session tracking functionality removed
    
# User ID generation removed
    
# Session recording removed
    
    def get_usage_stats(self) -> Dict:
        """Get current usage statistics for all services"""
        usage_data = self._get_usage_data()
        stats = {}
        
        for service in self.DEFAULT_LIMITS.keys():
            service_data = usage_data["services"].get(service, self._initialize_service_data(service))
            limits = self.DEFAULT_LIMITS[service]
            
            stats[service] = {
                "hourly_used": service_data["hourly_tokens"],
                "hourly_limit": limits["hourly"],
                "daily_used": service_data["daily_tokens"],
                "daily_limit": limits["daily"],
                "hourly_percent": (service_data["hourly_tokens"] / limits["hourly"]) * 100,
                "daily_percent": (service_data["daily_tokens"] / limits["daily"]) * 100,
                "total_requests": service_data["total_requests"],
                "last_used": service_data["last_used"],
                "exceed_behavior": self.EXCEED_BEHAVIOR[service]
            }
        
        return stats
    
# Session stats removed
    
    def force_reset(self, service: Optional[str] = None) -> None:
        """Force reset usage data for a service or all services"""
        usage_data = self._get_usage_data()
        
        if service:
            if service in usage_data["services"]:
                usage_data["services"][service] = self._initialize_service_data(service)
        else:
            # Reset all services
            for svc in usage_data["services"]:
                usage_data["services"][svc] = self._initialize_service_data(svc)
        
        st.session_state[self.session_key] = usage_data
        st.success(f"🔄 Usage data reset for {'all services' if not service else service}")

# Global instance
usage_manager = UsageManager()

# Convenience functions
def check_limit(service: str) -> Tuple[bool, str]:
    """Check if service is within limits"""
    return usage_manager.check_limit(service)

def record_usage(service: str, tokens_used: int) -> None:
    """Record token usage for a service"""
    usage_manager.record_usage(service, tokens_used)

# Session tracking convenience functions removed

def get_usage_stats() -> Dict:
    """Get current usage statistics"""
    return usage_manager.get_usage_stats()

# Session stats function removed

def force_reset(service: Optional[str] = None) -> None:
    """Force reset usage data"""
    usage_manager.force_reset(service)
