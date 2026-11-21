#!/usr/bin/env python
"""Quick script to check database data."""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.accounts.models import User
from apps.scholarships.models import Scholarship
from apps.opportunities.models import Opportunity

print(f"Users: {User.objects.count()}")
print(f"  - Superusers: {User.objects.filter(is_superuser=True).count()}")
print(f"  - Students: {User.objects.filter(role='student').count()}")
print(f"  - Consultants: {User.objects.filter(role='consultant').count()}")

print(f"\nScholarships: {Scholarship.objects.count()}")
print(f"  - Published: {Scholarship.objects.filter(status='published').count()}")
print(f"  - Draft: {Scholarship.objects.filter(status='draft').count()}")

print(f"\nOpportunities: {Opportunity.objects.count()}")
print(f"  - Published: {Opportunity.objects.filter(status='published').count()}")
print(f"  - Draft: {Opportunity.objects.filter(status='draft').count()}")
