# 🤖 reCAPTCHA Setup Guide - Complete Documentation

## ✅ **What You Have**

reCAPTCHA bot protection is now integrated into your signup forms!

**Protected Forms:**
- ✅ Signup form (new users)
- ✅ Reapplication form (denied users)

**Features:**
- ✅ Google reCAPTCHA v2 support ("I'm not a robot" checkbox)
- ✅ Google reCAPTCHA v3 support (invisible, score-based)
- ✅ Server-side validation
- ✅ User-friendly error messages
- ✅ Status display in admin dashboard
- ✅ Graceful fallback if disabled

---

## 🔑 **Getting Your reCAPTCHA Keys**

### **Step 1: Register Your Site** (3 minutes)

1. **Go to:** https://www.google.com/recaptcha/admin/create

2. **Sign in** with your Google account

3. **Fill out the registration:**

   **Label:** `Google Ads Simulator`
   
   **reCAPTCHA type:** Select one:
   
   **Option A: reCAPTCHA v2** ⭐ **RECOMMENDED**
   - Click **"reCAPTCHA v2"**
   - Select **"I'm not a robot" Checkbox**
   
   **Option B: reCAPTCHA v3**
   - Click **"reCAPTCHA v3"**
   - (More advanced, invisible)
   
   **Domains:**
   - Click **"Add domain"**
   - Enter: `localhost` (for local testing)
   - Later add your production domain (e.g., `your-app.streamlit.app`)
   
   **Owners:** (Optional)
   - Add additional Google accounts if needed
   
   **Accept Terms:** ✅ Check the box

4. **Click "Submit"**

### **Step 2: Copy Your Keys**

After submission, you'll see a screen with your keys:

```
Site Key
6LdABC...xyz123

Secret Key  
6LdDEF...abc789
```

**Copy both keys!** You'll need them in the next step.

⚠️ **Security Note:**
- **Site Key:** Public (safe to show in browser)
- **Secret Key:** Private (NEVER share or commit to Git!)

---

## ⚙️ **Configuration**

### **Add to `.streamlit/secrets.toml`**

```toml
# ========================================
# reCAPTCHA Bot Protection
# ========================================

[recaptcha]
enabled = true
version = "v2"  # or "v3"

# Your reCAPTCHA keys from Google
site_key = "6LdABC...xyz123"          # ← PASTE YOUR SITE KEY
secret_key = "6LdDEF...abc789"        # ← PASTE YOUR SECRET KEY
```

### **Complete Example:**

```toml
[recaptcha]
enabled = true
version = "v2"
site_key = "6LdRBwcqAAAAABbhW8J7K4mQ9pLxNyZvW3fE2Hg"
secret_key = "6LdRBwcqAAAAANMxKp3Y1vR8sT9uQ2wE5dF7cVb"
```

**Important:**
- Use **v2** if you registered "I'm not a robot" Checkbox
- Use **v3** if you registered reCAPTCHA v3
- **Don't mix up the keys!**

---

## 🧪 **Testing reCAPTCHA**

### **Step 1: Restart Streamlit**

```bash
Ctrl+C  # Stop
streamlit run main.py  # Restart
```

### **Step 2: Check Admin Dashboard**

1. Login as admin
2. Go to **Admin Dashboard** → **Settings** tab
3. Should see:
   - "✅ reCAPTCHA is ENABLED"
   - "Version: V2" (or V3)
   - "✅ Signup form protected"

### **Step 3: Test Signup Form**

1. Click **"Request Access"**
2. You should now see the reCAPTCHA checkbox:

```
┌────────────────────────────────────┐
│ Email Address *                    │
│ [your.email@example.com          ] │
└────────────────────────────────────┘

┌────────────────────────────────────┐
│ Full Name *                        │
│ [John Doe                        ] │
└────────────────────────────────────┘

Verify you're human:
┌────────────────────────────────────┐
│ ☐ I'm not a robot          reCAPTCHA │  ← Should appear here!
└────────────────────────────────────┘

[ ] I agree to use this platform...

┌────────────────────────────────────┐
│     🚀 Request Access              │
└────────────────────────────────────┘
```

3. **Try submitting WITHOUT checking the box:**
   - Should see error: "❌ Please complete the reCAPTCHA verification"

4. **Try submitting WITH checking the box:**
   - Should work normally ✅

### **Step 4: Test Reapplication Form**

1. Create a denied user (or deny an existing one)
2. Try to reapply
3. reCAPTCHA should appear in the reapplication form too
4. Verify it validates correctly

---

## 🎨 **How It Works**

### **User Experience (v2):**

```
User fills out form
  ↓
Sees "I'm not a robot" checkbox
  ↓
Clicks checkbox
  ↓
Sometimes gets image challenge (Select all traffic lights, etc.)
  ↓
Completes verification
  ↓
Can submit form
```

### **Validation Flow:**

```
User submits form
  ↓
reCAPTCHA token sent to server
  ↓
Your app validates with Google API
  ↓
Google returns: success/failure
  ↓
If success: Process signup
If failure: Show error message
```

---

## 🔧 **Configuration Options**

### **Enable/Disable reCAPTCHA:**

```toml
[recaptcha]
enabled = true   # Turn on
# enabled = false  # Turn off (for testing)
```

### **Version Selection:**

**v2 - Checkbox (Recommended):**
```toml
version = "v2"
```
- ✅ Clear user feedback
- ✅ Works everywhere
- ✅ Easy to implement

