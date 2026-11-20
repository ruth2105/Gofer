"""
Production settings for GOFER EXAM project.
"""

from .base import *
from decouple import config
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.core.validators import validate_email
import environ
from urllib.parse import urlsplit

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

if (
    SECRET_KEY.startswith('django-insecure-')
    or len(SECRET_KEY) < 32
    or len(set(SECRET_KEY)) < 5
):
    raise ImproperlyConfigured('Set a strong SECRET_KEY of at least 32 characters in production.')

ALLOWED_HOSTS = [
    host for host in config('ALLOWED_HOSTS', default='').split(',') if host
]
if not ALLOWED_HOSTS:
    raise ImproperlyConfigured('Set ALLOWED_HOSTS in production.')

frontend_url = urlsplit(GOFER_FRONTEND_URL)
if frontend_url.scheme != 'https' or not frontend_url.netloc:
    raise ImproperlyConfigured('GOFER_FRONTEND_URL must be an absolute HTTPS URL in production.')

# Database
DATABASES = {'default': environ.Env().db_url('DATABASE_URL')}
DATABASES['default']['CONN_MAX_AGE'] = 600
DATABASES['default']['OPTIONS'] = {'sslmode': 'require'}

# CORS Settings for Production
CORS_ALLOWED_ORIGINS = [
    origin for origin in config('CORS_ALLOWED_ORIGINS', default='').split(',') if origin
]
CORS_ALLOW_CREDENTIALS = True
CSRF_TRUSTED_ORIGINS = [
    origin for origin in config('CSRF_TRUSTED_ORIGINS', default='').split(',') if origin
]

# Security Settings
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Email Configuration for Production
EMAIL_BACKEND = config(
    'EMAIL_BACKEND',
    default='django.core.mail.backends.smtp.EmailBackend',
)
non_delivery_backends = {
    'django.core.mail.backends.console.EmailBackend',
    'django.core.mail.backends.dummy.EmailBackend',
    'django.core.mail.backends.locmem.EmailBackend',
    'django.core.mail.backends.filebased.EmailBackend',
}
if EMAIL_BACKEND in non_delivery_backends:
    raise ImproperlyConfigured(
        'Configure SMTP or a transactional provider email backend in production.'
    )
if (
    not DEFAULT_FROM_EMAIL
    or DEFAULT_FROM_EMAIL == 'webmaster@localhost'
    or 'YOUR_VERIFIED_DOMAIN' in DEFAULT_FROM_EMAIL
):
    raise ImproperlyConfigured('Set GOFER_EMAIL_FROM to the verified sender address.')
try:
    validate_email(DEFAULT_FROM_EMAIL)
except ValidationError as error:
    raise ImproperlyConfigured('GOFER_EMAIL_FROM must be a valid email address.') from error

if (
    EMAIL_BACKEND == 'config.email_backends.brevo.BrevoEmailBackend'
    and not BREVO_API_KEY.strip()
):
    raise ImproperlyConfigured('Set BREVO_API_KEY to configure Brevo email delivery.')

if EMAIL_BACKEND == 'django.core.mail.backends.smtp.EmailBackend':
    if not EMAIL_HOST:
        raise ImproperlyConfigured(
            'Set EMAIL_HOST to configure production email delivery.'
        )
    if EMAIL_USE_TLS and EMAIL_USE_SSL:
        raise ImproperlyConfigured('EMAIL_USE_TLS and EMAIL_USE_SSL cannot both be enabled.')
    if not EMAIL_USE_TLS and not EMAIL_USE_SSL:
        raise ImproperlyConfigured('Production SMTP must use TLS or SSL.')
    if not 1 <= EMAIL_PORT <= 65535:
        raise ImproperlyConfigured('EMAIL_PORT must be between 1 and 65535.')

# Storage Configuration Validation
if STORAGE_BACKEND not in ['LOCAL', 'S3', 'GCS', 'AZURE', 'R2']:
    raise ImproperlyConfigured(
        f'STORAGE_BACKEND must be one of: LOCAL, S3, GCS, AZURE, R2. Got: {STORAGE_BACKEND}'
    )

if STORAGE_BACKEND == 'LOCAL':
    # Warn about ephemeral storage in production
    import warnings
    warnings.warn(
        'Using LOCAL storage in production. Files will be lost on deployment/restart. '
        'Configure S3, GCS, Azure, or R2 for durable storage.',
        RuntimeWarning
    )

if STORAGE_BACKEND == 'S3':
    if not AWS_ACCESS_KEY_ID or not AWS_SECRET_ACCESS_KEY:
        raise ImproperlyConfigured('Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY for S3 storage.')
    if not AWS_STORAGE_BUCKET_NAME:
        raise ImproperlyConfigured('Set AWS_STORAGE_BUCKET_NAME for S3 storage.')

if STORAGE_BACKEND == 'GCS':
    if not GS_BUCKET_NAME:
        raise ImproperlyConfigured('Set GS_BUCKET_NAME for Google Cloud Storage.')
    if not GS_CREDENTIALS:
        raise ImproperlyConfigured(
            'Set GS_CREDENTIALS (path to service account JSON) for Google Cloud Storage.'
        )

if STORAGE_BACKEND == 'AZURE':
    if not AZURE_ACCOUNT_NAME or not AZURE_CONTAINER:
        raise ImproperlyConfigured('Set AZURE_ACCOUNT_NAME and AZURE_CONTAINER for Azure storage.')
    if not AZURE_ACCOUNT_KEY and not AZURE_CONNECTION_STRING:
        raise ImproperlyConfigured(
            'Set AZURE_ACCOUNT_KEY or AZURE_CONNECTION_STRING for Azure storage.'
        )

if STORAGE_BACKEND == 'R2':
    if not AWS_ACCESS_KEY_ID or not AWS_SECRET_ACCESS_KEY:
        raise ImproperlyConfigured(
            'Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY for Cloudflare R2.'
        )
    if not AWS_STORAGE_BUCKET_NAME:
        raise ImproperlyConfigured('Set AWS_STORAGE_BUCKET_NAME for Cloudflare R2.')
    if not AWS_S3_ENDPOINT_URL:
        raise ImproperlyConfigured(
            'Set AWS_S3_ENDPOINT_URL (e.g., https://<account_id>.r2.cloudflarestorage.com) '
            'for Cloudflare R2.'
        )

if EMAIL_BACKEND == 'django.core.mail.backends.smtp.EmailBackend':
    if bool(EMAIL_HOST_USER) != bool(EMAIL_HOST_PASSWORD):
        raise ImproperlyConfigured(
            'Set both EMAIL_HOST_USER and EMAIL_HOST_PASSWORD, or leave both empty for an authorized relay.'
        )

# Static files (AWS S3 or similar)
# Uncomment and configure when ready to use cloud storage
# STATICFILES_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
# DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
# AWS_ACCESS_KEY_ID = config('AWS_ACCESS_KEY_ID')
# AWS_SECRET_ACCESS_KEY = config('AWS_SECRET_ACCESS_KEY')
# AWS_STORAGE_BUCKET_NAME = config('AWS_STORAGE_BUCKET_NAME')
# AWS_S3_REGION_NAME = config('AWS_S3_REGION_NAME', default='us-east-1')
