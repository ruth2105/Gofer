#!/usr/bin/env python
"""
Email Configuration Test Script for GOFER EXAM

This script tests email configuration and sends a test email.
Run this after configuring your email backend to verify it works.

Usage:
    python test_email_config.py
    python test_email_config.py --to your-email@example.com
    python test_email_config.py --backend brevo
    python test_email_config.py --show-config
"""

import os
import sys
import django
from pathlib import Path

# Setup Django
sys.path.insert(0, str(Path(__file__).parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from django.conf import settings
from django.core.mail import send_mail
from django.core.mail.backends.base import BaseEmailBackend
import argparse


def show_config():
    """Display current email configuration."""
    print("\n" + "=" * 60)
    print("CURRENT EMAIL CONFIGURATION")
    print("=" * 60)
    
    print(f"\n[EMAIL_BACKEND]")
    print(f"   {settings.EMAIL_BACKEND}")
    
    backend_name = settings.EMAIL_BACKEND.split('.')[-1]
    
    if 'console' in settings.EMAIL_BACKEND.lower():
        print("\n   [INFO] Console Backend (Development)")
        print("   Emails will be printed to the console.")
        print("   No actual email delivery.")
    
    elif 'filebased' in settings.EMAIL_BACKEND.lower():
        print("\n   [INFO] File Backend (Development)")
        print("   Emails will be saved as .eml files.")
        path = getattr(settings, 'EMAIL_FILE_PATH', '/tmp/emails')
        print(f"   Location: {path}")
    
    elif 'brevo' in settings.EMAIL_BACKEND.lower():
        print("\n   [INFO] Brevo Backend (Production/Staging)")
        api_key = getattr(settings, 'BREVO_API_KEY', '')
        if api_key:
            masked = f"{api_key[:10]}...{api_key[-4:]}" if len(api_key) > 14 else "***"
            print(f"   API Key: {masked}")
        else:
            print("   [WARNING] BREVO_API_KEY not set!")
    
    elif 'smtp' in settings.EMAIL_BACKEND.lower():
        print("\n   [INFO] SMTP Backend")
        print(f"   Host: {settings.EMAIL_HOST}")
        print(f"   Port: {settings.EMAIL_PORT}")
        print(f"   TLS: {settings.EMAIL_USE_TLS}")
        print(f"   SSL: {settings.EMAIL_USE_SSL}")
        print(f"   User: {settings.EMAIL_HOST_USER or '(not set)'}")
        print(f"   Timeout: {settings.EMAIL_TIMEOUT}s")
    
    print(f"\n[DEFAULT_FROM_EMAIL]")
    print(f"   {settings.DEFAULT_FROM_EMAIL}")
    
    if settings.DEFAULT_FROM_EMAIL == 'webmaster@localhost':
        print("   [WARNING] Using default sender address!")
    
    print(f"\n[GOFER_FRONTEND_URL]")
    print(f"   {settings.GOFER_FRONTEND_URL}")
    
    print("\n" + "=" * 60)


def test_email_delivery(recipient):
    """Send a test email to verify configuration."""
    print("\n" + "=" * 60)
    print("SENDING TEST EMAIL")
    print("=" * 60)
    
    print(f"\n[From] {settings.DEFAULT_FROM_EMAIL}")
    print(f"[To] {recipient}")
    print(f"[Backend] {settings.EMAIL_BACKEND.split('.')[-1]}")
    
    subject = "GOFER EXAM - Email Configuration Test"
    message = f"""
Hello!

This is a test email from GOFER EXAM to verify your email configuration.

If you're seeing this message, your email backend is working correctly!

Configuration Details:
- Backend: {settings.EMAIL_BACKEND}
- From: {settings.DEFAULT_FROM_EMAIL}
- Frontend URL: {settings.GOFER_FRONTEND_URL}

Next Steps:
1. Test user registration email
2. Test password reset email
3. Test application notification emails

For more information, see: backend/EMAIL_TESTING_GUIDE.md

---
GOFER EXAM Platform
"""
    
    try:
        print("\n[INFO] Sending email...")
        count = send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient],
            fail_silently=False,
        )
        
        if count == 1:
            print("[SUCCESS] Email sent successfully!")
            
            if 'console' in settings.EMAIL_BACKEND.lower():
                print("\n[INFO] Check your console/terminal for the email output.")
            elif 'filebased' in settings.EMAIL_BACKEND.lower():
                path = getattr(settings, 'EMAIL_FILE_PATH', '/tmp/emails')
                print(f"\n[INFO] Check {path}/ for the .eml file.")
            else:
                print(f"\n[INFO] Check the inbox for: {recipient}")
                print("   (Don't forget to check your spam folder!)")
        else:
            print(f"[WARNING] send_mail returned {count}")
    
    except Exception as e:
        print(f"\n[ERROR] Failed to send email")
        print(f"\nError details:")
        print(f"   {type(e).__name__}: {e}")
        
        # Provide troubleshooting hints
        print(f"\n[TROUBLESHOOTING]")
        
        if 'brevo' in settings.EMAIL_BACKEND.lower():
            print("   - Check BREVO_API_KEY is set correctly")
            print("   - Verify sender email is verified in Brevo dashboard")
            print("   - Check you haven't exceeded rate limits (300/day free tier)")
        
        elif 'smtp' in settings.EMAIL_BACKEND.lower():
            print("   - Check EMAIL_HOST and EMAIL_PORT are correct")
            print("   - Verify EMAIL_HOST_USER and EMAIL_HOST_PASSWORD")
            print("   - For Gmail, ensure you're using an App Password")
            print("   - Check firewall isn't blocking SMTP port")
        
        print("\n   See backend/EMAIL_TESTING_GUIDE.md for detailed help.")
        return False
    
    print("\n" + "=" * 60)
    return True


def test_django_mail_command(recipient):
    """Test using Django's built-in sendtestemail command."""
    print("\n" + "=" * 60)
    print("TESTING WITH DJANGO'S sendtestemail COMMAND")
    print("=" * 60)
    
    from django.core.management import call_command
    
    try:
        print(f"\n⏳ Sending test email to {recipient}...")
        call_command('sendtestemail', recipient)
        print("✅ Command completed!")
    except Exception as e:
        print(f"❌ ERROR: {e}")


def main():
    parser = argparse.ArgumentParser(
        description='Test GOFER EXAM email configuration',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python test_email_config.py --show-config
  python test_email_config.py --to test@example.com
  python test_email_config.py --to test@example.com --django-command
        """
    )
    
    parser.add_argument(
        '--to',
        default='test@example.com',
        help='Recipient email address (default: test@example.com)'
    )
    
    parser.add_argument(
        '--show-config',
        action='store_true',
        help='Show current email configuration and exit'
    )
    
    parser.add_argument(
        '--django-command',
        action='store_true',
        help='Also test with Django\'s built-in sendtestemail command'
    )
    
    args = parser.parse_args()
    
    print("\n" + "=" * 60)
    print("GOFER EXAM - Email Configuration Test")
    print("=" * 60)
    
    # Always show config first
    show_config()
    
    if args.show_config:
        return
    
    # Test email delivery
    success = test_email_delivery(args.to)
    
    # Optionally test with Django command
    if args.django_command and success:
        test_django_mail_command(args.to)
    
    print("\n✨ Test complete!")
    print("\nFor detailed email testing guide, see:")
    print("   backend/EMAIL_TESTING_GUIDE.md\n")


if __name__ == '__main__':
    main()
