# auth/user_activity.py
"""
User Activity Logger
Tracks all user actions for audit trail and analytics.
"""

import streamlit as st
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import json

class UserActivityLogger:
    """Logs all user activities in the simulator."""
    
    ACTIVITY_TYPES = {
        'login': 'User Login',
        'logout': 'User Logout',
        'campaign_create': 'Campaign Created',
        'campaign_run': 'Simulation Run',
        'api_call': 'API Call Made',
        'keyword_research': 'Keyword Research',
        'report_view': 'Report Viewed',
        'export_data': 'Data Exported'
    }
    
    @staticmethod
    def log_activity(user_email: str, activity_type: str, details: Optional[Dict] = None):
        """
        Log a user activity.
        
        Args:
            user_email: User's email
            activity_type: Type of activity (from ACTIVITY_TYPES)
            details: Additional details about the activity
        """
        activity = {
            'timestamp': datetime.now().isoformat(),
            'user_email': user_email,
            'activity_type': activity_type,
            'activity_name': UserActivityLogger.ACTIVITY_TYPES.get(activity_type, activity_type),
            'details': details or {},
            'session_id': st.session_state.get('user_session', {}).get('session_id', 'unknown')
        }
        
        # Store in session state
        if 'user_activities' not in st.session_state:
            st.session_state['user_activities'] = []
        
        st.session_state['user_activities'].append(activity)
        
        # Keep only last 100 activities in memory
        if len(st.session_state['user_activities']) > 100:
            st.session_state['user_activities'] = st.session_state['user_activities'][-100:]
    
    @staticmethod
    def get_user_activities(user_email: str, limit: int = 50) -> List[Dict]:
        """
        Get recent activities for a user.
        
        Args:
            user_email: User's email
            limit: Maximum number of activities to return
            
        Returns:
            List of activity dictionaries
        """
        all_activities = st.session_state.get('user_activities', [])
        
        # Filter by user
        user_activities = [
            act for act in all_activities 
            if act['user_email'] == user_email
        ]
        
        # Sort by timestamp (most recent first)
        user_activities.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return user_activities[:limit]
    
    @staticmethod
    def get_activity_summary(user_email: str) -> Dict:
        """
        Get activity summary for a user.
        
        Returns:
            Summary statistics
        """
        activities = UserActivityLogger.get_user_activities(user_email, limit=1000)
        
        summary = {
            'total_activities': len(activities),
            'last_activity': activities[0]['timestamp'] if activities else None,
            'activity_breakdown': {}
        }
        
        # Count by type
        for activity in activities:
            act_type = activity['activity_type']
            if act_type not in summary['activity_breakdown']:
                summary['activity_breakdown'][act_type] = 0
            summary['activity_breakdown'][act_type] += 1
        
        return summary
    
    @staticmethod
    def export_activities(user_email: str) -> str:
        """
        Export user activities as JSON string.
        
        Returns:
            JSON string of activities
        """
        activities = UserActivityLogger.get_user_activities(user_email, limit=1000)
        return json.dumps(activities, indent=2)
