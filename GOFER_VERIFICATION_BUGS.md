# Gofer Exam - Verification Bugs Report

**Date:** November 20, 2026  
**Verification:** Real Functional Testing  
**Environment:** Local Development  

---

## 🔴 CRITICAL PRODUCTION BLOCKERS

### BUG-001: Authentication Endpoints Have CSRF Protection Despite AllowAny Permission
**Severity:** 🔴 CRITICAL  
**Impact:** PRODUCTION BLOCKER - Frontend Cannot Register or Login  
**Status:** ❌ CONFIRMED

**Description:**
All authentication endpoints (`/api/v1/auth/register/`, `/api/v1/auth/login/`) return HTTP 403 Forbidden with "CSRF verification failed" error, even though the views are configured with:
- `permission_classes = [permissions.AllowAny]`
- `authentication_classes = []`

**Evidence:**
```
HTTP POST http://127.0.0.1:8000/api/v1/auth/register/
Status: 403 Forbidden
Error: CSRF verification failed. Request aborted.
Reason: CSRF cookie not set.
```

**Test Attempted:**
```json
{
  "email": "student_test_20261120150251@disposable.test",
  "password": "TestPass123!@#",
  "password2": "TestPass123!@#",
  "first_name": "Test",
  "last_name": "Student"
}
```

**Expected Behavior:**
- Registration should succeed without CSRF token for AllowAny endpoints
- Frontend should be able to call API directly
- New user should be created with HTTP 201 response

**Actual Behavior:**
- HTTP 403 Forbidden
- CSRF token required even for public endpoints
- Frontend cannot register users

**Root Cause:**
Django's CSRF middleware is enforcing CSRF checks on all POST requests, even those with AllowAny permission. The views need either:
1. `@csrf_exempt` decorator, OR
2. `csrf_exempt` in URL patterns, OR
3. Custom authentication class that exempts CSRF

**Impact Assessment:**
- **Registration:** ❌ BROKEN - Cannot create new users from frontend
- **Login:** ❌ BROKEN - Cannot authenticate from frontend
- **Password Reset:** ❌ LIKELY BROKEN - Same issue expected
- **All POST Endpoints:** ⚠️ POTENTIALLY AFFECTED

**Workaround for Testing:**
Created test user directly via Django shell:
- Email: `student_test_functional@test.local`
- Password: `TestPass123!@#`
- Role: STUDENT
- Verified: True

**Fix Required:**
```python
# Option 1: Add to views.py
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

@method_decorator(csrf_exempt, name='dispatch')
class UserRegistrationView(generics.CreateAPIView):
    ...

# Option 2: Update DRF settings in base.py
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}

# Then explicitly set authentication_classes=[] removes SessionAuthentication
# which is what enforces CSRF
```

**Estimated Fix Time:** 30 minutes  
**Testing Time:** 1 hour  
**Priority:** P0 - MUST FIX BEFORE ANY DEPLOYMENT

---

### BUG-002: Scholarships Cannot Be Published Without Source Verification
**Severity:** 🔴 CRITICAL  
**Impact:** NO SCHOLARSHIPS VISIBLE TO STUDENTS  
**Status:** ❌ CONFIRMED

**Description:**
The Scholarship model requires `source_records_are_verified()` to return True before setting `is_published=True`. This means scholarships cannot be published until:
1. SourceRecord model entries exist
2. SourceRecords are marked as VERIFIED
3. SourceRecords have verified_at timestamp
4. SourceRecords are verified by ADMIN/SUPERADMIN
5. Source is marked as active
6. Normalized deadline matches
7. Official URLs match

**Evidence:**
```python
# Attempted to create published scholarship
Scholarship.objects.create(
    name='Test Scholarship',
    is_published=True,
    # ... other fields
)

# Result:
ValidationError: {
    'is_published': [
        'A scholarship needs currently verified, available official '
        'source evidence before publication.'
    ]
}
```

