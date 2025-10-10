# 📊 Session Tracking Improvements

## ✨ What's New

Two major improvements to session tracking:

1. **📏 Duration Format**: Changed from milliseconds to `mm:ss` format (more readable)
2. **🔒 Orphaned Session Handling**: Automatically closes sessions when users close browser without logging out

---

## 🎯 New Session Status System

### **Three Status Types**

| Status | When It Happens | What It Means |
|--------|----------------|---------------|
| **started** | User signs in | Session is active |
| **logged_out** | User clicks "Logout" button | Clean exit ✅ |
| **closed** | Browser closed without logout | Detected on next login ⚠️ |

---

## 📏 Duration Format Change

### **Before** ❌
```
Duration (ms)
45000
120000
3600000
```

### **After** ✅
```
Duration
00:45
02:00
60:00
```

**Format**: `mm:ss` (minutes:seconds)

---

## 🔒 How Orphaned Session Handling Works

### **Problem**
When users close their browser/tab without clicking "Logout":
- Session stays in "started" status
- No logout time recorded
- Duration not calculated
- User appears "online" forever ❌

### **Solution**
Automatic cleanup on next login:

```
1. User signs in (new session)
   ↓
2. System checks for orphaned sessions
   ↓
3. Finds sessions with:
   - Same email
   - Status = "started"
   - Empty logout_time
   ↓
4. Marks them as "closed"
   ↓
5. Calculates duration (login → now)
   ↓
6. Updates Google Sheet
```

---

## 📊 Google Sheets Schema (Updated)

### **Activity Tab**

| Column | Type | Example | Description |
|--------|------|---------|-------------|
| Email | String | user@example.com | User's email |
| Session ID | UUID | abc-123-def | Unique session ID |
| Trace ID | String | trace-abc123 | Request trace ID |
| Login Time | DateTime | 2025-10-10 14:30:00 | When logged in |
| Logout Time | DateTime | 2025-10-10 15:15:00 | When logged out |
| Tokens Used | Integer | 1500 | Total tokens |
| Operations | Integer | 25 | Operations count |
| **Duration** | **mm:ss** | **45:23** | **Session duration** ⭐ NEW |
| **Status** | **String** | **closed** | **Session status** ⭐ NEW |

---

## 🔄 Session Lifecycle Examples

### **Scenario 1: Clean Logout** ✅

```
14:30:00 | User signs in
         | Status: "started"
         | Duration: --
         ↓
14:35:00 | User works (tokens, operations tracked)
         ↓
14:45:00 | User clicks "Logout"
         | Status: "logged_out" ✅
         | Duration: "15:00"
```

**Google Sheet Entry**:
```
| user@example.com | session-123 | 14:30:00 | 14:45:00 | 1500 | 25 | 15:00 | logged_out |
```

---

### **Scenario 2: Browser Closed** ⚠️

```
14:30:00 | User signs in
         | Status: "started"
         | Duration: --
         ↓
14:35:00 | User works
         ↓
14:40:00 | User closes browser (no logout)
         | Status: "started" ⚠️
         | Duration: --
         ↓
15:00:00 | User signs in again (new session)
         | System detects orphaned session
         | Previous session updated:
         |   Status: "closed" ✅
         |   Logout Time: 15:00:00
         |   Duration: "30:00" (estimated)
```

**Google Sheet Entries**:
```
Before cleanup:
| user@example.com | session-123 | 14:30:00 | -- | 1500 | 25 | -- | started |

After cleanup (automatic):
| user@example.com | session-123 | 14:30:00 | 15:00:00 | 1500 | 25 | 30:00 | closed |
| user@example.com | session-456 | 15:00:00 | -- | 0 | 0 | -- | started |
```

---

### **Scenario 3: Multiple Orphaned Sessions** 🔍

