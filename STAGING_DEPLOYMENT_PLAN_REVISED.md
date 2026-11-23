# Gofer Exam Platform - Staging Deployment Plan (REVISED v2.0)

**Date:** November 2, 2026  
**Revision:** 2.0 - Addresses all critical concerns  
**Status:** Awaiting Approval - NO ACTIONS TAKEN  

---

## ⚠️ CRITICAL UPDATES - Must Read

This revision addresses four critical issues with accurate, verified information:

1. **Database Cost:** Free PostgreSQL expires after **30 days** (not 90 days) + 14-day grace period
2. **Storage Reality:** LOCAL storage is ephemeral - files deleted on EVERY restart/redeploy  
3. **Vercel 404:** Separated diagnosis for homepage vs API proxy failures
4. **Email Security:** Console backend logs contain verification tokens - test accounts only

---

## Executive Summary

**What This Plan Does:**
- Deploy isolated staging environment (zero production impact)
- Test ALL functionality except file persistence and long-term storage
- Use free tiers with clear limitations and expiry dates
- Provide step-by-step manual instructions (no automatic deployment)

**What This Plan Costs:**
- **Days 1-30:** $0 (completely free)
- **Day 31+:** $7/month (database Starter plan) OR data loss
- **Vercel:** $0 forever (free tier sufficient)

**Time Required:**
- Setup: 1 hour (manual steps)
- Testing: 2-3 hours (comprehensive)
- **Total: 3-4 hours**

**Critical Deadlines:**
- **Day 30:** Free database expires
- **Day 44:** Database permanently deleted (no recovery)
- **Action:** Upgrade to $7/month OR accept data loss

---

## 1. Database Cost & Expiry (VERIFIED FACTS)

### 1.1 Render Free PostgreSQL - Official Policy

