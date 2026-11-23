# P0-5: Health Checks, Logging & Monitoring Documentation

## Overview

Complete implementation of production-grade health checks, structured logging, and optional error monitoring for Gofer Exam platform.

**Status**: ✅ All tasks complete, tests passing (52/52)

---

## Health Check Endpoints

### Implemented Endpoints

#### 1. Liveness Probe (`/api/v1/health/liveness/`)

**Purpose**: Verifies application process is running  
**Use Case**: Container orchestrators (Kubernetes liveness probe)  
**Checks**: Application availability only (no database)  
**Response**: Always 200 if process responsive

**Example**:
```bash
curl https://api.example.com/api/v1/health/liveness/

# Response:
{
  "status": "alive",
  "timestamp": "2026-11-20T12:00:00Z"
}
```

#### 2. Readiness Probe (`/api/v1/health/readiness/`)

**Purpose**: Verifies application ready to serve traffic  
**Use Case**: Load balancers (route traffic decision)  
**Checks**: Application + database connectivity  
**Response**: 200 (ready) or 503 (not ready)

**Example**:
```bash
curl https://api.example.com/api/v1/health/readiness/

# Success (200):
{
  "status": "ready",
  "checks": {
    "application": "ok",
    "database": "ok"
  },
  "timestamp": "2026-11-20T12:00:00Z"
}

# Database unavailable (503):
{
  "status": "not_ready",
  "checks": {
    "application": "ok",
    "database": "error"
  },
  "timestamp": "2026-11-20T12:00:00Z"
}
```

#### 3. Health Check (`/api/v1/health/`)

**Purpose**: Comprehensive service status  
**Use Case**: Monitoring dashboards, manual inspection  
**Checks**: Application, database performance, response time  
**Response**: 200 (healthy) or 503 (unhealthy/degraded)

**Example**:
```bash
curl https://api.example.com/api/v1/health/

# Healthy (200):
{
  "status": "healthy",
  "timestamp": "2026-11-20T12:00:00Z",
  "checks": {
    "application": {
      "status": "healthy",
      "message": "Application is running"
    },
    "database": {
      "status": "healthy",
      "message": "Database is accessible",
      "response_time_ms": 12.34
    }
  }
}

# Degraded database (503):
{
  "status": "unhealthy",
  "timestamp": "2026-11-20T12:00:00Z",
  "checks": {
    "application": {
      "status": "healthy",
      "message": "Application is running"
    },
    "database": {
      "status": "degraded",
      "message": "Database responding slowly (1200ms)",
      "response_time_ms": 1200.0
    }
  }
}
```

### Configuration

**No environment variables required** - Health checks work out of the box.

**Render Configuration** (render.yaml):
```yaml
services:
  - type: web
    name: gofere-api
    healthCheckPath: /api/v1/health/
```

**Kubernetes Configuration**:
```yaml
livenessProbe:
  httpGet:
    path: /api/v1/health/liveness/
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /api/v1/health/readiness/
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 5
```

### Security

- ✅ **No authentication required** (public health checks)
- ✅ **No secrets exposed** (database credentials filtered)
- ✅ **No internal details** (error messages sanitized)
- ✅ **Rate limiting safe** (lightweight queries)

---

## Structured Logging

### Configuration

**Location**: `backend/config/settings/base.py`

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {name} {module} {funcName} {message}',
            'style': '{',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'django.security': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'INFO',  # Set to DEBUG to see SQL queries
            'propagate': False,
        },
        'apps': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
```

**Environment Variables**:
```bash
# Optional: Override Django log level
DJANGO_LOG_LEVEL=INFO  # Options: DEBUG, INFO, WARNING, ERROR, CRITICAL
```

### Log Format

**Example Output**:
```
INFO 2026-11-20 12:00:00 apps.health views get Health check passed
WARNING 2026-11-20 12:00:05 django.request log log_response Not Found: /api/v1/invalid/
ERROR 2026-11-20 12:00:10 apps.common.monitoring monitoring capture_exception Failed to capture exception
```

**Fields**:
- `levelname`: Log severity (INFO, WARNING, ERROR, etc.)
- `asctime`: Timestamp (YYYY-MM-DD HH:MM:SS)
- `name`: Logger name (e.g., `apps.health.views`)
- `module`: Python module
- `funcName`: Function name
- `message`: Log message

### Logging Utilities

**Location**: `backend/apps/common/logging_utils.py`

#### Safe Exception Logging

```python
from apps.common.logging_utils import safe_log_exception
import logging

