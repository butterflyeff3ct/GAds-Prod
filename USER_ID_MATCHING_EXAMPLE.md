# User ID Matching - Visual Example

## The Fix in Action

### **Scenario: John Doe Signs Up and Logs In**

---

## Step-by-Step Data Flow

### **STEP 1: User Signs Up (OAuth)**

**Code executed:**
```python
user_data = {
    "email": "john.doe@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "picture": "https://lh3.googleusercontent.com/a/..."
}

gsheet_logger.store_user_if_new(user_data)
# Generates User ID: "456789"
```

**Users Sheet - New Row Created:**
```
┌─────────┬──────────────────────┬──────────┬──────────────────┬─────────────────────┬─────────────┬────────────┬───────────────┬───────────────┬──────────────┬─────────────┬───────┬─────────────┐
│ User ID │ Email                │ Name     │ Status           │ Signup Timestamp    │ First Login │ Last Login │ Approval Date │ Denial Reason │ Reapply Count│ Added By    │ Notes │ Profile Pic │
├─────────┼──────────────────────┼──────────┼──────────────────┼─────────────────────┼─────────────┼────────────┼───────────────┼───────────────┼──────────────┼─────────────┼───────┼─────────────┤
│ 456789  │ john.doe@example.com │ John Doe │ pending_approval │ 2025-01-15 14:30:00 │             │            │               │               │ 0            │ self_signup │       │ https://... │
└─────────┴──────────────────────┴──────────┴──────────────────┴─────────────────────┴─────────────┴────────────┴───────────────┴───────────────┴──────────────┴─────────────┴───────┴─────────────┘
```

**Key Points:**
- ✅ User ID **456789** generated and stored in column A
- ✅ Status starts as "pending_approval"
- ✅ First Login and Last Login are empty (not logged in yet)

---

### **STEP 2: Admin Approves User**

**Admin action in admin dashboard:**
```python
# Admin clicks "Approve" button
# Updates Users sheet row
```

**Users Sheet - Row Updated:**
```
┌─────────┬──────────────────────┬──────────┬──────────┬─────────────────────┬─────────────┬────────────┬─────────────────────┬───────────────┬──────────────┬─────────────┬───────┬─────────────┐
│ User ID │ Email                │ Name     │ Status   │ Signup Timestamp    │ First Login │ Last Login │ Approval Date       │ Denial Reason │ Reapply Count│ Added By    │ Notes │ Profile Pic │
├─────────┼──────────────────────┼──────────┼──────────┼─────────────────────┼─────────────┼────────────┼─────────────────────┼───────────────┼──────────────┼─────────────┼───────┼─────────────┤
│ 456789  │ john.doe@example.com │ John Doe │ approved │ 2025-01-15 14:30:00 │             │            │ 2025-01-16 09:00:00 │               │ 0            │ self_signup │       │ https://... │
└─────────┴──────────────────────┴──────────┴──────────┴─────────────────────┴─────────────┴────────────┴─────────────────────┴───────────────┴──────────────┴─────────────┴───────┴─────────────┘
```

**Changes:**
- Status: "pending_approval" → "approved"
- Approval Date populated

---

### **STEP 3: User Logs In (First Time)**

**Code executed:**
```python
# 1. Store user if new (already exists, skips)
is_new_user = gsheet_logger.store_user_if_new(user_data)  # False

# 2. Update login timestamps
gsheet_logger.update_user_login_timestamps(
    email="john.doe@example.com",
    is_first_login=True  # New user's first login
)

# 3. Get User ID from Users sheet
user_id = gsheet_logger.get_user_id_by_email("john.doe@example.com")
# Returns: "456789"

# 4. Log session with matching User ID
gsheet_logger.log_session_start(
    email="john.doe@example.com",
    session_id="uuid-abc-123",
    user_id="456789"  # ← Same ID from Users sheet!
)
```

