# 📧 Email Notifications Setup Guide

## ✅ **What You Have**

Email notifications are now integrated! When you approve or deny users, they'll automatically receive emails.

**Email Types:**
- ✅ **Approval Email** - Sent when admin approves a user
- ✅ **Denial Email** - Sent when admin denies a user (includes reason and reapply option)
- 🧪 **Test Email** - Available in admin dashboard to test configuration

---

## 🔐 **Gmail App Password Setup (5 minutes)**

Gmail requires an "App Password" for SMTP access. Here's how to get one:

### **Step 1: Enable 2-Step Verification**

1. Go to your Google Account: https://myaccount.google.com/
2. Click **Security** in the left sidebar
3. Under **"Signing in to Google"**, click **2-Step Verification**
4. Follow the prompts to enable it (if not already enabled)

### **Step 2: Generate App Password**

1. Go back to **Security** page
2. Scroll down to **2-Step Verification** section
3. At the bottom, click **App passwords**
4. You might need to sign in again
5. Select these options:
   - **App:** Select "Mail"
   - **Device:** Select "Other (custom name)"
   - **Name:** Enter "Google Ads Simulator"
6. Click **Generate**
7. Google will show you a 16-character password like: `abcd efgh ijkl mnop`
8. **Copy this password** (remove spaces) → `abcdefghijklmnop`

⚠️ **Important:** This password is shown only once! Save it immediately.

---

## ⚙️ **Configure Streamlit Secrets**

### **Open `.streamlit/secrets.toml` and add this section:**

```toml
# ========================================
# Email Notifications Configuration
# ========================================

[email_notifications]
# Enable email notifications
enabled = true

# Gmail SMTP Settings
smtp_server = "smtp.gmail.com"
smtp_port = 587

# Your Gmail credentials
sender_email = "your.email@gmail.com"          # ← Your Gmail address
sender_password = "abcdefghijklmnop"           # ← Your App Password (no spaces!)
sender_name = "Google Ads Simulator"           # ← Name shown in "From" field
```

### **Example Configuration:**

```toml
[email_notifications]
enabled = true
smtp_server = "smtp.gmail.com"
smtp_port = 587
sender_email = "notifications@yourdomain.com"
sender_password = "xyzw abcd efgh ijkl"  # Replace with your actual app password
sender_name = "Google Ads Simulator - Admin"
```

---

## 🧪 **Test Email Configuration**

### **Method 1: Admin Dashboard (Recommended)**

1. Login to your app as admin
2. Go to **Admin Dashboard** → **Settings** tab
3. You should see "✅ Email notifications are ENABLED"
4. Enter your email in the test field
5. Click "🧪 Send Test Email"
6. Check your inbox (may take 30 seconds)

### **Method 2: Python Script**

```python
import streamlit as st
from utils.email_notifications import EmailNotifier

# Initialize
notifier = EmailNotifier()

# Send test
if notifier.enabled:
    success = notifier.send_test_email("your.email@gmail.com")
    print(f"Test email sent: {success}")
else:
    print("Email notifications not enabled")
```

---

## 📬 **What Emails Look Like**

### **Approval Email:**

```
From: Google Ads Simulator <your.email@gmail.com>
To: user@example.com
Subject: ✅ Your Access Request Has Been Approved!

🎉 Welcome to Google Ads Simulator!

Hi John Doe,

Great news! Your access request has been approved.

Your User ID: 123456
Status: Approved ✅

What's Next?
1. Visit the Google Ads Simulator
2. Click "Sign in with Google"
3. Use the email address: user@example.com
4. Start learning Google Ads campaign management!

💡 Tip: Save your User ID for reference.

Need Help?
📧 Email: admin@yourdomain.com
```

### **Denial Email:**

```
From: Google Ads Simulator <your.email@gmail.com>
To: user@example.com
Subject: ❌ Update on Your Access Request

Update on Your Access Request

Hi John Doe,

Thank you for your interest in the Google Ads Simulator. 
After reviewing your request, we're unable to approve your 
access at this time.

Your User ID: 123456
Status: Not Approved
Reason: Invalid email domain - corporate emails only

Can I Reapply?
Yes! If you believe this issue has been resolved, you're 
welcome to submit a new access request. You can reapply 
up to 3 times.

Need Help?
📧 Email: admin@yourdomain.com
Include your User ID: 123456
```

