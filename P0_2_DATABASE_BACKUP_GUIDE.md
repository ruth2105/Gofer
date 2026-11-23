# P0-2: Database Backup & Upgrade Guide

**Date:** 2026-11-02  
**Status:** Backup scripts implemented & tested locally  
**Purpose:** Database backup procedures, upgrade options, and disaster recovery planning

---

## Current State Summary

### Development (Local)
- **Database:** PostgreSQL 18.6 (localhost)
- **Name:** `gofer_exam`
- **Tables:** 32 tables, 54 migrations applied
- **Data:** 249 countries, 2 users (test data)
- **Backup:** ✅ Manual scripts working (159KB backup, 4sec, verified)

### Production (Render)
- **Database:** `gofere-db` (Render Free tier)
- **Plan:** FREE
- **Limitations:**
  - ❌ **NO automated backups**
  - ❌ **NO point-in-time recovery**
  - ⚠️ **30-day expiry** after inactivity
  - ⚠️ **Ephemeral** - can be deleted without warning
- **Status:** ❌ **NOT SUITABLE FOR PRODUCTION DATA**

---

## Backup Scripts

### Implemented Scripts

**Location:** `backend/scripts/`

1. **`backup_database.ps1`** (Windows/development)
   - Automated pg_dump with compression
   - SHA-256 integrity verification
   - Automated retention policy
   - Detailed logging
   - Tested: ✅ Works on local database

2. **`backup_database.sh`** (Linux/production)
   - Same features as PowerShell version
   - Works with DATABASE_URL (Render-compatible)
   - Retention policy (30 days default)
   - Untested on production (authorization required)

3. **`restore_database.sh`** (Linux/production)
   - Safe restore with verification
   - Dry-run mode
   - Hash verification
   - Rollback-friendly

4. **`test_backup_restore.ps1`** (Windows testing)
   - Automated test suite
   - Creates temporary database
   - Verifies data integrity
   - Cleanup after test

### Test Results (Local Only)

**Backup Test:**
```
Database: gofer_exam (local dev)
Duration: 4.06 seconds
Backup size: 159 KB (159,276 bytes)
Tables: 32
SHA-256: 681A4852E95E866158D19EE6FD7B9B26CF24AC99FEF630660000135BC8C0A5A0
Verification: PASSED
```

**Restore Test:**
```
Source: gofer_exam (32 tables, 249 countries, 54 migrations, 2 users)
Target: gofer_exam_restore_test20261120 (temporary)
Result: ✅ All data verified identical
Duration: ~10 seconds
Cleanup: ✅ Test database dropped
```

**Limitations:**
- Tests performed on LOCAL database only
- Production database NOT accessed
- No production restore drill performed yet

---

## Database Upgrade Options

### Option 1: Render Standard PostgreSQL ⭐ RECOMMENDED

**Pricing (2026):**
- **Starter:** $7/month
  - 0.1 GB RAM
  - 1 GB storage included ($0.30/GB additional)
  - Automated daily backups
  - 7-day point-in-time recovery (PITR)
  - 99.9% uptime SLA

- **Standard:** $25/month
  - 1 GB RAM
  - 10 GB storage included
  - Automated continuous backups
  - 7-day PITR
  - 99.95% uptime SLA

- **Pro:** $85/month
  - High availability (automatic failover)
  - Standby replica
  - Read replicas available
  - 14-day PITR
  - 99.99% uptime SLA

**Backup Features:**
- Continuous point-in-time recovery (paid plans only)
- Automated daily backups
- One-click restore to any point in time (within retention period)
- Backup storage: first 10 GB included, then $0.30/GB/month

**Migration Path:**
1. Upgrade plan in Render dashboard
2. No database recreation needed
3. Backups start automatically
4. Zero downtime

**Pros:**
- Easiest migration (no config changes)
- Same provider as current deployment
- Automatic PITR for paid plans
- No new credentials needed
- Integrated with Render services

**Cons:**
- Render-specific (vendor lock-in)
- Storage costs scale at $0.30/GB (higher than alternatives)
- Limited to 7-day PITR on Starter

**Recommendation:** **Starter ($7/month)** for launch, upgrade to Standard later if needed.

---

### Option 2: AWS RDS PostgreSQL

