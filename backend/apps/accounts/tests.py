from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from threading import Barrier

from unittest import skipUnless
from unittest.mock import Mock, patch

from django.db import IntegrityError
from django.db import close_old_connections, connection
from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.core.cache import cache
from django.test import TransactionTestCase, override_settings
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from rest_framework import serializers
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken

from .email_verification import _token_digest
from .models import EmailVerificationToken, SecurityAuditEvent, User
from .serializers import UserRegistrationSerializer


@skipUnless(connection.vendor == 'postgresql', 'Requires PostgreSQL')
class ConcurrentRegistrationTests(TransactionTestCase):
    reset_sequences = True

    def test_simultaneous_registration_creates_only_one_user(self):
        email = 'concurrent.student@example.com'
        barrier = Barrier(2, timeout=15)

        def register(email_input):
            close_old_connections()
            try:
                serializer = UserRegistrationSerializer(data={
                    'email': email_input,
                    'first_name': 'Concurrent',
                    'last_name': 'Student',
                    'password': 'Strong-Test-Password-123!',
                    'password2': 'Strong-Test-Password-123!',
                })

                if not serializer.is_valid():
                    return 'invalid', serializer.errors

                barrier.wait()

                try:
                    serializer.save()
                    return 'created', None
                except serializers.ValidationError as error:
                    return 'duplicate', error.detail
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [
                executor.submit(register, 'Concurrent.Student@Example.com'),
                executor.submit(register, 'concurrent.student@example.com'),
            ]
            results = [future.result(timeout=30) for future in futures]

        outcomes = [result[0] for result in results]

        self.assertCountEqual(outcomes, ['created', 'duplicate'])
        self.assertEqual(User.objects.filter(email=email).count(), 1)

        duplicate_result = next(
            result for result in results if result[0] == 'duplicate'
        )
        self.assertIn('email', duplicate_result[1])
        self.assertIn(
            'A user with this email already exists.',
            str(duplicate_result[1]['email']),
        )


