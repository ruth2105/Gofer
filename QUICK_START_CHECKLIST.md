# Gofer Exam - Quick Start Checklist

**Purpose:** Action-oriented checklist for getting to production  
**Date:** November 2, 2026  

---

## Pre-Launch Decision (THIS WEEK)

### Day 1: Review & Decide
- [ ] Read Executive Summary
- [ ] Review complete audit findings
- [ ] Discuss strategic options with team
- [ ] Choose path forward: Option 1, 2, 3, or 4
- [ ] Approve budget
- [ ] Identify team members/resources

---

## Phase 1: MVP Configuration (Week 1-2)

### Email Setup (2 hours)
- [ ] Sign up for AWS SES or SendGrid account
- [ ] Verify domain (add DNS records)
- [ ] Get SMTP credentials (access key + secret)
- [ ] Update `backend/config/settings/production.py`:
  ```python
  EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
  EMAIL_HOST = 'email-smtp.us-east-1.amazonaws.com'
  EMAIL_PORT = 587
  EMAIL_USE_TLS = True
  EMAIL_HOST_USER = os.environ.get('AWS_SES_ACCESS_KEY')
  EMAIL_HOST_PASSWORD = os.environ.get('AWS_SES_SECRET_KEY')
  DEFAULT_FROM_EMAIL = 'noreply@goferexam.com'
  ```
- [ ] Set environment variables in Render
- [ ] Test: Register new user → Receive real email
- [ ] Test: Password reset → Receive real email
- [ ] Verify emails not in spam folder

### Storage Setup (2 hours)
- [ ] Create AWS S3 bucket or Google Cloud Storage bucket
- [ ] Set bucket to private (not public)
- [ ] Get access credentials (access key + secret)
- [ ] Update `backend/config/settings/production.py`:
  ```python
  DEFAULT_FILE_STORAGE = 'config.storage_backends.S3MediaStorage'
  AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
  AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
  AWS_STORAGE_BUCKET_NAME = 'gofer-exam-media'
  AWS_S3_REGION_NAME = 'us-east-1'
  AWS_S3_FILE_OVERWRITE = False
  AWS_DEFAULT_ACL = None
  ```
- [ ] Set environment variables in Render
- [ ] Test: Upload document → Restart server → Download document (should work)
- [ ] Verify file persists after restart

### Backup Automation (3 hours)
- [ ] Update `backend/scripts/backup_database.sh` with S3 upload
- [ ] Add to `render.yaml`:
  ```yaml
  - type: cron
    name: database-backup
    env: docker
    schedule: "0 2 * * *"  # Daily at 2 AM UTC
    dockerCommand: ./scripts/backup_database.sh
  ```
- [ ] Or set up cron job on server (if using VPS)
- [ ] Test backup manually: `./scripts/backup_database.sh`
- [ ] Verify backup appears in S3
- [ ] Test restore: `./scripts/restore_database.sh backup.sql.gz`
- [ ] Set up backup monitoring/alerting (optional)

### Staging Deployment (6 hours)
- [ ] Sign up for Render.com (backend hosting)
- [ ] Create new Web Service (Docker)
- [ ] Connect GitHub repository
- [ ] Set environment variables:
  ```
  DJANGO_SETTINGS_MODULE=config.settings.production
  SECRET_KEY=[generate new secret]
  DATABASE_URL=[provided by Render]
  AWS_ACCESS_KEY_ID=[from AWS]
  AWS_SECRET_ACCESS_KEY=[from AWS]
  AWS_STORAGE_BUCKET_NAME=gofer-exam-media
  AWS_SES_ACCESS_KEY=[from AWS SES]
  AWS_SES_SECRET_KEY=[from AWS SES]
  ALLOWED_HOSTS=gofer-exam-backend.onrender.com,staging.goferexam.com
  CORS_ALLOWED_ORIGINS=https://staging.goferexam.com
  ```
- [ ] Deploy backend
- [ ] Run migrations (Render console): `python manage.py migrate`
- [ ] Create superuser: `python manage.py createsuperuser`
- [ ] Test health endpoint: `https://[your-app].onrender.com/api/v1/health/`
- [ ] Sign up for Vercel (frontend hosting)
- [ ] Import GitHub repository
- [ ] Set environment variable:
  ```
  API_PROXY_TARGET=https://[your-app].onrender.com
  ```
- [ ] Deploy frontend
- [ ] Test: Visit staging site, register, login, browse scholarships

