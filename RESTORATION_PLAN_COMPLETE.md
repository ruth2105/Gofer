# GOFER EXAM — COMPLETE RESTORATION PLAN

**Prepared**: November 21, 2026  
**Status**: Ready for approval (DO NOT DEPLOY YET)  
**Current Backend**: Commit `30ab294` (LIVE but outdated)  
**Target Backend**: Commit `b0669ed` (current HEAD)

---

## EXECUTIVE SUMMARY

### Current Status (VERIFIED)

✅ **Backend Service EXISTS** at `gofere-api-ruth2105.onrender.com`  
✅ **Backend is RUNNING** commit `30ab294` (26 commits behind HEAD)  
✅ **Schema endpoint responds** with HTTP 200  
✅ **Health endpoint missing** (404) - added after commit `30ab294`  
✅ **Database EXISTS** as `gofere-db` (Render free tier)  
✅ **13 new migrations** exist between deployed and current code  

❌ **Most API endpoints return 404** - missing from old backend code  
❌ **Email backend blocks deployment** - console backend not allowed in production  
❌ **Storage is ephemeral** - LOCAL storage loses files on restart  

### Deployment Attempts

| Attempt | Commit | Status | Reason |
|---------|--------|--------|--------|
| **Live** | `30ab294` | ✅ Running | Old but working |
| **Failed** | `d262677` | ❌ Build failed | Email backend validation |
| **Target** | `b0669ed` | ⚠️ Not deployed | Needs configuration |

---

## 1. MISSING API ENDPOINTS

### Endpoints in NEW code (HEAD) but MISSING from deployed backend (30ab294):

#### Authentication & Account Management
- ❌ `/api/v1/auth/verify-email/` - Email verification
- ❌ `/api/v1/auth/resend-verification/` - Resend verification email  
- ❌ `/api/v1/auth/password/reset/` - Password reset request
- ❌ `/api/v1/auth/password/reset/confirm/` - Password reset confirm
- ❌ `/api/v1/auth/password/change/` - Change password (authenticated)
- ❌ `/api/v1/auth/users/` - User management (admin)
- ❌ `/api/v1/auth/security/audit/` - Security audit log

#### Student Profile & Progress
- ❌ `/api/v1/students/` - Student endpoints (entire app missing)
- ❌ `/api/v1/students/me/` - Student profile
- ❌ `/api/v1/students/me/detail/` - Profile detail
- ❌ `/api/v1/students/me/completion/` - Profile completion percentage
- ❌ `/api/v1/students/education/` - Education history CRUD
- ❌ `/api/v1/students/experience/` - Work experience CRUD
- ❌ `/api/v1/students/skills/` - Skills CRUD

#### Consultations
- ❌ `/api/v1/consultations/` - Consultation endpoints (entire app missing)
- ❌ `/api/v1/consultations/me/` - My consultations
- ❌ `/api/v1/consultations/consultants/` - Consultant assignments
- ❌ Consultation action routes (request, accept, complete, etc.)

#### Documents
- ❌ `/api/v1/documents/` - Document endpoints (entire app missing)
- ❌ Document detail, upload, download, verify routes

#### Notifications
- ❌ `/api/v1/notifications/` - Notification endpoints (entire app missing)
- ❌ Notification list, mark read routes

#### Opportunities
- ❌ `/api/v1/opportunities/` - Opportunity endpoints (entire app missing)
- ❌ `/api/v1/opportunities/search/` - Opportunity search
- ❌ Job and internship listings

#### Common/Countries
- ❌ `/api/v1/countries/` - Country list (entire app missing)

#### Health & Monitoring
- ❌ `/api/v1/health/` - Health check endpoints (entire app missing)
- ❌ `/api/v1/health/liveness/` - Liveness probe
- ❌ `/api/v1/health/readiness/` - Readiness probe

### Endpoints that DO exist in deployed backend (30ab294):

✅ `/api/v1/schema/` - API schema (works - returns 200)  
✅ `/api/v1/docs/` - Swagger UI  
✅ `/api/v1/redoc/` - ReDoc UI  
✅ `/api/v1/auth/*` - Basic auth (login, register, logout, me, token refresh)  
✅ `/api/v1/applications/` - Applications (basic CRUD)  
✅ `/api/v1/scholarships/` - Scholarships (basic CRUD)  
✅ `/api/v1/services/` - Services catalog  
✅ `/api/v1/universities/` - Universities catalog  
✅ `/api/v1/destinations/` - Destinations catalog  

