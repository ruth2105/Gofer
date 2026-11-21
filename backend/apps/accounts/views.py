"""
Views for user authentication and profile management.
"""

from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ImproperlyConfigured
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from rest_framework import status, generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from drf_spectacular.utils import extend_schema, OpenApiResponse
from django.conf import settings
from django.middleware.csrf import get_token
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from rest_framework.decorators import api_view, authentication_classes, permission_classes, throttle_classes
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.throttling import ScopedRateThrottle, AnonRateThrottle

from apps.accounts.audit import record_security_event
from apps.accounts.models import SecurityAuditEvent
from apps.common.permissions import IsAdminUser, IsSuperAdmin
from .email_verification import (
    VerificationCooldownError,
    VerificationEmailDeliveryError,
    send_verification_email,
    verify_email_token,
)
from .password_reset import PasswordResetDeliveryError, send_password_reset_email
from .models import User
from .serializers import (
    UserRegistrationSerializer,
    UserLoginSerializer,
    UserSerializer,
    UserProfileUpdateSerializer,
    EmailVerificationSerializer,
    ResendVerificationSerializer,
    PasswordResetRequestSerializer,
    PasswordResetTokenSerializer,
    PasswordResetConfirmSerializer,
    PasswordChangeSerializer,
    ManagedUserSerializer,
    SecurityAuditEventSerializer,
)


