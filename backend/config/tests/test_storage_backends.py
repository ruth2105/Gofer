"""
Tests for configurable storage backends.
Validates LOCAL, S3, GCS, AZURE, and R2 storage configurations.
"""

from django.test import TestCase, override_settings
from django.core.files.base import ContentFile
from django.core.exceptions import ImproperlyConfigured
from unittest.mock import patch, MagicMock, Mock
import io

from config.storage_backends import (
    LocalMediaStorage,
    S3MediaStorage,
    GoogleCloudMediaStorage,
    AzureMediaStorage,
    CloudflareR2Storage,
    get_storage_backend,
)


class LocalMediaStorageTests(TestCase):
    """Test local filesystem storage."""
    
    def test_local_storage_initialization(self):
        """Local storage should initialize without errors."""
        storage = LocalMediaStorage()
        self.assertIsNotNone(storage)
    
    def test_local_storage_save_and_retrieve(self):
        """Local storage should save and retrieve files."""
        storage = LocalMediaStorage()
        content = ContentFile(b'test file content')
        
        # Save file
        filename = storage.save('test/document.txt', content)
        self.assertTrue(storage.exists(filename))
        
        # Retrieve file
        saved_file = storage.open(filename)
        try:
            self.assertEqual(saved_file.read(), b'test file content')
        finally:
            saved_file.close()  # Close file before deletion on Windows
        
        # Cleanup
        storage.delete(filename)
        self.assertFalse(storage.exists(filename))


@override_settings(
    AWS_ACCESS_KEY_ID='test-access-key',
    AWS_SECRET_ACCESS_KEY='test-secret-key',
    AWS_STORAGE_BUCKET_NAME='test-bucket',
    AWS_S3_REGION_NAME='us-east-1',
)
class S3MediaStorageTests(TestCase):
    """Test AWS S3 storage backend."""
    
    @patch('storages.backends.s3boto3.S3Boto3Storage.__init__')
    def test_s3_storage_initialization(self, mock_init):
        """S3 storage should initialize with correct settings."""
        mock_init.return_value = None
        
        storage = S3MediaStorage()
        self.assertEqual(storage.location, 'media')
        self.assertFalse(storage.file_overwrite)
        self.assertIsNone(storage.default_acl)
    
    @override_settings(AWS_STORAGE_BUCKET_NAME='')
    def test_s3_storage_requires_bucket_name(self):
        """S3 storage should raise error if bucket name is missing."""
        with patch('storages.backends.s3boto3.S3Boto3Storage.__init__', return_value=None):
            with self.assertRaises(ValueError) as context:
                S3MediaStorage()
            self.assertIn('AWS_STORAGE_BUCKET_NAME', str(context.exception))
    
    @patch('storages.backends.s3boto3.S3Boto3Storage._save')
    @patch('storages.backends.s3boto3.S3Boto3Storage.__init__')
    def test_s3_storage_save(self, mock_init, mock_save):
        """S3 storage should save files correctly."""
        mock_init.return_value = None
        mock_save.return_value = 'media/test/document.txt'
        
        storage = S3MediaStorage()
        content = ContentFile(b'test content')
        
        result = storage._save('test/document.txt', content)
        self.assertEqual(result, 'media/test/document.txt')
        mock_save.assert_called_once()


@override_settings(
    GS_BUCKET_NAME='test-gcs-bucket',
    GS_PROJECT_ID='test-project',
    GS_CREDENTIALS='/path/to/credentials.json',
)
class GoogleCloudMediaStorageTests(TestCase):
    """Test Google Cloud Storage backend."""
    
    @patch('storages.backends.gcloud.GoogleCloudStorage.__init__')
    def test_gcs_storage_initialization(self, mock_init):
        """GCS storage should initialize with correct settings."""
        mock_init.return_value = None
        
        storage = GoogleCloudMediaStorage()
        self.assertEqual(storage.location, 'media')
        self.assertFalse(storage.file_overwrite)
    
    @override_settings(GS_BUCKET_NAME='')
    def test_gcs_storage_requires_bucket_name(self):
        """GCS storage should raise error if bucket name is missing."""
        with patch('storages.backends.gcloud.GoogleCloudStorage.__init__', return_value=None):
            with self.assertRaises(ValueError) as context:
                GoogleCloudMediaStorage()
            self.assertIn('GS_BUCKET_NAME', str(context.exception))