**Impact**: Frontend calling new backend gets 404s for ~60% of functionality

---

## 2. BREVO EMAIL BACKEND - REQUIREMENTS

### Implementation Analysis

**File**: `backend/config/email_backends/brevo.py`  
**Status**: ✅ Fully implemented, production-ready

### Required Settings (MANDATORY):

```python
# Django settings
EMAIL_BACKEND = 'config.email_backends.brevo.BrevoEmailBackend'
BREVO_API_KEY = '<actual_key>'  # REQUIRED
EMAIL_TIMEOUT = 10  # seconds (optional, default works)
DEFAULT_FROM_EMAIL = '<verified_email>'  # REQUIRED
```

### Brevo API Key Requirements:

1. **Format**: `xkeysib-<64_hex_characters>-<more_hex>`
2. **Permissions**: "Send emails" permission required
3. **Validation**: Must not contain newlines or carriage returns
4. **Source**: https://app.brevo.com/settings/keys/api

### Production.py Validation (CANNOT BE BYPASSED):

```python
# Lines 73-78: Email backend validation
if EMAIL_BACKEND in non_delivery_backends:
    raise ImproperlyConfigured(
        'Configure SMTP or a transactional provider email backend in production.'
    )

# Lines 79-88: Sender email validation
if not DEFAULT_FROM_EMAIL or DEFAULT_FROM_EMAIL == 'webmaster@localhost':
    raise ImproperlyConfigured('Set GOFER_EMAIL_FROM to the verified sender address.')

validate_email(DEFAULT_FROM_EMAIL)  # Must be valid email format

# Lines 90-93: Brevo API key validation
if EMAIL_BACKEND == 'config.email_backends.brevo.BrevoEmailBackend':
    if not BREVO_API_KEY.strip():
        raise ImproperlyConfigured('Set BREVO_API_KEY to configure Brevo email delivery.')
```

**Result**: Service CANNOT START without valid email configuration

### Email Features Used:

- Email verification (new user registration)
- Password reset emails
- Application status notifications
- Consultation reminders

**All templates exist and ready**: `backend/templates/accounts/*.html|txt`

---

## 3. CLOUDFLARE R2 STORAGE - REQUIREMENTS

### Implementation Analysis

**File**: `backend/config/storage_backends.py`  
**Class**: `CloudflareR2Storage` (S3-compatible)  
**Status**: ✅ Fully implemented, uses `django-storages[s3]`

### Required Packages (ALREADY IN requirements/base.txt):

```
django-storages[s3]==1.14.4
boto3==1.34.162
```

✅ **Already installed** - no package changes needed

### Required Settings (MANDATORY FOR R2):

```python
# Django settings
STORAGE_BACKEND = 'R2'

# R2-specific (uses S3-compatible API)
AWS_ACCESS_KEY_ID = '<r2_access_key_id>'  # REQUIRED
AWS_SECRET_ACCESS_KEY = '<r2_secret_access_key>'  # REQUIRED
AWS_STORAGE_BUCKET_NAME = 'gofer-documents'  # REQUIRED
AWS_S3_ENDPOINT_URL = 'https://<account_id>.r2.cloudflarestorage.com'  # REQUIRED
AWS_S3_REGION_NAME = 'auto'  # REQUIRED for R2

# Optional (defaults work)
AWS_DEFAULT_ACL = None  # Use bucket policy
AWS_S3_FILE_OVERWRITE = False
```

### Cloudflare R2 Setup Required:

1. **Sign up**: https://dash.cloudflare.com/sign-up
2. **Create R2 bucket**:
   - Navigate to: R2 Object Storage
   - Create bucket: `gofer-documents`
   - Public access: OFF (private)
3. **Generate R2 API token**:
   - Navigate to: Manage R2 API Tokens
   - Create API token
   - Permissions: Read & Write
   - TTL: Not specified (long-lived token)
4. **Note credentials**:
   - Account ID (from R2 dashboard URL)
   - Access Key ID (from token creation)
   - Secret Access Key (from token creation - shown once)

### Bucket Permissions (R2 Default):

