# P0-1: Storage Configuration & Deployment Guide

**Date:** 2026-11-02  
**Status:** Implementation Complete - Deployment Pending  
**Purpose:** Guide for configuring durable file storage for Gofer Exam production deployment

---

## Overview

The Gofer Exam platform now supports configurable durable storage backends for student document uploads (transcripts, passports, certificates, photos). This implementation eliminates the production blocker of ephemeral local filesystem storage.

**What Changed:**
- ✅ Added `django-storages` with S3, GCS, and Azure support
- ✅ Created storage backend abstraction layer
- ✅ Implemented production validation
- ✅ Added comprehensive tests
- ⚠️ **Requires dependency installation** (`pip install -r requirements/base.txt`)
- ⚠️ **Requires storage provider setup** (before production deployment)

---

## Quick Start

### Development (Local Storage)

**Default configuration** - no changes needed:

```bash
# .env (development)
STORAGE_BACKEND=LOCAL
```

Files are stored in `backend/media/` directory (ephemeral, suitable for dev only).

### Production (AWS S3)

**Recommended configuration:**

```bash
# Render/production environment variables
STORAGE_BACKEND=S3
AWS_ACCESS_KEY_ID=<your-access-key>
AWS_SECRET_ACCESS_KEY=<your-secret-key>
AWS_STORAGE_BUCKET_NAME=gofer-exam-documents
AWS_S3_REGION_NAME=us-east-1
```

---

## Installation Steps

### 1. Install Dependencies

**Local development:**

```bash
cd backend
pip install -r requirements/base.txt
```

**Render deployment:**
- Dependencies automatically installed from `requirements/production.txt`
- Includes: `django-storages[s3,google,azure]==1.14.4`, `boto3==1.34.162`, `google-cloud-storage==2.18.2`, `azure-storage-blob==12.23.1`

### 2. Verify Installation

```bash
# Test that storage backends can be imported
python manage.py shell
>>> from config.storage_backends import get_storage_backend
>>> storage = get_storage_backend()
>>> print(type(storage))
<class 'config.storage_backends.LocalMediaStorage'>
```

---

## Provider Setup Guides

### AWS S3 (Recommended)

#### Step 1: Create S3 Bucket

```bash
# Using AWS CLI
aws s3 mb s3://gofer-exam-documents --region us-east-1
```

**Or via AWS Console:**
1. Navigate to S3 service
2. Click "Create bucket"
3. Bucket name: `gofer-exam-documents`
4. Region: `us-east-1` (or closest to your users)
5. **Block all public access**: ✅ Enabled (keep private)
6. **Bucket Versioning**: Optional (recommended for recovery)
7. **Server-side encryption**: ✅ Enable (S3-managed keys)

#### Step 2: Configure CORS (for frontend uploads)

**CORS Configuration** (if using direct frontend uploads):

```json
[
  {
    "AllowedHeaders": ["*"],
    "AllowedMethods": ["GET", "PUT", "POST", "DELETE"],
    "AllowedOrigins": [
      "https://your-frontend-domain.com",
      "http://localhost:3000"
    ],
    "ExposeHeaders": ["ETag"],
    "MaxAgeSeconds": 3000
  }
]
```

#### Step 3: Create IAM User

**IAM Policy** (minimum permissions):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:DeleteObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::gofer-exam-documents",
        "arn:aws:s3:::gofer-exam-documents/*"
      ]
    }
  ]
}
```

**Create IAM user:**
1. AWS Console → IAM → Users → Create user
2. Username: `gofer-exam-storage`
3. Access type: Programmatic access
4. Attach policy: Create inline policy (use JSON above)
5. **Save credentials** (access key ID and secret access key)

#### Step 4: Configure Environment Variables

**Render Dashboard:**

```
STORAGE_BACKEND=S3
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
AWS_STORAGE_BUCKET_NAME=gofer-exam-documents
AWS_S3_REGION_NAME=us-east-1
```

**Optional settings:**

```
AWS_S3_CUSTOM_DOMAIN=cdn.example.com  # For CloudFront CDN
AWS_QUERYSTRING_AUTH=True  # Generate signed URLs (default)
AWS_QUERYSTRING_EXPIRE=3600  # Signed URL expiry (1 hour)
```

#### Step 5: Test Upload

```bash
# Django shell test
python manage.py shell

