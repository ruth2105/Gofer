"""
Tests for health check endpoints.
"""

from unittest.mock import patch, MagicMock
from django.test import TestCase, override_settings
from django.urls import reverse
from django.db import OperationalError
import json


class LivenessViewTests(TestCase):
    """Tests for liveness probe endpoint."""
    
    def test_liveness_returns_200(self):
        """Liveness endpoint should always return 200 if process is running."""
        response = self.client.get('/api/v1/health/liveness/')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'alive')
        self.assertIn('timestamp', data)
    
    def test_liveness_does_not_check_database(self):
        """Liveness should not depend on database availability."""
        # Mock database failure
        with patch('django.db.connection.cursor') as mock_cursor:
            mock_cursor.side_effect = OperationalError('Database unavailable')
            
            # Liveness should still return 200
            response = self.client.get('/api/v1/health/liveness/')
            self.assertEqual(response.status_code, 200)


class ReadinessViewTests(TestCase):
    """Tests for readiness probe endpoint."""
    
    def test_readiness_returns_200_when_database_available(self):
        """Readiness should return 200 when database is accessible."""
        response = self.client.get('/api/v1/health/readiness/')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'ready')
        self.assertEqual(data['checks']['application'], 'ok')
        self.assertEqual(data['checks']['database'], 'ok')
        self.assertIn('timestamp', data)
    
    def test_readiness_returns_503_when_database_unavailable(self):
        """Readiness should return 503 when database is not accessible."""
        with patch('django.db.connection.cursor') as mock_cursor:
            mock_cursor.side_effect = OperationalError('Database unavailable')
            
            response = self.client.get('/api/v1/health/readiness/')
            
            self.assertEqual(response.status_code, 503)
            data = json.loads(response.content)
            self.assertEqual(data['status'], 'not_ready')
            self.assertEqual(data['checks']['application'], 'ok')
            self.assertEqual(data['checks']['database'], 'error')
    
    def test_readiness_does_not_expose_database_credentials(self):
        """Readiness check should not expose connection details in response."""
        with patch('django.db.connection.cursor') as mock_cursor:
            mock_cursor.side_effect = OperationalError(
                'FATAL: password authentication failed for user "secret_user"'
            )
            
            response = self.client.get('/api/v1/health/readiness/')
            content = response.content.decode('utf-8')
            
            # Response should not contain database credentials
            self.assertNotIn('secret_user', content)
            self.assertNotIn('password', content)
            self.assertNotIn('FATAL', content)


class HealthViewTests(TestCase):
    """Tests for comprehensive health check endpoint."""
    
    def test_health_returns_200_when_all_checks_pass(self):
        """Health endpoint should return 200 when all checks pass."""
        response = self.client.get('/api/v1/health/')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'healthy')
        self.assertIn('checks', data)
        self.assertIn('application', data['checks'])
        self.assertIn('database', data['checks'])
        self.assertEqual(data['checks']['application']['status'], 'healthy')
        self.assertEqual(data['checks']['database']['status'], 'healthy')
        self.assertIn('timestamp', data)
    
    def test_health_returns_503_when_database_fails(self):
        """Health endpoint should return 503 when database check fails."""
        with patch('django.db.connection.cursor') as mock_cursor:
            mock_cursor.side_effect = OperationalError('Database unavailable')
            
            response = self.client.get('/api/v1/health/')
            
            self.assertEqual(response.status_code, 503)
            data = json.loads(response.content)
            self.assertEqual(data['status'], 'unhealthy')
            self.assertEqual(data['checks']['application']['status'], 'healthy')
            self.assertEqual(data['checks']['database']['status'], 'unhealthy')
    
    def test_health_includes_database_response_time(self):
        """Health check should include database response time when successful."""
        response = self.client.get('/api/v1/health/')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('response_time_ms', data['checks']['database'])
        self.assertIsInstance(data['checks']['database']['response_time_ms'], (int, float))
        # Response time should be >= 0 (very fast queries can be 0.0)
        self.assertGreaterEqual(data['checks']['database']['response_time_ms'], 0)
    
    def test_health_returns_degraded_for_slow_database(self):
        """Health check should detect degraded database performance."""
        # Mock the _check_database method directly to return degraded status
        from unittest.mock import MagicMock
        from apps.health.views import HealthView
        
        with patch.object(HealthView, '_check_database') as mock_check_db:
            mock_check_db.return_value = {
                'status': 'degraded',
                'message': 'Database responding slowly (1500ms)',
                'response_time_ms': 1500.0,
            }
            
            response = self.client.get('/api/v1/health/')
            
            # Should return 503 for degraded (counts as unhealthy)
            self.assertEqual(response.status_code, 503)
            data = json.loads(response.content)
            self.assertEqual(data['checks']['database']['status'], 'degraded')
            self.assertIn('slowly', data['checks']['database']['message'])
    
    def test_health_does_not_expose_secrets(self):
        """Health check should not expose sensitive information."""
        with patch('django.db.connection.cursor') as mock_cursor:
            # Simulate error with sensitive information
            mock_cursor.side_effect = OperationalError(
                'connection failed: postgresql://user:password123@host:5432/dbname'
            )
            
            response = self.client.get('/api/v1/health/')
            content = response.content.decode('utf-8')
            
            # Response should not contain credentials or connection strings
            self.assertNotIn('password123', content)
            self.assertNotIn('postgresql://', content)
            self.assertNotIn(':5432', content)
    
    def test_health_logs_failures(self):
        """Health check should log when checks fail."""
        with patch('django.db.connection.cursor') as mock_cursor:
            mock_cursor.side_effect = OperationalError('Database error')
            
            with self.assertLogs('apps.health.views', level='WARNING') as logs:
                self.client.get('/api/v1/health/')
                
                # Should log the health check failure
                self.assertTrue(
                    any('Health check failed' in log for log in logs.output)
                )