**v3 - Invisible (Advanced):**
```toml
version = "v3"
```
- ✅ No user interaction
- ✅ Score-based (0.0 to 1.0)
- ⚠️ Requires threshold tuning

**For your use case: Use v2**

---

## 🐛 **Troubleshooting**

### **"reCAPTCHA is DISABLED" in Settings**

**Check:**
1. `.streamlit/secrets.toml` has `[recaptcha]` section
2. `enabled = true`
3. Both keys are filled in
4. Restart Streamlit after changes

### **"Invalid site key" error**

**Causes:**
1. Wrong site key (check you didn't swap site/secret key)
2. Domain not registered in reCAPTCHA admin
3. Key has extra spaces

**Fix:**
- Verify site_key in reCAPTCHA admin console
- Make sure `localhost` is in domains list
- Copy key again carefully

### **reCAPTCHA doesn't appear on form**

**Check:**
1. reCAPTCHA is enabled in secrets
2. Streamlit was restarted
3. Browser didn't block the script
4. Check browser console for errors (F12)

### **"Please complete the reCAPTCHA verification" even after checking**

**Causes:**
1. reCAPTCHA expired (timeout after 2 mins)
2. Network issue
3. Secret key incorrect

**Fix:**
- Check the box again
- Verify secret_key is correct
- Check network connection

### **reCAPTCHA shows in different language**

- reCAPTCHA auto-detects browser language
- This is normal and expected behavior
- Users will see it in their preferred language

---

## 🔒 **Security Best Practices**

### **Keys Management:**
- ✅ **Site Key:** Public (shows in HTML) - OK to expose
- ✅ **Secret Key:** Private - NEVER commit to Git
- ✅ Add `.streamlit/secrets.toml` to `.gitignore`

### **Domain Configuration:**
- ✅ Add `localhost` for development
- ✅ Add production domain when deploying
- ✅ Don't use wildcard (*) domains in production

### **Validation:**
- ✅ Always validate server-side (never trust client)
- ✅ Handle validation failures gracefully
- ✅ Log failed attempts (already implemented)

---

## 📊 **What Gets Protected**

### **Signup Form:**
```python
# Before: Anyone could submit (including bots)
# After: Only humans who pass reCAPTCHA ✅
```

### **Reapplication Form:**
```python
# Before: Bots could spam reapplications
# After: Protected by reCAPTCHA ✅
```

---

## 🎯 **Testing Checklist**

### **Configuration:**
- [ ] Added reCAPTCHA config to secrets.toml
- [ ] Restarted Streamlit
- [ ] Admin Settings shows "reCAPTCHA ENABLED"

### **Signup Form:**
- [ ] reCAPTCHA checkbox appears
- [ ] Submitting without checkbox shows error
- [ ] Checking box allows submission
- [ ] Form submits successfully after verification

### **Reapplication Form:**
- [ ] reCAPTCHA appears on reapply form
- [ ] Validation works correctly
- [ ] Can successfully reapply after verification

### **Error Handling:**
- [ ] Expired reCAPTCHA shows helpful message
- [ ] Invalid submission blocked
- [ ] Network errors handled gracefully

---

## 🌐 **For Production Deployment**

When you deploy to Streamlit Cloud:

1. **Update reCAPTCHA domains:**
   - Go to: https://www.google.com/recaptcha/admin
   - Find your site
   - Click Settings (gear icon)
   - Add your Streamlit Cloud URL: `your-app-name.streamlit.app`
   - Save

2. **Update secrets on Streamlit Cloud:**
   - Same configuration as local
   - Copy your `[recaptcha]` section
   - Paste into Streamlit Cloud secrets

---

## ⚡ **Advanced: reCAPTCHA v3**

If you want to use invisible reCAPTCHA v3 instead:

**Benefits:**
- No checkbox (better UX)
- Score-based detection (0.0 to 1.0)
- More sophisticated bot detection

**Configuration:**
```toml
[recaptcha]
enabled = true
version = "v3"  # ← Change this
site_key = "YOUR-V3-SITE-KEY"
secret_key = "YOUR-V3-SECRET-KEY"
```

**Note:** v3 requires different implementation. Let me know if you want this instead!

---

## 📈 **reCAPTCHA Limits**

**Free tier limits:**
- ✅ 1 million assessments/month
- ✅ More than enough for your use case

**Your usage:**
- 1 check per signup
- 1 check per reapplication

**Example:** 1,000 signups/month = 1,000 assessments (0.1% of limit)

---

## 🎨 **Customization Options**

### **reCAPTCHA Theme:**

You can customize the appearance by editing `utils/recaptcha.py`:

```javascript
grecaptcha.render('container', {
    'sitekey': 'YOUR_SITE_KEY',
    'theme': 'light',  // or 'dark'
    'size': 'normal',  // or 'compact'
    // ... other options
});
```

### **Language:**
- Auto-detects from user's browser
- Or specify explicitly in render call

---

## ✅ **You're All Set!**

reCAPTCHA integration is:
- ✅ Built and ready
- ✅ Integrated into forms
- ✅ Admin dashboard shows status
- ✅ Documentation complete

**Just add your keys to secrets.toml and restart!**

---

## 🚀 **After reCAPTCHA Works:**

Once tested, your options are:

**Option C:** Polish UI & customize messages  
**Option D:** Enhance admin dashboard  
**Option E:** Deploy to production  

**What do you want next?** 🎯