**Pricing (2026):**
Content rephrased for compliance based on [AWS RDS pricing information](https://aws.amazon.com/rds/postgresql/pricing/) and [managed database comparisons](https://encore.dev/articles/rds-vs-cloud-sql).

- **db.t4g.micro:** ~$15-20/month
  - 1 GB RAM, 1 vCPU (ARM-based)
  - 20 GB storage included (gp3)
  - Multi-AZ: +100% cost (~$40/month)
  - Backup storage: first 20 GB free

- **db.t4g.small:** ~$30-40/month
  - 2 GB RAM, 2 vCPU
  - Better performance for production workloads

**Backup Features:**
- Automated daily backups
- Up to 35 days retention
- Point-in-time recovery to any second
- Manual snapshots (unlimited retention)
- Cross-region backup copy available
- Backup storage: 100% of DB size free, then $0.095/GB/month

**Pros:**
- Industry standard, battle-tested
- Longest PITR retention (35 days vs 7-14 days)
- Read replicas for scaling
- Performance Insights included
- Strong ecosystem (CloudWatch, IAM, etc.)

**Cons:**
- Higher base cost ($15-40 vs $7)
- More complex setup (VPC, security groups, IAM)
- Requires AWS account and billing
- Need to configure DATABASE_URL in Render
- Network egress charges if Render backend not in same region

**Migration Path:**
1. Create RDS instance in AWS console
2. Configure VPC to allow Render IP ranges
3. Run backup: `pg_dump $RENDER_DB_URL > backup.sql`
4. Restore to RDS: `psql $RDS_URL < backup.sql`
5. Update DATABASE_URL in Render
6. Test application
7. Delete Render database

---

### Option 3: Google Cloud SQL for PostgreSQL

**Pricing (2026):**
- **db-f1-micro (shared):** ~$7-10/month
  - 0.6 GB RAM, shared vCPU
  - 10 GB storage included
  - Automated backups

- **db-g1-small:** ~$25-35/month
  - 1.7 GB RAM, 1 vCPU
  - High availability: +100% cost

**Backup Features:**
- Automated daily backups
- 7-30 days retention (configurable)
- Point-in-time recovery
- On-demand backups
- Backup storage: first 10 GB free, then $0.08/GB/month

**Pros:**
- Competitive pricing
- Good performance
- Integrated with GCP ecosystem
- Lower backup storage costs vs Render

**Cons:**
- Requires Google Cloud account
- Similar complexity to AWS
- Network egress fees
- Less familiar to most developers than RDS

---

### Option 4: DigitalOcean Managed PostgreSQL

**Pricing (2026):**
Per [managed database comparison sources](https://github.com/qzdy7644/digitalocean-postgresql-pricing):

- **Basic (1 GB RAM):** ~$15/month
  - 1 vCPU, 10 GB storage
  - Automated daily backups
  - Standby nodes: additional cost

- **Professional (2 GB RAM):** ~$55/month (with standby)
  - High availability included
  - 50 GB storage

**Backup Features:**
- Daily automated backups
- 7-day retention
- Point-in-time recovery (with standby)
- One-click restore

**Pros:**
- Developer-friendly UI
- Competitive pricing
- Good documentation
- Simpler than AWS/GCP

**Cons:**
- Shorter PITR retention (7 days)
- Smaller ecosystem
- Less feature-rich than AWS RDS

---

### Option 5: Supabase PostgreSQL

**Pricing (2026):**
- **Free:** $0/month
  - 500 MB database
  - 7-day PITR
  - 1 GB backup storage
  - 2 GB egress

- **Pro:** $25/month
  - 8 GB database
  - 7-day PITR
  - 100 GB backup storage
  - 50 GB egress

**Pros:**
- Free tier with backups (unlike Render Free)
- Modern developer experience
- Built-in auth and storage
- Generous free tier for small projects

**Cons:**
- Limited to 500 MB on free tier
- Supabase-specific ecosystem
- Less established than RDS/CloudSQL
- May need migration if outgrow platform

---

## Comparison Matrix

| Provider | Entry Cost | Storage | Backups | PITR Retention | HA Available | Migration Effort |
|----------|------------|---------|---------|----------------|--------------|------------------|
| **Render Free** | $0 | Ephemeral | ❌ None | N/A | No | N/A (current) |
| **Render Starter** ⭐ | $7/mo | 1 GB + $0.30/GB | ✅ Daily | 7 days | No | ⭐ Easy (upgrade) |
| **Render Standard** | $25/mo | 10 GB + $0.30/GB | ✅ Continuous | 7 days | No | ⭐ Easy |
| **AWS RDS Micro** | $15-20/mo | 20 GB + $0.10/GB | ✅ Daily | 35 days | Yes (+100%) | Medium |
| **GCP SQL Micro** | $7-10/mo | 10 GB + $0.08/GB | ✅ Daily | 7-30 days | Yes (+100%) | Medium |
| **DigitalOcean** | $15/mo | 10 GB + $0.15/GB | ✅ Daily | 7 days | Yes (+$40) | Medium |
| **Supabase Free** | $0 | 500 MB | ✅ Daily | 7 days | No | Hard (replatform) |

---

## Recommended Strategy

### Phase 1: Immediate (Launch Readiness)

**Upgrade to Render Starter ($7/month):**

1. **Before upgrade:**
   - Create final backup of Render Free database (if data exists)
   - Test backup scripts on local database (✅ done)
   - Document current row counts for verification

2. **Upgrade process:**
   ```bash
   # 1. Login to Render dashboard
   # 2. Navigate to gofere-db database
   # 3. Settings → Plans → Upgrade to Starter
   # 4. Confirm payment method
   # 5. Wait for upgrade (typically instant)
   ```

3. **Verify backups:**
   - Check Render dashboard → Database → Backups
   - Verify PITR is enabled (7-day window)
   - Test restore to point-in-time (use test data)

4. **Monitor:**
   - Set up database metrics alerts
   - Monitor storage usage
   - Plan for Standard upgrade if needed

**Cost:** $7/month = **$84/year**

**Benefits:**
- ✅ Automated daily backups
- ✅ 7-day point-in-time recovery
- ✅ Zero migration effort
- ✅ No application downtime
- ✅ Same DATABASE_URL

---

### Phase 2: Growth (6-12 months)

**Consider AWS RDS if:**
- Database >10 GB (Render storage costs add up)
- Need >7 days PITR
- Need read replicas
- Want multi-region capability

**Migration window:** After user base stabilizes, before critical mass

**Estimated cost:** $25-40/month with backups

---

### Phase 3: Scale (12+ months)

**Evaluate:**
- High availability needs (Multi-AZ, standby replicas)
- Performance optimization (connection pooling, read replicas)
- Disaster recovery requirements (cross-region backups)
- Compliance needs (encryption, audit logs)

**Budget:** $100-200/month for HA production setup

---

## Backup Schedule & Procedures

### Automated Backups (Post-Upgrade)

**Render Starter/Standard:**
- **Frequency:** Continuous (PITR) + Daily snapshots
- **Retention:** 7 days (Starter/Standard), 14 days (Pro)
- **Storage:** First 10 GB included, then $0.30/GB/month
- **Recovery Point Objective (RPO):** <1 minute (continuous PITR)
- **Recovery Time Objective (RTO):** 5-15 minutes (restore + reconnect)

**Backup verification:**
```bash
# Monthly drill (schedule in calendar)
1. Navigate to Render → Database → Backups
2. Select backup from 24 hours ago
3. Restore to new temporary database
4. Verify row counts match production
5. Test application connection
6. Delete temporary database
```

---

### Manual Off-Site Backups (Recommended)

**Frequency:** Weekly (Sundays, 2 AM UTC)

**Script:** `backend/scripts/backup_database.sh`

**Storage:** AWS S3, Google Cloud Storage, or Azure Blob
- **Cost:** ~$0.02/month for 1 GB (negligible)
- **Retention:** 90 days (4 weekly + 12 monthly backups)

**Procedure:**
```bash
# Run on Render or local machine with production access
export DATABASE_URL="postgresql://..."
export BACKUP_DIR="/path/to/backups"
export BACKUP_RETENTION_DAYS=90

./backend/scripts/backup_database.sh

# Upload to S3 (example)
aws s3 cp $BACKUP_DIR/*.dump s3://gofer-exam-db-backups/ \
    --storage-class GLACIER_IR \
    --expires $(date -d '+90 days' -u +%Y-%m-%dT%H:%M:%SZ)
```

**Benefits:**
- Off-site disaster recovery
- Protection against Render outages
- Longer retention than Render PITR
- Export for compliance/auditing

---

### Backup Automation Options

**Option A: Render Cron Job (Recommended)**
```yaml
# Add to render.yaml
services:
  - type: cron
    name: database-backup
    schedule: "0 2 * * 0"  # Weekly, Sundays at 2 AM UTC
    command: ./backend/scripts/backup_database.sh && ./upload_to_s3.sh
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: gofere-db
          property: connectionString
      - key: AWS_ACCESS_KEY_ID
        sync: false
      - key: AWS_SECRET_ACCESS_KEY
        sync: false
```

**Option B: GitHub Actions**
```yaml
# .github/workflows/database-backup.yml
name: Weekly Database Backup
on:
  schedule:
    - cron: '0 2 * * 0'  # Sundays at 2 AM UTC
  workflow_dispatch:  # Manual trigger

jobs:
  backup:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Backup database
        env:
          DATABASE_URL: ${{ secrets.RENDER_DATABASE_URL }}
        run: |
          cd backend/scripts
          chmod +x backup_database.sh
          ./backup_database.sh /tmp/backups
      - name: Upload to S3
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1
      - run: aws s3 sync /tmp/backups s3://gofer-exam-db-backups/
```

**Option C: Local Cron (Development)**
```bash
# Add to crontab
0 2 * * 0 cd /path/to/gofer-exam/backend/scripts && PGPASSWORD=123456 ./backup_database.sh
```

---

## Restore Procedures

### Scenario 1: Accidental Data Loss (Within PITR Window)

**Recovery Time:** 5-15 minutes

**Steps:**
1. Identify when the error occurred (e.g., "table dropped at 14:30 UTC")
2. Navigate to Render Dashboard → Database → Backups
3. Click "Restore to Point in Time"
4. Select timestamp BEFORE the error (e.g., 14:25 UTC)
5. Choose "Restore to new database" (safer) or "Restore in place" (faster)
6. Wait for restore to complete (~5-10 minutes for 1 GB)
7. If restored to new database:
   - Update DATABASE_URL in Render environment
   - Restart application
   - Verify data integrity
   - Delete old database
8. If restored in place:
   - Application reconnects automatically
   - Verify data integrity

**Verification:**
```sql
-- Check row counts
SELECT 'users' as table_name, COUNT(*) FROM users
UNION ALL SELECT 'applications', COUNT(*) FROM applications
UNION ALL SELECT 'documents', COUNT(*) FROM documents;

-- Check recent records
SELECT * FROM django_migrations ORDER BY applied DESC LIMIT 5;
```

---

### Scenario 2: Complete Database Loss (PITR Unavailable)

**Recovery Time:** 15-30 minutes (if off-site backup exists)

**Steps:**
1. Create new PostgreSQL database (Render or alternative)
2. Locate most recent backup file (S3, local, etc.)
3. Verify backup integrity:
   ```bash
   pg_restore --list backup.dump
   sha256sum backup.dump  # Compare with .sha256 file
   ```
4. Restore backup:
   ```bash
   ./backend/scripts/restore_database.sh backup.dump --verify
   # OR manually:
   pg_restore -d $DATABASE_URL -c --if-exists backup.dump
   ```
5. Run migrations (if backup is older than current code):
   ```bash
   python manage.py migrate
   ```
6. Update DATABASE_URL in Render
7. Restart application
8. Verify functionality with smoke tests

**Data Loss:**
- All data since last backup (RPO = backup frequency)
- Weekly backups = up to 7 days data loss
- Daily backups = up to 24 hours data loss

---

### Scenario 3: Bad Migration Recovery

**Recovery Time:** 10-20 minutes

**Steps:**
1. **DO NOT run reverse migration** (may cause further data loss)
2. Restore to point before migration:
   ```bash
   # Option A: Use PITR
   # Render Dashboard → Restore to timestamp before migration
   
   # Option B: Use backup
   pg_restore -d new_database backup.dump
   ```
3. Fix migration code
4. Test migration on development database
5. Apply corrected migration to restored database
6. Update DATABASE_URL if used new database
7. Restart application

**Prevention:**
- Always backup before applying migrations
- Test migrations on staging database first
- Use `--dry-run` for Django migrations when possible
- Review SQL generated by `sqlmigrate` before applying

---

## Recovery Checklist

### Pre-Disaster Preparation

- [ ] Upgraded to paid database plan with backups
- [ ] Verified PITR is enabled and working
- [ ] Set up off-site backup automation
- [ ] Tested restore procedure at least once
- [ ] Documented recovery contacts and credentials
- [ ] Created disaster recovery runbook (this document)
- [ ] Set up monitoring and alerts for database issues
- [ ] Configured backup retention policies

### During Disaster

- [ ] Assess scope of data loss
- [ ] Identify recovery point (timestamp or backup)
- [ ] Notify stakeholders (if user-facing)
- [ ] Create new database or restore in place
- [ ] Verify backup integrity before restoring
- [ ] Execute restore procedure
- [ ] Run post-restore verification
- [ ] Update application configuration if needed
- [ ] Test critical application flows
- [ ] Monitor for errors or issues

### Post-Recovery

- [ ] Document what happened and root cause
- [ ] Calculate actual RPO/RTO achieved
- [ ] Update backup/recovery procedures if needed
- [ ] Review monitoring and alerting
- [ ] Conduct post-mortem with team
- [ ] Implement preventive measures

---

## Cost Estimates

### Year 1 (Small Scale)

**Recommendation:** Render Starter + Weekly S3 backups

| Item | Monthly | Annual |
|------|---------|--------|
| Render Starter | $7 | $84 |
| Backup storage (S3) | $0.02 | $0.24 |
| **Total** | **$7.02** | **$84.24** |

### Year 2 (Growth)

**Recommendation:** Render Standard or AWS RDS

| Provider | Monthly | Annual |
|----------|---------|--------|
| Render Standard | $25 | $300 |
| AWS RDS t4g.micro | $20 | $240 |
| Backup storage | $0.50 | $6 |
| **Total (Render)** | **$25.50** | **$306** |
| **Total (AWS)** | **$20.50** | **$246** |

### Year 3 (Scale with HA)

**Recommendation:** AWS RDS Multi-AZ or Render Pro

| Provider | Monthly | Annual |
|----------|---------|--------|
| Render Pro (HA) | $85 | $1,020 |
| AWS RDS t4g.small Multi-AZ | $75 | $900 |
| Backup storage | $2 | $24 |
| **Total (Render)** | **$87** | **$1,044** |
| **Total (AWS)** | **$77** | **$924** |

---

## Assumptions & Limitations

### Verified

- ✅ Backup scripts work on local Windows database (PostgreSQL 18.6)
- ✅ Backup creates valid pg_dump custom format
- ✅ SHA-256 verification works correctly
- ✅ Restore to temporary database succeeds
- ✅ Data integrity verified post-restore (tables, migrations, records)

### Unverified (Requires Authorization)

- ❓ Backup scripts work with Render production DATABASE_URL
- ❓ Restore scripts work on Linux/Render environment
- ❓ Actual Render PITR functionality
- ❓ Restore time for production database size
- ❓ Network performance for backups from Render to S3

### Assumptions

- Database grows to ~1 GB in first year
- Weekly backups sufficient for RPO requirements
- 7-day PITR meets recovery needs
- Render Starter plan meets performance needs
- No compliance requirements for longer retention

---

## Next Steps

### Immediate (Before Launch)

1. ✅ **Backup scripts created and tested locally**
2. ⏭️ **Upgrade Render database** to Starter plan ($7/month)
3. ⏭️ **Verify PITR** is enabled in Render dashboard
4. ⏭️ **Set up backup alerts** (daily backup success notifications)
5. ⏭️ **Document DATABASE_URL** location and access

### Within First Month

1. ⏭️ **Perform restore drill** with production database
2. ⏭️ **Set up off-site backups** (weekly to S3/GCS)
3. ⏭️ **Create monitoring dashboard** for database metrics
4. ⏭️ **Document recovery procedures** for team

### Ongoing

1. ⏭️ **Monthly restore drill** (verify PITR and backups)
2. ⏭️ **Quarterly review** of backup costs and retention
3. ⏭️ **Annual review** of database plan (upgrade if needed)

---

## References

- [Render PostgreSQL Backups Documentation](https://render.com/docs/postgresql-backups)
- [AWS RDS Automated Backups](https://aws.amazon.com/rds/features/backup/)
- [PostgreSQL Backup & Restore Guide](https://www.postgresql.org/docs/current/backup.html)
- Backup scripts: `backend/scripts/backup_database.{ps1,sh}`
- Internal testing: Task #7 verification results

---

**Summary:** P0-2 implementation complete. Backup scripts created and tested locally. Production deployment requires Render Starter upgrade ($7/month) for automated backups. Off-site backups recommended for disaster recovery.
