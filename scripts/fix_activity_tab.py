"""
Quick Fix: Update Activity Tab to 13-Column Schema
Adds missing columns without disrupting existing data
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import gspread
from oauth2client.service_account import ServiceAccountCredentials
import streamlit as st


def fix_activity_tab():
    """Add missing columns to Activity tab"""
    
    print("\n" + "="*60)
    print("🔧 FIXING ACTIVITY TAB SCHEMA")
    print("="*60)
    
    try:
        # Get credentials
        gsheet_config = st.secrets.get("google_sheets", {})
        sheet_id = gsheet_config.get("sheet_id")
        credentials_info = gsheet_config.get("credentials")
        
        if not sheet_id or not credentials_info:
            print("❌ Error: Google Sheets configuration missing")
            return False
        
        # Connect to sheet
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive"
        ]
        
        credentials = ServiceAccountCredentials.from_json_keyfile_dict(
            credentials_info, scope
        )
        
        client = gspread.authorize(credentials)
        sheet = client.open_by_key(sheet_id)
        
        # Get Activity worksheet
        print("\n📊 Checking Activity worksheet...")
        activity_ws = sheet.worksheet("Activity")
        
        # Get current headers
        current_headers = activity_ws.row_values(1)
        print(f"✅ Found Activity worksheet")
        print(f"   Current columns ({len(current_headers)}): {', '.join(current_headers)}")
        
        # Expected new headers (13 columns)
        new_headers = [
            "Session ID",      # 1
            "User ID",         # 2
            "Email",           # 3
            "Login Time",      # 4
            "Logout Time",     # 5
            "Status",          # 6
            "Duration (mins)", # 7
            "Page Views",      # 8
            "Actions Taken",   # 9
            "IP Address",      # 10
            "User Agent",      # 11
            "Last Activity",   # 12
            "Idle Timeout"     # 13
        ]
        
        # Check if already updated
        if current_headers == new_headers:
            print("\n✅ Activity tab already has 13 columns!")
            print("   No update needed.")
            return True
        
        print(f"\n🔄 Updating schema from {len(current_headers)} to {len(new_headers)} columns...")
        
        # Create mapping of existing columns
        old_to_new_mapping = {
            "Email": "Email",
            "Session ID": "Session ID",
            "Trace ID": None,  # Remove this
            "Login Time": "Login Time",
            "Logout Time": "Logout Time",
            "Tokens Used": None,  # Remove this
            "Operations": "Actions Taken",  # Rename
            "Duration (mm:ss)": "Duration (mins)",  # Keep but will need to convert format
            "Duration": "Duration (mins)",
            "Status": "Status"
        }
        
        # Get all existing data
        all_data = activity_ws.get_all_values()
        
        if len(all_data) <= 1:
            # No data, just update headers
            print("   No session data to migrate, updating headers only...")
            activity_ws.clear()
            activity_ws.update('A1:M1', [new_headers])
            print("✅ Headers updated successfully!")
            return True
        
        # Create backup
        import time
        backup_name = f"Activity_Backup_{int(time.time())}"
        print(f"\n📦 Creating backup worksheet: {backup_name}")
        
        backup_ws = sheet.duplicate_sheet(
            activity_ws.id,
            new_sheet_name=backup_name
        )
        print(f"✅ Backup created!")
        
        # Transform data
        print("\n🔧 Transforming session data...")
        new_data = [new_headers]
        
        for row_idx, row in enumerate(all_data[1:], start=2):
            new_row = [""] * len(new_headers)
            
            # Map existing columns to new positions
            for old_idx, old_col in enumerate(current_headers):
                if old_col in old_to_new_mapping:
                    new_col = old_to_new_mapping[old_col]
                    if new_col:  # Skip None (removed columns)
                        new_idx = new_headers.index(new_col)
                        value = row[old_idx] if old_idx < len(row) else ""
                        
                        # Special handling for duration conversion
                        if old_col in ["Duration (mm:ss)", "Duration"] and new_col == "Duration (mins)":
                            # Try to convert mm:ss to minutes
                            if value and ":" in value:
                                try:
                                    parts = value.split(":")
                                    minutes = int(parts[0])
                                    seconds = int(parts[1])
                                    total_mins = minutes + (seconds / 60)
                                    value = f"{total_mins:.1f}"
                                except:
                                    value = "0"
                        
                        new_row[new_idx] = value
            
            # Set User ID if we have email (lookup from Users tab later)
            email_idx = new_headers.index("Email")
            user_id_idx = new_headers.index("User ID")
            if new_row[email_idx] and not new_row[user_id_idx]:
                # Try to get User ID from Users tab
                try:
                    users_ws = sheet.worksheet("Users")
                    users_data = users_ws.get_all_values()
                    email_to_find = new_row[email_idx]
                    
                    for user_row in users_data[1:]:
                        if len(user_row) >= 2 and user_row[1] == email_to_find:
                            new_row[user_id_idx] = user_row[0]  # User ID is first column
                            break
                except:
                    pass  # If lookup fails, leave empty
            
            # Set defaults for new columns
            if not new_row[new_headers.index("Page Views")]:
                new_row[new_headers.index("Page Views")] = "0"
            
            if not new_row[new_headers.index("Actions Taken")] and "Operations" in current_headers:
                # Try to copy from Operations if it exists
                ops_idx = current_headers.index("Operations")
                if ops_idx < len(row):
                    new_row[new_headers.index("Actions Taken")] = row[ops_idx]
            
            if not new_row[new_headers.index("Idle Timeout")]:
                new_row[new_headers.index("Idle Timeout")] = "false"
            
            new_data.append(new_row)
        
        # Write new data
        print(f"📝 Writing updated data ({len(new_data)-1} sessions)...")
        activity_ws.clear()
        activity_ws.update('A1', new_data)
        
        print(f"\n✅ Successfully updated Activity tab!")
        print(f"   - Migrated {len(new_data)-1} session records")
        print(f"   - Backup saved as: {backup_name}")
        print(f"   - New schema: {len(new_headers)} columns")
        
        print("\n" + "="*60)
        print("✅ ACTIVITY TAB FIX COMPLETE!")
        print("="*60)
        print("\nActivity tab now has:")
        for i, header in enumerate(new_headers, 1):
            print(f"  {i}. {header}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error updating Activity tab: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main function"""
    try:
        success = fix_activity_tab()
        
        if success:
            print("\n🎉 Activity tab is now ready!")
            print("\nNext steps:")
            print("  1. Verify the Activity tab in Google Sheets has 13 columns")
            print("  2. Check the backup worksheet if you need to rollback")
            print("  3. Test adding a new session to verify it works")
        else:
            print("\n❌ Fix failed. Please check errors above.")
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Fix cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