```
Day 1 @ 10:00 | User signs in → closes browser
Day 2 @ 14:00 | User signs in → closes browser  
Day 3 @ 16:00 | User signs in again
              ↓
              System cleanup:
              - Closes Day 1 session (status: "closed")
              - Closes Day 2 session (status: "closed")
              - Starts Day 3 session (status: "started")
```

---

## 🔧 Technical Implementation

### **New Methods in `gsheet_writer.py`**

#### 1. **Duration Formatting**
```python
def _format_duration(self, duration_ms: int) -> str:
    """Convert milliseconds to mm:ss format"""
    total_seconds = duration_ms // 1000
    minutes = total_seconds // 60
    seconds = total_seconds % 60
    return f"{minutes:02d}:{seconds:02d}"
```

**Usage**:
```python
# Input: 45000 ms (45 seconds)
_format_duration(45000)  # Returns: "00:45"

# Input: 3600000 ms (1 hour)
_format_duration(3600000)  # Returns: "60:00"
```

---

#### 2. **Orphaned Session Cleanup**
```python
def close_orphaned_sessions(self, email: str) -> int:
    """Find and close orphaned sessions
    
    Returns: Number of sessions closed
    """
    # Find all sessions with:
    # - Same email
    # - Status = "started"
    # - Empty logout_time
    
    # For each found:
    # - Calculate duration (login → now)
    # - Set status = "closed"
    # - Update Google Sheet
```

**Called automatically** when user signs in:
```python
# In _initialize_session_tracking()
closed_count = self.gsheet_logger_safe.close_orphaned_sessions(user_email)
```

---

### **Updated Methods**

#### `log_session_end()`
```python
# Now accepts duration_ms parameter
log_session_end(
    email="user@example.com",
    session_id="abc-123",
    tokens_used=1500,
    operations=25,
    duration_ms=900000,  # ← Now used for calculation
    status="logged_out"  # ← Status matters now
)
```

---

## 📈 Usage Examples

### **Example 1: Check User Activity**

**Query Google Sheet**:
```sql
SELECT Email, Status, COUNT(*) as Count
FROM Activity
GROUP BY Email, Status
```

**Sample Output**:
```
user@example.com | logged_out | 45    ← Clean exits
user@example.com | closed     | 12    ← Browser closes
user@example.com | started    | 1     ← Currently active
```

---

### **Example 2: Calculate Average Session Duration**

**Query**:
```sql
SELECT Email, AVG(Duration) as Avg_Duration
FROM Activity
WHERE Status IN ('logged_out', 'closed')
GROUP BY Email
```

**Note**: Duration is in `mm:ss` format, you may need to convert for calculations.

---

### **Example 3: Find Active Sessions**

**Query**:
```sql
SELECT Email, Login_Time, Session_ID
FROM Activity
WHERE Status = 'started'
AND Logout_Time IS NULL
```

**Use Case**: Monitor currently active users

---

## ✅ Verification Checklist

After implementing these changes:

### **Test Case 1: Normal Logout**
- [ ] Sign in to app
- [ ] Perform some actions
- [ ] Click "Logout"
- [ ] Check Google Sheet:
  - [ ] Status = "logged_out"
  - [ ] Duration shows as `mm:ss` (e.g., "05:30")
  - [ ] Logout time is recorded

### **Test Case 2: Browser Close**
- [ ] Sign in to app
- [ ] Perform some actions
- [ ] Close browser/tab (no logout)
- [ ] Sign in again (new session)
- [ ] Check Google Sheet:
  - [ ] Previous session Status = "closed"
  - [ ] Previous session has logout time
  - [ ] Previous session has duration in `mm:ss`
  - [ ] New session Status = "started"

### **Test Case 3: Multiple Orphaned Sessions**
- [ ] Create 2-3 sessions by signing in and closing browser
- [ ] Sign in again
- [ ] Check Google Sheet:
  - [ ] All previous sessions marked as "closed"
  - [ ] All have proper logout times
  - [ ] All have durations in `mm:ss` format

---

## 🎯 Benefits