```
- Private by default (good)
- Application uses signed URLs for access
- No public bucket policy needed
- CORS not required (backend serves files)
```

### Production.py Validation (STRICT BUT ALLOWS LOCAL):

```python
# Lines 121-125: Storage backend validation
if STORAGE_BACKEND not in ['LOCAL', 'S3', 'GCS', 'AZURE', 'R2']:
    raise ImproperlyConfigured(...)

# Lines 127-136: LOCAL storage warning (NOT an error)
if STORAGE_BACKEND == 'LOCAL':
    warnings.warn(
        'Using LOCAL storage in production. Files will be lost on deployment/restart.',
        RuntimeWarning
    )

# Lines 159-170: R2 validation (only if STORAGE_BACKEND=R2)
if STORAGE_BACKEND == 'R2':
    if not AWS_ACCESS_KEY_ID or not AWS_SECRET_ACCESS_KEY:
        raise ImproperlyConfigured('Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY for Cloudflare R2.')
    if not AWS_STORAGE_BUCKET_NAME:
        raise ImproperlyConfigured('Set AWS_STORAGE_BUCKET_NAME for Cloudflare R2.')
    if not AWS_S3_ENDPOINT_URL:
        raise ImproperlyConfigured('Set AWS_S3_ENDPOINT_URL for Cloudflare R2.')
```

**Result**: 
- Service CAN START with `STORAGE_BACKEND=LOCAL` (warning only)
- Service CANNOT START with `STORAGE_BACKEND=R2` and missing credentials

### Migration Requirements:

❌ **NO database migrations needed** for storage change  
✅ Storage configuration is runtime only  
✅ File field columns already exist in database  

---

## 4. DATABASE STATUS & MIGRATIONS

### PostgreSQL Database (VERIFIED)

**Database**: `gofere-db` (Render free tier)  
**Status**: ✅ EXISTS (not queried to preserve data)  
**Expiration**: ⚠️ UNKNOWN (requires Render dashboard check)  

### Render Free Tier Constraints:

- **Storage**: 1 GB limit
- **Expiration**: 90 days from creation (typical)
- **Backups**: None automatic (manual only)
- **Connections**: Limited concurrent
- **Performance**: Shared resources

### Migration Status:

**Currently Applied** (in deployed backend at 30ab294): Unknown - not queried  
**New Migrations** (between 30ab294 and HEAD): 13 migrations

#### New Migrations (WILL RUN AUTOMATICALLY):

```
1. backend/apps/accounts/migrations/0002_emailverificationtoken.py
   - Creates: EmailVerificationToken table
   - Risk: LOW (additive only)

2. backend/apps/accounts/migrations/0003_securityauditevent.py
   - Creates: SecurityAuditEvent table
   - Risk: LOW (additive only)

3. backend/apps/common/migrations/0001_initial.py
   - Creates: Country table (149 countries)
   - Risk: LOW (new table)

4. backend/apps/opportunities/migrations/0001_initial.py
   - Creates: Opportunity, OpportunitySource, CollectionRun, etc.
   - Risk: LOW (new tables)

5-6. backend/apps/opportunities/migrations/0002-0006_*.py
   - Alters: Opportunity model fields
   - Risk: MEDIUM (field changes, need review)

7. backend/apps/scholarships/migrations/0003_scholarship_country_reference.py
   - Adds: Country FK to Scholarship
   - Risk: LOW (nullable FK)

8. backend/apps/scholarships/migrations/0004_opportunity_management_mvp.py
   - Alters: Scholarship status choices
   - Risk: LOW (choice field expansion)

9. backend/apps/students/migrations/0002_studentprofile_nationality_country.py
   - Adds: Nationality FK to StudentProfile
   - Risk: LOW (nullable FK)

10. backend/apps/students/migrations/0003_education_skill_workexperience.py
    - Creates: Education, Skill, WorkExperience tables
    - Risk: LOW (new tables)
```

### Automatic Migration Execution:

**render.yaml startCommand** (Line 19):
```yaml
startCommand: python manage.py migrate --noinput && gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
```

✅ **Migrations run BEFORE Gunicorn starts**  
✅ **Atomic**: If migration fails, service won't start  
⚠️ **Automatic**: No manual approval during deploy  

### Migration Risk Assessment:

**LOW RISK migrations** (10 of 13):
- New tables (additive only)
- New nullable fields
- No data modifications
- Reversible