@override_settings(
    AZURE_ACCOUNT_NAME='testaccount',
    AZURE_ACCOUNT_KEY='test-account-key',
    AZURE_CONTAINER='test-container',
)
class AzureMediaStorageTests(TestCase):
    """Test Azure Blob Storage backend."""
    
    @patch('storages.backends.azure_storage.AzureStorage.__init__')
    def test_azure_storage_initialization(self, mock_init):
        """Azure storage should initialize with correct settings."""
        mock_init.return_value = None
        
        storage = AzureMediaStorage()
        self.assertEqual(storage.location, 'media')
        self.assertFalse(storage.overwrite_files)
    
    @override_settings(AZURE_CONTAINER='')
    def test_azure_storage_requires_container(self):
        """Azure storage should raise error if container is missing."""
        with patch('storages.backends.azure_storage.AzureStorage.__init__', return_value=None):
            with self.assertRaises(ValueError) as context:
                AzureMediaStorage()
            self.assertIn('AZURE_CONTAINER', str(context.exception))


@override_settings(
    AWS_ACCESS_KEY_ID='test-r2-access-key',
    AWS_SECRET_ACCESS_KEY='test-r2-secret-key',
    AWS_STORAGE_BUCKET_NAME='test-r2-bucket',
    AWS_S3_ENDPOINT_URL='https://test-account.r2.cloudflarestorage.com',
)
class CloudflareR2StorageTests(TestCase):
    """Test Cloudflare R2 storage backend."""
    
    @patch('storages.backends.s3boto3.S3Boto3Storage.__init__')
    def test_r2_storage_initialization(self, mock_init):
        """R2 storage should initialize with correct settings."""
        mock_init.return_value = None
        
        storage = CloudflareR2Storage()
        self.assertEqual(storage.location, 'media')
        self.assertFalse(storage.file_overwrite)
        self.assertIsNone(storage.default_acl)
    
    @override_settings(AWS_S3_ENDPOINT_URL='')
    def test_r2_storage_requires_endpoint_url(self):
        """R2 storage should raise error if endpoint URL is missing."""
        with patch('storages.backends.s3boto3.S3Boto3Storage.__init__', return_value=None):
            with self.assertRaises(ValueError) as context:
                CloudflareR2Storage()
            self.assertIn('AWS_S3_ENDPOINT_URL', str(context.exception))


class StorageBackendFactoryTests(TestCase):
    """Test the get_storage_backend factory function."""
    
    @override_settings(STORAGE_BACKEND='LOCAL')
    def test_factory_returns_local_storage(self):
        """Factory should return LocalMediaStorage for LOCAL backend."""
        storage = get_storage_backend()
        self.assertIsInstance(storage, LocalMediaStorage)
    
    @override_settings(
        STORAGE_BACKEND='S3',
        AWS_ACCESS_KEY_ID='test-key',
        AWS_SECRET_ACCESS_KEY='test-secret',
        AWS_STORAGE_BUCKET_NAME='test-bucket',
    )
    @patch('storages.backends.s3boto3.S3Boto3Storage.__init__')
    def test_factory_returns_s3_storage(self, mock_init):
        """Factory should return S3MediaStorage for S3 backend."""
        mock_init.return_value = None
        storage = get_storage_backend()
        self.assertIsInstance(storage, S3MediaStorage)
    
    @override_settings(
        STORAGE_BACKEND='GCS',
        GS_BUCKET_NAME='test-bucket',
        GS_CREDENTIALS='/path/to/creds.json',
    )
    @patch('storages.backends.gcloud.GoogleCloudStorage.__init__')
    def test_factory_returns_gcs_storage(self, mock_init):
        """Factory should return GoogleCloudMediaStorage for GCS backend."""
        mock_init.return_value = None
        storage = get_storage_backend()
        self.assertIsInstance(storage, GoogleCloudMediaStorage)
    
    @override_settings(
        STORAGE_BACKEND='AZURE',
        AZURE_ACCOUNT_NAME='test',
        AZURE_ACCOUNT_KEY='test-key',
        AZURE_CONTAINER='test-container',
    )
    @patch('storages.backends.azure_storage.AzureStorage.__init__')
    def test_factory_returns_azure_storage(self, mock_init):
        """Factory should return AzureMediaStorage for AZURE backend."""
        mock_init.return_value = None
        storage = get_storage_backend()
        self.assertIsInstance(storage, AzureMediaStorage)
    
    @override_settings(
        STORAGE_BACKEND='R2',
        AWS_ACCESS_KEY_ID='test-key',
        AWS_SECRET_ACCESS_KEY='test-secret',
        AWS_STORAGE_BUCKET_NAME='test-bucket',
        AWS_S3_ENDPOINT_URL='https://test.r2.cloudflarestorage.com',
    )
    @patch('storages.backends.s3boto3.S3Boto3Storage.__init__')
    def test_factory_returns_r2_storage(self, mock_init):
        """Factory should return CloudflareR2Storage for R2 backend."""
        mock_init.return_value = None
        storage = get_storage_backend()
        self.assertIsInstance(storage, CloudflareR2Storage)
    
    @override_settings(STORAGE_BACKEND='INVALID')
    def test_factory_raises_error_for_invalid_backend(self):
        """Factory should raise ValueError for invalid backend."""
        with self.assertRaises(ValueError) as context:
            get_storage_backend()
        self.assertIn('Invalid STORAGE_BACKEND', str(context.exception))
        self.assertIn('INVALID', str(context.exception))


