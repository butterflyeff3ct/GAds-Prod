"""Google Sheets Integration for User Tracking and Session Logging
Updated Schema with Rate Limiting and Caching
- Users Tab: Email | First Name | Last Name | First Login | Profile Pic | Locale | User ID
- Activity Tab: Email | Session ID | Trace ID | Login Time | Logout Time | Tokens Used | Operations | Duration (ms) | Status
"""
import gspread
import streamlit as st
import uuid
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Optional, Dict, Any
import time
import hashlib


class GSheetLogger:
    """Handles Google Sheets logging for users and activity tracking with rate limiting"""
    
    def __init__(self, sheet_id: Optional[str] = None):
        """Initialize Google Sheets client with caching"""
        try:
            # Get configuration from Streamlit secrets
            gsheet_config = st.secrets.get("google_sheets", {})
            self.sheet_id = sheet_id or gsheet_config.get("sheet_id")
            
            if not self.sheet_id:
                st.warning("⚠️ Google Sheets logging disabled - no sheet_id configured")
                self.enabled = False
                return
            
            # Rate limiting - track last request time
            self._last_request_time = 0
            self._min_request_interval = 2.0  # Minimum 2 seconds between requests
            
            # Cache for read operations
            self._user_cache = {}
            self._cache_ttl = 300  # 5 minutes cache
            self._cache_timestamp = 0
            
            # Set up Google Sheets client
            scope = [
                "https://spreadsheets.google.com/feeds",
                "https://www.googleapis.com/auth/drive"
            ]
            
            # Use credentials from secrets
            credentials_info = gsheet_config.get("credentials")
            if not credentials_info:
                st.warning("⚠️ Google Sheets logging disabled - no credentials configured")
                self.enabled = False
                return
            
            # Create credentials from dictionary
            from oauth2client.service_account import ServiceAccountCredentials
            credentials = ServiceAccountCredentials.from_json_keyfile_dict(
                credentials_info, scope
            )
            
            self.client = gspread.authorize(credentials)
            
            # Use cached worksheet access
            self._init_worksheets()
            
            self.enabled = True
            
        except Exception as e:
            st.error(f"❌ Google Sheets initialization failed: {e}")
            self.enabled = False
    
    def _rate_limit(self):
        """Enforce rate limiting between API calls"""
        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        
        if time_since_last < self._min_request_interval:
            sleep_time = self._min_request_interval - time_since_last
            time.sleep(sleep_time)
        
        self._last_request_time = time.time()
    
    def _init_worksheets(self):
        """Initialize worksheets with caching - only called once"""
        # This is called only during __init__, not on every operation
        try:
            self.sheet = self.client.open_by_key(self.sheet_id)
            
            # Get or create Users worksheet
            try:
                self.users_worksheet = self.sheet.worksheet("Users")
            except gspread.WorksheetNotFound:
                self._rate_limit()
                self.users_worksheet = self.sheet.add_worksheet(
                    title="Users", rows=1000, cols=7
                )
                self.users_worksheet.append_row([
                    "Email", "First Name", "Last Name", "First Login", 
                    "Profile Pic", "Locale", "User ID"
                ])
            
            # Get or create Activity worksheet
            try:
                self.activity_worksheet = self.sheet.worksheet("Activity")
            except gspread.WorksheetNotFound:
                self._rate_limit()
                self.activity_worksheet = self.sheet.add_worksheet(
                    title="Activity", rows=10000, cols=9
                )
                self.activity_worksheet.append_row([
                    "Email", "Session ID", "Trace ID", "Login Time", 
                    "Logout Time", "Tokens Used", "Operations", "Duration (ms)", "Status"
                ])
        except Exception as e:
            raise Exception(f"Failed to initialize worksheets: {e}")
    
    def _get_timestamp(self) -> str:
        """Get current timestamp in EST/EDT"""
        try:
            est_tz = ZoneInfo("America/New_York")
            return datetime.now(est_tz).strftime("%Y-%m-%d %H:%M:%S")
        except ImportError:
            from datetime import timezone, timedelta
            est_offset = timedelta(hours=-5)
            return datetime.now(timezone(est_offset)).strftime("%Y-%m-%d %H:%M:%S")
    
    def _check_user_exists_cached(self, email: str) -> bool:
        """Check if user exists using cache to avoid API calls"""
        # Check cache first
        current_time = time.time()
        if email in self._user_cache:
            return True
        
        # Only refresh cache if expired
        if current_time - self._cache_timestamp > self._cache_ttl:
            try:
                self._rate_limit()
                email_column = self.users_worksheet.col_values(1)
                existing_emails = email_column[1:]  # Skip header
                
                # Update cache
                self._user_cache = {e: True for e in existing_emails}
                self._cache_timestamp = current_time
            except Exception as e:
                # If read fails, assume user doesn't exist to try writing
                print(f"Cache refresh failed: {e}")
                return False
        
        return email in self._user_cache
    
    def store_user_if_new(self, user_data: Dict[str, Any]) -> bool:
        """Store user data if email doesn't already exist
        Schema: Email | First Name | Last Name | First Login | Profile Pic | Locale | User ID
        """
        if not self.enabled:
            return False
        
        try:
            email = user_data["email"]
            
            # Check cache first to avoid API call
            if self._check_user_exists_cached(email):
                return False
            
            # Rate limit before write
            self._rate_limit()
            
            # Add new user
            self.users_worksheet.append_row([
                user_data["email"],
                user_data.get("first_name", ""),
                user_data.get("last_name", ""),
                user_data.get("first_login", self._get_timestamp()),
                user_data.get("picture", ""),
                user_data.get("locale", ""),
                user_data.get("user_id", "")
            ])
            
            # Update cache
            self._user_cache[email] = True
            
            return True
            
        except Exception as e:
            if "429" in str(e) or "Quota exceeded" in str(e):
                st.warning("⚠️ Rate limit reached. User data will be logged on next session.")
            else:
                st.error(f"❌ Failed to store user data: {e}")
            return False
    
    def log_session_start(self, email: str, session_id: str, 
                         trace_id: str = "", login_time: Optional[str] = None) -> bool:
        """Log session start in Activity sheet
        Schema: Email | Session ID | Trace ID | Login Time | Logout Time | Tokens Used | Operations | Duration (ms) | Status
        """
        if not self.enabled:
            return False
        
        try:
            if login_time is None:
                login_time = self._get_timestamp()
            
            # Rate limit before write
            self._rate_limit()
            
            self.activity_worksheet.append_row([
                email,
                session_id,
                trace_id,
                login_time,
                "",
                "",
                "",
                "",
                "started"
            ])
            
            return True
            
        except Exception as e:
            if "429" in str(e) or "Quota exceeded" in str(e):
                st.warning("⚠️ Rate limit reached. Session will be logged on next operation.")
            else:
                st.error(f"❌ Failed to log session start: {e}")
            return False
    
    def log_session_end(self, email: str, session_id: str, 
                       logout_time: Optional[str] = None,
                       tokens_used: int = 0, operations: int = 0, 
                       duration_ms: int = 0, status: str = "completed") -> bool:
        """Update session end data in Activity sheet
        Schema: Email | Session ID | Trace ID | Login Time | Logout Time | Tokens Used | Operations | Duration (ms) | Status
        """
        if not self.enabled:
            return False
        
        try:
            if logout_time is None:
                logout_time = self._get_timestamp()
            
            # Rate limit before read
            self._rate_limit()
            
            # Find the row with matching email and session_id
            all_rows = self.activity_worksheet.get_all_values()
            
            for i, row in enumerate(all_rows):
                if (len(row) >= 2 and row[0] == email and 
                    row[1] == session_id and row[4] == ""):
                    
                    row_num = i + 1
                    
                    # Calculate duration if not provided
                    if duration_ms == 0 and row[3]:
                        try:
                            login_dt = datetime.strptime(row[3], "%Y-%m-%d %H:%M:%S")
                            logout_dt = datetime.strptime(logout_time, "%Y-%m-%d %H:%M:%S")
                            duration_ms = int((logout_dt - login_dt).total_seconds() * 1000)
                        except Exception:
                            pass
                    
                    # Batch update - single API call
                    self._rate_limit()
                    self.activity_worksheet.update(
                        f'E{row_num}:I{row_num}',
                        [[logout_time, str(tokens_used), str(operations), str(duration_ms), status]]
                    )
                    
                    return True
            
            # If no matching row found, create new one
            self._rate_limit()
            self.activity_worksheet.append_row([
                email,
                session_id,
                "",
                "",
                logout_time,
                str(tokens_used),
                str(operations),
                str(duration_ms),
                status
            ])
            
            return True
            
        except Exception as e:
            if "429" in str(e) or "Quota exceeded" in str(e):
                st.warning("⚠️ Rate limit reached. Session end will be logged later.")
            else:
                st.error(f"❌ Failed to log session end: {e}")
            return False
    
    def update_session_metrics(self, email: str, session_id: str, 
                              tokens_used: int, operations: int) -> bool:
        """Update session metrics during an active session - with reduced frequency"""
        if not self.enabled:
            return False
        
        # Skip frequent updates to avoid rate limits
        # Only update every 10 operations
        if operations % 10 != 0:
            return True
        
        try:
            self._rate_limit()
            all_rows = self.activity_worksheet.get_all_values()
            
            for i, row in enumerate(all_rows):
                if len(row) >= 2 and row[0] == email and row[1] == session_id:
                    row_num = i + 1
                    
                    # Batch update
                    self._rate_limit()
                    self.activity_worksheet.update(
                        f'F{row_num}:G{row_num}',
                        [[str(tokens_used), str(operations)]]
                    )
                    
                    return True
            
            return False
            
        except Exception as e:
            # Silently fail for metric updates to avoid spam
            return False
    
    def get_session_metrics(self, email: str, session_id: str) -> Dict[str, Any]:
        """Get metrics for a specific session - cached"""
        if not self.enabled:
            return {}
        
        # This is rarely called, so rate limiting is OK
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
            
        except Exception as e:
            return {}
    
    def get_user_sessions(self, email: str, limit: int = 10) -> list:
        """Get recent sessions for a specific user"""
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
            
        except Exception as e:
            return []


class SessionTracker:
    """Tracks session metrics and operations"""
    
    def __init__(self):
        """Initialize session tracker"""
        self.start_time = time.time()
        self.tokens_used = 0
        self.operations_count = 0
        self.session_id = str(uuid.uuid4())
        self.trace_id = ""
    
    def set_trace_id(self, trace_id: str):
        """Set trace ID for the session"""
        self.trace_id = trace_id
    
    def increment_tokens(self, count: int):
        """Increment token usage"""
        self.tokens_used += count
    
    def increment_operations(self, count: int = 1):
        """Increment operations count"""
        self.operations_count += count
    
    def get_duration_ms(self) -> int:
        """Get session duration in milliseconds"""
        return int((time.time() - self.start_time) * 1000)
    
    def get_session_data(self) -> Dict[str, Any]:
        """Get current session data"""
        return {
            "session_id": self.session_id,
            "trace_id": self.trace_id,
            "tokens_used": self.tokens_used,
            "operations": self.operations_count,
            "duration_ms": self.get_duration_ms()
        }

