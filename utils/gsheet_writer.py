"""Google Sheets Integration - FIXED Column Alignment
Ensures data always matches column headers exactly.
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
    """Handles Google Sheets logging with proper column alignment"""
    
    # Define column structure as constants for consistency
    # UPDATED: Match actual Google Sheets structure with approval workflow
    USERS_COLUMNS = [
        "User ID", "Email", "Name", "Status", "Signup Timestamp", 
        "First Login", "Last Login", "Approval Date", "Denial Reason", 
        "Reapply Count", "Added By", "Notes", "Profile Pic"
    ]
    ACTIVITY_COLUMNS = [
        "User ID", "Email", "Session ID", "Login Time", "Logout Time", 
        "Status", "Duration (mins)", "Page Views", "Actions Taken", 
        "IP Address", "User Agent", "Last Activity", "Idle Timeout"
    ]
    QUOTA_COLUMNS = [
        "Email", "Session ID", "Gemini Tokens", "Google Ads Ops", 
        "Last Updated", "Gemini Limit", "Ads Limit", "Status"
    ]
    GEMINI_USAGE_COLUMNS = [
        "User ID", "Session ID", "Operation Type", "Tokens Used", 
        "Timestamp", "Status"
    ]
    
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
            self._user_cache = {}  # Cache for email existence checks
            self._user_id_cache = {}  # NEW: Cache for email -> User ID mapping
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
        """Initialize worksheets with proper column headers"""
        try:
            self.sheet = self.client.open_by_key(self.sheet_id)
            
            # Users worksheet
            try:
                self.users_worksheet = self.sheet.worksheet("Users")
                # Verify headers match expected structure
                try:
                    existing_headers = self.users_worksheet.row_values(1)
                    if existing_headers != self.USERS_COLUMNS:
                        logger.warning(f"Users headers mismatch. Expected {len(self.USERS_COLUMNS)} columns, found {len(existing_headers)}")
                        logger.info("Auto-correcting Users headers...")
                        self._rate_limit()
                        self.users_worksheet.update('A1:M1', [self.USERS_COLUMNS])
                except Exception as e:
                    # If can't verify headers, log but continue
                    logger.warning(f"Could not verify Users headers: {e}")
            except gspread.WorksheetNotFound:
                logger.info("Creating new Users worksheet...")
                self._rate_limit()
                self.users_worksheet = self.sheet.add_worksheet(
                    title="Users", rows=1000, cols=len(self.USERS_COLUMNS)
                )
                self.users_worksheet.append_row(self.USERS_COLUMNS)
            
            # Activity worksheet
            try:
                self.activity_worksheet = self.sheet.worksheet("Activity")
                try:
                    existing_headers = self.activity_worksheet.row_values(1)
                    if existing_headers != self.ACTIVITY_COLUMNS:
                        logger.warning(f"Activity headers mismatch. Expected {len(self.ACTIVITY_COLUMNS)} columns, found {len(existing_headers)}")
                        logger.info("Auto-correcting Activity headers...")
                        self._rate_limit()
                        self.activity_worksheet.update('A1:M1', [self.ACTIVITY_COLUMNS])
                except Exception as e:
                    logger.warning(f"Could not verify Activity headers: {e}")
            except gspread.WorksheetNotFound:
                logger.info("Creating new Activity worksheet...")
                self._rate_limit()
                self.activity_worksheet = self.sheet.add_worksheet(
                    title="Activity", rows=10000, cols=len(self.ACTIVITY_COLUMNS)
                )
                self.activity_worksheet.append_row(self.ACTIVITY_COLUMNS)
            
            # Quotas worksheet
            try:
                self.quota_worksheet = self.sheet.worksheet("Quotas")
                existing_headers = self.quota_worksheet.row_values(1)
                if existing_headers != self.QUOTA_COLUMNS:
                    logger.warning("Quotas worksheet headers don't match - updating")
                    self._rate_limit()
                    self.quota_worksheet.update('A1:H1', [self.QUOTA_COLUMNS])
            except gspread.WorksheetNotFound:
                self._rate_limit()
                self.quota_worksheet = self.sheet.add_worksheet(title="Quotas", rows=1000, cols=len(self.QUOTA_COLUMNS))
                self.quota_worksheet.append_row(self.QUOTA_COLUMNS)
            
            # Gemini Usage worksheet
            try:
                self.gemini_usage_worksheet = self.sheet.worksheet("Gemini Usage")
                existing_headers = self.gemini_usage_worksheet.row_values(1)
                if existing_headers != self.GEMINI_USAGE_COLUMNS:
                    logger.warning("Gemini Usage worksheet headers don't match - updating")
                    self._rate_limit()
                    self.gemini_usage_worksheet.update('A1:F1', [self.GEMINI_USAGE_COLUMNS])
            except gspread.WorksheetNotFound:
                self._rate_limit()
                self.gemini_usage_worksheet = self.sheet.add_worksheet(
                    title="Gemini Usage", rows=10000, cols=len(self.GEMINI_USAGE_COLUMNS)
                )
                self.gemini_usage_worksheet.append_row(self.GEMINI_USAGE_COLUMNS)
                
        except Exception as e:
            raise Exception(f"Failed to initialize worksheets: {e}")
    
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
    
    def update_user_login_timestamps(self, email: str, is_first_login: bool = False) -> bool:
        """
        Update First Login (column F) and Last Login (column G) in Users sheet.
        
        Args:
            email: User's email address
            is_first_login: If True, updates First Login. Always updates Last Login.
            
        Returns:
            True if successful
        """
        if not self.enabled:
            return False
        
        try:
            self._rate_limit()
            all_rows = self.users_worksheet.get_all_values()
            current_time = self._get_timestamp()
            
            for i, row in enumerate(all_rows):
                if i == 0:  # Skip header
                    continue
                
                # Match by email (column B)
                if len(row) >= 2 and row[1] == email:
                    row_num = i + 1
                    self._rate_limit()
                    
                    if is_first_login or (len(row) > 5 and not row[5]):  # Column F empty
                        # Update First Login (column F)
                        self.users_worksheet.update(f'F{row_num}', [[current_time]])
                    
                    # Always update Last Login (column G)
                    self.users_worksheet.update(f'G{row_num}', [[current_time]])
                    return True
            
            return False
        except Exception:
            return False
    
    def get_user_id_by_email(self, email: str) -> str:
        """
        Get the 6-digit User ID for a user by their email.
        Uses caching for performance - rebuilds cache if User ID not found.
        
        Returns:
            6-digit User ID string, or empty string if not found
        """
        if not self.enabled:
            return ""
        
        # Check cache first
        if email in self._user_id_cache:
            return self._user_id_cache[email]
        
        # Not in cache - need to rebuild
        # Rebuild cache even if not stale (user might be newly added)
        try:
            self._rate_limit()
            all_rows = self.users_worksheet.get_all_values()
            
            # Clear and rebuild both caches
            self._user_id_cache.clear()
            self._user_cache.clear()
            
            for i, row in enumerate(all_rows):
                if i == 0:  # Skip header
                    continue
                
                # Email is in column B (index 1), User ID is in column A (index 0)
                if len(row) >= 2 and row[1]:  # Has email
                    user_email = row[1]
                    user_id = row[0]
                    self._user_id_cache[user_email] = user_id
                    self._user_cache[user_email] = True
            
            self._cache_timestamp = time.time()
            
            # Return from rebuilt cache
            return self._user_id_cache.get(email, "")
            
        except Exception:
            return ""
    
    def _check_user_exists_cached(self, email: str) -> bool:
        """Check if user exists using cache - also populates User ID cache"""
        current_time = time.time()
        if email in self._user_cache:
            return True
        
        # Rebuild both caches together (efficient - single API call)
        if current_time - self._cache_timestamp > self._cache_ttl:
            try:
                self._rate_limit()
                all_rows = self.users_worksheet.get_all_values()
                
                # Clear old caches
                self._user_cache.clear()
                self._user_id_cache.clear()
                
                # Populate both caches from same data read
                for i, row in enumerate(all_rows):
                    if i == 0:  # Skip header
                        continue
                    if len(row) >= 2 and row[1]:  # Has email in column B
                        user_email = row[1]
                        user_id = row[0]  # User ID from column A
                        self._user_cache[user_email] = True
                        self._user_id_cache[user_email] = user_id  # Cache email -> User ID mapping
                
                self._cache_timestamp = current_time
            except Exception:
                return False
        
        return email in self._user_cache
    
    def store_user_if_new(self, user_data: Dict[str, Any]) -> bool:
        """
        Store user data if email doesn't exist
        
        Columns: User ID, Email, Name, Status, Signup Timestamp, First Login, 
                 Last Login, Approval Date, Denial Reason, Reapply Count, Added By, Notes, Profile Pic
        """
        if not self.enabled:
            return False
        
        try:
            email = user_data["email"]
            
            if self._check_user_exists_cached(email):
                return False
            
            user_id = self._generate_user_id()
            current_time = self._get_timestamp()
            self._rate_limit()
            
            # FIXED: Match actual Users sheet structure (13 columns)
            row_data = [
                user_id,                                                    # A: User ID
                user_data["email"],                                        # B: Email
                user_data.get("name", 
                    f"{user_data.get('first_name', '')} {user_data.get('last_name', '')}".strip()),  # C: Name
                "pending_approval",                                        # D: Status (pending until admin approves)
                current_time,                                              # E: Signup Timestamp
                "",                                                        # F: First Login (empty until first login)
                "",                                                        # G: Last Login (empty until login)
                "",                                                        # H: Approval Date (empty until approved)
                "",                                                        # I: Denial Reason (empty)
                "0",                                                       # J: Reapply Count
                "self_signup",                                             # K: Added By
                "",                                                        # L: Notes
                user_data.get("picture", "")                              # M: Profile Pic
            ]
            
            self.users_worksheet.append_row(row_data)
            self._user_cache[email] = True
            self._user_id_cache[email] = user_id  # NEW: Cache the User ID immediately
            return True
            
        except Exception as e:
            if "429" in str(e) and self.is_production:
                st.warning("⚠️ Rate limit reached")
            return False
    
    def log_session_start(self, email: str, session_id: str, 
                         trace_id: str = "", login_time: Optional[str] = None,
                         user_id: str = "", ip_address: str = "", 
                         user_agent: str = "") -> bool:
        """
        Log session start with IP address and user agent
        
        Columns: User ID, Email, Session ID, Login Time, Logout Time, Status, 
                 Duration (mins), Page Views, Actions Taken, IP Address, User Agent, Last Activity, Idle Timeout
        
        IMPORTANT: User ID in column A will be the 6-digit ID from Users sheet (for referential integrity)
        
        Args:
            email: User email
            session_id: Unique session identifier
            trace_id: Trace ID for logging
            login_time: Login timestamp (auto-generated if not provided)
            user_id: User ID (auto-fetched if not provided)
            ip_address: Client IP address
            user_agent: Browser user agent string
        """
        if not self.enabled:
            return False
        
        try:
            if login_time is None:
                login_time = self._get_timestamp()
            
            # CRITICAL: Fetch the 6-digit User ID from Users sheet for referential integrity
            # First check cache (fast)
            user_id_6digit = self._user_id_cache.get(email)
            
            # If not in cache, fetch from sheet
            if not user_id_6digit:
                user_id_6digit = self.get_user_id_by_email(email)
            
            # If still not found, fall back to provided user_id or trace_id as last resort
            if not user_id_6digit:
                user_id_6digit = user_id or trace_id
            
            self._rate_limit()
            
            # FIXED: Provide all 13 values to match ACTIVITY_COLUMNS with IP and User Agent
            row_data = [
                user_id_6digit,         # A: User ID (6-digit from Users sheet)
                email,                  # B: Email
                session_id,             # C: Session ID
                login_time,             # D: Login Time
                "",                     # E: Logout Time (empty for start)
                "active",               # F: Status
                "00:00",                # G: Duration (mm:ss) (initial)
                "0",                    # H: Page Views (initial)
                "0",                    # I: Actions Taken (initial)
                ip_address or "",       # J: IP Address
                user_agent or "",       # K: User Agent
                login_time,             # L: Last Activity (same as login initially)
                ""                      # M: Idle Timeout
            ]
            
            self.activity_worksheet.append_row(row_data)
            return True
            
        except Exception:
            return False
    
    def log_session_end(self, email: str, session_id: str, 
                       logout_time: Optional[str] = None,
                       tokens_used: int = 0, operations: int = 0, 
                       duration_ms: int = 0, status: str = "completed") -> bool:
        """
        Update session end data
        
        Updates columns: Logout Time, Status, Duration (mins), Last Activity
        """
        if not self.enabled:
            return False
        
        try:
            if logout_time is None:
                logout_time = self._get_timestamp()
            
            self._rate_limit()
            all_rows = self.activity_worksheet.get_all_values()
            
            for i, row in enumerate(all_rows):
                if i == 0:  # Skip header
                    continue
                    
                # Match by email and session_id (columns B and C)
                if (len(row) >= 13 and row[1] == email and 
                    row[2] == session_id and row[4] == ""):  # Logout Time empty
                    
                    row_num = i + 1
                    
                    # Calculate duration in mm:ss format
                    duration_formatted = "00:00"
                    if duration_ms == 0 and row[3]:  # Login Time in column D
                        try:
                            login_dt = datetime.strptime(row[3], "%Y-%m-%d %H:%M:%S")
                            logout_dt = datetime.strptime(logout_time, "%Y-%m-%d %H:%M:%S")
                            duration_ms = int((logout_dt - login_dt).total_seconds() * 1000)
                            duration_formatted = self._format_duration(duration_ms)
                        except Exception:
                            pass
                    else:
                        duration_formatted = self._format_duration(duration_ms)
                    
                    self._rate_limit()
                    
                    # FIXED: Update columns E, F, G, L with mm:ss format for duration
                    # E: Logout Time, F: Status, G: Duration (mm:ss), L: Last Activity
                    self.activity_worksheet.update(f'E{row_num}', [[logout_time]])
                    self.activity_worksheet.update(f'F{row_num}', [[status]])
                    self.activity_worksheet.update(f'G{row_num}', [[duration_formatted]])
                    self.activity_worksheet.update(f'L{row_num}', [[logout_time]])
                    
                    return True
            
            # No matching row found - create new row with end data
            self._rate_limit()
            duration_formatted = self._format_duration(duration_ms)
            
            # FIXED: Provide all 13 values
            row_data = [
                "",                     # A: User ID (unknown)
                email,                  # B: Email
                session_id,             # C: Session ID
                "",                     # D: Login Time (unknown)
                logout_time,            # E: Logout Time
                status,                 # F: Status
                duration_formatted,     # G: Duration (mm:ss)
                "0",                    # H: Page Views
                "0",                    # I: Actions Taken
                "",                     # J: IP Address
                "",                     # K: User Agent
                logout_time,            # L: Last Activity
                ""                      # M: Idle Timeout
            ]
            
            self.activity_worksheet.append_row(row_data)
            return True
            
        except Exception:
            return False
    
    def update_session_metrics(self, email: str, session_id: str, 
                              tokens_used: int, operations: int) -> bool:
        """Update session metrics - Page Views and Actions (batched)"""
        if not self.enabled or operations % 10 != 0:
            return True
        
        try:
            self._rate_limit()
            all_rows = self.activity_worksheet.get_all_values()
            
            for i, row in enumerate(all_rows):
                if i == 0:  # Skip header
                    continue
                    
                # Match by email (column B) and session_id (column C)
                if len(row) >= 3 and row[1] == email and row[2] == session_id:
                    row_num = i + 1
                    self._rate_limit()
                    
                    # FIXED: Update columns H:I (Page Views, Actions Taken)
                    # We map tokens_used -> page_views and operations -> actions for now
                    self.activity_worksheet.update(
                        f'H{row_num}:I{row_num}',
                        [[str(tokens_used), str(operations)]]
                    )
                    return True
            return False
        except Exception:
            return False
    
    def get_session_metrics(self, email: str, session_id: str) -> Dict[str, Any]:
        """Get metrics for a specific session"""
        if not self.enabled:
            return {}
        
        try:
            self._rate_limit()
            all_rows = self.activity_worksheet.get_all_values()
            
            for i, row in enumerate(all_rows):
                if i == 0:  # Skip header
                    continue
                    
                # Match by email (column B) and session_id (column C)
                if len(row) >= 3 and row[1] == email and row[2] == session_id:
                    # FIXED: Parse according to actual ACTIVITY_COLUMNS structure
                    return {
                        "user_id": row[0] if len(row) > 0 else "",
                        "email": row[1] if len(row) > 1 else "",
                        "session_id": row[2] if len(row) > 2 else "",
                        "login_time": row[3] if len(row) > 3 else "",
                        "logout_time": row[4] if len(row) > 4 else "",
                        "status": row[5] if len(row) > 5 else "",
                        "duration": row[6] if len(row) > 6 else "00:00",  # mm:ss format
                        "page_views": int(row[7]) if len(row) > 7 and row[7].isdigit() else 0,
                        "actions_taken": int(row[8]) if len(row) > 8 and row[8].isdigit() else 0,
                        "ip_address": row[9] if len(row) > 9 else "",
                        "user_agent": row[10] if len(row) > 10 else "",
                        "last_activity": row[11] if len(row) > 11 else "",
                        "idle_timeout": row[12] if len(row) > 12 else ""
                    }
            return {}
        except Exception:
            return {}
    
    def close_orphaned_sessions(self, email: str) -> int:
        """Close any sessions that were left open"""
        if not self.enabled:
            return 0
        
        try:
            self._rate_limit()
            all_rows = self.activity_worksheet.get_all_values()
            closed_count = 0
            current_time = self._get_timestamp()
            
            for i, row in enumerate(all_rows):
                if i == 0:  # Skip header
                    continue
                    
                # Check if session is active but not ended
                # Email in column B, Session ID in column C, Logout Time in column E, Status in column F
                if (len(row) >= 13 and row[1] == email and 
                    row[5] == "active" and row[4] == ""):  # Active status, no logout time
                    
                    row_num = i + 1
                    
                    # Calculate duration in mm:ss format
                    duration_formatted = "00:00"
                    if row[3]:
                        try:
                            login_dt = datetime.strptime(row[3], "%Y-%m-%d %H:%M:%S")
                            current_dt = datetime.strptime(current_time, "%Y-%m-%d %H:%M:%S")
                            duration_ms = int((current_dt - login_dt).total_seconds() * 1000)
                            duration_formatted = self._format_duration(duration_ms)
                        except Exception:
                            pass
                    
                    self._rate_limit()
                    
                    # FIXED: Update columns E, F, G, L with mm:ss format
                    self.activity_worksheet.update(f'E{row_num}', [[current_time]])
                    self.activity_worksheet.update(f'F{row_num}', [["closed"]])
                    self.activity_worksheet.update(f'G{row_num}', [[duration_formatted]])
                    self.activity_worksheet.update(f'L{row_num}', [[current_time]])
                    
                    closed_count += 1
            
            # Only log if we actually closed sessions
            if closed_count > 0:
                logger.info(f"✅ Cleaned up {closed_count} session(s)")
            
            return closed_count
        except Exception:
            return 0
    
    def get_user_sessions(self, email: str, limit: int = 10) -> list:
        """Get recent sessions for a user"""
        if not self.enabled:
            return []
        
        try:
            self._rate_limit()
            all_rows = self.activity_worksheet.get_all_values()
            user_sessions = []
            
            for i, row in enumerate(all_rows):
                if i == 0:  # Skip header
                    continue
                    
                # Match by email (column B)
                if len(row) >= 1 and row[1] == email:
                    # FIXED: Parse according to actual ACTIVITY_COLUMNS
                    session_data = {
                        "user_id": row[0] if len(row) > 0 else "",
                        "email": row[1] if len(row) > 1 else "",
                        "session_id": row[2] if len(row) > 2 else "",
                        "login_time": row[3] if len(row) > 3 else "",
                        "logout_time": row[4] if len(row) > 4 else "",
                        "status": row[5] if len(row) > 5 else "",
                        "duration": row[6] if len(row) > 6 else "00:00",  # mm:ss format
                        "page_views": int(row[7]) if len(row) > 7 and row[7].isdigit() else 0,
                        "actions_taken": int(row[8]) if len(row) > 8 and row[8].isdigit() else 0,
                        "ip_address": row[9] if len(row) > 9 else "",
                        "user_agent": row[10] if len(row) > 10 else "",
                        "last_activity": row[11] if len(row) > 11 else "",
                        "idle_timeout": row[12] if len(row) > 12 else ""
                    }
                    user_sessions.append(session_data)
            
            # Return most recent sessions
            return user_sessions[-limit:][::-1]
        except Exception:
            return []
    
    # ============================================
    # QUOTA TRACKING METHODS
    # ============================================
    
    def log_quota_update(self, email: str, session_id: str, quota_type: str, 
                        used: int, timestamp: Optional[str] = None) -> bool:
        """
        Log quota usage update
        
        Columns: Email, Session ID, Gemini Tokens, Google Ads Ops, Last Updated, Gemini Limit, Ads Limit, Status
        """
        if not self.enabled:
            return False
        
        try:
            if timestamp is None:
                timestamp = self._get_timestamp()
            
            self._rate_limit()
            
            # Try to find and update existing row
            try:
                all_rows = self.quota_worksheet.get_all_values()
                
                for i, row in enumerate(all_rows):
                    if i == 0:  # Skip header
                        continue
                        
                    if len(row) >= 2 and row[0] == email and row[1] == session_id:
                        row_num = i + 1
                        self._rate_limit()
                        
                        # FIXED: Update correct column based on quota type
                        if quota_type == 'gemini_tokens':
                            # Update column C (Gemini Tokens) and E (Last Updated)
                            self.quota_worksheet.update(
                                f'C{row_num}:C{row_num}', [[str(used)]]
                            )
                            self.quota_worksheet.update(
                                f'E{row_num}:E{row_num}', [[timestamp]]
                            )
                        elif quota_type == 'google_ads_ops':
                            # Update column D (Google Ads Ops) and E (Last Updated)
                            self.quota_worksheet.update(
                                f'D{row_num}:D{row_num}', [[str(used)]]
                            )
                            self.quota_worksheet.update(
                                f'E{row_num}:E{row_num}', [[timestamp]]
                            )
                        
                        return True
            except Exception:
                pass  # Read failed - create new row
            
            # No existing row - create new one
            self._rate_limit()
            
            try:
                from app.quota_system.quota_manager import QuotaManager
                gemini_limit = QuotaManager.DEFAULT_GEMINI_TOKEN_LIMIT
                ads_limit = QuotaManager.DEFAULT_GOOGLE_ADS_OP_LIMIT
            except:
                gemini_limit = 7000
                ads_limit = 10
            
            gemini_used = used if quota_type == 'gemini_tokens' else 0
            ads_used = used if quota_type == 'google_ads_ops' else 0
            
            # FIXED: Provide all 8 values matching QUOTA_COLUMNS
            row_data = [
                email,                  # Email
                session_id,             # Session ID
                str(gemini_used),       # Gemini Tokens
                str(ads_used),          # Google Ads Ops
                timestamp,              # Last Updated
                str(gemini_limit),      # Gemini Limit
                str(ads_limit),         # Ads Limit
                "active"                # Status
            ]
            
            self.quota_worksheet.append_row(row_data)
            return True
            
        except Exception as e:
            # Silently handle rate limits (non-critical)
            if "429" in str(e) or "Quota exceeded" in str(e):
                pass
            return False
    
    def get_user_quotas(self, email: str) -> Optional[Dict[str, int]]:
        """Get user's current quota usage"""
        if not self.enabled:
            return None
        
        try:
            self._rate_limit()
            all_rows = self.quota_worksheet.get_all_values()
            
            # Find most recent row for this user
            for i in range(len(all_rows) - 1, 0, -1):  # Iterate backwards, skip header
                row = all_rows[i]
                if len(row) >= 1 and row[0] == email:
                    # FIXED: Parse according to QUOTA_COLUMNS
                    return {
                        'gemini_tokens': int(row[2]) if len(row) > 2 and row[2].isdigit() else 0,
                        'google_ads_ops': int(row[3]) if len(row) > 3 and row[3].isdigit() else 0
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
                if i == 0:  # Skip header
                    continue
                    
                if len(row) >= 1 and row[0] == email:
                    row_num = i + 1
                    self._rate_limit()
                    
                    # FIXED: Reset columns C:E (Gemini Tokens, Google Ads Ops, Last Updated)
                    self.quota_worksheet.update(
                        f'C{row_num}:E{row_num}',
                        [["0", "0", current_time]]
                    )
            
            return True
        except Exception:
            return False
    
    def log_gemini_usage(self, user_id: str, session_id: str, 
                        tokens_used: int, operation_type: str) -> bool:
        """
        Log individual Gemini API usage
        
        Columns: User ID, Session ID, Operation Type, Tokens Used, Timestamp, Status
        """
        if not self.enabled:
            return False
        
        try:
            self._rate_limit()
            
            # FIXED: Provide all 6 values matching GEMINI_USAGE_COLUMNS
            row_data = [
                user_id,                # User ID
                session_id,             # Session ID
                operation_type,         # Operation Type
                str(tokens_used),       # Tokens Used
                self._get_timestamp(),  # Timestamp
                "active"                # Status
            ]
            
            self.gemini_usage_worksheet.append_row(row_data)
            return True
        except Exception as e:
            print(f"Failed to log Gemini usage: {e}")
            return False
    
    def get_user_gemini_usage(self, user_id: str, session_id: str = None) -> Dict:
        """Get user's Gemini usage"""
        if not self.enabled:
            return {}
        
        try:
            self._rate_limit()
            all_rows = self.gemini_usage_worksheet.get_all_values()
            
            user_usage = []
            for i, row in enumerate(all_rows):
                if i == 0:  # Skip header
                    continue
                    
                if len(row) >= 6 and row[0] == user_id:
                    if session_id is None or row[1] == session_id:
                        # FIXED: Parse according to GEMINI_USAGE_COLUMNS
                        user_usage.append({
                            'user_id': row[0],
                            'session_id': row[1],
                            'operation_type': row[2],
                            'tokens_used': int(row[3]) if row[3].isdigit() else 0,
                            'timestamp': row[4],
                            'status': row[5]
                        })
            
            # Group usage by session
            by_session = {}
            for usage in user_usage:
                sid = usage['session_id']
                if sid not in by_session:
                    by_session[sid] = {
                        'total_tokens': 0,
                        'operations': 0,
                        'operations_list': []
                    }
                by_session[sid]['total_tokens'] += usage['tokens_used']
                by_session[sid]['operations'] += 1
                by_session[sid]['operations_list'].append(usage)
            
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