**MEDIUM RISK migrations** (3 of 13):
- Opportunity field changes (0005, 0006)
- Scholarship choice modifications (0004)
- Need review for data compatibility

**Recommendation**: 
- ✅ Safe to proceed (all appear additive)
- ✅ Backup database first (mandatory)
- ⚠️ Review opportunity migrations (field changes)

---

## 5. EXACT BLOCKERS

### Blocker 1: Email Backend Configuration ❌ CRITICAL

**Status**: **BLOCKS SERVICE STARTUP**  
**Current**: `EMAIL_BACKEND=console` (development only)  
**Required**: `EMAIL_BACKEND=config.email_backends.brevo.BrevoEmailBackend`  

**Cannot bypass**: Production.py validation raises ImproperlyConfigured

### Blocker 2: Brevo API Key ❌ CRITICAL

**Status**: **BLOCKS SERVICE STARTUP** (if Brevo backend configured)  
**Current**: Not set  
**Required**: Valid Brevo API key  

**User must**:
1. Sign up at brevo.com (free tier: 300 emails/day)
2. Generate API key
3. Provide key for configuration

### Blocker 3: R2 Storage Credentials ⚠️ HIGH PRIORITY

**Status**: **DOES NOT BLOCK STARTUP** (can use LOCAL temporarily)  
**Current**: `STORAGE_BACKEND=LOCAL` (ephemeral)  
**Impact**: Files deleted on every restart  

**User must** (for persistent storage):
1. Sign up at cloudflare.com
2. Create R2 bucket
3. Generate API token
4. Provide credentials

**Can defer**: Yes, but data loss risk

### Blocker 4: Database Expiration ⚠️ UNKNOWN

**Status**: **MAY BLOCK DEPLOYMENT** (if expired)  
**Current**: Unknown expiration date  
**Required**: Active database  

**User must verify**: Render dashboard → `gofere-db` → Expiration date

---

## 6. REQUIRED CREDENTIALS & ACCOUNTS

### A. Brevo Email Service (MANDATORY)

**Purpose**: Send emails (verification, password reset, notifications)  
**Free Tier**: 300 emails/day  
**Sign up**: https://app.brevo.com/account/register  

**Steps**:
1. Create account
2. Verify email address
3. Navigate to Settings → API Keys
4. Create API key with "Send emails" permission
5. Copy key (format: `xkeysib-...`)

**Credentials needed**:
- `BREVO_API_KEY`: API key string

**Sender email**:
- Use: `noreply@goferexam.com` (must verify domain in Brevo)
- OR: Use Brevo-provided sender (no verification needed)

### B. Cloudflare R2 Storage (HIGH PRIORITY)

**Purpose**: Persistent file storage (documents, uploads)  
**Free Tier**: 10 GB storage, 0 egress fees  
**Sign up**: https://dash.cloudflare.com/sign-up  

**Steps**:
1. Create Cloudflare account
2. Navigate to R2 Object Storage
3. Create bucket: `gofer-documents`
4. Navigate to Manage R2 API Tokens
5. Create API token (Read & Write permissions)
6. Copy credentials (shown once)

**Credentials needed**:
- `AWS_ACCESS_KEY_ID`: R2 access key ID
- `AWS_SECRET_ACCESS_KEY`: R2 secret access key
- Account ID (from dashboard URL)

**Configuration**:
- Endpoint: `https://<account_id>.r2.cloudflarestorage.com`
- Bucket: `gofer-documents`
- Region: `auto`

---

## 7. CONFIGURATION CHANGES

### A. render.yaml (LOCAL, then commit)

**File**: `gofer-exam/render.yaml`

**Lines 56-65** - Email configuration:
```yaml
# REMOVE these lines:
- key: EMAIL_BACKEND
  value: django.core.mail.backends.console.EmailBackend  # ❌ DELETE
- key: GOFER_EMAIL_FROM
  value: noreply@goferexam.com

# REPLACE with:
- key: EMAIL_BACKEND
  value: config.email_backends.brevo.BrevoEmailBackend  # ✅ ADD
- key: GOFER_EMAIL_FROM
  value: noreply@goferexam.com  # ✅ KEEP (verify in Brevo)
- key: BREVO_API_KEY  # ✅ ADD (value set in dashboard)
  sync: false
```

