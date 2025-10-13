# Google Sheets Quick Reference

## Column Index Reference

**CRITICAL: User ID Referential Integrity**
- Users sheet column A contains a 6-digit generated ID (e.g., "123456")
- Activity sheet column A contains the SAME 6-digit ID
- This creates a foreign key relationship: Activity.User_ID → Users.User_ID
- Use `get_user_id_by_email(email)` to fetch the correct ID before logging activity

---

### **Users Sheet (13 columns)**
```python
row[0]  = User ID           # A - 6 digit generated
row[1]  = Email             # B - Primary key
row[2]  = Name              # C - Full name
row[3]  = Status            # D - pending_approval/approved/denied
row[4]  = Signup Timestamp  # E - YYYY-MM-DD HH:MM:SS
row[5]  = First Login       # F - First login timestamp
row[6]  = Last Login        # G - Most recent login
row[7]  = Approval Date     # H - When approved by admin
row[8]  = Denial Reason     # I - Why denied (if applicable)
row[9]  = Reapply Count     # J - Number of reapplications
row[10] = Added By          # K - self_signup/admin/import
row[11] = Notes             # L - Admin notes
row[12] = Profile Pic       # M - URL from OAuth
```

### **Activity Sheet (13 columns)**
```python
row[0]  = User ID           # A - OAuth sub or generated ID
row[1]  = Email             # B - User email
row[2]  = Session ID        # C - UUID
row[3]  = Login Time        # D - YYYY-MM-DD HH:MM:SS
row[4]  = Logout Time       # E - YYYY-MM-DD HH:MM:SS
row[5]  = Status            # F - active/completed/closed
row[6]  = Duration (mins)   # G - Integer minutes
row[7]  = Page Views        # H - Count
row[8]  = Actions Taken     # I - Count
row[9]  = IP Address        # J - Client IP
row[10] = User Agent        # K - Browser info
row[11] = Last Activity     # L - Latest action timestamp
row[12] = Idle Timeout      # M - Seconds before timeout
```

### **Quotas Sheet (8 columns)**
```python
row[0] = Email              # A
row[1] = Session ID         # B
row[2] = Gemini Tokens      # C
row[3] = Google Ads Ops     # D
row[4] = Last Updated       # E
row[5] = Gemini Limit       # F
row[6] = Ads Limit          # G
row[7] = Status             # H
```

### **Gemini Usage Sheet (6 columns)**
```python
row[0] = User ID            # A
row[1] = Session ID         # B
row[2] = Operation Type     # C
row[3] = Tokens Used        # D
row[4] = Timestamp          # E
row[5] = Status             # F
```

---

## Common Operations

### **Find User by Email:**
```python
# Email is in column B (index 2 in Sheets API, index 1 in row array)
email_column = users_worksheet.col_values(2)  # Column B
user_emails = email_column[1:]  # Skip header
```

### **Find Session by Email:**
```python
# Email is in column B (index 1 in row array)
for i, row in enumerate(all_rows):
    if i == 0:  # Skip header
        continue
    if row[1] == email:  # Column B
        # Found session
```

### **Update Session Status:**
```python
# Status is in column F (row index 5)
# Update single cell
activity_worksheet.update(f'F{row_num}', [["completed"]])
```

### **Update Multiple Columns:**
```python
# Update Logout Time (E), Status (F), Duration (G), Last Activity (L)
activity_worksheet.update(f'E{row_num}', [[logout_time]])
activity_worksheet.update(f'F{row_num}', [[status]])
activity_worksheet.update(f'G{row_num}', [[str(duration_mins)]])
activity_worksheet.update(f'L{row_num}', [[last_activity]])
```

---

## Important Notes

### **Google Sheets API Indexing:**
- `col_values(1)` = Column A
- `col_values(2)` = Column B
- etc.

### **Python List Indexing:**
```python
row = ["A", "B", "C", "D"]
row[0] = "A"  # First column
row[1] = "B"  # Second column
```

### **Cell References:**
```python
# Single cell
worksheet.update('A1', [["value"]])

# Range
worksheet.update('A1:C1', [["val1", "val2", "val3"]])

# Row-based
worksheet.update(f'A{row_num}:C{row_num}', [[val1, val2, val3]])
```

### **Rate Limiting:**
Always call `_rate_limit()` before each Sheets API operation:
```python
self._rate_limit()
worksheet.append_row(data)
```

### **Duration Formats:**
- **OLD:** "05:30" (MM:SS string)
- **NEW:** "5" (integer minutes)
- **Conversion:** `duration_mins = duration_ms // 60000`

---

## Quick Debug

### **If data appears in wrong column:**

1. **Check header row:**
   ```python
   headers = worksheet.row_values(1)
   print(f"Headers: {headers}")
   print(f"Count: {len(headers)}")
   ```

2. **Check data row:**
   ```python
   row = worksheet.row_values(2)  # First data row
   print(f"Data: {row}")
   print(f"Count: {len(row)}")
   ```

3. **Compare:**
   - Headers count should match data count
   - Data should be in order matching headers

### **Common Mistakes:**

❌ Using `row[0]` for Email (should be `row[1]`)  
❌ Forgetting to skip header when iterating  
❌ Using `col_values(1)` for Email (should be `col_values(2)`)  
❌ Providing wrong number of values in row_data  
❌ Updating wrong column range  

✅ Always use column constants  
✅ Always document which column each value goes to  
✅ Always skip header row (i == 0) when iterating  
✅ Always verify row length before accessing indices  

---

## Status Values Reference

### **Users Sheet - Status (Column D):**
- `"pending_approval"` - Awaiting admin approval
- `"approved"` - Approved by admin, can use app
- `"denied"` - Denied by admin
- `"suspended"` - Temporarily blocked
- `"deleted"` - Marked for deletion

### **Activity Sheet - Status (Column F):**
- `"active"` - Session currently active
- `"completed"` - Normal session end
- `"closed"` - Orphaned session cleanup
- `"timeout"` - Idle timeout
- `"error"` - Session ended with error

### **Quotas Sheet - Status (Column H):**
- `"active"` - Currently tracking
- `"reset"` - Quotas were reset
- `"exceeded"` - Quota limit reached

---

## Example Usage in Code

### **Create New User:**
```python
user_data = {
    "email": "john@example.com",
    "first_name": "John",
    "last_name": "Doe", 
    "picture": "https://...",
    "locale": "en"
}

# Writes: [user_id, "john@example.com", "John Doe", "pending_approval", timestamp, "", "", "", "", "0", "self_signup", "", "https://..."]
gsheet_logger.store_user_if_new(user_data)
```

### **Log Session:**
```python
# Start
gsheet_logger.log_session_start(
    email="john@example.com",
    session_id=session_uuid,
    trace_id=trace_id,
    user_id=oauth_sub_id
)
# Writes: [oauth_sub_id, "john@example.com", session_uuid, login_time, "", "active", "0", "0", "0", "", "", login_time, ""]

# End
gsheet_logger.log_session_end(
    email="john@example.com",
    session_id=session_uuid,
    duration_ms=3600000  # 60 minutes
)
# Updates columns E, F, G, L
```

---

This reference guide should be kept up to date as you add more features! 📚
