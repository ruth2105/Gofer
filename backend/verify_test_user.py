#!/usr/bin/env python
"""Verify test user"""
import os
import django
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.accounts.models import User

email = sys.argv[1] if len(sys.argv) > 1 else 'verified_test_20261120152644@test.local'

try:
    user = User.objects.get(email=email)
    user.is_verified = True
    user.save()
    print(f'✅ Verified user: {user.email}')
except User.DoesNotExist:
    print(f'❌ User not found: {email}')
