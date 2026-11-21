#!/usr/bin/env python
"""Unpublish scholarships that don't have valid source records"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.scholarships.models import Scholarship

# Find scholarships without valid source records
invalid_scholarships = Scholarship.objects.filter(is_published=True)

for scholarship in invalid_scholarships:
    if not scholarship.source_records_are_verified():
        scholarship.is_published = False
        scholarship.save(update_fields=['is_published'])
        print(f'📝 Unpublished: {scholarship.name} (no valid source records)')
    else:
        print(f'✅ Valid: {scholarship.name}')

print(f'\n📊 Total scholarships: {Scholarship.objects.count()}')
print(f'📊 Published scholarships: {Scholarship.objects.filter(is_published=True).count()}')
