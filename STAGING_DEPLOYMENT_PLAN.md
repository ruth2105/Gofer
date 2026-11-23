# Gofer Exam Platform - Staging Deployment Plan (REVISED)

**Date:** November 2, 2026  
**Revision:** 2.0  
**Environment:** Staging (Isolated from Production)  
**Status:** Awaiting Approval - NO ACTIONS TAKEN  

---

## ⚠️ CRITICAL UPDATES IN THIS REVISION

1. **Database Expiry:** Free PostgreSQL expires after **30 days** (not 90 days)
2. **Storage Limitations:** LOCAL storage is ephemeral and deleted on every restart
3. **Vercel 404:** Separate diagnosis for homepage vs API proxy issues
4. **Email Security:** Detailed token protection and test data policies

---

## Overview

This plan provides step-by-step instructions for deploying the Gofer Exam Platform to a **staging environment** with complete isolation from production. The staging environment will use separate databases, environment variables, and service instances to safely test all functionality before production deployment.

**Scope:**
- ✅ Backend API deployment (Render staging)
- ✅ Frontend deployment (Vercel staging/preview)
- ✅ Staging database (Render PostgreSQL - **expires after 30 days**)
- ✅ Email testing (Django console backend - no real emails)
- ✅ File storage (LOCAL - **ephemeral, deleted on restart**)
- ✅ Health checks and monitoring
- ✅ Comprehensive functional testing

**Out of Scope:**
- ❌ Production deployment
- ❌ Production database access/migration
- ❌ Production environment variable changes
- ❌ Real email sending
- ❌ Cloud storage configuration (S3/GCS/Azure)
- ❌ External service account creation
- ❌ Secret rotation
- ❌ Purchases or paid services

**Critical Limitations:**
- ⚠️ Free database expires and is deleted after **30 days** (+ 14-day grace period)
- ⚠️ Uploaded files deleted on every service restart or redeploy
- ⚠️ Backend spins down after 15 minutes of inactivity (30-second cold start)
- ⚠️ No automatic backups on free tier
- ⚠️ Maximum 30 days of testing before upgrade required ($7/month)

---

## 1. Database Cost and Expiry Policy (VERIFIED)

### 1.1 Render Free PostgreSQL - Accurate Information

**Official Policy (as of May 20, 2024):**
- **Free database expires after 30 days** (changed from 90 days)
- **14-day grace period** after expiry before deletion
- **Total time before deletion: 44 days**
- **1 GB storage limit** (fixed, cannot be increased)
- **No automatic backups** on free tier
- **Data is permanently deleted** after grace period