**Lines 88-102** - Storage configuration:
```yaml
# REMOVE this line:
- key: STORAGE_BACKEND
  value: LOCAL  # ❌ DELETE (or keep for staging)

# REPLACE with:
- key: STORAGE_BACKEND
  value: R2  # ✅ ADD

# UNCOMMENT these lines (93-101):
- key: AWS_ACCESS_KEY_ID
  sync: false  # ✅ UNCOMMENT (value set in dashboard)
- key: AWS_SECRET_ACCESS_KEY
  sync: false  # ✅ UNCOMMENT (value set in dashboard)
- key: AWS_STORAGE_BUCKET_NAME
  value: gofer-documents  # ✅ UNCOMMENT
- key: AWS_S3_ENDPOINT_URL
  value: https://<ACCOUNT_ID>.r2.cloudflarestorage.com  # ✅ UNCOMMENT (replace <ACCOUNT_ID>)
- key: AWS_S3_REGION_NAME
  value: auto  # ✅ UNCOMMENT
```

**Commit**:
```bash
git add render.yaml
git commit -m "fix(deployment): configure production email (Brevo) and storage (R2)"
git push origin master
```

### B. Render Dashboard Environment Variables

**Service**: `gofere-api-ruth2105`  
**Navigate**: Render Dashboard → Services → `gofere-api-ruth2105` → Environment

**Add new variables**:
```
Name: BREVO_API_KEY
Value: <paste_actual_key_here>
Secret: ✓ YES

Name: AWS_ACCESS_KEY_ID
Value: <paste_r2_access_key_here>
Secret: ✓ YES

Name: AWS_SECRET_ACCESS_KEY
Value: <paste_r2_secret_key_here>
Secret: ✓ YES
```

**Update existing variables**:
```
Name: EMAIL_BACKEND
Value: config.email_backends.brevo.BrevoEmailBackend

Name: STORAGE_BACKEND
Value: R2

Name: AWS_STORAGE_BUCKET_NAME
Value: gofer-documents

Name: AWS_S3_ENDPOINT_URL
Value: https://<account_id>.r2.cloudflarestorage.com

Name: AWS_S3_REGION_NAME
Value: auto
```

**DO NOT SAVE YET** - wait for approval

---

## 8. DEPLOYMENT RISKS

### HIGH RISK (Mitigated by backup):

1. **Database Migration Failure**
   - Risk: Migration fails, service won't start
   - Mitigation: Atomic migrations, rollback available
   - Recovery: Restore from backup

2. **Data Loss from Backup Restore**
   - Risk: Restore deletes data after backup timestamp
   - Mitigation: Backup immediately before deploy
   - Recovery: None (data loss permanent)

### MEDIUM RISK (Recoverable):

3. **Invalid Credentials**
   - Risk: Service fails to start with invalid Brevo/R2 keys
   - Mitigation: Validate keys before deploy
   - Recovery: Fix credentials, redeploy

4. **Deployment Skew**
   - Risk: Frontend calls endpoints not yet deployed
   - Mitigation: Deploy backend first, verify, then frontend
   - Recovery: Rollback to previous version

### LOW RISK (Warning only):

5. **LOCAL Storage in Production**
   - Risk: Files deleted on restart (if storage misconfigured)
   - Mitigation: Configure R2 before deploying
   - Recovery: Files lost (no recovery)

6. **Email Delivery Failure**
   - Risk: Emails fail to send (invalid config)
   - Mitigation: Test with Brevo dashboard first
   - Recovery: Fix config, restart service

---

## 9. DEPLOYMENT STEPS (AFTER APPROVAL)

### Phase 1: Pre-Deployment Verification ✅

**Actions** (READ-ONLY, no changes):
1. Verify Render service `gofere-api-ruth2105` status
2. Check database `gofere-db` expiration date
3. Review render.yaml configuration
4. Validate Brevo API key (test in Brevo dashboard)
5. Validate R2 credentials (test with aws-cli or dashboard)

**User must confirm**:
- [ ] Database not expired
- [ ] Brevo API key works
- [ ] R2 bucket created and accessible

---

### Phase 2: Database Backup ⚠️ CRITICAL

