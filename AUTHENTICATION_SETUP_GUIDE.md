# AUTHENTICATION_SETUP_GUIDE.md

# Google OAuth Authentication & Quota System - Setup Guide

## 🎯 What This System Does

1. **Google OAuth Login** - Secure authentication
2. **Session Management** - 2-hour sessions with auto-extension
3. **Quota Tracking** - API limits per user (10 Google Ads API calls/hour, etc.)
4. **Rate Limiting** - Max 10 concurrent users
5. **Activity Logging** - Full audit trail
6. **User Dashboard** - See quota usage and activity

---

## 🚀 Setup Steps

### Step 1: Install New Dependencies

```bash
pip install -r requirements_with_auth.txt
```

Or install individually:
```bash
pip install google-auth google-auth-oauthlib sqlalchemy python-jose pyyaml
```

---

### Step 2: Get Google OAuth Credentials

1. **Go to Google Cloud Console:**
   https://console.cloud.google.com/

2. **Create/Select Project:**
   - Create new project or select existing
   - Name it "Google Ads Simulator"

3. **Enable APIs:**
   - Go to "APIs & Services" → "Library"
   - Search for "Google+ API" → Enable
   - Search for "People API" → Enable

4. **Create OAuth Credentials:**
   - Go to "APIs & Services" → "Credentials"
   - Click "Create Credentials" → "OAuth client ID"
   - Application type: "Web application"
   - Name: "Google Ads Simulator"
   
5. **Configure Redirect URI:**
   - Authorized redirect URIs: `http://localhost:8501`
   - (For production, add your domain)

6. **Download Credentials:**
   - Click Download JSON (optional)
   - Copy Client ID and Client Secret

---

### Step 3: Configure OAuth in Your Project

**Edit:** `config/oauth_config.yaml`

```yaml
google_oauth:
  client_id: "123456789-abc123.apps.googleusercontent.com"  # YOUR CLIENT ID
  client_secret: "GOCSPX-your_secret_here"  # YOUR CLIENT SECRET
  redirect_uri: "http://localhost:8501"
  scopes:
    - "openid"
    - "https://www.googleapis.com/auth/userinfo.email"
    - "https://www.googleapis.com/auth/userinfo.profile"

quota_limits:
  google_ads_api: 10
  gemini_api: 20
  keyword_planner: 15
  simulations_per_hour: 5
  campaigns_per_day: 10
  max_concurrent_users: 10
  max_hourly_logins: 50

admin_emails:
  - "your-email@gmail.com"  # YOUR EMAIL (gets admin access)
```

---

### Step 4: Activate Authentication

**Option A: Rename File (Recommended)**
```bash
# Backup current main.py
mv main.py main_no_auth.py

# Activate auth version
mv main_with_auth.py main.py
```

**Option B: Manual Integration**
Add to beginning of your current `main.py`:
```python
from app.login_page import render_login_page
from auth.session_manager import SessionManager

def main():
    # Authentication check FIRST
    if not SessionManager.is_authenticated():
        render_login_page()
        return
    
    # Rest of your existing main() code...
```

---

### Step 5: Test the System

```bash
# Run the app
streamlit run main.py

# Expected flow:
# 1. App loads → Login page appears
# 2. Click "Sign in with Google"
# 3. Google login popup
# 4. Grant permissions
# 5. Redirect back → Main app loads
# 6. See your name and quota in sidebar
```

---

## 🧪 Testing Checklist

- [ ] Login page appears on app load
- [ ] Google OAuth button works
- [ ] Can complete Google login flow
- [ ] Redirected back to app after login
- [ ] Username shows in sidebar
- [ ] Quota indicators visible
- [ ] Can use all app features
- [ ] Quotas decrement on API use
- [ ] Logout works
- [ ] Can login again

---

## 🔧 Troubleshooting

### Issue: "Redirect URI mismatch"
**Solution:** 
- Check Google Cloud Console → Credentials
- Ensure redirect URI is exactly: `http://localhost:8501`
- No trailing slash!

### Issue: "Invalid client"
**Solution:**
- Verify Client ID and Secret in oauth_config.yaml
- Check for extra spaces or quotes
- Regenerate credentials if needed

