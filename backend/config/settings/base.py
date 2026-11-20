"""
Base settings for GOFER EXAM project.
These settings are shared across all environments.
"""

from pathlib import Path
from decouple import config
from django.core.exceptions import ImproperlyConfigured

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY', default='django-insecure-change-this-in-production')

# Application definition
INSTALLED_APPS = [
    # Django apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third-party apps
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'drf_spectacular',
    
    # Local apps
    'apps.accounts',
    'apps.students',
    'apps.consultants',
    'apps.scholarships',
    'apps.universities',
    'apps.destinations',
    'apps.services',
    'apps.applications',
    'apps.consultations',
    'apps.documents',
    'apps.notifications',
    'apps.opportunities',
    'apps.common',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

# Media files (User uploads)
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Storage Backend Configuration
# Valid options: LOCAL, S3, GCS, AZURE, R2
STORAGE_BACKEND = config('STORAGE_BACKEND', default='LOCAL')

# AWS S3 Configuration (for S3 and R2 backends)
AWS_ACCESS_KEY_ID = config('AWS_ACCESS_KEY_ID', default='')
AWS_SECRET_ACCESS_KEY = config('AWS_SECRET_ACCESS_KEY', default='')
AWS_STORAGE_BUCKET_NAME = config('AWS_STORAGE_BUCKET_NAME', default='')
AWS_S3_REGION_NAME = config('AWS_S3_REGION_NAME', default='us-east-1')
AWS_S3_CUSTOM_DOMAIN = config('AWS_S3_CUSTOM_DOMAIN', default='')
AWS_S3_ENDPOINT_URL = config('AWS_S3_ENDPOINT_URL', default='')  # For R2 or S3-compatible services
AWS_S3_FILE_OVERWRITE = False
AWS_DEFAULT_ACL = None  # Use bucket policy instead of ACLs
AWS_S3_OBJECT_PARAMETERS = {
    'CacheControl': 'max-age=86400',  # 24 hours
}
AWS_QUERYSTRING_AUTH = True  # Generate signed URLs for private files
AWS_QUERYSTRING_EXPIRE = 3600  # Signed URL expiry in seconds (1 hour)

# Google Cloud Storage Configuration
GS_BUCKET_NAME = config('GS_BUCKET_NAME', default='')
GS_PROJECT_ID = config('GS_PROJECT_ID', default='')
GS_CREDENTIALS = config('GS_CREDENTIALS', default='')  # Path to service account JSON
GS_FILE_OVERWRITE = False
GS_DEFAULT_ACL = None
GS_QUERYSTRING_AUTH = True
GS_EXPIRATION = 3600  # Signed URL expiry in seconds (1 hour)

# Azure Blob Storage Configuration
AZURE_ACCOUNT_NAME = config('AZURE_ACCOUNT_NAME', default='')
AZURE_ACCOUNT_KEY = config('AZURE_ACCOUNT_KEY', default='')
AZURE_CONTAINER = config('AZURE_CONTAINER', default='')
AZURE_CUSTOM_DOMAIN = config('AZURE_CUSTOM_DOMAIN', default='')
AZURE_CONNECTION_STRING = config('AZURE_CONNECTION_STRING', default='')
AZURE_OVERWRITE_FILES = False

# Set DEFAULT_FILE_STORAGE based on STORAGE_BACKEND
if STORAGE_BACKEND == 'S3':
    DEFAULT_FILE_STORAGE = 'config.storage_backends.S3MediaStorage'
elif STORAGE_BACKEND == 'GCS':
    DEFAULT_FILE_STORAGE = 'config.storage_backends.GoogleCloudMediaStorage'
elif STORAGE_BACKEND == 'AZURE':
    DEFAULT_FILE_STORAGE = 'config.storage_backends.AzureMediaStorage'
elif STORAGE_BACKEND == 'R2':
    DEFAULT_FILE_STORAGE = 'config.storage_backends.CloudflareR2Storage'
else:  # LOCAL (default)
    DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom User Model
AUTH_USER_MODEL = 'accounts.User'

# Django Authentication Backends
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]

# Django REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'apps.accounts.authentication.CookieJWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': (
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ),
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'EXCEPTION_HANDLER': 'apps.common.exceptions.custom_exception_handler',
}

