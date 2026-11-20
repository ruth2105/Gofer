
from datetime import timedelta

from django.contrib.admin.sites import AdminSite
from django.contrib.messages.storage.fallback import FallbackStorage
from django.core.exceptions import ValidationError
from django.test import RequestFactory, TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.scholarships.models import Scholarship

from .admin import OpportunitySourceRecordAdmin
from .models import (
    CollectionRun,
    Opportunity,
    OpportunitySource,
    OpportunitySourceRecord,
)


def create_verified_opportunity_source(opportunity, verifier=None):
    verifier = verifier or User.objects.create_user(
        email=f'verifier-{opportunity.pk}@example.org',
        password='SecurePassword123!',
        role='ADMIN',
    )
    source_host = f'{opportunity.pk}.example.org'
    source = OpportunitySource.objects.create(
        name=f'Official source {opportunity.pk}',
        organization=opportunity.organization,
        base_url=f'https://{source_host}/',
        source_type='OFFICIAL_PROVIDER',
        collection_method='API',
        is_active=True,
    )
    run = CollectionRun.objects.create(source=source)
    return OpportunitySourceRecord.objects.create(
        source=source,
        collection_run=run,
        opportunity=opportunity,
        source_record_key=f'opportunity-{opportunity.pk}',
        official_source_url=f'https://{source_host}/listing/',
        official_application_url=opportunity.application_url,
        source_title=opportunity.title,
        normalized_title=opportunity.title.lower(),
        normalized_organization=opportunity.organization.lower(),
        normalized_deadline=opportunity.application_deadline,
        eligibility_scope=opportunity.eligibility_scope,
        eligible_nationalities=opportunity.eligible_nationalities,
        excluded_nationalities=opportunity.excluded_nationalities,
        eligibility_notes=opportunity.eligibility_notes,
        source_payload={'title': opportunity.title},
        content_hash='a' * 64,
        identity_fingerprint='b' * 64,
        verification_status='VERIFIED',
        verified_at=timezone.now(),
        verified_by=verifier,
    )


class OpportunitySourceTests(TestCase):
    def setUp(self):
        self.source_data = {
            'name': 'Example Foundation',
            'organization': 'Example Organization',
            'base_url': 'https://example.org/',
            'source_type': 'OFFICIAL_PROVIDER',
            'collection_method': 'PERMITTED_HTML',
        }

    def test_source_defaults(self):
        source = OpportunitySource.objects.create(
            **self.source_data
        )

        self.assertFalse(source.is_active)
        self.assertEqual(source.reliability_status, 'UNKNOWN')
        self.assertEqual(source.collection_interval_hours, 24)

    def test_source_normalizes_urls(self):
        source = OpportunitySource.objects.create(
            **{
                **self.source_data,
                'base_url': 'HTTPS://EXAMPLE.ORG:443/',
                'terms_url': 'HTTPS://EXAMPLE.ORG/TERMS/',
                'robots_url': 'HTTPS://EXAMPLE.ORG/ROBOTS.TXT/',
            }
        )

        self.assertEqual(source.base_url, 'https://example.org/')
        self.assertEqual(source.terms_url, 'https://example.org/TERMS')
        self.assertEqual(source.robots_url, 'https://example.org/ROBOTS.TXT')

    def test_duplicate_normalized_source_url_is_rejected(self):
        OpportunitySource.objects.create(**self.source_data)

        with self.assertRaises(ValidationError):
            OpportunitySource.objects.create(
                **{
                    **self.source_data,
                    'name': 'Another Source',
                    'base_url': 'HTTPS://EXAMPLE.ORG:443/',
                }
            )

    def test_invalid_collection_interval_is_rejected(self):
        with self.assertRaises(ValidationError):
            OpportunitySource.objects.create(
                **{
                    **self.source_data,
                    'collection_interval_hours': 0,
                }
            )

    def test_disabled_source_cannot_be_active(self):
        with self.assertRaises(ValidationError):
            OpportunitySource.objects.create(
                **{
                    **self.source_data,
                    'is_active': True,
                    'reliability_status': 'DISABLED',
                }
            )


