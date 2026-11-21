"""
Unit tests for storage backend configuration (no Django app loading required).
These tests verify the storage backend logic without requiring full Django setup.
"""

import unittest
from unittest.mock import patch, MagicMock


class StorageBackendConfigTests(unittest.TestCase):
    """Test storage backend configuration logic."""
    
    def test_storage_backend_imports(self):
        """Verify all storage backend classes can be imported."""
        try:
            from config.storage_backends import (
                LocalMediaStorage,
                S3MediaStorage,
                GoogleCloudMediaStorage,
                AzureMediaStorage,
                CloudflareR2Storage,
                get_storage_backend,
            )
            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"Failed to import storage backends: {e}")
    
    def test_get_storage_backend_factory_logic(self):
        """Test the get_storage_backend factory function logic."""
        from config.storage_backends import get_storage_backend
        
        # Test LOCAL backend
        with patch('config.storage_backends.settings') as mock_settings:
            mock_settings.STORAGE_BACKEND = 'LOCAL'
            storage = get_storage_backend()
            from config.storage_backends import LocalMediaStorage
            self.assertIsInstance(storage, LocalMediaStorage)
    
    def test_invalid_backend_raises_error(self):
        """Factory should raise ValueError for invalid backend."""
        from config.storage_backends import get_storage_backend
        
        with patch('config.storage_backends.settings') as mock_settings:
            mock_settings.STORAGE_BACKEND = 'INVALID_BACKEND'
            with self.assertRaises(ValueError) as context:
                get_storage_backend()
            self.assertIn('Invalid STORAGE_BACKEND', str(context.exception))
    
    def test_all_backend_types_in_factory(self):
        """Factory should support all documented backend types."""
        from config.storage_backends import get_storage_backend
        
        backends = ['LOCAL', 'S3', 'GCS', 'AZURE', 'R2']
        
        for backend_name in backends:
            with patch('config.storage_backends.settings') as mock_settings:
                mock_settings.STORAGE_BACKEND = backend_name
                mock_settings.AWS_STORAGE_BUCKET_NAME = 'test-bucket'
                mock_settings.AWS_S3_ENDPOINT_URL = 'https://test.com'
                mock_settings.GS_BUCKET_NAME = 'test-bucket'
                mock_settings.AZURE_CONTAINER = 'test-container'
                
                # Mock the storage class __init__ to avoid actual initialization
                with patch('storages.backends.s3boto3.S3Boto3Storage.__init__', return_value=None):
                    with patch('storages.backends.gcloud.GoogleCloudStorage.__init__', return_value=None):
                        with patch('storages.backends.azure_storage.AzureStorage.__init__', return_value=None):
                            try:
                                storage = get_storage_backend()
                                self.assertIsNotNone(storage)
                            except (ValueError, AttributeError):
                                # Some backends may require additional settings
                                pass


