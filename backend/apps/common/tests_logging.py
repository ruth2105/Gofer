"""
Tests for logging utilities.
"""

import logging
from django.test import TestCase, RequestFactory
from unittest.mock import Mock, patch
from .logging_utils import (
    filter_sensitive_data,
    safe_log_exception,
    get_request_id,
    log_api_request,
    log_security_event,
)


class FilterSensitiveDataTests(TestCase):
    """Tests for sensitive data filtering."""
    
    def test_filters_passwords(self):
        """Should filter password values from log messages."""
        text = 'Login failed with password="secret123"'
        filtered = filter_sensitive_data(text)
        
        self.assertNotIn('secret123', filtered)
        self.assertIn('password=***', filtered)
    
    def test_filters_tokens(self):
        """Should filter token values from log messages."""
        text = 'API call failed: token=eyJhbGciOiJIUzI1NiIs'
        filtered = filter_sensitive_data(text)
        
        self.assertNotIn('eyJhbGciOiJIUzI1NiIs', filtered)
        self.assertIn('token=***', filtered)
    
    def test_filters_api_keys(self):
        """Should filter API key values from log messages."""
        text = 'Brevo error: api_key="xkeysib-1234567890abcdef"'
        filtered = filter_sensitive_data(text)
        
        self.assertNotIn('xkeysib-1234567890abcdef', filtered)
        self.assertIn('api_key=***', filtered)
    
    def test_filters_database_passwords(self):
        """Should filter database passwords from connection strings."""
        text = 'Connection failed: postgresql://user:password123@host:5432/db'
        filtered = filter_sensitive_data(text)
        
        self.assertNotIn('password123', filtered)
        self.assertIn('postgresql://user:***@', filtered)
    
    def test_filters_email_host_password(self):
        """Should filter EMAIL_HOST_PASSWORD values."""
        text = 'SMTP error: EMAIL_HOST_PASSWORD=smtp_secret_pass'
        filtered = filter_sensitive_data(text)
        
        self.assertNotIn('smtp_secret_pass', filtered)
        self.assertIn('EMAIL_HOST_PASSWORD=***', filtered)
    
    def test_filters_cookies(self):
        """Should filter cookie values from headers."""
        text = 'Request headers: Cookie: sessionid=abc123; csrftoken=xyz789'
        filtered = filter_sensitive_data(text)
        
        self.assertNotIn('sessionid=abc123', filtered)
        self.assertNotIn('csrftoken=xyz789', filtered)
        self.assertIn('Cookie: ***', filtered)
    
    def test_preserves_non_sensitive_data(self):
        """Should not filter non-sensitive information."""
        text = 'User email: user@example.com, status: active'
        filtered = filter_sensitive_data(text)
        
        # Should preserve user email and status
        self.assertIn('user@example.com', filtered)
        self.assertIn('status: active', filtered)
    
    def test_handles_none_input(self):
        """Should handle None input gracefully."""
        filtered = filter_sensitive_data(None)
        self.assertIsNone(filtered)
    
    def test_handles_empty_string(self):
        """Should handle empty string input."""
        filtered = filter_sensitive_data('')
        self.assertEqual(filtered, '')


class SafeLogExceptionTests(TestCase):
    """Tests for safe exception logging."""
    
    def test_logs_exception_with_filtered_message(self):
        """Should log exception with sensitive data filtered."""
        logger = logging.getLogger('test_logger')
        
        with self.assertLogs('test_logger', level='ERROR') as logs:
            safe_log_exception(
                logger,
                'Authentication failed with password="secret123"',
                exc_info=False,
            )
            
            # Should filter password from log output
            log_output = ''.join(logs.output)
            self.assertNotIn('secret123', log_output)
            self.assertIn('password=***', log_output)
    
    def test_logs_with_filtered_extra_context(self):
        """Should filter sensitive data from extra context."""
        logger = logging.getLogger('test_logger')
        
        with self.assertLogs('test_logger', level='ERROR') as logs:
            safe_log_exception(
                logger,
                'API call failed',
                exc_info=False,
                extra={'api_key': 'xkeysib-secret', 'user_id': 123},
            )
            
            # Should filter api_key but preserve user_id
            log_output = ''.join(logs.output)
            self.assertNotIn('xkeysib-secret', log_output)
    
    def test_supports_different_log_levels(self):
        """Should support custom log levels."""
        logger = logging.getLogger('test_logger')
        
        with self.assertLogs('test_logger', level='WARNING') as logs:
            safe_log_exception(
                logger,
                'Non-critical error',
                exc_info=False,
                level=logging.WARNING,
            )
            
            self.assertTrue(any('WARNING' in log for log in logs.output))


