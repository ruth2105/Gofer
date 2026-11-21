#!/usr/bin/env python
"""
Create verified scholarship test data with proper OpportunitySourceRecord entries.
This follows the production workflow for publishing scholarships.
"""
import os
import django
from datetime import date, timedelta
import hashlib

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from django.utils import timezone
from apps.accounts.models import User
from apps.opportunities.models import OpportunitySource, CollectionRun, OpportunitySourceRecord
from apps.scholarships.models import Scholarship
from apps.common.models import Country

def create_test_data():
    print("=" * 60)
    print("CREATING VERIFIED SCHOLARSHIP TEST DATA")
    print("=" * 60)
    
    # Step 1: Create or get admin user
    print("\n[1/7] Creating/Getting Admin User...")
    admin_user = User.objects.filter(role='ADMIN').first()
    if not admin_user:
        admin_user = User.objects.create_user(
            email='admin_test@test.local',
            password='AdminPass123!@#',
            first_name='Admin',
            last_name='Test',
            phone_number='+1234567890',
            role='ADMIN',
            is_verified=True,
            is_staff=True
        )
        print(f"   Created admin user: {admin_user.email}")
    else:
        print(f"   Using existing admin: {admin_user.email}")
    
    # Step 2: Create or get OpportunitySource
    print("\n[2/7] Creating/Getting Opportunity Source...")
    try:
        source = OpportunitySource.objects.get(name='Test Scholarship Database')
        print(f"   Using existing source: {source.name}")
        # Ensure it's active
        if not source.is_active:
            source.is_active = True
            source.save()
            print("   Activated source")
    except OpportunitySource.DoesNotExist:
        source = OpportunitySource.objects.create(
            name='Test Scholarship Database',
            organization='Test Organization',
            base_url='https://test-scholarship-source.example.com',
            source_type='OFFICIAL_PROVIDER',
            collection_method='API',
            is_active=True,
            reliability_status='HEALTHY',
            collection_interval_hours=24
        )
        print(f"   Created source: {source.name}")
    
    # Step 3: Create CollectionRun
    print("\n[3/7] Creating Collection Run...")
    collection_run = CollectionRun.objects.create(
        source=source,
        status='SUCCEEDED',
        records_seen=5,
        records_created=5,
        records_updated=0,
        started_at=timezone.now() - timedelta(hours=1),
        finished_at=timezone.now()
    )
    print(f"   Created collection run: {collection_run.id}")
    
    # Step 4: Get country for scholarships
    print("\n[4/7] Getting Country...")
    ethiopia = Country.objects.filter(code='ET').first()
    if not ethiopia:
        print("   WARNING: Ethiopia country not found, using first available country")
        ethiopia = Country.objects.first()
    
    if ethiopia:
        print(f"   Using country: {ethiopia.name} ({ethiopia.code})")
    else:
        print("   WARNING: No countries found in database")
    
    # Step 5: Create test scholarships
    print("\n[5/7] Creating Test Scholarships...")
    scholarship_data = [
        {
            'name': 'Verified Test Scholarship 1',
            'provider': 'Test University',
            'description': 'A fully verified test scholarship for verification testing.',
            'amount': 10000,
            'type': 'FULL',
            'level': 'UNDERGRADUATE',
            'application_deadline': date.today() + timedelta(days=90)
        },
        {
            'name': 'Verified Test Scholarship 2',
            'provider': 'Test Foundation',
            'description': 'Another verified scholarship for testing public API.',
            'amount': 5000,
            'type': 'PARTIAL',
            'level': 'GRADUATE',
            'application_deadline': date.today() + timedelta(days=60)
        },
        {
            'name': 'Verified Test Scholarship 3',
            'provider': 'Test Organization',
            'description': 'Third verified scholarship for pagination testing.',
            'amount': 15000,
            'type': 'MERIT',
            'level': 'POSTGRADUATE',
            'application_deadline': date.today() + timedelta(days=120)
        },
    ]
    
    scholarships = []
    for data in scholarship_data:
        # Check if scholarship already exists
        existing = Scholarship.objects.filter(name=data['name']).first()
        if existing:
            scholarship = existing
            print(f"   Using existing: {scholarship.name}")
        else:
            scholarship = Scholarship.objects.create(
                **data,
                country='Ethiopia',  # String field
                country_reference=ethiopia,  # Foreign key
                status='OPEN',
                nationality_eligibility='ALL',
                is_featured=False,
                is_published=False,  # Will be published after source record
                website_url='https://test-scholarship.example.com',
                application_url='https://test-scholarship.example.com/apply'
            )
            print(f"   Created: {scholarship.name}")
        scholarships.append(scholarship)
    
    # Step 6: Create verified OpportunitySourceRecords
    print("\n[6/7] Creating Verified Source Records...")
    for i, scholarship in enumerate(scholarships, 1):
        # Generate unique content hash
        content_str = f"{scholarship.name}_{scholarship.provider}_{scholarship.application_deadline}"
        content_hash = hashlib.sha256(content_str.encode()).hexdigest()
        identity_hash = hashlib.sha256(f"{source.base_url}_{i}".encode()).hexdigest()
        
        # Check if source record exists
        existing_record = OpportunitySourceRecord.objects.filter(
            source=source,
            source_record_key=f'test_scholarship_{i}'
        ).first()
        
        if existing_record:
            source_record = existing_record
            print(f"   Using existing record for: {scholarship.name}")
        else:
            source_record = OpportunitySourceRecord.objects.create(
                source=source,
                collection_run=collection_run,
                scholarship=scholarship,
                source_record_key=f'test_scholarship_{i}',
                official_source_url=scholarship.website_url,
                official_application_url=scholarship.application_url or '',
                source_title=scholarship.name,
                normalized_title=scholarship.name,
                normalized_organization=scholarship.provider,
                normalized_deadline=scholarship.application_deadline,
                eligibility_scope='UNSPECIFIED',
                content_hash=content_hash,
                identity_fingerprint=identity_hash,
                source_status='AVAILABLE',
                verification_status='VERIFIED',
                verified_at=timezone.now(),
                verified_by=admin_user
            )
            print(f"   Created verified record for: {scholarship.name}")
    
    # Step 7: Publish scholarships
    print("\n[7/7] Publishing Scholarships...")
    for scholarship in scholarships:
        if not scholarship.is_published:
            scholarship.is_published = True
            scholarship.save()
            print(f"   Published: {scholarship.name}")
        else:
            print(f"   Already published: {scholarship.name}")
    
    # Verification
    print("\n" + "=" * 60)
    print("VERIFICATION")
    print("=" * 60)
    
    print(f"\nScholarships created: {len(scholarships)}")
    published_count = Scholarship.objects.filter(is_published=True).count()
    print(f"Published scholarships: {published_count}")
    
    verified_records = OpportunitySourceRecord.objects.filter(
        verification_status='VERIFIED',
        source_status='AVAILABLE',
        source__is_active=True
    ).count()
    print(f"Verified source records: {verified_records}")
    
    # Test get_public_scholarships query
    from apps.scholarships.services.matching import get_public_scholarships
    public_scholarships = get_public_scholarships()
    print(f"\nPublic scholarships visible: {public_scholarships.count()}")
    
    if public_scholarships.exists():
        print("\nPublic scholarships:")
        for s in public_scholarships[:5]:
            print(f"  - {s.name} ({s.provider})")
    else:
        print("\nWARNING: No scholarships visible in public API!")
        print("Debugging info:")
        all_scholarships = Scholarship.objects.filter(is_published=True)
        for s in all_scholarships:
            records = s.source_records.all()
            print(f"\n  Scholarship: {s.name}")
            print(f"    is_published: {s.is_published}")
            print(f"    source_records count: {records.count()}")
            for r in records:
                print(f"      - verification_status: {r.verification_status}")
                print(f"      - source_status: {r.source_status}")
                print(f"      - source.is_active: {r.source.is_active}")
                print(f"      - verified_by: {r.verified_by}")
                print(f"      - verified_at: {r.verified_at}")
    
    print("\n" + "=" * 60)
    print("TEST DATA CREATION COMPLETE")
    print("=" * 60)
    
    return {
        'admin_user': admin_user,
        'source': source,
        'collection_run': collection_run,
        'scholarships': scholarships,
        'public_count': public_scholarships.count()
    }

if __name__ == '__main__':
    result = create_test_data()
    print(f"\nSummary: Created {len(result['scholarships'])} scholarships, {result['public_count']} visible publicly")