AUTH_ACCESS_COOKIE_NAME = 'access_token'
AUTH_REFRESH_COOKIE_NAME = 'refresh_token'
AUTH_SESSION_COOKIE_NAME = 'gofer_session'
AUTH_ACCESS_COOKIE_PATH = '/api/v1/'
AUTH_REFRESH_COOKIE_PATH = '/api/v1/auth/'
AUTH_COOKIE_SECURE = config('AUTH_COOKIE_SECURE', default=True, cast=bool)
AUTH_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Lax'

# Simple JWT Settings
from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    'CHECK_REVOKE_TOKEN': True,
}

PASSWORD_RESET_TIMEOUT = 60 * 60

# DRF Spectacular (OpenAPI documentation)
SPECTACULAR_SETTINGS = {
    'TITLE': 'GOFER EXAM API',
    'DESCRIPTION': 'REST API foundation for GOFER EXAM study-abroad information and consultancy services',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'SCHEMA_PATH_PREFIX': '/api/v1/',
    'COMPONENT_SPLIT_REQUEST': True,
    'SORT_OPERATIONS': False,
}

# Email Configuration
EMAIL_BACKEND = config(
    'EMAIL_BACKEND',
    default='django.core.mail.backends.console.EmailBackend',
)
EMAIL_HOST = config('EMAIL_HOST', default='')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_USE_SSL = config('EMAIL_USE_SSL', default=False, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
EMAIL_TIMEOUT = config('EMAIL_TIMEOUT', default=10, cast=int)
BREVO_API_KEY = config('BREVO_API_KEY', default='')
DEFAULT_FROM_EMAIL = config('GOFER_EMAIL_FROM', default='webmaster@localhost')
GOFER_FRONTEND_URL = config(
    'GOFER_FRONTEND_URL',
    default='http://localhost:3000',
).rstrip('/')
EMAIL_VERIFICATION_TOKEN_TTL_MINUTES = config(
    'EMAIL_VERIFICATION_TOKEN_TTL_MINUTES',
    default=60,
    cast=int,
)
EMAIL_VERIFICATION_RESEND_COOLDOWN_SECONDS = config(
    'EMAIL_VERIFICATION_RESEND_COOLDOWN_SECONDS',
    default=60,
    cast=int,
)
if EMAIL_VERIFICATION_TOKEN_TTL_MINUTES < 1:
    raise ImproperlyConfigured('EMAIL_VERIFICATION_TOKEN_TTL_MINUTES must be positive.')
if EMAIL_VERIFICATION_RESEND_COOLDOWN_SECONDS < 1:
    raise ImproperlyConfigured('EMAIL_VERIFICATION_RESEND_COOLDOWN_SECONDS must be positive.')

REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'] = {
    'auth_register': '5/hour',
    'auth_login': '10/hour',
    'auth_verify': '20/hour',
    'auth_resend': '3/hour',
    'auth_password_reset': '3/hour',
    'auth_password_confirm': '10/hour',
    'auth_password_change': '5/hour',
    'auth_user_management': '60/hour',
}

# Logging Configuration
# Structured logging with timestamps, severity levels, and request correlation
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {name} {module} {funcName} {message}',
            'style': '{',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
        'simple': {
            'format': '{levelname} {asctime} {message}',
            'style': '{',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'console_simple': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'null': {
            'class': 'logging.NullHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': config('DJANGO_LOG_LEVEL', default='INFO'),
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
            # SQL queries - set to DEBUG to see queries, INFO to hide
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'apps': {
            # All application loggers
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}


# Error Monitoring Configuration (Optional)
# Set SENTRY_DSN to enable error monitoring with Sentry
# Application continues normally if monitoring is unavailable
MONITORING_ENABLED = config('MONITORING_ENABLED', default=True, cast=bool)
SENTRY_DSN = config('SENTRY_DSN', default='')
SENTRY_ENVIRONMENT = config('SENTRY_ENVIRONMENT', default='production')
SENTRY_TRACES_SAMPLE_RATE = config('SENTRY_TRACES_SAMPLE_RATE', default=0.0, cast=float)