def set_auth_cookies(response, refresh_token, access_token=None):
    refresh = RefreshToken(refresh_token)
    access = access_token or str(refresh.access_token)
    response.set_cookie(
        settings.AUTH_ACCESS_COOKIE_NAME,
        access,
        max_age=int(settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'].total_seconds()),
        httponly=True,
        secure=settings.AUTH_COOKIE_SECURE,
        samesite=settings.AUTH_COOKIE_SAMESITE,
        path=settings.AUTH_ACCESS_COOKIE_PATH,
    )
    response.set_cookie(
        settings.AUTH_REFRESH_COOKIE_NAME,
        str(refresh),
        max_age=int(settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds()),
        httponly=True,
        secure=settings.AUTH_COOKIE_SECURE,
        samesite=settings.AUTH_COOKIE_SAMESITE,
        path=settings.AUTH_REFRESH_COOKIE_PATH,
    )
    response.set_cookie(
        settings.AUTH_SESSION_COOKIE_NAME,
        '1',
        max_age=int(settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds()),
        httponly=True,
        secure=settings.AUTH_COOKIE_SECURE,
        samesite=settings.AUTH_COOKIE_SAMESITE,
        path='/',
    )


def clear_auth_cookies(response):
    response.delete_cookie(
        settings.AUTH_ACCESS_COOKIE_NAME,
        path=settings.AUTH_ACCESS_COOKIE_PATH,
        samesite=settings.AUTH_COOKIE_SAMESITE,
    )
    response.delete_cookie(
        settings.AUTH_REFRESH_COOKIE_NAME,
        path=settings.AUTH_REFRESH_COOKIE_PATH,
        samesite=settings.AUTH_COOKIE_SAMESITE,
    )
    response.delete_cookie(
        settings.AUTH_SESSION_COOKIE_NAME,
        path='/',
        samesite=settings.AUTH_COOKIE_SAMESITE,
    )


def revoke_user_refresh_tokens(user):
    for token in OutstandingToken.objects.filter(user=user):
        BlacklistedToken.objects.get_or_create(token=token)


@api_view(['GET'])
@authentication_classes([])
@permission_classes([permissions.AllowAny])
@throttle_classes([AnonRateThrottle])
def csrf_token(request):
    return Response({'csrfToken': get_token(request._request)})


@method_decorator(csrf_protect, name='dispatch')
class UserRegistrationView(generics.CreateAPIView):
    """
    Register a new user account.
    Creates a STUDENT role by default.
    """
    
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]
    authentication_classes = []
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'auth_register'
    
    @extend_schema(
        tags=['Authentication'],
        summary='Register new user',
        description='Create an unverified student account and send an email-verification link.',
        responses={
            201: OpenApiResponse(description='Account created and verification email accepted'),
            400: OpenApiResponse(description='Validation error'),
            503: OpenApiResponse(description='Verification email could not be accepted'),
        }
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        try:
            send_verification_email(user)
        except VerificationEmailDeliveryError:
            return Response({
                'error': (
                    'Your account was created, but the email provider could not accept '
                    'the verification message. You can request another message from the '
                    'sign-in page.'
                ),
                'status_code': status.HTTP_503_SERVICE_UNAVAILABLE,
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except ImproperlyConfigured:
            return Response({
                'error': (
                    'Your account was created, but email delivery is not configured. '
                    'Please contact support.'
                ),
                'status_code': status.HTTP_503_SERVICE_UNAVAILABLE,
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        if settings.EMAIL_BACKEND == 'django.core.mail.backends.console.EmailBackend':
            delivery_message = (
                'Your account was created. In development, the verification message '
                'was printed to the Django console.'
            )
        else:
            delivery_message = (
                'Your account was created. The configured email backend accepted the '
                'verification message; inbox delivery is not guaranteed.'
            )

        return Response({
            'user': UserSerializer(user).data,
            'email': user.email,
            'message': delivery_message,
            'resend_cooldown_seconds': settings.EMAIL_VERIFICATION_RESEND_COOLDOWN_SECONDS,
        }, status=status.HTTP_201_CREATED)


@method_decorator(csrf_protect, name='dispatch')
class EmailVerificationView(APIView):
    """Consume a one-time email-verification token."""

    permission_classes = [permissions.AllowAny]
    authentication_classes = []
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'auth_verify'

    @extend_schema(
        tags=['Authentication'],
        summary='Verify an email address',
        request=EmailVerificationSerializer,
        responses={
            200: OpenApiResponse(description='Email verified or already verified'),
            400: OpenApiResponse(description='Invalid or expired verification token'),
        },
    )
    def post(self, request):
        serializer = EmailVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = verify_email_token(serializer.validated_data['token'])

        if result == 'verified':
            return Response({
                'status': result,
                'message': 'Your email is verified. You can now sign in.',
            }, status=status.HTTP_200_OK)
        if result == 'already_verified':
            return Response({
                'status': result,
                'message': 'This email address has already been verified. You can sign in.',
            }, status=status.HTTP_200_OK)
        if result == 'expired':
            return Response({
                'status': result,
                'error': 'This verification link has expired. Request a new one to continue.',
            }, status=status.HTTP_400_BAD_REQUEST)
        return Response({
            'status': 'invalid',
            'error': 'This verification link is invalid. Request a new one to continue.',
        }, status=status.HTTP_400_BAD_REQUEST)


@method_decorator(csrf_protect, name='dispatch')
class ResendVerificationEmailView(APIView):
    """Resend an email-verification link without revealing account status."""

    permission_classes = [permissions.AllowAny]
    authentication_classes = []
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'auth_resend'

    @extend_schema(
        tags=['Authentication'],
        summary='Resend an email-verification link',
        request=ResendVerificationSerializer,
        responses={
            202: OpenApiResponse(description='Request accepted without disclosing account status'),
            503: OpenApiResponse(description='Email provider did not accept the message'),
        },
    )
    def post(self, request):
        serializer = ResendVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = User.objects.filter(
            email__iexact=serializer.validated_data['email'],
            role='STUDENT',
            is_verified=False,
            is_active=True,
        ).first()

        if user:
            try:
                send_verification_email(user)
            except VerificationCooldownError:
                pass
            except (VerificationEmailDeliveryError, ImproperlyConfigured):
                return Response({
                    'error': (
                        'The email provider could not accept the verification message. '
                        'Please try again later.'
                    ),
                    'status_code': status.HTTP_503_SERVICE_UNAVAILABLE,
                }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        return Response({
            'message': (
                'If this address belongs to an unverified account and the resend '
                'cooldown has elapsed, a verification message will be sent.'
            ),
            'cooldown_seconds': settings.EMAIL_VERIFICATION_RESEND_COOLDOWN_SECONDS,
        }, status=status.HTTP_202_ACCEPTED)


@method_decorator(csrf_protect, name='dispatch')
class UserLoginView(APIView):
    """
    Login with email and password.
    Sets JWT session cookies.
    """
    
    permission_classes = [permissions.AllowAny]
    authentication_classes = []
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'auth_login'
    serializer_class = UserLoginSerializer
    
    @extend_schema(
        tags=['Authentication'],
        summary='User login',
        description='Authenticate with email and password. Sets HttpOnly JWT session cookies.',
        request=UserLoginSerializer,
        responses={
            200: OpenApiResponse(description='Login successful'),
            400: OpenApiResponse(description='Invalid credentials'),
        }
    )
    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = serializer.validated_data['user']
        record_security_event(
            'LOGIN_SUCCEEDED',
            actor=user,
            target=user,
        )

        refresh = RefreshToken.for_user(user)
        response = Response({
            'user': UserSerializer(user).data,
            'message': 'Login successful'
        }, status=status.HTTP_200_OK)
        set_auth_cookies(response, str(refresh))
        return response


@method_decorator(csrf_protect, name='dispatch')
class UserLogoutView(APIView):
    """
    Logout and blacklist refresh token.
    """
    
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    @extend_schema(
        tags=['Authentication'],
        summary='User logout',
        description='Logout and blacklist the refresh token.',
        responses={
            200: OpenApiResponse(description='Logout successful'),
            400: OpenApiResponse(description='Invalid token'),
        }
    )
    def post(self, request):
        refresh_token = request.COOKIES.get(settings.AUTH_REFRESH_COOKIE_NAME)
        response = Response({'message': 'Logout successful'}, status=status.HTTP_200_OK)
        if refresh_token:
            try:
                RefreshToken(refresh_token).blacklist()
            except TokenError:
                error_response = Response(
                    {'error': 'The session was cleared, but its refresh token was invalid or expired.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
                clear_auth_cookies(error_response)
                return error_response
        clear_auth_cookies(response)
        return response


@method_decorator(csrf_protect, name='dispatch')
class CookieTokenRefreshView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    @extend_schema(
        tags=['Authentication'],
        summary='Refresh user session',
        description='Refresh the access cookie using the HttpOnly refresh cookie.',
        responses={
            200: OpenApiResponse(description='Session refreshed'),
            401: OpenApiResponse(description='Session expired or invalid'),
        },
    )
    def post(self, request):
        refresh_token = request.COOKIES.get(settings.AUTH_REFRESH_COOKIE_NAME)
        if not refresh_token:
            response = Response(
                {'error': 'Session expired. Please sign in again.'},
                status=status.HTTP_401_UNAUTHORIZED,
            )
            clear_auth_cookies(response)
            return response

        try:
            refresh = RefreshToken(refresh_token)
            user_id = refresh[settings.SIMPLE_JWT['USER_ID_CLAIM']]
        except (TokenError, KeyError):
            user_id = None
            user = None
        else:
            user = User.objects.filter(pk=user_id).first()

        if (
            user is None
            or not user.is_active
            or (user.is_student and not user.is_verified)
        ):
            response = Response(
                {'error': 'Session expired. Please sign in again.'},
                status=status.HTTP_401_UNAUTHORIZED,
            )
            clear_auth_cookies(response)
            return response

        serializer = TokenRefreshSerializer(data={'refresh': refresh_token})
        if not serializer.is_valid():
            response = Response(
                {'error': 'Session expired. Please sign in again.'},
                status=status.HTTP_401_UNAUTHORIZED,
            )
            clear_auth_cookies(response)
            return response

        tokens = serializer.validated_data
        response = Response({'message': 'Session refreshed'}, status=status.HTTP_200_OK)
        set_auth_cookies(
            response,
            tokens.get('refresh', refresh_token),
            access_token=tokens['access'],
        )
        return response


@method_decorator(csrf_protect, name='dispatch')
class PasswordResetRequestView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'auth_password_reset'

    @extend_schema(
        tags=['Authentication'],
        summary='Request a password reset',
        request=PasswordResetRequestSerializer,
        responses={202: OpenApiResponse(description='Request accepted without account disclosure')},
    )
    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = User.objects.filter(
            email__iexact=serializer.validated_data['email'],
            is_active=True,
        ).first()

        if user:
            try:
                send_password_reset_email(user)
            except PasswordResetDeliveryError:
                record_security_event(
                    'PASSWORD_RESET_EMAIL_FAILED',
                    target=user,
                )
            else:
                record_security_event(
                    'PASSWORD_RESET_EMAIL_ACCEPTED',
                    target=user,
                )

        return Response({
            'message': (
                'If an active account uses this address, password reset instructions '
                'will be sent when email delivery is available. This response does '
                'not confirm that a message was delivered.'
            ),
        }, status=status.HTTP_202_ACCEPTED)


@method_decorator(csrf_protect, name='dispatch')
class PasswordResetConfirmView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'auth_password_confirm'

    @extend_schema(
        tags=['Authentication'],
        summary='Set a new password with a one-time reset token',
        request=PasswordResetConfirmSerializer,
        responses={
            200: OpenApiResponse(description='Password reset'),
            400: OpenApiResponse(description='Invalid or expired reset link'),
        },
    )
    def post(self, request):
        token_data = PasswordResetTokenSerializer(data=request.data)
        token_data.is_valid(raise_exception=True)

        try:
            user_id = force_str(urlsafe_base64_decode(token_data.validated_data['uid']))
        except (TypeError, ValueError, UnicodeDecodeError):
            return Response(
                {'error': 'This password reset link is invalid or expired.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            user = User.objects.select_for_update().filter(
                pk=user_id,
                is_active=True,
            ).first()
            if (
                user is None
                or not default_token_generator.check_token(
                    user,
                    token_data.validated_data['token'],
                )
            ):
                return Response(
                    {'error': 'This password reset link is invalid or expired.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            password_data = PasswordResetConfirmSerializer(
                data=request.data,
                context={'user': user},
            )
            password_data.is_valid(raise_exception=True)
            user.set_password(password_data.validated_data['new_password'])
            user.save(update_fields=['password', 'updated_at'])
            revoke_user_refresh_tokens(user)
            record_security_event(
                'PASSWORD_RESET_COMPLETED',
                actor=user,
                target=user,
            )

        response = Response(
            {'message': 'Your password has been reset. Sign in with your new password.'},
            status=status.HTTP_200_OK,
        )
        clear_auth_cookies(response)
        return response


@method_decorator(csrf_protect, name='dispatch')
class PasswordChangeView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'auth_password_change'

    @extend_schema(
        tags=['Authentication'],
        summary='Change the authenticated account password',
        request=PasswordChangeSerializer,
        responses={200: OpenApiResponse(description='Password changed')},
    )
    def post(self, request):
        serializer = PasswordChangeSerializer(
            data=request.data,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            user = User.objects.select_for_update().get(pk=request.user.pk)
            user.set_password(serializer.validated_data['new_password'])
            user.save(update_fields=['password', 'updated_at'])
            revoke_user_refresh_tokens(user)
            record_security_event(
                'PASSWORD_CHANGED',
                actor=user,
                target=user,
            )

        response = Response(
            {'message': 'Your password was changed. Sign in again to continue.'},
            status=status.HTTP_200_OK,
        )
        clear_auth_cookies(response)
        return response


class ManagedUserListView(generics.ListAPIView):
    serializer_class = ManagedUserSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'auth_user_management'

    def get_queryset(self):
        queryset = User.objects.order_by('email')
        if not self.request.user.is_superadmin:
            queryset = queryset.filter(role__in=('STUDENT', 'CONSULTANT'))
        return queryset


class ManagedUserDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'auth_user_management'

    def get_object(self, user_id, *, for_update=False):
        queryset = User.objects.all()
        if for_update:
            queryset = queryset.select_for_update()
        user = get_object_or_404(queryset, pk=user_id)
        if not self.request.user.is_superadmin and user.role not in ('STUDENT', 'CONSULTANT'):
            raise PermissionDenied(
                'Administrators can manage student and consultant accounts only.'
            )
        return user

    def get(self, request, user_id):
        return Response(ManagedUserSerializer(self.get_object(user_id)).data)

    @transaction.atomic
    def patch(self, request, user_id):
        user = self.get_object(user_id, for_update=True)
        old_role = user.role
        old_active = user.is_active
        serializer = ManagedUserSerializer(
            user,
            data=request.data,
            partial=True,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        updated_user = serializer.save()

        if old_active != updated_user.is_active and not updated_user.is_active:
            revoke_user_refresh_tokens(updated_user)
        if old_role != updated_user.role or old_active != updated_user.is_active:
            if old_role != updated_user.role:
                action = 'USER_ROLE_CHANGED'
            elif updated_user.is_active:
                action = 'USER_ACTIVATED'
            else:
                action = 'USER_DEACTIVATED'
            record_security_event(
                action,
                actor=request.user,
                target=updated_user,
                details={
                    'before': {'role': old_role, 'is_active': old_active},
                    'after': {
                        'role': updated_user.role,
                        'is_active': updated_user.is_active,
                    },
                },
            )

        return Response(ManagedUserSerializer(updated_user).data)


class SecurityAuditEventListView(generics.ListAPIView):
    serializer_class = SecurityAuditEventSerializer
    permission_classes = [permissions.IsAuthenticated, IsSuperAdmin]

    def get_queryset(self):
        return SecurityAuditEvent.objects.order_by('-created_at')


class CurrentUserView(generics.RetrieveUpdateAPIView):
    """
    Get or update current user profile.
    """
    
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user
    
    def get_serializer_class(self):
        if self.request.method == 'PUT' or self.request.method == 'PATCH':
            return UserProfileUpdateSerializer
        return UserSerializer
    
    @extend_schema(
        tags=['User Profile'],
        summary='Get current user',
        description='Retrieve authenticated user profile information.',
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @extend_schema(
        tags=['User Profile'],
        summary='Update current user',
        description='Update authenticated user profile information.',
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)
