import base64
import json
import os
from email.mime.text import MIMEText
from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.core.mail import EmailMultiAlternatives
from django.test import SimpleTestCase, override_settings

from .brevo import BrevoEmailBackend, BrevoEmailBackendError


class BrevoEmailBackendTests(SimpleTestCase):
    @override_settings(
        BREVO_API_KEY='test-api-key',
        EMAIL_TIMEOUT=8,
        DEFAULT_CHARSET='utf-8',
    )
    @patch('config.email_backends.brevo.http.client.HTTPSConnection')
    def test_sends_plain_text_message_and_uses_finite_timeout(self, mock_https):
        mock_response = mock_https.return_value.getresponse.return_value
        mock_response.status = 201
        message = EmailMultiAlternatives(
            subject='Test subject',
            body='Plain text body',
            from_email='sender@example.com',
            to=['recipient@example.com'],
        )

        sent = BrevoEmailBackend().send_messages([message])

        self.assertEqual(sent, 1)
        mock_https.assert_called_once_with('api.brevo.com', port=443, timeout=8)
        mock_https.return_value.request.assert_called_once()
        request = mock_https.return_value.request.call_args
        self.assertEqual(request.args[:2], ('POST', '/v3/smtp/email'))
        self.assertEqual(request.kwargs['headers']['api-key'], 'test-api-key')
        self.assertEqual(json.loads(request.kwargs['body']), {
            'sender': {'email': 'sender@example.com'},
            'to': [{'email': 'recipient@example.com'}],
            'subject': 'Test subject',
            'textContent': 'Plain text body',
        })
        mock_https.return_value.close.assert_called_once()

    @override_settings(
        BREVO_API_KEY='test-api-key',
        DEFAULT_FROM_EMAIL='sender@example.com',
        EMAIL_BACKEND='config.email_backends.brevo.BrevoEmailBackend',
    )
    @patch.dict(os.environ, {'GOFER_TEST_EMAIL_AUTHORIZED_OPERATORS': 'local-reviewer'})
    @patch('config.email_backends.brevo.http.client.HTTPSConnection')
    def test_existing_send_test_email_command_works_with_backend(self, mock_https):
        mock_https.return_value.getresponse.return_value.status = 201
        output = StringIO()

        call_command(
            'send_test_email',
            recipient='recipient@example.com',
            operator='local-reviewer',
            skip_checks=True,
            stdout=output,
        )

        self.assertIn('One test email was accepted', output.getvalue())
        mock_https.assert_called_once()
        mock_https.return_value.request.assert_called_once()
        payload = json.loads(mock_https.return_value.request.call_args.kwargs['body'])
        self.assertEqual(
            payload['textContent'],
            'This is a test message to verify email delivery.',
        )

    @override_settings(BREVO_API_KEY='test-api-key')
    @patch('config.email_backends.brevo.http.client.HTTPSConnection')
    def test_preserves_multiple_recipients_cc_bcc_and_reply_to(self, mock_https):
        mock_https.return_value.getresponse.return_value.status = 201
        message = EmailMultiAlternatives(
            subject='Recipients',
            body='Hello',
            from_email='Gofer <sender@example.com>',
            to=['First Recipient <first@example.com>', 'second@example.com'],
            cc=['copy@example.com'],
            bcc=['blind-copy@example.com'],
            reply_to=['reply@example.com'],
        )

        self.assertEqual(BrevoEmailBackend().send_messages([message]), 1)

        payload = json.loads(mock_https.return_value.request.call_args.kwargs['body'])
        self.assertEqual(payload['sender'], {
            'email': 'sender@example.com',
            'name': 'Gofer',
        })
        self.assertEqual(payload['to'], [
            {'email': 'first@example.com', 'name': 'First Recipient'},
            {'email': 'second@example.com'},
        ])
        self.assertEqual(payload['cc'], [{'email': 'copy@example.com'}])
        self.assertEqual(payload['bcc'], [{'email': 'blind-copy@example.com'}])
        self.assertEqual(payload['replyTo'], {'email': 'reply@example.com'})

    @override_settings(BREVO_API_KEY='test-api-key')
    @patch('config.email_backends.brevo.http.client.HTTPSConnection')
    def test_preserves_html_alternative(self, mock_https):
        mock_https.return_value.getresponse.return_value.status = 201
        message = EmailMultiAlternatives(
            subject='HTML',
            body='Plain text',
            from_email='sender@example.com',
            to=['recipient@example.com'],
        )
        message.attach_alternative('<p>Hello</p>', 'text/html')

        self.assertEqual(BrevoEmailBackend().send_messages([message]), 1)

        payload = json.loads(mock_https.return_value.request.call_args.kwargs['body'])
        self.assertEqual(payload['textContent'], 'Plain text')
        self.assertEqual(payload['htmlContent'], '<p>Hello</p>')

    @override_settings(BREVO_API_KEY='test-api-key')
    @patch('config.email_backends.brevo.http.client.HTTPSConnection')
    def test_preserves_attachments_as_base64(self, mock_https):
        mock_https.return_value.getresponse.return_value.status = 201
        message = EmailMultiAlternatives(
            subject='Attachment',
            body='See attached',
            from_email='sender@example.com',
            to=['recipient@example.com'],
        )
        message.attach('report.txt', 'sample attachment', 'text/plain')
        mime_attachment = MIMEText('mime content', _subtype='plain')
        mime_attachment.add_header(
            'Content-Disposition',
            'attachment',
            filename='mime.txt',
        )
        message.attach(mime_attachment)

        self.assertEqual(BrevoEmailBackend().send_messages([message]), 1)

        payload = json.loads(mock_https.return_value.request.call_args.kwargs['body'])
        self.assertEqual(payload['attachment'], [
            {
                'name': 'report.txt',
                'content': base64.b64encode(b'sample attachment').decode('ascii'),
            },
            {
                'name': 'mime.txt',
                'content': base64.b64encode(b'mime content').decode('ascii'),
            },
        ])

    @override_settings(BREVO_API_KEY='test-api-key')
    @patch('config.email_backends.brevo.http.client.HTTPSConnection')
    def test_api_failure_is_sanitized(self, mock_https):
        mock_https.return_value.getresponse.return_value.status = 400
        message = EmailMultiAlternatives(
            subject='Failure',
            body='Hello',
            from_email='sender@example.com',
            to=['recipient@example.com'],
        )

        with self.assertRaises(BrevoEmailBackendError) as raised:
            BrevoEmailBackend().send_messages([message])

        self.assertEqual(str(raised.exception), 'Email delivery failed.')
        self.assertIsNone(raised.exception.__cause__)
        self.assertNotIn('sensitive', str(raised.exception))
        mock_https.return_value.close.assert_called_once()

    @override_settings(BREVO_API_KEY='test-api-key')
    @patch('config.email_backends.brevo.http.client.HTTPSConnection')
    def test_unexpected_error_is_sanitized(self, mock_https):
        mock_https.return_value.request.side_effect = RuntimeError(
            'sensitive provider details',
        )
        message = EmailMultiAlternatives(
            subject='Unexpected failure',
            body='Hello',
            from_email='sender@example.com',
            to=['recipient@example.com'],
        )

        with self.assertRaises(BrevoEmailBackendError) as raised:
            BrevoEmailBackend().send_messages([message])

        self.assertEqual(str(raised.exception), 'Email delivery failed.')
        self.assertNotIn('sensitive provider details', str(raised.exception))
        mock_https.return_value.close.assert_called_once()

    @override_settings(BREVO_API_KEY='')
    @patch('config.email_backends.brevo.http.client.HTTPSConnection')
    def test_missing_api_key_fails_without_request(self, mock_https):
        message = EmailMultiAlternatives(
            subject='Missing key',
            body='Hello',
            from_email='sender@example.com',
            to=['recipient@example.com'],
        )

        with self.assertRaisesMessage(BrevoEmailBackendError, 'Email delivery failed.'):
            BrevoEmailBackend().send_messages([message])

        mock_https.assert_not_called()

    @override_settings(BREVO_API_KEY='test-api-key')
    @patch('config.email_backends.brevo.http.client.HTTPSConnection')
    def test_fail_silently_suppresses_api_error(self, mock_https):
        mock_https.return_value.request.side_effect = RuntimeError(
            'sensitive provider details',
        )
        message = EmailMultiAlternatives(
            subject='Silent failure',
            body='Hello',
            from_email='sender@example.com',
            to=['recipient@example.com'],
        )

        self.assertEqual(
            BrevoEmailBackend(fail_silently=True).send_messages([message]),
            0,
        )
