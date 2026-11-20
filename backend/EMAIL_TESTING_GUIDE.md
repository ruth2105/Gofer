# Email Testing Guide - GOFER EXAM

This guide explains how to configure and test email functionality in different environments.

---

## 📋 Table of Contents

1. [Email Backends Available](#email-backends-available)
2. [Development Setup](#development-setup)
3. [Staging Setup](#staging-setup)
4. [Testing Email Flows](#testing-email-flows)
5. [Troubleshooting](#troubleshooting)

---

## Email Backends Available

### 1. Console Backend (Default for Development)
**Best for:** Local development, debugging email content  
**Configuration:**
```env
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```
- Prints emails to console/terminal
- No actual email delivery
- No credentials required
- Useful for testing email content and templates

### 2. File Backend
**Best for:** Development when you need to review emails later  
**Configuration:**
```env
EMAIL_BACKEND=django.core.mail.backends.filebased.EmailBackend
EMAIL_FILE_PATH=/tmp/gofer-emails  # Or any directory you prefer
```
- Saves emails as `.eml` files to disk
- Can open files with email client to preview
- No actual email delivery

### 3. SMTP Backend (Gmail, SendGrid, etc.)
**Best for:** Staging, sending real test emails  
**Configuration for Gmail:**
```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-specific-password
GOFER_EMAIL_FROM=your-email@gmail.com
```

**Note for Gmail:** You must generate an "App Password" (not your regular password):
1. Go to Google Account Settings
2. Security → 2-Step Verification (must be enabled)
3. App passwords → Generate password for "Mail"
4. Use that 16-character password as `EMAIL_HOST_PASSWORD`

### 4. Brevo (SendinBlue) Backend
**Best for:** Production, staging with real transactional email  
**Configuration:**
```env
EMAIL_BACKEND=config.email_backends.brevo.BrevoEmailBackend
BREVO_API_KEY=xkeysib-your-api-key-here
GOFER_EMAIL_FROM=noreply@yourdomain.com
```

**Setup Steps:**
1. Sign up at [Brevo](https://www.brevo.com/) (free tier available)
2. Verify your sender email or domain
3. Get API key from Settings → SMTP & API → API Keys
4. Copy the key (starts with `xkeysib-`)

---

## Development Setup

### Option 1: Console Backend (Simplest)

**No configuration needed!** This is the default. Just start the server:

```bash
cd backend
python manage.py runserver
```

Emails will print to the console where the server is running.

**Test it:**
```bash
python manage.py shell
```
```python
from django.core.mail import send_mail
send_mail(
    'Test Subject',
    'Test message body',
    'from@example.com',
    ['to@example.com'],
)
# Check your console - you should see the email printed
```

### Option 2: File Backend (Review Emails Later)

Create a `.env` file in `backend/`:

```env
EMAIL_BACKEND=django.core.mail.backends.filebased.EmailBackend
EMAIL_FILE_PATH=./email_output
```

Restart the server and send a test email. Check `backend/email_output/` for `.eml` files.

### Option 3: Real Email with Gmail (Actual Delivery)

Create a `.env` file in `backend/`:

```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-personal-gmail@gmail.com
EMAIL_HOST_PASSWORD=your-16-char-app-password
GOFER_EMAIL_FROM=your-personal-gmail@gmail.com
```

**Gmail App Password Setup:**
1. Go to https://myaccount.google.com/security
2. Enable 2-Step Verification if not already enabled
3. Go to "App passwords" → Generate
4. Select "Mail" and your device
5. Copy the 16-character password (no spaces)
6. Use it as `EMAIL_HOST_PASSWORD`

**Test it:**
```bash
python manage.py shell
```
```python
from django.core.mail import send_mail
send_mail(
    'Test from Gofer Exam',
    'This is a test email from development.',
    'your-personal-gmail@gmail.com',
    ['your-personal-gmail@gmail.com'],  # Send to yourself for testing
)
# Check your Gmail inbox!
```

---

## Staging Setup

### Recommended: Use Brevo for Staging

Brevo offers a free tier with 300 emails/day, perfect for staging.

**1. Sign up for Brevo:**
- Visit https://www.brevo.com/
- Create a free account
- Verify your email address

**2. Verify Sender Email/Domain:**
- Go to Senders → Add a Sender
- Add your staging email (e.g., `staging@yourdomain.com`)
- Click the verification link sent to that email
- Or set up domain verification (SPF/DKIM) for better deliverability

**3. Get API Key:**
- Go to Settings → SMTP & API
- Click "Generate a new API key"
- Copy the key (format: `xkeysib-...`)

**4. Configure Staging Environment:**

Create `backend/.env.staging`:

```env
# Core settings
SECRET_KEY=your-staging-secret-key
ALLOWED_HOSTS=staging.yourdomain.com,staging-api.yourdomain.com
DATABASE_URL=postgres://user:pass@staging-db-host:5432/gofer_staging

# Frontend
GOFER_FRONTEND_URL=https://staging.yourdomain.com
CORS_ALLOWED_ORIGINS=https://staging.yourdomain.com
CSRF_TRUSTED_ORIGINS=https://staging.yourdomain.com

# Email - Brevo Configuration
EMAIL_BACKEND=config.email_backends.brevo.BrevoEmailBackend
BREVO_API_KEY=xkeysib-your-brevo-staging-key-here
GOFER_EMAIL_FROM=staging@yourdomain.com

# Security
AUTH_COOKIE_SECURE=True
```

**5. Test Email Delivery:**

```bash
# Connect to staging server
ssh your-staging-server

# Activate environment
cd /path/to/gofer-exam/backend
source venv/bin/activate

# Set environment
export DJANGO_SETTINGS_MODULE=config.settings.staging

# Test email
python manage.py shell
```

```python
from django.core.mail import send_mail
send_mail(
    'Staging Email Test',
    'If you receive this, Brevo is working!',
    'staging@yourdomain.com',
    ['your-test-email@example.com'],
)
```

Check your inbox (including spam folder).

---

## Testing Email Flows

### 1. Registration Email Verification

**Flow:**
1. User registers → Verification email sent
2. User clicks link → Account verified

**Test Script:**
```bash
# Option A: Test via API
curl -X POST http://localhost:8000/api/v1/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "testuser@example.com",
    "password": "SecurePass123!",
    "first_name": "Test",
    "last_name": "User"
  }'

# Check console/email for verification link
# Link format: http://localhost:3000/verify-email?token=<TOKEN>
```

**Option B: Test via Django Shell:**
```python
from django.contrib.auth import get_user_model
from apps.accounts.email_verification import send_verification_email

User = get_user_model()

# Create test user
user = User.objects.create_user(
    email='test@example.com',
    password='TestPass123!',
    first_name='Test',
    last_name='User'
)

# Send verification email
send_verification_email(user)

# Check console/email for the verification link
```

**Expected Email:**
- **Subject:** Verify your GOFER EXAM account
- **Body:** Contains verification link
- **Link:** Should work when clicked (redirects to frontend)

### 2. Password Reset Email

**Test via API:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/password/reset/ \
  -H "Content-Type: application/json" \
  -d '{"email": "testuser@example.com"}'
```

**Test via Django Shell:**
```python
from django.contrib.auth import get_user_model
from apps.accounts.password_reset import send_password_reset_email

User = get_user_model()
user = User.objects.get(email='test@example.com')

send_password_reset_email(user)
# Check console/email for reset link
```

**Expected Email:**
- **Subject:** Reset your GOFER EXAM password
- **Body:** Contains reset link
- **Link:** Should redirect to frontend password reset form

### 3. Application Status Notification

When application status changes, users should receive notification emails.

**Test:**
```python
from apps.applications.models import Application
from django.contrib.auth import get_user_model

User = get_user_model()

# Get or create test user and application
user = User.objects.get(email='test@example.com')
application = Application.objects.filter(student=user.student_profile).first()

# Update application status
application.status = 'UNDER_REVIEW'
application.save()

# Check if email was sent
```

### 4. Bulk Email Test

**Test multiple emails quickly:**
```python
from django.core.mail import send_mass_mail

messages = [
    ('Subject 1', 'Body 1', 'from@example.com', ['user1@example.com']),
    ('Subject 2', 'Body 2', 'from@example.com', ['user2@example.com']),
    ('Subject 3', 'Body 3', 'from@example.com', ['user3@example.com']),
]

send_mass_mail(messages, fail_silently=False)
```

---

## Troubleshooting

### Issue: "Email delivery failed" with Brevo

**Check:**
1. **API Key valid?**
   ```python
   from django.conf import settings
   print(settings.BREVO_API_KEY)  # Should start with 'xkeysib-'
   ```

2. **Sender email verified?**
   - Go to Brevo dashboard → Senders
   - Ensure sender is verified (green checkmark)

3. **API Key has permission?**
   - Some keys may be restricted
   - Create a new unrestricted key

4. **Rate limit exceeded?**
   - Brevo free tier: 300 emails/day
   - Check your usage in Brevo dashboard

### Issue: SMTP authentication failed (Gmail)

**Check:**
1. **Using App Password?**
   - Regular password won't work
   - Must generate App Password

2. **2-Step Verification enabled?**
   - Required for App Passwords
   - Enable at: https://myaccount.google.com/security

3. **"Less secure apps" blocked?**
   - Google deprecated this
   - Use App Passwords instead

### Issue: Emails go to spam

**Solutions:**
1. **Set up SPF record** for your domain
   ```
   v=spf1 include:_spf.brevo.com ~all
   ```

2. **Set up DKIM** in Brevo dashboard
   - Go to Settings → Senders
   - Click "Authenticate your domain"
   - Add DNS records provided

3. **Use verified sender email**
   - Emails from unverified addresses often flagged

4. **Test with mail-tester.com**
   - Send email to address provided by mail-tester
   - Get deliverability score and recommendations

### Issue: Console backend not showing emails

**Check:**
1. **Running development server?**
   ```bash
   python manage.py runserver
   ```
   Emails only show in the terminal where server is running

2. **EMAIL_BACKEND set correctly?**
   ```python
   from django.conf import settings
   print(settings.EMAIL_BACKEND)
   # Should be: django.core.mail.backends.console.EmailBackend
   ```

3. **Check for errors:**
   ```python
   from django.core.mail import send_mail
   try:
       send_mail('Test', 'Body', 'from@example.com', ['to@example.com'])
       print("Email sent!")
   except Exception as e:
       print(f"Error: {e}")
   ```

### Issue: Timeout errors with SMTP

**Check:**
1. **Firewall blocking port 587?**
   ```bash
   telnet smtp.gmail.com 587
   # Should connect successfully
   ```

2. **Increase timeout:**
   ```env
   EMAIL_TIMEOUT=30  # Increase from default 10
   ```

3. **Try port 465 with SSL:**
   ```env
   EMAIL_PORT=465
   EMAIL_USE_SSL=True
   EMAIL_USE_TLS=False
   ```

### Debug Email Settings

**Print all email-related settings:**
```python
from django.conf import settings

print(f"EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
print(f"EMAIL_HOST: {settings.EMAIL_HOST}")
print(f"EMAIL_PORT: {settings.EMAIL_PORT}")
print(f"EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
print(f"EMAIL_USE_SSL: {settings.EMAIL_USE_SSL}")
print(f"EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
print(f"DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")

# For Brevo
if hasattr(settings, 'BREVO_API_KEY'):
    key = settings.BREVO_API_KEY
    print(f"BREVO_API_KEY: {key[:10]}...{key[-4:] if len(key) > 14 else ''}")
```

---

## Quick Reference: Environment Variables

### Development (Console - Default)
```env
# No configuration needed!
# Emails print to console automatically
```

### Development (Real Email - Gmail)
```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
GOFER_EMAIL_FROM=your-email@gmail.com
```

### Staging/Production (Brevo)
```env
EMAIL_BACKEND=config.email_backends.brevo.BrevoEmailBackend
BREVO_API_KEY=xkeysib-your-api-key
GOFER_EMAIL_FROM=noreply@yourdomain.com
```

### Production (SMTP)
```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=SG.your-sendgrid-api-key
GOFER_EMAIL_FROM=noreply@yourdomain.com
```

---

## Additional Resources

- **Django Email Documentation:** https://docs.djangoproject.com/en/5.0/topics/email/
- **Brevo Documentation:** https://developers.brevo.com/
- **Gmail SMTP:** https://support.google.com/mail/answer/7126229
- **SendGrid SMTP:** https://docs.sendgrid.com/for-developers/sending-email/integrating-with-the-smtp-api
- **Email Tester:** https://www.mail-tester.com/
- **SPF Record Checker:** https://mxtoolbox.com/spf.aspx

---

**Need Help?**
- Check Django logs for detailed error messages
- Test with `python manage.py sendtestemail your@email.com`
- Use Django shell to test email sending interactively
- Review Brevo/SMTP provider's logs for delivery status
