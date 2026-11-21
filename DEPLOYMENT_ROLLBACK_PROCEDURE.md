# GOFER EXAM - DEPLOYMENT ROLLBACK PROCEDURE

**Document Version:** 1.0  
**Last Updated:** 2026-11-02  
**Owner:** DevOps Team

---

## PURPOSE

This document provides step-by-step procedures for rolling back a failed production deployment of the Gofer Exam platform. Use this procedure when a deployment causes critical issues that cannot be quickly fixed forward.

---

## ROLLBACK DECISION CRITERIA

### Immediate Rollback Required
Roll back immediately if any of these conditions occur:

- **Critical P0 Issues:**
  - ❌ Users unable to register or log in
  - ❌ Database corruption or data loss
  - ❌ Complete service outage (>5 minutes)
  - ❌ Security vulnerability exposed
  - ❌ Email verification completely broken
  - ❌ Payment processing failures (if applicable)

### Rollback Recommended
Consider rolling back if:

- **Severe P1 Issues:**
  - ⚠️ Major feature completely broken
  - ⚠️ Performance degradation >50%
  - ⚠️ Error rate >10% of requests
  - ⚠️ Database migrations failed partially
  - ⚠️ Critical user workflows broken

### Monitor and Fix Forward
Do NOT roll back if:

- ✅ Minor UI issues
- ✅ Non-critical feature bugs
- ✅ Issues affecting <5% of users
- ✅ Issues with workarounds available
- ✅ Performance degradation <20%

---

## PRE-ROLLBACK CHECKLIST

Before initiating rollback:

- [ ] **Confirm the issue** - Verify the problem is real and not user error
- [ ] **Check monitoring** - Review Sentry errors, health checks, logs
- [ ] **Estimate impact** - How many users affected? For how long?
- [ ] **Try quick fixes first** - Can this be fixed forward in <15 minutes?
- [ ] **Notify stakeholders** - Alert team that rollback is being initiated
- [ ] **Document the issue** - Record what went wrong for post-mortem

**Time Budget:** 
- P0 issues: Decide rollback within 5 minutes
- P1 issues: Decide rollback within 15 minutes

---

## ROLLBACK PROCEDURES

### Option 1: Backend Rollback (Django/Render)

**Use When:** Backend code or migrations caused the issue

#### Step 1: Identify Previous Working Deployment

```bash
# On Render dashboard or via CLI
# 1. Go to https://dashboard.render.com
# 2. Select "gofere-api-ruth2105" service
# 3. Click "Events" tab
# 4. Identify the last successful deployment before the problematic one
# 5. Note the commit SHA or deployment ID
```

#### Step 2: Check Database State

```bash
# Connect to production database
# From Render dashboard: Shell > Connect via psql

# Check current migration state
\c gofere
SELECT * FROM django_migrations ORDER BY applied DESC LIMIT 20;

# Document current state for rollback
```

#### Step 3: Decide on Database Rollback Strategy

**Option A: Migrations are backward compatible (PREFERRED)**
- New migrations only added columns/tables
- No data destructive operations
- Safe to rollback code without database rollback

**Option B: Migrations changed schema destructively**
- Renamed/deleted columns
- Changed data types
- Requires database rollback

#### Step 4A: Code-Only Rollback (If migrations compatible)

```bash
# On Render dashboard:
# 1. Go to service settings
# 2. Click "Manual Deploy"
# 3. Select "Deploy previous version"
# 4. Choose the last working commit
# 5. Click "Deploy"

# Monitor deployment:
# - Watch build logs
# - Check health endpoint: https://gofere-api-ruth2105.onrender.com/api/v1/health/
# - Monitor Sentry for errors
```

#### Step 4B: Database + Code Rollback (If schema changed)

**⚠️ CRITICAL: This causes downtime**

```bash
# Step 1: Put site in maintenance mode (if available)
# Or temporarily set ALLOWED_HOSTS to empty to block traffic

# Step 2: Create immediate database backup
# From Render dashboard:
# - Go to gofere-db database
# - Click "Backups"
# - Click "Create Manual Backup"
# - Wait for backup completion
# - Download backup locally as safety

# Step 3: Rollback migrations
# Connect to Render shell:
render shell

# Inside shell:
cd /opt/render/project/src/backend
python manage.py showmigrations

# Identify migration to rollback to
# Example: rollback scholarships app to migration 0005
python manage.py migrate scholarships 0005

# Verify no errors
# Repeat for each app that needs rollback

# Step 4: Deploy previous code version
# Follow Step 4A procedure above

# Step 5: Verify rollback
# - Health check returns 200
# - Test critical user flows
# - Check Sentry for errors

# Step 6: Remove maintenance mode
```

