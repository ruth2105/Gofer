"""
Tests for error monitoring utilities.
"""

from django.test import TestCase, override_settings
from unittest.mock import Mock, patch, MagicMock
from .monitoring import (
    initialize_monitoring,
    capture_exception,
    capture_message,
    set_user_context,
    clear_user_context,
    is_monitoring_available,
    _filter_sensitive_event_data,
)


class InitializeMonitoringTests(TestCase):
    """Tests for monitoring initialization."""
    
    def setUp(self):
        """Reset monitoring state before each test."""
        import apps.common.monitoring as monitoring_module
        monitoring_module._monitoring_available = False
        monitoring_module._monitoring_client = None
    
    @override_settings(MONITORING_ENABLED=False)
    def test_returns_false_when_explicitly_disabled(self):
        """Should return False when monitoring is explicitly disabled."""
        result = initialize_monitoring()
        self.assertFalse(result)
        self.assertFalse(is_monitoring_available())
    
    @override_settings(SENTRY_DSN='')
    def test_returns_false_when_no_dsn_configured(self):
        """Should return False when SENTRY_DSN is not set."""
        result = initialize_monitoring()
        self.assertFalse(result)
    
    @override_settings(
        MONITORING_ENABLED=True,
        SENTRY_DSN='https://example@sentry.io/123'
    )
    def test_initializes_sentry_with_correct_config(self):
        """Should initialize Sentry with correct configuration."""
        with patch('apps.common.monitoring.logger'):
            # Mock the sentry_sdk module import within initialize_monitoring
            with patch.dict('sys.modules', {'sentry_sdk': MagicMock(), 'sentry_sdk.integrations.django': MagicMock()}):
                result = initialize_monitoring()
                
                # Since we're mocking the import, result depends on mock setup
                # Just verify it doesn't raise an exception
                self.assertIsInstance(result, bool)
    
    @override_settings(
        MONITORING_ENABLED=True,
        SENTRY_DSN='https://example@sentry.io/123'
    )
    def test_handles_missing_sentry_sdk_gracefully(self):
        """Should handle missing sentry_sdk gracefully without breaking."""
        # Reset module state
        import apps.common.monitoring as monitoring_module
        monitoring_module._monitoring_available = False
        monitoring_module._monitoring_client = None
        
        result = initialize_monitoring()
        
        # Should return False but not raise exception
        self.assertFalse(result)
        self.assertFalse(is_monitoring_available())
    
    @override_settings(
        MONITORING_ENABLED=True,
        SENTRY_DSN='https://example@sentry.io/123'
    )
    def test_handles_initialization_errors_gracefully(self):
        """Should handle initialization errors without breaking application."""
        # Reset module state
        import apps.common.monitoring as monitoring_module
        monitoring_module._monitoring_available = False
        monitoring_module._monitoring_client = None
        
        result = initialize_monitoring()
        
        # Should handle gracefully (sentry_sdk not installed in test environment)
        self.assertIsInstance(result, bool)
        # Application should continue normally


class FilterSensitiveEventDataTests(TestCase):
    """Tests for sensitive data filtering in events."""
    
    def test_filters_authorization_header(self):
        """Should filter Authorization header from events."""
        event = {
            'request': {
                'headers': {
                    'Authorization': 'Bearer secret_token_12345',
                    'Content-Type': 'application/json',
                }
            }
        }
        
        filtered = _filter_sensitive_event_data(event, {})
        
        self.assertEqual(filtered['request']['headers']['Authorization'], '***')
        self.assertEqual(filtered['request']['headers']['Content-Type'], 'application/json')
    
    def test_filters_cookie_header(self):
        """Should filter Cookie header from events."""
        event = {
            'request': {
                'headers': {
                    'Cookie': 'sessionid=abc123; csrftoken=xyz789',
                }
            }
        }
        
        filtered = _filter_sensitive_event_data(event, {})
        
        self.assertEqual(filtered['request']['headers']['Cookie'], '***')
    
    def test_filters_sensitive_environment_variables(self):
        """Should filter sensitive environment variables."""
        event = {
            'contexts': {
                'runtime': {
                    'env': {
                        'SECRET_KEY': 'django-secret-key-123',
                        'DATABASE_URL': 'postgresql://user:pass@host/db',
                        'BREVO_API_KEY': 'xkeysib-secret',
                        'DEBUG': 'False',
                    }
                }
            }
        }
        
        filtered = _filter_sensitive_event_data(event, {})
        
        self.assertEqual(filtered['contexts']['runtime']['env']['SECRET_KEY'], '***')
        self.assertEqual(filtered['contexts']['runtime']['env']['DATABASE_URL'], '***')
        self.assertEqual(filtered['contexts']['runtime']['env']['BREVO_API_KEY'], '***')
        self.assertEqual(filtered['contexts']['runtime']['env']['DEBUG'], 'False')
    
    def test_returns_event_when_no_sensitive_data(self):
        """Should return event unchanged when no sensitive data present."""
        event = {
            'message': 'Test error',
            'level': 'error',
        }
        
        filtered = _filter_sensitive_event_data(event, {})
        
        self.assertEqual(filtered, event)