from apps.documents.models import Document
from apps.accounts.models import User
from django.core.files.uploadedfile import SimpleUploadedFile

user = User.objects.get(email='test@example.com')
file = SimpleUploadedFile('test.pdf', b'test content')

doc = Document.objects.create(
    user=user,
    document_type='PASSPORT',
    title='Test Document',
    file=file
)

print(f"File URL: {doc.file.url}")
print(f"File exists: {doc.file.storage.exists(doc.file.name)}")

# Cleanup
doc.delete()
```

---

### Google Cloud Storage

#### Step 1: Create GCS Bucket

```bash
# Using gcloud CLI
gsutil mb -c STANDARD -l us-east1 gs://gofer-exam-documents/
```

**Or via GCP Console:**
1. Navigate to Cloud Storage
2. Create bucket
3. Name: `gofer-exam-documents`
4. Location type: Region → `us-east1`
5. Storage class: Standard
6. Access control: Uniform
7. Encryption: Google-managed

#### Step 2: Create Service Account

```bash
# Create service account
gcloud iam service-accounts create gofer-exam-storage \
    --display-name="Gofer Exam Storage"

# Grant storage permissions
gsutil iam ch \
    serviceAccount:gofer-exam-storage@PROJECT_ID.iam.gserviceaccount.com:objectAdmin \
    gs://gofer-exam-documents

# Generate key file
gcloud iam service-accounts keys create gcs-key.json \
    --iam-account=gofer-exam-storage@PROJECT_ID.iam.gserviceaccount.com
```

#### Step 3: Configure Environment Variables

**Render Dashboard:**

```
STORAGE_BACKEND=GCS
GS_BUCKET_NAME=gofer-exam-documents
GS_PROJECT_ID=your-gcp-project-id
GS_CREDENTIALS=/path/to/gcs-key.json
```

**Note:** Store `gcs-key.json` securely or use Render's file upload feature for secrets.

---

### Azure Blob Storage

#### Step 1: Create Storage Account

```bash
# Using Azure CLI
az storage account create \
    --name goferexamstorage \
    --resource-group gofer-exam-rg \
    --location eastus \
    --sku Standard_LRS
```

#### Step 2: Create Container

```bash
az storage container create \
    --name documents \
    --account-name goferexamstorage
```

#### Step 3: Get Connection String

```bash
az storage account show-connection-string \
    --name goferexamstorage \
    --resource-group gofer-exam-rg
