# /monitor/google_ads_monitor.py
"""
Google Ads API Real-Time Operations Monitor
Tracks live request counts and quota usage
"""

import streamlit as st
import time
from datetime import datetime, timedelta
from typing import Dict, Optional
from .usage_logger import get_usage_logger

try:
    from google.cloud import monitoring_v3
    from google.protobuf.timestamp_pb2 import Timestamp
    MONITORING_AVAILABLE = True
except ImportError:
    MONITORING_AVAILABLE = False

class GoogleAdsMonitor:
    """Real-time monitoring for Google Ads API operations"""
    
    def __init__(self, project_id: str = None):
        self.project_id = project_id or self._get_project_id()
        self.monitoring_client = None
        self.logger = get_usage_logger()
        
        if MONITORING_AVAILABLE and self.project_id:
            try:
                self.monitoring_client = monitoring_v3.MetricServiceClient()
            except Exception as e:
                st.warning(f"⚠️ Could not initialize Google Cloud Monitoring: {e}")
    
    def _get_project_id(self) -> Optional[str]:
        """Get GCP project ID from environment or secrets"""
        import os
        
        # Try from environment
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
        if project_id:
            return project_id
        
        # Try from Streamlit secrets
        try:
            project_id = st.secrets.get("gcp", {}).get("project_id")
            if project_id:
                return project_id
        except:
            pass
        
        # Try from Google Ads config
        try:
            project_id = st.secrets.get("google_ads", {}).get("project_id")
            if project_id:
                return project_id
        except:
            pass
        
        return None
    
    def get_live_usage_from_monitoring(self) -> Dict:
        """Get live usage data from Google Cloud Monitoring API"""
        if not self.monitoring_client or not self.project_id:
            return {"total_requests": 0, "error": "Monitoring not available"}
        
        try:
            project_name = f"projects/{self.project_id}"
            metric_type = "serviceruntime.googleapis.com/api/request_count"
            
            # Create time interval for last hour
            interval = monitoring_v3.TimeInterval()
            now = Timestamp()
            now.GetCurrentTime()
            interval.end_time = now
            interval.start_time.seconds = int(time.time() - 3600)  # last 1 hour
            
            # Query for Google Ads API requests
            results = self.monitoring_client.list_time_series(
                request={
                    "name": project_name,
                    "filter": f'metric.type="{metric_type}" AND resource.label."service"="googleads.googleapis.com"',
                    "interval": interval,
                    "view": monitoring_v3.ListTimeSeriesRequest.TimeSeriesView.FULL,
                }
            )
            
            total_requests = 0
            for time_series in results:
                for point in time_series.points:
                    if point.value.int64_value:
                        total_requests += int(point.value.int64_value)
            
            return {"total_requests": total_requests, "error": None}
            
        except Exception as e:
            return {"total_requests": 0, "error": str(e)}
    
    def get_usage_from_logs(self) -> Dict:
        """Get usage data from our local logs"""
        try:
            # Get last hour usage
            hourly_usage = self.logger.get_usage_last_hour("Google Ads")
            
            # Get today's usage
            daily_usage = self.logger.get_usage_today("Google Ads")
            
            return {
                "hourly_operations": hourly_usage["total_operations"],
                "daily_operations": daily_usage["total_operations"],
                "hourly_requests": hourly_usage["total_requests"],
                "daily_requests": daily_usage["total_requests"],
                "avg_response_time_ms": hourly_usage["avg_response_time_ms"]
            }
            
        except Exception as e:
            return {
                "hourly_operations": 0,
                "daily_operations": 0,
                "hourly_requests": 0,
                "daily_requests": 0,
                "avg_response_time_ms": 0,
                "error": str(e)
            }
    
    def get_comprehensive_usage(self) -> Dict:
        """Get comprehensive usage data combining live monitoring and logs"""
        # Get live monitoring data
        live_data = self.get_live_usage_from_monitoring()
        
        # Get logged data
        logged_data = self.get_usage_from_logs()
        
        # Combine data
        result = {
            "live_requests_last_hour": live_data.get("total_requests", 0),
            "logged_requests_last_hour": logged_data.get("hourly_requests", 0),
            "logged_operations_last_hour": logged_data.get("hourly_operations", 0),
            "logged_requests_today": logged_data.get("daily_requests", 0),
            "logged_operations_today": logged_data.get("daily_operations", 0),
            "avg_response_time_ms": logged_data.get("avg_response_time_ms", 0),
            "monitoring_available": self.monitoring_client is not None,
            "last_updated": datetime.now().isoformat()
        }
        
        # Add error info if any
        if live_data.get("error"):
            result["monitoring_error"] = live_data["error"]
        if logged_data.get("error"):
            result["logging_error"] = logged_data["error"]
        
        return result
    
    def log_operation(self, operation_type: str, response_time_ms: int, success: bool = True, error_message: str = None):
        """Log a Google Ads API operation"""
        self.logger.log_api_call(
            api_name="Google Ads",
            operation_type=operation_type,
            operations_count=1,
            response_time_ms=response_time_ms,
            success=success,
            error_message=error_message,
            metadata={
                "service": "googleads.googleapis.com",
                "operation": operation_type
            }
        )

# Global monitor instance
_monitor_instance = None

def get_google_ads_monitor() -> GoogleAdsMonitor:
    """Get the global Google Ads monitor instance"""
    global _monitor_instance
    if _monitor_instance is None:
        _monitor_instance = GoogleAdsMonitor()
    return _monitor_instance

# Convenience functions
def get_google_ads_usage() -> Dict:
    """Get comprehensive Google Ads usage data"""
    monitor = get_google_ads_monitor()
    return monitor.get_comprehensive_usage()

def log_google_ads_operation(operation_type: str, response_time_ms: int, success: bool = True, error_message: str = None):
    """Log a Google Ads operation"""
    monitor = get_google_ads_monitor()
    monitor.log_operation(operation_type, response_time_ms, success, error_message)
