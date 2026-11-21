#!/usr/bin/env python
"""Create a complete test user with proper password."""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.accounts.models import User
from django.contrib.auth.hashers import make_password

# Delete existing test user if exists
User.objects.filter(email='testuser@gofer.test').delete()

# Create test user
user = User.objects.create(
    email='testuser@gofer.test',
    password=make_password('TestPass123!'),
    first_name='Test',
    last_name='User',
    phone_number='+251911111111',
    role='STUDENT',
    is_verified=True,
    is_active=True
)

print(f"Created user: {user.email}")
print(f"Password: TestPass123!")
print(f"Role: {user.role}")
print(f"Verified: {user.is_verified}")

# Create an admin user
User.objects.filter(email='admin@gofer.test').delete()
admin = User.objects.create(
    email='admin@gofer.test',
    password=make_password('AdminPass123!'),
    first_name='Admin',
    last_name='User',
    phone_number='+251922222222',
    role='ADMIN',
    is_verified=True,
    is_active=True,
    is_staff=True
)

print(f"\nCreated admin: {admin.email}")
print(f"Password: AdminPass123!")
print(f"Role: {admin.role}")

# Create a consultant user
User.objects.filter(email='consultant@gofer.test').delete()
consultant = User.objects.create(
    email='consultant@gofer.test',
    password=make_password('ConsultPass123!'),
    first_name='Consultant',
    last_name='User',
    phone_number='+251933333333',
    role='CONSULTANT',
    is_verified=True,
    is_active=True
)

print(f"\nCreated consultant: {consultant.email}")
print(f"Password: ConsultPass123!")
print(f"Role: {consultant.role}")