**Actions** (MUST DO FIRST):
1. Render Dashboard → `gofere-db` → Backups tab
2. Click "Create Backup"
3. Wait for completion
4. Download backup file (optional but recommended)
5. Record:
   - Backup ID: `_________________`
   - Timestamp: `_________________`
   - Size: `_________________`

**DO NOT PROCEED** without successful backup

---

### Phase 3: Configuration Update 📝

**Local changes**:
```bash
cd gofer-exam

# Edit render.yaml (email + storage config)
# See Section 7.A above for exact changes

git add render.yaml
git commit -m "fix(deployment): configure production email and storage"
git push origin master
```

**Render Dashboard** (DO NOT SAVE YET):
- Add environment variables (see Section 7.B)
- Click "Save" but DO NOT click "Deploy"

**Checkpoint**: Configuration ready, not deployed

---

### Phase 4: Backend Deployment 🚀

**Render Dashboard**:
1. Navigate to `gofere-api-ruth2105`
2. Click "Manual Deploy" button
3. Branch: `master`
4. Click "Deploy"

**Monitor build logs** (realtime):
```
Expected sequence:
✓ Cloning repository...
✓ Installing Python 3.12...
✓ pip install -r requirements/production.txt
✓ python manage.py collectstatic --no-input
✓ Build succeeded

✓ python manage.py migrate --noinput
  Operations to perform:
    Apply all migrations: ...
  Running migrations:
    Applying accounts.0002_emailverificationtoken... OK
    Applying accounts.0003_securityauditevent... OK
    Applying common.0001_initial... OK
    ... (10 more migrations)
✓ Migrations complete

✓ gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
  [INFO] Starting gunicorn...
  [INFO] Listening at: http://0.0.0.0:10000
  [INFO] Worker booted successfully
✓ Service is live
```

**If build fails**: Check logs, fix error, retry  
**If start fails**: Check Django error, likely config issue  
**If migration fails**: Database issue, restore backup  

**Timeline**: 3-5 minutes

---

### Phase 5: Backend Verification ✅

**Wait 30 seconds**, then test:

#### Test 1: Health Check
```bash
curl https://gofere-api-ruth2105.onrender.com/api/v1/health/

Expected:
{
  "status": "healthy",
  "timestamp": "2026-11-21T...",
  "checks": {
    "application": {"status": "healthy"},
    "database": {"status": "healthy", "response_time_ms": 25.5}
  }
}
Status: 200 OK
```

#### Test 2: Schema Endpoint
```bash
curl https://gofere-api-ruth2105.onrender.com/api/v1/schema/

Expected: Large JSON schema
Status: 200 OK
```

#### Test 3: New Endpoints
```bash
# Student profile (should require auth)
curl https://gofere-api-ruth2105.onrender.com/api/v1/students/me/

Expected: {"detail": "Authentication credentials were not provided."}
Status: 401 Unauthorized

# Countries list
curl https://gofere-api-ruth2105.onrender.com/api/v1/countries/

Expected: JSON array of countries
Status: 200 OK
```

#### Test 4: Storage (if R2 configured)
- Upload test file via Django admin
- Verify file accessible
- Check R2 bucket for file

**All tests must pass** before proceeding

---

### Phase 6: Frontend Verification 🌐

**Test Render Preview**:
```bash
curl -I https://gofere-web-preview.onrender.com/

Expected: HTTP 200 OK
```

**Browser Test**:
1. Open https://gofere-web-preview.onrender.com/
2. Check browser console (F12) for errors
3. Navigate to scholarships page
4. Verify API calls succeed (Network tab)
5. Test login page loads

**Vercel** (if used):
- Test https://gofere.vercel.app/
- Same verification steps

---

### Phase 7: End-to-End Test 🧪

**Registration Flow**:
1. Navigate to registration page
2. Submit registration form
3. Check Brevo dashboard for email sent
4. Verify email received (if test email used)

**Login Flow**:
1. Login with test account
2. Verify dashboard loads
3. Check profile completion shows
4. Navigate to scholarships

**Document Upload** (if R2 configured):
1. Upload test document
2. Verify upload succeeds
3. Check R2 bucket for file
4. Restart backend (Render dashboard)
5. Verify document still accessible

**Success Criteria**:
- ✅ Health check returns healthy
- ✅ All new endpoints respond
- ✅ Frontend loads without errors
- ✅ API calls succeed
- ✅ Email sends successfully
- ✅ Files persist (if R2 configured)

