"""
Setup Script for Enhanced Google Sheets User Management
Run this to initialize or migrate your Google Sheets to the new schema
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.user_management_sheets import UserManagementSheets
import gspread
from oauth2client.service_account import ServiceAccountCredentials


class SheetsSetup:
    """Setup and migration utility for Google Sheets"""
    
    def __init__(self):
        """Initialize setup utility"""
        # Get credentials from environment or secrets
        try:
            import streamlit as st
            gsheet_config = st.secrets.get("google_sheets", {})
        except:
            print("❌ Error: Cannot load Streamlit secrets")
            print("Make sure you have .streamlit/secrets.toml configured")
            sys.exit(1)
        
        self.sheet_id = gsheet_config.get("sheet_id")
        credentials_info = gsheet_config.get("credentials")
        
        if not self.sheet_id or not credentials_info:
            print("❌ Error: Google Sheets configuration missing")
            print("Check your .streamlit/secrets.toml file")
            sys.exit(1)
        
        # Set up credentials
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive"
        ]
        
        credentials = ServiceAccountCredentials.from_json_keyfile_dict(
            credentials_info, scope
        )
        
        self.client = gspread.authorize(credentials)
        self.sheet = self.client.open_by_key(self.sheet_id)
    
    def check_existing_schema(self):
        """Check current sheet schema"""
        print("\n📊 Checking Existing Schema...")
        print("-" * 60)
        
        try:
            # Check Users worksheet
            users_ws = self.sheet.worksheet("Users")
            users_headers = users_ws.row_values(1)
            print(f"✅ Users worksheet found")
            print(f"   Current columns ({len(users_headers)}): {', '.join(users_headers)}")
            
            # Check Activity worksheet
            activity_ws = self.sheet.worksheet("Activity")
            activity_headers = activity_ws.row_values(1)
            print(f"✅ Activity worksheet found")
            print(f"   Current columns ({len(activity_headers)}): {', '.join(activity_headers)}")
            
            # Check Admin Config worksheet
            try:
                config_ws = self.sheet.worksheet("Admin Config")
                config_headers = config_ws.row_values(1)
                print(f"✅ Admin Config worksheet found")
                print(f"   Current columns ({len(config_headers)}): {', '.join(config_headers)}")
            except gspread.WorksheetNotFound:
                print(f"⚠️  Admin Config worksheet NOT found - will be created")
            
            print()
            return True
            
        except gspread.WorksheetNotFound as e:
            print(f"⚠️  Some worksheets missing: {e}")
            return False
        except Exception as e:
            print(f"❌ Error checking schema: {e}")
            return False
    
    def migrate_existing_data(self):
        """Migrate existing Users data to new schema (non-destructive)"""
        print("\n🔄 Migrating Existing Data...")
        print("-" * 60)
        
        try:
            users_ws = self.sheet.worksheet("Users")
            current_headers = users_ws.row_values(1)
            
            # New enhanced headers
            new_headers = [
                "User ID", "Email", "Name", "Status", "Signup Timestamp",
                "First Login", "Last Login", "Approval Date", "Denial Reason",
                "Reapply Count", "Added By", "Notes", "Profile Pic", "Locale"
            ]
            
            # Check if migration needed
            if current_headers == new_headers:
                print("✅ Schema already up to date!")
                return True
            
            print(f"Current headers: {len(current_headers)} columns")
            print(f"New headers: {len(new_headers)} columns")
            
            # Get all existing data
            all_data = users_ws.get_all_values()
            
            if len(all_data) <= 1:
                # No data to migrate, just update headers
                print("ℹ️  No user data to migrate, updating headers only...")
                users_ws.update('A1:N1', [new_headers])
                print("✅ Headers updated successfully!")
                return True
            
            # Create backup worksheet
            import time
            backup_name = f"Users_Backup_{int(time.time())}"
            print(f"📦 Creating backup worksheet: {backup_name}")
            
            backup_ws = self.sheet.duplicate_sheet(
                users_ws.id,
                new_sheet_name=backup_name
            )
            print(f"✅ Backup created!")
            
            # Map old columns to new columns
            old_to_new_mapping = {
                "Email": "Email",
                "First Name": "Name",  # Combine first + last if they exist
                "Last Name": "Name",
                "First Login": "First Login",
                "Profile Pic": "Profile Pic",
                "Locale": "Locale",
                "User ID": "User ID"
            }
            
            # Build new data structure
            print("🔧 Transforming data...")
            new_data = [new_headers]
            
            for row in all_data[1:]:  # Skip header row
                new_row = [""] * len(new_headers)
                
                # Map existing columns
                for old_idx, old_col in enumerate(current_headers):
                    if old_col in old_to_new_mapping:
                        new_col = old_to_new_mapping[old_col]
                        new_idx = new_headers.index(new_col)
                        
                        # Special handling for Name (combine first + last)
                        if old_col == "First Name":
                            new_row[new_idx] = row[old_idx] if old_idx < len(row) else ""
                        elif old_col == "Last Name":
                            name_idx = new_headers.index("Name")
                            existing_name = new_row[name_idx]
                            last_name = row[old_idx] if old_idx < len(row) else ""
                            new_row[name_idx] = f"{existing_name} {last_name}".strip()
                        else:
                            new_row[new_idx] = row[old_idx] if old_idx < len(row) else ""
                
                # Set default values for new columns
                user_id_idx = new_headers.index("User ID")
                if not new_row[user_id_idx]:
                    # Generate user ID if missing
                    import random
                    new_row[user_id_idx] = str(random.randint(100000, 999999))
                
                status_idx = new_headers.index("Status")
                new_row[status_idx] = "active"  # Existing users are active
                
                signup_idx = new_headers.index("Signup Timestamp")
                first_login_idx = new_headers.index("First Login")
                if new_row[first_login_idx]:
                    new_row[signup_idx] = new_row[first_login_idx]  # Use first login as signup
                
                added_by_idx = new_headers.index("Added By")
                new_row[added_by_idx] = "migrated"  # Mark as migrated
                
                reapply_idx = new_headers.index("Reapply Count")
                new_row[reapply_idx] = "0"
                
                new_data.append(new_row)
            
            # Clear existing data and write new structure
            print("📝 Writing migrated data...")
            users_ws.clear()
            users_ws.update('A1', new_data)
            
            print(f"✅ Successfully migrated {len(new_data)-1} user records!")
            print(f"   Backup saved as: {backup_name}")
            
            return True
            
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def initialize_admin_config(self):
        """Initialize or update Admin Config worksheet"""
        print("\n⚙️  Setting Up Admin Config...")
        print("-" * 60)
        
        try:
            # Check if Admin Config exists
            try:
                config_ws = self.sheet.worksheet("Admin Config")
                print("✅ Admin Config worksheet already exists")
            except gspread.WorksheetNotFound:
                print("📝 Creating Admin Config worksheet...")
                config_ws = self.sheet.add_worksheet(
                    title="Admin Config", rows=100, cols=4
                )
                
                # Add headers
                headers = ["Setting", "Value", "Description", "Last Updated"]
                config_ws.append_row(headers)
                
                # Add default configurations
                from datetime import datetime
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                default_configs = [
                    ["auto_approve_enabled", "false", "Auto-approve new signups", timestamp],
                    ["max_reapply_count", "3", "Maximum times user can reapply after denial", timestamp],
                    ["session_timeout_mins", "30", "Session timeout in minutes", timestamp],
                    ["require_admin_review", "true", "Require manual admin review for signups", timestamp],
                    ["max_daily_signups", "100", "Maximum daily signups allowed", timestamp],
                    ["notification_email", "", "Email for admin notifications", timestamp]
                ]
                
                for config in default_configs:
                    config_ws.append_row(config)
                
                print(f"✅ Admin Config initialized with {len(default_configs)} settings")
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to initialize Admin Config: {e}")
            return False
    
    def add_sample_data(self):
        """Add sample data for testing"""
        print("\n🎭 Adding Sample Data...")
        print("-" * 60)
        
        response = input("Do you want to add sample test users? (y/n): ")
        
        if response.lower() != 'y':
            print("Skipping sample data...")
            return True
        
        try:
            manager = UserManagementSheets(sheet_id=self.sheet_id)
            
            sample_users = [
                {
                    "email": "john.doe@example.com",
                    "name": "John Doe",
                    "added_by": "admin@company.com"  # Pre-approved
                },
                {
                    "email": "jane.smith@example.com",
                    "name": "Jane Smith",
                    "added_by": "self"  # Pending approval
                },
                {
                    "email": "test.user@example.com",
                    "name": "Test User",
                    "added_by": "self"  # Pending approval
                }
            ]
            
            print("\nAdding sample users...")
            for user in sample_users:
                result = manager.add_user_signup(**user)
                if result["success"]:
                    print(f"✅ Added: {user['email']} (Status: {result['status']})")
                else:
                    print(f"⚠️  Skipped: {user['email']} ({result.get('error', 'Unknown error')})")
            
            print(f"\n✅ Sample data added successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Failed to add sample data: {e}")
            return False
    
    def run_full_setup(self):
        """Run complete setup process"""
        print("\n" + "="*60)
        print("🚀 GOOGLE SHEETS SETUP FOR USER MANAGEMENT")
        print("="*60)
        
        # Step 1: Check existing schema
        if not self.check_existing_schema():
            print("\n❌ Setup cannot continue. Please check your Google Sheets configuration.")
            return False
        
        # Step 2: Migrate existing data
        if not self.migrate_existing_data():
            print("\n❌ Migration failed. Please check errors above.")
            return False
        
        # Step 3: Initialize Admin Config
        if not self.initialize_admin_config():
            print("\n❌ Admin Config setup failed.")
            return False
        
        # Step 4: Add sample data (optional)
        self.add_sample_data()
        
        print("\n" + "="*60)
        print("✅ SETUP COMPLETE!")
        print("="*60)
        print("\nYour Google Sheets is now ready with:")
        print("  ✓ Enhanced Users schema (14 columns)")
        print("  ✓ Enhanced Activity schema (13 columns)")
        print("  ✓ Admin Config worksheet")
        print("\nNext steps:")
        print("  1. Test the new user management features")
        print("  2. Create an admin interface for approvals")
        print("  3. Implement signup/login flow")
        print()
        
        return True


def main():
    """Main setup function"""
    try:
        setup = SheetsSetup()
        setup.run_full_setup()
    except KeyboardInterrupt:
        print("\n\n⚠️  Setup cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Setup failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
