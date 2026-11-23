# P0-3: Production Email Configuration Guide

## Overview

Gofer Exam uses a custom Brevo (formerly Sendinblue) email backend for transactional emails. This document covers production configuration, security requirements, and the API key rotation process.

---

## Email Backend Implementation

**Location**: `backend/config/email_backends/brevo.py`

### Features
- **Protocol**: HTTPS API (port 443)
- **Endpoint**: `api.brevo.com/v3/smtp/email`
- **Supported**: Plain text, HTML, CC/BCC, reply-to, file attachments (base64)
- **Error Handling**: Sanitized error messages (no sensitive data exposed)
- **Timeout**: Configurable via `EMAIL_TIMEOUT` setting

### Test Coverage
**Location**: `backend/config/email_backends/tests.py`

9 comprehensive tests covering:
1. ✅ Plain text messages with finite timeout
2. ✅ Integration with Django's `send_test_email` command
3. ✅ Multiple recipients, CC, BCC, reply-to
4. ✅ HTML alternatives
5. ✅ File attachments (base64 encoding)
6. ✅ API failure handling (sanitized errors)
7. ✅ Unexpected error handling (no sensitive data leakage)
8. ✅ Missing API key validation
9. ✅ `fail_silently` flag behavior

**Test Command**:
```powershell
# Activate virtual environment first
.\venv\Scripts\Activate.ps1

# Run Brevo backend tests only
python manage.py test config.email_backends.tests

# Run all email-related tests
python manage.py test --pattern="*email*"
```

---

## Production Configuration

### Required Environment Variables

```bash
# Brevo API Configuration
BREVO_API_KEY=xkeysib-xxxxxxxxxxxxxxxxxxxx  # REQUIRED: Brevo API key
EMAIL_BACKEND=config.email_backends.brevo.BrevoEmailBackend

# Email Settings
DEFAULT_FROM_EMAIL=noreply@goferexam.com
EMAIL_TIMEOUT=30  # Seconds (default: 30)
DEFAULT_CHARSET=utf-8

# Authorized operators for test emails (comma-separated)
GOFER_TEST_EMAIL_AUTHORIZED_OPERATORS=admin,devops
```

### Django Settings

**File**: `backend/config/settings/production.py`

```python
# Email Backend
EMAIL_BACKEND = env('EMAIL_BACKEND', default='config.email_backends.brevo.BrevoEmailBackend')
BREVO_API_KEY = env('BREVO_API_KEY', default='')
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='noreply@goferexam.com')
EMAIL_TIMEOUT = env.int('EMAIL_TIMEOUT', default=30)

# Validate critical email settings
if not BREVO_API_KEY:
    raise ImproperlyConfigured('BREVO_API_KEY environment variable is required in production')
```

---

## Security: API Key Rotation

### ⚠️ CRITICAL: Exposed API Key

**Issue**: The BREVO_API_KEY was previously committed to version control and must be rotated immediately.

### Rotation Process

#### 1. Generate New API Key (Brevo Dashboard)