class CollectionRunTests(TestCase):
    def setUp(self):
        self.source = OpportunitySource.objects.create(
            name='Example Foundation',
            organization='Example Organization',
            base_url='https://example.org/',
            source_type='OFFICIAL_PROVIDER',
            collection_method='PERMITTED_HTML',
        )

    def test_collection_run_defaults(self):
        run = CollectionRun.objects.create(
            source=self.source,
        )

        self.assertEqual(run.status, 'RUNNING')
        self.assertEqual(run.trigger_type, 'MANUAL')
        self.assertEqual(run.records_seen, 0)
        self.assertIsNone(run.finished_at)

    def test_collection_run_uses_uuid(self):
        run = CollectionRun.objects.create(
            source=self.source,
        )

        self.assertIsNotNone(run.id)

    def test_completed_run_requires_valid_completion_time(self):
        with self.assertRaises(ValidationError):
            CollectionRun.objects.create(
                source=self.source,
                status='SUCCEEDED',
            )

    def test_running_run_cannot_have_completion_time(self):
        with self.assertRaises(ValidationError):
            CollectionRun.objects.create(
                source=self.source,
                status='RUNNING',
                finished_at=timezone.now(),
            )

    def test_negative_counters_are_rejected(self):
        with self.assertRaises(ValidationError):
            CollectionRun.objects.create(
                source=self.source,
                records_seen=-1,
            )