**Source:** [Render Changelog (May 20, 2024)](https://render.com/changelog/free-postgresql-instances-now-expire-after-30-days-previously-90)

```
Free Database Lifecycle:
├── Day 1-30:  Active (free, fully functional)
├── Day 31:    EXPIRED (grace period begins)
├── Day 31-44: Grace period (14 days)
│              - Database still accessible
│              - Must upgrade or data will be deleted
├── Day 45:    PERMANENTLY DELETED
└──            - No recovery possible
               - No backups available
```

**Costs (VERIFIED):**
```
Free Tier:
  Duration: 30 days + 14-day grace
  Storage:  1 GB
  Backups:  NONE
  Cost:     $0

Starter Plan:
  Duration: No expiry (permanent)
  Storage:  1 GB (expandable)
  Backups:  Daily (7-day retention)
  Cost:     $7/month

Upgrade:  Can be done anytime before day 45
Data:     Preserved when upgrading (no downtime)
```

### 1.2 Three Scenarios

**Scenario A: 30-Day Sprint (Recommended for Initial Testing)**
```
Plan:    Use free tier for 30 days
Day 28:  Export database backup manually
Day 30:  Database expires
Day 44:  Database deleted
Result:  $0 cost, data backed up, can recreate if needed
Risk:    Must complete testing within 30 days
```

**Scenario B: Upgrade Before Expiry (Recommended for Extended Testing)**
```
Plan:    Upgrade to Starter on day 25-29
Cost:    $0 for 30 days, then $7/month
Result:  Data preserved, no interruption
Risk:    Ongoing $7/month cost
```

**Scenario C: Recreate Cycle (Budget Option)**
```
Plan:    Export data day 28, let expire, create new free database day 31
Cost:    $0 (repeated 30-day cycles)
Result:  Manual backup/restore required
Risk:    Data loss if backup fails, manual effort
```

### 1.3 How to Preserve Data

**Option 1: Manual Backup (Before Day 30)**
```bash
# Create backup
pg_dump -h <render-host> -U <user> -d gofer_exam_staging \
  -F custom -f staging_backup_$(date +%Y%m%d).dump

# Verify backup
pg_restore --list staging_backup_20261102.dump

# Store backup securely (local or cloud storage)
```

**Option 2: Upgrade to Starter**
```bash
# Render Dashboard → Database → Settings → Plan
# Select: Starter ($7/month)
# No downtime, data preserved automatically
```

### 1.4 Costs: What You WILL Pay

```
┌────────────────────────────────────────────────────┐
│ ACCURATE STAGING COSTS                             │
├──────────────┬──────────┬─────────────────────────┤
│ Component    │ Free     │ Paid (if chosen)        │
├──────────────┼──────────┼─────────────────────────┤
│ Backend      │ $0       │ $7/mo (always-on)       │
│ Database     │ $0×30d   │ $7/mo (after day 30)    │
│ Frontend     │ $0       │ $0 (free tier sufficient│
├──────────────┼──────────┼─────────────────────────┤
│ MINIMUM      │ $0×30d   │ $0/month                │
│ RECOMMENDED  │ $0×30d   │ $7/month (DB only)      │
│ ALWAYS-ON    │ $0×30d   │ $14/month (DB+Backend)  │
└──────────────┴──────────┴─────────────────────────┘

No hidden costs. No auto-charges. No credit card required for free tier.
```

---

## 2. Storage Limitations (CRITICAL REALITY)

### 2.1 Ephemeral Storage Explained

**What "Ephemeral" Actually Means:**
- Files stored in container filesystem (like `/tmp`)
- Container is DESTROYED on restart/redeploy
- ALL files in container are DELETED (no exceptions)
- New container starts with EMPTY filesystem
- Database is separate (NOT affected)

**Source:** [Render Docs - Persistent Disks](https://render.com/docs/disks): "Without a persistent disk, any changes you make to a service's local files are lost every time the service redeploys or restarts."

### 2.2 When Files Are Deleted

```
Event Triggering File Deletion:
├── Service spins down (after 15 min inactivity) → Files deleted
├── Service spins up (new container)            → Empty filesystem
├── Git push (new deployment)                   → Files deleted
├── Manual redeploy button clicked              → Files deleted
├── Service scaling                             → Files deleted
├── Platform maintenance                        → Files deleted
└── ANY restart for ANY reason                  → Files deleted

Frequency: Minimum every 15 minutes (free tier spin-down)
```

### 2.3 File Persistence Test (REQUIRED)

**Purpose:** Demonstrate ephemeral storage to team (educational test).

```bash
# PHASE 1: Upload and Verify
1. Login to staging
2. Upload document: test.pdf
3. Get file URL: https://gofere-api-staging.onrender.com/media/documents/test.pdf
4. Access URL → File accessible ✅
5. Check database → Record exists ✅

# PHASE 2: Trigger Restart
git commit --allow-empty -m "Test: Ephemeral storage demonstration"
git push origin main
# Wait 3-5 minutes for redeploy

# PHASE 3: Verify Deletion
6. Access same URL → 404 Not Found ❌ (EXPECTED)
7. Check database → Record still exists ✅
8. File path in database → Points to deleted file
9. Try downloading → Fails (file gone)

✅ TEST PASSES if file is deleted
❌ TEST FAILS if file persists (unexpected)
```

### 2.4 What Can vs Cannot Be Tested

**✅ CAN Test (Functional Behavior):**
- File upload endpoint works
- File validation (type, size)
- Authorization (who can upload/download)
- Database record creation
- Error handling
- UI/UX of upload flow
- Immediate file access (before restart)

**❌ CANNOT Test (Persistence):**
- Long-term file storage
- File access after restart
- File availability between sessions
- CDN integration
- S3/GCS/Azure behavior
- Production file management

**For Production:**
- Files stored in S3/GCS/Azure (persistent)
- Files survive restarts/redeploys
- Costs ~$0.02/GB/month
- Configuration not included in this staging plan

---

## 3. Vercel 404 Diagnosis (EVIDENCE-BASED)

### 3.1 Two Separate Problems

**Problem A: Homepage 404**
```
Symptom:  https://gofere.vercel.app/ → "404: This page could not be found"
Cause:    Next.js build failure OR missing app/page.tsx
Fix:      Resolve build errors, verify files exist
NOT related to API_PROXY_TARGET
```

**Problem B: API Proxy 404**
```
Symptom:  API calls to /api/v1/* fail with 404
Cause:    API_PROXY_TARGET not set OR backend not responding
Fix:      Set API_PROXY_TARGET, verify backend URL
NOT related to homepage
```

### 3.2 Current Evidence Status

**KNOWN (From Code Review):**
- ✅ `next.config.ts` has rewrite configuration (lines 8-13)
- ✅ `API_PROXY_TARGET` environment variable used
- ✅ Rewrite sends `/api/v1/*` to `${apiProxyTarget}/*`
- ✅ Backend health endpoints exist

**UNKNOWN (Not Provided):**
- ❓ Which URL returns 404 (homepage or API)?
- ❓ Exact error message
- ❓ Browser console errors
- ❓ Network tab showing requests
- ❓ Vercel build logs
- ❓ Current Vercel environment variables

### 3.3 Proposed Fix (HYPOTHESIS)

**IF Problem is API Proxy 404:**
```bash
# Set in Vercel Dashboard → Environment Variables:
API_PROXY_TARGET=https://gofere-api-staging.onrender.com/api/v1

# Reasoning:
- next.config.ts uses this variable
- Rewrites API calls to backend
- Should fix API 404s

# Limitation:
- Does NOT fix homepage 404
- Only fixes API proxy issues
```

**IF Problem is Homepage 404:**
```bash
# API_PROXY_TARGET won't help
# Need to:
1. Check Vercel build logs for errors
2. Verify app/page.tsx exists
3. Fix TypeScript/ESLint errors
4. Redeploy with clean build
```

### 3.4 Diagnosis Procedure (BEFORE DEPLOYMENT)

**Step 1: Identify the 404**
```bash
# Test homepage
curl -I https://gofere.vercel.app/
# 200 = Homepage works
# 404 = Homepage broken (not API issue)

# Test API proxy
curl -I https://gofere.vercel.app/api/v1/health/liveness/
# 200 = Proxy works
# 404 = Proxy broken (API_PROXY_TARGET issue)
```

**Step 2: Collect Evidence**
```
□ Screenshot of 404 error
□ Browser console output (F12 → Console)
□ Network tab showing failed requests
□ Vercel build logs
□ Exact URL causing 404
```

**Step 3: Apply Targeted Fix**
```
IF homepage 404:
  → Fix Next.js build errors
  → NOT an API_PROXY_TARGET issue

IF API 404:
  → Set API_PROXY_TARGET
  → Set CORS headers in backend
  → Verify backend is running
```

**Recommendation:**
```
⚠️ Do NOT assume API_PROXY_TARGET fixes all 404s
✅ Diagnose first, then apply correct fix
✅ Homepage 404 ≠ API 404 (different root causes)
```

---

## 4. Email Security & Test Data Policy

### 4.1 Console Backend Security

**How It Works:**
```python
# Backend configuration
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Result:
- Emails logged to Render console (visible in logs)
- NOT sent to real email addresses
- Tokens visible in plain text in logs
- Anyone with Render dashboard access can see logs
```

**Security Implications:**
```
Threat:        Verification/reset tokens visible in logs
Exposure:      Anyone with Render dashboard access
Mitigation:    Use test accounts only, no real data
Risk Level:    LOW (staging only, test accounts)
Acceptable:    YES (for staging purposes)
```

### 4.2 Test Account Policy (MANDATORY)

**ONLY Use Test Accounts:**
```
✅ ALLOWED:
  test-student@example.com
  test-consultant@example.com
  staging-user-001@example.com
  john-test@example.com

❌ FORBIDDEN:
  Real user email addresses
  Personal email addresses  
  Client email addresses
  Company email addresses
  Any @gmail.com, @outlook.com with real names
```

**Test Data Guidelines:**
```
Names:      Test Student, Jane Test, John Staging
Emails:     *@example.com (reserved test domain)
Passwords:  TestPass123! (never use real passwords)
Documents:  test-passport.pdf, sample-transcript.pdf
Addresses:  123 Test Street, Staging City
Phone:      +1-555-0100 (reserved test numbers)
SSN/ID:     000-00-0000 (fake test numbers)
```

### 4.3 Token Extraction from Logs

**Process:**
```bash
# 1. User registers on staging
POST /api/v1/auth/register/
Body: { "email": "test@example.com", ... }

# 2. Check Render logs
Render Dashboard → gofere-api-staging → Logs

# 3. Find email log entry
INFO apps.accounts.email_verification send_verification_email
  Verification email accepted by backend for user_id=<uuid>

# Console email output (in logs):
Subject: Verify Your Gofer Exam Account
To: test@example.com
Body: Click here to verify:
https://gofere-staging.vercel.app/verify-email?token=abc123...

# 4. Extract token manually
TOKEN=abc123def456...

# 5. Verify email manually
POST /api/v1/auth/verify-email/
Body: { "token": "abc123def456..." }
```

**Security Checklist:**
```
□ ONLY test accounts used (never real users)
□ Tokens extracted manually from logs
□ No automated token extraction
□ Render dashboard access limited to team
□ Staging environment clearly labeled
□ Test data policy documented and followed
□ No real PII (personally identifiable information)
```

### 4.4 Email Testing Scenarios

**1. Registration Verification**
```
Action:  User registers
Result:  Verification email logged (not sent)
Verify:  Extract token from logs, call verify endpoint
Test:    Email content, token validity, link format
```

**2. Password Reset**
```
Action:  User requests password reset
Result:  Reset email logged (not sent)
Verify:  Extract token from logs, call reset endpoint
Test:    Email content, token validity, expiry (60 min)
```

**3. Email Delivery Failure**
```
Action:  Simulate email backend failure
Result:  Error logged (no email sent)
Verify:  Error handling, user feedback
Test:    Graceful degradation
```

---

## 5. Services and Exact Costs

### 5.1 Required Services

**Service 1: Render PostgreSQL (Database)**
```
Name:        gofere-db-staging
Type:        PostgreSQL 18
Plan:        Free
Duration:    30 days (expires day 30, deleted day 45)
Storage:     1 GB
Backups:     None
Cost:        $0 for 30 days
After Day 30: Must upgrade ($7/month) or data deleted
```

**Service 2: Render Web Service (Backend)**
```
Name:        gofere-api-staging
Type:        Web Service
Runtime:     Python 3.12
Plan:        Free
Behavior:    Spins down after 15 min inactivity
Cold Start:  ~30 seconds
Storage:     Ephemeral (files deleted on restart)
Cost:        $0 forever (can stay on free tier)
```

**Service 3: Vercel Deployment (Frontend)**
```
Name:        gofer-exam (preview deployment)
Type:        Next.js Application
Plan:        Hobby (free tier)
Bandwidth:   100 GB/month
Builds:      Unlimited
Cost:        $0 forever
```

### 5.2 Total Costs Summary

```
MONTH 1 (Days 1-30):
├── Backend:   $0 (free tier)
├── Database:  $0 (free tier)
├── Frontend:  $0 (free tier)
└── TOTAL:     $0

MONTH 2+ (Day 31+):
├── Backend:   $0 (stay on free tier)
├── Database:  $7/month (must upgrade or lose data)
├── Frontend:  $0 (free tier)
└── TOTAL:     $7/month

OPTIONAL ALWAYS-ON:
├── Backend:   $7/month (Starter - no spin down)
├── Database:  $7/month (required after day 30)
├── Frontend:  $0 (free tier)
└── TOTAL:     $14/month
```

**No Hidden Costs:**
- ✅ No credit card required for free tier
- ✅ No auto-upgrade charges
- ✅ No surprise bills
- ✅ Clear expiry warnings (days 25, 30, 40, 44)

### 5.3 What Free Tier Includes

**✅ Fully Functional:**
- All API endpoints
- Database operations
- User authentication
- File uploads (ephemeral)
- Health checks
- Logging
- Frontend deployment

**⚠️ Limitations:**
- Backend spins down (15 min inactivity)
- Database expires (30 days)
- Files deleted on restart
- No automatic backups
- Slower performance

**❌ NOT Included:**
- Persistent file storage
- Always-on availability
- Automatic backups
- Long-term database
- Production performance

---

## 6. Testing Capabilities

### 6.1 Can Test on Free Tier

**✅ Functional Testing (Full Coverage):**
```
□ User registration/login
□ Email verification (console logs)
□ Password reset (console logs)
□ Student profiles (CRUD)
□ Scholarship listings
□ Application submission
□ Document upload (functional)
□ Authorization/permissions
□ API endpoint responses
□ Frontend-backend integration
□ Health checks
□ Error handling
□ Form validation
□ UI/UX flows
```

**Time Estimate:** 2-3 hours comprehensive testing

### 6.2 Cannot Test on Free Tier

**❌ Requires Paid/Persistent Infrastructure:**
```
□ File persistence between restarts
□ Long-term data retention (>30 days)
□ Automated database backups
□ Point-in-time recovery
□ Always-on availability (no cold starts)
□ Production performance benchmarks
□ Real email delivery (requires SMTP/SES)
□ S3/GCS/Azure storage integration
□ CDN integration
□ High availability
□ Load balancing
□ Disaster recovery procedures
```

**For Production Only:** These require paid services ($14-91/month)

### 6.3 Workarounds for Limitations

**File Persistence:**
```
Limitation: Files deleted on restart
Workaround: Re-upload test files after restart
Test Focus: Upload functionality, not persistence
```

**Database Expiry:**
```
Limitation: 30-day limit
Workaround: Manual backup before day 30
Test Focus: Complete testing within 30 days
```

**Cold Starts:**
```
Limitation: 30-second delay after 15 min inactivity
Workaround: Ping health check every 10 minutes during testing
Test Focus: Functionality, not response times
```

**No Backups:**
```
Limitation: No automatic backups
Workaround: Manual pg_dump backups
Test Focus: Backup scripts work, not automation
```

---

## 7. Rollback and Cleanup

### 7.1 Complete Rollback Procedure

**If Deployment Fails or Issues Found:**

**Step 1: Stop All Services**
```bash
# Render Dashboard
1. Go to gofere-api-staging → Settings
2. Click "Suspend Service" (stops charges, preserves config)
3. Database remains (data preserved if within 44 days)
```

**Step 2: Delete Services (Optional)**
```bash
# If you want complete cleanup:
1. Render: Delete web service (Settings → Delete)
2. Render: Delete database (Settings → Delete - WARNING: permanent)
3. Vercel: Delete deployment (Settings → Delete)

# Result: Zero resources, zero costs, clean slate
```

**Step 3: Verify Cleanup**
```bash
# Check no running services
Render Dashboard → Should show 0 services

# Check no charges
Render → Usage → Should show $0

# Check no orphaned resources
- No databases
- No web services  
- No cron jobs
- No environment variables stored
```

### 7.2 Partial Cleanup (Keep Database)

**If You Want to Pause but Preserve Data:**
```bash
# Suspend backend (stops serving, stops charges)
1. Render → gofere-api-staging → Settings → Suspend

# Keep database running (no charges on free tier)
2. Database continues running (free for 30 days)

# Resume later
3. Unsuspend service when needed
4. Data preserved, no re-setup needed
```

### 7.3 Data Export Before Cleanup

**Critical: Export Before Deleting**
```bash
# 1. Export database
pg_dump -h <host> -U <user> -d gofer_exam_staging \
  -F custom -f final_staging_backup.dump

# 2. Verify export
pg_restore --list final_staging_backup.dump
# Should show all 32 tables

# 3. Store backup securely
# Local: ~/backups/staging/
# Cloud: S3/Google Drive/Dropbox

# 4. NOW safe to delete services
# Database can be restored anytime to new instance
```

### 7.4 Impact Assessment

**What Rollback Affects:**
```
Staging Environment:
✅ Completely removed
✅ No resources running
✅ No costs incurred
✅ No data accessible

Production Environment:
✅ Completely unaffected
✅ No changes made
✅ No downtime
✅ No data modified

Development Environment:
✅ Completely unaffected
✅ Local development continues
✅ Code unchanged
✅ No impact
```

**Rollback is Safe:**
- ✅ No production impact
- ✅ No data loss (if backed up)
- ✅ Can redeploy anytime
- ✅ All work preserved in git

---

## 8. Manual Steps Required

### 8.1 Your Actions (Step-by-Step)

**PHASE 1: Render Backend Setup (30 minutes)**

**Step 1: Create Database (5 min)**
```
1. Go to https://dashboard.render.com
2. Click "New +" → "PostgreSQL"
3. Fill form:
   - Name: gofere-db-staging
   - Database: gofer_exam_staging  
   - User: gofer_staging_user
   - Region: Oregon (us-west-2)
   - PostgreSQL Version: 18
   - Plan: Free
4. Click "Create Database"
5. Wait for provisioning (~2 minutes)
6. Copy "Internal Database URL" (starts with postgresql://)
   Example: postgresql://user:pass@host:5432/dbname
```

**Step 2: Create Web Service (10 min)**
```
1. Click "New +" → "Web Service"
2. Connect Repository:
   - Select "Connect Git"
   - Choose GitHub
   - Select "gofer-exam" repository
   - Branch: main
3. Fill form:
   - Name: gofere-api-staging
   - Region: Oregon (us-west-2)
   - Root Directory: backend
   - Runtime: Python 3
   - Build Command: pip install -r requirements/production.txt && python manage.py collectstatic --no-input
   - Start Command: python manage.py migrate --noinput && gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
   - Plan: Free
4. Click "Create Web Service" (don't deploy yet)
```

**Step 3: Set Environment Variables (15 min)**
```
1. In web service → Environment tab
2. Click "Add Environment Variable" for each:

   DJANGO_SETTINGS_MODULE=config.settings.production
   DEBUG=False
   DJANGO_LOG_LEVEL=INFO
   SECRET_KEY=[Click "Generate" button]
   DATABASE_URL=[Paste from Step 1]
   ALLOWED_HOSTS=gofere-api-staging.onrender.com
   GOFER_FRONTEND_URL=https://gofere-staging.vercel.app
   CORS_ALLOWED_ORIGINS=https://gofere-staging.vercel.app
   CSRF_TRUSTED_ORIGINS=https://gofere-api-staging.onrender.com,https://gofere-staging.vercel.app
   EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
   GOFER_EMAIL_FROM=staging@example.com
   STORAGE_BACKEND=LOCAL
   MONITORING_ENABLED=False

3. Click "Save Changes"
4. Click "Manual Deploy" → "Deploy latest commit"
5. Wait for deployment (~5 minutes)
```

**Step 4: Verify Backend (2 min)**
```
1. Click on service URL (https://gofere-api-staging.onrender.com)
2. Add to URL: /api/v1/health/liveness/
3. Should see: {"status": "alive"}
4. If 404 or error, check logs
```

**PHASE 2: Vercel Frontend Setup (20 minutes)**

**Step 5: Create Vercel Project (5 min)**
```
1. Go to https://vercel.com/dashboard
2. Click "Add New..." → "Project"
3. Import "gofer-exam" repository
4. Configure:
   - Framework Preset: Next.js
   - Root Directory: ./
   - Build Command: npm run build
   - Output Directory: .next
   - Install Command: npm install
5. DO NOT deploy yet (click "Cancel" or "Configure")
```

**Step 6: Set Frontend Environment Variables (10 min)**
```
1. Project Settings → Environment Variables
2. Add variables:

   NEXT_PUBLIC_APP_NAME=Gofer Exam (Staging)
   NEXT_PUBLIC_APP_URL=https://gofere-staging.vercel.app
   API_PROXY_TARGET=https://gofere-api-staging.onrender.com/api/v1
   NEXT_PUBLIC_API_URL=https://gofere-api-staging.onrender.com/api/v1

3. Set for: Production, Preview, Development (all checked)
4. Click "Save"
```

**Step 7: Deploy Frontend (5 min)**
```
1. Go to Deployments tab
2. Click "Deploy" or trigger by pushing to git
3. Wait for build (~3 minutes)
4. Copy preview URL (e.g., gofer-exam-git-main-yourname.vercel.app)
```

**PHASE 3: Update CORS (10 minutes)**

**Step 8: Update Backend CORS with Actual Frontend URL**
```
1. Go back to Render → gofere-api-staging
2. Environment tab
3. Edit CORS_ALLOWED_ORIGINS:
   - Replace gofere-staging.vercel.app with actual Vercel URL from Step 7
   - Example: https://gofer-exam-git-main-yourname.vercel.app
4. Edit CSRF_TRUSTED_ORIGINS:
   - Add actual Vercel URL
5. Click "Save Changes"
6. Service will auto-redeploy (~3 minutes)
```

**Step 9: Test End-to-End (5 min)**
```
1. Open Vercel preview URL in browser
2. Open browser DevTools (F12)
3. Check Console for errors
4. Try accessing homepage
5. Try accessing /api/v1/health/liveness/ through frontend
6. If CORS errors, verify Step 8 URLs match exactly
```

### 8.2 Timeline Summary

```
Phase 1: Render Backend    30 min
Phase 2: Vercel Frontend   20 min
Phase 3: CORS Update       10 min
─────────────────────────────────
Setup Total:                1 hour

Functional Testing:       2-3 hours
─────────────────────────────────
GRAND TOTAL:             3-4 hours
```

### 8.3 Dependencies

**Before You Begin:**
```
□ Render account (free, no credit card)
□ Vercel account (free, no credit card)
□ GitHub repository access
□ Git installed locally
□ PostgreSQL client (optional, for backups)
□ 3-4 hours available time
□ Team member for testing (optional)
```

---

## 9. Success Criteria

### 9.1 Deployment Successful If:

**Backend:**
```
✅ Service shows "Live" status in Render
✅ /api/v1/health/liveness/ returns {"status": "alive"}
✅ /api/v1/health/readiness/ returns {"status": "ready"}
✅ Logs show "migrate" completed successfully
✅ No error logs on startup
```

**Frontend:**
```
✅ Vercel build shows "Completed"
✅ Homepage loads without errors
✅ No 404 errors in browser console
✅ No CORS errors in console
✅ API calls visible in Network tab
```

**Integration:**
```
✅ Frontend can call backend APIs
✅ Login page loads
✅ No CORS errors when submitting forms
✅ Backend logs show incoming requests from frontend
```

### 9.2 Testing Complete If:

```
✅ User can register (email logged in Render)
✅ User can login (receives JWT tokens)
✅ User can view profile
✅ User can update profile
✅ User can upload document (before restart)
✅ User can view scholarships
✅ User can create application
✅ Admin can access Django admin
✅ Password reset works (token in logs)
✅ Permissions enforced (student cannot access admin)
✅ File persistence test shows deletion (expected behavior)
✅ All core user flows functional
```

---

## 10. Final Checklist & Approval

### 10.1 Pre-Approval Checklist

**I understand:**
```
□ Free database expires after 30 days (not 90)
□ Database deleted permanently after 44 days if not upgraded
□ Upgrade costs $7/month (required after day 30 to keep data)
□ Files are deleted on every service restart (ephemeral storage)
□ File persistence cannot be tested (requires S3/GCS/Azure)
□ Vercel 404 may be homepage OR API proxy (need diagnosis)
□ Console email logs contain tokens (test accounts only policy)
□ No real user data or email addresses in staging
□ Staging is completely isolated from production
□ No production impact from this deployment
□ I must perform all steps manually (no automation)
□ Total time required: 3-4 hours
□ Rollback is safe and reversible
```

### 10.2 Approval Questions

**Before approving, confirm:**

1. **Budget:** Accept $0 for 30 days, then $7/month OR data loss?
   - [ ] Yes, accept costs
   - [ ] No, need different plan

2. **Timeline:** Can complete testing within 30 days?
   - [ ] Yes, 30 days sufficient
   - [ ] No, need to upgrade immediately

3. **Storage:** Accept ephemeral storage limitations?
   - [ ] Yes, understand files will be deleted
   - [ ] No, need persistent storage now

4. **Vercel 404:** Need to diagnose before staging deployment?
   - [ ] Yes, diagnose first
   - [ ] No, proceed and diagnose during deployment

5. **Data:** Confirm test accounts only, no real data?
   - [ ] Yes, test accounts only
   - [ ] No, need clarification

### 10.3 Approval Statement

**I hereby approve this staging deployment plan with full understanding of:**
- 30-day database expiry
- Ephemeral file storage
- $0-7/month costs
- Manual deployment steps
- Test data policy
- Rollback procedures

**Approved by:** ___________________  
**Date:** ___________________  
**Ready to proceed:** [ ] YES / [ ] NO  

---

## 11. What Happens Next (After Approval)

**Immediate Next Steps:**
1. I will guide you through Phase 1 (Render setup)
2. You perform manual steps in Render dashboard
3. I verify each step completed correctly
4. Move to Phase 2 (Vercel setup)
5. You perform manual steps in Vercel dashboard
6. Update CORS configuration
7. Test end-to-end functionality
8. Begin comprehensive functional testing

**I will NOT:**
- Create services (you create them)
- Deploy automatically (you click buttons)
- Modify production (completely isolated)
- Purchase anything (you control costs)
- Access your accounts (you perform all steps)

**You will:**
- Create Render account (if needed)
- Create Vercel account (if needed)
- Click buttons in dashboards
- Copy/paste environment variables
- Verify each step
- Report results

**Support Provided:**
- Step-by-step instructions
- Environment variable values
- Troubleshooting guidance
- Success verification
- Testing procedures

---

## Document Information

**Version:** 2.0 (Revised)  
**Date:** November 2, 2026  
**Revisions:** Addressed 4 critical issues
- Database cost & expiry (verified 30 days)
- Storage limitations (ephemeral reality)
- Vercel 404 diagnosis (separated homepage/API)
- Email security (test accounts policy)

**Status:** AWAITING APPROVAL  
**Next Action:** User approval required before proceeding  

**Related Documents:**
- FINAL_INDEPENDENT_VERIFICATION.md
- P0_PRODUCTION_READINESS_FINAL_REPORT.md
- Original STAGING_DEPLOYMENT_PLAN.md (reference only)

---

**END OF REVISED STAGING DEPLOYMENT PLAN**

**Questions before approval? Ask now.**  
**Ready to approve? Confirm above checklist.**  
**Need modifications? Specify what to change.**
