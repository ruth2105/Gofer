#!/usr/bin/env python
"""Check scholarship statuses."""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.scholarships.models import Scholarship
from django.db.models import Count

print(f"Total scholarships: {Scholarship.objects.count()}")
print("\nBy status:")
for item in Scholarship.objects.values('status').annotate(count=Count('id')):
    print(f"  {item['status']}: {item['count']}")

print("\nAll scholarships:")
for s in Scholarship.objects.all():
    print(f"- {s.name} - Status: {s.status}")