```

#### Step 4: Configure Environment Variables

**Render Dashboard:**

```
STORAGE_BACKEND=AZURE
AZURE_ACCOUNT_NAME=goferexamstorage
AZURE_CONTAINER=documents
AZURE_ACCOUNT_KEY=<account-key>
# OR
AZURE_CONNECTION_STRING=<connection-string>
```

---

### Cloudflare R2 (S3-Compatible)

#### Step 1: Create R2 Bucket

1. Cloudflare Dashboard → R2
2. Create bucket: `gofer-exam-documents`
3. Note the account ID from URL

#### Step 2: Create API Token

1. R2 → Manage R2 API Tokens
2. Create API Token
3. Permissions: Object Read & Write
4. **Save credentials** (Access Key ID and Secret Access Key)

#### Step 3: Configure Environment Variables

**Render Dashboard:**

```
STORAGE_BACKEND=R2
AWS_ACCESS_KEY_ID=<r2-access-key>
AWS_SECRET_ACCESS_KEY=<r2-secret-key>
AWS_STORAGE_BUCKET_NAME=gofer-exam-documents
AWS_S3_ENDPOINT_URL=https://<account-id>.r2.cloudflarestorage.com
AWS_S3_REGION_NAME=auto
```

**Advantage:** Zero egress fees (no cost for downloads).

---

## Environment Variable Reference

### Required Variables

| Variable | Backend | Description | Example |
|----------|---------|-------------|---------|
| `STORAGE_BACKEND` | All | Storage provider selection | `LOCAL`, `S3`, `GCS`, `AZURE`, `R2` |

### AWS S3 / Cloudflare R2

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `AWS_ACCESS_KEY_ID` | Yes | - | IAM user access key |
| `AWS_SECRET_ACCESS_KEY` | Yes | - | IAM user secret key |
| `AWS_STORAGE_BUCKET_NAME` | Yes | - | S3 bucket name |
| `AWS_S3_REGION_NAME` | No | `us-east-1` | AWS region |
| `AWS_S3_CUSTOM_DOMAIN` | No | - | CloudFront CDN domain |
| `AWS_S3_ENDPOINT_URL` | R2 only | - | Cloudflare R2 endpoint |
| `AWS_QUERYSTRING_AUTH` | No | `True` | Generate signed URLs |
| `AWS_QUERYSTRING_EXPIRE` | No | `3600` | Signed URL expiry (seconds) |

### Google Cloud Storage

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GS_BUCKET_NAME` | Yes | - | GCS bucket name |
| `GS_PROJECT_ID` | No | - | GCP project ID |
| `GS_CREDENTIALS` | Yes | - | Path to service account JSON |
| `GS_QUERYSTRING_AUTH` | No | `True` | Generate signed URLs |
| `GS_EXPIRATION` | No | `3600` | Signed URL expiry (seconds) |

### Azure Blob Storage

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `AZURE_ACCOUNT_NAME` | Yes | - | Storage account name |
| `AZURE_CONTAINER` | Yes | - | Container name |
| `AZURE_ACCOUNT_KEY` | Yes* | - | Storage account key |
| `AZURE_CONNECTION_STRING` | Yes* | - | Full connection string |
| `AZURE_CUSTOM_DOMAIN` | No | - | Azure CDN domain |

*Either `AZURE_ACCOUNT_KEY` or `AZURE_CONNECTION_STRING` required.

---

## Deployment Checklist

### Pre-Deployment

- [ ] **Install dependencies**: `pip install -r requirements/production.txt`
- [ ] **Choose storage provider**: AWS S3 (recommended)
- [ ] **Create storage bucket/container** with private access
- [ ] **Create IAM user/service account** with minimum permissions
- [ ] **Generate access credentials** (keys, service account JSON)
- [ ] **Configure CORS** (if needed for direct frontend uploads)
- [ ] **Enable encryption** at rest (provider-managed keys)
- [ ] **Set up lifecycle rules** (optional - auto-delete expired docs)

### Render Configuration

- [ ] Add environment variables in Render dashboard
- [ ] Set `STORAGE_BACKEND=S3` (or GCS/AZURE/R2)
- [ ] Add provider-specific credentials
- [ ] **Verify variables** in Render → Service → Environment
- [ ] **Trigger deployment** to apply changes

### Post-Deployment Verification

- [ ] **Check startup logs** for storage validation errors
- [ ] **Test file upload** via admin interface or API
- [ ] **Verify file appears** in cloud storage bucket
- [ ] **Test file download** via document API
- [ ] **Test file deletion** (verify removed from bucket)
- [ ] **Monitor storage costs** in provider dashboard

---

## Testing

### Run Storage Tests

**Unit tests** (with mocked backends):

```bash
python -m unittest config.tests.test_storage_config -v
```

**Django integration tests** (requires installed packages):

```bash
python manage.py test config.tests.test_storage_backends
```