**Users Sheet - Login Timestamps Updated:**
```
┌─────────┬──────────────────────┬──────────┬──────────┬─────────────────────┬─────────────────────┬─────────────────────┬─────────────────────┬───────────────┬──────────────┬─────────────┬───────┬─────────────┐
│ User ID │ Email                │ Name     │ Status   │ Signup Timestamp    │ First Login         │ Last Login          │ Approval Date       │ Denial Reason │ Reapply Count│ Added By    │ Notes │ Profile Pic │
├─────────┼──────────────────────┼──────────┼──────────┼─────────────────────┼─────────────────────┼─────────────────────┼─────────────────────┼───────────────┼──────────────┼─────────────┼───────┼─────────────┤
│ 456789  │ john.doe@example.com │ John Doe │ approved │ 2025-01-15 14:30:00 │ 2025-01-16 10:00:00 │ 2025-01-16 10:00:00 │ 2025-01-16 09:00:00 │               │ 0            │ self_signup │       │ https://... │
└─────────┴──────────────────────┴──────────┴──────────┴─────────────────────┴─────────────────────┴─────────────────────┴─────────────────────┴───────────────┴──────────────┴─────────────┴───────┴─────────────┘
```

**Activity Sheet - New Session Row Created:**
```
┌─────────┬──────────────────────┬──────────────┬─────────────────────┬─────────────┬───────────┬────────────────┬────────────┬───────────────┬────────────┬────────────┬─────────────────────┬──────────────┐
│ User ID │ Email                │ Session ID   │ Login Time          │ Logout Time │ Status    │ Duration (mins)│ Page Views │ Actions Taken │ IP Address │ User Agent │ Last Activity       │ Idle Timeout │
├─────────┼──────────────────────┼──────────────┼─────────────────────┼─────────────┼───────────┼────────────────┼────────────┼───────────────┼────────────┼────────────┼─────────────────────┼──────────────┤
│ 456789  │ john.doe@example.com │ uuid-abc-123 │ 2025-01-16 10:00:00 │             │ active    │ 0              │ 0          │ 0             │            │            │ 2025-01-16 10:00:00 │              │
└─────────┴──────────────────────┴──────────────┴─────────────────────┴─────────────┴───────────┴────────────────┴────────────┴───────────────┴────────────┴────────────┴─────────────────────┴──────────────┘
```

**🎯 CRITICAL:** User ID **456789** appears in **BOTH** sheets! ✅

---

### **STEP 4: User Logs Out**

**Code executed:**
```python
gsheet_logger.log_session_end(
    email="john.doe@example.com",
    session_id="uuid-abc-123",
    duration_ms=3600000  # 60 minutes
)
```

**Activity Sheet - Session Row Updated:**
```
┌─────────┬──────────────────────┬──────────────┬─────────────────────┬─────────────────────┬───────────┬────────────────┬────────────┬───────────────┬────────────┬────────────┬─────────────────────┬──────────────┐
│ User ID │ Email                │ Session ID   │ Login Time          │ Logout Time         │ Status    │ Duration (mins)│ Page Views │ Actions Taken │ IP Address │ User Agent │ Last Activity       │ Idle Timeout │
├─────────┼──────────────────────┼──────────────┼─────────────────────┼─────────────────────┼───────────┼────────────────┼────────────┼───────────────┼────────────┼────────────┼─────────────────────┼──────────────┤
│ 456789  │ john.doe@example.com │ uuid-abc-123 │ 2025-01-16 10:00:00 │ 2025-01-16 11:00:00 │ completed │ 60             │ 0          │ 0             │            │            │ 2025-01-16 11:00:00 │              │
└─────────┴──────────────────────┴──────────────┴─────────────────────┴─────────────────────┴───────────┴────────────────┴────────────┴───────────────┴────────────┴────────────┴─────────────────────┴──────────────┘
```

**Updates:** Columns E, F, G, L updated

---

### **STEP 5: User Returns Next Day**

**Users Sheet - Last Login Updated:**
```
┌─────────┬──────────────────────┬──────────┬──────────┬─────────────────────┬─────────────────────┬─────────────────────┬─────────────────────┬───────────────┬──────────────┬─────────────┬───────┬─────────────┐
│ User ID │ Email                │ Name     │ Status   │ Signup Timestamp    │ First Login         │ Last Login          │ Approval Date       │ Denial Reason │ Reapply Count│ Added By    │ Notes │ Profile Pic │
├─────────┼──────────────────────┼──────────┼──────────┼─────────────────────┼─────────────────────┼─────────────────────┼─────────────────────┼───────────────┼──────────────┼─────────────┼───────┼─────────────┤
│ 456789  │ john.doe@example.com │ John Doe │ approved │ 2025-01-15 14:30:00 │ 2025-01-16 10:00:00 │ 2025-01-17 14:00:00 │ 2025-01-16 09:00:00 │               │ 0            │ self_signup │       │ https://... │
└─────────┴──────────────────────┴──────────┴──────────┴─────────────────────┴─────────────────────┴─────────────────────┴─────────────────────┴───────────────┴──────────────┴─────────────┴───────┴─────────────┘
```

