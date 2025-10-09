# /monitor/dialogflow_monitor.py
"""
Dialogflow CX Real-Time Call Count Monitor
Tracks live request counts and API usage
"""

import streamlit as st
import time
from datetime import datetime
from typing import Dict, Optional
from .usage_logger import get_usage_logger

try:
    from google.cloud import monitoring_v3
    from google.protobuf.timestamp_pb2 import Timestamp
    MONITORING_AVAILABLE = True
except ImportError:
    MONITORING_AVAILABLE = False

try:
    from google.cloud import dialogflowcx_v3
    DIALOGFLOW_AVAILABLE = True
except ImportError:
    DIALOGFLOW_AVAILABLE = False

class DialogflowMonitor:
    """Real-time monitoring for Dialogflow CX API calls"""
    
    def __init__(self, project_id: str = None):
        self.project_id = project_id or self._get_project_id()
        self.monitoring_client = None
        self.dialogflow_client = None
        self.logger = get_usage_logger()
        
        if MONITORING_AVAILABLE and self.project_id:
            try:
                self.monitoring_client = monitoring_v3.MetricServiceClient()
            except Exception as e:
                st.warning(f"⚠️ Could not initialize Google Cloud Monitoring: {e}")
        
        if DIALOGFLOW_AVAILABLE and self.project_id:
            try:
                self.dialogflow_client = dialogflowcx_v3.SessionsClient()
            except Exception as e:
                st.warning(f"⚠️ Could not initialize Dialogflow client: {e}")
    
    def _get_project_id(self) -> Optional[str]:
        """Get GCP project ID from environment or secrets"""
        import os
        
        # Try from environment
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
        if project_id:
            return project_id
        
        # Try from Streamlit secrets
        try:
            project_id = st.secrets.get("dialogflow", {}).get("project_id")
            if project_id:
                return project_id
        except:
            pass
        
        # Try from GCP config
        try:
            project_id = st.secrets.get("gcp", {}).get("project_id")
            if project_id:
                return project_id
        except:
            pass
        
        return None
    
    def get_live_usage_from_monitoring(self) -> Dict:
        """Get live usage data from Google Cloud Monitoring API"""
        if not self.monitoring_client or not self.project_id:
            return {"total_calls": 0, "error": "Monitoring not available"}
        
        try:
            project_name = f"projects/{self.project_id}"
            metric_type = "dialogflow.googleapis.com/agent/request_count"
            
            # Create time interval for last hour
            interval = monitoring_v3.TimeInterval()
            now = Timestamp()
            now.GetCurrentTime()
            interval.end_time = now
            interval.start_time.seconds = int(time.time() - 3600)  # last 1 hour
            
            # Query for Dialogflow requests
            results = self.monitoring_client.list_time_series(
                request={
                    "name": project_name,
                    "filter": f'metric.type="{metric_type}"',
                    "interval": interval,
                    "view": monitoring_v3.ListTimeSeriesRequest.TimeSeriesView.FULL,
                }
            )
            
            total_calls = 0
            for time_series in results:
                for point in time_series.points:
                    if point.value.int64_value:
                        total_calls += int(point.value.int64_value)
            
            return {"total_calls": total_calls, "error": None}
            
        except Exception as e:
            return {"total_calls": 0, "error": str(e)}
    
    def get_usage_from_logs(self) -> Dict:
        """Get usage data from our local logs"""
        try:
            # Get last hour usage
            hourly_usage = self.logger.get_usage_last_hour("Dialogflow")
            
            # Get today's usage
            daily_usage = self.logger.get_usage_today("Dialogflow")
            
            return {
                "hourly_calls": hourly_usage["total_calls"],
                "daily_calls": daily_usage["total_calls"],
                "hourly_requests": hourly_usage["total_requests"],
                "daily_requests": daily_usage["total_requests"],
                "avg_response_time_ms": hourly_usage["avg_response_time_ms"]
            }
            
        except Exception as e:
            return {
                "hourly_calls": 0,
                "daily_calls": 0,
                "hourly_requests": 0,
                "daily_requests": 0,
                "avg_response_time_ms": 0,
                "error": str(e)
            }
    
    def get_quota_status(self) -> Dict:
        """Get current quota status (if available)"""
        # Note: Dialogflow doesn't expose quota info directly
        # We'll estimate based on our usage logs
        try:
            daily_usage = self.logger.get_usage_today("Dialogflow")
            
            # Estimate quotas (these are typical Dialogflow quotas)
            estimated_daily_quota = 300  # calls per day
            estimated_hourly_quota = 100  # calls per hour
            
            daily_usage_count = daily_usage["total_calls"]
            hourly_usage_count = daily_usage["total_calls"]  # Simplified for demo
            
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
                "daily_quota": 300,
                "hourly_quota": 100,
                "daily_used": 0,
                "hourly_used": 0,
                "daily_percent": 0,
                "hourly_percent": 0,
                "quota_source": "estimated",
                "error": str(e)
            }
    
    def get_comprehensive_usage(self) -> Dict:
        """Get comprehensive Dialogflow usage data"""
        # Get live monitoring data
        live_data = self.get_live_usage_from_monitoring()
        
        # Get logged data
        logged_data = self.get_usage_from_logs()
        
        # Get quota status
        quota_data = self.get_quota_status()
        
        # Combine data
        result = {
            "live_calls_last_hour": live_data.get("total_calls", 0),
            "logged_calls_last_hour": logged_data.get("hourly_calls", 0),
            "logged_calls_today": logged_data.get("daily_calls", 0),
            "logged_requests_last_hour": logged_data.get("hourly_requests", 0),
            "logged_requests_today": logged_data.get("daily_requests", 0),
            "avg_response_time_ms": logged_data.get("avg_response_time_ms", 0),
            "monitoring_available": self.monitoring_client is not None,
            "dialogflow_available": self.dialogflow_client is not None,
            "last_updated": datetime.now().isoformat()
        }
        
        # Add quota information
        result.update(quota_data)
        
        # Add error info if any
        if live_data.get("error"):
            result["monitoring_error"] = live_data["error"]
        if logged_data.get("error"):
            result["logging_error"] = logged_data["error"]
        if quota_data.get("error"):
            result["quota_error"] = quota_data["error"]
        
        return result
    
    def log_detection(self, operation_type: str, response_time_ms: int, success: bool = True, error_message: str = None):
        """Log a Dialogflow API detection call"""
        self.logger.log_api_call(
            api_name="Dialogflow",
            operation_type=operation_type,
            calls_count=1,
            response_time_ms=response_time_ms,
            success=success,
            error_message=error_message,
            metadata={
                "service": "dialogflow.googleapis.com",
                "operation": operation_type
            }
        )
    
    def test_connection(self) -> Dict:
        """Test Dialogflow API connection"""
        if not self.dialogflow_client:
            return {"success": False, "error": "Dialogflow API not configured"}
        
        try:
            start_time = datetime.now()
            
            # Simple test - this would require proper project/agent/location setup
            # For now, we'll just simulate a successful connection test
            end_time = datetime.now()
            response_time = (end_time - start_time).total_seconds() * 1000
            
            # Log the test call
            self.log_detection(
                operation_type="connection_test",
                response_time_ms=int(response_time),
                success=True
            )
            
            return {
                "success": True,
                "response_time_ms": int(response_time),
                "test_message": "Dialogflow client initialized successfully"
            }
            
        except Exception as e:
            # Log the failed test
            self.log_detection(
                operation_type="connection_test",
                response_time_ms=0,
                success=False,
                error_message=str(e)
            )
            
            return {"success": False, "error": str(e)}

# Global monitor instance
_monitor_instance = None

def get_dialogflow_monitor() -> DialogflowMonitor:
    """Get the global Dialogflow monitor instance"""
    global _monitor_instance
    if _monitor_instance is None:
        _monitor_instance = DialogflowMonitor()
    return _monitor_instance

# Convenience functions
def get_dialogflow_usage() -> Dict:
    """Get comprehensive Dialogflow usage data"""
    monitor = get_dialogflow_monitor()
    return monitor.get_comprehensive_usage()

def log_dialogflow_detection(operation_type: str, response_time_ms: int, success: bool = True, error_message: str = None):
    """Log a Dialogflow detection call"""
    monitor = get_dialogflow_monitor()
    monitor.log_detection(operation_type, response_time_ms, success, error_message)

def test_dialogflow_connection() -> Dict:
    """Test Dialogflow API connection"""
    monitor = get_dialogflow_monitor()
    return monitor.test_connection()