**Full test suite** (verify no regressions):

```bash
python manage.py test --keepdb
```

### Manual Testing

```python
# Django shell
python manage.py shell

# 1. Check current storage backend
from django.conf import settings
print(f"Storage backend: {settings.STORAGE_BACKEND}")
print(f"DEFAULT_FILE_STORAGE: {settings.DEFAULT_FILE_STORAGE}")

# 2. Get storage instance
from config.storage_backends import get_storage_backend
storage = get_storage_backend()
print(f"Storage class: {type(storage)}")

# 3. Test file operations
from django.core.files.base import ContentFile
name = storage.save('test/sample.txt', ContentFile(b'Hello World'))
print(f"Saved: {name}")
print(f"Exists: {storage.exists(name)}")
print(f"URL: {storage.url(name)}")

# 4. Cleanup
storage.delete(name)
```

---

## Cost Estimates

### Storage Costs (First Year)

**Assumptions:**
- 100 students
- 5 documents per student (avg)
- 2 MB per document
- Total: 1 GB storage
- 10 GB egress/month (downloads)

| Provider | Storage | Operations | Egress | **Monthly** | **Annual** |
|----------|---------|------------|--------|-------------|------------|
| **AWS S3** | $0.02 | $0.01 | $0.90 | $0.93 | $11.16 |
| **GCS** | $0.02 | $0.01 | $1.20 | $1.23 | $14.76 |
| **Azure** | $0.02 | $0.01 | $0.87 | $0.90 | $10.80 |
| **Cloudflare R2** | $0.02 | $0.01 | $0.00 | $0.03 | $0.36 |

**Recommendation:** All providers cost <$2/month for early-stage usage. AWS S3 recommended for ecosystem maturity despite slightly higher cost than R2.

### Scaling Costs (1,000 students)

**Assumptions:** 10 GB storage, 100 GB egress/month

| Provider | Monthly Cost |
|----------|--------------|
| AWS S3 | $9.23 |
| GCS | $12.23 |
| Azure | $8.90 |
| Cloudflare R2 | $0.15 |

**Note:** R2's zero egress fees become very attractive at scale.

---

## Security Best Practices

### Access Control

1. **Private Buckets Only**
   - Never make buckets publicly readable
   - Use signed URLs for authenticated downloads

2. **Minimum IAM Permissions**
   - Grant only `PutObject`, `GetObject`, `DeleteObject`, `ListBucket`
   - No `*` wildcards in IAM policies

3. **Credential Management**
   - Store credentials in environment variables, never in code
   - Rotate credentials every 90 days
   - Use separate credentials for dev/staging/prod

4. **Encryption**
   - Enable server-side encryption (provider-managed keys)
   - Consider client-side encryption for sensitive documents

### Application Security

1. **File Validation**
   - Already implemented: 10MB size limit
   - Already implemented: Extension whitelist (pdf, doc, docx, jpg, jpeg, png)
   - Consider: Virus scanning integration (ClamAV, VirusTotal API)

2. **Access Control**
   - Already implemented: Permission checks in DocumentViewSet
   - Students can only access their own documents
   - Consultants can access assigned students' documents
   - Admins can access all documents

3. **Signed URLs**
   - Default: 1-hour expiry for download links
   - Prevents unauthorized sharing of permanent URLs

---

## Troubleshooting

### Error: "ModuleNotFoundError: No module named 'storages'"

**Cause:** Dependencies not installed.

**Fix:**
```bash
pip install -r requirements/base.txt
```

### Error: "AWS_STORAGE_BUCKET_NAME must be set when using S3 storage"

**Cause:** Missing environment variable.

**Fix:** Add to Render environment variables:
```
STORAGE_BACKEND=S3
AWS_STORAGE_BUCKET_NAME=your-bucket-name
```

### Error: "The AWS Access Key Id you provided does not exist"

