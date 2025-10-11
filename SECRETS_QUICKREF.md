# 🔐 Complete Secrets Configuration - Quick Reference

## 📝 **Your `.streamlit/secrets.toml` Should Have All These Sections:**

```toml
# ========================================
# Google OAuth 2.0 Configuration
# ========================================
[google_oauth]
client_id = "your-client-id.apps.googleusercontent.com"
client_secret = "your-client-secret"
redirect_uri_local = "http://localhost:8501"
redirect_uri_deployed = "https://your-app.streamlit.app"


# ========================================
# Google Sheets Configuration
# ========================================
[google_sheets]
sheet_id = "your-google-sheet-id"

[google_sheets.credentials]
type = "service_account"
project_id = "your-project-id"
private_key_id = "your-private-key-id"
private_key = "-----BEGIN PRIVATE KEY-----\nYour-Key-Here\n-----END PRIVATE KEY-----\n"
client_email = "your-service-account@project.iam.gserviceaccount.com"
client_id = "123456789"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/..."


# ========================================
# Email Notifications (Gmail SMTP)
# ========================================
[email_notifications]
enabled = true
smtp_server = "smtp.gmail.com"
smtp_port = 587
sender_email = "your.email@gmail.com"           # ← Your Gmail
sender_password = "abcdefghijklmnop"            # ← Gmail App Password (16 chars, no spaces)
sender_name = "Google Ads Simulator"


# ========================================
# reCAPTCHA Bot Protection
# ========================================
[recaptcha]
enabled = true
version = "v2"
site_key = "6LdABC...xyz123"                    # ← Your reCAPTCHA Site Key
secret_key = "6LdDEF...abc789"                  # ← Your reCAPTCHA Secret Key
```

---

## ✅ **Configuration Checklist**

- [ ] **Google OAuth** - Configured (you already have this)
- [ ] **Google Sheets** - Configured (you already have this)
- [ ] **Email Notifications** - ADD: Gmail email + App Password
- [ ] **reCAPTCHA** - ADD: Site Key + Secret Key

---

## 🎯 **What to Add Right Now:**

Since you have your reCAPTCHA keys, just add this section to your secrets:

```toml
[recaptcha]
enabled = true
version = "v2"
site_key = "PASTE_YOUR_SITE_KEY_HERE"
secret_key = "PASTE_YOUR_SECRET_KEY_HERE"
```

---

## 🔧 **After Adding Secrets:**

```bash
Ctrl+C  # Stop Streamlit
streamlit run main.py  # Restart
```

---

## 🧪 **Quick Test:**

1. Click "Request Access"
2. Should see reCAPTCHA checkbox ✅
3. Admin Dashboard → Settings → Should show "reCAPTCHA ENABLED" ✅

---

**Add your keys and let me know when it's working!** 🚀
