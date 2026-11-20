import base64
import http.client
import json
from email.mime.base import MIMEBase
from email.utils import parseaddr

from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend


class BrevoEmailBackendError(Exception):
    """Raised when Brevo does not accept a transactional email."""


class BrevoEmailBackend(BaseEmailBackend):
    host = 'api.brevo.com'
    path = '/v3/smtp/email'

    def send_messages(self, email_messages):
        sent_count = 0
        for email_message in email_messages:
            try:
                if self._send(email_message):
                    sent_count += 1
            except Exception:
                if self.fail_silently:
                    continue
                raise BrevoEmailBackendError('Email delivery failed.') from None
        return sent_count

    def _send(self, email_message):
        if not email_message.recipients():
            return False

        api_key = settings.BREVO_API_KEY.strip()
        if not api_key or '\r' in api_key or '\n' in api_key:
            raise BrevoEmailBackendError('Email delivery failed.')

        payload = self._build_payload(email_message)
        connection = http.client.HTTPSConnection(
            self.host,
            port=443,
            timeout=max(1, int(settings.EMAIL_TIMEOUT)),
        )
        try:
            connection.request(
                'POST',
                self.path,
                body=json.dumps(payload).encode('utf-8'),
                headers={
                    'api-key': api_key,
                    'accept': 'application/json',
                    'content-type': 'application/json',
                },
            )
            response = connection.getresponse()
            if response.status != 201:
                raise BrevoEmailBackendError('Email delivery failed.')
        finally:
            connection.close()
        return True

    @classmethod
    def _build_payload(cls, email_message):
        payload = {
            'sender': cls._address(email_message.from_email),
            'to': [cls._address(address) for address in email_message.to],
            'subject': email_message.subject,
        }

        if email_message.cc:
            payload['cc'] = [cls._address(address) for address in email_message.cc]
        if email_message.bcc:
            payload['bcc'] = [cls._address(address) for address in email_message.bcc]
        if email_message.reply_to:
            if len(email_message.reply_to) != 1:
                raise ValueError('Only one reply-to address is supported.')
            payload['replyTo'] = cls._address(email_message.reply_to[0])

        if email_message.content_subtype == 'html':
            payload['htmlContent'] = str(email_message.body)
        else:
            payload['textContent'] = str(email_message.body)

        alternatives = getattr(email_message, 'alternatives', ())
        html_alternatives = [
            content
            for content, mimetype in alternatives
            if mimetype == 'text/html'
        ]
        unsupported_alternatives = [
            mimetype
            for _, mimetype in alternatives
            if mimetype != 'text/html'
        ]
        if unsupported_alternatives or len(html_alternatives) > 1:
            raise ValueError('The email contains an unsupported alternative.')
        if html_alternatives:
            payload['htmlContent'] = str(html_alternatives[0])

        if email_message.attachments:
            payload['attachment'] = [
                cls._attachment(attachment)
                for attachment in email_message.attachments
            ]
        return payload

    @staticmethod
    def _address(value):
        name, address = parseaddr(value)
        if not address:
            raise ValueError('The email contains an invalid address.')
        result = {'email': address}
        if name:
            result['name'] = name
        return result

    @staticmethod
    def _attachment(attachment):
        if isinstance(attachment, MIMEBase):
            if attachment.get('Content-ID'):
                raise ValueError('Inline attachments are not supported.')
            filename = attachment.get_filename() or 'attachment'
            content = attachment.get_payload(decode=True)
            if content is None:
                content = attachment.get_payload()
        else:
            filename, content, _ = attachment

        if isinstance(content, str):
            content = content.encode(settings.DEFAULT_CHARSET)
        encoded_content = base64.b64encode(bytes(content)).decode('ascii')
        return {
            'name': filename or 'attachment',
            'content': encoded_content,
        }
