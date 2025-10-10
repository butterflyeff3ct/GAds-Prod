# 🚀 Streamlit Cloud Deployment Guide

## Issue: Google Sheets Logging Not Working on Deployed App

Your app works perfectly on **localhost** but Google Sheets logging doesn't work on the **deployed Streamlit Cloud** app. This guide fixes that.

---

## 🔍 Root Cause

**Problem**: Streamlit Cloud doesn't have access to your local `.streamlit/secrets.toml` file.

**Solution**: You must manually configure secrets in the Streamlit Cloud dashboard.

---

## ✅ Step-by-Step Fix

### **Step 1: Access Streamlit Cloud Dashboard**

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Sign in with your GitHub account
3. Find your deployed app: `butterflyeff3ct-gads-prod-main-qnzzei`
4. Click on your app

### **Step 2: Open Secrets Configuration**

1. Click the **⚙️ Settings** button (or three dots menu)
2. Select **"Secrets"**
3. You'll see a text editor where you can paste your secrets

### **Step 3: Add Your Secrets**

Copy the content below and **replace** the placeholder values with your actual credentials:

```toml
# ========================================
# Google OAuth 2.0 Configuration
# ========================================
[google_oauth]
client_id = "YOUR_ACTUAL_CLIENT_ID.apps.googleusercontent.com"
client_secret = "YOUR_ACTUAL_CLIENT_SECRET"

# ⚠️ CRITICAL: Use your deployed app URL
redirect_uri_local = "http://localhost:8501"
redirect_uri_deployed = "https://butterflyeff3ct-gads-prod-main-qnzzei.streamlit.app/"


# ========================================
# Google Sheets Configuration
# ========================================
[google_sheets]
# Your Google Sheet ID from the URL
# Example: https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID_HERE/edit
sheet_id = "YOUR_ACTUAL_SHEET_ID"

# Service Account Credentials
# ⚠️ IMPORTANT: These are from your service account JSON file
[google_sheets.credentials]
type = "service_account"
project_id = "your-actual-project-id"
private_key_id = "your-actual-private-key-id"
private_key = "-----BEGIN PRIVATE KEY-----\nYour-Actual-Private-Key-Here\n-----END PRIVATE KEY-----\n"
client_email = "your-service-account@your-project.iam.gserviceaccount.com"
client_id = "123456789012345678901"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/your-service-account%40your-project.iam.gserviceaccount.com"


# ========================================
# Microsoft Clarity (Optional)
# ========================================
[clarity]
project_id = "YOUR_CLARITY_PROJECT_ID"  # Optional


# ========================================
# Gemini API (if applicable)
# ========================================
[gemini]
api_key = "YOUR_GEMINI_API_KEY"  # If you're using Gemini


# ========================================
# Google Ads API (if applicable)
# ========================================
[google_ads]
developer_token = "YOUR_DEV_TOKEN"
client_id = "YOUR_ADS_CLIENT_ID"
client_secret = "YOUR_ADS_CLIENT_SECRET"
refresh_token = "YOUR_REFRESH_TOKEN"
customer_id = "YOUR_CUSTOMER_ID"
```

### **Step 4: Get Your Actual Values**

#### **A. Get Google Sheets Credentials**

