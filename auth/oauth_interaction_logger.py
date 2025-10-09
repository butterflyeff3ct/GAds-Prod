"""
OAuth Interaction Logger
Tracks all Google OAuth authentication interactions and errors.
"""

import json
import os
import logging
from datetime import datetime
from typing import Dict, Any, Optional
import streamlit as st

class OAuthInteractionLogger:
    """Logs all OAuth authentication interactions and errors."""
    
    def __init__(self, log_file: str = "logs/oauth_interactions.json"):
        """Initialize the OAuth logger."""
        self.log_file = log_file
        self.ensure_log_directory()
        self.setup_logging()
    
    def ensure_log_directory(self):
        """Ensure the logs directory exists."""
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
    
    def setup_logging(self):
        """Setup file logging for OAuth interactions."""
        # Create logs directory if it doesn't exist
        os.makedirs("logs", exist_ok=True)
        
        # Setup logging configuration
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/oauth_auth.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def log_oauth_attempt(self, user_ip: str = None, user_agent: str = None) -> str:
        """Log an OAuth authentication attempt."""
        interaction_id = f"oauth_attempt_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        log_entry = {
            "interaction_id": interaction_id,
            "timestamp": datetime.now().isoformat(),
            "event_type": "oauth_attempt",
            "user_ip": user_ip or "unknown",
            "user_agent": user_agent or "unknown",
            "status": "initiated",
            "errors": [],
            "success": False
        }
        
        self._write_log_entry(log_entry)
        self.logger.info(f"OAuth attempt initiated: {interaction_id}")
        
        return interaction_id
    
    def log_oauth_config_check(self, interaction_id: str, config_status: Dict[str, Any]):
        """Log OAuth configuration check results."""
        log_entry = {
            "interaction_id": interaction_id,
            "timestamp": datetime.now().isoformat(),
            "event_type": "config_check",
            "config_status": config_status,
            "has_client_id": config_status.get("client_id_present", False),
            "has_client_secret": config_status.get("client_secret_present", False),
            "has_redirect_uri": config_status.get("redirect_uri_present", False),
            "is_configured": config_status.get("is_configured", False)
        }
        
        self._write_log_entry(log_entry)
        
        if not config_status.get("is_configured", False):
            error_msg = "OAuth not configured properly"
            self.logger.warning(f"OAuth config issue: {error_msg}")
            self.log_oauth_error(interaction_id, "config_error", error_msg, config_status)
    
    def log_oauth_url_generation(self, interaction_id: str, auth_url: str = None, success: bool = False):
        """Log OAuth URL generation attempt."""
        log_entry = {
            "interaction_id": interaction_id,
            "timestamp": datetime.now().isoformat(),
            "event_type": "url_generation",
            "success": success,
            "auth_url_generated": auth_url is not None,
            "auth_url_length": len(auth_url) if auth_url else 0
        }
        
        self._write_log_entry(log_entry)
        
        if success:
            self.logger.info(f"OAuth URL generated successfully: {interaction_id}")
        else:
            error_msg = "Failed to generate OAuth authorization URL"
            self.logger.error(f"OAuth URL generation failed: {error_msg}")
            self.log_oauth_error(interaction_id, "url_generation_error", error_msg)
    
    def log_oauth_callback(self, interaction_id: str, callback_data: Dict[str, Any]):
        """Log OAuth callback received."""
        log_entry = {
            "interaction_id": interaction_id,
            "timestamp": datetime.now().isoformat(),
            "event_type": "callback_received",
            "has_code": "code" in callback_data,
            "has_error": "error" in callback_data,
            "callback_params": list(callback_data.keys()),
            "error_code": callback_data.get("error"),
            "error_description": callback_data.get("error_description")
        }
        
        self._write_log_entry(log_entry)
        
        if "error" in callback_data:
            error_msg = f"OAuth callback error: {callback_data.get('error')} - {callback_data.get('error_description', '')}"
            self.logger.error(f"OAuth callback error: {error_msg}")
            self.log_oauth_error(interaction_id, "callback_error", error_msg, callback_data)
        else:
            self.logger.info(f"OAuth callback received successfully: {interaction_id}")
    
    def log_token_exchange(self, interaction_id: str, success: bool = False, user_info: Dict[str, Any] = None, error: str = None):
        """Log token exchange attempt."""
        log_entry = {
            "interaction_id": interaction_id,
            "timestamp": datetime.now().isoformat(),
            "event_type": "token_exchange",
            "success": success,
            "user_email": user_info.get("email") if user_info else None,
            "user_name": user_info.get("name") if user_info else None,
            "google_id": user_info.get("google_id") if user_info else None
        }
        
        self._write_log_entry(log_entry)
        
        if success:
            self.logger.info(f"Token exchange successful for user: {user_info.get('email', 'unknown')}")
        else:
            error_msg = f"Token exchange failed: {error or 'Unknown error'}"
            self.logger.error(f"Token exchange error: {error_msg}")
            self.log_oauth_error(interaction_id, "token_exchange_error", error_msg)
    
    def log_session_creation(self, interaction_id: str, user_email: str, success: bool = False, error: str = None):
        """Log session creation attempt."""
        log_entry = {
            "interaction_id": interaction_id,
            "timestamp": datetime.now().isoformat(),
            "event_type": "session_creation",
            "user_email": user_email,
            "success": success,
            "error": error
        }
        
        self._write_log_entry(log_entry)
        
        if success:
            self.logger.info(f"Session created successfully for user: {user_email}")
        else:
            error_msg = f"Session creation failed: {error or 'Unknown error'}"
            self.logger.error(f"Session creation error: {error_msg}")
            self.log_oauth_error(interaction_id, "session_creation_error", error_msg)
    
    def log_oauth_success(self, interaction_id: str, user_email: str, user_name: str):
        """Log successful OAuth authentication."""
        log_entry = {
            "interaction_id": interaction_id,
            "timestamp": datetime.now().isoformat(),
            "event_type": "oauth_success",
            "user_email": user_email,
            "user_name": user_name,
            "success": True
        }
        
        self._write_log_entry(log_entry)
        self.logger.info(f"OAuth authentication successful for user: {user_email}")
    
    def log_oauth_error(self, interaction_id: str, error_type: str, error_message: str, additional_data: Dict[str, Any] = None):
        """Log OAuth authentication errors."""
        log_entry = {
            "interaction_id": interaction_id,
            "timestamp": datetime.now().isoformat(),
            "event_type": "oauth_error",
            "error_type": error_type,
            "error_message": error_message,
            "additional_data": additional_data or {},
            "success": False
        }
        
        self._write_log_entry(log_entry)
        self.logger.error(f"OAuth error [{error_type}]: {error_message}")
    
    def log_oauth_timeout(self, interaction_id: str, timeout_duration: int = 30):
        """Log OAuth authentication timeout."""
        log_entry = {
            "interaction_id": interaction_id,
            "timestamp": datetime.now().isoformat(),
            "event_type": "oauth_timeout",
            "timeout_duration": timeout_duration,
            "success": False
        }
        
        self._write_log_entry(log_entry)
        self.logger.warning(f"OAuth authentication timeout after {timeout_duration}s: {interaction_id}")
    
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
            
            # Keep only last 1000 entries to prevent file from growing too large
            if len(logs) > 1000:
                logs = logs[-1000:]
            
            with open(self.log_file, 'w') as f:
                json.dump(logs, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Failed to write log entry: {e}")
    
    def get_oauth_logs(self, limit: int = 50) -> list:
        """Get recent OAuth logs."""
        try:
            if os.path.exists(self.log_file):
                with open(self.log_file, 'r') as f:
                    logs = json.load(f)
                return logs[-limit:] if logs else []
            return []
        except Exception as e:
            self.logger.error(f"Failed to read OAuth logs: {e}")
            return []
    
    def get_oauth_errors(self, limit: int = 20) -> list:
        """Get recent OAuth errors."""
        logs = self.get_oauth_logs(limit * 2)  # Get more logs to filter
        return [log for log in logs if log.get("event_type") == "oauth_error"][-limit:]
    
    def get_oauth_success_rate(self, hours: int = 24) -> Dict[str, Any]:
        """Calculate OAuth success rate for the last N hours."""
        logs = self.get_oauth_logs(1000)
        
        # Filter logs from last N hours
        cutoff_time = datetime.now().timestamp() - (hours * 3600)
        recent_logs = [
            log for log in logs 
            if datetime.fromisoformat(log["timestamp"]).timestamp() > cutoff_time
        ]
        
        if not recent_logs:
            return {"success_rate": 0, "total_attempts": 0, "successful": 0, "failed": 0}
        
        # Count attempts and successes
        attempts = [log for log in recent_logs if log.get("event_type") == "oauth_attempt"]
        successes = [log for log in recent_logs if log.get("event_type") == "oauth_success"]
        
        total_attempts = len(attempts)
        successful = len(successes)
        failed = total_attempts - successful
        
        success_rate = (successful / total_attempts * 100) if total_attempts > 0 else 0
        
        return {
            "success_rate": round(success_rate, 2),
            "total_attempts": total_attempts,
            "successful": successful,
            "failed": failed,
            "time_period_hours": hours
        }

# Global logger instance
oauth_logger = OAuthInteractionLogger()

# Convenience functions
def log_oauth_attempt(**kwargs) -> str:
    """Log OAuth attempt and return interaction ID."""
    return oauth_logger.log_oauth_attempt(**kwargs)

def log_oauth_config_check(interaction_id: str, config_status: Dict[str, Any]):
    """Log OAuth configuration check."""
    oauth_logger.log_oauth_config_check(interaction_id, config_status)

def log_oauth_url_generation(interaction_id: str, auth_url: str = None, success: bool = False):
    """Log OAuth URL generation."""
    oauth_logger.log_oauth_url_generation(interaction_id, auth_url, success)

def log_oauth_callback(interaction_id: str, callback_data: Dict[str, Any]):
    """Log OAuth callback."""
    oauth_logger.log_oauth_callback(interaction_id, callback_data)

def log_token_exchange(interaction_id: str, success: bool = False, user_info: Dict[str, Any] = None, error: str = None):
    """Log token exchange."""
    oauth_logger.log_token_exchange(interaction_id, success, user_info, error)

def log_session_creation(interaction_id: str, user_email: str, success: bool = False, error: str = None):
    """Log session creation."""
    oauth_logger.log_session_creation(interaction_id, user_email, success, error)

def log_oauth_success(interaction_id: str, user_email: str, user_name: str):
    """Log OAuth success."""
    oauth_logger.log_oauth_success(interaction_id, user_email, user_name)

def log_oauth_error(interaction_id: str, error_type: str, error_message: str, additional_data: Dict[str, Any] = None):
    """Log OAuth error."""
    oauth_logger.log_oauth_error(interaction_id, error_type, error_message, additional_data)

def log_oauth_timeout(interaction_id: str, timeout_duration: int = 30):
    """Log OAuth timeout."""
    oauth_logger.log_oauth_timeout(interaction_id, timeout_duration)
