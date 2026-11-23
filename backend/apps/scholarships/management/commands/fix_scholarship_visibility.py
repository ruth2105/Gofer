"""
Management command to fix scholarship visibility by ensuring they are:
1. Published (is_published=True)
2. Have valid deadlines (application_deadline >= today)
3. Have verified OpportunitySourceRecords

This can be run on production to make existing scholarships visible.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from datetime import date, timedelta
from apps.scholarships.models import Scholarship
from apps.sources.models import OpportunitySourceRecord, OpportunitySource
from apps.accounts.models import User


class Command(BaseCommand):
    help = 'Fix scholarship visibility by updating publication and verification status'

    def add_arguments(self, parser):
        parser.add_argument(
            '--publish-all',
            action='store_true',
            help='Publish all unpublished scholarships',
        )
        parser.add_argument(
            '--extend-deadlines',
            action='store_true',
            help='Extend expired deadlines to 3 months from today',
        )
        parser.add_argument(
            '--verify-sources',
            action='store_true',
            help='Verify all unverified OpportunitySourceRecords',
        )
        parser.add_argument(
            '--admin-email',
            type=str,
            help='Email of admin user to use as verified_by (required for --verify-sources)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be changed without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('\n=== DRY RUN MODE - NO CHANGES WILL BE MADE ===\n'))
        
        self.stdout.write(self.style.SUCCESS('\n=== SCHOLARSHIP VISIBILITY FIX ===\n'))
        
        changes_made = False
        
        # Publish all scholarships
        if options['publish_all']:
            unpublished = Scholarship.objects.filter(is_published=False)
            count = unpublished.count()
            if count > 0:
                self.stdout.write(f'Found {count} unpublished scholarships')
                if not dry_run:
                    with transaction.atomic():
                        unpublished.update(is_published=True)
                    self.stdout.write(self.style.SUCCESS(f'✓ Published {count} scholarships'))
                else:
                    self.stdout.write(f'Would publish {count} scholarships')
                changes_made = True
            else:
                self.stdout.write('All scholarships are already published')
        
        # Extend expired deadlines
        if options['extend_deadlines']:
            today = date.today()
            future_date = today + timedelta(days=90)
            expired = Scholarship.objects.filter(application_deadline__lt=today)
            count = expired.count()
            if count > 0:
                self.stdout.write(f'\nFound {count} scholarships with expired deadlines')
                if not dry_run:
                    with transaction.atomic():
                        expired.update(application_deadline=future_date)
                    self.stdout.write(self.style.SUCCESS(f'✓ Extended {count} deadlines to {future_date}'))
                else:
                    self.stdout.write(f'Would extend {count} deadlines to {future_date}')
                changes_made = True
            else:
                self.stdout.write('\nAll scholarships have valid deadlines')
        
        # Verify source records
        if options['verify_sources']:
            if not options['admin_email']:
                self.stdout.write(self.style.ERROR('\n❌ --admin-email is required for --verify-sources'))
                return
            
            try:
                admin_user = User.objects.get(email=options['admin_email'])
                if admin_user.role not in ['ADMIN', 'SUPERADMIN']:
                    self.stdout.write(self.style.ERROR(f'\n❌ User {options["admin_email"]} is not an admin (role: {admin_user.role})'))
                    return
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'\n❌ User with email {options["admin_email"]} not found'))
                return
            
            unverified = OpportunitySourceRecord.objects.exclude(
                verification_status='VERIFIED',
                source_status='AVAILABLE',
                verified_at__isnull=False,
                verified_by__isnull=False
            )
            count = unverified.count()
            
            if count > 0:
                self.stdout.write(f'\nFound {count} unverified source records')
                if not dry_run:
                    with transaction.atomic():
                        for record in unverified:
                            record.verification_status = 'VERIFIED'
                            record.source_status = 'AVAILABLE'
                            record.verified_at = timezone.now()
                            record.verified_by = admin_user
                            record.save()
                    self.stdout.write(self.style.SUCCESS(f'✓ Verified {count} source records'))
                else:
                    self.stdout.write(f'Would verify {count} source records')
                changes_made = True
            else:
                self.stdout.write('\nAll source records are already verified')
        
        if not changes_made:
            self.stdout.write(self.style.WARNING('\nNo changes specified. Use --help to see available options.'))
        
        # Show current status
        self.stdout.write('\n--- Current Status ---')
        total = Scholarship.objects.count()
        published = Scholarship.objects.filter(is_published=True).count()
        today = date.today()
        valid_deadline = Scholarship.objects.filter(
            is_published=True,
            application_deadline__gte=today
        ).count()
        
        self.stdout.write(f'Total scholarships: {total}')
        self.stdout.write(f'Published: {published}')
        self.stdout.write(f'Published + valid deadline: {valid_deadline}')
        
        verified_sources = OpportunitySourceRecord.objects.filter(
            verification_status='VERIFIED',
            source_status='AVAILABLE',
            verified_at__isnull=False,
            verified_by__isnull=False
        ).count()
        self.stdout.write(f'Verified source records: {verified_sources}')
        
        self.stdout.write(self.style.SUCCESS('\n=== END FIX ===\n'))
        
        if dry_run:
            self.stdout.write(self.style.WARNING('NOTE: This was a dry run. Add the flags without --dry-run to apply changes.\n'))
