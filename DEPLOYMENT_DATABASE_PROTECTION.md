# Database Protection & Backup Strategy

**Date**: November 21, 2026  
**Database**: PostgreSQL (gofere-db on Render)  
**Current Local Migrations**: All applied (56 total migrations)

## Pre-Deployment Checklist

### 1. Verify Database Status (REQUIRED - User Action)

**Via Render Dashboard**:
1. Go to: https://dashboard.render.com/
2. Navigate to: Databases → `gofere-db`
3. Check **Status**: Should be "Available"
4. Check **Expiration Date**: Free tier databases expire after 90 days
5. Check **Last Backup**: Verify automated backups are enabled

### 2. Create Manual Backup (REQUIRED Before Deployment)

**Option A: Via Render Dashboard** (Recommended)
1. Render Dashboard → `gofere-db` → Backups tab
2. Click "Create Manual Backup"
3. Wait for completion
4. Download backup file for local storage

**Option B: Via Command Line** (Requires DATABASE_URL from Render)
```bash
# Get DATABASE_URL from Render Dashboard → gofere-db → Connection Info
pg_dump $DATABASE_URL > gofer_backup_$(date +%Y%m%d_%H%M%S).sql

# Verify backup file size
ls -lh gofer_backup_*.sql
```

### 3. Test Backup Restore (Recommended)

```bash
# Create test database locally
createdb gofer_test_restore

# Restore backup to test database
psql gofer_test_restore < gofer_backup_YYYYMMDD_HHMMSS.sql

# Verify restoration
psql gofer_test_restore -c "SELECT COUNT(*) FROM accounts_user;"
psql gofer_test_restore -c "SELECT COUNT(*) FROM scholarships_scholarship;"

# Clean up test database
dropdb gofer_test_restore
```

## Migration Analysis

### Current Migration State (Local - All Applied)

```
Total Migrations: 56
- accounts: 3 migrations
- applications: 1 migration
- common: 1 migration (249 countries seeded)
- consultants: 1 migration
- consultations: 1 migration
- destinations: 1 migration
- documents: 1 migration
- health: 0 migrations (no models)
- notifications: 1 migration
- opportunities: 6 migrations
- scholarships: 4 migrations
- services: 1 migration
- students: 3 migrations
- universities: 1 migration
- token_blacklist: 12 migrations (JWT)
```

### Migrations Since Last Production Deploy (30ab294)

Based on git history, production is running commit **30ab294** (Sept 6, 2024).  
Current HEAD is **b0669ed** (Nov 21, 2026).

**New migrations to be applied in production**:

1. **accounts/0002_emailverificationtoken.py**
   - Risk: LOW
   - Action: Creates new table for email verification tokens
   - Impact: No existing data affected

2. **accounts/0003_securityauditevent.py**
   - Risk: LOW
   - Action: Creates new table for security audit logging
   - Impact: No existing data affected

3. **common/0001_initial.py**
   - Risk: LOW
   - Action: Creates Country table and seeds 249 countries
   - Impact: New functionality, no existing data affected

4. **opportunities/0001-0006** (6 migrations)
   - Risk: LOW-MEDIUM
   - Action: Creates opportunity management system
   - Impact: New tables, no existing data affected

5. **scholarships/0003_scholarship_country_reference**
   - Risk: MEDIUM
   - Action: Adds country FK to Scholarship model
   - Impact: **Modifies existing scholarships table**
   - Safety: Field is nullable, existing records preserved

6. **scholarships/0004_opportunity_management_mvp**
   - Risk: MEDIUM  
   - Action: Alters status field choices in Opportunity model
   - Impact: **Modifies field constraints**
   - Safety: Only extends choices, existing values remain valid

7. **students/0002_studentprofile_nationality_country**
   - Risk: MEDIUM
   - Action: Adds nationality FK to StudentProfile
   - Impact: **Modifies existing student profiles**
   - Safety: Field is nullable, existing records preserved

8. **students/0003_education_skill_workexperience**
   - Risk: LOW
   - Action: Creates new tables for student details
   - Impact: No existing data affected

### Migration Risk Assessment

**Safe to Deploy**: ✅ YES

All migrations are:
- Additive (new tables/fields) OR
- Non-destructive modifications (nullable foreign keys, extended choices)
- No data deletion
- No field removals
- No table drops

**However**: Database backup is **MANDATORY** before proceeding.

## Rollback Strategy

### If Deployment Fails During Migrations

Render automatically handles this:
- Failed deployment stays on old version
- Database migrations are NOT rolled back
- Old backend (30ab294) continues running
- New backend fails to start

**Manual Intervention Required**:
```bash
# Connect to production database
psql $DATABASE_URL

# Check last applied migration
SELECT * FROM django_migrations ORDER BY applied DESC LIMIT 5;

# If migrations partially applied, you may need to:
# 1. Keep the new migrations (safe - they're additive)
# 2. Fix the deployment issue
# 3. Redeploy

# DO NOT manually reverse migrations unless data is corrupted
```

### If Application Works but Data Issues Appear

**Restore from Backup** (LAST RESORT ONLY):
```bash
# ⚠️ WARNING: This will ERASE all data since backup
# Only use if data is corrupted and unusable

# 1. Download backup from Render dashboard
# 2. Restore via Render dashboard: Backups → Restore

# OR via command line:
psql $DATABASE_URL < gofer_backup_YYYYMMDD_HHMMSS.sql
```

## Production Deployment Command Sequence

Render will execute these automatically:

```bash
# 1. Build phase (runs in clean environment)
pip install -r requirements/production.txt
python manage.py collectstatic --no-input

# 2. Start phase (runs migrations before starting server)
python manage.py migrate --noinput
gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
```

**Migration logs will appear in**: Render Dashboard → gofere-api-ruth2105 → Logs

## Post-Deployment Verification

### 1. Check Migration Status

```bash
# Via Render Shell (Dashboard → Shell tab)
python manage.py showmigrations

# All should show [X]
```

### 2. Verify Data Integrity

```bash
# Check user count
python manage.py shell -c "from apps.accounts.models import User; print(User.objects.count())"

# Check scholarship count  
python manage.py shell -c "from apps.scholarships.models import Scholarship; print(Scholarship.objects.count())"

# Check country seeding worked
python manage.py shell -c "from apps.common.models import Country; print(Country.objects.count())"
# Expected: 249 countries
```

### 3. API Health Checks

```bash
# Health endpoint (should return 200)
curl https://gofere-api-ruth2105.onrender.com/api/v1/health/

# Schema endpoint (should return 200)
curl https://gofere-api-ruth2105.onrender.com/api/v1/schema/
```

## Database Expiration Warning

**Render Free Tier**: PostgreSQL databases expire after **90 days** of creation.

**Action Required**:
1. Check creation date in Render dashboard
2. If approaching expiration, upgrade to paid tier OR
3. Export all data before expiration
4. Create new database and restore data

## Summary

- ✅ **All migrations are safe** (additive/non-destructive)
- ✅ **No pending migrations locally** (makemigrations --check passes)
- ⚠️ **Manual backup REQUIRED before deployment**
- ⚠️ **Verify database expiration date**
- ✅ **Rollback strategy documented**
- ✅ **Production deployment will auto-run migrations**

**Next Steps**:
1. User creates manual backup via Render dashboard
2. User verifies database expiration date
3. User adds BREVO_API_KEY to Render environment variables
4. Deploy updated code to Render
5. Verify migrations completed successfully
6. Test live API endpoints
