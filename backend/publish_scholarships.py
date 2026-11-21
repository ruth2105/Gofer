#!/usr/bin/env python
"""Publish all scholarships for testing."""
import os
import django
from django.utils import timezone

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.scholarships.models import Scholarship

# Publish all scholarships
count = Scholarship.objects.filter(is_published=False).update(
    is_published=True,
    published_at=timezone.now()
)

print(f"Published {count} scholarships")
print(f"Total published scholarships: {Scholarship.objects.filter(is_published=True).count()}")