### Testing (12 hours)
- [ ] Populate test data: 50+ scholarships, 10+ opportunities
- [ ] Run critical tests from GOFER_END_TO_END_TEST_PLAN.md
- [ ] Document all failures in bug tracker
- [ ] Fix critical bugs (P0)
- [ ] Re-test after fixes
- [ ] Verify 100% critical tests passing

---

## Phase 2: Production Launch (Week 3)

### Production Deployment (6 hours)
- [ ] Create production database (Render Postgres Pro - $7/month)
- [ ] Create production S3 bucket (separate from staging)
- [ ] Clone Render service for production (new environment)
- [ ] Update environment variables (production values)
- [ ] Set up custom domain in Vercel
- [ ] Configure DNS (CNAME records)
- [ ] Enable HTTPS (automatic in Vercel/Render)
- [ ] Test production deployment

### Content Population (8 hours)
- [ ] Import real scholarship data (50-100 scholarships)
- [ ] Add study destinations (10-20 countries)
- [ ] Add universities (20-50)
- [ ] Add job/internship opportunities (20-50)
- [ ] Add consulting services (5-10)
- [ ] Create consultant profiles
- [ ] Add FAQ content
- [ ] Write about/contact page content

### Launch Preparation (6 hours)
- [ ] Set up Google Analytics
- [ ] Add analytics tracking code to frontend
- [ ] Create meta tags for SEO (title, description)
- [ ] Generate sitemap.xml
- [ ] Create robots.txt
- [ ] Write terms of service
- [ ] Write privacy policy
- [ ] Set up support email (support@goferexam.com)
- [ ] Create launch announcement (email, social media)
- [ ] Prepare user documentation (FAQs, how-to guides)

### Final Checks
- [ ] Smoke test all critical features
- [ ] Test on mobile devices
- [ ] Test in multiple browsers
- [ ] Verify emails being sent
- [ ] Verify files persisting
- [ ] Check error monitoring (Sentry)
- [ ] Verify backups running
- [ ] Test support email delivery

### Go-Live
- [ ] Final team review
- [ ] Get stakeholder approval
- [ ] Make DNS changes (switch to production)
- [ ] Announce launch
- [ ] Monitor for issues (first 24 hours critical)

---

## Phase 3: Post-Launch (Week 4+)

### Week 1 Post-Launch
- [ ] Monitor error rates daily
- [ ] Check user feedback
- [ ] Fix any critical bugs immediately
- [ ] Monitor server performance
- [ ] Check database connection pool usage
- [ ] Verify backups running successfully

### Week 2-4
- [ ] Analyze Google Analytics data
- [ ] Identify user friction points
- [ ] Collect user feedback (surveys, emails)
- [ ] Prioritize quick wins
- [ ] Plan Phase 4 (if Option 2/3/4)

---

## Phase 4: Monetization (IF CHOSEN)

### Stripe Setup (2 hours)
- [ ] Sign up for Stripe account
- [ ] Complete account verification
- [ ] Get API keys (test + live)
- [ ] Install Stripe libraries
- [ ] Review Stripe documentation

### Payment Models (8 hours)
- [ ] Create Django app: `payments`
- [ ] Create models: Payment, Transaction, Invoice
- [ ] Create migrations
- [ ] Create serializers
- [ ] Write tests

### Checkout Flow (20 hours)
- [ ] Backend: Create Checkout Session endpoint
- [ ] Backend: Webhook handler for payment success
- [ ] Frontend: Service pricing page
- [ ] Frontend: Checkout component (Stripe Elements)
- [ ] Frontend: Payment success page
- [ ] Frontend: Payment failure page
- [ ] Test with Stripe test cards

### Invoice Generation (10 hours)
- [ ] Install PDF library (ReportLab or WeasyPrint)
- [ ] Create invoice template
- [ ] Generate invoice on payment success
- [ ] Email invoice to customer
- [ ] Invoice download endpoint

### Testing (10 hours)
- [ ] Test all payment flows
- [ ] Test webhook handlers
- [ ] Test refund process
- [ ] Security audit
- [ ] Load testing

---

## Phase 5: Exam Platform (IF CHOSEN)

### Question Bank (60 hours)
- [ ] Design question models
- [ ] Create admin interface for questions
- [ ] Import 100+ IELTS questions
- [ ] Categorize by section
- [ ] Add difficulty tags
- [ ] Review/approve questions

### Test Engine (70 hours)
- [ ] Design test models
- [ ] Build test generation algorithm
- [ ] Create test-taking interface
- [ ] Implement timer
- [ ] Answer submission
- [ ] Test review page
- [ ] Progress saving