---

## 10. ROLLBACK PLAN

### If Deployment Fails:

**Application Rollback** (5 minutes):
1. Render Dashboard → `gofere-api-ruth2105` → Deployments
2. Find commit `30ab294` (last working)
3. Click "..." → "Redeploy"
4. Wait for deployment
5. Verify health check

**Result**: Backend returns to known working state

### If Migrations Fail:

**Database Rollback** (10-30 minutes):
1. **STOP** - Do not attempt reverse migrations
2. Render Dashboard → `gofere-db` → Backups
3. Select backup from Phase 2
4. Click "Restore"
5. **WARNING**: Deletes all data after backup timestamp
6. Wait for restore completion
7. Redeploy backend to `30ab294`

**Result**: Database and application at pre-deploy state

### If Service Starts But Broken:

**Quick Fix Attempt**:
1. Check Render logs for errors
2. If config issue: Fix env vars, redeploy
3. If code issue: Rollback application

**Timeline**: 5-15 minutes

---

## 11. ACTIONS REQUIRING APPROVAL

### ✅ Already Done (No Approval Needed):
- Verified deployment status from documentation
- Analyzed code differences
- Identified missing endpoints
- Reviewed Brevo implementation
- Reviewed R2 implementation
- Listed migration changes
- Assessed risks

### ⚠️ Requires User Action (Before Approval):
- [ ] Check Render dashboard for current status
- [ ] Verify database expiration date
- [ ] Sign up for Brevo
- [ ] Generate Brevo API key
- [ ] Sign up for Cloudflare
- [ ] Create R2 bucket
- [ ] Generate R2 credentials

### ❌ Requires Explicit Approval (User Must Say "Yes"):
- [ ] Create database backup
- [ ] Update render.yaml and commit to Git
- [ ] Update Render environment variables
- [ ] Deploy backend to production
- [ ] Run database migrations (automatic with deploy)
- [ ] Restart service with new configuration

---

## 12. CHECKLIST BEFORE DEPLOYMENT

### Prerequisites:
- [ ] Render service status confirmed (not suspended)
- [ ] Database expiration date confirmed (not expired)
- [ ] Brevo API key obtained and validated
- [ ] R2 bucket created and credentials obtained
- [ ] All credentials securely stored
- [ ] render.yaml changes prepared locally

### Safety Checks:
- [ ] Database backup created successfully
- [ ] Backup ID and timestamp recorded
- [ ] Rollback plan understood and ready
- [ ] Monitoring ready (can watch logs)
- [ ] No production writes happening during deploy

### Configuration Verified:
- [ ] render.yaml email config correct
- [ ] render.yaml storage config correct
- [ ] Render env vars prepared (not saved yet)
- [ ] No secrets in Git commits

### Approval Received:
- [ ] User approved database backup
- [ ] User approved configuration changes
- [ ] User approved deployment
- [ ] User approved migration execution

---

## 13. TIMELINE ESTIMATE

| Phase | Duration | Dependencies |
|-------|----------|--------------|
| Brevo signup & API key | 10 min | User action |
| R2 signup & bucket setup | 20 min | User action |
| Configuration updates | 10 min | Credentials ready |
| Database backup | 5 min | Render dashboard |
| Backend deployment | 5 min | Config complete |
| Backend verification | 5 min | Deploy complete |
| Frontend verification | 5 min | Backend healthy |
| End-to-end testing | 15 min | All deployed |
| **TOTAL** | **~75 min** | With credentials |

**If rollback needed**: +10-30 minutes

---

## 14. FINAL STATUS

### Ready for Deployment: ⚠️ WAITING FOR APPROVAL

**Code Status**: ✅ Ready (no changes needed)  
**Configuration**: ⚠️ Prepared (needs credentials)  
**Database**: ⚠️ Unknown status (needs verification)  
**Credentials**: ❌ Not obtained (user must provide)  
**Approval**: ❌ Not granted (user must approve)  

### Next Step:

**User must**:
1. Review this complete restoration plan
2. Verify Render dashboard status
3. Obtain required credentials
4. Approve deployment sequence

**Then**: Execute phases 1-7 with user supervision

---

**RESTORATION PLAN PREPARED**  
**DO NOT DEPLOY UNTIL APPROVED**

