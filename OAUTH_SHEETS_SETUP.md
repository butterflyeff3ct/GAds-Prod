# Google OAuth + Sheets Setup Guide
## Complete Integration for Google Ads Simulator

This guide will help you set up Google OAuth 2.0 authentication and Google Sheets logging for your application.

---

## 🔑 Part 1: Google OAuth 2.0 Setup (NOT Google+)

**Important:** Google+ API was deprecated in 2019. This app uses the modern **Google Identity Platform / OAuth 2.0** API.

### Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click "Select a project" → "New Project"
3. Name it: "Google Ads Simulator" (or your preferred name)
4. Click "Create"

### Step 2: Enable Required APIs

1. In your project, go to **"APIs & Services"** → **"Library"**
2. Search for and enable:
   - ✅ **Google Identity Services API** (for OAuth 2.0)
   - ✅ **Google Sheets API** (for logging)
   - ✅ **Google Drive API** (optional, for file access)

### Step 3: Configure OAuth Consent Screen

1. Go to **"APIs & Services"** → **"OAuth consent screen"**
2. Choose **"External"** (unless you have a Google Workspace)
3. Fill in required fields:
   - **App name:** Google Ads Simulator
   - **User support email:** Your email
   - **Developer contact email:** Your email
4. Click "Save and Continue"
5. **Scopes:** Click "Add or Remove Scopes"
   - Add: `./auth/userinfo.email`
   - Add: `./auth/userinfo.profile`
   - Add: `openid`
6. Click "Save and Continue"
7. **Test users:** Add your Gmail address (required for testing)
8. Click "Save and Continue"

### Step 4: Create OAuth 2.0 Credentials

1. Go to **"APIs & Services"** → **"Credentials"**
2. Click **"+ Create Credentials"** → **"OAuth client ID"**
3. Choose **"Web application"**
4. **Name:** "Google Ads Simulator Web Client"
5. **Authorized JavaScript origins:** (Leave empty)
6. **Authorized redirect URIs:** Add BOTH:
   ```
   http://localhost:8501
   https://your-app-name.streamlit.app
   ```
   Replace `your-app-name` with your actual Streamlit app URL
