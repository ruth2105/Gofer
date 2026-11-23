# P0-1: Storage Provider Comparison for Gofer Exam

**Date:** 2026-11-02  
**Purpose:** Evaluate durable object storage providers for student document uploads (transcripts, passports, certificates, photos)

---

## Current State

**Local Filesystem Storage:**
- MEDIA_ROOT: `backend/media/`
- Ephemeral: Files lost on Render deployment/restart
- No redundancy or backups
- Cannot scale across multiple containers
- **BLOCKER for production**

**Document Requirements:**
- File types: PDF, DOC, DOCX, JPG, JPEG, PNG
- Max file size: 10MB per document
- Expected volume: ~50-200 GB in first year (estimated)
- Access pattern: Write-once, read occasionally, long-term retention
- Security: Per-document access control, confidential flag support

---

## Storage Provider Comparison

### Pricing Summary (2026)

Content rephrased for compliance with licensing restrictions based on research from multiple [cloud storage comparison sources](https://www.finout.io/blog/cloud-storage-pricing-comparison).

| Provider | Storage Cost | Retrieval Cost | Egress Cost | Free Tier |
|----------|--------------|----------------|-------------|-----------|
| **AWS S3 Standard** | $0.023/GB/month | $0.0004/1K requests | $0.09/GB | 5 GB, 12 months |
| **Google Cloud Storage** | $0.020/GB/month | $0.0004/1K requests | $0.12/GB | 5 GB always free |
| **Azure Blob Hot** | $0.018/GB/month | $0.0004/1K requests | $0.087/GB | 5 GB, 12 months |
| **Cloudflare R2** | $0.015/GB/month | $0 (free) | $0 (free) | 10 GB always free |

**Source Notes:**
- Pricing information aggregated from [AWS S3 pricing](https://aws.amazon.com/s3/pricing/), [GCS pricing comparison](https://www.nops.io/blog/google-cloud-storage-pricing/), and [multi-cloud storage comparisons](https://press.farm/aws-s3-vs-azure-blob-vs-google-cloud-storage/)
- Rates are for hot/standard tier in US regions
- All providers charge for PUT/POST/DELETE operations (~$0.005 per 1K requests)

### Cost Estimates for Gofer Exam

**Scenario: 100 GB storage, 500 uploads/month, 1,000 downloads/month**

| Provider | Storage | Operations | Egress (10 GB/mo) | **Total/Month** |
|----------|---------|------------|-------------------|-----------------|
| AWS S3 | $2.30 | $0.01 | $0.90 | **~$3.21** |
| GCS | $2.00 | $0.01 | $1.20 | **~$3.21** |
| Azure Blob | $1.80 | $0.01 | $0.87 | **~$2.68** |
| Cloudflare R2 | $1.50 | $0.01 | $0.00 | **~$1.51** |

**For first year (50 GB avg storage):**
- AWS S3: ~$15-20/year
- GCS: ~$15-20/year
- Azure: ~$12-18/year
- Cloudflare R2: ~$9-12/year

---

## Django Integration via django-storages

**Package:** [`django-storages`](https://pypi.org/project/django-storages/) (industry standard, 10K+ GitHub stars)

### Supported Backends

Per [django-storages documentation](https://django-storages.readthedocs.io/):

1. **AWS S3** (`storages.backends.s3boto3.S3Boto3Storage`)
   - Requires: `boto3` package
   - Most mature integration
   - Extensive community support

2. **Google Cloud Storage** (`storages.backends.gcloud.GoogleCloudStorage`)
   - Requires: `google-cloud-storage` package
   - Official Google SDK

3. **Azure Blob Storage** (`storages.backends.azure_storage.AzureStorage`)
   - Requires: `azure-storage-blob` package
   - Official Microsoft SDK

4. **Cloudflare R2** (S3-compatible)
   - Use S3Boto3Storage with R2 endpoint
   - No egress fees (major advantage)

### Configuration Pattern

All backends use similar Django settings:

```python
# AWS S3 Example
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
AWS_ACCESS_KEY_ID = 'your-access-key'
AWS_SECRET_ACCESS_KEY = 'your-secret-key'
AWS_STORAGE_BUCKET_NAME = 'your-bucket-name'
AWS_S3_REGION_NAME = 'us-east-1'
AWS_S3_FILE_OVERWRITE = False
AWS_DEFAULT_ACL = None  # Use bucket policy
```

**No code changes required** - Django's FileField API remains identical.

---

## Provider Evaluation Matrix

| Criteria | AWS S3 | GCS | Azure Blob | Cloudflare R2 |
|----------|--------|-----|------------|---------------|
| **Pricing** | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Django Integration** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Reliability** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Documentation** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Free Tier** | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Egress Costs** | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Market Share** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |

---

## Recommendation

### Primary: **AWS S3**

**Reasons:**
1. **Industry Standard** - Most common choice, extensive documentation
2. **Best Django Integration** - Most tested with django-storages
3. **Mature Ecosystem** - IAM policies, CloudFront CDN, versioning, lifecycle rules
4. **Proven Reliability** - 99.999999999% (11 nines) durability
5. **Team Familiarity** - Most developers know S3 basics
6. **Cost Acceptable** - ~$15-20/year for first year storage needs

**Tradeoffs:**
- Slightly higher cost than Azure/R2
- Egress fees (but minimal for document download use case)

### Alternative 1: **Cloudflare R2**

**When to Choose:**
- If egress costs become significant (high download volume)
- Tightest budget constraints
- Already using Cloudflare services

**Concerns:**
- Newer service (less battle-tested than S3/GCS/Azure)
- Smaller community/fewer troubleshooting resources

### Alternative 2: **Google Cloud Storage**

**When to Choose:**
- Already using Google Cloud Platform
- Prefer Google's always-free tier (5 GB vs AWS 12-month limit)
- Need advanced ML/AI integrations

### Alternative 3: **Azure Blob Storage**

**When to Choose:**
- Already using Azure services
- Lowest base storage cost matters most
- Microsoft-centric infrastructure

---

## Implementation Strategy

### Phase 1: Local Implementation (This Sprint)
1. Add `django-storages` and `boto3` to requirements
2. Create configurable storage backend
3. Implement settings abstraction (LOCAL vs S3 vs GCS vs AZURE)
4. Add environment variables with sensible defaults
5. Write tests with mocked storage
6. Update documentation

### Phase 2: Provider Setup (Before Production Deploy)
1. Create AWS account / S3 bucket (or alternative provider)
2. Configure IAM user with minimal permissions (PutObject, GetObject, DeleteObject)
3. Set bucket policy (private, CORS for frontend access)
4. Generate access credentials
5. Add credentials to Render environment variables
6. Test upload/download in staging

### Phase 3: Migration (If Needed)
- No migration needed - no production files exist yet
- Fresh start with durable storage

---

## Security Considerations

### IAM Policy (AWS S3 Example)

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:DeleteObject"
      ],
      "Resource": "arn:aws:s3:::gofer-exam-documents/*"
    },
    {
      "Effect": "Allow",
      "Action": ["s3:ListBucket"],
      "Resource": "arn:aws:s3:::gofer-exam-documents"
    }
  ]
}
```

### Bucket Configuration

- **Private bucket** (no public access)
- **CORS rules** for frontend upload/download
- **Versioning enabled** (optional - adds cost but enables recovery)
- **Lifecycle rules** (optional - auto-delete expired documents)
- **Encryption at rest** (server-side, S3-managed keys)

### Django Settings Security

- **Never commit credentials** - use environment variables
- **Validate bucket name** in production settings
- **Use bucket policies** over ACLs (AWS_DEFAULT_ACL = None)
- **Serve downloads via signed URLs** (future enhancement for extra security)

---

## Next Steps

1. ✅ Compare providers (this document)
2. ⏭️ Implement configurable storage backend
3. ⏭️ Add tests for storage abstraction
4. ⏭️ Document setup procedures per provider
5. ⏭️ Add deployment checklist

---

## References

- [AWS S3 Pricing](https://aws.amazon.com/s3/pricing/)
- [Cloud Storage Pricing Comparison 2026](https://www.finout.io/blog/cloud-storage-pricing-comparison)
- [django-storages Documentation](https://django-storages.readthedocs.io/)
- [Django File Storage Guide](https://reintech.io/blog/setting-up-file-storage-in-django)
- [S3 vs Azure Blob vs GCS Comparison](https://press.farm/aws-s3-vs-azure-blob-vs-google-cloud-storage/)

---

**Decision:** Proceed with **AWS S3** as primary implementation, with configuration abstraction allowing easy migration to GCS/Azure/R2 if requirements change.

**Cost Impact:** $15-20/year (negligible compared to database/compute costs)

**Implementation Effort:** 4-6 hours (django-storages makes this straightforward)
