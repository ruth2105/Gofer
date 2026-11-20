"""
URL patterns for health check endpoints.
"""

from django.urls import path
from .views import LivenessView, ReadinessView, HealthView

urlpatterns = [
    path('liveness/', LivenessView.as_view(), name='health-liveness'),
    path('readiness/', ReadinessView.as_view(), name='health-readiness'),
    path('', HealthView.as_view(), name='health-check'),
]