logger = logging.getLogger(__name__)

try:
    process_payment(api_key='secret-key-123')
except Exception as e:
    safe_log_exception(
        logger,
        'Payment processing failed',
        extra={'user_id': user.id, 'amount': 100.00}
    )
    # Sensitive data (api_key) automatically filtered from logs
```

#### API Request Logging

```python
from apps.common.logging_utils import log_api_request
import time

start_time = time.time()
response = view_function(request)
response_time = (time.time() - start_time) * 1000

log_api_request(logger, request, response.status_code, response_time)
# Logs: GET /api/v1/scholarships/ 200 45ms
```

#### Security Event Logging

```python
from apps.common.logging_utils import log_security_event

log_security_event(
    logger,
    'login_failed',
    user_id=None,
    ip_address=request.META['REMOTE_ADDR'],
    details={'email': 'user@example.com', 'reason': 'invalid_credentials'}
)
```

### Filtered Sensitive Data

**Automatically filtered patterns**:
- Passwords (`password="secret"` → `password=***`)
- Tokens (`token=abc123` → `token=***`)
- API keys (`api_key="xkeysib-123"` → `api_key=***`)
- Database connection strings (`postgresql://user:pass@host` → `postgresql://user:***@host`)
- Email credentials (`EMAIL_HOST_PASSWORD=secret` → `EMAIL_HOST_PASSWORD=***`)
- Cookies (`Cookie: sessionid=abc` → `Cookie: ***`)

---

## Error Monitoring

### Overview

Optional integration with error monitoring services (Sentry). Application continues normally when monitoring is disabled or unavailable.

### Configuration

**Environment Variables** (Optional):
```bash
# Enable/disable monitoring
MONITORING_ENABLED=true  # Default: true (if SENTRY_DSN present)

# Sentry Configuration (optional)
SENTRY_DSN=https://public_key@sentry.io/project_id
SENTRY_ENVIRONMENT=production  # or staging, development
SENTRY_TRACES_SAMPLE_RATE=0.1  # 10% of transactions (0.0 to 1.0)
```

### Installation

**With Sentry** (optional):
```bash
pip install sentry-sdk
```

**Without Sentry**:
- No installation required
- Application logs warnings but continues normally
- No functionality is lost

### Usage

#### Initialize Monitoring (in application startup)

```python
from apps.common.monitoring import initialize_monitoring

# Call during application initialization (e.g., in wsgi.py or asgi.py)
initialize_monitoring()
# Returns True if successful, False otherwise
# Application continues normally in both cases
```

#### Capture Exceptions

```python
from apps.common.monitoring import capture_exception

try:
    risky_operation()
except Exception as e:
    event_id = capture_exception(
        e,
        context={'user_id': user.id, 'request_id': request_id}
    )
    # event_id is None if monitoring unavailable
```

#### Capture Custom Messages

```python
from apps.common.monitoring import capture_message

capture_message(
    'Daily backup completed',
    level='info',
    context={'backup_size_mb': 250, 'duration_seconds': 45}
)
```

#### Set User Context

```python
from apps.common.monitoring import set_user_context, clear_user_context

# After login
set_user_context(user_id=user.id, email=user.email)

# After logout
clear_user_context()
```

### Data Privacy

**Sensitive data automatically filtered**:
- ✅ PII sending disabled (`send_default_pii=False`)
- ✅ Authorization headers filtered
- ✅ Cookie headers filtered
- ✅ Database credentials filtered
- ✅ API keys filtered
- ✅ Email passwords filtered

### Cost Comparison

| Provider | Free Tier | Paid Plans | Notes |
|----------|-----------|------------|-------|
| **Sentry** | 5K errors/month | $26/month (50K errors) | Most popular, best Django integration |
| **Rollbar** | 5K errors/month | $12/month (25K errors) | Good alternative |
| **Bugsnag** | 500 errors/month | $59/month (unlimited) | Enterprise features |
| **Self-Hosted Sentry** | Unlimited | Infrastructure costs | ~$20-50/month for small deployment |