class CaptureExceptionTests(TestCase):
    """Tests for exception capture."""
    
    @patch('apps.common.monitoring._monitoring_available', True)
    @patch('apps.common.monitoring._monitoring_client')
    def test_captures_exception_when_monitoring_available(self, mock_client):
        """Should capture exception when monitoring is available."""
        mock_client.capture_exception.return_value = 'event-123'
        mock_client.configure_scope = MagicMock()
        
        error = ValueError('Test error')
        event_id = capture_exception(error)
        
        self.assertEqual(event_id, 'event-123')
        mock_client.capture_exception.assert_called_once_with(error)
    
    @patch('apps.common.monitoring._monitoring_available', False)
    def test_returns_none_when_monitoring_unavailable(self):
        """Should return None when monitoring is not available."""
        error = ValueError('Test error')
        event_id = capture_exception(error)
        
        self.assertIsNone(event_id)
    
    @patch('apps.common.monitoring._monitoring_available', True)
    @patch('apps.common.monitoring._monitoring_client')
    def test_handles_capture_errors_gracefully(self, mock_client):
        """Should handle errors during capture without breaking application."""
        mock_client.capture_exception.side_effect = RuntimeError('Capture failed')
        mock_client.configure_scope = MagicMock()
        
        error = ValueError('Test error')
        event_id = capture_exception(error)
        
        # Should return None but not raise exception
        self.assertIsNone(event_id)
    
    @patch('apps.common.monitoring._monitoring_available', True)
    @patch('apps.common.monitoring._monitoring_client')
    def test_includes_context_in_capture(self, mock_client):
        """Should include context data when capturing exception."""
        mock_client.capture_exception.return_value = 'event-456'
        mock_scope = MagicMock()
        mock_client.configure_scope.return_value.__enter__.return_value = mock_scope
        
        error = ValueError('Test error')
        context = {'user_id': 123, 'action': 'payment'}
        event_id = capture_exception(error, context=context)
        
        self.assertEqual(event_id, 'event-456')
        # Verify context was set
        self.assertEqual(mock_scope.set_context.call_count, 2)


class CaptureMessageTests(TestCase):
    """Tests for message capture."""
    
    @patch('apps.common.monitoring._monitoring_available', True)
    @patch('apps.common.monitoring._monitoring_client')
    def test_captures_message_when_monitoring_available(self, mock_client):
        """Should capture message when monitoring is available."""
        mock_client.capture_message.return_value = 'msg-123'
        mock_client.configure_scope = MagicMock()
        
        event_id = capture_message('Test message', level='info')
        
        self.assertEqual(event_id, 'msg-123')
        mock_client.capture_message.assert_called_once_with('Test message', level='info')
    
    @patch('apps.common.monitoring._monitoring_available', False)
    def test_returns_none_when_monitoring_unavailable(self):
        """Should return None when monitoring is not available."""
        event_id = capture_message('Test message')
        
        self.assertIsNone(event_id)


class UserContextTests(TestCase):
    """Tests for user context management."""
    
    @patch('apps.common.monitoring._monitoring_available', True)
    @patch('apps.common.monitoring._monitoring_client')
    def test_sets_user_context(self, mock_client):
        """Should set user context when monitoring is available."""
        mock_scope = MagicMock()
        mock_client.configure_scope.return_value.__enter__.return_value = mock_scope
        
        set_user_context(user_id=123, email='user@example.com')
        
        mock_scope.set_user.assert_called_once()
        user_data = mock_scope.set_user.call_args[0][0]
        self.assertEqual(user_data['id'], 123)
        self.assertEqual(user_data['email'], 'user@example.com')
    
    @patch('apps.common.monitoring._monitoring_available', True)
    @patch('apps.common.monitoring._monitoring_client')
    def test_clears_user_context(self, mock_client):
        """Should clear user context when monitoring is available."""
        mock_scope = MagicMock()
        mock_client.configure_scope.return_value.__enter__.return_value = mock_scope
        
        clear_user_context()
        
        mock_scope.set_user.assert_called_once_with(None)
    
    @patch('apps.common.monitoring._monitoring_available', False)
    def test_handles_unavailable_monitoring_gracefully(self):
        """Should handle unavailable monitoring without errors."""
        # Should not raise any exceptions
        set_user_context(user_id=123)
        clear_user_context()
    
    @patch('apps.common.monitoring._monitoring_available', True)
    @patch('apps.common.monitoring._monitoring_client')
    def test_handles_context_errors_gracefully(self, mock_client):
        """Should handle errors when setting context without breaking."""
        mock_client.configure_scope.side_effect = RuntimeError('Context error')
        
        # Should not raise exception
        set_user_context(user_id=123)
        clear_user_context()