class OpportunitySourceRecordTests(TestCase):
    def setUp(self):
        self.source = OpportunitySource.objects.create(
            name='Example Foundation',
            organization='Example Organization',
            base_url='https://example.org/',
            source_type='OFFICIAL_PROVIDER',
            collection_method='PERMITTED_HTML',
            is_active=True,
        )

        self.other_source = OpportunitySource.objects.create(
            name='Another Foundation',
            organization='Another Organization',
            base_url='https://another-example.org/',
            source_type='OFFICIAL_PROVIDER',
            collection_method='PERMITTED_HTML',
        )

        self.run = CollectionRun.objects.create(
            source=self.source,
        )

        self.other_run = CollectionRun.objects.create(
            source=self.other_source,
        )

    def record_kwargs(self, **overrides):
        data = {
            'source': self.source,
            'collection_run': self.run,
            'source_record_key': 'example-1',
            'official_source_url': 'https://example.org/opportunities/1/',
            'official_application_url': 'https://example.org/apply/1/',
            'source_title': 'Example opportunity',
            'normalized_title': 'example opportunity',
            'normalized_organization': 'example foundation',
            'eligibility_scope': 'ETHIOPIA_AND_OTHERS',
            'eligible_nationalities': ['ET', 'KE', 'NG'],
            'excluded_nationalities': [],
            'eligibility_notes': (
                'Applicants from eligible low- and middle-income '
                'countries may apply.'
            ),
            'source_payload': {
                'title': 'Example opportunity',
            },
            'content_hash': 'a' * 64,
            'identity_fingerprint': 'b' * 64,
        }

        opportunity = overrides.get('opportunity')
        if opportunity:
            data.update({
                'normalized_deadline': opportunity.application_deadline,
                'eligibility_scope': opportunity.eligibility_scope,
                'eligible_nationalities': opportunity.eligible_nationalities,
                'excluded_nationalities': opportunity.excluded_nationalities,
                'eligibility_notes': opportunity.eligibility_notes,
                'official_application_url': opportunity.application_url,
            })

        scholarship = overrides.get('scholarship')
        if scholarship:
            data.update({
                'normalized_deadline': scholarship.application_deadline,
                'official_application_url': scholarship.application_url or '',
            })

        data.update(overrides)
        return data

    def test_source_record_defaults(self):
        record = OpportunitySourceRecord.objects.create(
            **self.record_kwargs()
        )

        self.assertEqual(record.source_status, 'AVAILABLE')
        self.assertEqual(record.verification_status, 'DISCOVERED')
        self.assertIsNone(record.scholarship)
        self.assertIsNone(record.opportunity)

    def test_source_record_uses_uuid(self):
        record = OpportunitySourceRecord.objects.create(
            **self.record_kwargs()
        )

        self.assertIsNotNone(record.id)

    def test_source_record_normalizes_urls(self):
        record = OpportunitySourceRecord.objects.create(
            **self.record_kwargs(
                official_source_url=(
                    'HTTPS://EXAMPLE.ORG:443/OPPORTUNITIES/1/'
                ),
                official_application_url=(
                    'HTTPS://EXAMPLE.ORG:443/APPLY/1/'
                ),
            )
        )

        self.assertEqual(
            record.official_source_url,
            'https://example.org/OPPORTUNITIES/1',
        )

        self.assertEqual(
            record.official_application_url,
            'https://example.org/APPLY/1',
        )

    def test_duplicate_source_record_key_is_rejected(self):
        OpportunitySourceRecord.objects.create(
            **self.record_kwargs()
        )

        with self.assertRaises(ValidationError):
            OpportunitySourceRecord.objects.create(
                **self.record_kwargs()
            )

    def test_collection_run_must_belong_to_source(self):
        with self.assertRaises(ValidationError):
            OpportunitySourceRecord.objects.create(
                **self.record_kwargs(
                    collection_run=self.other_run
                )
            )

    def test_verified_record_requires_verifier_metadata(self):
        # A verified record without verifier metadata must be rejected.
        with self.assertRaises(ValidationError):
            OpportunitySourceRecord.objects.create(
                **self.record_kwargs(
                    verification_status='VERIFIED'
                )
            )

        verifier = User.objects.create_user(
            email='admin@example.com',
            password='SecurePassword123!',
            role='ADMIN',
        )

        scholarship = Scholarship.objects.create(
            name='Verified test scholarship',
            description='Test scholarship description',
            provider='Example Foundation',
            country='Ethiopia',
            type='FULL',
            level='GRADUATE',
            amount=1000,
            application_url='https://example.org/apply/',
            application_deadline=(
                timezone.now() + timedelta(days=30)
            ).date(),
        )

        record = OpportunitySourceRecord.objects.create(
            **self.record_kwargs(
                scholarship=scholarship,
                verification_status='VERIFIED',
                verified_at=timezone.now(),
                verified_by=verifier,
            )
        )

        self.assertEqual(record.verified_by, verifier)
        self.assertEqual(record.scholarship, scholarship)

    def test_external_scholarship_cannot_publish_until_source_is_verified(self):
        scholarship = Scholarship.objects.create(
            name='Source-backed scholarship',
            description='A source-backed scholarship.',
            provider='Example Foundation',
            country='Ethiopia',
            type='FULL',
            level='GRADUATE',
            amount=1000,
            application_url='https://example.org/apply/',
            application_deadline=(
                timezone.now() + timedelta(days=30)
            ).date(),
        )
        record = OpportunitySourceRecord.objects.create(
            **self.record_kwargs(scholarship=scholarship)
        )

        scholarship.is_published = True
        with self.assertRaises(ValidationError):
            scholarship.save()

        verifier = User.objects.create_user(
            email='scholarship-reviewer@example.com',
            password='SecurePassword123!',
            role='ADMIN',
        )
        record.verification_status = 'VERIFIED'
        record.verified_at = timezone.now()
        record.verified_by = verifier
        record.save()

        scholarship.is_published = True
        scholarship.save()
        scholarship.refresh_from_db()
        self.assertTrue(scholarship.is_published)

    def test_unavailable_linked_source_unpublishes_scholarship(self):
        scholarship = Scholarship.objects.create(
            name='Verified scholarship',
            description='A verified scholarship.',
            provider='Example Foundation',
            country='Ethiopia',
            type='FULL',
            level='GRADUATE',
            amount=1000,
            application_url='https://example.org/apply/',
            application_deadline=(
                timezone.now() + timedelta(days=30)
            ).date(),
        )
        verifier = User.objects.create_user(
            email='scholarship-verifier@example.com',
            password='SecurePassword123!',
            role='ADMIN',
        )
        record = OpportunitySourceRecord.objects.create(
            **self.record_kwargs(
                scholarship=scholarship,
                verification_status='VERIFIED',
                verified_at=timezone.now(),
                verified_by=verifier,
            )
        )
        scholarship.is_published = True
        scholarship.save()

        record.source_status = 'UNAVAILABLE'
        record.save()

        scholarship.refresh_from_db()
        record.refresh_from_db()
        self.assertFalse(scholarship.is_published)
        self.assertEqual(record.verification_status, 'SOURCE_UNAVAILABLE')
        self.assertIsNone(record.verified_at)
        self.assertIsNone(record.verified_by_id)

    def test_disabling_linked_source_unpublishes_scholarship(self):
        scholarship = Scholarship.objects.create(
            name='Active source scholarship',
            description='A scholarship from an active source.',
            provider='Example Foundation',
            country='Ethiopia',
            type='FULL',
            level='GRADUATE',
            amount=1000,
            application_url='https://example.org/apply/',
            application_deadline=(
                timezone.now() + timedelta(days=30)
            ).date(),
        )
        verifier = User.objects.create_user(
            email='active-source-verifier@example.com',
            password='SecurePassword123!',
            role='ADMIN',
        )
        OpportunitySourceRecord.objects.create(
            **self.record_kwargs(
                scholarship=scholarship,
                verification_status='VERIFIED',
                verified_at=timezone.now(),
                verified_by=verifier,
            )
        )
        scholarship.is_published = True
        scholarship.save()

        self.source.is_active = False
        self.source.save()

        scholarship.refresh_from_db()
        self.assertFalse(scholarship.is_published)

    def test_optional_scholarship_and_verifier_deletions_preserve_record(self):
        scholarship = Scholarship.objects.create(
            name='Linked scholarship',
            description='Description',
            provider='Example Foundation',
            country='Ethiopia',
            type='FULL',
            level='GRADUATE',
            amount=1000,
            application_deadline=(
                timezone.now() + timedelta(days=30)
            ).date(),
        )

        verifier = User.objects.create_user(
            email='reviewer@example.com',
            password='SecurePassword123!',
            role='ADMIN',
        )

        record = OpportunitySourceRecord.objects.create(
            **self.record_kwargs(
                scholarship=scholarship,
            )
        )

        record.scholarship = scholarship
        record.save()

        scholarship.delete()
        record.refresh_from_db()

        self.assertIsNone(record.scholarship)

        record.verification_status = 'VERIFIED'
        record.verified_at = timezone.now()
        record.verified_by = verifier
        record.opportunity = Opportunity.objects.create(
            title='Test linked opportunity',
            description='Test description',
            organization='Example Organization',
            category='INTERNSHIP',
        )
        record.normalized_deadline = record.opportunity.application_deadline
        record.eligibility_scope = record.opportunity.eligibility_scope
        record.eligible_nationalities = record.opportunity.eligible_nationalities
        record.excluded_nationalities = record.opportunity.excluded_nationalities
        record.eligibility_notes = record.opportunity.eligibility_notes
        record.official_application_url = record.opportunity.application_url
        record.save()

        verifier.delete()
        record.refresh_from_db()

        self.assertIsNone(record.verified_by)
        self.assertIsNotNone(record.opportunity)

    def test_payload_must_be_json_object(self):
        with self.assertRaises(ValidationError):
            OpportunitySourceRecord.objects.create(
                **self.record_kwargs(
                    source_payload=['not', 'an', 'object']
                )
            )

    def test_invalid_fingerprint_is_rejected(self):
        with self.assertRaises(ValidationError):
            OpportunitySourceRecord.objects.create(
                **self.record_kwargs(
                    content_hash='invalid-fingerprint'
                )
            )

    def test_invalid_nationality_code_is_rejected(self):
        with self.assertRaises(ValidationError):
            OpportunitySourceRecord.objects.create(
                **self.record_kwargs(
                    eligible_nationalities=['ET', 'ethiopia']
                )
            )

    def test_unavailable_source_record_cannot_be_verified(self):
        verifier = User.objects.create_user(
            email='reviewer@example.com',
            password='SecurePassword123!',
            role='ADMIN',
        )
        opportunity = Opportunity.objects.create(
            title='Verified record target',
            description='Description',
            organization='Example Organization',
            category='INTERNSHIP',
            application_url='https://example.org/apply/',
        )

        with self.assertRaises(ValidationError):
            OpportunitySourceRecord.objects.create(
                **self.record_kwargs(
                    opportunity=opportunity,
                    source_status='UNAVAILABLE',
                    verification_status='VERIFIED',
                    verified_at=timezone.now(),
                    verified_by=verifier,
                )
            )

    def test_non_admin_cannot_be_recorded_as_verifier(self):
        student = User.objects.create_user(
            email='student@example.com',
            password='SecurePassword123!',
            role='STUDENT',
        )
        opportunity = Opportunity.objects.create(
            title='Student verified record target',
            description='Description',
            organization='Example Organization',
            category='INTERNSHIP',
            application_url='https://example.org/apply/',
        )

        with self.assertRaises(ValidationError):
            OpportunitySourceRecord.objects.create(
                **self.record_kwargs(
                    opportunity=opportunity,
                    verification_status='VERIFIED',
                    verified_at=timezone.now(),
                    verified_by=student,
                )
            )

    def test_overlapping_nationalities_are_rejected(self):
        with self.assertRaises(ValidationError):
            OpportunitySourceRecord.objects.create(
                **self.record_kwargs(
                    eligible_nationalities=['ET', 'KE'],
                    excluded_nationalities=['KE'],
                )
            )

    def test_ethiopia_only_requires_only_et(self):
        with self.assertRaises(ValidationError):
            OpportunitySourceRecord.objects.create(
                **self.record_kwargs(
                    eligibility_scope='ETHIOPIA_ONLY',
                    eligible_nationalities=['ET', 'KE'],
                )
            )

    def test_source_record_cannot_link_to_both_public_targets(self):
        scholarship = Scholarship.objects.create(
            name='Another scholarship',
            description='Description',
            provider='Example Foundation',
            country='Ethiopia',
            type='FULL',
            level='GRADUATE',
            amount=1000,
            application_deadline=(
                timezone.now() + timedelta(days=30)
            ).date(),
        )

        opportunity = Opportunity.objects.create(
            title='Another opportunity',
            description='Description',
            organization='Example Organization',
            category='INTERNSHIP',
        )

        with self.assertRaises(ValidationError):
            OpportunitySourceRecord.objects.create(
                **self.record_kwargs(
                    scholarship=scholarship,
                    opportunity=opportunity,
                )
            )