### Issue: "API not enabled"
**Solution:**
- Enable Google+ API in Cloud Console
- Enable People API
- Wait 1-2 minutes for propagation

### Issue: "10 users limit reached"
**Solution:**
- Wait for inactive sessions to expire
- Or increase `max_concurrent_users` in config
- Or clear database: `rm database/users.db` (dev only!)

### Issue: Database errors
**Solution:**
```bash
# Recreate database
rm database/users.db
python -c "from database.db_manager import DatabaseManager; DatabaseManager()"
```

---

## 📊 Quota System Behavior

### What Happens When User Hits Limit:

**Soft Limit (80% usage):**
```
⚠️ Warning: You've used 8/10 Google Ads API calls
💡 Consider using mock data for testing
```

**Hard Limit (100% usage):**
```
🚫 Google Ads API quota exceeded
Limit: 10 calls/hour
Resets in: 23 minutes

The app will automatically use mock data instead.
Your simulation will still work!
```

**Global Limit (10 users):**
```
⚠️ Maximum concurrent users (10) reached
Please try again in a few minutes

Estimated wait time: 5-15 minutes
```

---

## 🎨 UI Changes After Setup

### Before Authentication:
```
[App loads] → [Main Dashboard immediately]
```

### After Authentication:
```
[App loads] → [Login Page]
           ↓
[Google OAuth] → [Verify]
           ↓
[Create Session] → [Main App]
```

### Sidebar with Auth:
```
👤 John Doe
📧 john@example.com

📊 Your Quotas:
━━━━━━━━━━━━━━━━
Google Ads API: 7/10 ●●●●●●●○○○ 70%
Gemini API: 15/20 ●●●●●●●●○○ 75%
Simulations: 3/5 ●●●○○ 60%

⏰ Resets in: 23 minutes
🕐 Session: 1h 45m remaining

[📈 View Detailed Usage]
[🚪 Logout]
```

---

## 🔐 Security Features

✅ OAuth 2.0 with Google (industry standard)  
✅ Session tokens with expiration  
✅ Activity logging (full audit trail)  
✅ Rate limiting (per-user and global)  
✅ Automatic session timeout (2 hours)  
✅ Secure credential storage  
✅ SQL injection protection (SQLAlchemy ORM)  

---

## 📝 Next Steps After Setup

1. ✅ Test login flow
2. ✅ Set yourself as admin in config
3. ✅ Test quota system (make 10 API calls)
4. ✅ Check activity logging
5. ✅ Test with multiple users (friends/colleagues)
6. ✅ Monitor database growth
7. ✅ Set up production domain (optional)

---

## 🌐 Production Deployment (Optional)

### Update for Production Domain:

**1. Google Cloud Console:**
- Add production domain to authorized redirect URIs
- Example: `https://your-domain.com`

**2. config/oauth_config.yaml:**
```yaml
google_oauth:
  redirect_uri: "https://your-domain.com"  # Update this
```

**3. Streamlit Config:**
```toml
# .streamlit/config.toml
[server]
headless = true
enableCORS = false
enableXsrfProtection = true
```

---

## 📚 File Summary

### New Files Created:
1. `auth/google_oauth.py` - OAuth flow management
2. `auth/session_manager.py` - Session handling
3. `auth/quota_manager.py` - Quota tracking
4. `auth/user_activity.py` - Activity logging
5. `database/models.py` - Database schema
6. `database/db_manager.py` - Database operations
7. `app/login_page.py` - Login UI
8. `app/quota_page.py` - Quota dashboard
9. `config/oauth_config.yaml` - OAuth config
10. `main_with_auth.py` - Auth-enabled entry point

### Total New Code: ~1,200 lines
### Databases Created: `database/users.db` (auto-created)

---

## ✅ Ready to Use!

After completing setup steps, your simulator will have:
- ✅ Secure Google login
- ✅ 10 users/hour limit enforced
- ✅ Per-user API quotas
- ✅ Activity tracking
- ✅ Admin capabilities
- ✅ Professional authentication system

**Questions? Issues? Let me know!**