#### Step 5: Verify Backend Rollback

```bash
# Health check
curl -I https://gofere-api-ruth2105.onrender.com/api/v1/health/

# Test critical endpoints
curl https://gofere-api-ruth2105.onrender.com/api/v1/csrf/
curl https://gofere-api-ruth2105.onrender.com/api/v1/scholarships/

# Check Sentry dashboard
# - Error rate should decrease
# - No new critical errors

# Test complete user journey
# 1. Registration
# 2. Email verification
# 3. Login
# 4. Browse scholarships
```

---

### Option 2: Frontend Rollback (Next.js/Vercel)

**Use When:** Frontend code caused the issue

#### Step 1: Identify Previous Deployment

```bash
# On Vercel dashboard
# 1. Go to https://vercel.com/dashboard
# 2. Select "gofere" project
# 3. Click "Deployments" tab
# 4. Identify last successful deployment
# 5. Note the deployment URL
```

#### Step 2: Rollback to Previous Deployment

```bash
# Option A: Via Vercel Dashboard (RECOMMENDED)
# 1. Click on the working deployment
# 2. Click "..." menu
# 3. Click "Promote to Production"
# 4. Confirm promotion

# Option B: Via Vercel CLI
vercel rollback https://gofere-xyz123.vercel.app
```

#### Step 3: Verify Frontend Rollback

```bash
# Clear browser cache or use incognito
# Visit: https://gofere.vercel.app

# Test critical pages:
# - Homepage loads
# - Navigation works
# - Scholarships page loads
# - Login page loads
# - Registration page loads

# Check browser console for errors
# Check Network tab for failed requests
```

---

### Option 3: Full Stack Rollback

**Use When:** Both frontend and backend need rollback

1. **Roll back backend first** (Option 1)
2. **Verify backend working**
3. **Roll back frontend** (Option 2)
4. **Verify end-to-end functionality**

---

## POST-ROLLBACK PROCEDURES

### Immediate Actions (Within 30 minutes)

- [ ] **Verify rollback success**
  - All health checks passing
  - Error rate back to baseline
  - Critical user flows working
  
- [ ] **Monitor for 30 minutes**
  - Watch Sentry for new errors
  - Check server resources (CPU, memory, database connections)
  - Monitor user reports/support tickets
  
- [ ] **Update stakeholders**
  - Post in team chat: "Rollback complete, services restored"
  - Update status page if public incident
  - Notify users if needed

- [ ] **Secure failed deployment artifacts**
  - Don't delete the failed code
  - Keep logs and error reports
  - Document what happened

### Within 24 Hours

- [ ] **Create incident report**
  - What went wrong?
  - How was it detected?
  - How long was impact?
  - How many users affected?
  - What was the fix?
  
- [ ] **Schedule post-mortem meeting**
  - Include all involved team members
  - Focus on process improvement, not blame
  
- [ ] **Update deployment procedures**
  - Add new checks to prevent recurrence
  - Update testing requirements
  - Improve monitoring/alerting

### Within 1 Week

- [ ] **Fix root cause**
  - Identify what caused the failure
  - Implement proper fix
  - Add tests to prevent regression
  
- [ ] **Test fix thoroughly**
  - Staging environment testing
  - Load testing if performance issue
  - End-to-end testing
  
- [ ] **Plan re-deployment**
  - Schedule during low-traffic window
  - Have team available for monitoring
  - Prepare rollback plan for re-attempt

---

## DATABASE RECOVERY PROCEDURES

### Scenario 1: Database Corrupted

```bash
# CRITICAL: Stop all write operations immediately
# Set backend to read-only mode or take offline

# Step 1: Assess damage
# Connect to database
psql $DATABASE_URL

# Check table integrity
\dt
SELECT count(*) FROM accounts_user;
SELECT count(*) FROM scholarships_scholarship;
# etc.

# Step 2: Restore from backup
# From Render dashboard:
# - Go to gofere-db database
# - Click "Backups"
# - Select most recent backup before corruption
# - Click "Restore" (creates new database)

# Step 3: Update DATABASE_URL
# - Point backend to restored database
# - Redeploy backend with new DATABASE_URL

# Step 4: Data reconciliation
# - Identify lost data (between backup and corruption)
# - Communicate data loss to users if needed
# - Implement recovery plan for lost data
```

### Scenario 2: Migration Failed Partially

