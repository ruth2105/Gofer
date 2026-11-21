#!/usr/bin/env python
"""Create test data for verification"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.scholarships.models import Scholarship
from datetime import datetime, timedelta
import random

# Create test scholarships
countries = ['USA', 'Canada', 'UK', 'Germany', 'Australia']
levels = ['UNDERGRADUATE', 'GRADUATE', 'DOCTORATE']
types = ['FULL', 'PARTIAL', 'MERIT']

for i in range(10):
    Scholarship.objects.get_or_create(
        name=f'Test Scholarship {i+1}',
        defaults={
            'description': f'This is a test scholarship for testing purposes. Number {i+1}. Provides funding for qualified students.',
            'short_description': f'Test scholarship {i+1}',
            'provider': f'Test University {i+1}',
            'country': random.choice(countries),
            'amount': random.randint(5000, 50000),
            'amount_type': 'Full Tuition',
            'type': random.choice(types),
            'level': random.choice(levels),
            'fields': ['Computer Science', 'Engineering'],
            'application_deadline': datetime.now().date() + timedelta(days=random.randint(30, 365)),
            'eligibility': ['Minimum GPA 3.0', 'Acceptance letter required'],
            'application_url': f'https://example.com/apply/{i+1}',
            'is_published': False,  # Cannot publish without source verification
            'is_featured': (i < 3),
            'status': 'OPEN',
            'nationality_eligibility': 'ALL',
            'benefits': ['Tuition coverage', 'Living stipend']
        }
    )

print(f'Total scholarships: {Scholarship.objects.count()}')
