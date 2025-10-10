# 🔍 Google Sheets Not Updating - Troubleshooting Guide

## ✅ Changes Made

1. **Added 6-digit User ID generation** - Auto-generates unique IDs for new users
2. **Added debug logging** - Prints detailed messages to help diagnose issues
3. **Enhanced error messages** - More informative errors when things go wrong

---

## 🧪 Quick Test (5 Minutes)

### **Step 1: Test Locally First**

```bash
# From your project directory
streamlit run main.py
```

1. Sign in with Google
2. Check your terminal/console for `[DEBUG]` messages
3. Look for these specific messages:
   ```
   [DEBUG] Environment: Local Development
   [DEBUG] GSheetLogger initialized successfully
   [DEBUG] Attempting to store user: your@email.com
   [DEBUG] Generated 6-digit User ID: 123456
   [DEBUG] ✅ Successfully added user your@email.com with ID 123456
   [DEBUG] Logging session start for your@email.com
   [DEBUG] ✅ Successfully logged session start
   ```

4. Check your Google Sheet
   - **Users tab**: Should have your email + 6-digit User ID
   - **Activity tab**: Should have session with "started" status

---

### **Step 2: Check Debug Output**

**If you see:**
```
[DEBUG] GSheetLogger not enabled
```
**Problem**: Logger failed to initialize

**Solutions**:
1. Check `.streamlit/secrets.toml` exists and has `google_sheets` section
2. Verify `sheet_id` is correct
3. Verify `credentials` are complete

---

**If you see:**
```
[DEBUG] User your@email.com already exists - skipping
```
**This is NORMAL!** It means the user was added before. Check Google Sheet - they should be there.

---

**If you see:**
```
[DEBUG] ❌ Error storing user: [some error]
```
**Problem**: API call failed

**Common errors**:
- `Permission denied` → Service account not shared with sheet
- `429` or `rate limit` → Too many requests (wait 2-3 seconds)
- `Spreadsheet not found` → Wrong `sheet_id`

---

## 🌐 For Deployed App (Streamlit Cloud)

### **Step 1: Check Streamlit Cloud Logs**

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Find your app: `butterflyeff3ct-gads-prod-main-qnzzei`
3. Click **"Manage app"**
4. Click **"Logs"**
5. Look for `[DEBUG]` messages

---

### **Step 2: Verify Secrets Configuration**

**Check these in Streamlit Cloud dashboard (Settings → Secrets)**:

```toml
[google_sheets]
sheet_id = "14mxB2Uelj-CUiprrpOiznSK0NW7_ar2meDH5HeEeRQg"  # Your actual ID

[google_sheets.credentials]
type = "service_account"
project_id = "static-dock-470519-j1"
private_key_id = "ebea85893eb7d620a162ab062e3b06543c9e6389"
private_key = "-----BEGIN PRIVATE KEY-----\n...actual key...\n-----END PRIVATE KEY-----\n"
client_email = "gads-sim-sheets@static-dock-470519-j1.iam.gserviceaccount.com"
# ... rest of credentials
```

⚠️ **CRITICAL**: 
- `private_key` must include `\n` characters (newlines)
- All fields must be present
- No trailing commas or syntax errors

---

### **Step 3: Verify Google Sheet Sharing**

1. Open your Google Sheet: `https://docs.google.com/spreadsheets/d/14mxB2Uelj-CUiprrpOiznSK0NW7_ar2meDH5HeEeRQg/edit`

2. Click **"Share"** button

3. Verify this email is added with **Editor** permission:
   ```
   gads-sim-sheets@static-dock-470519-j1.iam.gserviceaccount.com
   ```

4. If not, add it now:
   - Click "Share"
   - Paste service account email
   - Change permission to "Editor"
   - Click "Send"

---

## 🔧 Common Issues & Fixes

### ❌ Issue 1: "GSheetLogger not enabled"

**Cause**: Initialization failed

**Debug Steps**:
1. Check if secrets exist:
   ```python
   import streamlit as st
   print(st.secrets.get("google_sheets"))
   ```

2. Check if `sheet_id` is set:
   ```python
   print(st.secrets["google_sheets"].get("sheet_id"))
   ```

3. Check if credentials exist:
   ```python
   print("credentials" in st.secrets["google_sheets"])
   ```

**Fix**: Add missing configuration to secrets

---

### ❌ Issue 2: No Debug Messages at All

**Cause**: Code not running or old version deployed

**Fix**:
1. **Push changes**:
   ```bash
   git add .
   git commit -m "fix: Add debug logging and user ID generation"
   git push origin main
   ```

2. **Wait for deployment**: ~1-2 minutes

3. **Clear cache**: Hard refresh browser (Ctrl+Shift+R or Cmd+Shift+R)

4. **Sign in again**

---

### ❌ Issue 3: "User already exists" but not in sheet

**Cause**: Cache issue

**Fix**:
1. **Clear cache**:
   ```python
   # In your code, temporarily
   logger._user_cache = {}
   logger._cache_timestamp = 0
   ```

2. **Or wait 5 minutes** (cache expires automatically)

