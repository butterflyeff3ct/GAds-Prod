"""
Enhanced Google Sheets Schema for User Management System
Extends existing gsheet_writer.py with approval workflow features

NEW SCHEMA:
===========

Users Tab (Enhanced):
--------------------
| User ID | Email | Name | Status | Signup Timestamp | First Login | 
| Last Login | Approval Date | Denial Reason | Reapply Count | 
| Added By | Notes | Profile Pic | Locale |

Activity Tab (Enhanced):
-----------------------
| Session ID | User ID | Email | Login Time | Logout Time | Status | 
| Duration (mins) | Page Views | Actions Taken | IP Address | 
| User Agent | Last Activity | Idle Timeout |

Admin Config Tab (New):
----------------------
| Setting | Value | Description | Last Updated |
"""

import gspread
import streamlit as st
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Optional, Dict, Any, List
import time
import random
from oauth2client.service_account import ServiceAccountCredentials


class UserManagementSheets:
    """Enhanced Google Sheets client for user management with approval workflow"""
    
    # Status constants
    STATUS_PENDING = "pending"
    STATUS_APPROVED = "approved"
    STATUS_ACTIVE = "active"
    STATUS_DENIED = "denied"
    STATUS_SUSPENDED = "suspended"
    
    # Session status constants
    SESSION_STARTED = "started"
    SESSION_ACTIVE = "active"
    SESSION_LOGGED_OUT = "logged_out"
    SESSION_TIMEOUT = "timeout"
    SESSION_CLOSED = "closed"
    
    def __init__(self, sheet_id: Optional[str] = None, show_warnings: bool = True):
        """Initialize Google Sheets client with user management capabilities"""
        try:
            # Get configuration
            gsheet_config = st.secrets.get("google_sheets", {})
            self.sheet_id = sheet_id or gsheet_config.get("sheet_id")
            
            if not self.sheet_id:
                if show_warnings:
                    st.warning("⚠️ Google Sheets not configured. See DEPLOYMENT_GUIDE.md")
                self.enabled = False
                return
            
            # Rate limiting
            self._last_request_time = 0
            self._min_request_interval = 2.0  # 2 seconds between requests
            
            # Set up credentials
            scope = [
                "https://spreadsheets.google.com/feeds",
                "https://www.googleapis.com/auth/drive"
            ]
            
            credentials_info = gsheet_config.get("credentials")
            if not credentials_info:
                if show_warnings:
                    st.warning("⚠️ Google Sheets credentials missing")
                self.enabled = False
                return
            
            credentials = ServiceAccountCredentials.from_json_keyfile_dict(
                credentials_info, scope
            )
            
            self.client = gspread.authorize(credentials)
            self._init_worksheets()
            self.enabled = True
            
            print("[DEBUG] UserManagementSheets initialized successfully")
            
        except Exception as e:
            print(f"[ERROR] UserManagementSheets initialization failed: {e}")
            if show_warnings:
                st.error(f"❌ Failed to initialize user management: {e}")
            self.enabled = False
    
    def _rate_limit(self):
        """Enforce rate limiting between API calls"""
        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        
        if time_since_last < self._min_request_interval:
            sleep_time = self._min_request_interval - time_since_last
            time.sleep(sleep_time)
        
        self._last_request_time = time.time()
    
    def _get_timestamp(self) -> str:
        """Get current timestamp in EST/EDT"""
        try:
            est_tz = ZoneInfo("America/New_York")
            return datetime.now(est_tz).strftime("%Y-%m-%d %H:%M:%S")
        except ImportError:
            from datetime import timezone, timedelta
            est_offset = timedelta(hours=-5)
            return datetime.now(timezone(est_offset)).strftime("%Y-%m-%d %H:%M:%S")
    
    def _init_worksheets(self):
        """Initialize or migrate worksheets with new schema"""
        try:
            self.sheet = self.client.open_by_key(self.sheet_id)
            print(f"[DEBUG] Successfully opened Google Sheet: {self.sheet_id}")
            
            # Initialize Users worksheet with enhanced schema
            try:
                self.users_worksheet = self.sheet.worksheet("Users")
                print("[DEBUG] Found existing Users worksheet")
                # TODO: Add migration logic if needed
            except gspread.WorksheetNotFound:
                self._rate_limit()
                self.users_worksheet = self.sheet.add_worksheet(
                    title="Users", rows=1000, cols=14
                )
                # Enhanced Users schema
                headers = [
                    "User ID", "Email", "Name", "Status", "Signup Timestamp",
                    "First Login", "Last Login", "Approval Date", "Denial Reason",
                    "Reapply Count", "Added By", "Notes", "Profile Pic", "Locale"
                ]
                self.users_worksheet.append_row(headers)
                print("[DEBUG] Created new Users worksheet with enhanced schema")
            
            # Initialize Activity worksheet with enhanced schema
            try:
                self.activity_worksheet = self.sheet.worksheet("Activity")
                print("[DEBUG] Found existing Activity worksheet")
            except gspread.WorksheetNotFound:
                self._rate_limit()
                self.activity_worksheet = self.sheet.add_worksheet(
                    title="Activity", rows=10000, cols=13
                )
                # Enhanced Activity schema
                headers = [
                    "Session ID", "User ID", "Email", "Login Time", "Logout Time",
                    "Status", "Duration (mins)", "Page Views", "Actions Taken",
                    "IP Address", "User Agent", "Last Activity", "Idle Timeout"
                ]
                self.activity_worksheet.append_row(headers)
                print("[DEBUG] Created new Activity worksheet with enhanced schema")
            
            # Initialize Admin Config worksheet
            try:
                self.config_worksheet = self.sheet.worksheet("Admin Config")
                print("[DEBUG] Found existing Admin Config worksheet")
            except gspread.WorksheetNotFound:
                self._rate_limit()
                self.config_worksheet = self.sheet.add_worksheet(
                    title="Admin Config", rows=100, cols=4
                )
                headers = ["Setting", "Value", "Description", "Last Updated"]
                self.config_worksheet.append_row(headers)
                
                # Add default config values
                default_configs = [
                    ["auto_approve_enabled", "false", "Auto-approve new signups", self._get_timestamp()],
                    ["max_reapply_count", "3", "Maximum times user can reapply after denial", self._get_timestamp()],
                    ["session_timeout_mins", "30", "Session timeout in minutes", self._get_timestamp()],
                    ["require_admin_review", "true", "Require manual admin review for signups", self._get_timestamp()]
                ]
                for config in default_configs:
                    self._rate_limit()
                    self.config_worksheet.append_row(config)
                
                print("[DEBUG] Created new Admin Config worksheet")
                
        except Exception as e:
            print(f"[ERROR] Failed to initialize worksheets: {e}")
            raise
    
    def _generate_user_id(self) -> str:
        """Generate unique 6-digit user ID"""
        return str(random.randint(100000, 999999))
    
    def add_user_signup(self, email: str, name: str = "", added_by: str = "self") -> Dict[str, Any]:
        """
        Add new user signup with pending status
        
        Args:
            email: User email
            name: User full name
            added_by: 'self' for self-signup, or admin email if pre-approved
            
        Returns:
            Dict with user_id and status
        """
        if not self.enabled:
            return {"success": False, "error": "Sheets not enabled"}
        
        try:
            # Check if user already exists
            existing_user = self.get_user_by_email(email)
            if existing_user:
                return {
                    "success": False,
                    "error": "User already exists",
                    "user_id": existing_user.get("user_id"),
                    "status": existing_user.get("status")
                }
            
            # Generate user ID
            user_id = self._generate_user_id()
            
            # Determine initial status
            if added_by != "self":
                # Admin-added users are pre-approved
                status = self.STATUS_APPROVED
                approval_date = self._get_timestamp()
            else:
                # Self-signups are pending
                status = self.STATUS_PENDING
                approval_date = ""
            
            self._rate_limit()
            
            # Add user row
            row_data = [
                user_id,                    # User ID
                email,                      # Email
                name,                       # Name
                status,                     # Status
                self._get_timestamp(),      # Signup Timestamp
                "",                         # First Login (empty until they log in)
                "",                         # Last Login
                approval_date,              # Approval Date
                "",                         # Denial Reason
                "0",                        # Reapply Count
                added_by,                   # Added By
                "",                         # Notes
                "",                         # Profile Pic
                ""                          # Locale
            ]
            
            self.users_worksheet.append_row(row_data)
            
            print(f"[DEBUG] ✅ Added user {email} with ID {user_id}, status: {status}")
            
            return {
                "success": True,
                "user_id": user_id,
                "email": email,
                "status": status,
                "added_by": added_by
            }
            
        except Exception as e:
            print(f"[ERROR] Failed to add user signup: {e}")
            return {"success": False, "error": str(e)}
    
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user data by email"""
        if not self.enabled:
            return None
        
        try:
            self._rate_limit()
            all_rows = self.users_worksheet.get_all_values()
            
            for row in all_rows[1:]:  # Skip header
                if row[1] == email:  # Email is column 2 (index 1)
                    return {
                        "user_id": row[0],
                        "email": row[1],
                        "name": row[2],
                        "status": row[3],
                        "signup_timestamp": row[4] if len(row) > 4 else "",
                        "first_login": row[5] if len(row) > 5 else "",
                        "last_login": row[6] if len(row) > 6 else "",
                        "approval_date": row[7] if len(row) > 7 else "",
                        "denial_reason": row[8] if len(row) > 8 else "",
                        "reapply_count": int(row[9]) if len(row) > 9 and row[9] else 0,
                        "added_by": row[10] if len(row) > 10 else "",
                        "notes": row[11] if len(row) > 11 else "",
                        "profile_pic": row[12] if len(row) > 12 else "",
                        "locale": row[13] if len(row) > 13 else ""
                    }
            
            return None
            
        except Exception as e:
            print(f"[ERROR] Failed to get user by email: {e}")
            return None
    
    def update_user_status(self, email: str, new_status: str, 
                          denial_reason: str = "", notes: str = "") -> bool:
        """
        Update user status (approve/deny/suspend)
        
        Args:
            email: User email
            new_status: New status (approved, denied, suspended)
            denial_reason: Reason for denial (if applicable)
            notes: Admin notes
        """
        if not self.enabled:
            return False
        
        try:
            self._rate_limit()
            all_rows = self.users_worksheet.get_all_values()
            
            for i, row in enumerate(all_rows[1:], start=2):  # Start from row 2 (skip header)
                if row[1] == email:  # Email column
                    # Prepare update data
                    row_num = i
                    current_status = row[3]
                    
                    # Build update dictionary
                    updates = {}
                    
                    # Update status
                    updates['D'] = new_status  # Status column
                    
                    # If approving
                    if new_status == self.STATUS_APPROVED and current_status != self.STATUS_APPROVED:
                        updates['H'] = self._get_timestamp()  # Approval Date
                    
                    # If denying
                    if new_status == self.STATUS_DENIED:
                        updates['I'] = denial_reason  # Denial Reason
                        # Increment reapply count
                        reapply_count = int(row[9]) if len(row) > 9 and row[9] else 0
                        updates['J'] = str(reapply_count + 1)  # Reapply Count
                    
                    # Update notes if provided
                    if notes:
                        updates['L'] = notes  # Notes column
                    
                    # Perform batch update
                    self._rate_limit()
                    for col, value in updates.items():
                        self.users_worksheet.update(f'{col}{row_num}', [[value]])
                        time.sleep(0.5)  # Small delay between updates
                    
                    print(f"[DEBUG] ✅ Updated user {email} status to {new_status}")
                    return True
            
            print(f"[WARNING] User {email} not found")
            return False
            
        except Exception as e:
            print(f"[ERROR] Failed to update user status: {e}")
            return False
    
    def get_pending_users(self) -> List[Dict[str, Any]]:
        """Get all users with pending status"""
        if not self.enabled:
            return []
        
        try:
            self._rate_limit()
            all_rows = self.users_worksheet.get_all_values()
            pending_users = []
            
            for row in all_rows[1:]:  # Skip header
                if row[3] == self.STATUS_PENDING:  # Status column
                    pending_users.append({
                        "user_id": row[0],
                        "email": row[1],
                        "name": row[2],
                        "signup_timestamp": row[4] if len(row) > 4 else "",
                        "added_by": row[10] if len(row) > 10 else ""
                    })
            
            return pending_users
            
        except Exception as e:
            print(f"[ERROR] Failed to get pending users: {e}")
            return []
    
    def update_user_login(self, email: str, is_first_login: bool = False) -> bool:
        """Update user login timestamps"""
        if not self.enabled:
            return False
        
        try:
            self._rate_limit()
            all_rows = self.users_worksheet.get_all_values()
            
            for i, row in enumerate(all_rows[1:], start=2):
                if row[1] == email:
                    row_num = i
                    timestamp = self._get_timestamp()
                    
                    # Update last login
                    self._rate_limit()
                    self.users_worksheet.update(f'G{row_num}', [[timestamp]])
                    
                    # Update first login if needed
                    if is_first_login or not row[5]:
                        self._rate_limit()
                        self.users_worksheet.update(f'F{row_num}', [[timestamp]])
                        
                        # Change status from approved to active
                        if row[3] == self.STATUS_APPROVED:
                            self._rate_limit()
                            self.users_worksheet.update(f'D{row_num}', [[self.STATUS_ACTIVE]])
                    
                    print(f"[DEBUG] ✅ Updated login timestamp for {email}")
                    return True
            
            return False
            
        except Exception as e:
            print(f"[ERROR] Failed to update user login: {e}")
            return False
    
    def get_config_value(self, setting: str, default: str = "") -> str:
        """Get configuration value from Admin Config sheet"""
        if not self.enabled:
            return default
        
        try:
            self._rate_limit()
            all_rows = self.config_worksheet.get_all_values()
            
            for row in all_rows[1:]:  # Skip header
                if row[0] == setting:
                    return row[1]
            
            return default
            
        except Exception as e:
            print(f"[ERROR] Failed to get config value: {e}")
            return default


# Helper function for easy integration
def get_user_manager() -> UserManagementSheets:
    """Get or create UserManagementSheets instance"""
    if 'user_manager' not in st.session_state:
        st.session_state.user_manager = UserManagementSheets()
    return st.session_state.user_manager