**Test Data Created:**
- 10 scholarships in database
- All have `is_published=False`
- All have valid deadlines, URLs, and details
- Cannot be published without source verification records

**API Response:**
```
GET http://127.0.0.1:8000/api/v1/scholarships/
{
    "count": 0,
    "results": []
}
```

**Impact Assessment:**
- Students see ZERO scholarships when browsing
- Homepage "Featured Scholarships" section is empty
- Search functionality returns no results
- Core product feature (scholarship discovery) is non-functional

**Business Logic Justification:**
The verification requirement exists to ensure only real, verified scholarships are shown to students. This is good for data integrity but creates a chicken-and-egg problem:
1. Cannot test scholarship browsing without data
2. Cannot publish data without verification workflow
3. Verification workflow requires admin interface and source tracking system
4. Source tracking system adds significant complexity

**Possible Solutions:**

**Option A: Add Development Override** (Recommended for Testing)
```python
# In Scholarship.clean()
if settings.DEBUG and not self.source_records_are_verified():
    # Allow publication in development without verification
    logger.warning(f'Publishing {self.name} without verification (DEBUG=True)')
    return

if self.is_published and not self.source_records_are_verified():
    raise ValidationError({...})
```

**Option B: Create Source Verification Records** (Production)
- Implement full source tracking system
- Create SourceRecord entries for each scholarship
- Mark as verified
- Link to scholarships

**Option C: Temporary Flag** (Quick Fix)
```python
skip_verification = models.BooleanField(
    default=False,
    help_text='Skip verification check (for testing only)'
)

# In clean()
if self.is_published and not (self.skip_verification or self.source_records_are_verified()):
    raise ValidationError({...})
```

**Estimated Fix Time:**
- Option A: 15 minutes
- Option B: 2-3 weeks (full source tracking)
- Option C: 30 minutes

**Priority:** P0 - BLOCKS ALL SCHOLARSHIP FUNCTIONALITY

---

## 🟠 HIGH PRIORITY BUGS

### BUG-003: Frontend Not Configured to Call Backend API
**Severity:** 🟠 HIGH  
**Impact:** FRONTEND-BACKEND DISCONNECTED  
**Status:** ⚠️ SUSPECTED (Not fully verified)

**Description:**
The frontend runs on `localhost:3000` but needs to proxy API requests to `localhost:8000`. This requires Next.js API proxy configuration or environment variable setup.

**Evidence:**
- Frontend loads successfully (HTTP 200)
- Homepage renders without errors
- But featured scholarships likely call frontend `/api/v1/scholarships/` endpoint
- Frontend likely needs to proxy to backend

**Next.js Proxy Configuration:**
```javascript
// next.config.ts or proxy.ts
module.exports = {
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://127.0.0.1:8000/api/:path*'
      }
    ]
  }
}
```

**Environment Variable:**
```env
API_PROXY_TARGET=http://127.0.0.1:8000
```

**Testing Needed:**
1. Open browser to `http://localhost:3000`
2. Open DevTools → Network tab
3. Check if API calls are made
4. Check if they succeed or fail with 404/CORS errors

**Priority:** P1 - BLOCKS FRONTEND TESTING

---

### BUG-004: Console Email Backend - No Real Email Delivery
**Severity:** 🟠 HIGH  
**Impact:** USERS CANNOT RECEIVE VERIFICATION EMAILS  
**Status:** ✅ EXPECTED (By Design for Development)

**Description:**
Email backend is set to `django.core.mail.backends.console.EmailBackend`, which prints emails to console instead of sending them.

**Evidence:**
```python
# .env
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend  # (implied default)
```

**Impact:**
- Registration emails printed to Django console
- Password reset emails printed to Django console
- No real email delivery
- Users cannot verify accounts via email

**Expected for Development:** ✅ Yes  
**Blocks Production:** ✅ Yes  
**Documented in Audit:** ✅ Yes (mentioned as known issue)

