# GOFER EXAM - Deployment Guide

## 📋 Table of Contents

1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Environment Setup](#environment-setup)
3. [Database Setup](#database-setup)
4. [Backend Deployment](#backend-deployment)
5. [Frontend Deployment](#frontend-deployment)
6. [Post-Deployment Verification](#post-deployment-verification)
7. [Rollback Procedure](#rollback-procedure)

---

## Pre-Deployment Checklist

### Code Quality & Testing

- [ ] All 191 backend tests pass (`python manage.py test --keepdb`)
- [ ] Frontend builds without errors (`npm run build`)
- [ ] No critical linting errors
- [ ] Git branch is up-to-date with main/production branch
- [ ] All feature branches merged and tested together
- [ ] Code review completed and approved
- [ ] Security audit completed (if applicable)

### Infrastructure & Services

- [ ] Database provisioned and accessible
- [ ] Database backups configured
- [ ] Email provider configured (SMTP or Brevo)
- [ ] Sender email verified with email provider
- [ ] Cloud storage configured (S3/GCS/Azure/R2) - if needed
- [ ] SSL/TLS certificates installed and valid
- [ ] DNS records configured correctly
- [ ] CDN configured (if applicable)
- [ ] Monitoring service set up (Sentry recommended)

### Security

- [ ] Secrets stored in secure secrets manager (not in code)
- [ ] Strong SECRET_KEY generated (32+ characters, high entropy)
- [ ] Database credentials are unique and strong
- [ ] Firewall rules configured (allow only necessary ports)
- [ ] HTTPS enforced (HTTP redirects to HTTPS)
- [ ] CORS and CSRF origins properly configured
- [ ] Rate limiting tested
- [ ] Security headers configured (HSTS, X-Frame-Options, etc.)

---

## Environment Setup

### 1. Backend Environment Configuration

**Location:** `backend/.env.production` (or `.env.staging` for staging)

```bash
# Copy the example file
cd backend
cp .env.production.example .env.production

# Edit with your actual values
# CRITICAL: Never commit .env.production to version control
nano .env.production
```

**Required Environment Variables:**

| Variable | Description | Example |
|----------|-------------|---------|
| `SECRET_KEY` | Django secret key (32+ chars) | Generate: `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"` |
| `ALLOWED_HOSTS` | Comma-separated hostnames | `goferexam.com,api.goferexam.com` |
| `DATABASE_URL` | PostgreSQL connection string | `postgres://user:pass@host:5432/dbname` |
| `GOFER_FRONTEND_URL` | Frontend HTTPS URL | `https://goferexam.com` |
| `CORS_ALLOWED_ORIGINS` | Frontend origins for CORS | `https://goferexam.com` |
| `CSRF_TRUSTED_ORIGINS` | Trusted origins for CSRF | `https://goferexam.com` |
| `EMAIL_BACKEND` | Email backend class | `django.core.mail.backends.smtp.EmailBackend` |
| `GOFER_EMAIL_FROM` | Verified sender email | `noreply@goferexam.com` |
| `STORAGE_BACKEND` | File storage type | `S3`, `GCS`, `AZURE`, `R2`, or `LOCAL` |

**For SMTP Email (example with Gmail):**
```env
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-specific-password
```

**For Brevo Email:**
```env
EMAIL_BACKEND=config.email_backends.brevo.BrevoEmailBackend
BREVO_API_KEY=your-brevo-api-key
```

### 2. Frontend Environment Configuration

**Location:** `frontend/.env.production`

```bash
cd frontend
cp .env.production.example .env.production
nano .env.production
```

**Required Variables:**
```env
NEXT_PUBLIC_API_URL=https://api.goferexam.com
NEXT_PUBLIC_SITE_URL=https://goferexam.com
```

---

## Database Setup

### 1. Create Production Database

```bash
# PostgreSQL example
createdb -U postgres gofer_production

# Or via SQL
psql -U postgres
CREATE DATABASE gofer_production;
CREATE USER gofer_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE gofer_production TO gofer_user;
\q
```

### 2. Run Migrations

```bash
cd backend

# Verify settings are correct
python manage.py check --deploy

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser
```

### 3. Load Initial Data (Optional)

```bash
# Load countries data
python manage.py loaddata fixtures/countries.json

# Or create fixtures from staging
python manage.py dumpdata common.Country --indent 2 > fixtures/countries.json
```

---

## Backend Deployment

### Option A: Deploy to Cloud Platform (Heroku, Render, Railway, etc.)

#### Heroku Example:

```bash
# Install Heroku CLI and login
heroku login

# Create app
heroku create gofer-exam-prod

# Add PostgreSQL
heroku addons:create heroku-postgresql:standard-0

# Set environment variables
heroku config:set SECRET_KEY="your-secret-key"
heroku config:set ALLOWED_HOSTS="goferexam.herokuapp.com"
heroku config:set GOFER_FRONTEND_URL="https://goferexam.com"
# ... set all required variables

# Deploy
git push heroku main

# Run migrations
heroku run python backend/manage.py migrate

# Create superuser
heroku run python backend/manage.py createsuperuser
```

### Option B: Deploy to VPS (Ubuntu/Debian)

#### 1. Install Dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python, PostgreSQL, Nginx
sudo apt install -y python3.12 python3.12-venv python3-pip postgresql nginx

# Install Node.js (for frontend)
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs
```

#### 2. Setup Application

```bash
# Clone repository
cd /var/www
sudo git clone https://github.com/yourusername/gofer-exam.git
cd gofer-exam

# Setup Python virtual environment
cd backend
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Copy and configure environment
cp .env.production.example .env.production
nano .env.production

# Run Django checks
python manage.py check --deploy

# Collect static files
python manage.py collectstatic --noinput

# Run migrations
python manage.py migrate
```

#### 3. Setup Gunicorn Service

```bash
# Create systemd service file
sudo nano /etc/systemd/system/gofer-backend.service
```

```ini
[Unit]
Description=Gofer Exam Backend
After=network.target

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/var/www/gofer-exam/backend
Environment="PATH=/var/www/gofer-exam/backend/venv/bin"
ExecStart=/var/www/gofer-exam/backend/venv/bin/gunicorn \
    --workers 4 \
    --bind 127.0.0.1:8000 \
    --timeout 120 \
    --access-logfile /var/log/gofer/access.log \
    --error-logfile /var/log/gofer/error.log \
    config.wsgi:application

[Install]
WantedBy=multi-user.target
```

```bash
# Create log directory
sudo mkdir -p /var/log/gofer
sudo chown www-data:www-data /var/log/gofer

# Start service
sudo systemctl daemon-reload
sudo systemctl start gofer-backend
sudo systemctl enable gofer-backend
sudo systemctl status gofer-backend
```

#### 4. Configure Nginx

```bash
sudo nano /etc/nginx/sites-available/gofer-exam
```

```nginx
upstream gofer_backend {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name api.goferexam.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.goferexam.com;

    ssl_certificate /etc/letsencrypt/live/api.goferexam.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.goferexam.com/privkey.pem;

    client_max_body_size 10M;

    location /static/ {
        alias /var/www/gofer-exam/backend/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location /media/ {
        alias /var/www/gofer-exam/backend/media/;
        expires 7d;
    }

    location / {
        proxy_pass http://gofer_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }
}
```

```bash
# Enable site and restart Nginx
sudo ln -s /etc/nginx/sites-available/gofer-exam /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## Frontend Deployment

### Option A: Deploy to Vercel (Recommended for Next.js)

```bash
cd frontend

# Install Vercel CLI
npm install -g vercel

# Login
vercel login

# Deploy to production
vercel --prod

# Set environment variables in Vercel dashboard
# https://vercel.com/your-username/gofer-exam/settings/environment-variables
```

### Option B: Deploy to VPS with PM2

```bash
cd /var/www/gofer-exam/frontend

# Install dependencies
npm ci --production

# Build
npm run build

# Install PM2
sudo npm install -g pm2

# Start application
pm2 start npm --name "gofer-frontend" -- start

# Save PM2 configuration
pm2 save

# Setup PM2 to start on boot
pm2 startup
```

**Nginx configuration for frontend:**

```nginx
server {
    listen 80;
    server_name goferexam.com www.goferexam.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name goferexam.com www.goferexam.com;

    ssl_certificate /etc/letsencrypt/live/goferexam.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/goferexam.com/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

---

## Post-Deployment Verification

### 1. Backend Health Checks

```bash
# Health check endpoint
curl https://api.goferexam.com/api/v1/health/

# Expected response:
# {"status": "healthy", "database": "connected", "cache": "connected"}

# Django system check
python manage.py check --deploy

# Run a quick test suite
python manage.py test apps.accounts.tests.HealthCheckTests --keepdb
```

### 2. Frontend Health Checks

```bash
# Visit homepage
curl https://goferexam.com/

# Check API connectivity
# Open browser console and verify no CORS errors
```

### 3. Critical User Flows

Test these flows manually in production:

- [ ] **Registration Flow**
  - Visit registration page
  - Fill in form and submit
  - Check email received (verification email)
  - Click verification link
  - Confirm account is verified

- [ ] **Login Flow**
  - Visit login page
  - Enter credentials
  - Verify successful login
  - Check authentication cookies set
  - Verify `/api/v1/auth/me/` returns user data

- [ ] **Password Reset Flow**
  - Visit forgot password page
  - Submit email
  - Check password reset email received
  - Click reset link
  - Set new password
  - Login with new password

- [ ] **Scholarship Browsing**
  - Visit scholarships page
  - Verify scholarships load
  - Test search functionality
  - Test filters (level, type, nationality)
  - Click on a scholarship
  - Verify detail page loads

- [ ] **Application Submission** (if user is logged in)
  - Navigate to scholarship
  - Click "Apply"
  - Fill application form
  - Upload documents (test file upload)
  - Submit application
  - Verify success message

### 4. Monitoring Setup Verification

```bash
# Check Sentry is receiving events (if configured)
# Trigger a test error:
python manage.py shell
>>> from django.core.exceptions import ImproperlyConfigured
>>> raise ImproperlyConfigured("Test Sentry integration")

# Check Sentry dashboard for the error
```

### 5. Performance Checks

```bash
# Check response times
curl -w "\nTime: %{time_total}s\n" https://api.goferexam.com/api/v1/scholarships/

# Load test (optional, use with caution)
# ab -n 100 -c 10 https://api.goferexam.com/api/v1/health/
```

---

## Rollback Procedure

### If Deployment Fails

#### Backend Rollback (Heroku/Platform):

```bash
# List recent releases
heroku releases

# Rollback to previous version
heroku rollback v123
```

#### Backend Rollback (VPS):

```bash
# Stop current version
sudo systemctl stop gofer-backend

# Checkout previous commit
cd /var/www/gofer-exam
git log --oneline  # Find commit hash
git checkout <previous-commit-hash>

# Rollback migrations (if necessary)
cd backend
source venv/bin/activate
python manage.py migrate <app_name> <previous_migration_number>

# Restart service
sudo systemctl start gofer-backend
sudo systemctl status gofer-backend
```

#### Frontend Rollback (Vercel):

```bash
# In Vercel dashboard:
# Deployments → Find previous deployment → Promote to Production
```

#### Frontend Rollback (VPS):

```bash
cd /var/www/gofer-exam/frontend
git checkout <previous-commit-hash>
npm ci
npm run build
pm2 restart gofer-frontend
```

### Emergency Rollback Checklist

- [ ] Stop incoming traffic (maintenance page or load balancer)
- [ ] Rollback backend code
- [ ] Rollback database migrations (if necessary)
- [ ] Rollback frontend code
- [ ] Verify health checks pass
- [ ] Test critical user flows
- [ ] Restore traffic
- [ ] Investigate root cause
- [ ] Document incident

---

## Troubleshooting

### Common Issues

**Issue: 502 Bad Gateway**
- Check backend service is running: `sudo systemctl status gofer-backend`
- Check logs: `sudo journalctl -u gofer-backend -n 50`
- Verify Gunicorn is binding to correct port

**Issue: CORS Errors**
- Verify `CORS_ALLOWED_ORIGINS` matches frontend URL
- Check `CSRF_TRUSTED_ORIGINS` is set correctly
- Ensure frontend URL has no trailing slash

**Issue: Email Not Sending**
- Check `EMAIL_BACKEND` is not console/dummy
- Verify email credentials are correct
- Check firewall allows outbound SMTP (port 587/465)
- Test email manually: `python manage.py shell`
  ```python
  from django.core.mail import send_mail
  send_mail('Test', 'Test message', 'from@example.com', ['to@example.com'])
  ```

**Issue: Static Files Not Loading**
- Run `python manage.py collectstatic`
- Check Nginx configuration for `/static/` location
- Verify file permissions: `sudo chown -R www-data:www-data /var/www/gofer-exam/backend/staticfiles/`

**Issue: Database Connection Errors**
- Verify `DATABASE_URL` is correct
- Check PostgreSQL is running: `sudo systemctl status postgresql`
- Test connection: `psql $DATABASE_URL`
- Verify firewall allows database port (5432)

---

## Security Best Practices

1. **Keep secrets secure**
   - Never commit `.env` files
   - Use environment variables or secrets manager
   - Rotate credentials regularly

2. **Monitor logs**
   - Set up log aggregation (CloudWatch, Papertrail, Logtail)
   - Monitor error rates
   - Set up alerts for critical errors

3. **Regular updates**
   - Keep dependencies updated
   - Subscribe to security advisories
   - Apply security patches promptly

4. **Backup strategy**
   - Daily automated database backups
   - Test restoration procedure
   - Store backups in multiple locations

5. **Access control**
   - Use principle of least privilege
   - Enable two-factor authentication
   - Audit access logs regularly

---

## Support & Contact

For deployment support or questions:
- Documentation: `/docs/`
- Issue Tracker: GitHub Issues
- Team Contact: [your-contact-info]

---

**Document Version:** 1.0  
**Last Updated:** 2026-11-02  
**Maintainer:** Gofer Exam Development Team
