# Google Sheets Column Mapping - CRITICAL UPDATE

## ⚠️ BREAKING CHANGE ALERT

Your actual Google Sheets structure is **completely different** from what the code was designed for. This caused all data to be written to wrong columns.

---

## Actual Sheet Structures (From Your Screenshots)

### **Users Tab** (13 columns)
```
A: User ID
B: Email  
C: Name
D: Status
E: Signup Timestamp
F: First Login
G: Last Login
H: Approval Date
I: Denial Reason
J: Reapply Count
K: Added By
L: Notes
M: Profile Pic
```

### **Activity Tab** (13 columns)
```
A: User ID
B: Email
C: Session ID
D: Login Time
E: Logout Time
F: Status
G: Duration (mins)
H: Page Views
I: Actions Taken
J: IP Address
K: User Agent
L: Last Activity
M: Idle Timeout
```

### **Quotas Tab** (8 columns - unchanged)
```
A: Email
B: Session ID
C: Gemini Tokens
D: Google Ads Ops
E: Last Updated
F: Gemini Limit
G: Ads Limit
H: Status
```

### **Gemini Usage Tab** (6 columns - unchanged)
```
A: User ID
B: Session ID
C: Operation Type
D: Tokens Used
E: Timestamp
F: Status
```

---

## What Was Fixed

### ✅ **Users Sheet**
- **Before:** Writing 7 columns (Email, First Name, Last Name, etc.)
- **After:** Writing 13 columns matching your approval workflow
- **New fields:** Status, Signup Timestamp, Approval Date, Denial Reason, Reapply Count, Added By, Notes

### ✅ **Activity Sheet**
- **Before:** Writing 9 columns (Email, Session ID, Trace ID, Tokens, Ops, Duration, Status)
- **After:** Writing 13 columns matching your tracking system
- **New fields:** User ID, Page Views, Actions Taken, IP Address, User Agent, Last Activity, Idle Timeout
- **Changed:** Duration now in minutes (was MM:SS format)

### ⚠️ **Still Need to Fix:**
These methods still need updating to read from correct columns:
- `get_session_metrics()`
- `update_session_metrics()` 
- `close_orphaned_sessions()`
- `get_user_sessions()`

---

## Testing Checklist

After deploying:

### **Test Users Tab:**
1. New user signs up
2. Check Users sheet row has all 13 values
3. Verify: User ID in column A, Email in column B, Status="pending_approval" in column D

### **Test Activity Tab:**
1. User logs in
2. Check Activity sheet row has all 13 values
3. Verify: User ID in column A, Email in column B, Status="active" in column F
4. User logs out
5. Verify: Logout Time in column E, Duration in minutes in column G

### **Known Issues:**
- Page Views, Actions Taken, IP Address, User Agent columns will be empty (not yet tracked)
- Old data before this fix will have misaligned columns
- Need to add methods to update Page Views and Actions count

---

## Data Migration

### **Option 1: Fresh Start (Recommended)**
```
1. Rename current sheets to: Users_OLD, Activity_OLD
2. Delete rows 2+ (keep headers only)  
3. Let app create fresh data
```

### **Option 2: Partial Fix**
```
1. Keep existing data
2. Headers will auto-correct on next run
3. New data will align properly
4. Old data may remain misaligned
```

### **Option 3: Manual Cleanup**
```
1. Export sheets to CSV
2. Delete all data rows (keep headers)
3. Manually map old data to new columns
4. Re-import
```

---

## Next Steps

1. **Commit current fixes**
2. **Test with new user signup**
3. **Update remaining read methods**
4. **Add tracking for missing fields:**
   - Page Views counter
   - Actions Taken counter
   - IP Address capture
   - User Agent capture
   - Idle Timeout tracking

5. **Add admin methods:**
   - Approve user (update Status, Approval Date)
   - Deny user (update Status, Denial Reason)
   - View pending approvals

---

## Code Changes Summary

### **Updated:**
- `USERS_COLUMNS` constant - 13 columns
- `ACTIVITY_COLUMNS` constant - 13 columns
- `store_user_if_new()` - writes all 13 user columns
- `log_session_start()` - writes all 13 activity columns  
- `log_session_end()` - updates correct columns (E, F, G, L)

### **Still Using Old Structure:**
- `get_session_metrics()` - reads from wrong columns
- `update_session_metrics()` - updates wrong columns
- `close_orphaned_sessions()` - reads/updates wrong columns
- `get_user_sessions()` - parses wrong columns

---

## Critical Notes

⚠️ **Duration Format Changed:**
- Old: "MM:SS" format (e.g., "05:30")
- New: Minutes as integer (e.g., "5")
- Reason: Matches your sheet structure

⚠️ **User ID Now Required:**
- Old: User ID was last column
- New: User ID is first column
- `log_session_start()` now takes optional `user_id` parameter

⚠️ **Status Values:**
- Users: "pending_approval", "approved", "denied"
- Activity: "active", "completed", "closed", "timeout"

---

## Deployment Command

```powershell
git add utils/gsheet_writer.py
git add GOOGLE_SHEETS_COLUMN_MAPPING.md
git commit -m "CRITICAL: Fix Google Sheets to match actual structure

- Update Users tab to 13 columns with approval workflow
- Update Activity tab to 13 columns with detailed tracking
- Fix store_user_if_new to write User ID in column A
- Fix log_session_start/end to match actual columns
- Change duration from MM:SS to minutes (integer)
- Add user_id parameter to log_session_start

BREAKING CHANGE: Old data will be misaligned
Recommend fresh start or manual migration"

git push origin main
```

---

Your Google Sheets integration should now write to the correct columns! 🎉
