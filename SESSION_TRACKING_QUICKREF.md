# ⚡ Session Tracking Quick Reference

## 🎯 Quick Summary

**Duration Format**: Now shows as `mm:ss` (e.g., `15:30` = 15 minutes 30 seconds)

**Session Statuses**:
- `started` → User is currently active
- `logged_out` → User clicked logout button ✅
- `closed` → User closed browser without logout ⚠️

**Auto-Cleanup**: Orphaned sessions automatically close on next user login ✅

---

## 📊 Google Sheets Column Schema

```
| Email | Session ID | Trace ID | Login Time | Logout Time | Tokens | Operations | Duration | Status |
|-------|------------|----------|------------|-------------|--------|------------|----------|--------|
| Type  | UUID       | String   | DateTime   | DateTime    | Int    | Int        | mm:ss    | String |
```

---

## 🔄 Session Flow

### **Normal Flow** (logged_out)
```
Sign In → Work → Click Logout → Duration: 15:30, Status: logged_out ✅
```

### **Browser Close** (closed)
```
Sign In → Work → Close Browser → Next Login: Duration: 30:45, Status: closed ⚠️
```

---

## 📝 Example Entries

### Entry 1: Clean Logout
```
user@example.com | abc-123 | trace-abc | 14:00:00 | 14:15:30 | 1500 | 25 | 15:30 | logged_out
```

### Entry 2: Browser Closed
```
user@example.com | def-456 | trace-def | 10:00:00 | 10:45:23 | 800 | 12 | 45:23 | closed
```

### Entry 3: Currently Active
```
user@example.com | ghi-789 | trace-ghi | 16:30:00 | -- | 200 | 5 | -- | started
```

---

## 🧪 Quick Test

**Test Clean Logout**:
1. Sign in
2. Wait 1 minute
3. Click "Logout"
4. Check sheet: Duration should be ~`01:00`, Status: `logged_out`

**Test Browser Close**:
1. Sign in
2. Wait 2 minutes
3. Close browser/tab
4. Sign in again
5. Check sheet: Previous session Duration: ~`02:00`, Status: `closed`

---

## 🔍 SQL Queries for Analysis

### Count by Status
```sql
SELECT Status, COUNT(*) as Count
FROM Activity
GROUP BY Status
```

### Average Duration by Status
```sql
SELECT Status, AVG(Duration_Seconds) as Avg_Duration
FROM Activity
GROUP BY Status
```

### Active Users Right Now
```sql
SELECT Email, Login_Time, Session_ID
FROM Activity
WHERE Status = 'started'
```

### Users Who Never Logout Cleanly
```sql
SELECT Email, 
       SUM(CASE WHEN Status='logged_out' THEN 1 ELSE 0 END) as Clean_Exits,
       SUM(CASE WHEN Status='closed' THEN 1 ELSE 0 END) as Browser_Closes
FROM Activity
GROUP BY Email
HAVING Clean_Exits = 0
```

---

## 💡 Duration Conversion

**From `mm:ss` to seconds**:
```python
def duration_to_seconds(duration_str):
    """Convert 'mm:ss' to seconds"""
    m, s = duration_str.split(':')
    return int(m) * 60 + int(s)

# Example
duration_to_seconds("15:30")  # Returns: 930 seconds
```

**From seconds to `mm:ss`**:
```python
def seconds_to_duration(seconds):
    """Convert seconds to 'mm:ss'"""
    m = seconds // 60
    s = seconds % 60
    return f"{m:02d}:{s:02d}"

# Example
seconds_to_duration(930)  # Returns: "15:30"
```

---

## 📈 Key Metrics to Track

| Metric | What It Tells You |
|--------|-------------------|
| % logged_out | User engagement quality |
| % closed | Normal browser behavior |
| Avg duration (logged_out) | Engaged session time |
| Avg duration (closed) | Quick visit time |
| Active count (started) | Current users |

---

## ⚠️ Important Notes

1. **Duration Format**: Always `mm:ss`, never milliseconds
2. **Orphaned Sessions**: Auto-closed on next user login
3. **Status Values**: Only 3 valid values (started, logged_out, closed)
4. **Backward Compatibility**: Old entries (ms format) still work
5. **No Manual Cleanup**: System handles everything automatically ✅

---

## 🚨 Alert Rules (Suggested)

**Alert if**:
```
- More than 10 sessions stuck in "started" for >24 hours
- Zero "logged_out" sessions in last 7 days (might indicate UX issue)
- Average duration < 1 minute (users not engaging)
- More than 90% "closed" vs "logged_out" (consider auto-save feature)
```

---

## 🎯 Best Practices

1. **Check daily**: Review session statuses
2. **Monitor ratios**: logged_out vs closed
3. **Analyze patterns**: When do users leave?
4. **Duration insights**: How long do they stay?
5. **User engagement**: Track token usage + operations

---

## 📞 Need More Info?

- **Full Guide**: See `SESSION_TRACKING_IMPROVEMENTS.md`
- **Deployment**: See `DEPLOYMENT_GUIDE.md`
- **System Overview**: See `SYSTEM_OVERVIEW.md`

---

**Version**: 2.0 (Duration + Status improvements)

**Last Updated**: October 2025

**Backward Compatible**: ✅ Yes

**Auto-Cleanup**: ✅ Enabled