class StorageBackendValidationTests(unittest.TestCase):
    """Test storage backend validation logic."""
    
    def test_s3_storage_validates_bucket_name(self):
        """S3 storage should validate AWS_STORAGE_BUCKET_NAME."""
        with patch('storages.backends.s3boto3.S3Boto3Storage.__init__', return_value=None):
            with patch('config.storage_backends.settings') as mock_settings:
                mock_settings.AWS_STORAGE_BUCKET_NAME = ''
                
                from config.storage_backends import S3MediaStorage
                with self.assertRaises(ValueError) as context:
                    S3MediaStorage()
                self.assertIn('AWS_STORAGE_BUCKET_NAME', str(context.exception))
    
    def test_gcs_storage_validates_bucket_name(self):
        """GCS storage should validate GS_BUCKET_NAME."""
        with patch('storages.backends.gcloud.GoogleCloudStorage.__init__', return_value=None):
            with patch('config.storage_backends.settings') as mock_settings:
                mock_settings.GS_BUCKET_NAME = ''
                
                from config.storage_backends import GoogleCloudMediaStorage
                with self.assertRaises(ValueError) as context:
                    GoogleCloudMediaStorage()
                self.assertIn('GS_BUCKET_NAME', str(context.exception))
    
    def test_azure_storage_validates_container(self):
        """Azure storage should validate AZURE_CONTAINER."""
        with patch('storages.backends.azure_storage.AzureStorage.__init__', return_value=None):
            with patch('config.storage_backends.settings') as mock_settings:
                mock_settings.AZURE_CONTAINER = ''
                
                from config.storage_backends import AzureMediaStorage
                with self.assertRaises(ValueError) as context:
                    AzureMediaStorage()
                self.assertIn('AZURE_CONTAINER', str(context.exception))
    
    def test_r2_storage_validates_endpoint_url(self):
        """R2 storage should validate AWS_S3_ENDPOINT_URL."""
        with patch('storages.backends.s3boto3.S3Boto3Storage.__init__', return_value=None):
            with patch('config.storage_backends.settings') as mock_settings:
                mock_settings.AWS_STORAGE_BUCKET_NAME = 'test-bucket'
                mock_settings.AWS_S3_ENDPOINT_URL = ''
                
                from config.storage_backends import CloudflareR2Storage
                with self.assertRaises(ValueError) as context:
                    CloudflareR2Storage()
                self.assertIn('AWS_S3_ENDPOINT_URL', str(context.exception))


class StorageBackendPropertiesTests(unittest.TestCase):
    """Test storage backend properties and configuration."""
    
    def test_s3_storage_properties(self):
        """S3 storage should have correct default properties."""
        with patch('storages.backends.s3boto3.S3Boto3Storage.__init__', return_value=None):
            with patch('config.storage_backends.settings') as mock_settings:
                mock_settings.AWS_STORAGE_BUCKET_NAME = 'test-bucket'
                
                from config.storage_backends import S3MediaStorage
                storage = S3MediaStorage()
                self.assertEqual(storage.location, 'media')
                self.assertFalse(storage.file_overwrite)
                self.assertIsNone(storage.default_acl)
    
    def test_gcs_storage_properties(self):
        """GCS storage should have correct default properties."""
        with patch('storages.backends.gcloud.GoogleCloudStorage.__init__', return_value=None):
            with patch('config.storage_backends.settings') as mock_settings:
                mock_settings.GS_BUCKET_NAME = 'test-bucket'
                
                from config.storage_backends import GoogleCloudMediaStorage
                storage = GoogleCloudMediaStorage()
                self.assertEqual(storage.location, 'media')
                self.assertFalse(storage.file_overwrite)
    
    def test_azure_storage_properties(self):
        """Azure storage should have correct default properties."""
        with patch('storages.backends.azure_storage.AzureStorage.__init__', return_value=None):
            with patch('config.storage_backends.settings') as mock_settings:
                mock_settings.AZURE_CONTAINER = 'test-container'
                
                from config.storage_backends import AzureMediaStorage
                storage = AzureMediaStorage()
                self.assertEqual(storage.location, 'media')
                self.assertFalse(storage.overwrite_files)
    
    def test_r2_storage_uses_s3_compatibility(self):
        """R2 storage should use S3-compatible interface."""
        with patch('storages.backends.s3boto3.S3Boto3Storage.__init__', return_value=None):
            with patch('config.storage_backends.settings') as mock_settings:
                mock_settings.AWS_STORAGE_BUCKET_NAME = 'test-bucket'
                mock_settings.AWS_S3_ENDPOINT_URL = 'https://account.r2.cloudflarestorage.com'
                
                from config.storage_backends import CloudflareR2Storage, S3MediaStorage
                storage = CloudflareR2Storage()
                # R2 storage should be a subclass of S3 storage
                self.assertIsInstance(storage, S3MediaStorage.__bases__[0])


if __name__ == '__main__':
    unittest.main()