### Scoring (40 hours)
- [ ] Automated scoring for MCQ
- [ ] Band score calculation
- [ ] Manual scoring interface
- [ ] Score reports
- [ ] Analytics

### Progress Tracking (40 hours)
- [ ] Test history
- [ ] Performance dashboard
- [ ] Weak areas identification
- [ ] Study recommendations
- [ ] Charts/graphs

### Testing (70 hours)
- [ ] Create 10 full practice tests
- [ ] Comprehensive testing
- [ ] Bug fixes
- [ ] Performance optimization
- [ ] User acceptance testing

---

## Quick Reference: Commands

### Local Development
```bash
# Backend
cd backend
python manage.py runserver

# Frontend
cd gofer-exam
npm run dev

# Run tests
cd backend
python manage.py test

# Create superuser
python manage.py createsuperuser

# Make migrations
python manage.py makemigrations
python manage.py migrate

# Populate test data
python manage.py create_test_data
```

### Deployment
```bash
# Backend (Render auto-deploys on git push)
git push origin main

# Frontend (Vercel auto-deploys)
git push origin main

# Manual deploy (if needed)
cd gofer-exam
npm run build
vercel --prod
```

### Database
```bash
# Backup
./backend/scripts/backup_database.sh

# Restore
./backend/scripts/restore_database.sh backup.sql.gz

# Connect to production DB (Render)
# Get connection string from Render dashboard
psql [DATABASE_URL]
```

---

## Emergency Contacts

**If things break in production:**

1. **Check health endpoint:** `https://api.goferexam.com/api/v1/health/`
2. **Check Render logs:** Render Dashboard → Your Service → Logs
3. **Check Vercel logs:** Vercel Dashboard → Your Project → Functions
4. **Check Sentry:** (if configured) for error details
5. **Rollback:** Render → Deployments → Previous deployment → Redeploy

**Common Issues:**

**Issue: Site down**
- Check: Render service status
- Check: Database connection (health endpoint)
- Solution: Restart service or restore from backup

**Issue: Emails not sending**
- Check: AWS SES quota not exceeded
- Check: Environment variables set correctly
- Check: Logs for error messages
- Solution: Verify AWS SES configuration

**Issue: File uploads failing**
- Check: S3 credentials valid
- Check: S3 bucket permissions
- Check: File size within limits
- Solution: Verify AWS S3 configuration

**Issue: Performance slow**
- Check: Database connection pool
- Check: API response times
- Check: Server CPU/memory usage
- Solution: Scale up Render service or optimize queries

---

## Resource Links

**Official Docs:**
- Django: https://docs.djangoproject.com/
- Next.js: https://nextjs.org/docs
- Render: https://render.com/docs
- Vercel: https://vercel.com/docs
- AWS SES: https://docs.aws.amazon.com/ses/
- AWS S3: https://docs.aws.amazon.com/s3/
- Stripe: https://stripe.com/docs

**Project Docs:**
- Complete Audit: `GOFER_COMPLETE_FUNCTIONAL_AUDIT.md`
- Missing Features: `GOFER_MISSING_FEATURES.md`
- Test Plan: `GOFER_END_TO_END_TEST_PLAN.md`
- Roadmap: `GOFER_DEVELOPMENT_ROADMAP.md`

**Support:**
- Render Support: support@render.com
- Vercel Support: https://vercel.com/support
- AWS Support: https://console.aws.amazon.com/support/
- Stripe Support: https://support.stripe.com/

---

## Success Checklist

### MVP Launch Success ✅
- [ ] Site accessible at production URL
- [ ] Users can register and login
- [ ] Real emails being sent (not console)
- [ ] Files persist after server restart
- [ ] Backups running daily
- [ ] No critical bugs
- [ ] 100+ scholarships populated
- [ ] Analytics tracking active
- [ ] Support email working

### Monetization Success 💰
- [ ] Can accept test payments (Stripe test mode)
- [ ] Can accept real payments (Stripe live mode)
- [ ] Invoices generated automatically
- [ ] Payment notifications working
- [ ] Refund process tested
- [ ] First paying customer! 🎉

### Exam Platform Success 🎯
- [ ] 500+ practice questions live
- [ ] 10+ full practice tests available
- [ ] Automated scoring working
- [ ] Progress tracking functional
- [ ] First completed practice test!
- [ ] Users reporting improved scores 📈

---

**Print this checklist and check off items as you complete them!**

**Remember:** Don't try to do everything at once. Focus on one phase at a time.

**Good luck! 🚀**