1. **Find your Service Account JSON file**:
   - This should be in your project folder (usually `.json` file)
   - Or download it from: [Google Cloud Console → Service Accounts](https://console.cloud.google.com/iam-admin/serviceaccounts)

2. **Open the JSON file** and copy these values:
   ```json
   {
     "type": "service_account",
     "project_id": "YOUR_PROJECT",        ← Copy this
     "private_key_id": "abc123...",       ← Copy this
     "private_key": "-----BEGIN...",      ← Copy this (entire key)
     "client_email": "service@...",       ← Copy this
     "client_id": "123456...",            ← Copy this
     ...
   }
   ```

3. **Find your Google Sheet ID**:
   - Open your Google Sheet
   - Look at the URL: `https://docs.google.com/spreadsheets/d/THIS_IS_YOUR_SHEET_ID/edit`
   - Copy the `THIS_IS_YOUR_SHEET_ID` part

#### **B. Get Google OAuth Credentials**

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your project
3. Go to **APIs & Services → Credentials**
4. Find your OAuth 2.0 Client ID
5. Copy:
   - **Client ID**: `xxxxx.apps.googleusercontent.com`
   - **Client Secret**: `GOCSPX-xxxxx`

### **Step 5: Update OAuth Redirect URI**

**CRITICAL**: Add your deployed app URL to authorized redirect URIs:

1. Go to [Google Cloud Console → Credentials](https://console.cloud.google.com/apis/credentials)
2. Click on your OAuth 2.0 Client ID
3. Under **"Authorized redirect URIs"**, add:
   ```
   https://butterflyeff3ct-gads-prod-main-qnzzei.streamlit.app/
   ```
   ⚠️ **Make sure to include the trailing `/`**
4. Click **Save**

### **Step 6: Share Google Sheet with Service Account**

1. Open your Google Sheet
2. Click **Share** (top right)
3. Add your service account email:
   ```
   your-service-account@your-project.iam.gserviceaccount.com
   ```
4. Give it **Editor** permission
5. Click **Send**

### **Step 7: Save and Restart**

1. Click **"Save"** in the Streamlit secrets editor
2. Your app will automatically restart
3. Wait ~30 seconds for the redeployment

### **Step 8: Test**

1. Visit your app: `https://butterflyeff3ct-gads-prod-main-qnzzei.streamlit.app/`
2. Sign in with Google
3. Check your Google Sheet - you should see new entries in:
   - **Users** tab (your email, name, etc.)
   - **Activity** tab (session start, login time, etc.)

---

## 🔧 Troubleshooting

### ❌ "Google Sheets Logging Not Configured" Warning

**Cause**: Secrets not properly added to Streamlit Cloud

**Fix**:
1. Double-check you added secrets to **Streamlit Cloud dashboard** (not just locally)
2. Verify `sheet_id` is correct
3. Ensure `credentials` section has all required fields
4. Click "Save" after pasting secrets

---

### ❌ "Failed to store user data" Error

**Cause**: Service account doesn't have access to the sheet

**Fix**:
1. Share your Google Sheet with the service account email
2. Give it **Editor** permission (not just Viewer)
3. Try signing in again

---

### ❌ OAuth Error: "redirect_uri_mismatch"

**Cause**: Deployed app URL not added to authorized redirect URIs

**Fix**:
1. Go to Google Cloud Console → Credentials
2. Add your Streamlit Cloud URL to authorized redirect URIs:
   ```
   https://butterflyeff3ct-gads-prod-main-qnzzei.streamlit.app/
   ```
3. Include the trailing `/`
4. Wait 5-10 minutes for changes to propagate
5. Clear browser cache and try again

---

### ❌ "Rate limit reached" Warning

**Cause**: Too many Google Sheets API calls

**Fix**:
- This is normal - the app has built-in rate limiting
- Data will be logged on the next operation
- If it happens frequently, reduce the number of operations

---

## 📋 Verification Checklist

- [ ] Secrets added to **Streamlit Cloud dashboard** (not just local file)
- [ ] `sheet_id` is correct from Google Sheet URL
- [ ] Service account credentials are complete (all fields from JSON)
- [ ] `private_key` includes `\n` characters (newlines)
- [ ] Deployed app URL added to OAuth redirect URIs
- [ ] Google Sheet shared with service account email
- [ ] Service account has **Editor** permission on sheet
- [ ] Secrets saved and app restarted
- [ ] Tested sign-in on deployed app
- [ ] Checked Google Sheet for new user/activity entries

---

## 💡 Pro Tips

1. **Test locally first**: Make sure it works on `localhost:8501` before deploying
2. **Use environment detection**: The app now automatically detects localhost vs production
3. **Check logs**: Look at Streamlit Cloud logs for any error messages
4. **Separate sheets**: Consider using different sheets for localhost and production
5. **Backup secrets**: Keep a copy of your secrets in a secure location (not Git!)

---

## 🎯 Quick Reference

### Where to Find Things:

| Item | Location |
|------|----------|
| Streamlit Secrets | [share.streamlit.io](https://share.streamlit.io) → Your App → Settings → Secrets |
| OAuth Credentials | [console.cloud.google.com/apis/credentials](https://console.cloud.google.com/apis/credentials) |
| Service Account | [console.cloud.google.com/iam-admin/serviceaccounts](https://console.cloud.google.com/iam-admin/serviceaccounts) |
| Google Sheet | Your actual tracking sheet URL |

---

## ✅ After Following This Guide

You should see:
- ✅ No warning messages about Google Sheets configuration
- ✅ New user entries in your Google Sheet "Users" tab
- ✅ Session tracking in your Google Sheet "Activity" tab
- ✅ Successful OAuth sign-in on deployed app

---

## 🆘 Still Having Issues?

If you've followed all steps and it's still not working:

1. Check Streamlit Cloud logs:
   - Go to your app dashboard
   - Click "Manage app"
   - View the logs for error messages

2. Verify secrets format:
   - Ensure proper TOML syntax
   - Check for extra quotes or spaces
   - Verify `private_key` has `\n` characters

3. Test individual components:
   - Test OAuth sign-in first
   - Then test Google Sheets access separately

4. Contact support:
   - Streamlit Community Forum: [discuss.streamlit.io](https://discuss.streamlit.io)
   - Include relevant log messages (redact sensitive info)

---

**Remember**: Local `.streamlit/secrets.toml` ≠ Streamlit Cloud secrets!

You must add secrets **manually** in the Streamlit Cloud dashboard. 🎯
