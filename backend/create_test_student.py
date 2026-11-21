#!/usr/bin/env python
"""Create test student for functional verification"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.accounts.models import User

email = 'student_test_functional@test.local'
if not User.objects.filter(email=email).exists():
    user = User.objects.create_user(
        email=email,
        password='TestPass123!@#',
        first_name='Functional',
        last_name='Test',
        role='STUDENT',
        is_verified=True
    )
    print(f'✅ Created user: {user.email} (ID: {user.id})')
    print(f'   Password: TestPass123!@#')
    print(f'   Verified: {user.is_verified}')
else:
    user = User.objects.get(email=email)
    print(f'ℹ️  User already exists: {user.email} (ID: {user.id})')
    print(f'   Verified: {user.is_verified}')
