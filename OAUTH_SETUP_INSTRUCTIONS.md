# 🔐 OAuth Setup Instructions

## For Streamlit Cloud Deployment (Recommended)

### Step 1: Get Google OAuth Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable the Google+ API
4. Go to "Credentials" → "Create Credentials" → "OAuth 2.0 Client IDs"
5. Choose "Web application"
6. Add authorized redirect URIs:
   - `https://butterflyeff3ct-gads-prod-main-qnzzei.streamlit.app/oauth2callback`
   - `http://localhost:8501/oauth2callback` (for local testing)

### Step 2: Add Secrets to Streamlit Cloud

1. Go to your Streamlit Cloud app dashboard
2. Click "Settings" → "Secrets"
3. Add this configuration:

```toml
[google_oauth]
client_id = "your-actual-client-id-here"
client_secret = "your-actual-client-secret-here"
redirect_uri = "https://butterflyeff3ct-gads-prod-main-qnzzei.streamlit.app/oauth2callback"
```

### Step 3: Deploy

The app will automatically detect the secrets and enable OAuth authentication.

---

## For Local Development

### Option A: Use Local Config File

1. Copy the template:
```bash
cp config/oauth_config_template.yaml config/oauth_config.yaml
```

2. Edit `config/oauth_config.yaml` with your actual credentials:
```yaml
google_oauth:
  client_id: "your-actual-client-id"
  client_secret: "your-actual-client-secret"
  redirect_uri: "http://localhost:8501/oauth2callback"
  scopes:
    - "openid"
    - "https://www.googleapis.com/auth/userinfo.email"
    - "https://www.googleapis.com/auth/userinfo.profile"
```

### Option B: Use Streamlit Secrets Locally

Create `.streamlit/secrets.toml`:
```toml
[google_oauth]
client_id = "your-actual-client-id"
client_secret = "your-actual-client-secret"
redirect_uri = "http://localhost:8501/oauth2callback"
```

---

## Current Status

✅ **App is working correctly** - showing appropriate warnings
✅ **OAuth system is ready** - just needs credentials
✅ **Fallbacks implemented** - app works without OAuth
✅ **Production URL configured** - ready for Streamlit Cloud

## Next Steps

1. **Get Google OAuth credentials** (5 minutes)
2. **Add to Streamlit Cloud secrets** (2 minutes)
3. **Deploy and test** (automatic)

The app will automatically detect the OAuth configuration and enable authentication!