**Recommendation**: Start with Sentry free tier (5K errors/month sufficient for MVP).

---

## Deployment Verification Checklist

### Pre-Deployment

- [ ] Health check endpoints accessible locally (`/api/v1/health/`)
- [ ] Logs show structured format with timestamps
- [ ] No sensitive data in logs (check with test exceptions)
- [ ] Monitoring optional (app works without Sentry configured)
- [ ] All tests passing (health, logging, monitoring)

### Post-Deployment

**Health Checks**:
- [ ] Liveness probe returns 200: `curl https://api.example.com/api/v1/health/liveness/`
- [ ] Readiness probe returns 200: `curl https://api.example.com/api/v1/health/readiness/`
- [ ] Health check returns 200: `curl https://api.example.com/api/v1/health/`
- [ ] Database response time < 100ms (check `response_time_ms` field)
- [ ] Load balancer configured to use readiness probe

**Logging**:
- [ ] Logs visible in deployment dashboard (Render/Heroku logs)
- [ ] Log format includes timestamps and severity
- [ ] Error logs do not expose secrets (check for `***` filtering)
- [ ] Log level appropriate for environment (INFO for production)

**Monitoring** (if configured):
- [ ] Sentry dashboard shows connection
- [ ] Test exception captured in Sentry
- [ ] User context visible in error details
- [ ] No PII (email, passwords) in error reports
- [ ] Error alerts configured (optional)

### Troubleshooting

**Health check returns 503**:
```bash
# Check which component failing
curl https://api.example.com/api/v1/health/ | jq '.checks'

# Database issue if:
{
  "database": {
    "status": "unhealthy",
    "message": "Database connection failed"
  }
}

# Verify database accessible
psql $DATABASE_URL -c "SELECT 1"
```

**Logs not appearing**:
```bash
# Check DJANGO_LOG_LEVEL not set too high
echo $DJANGO_LOG_LEVEL  # Should be INFO or DEBUG

# Verify logging configuration
python manage.py shell
>>> from django.conf import settings
>>> settings.LOGGING
```

**Monitoring not working**:
```bash
# Check if Sentry SDK installed
pip list | grep sentry-sdk

# Verify SENTRY_DSN set
echo $SENTRY_DSN  # Should start with https://

# Check initialization
python manage.py shell
>>> from apps.common.monitoring import is_monitoring_available
>>> is_monitoring_available()
True  # If monitoring active
```

---

## Implementation Files

### Created Files

1. **Health Check Implementation**:
   - `backend/apps/health/__init__.py`
   - `backend/apps/health/views.py` (LivenessView, ReadinessView, HealthView)
   - `backend/apps/health/urls.py`
   - `backend/apps/health/tests.py` (11 tests)

2. **Logging Utilities**:
   - `backend/apps/common/logging_utils.py`
   - `backend/apps/common/tests_logging.py` (22 tests)

3. **Error Monitoring**:
   - `backend/apps/common/monitoring.py`
   - `backend/apps/common/tests_monitoring.py` (19 tests)

### Modified Files

1. **URL Configuration**:
   - `backend/config/urls.py` (added health check route)

2. **Settings**:
   - `backend/config/settings/base.py` (enhanced logging, added monitoring config)

3. **Models** (Bug Fix):
   - `backend/apps/opportunities/models.py` (fixed CheckConstraint for Django 5.0 compatibility: `condition=` → `check=`)

---

## Test Results

**All Tests Passing**: ✅ 52/52 (100%)

### Health Checks: ✅ 11/11
```
test_health_does_not_expose_secrets ... ok
test_health_includes_database_response_time ... ok
test_health_logs_failures ... ok
test_health_returns_200_when_all_checks_pass ... ok
test_health_returns_503_when_database_fails ... ok
test_health_returns_degraded_for_slow_database ... ok
test_liveness_does_not_check_database ... ok
test_liveness_returns_200 ... ok
test_readiness_does_not_expose_database_credentials ... ok
test_readiness_returns_200_when_database_available ... ok
test_readiness_returns_503_when_database_unavailable ... ok
```

