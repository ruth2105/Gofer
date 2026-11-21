#!/usr/bin/env python
"""Quick API test script."""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.accounts.models import User
from apps.scholarships.models import Scholarship
from apps.opportunities.models import Opportunity

print("=== USER ACCOUNTS ===")
users = User.objects.all()
for user in users:
    print(f"- {user.email} ({user.role}) - Verified: {user.is_verified}")

print(f"\n=== SCHOLARSHIPS ({Scholarship.objects.filter(status='published').count()} published) ===")
for scholarship in Scholarship.objects.filter(status='published')[:3]:
    print(f"- {scholarship.name} ({scholarship.country}) - Deadline: {scholarship.application_deadline}")

print(f"\n=== OPPORTUNITIES ({Opportunity.objects.filter(is_published=True).count()} published) ===")
for opp in Opportunity.objects.filter(is_published=True)[:3]:
    print(f"- {opp.title} ({opp.country}) - Category: {opp.category}")