class AuthenticationApiTests(APITestCase):
    def setUp(self):
        cache.clear()

    def registration_data(self, email='student@example.com'):
        return {
            'email': email,
            'first_name': 'Test',
            'last_name': 'Student',
            'password': 'Strong-Test-Password-123!',
            'password2': 'Strong-Test-Password-123!',
        }

    def test_registration_handles_creation_race_as_duplicate_validation(self):
        serializer = UserRegistrationSerializer(data=self.registration_data())
        self.assertTrue(serializer.is_valid())

        with patch(
            'apps.accounts.serializers.User.objects.create_user',
            side_effect=IntegrityError('unique constraint'),
        ), patch(
            'apps.accounts.serializers.User.objects.filter',
            return_value=Mock(exists=Mock(return_value=True)),
        ):
            with self.assertRaises(serializers.ValidationError) as error:
                serializer.save()

        self.assertEqual(
            str(error.exception.detail['email']),
            'A user with this email already exists.',
        )

    def test_registration_reraises_unrelated_integrity_error(self):
        serializer = UserRegistrationSerializer(data=self.registration_data())
        self.assertTrue(serializer.is_valid())

        with patch(
            'apps.accounts.serializers.User.objects.create_user',
            side_effect=IntegrityError('unrelated database failure'),
        ), patch(
            'apps.accounts.serializers.User.objects.filter',
            return_value=Mock(exists=Mock(return_value=False)),
        ):
            with self.assertRaises(IntegrityError):
                serializer.save()

    def test_registration_normalizes_mixed_case_email(self):
        response = self.client.post(
            '/api/v1/auth/register/',
            {
                'email': '  Student@Example.COM ',
                'first_name': 'Test',
                'last_name': 'Student',
                'password': 'Strong-Test-Password-123!',
                'password2': 'Strong-Test-Password-123!',
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email='student@example.com').exists())

    def test_public_registration_rejects_privileged_role_requests(self):
        response = self.client.post(
            '/api/v1/auth/register/',
            {
                **self.registration_data(),
                'role': 'SUPERADMIN',
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(User.objects.filter(email='student@example.com').exists())

    def test_self_profile_cannot_change_role_or_verification(self):
        user = User.objects.create_user(
            email='profile-role@example.com',
            password='Strong-Test-Password-123!',
        )
        self.client.force_authenticate(user=user)
        response = self.client.patch(
            '/api/v1/auth/me/',
            {'role': 'ADMIN', 'is_verified': True},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        user.refresh_from_db()
        self.assertEqual(user.role, 'STUDENT')
        self.assertFalse(user.is_verified)

    def test_mixed_case_login_uses_canonical_email(self):
        User.objects.create_user(
            email='student@example.com',
            password='Strong-Test-Password-123!',
            is_verified=True,
        )

        response = self.client.post(
            '/api/v1/auth/login/',
            {'email': 'Student@EXAMPLE.com', 'password': 'Strong-Test-Password-123!'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user']['email'], 'student@example.com')
        self.assertTrue(response.cookies['access_token']['httponly'])

    def test_registration_rejects_duplicate_email_with_different_casing(self):
        User.objects.create_user(
            email='student@example.com',
            password='Strong-Test-Password-123!',
        )

        response = self.client.post(
            '/api/v1/auth/register/',
            {
                'email': 'STUDENT@EXAMPLE.COM',
                'first_name': 'Duplicate',
                'last_name': 'Student',
                'password': 'Strong-Test-Password-123!',
                'password2': 'Strong-Test-Password-123!',
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data['details'])

    def test_login_rejects_inactive_account(self):
        User.objects.create_user(
            email='inactive@example.com',
            password='Strong-Test-Password-123!',
            is_active=False,
        )

        response = self.client.post(
            '/api/v1/auth/login/',
            {'email': 'INACTIVE@example.com', 'password': 'Strong-Test-Password-123!'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_registration_creates_unverified_student_and_sends_email(self):
        response = self.client.post(
            '/api/v1/auth/register/',
            {
                'email': 'student@example.com',
                'first_name': 'Test',
                'last_name': 'Student',
                'phone_number': '+251900000000',
                'password': 'Strong-Test-Password-123!',
                'password2': 'Strong-Test-Password-123!',
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['user']['role'], 'STUDENT')
        self.assertFalse(response.data['user']['is_verified'])
        self.assertNotIn('tokens', response.data)
        self.assertNotIn('access_token', response.cookies)
        self.assertNotIn('refresh_token', response.cookies)
        self.assertTrue(User.objects.get(email='student@example.com').check_password(
            'Strong-Test-Password-123!'
        ))
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['student@example.com'])
        self.assertIn('Verify email address', mail.outbox[0].alternatives[0][0])
        token = self.extract_token(mail.outbox[0].body)
        verification = EmailVerificationToken.objects.get(
            user__email='student@example.com'
        )
        self.assertEqual(verification.token_hash, _token_digest(token))
        self.assertNotEqual(verification.token_hash, token)

    @staticmethod
    def extract_token(body):
        import re

        match = re.search(r'[?&]token=([A-Za-z0-9_-]+)', body)
        if not match:
            raise AssertionError('Verification token was not found in the email body.')
        return match.group(1)

    def test_login_rejects_invalid_password(self):
        User.objects.create_user(
            email='student@example.com',
            password='Strong-Test-Password-123!',
        )

        response = self.client.post(
            '/api/v1/auth/login/',
            {'email': 'student@example.com', 'password': 'wrong-password'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_profile_requires_authentication_and_returns_authenticated_user(self):
        user = User.objects.create_user(
            email='student@example.com',
            password='Strong-Test-Password-123!',
        )
        anonymous_response = self.client.get('/api/v1/auth/me/')
        self.assertEqual(anonymous_response.status_code, status.HTTP_401_UNAUTHORIZED)

        self.client.force_authenticate(user=user)
        response = self.client.get('/api/v1/auth/me/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], user.email)

    def test_logout_does_not_expose_invalid_token_details(self):
        self.client.cookies['refresh_token'] = 'not-a-refresh-token'
        response = self.client.post('/api/v1/auth/logout/', {}, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data['error'],
            'The session was cleared, but its refresh token was invalid or expired.',
        )
        self.assertNotIn('not-a-refresh-token', str(response.data))

    def test_logout_blacklists_the_refresh_token(self):
        user = User.objects.create_user(
            email='student@example.com',
            password='Strong-Test-Password-123!',
        )
        refresh = RefreshToken.for_user(user)
        self.client.cookies['refresh_token'] = str(refresh)

        response = self.client.post('/api/v1/auth/logout/', {}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            BlacklistedToken.objects.filter(token__jti=refresh['jti']).exists()
        )
        self.assertEqual(response.cookies['access_token']['max-age'], 0)
        self.assertEqual(response.cookies['refresh_token']['max-age'], 0)

    def test_login_sets_session_cookies_without_returning_tokens(self):
        User.objects.create_user(
            email='student@example.com',
            password='Strong-Test-Password-123!',
            is_verified=True,
        )

        response = self.client.post(
            '/api/v1/auth/login/',
            {'email': 'student@example.com', 'password': 'Strong-Test-Password-123!'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn('tokens', response.data)
        self.assertTrue(response.cookies['access_token']['httponly'])
        self.assertTrue(response.cookies['refresh_token']['httponly'])

    def test_login_rejects_unverified_student(self):
        User.objects.create_user(
            email='student@example.com',
            password='Strong-Test-Password-123!',
        )

        response = self.client.post(
            '/api/v1/auth/login/',
            {'email': 'student@example.com', 'password': 'Strong-Test-Password-123!'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('verify your email', str(response.data).lower())
        self.assertNotIn('access_token', response.cookies)

    def test_access_cookie_authenticates_current_user(self):
        user = User.objects.create_user(
            email='student@example.com',
            password='Strong-Test-Password-123!',
            is_verified=True,
        )
        refresh = RefreshToken.for_user(user)
        self.client.cookies['access_token'] = str(refresh.access_token)

        response = self.client.get('/api/v1/auth/me/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], user.email)

    def test_existing_unverified_access_cookie_is_rejected(self):
        user = User.objects.create_user(
            email='unverified@example.com',
            password='Strong-Test-Password-123!',
        )
        refresh = RefreshToken.for_user(user)
        self.client.cookies['access_token'] = str(refresh.access_token)

        response = self.client.get('/api/v1/auth/me/')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_existing_unverified_refresh_cookie_is_rejected(self):
        user = User.objects.create_user(
            email='unverified@example.com',
            password='Strong-Test-Password-123!',
        )
        refresh = RefreshToken.for_user(user)
        self.client.cookies['refresh_token'] = str(refresh)

        response = self.client.post('/api/v1/auth/token/refresh/', {}, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.cookies['access_token']['max-age'], 0)
        self.assertEqual(response.cookies['refresh_token']['max-age'], 0)

    def test_cookie_authenticated_mutations_require_valid_csrf_token(self):
        user = User.objects.create_user(
            email='student@example.com',
            password='Strong-Test-Password-123!',
            is_verified=True,
        )
        refresh = RefreshToken.for_user(user)
        client = APIClient(enforce_csrf_checks=True)
        client.cookies['access_token'] = str(refresh.access_token)

        rejected = client.patch(
            '/api/v1/auth/me/',
            {'first_name': 'Updated'},
            format='json',
        )
        self.assertEqual(rejected.status_code, status.HTTP_403_FORBIDDEN)

        csrf_response = client.get('/api/v1/auth/csrf/')
        csrf_token = csrf_response.data['csrfToken']
        accepted = client.patch(
            '/api/v1/auth/me/',
            {'first_name': 'Updated'},
            format='json',
            HTTP_X_CSRFTOKEN=csrf_token,
        )

        self.assertEqual(accepted.status_code, status.HTTP_200_OK)
        self.assertEqual(accepted.data['first_name'], 'Updated')

    def test_refresh_uses_httponly_cookie_without_returning_token(self):
        user = User.objects.create_user(
            email='student@example.com',
            password='Strong-Test-Password-123!',
            is_verified=True,
        )
        refresh = RefreshToken.for_user(user)
        self.client.cookies['refresh_token'] = str(refresh)

        response = self.client.post('/api/v1/auth/token/refresh/', {}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn('access', response.data)
        self.assertNotIn('refresh', response.data)
        self.assertTrue(response.cookies['access_token']['httponly'])
        self.assertTrue(response.cookies['refresh_token']['httponly'])

    def test_registration_requires_csrf_token_for_browser_flow(self):
        client = APIClient(enforce_csrf_checks=True)
        registration_data = {
            'email': 'csrf-student@example.com',
            'first_name': 'CSRF',
            'last_name': 'Student',
            'password': 'Strong-Test-Password-123!',
            'password2': 'Strong-Test-Password-123!',
        }

        rejected = client.post(
            '/api/v1/auth/register/',
            registration_data,
            format='json',
        )
        self.assertEqual(rejected.status_code, status.HTTP_403_FORBIDDEN)

        csrf_response = client.get('/api/v1/auth/csrf/')
        accepted = client.post(
            '/api/v1/auth/register/',
            registration_data,
            format='json',
            HTTP_X_CSRFTOKEN=csrf_response.data['csrfToken'],
        )

        self.assertEqual(accepted.status_code, status.HTTP_201_CREATED)
        self.assertNotIn('tokens', accepted.data)


class EmailVerificationWorkflowTests(APITestCase):
    def setUp(self):
        cache.clear()

    def register(self, email='verify@example.com'):
        return self.client.post(
            '/api/v1/auth/register/',
            {
                'email': email,
                'first_name': 'Verify',
                'last_name': 'Student',
                'password': 'Strong-Test-Password-123!',
                'password2': 'Strong-Test-Password-123!',
            },
            format='json',
        )

    @staticmethod
    def token_from_email():
        import re

        match = re.search(r'[?&]token=([A-Za-z0-9_-]+)', mail.outbox[0].body)
        if not match:
            raise AssertionError('Verification token was not found in the email body.')
        return match.group(1)

    def test_valid_token_verifies_only_its_account_and_cannot_be_reused(self):
        response = self.register()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        token = self.token_from_email()
        unverified_user = User.objects.get(email='verify@example.com')
        stale_refresh = RefreshToken.for_user(unverified_user)
        self.client.cookies['access_token'] = str(stale_refresh.access_token)
        other_user = User.objects.create_user(
            email='other@example.com',
            password='Strong-Test-Password-123!',
        )

        verified = self.client.post(
            '/api/v1/auth/verify-email/',
            {'token': token},
            format='json',
        )
        self.assertEqual(verified.status_code, status.HTTP_200_OK)
        self.assertEqual(verified.data['status'], 'verified')
        self.assertTrue(User.objects.get(email='verify@example.com').is_verified)
        other_user.refresh_from_db()
        self.assertFalse(other_user.is_verified)

        reused = self.client.post(
            '/api/v1/auth/verify-email/',
            {'token': token},
            format='json',
        )
        self.assertEqual(reused.status_code, status.HTTP_200_OK)
        self.assertEqual(reused.data['status'], 'already_verified')

        login = self.client.post(
            '/api/v1/auth/login/',
            {'email': 'verify@example.com', 'password': 'Strong-Test-Password-123!'},
            format='json',
        )
        self.assertEqual(login.status_code, status.HTTP_200_OK)

    def test_invalid_token_is_rejected(self):
        response = self.client.post(
            '/api/v1/auth/verify-email/',
            {'token': 'not-a-valid-token'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['status'], 'invalid')

    def test_expired_token_is_rejected_with_expired_state(self):
        self.register()
        verification = EmailVerificationToken.objects.get(
            user__email='verify@example.com'
        )
        verification.expires_at = timezone.now() - timedelta(seconds=1)
        verification.save(update_fields=['expires_at'])

        response = self.client.post(
            '/api/v1/auth/verify-email/',
            {'token': self.token_from_email()},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['status'], 'expired')
        self.assertFalse(User.objects.get(email='verify@example.com').is_verified)

    def test_resend_cooldown_and_token_rotation(self):
        self.register()
        verification = EmailVerificationToken.objects.get(
            user__email='verify@example.com'
        )
        original_hash = verification.token_hash

        cooled_down = self.client.post(
            '/api/v1/auth/resend-verification/',
            {'email': 'verify@example.com'},
            format='json',
        )
        self.assertEqual(cooled_down.status_code, status.HTTP_202_ACCEPTED)
        self.assertEqual(len(mail.outbox), 1)
        verification.refresh_from_db()
        self.assertEqual(verification.token_hash, original_hash)

        verification.last_sent_at = timezone.now() - timedelta(
            seconds=60,
        )
        verification.save(update_fields=['last_sent_at'])
        resent = self.client.post(
            '/api/v1/auth/resend-verification/',
            {'email': 'verify@example.com'},
            format='json',
        )

        self.assertEqual(resent.status_code, status.HTTP_202_ACCEPTED)
        self.assertEqual(len(mail.outbox), 2)
        verification.refresh_from_db()
        self.assertNotEqual(verification.token_hash, original_hash)
        old_token = self.token_from_email()
        invalidated = self.client.post(
            '/api/v1/auth/verify-email/',
            {'token': old_token},
            format='json',
        )
        self.assertEqual(invalidated.data['status'], 'invalid')

    def test_email_provider_failure_does_not_verify_or_expose_token(self):
        with patch(
            'apps.accounts.email_verification.EmailMultiAlternatives.send',
            side_effect=OSError('sensitive provider details'),
        ):
            response = self.register()

        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertIn('account was created', response.data['error'])
        self.assertNotIn('sensitive provider details', str(response.data))
        user = User.objects.get(email='verify@example.com')
        self.assertFalse(user.is_verified)
        self.assertFalse(
            EmailVerificationToken.objects.filter(user=user).exists()
        )

    def test_resend_endpoint_is_rate_limited(self):
        responses = [
            self.client.post(
                '/api/v1/auth/resend-verification/',
                {'email': 'unknown@example.com'},
                format='json',
            )
            for _ in range(4)
        ]

        self.assertEqual(
            [response.status_code for response in responses],
            [
                status.HTTP_202_ACCEPTED,
                status.HTTP_202_ACCEPTED,
                status.HTTP_202_ACCEPTED,
                status.HTTP_429_TOO_MANY_REQUESTS,
            ],
        )


class RoleManagementApiTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.student = User.objects.create_user(
            email='managed.student@example.com',
            password='Strong-Test-Password-123!',
        )
        self.consultant = User.objects.create_user(
            email='managed.consultant@example.com',
            password='Strong-Test-Password-123!',
            role='CONSULTANT',
        )
        self.admin = User.objects.create_user(
            email='manager@example.com',
            password='Strong-Test-Password-123!',
            role='ADMIN',
            is_staff=True,
        )
        self.superadmin = User.objects.create_superuser(
            email='root@example.com',
            password='Strong-Test-Password-123!',
        )

    def test_guest_and_student_cannot_access_user_management(self):
        anonymous = self.client.get('/api/v1/auth/users/')
        self.assertEqual(anonymous.status_code, status.HTTP_401_UNAUTHORIZED)

        self.client.force_authenticate(user=self.student)
        student_response = self.client.get('/api/v1/auth/users/')
        self.assertEqual(student_response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_lists_only_ordinary_accounts(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get('/api/v1/auth/users/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        listed_ids = {row['id'] for row in response.data['results']}
        self.assertEqual(
            listed_ids,
            {str(self.student.pk), str(self.consultant.pk)},
        )

    def test_admin_cannot_escalate_role_or_manage_an_admin_account(self):
        self.client.force_authenticate(user=self.admin)
        role_escalation = self.client.patch(
            f'/api/v1/auth/users/{self.student.pk}/',
            {'role': 'ADMIN'},
            format='json',
        )
        self.assertEqual(role_escalation.status_code, status.HTTP_403_FORBIDDEN)
        self.student.refresh_from_db()
        self.assertEqual(self.student.role, 'STUDENT')

        system_flag = self.client.patch(
            f'/api/v1/auth/users/{self.student.pk}/',
            {'is_superuser': True},
            format='json',
        )
        self.assertEqual(system_flag.status_code, status.HTTP_403_FORBIDDEN)

        admin_target = self.client.get(f'/api/v1/auth/users/{self.superadmin.pk}/')
        self.assertEqual(admin_target.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_manage_ordinary_account_without_changing_role(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.patch(
            f'/api/v1/auth/users/{self.student.pk}/',
            {'is_active': False, 'first_name': 'Disabled'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.student.refresh_from_db()
        self.assertFalse(self.student.is_active)
        self.assertEqual(self.student.first_name, 'Disabled')
        self.assertEqual(self.student.role, 'STUDENT')
        self.assertTrue(
            SecurityAuditEvent.objects.filter(
                action='USER_DEACTIVATED',
                actor=self.admin,
                target=self.student,
            ).exists()
        )

    def test_superadmin_can_assign_roles_and_manage_admin_accounts(self):
        self.client.force_authenticate(user=self.superadmin)
        response = self.client.patch(
            f'/api/v1/auth/users/{self.student.pk}/',
            {'role': 'ADMIN'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.student.refresh_from_db()
        self.assertEqual(self.student.role, 'ADMIN')
        self.assertTrue(self.student.is_staff)
        self.assertFalse(self.student.is_superuser)
        self.assertTrue(
            SecurityAuditEvent.objects.filter(
                action='USER_ROLE_CHANGED',
                actor=self.superadmin,
                target=self.student,
            ).exists()
        )

    def test_superadmin_cannot_lock_out_own_account(self):
        self.client.force_authenticate(user=self.superadmin)
        response = self.client.patch(
            f'/api/v1/auth/users/{self.superadmin.pk}/',
            {'is_active': False},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_security_audit_is_superadmin_only_and_read_only(self):
        record_security_event_for_test = SecurityAuditEvent.objects.create(
            action='TEST_EVENT',
            actor=self.admin,
            actor_role=self.admin.role,
            target=self.student,
            target_role=self.student.role,
        )
        self.client.force_authenticate(user=self.admin)
        denied = self.client.get('/api/v1/auth/security/audit/')
        self.assertEqual(denied.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(user=self.superadmin)
        allowed = self.client.get('/api/v1/auth/security/audit/')
        self.assertEqual(allowed.status_code, status.HTTP_200_OK)
        self.assertEqual(allowed.data['results'][0]['id'], record_security_event_for_test.pk)
        self.assertNotIn('email', allowed.data['results'][0])


class PasswordLifecycleApiTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(
            email='reset.student@example.com',
            password='Strong-Test-Password-123!',
            is_verified=True,
        )

    def request_reset(self, email=None):
        return self.client.post(
            '/api/v1/auth/password/reset/',
            {'email': email or self.user.email},
            format='json',
        )

    def reset_link_data(self):
        import re

        match = re.search(
            r'[?&]uid=([A-Za-z0-9_-]+)&token=([A-Za-z0-9_-]+)',
            mail.outbox[-1].body,
        )
        if not match:
            raise AssertionError('Password reset token was not found in the email body.')
        return {'uid': match.group(1), 'token': match.group(2)}

    def confirm_reset(self, link, password='Another-Strong-Password-456!'):
        return self.client.post(
            '/api/v1/auth/password/reset/confirm/',
            {
                **link,
                'new_password': password,
                'new_password2': password,
            },
            format='json',
        )

    def test_reset_request_does_not_disclose_account_existence(self):
        registered = self.request_reset()
        unknown = self.request_reset('unknown@example.com')

        self.assertEqual(registered.status_code, status.HTTP_202_ACCEPTED)
        self.assertEqual(unknown.status_code, status.HTTP_202_ACCEPTED)
        self.assertEqual(registered.data, unknown.data)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('does not confirm', registered.data['message'])

    def test_reset_token_is_single_use_and_password_change_revokes_sessions(self):
        refresh = RefreshToken.for_user(self.user)
        response = self.request_reset()
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        link = self.reset_link_data()

        reset = self.confirm_reset(link)
        self.assertEqual(reset.status_code, status.HTTP_200_OK)
        self.assertTrue(reset.cookies['access_token']['max-age'] == 0)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('Another-Strong-Password-456!'))
        self.assertTrue(
            BlacklistedToken.objects.filter(token__jti=refresh['jti']).exists()
        )

        replay = self.confirm_reset(link)
        self.assertEqual(replay.status_code, status.HTTP_400_BAD_REQUEST)
        old_login = self.client.post(
            '/api/v1/auth/login/',
            {'email': self.user.email, 'password': 'Strong-Test-Password-123!'},
            format='json',
        )
        self.assertEqual(old_login.status_code, status.HTTP_400_BAD_REQUEST)

    @override_settings(PASSWORD_RESET_TIMEOUT=60)
    def test_expired_password_reset_token_is_rejected(self):
        self.request_reset()
        link = self.reset_link_data()
        with patch.object(
            default_token_generator,
            '_now',
            return_value=datetime.now() + timedelta(seconds=61),
        ):
            response = self.confirm_reset(link)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data['error'],
            'This password reset link is invalid or expired.',
        )

    def test_invalid_password_reset_token_is_rejected(self):
        response = self.confirm_reset({'uid': 'invalid', 'token': 'invalid'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_reset_email_provider_failure_is_generic_and_logged_safely(self):
        with patch(
            'apps.accounts.password_reset.EmailMultiAlternatives.send',
            side_effect=OSError('private provider response'),
        ):
            registered = self.request_reset()
        unknown = self.request_reset('unknown@example.com')

        self.assertEqual(registered.status_code, status.HTTP_202_ACCEPTED)
        self.assertEqual(registered.data, unknown.data)
        self.assertNotIn('private provider response', str(registered.data))
        self.assertTrue(
            SecurityAuditEvent.objects.filter(
                action='PASSWORD_RESET_EMAIL_FAILED',
                target=self.user,
            ).exists()
        )

    def test_password_change_requires_current_password_and_revokes_old_tokens(self):
        refresh = RefreshToken.for_user(self.user)
        access = refresh.access_token
        self.client.cookies['access_token'] = str(access)
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            '/api/v1/auth/password/change/',
            {
                'old_password': 'Strong-Test-Password-123!',
                'new_password': 'Changed-Strong-Password-789!',
                'new_password2': 'Changed-Strong-Password-789!',
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('Changed-Strong-Password-789!'))
        self.assertTrue(
            BlacklistedToken.objects.filter(token__jti=refresh['jti']).exists()
        )
        self.assertEqual(response.cookies['access_token']['max-age'], 0)

        self.client.force_authenticate(user=None)
        self.client.cookies['access_token'] = str(access)
        old_session = self.client.get('/api/v1/auth/me/')
        self.assertEqual(old_session.status_code, status.HTTP_401_UNAUTHORIZED)


class InactiveAndExpiredSessionApiTests(APITestCase):
    def test_inactive_account_cannot_use_access_or_refresh_tokens(self):
        user = User.objects.create_user(
            email='inactive.token@example.com',
            password='Strong-Test-Password-123!',
            is_verified=True,
        )
        refresh = RefreshToken.for_user(user)
        user.is_active = False
        user.save(update_fields=['is_active', 'updated_at'])

        self.client.cookies['access_token'] = str(refresh.access_token)
        access_response = self.client.get('/api/v1/auth/me/')
        self.assertEqual(access_response.status_code, status.HTTP_401_UNAUTHORIZED)

        self.client.cookies['refresh_token'] = str(refresh)
        refresh_response = self.client.post('/api/v1/auth/token/refresh/', {}, format='json')
        self.assertEqual(refresh_response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(refresh_response.cookies['refresh_token']['max-age'], 0)

    def test_expired_or_invalid_access_tokens_are_rejected(self):
        user = User.objects.create_user(
            email='expired.token@example.com',
            password='Strong-Test-Password-123!',
            is_verified=True,
        )
        expired = AccessToken.for_user(user)
        expired.set_exp(lifetime=timedelta(seconds=-1))
        self.client.cookies['access_token'] = str(expired)
        expired_response = self.client.get('/api/v1/auth/me/')
        self.assertEqual(expired_response.status_code, status.HTTP_401_UNAUTHORIZED)

        self.client.cookies['access_token'] = 'not-a-token'
        invalid_response = self.client.get('/api/v1/auth/me/')
        self.assertEqual(invalid_response.status_code, status.HTTP_401_UNAUTHORIZED)
