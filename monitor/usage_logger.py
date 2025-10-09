# /monitor/usage_logger.py
"""
API Usage Logger for Historical Tracking
Logs API calls to JSON and SQLite for trend analysis
"""

import json
import os
import sqlite3
import streamlit as st
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path

class UsageLogger:
    """Handles logging and retrieval of API usage data"""
    
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        self.json_log_file = self.log_dir / "api_usage_log.json"
        self.sqlite_db = self.log_dir / "api_usage.db"
        
        # Initialize SQLite database
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database for structured logging"""
        try:
            with sqlite3.connect(self.sqlite_db) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS api_usage (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        api_name TEXT NOT NULL,
                        operation_type TEXT,
                        tokens_used INTEGER DEFAULT 0,
                        operations_count INTEGER DEFAULT 0,
                        calls_count INTEGER DEFAULT 0,
                        response_time_ms INTEGER DEFAULT 0,
                        success BOOLEAN DEFAULT 1,
                        error_message TEXT,
                        metadata TEXT
                    )
                """)
                
                # Create indexes for faster queries
                conn.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON api_usage(timestamp)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_api_name ON api_usage(api_name)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_operation_type ON api_usage(operation_type)")
                
        except Exception as e:
            st.warning(f"⚠️ Could not initialize SQLite database: {e}")
    
    def log_api_call(self, 
                    api_name: str,
                    operation_type: str = "unknown",
                    tokens_used: int = 0,
                    operations_count: int = 0,
                    calls_count: int = 0,
                    response_time_ms: int = 0,
                    success: bool = True,
                    error_message: str = None,
                    metadata: Dict = None):
        """Log an API call to both JSON and SQLite"""
        
        timestamp = datetime.utcnow().isoformat()
        
        # JSON logging (append mode)
        try:
            log_entry = {
                "timestamp": timestamp,
                "api": api_name,
                "operation_type": operation_type,
                "tokens": tokens_used,
                "operations": operations_count,
                "calls": calls_count,
                "response_time_ms": response_time_ms,
                "success": success,
                "error_message": error_message,
                "metadata": metadata or {}
            }
            
            with open(self.json_log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry) + "\n")
                
        except Exception as e:
            st.warning(f"⚠️ Could not write to JSON log: {e}")
        
        # SQLite logging
        try:
            with sqlite3.connect(self.sqlite_db) as conn:
                conn.execute("""
                    INSERT INTO api_usage 
                    (timestamp, api_name, operation_type, tokens_used, operations_count, 
                     calls_count, response_time_ms, success, error_message, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    timestamp, api_name, operation_type, tokens_used, operations_count,
                    calls_count, response_time_ms, success, error_message, 
                    json.dumps(metadata) if metadata else None
                ))
                
        except Exception as e:
            st.warning(f"⚠️ Could not write to SQLite database: {e}")
    
    def get_usage_today(self, api_name: str = None) -> Dict:
        """Get usage statistics for today"""
        today = datetime.now().date().isoformat()
        
        try:
            with sqlite3.connect(self.sqlite_db) as conn:
                query = """
                    SELECT 
                        SUM(tokens_used) as total_tokens,
                        SUM(operations_count) as total_operations,
                        SUM(calls_count) as total_calls,
                        COUNT(*) as total_requests,
                        AVG(response_time_ms) as avg_response_time
                    FROM api_usage 
                    WHERE DATE(timestamp) = ? AND success = 1
                """
                params = [today]
                
                if api_name:
                    query += " AND api_name = ?"
                    params.append(api_name)
                
                result = conn.execute(query, params).fetchone()
                
                return {
                    "total_tokens": result[0] or 0,
                    "total_operations": result[1] or 0,
                    "total_calls": result[2] or 0,
                    "total_requests": result[3] or 0,
                    "avg_response_time_ms": result[4] or 0
                }
                
        except Exception as e:
            st.warning(f"⚠️ Could not query usage data: {e}")
            return {"total_tokens": 0, "total_operations": 0, "total_calls": 0, "total_requests": 0, "avg_response_time_ms": 0}
    
    def get_usage_last_hour(self, api_name: str = None) -> Dict:
        """Get usage statistics for the last hour"""
        one_hour_ago = (datetime.now() - timedelta(hours=1)).isoformat()
        
        try:
            with sqlite3.connect(self.sqlite_db) as conn:
                query = """
                    SELECT 
                        SUM(tokens_used) as total_tokens,
                        SUM(operations_count) as total_operations,
                        SUM(calls_count) as total_calls,
                        COUNT(*) as total_requests,
                        AVG(response_time_ms) as avg_response_time
                    FROM api_usage 
                    WHERE timestamp >= ? AND success = 1
                """
                params = [one_hour_ago]
                
                if api_name:
                    query += " AND api_name = ?"
                    params.append(api_name)
                
                result = conn.execute(query, params).fetchone()
                
                return {
                    "total_tokens": result[0] or 0,
                    "total_operations": result[1] or 0,
                    "total_calls": result[2] or 0,
                    "total_requests": result[3] or 0,
                    "avg_response_time_ms": result[4] or 0
                }
                
        except Exception as e:
            st.warning(f"⚠️ Could not query usage data: {e}")
            return {"total_tokens": 0, "total_operations": 0, "total_calls": 0, "total_requests": 0, "avg_response_time_ms": 0}
    
    def get_historical_trends(self, api_name: str = None, days: int = 7) -> List[Dict]:
        """Get historical usage trends for the last N days"""
        start_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        try:
            with sqlite3.connect(self.sqlite_db) as conn:
                query = """
                    SELECT 
                        DATE(timestamp) as date,
                        SUM(tokens_used) as total_tokens,
                        SUM(operations_count) as total_operations,
                        SUM(calls_count) as total_calls,
                        COUNT(*) as total_requests
                    FROM api_usage 
                    WHERE timestamp >= ? AND success = 1
                """
                params = [start_date]
                
                if api_name:
                    query += " AND api_name = ?"
                    params.append(api_name)
                
                query += " GROUP BY DATE(timestamp) ORDER BY date"
                
                results = conn.execute(query, params).fetchall()
                
                return [
                    {
                        "date": row[0],
                        "total_tokens": row[1] or 0,
                        "total_operations": row[2] or 0,
                        "total_calls": row[3] or 0,
                        "total_requests": row[4] or 0
                    }
                    for row in results
                ]
                
        except Exception as e:
            st.warning(f"⚠️ Could not query historical trends: {e}")
            return []
    
    def get_api_health_stats(self) -> Dict:
        """Get API health statistics (success rates, error counts)"""
        try:
            with sqlite3.connect(self.sqlite_db) as conn:
                # Success rates by API
                success_rates = conn.execute("""
                    SELECT 
                        api_name,
                        COUNT(*) as total_calls,
                        SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful_calls,
                        AVG(response_time_ms) as avg_response_time
                    FROM api_usage 
                    WHERE timestamp >= datetime('now', '-24 hours')
                    GROUP BY api_name
                """).fetchall()
                
                # Recent errors
                recent_errors = conn.execute("""
                    SELECT api_name, error_message, timestamp
                    FROM api_usage 
                    WHERE success = 0 AND timestamp >= datetime('now', '-1 hour')
                    ORDER BY timestamp DESC
                    LIMIT 10
                """).fetchall()
                
                return {
                    "success_rates": {
                        row[0]: {
                            "total_calls": row[1],
                            "successful_calls": row[2],
                            "success_rate": (row[2] / row[1] * 100) if row[1] > 0 else 0,
                            "avg_response_time_ms": row[3] or 0
                        }
                        for row in success_rates
                    },
                    "recent_errors": [
                        {"api": row[0], "error": row[1], "timestamp": row[2]}
                        for row in recent_errors
                    ]
                }
                
        except Exception as e:
            st.warning(f"⚠️ Could not query health stats: {e}")
            return {"success_rates": {}, "recent_errors": []}

# Global logger instance
_logger_instance = None

def get_usage_logger() -> UsageLogger:
    """Get the global usage logger instance"""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = UsageLogger()
    return _logger_instance

# Convenience functions
def log_api_call(api_name: str, **kwargs):
    """Log an API call using the global logger"""
    logger = get_usage_logger()
    logger.log_api_call(api_name, **kwargs)

def get_today_usage(api_name: str = None) -> Dict:
    """Get today's usage statistics"""
    logger = get_usage_logger()
    return logger.get_usage_today(api_name)

def get_hourly_usage(api_name: str = None) -> Dict:
    """Get last hour's usage statistics"""
    logger = get_usage_logger()
    return logger.get_usage_last_hour(api_name)