**Activity Sheet - Second Session Logged:**
```
┌─────────┬──────────────────────┬──────────────┬─────────────────────┬─────────────────────┬───────────┬────────────────┬────────────┬───────────────┬────────────┬────────────┬─────────────────────┬──────────────┐
│ User ID │ Email                │ Session ID   │ Login Time          │ Logout Time         │ Status    │ Duration (mins)│ Page Views │ Actions Taken │ IP Address │ User Agent │ Last Activity       │ Idle Timeout │
├─────────┼──────────────────────┼──────────────┼─────────────────────┼─────────────────────┼───────────┼────────────────┼────────────┼───────────────┼────────────┼────────────┼─────────────────────┼──────────────┤
│ 456789  │ john.doe@example.com │ uuid-abc-123 │ 2025-01-16 10:00:00 │ 2025-01-16 11:00:00 │ completed │ 60             │ 0          │ 0             │            │            │ 2025-01-16 11:00:00 │              │
├─────────┼──────────────────────┼──────────────┼─────────────────────┼─────────────────────┼───────────┼────────────────┼────────────┼───────────────┼────────────┼────────────┼─────────────────────┼──────────────┤
│ 456789  │ john.doe@example.com │ uuid-def-456 │ 2025-01-17 14:00:00 │                     │ active    │ 0              │ 0          │ 0             │            │            │ 2025-01-17 14:00:00 │              │
└─────────┴──────────────────────┴──────────────┴─────────────────────┴─────────────────────┴───────────┴────────────────┴────────────┴───────────────┴────────────┴────────────┴─────────────────────┴──────────────┘
```

**🎯 Notice:** User ID **456789** appears in:
- ✅ Column A of Users sheet (generated once)
- ✅ Column A of Activity sheet (first session)
- ✅ Column A of Activity sheet (second session)

**All the same User ID!** This is referential integrity! 🎉

---

## Why This Matters

### **Before Fix (BROKEN):**

**Users Sheet:**
```
User ID: 456789  ← 6-digit generated ID
```

**Activity Sheet:**
```
User ID: 108234567890123456789  ← OAuth sub ID (different!)
```

**Problem:**
- ❌ Cannot join sheets on User ID
- ❌ Cannot filter Activity by User ID from Users sheet
- ❌ Cannot count sessions per user
- ❌ No relationship between tables

---

### **After Fix (WORKING):**

**Users Sheet:**
```
User ID: 456789  ← 6-digit generated ID
```

**Activity Sheet:**
```
User ID: 456789  ← SAME 6-digit ID!
```

**Benefits:**
- ✅ Can join sheets on User ID
- ✅ Can filter all sessions for a user
- ✅ Can count sessions, duration, activities per user
- ✅ Proper foreign key relationship

---

## Real-World Example Queries

Now that User IDs match, you can do powerful reporting:

### **Query 1: Get All Sessions for User 456789**

**Google Sheets Formula:**
```
=FILTER(Activity!A:M, Activity!A:A = "456789")
```

**Result:**
```
All sessions where User ID = 456789
- Session 1: 2025-01-16 (60 mins)
- Session 2: 2025-01-17 (active)
```

---

### **Query 2: User Summary Report**

**Google Sheets Formula:**
```
=QUERY(Activity!A:M, 
  "SELECT A, B, COUNT(C), AVG(G), MAX(L) 
   WHERE A = '456789' 
   GROUP BY A, B")
```

**Result:**
```
User ID | Email                | Sessions | Avg Duration | Last Active
456789  | john.doe@example.com | 2        | 30 mins      | 2025-01-17 14:00:00
```

---

### **Query 3: Most Active Users**

**Google Sheets Formula:**
```
=QUERY(Activity!A:M, 
  "SELECT A, COUNT(C) as Sessions, SUM(G) as TotalMins 
   GROUP BY A 
   ORDER BY Sessions DESC 
   LIMIT 10")
```