class OpportunityModelTests(TestCase):
    def valid_opportunity_data(self, **overrides):
        return {
            'title': 'Global Research Fellowship',
            'description': 'A research fellowship description.',
            'organization': 'Example Institute',
            'category': 'FELLOWSHIP',
            'country': 'Ethiopia',
            'application_url': 'https://example.org/apply/',
            **overrides,
        }

    def test_unpublished_opportunities_are_the_default(self):
        opportunity = Opportunity.objects.create(
            **self.valid_opportunity_data()
        )

        self.assertFalse(opportunity.is_published)
        self.assertEqual(opportunity.slug, 'global-research-fellowship')

    def test_duplicate_title_and_organization_are_rejected(self):
        Opportunity.objects.create(**self.valid_opportunity_data())

        with self.assertRaises(ValidationError):
            Opportunity.objects.create(
                **self.valid_opportunity_data(
                    title='global research fellowship',
                )
            )

    def test_published_opportunity_requires_official_link(self):
        with self.assertRaises(ValidationError):
            Opportunity.objects.create(
                **self.valid_opportunity_data(
                    application_url='',
                    is_published=True,
                )
            )

    def test_published_opportunity_requires_linked_source_records_verified(self):
        opportunity = Opportunity.objects.create(
            **self.valid_opportunity_data()
        )
        source = OpportunitySource.objects.create(
            name='Research Institute',
            organization='Example Institute',
            base_url='https://example.org/',
            source_type='OFFICIAL_PROVIDER',
            collection_method='API',
        )
        run = CollectionRun.objects.create(source=source)
        OpportunitySourceRecord.objects.create(
            source=source,
            collection_run=run,
            opportunity=opportunity,
            source_record_key='fellowship-1',
            official_source_url='https://example.org/fellowship/',
            official_application_url='https://example.org/apply/',
            source_title=opportunity.title,
            normalized_title=opportunity.title.lower(),
            normalized_organization=opportunity.organization.lower(),
            source_payload={'title': opportunity.title},
            content_hash='a' * 64,
            identity_fingerprint='b' * 64,
        )

        opportunity.is_published = True
        with self.assertRaises(ValidationError):
            opportunity.save()


class OpportunityApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = '/api/v1/opportunities/'
        self.published = Opportunity.objects.create(
            title='Global Research Fellowship',
            description='Research placement for emerging scientists.',
            short_description='A research fellowship.',
            organization='Example Institute',
            country='Ethiopia',
            category='FELLOWSHIP',
            level='GRADUATE',
            eligibility_scope='ETHIOPIA_AND_OTHERS',
            eligible_nationalities=['ET', 'KE'],
            excluded_nationalities=['US'],
            eligibility_notes='Applicants must meet the provider criteria.',
            documents_required=['Academic transcript', 'Reference letter'],
            application_deadline=(timezone.now() + timedelta(days=30)).date(),
            application_url='https://example.org/apply/',
            official_website='https://example.org/',
        )
        create_verified_opportunity_source(self.published)
        self.published.is_published = True
        self.published.save()
        self.draft = Opportunity.objects.create(
            title='Private Training Opportunity',
            description='A private, unpublished training listing.',
            organization='Example Training Center',
            category='TRAINING',
            application_url='https://training.example.org/apply/',
        )

    def test_public_api_only_returns_published_opportunities(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['slug'], self.published.slug)
        self.assertEqual(
            self.client.get(f'{self.url}{self.draft.slug}/').status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_public_api_supports_search_country_and_category_filters(self):
        response = self.client.get(
            self.url,
            {
                'search': 'emerging scientists',
                'country': 'Ethiopia',
                'category': 'FELLOWSHIP',
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], str(self.published.id))

    def test_detail_includes_nationality_and_document_requirements(self):
        response = self.client.get(f'{self.url}{self.published.slug}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['eligibility_scope'], 'ETHIOPIA_AND_OTHERS')
        self.assertEqual(response.data['eligible_nationalities'], ['ET', 'KE'])
        self.assertEqual(response.data['excluded_nationalities'], ['US'])
        self.assertEqual(response.data['eligibility_notes'], 'Applicants must meet the provider criteria.')
        self.assertEqual(
            response.data['documents_required'],
            ['Academic transcript', 'Reference letter'],
        )
        self.assertEqual(
            response.data['verified_sources'][0]['url'],
            f'https://{self.published.pk}.example.org/listing',
        )

    def test_public_nationality_filter_requires_explicit_confirmed_eligibility(self):
        eligible = Opportunity.objects.create(
            title='Explicitly eligible job',
            description='A confirmed job listing.',
            organization='Example Employer',
            category='JOB',
            eligibility_scope='ETHIOPIA_AND_OTHERS',
            eligible_nationalities=['ET'],
            compensation_status='PAID',
            application_url='https://example.org/job/',
        )
        create_verified_opportunity_source(eligible)
        eligible.is_published = True
        eligible.save()

        unknown = Opportunity.objects.create(
            title='Unknown eligibility job',
            description='A job with unknown eligibility.',
            organization='Other Employer',
            category='JOB',
            application_url='https://example.org/unknown-job/',
        )
        create_verified_opportunity_source(unknown)
        unknown.is_published = True
        unknown.save()

        response = self.client.get(
            self.url,
            {'nationality': 'et', 'category': 'JOB'},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['slug'], eligible.slug)

    def test_invalid_nationality_filter_is_rejected(self):
        response = self.client.get(self.url, {'nationality': 'ETH'})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_api_filters_job_compensation_and_education(self):
        job = Opportunity.objects.create(
            title='Paid graduate role',
            description='Graduate work opportunity.',
            organization='Example Employer',
            category='JOB',
            level='GRADUATE',
            compensation_status='PAID',
            employment_type='FULL_TIME',
            work_mode='REMOTE',
            application_url='https://example.org/role/',
        )
        create_verified_opportunity_source(job)
        job.is_published = True
        job.save()

        response = self.client.get(
            self.url,
            {'category': 'JOB', 'funding': 'PAID', 'education': 'GRADUATE'},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['slug'], job.slug)

    def test_expired_opportunities_are_hidden_from_public_api(self):
        expired = Opportunity.objects.create(
            title='Expired opportunity',
            description='An expired test opportunity.',
            organization='Example Organization',
            category='INTERNSHIP',
            application_deadline=timezone.localdate() + timedelta(days=1),
            application_url='https://example.org/expired/',
        )
        create_verified_opportunity_source(expired)
        expired.is_published = True
        expired.save()
        expired_deadline = timezone.localdate() - timedelta(days=1)
        Opportunity.objects.filter(pk=expired.pk).update(
            application_deadline=expired_deadline,
            status='EXPIRED',
        )
        OpportunitySourceRecord.objects.filter(
            opportunity=expired,
        ).update(normalized_deadline=expired_deadline)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn(
            expired.slug,
            [item['slug'] for item in response.data['results']],
        )

    def test_public_api_paginates_matching_results(self):
        for index in range(20):
            opportunity = Opportunity.objects.create(
                title=f'Paginated opportunity {index}',
                description='A current verified listing.',
                organization=f'Example Organization {index}',
                category='INTERNSHIP',
                application_url=f'https://example.org/apply/{index}/',
            )
            create_verified_opportunity_source(opportunity)
            opportunity.is_published = True
            opportunity.save()

        first_page = self.client.get(self.url)
        second_page = self.client.get(self.url, {'page': 2})

        self.assertEqual(first_page.status_code, status.HTTP_200_OK)
        self.assertEqual(first_page.data['count'], 21)
        self.assertEqual(len(first_page.data['results']), 20)
        self.assertIsNotNone(first_page.data['next'])
        self.assertEqual(second_page.status_code, status.HTTP_200_OK)
        self.assertEqual(len(second_page.data['results']), 1)

    def test_public_api_sorts_by_application_deadline(self):
        earliest = Opportunity.objects.create(
            title='Earliest deadline internship',
            description='A current verified listing.',
            organization='Example Organization Earliest',
            category='INTERNSHIP',
            application_deadline=timezone.localdate() + timedelta(days=2),
            application_url='https://example.org/earliest/',
        )
        create_verified_opportunity_source(earliest)
        earliest.is_published = True
        earliest.save()

        latest = Opportunity.objects.create(
            title='Latest deadline internship',
            description='A current verified listing.',
            organization='Example Organization Latest',
            category='INTERNSHIP',
            application_deadline=timezone.localdate() + timedelta(days=60),
            application_url='https://example.org/latest/',
        )
        create_verified_opportunity_source(latest)
        latest.is_published = True
        latest.save()

        ascending = self.client.get(self.url, {'ordering': 'application_deadline'})
        descending = self.client.get(self.url, {'ordering': '-application_deadline'})

        self.assertEqual(ascending.data['results'][0]['slug'], earliest.slug)
        self.assertEqual(descending.data['results'][0]['slug'], latest.slug)

    def test_opportunity_cannot_be_both_eligible_and_excluded_by_nationality(self):
        with self.assertRaises(ValidationError):
            Opportunity.objects.create(
                title='Conflicting nationality rules',
                description='A test listing.',
                organization='Example Organization',
                category='FELLOWSHIP',
                eligible_nationalities=['ET'],
                excluded_nationalities=['ET'],
                application_url='https://example.org/apply/',
            )

    def test_ethiopia_only_opportunity_requires_only_ethiopia_as_eligible(self):
        with self.assertRaises(ValidationError):
            Opportunity.objects.create(
                title='Incomplete Ethiopia-only eligibility',
                description='A test listing.',
                organization='Example Organization',
                category='FELLOWSHIP',
                eligibility_scope='ETHIOPIA_ONLY',
                eligible_nationalities=[],
                application_url='https://example.org/apply/',
            )

    def test_public_api_hides_opportunity_with_unverified_source_record(self):
        source_backed = Opportunity.objects.create(
            title='Source-backed internship',
            description='A source-backed internship listing.',
            organization='Example Institute',
            country='Ethiopia',
            category='INTERNSHIP',
            application_url='https://example.org/apply/',
        )
        source = OpportunitySource.objects.create(
            name='Research Institute',
            organization='Example Institute',
            base_url='https://example.org/',
            source_type='OFFICIAL_PROVIDER',
            collection_method='API',
        )
        run = CollectionRun.objects.create(source=source)
        OpportunitySourceRecord.objects.create(
            source=source,
            collection_run=run,
            opportunity=source_backed,
            source_record_key='fellowship-1',
            official_source_url='https://example.org/fellowship/',
            official_application_url='https://example.org/apply/',
            source_title=source_backed.title,
            normalized_title=source_backed.title.lower(),
            normalized_organization=source_backed.organization.lower(),
            source_payload={'title': source_backed.title},
            content_hash='c' * 64,
            identity_fingerprint='d' * 64,
        )
        Opportunity.objects.filter(pk=source_backed.pk).update(is_published=True)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        slugs = [item['slug'] for item in response.data['results']]
        self.assertIn(self.published.slug, slugs)
        self.assertNotIn(source_backed.slug, slugs)

    def test_student_cannot_create_or_publish_opportunities(self):
        student = User.objects.create_user(
            email='student@example.com',
            password='SecurePassword123!',
            role='STUDENT',
        )
        self.client.force_authenticate(user=student)

        create_response = self.client.post(
            self.url,
            {
                'title': 'Student-created opportunity',
                'description': 'Should not be accepted.',
                'organization': 'Example Organization',
                'category': 'INTERNSHIP',
                'application_url': 'https://example.org/apply/',
            },
            format='json',
        )
        publish_response = self.client.patch(
            f'{self.url}{self.draft.slug}/',
            {'is_published': True},
            format='json',
        )

        self.assertEqual(create_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(publish_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(Opportunity.objects.filter(
            title='Student-created opportunity',
        ).exists())

    def test_admin_can_create_draft_and_publish_opportunity(self):
        admin_user = User.objects.create_user(
            email='admin@example.com',
            password='SecurePassword123!',
            role='ADMIN',
        )
        self.client.force_authenticate(user=admin_user)
        response = self.client.post(
            self.url,
            {
                'title': 'New Graduate Internship',
                'description': 'An administrator-created opportunity.',
                'organization': 'Example Lab',
                'category': 'INTERNSHIP',
                'country': 'Ethiopia',
                'application_url': 'https://example.org/internship/',
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        created = Opportunity.objects.get(pk=response.data['id'])
        self.assertFalse(created.is_published)
        create_verified_opportunity_source(created, admin_user)

        publish_response = self.client.patch(
            f'{self.url}{created.slug}/',
            {'is_published': True},
            format='json',
        )

        self.assertEqual(publish_response.status_code, status.HTTP_200_OK)
        created.refresh_from_db()
        self.assertTrue(created.is_published)

        edit_response = self.client.patch(
            f'{self.url}{created.slug}/',
            {'short_description': 'Updated by an administrator.'},
            format='json',
        )
        self.assertEqual(edit_response.status_code, status.HTTP_200_OK)
        created.refresh_from_db()
        self.assertEqual(
            created.short_description,
            'Updated by an administrator.',
        )

    def test_admin_cannot_publish_opportunity_without_verified_source(self):
        admin_user = User.objects.create_user(
            email='publication-reviewer@example.com',
            password='SecurePassword123!',
            role='ADMIN',
        )
        self.client.force_authenticate(user=admin_user)

        response = self.client.patch(
            f'{self.url}{self.draft.slug}/',
            {'is_published': True},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        details = response.data.get('details', response.data)
        self.assertIn('is_published', details)
        self.assertIn('verified', str(details['is_published']).lower())
        self.draft.refresh_from_db()
        self.assertFalse(self.draft.is_published)

    def test_admin_cannot_create_published_opportunity_without_verified_source(self):
        admin_user = User.objects.create_user(
            email='publication-creator@example.com',
            password='SecurePassword123!',
            role='ADMIN',
        )
        self.client.force_authenticate(user=admin_user)

        response = self.client.post(
            self.url,
            {
                'title': 'Unverified Published Opportunity',
                'description': 'This must remain unpublished.',
                'organization': 'Example Organization',
                'category': 'JOB',
                'application_url': 'https://example.org/unverified-job/',
                'is_published': True,
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        details = response.data.get('details', response.data)
        self.assertIn('is_published', details)
        self.assertIn('verified', str(details['is_published']).lower())
        self.assertFalse(Opportunity.objects.filter(
            title='Unverified Published Opportunity',
        ).exists())


class OpportunitySourceRecordAdminTests(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_user(
            email='reviewer@example.com',
            password='SecurePassword123!',
            role='ADMIN',
            is_staff=True,
        )
        self.source = OpportunitySource.objects.create(
            name='Official Provider',
            organization='Example Organization',
            base_url='https://example.org/',
            source_type='OFFICIAL_PROVIDER',
            collection_method='API',
            is_active=True,
        )
        self.run = CollectionRun.objects.create(source=self.source)
        self.opportunity = Opportunity.objects.create(
            title='Reviewed internship',
            description='An official internship opportunity.',
            organization='Example Organization',
            category='INTERNSHIP',
            application_url='https://example.org/apply/',
        )
        self.record = OpportunitySourceRecord.objects.create(
            source=self.source,
            collection_run=self.run,
            opportunity=self.opportunity,
            source_record_key='reviewed-internship',
            official_source_url='https://example.org/internship/',
            official_application_url='https://example.org/apply/',
            source_title=self.opportunity.title,
            normalized_title=self.opportunity.title.lower(),
            normalized_organization=self.opportunity.organization.lower(),
            source_payload={'title': self.opportunity.title},
            content_hash='e' * 64,
            identity_fingerprint='f' * 64,
        )
        self.model_admin = OpportunitySourceRecordAdmin(
            OpportunitySourceRecord,
            AdminSite(),
        )

    def admin_request(self):
        request = RequestFactory().post('/admin/')
        request.user = self.admin_user
        request.session = {}
        request._messages = FallbackStorage(request)
        return request

    def test_verify_action_records_current_admin_and_time(self):
        self.model_admin.mark_selected_verified(
            self.admin_request(),
            OpportunitySourceRecord.objects.filter(pk=self.record.pk),
        )

        self.record.refresh_from_db()
        self.assertEqual(self.record.verification_status, 'VERIFIED')
        self.assertEqual(self.record.verified_by, self.admin_user)
        self.assertIsNotNone(self.record.verified_at)

    def test_verify_action_rejects_record_without_public_target(self):
        self.record.opportunity = None
        self.record.save()
        request = self.admin_request()

        self.model_admin.mark_selected_verified(
            request,
            OpportunitySourceRecord.objects.filter(pk=self.record.pk),
        )

        self.record.refresh_from_db()
        self.assertEqual(self.record.verification_status, 'DISCOVERED')
        self.assertIsNone(self.record.verified_by)
        self.assertTrue(list(request._messages))

    def test_rejecting_linked_verified_record_unpublishes_opportunity(self):
        self.record.verification_status = 'VERIFIED'
        self.record.verified_at = timezone.now()
        self.record.verified_by = self.admin_user
        self.record.save()
        self.opportunity.is_published = True
        self.opportunity.save()

        self.model_admin.reject_selected(
            self.admin_request(),
            OpportunitySourceRecord.objects.filter(pk=self.record.pk),
        )

        self.record.refresh_from_db()
        self.opportunity.refresh_from_db()
        self.assertEqual(self.record.verification_status, 'REJECTED')
        self.assertIsNone(self.record.verified_at)
        self.assertIsNone(self.record.verified_by)
        self.assertFalse(self.opportunity.is_published)
