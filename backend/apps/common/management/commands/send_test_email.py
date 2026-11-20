import os
import smtplib

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.core.mail import EmailMessage
from django.core.management.base import BaseCommand, CommandError
from django.core.validators import validate_email


class Command(BaseCommand):
    help = 'Send one plain-text configuration test email to an authorized recipient.'

    def add_arguments(self, parser):
        parser.add_argument('--recipient', required=True)
        parser.add_argument('--operator', required=True)

    def handle(self, *args, **options):
        operator = options['operator'].strip().casefold()
        authorized_operators = {
            entry.strip().casefold()
            for entry in os.environ.get(
                'GOFER_TEST_EMAIL_AUTHORIZED_OPERATORS',
                '',
            ).split(',')
            if entry.strip()
        }
        if not operator or operator not in authorized_operators:
            raise CommandError('Not authorized to send a test email.')

        recipient = options['recipient'].strip()
        try:
            validate_email(recipient)
        except ValidationError:
            raise CommandError('Recipient must be a valid email address.') from None

        message = EmailMessage(
            subject='GOFER EXAM email configuration test',
            body='This is a test message to verify email delivery.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[recipient],
        )
        try:
            accepted_count = message.send(fail_silently=False)
        except Exception:
            raise CommandError(
                'The test email send attempt failed. Check mail delivery logs before retrying.'
            ) from None

        if accepted_count != 1:
            raise CommandError(
                'The mail backend did not confirm one accepted message. '
                'Check mail delivery logs before retrying.'
            )

        self.stdout.write(self.style.SUCCESS('One test email was accepted by the mail backend.'))