---

## 🎨 **Customize Email Templates**

Want to customize the emails? Edit these methods in `utils/email_notifications.py`:

### **Approval Email:** 
- Method: `send_approval_email()` (line ~95)
- Update HTML and text templates
- Change colors, add logo, modify text

### **Denial Email:**
- Method: `send_denial_email()` (line ~150)
- Customize messaging
- Add custom branding

### **Test Email:**
- Method: `send_test_email()` (line ~220)
- Simple test template

---

## 🔧 **Troubleshooting**

### **"Email notifications are DISABLED"**

**Check:**
1. `.streamlit/secrets.toml` has `[email_notifications]` section
2. `enabled = true`
3. `sender_email` and `sender_password` are filled in
4. Restart your Streamlit app after updating secrets

### **"SMTP Authentication failed"**

**Common causes:**
1. Using regular password instead of App Password
2. App Password has spaces (remove them!)
3. 2-Step Verification not enabled on Gmail
4. Wrong email address

**Solution:**
- Regenerate App Password
- Make sure it's 16 characters, no spaces
- Use the exact Gmail address

### **"Test email not received"**

**Check:**
1. Spam/Junk folder
2. Gmail SMTP limits (500 emails/day)
3. Email address is correct
4. Network/firewall isn't blocking SMTP

### **"Email sent but looks weird"**

- Some email clients don't support HTML
- Plain text fallback is included
- Test with multiple email clients

---

## 📊 **Email Delivery Status**

When admin approves/denies:
- ✅ **Success:** "✉️ Approval email sent successfully"
- ⚠️ **Failure:** "⚠️ User approved but email failed to send"

**Note:** User status is updated regardless of email success. Email failures won't block approvals.

---

## 🔒 **Security Best Practices**

### **Gmail App Passwords:**
- ✅ Use App Passwords (more secure than regular password)
- ✅ One password per app
- ✅ Can be revoked anytime
- ✅ Doesn't expose your main password

### **Secrets Management:**
- ✅ Never commit `.streamlit/secrets.toml` to Git
- ✅ Add to `.gitignore`
- ✅ Store backups securely
- ✅ Rotate passwords periodically

### **Rate Limiting:**
- Gmail SMTP: **500 emails/day** limit
- For higher volume, consider SendGrid or AWS SES
- Current usage: 1 email per approval/denial

---

## 📈 **Usage Limits**

### **Gmail SMTP Limits:**
- **Free:** 500 emails per day
- **Google Workspace:** 2,000 emails per day

**Your usage:**
- 1 email per user approval
- 1 email per user denial
- Test emails

**Example:** If you approve 50 users/day = 50 emails (well within limits)

---

## 🚀 **Next Steps After Setup**

1. **Add your Gmail credentials** to `.streamlit/secrets.toml`
2. **Restart Streamlit** (`Ctrl+C` then `streamlit run main.py`)
3. **Test** from Admin Dashboard → Settings → Send Test Email
4. **Approve a test user** and verify they receive email
5. **Customize templates** (optional) in `utils/email_notifications.py`

---

## 📞 **Need Help?**

**Common questions:**

**Q: Can I use Outlook/Yahoo instead of Gmail?**  
A: Yes! Update these in secrets:
```toml
# Outlook
smtp_server = "smtp-mail.outlook.com"
smtp_port = 587

# Yahoo
smtp_server = "smtp.mail.yahoo.com"
smtp_port = 587
```

**Q: Can I send from a custom domain?**  
A: Yes, if you have Google Workspace or custom SMTP server.

**Q: What if email fails to send?**  
A: User is still approved/denied. Email failure won't block the action. Check SMTP logs.

**Q: How do I add CC or BCC?**  
A: Edit `send_email()` method in `email_notifications.py` and add CC/BCC fields.

---

## ✅ **Email Notifications Complete!**

You now have:
- ✅ Professional email templates
- ✅ Automatic notifications on approve/deny
- ✅ Test email feature in admin dashboard
- ✅ HTML + plain text fallback
- ✅ Error handling

**Configure your Gmail App Password and test it!** 🎉
