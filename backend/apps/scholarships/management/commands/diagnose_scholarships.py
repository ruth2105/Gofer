"""
Diagnostic command to investigate why scholarships aren't visible in production.
Checks publication status, deadlines, verification status, and source records.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date
from apps.scholarships.models import Scholarship
from apps.sources.models import OpportunitySourceRecord


class Command(BaseCommand):
    help = 'Diagnose scholarship visibility issues'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n=== SCHOLARSHIP VISIBILITY DIAGNOSTIC ===\n'))
        
        # Total scholarships
        total_scholarships = Scholarship.objects.count()
        self.stdout.write(f'Total scholarships in database: {total_scholarships}')
        
        if total_scholarships == 0:
            self.stdout.write(self.style.ERROR('\n❌ NO SCHOLARSHIPS IN DATABASE'))
            self.stdout.write('This explains why nothing is visible.')
            return
        
        # Published scholarships
        published = Scholarship.objects.filter(is_published=True)
        published_count = published.count()
        self.stdout.write(f'Published scholarships (is_published=True): {published_count}')
        
        # Scholarships with valid deadlines
        today = date.today()
        valid_deadline = Scholarship.objects.filter(
            is_published=True,
            application_deadline__gte=today
        )
        valid_deadline_count = valid_deadline.count()
        self.stdout.write(f'Published with valid deadline (>= {today}): {valid_deadline_count}')
        
        # Check OpportunitySourceRecord requirements
        self.stdout.write('\n--- Checking OpportunitySourceRecord requirements ---')
        
        scholarships_with_source = Scholarship.objects.filter(
            is_published=True,
            application_deadline__gte=today,
            opportunity_source__isnull=False
        )
        self.stdout.write(f'Published + valid deadline + has source: {scholarships_with_source.count()}')
        
        # Check verified source records
        verified_sources = OpportunitySourceRecord.objects.filter(
            verification_status='VERIFIED',
            source_status='AVAILABLE',
            verified_at__isnull=False
        )
        self.stdout.write(f'Verified OpportunitySourceRecords: {verified_sources.count()}')
        
        # Scholarships that should be visible
        visible_scholarships = []
        for scholarship in scholarships_with_source:
            source_record = scholarship.opportunity_source
            if (source_record and 
                source_record.verification_status == 'VERIFIED' and
                source_record.source_status == 'AVAILABLE' and
                source_record.verified_at is not None and
                source_record.verified_by and
                source_record.verified_by.role in ['ADMIN', 'SUPERADMIN'] and
                source_record.source.is_active):
                visible_scholarships.append(scholarship)
        
        self.stdout.write(f'\n✓ Scholarships that SHOULD BE VISIBLE: {len(visible_scholarships)}')
        
        if len(visible_scholarships) == 0:
            self.stdout.write(self.style.ERROR('\n❌ NO SCHOLARSHIPS MEET VISIBILITY CRITERIA'))
            self.stdout.write('\nBreakdown of issues:')
            
            # Detailed breakdown
            unpublished = total_scholarships - published_count
            if unpublished > 0:
                self.stdout.write(f'  - {unpublished} not published (is_published=False)')
            
            expired = published_count - valid_deadline_count
            if expired > 0:
                self.stdout.write(f'  - {expired} published but deadline passed')
            
            no_source = valid_deadline_count - scholarships_with_source.count()
            if no_source > 0:
                self.stdout.write(f'  - {no_source} published + valid deadline but no source record')
            
            unverified = scholarships_with_source.count() - len(visible_scholarships)
            if unverified > 0:
                self.stdout.write(f'  - {unverified} published + valid deadline + has source but source not verified')
                
                # Show specific verification issues
                self.stdout.write('\n  Verification issues found:')
                for scholarship in scholarships_with_source:
                    source = scholarship.opportunity_source
                    if source:
                        issues = []
                        if source.verification_status != 'VERIFIED':
                            issues.append(f"status={source.verification_status}")
                        if source.source_status != 'AVAILABLE':
                            issues.append(f"source_status={source.source_status}")
                        if source.verified_at is None:
                            issues.append("not verified_at")
                        if not source.verified_by:
                            issues.append("no verified_by")
                        elif source.verified_by.role not in ['ADMIN', 'SUPERADMIN']:
                            issues.append(f"verified_by role={source.verified_by.role}")
                        if not source.source.is_active:
                            issues.append("source not active")
                        
                        if issues:
                            self.stdout.write(f'    • {scholarship.title[:50]}: {", ".join(issues)}')
        else:
            self.stdout.write(self.style.SUCCESS(f'\n✓ {len(visible_scholarships)} scholarships should be visible'))
            self.stdout.write('\nSample visible scholarships:')
            for scholarship in visible_scholarships[:5]:
                self.stdout.write(f'  • {scholarship.title} (deadline: {scholarship.application_deadline})')
        
        # Check if there are any scholarships at all
        self.stdout.write('\n--- Sample scholarship data ---')
        sample_scholarships = Scholarship.objects.all()[:3]
        for scholarship in sample_scholarships:
            self.stdout.write(f'\n{scholarship.title}')
            self.stdout.write(f'  Published: {scholarship.is_published}')
            self.stdout.write(f'  Deadline: {scholarship.application_deadline}')
            self.stdout.write(f'  Has source: {scholarship.opportunity_source is not None}')
            if scholarship.opportunity_source:
                source = scholarship.opportunity_source
                self.stdout.write(f'  Source verification: {source.verification_status}')
                self.stdout.write(f'  Source status: {source.source_status}')
                self.stdout.write(f'  Verified at: {source.verified_at}')
                self.stdout.write(f'  Verified by: {source.verified_by}')
        
        self.stdout.write(self.style.SUCCESS('\n=== END DIAGNOSTIC ===\n'))
