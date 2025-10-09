# /monitor/gemini_monitor.py
"""
Gemini AI Real-Time Token Usage Monitor
Tracks live token consumption and API calls
"""

import streamlit as st
from datetime import datetime
from typing import Dict, Optional
from .usage_logger import get_usage_logger

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

class GeminiMonitor:
    """Real-time monitoring for Gemini AI token usage"""
    
    def __init__(self):
        self.logger = get_usage_logger()
        self.api_key = self._get_api_key()
        self.model = None
        
        if GEMINI_AVAILABLE and self.api_key:
            try:
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel("gemini-2.0-flash-exp")
            except Exception as e:
                st.warning(f"⚠️ Could not initialize Gemini API: {e}")
    
    def _get_api_key(self) -> Optional[str]:
        """Get Gemini API key from secrets"""
        try:
            return st.secrets.get("gemini", {}).get("api_key")
        except:
            return None
    
    def extract_token_usage(self, response) -> Dict:
        """Extract token usage from Gemini API response"""
        if not hasattr(response, 'usage_metadata') or not response.usage_metadata:
            return {
                "input_tokens": 0,
                "output_tokens": 0,
                "total_tokens": 0
            }
        
        metadata = response.usage_metadata
        
        return {
            "input_tokens": getattr(metadata, 'prompt_token_count', 0),
            "output_tokens": getattr(metadata, 'candidates_token_count', 0),
            "total_tokens": getattr(metadata, 'total_token_count', 0)
        }
    
    def get_usage_from_logs(self) -> Dict:
        """Get usage data from our local logs"""
        try:
            # Get last hour usage
            hourly_usage = self.logger.get_usage_last_hour("Gemini")
            
            # Get today's usage
            daily_usage = self.logger.get_usage_today("Gemini")
            
            return {
                "hourly_tokens": hourly_usage["total_tokens"],
                "daily_tokens": daily_usage["total_tokens"],
                "hourly_calls": hourly_usage["total_requests"],
                "daily_calls": daily_usage["total_requests"],
                "avg_response_time_ms": hourly_usage["avg_response_time_ms"]
            }
            
        except Exception as e:
            return {
                "hourly_tokens": 0,
                "daily_tokens": 0,
                "hourly_calls": 0,
                "daily_calls": 0,
                "avg_response_time_ms": 0,
                "error": str(e)
            }
    
    def get_quota_status(self) -> Dict:
        """Get current quota status (if available)"""
        # Note: Gemini API doesn't expose quota info directly
        # We'll estimate based on our usage logs
        try:
            daily_usage = self.logger.get_usage_today("Gemini")
            
            # Estimate quotas (these are typical Gemini quotas)
            estimated_daily_quota = 5000  # tokens per day
            estimated_hourly_quota = 1500  # tokens per hour
            
            daily_usage_count = daily_usage["total_tokens"]
            hourly_usage_count = daily_usage["total_tokens"]  # Simplified for demo
            
            return {
                "daily_quota": estimated_daily_quota,
                "hourly_quota": estimated_hourly_quota,
                "daily_used": daily_usage_count,
                "hourly_used": hourly_usage_count,
                "daily_percent": (daily_usage_count / estimated_daily_quota) * 100,
                "hourly_percent": (hourly_usage_count / estimated_hourly_quota) * 100,
                "quota_source": "estimated"
            }
            
        except Exception as e:
            return {
                "daily_quota": 5000,
                "hourly_quota": 1500,
                "daily_used": 0,
                "hourly_used": 0,
                "daily_percent": 0,
                "hourly_percent": 0,
                "quota_source": "estimated",
                "error": str(e)
            }
    
    def get_comprehensive_usage(self) -> Dict:
        """Get comprehensive Gemini usage data"""
        # Get logged usage
        logged_data = self.get_usage_from_logs()
        
        # Get quota status
        quota_data = self.get_quota_status()
        
        # Combine data
        result = {
            "tokens_last_hour": logged_data.get("hourly_tokens", 0),
            "tokens_today": logged_data.get("daily_tokens", 0),
            "calls_last_hour": logged_data.get("hourly_calls", 0),
            "calls_today": logged_data.get("daily_calls", 0),
            "avg_response_time_ms": logged_data.get("avg_response_time_ms", 0),
            "api_available": self.model is not None,
            "last_updated": datetime.now().isoformat()
        }
        
        # Add quota information
        result.update(quota_data)
        
        # Add error info if any
        if logged_data.get("error"):
            result["logging_error"] = logged_data["error"]
        if quota_data.get("error"):
            result["quota_error"] = quota_data["error"]
        
        return result
    
    def log_generation(self, operation_type: str, tokens_used: int, response_time_ms: int, success: bool = True, error_message: str = None):
        """Log a Gemini API generation call"""
        self.logger.log_api_call(
            api_name="Gemini",
            operation_type=operation_type,
            tokens_used=tokens_used,
            calls_count=1,
            response_time_ms=response_time_ms,
            success=success,
            error_message=error_message,
            metadata={
                "service": "generativeai.googleapis.com",
                "model": "gemini-2.0-flash-exp",
                "operation": operation_type
            }
        )
    
    def test_connection(self) -> Dict:
        """Test Gemini API connection and log the test"""
        if not self.model:
            return {"success": False, "error": "Gemini API not configured"}
        
        try:
            start_time = datetime.now()
            
            # Simple test prompt
            test_prompt = "Hello, this is a test. Please respond with 'API test successful'."
            response = self.model.generate_content(test_prompt)
            
            end_time = datetime.now()
            response_time = (end_time - start_time).total_seconds() * 1000
            
            # Extract token usage
            token_usage = self.extract_token_usage(response)
            
            # Log the test call
            self.log_generation(
                operation_type="connection_test",
                tokens_used=token_usage["total_tokens"],
                response_time_ms=int(response_time),
                success=True
            )
            
            return {
                "success": True,
                "response_time_ms": int(response_time),
                "tokens_used": token_usage["total_tokens"],
                "test_response": response.text[:100] if response.text else "No response text"
            }
            
        except Exception as e:
            # Log the failed test
            self.log_generation(
                operation_type="connection_test",
                tokens_used=0,
                response_time_ms=0,
                success=False,
                error_message=str(e)
            )
            
            return {"success": False, "error": str(e)}

# Global monitor instance
_monitor_instance = None

def get_gemini_monitor() -> GeminiMonitor:
    """Get the global Gemini monitor instance"""
    global _monitor_instance
    if _monitor_instance is None:
        _monitor_instance = GeminiMonitor()
    return _monitor_instance

# Convenience functions
def get_gemini_usage() -> Dict:
    """Get comprehensive Gemini usage data"""
    monitor = get_gemini_monitor()
    return monitor.get_comprehensive_usage()

def log_gemini_generation(operation_type: str, tokens_used: int, response_time_ms: int, success: bool = True, error_message: str = None):
    """Log a Gemini generation call"""
    monitor = get_gemini_monitor()
    monitor.log_generation(operation_type, tokens_used, response_time_ms, success, error_message)

def test_gemini_connection() -> Dict:
    """Test Gemini API connection"""
    monitor = get_gemini_monitor()
    return monitor.test_connection()
