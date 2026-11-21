#!/usr/bin/env python
"""Check test user status"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.accounts.models import User

email = 'student_test_functional@test.local'
user = User.objects.filter(email=email).first()

if user:
    print(f"✓ User exists: {email}")
    print(f"  - ID: {user.id}")
    print(f"  - Is verified: {user.is_verified}")
    print(f"  - Role: {user.role}")
    print(f"  - Password check: {user.check_password('TestPass123!@#')}")
else:
    print(f"✗ User not found: {email}")
