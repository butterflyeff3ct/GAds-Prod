# /monitor/__init__.py
"""
Real-Time API Usage Monitoring System
Tracks live token/operation/call counts for Gemini, Google Ads, and Dialogflow
"""

__version__ = "1.0.0"
__author__ = "Google Ads Search Campaign Simulator"

# Export main components
from .usage_logger import UsageLogger, get_usage_logger
from .api_usage_dashboard import render_api_usage_dashboard

__all__ = [
    "UsageLogger",
    "get_usage_logger", 
    "render_api_usage_dashboard"
]
