"""
Error monitoring configuration and utilities.

Supports optional integration with error monitoring services like Sentry.
Application continues to function normally when monitoring is disabled or unavailable.
"""

import logging
from typing import Optional, Dict, Any
from django.conf import settings

logger = logging.getLogger(__name__)

# Global monitoring client (initialized on first use)
_monitoring_client = None
_monitoring_available = False


def initialize_monitoring() -> bool:
    """
    Initialize error monitoring if configured.
    
    Returns:
        True if monitoring was successfully initialized, False otherwise
    
    Environment Variables:
        SENTRY_DSN: Sentry Data Source Name (optional)
        SENTRY_ENVIRONMENT: Environment name (e.g., 'production', 'staging')
        SENTRY_TRACES_SAMPLE_RATE: Performance monitoring sample rate (0.0 to 1.0)
        MONITORING_ENABLED: Explicit enable/disable flag (default: True if DSN present)
    
    Note:
        If monitoring initialization fails, the application continues normally.
        Errors are logged but do not break the application.
    """
    global _monitoring_client, _monitoring_available
    
    # Check if monitoring is explicitly disabled
    monitoring_enabled = getattr(settings, 'MONITORING_ENABLED', True)
    if not monitoring_enabled:
        logger.info('Error monitoring is explicitly disabled')
        return False
    
    # Check for Sentry DSN
    sentry_dsn = getattr(settings, 'SENTRY_DSN', None)
    if not sentry_dsn:
        logger.info('No SENTRY_DSN configured, monitoring disabled')
        return False
    
    try:
        import sentry_sdk
        from sentry_sdk.integrations.django import DjangoIntegration
        
        # Configure Sentry
        sentry_sdk.init(
            dsn=sentry_dsn,
            environment=getattr(settings, 'SENTRY_ENVIRONMENT', 'production'),
            traces_sample_rate=getattr(settings, 'SENTRY_TRACES_SAMPLE_RATE', 0.0),
            send_default_pii=False,  # Don't send personally identifiable information
            integrations=[
                DjangoIntegration(),
            ],
            # Filter sensitive data
            before_send=_filter_sensitive_event_data,
        )
        
        _monitoring_client = sentry_sdk
        _monitoring_available = True
        
        logger.info(
            'Error monitoring initialized',
            extra={
                'service': 'sentry',
                'environment': getattr(settings, 'SENTRY_ENVIRONMENT', 'production'),
            },
        )
        return True
        
    except ImportError:
        logger.warning(
            'Sentry SDK not installed. Install with: pip install sentry-sdk. '
            'Application continues without error monitoring.'
        )
        return False
        
    except Exception as error:
        logger.error(
            'Failed to initialize error monitoring',
            extra={'error_type': type(error).__name__},
            exc_info=False,
        )
        return False


def _filter_sensitive_event_data(event: Dict[str, Any], hint: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Filter sensitive data from error events before sending to monitoring service.
    
    Args:
        event: Sentry event dict
        hint: Additional context
        
    Returns:
        Filtered event, or None to drop the event entirely
    """
    # Remove sensitive headers
    if 'request' in event and 'headers' in event['request']:
        headers = event['request']['headers']
        sensitive_headers = ['Authorization', 'Cookie', 'X-Api-Key']
        for header in sensitive_headers:
            if header in headers:
                headers[header] = '***'
    
    # Remove sensitive environment variables
    if 'contexts' in event and 'runtime' in event['contexts']:
        runtime = event['contexts']['runtime']
        if 'env' in runtime:
            sensitive_env_vars = [
                'SECRET_KEY',
                'DATABASE_URL',
                'BREVO_API_KEY',
                'EMAIL_HOST_PASSWORD',
                'AWS_SECRET_ACCESS_KEY',
                'AZURE_ACCOUNT_KEY',
            ]
            for var in sensitive_env_vars:
                if var in runtime['env']:
                    runtime['env'][var] = '***'
    
    return event


def capture_exception(
    error: Exception,
    context: Optional[Dict[str, Any]] = None,
    level: str = 'error',
) -> Optional[str]:
    """
    Capture exception in monitoring service.
    
    Args:
        error: Exception to capture
        context: Additional context (user_id, request_id, etc.)
        level: Severity level ('error', 'warning', 'info')
        
    Returns:
        Event ID from monitoring service, or None if monitoring unavailable
    
    Example:
        try:
            process_payment(card_data)
        except PaymentError as e:
            event_id = capture_exception(
                e,
                context={'user_id': user.id, 'amount': 100.00}
            )
    
    Note:
        If monitoring is unavailable, this function does nothing and returns None.
        The application continues normally.
    """
    if not _monitoring_available or not _monitoring_client:
        return None
    
    try:
        # Set context if provided
        if context:
            with _monitoring_client.configure_scope() as scope:
                for key, value in context.items():
                    scope.set_context(key, value)
        
        # Capture exception
        event_id = _monitoring_client.capture_exception(error)
        return event_id
        
    except Exception as capture_error:
        # Log but don't break application if capture fails
        logger.error(
            'Failed to capture exception in monitoring service',
            extra={'error_type': type(capture_error).__name__},
            exc_info=False,
        )
        return None


def capture_message(
    message: str,
    level: str = 'info',
    context: Optional[Dict[str, Any]] = None,
) -> Optional[str]:
    """
    Capture custom message in monitoring service.
    
    Args:
        message: Message to capture
        level: Severity level ('error', 'warning', 'info', 'debug')
        context: Additional context
        
    Returns:
        Event ID from monitoring service, or None if monitoring unavailable
    
    Example:
        capture_message(
            'Daily backup completed',
            level='info',
            context={'backup_size_mb': 250, 'duration_seconds': 45}
        )
    """
    if not _monitoring_available or not _monitoring_client:
        return None
    
    try:
        # Set context if provided
        if context:
            with _monitoring_client.configure_scope() as scope:
                for key, value in context.items():
                    scope.set_context(key, value)
        
        # Capture message
        event_id = _monitoring_client.capture_message(message, level=level)
        return event_id
        
    except Exception as capture_error:
        logger.error(
            'Failed to capture message in monitoring service',
            extra={'error_type': type(capture_error).__name__},
            exc_info=False,
        )
        return None


def set_user_context(user_id: int, email: Optional[str] = None):
    """
    Set user context for error tracking.
    
    Args:
        user_id: User ID
        email: User email (optional, will be filtered if send_default_pii=False)
    
    Note:
        This associates subsequent errors with the user.
        If monitoring is unavailable, this function does nothing.
    """
    if not _monitoring_available or not _monitoring_client:
        return
    
    try:
        with _monitoring_client.configure_scope() as scope:
            user_data = {'id': user_id}
            if email:
                user_data['email'] = email
            scope.set_user(user_data)
    except Exception:
        # Silently fail if setting user context fails
        pass


def clear_user_context():
    """
    Clear user context (e.g., after logout).
    
    Note:
        If monitoring is unavailable, this function does nothing.
    """
    if not _monitoring_available or not _monitoring_client:
        return
    
    try:
        with _monitoring_client.configure_scope() as scope:
            scope.set_user(None)
    except Exception:
        pass


def is_monitoring_available() -> bool:
    """
    Check if error monitoring is available.
    
    Returns:
        True if monitoring is initialized and available, False otherwise
    """
    return _monitoring_available