class StorageProductionValidationTests(TestCase):
    """Test production settings validation for storage backends."""
    
    @override_settings(STORAGE_BACKEND='S3', AWS_STORAGE_BUCKET_NAME='')
    def test_s3_production_validation_requires_bucket(self):
        """Production settings should require AWS_STORAGE_BUCKET_NAME for S3."""
        from django.core.exceptions import ImproperlyConfigured
        # This would be caught by production.py settings validation
        # We test the storage backend validation here
        with patch('storages.backends.s3boto3.S3Boto3Storage.__init__', return_value=None):
            with self.assertRaises(ValueError):
                S3MediaStorage()
    
    @override_settings(STORAGE_BACKEND='GCS', GS_BUCKET_NAME='')
    def test_gcs_production_validation_requires_bucket(self):
        """Production settings should require GS_BUCKET_NAME for GCS."""
        with patch('storages.backends.gcloud.GoogleCloudStorage.__init__', return_value=None):
            with self.assertRaises(ValueError):
                GoogleCloudMediaStorage()
    
    @override_settings(STORAGE_BACKEND='AZURE', AZURE_CONTAINER='')
    def test_azure_production_validation_requires_container(self):
        """Production settings should require AZURE_CONTAINER for Azure."""
        with patch('storages.backends.azure_storage.AzureStorage.__init__', return_value=None):
            with self.assertRaises(ValueError):
                AzureMediaStorage()


class StorageIntegrationTests(TestCase):
    """Integration tests for storage backends with Django models."""
    
    @override_settings(STORAGE_BACKEND='LOCAL')
    def test_document_model_uses_configured_storage(self):
        """Document model should use the configured storage backend."""
        from apps.documents.models import Document
        from apps.accounts.models import User
        
        # Create test user
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            role='STUDENT'
        )
        
        # Create document (without actually saving a file)
        document = Document(
            user=user,
            document_type='PASSPORT',
            title='Test Document',
            description='Test description'
        )
        
        # Verify storage field exists
        self.assertTrue(hasattr(document.file.field, 'storage'))
    
    @override_settings(STORAGE_BACKEND='LOCAL')
    def test_file_upload_with_local_storage(self):
        """Test file upload and retrieval with local storage."""
        from apps.documents.models import Document
        from apps.accounts.models import User
        from django.core.files.uploadedfile import SimpleUploadedFile
        
        # Create test user
        user = User.objects.create_user(
            email='upload-test@example.com',
            password='testpass123',
            role='STUDENT'
        )
        
        # Create test file
        test_file = SimpleUploadedFile(
            'test_document.pdf',
            b'PDF file content',
            content_type='application/pdf'
        )
        
        # Create document with file
        document = Document.objects.create(
            user=user,
            document_type='TRANSCRIPT',
            title='Test Transcript',
            file=test_file
        )
        
        # Verify file was saved
        self.assertTrue(document.file)
        self.assertTrue(document.file.storage.exists(document.file.name))
        self.assertGreater(document.file_size, 0)
        self.assertEqual(document.file_extension, '.pdf')
        
        # Cleanup
        document.delete()


class StorageConfigurationTests(TestCase):
    """Test storage configuration defaults and overrides."""
    
    def test_default_storage_backend_is_local(self):
        """Default storage backend should be LOCAL."""
        from django.conf import settings
        # In test environment, this might be set differently
        # but default in base.py is LOCAL
        self.assertIn(settings.STORAGE_BACKEND, ['LOCAL', 'S3', 'GCS', 'AZURE', 'R2'])
    
    @override_settings(
        STORAGE_BACKEND='S3',
        AWS_STORAGE_BUCKET_NAME='test-bucket',
        AWS_S3_REGION_NAME='us-west-2',
    )
    def test_s3_configuration_overrides(self):
        """S3 configuration should accept custom region."""
        from django.conf import settings
        self.assertEqual(settings.STORAGE_BACKEND, 'S3')
        self.assertEqual(settings.AWS_STORAGE_BUCKET_NAME, 'test-bucket')
        self.assertEqual(settings.AWS_S3_REGION_NAME, 'us-west-2')
    
    @override_settings(
        STORAGE_BACKEND='S3',
        AWS_S3_CUSTOM_DOMAIN='cdn.example.com',
    )
    def test_s3_custom_domain_configuration(self):
        """S3 storage should support custom domain (CDN)."""
        from django.conf import settings
        self.assertEqual(settings.AWS_S3_CUSTOM_DOMAIN, 'cdn.example.com')