```bash
# Step 1: Check migration state
python manage.py showmigrations

# Step 2: Try to complete migration
python manage.py migrate --fake-initial

# If that fails:
# Step 3: Manual migration repair
# Connect to database and manually fix schema
# Then fake the migration
python manage.py migrate app_name migration_name --fake

# Step 4: Verify database consistency
python manage.py check
python manage.py test
```

---

## EMERGENCY CONTACTS

**Deployment Team:**
- DevOps Lead: [contact info]
- Backend Lead: [contact info]
- Frontend Lead: [contact info]

**Service Providers:**
- Render Support: https://render.com/support
- Vercel Support: https://vercel.com/support
- Database Admin: [contact info]

**Escalation Path:**
1. DevOps Lead (0-15 min)
2. Technical Lead (15-30 min)
3. CTO/Engineering Manager (30+ min)

---

## ROLLBACK TIME ESTIMATES

| Scenario | Estimated Time | Downtime |
|----------|---------------|----------|
| Frontend only | 5 minutes | None (Vercel atomic) |
| Backend code only | 10-15 minutes | None (rolling deploy) |
| Backend + database (compatible) | 15-20 minutes | None |
| Backend + database (incompatible) | 30-60 minutes | 15-30 minutes |
| Full stack | 20-30 minutes | None to 15 min |
| Database restore | 45-90 minutes | 30-60 minutes |

---

## ROLLBACK TESTING CHECKLIST

**After every rollback, test these critical flows:**

### Authentication
- [ ] User registration
- [ ] Email verification
- [ ] User login
- [ ] Password reset

### Core Features  
- [ ] Browse scholarships
- [ ] Filter scholarships
- [ ] View scholarship details
- [ ] Browse opportunities
- [ ] Student profile

### Admin Functions
- [ ] Admin login
- [ ] View dashboard
- [ ] Manage content

### System Health
- [ ] Health endpoint returns 200
- [ ] API response times <2s
- [ ] Error rate <1%
- [ ] Database connections stable

---

## PREVENTION MEASURES

**To reduce need for rollbacks:**

1. **Staging Environment**
   - Always deploy to staging first
   - Test for 24 hours minimum
   - Run load tests on staging

2. **Gradual Rollouts**
   - Use feature flags for new features
   - Deploy to 10% of users first
   - Monitor for 1 hour before full deploy

3. **Automated Testing**
   - All tests must pass before deploy
   - Include integration tests
   - Run performance regression tests

4. **Database Migrations**
   - Always write backward-compatible migrations
   - Test migrations on copy of production data
   - Have rollback migrations prepared

5. **Monitoring**
   - Set up alerts for critical metrics
   - Monitor error rates during deploy
   - Have kill switch ready

6. **Communication**
   - Notify team before deployment
   - Have team available during deploy
   - Schedule deploys during low-traffic windows

---

## LESSONS LEARNED LOG

| Date | Issue | Cause | Resolution | Prevention |
|------|-------|-------|------------|------------|
| 2026-11-02 | Audit identified no rollback plan | Planning gap | Created this document | Include in deployment checklist |
| | | | | |

*Update this log after each rollback to improve procedures*

---

## DOCUMENT MAINTENANCE

- **Review Frequency:** Quarterly
- **Owner:** DevOps Team
- **Next Review:** 2027-02-02
- **Version History:**
  - v1.0 (2026-11-02): Initial version

---

## APPENDIX A: Quick Reference Commands

```bash
# Backend Rollback (Render)
render deploy [service-name] [commit-sha]

# Frontend Rollback (Vercel)
vercel rollback [deployment-url]

# Database Backup
# Via Render dashboard: Database > Backups > Create Manual Backup

# Check Migration Status
python manage.py showmigrations

# Rollback Migration
python manage.py migrate [app-name] [migration-name]

# Health Check
curl https://gofere-api-ruth2105.onrender.com/api/v1/health/

# Test CSRF Endpoint
curl https://gofere-api-ruth2105.onrender.com/api/v1/csrf/

# Check Frontend
curl -I https://gofere.vercel.app
```

---

## APPENDIX B: Rollback Decision Tree

```
Issue Detected
    │
    ├─ Critical (P0)?
    │  └─ YES → Immediate Rollback
    │
    ├─ Severe (P1)?
    │  ├─ Can fix forward in <15 min?
    │  │  ├─ YES → Fix forward
    │  │  └─ NO → Rollback
    │  └─ Affects >50% users?
    │     ├─ YES → Rollback
    │     └─ NO → Monitor and decide
    │
    └─ Minor (P2)?
       └─ Fix forward, no rollback needed
```

---

**END OF DOCUMENT**
