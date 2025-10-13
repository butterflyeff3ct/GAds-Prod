"""Google Sheets Integration - Minimal Logging Version
Only logs initialization status and critical errors.
"""
import gspread
import streamlit as st
import uuid
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Optional, Dict, Any
import time
import os
import random
import logging

# Get logger for Google Sheets operations
logger = logging.getLogger('google_sheets_api')

# Track if we've already logged initialization
_init_logged = False


class GSheetLogger:
    """Handles Google Sheets logging with minimal console output"""
    
    def __init__(self, sheet_id: Optional[str] = None, show_warnings: bool = True):
        """Initialize Google Sheets client"""
        global _init_logged
        
        try:
            self.is_production = self._is_production_environment()
            
            try:
                gsheet_config = st.secrets.get("google_sheets", {})
            except Exception:
                if show_warnings and self.is_production:
                    self._show_config_warning()
                self.enabled = False
                return
                
            self.sheet_id = sheet_id or gsheet_config.get("sheet_id")
            
            if not self.sheet_id:
                if show_warnings and self.is_production:
                    self._show_config_warning()
                self.enabled = False
                return
            
            self._last_request_time = 0
            self._min_request_interval = 2.0
            self._user_cache = {}
            self._cache_ttl = 300
            self._cache_timestamp = 0
            
            scope = [
                "https://spreadsheets.google.com/feeds",
                "https://www.googleapis.com/auth/drive"
            ]
            
            credentials_info = gsheet_config.get("credentials")
            if not credentials_info:
                if show_warnings and self.is_production:
                    self._show_config_warning()
                self.enabled = False
                return
            
            from oauth2client.service_account import ServiceAccountCredentials
            credentials = ServiceAccountCredentials.from_json_keyfile_dict(
                credentials_info, scope
            )
            
            self.client = gspread.authorize(credentials)
            self._init_worksheets()
            self.enabled = True
            
            # Only log once
            if not _init_logged:
                logger.info("✅ Google Sheets API: Connected")
                _init_logged = True
            
        except Exception as e:
            error_msg = str(e)
            
            # Only log critical errors once
            if not _init_logged and ("429" in error_msg or "Quota exceeded" in error_msg):
                logger.error(f"❌ Google Sheets API: Quota exceeded")
                _init_logged = True
            elif not _init_logged:
                logger.error(f"❌ Google Sheets API: Failed")
                _init_logged = True
            
            if show_warnings and self.is_production:
                if "credentials" in error_msg.lower() or "authentication" in error_msg.lower():
                    self._show_config_warning()
            
            self.enabled = False
    
    def _is_production_environment(self) -> bool:
        """Detect if running on Streamlit Cloud"""
        indicators = [
            "streamlit.app" in os.getenv("HOSTNAME", ""),
            os.getenv("STREAMLIT_SHARING_MODE") == "true",
            "/mount/src" in os.getcwd(),
            "streamlit-cloud" in os.getenv("HOME", "").lower(),
            os.path.exists("/mount/src")
        ]
        return any(indicators)
    
    def _show_config_warning(self):
        """Show config warning for production"""
        st.warning("""
        ⚠️ **Google Sheets Logging Not Configured**
        
        To enable user tracking in production:
        1. Go to your Streamlit Cloud dashboard
        2. Click on your app → Settings → Secrets
        3. Add your Google Sheets configuration
        """)
    
    def _rate_limit(self):
        """Enforce rate limiting"""
        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        
        if time_since_last < self._min_request_interval:
            time.sleep(self._min_request_interval - time_since_last)
        
        self._last_request_time = time.time()
    
    def _init_worksheets(self):
        """Initialize worksheets"""
        try:
            self.sheet = self.client.open_by_key(self.sheet_id)
            
            try:
                self.users_worksheet = self.sheet.worksheet("Users")
            except gspread.WorksheetNotFound:
                self._rate_limit()
                self.users_worksheet = self.sheet.add_worksheet(title="Users", rows=1000, cols=7)
                self.users_worksheet.append_row([
                    "Email", "First Name", "Last Name", "First Login", 
                    "Profile Pic", "Locale", "User ID"
                ])
            
            try:
                self.activity_worksheet = self.sheet.worksheet("Activity")
            except gspread.WorksheetNotFound:
                self._rate_limit()
                self.activity_worksheet = self.sheet.add_worksheet(title="Activity", rows=10000, cols=9)
                self.activity_worksheet.append_row([
                    "Email", "Session ID", "Trace ID", "Login Time", 
                    "Logout Time", "Tokens Used", "Operations", "Duration", "Status"
                ])
            
            # NEW: Initialize Quota worksheet
            try:
                self.quota_worksheet = self.sheet.worksheet("Quotas")
            except gspread.WorksheetNotFound:
                self._rate_limit()
                self.quota_worksheet = self.sheet.add_worksheet(title="Quotas", rows=1000, cols=8)
                self.quota_worksheet.append_row([
                    "Email", "Session ID", "Gemini Tokens", "Google Ads Ops",
                    "Last Updated", "Gemini Limit", "Ads Limit", "Status"
                ])
        except Exception as e:
            raise Exception(f"Failed to initialize worksheets: {e}")
        
        # Get or create Gemini Usage worksheet for user-specific tracking
        try:
            self.gemini_usage_worksheet = self.sheet.worksheet("Gemini Usage")
        except gspread.WorksheetNotFound:
            self._rate_limit()
            self.gemini_usage_worksheet = self.sheet.add_worksheet(
                title="Gemini Usage", rows=10000, cols=6
            )
            self.gemini_usage_worksheet.append_row([
                "User ID", "Session ID", "Operation Type", "Tokens Used", "Timestamp", "Status"
            ])
    
    def _get_timestamp(self) -> str:
        """Get current timestamp in EST"""
        try:
            est_tz = ZoneInfo("America/New_York")
            return datetime.now(est_tz).strftime("%Y-%m-%d %H:%M:%S")
        except ImportError:
            from datetime import timezone, timedelta
            est_offset = timedelta(hours=-5)
            return datetime.now(timezone(est_offset)).strftime("%Y-%m-%d %H:%M:%S")
    
    def _format_duration(self, duration_ms: int) -> str:
        """Convert duration from ms to mm:ss"""
        if duration_ms <= 0:
            return "00:00"
        total_seconds = duration_ms // 1000
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        return f"{minutes:02d}:{seconds:02d}"
    
    def _generate_user_id(self) -> str:
        """Generate 6-digit user ID"""
        return str(random.randint(100000, 999999))
    
    def _check_user_exists_cached(self, email: str) -> bool:
        """Check if user exists using cache"""
        current_time = time.time()
        if email in self._user_cache:
            return True
        
        if current_time - self._cache_timestamp > self._cache_ttl:
            try:
                self._rate_limit()
                email_column = self.users_worksheet.col_values(1)
                existing_emails = email_column[1:]
                self._user_cache = {e: True for e in existing_emails}
                self._cache_timestamp = current_time
            except Exception:
                return False
        
        return email in self._user_cache
    
    def store_user_if_new(self, user_data: Dict[str, Any]) -> bool:
        """Store user data if email doesn't exist - NO LOGGING"""
        if not self.enabled:
            return False
        
        try:
            email = user_data["email"]
            
            if self._check_user_exists_cached(email):
                return False
            
            user_id = self._generate_user_id()
            self._rate_limit()
            
            row_data = [
                user_data["email"],
                user_data.get("first_name", ""),
                user_data.get("last_name", ""),
                user_data.get("first_login", self._get_timestamp()),
                user_data.get("picture", ""),
                user_data.get("locale", ""),
                user_id
            ]
            
            self.users_worksheet.append_row(row_data)
            self._user_cache[email] = True
            return True
            
        except Exception as e:
            if "429" in str(e) and self.is_production:
                st.warning("⚠️ Rate limit reached")
            return False
    
    def log_session_start(self, email: str, session_id: str, 
                         trace_id: str = "", login_time: Optional[str] = None) -> bool:
        """Log session start - NO LOGGING"""
        if not self.enabled:
            return False
        
        try:
            if login_time is None:
                login_time = self._get_timestamp()
            
            self._rate_limit()
            
            row_data = [email, session_id, trace_id, login_time, "", "", "", "", "started"]
            self.activity_worksheet.append_row(row_data)
            return True
            
        except Exception:
            return False
    
    def log_session_end(self, email: str, session_id: str, 
                       logout_time: Optional[str] = None,
                       tokens_used: int = 0, operations: int = 0, 
                       duration_ms: int = 0, status: str = "completed") -> bool:
        """Update session end data - NO LOGGING"""
        if not self.enabled:
            return False
        
        try:
            if logout_time is None:
                logout_time = self._get_timestamp()
            
            self._rate_limit()
            all_rows = self.activity_worksheet.get_all_values()
            
            for i, row in enumerate(all_rows):
                if (len(row) >= 2 and row[0] == email and 
                    row[1] == session_id and row[4] == ""):
                    
                    row_num = i + 1
                    
                    if duration_ms == 0 and row[3]:
                        try:
                            login_dt = datetime.strptime(row[3], "%Y-%m-%d %H:%M:%S")
                            logout_dt = datetime.strptime(logout_time, "%Y-%m-%d %H:%M:%S")
                            duration_ms = int((logout_dt - login_dt).total_seconds() * 1000)
                        except Exception:
                            pass
                    
                    duration_formatted = self._format_duration(duration_ms)
                    self._rate_limit()
                    
                    update_data = [[logout_time, str(tokens_used), str(operations), duration_formatted, status]]
                    self.activity_worksheet.update(f'E{row_num}:I{row_num}', update_data)
                    return True
            
            # No matching row found
            self._rate_limit()
            duration_formatted = self._format_duration(duration_ms)
            
            self.activity_worksheet.append_row([
                email, session_id, "", "", logout_time,
                str(tokens_used), str(operations), duration_formatted, status
            ])
            return True
            
        except Exception:
            return False
    
    def update_session_metrics(self, email: str, session_id: str, 
                              tokens_used: int, operations: int) -> bool:
        """Update session metrics - NO LOGGING"""
        if not self.enabled or operations % 10 != 0:
            return True
        
        try:
            self._rate_limit()
            all_rows = self.activity_worksheet.get_all_values()
            
            for i, row in enumerate(all_rows):
                if len(row) >= 2 and row[0] == email and row[1] == session_id:
                    row_num = i + 1
                    self._rate_limit()
                    self.activity_worksheet.update(
                        f'F{row_num}:G{row_num}',
                        [[str(tokens_used), str(operations)]]
                    )
                    return True
            return False
        except Exception:
            return False
    
    def get_session_metrics(self, email: str, session_id: str) -> Dict[str, Any]:
        """Get metrics for session"""
        if not self.enabled:
            return {}
        
        try:
            self._rate_limit()
            all_rows = self.activity_worksheet.get_all_values()
            
            for row in all_rows:
                if len(row) >= 2 and row[0] == email and row[1] == session_id:
                    return {
                        "email": row[0],
                        "session_id": row[1],
                        "trace_id": row[2] if len(row) > 2 else "",
                        "login_time": row[3] if len(row) > 3 else "",
                        "logout_time": row[4] if len(row) > 4 else "",
                        "tokens_used": int(row[5]) if len(row) > 5 and row[5] else 0,
                        "operations": int(row[6]) if len(row) > 6 and row[6] else 0,
                        "duration_ms": int(row[7]) if len(row) > 7 and row[7] else 0,
                        "status": row[8] if len(row) > 8 else ""
                    }
            return {}
        except Exception:
            return {}
    
    def close_orphaned_sessions(self, email: str) -> int:
        """Close orphaned sessions - ONLY logs if found"""
        if not self.enabled:
            return 0
        
        try:
            self._rate_limit()
            all_rows = self.activity_worksheet.get_all_values()
            closed_count = 0
            current_time = self._get_timestamp()
            
            for i, row in enumerate(all_rows):
                if (len(row) >= 9 and row[0] == email and 
                    row[8] == "started" and row[4] == ""):
                    
                    row_num = i + 1
                    duration_ms = 0
                    
                    if row[3]:
                        try:
                            login_dt = datetime.strptime(row[3], "%Y-%m-%d %H:%M:%S")
                            current_dt = datetime.strptime(current_time, "%Y-%m-%d %H:%M:%S")
                            duration_ms = int((current_dt - login_dt).total_seconds() * 1000)
                        except Exception:
                            pass
                    
                    duration_formatted = self._format_duration(duration_ms)
                    tokens_used = row[5] if len(row) > 5 else "0"
                    operations = row[6] if len(row) > 6 else "0"
                    
                    self._rate_limit()
                    self.activity_worksheet.update(
                        f'E{row_num}:I{row_num}',
                        [[current_time, tokens_used, operations, duration_formatted, "closed"]]
                    )
                    closed_count += 1
            
            # Only log if we actually closed sessions
            if closed_count > 0:
                logger.info(f"✅ Cleaned up {closed_count} session(s)")
            
            return closed_count
        except Exception:
            return 0
    
    def get_user_sessions(self, email: str, limit: int = 10) -> list:
        """Get recent sessions"""
        if not self.enabled:
            return []
        
        try:
            self._rate_limit()
            all_rows = self.activity_worksheet.get_all_values()
            user_sessions = []
            
            for row in all_rows[1:]:
                if len(row) >= 1 and row[0] == email:
                    session_data = {
                        "email": row[0],
                        "session_id": row[1] if len(row) > 1 else "",
                        "trace_id": row[2] if len(row) > 2 else "",
                        "login_time": row[3] if len(row) > 3 else "",
                        "logout_time": row[4] if len(row) > 4 else "",
                        "tokens_used": int(row[5]) if len(row) > 5 and row[5] else 0,
                        "operations": int(row[6]) if len(row) > 6 and row[6] else 0,
                        "duration_ms": int(row[7]) if len(row) > 7 and row[7] else 0,
                        "status": row[8] if len(row) > 8 else ""
                    }
                    user_sessions.append(session_data)
            
            return user_sessions[-limit:][::-1]
        except Exception:
            return []
    
    # ============================================
    # QUOTA TRACKING METHODS
    # ============================================
    
    def log_quota_update(self, email: str, session_id: str, quota_type: str, 
                        used: int, timestamp: Optional[str] = None) -> bool:
        """Log quota usage update to Google Sheets (with rate limit protection)"""
        if not self.enabled:
            return False
        
        try:
            if timestamp is None:
                timestamp = self._get_timestamp()
            
            # Apply rate limiting
            self._rate_limit()
            
            # Try to update existing row (minimize API calls)
            try:
                all_rows = self.quota_worksheet.get_all_values()
                
                for i, row in enumerate(all_rows):
                    if len(row) >= 2 and row[0] == email and row[1] == session_id:
                        row_num = i + 1
                        
                        # Update only changed column (minimize writes)
                        self._rate_limit()
                        
                        if quota_type == 'gemini_tokens':
                            self.quota_worksheet.update(f'C{row_num}', [[str(used)]])
                        elif quota_type == 'google_ads_ops':
                            self.quota_worksheet.update(f'D{row_num}', [[str(used)]])
                        
                        return True
            except Exception:
                # Read failed - skip update (non-critical)
                return False
            
            # No existing row - create new one
            self._rate_limit()
            gemini_used = used if quota_type == 'gemini_tokens' else 0
            ads_used = used if quota_type == 'google_ads_ops' else 0
            
            from app.quota_system.quota_manager import QuotaManager
            
            self.quota_worksheet.append_row([
                email,
                session_id,
                str(gemini_used),
                str(ads_used),
                timestamp,
                str(QuotaManager.DEFAULT_GEMINI_TOKEN_LIMIT),
                str(QuotaManager.DEFAULT_GOOGLE_ADS_OP_LIMIT),
                "active"
            ])
            return True
            
        except Exception as e:
            # Silently handle rate limits (non-critical)
            if "429" in str(e) or "Quota exceeded" in str(e):
                pass  # Skip sync, not critical
            return False
    
    def get_user_quotas(self, email: str) -> Optional[Dict[str, int]]:
        """Get user's current quota usage from Google Sheets"""
        if not self.enabled:
            return None
        
        try:
            self._rate_limit()
            all_rows = self.quota_worksheet.get_all_values()
            
            # Find most recent row for this user
            for row in reversed(all_rows):
                if len(row) >= 1 and row[0] == email:
                    return {
                        'gemini_tokens': int(row[2]) if len(row) > 2 and row[2] else 0,
                        'google_ads_ops': int(row[3]) if len(row) > 3 and row[3] else 0
                    }
            
            return None
        except Exception:
            return None
    
    def reset_user_quotas(self, email: str) -> bool:
        """Reset quotas for a specific user (admin only)"""
        if not self.enabled:
            return False
        
        try:
            self._rate_limit()
            all_rows = self.quota_worksheet.get_all_values()
            current_time = self._get_timestamp()
            
            # Update all rows for this user
            for i, row in enumerate(all_rows):
                if len(row) >= 1 and row[0] == email:
                    row_num = i + 1
                    self._rate_limit()
                    self.quota_worksheet.update(
                        f'C{row_num}:E{row_num}',
                        [["0", "0", current_time]]
                    )
            
            return True
        except Exception:
            return False
    
    def log_gemini_usage(self, user_id: str, session_id: str, 
                        tokens_used: int, operation_type: str) -> bool:
        """Log individual Gemini API usage to sheets"""
        if not self.enabled:
            return False
        
        try:
            self._rate_limit()
            self.gemini_usage_worksheet.append_row([
                user_id,
                session_id,
                operation_type,
                str(tokens_used),
                self._get_timestamp(),
                "active"
            ])
            return True
        except Exception as e:
            print(f"Failed to log Gemini usage: {e}")
            return False
    
    def get_user_gemini_usage(self, user_id: str, session_id: str = None) -> Dict:
        """Get user's Gemini usage for current session or all sessions"""
        if not self.enabled:
            return {}
        
        try:
            self._rate_limit()
            all_rows = self.gemini_usage_worksheet.get_all_values()
            
            user_usage = []
            for row in all_rows[1:]:  # Skip header
                if len(row) >= 6 and row[0] == user_id:
                    if session_id is None or row[1] == session_id:
                        user_usage.append({
                            'session_id': row[1],
                            'operation_type': row[2],
                            'tokens_used': int(row[3]) if row[3] else 0,
                            'timestamp': row[4],
                            'status': row[5]
                        })
            
            # Group usage by session
            by_session = {}
            for usage in user_usage:
                session_id = usage['session_id']
                if session_id not in by_session:
                    by_session[session_id] = {
                        'total_tokens': 0,
                        'operations': 0,
                        'operations_list': []
                    }
                by_session[session_id]['total_tokens'] += usage['tokens_used']
                by_session[session_id]['operations'] += 1
                by_session[session_id]['operations_list'].append(usage)
            
            return {
                'total_tokens': sum(usage['tokens_used'] for usage in user_usage),
                'total_operations': len(user_usage),
                'by_session': by_session
            }
        except Exception:
            return {}


class SessionTracker:
    """Tracks session metrics and operations"""
    
    def __init__(self):
        self.start_time = time.time()
        self.tokens_used = 0
        self.operations_count = 0
        self.session_id = str(uuid.uuid4())
        self.trace_id = ""
    
    def set_trace_id(self, trace_id: str):
        self.trace_id = trace_id
    
    def increment_tokens(self, count: int):
        self.tokens_used += count
    
    def increment_operations(self, count: int = 1):
        self.operations_count += count
    
    def get_duration_ms(self) -> int:
        return int((time.time() - self.start_time) * 1000)
    
    def get_session_data(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "trace_id": self.trace_id,
            "tokens_used": self.tokens_used,
            "operations": self.operations_count,
            "duration_ms": self.get_duration_ms()
        }
