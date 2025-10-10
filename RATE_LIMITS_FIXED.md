# Google Sheets API Rate Limits - What You Need to Know

## 🚨 The Problem

Google Sheets API has rate limits:
- **60 read requests per minute per user**
- **60 write requests per minute per user**

When you exceed these limits, you get:
```
APIError: [429]: Quota exceeded for quota metric 'Read requests'
```

---

## ✅ What I Fixed

### 1. **Added Caching** (Reduced Read Requests)
- User existence checks are now cached for 5 minutes
- Worksheet references are cached during initialization
- Only refreshes cache when expired

### 2. **Added Rate Limiting** (Minimum 2 seconds between requests)
- Enforces minimum 2-second delay between API calls
- Prevents rapid-fire requests

### 3. **Batch Updates** (Reduced Write Requests)
- Multiple cell updates in single API call
- Example: Updating 5 columns = 1 API call (instead of 5)

### 4. **Reduced Update Frequency**
- Session metrics only update every 10 operations (not every operation)
- Prevents constant writes during active sessions

### 5. **Graceful Degradation**
- If rate limit hit, shows warning but doesn't crash
- Data logged on next opportunity
- Silent failures for non-critical updates

---

## 🎯 How to Avoid Rate Limits

### Best Practices:

1. **Don't Refresh Too Often**
   - Each page refresh = potential API calls
   - Let the app run without refreshing

2. **Avoid Data Inspector During Active Session**
   - Use it ONCE to check your data
   - Don't keep it open or refresh it repeatedly

3. **Let Cache Work**
   - First login may take a few seconds
   - Subsequent operations are faster (cached)

4. **Wait Between Tests**
   - If testing, wait 1-2 minutes between test runs
   - Allows quota to reset

5. **Normal Usage is Fine**
   - Regular login/logout: ✅ No problem
   - Creating campaigns: ✅ No problem
   - Using the app normally: ✅ No problem
   - Rapidly refreshing pages: ❌ Can cause issues

---

## 📊 Current Quotas After Fix

With the fixes, typical usage:
- **Login**: 2-3 API calls (check user, log session)
- **Session Updates**: 1 call per 10 operations
- **Logout**: 2-3 API calls (update session end)

**Total for normal session**: ~10 API calls
**Quota available**: 60 calls per minute

You'd need to log in/out **6+ times per minute** to hit limits - which won't happen in normal usage!

---

## 🔧 What to Do if You Hit Rate Limit

### Immediate Fix:
1. **Wait 60 seconds** - Quota resets every minute
2. **Don't refresh** - Let the page sit
3. **Continue using app** - It will work after the minute passes

### Long-term:
The fixes I implemented should prevent this from happening during normal use.

---

## 🧪 Testing the Fix

Now that I've added rate limiting and caching:

1. **Restart your app:**
   ```bash
   streamlit run main.py
   ```

2. **Log in normally** - Should work fine

3. **Use Data Inspector** - Safe to use (no Sheets API calls now)

4. **Normal app usage** - Should never hit rate limits

---

## 📈 Monitoring

If you want to see what's happening:

Check the terminal output - I added debug prints:
- `🔍 User Info from Google:` - Shows OAuth data
- Rate limiting delays will show as brief pauses (2 seconds)

---

## 💡 Why This Happened

The original code was:
- Reading user list on EVERY login
- Not caching anything
- Making individual cell updates
- No rate limiting

With multiple refreshes or reruns, this could easily exceed 60 requests/minute.

The new code:
- ✅ Caches user data
- ✅ Batches updates
- ✅ Rate limits all requests
- ✅ Reduces update frequency

**Result**: Should never hit rate limits during normal usage! 🎉

---

## 🔐 Privacy Note

The rate limits are **per user** (the service account), not per end-user.

This means:
- All your app users share the same quota
- If you have many simultaneous users, consider upgrading to Google Workspace
- For personal/small team use, these limits are more than enough

---

Try the app now - it should work perfectly! 🚀
