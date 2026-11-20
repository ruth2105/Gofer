"""
Configurable storage backends for GOFER EXAM.
Supports local filesystem, AWS S3, Google Cloud Storage, and Azure Blob Storage.
"""

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from storages.backends.s3boto3 import S3Boto3Storage
from storages.backends.gcloud import GoogleCloudStorage
from storages.backends.azure_storage import AzureStorage


class LocalMediaStorage(FileSystemStorage):
    """
    Local filesystem storage for development.
    Files stored in MEDIA_ROOT directory.
    """
    pass


class S3MediaStorage(S3Boto3Storage):
    """
    AWS S3 storage backend for production.
    Configurable via AWS_* settings.
    """
    location = 'media'
    file_overwrite = False
    default_acl = None  # Use bucket policy instead
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ensure bucket configuration
        if not settings.AWS_STORAGE_BUCKET_NAME:
            raise ValueError('AWS_STORAGE_BUCKET_NAME must be set when using S3 storage')


class GoogleCloudMediaStorage(GoogleCloudStorage):
    """
    Google Cloud Storage backend for production.
    Configurable via GS_* settings.
    """
    location = 'media'
    file_overwrite = False
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ensure bucket configuration
        if not settings.GS_BUCKET_NAME:
            raise ValueError('GS_BUCKET_NAME must be set when using Google Cloud Storage')


class AzureMediaStorage(AzureStorage):
    """
    Azure Blob Storage backend for production.
    Configurable via AZURE_* settings.
    """
    location = 'media'
    overwrite_files = False
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ensure container configuration
        if not settings.AZURE_CONTAINER:
            raise ValueError('AZURE_CONTAINER must be set when using Azure storage')


class CloudflareR2Storage(S3Boto3Storage):
    """
    Cloudflare R2 storage backend (S3-compatible).
    Zero egress fees, S3-compatible API.
    """
    location = 'media'
    file_overwrite = False
    default_acl = None
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ensure R2 configuration
        if not settings.AWS_STORAGE_BUCKET_NAME or not settings.AWS_S3_ENDPOINT_URL:
            raise ValueError(
                'AWS_STORAGE_BUCKET_NAME and AWS_S3_ENDPOINT_URL '
                'must be set when using Cloudflare R2'
            )


def get_storage_backend():
    """
    Factory function to return the configured storage backend.
    Allows runtime selection based on STORAGE_BACKEND setting.
    """
    backend = getattr(settings, 'STORAGE_BACKEND', 'LOCAL')
    
    backends = {
        'LOCAL': LocalMediaStorage,
        'S3': S3MediaStorage,
        'GCS': GoogleCloudMediaStorage,
        'AZURE': AzureMediaStorage,
        'R2': CloudflareR2Storage,
    }
    
    if backend not in backends:
        raise ValueError(
            f'Invalid STORAGE_BACKEND: {backend}. '
            f'Valid options: {", ".join(backends.keys())}'
        )
    
    return backends[backend]()