7. Click **"Create"**
8. **Download the JSON** (you'll need this)

---

## 📊 Part 2: Google Sheets Setup

### Step 1: Create a Google Sheet

1. Go to [Google Sheets](https://sheets.google.com)
2. Create a new spreadsheet
3. Name it: "Google Ads Simulator - User Data"
4. **Keep it private** (don't share it yet)
5. Copy the **Sheet ID** from the URL:
   ```
   https://docs.google.com/spreadsheets/d/[THIS_IS_YOUR_SHEET_ID]/edit
   ```

### Step 2: The sheets will be auto-created on first use:
- **Users** tab: Email | First Name | Last Name | First Login | Profile Pic | Locale | User ID
- **Activity** tab: Email | Session ID | Trace ID | Login Time | Logout Time | Tokens Used | Operations | Duration (ms) | Status

### Step 3: Create Service Account for Sheets Access

1. Go back to [Google Cloud Console](https://console.cloud.google.com/)
2. Navigate to **"IAM & Admin"** → **"Service Accounts"**
3. Click **"+ Create Service Account"**
4. **Service account name:** "gsheets-logger"
5. Click **"Create and Continue"**
6. **Role:** Select "Editor" (or "Basic" → "Editor")
7. Click **"Continue"** → **"Done"**

### Step 4: Generate Service Account Key

1. Click on the service account you just created
2. Go to **"Keys"** tab
3. Click **"Add Key"** → **"Create new key"**
4. Choose **"JSON"**
5. Click **"Create"** (downloads a JSON file)
6. **Keep this file safe!** You'll add its contents to your secrets

### Step 5: Share Sheet with Service Account

1. Open the downloaded JSON file
2. Find the `"client_email"` field (looks like `xxx@xxx.iam.gserviceaccount.com`)
3. Go back to your Google Sheet
4. Click **"Share"** button
5. Paste the service account email
6. Set permission to **"Editor"**
7. **Uncheck** "Notify people"
8. Click **"Share"**

---

## 🔐 Part 3: Configure Streamlit Secrets

### Create/Update `.streamlit/secrets.toml`

Create or update the file at: `.streamlit/secrets.toml`

```toml
# Google OAuth 2.0 Configuration (for user login)
[google_oauth]
client_id = "YOUR_OAUTH_CLIENT_ID.apps.googleusercontent.com"
client_secret = "YOUR_OAUTH_CLIENT_SECRET"
redirect_uri_local = "http://localhost:8501"
redirect_uri_deployed = "https://your-app-name.streamlit.app"

# Google Sheets Configuration (for logging)
[google_sheets]
sheet_id = "YOUR_GOOGLE_SHEET_ID"

# Service Account Credentials (paste entire JSON contents here)
[google_sheets.credentials]
type = "service_account"
project_id = "your-project-id"
private_key_id = "your-private-key-id"
private_key = "-----BEGIN PRIVATE KEY-----\nYour-Private-Key-Here\n-----END PRIVATE KEY-----\n"
client_email = "gsheets-logger@your-project.iam.gserviceaccount.com"
client_id = "123456789"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/xxx"
```

**How to fill this in:**

1. **OAuth Section:**
   - `client_id`: From OAuth credentials JSON (step 1.4)
   - `client_secret`: From OAuth credentials JSON
   - `redirect_uri_deployed`: Your Streamlit app URL

2. **Sheets Section:**
   - `sheet_id`: From your Google Sheet URL (step 2.1)
   - `credentials`: Copy entire contents from service account JSON (step 2.4)

---

## 🚀 Part 4: Testing the Integration

### Local Testing

1. Make sure you've completed all setup steps above
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the app:
   ```bash
   streamlit run main.py
   ```

4. Test the integration:
   - Click "Sign in with Google"
   - Authorize the app
   - After login, check the **"🔍 Google Sheets Integration Status"** expander
   - Click **"🧪 Test Google Sheets Integration"** button
   - Verify data appears in your Google Sheet

### Deploy to Streamlit Cloud

1. Push your code to GitHub (DON'T include secrets.toml!)
2. Go to [Streamlit Cloud](https://share.streamlit.io/)
3. Create a new app from your GitHub repo
4. In **Advanced settings** → **Secrets**, paste your `secrets.toml` content
5. Deploy!

---

## 📋 Checklist

Before going live, verify:

- [ ] Google Cloud Project created
- [ ] OAuth 2.0 credentials created
- [ ] Consent screen configured with test users
- [ ] Both redirect URIs added (localhost + deployed URL)
- [ ] Google Sheets API enabled
- [ ] Service account created with JSON key
- [ ] Google Sheet shared with service account email
- [ ] secrets.toml configured correctly
- [ ] Local testing successful
- [ ] Data appearing in Google Sheets

---

## 🔧 Troubleshooting

### "invalid_grant" Error
- **Cause:** Authorization code expired or reused
- **Fix:** Don't refresh during login, just click "Sign in" again

### "Access blocked" Error
- **Cause:** Not added as test user
- **Fix:** Add your email in OAuth consent screen → Test users

### "Spreadsheet not found"
- **Cause:** Wrong Sheet ID or not shared
- **Fix:** 
  1. Check Sheet ID is correct
  2. Share sheet with service account email as Editor

### "Invalid redirect URI"
- **Cause:** Mismatch between code and Google Cloud
- **Fix:** Verify URIs match EXACTLY (no trailing slashes)

### Data not appearing in sheet
- **Cause:** Permissions or credentials issue
- **Fix:**
  1. Verify service account has Editor access
  2. Check credentials JSON is complete in secrets.toml
  3. Look for error messages in app

---

## 🔒 Security Notes

1. **Never commit secrets.toml to Git!**
   - Add `.streamlit/` to `.gitignore`
   
2. **Keep service account JSON private**
   - This grants access to your Google Sheet
   
3. **Rotate credentials periodically**
   - Generate new keys every 90 days
   
4. **Use environment-specific configs**
   - Different credentials for dev/prod

---

## 📞 Support

If you encounter issues:

1. Check the troubleshooting section above
2. Verify all checklist items are complete
3. Check Streamlit app logs for detailed errors
4. Review Google Cloud Console audit logs

---

## 🎉 Success!

Once configured, your app will:
- ✅ Authenticate users with Google OAuth 2.0 (NOT Google+)
- ✅ Log user information to "Users" tab
- ✅ Track session activity in "Activity" tab
- ✅ Keep sheets private (only accessible via service account)
- ✅ Support both local development and cloud deployment