1. Log in to [Brevo](https://app.brevo.com)
2. Navigate to: **SMTP & API** → **API Keys**
3. Click **Generate a new API key**
4. Name: `gofer-exam-production-2026-11`
5. Permissions: **Send emails** (minimum required)
6. Copy the key immediately (shown only once)

#### 2. Update Production Environment

**Render.com (Current Deployment)**:
```bash
# Via Render Dashboard
1. Go to your web service
2. Environment → Edit
3. Update BREVO_API_KEY value
4. Save Changes (triggers automatic redeploy)

# Via Render CLI
render env set BREVO_API_KEY="xkeysib-NEW_KEY_HERE" --service=gofer-exam-backend
```

**Alternative Deployment (AWS/GCP/Azure)**:
- Store in **AWS Secrets Manager** / **GCP Secret Manager** / **Azure Key Vault**
- Update environment variable reference
- Restart application

#### 3. Delete Old API Key

1. Return to Brevo → **API Keys**
2. Find the old key
3. Click **Delete**
4. Confirm deletion

#### 4. Verify Email Delivery

```bash
# Test email functionality
python manage.py send_test_email recipient@example.com operator=admin

# Check logs for successful delivery
```

### API Key Best Practices

- ✅ **Never commit API keys** to version control
- ✅ **Use environment variables** for all secrets
- ✅ **Rotate keys quarterly** or after any exposure
- ✅ **Use separate keys** for staging/production environments
- ✅ **Set minimum permissions** (e.g., only "Send emails")
- ✅ **Monitor API usage** in Brevo dashboard for anomalies

---

## Email Usage in Application

### Current Email Flows

1. **Email Verification** (`backend/apps/users/utils/email_verification.py`)
   - Sent when: User registers
   - Template: Plain text with verification link
   - Sender: `DEFAULT_FROM_EMAIL`

2. **Password Reset** (`backend/apps/users/utils/password_reset.py`)
   - Sent when: User requests password reset
   - Template: Plain text with reset link
   - Sender: `DEFAULT_FROM_EMAIL`

3. **Test Emails** (`backend/apps/users/management/commands/send_test_email.py`)
   - Sent when: Admin tests email configuration
   - Requires: Authorized operator name
   - Purpose: Verify production email delivery

### Adding New Email Types

```python
from django.core.mail import EmailMultiAlternatives

# Basic plain text email
message = EmailMultiAlternatives(
    subject='Your Exam Results',
    body='Congratulations! You passed.',
    from_email='noreply@goferexam.com',
    to=['student@example.com'],
)
message.send()

# HTML email with plain text fallback
message = EmailMultiAlternatives(
    subject='Your Exam Results',
    body='Congratulations! You passed.',
    from_email='noreply@goferexam.com',
    to=['student@example.com'],
)
message.attach_alternative('<p>Congratulations! You <strong>passed</strong>.</p>', 'text/html')
message.send()

# Email with attachment
message = EmailMultiAlternatives(
    subject='Exam Certificate',
    body='Your certificate is attached.',
    from_email='noreply@goferexam.com',
    to=['student@example.com'],
)
message.attach('certificate.pdf', pdf_content, 'application/pdf')
message.send()
```

---

## Monitoring & Troubleshooting

### Brevo Dashboard Metrics

Monitor these metrics in [Brevo Dashboard](https://app.brevo.com):

- **Sent**: Total emails accepted by Brevo
- **Delivered**: Successfully delivered to recipient
- **Bounced**: Invalid email address or delivery failure
- **Opened**: Recipient opened the email (requires HTML tracking)
- **Clicked**: Recipient clicked a link (requires link tracking)

### Common Issues

#### Issue: Emails not being sent
```bash
# Check API key is set
python manage.py shell
>>> from django.conf import settings
>>> settings.BREVO_API_KEY
'xkeysib-...'  # Should show your key (masked in logs)

# Check backend is configured
>>> settings.EMAIL_BACKEND
'config.email_backends.brevo.BrevoEmailBackend'

# Test connection
>>> from django.core.mail import send_mail
>>> send_mail('Test', 'Body', 'noreply@goferexam.com', ['your@email.com'])
1  # Success: returns number of emails sent
```

#### Issue: "Email delivery failed" error
- **Cause**: Invalid API key, network timeout, Brevo service outage
- **Fix**: Check API key validity, increase `EMAIL_TIMEOUT`, check [Brevo status](https://status.brevo.com)

#### Issue: Emails going to spam
- **Cause**: Missing SPF/DKIM records, suspicious content
- **Fix**: 
  1. Configure SPF record: `v=spf1 include:spf.brevo.com ~all`
  2. Configure DKIM in Brevo → Settings → Senders & IP
  3. Avoid spam trigger words in subject/body

---

## Cost Estimation

### Brevo Pricing (as of 2026)

**Free Plan**:
- 300 emails/day
- ✅ Suitable for: Development, staging, low-traffic production

**Lite Plan** ($25/month):
- 10,000 emails/month + pay-as-you-go
- $0.50 per 1,000 additional emails
- ✅ Suitable for: Small to medium production deployments

**Business Plan** ($65/month):
- 20,000 emails/month + pay-as-you-go
- $0.40 per 1,000 additional emails
- ✅ Suitable for: High-traffic production deployments

**Estimated Monthly Costs** (based on volume):
- 500 users × 2 emails/month = 1,000 emails → **Free Plan** (Free)
- 5,000 users × 2 emails/month = 10,000 emails → **Lite Plan** ($25/month)
- 20,000 users × 2 emails/month = 40,000 emails → **Business Plan** ($65 + $8 overage = $73/month)

---

## Testing Strategy

### Local Development

Use Django's **Console backend** for local testing (no real emails sent):

```python
# backend/config/settings/local.py
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```

Emails will be printed to the console instead of sent.

### Staging Environment

Use Brevo with a **separate API key**:

```bash
# Staging environment variables
BREVO_API_KEY=xkeysib-STAGING_KEY_HERE
EMAIL_BACKEND=config.email_backends.brevo.BrevoEmailBackend
DEFAULT_FROM_EMAIL=staging@goferexam.com
```

### Production Environment

Use Brevo with **production API key** (rotated regularly):

```bash
# Production environment variables
BREVO_API_KEY=xkeysib-PRODUCTION_KEY_HERE
EMAIL_BACKEND=config.email_backends.brevo.BrevoEmailBackend
DEFAULT_FROM_EMAIL=noreply@goferexam.com
```

---

## Deployment Checklist

Before deploying to production:

- [ ] Generate new Brevo API key (production-specific)
- [ ] Set `BREVO_API_KEY` environment variable
- [ ] Set `EMAIL_BACKEND=config.email_backends.brevo.BrevoEmailBackend`
- [ ] Set `DEFAULT_FROM_EMAIL` (verified sender in Brevo)
- [ ] Configure SPF record for domain
- [ ] Configure DKIM in Brevo dashboard
- [ ] Test email delivery with `send_test_email` command
- [ ] Verify emails don't go to spam
- [ ] Set up email monitoring in Brevo dashboard
- [ ] Document API key rotation schedule (quarterly)

---

## Compliance & Privacy

### Data Processing

Brevo processes the following data:
- **Recipient email addresses** (stored for 90 days)
- **Email content** (plain text and HTML)
- **Attachments** (if any)
- **Sender information** (configured in Django)

### GDPR Compliance

- ✅ Brevo is GDPR-compliant (EU-based company)
- ✅ Data processing agreement available
- ✅ Recipient data can be deleted on request
- ✅ No tracking pixels by default (configurable)

### User Privacy

- **Do not send** sensitive personal information in email bodies
- **Use secure links** for password resets (time-limited tokens)
- **Encrypt attachments** if containing sensitive data
- **Respect unsubscribe requests** (add unsubscribe link for marketing emails)

---

## Next Steps (Post-Deployment)

1. **Monitor email metrics** in Brevo dashboard daily for first week
2. **Set up alerts** for high bounce rates (>5%)
3. **Review spam reports** and adjust content if needed
4. **Schedule quarterly API key rotation** (calendar reminder)
5. **Consider email templates** (Brevo templates for branded emails)

---

## References

- [Brevo API Documentation](https://developers.brevo.com/docs/send-email-with-api)
- [Django Email Documentation](https://docs.djangoproject.com/en/5.0/topics/email/)
- [Brevo Status Page](https://status.brevo.com)
- [SPF Configuration Guide](https://www.brevo.com/blog/spf-record/)

---

## Summary

**P0-3 Status**: ✅ **READY FOR PRODUCTION** (after API key rotation)

- ✅ Custom Brevo email backend implemented
- ✅ Comprehensive test coverage (9 tests with mocked HTTP)
- ✅ Error handling with sanitized messages
- ✅ Configuration documented
- ⚠️ **ACTION REQUIRED**: Rotate exposed API key immediately before deployment
- ✅ Monitoring and troubleshooting guide provided
- ✅ Cost estimation and scaling considerations documented

**Next**: P0-4 (Deployment configuration) and P0-5 (Health checks & monitoring)
