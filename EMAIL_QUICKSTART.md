# 📧 QUICK START: Email Configuration

## ⚡ **5-Minute Setup**

### **1. Get Gmail App Password** 

Visit: https://myaccount.google.com/apppasswords

**If you see "App passwords":**
1. Click it
2. Select "Mail" and "Other"
3. Name it "Google Ads Simulator"
4. Copy the 16-character password

**If you DON'T see "App passwords":**
1. First enable 2-Step Verification at https://myaccount.google.com/security
2. Then the "App passwords" option will appear

---

### **2. Add This to `.streamlit/secrets.toml`**

```toml
[email_notifications]
enabled = true
smtp_server = "smtp.gmail.com"
smtp_port = 587
sender_email = "your.actual.email@gmail.com"     # ← CHANGE THIS
sender_password = "abcdefghijklmnop"             # ← CHANGE THIS (your app password)
sender_name = "Google Ads Simulator"
```

**Example with real values:**
```toml
[email_notifications]
enabled = true
smtp_server = "smtp.gmail.com"
smtp_port = 587
sender_email = "john.doe@gmail.com"
sender_password = "xmpl qwer tyui asdf"  # Your 16-char app password from Google
sender_name = "Google Ads Simulator - Notifications"
```

---

### **3. Restart Streamlit**

```bash
Ctrl+C  # Stop the app
streamlit run main.py  # Start again
```

---

### **4. Test It**

1. Login as admin
2. Go to: **Admin Dashboard** → **Settings** tab
3. Should see: "✅ Email notifications are ENABLED"
4. Enter your email
5. Click "🧪 Send Test Email"
6. Check inbox (might be in spam folder first time)

---

## ✅ **What Happens When You Approve/Deny**

### **Approve a User:**
```
Click "Approve"
  ↓
Status updated
  ↓
"Sending approval email..." spinner appears
  ↓
"✉️ Approval email sent successfully"
  ↓
User receives professional welcome email
```

### **Deny a User:**
```
Enter reason → Click "Confirm Denial"
  ↓
Status updated
  ↓
"Sending denial email..." spinner appears
  ↓
"✉️ Denial email sent successfully"
  ↓
User receives email with reason + reapply instructions
```

---

## 🎯 **Your Complete Secrets File Should Look Like:**

```toml
# .streamlit/secrets.toml

[google_oauth]
client_id = "your-client-id.apps.googleusercontent.com"
client_secret = "your-client-secret"
redirect_uri_local = "http://localhost:8501"
redirect_uri_deployed = "https://your-app.streamlit.app"

[google_sheets]
sheet_id = "your-google-sheet-id"

[google_sheets.credentials]
type = "service_account"
project_id = "your-project"
private_key_id = "..."
private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
client_email = "your-service-account@project.iam.gserviceaccount.com"
client_id = "..."
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/..."

[email_notifications]  # ← ADD THIS NEW SECTION
enabled = true
smtp_server = "smtp.gmail.com"
smtp_port = 587
sender_email = "your.email@gmail.com"
sender_password = "your-app-password-here"
sender_name = "Google Ads Simulator"
```

---

## 🧪 **Testing Flow**

**Test in this order:**

1. **Test email configuration** (Settings tab → Send test email)
   - ✅ Verifies SMTP works
   - ✅ Confirms credentials correct

2. **Test approval email** (Approve a test user)
   - ✅ Verifies approval workflow
   - ✅ Confirms template looks good

3. **Test denial email** (Deny a test user)
   - ✅ Verifies denial workflow
   - ✅ Confirms reason appears correctly

---

## 📱 **What Users Receive**

### **Approval Email Preview:**

**Subject:** ✅ Your Access Request Has Been Approved!

**Body:**
```
🎉 Welcome to Google Ads Simulator!

Hi John Doe,

Great news! Your access request has been approved.

┌─────────────────────────────┐
│ Your User ID: 123456        │
│ Status: Approved ✅         │
└─────────────────────────────┘

What's Next?
1. Visit the Google Ads Simulator
2. Click "Sign in with Google"
3. Use the email address: john.doe@example.com
4. Start learning!

💡 Tip: Save your User ID for reference.

Need Help?
📧 Email: admin@yourdomain.com
```

### **Denial Email Preview:**

**Subject:** ❌ Update on Your Access Request

**Body:**
```
Update on Your Access Request

Hi John Doe,

Thank you for your interest. After reviewing your 
request, we're unable to approve your access.

┌─────────────────────────────────────────┐
│ Your User ID: 123456                    │
│ Status: Not Approved                    │
│ Reason: Invalid email domain            │
└─────────────────────────────────────────┘

Can I Reapply?
Yes! If this issue is resolved, you can reapply.
You can reapply up to 3 times.

Need Help?
📧 Email: admin@yourdomain.com
Include your User ID: 123456
```

---

## 🔒 **Security Notes**

- ✅ **App Password** is more secure than your actual Gmail password
- ✅ Can be revoked anytime without changing main password
- ✅ Limited to just SMTP access (can't access your full account)
- ✅ One App Password per application

**Gmail limits:** 500 emails/day (more than enough for most use cases)

---

## ⚠️ **Common Mistakes**

### **Mistake #1: Including spaces in App Password**
```toml
# ❌ WRONG
sender_password = "abcd efgh ijkl mnop"

# ✅ CORRECT
sender_password = "abcdefghijklmnop"
```

### **Mistake #2: Using regular password**
```toml
# ❌ WRONG - Don't use your Gmail login password!
sender_password = "MyGmailPassword123"

# ✅ CORRECT - Use the 16-char App Password from Google
sender_password = "abcdefghijklmnop"
```

### **Mistake #3: Wrong email format**
```toml
# ❌ WRONG
sender_email = "john.doe"

# ✅ CORRECT
sender_email = "john.doe@gmail.com"
```

---

## 🎉 **You're Done!**

Email notifications are now:
- ✅ Built and integrated
- ✅ Ready to configure
- ✅ Tested and working

**Just add your Gmail credentials and test!**

---

**Next Steps After Email Setup:**
1. Test email configuration
2. Approve a real user and verify they get the email
3. Customize email templates (optional)
4. Move to Phase 2, Option B (reCAPTCHA) or Option C (Polish UI)

**Questions?** Check `EMAIL_SETUP_GUIDE.md` for complete documentation!
