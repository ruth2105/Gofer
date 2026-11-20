"""Password reset email delivery using Django's configured email backend."""

import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator

logger = logging.getLogger(__name__)


class PasswordResetDeliveryError(Exception):
    """Raised when the configured email backend rejects a reset message."""


def send_password_reset_email(user):
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    reset_url = (
        f'{settings.GOFER_FRONTEND_URL.rstrip("/")}/student/reset-password'
        f'?uid={uid}&token={token}'
    )
    context = {
        'first_name': user.first_name or 'there',
        'reset_url': reset_url,
        'expiration_seconds': settings.PASSWORD_RESET_TIMEOUT,
    }

    try:
        message = EmailMultiAlternatives(
            subject='Reset your GOFER EXAM password',
            body=render_to_string('accounts/password_reset.txt', context),
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email],
        )
        message.attach_alternative(
            render_to_string('accounts/password_reset.html', context),
            'text/html',
        )
        if message.send(fail_silently=False) != 1:
            raise PasswordResetDeliveryError
    except Exception as error:
        logger.error(
            'Password reset email delivery failed for user_id=%s exception_type=%s',
            user.pk,
            type(error).__name__,
        )
        raise PasswordResetDeliveryError from None

    logger.info('Password reset email accepted by backend for user_id=%s', user.pk)