Source: [Render Changelog - Free PostgreSQL instances now expire after 30 days](https://render.com/changelog/free-postgresql-instances-now-expire-after-30-days-previously-90)

**What Happens at Expiry:**

```
Day 1-30:  Database active and accessible
Day 31:    Database expires (marked for deletion)
Day 31-44: Grace period (14 days)
           - Database still accessible
           - Warning: "Upgrade or database will be deleted"
           - Can upgrade to Starter ($7/month) to preserve data
Day 45:    Database and all data permanently deleted
           - No recovery possible
           - No backups available
```

### 1.2 Cost Scenarios (ACCURATE)

**Scenario A: 30-Day Free Trial Only**
```
Days 1-30:  Free ($0)
Day 31:     Must upgrade or lose data
Cost:       $0 total (if testing complete within 30 days)
Risk:       Data loss if not upgraded
```

**Scenario B: Upgrade Before Expiry**
```
Days 1-30:  Free ($0)
Day 25-30:  Upgrade to Starter ($7/month) before expiry
Days 31+:   Starter plan ($7/month)
Cost:       $7/month after day 30
Benefit:    Data preserved, 7-day backups, no expiry
```

**Scenario C: Upgrade During Grace Period**
```
Days 1-30:  Free ($0)
Day 31:     Expired (grace period begins)
Days 31-44: Upgrade to Starter during grace period
Days 45+:   Starter plan ($7/month)
Cost:       $7/month after upgrade
Benefit:    Data recovered, no loss
Warning:    Must upgrade before day 45
```

**Scenario D: No Upgrade (Data Loss)**
```
Days 1-30:  Free ($0)
Days 31-44: Grace period ignored
Day 45:     Database permanently deleted
Cost:       $0 total
Result:     All staging data lost permanently
```

### 1.3 How to Preserve Staging Data

**Option 1: Manual Backup Before Expiry (Recommended for Testing)**
```bash
# Day 28-29: Create backup before expiry
pg_dump -h <render-staging-host> \
  -U gofer_staging_user \
  -d gofer_exam_staging \
  -F custom \
  -f staging_backup_final.dump

# Store backup locally
# Database expires on day 30
# If needed later, create new free database and restore
```

**Option 2: Upgrade to Starter Plan (Recommended for Extended Testing)**
```bash
# Day 25-29: Upgrade before expiry
# Render Dashboard → Database → Upgrade
# Select: Starter ($7/month)
# Data automatically preserved
# No downtime
```

**Option 3: Export Then Recreate (Manual Process)**
```bash
# Day 29: Export data
pg_dump -h <old-host> -U old_user -d old_db -f backup.sql

# Day 31: Create new free database
# New 30-day timer starts

# Restore data to new database
psql -h <new-host> -U new_user -d new_db -f backup.sql

# Update backend DATABASE_URL
# Redeploy backend
```

### 1.4 Cost Comparison (VERIFIED)

**Free Tier Limitations:**
```
Duration:       30 days only (+ 14-day grace)
Storage:        1 GB (fixed)
Backups:        None (no automatic backups)
Expiry:         Yes (database deleted after 44 days)
Downtime:       Yes (backend spins down after 15 min)
Cost:           $0
```

**Starter Tier Benefits:**
```
Duration:       No expiry (permanent)
Storage:        1 GB (can be increased)
Backups:        Daily (7-day retention)
Expiry:         No expiry
Downtime:       Backend can be set to always-on ($7/month)
Cost:           $7/month (database only)
```

**Total Staging Costs (ACCURATE):**

```
OPTION A: 30-Day Free Testing
Backend:     $0 (Free tier, spins down)
Database:    $0 (Free tier, expires day 30)
Frontend:    $0 (Vercel free tier)
Duration:    30 days maximum
Total:       $0 for 30 days
After Day 30: Must upgrade or data lost

OPTION B: Extended Testing (Recommended)
Backend:     $0 (Free tier, spins down)
Database:    $7/month (Starter, no expiry)
Frontend:    $0 (Vercel free tier)
Duration:    Unlimited
Total:       $7/month after day 30

OPTION C: Always-On Staging
Backend:     $7/month (Starter, always on)
Database:    $7/month (Starter, no expiry)
Frontend:    $0 (Vercel free tier)
Duration:    Unlimited
Total:       $14/month

RECOMMENDATION: Start with Option A (free 30 days)
                Upgrade to Option B before day 30 if needed
                Option C only if cold starts unacceptable
```

### 1.5 Staging Data Preservation Checklist

**Before Day 30 (Critical Actions):**
```
Day 1:    □ Create staging database (30-day timer starts)
Day 10:   □ Review data preservation strategy
Day 20:   □ Decide: Upgrade or backup-and-delete
Day 25:   □ If upgrading: Upgrade to Starter ($7/month)
Day 28:   □ If not upgrading: Create final backup
Day 29:   □ Verify backup integrity
Day 30:   □ Database expires (grace period begins)
Day 44:   □ FINAL DAY before deletion
```

**Automated Reminders (Manual Setup):**
```bash
# Set calendar reminders:
Day 1:  "Staging database created - 30 days until expiry"
Day 20: "10 days until staging database expires - decide now"
Day 25: "5 days until expiry - upgrade or backup NOW"
Day 30: "Database expired - 14-day grace period begins"
Day 40: "4 days until permanent deletion - upgrade NOW"
```

### 1.6 What Cannot Be Tested on Free Tier

**Cannot Test (Free Tier Limitations):**
- ❌ Automated backups (no backups on free tier)
- ❌ Point-in-time recovery (Starter+ only)
- ❌ Long-term data retention (30 days max)
- ❌ Database persistence beyond 30 days
- ❌ Backup restoration (no backups to restore)
- ❌ Always-on availability (backend spins down)
- ❌ Production-like performance (shared CPU)

**Can Test (Free Tier Capabilities):**
- ✅ Database connectivity
- ✅ Schema migrations
- ✅ CRUD operations
- ✅ API functionality
- ✅ User authentication/authorization
- ✅ Application logic
- ✅ Frontend-backend integration
- ✅ Manual backup/restore scripts
- ✅ Cold start behavior
- ✅ Basic performance testing

---

## 2. Staging Architecture

### 2.1 Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    STAGING ENVIRONMENT                       │
│                   (Completely Isolated)                      │
└─────────────────────────────────────────────────────────────┘

┌──────────────────┐        ┌──────────────────┐
│  Vercel Preview  │───────▶│  Render Staging  │
│  (Frontend)      │  HTTPS │  (Backend API)   │
│                  │        │                  │
│  gofere-staging  │        │  gofere-api-stg  │
│  .vercel.app     │        │  .onrender.com   │
└──────────────────┘        └──────────────────┘
                                     │
                                     │ PostgreSQL
                                     │ Connection
                                     ▼
                            ┌──────────────────┐
                            │  Render Postgres │
                            │  (Staging DB)    │
                            │                  │
                            │  gofere-db-stg   │
                            └──────────────────┘

┌──────────────────────────────────────────────────────────────┐
│  Isolated Components:                                         │
│  • Separate database instance                                 │
│  • Separate web service                                       │
│  • Separate environment variables                             │
│  • LOCAL file storage (ephemeral - /tmp)                      │
│  • Console email backend (no real emails)                     │
│  • No connection to production                                │
└──────────────────────────────────────────────────────────────┘
```

### 2.2 Isolation Strategy

**Database Isolation:**
- ✅ Separate PostgreSQL instance: `gofere-db-staging`
- ✅ Different database name: `gofer_exam_staging`
- ✅ Different user credentials
- ✅ No replication from/to production
- ✅ Can be dropped/recreated freely

**Environment Variable Isolation:**
- ✅ Separate `.env` configuration in Render
- ✅ Different SECRET_KEY
- ✅ Different ALLOWED_HOSTS
- ✅ Different CORS_ALLOWED_ORIGINS
- ✅ Staging-specific frontend URL

**Service Isolation:**
- ✅ Separate Render web service: `gofere-api-staging`
- ✅ Separate Vercel deployment: Preview or staging branch
- ✅ No shared resources with production
- ✅ Can be deployed/redeployed without affecting production

**Data Isolation:**
- ✅ Test data only (no real user data)
- ✅ Fake email addresses (@example.com)
- ✅ Test documents only
- ✅ Can be wiped and recreated

### 2.3 Safety Features

**Email Safety:**
```python
# Staging uses console backend (logs emails, doesn't send)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# All emails logged to console, visible in Render logs
# NO REAL EMAILS SENT TO USERS
```

**Storage Safety:**
```python
# Staging uses LOCAL storage (ephemeral, in /tmp)
STORAGE_BACKEND = 'LOCAL'
DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'

# Files stored in container filesystem (ephemeral)
# ⚠️ CRITICAL: Files are PERMANENTLY DELETED on:
#   - Service restart
#   - Service redeploy
#   - Service scale-up/scale-down
#   - Container recreation

# This is EXPECTED behavior for free tier
# Production will use S3/GCS/Azure (persistent storage)
```

**Storage Persistence Reality:**
```
Event                           Files Deleted?    Database Affected?
────────────────────────────────────────────────────────────────────
Service restart                 YES ❌            NO ✅
Service redeploy (git push)     YES ❌            NO ✅
Manual redeploy                 YES ❌            NO ✅
Service scaling                 YES ❌            NO ✅
Service migration               YES ❌            NO ✅
Database restart                NO ✅             NO ✅ (data persists)
Container update                YES ❌            NO ✅
```

**What This Means:**
- Files uploaded before 12:00 PM will be gone after 12:15 PM (if service restarted)
- Every git push deletes all uploaded files
- File database records remain, but files themselves are gone
- This is LOCAL storage limitation, not a bug
- **Staging is for functional testing ONLY, not file persistence testing**

**Database Safety:**
- Separate instance, cannot affect production
- Free tier (no costs)
- Can be dropped and recreated
- Test data only

---

## 3. Storage Limitations and File Persistence

### 3.1 LOCAL Storage Reality (CRITICAL UNDERSTANDING)

**Render Free Tier Storage:**
- Filesystem is **ephemeral** (temporary, not persistent)
- Files stored in `/tmp` or container filesystem
- **ALL files deleted** on service restart, redeploy, or scaling
- No warning before deletion
- No recovery possible after deletion
- This is architectural limitation, not a bug

**Source:** [Render Docs - Persistent Disks](https://render.com/docs/disks): "Without a persistent disk, any changes you make to a service's local files are lost every time the service redeploys or restarts."

### 3.2 What Triggers File Deletion

**Automatic File Deletion Events:**

1. **Service Restart**
   - Backend spins down after 15 min inactivity
   - Next request spins up NEW container
   - Old container destroyed → files deleted

2. **Git Push (Redeploy)**
   - New code pushed to repository
   - Render builds new container
   - Old container destroyed → files deleted

3. **Manual Redeploy**
   - Click "Manual Deploy" in Render dashboard
   - New container created
   - Old container destroyed → files deleted

4. **Service Scaling**
   - Service scaled up or down
   - New containers created
   - Old containers destroyed → files deleted

5. **Platform Maintenance**
   - Render performs maintenance
   - Containers migrated
   - Old containers destroyed → files deleted

**Frequency:**
- Free tier: Every 15 minutes of inactivity
- After every git push
- Unpredictable platform events

### 3.3 File Persistence Test (REQUIRED)

**Purpose:** Verify ephemeral storage behavior and train team on limitations.

**Test Procedure:**

```bash
# STEP 1: Upload Test File
1. Login to staging frontend
2. Navigate to profile → Documents
3. Upload file: test-document.pdf
4. Verify upload successful
5. Copy file URL from response
6. Access file URL → File accessible ✅

# STEP 2: Trigger Service Restart
# Option A: Wait 15 minutes (service spins down)
# Option B: Manual restart in Render dashboard
# Option C: Push empty commit to trigger redeploy

git commit --allow-empty -m "Test: Trigger service restart"
git push origin main

# STEP 3: Wait for Redeploy
# Watch Render logs
# Wait for "Service started successfully"
# Time: ~3-5 minutes

# STEP 4: Verify File Deleted
1. Access same file URL from step 1
2. Expected result: 404 Not Found or empty response
3. File is GONE (expected behavior)

# STEP 5: Verify Database Record Remains
curl https://gofere-api-staging.onrender.com/api/v1/documents/ \
  -H "Authorization: Bearer <token>"

# Expected: Document record still exists
# But file field points to non-existent file
# Database NOT affected by file deletion
```

**Expected Results:**
```
File Accessible Before Restart:  YES ✅
File Accessible After Restart:   NO ❌ (EXPECTED)
Database Record Before Restart:  EXISTS ✅
Database Record After Restart:   EXISTS ✅ (file path remains)
File Data After Restart:         DELETED ❌ (EXPECTED)
```

**Success Criteria:**
```
□ File uploads successfully
□ File accessible immediately after upload
□ File deleted after service restart (confirmed)
□ Database record persists (confirmed)
□ Team understands ephemeral storage limitation
□ Team aware production will use S3/GCS/Azure
```

### 3.4 Persistent Storage Options (NOT IN THIS PLAN)

**Render Persistent Disks (Paid Feature):**
```
Cost:      $0.25/GB/month
Minimum:   1 GB ($0.25/month)
Available: Starter tier and above ($7/month service + disk cost)
Total:     $7.25/month minimum
Not included in free tier
```

**Cloud Storage (Production Only):**
```
AWS S3:    $0.023/GB/month
GCS:       $0.020/GB/month
Azure:     $0.018/GB/month
Not configured in this staging plan
```

**For Staging:**
```
Use LOCAL storage (ephemeral)
Accept file deletion on restart
Test file upload FUNCTIONALITY only
Do NOT test file PERSISTENCE
Do NOT rely on uploaded files between sessions
```

### 3.5 What CAN Be Tested with LOCAL Storage

**Testable Functionality:**
- ✅ File upload API endpoint
- ✅ File validation (type, size, extension)
- ✅ File metadata extraction (size, extension)
- ✅ Database record creation
- ✅ File URL generation
- ✅ Immediate file access (before restart)
- ✅ Authorization checks (who can upload/access)
- ✅ Error handling (file too large, wrong type)
- ✅ Frontend upload UI
- ✅ Progress indicators
- ✅ Success/error messages

**NOT Testable:**
- ❌ Long-term file persistence
- ❌ File access after restart
- ❌ File availability after redeploy
- ❌ CDN integration
- ❌ Signed URL expiry (S3/GCS feature)
- ❌ Bucket policies
- ❌ Cross-region replication
- ❌ File versioning
- ❌ Production-grade file management

### 3.6 Staging vs Production Storage

```
STAGING (LOCAL):
Storage:     Ephemeral filesystem (/tmp)
Persistence: None (files deleted on restart)
Cost:        $0
Use Case:    Functional testing only
Suitable For: Upload/download functionality testing
NOT For:     File persistence, long-term storage

PRODUCTION (S3/GCS/Azure):
Storage:     Cloud object storage
Persistence: Permanent (until explicitly deleted)
Cost:        ~$0.02/GB/month + transfer
Use Case:    Production file storage
Suitable For: All production use cases
Required For: Real user documents, long-term storage
```

---

## 4. Vercel 404 Diagnosis and Resolution

### 2.1 Required Render Services

**Service 1: Staging Database**
```yaml
Service Type: PostgreSQL
Name: gofere-db-staging
Plan: Free (Starter after 90 days: $7/month)
Database Name: gofer_exam_staging
User: gofer_staging_user
Region: Oregon (us-west-2) or closest
```

**Service 2: Staging Web Service**
```yaml
Service Type: Web Service
Name: gofere-api-staging
Plan: Free (or Starter: $7/month for always-on)
Runtime: Python 3.12
Root Directory: backend
Build Command: pip install -r requirements/production.txt && python manage.py collectstatic --no-input
Start Command: python manage.py migrate --noinput && gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
Health Check Path: /api/v1/health/liveness/
Auto-Deploy: Yes (from main branch)
```

### 2.2 Staging Environment Variables (Backend)

**CRITICAL - Set in Render Dashboard:**

```bash
# Django Core Settings
DJANGO_SETTINGS_MODULE=config.settings.production
SECRET_KEY=<Auto-generated by Render - different from production>
DEBUG=False
ALLOWED_HOSTS=gofere-api-staging.onrender.com
DJANGO_LOG_LEVEL=INFO

# Database (Auto-configured from Render PostgreSQL)
DATABASE_URL=<From Render Database: gofere-db-staging>

# CORS and CSRF (Frontend URLs)
CORS_ALLOWED_ORIGINS=https://gofere-staging.vercel.app,https://gofer-exam-git-staging-yourusername.vercel.app
CSRF_TRUSTED_ORIGINS=https://gofere-api-staging.onrender.com,https://gofere-staging.vercel.app

# Frontend URL
GOFER_FRONTEND_URL=https://gofere-staging.vercel.app

# Email Settings (CONSOLE BACKEND - NO REAL EMAILS)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
GOFER_EMAIL_FROM=staging@example.com
EMAIL_VERIFICATION_TOKEN_TTL_MINUTES=60
EMAIL_VERIFICATION_RESEND_COOLDOWN_SECONDS=60

# Storage Settings (LOCAL - EPHEMERAL)
STORAGE_BACKEND=LOCAL

# Monitoring (Optional)
MONITORING_ENABLED=False
# SENTRY_DSN=<Optional - can use free tier for staging>
# SENTRY_ENVIRONMENT=staging

# Python Version
PYTHON_VERSION=3.12.10
```

**Environment Variables Summary:**
- Total Required: 13 variables
- Auto-Generated: 2 (SECRET_KEY, DATABASE_URL)
- Manual Entry: 11 variables
- Sensitive: 0 (no credentials needed for staging)

### 2.3 Render Deployment Steps (Backend)

**STEP-BY-STEP (NO ACTION YET - AWAITING APPROVAL):**

1. **Create Staging Database**
   - Go to Render Dashboard → New → PostgreSQL
   - Name: `gofere-db-staging`
   - Plan: Free
   - Region: Oregon (us-west-2)
   - Wait for provisioning (~2 minutes)
   - Copy DATABASE_URL (internal connection string)

2. **Create Staging Web Service**
   - Go to Render Dashboard → New → Web Service
   - Connect to GitHub repository: `gofer-exam`
   - Branch: `main` (or create `staging` branch)
   - Name: `gofere-api-staging`
   - Runtime: Python 3
   - Plan: Free (or Starter for always-on)
   - Root Directory: `backend`
   - Build Command: `pip install -r requirements/production.txt && python manage.py collectstatic --no-input`
   - Start Command: `python manage.py migrate --noinput && gunicorn config.wsgi:application --bind 0.0.0.0:$PORT`

3. **Configure Environment Variables**
   - In web service settings → Environment
   - Add all 13 variables listed above
   - Set DATABASE_URL from staging database
   - Generate SECRET_KEY (use Render's auto-generate)
   - Set ALLOWED_HOSTS to actual Render URL
   - Set CORS_ALLOWED_ORIGINS to Vercel preview URL

4. **Set Health Check**
   - Health Check Path: `/api/v1/health/liveness/`
   - Wait for first deployment (~5 minutes)

5. **Verify Deployment**
   - Check Render logs for successful startup
   - Visit: `https://gofere-api-staging.onrender.com/api/v1/health/liveness/`
   - Should return: `{"status": "alive"}`

**Estimated Time:** 15-20 minutes  
**Cost:** $0 (Free tier for 90 days, then $7/month per service)

---

## 3. Vercel Configuration (Frontend)

### 3.1 Required Vercel Configuration

**Deployment Type:** Preview Deployment (automatic on branch push)

**Option A: Automatic Preview (Recommended)**
```yaml
Branch: main
Deployment: Automatic preview on every commit
URL: https://gofer-exam-git-main-yourusername.vercel.app
Cost: Free
```

**Option B: Staging Branch**
```yaml
Branch: staging (create new branch)
Deployment: Automatic preview on staging branch
URL: https://gofere-staging.vercel.app (custom domain)
Cost: Free
```

### 3.2 Staging Environment Variables (Frontend)

**CRITICAL - Set in Vercel Dashboard → Settings → Environment Variables:**

```bash
# App Configuration
NEXT_PUBLIC_APP_NAME=Gofer Exam (Staging)
NEXT_PUBLIC_APP_URL=https://gofere-staging.vercel.app
API_PROXY_TARGET=https://gofere-api-staging.onrender.com/api/v1
NEXT_PUBLIC_API_URL=https://gofere-api-staging.onrender.com/api/v1

# Environment Indicator
NEXT_PUBLIC_ENV=staging
```

**Environment Variables Summary:**
- Total Required: 4 variables
- All public (NEXT_PUBLIC_* are exposed to browser)
- No sensitive data

### 3.3 Vercel Deployment Steps (Frontend)

**STEP-BY-STEP (NO ACTION YET - AWAITING APPROVAL):**

1. **Connect GitHub Repository**
   - Go to Vercel Dashboard → Add New → Project
   - Import `gofer-exam` repository
   - Configure project settings:
     - Framework Preset: Next.js
     - Root Directory: `.` (project root)
     - Build Command: `npm run build`
     - Output Directory: `.next`
     - Install Command: `npm install`

2. **Configure Environment Variables**
   - In Project Settings → Environment Variables
   - Add 4 variables listed above
   - Set for: Production, Preview, and Development
   - **CRITICAL:** `API_PROXY_TARGET` must point to Render staging backend

3. **Deploy**
   - Click "Deploy"
   - Wait for build (~3-5 minutes)
   - Vercel will assign preview URL automatically

4. **Get Preview URL**
   - Copy preview URL (e.g., `gofer-exam-git-main-yourusername.vercel.app`)
   - Update Render CORS_ALLOWED_ORIGINS with this URL
   - Redeploy Render backend

**Estimated Time:** 10-15 minutes  
**Cost:** $0 (Free tier)

### 3.4 Resolving Vercel 404 Issues

**ROOT CAUSE ANALYSIS:**

The 404 errors likely occur because of API proxy configuration mismatch between frontend and backend.

**INVESTIGATION STEPS:**

1. **Check Next.js Rewrites**
   ```typescript
   // next.config.ts (ALREADY CONFIGURED)
   async rewrites() {
     return [{
       source: "/api/v1/:path*",
       destination: `${apiProxyTarget}/:path*/`,  // Proxies to backend
     }];
   }
   ```

2. **Verify API_PROXY_TARGET**
   - Frontend makes requests to: `/api/v1/auth/login/`
   - Next.js rewrites to: `https://gofere-api-staging.onrender.com/api/v1/auth/login/`
   - Backend should respond at this URL

3. **Common 404 Causes:**
   - ❌ `API_PROXY_TARGET` not set in Vercel
   - ❌ `API_PROXY_TARGET` has trailing slash (already handled in code)
   - ❌ CORS headers blocking requests
   - ❌ Backend URL incorrect
   - ❌ Backend not deployed/running

**RESOLUTION CHECKLIST:**

```bash
# 1. Verify API_PROXY_TARGET is set in Vercel
✅ API_PROXY_TARGET=https://gofere-api-staging.onrender.com/api/v1

# 2. Verify backend is responding
✅ curl https://gofere-api-staging.onrender.com/api/v1/health/liveness/
   Expected: {"status": "alive"}

# 3. Verify CORS is configured
✅ CORS_ALLOWED_ORIGINS includes Vercel preview URL

# 4. Test API directly from browser
✅ Open: https://gofere-api-staging.onrender.com/api/v1/schema/
   Expected: OpenAPI schema (HTML page)

# 5. Check browser console for errors
✅ Open frontend, check DevTools Console
   Look for: CORS errors, 404 errors, network failures

# 6. Verify rewrite in production build
✅ Check Vercel build logs for rewrites configuration
```

**FIX IMPLEMENTATION:**

1. **Set API_PROXY_TARGET in Vercel**
   - Vercel Dashboard → Project → Settings → Environment Variables
   - Add: `API_PROXY_TARGET` = `https://gofere-api-staging.onrender.com/api/v1`
   - Redeploy frontend

2. **Update CORS in Render**
   - Get actual Vercel preview URL
   - Update `CORS_ALLOWED_ORIGINS` in Render
   - Redeploy backend

3. **Test End-to-End**
   - Open frontend preview URL
   - Try login/registration
   - Check browser console for errors
   - Check Render logs for incoming requests

**ESTIMATED TIME TO RESOLVE:** 30-60 minutes

---

## 4. Required Environment Variables Reference

### 4.1 Backend Environment Variables (13 Total)

**Django Core (4 variables):**
```
DJANGO_SETTINGS_MODULE    Required   config.settings.production
SECRET_KEY                Auto-gen   (Render generates unique key)
DEBUG                     Required   False
DJANGO_LOG_LEVEL          Optional   INFO (default)
```

**Database (1 variable):**
```
DATABASE_URL              Auto-gen   (From Render PostgreSQL staging)
```

**Network Configuration (3 variables):**
```
ALLOWED_HOSTS             Required   gofere-api-staging.onrender.com
CORS_ALLOWED_ORIGINS      Required   https://gofere-staging.vercel.app,...
CSRF_TRUSTED_ORIGINS      Required   https://gofere-api-staging.onrender.com,...
```

**Frontend Integration (1 variable):**
```
GOFER_FRONTEND_URL        Required   https://gofere-staging.vercel.app
```

**Email Configuration (3 variables):**
```
EMAIL_BACKEND             Required   django.core.mail.backends.console.EmailBackend
GOFER_EMAIL_FROM          Required   staging@example.com
EMAIL_VERIFICATION_TOKEN_TTL_MINUTES  Optional  60 (default)
```

**Storage Configuration (1 variable):**
```
STORAGE_BACKEND           Optional   LOCAL (default)
```

**Monitoring (2 variables - optional):**
```
MONITORING_ENABLED        Optional   False
SENTRY_DSN                Optional   (empty or Sentry staging DSN)
```

### 4.2 Frontend Environment Variables (4 Total)

**App Configuration:**
```
NEXT_PUBLIC_APP_NAME      Required   Gofer Exam (Staging)
NEXT_PUBLIC_APP_URL       Required   https://gofere-staging.vercel.app
API_PROXY_TARGET          Required   https://gofere-api-staging.onrender.com/api/v1
NEXT_PUBLIC_API_URL       Optional   https://gofere-api-staging.onrender.com/api/v1
```

**IMPORTANT NOTES:**
- All `NEXT_PUBLIC_*` variables are exposed to browser (public)
- No sensitive credentials should be in frontend environment
- `API_PROXY_TARGET` is used server-side (Next.js rewrites)
- `NEXT_PUBLIC_API_URL` is used client-side (if needed)

---

## 5. Functional Testing Plan

### 5.1 Health Check Testing (5 minutes)

**Test 1: Liveness Check**
```bash
# Request
curl https://gofere-api-staging.onrender.com/api/v1/health/liveness/

# Expected Response
{
  "status": "alive"
}

# Success Criteria
✅ HTTP 200 OK
✅ Response contains "status": "alive"
✅ Response time < 1 second
```

**Test 2: Readiness Check**
```bash
# Request
curl https://gofere-api-staging.onrender.com/api/v1/health/readiness/

# Expected Response
{
  "status": "ready",
  "database": "healthy"
}

# Success Criteria
✅ HTTP 200 OK
✅ Database connection successful
✅ Response time < 2 seconds
```

**Test 3: Comprehensive Health Check**
```bash
# Request
curl https://gofere-api-staging.onrender.com/api/v1/health/

# Expected Response
{
  "status": "healthy",
  "database": "healthy",
  "response_time_ms": 15
}

# Success Criteria
✅ HTTP 200 OK
✅ Status is "healthy"
✅ Database is "healthy"
✅ Response time < 3 seconds
```

### 5.2 User Registration Testing (10 minutes)

**Test 1: Student Registration**
```bash
# Frontend Test (Recommended)
1. Open: https://gofere-staging.vercel.app/student/register
2. Fill form:
   - Email: test-student@example.com
   - Password: TestPass123!
   - First Name: Test
   - Last Name: Student
   - Role: Student
3. Submit form

# Backend Test (API Direct)
curl -X POST https://gofere-api-staging.onrender.com/api/v1/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "api-test-student@example.com",
    "password": "TestPass123!",
    "password_confirm": "TestPass123!",
    "first_name": "API",
    "last_name": "Student",
    "role": "STUDENT"
  }'

# Success Criteria
✅ HTTP 201 Created
✅ Response contains user ID
✅ Email verification logged in Render logs (console backend)
✅ Can see email content in logs: "Verification email accepted..."
✅ User created in staging database
```

**Verification Email Check:**
```bash
# Check Render logs for email content
# Render Dashboard → gofere-api-staging → Logs
# Search for: "Verification email accepted"
# Should show:
INFO apps.accounts.email_verification send_verification_email 
  Verification email accepted by backend for user_id=<uuid>
  
# Email content logged to console (not sent):
Subject: Verify Your Gofer Exam Account
To: test-student@example.com
Body: Click here to verify: https://gofere-staging.vercel.app/verify-email?token=...
```

**Test 2: Consultant Registration**
```bash
# Same as above, but role: CONSULTANT
curl -X POST https://gofere-api-staging.onrender.com/api/v1/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test-consultant@example.com",
    "password": "TestPass123!",
    "password_confirm": "TestPass123!",
    "first_name": "Test",
    "last_name": "Consultant",
    "role": "CONSULTANT"
  }'
```

**Test 3: Admin Creation (Django Admin)**
```bash
# SSH into Render service or use Render Shell
python manage.py createsuperuser
# Email: admin@example.com
# Password: AdminPass123!

# Access Django admin:
https://gofere-api-staging.onrender.com/admin/
```

### 5.3 Login Testing (10 minutes)

**Test 1: Student Login**
```bash
# Frontend Test
1. Open: https://gofere-staging.vercel.app/student/login
2. Email: test-student@example.com
3. Password: TestPass123!
4. Click Login

# API Test
curl -X POST https://gofere-api-staging.onrender.com/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test-student@example.com",
    "password": "TestPass123!"
  }'

# Expected Response
{
  "access": "<jwt-token>",
  "refresh": "<jwt-token>",
  "user": {
    "id": "<uuid>",
    "email": "test-student@example.com",
    "role": "STUDENT",
    "first_name": "Test",
    "last_name": "Student"
  }
}

# Success Criteria
✅ HTTP 200 OK
✅ Receives access and refresh tokens
✅ User object contains correct data
✅ Frontend stores tokens in cookies
✅ Redirects to student dashboard
```

**Test 2: Failed Login**
```bash
# Wrong password
curl -X POST https://gofere-api-staging.onrender.com/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test-student@example.com",
    "password": "WrongPassword"
  }'

# Expected Response
{
  "detail": "Invalid credentials"
}

# Success Criteria
✅ HTTP 401 Unauthorized
✅ Error message displayed
✅ No tokens issued
```

### 5.4 Student Profile Testing (15 minutes)

**Test 1: View Profile**
```bash
# Frontend Test
1. Login as student
2. Navigate to: /student/profile
3. Verify profile data displayed

# API Test
curl https://gofere-api-staging.onrender.com/api/v1/students/me/ \
  -H "Authorization: Bearer <access-token>"

# Expected Response
{
  "id": "<uuid>",
  "user": {
    "email": "test-student@example.com",
    "first_name": "Test",
    "last_name": "Student",
    "role": "STUDENT"
  },
  "date_of_birth": null,
  "gender": null,
  "phone_number": null,
  "address": null,
  "country": null,
  "profile_completed": false
}

# Success Criteria
✅ HTTP 200 OK
✅ Profile data displayed
✅ Can view all fields
```

**Test 2: Update Profile**
```bash
# Frontend Test
1. Click "Edit Profile"
2. Update fields:
   - Date of Birth: 2000-01-01
   - Gender: Male
   - Phone: +1234567890
   - Address: 123 Test St
   - Country: United States
3. Submit form

# API Test
curl -X PATCH https://gofere-api-staging.onrender.com/api/v1/students/me/ \
  -H "Authorization: Bearer <access-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "date_of_birth": "2000-01-01",
    "gender": "MALE",
    "phone_number": "+1234567890",
    "address": "123 Test St",
    "country": "United States"
  }'

# Success Criteria
✅ HTTP 200 OK
✅ Profile updated successfully
✅ Changes persisted in database
✅ profile_completed becomes true
```

**Test 3: Add Education**
```bash
# Create education entry
curl -X POST https://gofere-api-staging.onrender.com/api/v1/students/me/education/ \
  -H "Authorization: Bearer <access-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "institution": "Test University",
    "degree": "Bachelor of Science",
    "field_of_study": "Computer Science",
    "start_date": "2018-09-01",
    "end_date": "2022-06-01",
    "grade": "3.8 GPA"
  }'

# Success Criteria
✅ HTTP 201 Created
✅ Education entry created
✅ Visible in profile
```

### 5.5 Scholarship Testing (20 minutes)

**Test 1: List Scholarships**
```bash
# Frontend Test
1. Navigate to: /scholarships
2. Verify scholarships displayed

# API Test
curl https://gofere-api-staging.onrender.com/api/v1/scholarships/

# Expected Response
{
  "count": 5,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "<uuid>",
      "title": "Test Scholarship",
      "description": "...",
      "amount": "5000.00",
      "currency": "USD",
      "deadline": "2027-06-01",
      "is_published": true
    },
    ...
  ]
}

# Success Criteria
✅ HTTP 200 OK
✅ Scholarships listed
✅ Pagination working
✅ Published scholarships only (for non-admin)
```

**Test 2: View Scholarship Detail**
```bash
# Frontend Test
1. Click on a scholarship
2. View full details

# API Test
curl https://gofere-api-staging.onrender.com/api/v1/scholarships/<scholarship-id>/

# Success Criteria
✅ HTTP 200 OK
✅ Full scholarship details displayed
✅ Eligibility criteria shown
✅ Application instructions visible
```

**Test 3: Admin Create Scholarship**
```bash
# Login as admin
curl -X POST https://gofere-api-staging.onrender.com/api/v1/scholarships/ \
  -H "Authorization: Bearer <admin-access-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Staging Test Scholarship",
    "description": "Test scholarship for staging",
    "amount": "10000.00",
    "currency": "USD",
    "deadline": "2027-12-31",
    "eligibility_criteria": {
      "min_gpa": 3.0,
      "countries": ["United States", "Canada"]
    },
    "is_published": true
  }'

# Success Criteria
✅ HTTP 201 Created
✅ Admin can create scholarships
✅ Non-admin cannot create (403 Forbidden)
```

### 5.6 Application Testing (20 minutes)

**Test 1: Create Application**
```bash
# Frontend Test
1. Login as student
2. Navigate to scholarship detail
3. Click "Apply Now"
4. Fill application form
5. Submit

# API Test
curl -X POST https://gofere-api-staging.onrender.com/api/v1/applications/ \
  -H "Authorization: Bearer <student-access-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "scholarship": "<scholarship-id>",
    "motivation_letter": "I am applying because...",
    "additional_info": "Additional details..."
  }'

# Success Criteria
✅ HTTP 201 Created
✅ Application created with status: DRAFT
✅ Student can view in "My Applications"
✅ Application number generated
```

**Test 2: Submit Application**
```bash
# Frontend Test
1. View application in draft
2. Click "Submit"
3. Confirm submission

# API Test
curl -X POST https://gofere-api-staging.onrender.com/api/v1/applications/<application-id>/submit/ \
  -H "Authorization: Bearer <student-access-token>"

# Success Criteria
✅ HTTP 200 OK
✅ Status changes to: SUBMITTED
✅ submitted_at timestamp set
✅ Can no longer edit application
✅ Consultant/admin can now see application
```

**Test 3: Consultant Review Application**
```bash
# Login as consultant
curl https://gofere-api-staging.onrender.com/api/v1/applications/consultant/assigned/ \
  -H "Authorization: Bearer <consultant-access-token>"

# Start review
curl -X POST https://gofere-api-staging.onrender.com/api/v1/applications/consultant/assigned/<application-id>/start-review/ \
  -H "Authorization: Bearer <consultant-access-token>"

# Success Criteria
✅ Consultant can view assigned applications
✅ Status changes to: UNDER_REVIEW
✅ reviewed_at timestamp set
```

### 5.7 Private Document Upload Testing (15 minutes)

**Test 1: Upload Document (LOCAL Storage)**
```bash
# Frontend Test
1. Login as student
2. Navigate to: /student/profile → Documents
3. Click "Upload Document"
4. Select file: test-passport.pdf
5. Document type: Passport
6. Submit

# API Test (multipart/form-data)
curl -X POST https://gofere-api-staging.onrender.com/api/v1/documents/ \
  -H "Authorization: Bearer <student-access-token>" \
  -F "file=@test-passport.pdf" \
  -F "document_type=PASSPORT" \
  -F "title=My Passport" \
  -F "description=Passport for verification"

# Success Criteria
✅ HTTP 201 Created
✅ File uploaded to /tmp/media/documents/ (LOCAL storage)
✅ Document record created in database
✅ file_size calculated
✅ file_extension extracted (.pdf)
✅ uploaded_at timestamp set
```

**Test 2: View Own Documents**
```bash
# Frontend Test
1. View documents list
2. Verify uploaded document appears

# API Test
curl https://gofere-api-staging.onrender.com/api/v1/documents/ \
  -H "Authorization: Bearer <student-access-token>"

# Expected Response
{
  "count": 1,
  "results": [
    {
      "id": "<uuid>",
      "document_type": "PASSPORT",
      "title": "My Passport",
      "file": "/media/documents/test-passport.pdf",
      "file_size": 1024000,
      "file_extension": ".pdf",
      "uploaded_at": "2026-11-02T10:30:00Z",
      "user": "<user-id>"
    }
  ]
}

# Success Criteria
✅ Student can see their own documents
✅ File URL returned
✅ File metadata correct
```

**Test 3: Authorization Check (Cannot View Others' Documents)**
```bash
# Login as different student
curl https://gofere-api-staging.onrender.com/api/v1/documents/<document-id>/ \
  -H "Authorization: Bearer <different-student-token>"

# Expected Response
{
  "detail": "Not found."
}

# Success Criteria
✅ HTTP 404 Not Found
✅ Students cannot access others' documents
✅ Authorization working correctly
```

**Test 4: File Persistence (Ephemeral Storage Warning)**
```bash
# Test file access
curl https://gofere-api-staging.onrender.com/media/documents/test-passport.pdf \
  -H "Authorization: Bearer <student-access-token>"

# After Render restart (redeploy)
curl https://gofere-api-staging.onrender.com/media/documents/test-passport.pdf \
  -H "Authorization: Bearer <student-access-token>"

# Expected Behavior
⚠️ File will be deleted after restart (LOCAL storage is ephemeral)
⚠️ Database record remains, but file is gone
⚠️ This is EXPECTED for staging (files in /tmp)
⚠️ Production will use S3/GCS/Azure (persistent)

# Success Criteria
✅ File accessible before restart
✅ File deleted after restart (ephemeral warning confirmed)
✅ No impact on production (separate environment)
```

### 5.8 Password Reset Testing (10 minutes)

**Test 1: Request Password Reset**
```bash
# Frontend Test
1. Navigate to: /student/forgot-password
2. Enter email: test-student@example.com
3. Submit

# API Test
curl -X POST https://gofere-api-staging.onrender.com/api/v1/auth/password/reset/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test-student@example.com"
  }'

# Expected Response
{
  "detail": "Password reset email sent."
}

# Success Criteria
✅ HTTP 200 OK
✅ Email logged in Render logs (console backend)
✅ Reset token generated
✅ Check logs for email content
```

**Password Reset Email Check:**
```bash
# Check Render logs
# Search for: "Password reset email accepted"
INFO apps.accounts.password_reset send_password_reset_email 
  Password reset email accepted by backend for user_id=<uuid>
  
# Email content logged:
Subject: Reset Your Gofer Exam Password
To: test-student@example.com
Body: Click here to reset: https://gofere-staging.vercel.app/reset-password?token=...

# Extract token from logs for next test
```

**Test 2: Reset Password with Token**
```bash
# Frontend Test
1. Extract token from logs
2. Navigate to: /student/reset-password?token=<token>
3. Enter new password: NewPass456!
4. Confirm password: NewPass456!
5. Submit

# API Test
curl -X POST https://gofere-api-staging.onrender.com/api/v1/auth/password/reset/confirm/ \
  -H "Content-Type: application/json" \
  -d '{
    "token": "<token-from-logs>",
    "password": "NewPass456!",
    "password_confirm": "NewPass456!"
  }'

# Success Criteria
✅ HTTP 200 OK
✅ Password changed successfully
✅ Can login with new password
✅ Cannot login with old password
✅ Token is single-use (cannot reuse)
```

### 5.9 Permission Testing (15 minutes)

**Test 1: Student Permissions**
```bash
# Can Access:
✅ /api/v1/students/me/ (own profile)
✅ /api/v1/scholarships/ (list public)
✅ /api/v1/applications/ (own applications)
✅ /api/v1/documents/ (own documents)

# Cannot Access:
❌ /api/v1/auth/users/ (user management - admin only)
✅ HTTP 403 Forbidden

# Cannot Access:
❌ /api/v1/applications/admin/overview/ (admin endpoint)
✅ HTTP 403 Forbidden

# Cannot Access:
❌ /api/v1/applications/consultant/assigned/ (consultant endpoint)
✅ HTTP 403 Forbidden
```

**Test 2: Consultant Permissions**
```bash
# Can Access:
✅ /api/v1/applications/consultant/assigned/ (assigned applications)
✅ /api/v1/consultations/ (consultations)

# Cannot Access:
❌ /api/v1/auth/users/ (user management - admin only)
✅ HTTP 403 Forbidden

# Cannot Access:
❌ /api/v1/scholarships/ (create/update - admin only)
✅ HTTP 403 Forbidden for POST/PUT
✅ HTTP 200 OK for GET (can view)
```

**Test 3: Admin Permissions**
```bash
# Can Access:
✅ /api/v1/auth/users/ (user management)
✅ /api/v1/scholarships/ (create/update/delete)
✅ /api/v1/applications/admin/overview/ (all applications)
✅ /admin/ (Django admin panel)

# Full CRUD access to all resources
```

**Test 4: Unauthenticated Access**
```bash
# Can Access (Public):
✅ /api/v1/health/liveness/
✅ /api/v1/health/readiness/
✅ /api/v1/health/
✅ /api/v1/schema/ (API documentation)

# Cannot Access (Requires Auth):
❌ /api/v1/students/me/
❌ /api/v1/applications/
❌ /api/v1/documents/
✅ HTTP 401 Unauthorized for all
```

### 5.10 Testing Summary Checklist

```
FUNCTIONAL TESTS CHECKLIST:
□ Health checks (3 endpoints)
□ User registration (student, consultant)
□ User login (success, failure)
□ Student profile (view, update, education)
□ Scholarships (list, detail, admin create)
□ Applications (create, submit, review)
□ Document upload (LOCAL storage)
□ Document authorization (cannot view others)
□ Password reset (request, confirm)
□ Permissions (student, consultant, admin, unauthenticated)

ESTIMATED TOTAL TIME: 2-3 hours for comprehensive testing
```

---

## 6. Database Backup and Restoration in Staging

### 6.1 Staging Backup Strategy

**Backup Approach for Staging:**
```bash
# Staging backups are for:
- Testing backup/restore procedures
- Recovering from test data corruption
- Creating baseline test datasets

# Staging backups are NOT for:
- Production data protection
- Compliance requirements
- Long-term retention
```

### 6.2 Manual Backup Testing

**Step 1: Create Staging Database Backup**
```bash
# Option A: From local machine (if have access)
pg_dump -h <render-staging-host> \
  -p 5432 \
  -U gofer_staging_user \
  -d gofer_exam_staging \
  -F custom \
  -f staging_backup_$(date +%Y%m%d_%H%M%S).dump

# Option B: From Render Shell
# Render Dashboard → gofere-api-staging → Shell
cd backend
./scripts/backup_database.sh

# Backup will be created in: backend/backups/
# File: gofer_exam_staging_backup_YYYYMMDD_HHMMSS.dump
```

**Step 2: Verify Backup**
```bash
# Check backup file
ls -lh backend/backups/

# Expected output:
-rw-r--r-- 1 user user 2.5M Nov 02 14:30 gofer_exam_staging_backup_20261102_143000.dump
-rw-r--r-- 1 user user   64 Nov 02 14:30 gofer_exam_staging_backup_20261102_143000.dump.sha256
-rw-r--r-- 1 user user  500 Nov 02 14:30 gofer_exam_staging_backup_20261102_143000.log

# Verify SHA-256 checksum
sha256sum -c backend/backups/gofer_exam_staging_backup_20261102_143000.dump.sha256

# Expected: gofer_exam_staging_backup_20261102_143000.dump: OK
```

**Step 3: Test Restore to Temporary Database**
```bash
# Create temporary database
psql -h <render-staging-host> -U gofer_staging_user -d postgres \
  -c "CREATE DATABASE gofer_exam_staging_restore_test;"

# Restore backup
pg_restore -h <render-staging-host> \
  -U gofer_staging_user \
  -d gofer_exam_staging_restore_test \
  --clean \
  --if-exists \
  -F custom \
  backend/backups/gofer_exam_staging_backup_20261102_143000.dump

# Verify restore
psql -h <render-staging-host> -U gofer_staging_user -d gofer_exam_staging_restore_test \
  -c "\dt"  # List tables
  
# Expected: 32 tables (same as original)

# Verify data
psql -h <render-staging-host> -U gofer_staging_user -d gofer_exam_staging_restore_test \
  -c "SELECT COUNT(*) FROM accounts_user;"
  
# Expected: Same count as original database
```

**Step 4: Cleanup Temporary Database**
```bash
# Drop test restore database
psql -h <render-staging-host> -U gofer_staging_user -d postgres \
  -c "DROP DATABASE gofer_exam_staging_restore_test;"

# Verify cleanup
psql -h <render-staging-host> -U gofer_staging_user -d postgres \
  -c "\l gofer_exam_staging_restore_test"
  
# Expected: database "gofer_exam_staging_restore_test" does not exist
```

### 6.3 Automated Backup Testing (Optional)

**Setup Backup Script in Render:**
```bash
# Render Dashboard → gofere-api-staging → Environment
# Add:
POSTGRES_DB=gofer_exam_staging
POSTGRES_USER=gofer_staging_user
POSTGRES_HOST=<render-pg-host>
POSTGRES_PASSWORD=<from-render-pg>

# Run backup test
# Render Shell → 
cd backend
bash scripts/test_backup_restore.sh

# Expected output:
Starting backup and restore test...
Creating backup...
Backup created: backend/backups/test/gofer_exam_backup_20261102_143500.dump
Creating temporary database...
Restoring backup...
Restore completed.
Verifying restore...
Tables verified: 32
Data verified: PASS
Cleaning up temporary database...
Cleanup complete.
Test PASSED
```

### 6.4 Backup Verification Checklist

```
BACKUP TESTING CHECKLIST:
□ Backup script runs without errors
□ Backup file created with .dump extension
□ SHA-256 checksum file created
□ Log file created with metadata
□ Backup file size > 0 bytes
□ Checksum verification passes
□ Temporary database creation succeeds
□ Restore completes with exit code 0 or 1 (warnings OK)
□ All 32 tables restored
□ Data integrity verified (row counts match)
□ Temporary database cleanup completes
□ No leftover test databases

ESTIMATED TIME: 30-45 minutes
```

---

## 7. Safe Email Testing Without Real Sends

### 7.1 Console Email Backend Configuration

**Current Configuration (Verified):**
```python
# config/settings/production.py (staging)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
GOFER_EMAIL_FROM = 'staging@example.com'

# All emails logged to console (Render logs)
# NO REAL EMAILS SENT
```

### 7.2 Email Testing Workflow

**Step 1: Trigger Email Event**
```bash
# Registration (triggers verification email)
curl -X POST https://gofere-api-staging.onrender.com/api/v1/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test-user@example.com",
    "password": "TestPass123!",
    "password_confirm": "TestPass123!",
    "first_name": "Test",
    "last_name": "User",
    "role": "STUDENT"
  }'
```

**Step 2: Check Render Logs**
```bash
# Render Dashboard → gofere-api-staging → Logs
# Real-time log stream

# Look for:
INFO apps.accounts.email_verification send_verification_email 
  Verification email accepted by backend for user_id=<uuid>

# Full email content will be logged:
Content-Type: text/plain; charset="utf-8"
MIME-Version: 1.0
Content-Transfer-Encoding: 7bit
Subject: Verify Your Gofer Exam Account
From: staging@example.com
To: test-user@example.com
Date: Sat, 02 Nov 2026 14:45:00 -0000
Message-ID: <...>

Hello Test User,

Thank you for registering at Gofer Exam.

Please verify your email address by clicking the link below:
https://gofere-staging.vercel.app/verify-email?token=abc123...

This link will expire in 60 minutes.

If you did not create an account, please ignore this email.

Best regards,
Gofer Exam Team
```

**Step 3: Extract Verification Token**
```bash
# From log output, copy token from URL
TOKEN=abc123def456ghi789...

# Use token to verify email
curl -X POST https://gofere-api-staging.onrender.com/api/v1/auth/verify-email/ \
  -H "Content-Type: application/json" \
  -d '{
    "token": "abc123def456ghi789..."
  }'

# Expected Response
{
  "detail": "Email verified successfully."
}
```

### 7.3 Email Event Testing Checklist

**All Email Events to Test:**

1. **Registration Verification Email**
   - Trigger: User registers
   - Log search: "Verification email accepted"
   - Contains: Verification link with token
   - Expiry: 60 minutes

2. **Password Reset Email**
   - Trigger: User requests password reset
   - Log search: "Password reset email accepted"
   - Contains: Reset link with token
   - Expiry: 60 minutes (PASSWORD_RESET_TIMEOUT)

3. **Email Delivery Failure**
   - Trigger: Simulate email failure (mock)
   - Log search: "email delivery failed"
   - Contains: Exception details
   - Status: Logged but not sent

**Email Testing Checklist:**
```
EMAIL TESTING CHECKLIST:
□ Console backend configured (EMAIL_BACKEND=console)
□ Registration email logged
□ Verification token visible in logs
□ Verification link includes staging frontend URL
□ Password reset email logged
□ Password reset token visible in logs
□ Email content is properly formatted
□ From address is staging@example.com
□ To address matches test user
□ Subject line correct
□ Email templates render correctly
□ Links point to staging frontend
□ Tokens work when extracted
□ No real emails sent to users

ESTIMATED TIME: 15-20 minutes
```

### 7.4 Email Testing Best Practices

**Safe Email Addresses for Testing:**
```bash
# Use @example.com domain (reserved for testing)
test-student@example.com
test-consultant@example.com
test-admin@example.com

# Or use + addressing (if testing with real domain later)
staging+student1@yourdomain.com
staging+student2@yourdomain.com

# NEVER use:
- Real user email addresses
- Personal email addresses
- Client email addresses
- Production email addresses
```

**Email Content Verification:**
```bash
# Verify email content includes:
✅ Correct recipient name
✅ Staging frontend URL (not production)
✅ Valid token (UUID format)
✅ Proper expiry warning
✅ Professional formatting
✅ No sensitive data (passwords, etc.)
✅ Unsubscribe link (optional for staging)
```

---

## 8. Cost Estimation and Free Tier Limitations

### 8.1 Render Costs (Backend + Database)

**Free Tier Limitations:**
```
Render Free Tier (Per Service):
- Spin down after 15 minutes of inactivity
- Spin up takes ~30 seconds on first request
- 750 hours/month free compute (enough for 1 service 24/7)
- Shared CPU and memory
- SSL certificates included
- Automatic deploys on git push

PostgreSQL Free Tier:
- 90 days free (then $7/month Starter plan)
- 1 GB storage
- 1 GB RAM
- Shared CPU
- Daily backups (1-day retention)
- SSL connections

Limitations:
⚠️ Services spin down after inactivity (cold starts)
⚠️ No guaranteed uptime
⚠️ Slower performance than paid tiers
⚠️ Limited support
```

**Starter Tier ($7/month per service):**
```
Web Service Starter ($7/month):
- Always on (no spin down)
- 0.5 GB RAM
- Shared CPU
- SSL certificates
- Automatic deploys
- Custom domains
- Better performance

PostgreSQL Starter ($7/month):
- 1 GB storage
- 1 GB RAM
- Daily backups (7-day retention)
- SSL connections
- Always available
```

**Staging Cost Scenarios:**

**Option A: Full Free Tier (90 days)**
```
Backend API (Render Web):      $0/month
Database (Render PostgreSQL):  $0/month (90 days free)
Frontend (Vercel):             $0/month
-------------------------------------------
TOTAL:                         $0/month for 90 days
                               $7/month after (database only)

Limitations:
⚠️ Backend spins down after 15 min inactivity
⚠️ First request takes ~30 seconds (cold start)
⚠️ Database becomes paid after 90 days
```

**Option B: Always-On Backend ($7/month)**
```
Backend API (Starter):         $7/month
Database (Free 90 days):       $0/month
Frontend (Vercel):             $0/month
-------------------------------------------
TOTAL:                         $7/month for 90 days
                               $14/month after

Benefits:
✅ No cold starts
✅ Faster response times
✅ Better for testing
```

**Option C: Full Starter ($14/month)**
```
Backend API (Starter):         $7/month
Database (Starter):            $7/month
Frontend (Vercel):             $0/month
-------------------------------------------
TOTAL:                         $14/month

Benefits:
✅ No cold starts
✅ Always available
✅ Better performance
✅ 7-day backup retention
✅ Custom domain support
```

### 8.2 Vercel Costs (Frontend)

**Free Tier (Hobby):**
```
Vercel Free Tier:
- Unlimited personal projects
- 100 GB bandwidth/month
- Automatic preview deployments
- SSL certificates
- Global CDN
- Serverless functions (100 GB-hours)
- 1,000 image optimizations/month
- Custom domains (1 per project)

Limitations:
✅ More than enough for staging
✅ No cold starts (always fast)
✅ Automatic HTTPS
✅ Git integration
```

**Pro Tier ($20/month - NOT NEEDED FOR STAGING):**
```
- More bandwidth (1 TB)
- More functions
- Analytics
- Password protection
- Team collaboration

NOT NEEDED FOR STAGING
```

### 8.3 Total Staging Costs

**Recommended Staging Configuration:**

**Month 1-3 (Free Tier Test):**
```
Backend:  $0 (Free tier with cold starts)
Database: $0 (Free tier - 90 days)
Frontend: $0 (Vercel free tier)
-----------------------------------------
TOTAL:    $0/month

Use case: Initial testing, low usage
```

**Month 4+ (After Testing):**

**Option 1: Keep Free Backend, Paid Database**
```
Backend:  $0 (Free tier - keep accepting cold starts)
Database: $7/month (Starter plan - required after 90 days)
Frontend: $0 (Vercel free tier)
-----------------------------------------
TOTAL:    $7/month

Use case: Infrequent staging use, cold starts acceptable
```

**Option 2: Always-On Staging (Recommended)**
```
Backend:  $7/month (Starter - no cold starts)
Database: $7/month (Starter - required after 90 days)
Frontend: $0 (Vercel free tier)
-----------------------------------------
TOTAL:    $14/month

Use case: Active development, frequent testing
```

### 8.4 Cost Comparison Summary

```
COST SUMMARY:
┌─────────────────┬──────────┬───────────┬──────────────┐
│ Configuration   │ Month 1-3│ Month 4+  │ Recommended  │
├─────────────────┼──────────┼───────────┼──────────────┤
│ Full Free       │ $0       │ $7        │ Testing only │
│ Always-On Back  │ $7       │ $14       │ Development  │
│ Full Starter    │ $14      │ $14       │ Production   │
└─────────────────┴──────────┴───────────┴──────────────┘

COMPARISON WITH PRODUCTION:
Staging:    $0-14/month
Production: $14-91/month (depends on scale)

SAVINGS: Staging is 50-85% cheaper than production
```

### 8.5 Free Tier Optimization Tips

**Maximize Free Tier Usage:**

1. **Keep Backend on Free Tier Initially**
   - Accept cold starts (30 seconds)
   - Test during active hours
   - Upgrade to Starter if cold starts become issue

2. **Use 90-Day Database Free Trial**
   - Full testing period at no cost
   - Decide on Starter plan after testing complete

3. **Leverage Vercel Free Tier**
   - Already sufficient for staging
   - No upgrade needed

4. **Schedule Testing**
   - Backend stays warm for 15 minutes
   - Run tests in batches to avoid cold starts
   - Ping health check every 10 minutes to keep warm

5. **Use Render Shell for Backups**
   - Free access to database
   - No egress charges
   - Run backup scripts directly

**Cost Avoidance Checklist:**
```
AVOID COSTS BY:
□ Using LOCAL storage (no S3/GCS/Azure)
□ Using console email backend (no AWS SES/Brevo)
□ Using free tier services
□ No paid monitoring (use free Sentry tier or none)
□ No custom domain (use .onrender.com and .vercel.app)
□ Accept cold starts on free tier
□ Limit staging to essential testing
□ Drop staging after production launch (if desired)

CANNOT AVOID:
□ Database after 90 days ($7/month)
```

---

## 9. Deployment Execution Timeline

### 9.1 Pre-Deployment Checklist

**BEFORE STARTING (Verify locally):**
```
□ All 297 tests passing
□ Git working copy clean or committed
□ Backend requirements.txt up to date
□ Frontend package.json up to date
□ Health check endpoints working locally
□ .env.example files up to date
□ Documentation reviewed
□ Approval received from stakeholder
```

### 9.2 Deployment Phases

**Phase 1: Render Backend Setup (30 minutes)**
```
Step 1.1: Create Staging Database (5 min)
  □ Log into Render dashboard
  □ Create new PostgreSQL instance
  □ Name: gofere-db-staging
  □ Plan: Free
  □ Copy DATABASE_URL

Step 1.2: Create Staging Web Service (10 min)
  □ Create new Web Service
  □ Connect GitHub repo
  □ Configure build/start commands
  □ Set root directory: backend

Step 1.3: Configure Environment Variables (15 min)
  □ Set 13 required environment variables
  □ Use DATABASE_URL from step 1.1
  □ Generate SECRET_KEY
  □ Set ALLOWED_HOSTS
  □ Configure email (console backend)
  □ Save and deploy
```

**Phase 2: Initial Backend Deployment (10 minutes)**
```
Step 2.1: Monitor Deployment (5 min)
  □ Watch Render build logs
  □ Verify dependencies install
  □ Verify collectstatic runs
  □ Verify migrations run

Step 2.2: Test Health Checks (5 min)
  □ Visit /api/v1/health/liveness/
  □ Visit /api/v1/health/readiness/
  □ Visit /api/v1/health/
  □ Verify database connection
```

**Phase 3: Vercel Frontend Setup (20 minutes)**
```
Step 3.1: Create Vercel Project (5 min)
  □ Log into Vercel dashboard
  □ Import gofer-exam repository
  □ Configure framework: Next.js
  □ Set build settings

Step 3.2: Configure Frontend Environment Variables (5 min)
  □ Set 4 required variables
  □ Set API_PROXY_TARGET to Render backend URL
  □ Set NEXT_PUBLIC_APP_URL

Step 3.3: Deploy Frontend (10 min)
  □ Trigger deployment
  □ Wait for build
  □ Get preview URL
  □ Test frontend loads
```

**Phase 4: CORS Configuration (15 minutes)**
```
Step 4.1: Update Backend CORS (10 min)
  □ Copy Vercel preview URL
  □ Update CORS_ALLOWED_ORIGINS in Render
  □ Update CSRF_TRUSTED_ORIGINS
  □ Redeploy backend

Step 4.2: Test Cross-Origin Requests (5 min)
  □ Open frontend
  □ Check browser console
  □ Verify no CORS errors
  □ Test API call (login page)
```

**Phase 5: Functional Testing (2-3 hours)**
```
Step 5.1: Core Functionality (30 min)
  □ Health checks
  □ User registration
  □ User login
  □ Email verification (logs)

Step 5.2: Profile & Data (45 min)
  □ Student profile
  □ Scholarships
  □ Applications

Step 5.3: Files & Permissions (45 min)
  □ Document upload
  □ Authorization
  □ Password reset
  □ Permissions

Step 5.4: Backup Testing (30 min)
  □ Create backup
  □ Verify backup
  □ Test restore
  □ Cleanup
```

**Phase 6: Documentation & Handoff (30 minutes)**
```
Step 6.1: Document Configuration (15 min)
  □ Record all environment variables
  □ Document Render URLs
  □ Document Vercel URLs
  □ Note any issues

Step 6.2: Create Test Accounts (15 min)
  □ Create admin account
  □ Create test student account
  □ Create test consultant account
  □ Document credentials (secure)
```

### 9.3 Total Timeline Summary

```
DEPLOYMENT TIMELINE:
Phase 1: Render Backend Setup         30 min
Phase 2: Initial Deployment           10 min
Phase 3: Vercel Frontend Setup        20 min
Phase 4: CORS Configuration           15 min
Phase 5: Functional Testing        2-3 hours
Phase 6: Documentation & Handoff      30 min
------------------------------------------------
TOTAL:                             3.5-4.5 hours

RECOMMENDED: Schedule 4-5 hours for complete deployment
```

---

## 10. Risk Assessment & Mitigation

### 10.1 Deployment Risks

**Risk 1: Backend Cold Starts (Free Tier)**
```
Probability: HIGH
Impact: MEDIUM
Mitigation:
  - Accept 30-second first-request delay
  - Upgrade to Starter ($7/month) if unacceptable
  - Ping health check every 10 minutes to keep warm
```

**Risk 2: Database Free Tier Expiry**
```
Probability: CERTAIN (90 days)
Impact: LOW
Mitigation:
  - Budget $7/month after 90 days
  - Set calendar reminder
  - Upgrade to Starter plan before expiry
```

**Risk 3: CORS Misconfiguration**
```
Probability: MEDIUM
Impact: HIGH (Frontend cannot access API)
Mitigation:
  - Double-check Vercel preview URL
  - Test after every CORS change
  - Use browser DevTools to debug
  - Follow Phase 4 carefully
```

**Risk 4: File Loss (LOCAL Storage)**
```
Probability: CERTAIN (on restart)
Impact: LOW (staging only)
Mitigation:
  - Document ephemeral nature
  - Don't rely on uploaded files
  - Re-upload test files after restart
  - Production will use S3/GCS/Azure
```

**Risk 5: Email Not Visible**
```
Probability: LOW
Impact: MEDIUM
Mitigation:
  - Use console backend (logged)
  - Check Render logs for email content
  - Extract tokens from logs
  - Test verification manually
```

### 10.2 Rollback Plan

**If Deployment Fails:**

1. **Backend Deployment Fails**
   ```
   - Check Render logs for errors
   - Verify environment variables
   - Verify DATABASE_URL connection
   - Check requirements.txt
   - Redeploy from previous commit
   ```

2. **Frontend Deployment Fails**
   ```
   - Check Vercel build logs
   - Verify package.json
   - Verify next.config.ts
   - Test locally: npm run build
   - Redeploy from previous commit
   ```

3. **Complete Rollback**
   ```
   - Delete Render web service
   - Delete Render database (if needed)
   - Delete Vercel project (if needed)
   - No impact on production (isolated)
   - Can restart deployment anytime
   ```

### 10.3 Success Criteria

**Staging Deployment Successful If:**
```
✅ Backend responds to health checks
✅ Frontend loads without errors
✅ User can register (email logged)
✅ User can login
✅ User can view profile
✅ User can upload document
✅ Password reset works (token in logs)
✅ No CORS errors in browser console
✅ All permissions working
✅ Database backup/restore tested
✅ All 297 tests still passing
```

---

## 11. Next Steps After Staging Deployment

### 11.1 Immediate Post-Deployment

**Day 1:**
```
□ Monitor Render logs for errors
□ Test all critical user flows
□ Verify email logging
□ Check database connections
□ Document any issues
```

**Week 1:**
```
□ Run full functional test suite daily
□ Test backup/restore weekly
□ Monitor cold starts (free tier)
□ Collect feedback from team
□ Fix any bugs found
```

### 11.2 Preparing for Production

**Before Production Deployment:**
```
□ Resolve all staging issues
□ Complete all functional tests
□ Create AWS SES account (or email provider)
□ Create S3 bucket (or storage provider)
□ Set up Sentry (optional)
□ Schedule automated backups
□ Document production procedures
□ Get stakeholder approval
```

### 11.3 Maintenance

**Ongoing Staging Maintenance:**
```
□ Keep staging in sync with development
□ Redeploy after major changes
□ Test new features in staging first
□ Reset database periodically (drop test data)
□ Monitor costs (free tier limits)
□ Upgrade to Starter plan after 90 days (database)
```

---

## 12. Approval Required

**THIS PLAN IS AWAITING YOUR APPROVAL**

Please review the plan and confirm:

1. ✅ Architecture is safe (isolated from production)
2. ✅ Environment variables are acceptable
3. ✅ Costs are acceptable ($0 for 90 days, $7-14/month after)
4. ✅ Testing approach is comprehensive
5. ✅ Timeline is reasonable (3.5-4.5 hours)
6. ✅ Risks are acceptable and mitigated

**ONCE APPROVED, I WILL:**
1. Prepare all configuration files
2. Generate environment variable templates
3. Create step-by-step execution scripts
4. Document each step with screenshots/commands
5. Wait for your signal to begin deployment

**I WILL NOT:**
- Create external services without permission
- Change production settings
- Deploy without confirmation
- Migrate production database
- Rotate secrets
- Purchase anything

**Ready to proceed when you approve.**

---

## Document Information

**Version:** 1.0  
**Date:** November 2, 2026  
**Status:** AWAITING APPROVAL  
**Author:** Kiro AI  
**Approver:** Project Owner  

**Related Documents:**
- FINAL_INDEPENDENT_VERIFICATION.md
- P0_PRODUCTION_READINESS_FINAL_REPORT.md
- render.yaml
- next.config.ts

---

**END OF STAGING DEPLOYMENT PLAN**
