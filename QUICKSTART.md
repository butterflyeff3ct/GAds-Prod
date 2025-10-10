# ⚡ Quick Start Guide - OAuth + Google Sheets

This is a condensed version. For complete instructions, see `OAUTH_SHEETS_SETUP.md`.

---

## 📝 Prerequisites Checklist

Before you start, you need:
- [ ] Google Account
- [ ] Access to Google Cloud Console
- [ ] 15-20 minutes of setup time

---

## 🚀 Setup in 5 Steps

### Step 1: Google Cloud Setup (5 min)

1. Go to [console.cloud.google.com](https://console.cloud.google.com/)
2. Create new project: "Google Ads Simulator"
3. Enable APIs:
   - Google Identity Services API
   - Google Sheets API
4. Create OAuth 2.0 Client:
   - APIs & Services → Credentials → Create OAuth Client ID
   - Type: Web application
   - Authorized redirect URIs:
     ```
     http://localhost:8501
     https://your-app.streamlit.app
     ```
   - Download JSON

### Step 2: OAuth Consent Screen (3 min)

1. APIs & Services → OAuth consent screen
2. External → Fill required fields
3. Add scopes: `email`, `profile`, `openid`
4. **Add yourself as test user** ⚠️ Important!

### Step 3: Service Account (3 min)

1. IAM & Admin → Service Accounts → Create
2. Name: "gsheets-logger"
3. Role: Editor
4. Create Key → JSON → Download

### Step 4: Google Sheet (2 min)

1. Create new Google Sheet
2. Copy Sheet ID from URL
3. Share with service account email (from JSON)
4. Permission: Editor
5. Uncheck "Notify people"

### Step 5: Configure secrets.toml (5 min)

Create `.streamlit/secrets.toml`:

```toml
[google_oauth]
client_id = "YOUR_OAUTH_CLIENT_ID.apps.googleusercontent.com"
client_secret = "YOUR_OAUTH_CLIENT_SECRET"
redirect_uri_local = "http://localhost:8501"
redirect_uri_deployed = "https://your-app.streamlit.app"

[google_sheets]
sheet_id = "YOUR_SHEET_ID"

[google_sheets.credentials]
# Paste entire service account JSON contents here
type = "service_account"
project_id = "..."
private_key_id = "..."
private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
client_email = "gsheets-logger@....iam.gserviceaccount.com"
# ... rest of JSON fields
```

---

## 🧪 Test It

```bash
# Install dependencies
pip install -r requirements.txt

# Run app
streamlit run main.py

# After login:
# 1. Check "🔍 Google Sheets Integration Status" expander
# 2. Click "🧪 Test Google Sheets Integration" button
# 3. Verify data in your Google Sheet
```

---

## ✅ Success Checklist

Your setup is complete when:

- [ ] Can login with Google
- [ ] No red errors in status expander
- [ ] Test button creates data in sheet
- [ ] "Users" tab has your info
- [ ] "Activity" tab has session data

---

## 🔧 Common Issues

**"invalid_grant"**
→ Don't refresh during login. Just click "Sign in" again.

**"Access blocked"**
→ Add yourself as test user in OAuth consent screen.

**"Sheet not found"**
→ Check Sheet ID and verify it's shared with service account email.

---

## 📚 Full Documentation

- **Complete Setup:** `OAUTH_SHEETS_SETUP.md`
- **What Changed:** `IMPLEMENTATION_SUMMARY.md`
- **Config Template:** `.streamlit/secrets.toml.template`

---

## 🎯 Quick Reference

**OAuth 2.0 API** (NOT Google+)
- Google+ was deprecated in 2019
- This uses modern Google Identity Platform
- Scopes: openid, email, profile

**Sheets Schema**
- Users: Email | First Name | Last Name | First Login | Profile Pic | Locale | User ID
- Activity: Email | Session ID | Trace ID | Login Time | Logout Time | Tokens Used | Operations | Duration (ms) | Status

**Security**
- Never commit secrets.toml
- Keep sheets private
- Rotate credentials every 90 days

---

**Need help?** Check the troubleshooting section in `OAUTH_SHEETS_SETUP.md`
