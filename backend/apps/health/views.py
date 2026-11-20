"""
Health check views for monitoring application and service availability.

Provides endpoints for:
- Liveness probe: Basic application availability
- Readiness probe: Application + database connectivity
- Health check: Comprehensive service status
"""

import logging
from django.db import connection
from django.http import JsonResponse
from django.views import View
from django.utils import timezone

logger = logging.getLogger(__name__)


class LivenessView(View):
    """
    Liveness probe endpoint.
    
    Returns 200 if the application process is running.
    Does NOT check database or external dependencies.
    
    Used by container orchestrators to determine if the process should be restarted.
    """
    
    def get(self, request):
        """Return basic liveness status."""
        return JsonResponse({
            'status': 'alive',
            'timestamp': timezone.now().isoformat(),
        })


class ReadinessView(View):
    """
    Readiness probe endpoint.
    
    Returns 200 if the application is ready to serve traffic.
    Checks:
    - Application is running
    - Database is accessible
    
    Used by load balancers to determine if traffic should be routed to this instance.
    """
    
    def get(self, request):
        """Check if application is ready to serve requests."""
        status = 'ready'
        http_status = 200
        checks = {
            'application': 'ok',
            'database': 'unknown',
        }
        
        # Check database connectivity
        try:
            with connection.cursor() as cursor:
                cursor.execute('SELECT 1')
                cursor.fetchone()
            checks['database'] = 'ok'
        except Exception as error:
            checks['database'] = 'error'
            status = 'not_ready'
            http_status = 503
            logger.error(
                'Database readiness check failed',
                extra={
                    'check': 'database',
                    'error_type': type(error).__name__,
                },
                exc_info=False,  # Don't include traceback (may contain connection details)
            )
        
        return JsonResponse({
            'status': status,
            'checks': checks,
            'timestamp': timezone.now().isoformat(),
        }, status=http_status)


class HealthView(View):
    """
    Comprehensive health check endpoint.
    
    Returns detailed service status including:
    - Application status
    - Database connectivity and performance
    - Optional: Additional service dependencies
    
    Returns:
    - 200: All checks passed (healthy)
    - 503: One or more checks failed (unhealthy)
    
    Security:
    - Does NOT expose database credentials
    - Does NOT expose internal infrastructure details
    - Does NOT expose sensitive configuration
    """
    
    def get(self, request):
        """Perform comprehensive health checks."""
        all_checks_passed = True
        checks = {}
        
        # Application check (always passes if we reach here)
        checks['application'] = {
            'status': 'healthy',
            'message': 'Application is running',
        }
        
        # Database check
        db_check = self._check_database()
        checks['database'] = db_check
        if db_check['status'] != 'healthy':
            all_checks_passed = False
        
        # Overall status
        overall_status = 'healthy' if all_checks_passed else 'unhealthy'
        http_status = 200 if all_checks_passed else 503
        
        response_data = {
            'status': overall_status,
            'timestamp': timezone.now().isoformat(),
            'checks': checks,
        }
        
        # Log unhealthy status
        if not all_checks_passed:
            logger.warning(
                'Health check failed',
                extra={
                    'status': overall_status,
                    'failed_checks': [
                        name for name, check in checks.items()
                        if check['status'] != 'healthy'
                    ],
                },
            )
        
        return JsonResponse(response_data, status=http_status)
    
    def _check_database(self):
        """
        Check database connectivity and basic performance.
        
        Returns dict with:
        - status: 'healthy', 'degraded', or 'unhealthy'
        - message: Human-readable status description
        - response_time_ms: Query execution time (if successful)
        """
        import time
        
        try:
            start_time = time.time()
            
            # Simple connectivity check
            with connection.cursor() as cursor:
                cursor.execute('SELECT 1')
                result = cursor.fetchone()
            
            response_time = (time.time() - start_time) * 1000  # Convert to ms
            
            # Basic performance check
            if response_time > 1000:  # > 1 second is degraded
                return {
                    'status': 'degraded',
                    'message': f'Database responding slowly ({response_time:.0f}ms)',
                    'response_time_ms': round(response_time, 2),
                }
            
            return {
                'status': 'healthy',
                'message': 'Database is accessible',
                'response_time_ms': round(response_time, 2),
            }
            
        except Exception as error:
            logger.error(
                'Database health check failed',
                extra={
                    'error_type': type(error).__name__,
                },
                exc_info=False,  # Avoid logging connection strings
            )
            
            return {
                'status': 'unhealthy',
                'message': 'Database connection failed',
                'error_type': type(error).__name__,
            }