### **For You** 👨‍💻
- ✅ Accurate session tracking
- ✅ Know real user engagement time
- ✅ Distinguish between clean exits and unexpected closes
- ✅ No manual cleanup needed

### **For Users** 👥
- ✅ Seamless experience
- ✅ No need to remember to logout
- ✅ Sessions auto-close on next login

### **For Data Analysis** 📊
- ✅ Clean data (no stuck "started" sessions)
- ✅ Real duration metrics
- ✅ Better understanding of user behavior
- ✅ Can analyze dropout patterns

---

## 📊 Data Analysis Tips

### **Session Quality Metrics**

```python
# Pseudocode for analysis

clean_exits = count(status == "logged_out")
unexpected_closes = count(status == "closed")

exit_quality_ratio = clean_exits / (clean_exits + unexpected_closes)

# If ratio < 0.7 (70%), investigate:
# - Is logout button visible?
# - Are users finding what they need?
# - Is there confusion about how to exit?
```

### **Peak Usage Times**

```python
# Group by hour from Login_Time
# Count sessions
# Identify peak hours

peak_hours = group_by(Login_Time.hour).count()
```

### **Average Session Duration by Status**

```python
avg_duration_logout = average(duration WHERE status="logged_out")
avg_duration_closed = average(duration WHERE status="closed")

# Compare:
# - If closed sessions are much shorter → users leaving unsatisfied?
# - If similar → users just closing browser normally
```

---

## 🔄 Migration Notes

### **Existing Data**

**Old entries** (before this update):
- Duration in milliseconds (e.g., `45000`)
- Status might be missing or different
- No distinction between logout types

**New entries** (after this update):
- Duration in `mm:ss` (e.g., `00:45`)
- Clear status: `started`, `logged_out`, or `closed`
- Automatic cleanup of orphaned sessions

### **Backward Compatibility**

The system handles both formats:
- Old entries: Work as-is (but in old format)
- New entries: Use new format
- No data loss
- No manual migration needed ✅

---

## 💡 Pro Tips

1. **Monitor Status Distribution**
   - If too many "closed" vs "logged_out" → improve UX
   
2. **Set Alerts**
   - Email yourself if >10 sessions stay "started" for >24 hours
   - Indicates potential logging issues
   
3. **Regular Cleanup**
   - The system auto-cleans on login
   - For admin cleanup, run `close_orphaned_sessions()` for all users
   
4. **Duration Analysis**
   - Convert `mm:ss` to seconds for calculations:
     ```python
     def parse_duration(duration_str):
         m, s = duration_str.split(':')
         return int(m) * 60 + int(s)
     ```

---

## 🆘 Troubleshooting

### **Issue: Old sessions still showing "started"**

**Cause**: User hasn't logged in since update

**Fix**: Wait for next login (auto-cleanup) or manually run cleanup

---

### **Issue: Duration shows "00:00"**

**Cause**: Session ended immediately or duration calculation failed

**Check**:
- Login time exists?
- Logout time exists?
- Times are valid?

---

### **Issue: Too many "closed" sessions**

**Analysis**: This is actually **good data**!
- Shows real user behavior
- Most users close browsers without logout
- Not a bug ✅

**Action**: Use this data to improve UX

---

## 🎉 Summary

### **What Changed**

| Feature | Before | After |
|---------|--------|-------|
| Duration Format | `45000` (ms) | `00:45` (mm:ss) |
| Status Options | None | `started`, `logged_out`, `closed` |
| Orphaned Sessions | Stuck forever | Auto-closed on next login |
| Session Quality | Unknown | Trackable |

### **What You Get**

- ✅ Readable duration format
- ✅ Accurate session tracking
- ✅ Automatic cleanup
- ✅ Better analytics
- ✅ Real user behavior insights

---

**Implemented**: October 2025

**Affects**: All new sessions after deployment

**Backward Compatible**: Yes ✅

**Manual Action Required**: None (automatic) ✅

---

**Ready to deploy!** 🚀
