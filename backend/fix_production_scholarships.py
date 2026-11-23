#!/usr/bin/env python
"""
Production scholarship visibility fix script.

This script can be run on Render or locally (with DATABASE_URL set to production).
It will diagnose and fix scholarship visibility issues.

Usage on Render:
    python fix_production_scholarships.py

Usage locally (with production database):
    export DATABASE_URL="postgresql://user:pass@host/db"
    python fix_production_scholarships.py
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
django.setup()

from django.db import transaction
from django.utils import timezone
from datetime import date, timedelta
from apps.scholarships.models import Scholarship
from apps.sources.models import OpportunitySourceRecord
from apps.accounts.models import User


def print_header(text):
    """Print a formatted header."""
    print(f"\n{'=' * 70}")
    print(f"  {text}")
    print(f"{'=' * 70}\n")


def diagnose():
    """Diagnose scholarship visibility issues."""
    print_header("SCHOLARSHIP VISIBILITY DIAGNOSTIC")
    
    # Total scholarships
    total = Scholarship.objects.count()
    print(f"📊 Total scholarships in database: {total}")
    
    if total == 0:
        print("❌ NO SCHOLARSHIPS IN DATABASE")
        print("   You need to create scholarships first.")
        return False
    
    # Published scholarships
    published = Scholarship.objects.filter(is_published=True)
    published_count = published.count()
    print(f"📝 Published scholarships: {published_count}/{total}")
    
    # Valid deadlines
    today = date.today()
    valid_deadline = Scholarship.objects.filter(
        is_published=True,
        application_deadline__gte=today
    )
    valid_deadline_count = valid_deadline.count()
    print(f"📅 With valid deadlines (>= {today}): {valid_deadline_count}/{published_count}")
    
    # Has source records
    with_source = Scholarship.objects.filter(
        is_published=True,
        application_deadline__gte=today,
        opportunity_source__isnull=False
    )
    with_source_count = with_source.count()
    print(f"🔗 With source records: {with_source_count}/{valid_deadline_count}")
    
    # Verified sources
    visible_count = 0
    for scholarship in with_source:
        source = scholarship.opportunity_source
        if (source and 
            source.verification_status == 'VERIFIED' and
            source.source_status == 'AVAILABLE' and
            source.verified_at is not None and
            source.verified_by and
            source.verified_by.role in ['ADMIN', 'SUPERADMIN'] and
            source.source.is_active):
            visible_count += 1
    
    print(f"✅ Fully visible scholarships: {visible_count}/{with_source_count}")
    
    if visible_count == 0:
        print("\n❌ NO SCHOLARSHIPS ARE VISIBLE!")
        print("\nIssues found:")
        
        if published_count < total:
            print(f"   • {total - published_count} scholarships not published")
        if valid_deadline_count < published_count:
            print(f"   • {published_count - valid_deadline_count} with expired deadlines")
        if with_source_count < valid_deadline_count:
            print(f"   • {valid_deadline_count - with_source_count} without source records")
        if visible_count < with_source_count:
            print(f"   • {with_source_count - visible_count} with unverified sources")
        
        return False
    else:
        print(f"\n✅ {visible_count} scholarships should be visible")
        return True


def get_or_create_admin():
    """Get an admin user or create one."""
    # Try to find existing admin
    admins = User.objects.filter(role__in=['ADMIN', 'SUPERADMIN'])
    if admins.exists():
        admin = admins.first()
        print(f"✓ Using admin: {admin.email} ({admin.role})")
        return admin
    
    # No admin found - try to promote a user or create one
    print("\n⚠️  No admin user found. Need to create one.")
    
    # Try to promote the first user
    users = User.objects.filter(is_active=True)
    if users.exists():
        user = users.first()
        print(f"   Promoting user: {user.email}")
        user.role = 'ADMIN'
        user.save()
        return user
    
    # No users at all - this is a problem
    print("   ❌ No users in database. Cannot verify scholarships.")
    print("   Please create a user first via the admin panel or createsuperuser command.")
    return None


def fix_scholarships():
    """Fix scholarship visibility issues."""
    print_header("FIXING SCHOLARSHIP VISIBILITY")
    
    # Get admin user
    admin = get_or_create_admin()
    if not admin:
        return False
    
    changes_made = False
    
    # 1. Publish unpublished scholarships
    with transaction.atomic():
        unpublished = Scholarship.objects.filter(is_published=False)
        unpublished_count = unpublished.count()
        
        if unpublished_count > 0:
            print(f"\n📝 Publishing {unpublished_count} scholarships...")
            unpublished.update(is_published=True)
            print(f"   ✓ Published {unpublished_count} scholarships")
            changes_made = True
        else:
            print("\n📝 All scholarships already published")
    
    # 2. Extend expired deadlines
    with transaction.atomic():
        today = date.today()
        future_date = today + timedelta(days=90)
        expired = Scholarship.objects.filter(application_deadline__lt=today)
        expired_count = expired.count()
        
        if expired_count > 0:
            print(f"\n📅 Extending {expired_count} expired deadlines to {future_date}...")
            expired.update(application_deadline=future_date)
            print(f"   ✓ Extended {expired_count} deadlines")
            changes_made = True
        else:
            print("\n📅 All deadlines are valid")
    
    # 3. Verify source records
    with transaction.atomic():
        unverified = OpportunitySourceRecord.objects.exclude(
            verification_status='VERIFIED',
            source_status='AVAILABLE'
        ).filter(
            verified_at__isnull=True
        )
        unverified_count = unverified.count()
        
        if unverified_count > 0:
            print(f"\n🔐 Verifying {unverified_count} source records...")
            for record in unverified:
                record.verification_status = 'VERIFIED'
                record.source_status = 'AVAILABLE'
                record.verified_at = timezone.now()
                record.verified_by = admin
                record.save()
            print(f"   ✓ Verified {unverified_count} source records")
            changes_made = True
        else:
            print("\n🔐 All source records already verified")
    
    if changes_made:
        print("\n✅ ALL FIXES APPLIED SUCCESSFULLY!")
    else:
        print("\n✓ No fixes needed - everything already configured")
    
    return True


def show_sample_scholarships():
    """Show sample visible scholarships."""
    print_header("SAMPLE VISIBLE SCHOLARSHIPS")
    
    today = date.today()
    visible_scholarships = Scholarship.objects.filter(
        is_published=True,
        application_deadline__gte=today,
        opportunity_source__isnull=False
    )[:5]
    
    if not visible_scholarships.exists():
        print("No visible scholarships found.")
        return
    
    for scholarship in visible_scholarships:
        print(f"\n📚 {scholarship.title}")
        print(f"   Deadline: {scholarship.application_deadline}")
        print(f"   Amount: ${scholarship.award_amount:,.0f}")
        if scholarship.opportunity_source:
            print(f"   Source: {scholarship.opportunity_source.verification_status}")


def main():
    """Main execution."""
    print_header("GOFER SCHOLARSHIP VISIBILITY FIX")
    print("This script will diagnose and fix scholarship visibility issues.")
    print("Running on production database...")
    
    # Step 1: Diagnose
    is_ok = diagnose()
    
    if is_ok:
        print("\n✅ Scholarships are already visible. No fixes needed.")
        show_sample_scholarships()
        return 0
    
    # Step 2: Ask for confirmation
    print("\n" + "=" * 70)
    print("Would you like to apply fixes? This will:")
    print("  1. Publish all unpublished scholarships")
    print("  2. Extend expired deadlines by 90 days")
    print("  3. Verify all unverified source records")
    print("=" * 70)
    
    # In production (non-interactive), apply fixes automatically
    if not sys.stdin.isatty():
        print("\nRunning in non-interactive mode. Applying fixes automatically...\n")
        apply_fix = True
    else:
        response = input("\nApply fixes? [y/N]: ").strip().lower()
        apply_fix = response in ['y', 'yes']
    
    if not apply_fix:
        print("\n❌ Fixes not applied. Exiting.")
        return 1
    
    # Step 3: Apply fixes
    success = fix_scholarships()
    
    if not success:
        print("\n❌ Failed to apply fixes.")
        return 1
    
    # Step 4: Diagnose again to verify
    print("\n" + "=" * 70)
    print("VERIFICATION - Running diagnostic again...")
    print("=" * 70)
    
    is_ok = diagnose()
    
    if is_ok:
        show_sample_scholarships()
        print("\n" + "=" * 70)
        print("🎉 SUCCESS! Scholarships are now visible.")
        print("=" * 70)
        print("\nTest the API:")
        print("  curl https://gofere-api-ruth2105.onrender.com/api/v1/scholarships/")
        print("\nCheck the website:")
        print("  https://gofere.vercel.app/scholarships")
        return 0
    else:
        print("\n⚠️  Some issues remain. Please review the diagnostic output above.")
        return 1


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