### Logging Utilities: ✅ 22/22
```
test_filters_api_keys ... ok
test_filters_cookies ... ok
test_filters_database_passwords ... ok
test_filters_email_host_password ... ok
test_filters_passwords ... ok
test_filters_tokens ... ok
test_handles_empty_string ... ok
test_handles_none_input ... ok
test_preserves_non_sensitive_data ... ok
test_logs_exception_with_filtered_message ... ok
test_logs_with_filtered_extra_context ... ok
test_supports_different_log_levels ... ok
test_extracts_x_correlation_id_header ... ok
test_extracts_x_request_id_header ... ok
test_returns_none_when_no_request_id ... ok
test_includes_request_correlation_id ... ok
test_logs_client_error_at_warning_level ... ok
test_logs_server_error_at_error_level ... ok
test_logs_successful_request ... ok
test_filters_sensitive_details ... ok
test_handles_missing_details ... ok
test_logs_security_event ... ok
```

### Error Monitoring: ✅ 19/19
```
test_handles_initialization_errors_gracefully ... ok
test_handles_missing_sentry_sdk_gracefully ... ok
test_initializes_sentry_with_correct_config ... ok
test_returns_false_when_explicitly_disabled ... ok
test_returns_false_when_no_dsn_configured ... ok
test_filters_authorization_header ... ok
test_filters_cookie_header ... ok
test_filters_sensitive_environment_variables ... ok
test_returns_event_when_no_sensitive_data ... ok
test_captures_exception_when_monitoring_available ... ok
test_handles_capture_errors_gracefully ... ok
test_includes_context_in_capture ... ok
test_returns_none_when_monitoring_unavailable ... ok
test_captures_message_when_monitoring_available ... ok
test_returns_none_when_monitoring_unavailable ... ok
test_clears_user_context ... ok
test_handles_context_errors_gracefully ... ok
test_handles_unavailable_monitoring_gracefully ... ok
test_sets_user_context ... ok
```

---

## Security Features

### Health Checks
- ✅ No database credentials in responses
- ✅ No connection strings in error messages
- ✅ Sanitized error messages (generic "Database connection failed")
- ✅ No stack traces in responses
- ✅ Response time safe to expose (no timing attacks possible)

### Logging
- ✅ Passwords automatically filtered (`password=***`)
- ✅ API keys automatically filtered (`api_key=***`)
- ✅ Tokens automatically filtered (`token=***`)
- ✅ Database passwords filtered from connection strings
- ✅ Email credentials filtered
- ✅ Cookies filtered from HTTP headers
- ✅ Safe exception handling (no sensitive data in tracebacks)

### Monitoring
- ✅ PII sending disabled by default
- ✅ Authorization headers filtered before sending to Sentry
- ✅ Cookie headers filtered
- ✅ Environment variables filtered (SECRET_KEY, DATABASE_URL, etc.)
- ✅ Application continues normally if monitoring unavailable
- ✅ Capture errors logged locally but don't break application

---

## Next Steps (Optional Enhancements)

### Short Term
1. **Add metrics endpoint** (`/api/v1/metrics/` with Prometheus format)
2. **Add disk space check** to health endpoint
3. **Add email service check** (test SMTP/Brevo connection)
4. **Configure Sentry alerts** (email on critical errors)

### Long Term
1. **Request ID middleware** (generate X-Request-ID for correlation)
2. **Performance monitoring** (Sentry APM or New Relic)
3. **Log aggregation** (Papertrail, Loggly, or ELK stack)
4. **Custom dashboards** (Grafana + Prometheus)
5. **Distributed tracing** (Jaeger or Zipkin)

---

## References

- [Django Logging Documentation](https://docs.djangoproject.com/en/5.0/topics/logging/)
- [Sentry Django Integration](https://docs.sentry.io/platforms/python/guides/django/)
- [Kubernetes Health Checks](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/)
- [Render Health Checks](https://render.com/docs/web-services#health-checks)

---

## Summary

**P0-5 Status**: ✅ **COMPLETE**

- ✅ Health checks implemented (liveness, readiness, comprehensive)
- ✅ Structured logging configured with sensitive data filtering
- ✅ Optional error monitoring (Sentry integration)
- ✅ All tests passing (52/52 - 100%)
- ✅ Documentation complete
- ✅ Security features implemented (no secrets exposed)
- ✅ Production-ready deployment configuration

**No External Costs**: All features work without paid services. Sentry optional (free tier: 5K errors/month).

**No Production Changes**: All implementation local, no deployments made.