**Causes:**
- Incorrect AWS_ACCESS_KEY_ID
- IAM user doesn't have S3 permissions
- Wrong AWS region

**Fix:**
1. Verify credentials in AWS IAM console
2. Check IAM policy grants S3 access
3. Verify bucket exists in specified region

### Error: "Access Denied" when uploading

**Causes:**
- IAM policy missing `s3:PutObject` permission
- Bucket policy blocking uploads

**Fix:**
1. Add `s3:PutObject` to IAM policy
2. Check bucket policy doesn't deny uploads

### Warning: "Using LOCAL storage in production"

**Cause:** `STORAGE_BACKEND=LOCAL` in production settings.

**Impact:** Files will be lost on deployment/restart.

**Fix:** Configure durable storage (S3/GCS/Azure/R2).

---

## Migration Guide

### From Local to Cloud Storage

**Scenario:** You have existing files in `backend/media/` that need to be migrated to S3.

**Steps:**

1. **Backup existing files**
   ```bash
   tar -czf media-backup-$(date +%Y%m%d).tar.gz backend/media/
   ```

2. **Upload to S3** (using AWS CLI)
   ```bash
   aws s3 sync backend/media/ s3://gofer-exam-documents/media/ \
       --exclude "*.pyc" \
       --exclude "__pycache__/*"
   ```

3. **Update environment variables**
   ```
   STORAGE_BACKEND=S3
   ```

4. **Deploy application**

5. **Verify migration**
   - Test file downloads through application
   - Check database `file` field paths match S3 structure

6. **Clean up local files** (after verification)
   ```bash
   rm -rf backend/media/*
   ```

**Note:** No migration needed for Gofer Exam production - no existing production files.

---

## Rollback Plan

If storage migration causes issues:

1. **Stop accepting uploads** (maintenance mode)

2. **Revert environment variables**
   ```
   STORAGE_BACKEND=LOCAL
   ```

3. **Redeploy** to previous version

4. **Restore local files** (if migrated)
   ```bash
   tar -xzf media-backup-YYYYMMDD.tar.gz
   ```

5. **Investigate issue** in staging environment

---

## Support & Resources

### Documentation

- [django-storages Documentation](https://django-storages.readthedocs.io/)
- [AWS S3 Documentation](https://docs.aws.amazon.com/s3/)
- [Google Cloud Storage Documentation](https://cloud.google.com/storage/docs)
- [Azure Blob Storage Documentation](https://docs.microsoft.com/azure/storage/blobs/)
- [Cloudflare R2 Documentation](https://developers.cloudflare.com/r2/)

### Internal Documentation

- [P0_1_STORAGE_PROVIDER_COMPARISON.md](./P0_1_STORAGE_PROVIDER_COMPARISON.md) - Provider evaluation
- [config/storage_backends.py](./backend/config/storage_backends.py) - Implementation
- [config/tests/test_storage_backends.py](./backend/config/tests/test_storage_backends.py) - Tests

### Getting Help

1. Check application logs in Render dashboard
2. Test storage backend in Django shell
3. Verify environment variables are set correctly
4. Review provider-specific documentation
5. Check IAM/service account permissions

---

## Summary

**What's Complete:**
- ✅ Configurable storage backend implementation
- ✅ Support for LOCAL, S3, GCS, AZURE, R2
- ✅ Production validation and error handling
- ✅ Comprehensive test coverage
- ✅ Security best practices (private buckets, signed URLs)

**What's Required for Production:**
- ⚠️ Install dependencies: `pip install -r requirements/production.txt`
- ⚠️ Choose provider and create bucket/container
- ⚠️ Configure IAM/service account with minimum permissions
- ⚠️ Add environment variables to Render
- ⚠️ Deploy and verify file operations

**Estimated Setup Time:** 30-60 minutes per environment (dev/staging/prod)

**Cost Impact:** $11-15/year for first year, negligible compared to other infrastructure costs