**Result:**
```
User ID | Sessions | Total Minutes
456789  | 2        | 60
123456  | 5        | 240
789012  | 3        | 180
```

---

### **Query 4: Join User Info with Activity**

**In Google Sheets, you can now VLOOKUP:**
```
=VLOOKUP(A2, Users!A:C, 3, FALSE)
```

**Example:**
```
From Activity sheet row:
User ID: 456789

Lookup in Users sheet:
Returns: "John Doe"
```

**Build combined report:**
```
Session ID    | User ID | User Name | Duration | Status
uuid-abc-123  | 456789  | John Doe  | 60 mins  | completed
uuid-def-456  | 456789  | John Doe  | active   | active
```

---

## Comparison: Before vs After

### **Users Sheet Column A:**

| Before | After |
|--------|-------|
| 456789 | 456789 |
| ✅ Correct | ✅ Correct |

### **Activity Sheet Column A:**

| Before | After |
|--------|-------|
| 108234567890... (OAuth sub) | 456789 (matches Users!) |
| ❌ Wrong - OAuth ID | ✅ Correct - 6-digit ID |

---

## Code Implementation Details

### **The Lookup Function:**

```python
def get_user_id_by_email(self, email: str) -> str:
    """Fetch 6-digit User ID from Users sheet"""
    
    all_rows = users_worksheet.get_all_values()
    
    for row in all_rows[1:]:  # Skip header
        if row[1] == email:  # Column B = Email
            return row[0]     # Column A = User ID
    
    return ""  # Not found
```

**Example:**
```python
user_id = get_user_id_by_email("john.doe@example.com")
# Reads Users sheet, finds email in column B
# Returns User ID from column A: "456789"
```

### **The Session Logging:**

```python
# OLD (BROKEN):
user_id = user_info.get("sub")  # OAuth sub ID (long string)
log_session_start(..., user_id="108234567890...")

# NEW (FIXED):
user_id = get_user_id_by_email(email)  # 6-digit ID from Users sheet
log_session_start(..., user_id="456789")
```

---

## Visual Verification

### **In Your Google Sheet:**

**1. Open Users tab, find a user:**
```
Row 2: User ID = 456789, Email = john.doe@example.com
```

**2. Open Activity tab, filter by User ID:**
```
All rows with User ID = 456789
Should show all sessions for john.doe@example.com
```

**3. Verify the match:**
```
Users.A2 = "456789"
Activity.A2 = "456789"
Activity.A3 = "456789"
...

All sessions for the same user have the SAME User ID! ✅
```

---

## Testing Instructions

After deployment, test with a real user:

### **Test 1: New User**
```
1. New user signs up
2. Check Users sheet → Note User ID (e.g., "789012")
3. Admin approves user
4. User logs in
5. Check Activity sheet → User ID should be "789012" (same!)
```

### **Test 2: Existing User**
```
1. Existing user logs in again
2. Check their User ID in Users sheet (e.g., "456789")
3. Check new Activity row → Should have "456789"
4. All their Activity rows should have "456789"
```

### **Test 3: Multiple Sessions**
```
1. User logs in/out 3 times
2. Users sheet → Still has one row (User ID = "456789")
3. Activity sheet → Has 3 rows, all with User ID = "456789"
4. Can filter/query by this ID to see all sessions
```

---

## Success Indicators

After deployment, you should see:

✅ Same User ID appears in both Users and Activity sheets  
✅ User ID is always 6 digits (e.g., "456789")  
✅ Can filter Activity by User ID to get all user sessions  
✅ First Login only populated once per user  
✅ Last Login updates on every login  
✅ All 13 columns populated correctly  
✅ No OAuth sub IDs in Activity sheet  

---

## Summary

**What was broken:**
- Activity sheet used OAuth sub ID (long string)
- Users sheet had 6-digit ID
- IDs didn't match → couldn't relate data

**What is fixed:**
- Activity sheet now uses 6-digit ID from Users sheet
- Code automatically looks up the correct ID
- Perfect referential integrity
- Can now join/query data like a real database

**How it works:**
1. User signs up → 6-digit ID generated and stored in Users sheet
2. User logs in → Code fetches that same 6-digit ID
3. Session logged → Uses the fetched 6-digit ID
4. Result → Same ID in both sheets!

Your Google Sheets now works like a **proper relational database**! 🎉