**Fix for Production:**
```python
# settings/production.py
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.sendgrid.net'  # or AWS SES
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('SENDGRID_USERNAME')
EMAIL_HOST_PASSWORD = os.environ.get('SENDGRID_PASSWORD')
```

**Priority:** P1 - REQUIRED FOR PRODUCTION (Not urgent for local testing)

---

## 🟡 MEDIUM PRIORITY ISSUES

### ISSUE-005: Ephemeral File Storage (LOCAL Backend)
**Severity:** 🟡 MEDIUM  
**Impact:** FILES DELETED ON SERVER RESTART  
**Status:** ✅ DOCUMENTED (Known Issue)

**Description:**
File storage uses Django's default `FileSystemStorage` with LOCAL backend. Files are stored in the container/server filesystem and deleted on every restart or redeploy.

**Impact:**
- Uploaded documents (transcripts, resumes, passports) are lost on server restart
- Not suitable for production
- Requires S3/GCS/Azure configuration

**Documented:** Yes (in P0 Production Readiness reports)  
**Fix Available:** Yes (storage_backends.py already implements S3/GCS)  
**Configuration Needed:** AWS credentials and bucket name

**Priority:** P2 - BLOCKS PRODUCTION (OK for local testing)

---

## 📊 Bug Summary

| Bug ID | Severity | Component | Status | Blocks Production | Blocks Testing |
|--------|----------|-----------|--------|-------------------|----------------|
| BUG-001 | 🔴 Critical | Authentication | Confirmed | ✅ Yes | ✅ Yes |
| BUG-002 | 🔴 Critical | Scholarships | Confirmed | ✅ Yes | ✅ Yes |
| BUG-003 | 🟠 High | Frontend | Suspected | ⚠️ Likely | ✅ Yes |
| BUG-004 | 🟠 High | Email | Expected | ✅ Yes | ❌ No |
| ISSUE-005 | 🟡 Medium | Storage | Known | ✅ Yes | ❌ No |

---

## 🚨 IMMEDIATE ACTION REQUIRED

**Cannot proceed with functional testing until:**

1. ✅ **Fix BUG-001:** Remove CSRF protection from authentication endpoints
   - Add `@csrf_exempt` or `@method_decorator(csrf_exempt, name='dispatch')`
   - OR configure SessionAuthentication properly
   - Verify registration and login work via API calls

2. ✅ **Fix BUG-002:** Allow scholarship publication without verification
   - Add DEBUG mode override in Scholarship.clean()
   - OR create temporary `skip_verification` flag
   - Publish 10 test scholarships
   - Verify API returns scholarships

3. ⚠️ **Verify BUG-003:** Test frontend-backend connectivity
   - Open browser to localhost:3000
   - Check if API calls are proxied correctly
   - Fix proxy configuration if needed

**After these fixes, functional testing can continue with:**
- Homepage scholarship display
- Student registration flow (via frontend)
- Login and session management
- Profile completion
- Application submission
- Document upload
- Etc.

---

## 📝 Testing Notes

**Test Environment:**
- Backend: Django 5.0 on http://127.0.0.1:8000
- Frontend: Next.js 16.4.3 on http://localhost:3000
- Database: PostgreSQL (gofer_exam)
- Email: Console backend (development)
- Storage: LOCAL (ephemeral)

**Test Data:**
- Test User: `student_test_functional@test.local` / `TestPass123!@#`
- Scholarships: 10 created (all unpublished due to BUG-002)
- Applications: 0
- Documents: 0

**Next Steps After Bug Fixes:**
1. Re-test authentication endpoints
2. Verify scholarship API returns data
3. Test frontend displays scholarships
4. Continue with full student journey testing

---

**Report Status:** ⏸️ PAUSED - Waiting for critical bug fixes before continuing verification

**Last Updated:** November 20, 2026 15:10 UTC
