"""
URL patterns for authentication.
"""

from django.urls import path
from .views import (
    UserRegistrationView,
    UserLoginView,
    UserLogoutView,
    CookieTokenRefreshView,
    CurrentUserView,
    csrf_token,
    EmailVerificationView,
    ResendVerificationEmailView,
    PasswordResetRequestView,
    PasswordResetConfirmView,
    PasswordChangeView,
    ManagedUserListView,
    ManagedUserDetailView,
    SecurityAuditEventListView,
)

app_name = 'accounts'

urlpatterns = [
    # Authentication
    path('csrf/', csrf_token, name='csrf_token'),
    path('register/', UserRegistrationView.as_view(), name='register'),
    path('verify-email/', EmailVerificationView.as_view(), name='verify_email'),
    path('resend-verification/', ResendVerificationEmailView.as_view(), name='resend_verification'),
    path('login/', UserLoginView.as_view(), name='login'),
    path('logout/', UserLogoutView.as_view(), name='logout'),
    path('token/refresh/', CookieTokenRefreshView.as_view(), name='token_refresh'),
    path('password/reset/', PasswordResetRequestView.as_view(), name='password_reset_request'),
    path('password/reset/confirm/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('password/change/', PasswordChangeView.as_view(), name='password_change'),
    path('users/', ManagedUserListView.as_view(), name='managed_users'),
    path('users/<uuid:user_id>/', ManagedUserDetailView.as_view(), name='managed_user_detail'),
    path('security/audit/', SecurityAuditEventListView.as_view(), name='security_audit'),
    
    # User Profile
    path('me/', CurrentUserView.as_view(), name='current_user'),
]