class GetRequestIdTests(TestCase):
    """Tests for request ID extraction."""
    
    def setUp(self):
        self.factory = RequestFactory()
    
    def test_extracts_x_request_id_header(self):
        """Should extract X-Request-ID from headers."""
        request = self.factory.get('/', HTTP_X_REQUEST_ID='req-12345')
        request_id = get_request_id(request)
        
        self.assertEqual(request_id, 'req-12345')
    
    def test_extracts_x_correlation_id_header(self):
        """Should extract X-Correlation-ID as fallback."""
        request = self.factory.get('/', HTTP_X_CORRELATION_ID='corr-67890')
        request_id = get_request_id(request)
        
        self.assertEqual(request_id, 'corr-67890')
    
    def test_returns_none_when_no_request_id(self):
        """Should return None when no request ID headers present."""
        request = self.factory.get('/')
        request_id = get_request_id(request)
        
        self.assertIsNone(request_id)


class LogApiRequestTests(TestCase):
    """Tests for API request logging."""
    
    def setUp(self):
        self.factory = RequestFactory()
        self.logger = logging.getLogger('test_api_logger')
    
    def test_logs_successful_request(self):
        """Should log successful API request at INFO level."""
        request = self.factory.get('/api/v1/scholarships/')
        request.user = Mock(id=123)
        
        with self.assertLogs('test_api_logger', level='INFO') as logs:
            log_api_request(self.logger, request, 200, 45.5)
            
            log_output = logs.output[0]
            self.assertIn('INFO', log_output)
            self.assertIn('GET', log_output)
            self.assertIn('/api/v1/scholarships/', log_output)
            self.assertIn('200', log_output)
            # Rounding may occur, so check for 45 or 46ms
            self.assertTrue('45ms' in log_output or '46ms' in log_output)
    
    def test_logs_client_error_at_warning_level(self):
        """Should log 4xx errors at WARNING level."""
        request = self.factory.get('/api/v1/invalid/')
        request.user = Mock(id=None)
        
        with self.assertLogs('test_api_logger', level='WARNING') as logs:
            log_api_request(self.logger, request, 404, 10.0)
            
            self.assertTrue(any('WARNING' in log for log in logs.output))
            self.assertTrue(any('404' in log for log in logs.output))
    
    def test_logs_server_error_at_error_level(self):
        """Should log 5xx errors at ERROR level."""
        request = self.factory.post('/api/v1/applications/')
        request.user = Mock(id=456)
        
        with self.assertLogs('test_api_logger', level='ERROR') as logs:
            log_api_request(self.logger, request, 500, 250.0)
            
            self.assertTrue(any('ERROR' in log for log in logs.output))
            self.assertTrue(any('500' in log for log in logs.output))
    
    def test_includes_request_correlation_id(self):
        """Should include request ID if present."""
        request = self.factory.get('/api/v1/health/', HTTP_X_REQUEST_ID='req-abc123')
        request.user = None
        
        # We can't easily assert on extra fields in assertLogs,
        # but we can verify the function runs without error
        with self.assertLogs('test_api_logger', level='INFO'):
            log_api_request(self.logger, request, 200, 5.0)


class LogSecurityEventTests(TestCase):
    """Tests for security event logging."""
    
    def setUp(self):
        self.logger = logging.getLogger('test_security_logger')
    
    def test_logs_security_event(self):
        """Should log security events at WARNING level."""
        with self.assertLogs('test_security_logger', level='WARNING') as logs:
            log_security_event(
                self.logger,
                'login_failed',
                user_id=None,
                ip_address='192.168.1.100',
                details={'email': 'user@example.com', 'reason': 'invalid_credentials'},
            )
            
            log_output = logs.output[0]
            self.assertIn('WARNING', log_output)
            self.assertIn('Security event: login_failed', log_output)
    
    def test_filters_sensitive_details(self):
        """Should filter sensitive information from security event details."""
        with self.assertLogs('test_security_logger', level='WARNING') as logs:
            log_security_event(
                self.logger,
                'api_abuse_detected',
                user_id=789,
                ip_address='203.0.113.42',
                details={'api_key': 'xkeysib-secret123', 'endpoint': '/api/v1/data/'},
            )
            
            # Should filter api_key but preserve endpoint
            log_output = ''.join(logs.output)
            self.assertNotIn('xkeysib-secret123', log_output)
    
    def test_handles_missing_details(self):
        """Should handle security events without additional details."""
        with self.assertLogs('test_security_logger', level='WARNING'):
            log_security_event(
                self.logger,
                'permission_denied',
                user_id=100,
                ip_address='10.0.0.1',
                details=None,
            )