3. **Or sign in with different email** to test

---

### ❌ Issue 4: Session not logging

**Cause**: Logger enabled but session start failed

**Debug**:
1. Check logs for:
   ```
   [DEBUG] Logging session start for your@email.com
   ```

2. If you see error:
   ```
   [DEBUG] ❌ Error logging session start: [error]
   ```
   - Check the error message
   - Verify Activity worksheet exists
   - Verify service account has write permission

---

### ❌ Issue 5: Rate Limit Errors

**Cause**: Too many API calls

**Symptoms**:
```
429 error
Rate limit exceeded
Quota exceeded
```

**Fix**:
- **Wait 2-3 seconds** between operations
- **This is normal** - system handles it automatically
- Just retry after waiting

---

## 📋 Verification Checklist

Run through this checklist:

### **Configuration**
- [ ] `.streamlit/secrets.toml` exists (localhost)
- [ ] Secrets configured in Streamlit Cloud dashboard (production)
- [ ] `google_sheets.sheet_id` is correct
- [ ] `google_sheets.credentials` section is complete
- [ ] `private_key` includes `\n` characters

### **Google Sheet**
- [ ] Sheet exists and is accessible
- [ ] Service account email added to sheet
- [ ] Service account has **Editor** permission
- [ ] Sheet has "Users" tab
- [ ] Sheet has "Activity" tab

### **Deployment**
- [ ] Latest code pushed to GitHub
- [ ] Streamlit Cloud shows deployment complete
- [ ] Browser cache cleared

### **Testing**
- [ ] Can sign in successfully
- [ ] See debug messages in logs/console
- [ ] User appears in Google Sheet "Users" tab
- [ ] Session appears in "Activity" tab with "started" status
- [ ] User ID is 6-digit number

---

## 🎯 Expected Behavior

When everything works correctly:

### **Console/Logs Output**:
```
[DEBUG] Environment: Production (Streamlit Cloud)
[DEBUG] GSheetLogger initialized successfully
[DEBUG] Successfully opened Google Sheet: 14mxB2Uelj-CUiprrpOiznSK0NW7_ar2meDH5HeEeRQg
[DEBUG] Found existing Users worksheet
[DEBUG] Found existing Activity worksheet
[DEBUG] Attempting to store user: user@example.com
[DEBUG] User user@example.com found in cache
[DEBUG] Checking for orphaned sessions for user@example.com
[DEBUG] No orphaned sessions found for user@example.com
[DEBUG] Logging session start for user@example.com, session: abc-123-def
[DEBUG] Writing to Activity sheet: ['user@example.com', 'abc-123', 'trace-abc', '2025-10-10 14:30:00', '', '', '', '', 'started']
[DEBUG] ✅ Successfully logged session start for user@example.com
```

### **Google Sheet "Users" Tab**:
```
| Email              | First Name | Last Name | First Login      | Profile Pic | Locale | User ID |
|--------------------|------------|-----------|------------------|-------------|--------|---------|
| user@example.com   | John       | Doe       | 2025-10-10 14:30 | [url]       | en     | 123456  |
```

### **Google Sheet "Activity" Tab**:
```
| Email            | Session ID  | Trace ID  | Login Time       | Logout Time | Tokens | Operations | Duration | Status  |
|------------------|-------------|-----------|------------------|-------------|--------|------------|----------|---------|
| user@example.com | abc-123-def | trace-abc | 2025-10-10 14:30 |             |        |            |          | started |
```

---

## 💡 Quick Fixes

### **Nothing in Sheet?**
1. **Check logs** for `[DEBUG]` messages
2. **Verify service account email** is shared with sheet
3. **Try with new email** to bypass cache

### **Can't see logs?**
- **Localhost**: Check terminal/console where you ran `streamlit run`
- **Streamlit Cloud**: Dashboard → Manage app → Logs

### **Still stuck?**
1. **Delete and recreate** the Google Sheet
2. **Share again** with service account
3. **Push code again** to force redeploy
4. **Clear browser cache** completely

---

## 📞 Need More Help?

**Try this test script**:

```python
# test_sheets_connection.py
import streamlit as st
from utils.gsheet_writer import GSheetLogger

st.title("Google Sheets Connection Test")

# Test initialization
logger = GSheetLogger(show_warnings=True)

st.write(f"Logger enabled: {logger.enabled}")
st.write(f"Is production: {logger.is_production}")

if logger.enabled:
    st.success("✅ Google Sheets logger initialized!")
    
    # Test user storage
    test_user = {
        "email": "test@example.com",
        "first_name": "Test",
        "last_name": "User",
        "locale": "en"
    }
    
    if st.button("Test User Storage"):
        result = logger.store_user_if_new(test_user)
        if result:
            st.success("✅ User stored successfully!")
        else:
            st.info("ℹ️ User already exists or storage skipped")
else:
    st.error("❌ Google Sheets logger NOT enabled")
    st.info("Check console/logs for [DEBUG] messages")
```

Run this and check the output + logs!

---

**Last Updated**: October 2025  
**Version**: 2.1 (with debug logging + User ID)
