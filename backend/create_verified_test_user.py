#!/usr/bin/env python
"""Create a verified test user for authentication testing"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.accounts.models import User

email = 'student_test_functional@test.local'
password = 'TestPass123!@#'

# Check if user exists
existing_user = User.objects.filter(email=email).first()
if existing_user:
    print(f"User already exists: {email}")
    if not existing_user.is_verified:
        existing_user.is_verified = True
        existing_user.save()
        print("  - Marked as verified")
    else:
        print("  - Already verified")
    print(f"  - ID: {existing_user.id}")
else:
    # Create verified user
    user = User.objects.create_user(
        email=email,
        password=password,
        first_name='Test',
        last_name='Student',
        phone_number='+1234567890',
        role='STUDENT',
        is_verified=True
    )
    print(f"✓ Created verified test user: {email}")
    print(f"  - ID: {user.id}")
    print(f"  - Password: {password}")
