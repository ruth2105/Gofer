#!/usr/bin/env python
"""Publish test scholarships for verification"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.scholarships.models import Scholarship

# Update all scholarships to published
count = Scholarship.objects.filter(is_published=False).update(is_published=True)
print(f'✅ Published {count} scholarships')

# Verify
total = Scholarship.objects.count()
published = Scholarship.objects.filter(is_published=True).count()
print(f'📊 Total: {total}, Published: {published}')
