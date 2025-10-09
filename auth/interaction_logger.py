"""
Comprehensive Interaction Logger
Logs all user interactions including OAuth, API calls, and general activities.
"""

import json
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import streamlit as st
import traceback

class InteractionLogger:
    """Logs all user interactions and system events."""
    
    def __init__(self, log_file: str = "logs/interactions.json"):
        """Initialize the interaction logger."""
        self.log_file = log_file
        self.ensure_log_directory()
        self.setup_logging()
    
    def ensure_log_directory(self):
        """Ensure the logs directory exists."""
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
    
    def setup_logging(self):
        """Setup file logging for interactions."""
        # Create logs directory if it doesn't exist
        os.makedirs("logs", exist_ok=True)
        
        # Setup logging configuration
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/interactions.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def log_interaction(self, 
                       event_type: str, 
                       user_email: str = None, 
                       success: bool = True, 
                       error_message: str = None,
                       additional_data: Dict[str, Any] = None,
                       interaction_id: str = None) -> str:
        """
        Log a general interaction.
        
        Args:
            event_type: Type of interaction (login, api_call, etc.)
            user_email: User's email (if authenticated)
            success: Whether the interaction was successful
            error_message: Error message if unsuccessful
            additional_data: Additional context data
            interaction_id: Existing interaction ID to link to
            
        Returns:
            Interaction ID for tracking
        """
        if not interaction_id:
            interaction_id = f"interaction_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]}"
        
        # Get user info from session if not provided
        if not user_email and hasattr(st, 'session_state'):
            user_email = st.session_state.get('user_email', 'anonymous')
        
        log_entry = {
            "interaction_id": interaction_id,
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "user_email": user_email or "anonymous",
            "success": success,
            "error_message": error_message,
            "additional_data": additional_data or {},
            "session_id": st.session_state.get('user_session', {}).get('session_id', 'unknown') if hasattr(st, 'session_state') else 'unknown',
            "user_agent": self._get_user_agent(),
            "ip_address": self._get_client_ip()
        }
        
        self._write_log_entry(log_entry)
        
        if success:
            self.logger.info(f"Interaction successful: {event_type} - {user_email or 'anonymous'}")
        else:
            self.logger.error(f"Interaction failed: {event_type} - {error_message or 'Unknown error'}")
        
        return interaction_id
    
    def log_api_call(self, 
                    api_name: str, 
                    endpoint: str = None, 
                    method: str = "GET", 
                    success: bool = True, 
                    response_time_ms: int = None,
                    error_message: str = None,
                    user_email: str = None) -> str:
        """Log API call interactions."""
        additional_data = {
            "api_name": api_name,
            "endpoint": endpoint,
            "method": method,
            "response_time_ms": response_time_ms
        }
        
        return self.log_interaction(
            event_type="api_call",
            user_email=user_email,
            success=success,
            error_message=error_message,
            additional_data=additional_data
        )
    
    def log_simulation_run(self, 
                          campaign_data: Dict[str, Any], 
                          success: bool = True, 
                          error_message: str = None,
                          user_email: str = None) -> str:
        """Log simulation run interactions."""
        additional_data = {
            "campaign_data": campaign_data,
            "keywords_count": len(campaign_data.get('keywords', [])),
            "budget": campaign_data.get('budget'),
            "duration_days": campaign_data.get('duration_days')
        }
        
        return self.log_interaction(
            event_type="simulation_run",
            user_email=user_email,
            success=success,
            error_message=error_message,
            additional_data=additional_data
        )
    
    def log_keyword_research(self, 
                           query: str, 
                           results_count: int = 0, 
                           success: bool = True, 
                           error_message: str = None,
                           user_email: str = None) -> str:
        """Log keyword research interactions."""
        additional_data = {
            "query": query,
            "results_count": results_count
        }
        
        return self.log_interaction(
            event_type="keyword_research",
            user_email=user_email,
            success=success,
            error_message=error_message,
            additional_data=additional_data
        )
    
    def log_page_view(self, 
                     page_name: str, 
                     user_email: str = None) -> str:
        """Log page view interactions."""
        additional_data = {
            "page_name": page_name
        }
        
        return self.log_interaction(
            event_type="page_view",
            user_email=user_email,
            success=True,
            additional_data=additional_data
        )
    
    def log_error(self, 
                 error_type: str, 
                 error_message: str, 
                 stack_trace: str = None,
                 user_email: str = None,
                 additional_data: Dict[str, Any] = None) -> str:
        """Log error interactions."""
        error_data = {
            "error_type": error_type,
            "stack_trace": stack_trace or traceback.format_exc(),
            **(additional_data or {})
        }
        
        return self.log_interaction(
            event_type="error",
            user_email=user_email,
            success=False,
            error_message=error_message,
            additional_data=error_data
        )
    
    def log_security_event(self, 
                          event_type: str, 
                          description: str,
                          severity: str = "medium",
                          user_email: str = None,
                          additional_data: Dict[str, Any] = None) -> str:
        """Log security-related events."""
        security_data = {
            "security_event_type": event_type,
            "severity": severity,
            "description": description,
            **(additional_data or {})
        }
        
        return self.log_interaction(
            event_type="security_event",
            user_email=user_email,
            success=False,  # Security events are typically negative
            error_message=description,
            additional_data=security_data
        )
    
    def _get_user_agent(self) -> str:
        """Get user agent from request headers."""
        try:
            # Try to get user agent from Streamlit session state or headers
            if hasattr(st, 'session_state') and 'user_agent' in st.session_state:
                return st.session_state['user_agent']
            
            # Try to get from request context if available
            import streamlit.web.server.server as server
            if hasattr(server, 'Server'):
                # This is a simplified approach - in production you might want more sophisticated header extraction
                return "streamlit_app"
            
            return "unknown"
        except:
            return "unknown"
    
    def _get_client_ip(self) -> str:
        """Get client IP address."""
        try:
            # Try to get IP from Streamlit session state
            if hasattr(st, 'session_state') and 'client_ip' in st.session_state:
                return st.session_state['client_ip']
            
            # In a real deployment, you'd extract this from request headers
            return "unknown"
        except:
            return "unknown"
    
    def _write_log_entry(self, log_entry: Dict[str, Any]):
        """Write log entry to JSON file."""
        try:
            # Append to JSON log file
            if os.path.exists(self.log_file):
                with open(self.log_file, 'r') as f:
                    logs = json.load(f)
            else:
                logs = []
            
            logs.append(log_entry)
            
            # Keep only last 5000 entries to prevent file from growing too large
            if len(logs) > 5000:
                logs = logs[-5000:]
            
            with open(self.log_file, 'w') as f:
                json.dump(logs, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Failed to write interaction log entry: {e}")
    
    def get_interactions(self, 
                        user_email: str = None, 
                        event_type: str = None, 
                        hours: int = 24, 
                        limit: int = 100) -> List[Dict]:
        """Get recent interactions with optional filtering."""
        try:
            if os.path.exists(self.log_file):
                with open(self.log_file, 'r') as f:
                    logs = json.load(f)
            else:
                return []
            
            # Filter by time
            cutoff_time = datetime.now().timestamp() - (hours * 3600)
            recent_logs = [
                log for log in logs 
                if datetime.fromisoformat(log["timestamp"]).timestamp() > cutoff_time
            ]
            
            # Filter by user email if provided
            if user_email:
                recent_logs = [log for log in recent_logs if log.get("user_email") == user_email]
            
            # Filter by event type if provided
            if event_type:
                recent_logs = [log for log in recent_logs if log.get("event_type") == event_type]
            
            # Sort by timestamp (most recent first)
            recent_logs.sort(key=lambda x: x['timestamp'], reverse=True)
            
            return recent_logs[:limit]
            
        except Exception as e:
            self.logger.error(f"Failed to read interaction logs: {e}")
            return []
    
    def get_error_logs(self, hours: int = 24, limit: int = 50) -> List[Dict]:
        """Get recent error logs."""
        return self.get_interactions(event_type="error", hours=hours, limit=limit)
    
    def get_user_activity_summary(self, user_email: str, hours: int = 24) -> Dict[str, Any]:
        """Get activity summary for a user."""
        interactions = self.get_interactions(user_email=user_email, hours=hours, limit=1000)
        
        if not interactions:
            return {"total_interactions": 0, "activity_breakdown": {}, "success_rate": 0}
        
        # Count by event type
        activity_breakdown = {}
        successful = 0
        
        for interaction in interactions:
            event_type = interaction.get("event_type", "unknown")
            if event_type not in activity_breakdown:
                activity_breakdown[event_type] = 0
            activity_breakdown[event_type] += 1
            
            if interaction.get("success", False):
                successful += 1
        
        total = len(interactions)
        success_rate = (successful / total * 100) if total > 0 else 0
        
        return {
            "total_interactions": total,
            "activity_breakdown": activity_breakdown,
            "success_rate": round(success_rate, 2),
            "successful_interactions": successful,
            "failed_interactions": total - successful
        }
    
    def get_system_health_metrics(self, hours: int = 24) -> Dict[str, Any]:
        """Get system health metrics."""
        interactions = self.get_interactions(hours=hours, limit=5000)
        
        if not interactions:
            return {"total_interactions": 0, "error_rate": 0, "unique_users": 0}
        
        total = len(interactions)
        errors = len([i for i in interactions if not i.get("success", True)])
        unique_users = len(set([i.get("user_email", "unknown") for i in interactions if i.get("user_email")]))
        
        error_rate = (errors / total * 100) if total > 0 else 0
        
        return {
            "total_interactions": total,
            "error_rate": round(error_rate, 2),
            "unique_users": unique_users,
            "errors": errors,
            "time_period_hours": hours
        }

# Global logger instance
interaction_logger = InteractionLogger()

# Convenience functions
def log_interaction(event_type: str, user_email: str = None, success: bool = True, error_message: str = None, additional_data: Dict[str, Any] = None) -> str:
    """Log a general interaction."""
    return interaction_logger.log_interaction(event_type, user_email, success, error_message, additional_data)

def log_api_call(api_name: str, endpoint: str = None, method: str = "GET", success: bool = True, response_time_ms: int = None, error_message: str = None, user_email: str = None) -> str:
    """Log API call interaction."""
    return interaction_logger.log_api_call(api_name, endpoint, method, success, response_time_ms, error_message, user_email)

def log_simulation_run(campaign_data: Dict[str, Any], success: bool = True, error_message: str = None, user_email: str = None) -> str:
    """Log simulation run interaction."""
    return interaction_logger.log_simulation_run(campaign_data, success, error_message, user_email)

def log_keyword_research(query: str, results_count: int = 0, success: bool = True, error_message: str = None, user_email: str = None) -> str:
    """Log keyword research interaction."""
    return interaction_logger.log_keyword_research(query, results_count, success, error_message, user_email)

def log_page_view(page_name: str, user_email: str = None) -> str:
    """Log page view interaction."""
    return interaction_logger.log_page_view(page_name, user_email)

def log_error(error_type: str, error_message: str, stack_trace: str = None, user_email: str = None, additional_data: Dict[str, Any] = None) -> str:
    """Log error interaction."""
    return interaction_logger.log_error(error_type, error_message, stack_trace, user_email, additional_data)

def log_security_event(event_type: str, description: str, severity: str = "medium", user_email: str = None, additional_data: Dict[str, Any] = None) -> str:
    """Log security event."""
    return interaction_logger.log_security_event(event_type, description, severity, user_email, additional_data)
