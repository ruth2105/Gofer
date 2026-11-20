"""
Logging utilities for safe, structured logging.

Provides utilities for:
- Safe exception logging (filters sensitive data)
- Request correlation
- Consistent log formatting
- Sensitive data filtering
"""

import logging
import re
from typing import Any, Dict, Optional

# Sensitive patterns to filter from logs
SENSITIVE_PATTERNS = [
    # Passwords and tokens
    (re.compile(r'password["\']?\s*[:=]\s*["\']?([^"\'\s,}]+)', re.IGNORECASE), 'password=***'),
    (re.compile(r'token["\']?\s*[:=]\s*["\']?([^"\'\s,}]+)', re.IGNORECASE), 'token=***'),
    (re.compile(r'api[_-]?key["\']?\s*[:=]\s*["\']?([^"\'\s,}]+)', re.IGNORECASE), 'api_key=***'),
    (re.compile(r'secret["\']?\s*[:=]\s*["\']?([^"\'\s,}]+)', re.IGNORECASE), 'secret=***'),
    (re.compile(r'authorization["\']?\s*[:=]\s*["\']?([^"\'\s,}]+)', re.IGNORECASE), 'authorization=***'),
    
    # Database connection strings
    (re.compile(r'postgresql://[^:]+:([^@]+)@', re.IGNORECASE), 'postgresql://user:***@'),
    (re.compile(r'mysql://[^:]+:([^@]+)@', re.IGNORECASE), 'mysql://user:***@'),
    
    # Email addresses in certain contexts (preserve in user-facing logs, filter in error details)
    (re.compile(r'EMAIL_HOST_PASSWORD["\']?\s*[:=]\s*["\']?([^"\'\s,}]+)', re.IGNORECASE), 'EMAIL_HOST_PASSWORD=***'),
    
    # Cookie values
    (re.compile(r'Cookie:\s*([^\n]+)', re.IGNORECASE), 'Cookie: ***'),
    (re.compile(r'Set-Cookie:\s*([^\n]+)', re.IGNORECASE), 'Set-Cookie: ***'),
]


def filter_sensitive_data(text: str) -> str:
    """
    Filter sensitive information from log messages.
    
    Args:
        text: Log message that may contain sensitive data
        
    Returns:
        Filtered message with sensitive data replaced
    """
    if not text:
        return text
    
    filtered = text
    for pattern, replacement in SENSITIVE_PATTERNS:
        filtered = pattern.sub(replacement, filtered)
    
    return filtered


def safe_log_exception(
    logger: logging.Logger,
    message: str,
    exc_info: bool = True,
    extra: Optional[Dict[str, Any]] = None,
    level: int = logging.ERROR,
):
    """
    Log an exception with sensitive data filtered.
    
    Args:
        logger: Logger instance to use
        message: Human-readable error message
        exc_info: Whether to include exception traceback
        extra: Additional context (will be filtered)
        level: Log level (default: ERROR)
    
    Example:
        try:
            process_payment(card_number='1234-5678-9012-3456')
        except Exception as e:
            safe_log_exception(
                logger,
                'Payment processing failed',
                extra={'user_id': user.id, 'amount': 100.00}
            )
    """
    # Filter message
    filtered_message = filter_sensitive_data(message)
    
    # Filter extra context
    filtered_extra = {}
    if extra:
        for key, value in extra.items():
            if isinstance(value, str):
                filtered_extra[key] = filter_sensitive_data(value)
            else:
                filtered_extra[key] = value
    
    # Log with appropriate level
    logger.log(
        level,
        filtered_message,
        exc_info=exc_info,
        extra=filtered_extra,
    )


def get_request_id(request) -> Optional[str]:
    """
    Extract or generate request ID for correlation.
    
    Args:
        request: Django request object
        
    Returns:
        Request ID string, or None if not available
    """
    # Check for X-Request-ID header (common in load balancers)
    request_id = request.META.get('HTTP_X_REQUEST_ID')
    
    if not request_id:
        # Check for other common request ID headers
        request_id = (
            request.META.get('HTTP_X_CORRELATION_ID')
            or request.META.get('HTTP_REQUEST_ID')
        )
    
    return request_id


def log_api_request(
    logger: logging.Logger,
    request,
    response_status: int,
    response_time_ms: float,
):
    """
    Log API request with correlation ID and timing.
    
    Args:
        logger: Logger instance
        request: Django request object
        response_status: HTTP response status code
        response_time_ms: Response time in milliseconds
    
    Example:
        start_time = time.time()
        response = view_function(request)
        response_time = (time.time() - start_time) * 1000
        log_api_request(logger, request, response.status_code, response_time)
    """
    extra = {
        'method': request.method,
        'path': request.path,
        'status': response_status,
        'response_time_ms': round(response_time_ms, 2),
        'user_id': getattr(request.user, 'id', None) if hasattr(request, 'user') else None,
        'request_id': get_request_id(request),
    }
    
    # Log level based on status code
    if response_status >= 500:
        level = logging.ERROR
    elif response_status >= 400:
        level = logging.WARNING
    else:
        level = logging.INFO
    
    logger.log(
        level,
        f'{request.method} {request.path} {response_status} {response_time_ms:.0f}ms',
        extra=extra,
    )


def log_security_event(
    logger: logging.Logger,
    event_type: str,
    user_id: Optional[int],
    ip_address: str,
    details: Optional[Dict[str, Any]] = None,
):
    """
    Log security-relevant events for audit trail.
    
    Args:
        logger: Logger instance
        event_type: Type of security event (e.g., 'login_failed', 'permission_denied')
        user_id: User ID if authenticated, None otherwise
        ip_address: Client IP address
        details: Additional event details (will be filtered)
    
    Example:
        log_security_event(
            logger,
            'login_failed',
            user_id=None,
            ip_address=request.META['REMOTE_ADDR'],
            details={'email': 'user@example.com', 'reason': 'invalid_credentials'}
        )
    """
    extra = {
        'event_type': event_type,
        'user_id': user_id,
        'ip_address': ip_address,
    }
    
    if details:
        # Filter sensitive data from details
        filtered_details = {}
        for key, value in details.items():
            if isinstance(value, str):
                filtered_details[key] = filter_sensitive_data(value)
            else:
                filtered_details[key] = value
        extra['details'] = filtered_details
    
    logger.warning(
        f'Security event: {event_type}',
        extra=extra,
    )
