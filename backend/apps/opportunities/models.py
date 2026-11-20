
"""
Opportunity models for Gofer Exam.

Includes:
- External source configuration
- Collection run history
- Source-specific collected records
- Public general opportunities
"""

import json
import re
import uuid
from urllib.parse import urlsplit, urlunsplit

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator, URLValidator
from django.db import models, transaction
from django.utils import timezone
from django.utils.text import slugify


MAX_PAYLOAD_BYTES = 512 * 1024
MAX_PAYLOAD_ITEMS = 200


def normalize_url(value):
    """Normalize an absolute URL for consistent source identity checks."""
    if not value:
        return value

    value = value.strip()
    parts = urlsplit(value)
    scheme = parts.scheme.lower()
    hostname = (parts.hostname or '').lower()

    if not scheme or not hostname:
        return value

    if parts.port:
        default_port = (
            (scheme == 'http' and parts.port == 80)
            or (scheme == 'https' and parts.port == 443)
        )
        host = hostname if default_port else f'{hostname}:{parts.port}'
    else:
        host = hostname

    path = parts.path or '/'

    if path != '/' and path.endswith('/'):
        path = path.rstrip('/')

    return urlunsplit((scheme, host, path, parts.query, ''))


def validate_payload(value):
    """Keep stored source metadata bounded and structured."""
    if not isinstance(value, dict):
        raise ValidationError('Payload must be a JSON object.')

    if len(value) > MAX_PAYLOAD_ITEMS:
        raise ValidationError(
            f'Payload cannot contain more than {MAX_PAYLOAD_ITEMS} top-level items.'
        )

    try:
        payload_size = len(
            json.dumps(value, ensure_ascii=False).encode('utf-8')
        )
    except (TypeError, ValueError) as error:
        raise ValidationError(
            'Payload must contain JSON-serializable values.'
        ) from error

    if payload_size > MAX_PAYLOAD_BYTES:
        raise ValidationError(
            'Payload exceeds the maximum permitted size.'
        )


def validate_fingerprint(value):
    """Validate hexadecimal content fingerprints."""
    if value and not re.fullmatch(r'[0-9a-fA-F]{32,128}', value):
        raise ValidationError(
            'Fingerprint must be a hexadecimal digest.'
        )


def validate_nationality_codes(value):
    """Validate ISO alpha-2 nationality codes."""
    if not isinstance(value, list):
        raise ValidationError(
            'Nationality codes must be a JSON array.'
        )

    if any(
        not isinstance(code, str)
        or not re.fullmatch(r'[A-Z]{2}', code)
        for code in value
    ):
        raise ValidationError(
            'Nationality codes must be uppercase ISO 3166-1 alpha-2 codes.'
        )


class OpportunitySource(models.Model):
    """An approved external source for opportunity collection."""

    SOURCE_TYPE_CHOICES = [
        ('OFFICIAL_PROVIDER', 'Official provider'),
        ('UNIVERSITY', 'University'),
        ('GOVERNMENT', 'Government'),
        ('ORGANIZATION', 'Organization'),
        ('RSS', 'RSS feed'),
        ('API', 'API'),
    ]

    COLLECTION_METHOD_CHOICES = [
        ('API', 'API'),
        ('RSS', 'RSS'),
        ('STRUCTURED_DATA', 'Structured data'),
        ('PERMITTED_HTML', 'Permitted HTML'),
    ]

    RELIABILITY_STATUS_CHOICES = [
        ('UNKNOWN', 'Unknown'),
        ('HEALTHY', 'Healthy'),
        ('DEGRADED', 'Degraded'),
        ('FAILING', 'Failing'),
        ('DISABLED', 'Disabled'),
    ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    name = models.CharField(max_length=200)
    organization = models.CharField(max_length=200)

    base_url = models.URLField(
        unique=True,
        validators=[URLValidator(schemes=['http', 'https'])],
    )

    source_type = models.CharField(
        max_length=30,
        choices=SOURCE_TYPE_CHOICES,
    )

    collection_method = models.CharField(
        max_length=20,
        choices=COLLECTION_METHOD_CHOICES,
    )

    terms_url = models.URLField(
        blank=True,
        validators=[URLValidator(schemes=['http', 'https'])],
    )

    robots_url = models.URLField(
        blank=True,
        validators=[URLValidator(schemes=['http', 'https'])],
    )

    is_active = models.BooleanField(default=False)

    collection_interval_hours = models.PositiveIntegerField(
        default=24,
        validators=[MinValueValidator(1)],
    )

    last_success_at = models.DateTimeField(null=True, blank=True)
    last_failure_at = models.DateTimeField(null=True, blank=True)

    last_error_code = models.CharField(max_length=100, blank=True)
    last_error_message = models.TextField(blank=True)

    reliability_status = models.CharField(
        max_length=20,
        choices=RELIABILITY_STATUS_CHOICES,
        default='UNKNOWN',
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['is_active', 'reliability_status']),
            models.Index(fields=['source_type']),
            models.Index(fields=['last_success_at']),
        ]

    def clean(self):
        self.base_url = normalize_url(self.base_url)
        self.terms_url = normalize_url(self.terms_url)
        self.robots_url = normalize_url(self.robots_url)

        super().clean()

        if self.last_success_at and self.last_failure_at:
            if self.last_failure_at < self.last_success_at:
                raise ValidationError({
                    'last_failure_at': (
                        'Failure time cannot precede the last success time.'
                    )
                })

        if self.reliability_status == 'DISABLED' and self.is_active:
            raise ValidationError({
                'is_active': 'A disabled source cannot be active.'
            })

    def save(self, *args, **kwargs):
        self.base_url = normalize_url(self.base_url)
        self.terms_url = normalize_url(self.terms_url)
        self.robots_url = normalize_url(self.robots_url)

        self.full_clean()

        with transaction.atomic():
            result = super().save(*args, **kwargs)

            if self.pk and (
                not self.is_active or self.reliability_status == 'DISABLED'
            ):
                from apps.scholarships.models import Scholarship

                Scholarship.objects.filter(
                    is_published=True,
                    source_records__source_id=self.pk,
                ).update(
                    is_published=False,
                    updated_at=timezone.now(),
                )
                Opportunity.objects.filter(
                    is_published=True,
                    source_records__source_id=self.pk,
                ).update(
                    is_published=False,
                    updated_at=timezone.now(),
                )

            return result

    def __str__(self):
        return f'{self.name} ({self.organization})'


class CollectionRun(models.Model):
    """One collection attempt for a configured source."""

    TRIGGER_TYPE_CHOICES = [
        ('MANUAL', 'Manual'),
        ('SCHEDULED', 'Scheduled'),
        ('RETRY', 'Retry'),
    ]

    STATUS_CHOICES = [
        ('RUNNING', 'Running'),
        ('SUCCEEDED', 'Succeeded'),
        ('PARTIAL', 'Partial'),
        ('FAILED', 'Failed'),
        ('CANCELLED', 'Cancelled'),
    ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    source = models.ForeignKey(
        OpportunitySource,
        on_delete=models.PROTECT,
        related_name='collection_runs',
    )

    trigger_type = models.CharField(
        max_length=20,
        choices=TRIGGER_TYPE_CHOICES,
        default='MANUAL',
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='RUNNING',
    )

    started_at = models.DateTimeField(default=timezone.now)
    finished_at = models.DateTimeField(null=True, blank=True)

    records_seen = models.PositiveIntegerField(default=0)
    records_created = models.PositiveIntegerField(default=0)
    records_updated = models.PositiveIntegerField(default=0)
    records_unchanged = models.PositiveIntegerField(default=0)
    records_flagged_duplicate = models.PositiveIntegerField(default=0)
    records_rejected = models.PositiveIntegerField(default=0)
    error_count = models.PositiveIntegerField(default=0)

    error_summary = models.JSONField(
        default=dict,
        blank=True,
        validators=[validate_payload],
    )

    collector_version = models.CharField(max_length=100, blank=True)

    request_metadata = models.JSONField(
        default=dict,
        blank=True,
        validators=[validate_payload],
    )

    class Meta:
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['source', 'started_at']),
            models.Index(fields=['status', 'started_at']),
        ]

    def clean(self):
        super().clean()

        if self.finished_at and self.finished_at < self.started_at:
            raise ValidationError({
                'finished_at': (
                    'Completion time cannot precede the start time.'
                )
            })

        if self.status == 'RUNNING' and self.finished_at:
            raise ValidationError({
                'finished_at': (
                    'A running collection cannot have a completion time.'
                )
            })

        if self.status != 'RUNNING' and not self.finished_at:
            raise ValidationError({
                'finished_at': (
                    'Completed collection runs require a completion time.'
                )
            })

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return (
            f'{self.source.name} - {self.status} '
            f'({self.started_at:%Y-%m-%d %H:%M})'
        )


class Opportunity(models.Model):
    """Public-facing jobs, internships, and other non-scholarship opportunities."""

    CATEGORY_CHOICES = [
        ('JOB', 'Job'),
        ('INTERNSHIP', 'Internship'),
        ('FELLOWSHIP', 'Fellowship'),
        ('EXCHANGE', 'Exchange Program'),
        ('TRAINING', 'Training'),
        ('RESEARCH', 'Research'),
        ('COMPETITION', 'Competition'),
        ('GRANT', 'Grant'),
        ('OTHER', 'Other'),
    ]

    LEVEL_CHOICES = [
        ('HIGH_SCHOOL', 'High School'),
        ('UNDERGRADUATE', 'Undergraduate'),
        ('GRADUATE', 'Graduate'),
        ('POSTGRADUATE', 'Postgraduate'),
        ('DOCTORATE', 'Doctorate'),
        ('ALL_LEVELS', 'All Levels'),
    ]

    STATUS_CHOICES = [
        ('UPCOMING', 'Upcoming'),
        ('OPEN', 'Open'),
        ('CLOSED', 'Closed'),
        ('EXPIRED', 'Expired'),
    ]

    EMPLOYMENT_TYPE_CHOICES = [
        ('UNKNOWN', 'Not confirmed'),
        ('FULL_TIME', 'Full time'),
        ('PART_TIME', 'Part time'),
        ('CONTRACT', 'Contract'),
        ('TEMPORARY', 'Temporary'),
        ('OTHER', 'Other'),
    ]

    WORK_MODE_CHOICES = [
        ('UNKNOWN', 'Not confirmed'),
        ('ON_SITE', 'On-site'),
        ('HYBRID', 'Hybrid'),
        ('REMOTE', 'Remote'),
    ]

    COMPENSATION_STATUS_CHOICES = [
        ('UNKNOWN', 'Not confirmed'),
        ('PAID', 'Paid'),
        ('UNPAID', 'Unpaid'),
    ]

    COMPENSATION_PERIOD_CHOICES = [
        ('HOURLY', 'Hourly'),
        ('MONTHLY', 'Monthly'),
        ('ANNUAL', 'Annual'),
        ('PROJECT', 'Per project'),
        ('OTHER', 'Other'),
    ]

    ELIGIBILITY_SCOPE_CHOICES = [
        ('UNSPECIFIED', 'Unspecified'),
        ('ETHIOPIA_ONLY', 'Ethiopia only'),
        ('ETHIOPIA_AND_OTHERS', 'Ethiopia and others'),
        ('OTHER_NATIONALITIES', 'Other nationalities'),
    ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    title = models.CharField(max_length=300)
    slug = models.SlugField(
        max_length=350,
        unique=True,
        blank=True,
    )

    short_description = models.CharField(
        max_length=500,
        blank=True,
    )

    description = models.TextField()

    organization = models.CharField(max_length=300)
    country = models.CharField(max_length=150, blank=True)
    location = models.CharField(max_length=250, blank=True)

    category = models.CharField(
        max_length=30,
        choices=CATEGORY_CHOICES,
    )

    level = models.CharField(
        max_length=30,
        choices=LEVEL_CHOICES,
        default='ALL_LEVELS',
    )

    eligibility = models.JSONField(default=list, blank=True)
    eligibility_scope = models.CharField(
        max_length=30,
        choices=ELIGIBILITY_SCOPE_CHOICES,
        default='UNSPECIFIED',
    )
    eligible_nationalities = models.JSONField(
        default=list,
        blank=True,
        validators=[validate_nationality_codes],
    )
    excluded_nationalities = models.JSONField(
        default=list,
        blank=True,
        validators=[validate_nationality_codes],
    )
    eligibility_notes = models.TextField(blank=True)
    benefits = models.JSONField(default=list, blank=True)
    documents_required = models.JSONField(default=list, blank=True)
    required_skills = models.JSONField(default=list, blank=True)

    employment_type = models.CharField(
        max_length=20,
        choices=EMPLOYMENT_TYPE_CHOICES,
        default='UNKNOWN',
    )
    work_mode = models.CharField(
        max_length=20,
        choices=WORK_MODE_CHOICES,
        default='UNKNOWN',
    )
    compensation_status = models.CharField(
        max_length=20,
        choices=COMPENSATION_STATUS_CHOICES,
        default='UNKNOWN',
    )
    compensation_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
    )
    compensation_currency = models.CharField(max_length=3, blank=True)
    compensation_period = models.CharField(
        max_length=20,
        choices=COMPENSATION_PERIOD_CHOICES,
        blank=True,
    )
    duration = models.CharField(max_length=100, blank=True)
    experience_requirement = models.TextField(blank=True)
    minimum_experience_years = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MaxValueValidator(80)],
    )

    application_deadline = models.DateField(
        null=True,
        blank=True,
    )

    application_url = models.URLField(
        blank=True,
        validators=[URLValidator(schemes=['http', 'https'])],
    )

    official_website = models.URLField(
        blank=True,
        validators=[URLValidator(schemes=['http', 'https'])],
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='OPEN',
    )

    is_published = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'opportunities'
        ordering = ['application_deadline', '-created_at']
        indexes = [
            models.Index(fields=['category', 'status']),
            models.Index(fields=['is_published', 'application_deadline']),
            models.Index(fields=['country']),
        ]

    def clean(self):
        self.application_url = normalize_url(self.application_url)
        self.official_website = normalize_url(self.official_website)
        super().clean()

        self.compensation_currency = self.compensation_currency.strip().upper()

        duplicates = Opportunity.objects.filter(
            title__iexact=self.title.strip(),
            organization__iexact=self.organization.strip(),
        ).exclude(pk=self.pk)
        if self.title and self.organization and duplicates.exists():
            raise ValidationError({
                'title': 'An opportunity with this title and organization already exists.'
            })

        overlapping_nationalities = set(
            self.eligible_nationalities or []
        ).intersection(
            self.excluded_nationalities or []
        )
        if overlapping_nationalities:
            raise ValidationError({
                'excluded_nationalities': (
                    'A nationality cannot be both eligible and excluded.'
                )
            })

        if self.compensation_amount is not None:
            if not self.compensation_currency or not self.compensation_period:
                raise ValidationError({
                    'compensation_currency': (
                        'Currency and pay period are required when an amount is specified.'
                    )
                })
            if len(self.compensation_currency) != 3 or not self.compensation_currency.isalpha():
                raise ValidationError({
                    'compensation_currency': 'Use a three-letter currency code.'
                })

        if self.compensation_status == 'UNPAID' and self.compensation_amount is not None:
            raise ValidationError({
                'compensation_amount': 'Unpaid opportunities cannot have a compensation amount.'
            })

        if (
            self.eligibility_scope == 'ETHIOPIA_ONLY'
            and set(self.eligible_nationalities or []) != {'ET'}
        ):
            raise ValidationError({
                'eligible_nationalities': (
                    'Ethiopia-only eligibility must contain only ET.'
                )
            })

        if self.is_published:
            if not (self.application_url or self.official_website):
                raise ValidationError({
                    'application_url': (
                        'A published opportunity must include an official application '
                        'or organization website.'
                    )
                })

            if self.status not in ('OPEN', 'UPCOMING'):
                raise ValidationError({
                    'status': 'Only open or upcoming opportunities can be published.'
                })

            if self.application_deadline and self.application_deadline < timezone.localdate():
                raise ValidationError({
                    'application_deadline': 'Expired opportunities cannot be published.'
                })

            valid_source_records = self.source_records.filter(
                verification_status='VERIFIED',
                source_status='AVAILABLE',
                verified_at__isnull=False,
                verified_by__role__in=('ADMIN', 'SUPERADMIN'),
                source__is_active=True,
                normalized_deadline=self.application_deadline,
                eligibility_scope=self.eligibility_scope,
                eligible_nationalities=self.eligible_nationalities,
                excluded_nationalities=self.excluded_nationalities,
            ).filter(
                models.Q(normalized_deadline__isnull=True)
                | models.Q(normalized_deadline__gte=timezone.localdate())
            ).filter(
                models.Q(official_application_url=self.application_url)
                | models.Q(official_source_url=self.application_url)
                | models.Q(official_source_url=self.official_website)
            )
            if not valid_source_records.exists():
                raise ValidationError({
                    'is_published': (
                        'An opportunity needs at least one currently verified, '
                        'available official source before publication.'
                    )
                })

            if self.source_records.exclude(
                pk__in=valid_source_records.values('pk')
            ).exists():
                raise ValidationError({
                    'is_published': (
                        'Every linked source record must remain verified and available.'
                    )
                })

    def save(self, *args, **kwargs):
        self.full_clean()

        if not self.slug:
            base_slug = slugify(self.title) or 'opportunity'
            candidate = base_slug
            counter = 1

            while Opportunity.objects.filter(
                slug=candidate
            ).exclude(pk=self.pk).exists():
                candidate = f'{base_slug}-{counter}'
                counter += 1

            self.slug = candidate

        return super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class OpportunitySourceRecord(models.Model):
    """A source-specific observation that is not itself publicly visible."""

    SOURCE_STATUS_CHOICES = [
        ('AVAILABLE', 'Available'),
        ('UNAVAILABLE', 'Unavailable'),
        ('REMOVED', 'Removed'),
        ('INCOMPLETE', 'Incomplete'),
    ]

    VERIFICATION_STATUS_CHOICES = [
        ('DISCOVERED', 'Discovered'),
        ('NEEDS_REVIEW', 'Needs review'),
        ('VERIFIED', 'Verified'),
        ('REJECTED', 'Rejected'),
        ('EXPIRED', 'Expired'),
        ('SOURCE_UNAVAILABLE', 'Source unavailable'),
    ]

    ELIGIBILITY_SCOPE_CHOICES = [
        ('UNSPECIFIED', 'Unspecified'),
        ('ETHIOPIA_ONLY', 'Ethiopia only'),
        ('ETHIOPIA_AND_OTHERS', 'Ethiopia and others'),
        ('OTHER_NATIONALITIES', 'Other nationalities'),
    ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    source = models.ForeignKey(
        OpportunitySource,
        on_delete=models.PROTECT,
        related_name='source_records',
    )

    collection_run = models.ForeignKey(
        CollectionRun,
        on_delete=models.PROTECT,
        related_name='source_records',
    )

    scholarship = models.ForeignKey(
        'scholarships.Scholarship',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='source_records',
    )

    opportunity = models.ForeignKey(
        Opportunity,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='source_records',
    )

    source_record_key = models.CharField(max_length=500)

    official_source_url = models.URLField(
        validators=[URLValidator(schemes=['http', 'https'])],
    )

    official_application_url = models.URLField(
        blank=True,
        validators=[URLValidator(schemes=['http', 'https'])],
    )

    source_title = models.CharField(max_length=500)
    normalized_title = models.CharField(max_length=500)
    normalized_organization = models.CharField(max_length=300)

    normalized_deadline = models.DateField(
        null=True,
        blank=True,
    )

    eligibility_scope = models.CharField(
        max_length=30,
        choices=ELIGIBILITY_SCOPE_CHOICES,
        default='UNSPECIFIED',
    )

    eligible_nationalities = models.JSONField(
        default=list,
        blank=True,
        validators=[validate_nationality_codes],
    )

    excluded_nationalities = models.JSONField(
        default=list,
        blank=True,
        validators=[validate_nationality_codes],
    )

    eligibility_notes = models.TextField(blank=True)

    source_payload = models.JSONField(
        default=dict,
        blank=True,
        validators=[validate_payload],
    )

    content_hash = models.CharField(
        max_length=128,
        validators=[validate_fingerprint],
    )

    identity_fingerprint = models.CharField(
        max_length=128,
        validators=[validate_fingerprint],
    )

    similarity_fingerprint = models.CharField(
        max_length=128,
        blank=True,
        validators=[validate_fingerprint],
    )

    source_status = models.CharField(
        max_length=20,
        choices=SOURCE_STATUS_CHOICES,
        default='AVAILABLE',
    )

    verification_status = models.CharField(
        max_length=25,
        choices=VERIFICATION_STATUS_CHOICES,
        default='DISCOVERED',
    )

    last_seen_at = models.DateTimeField(default=timezone.now)
    last_changed_at = models.DateTimeField(null=True, blank=True)

    verified_at = models.DateTimeField(null=True, blank=True)

    verified_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_opportunity_source_records',
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-last_seen_at']

        constraints = [
            models.UniqueConstraint(
                fields=['source', 'source_record_key'],
                name='opportunity_source_record_unique_key',
            ),
            models.CheckConstraint(
                check=(
                    models.Q(scholarship__isnull=True)
                    | models.Q(opportunity__isnull=True)
                ),
                name='source_record_one_public_target',
            ),
        ]

        indexes = [
            models.Index(fields=['source', 'source_record_key']),
            models.Index(fields=['verification_status', 'last_seen_at']),
            models.Index(fields=['scholarship', 'verification_status']),
            models.Index(fields=['opportunity', 'verification_status']),
            models.Index(fields=['official_source_url']),
            models.Index(fields=['identity_fingerprint']),
        ]

    def clean(self):
        self.official_source_url = normalize_url(
            self.official_source_url
        )
        self.official_application_url = normalize_url(
            self.official_application_url
        )

        super().clean()

        if self.collection_run_id and self.source_id:
            if self.collection_run.source_id != self.source_id:
                raise ValidationError({
                    'collection_run': (
                        'Collection run must belong to the selected source.'
                    )
                })

        if self.scholarship_id and self.opportunity_id:
            raise ValidationError(
                'A source record cannot link to both a scholarship and an opportunity.'
            )

        if self.pk:
            previous = OpportunitySourceRecord.objects.filter(
                pk=self.pk,
            ).values(
                'scholarship_id',
                'opportunity_id',
                'verification_status',
            ).first()
            if (
                previous
                and previous['verification_status'] == 'VERIFIED'
                and (
                    previous['scholarship_id'] != self.scholarship_id
                    or previous['opportunity_id'] != self.opportunity_id
                )
            ):
                raise ValidationError({
                    'opportunity': (
                        'Mark this source record as needing review before changing '
                        'its linked public target.'
                    )
                })

        if self.verification_status == 'VERIFIED':
            if not self.verified_at or not self.verified_by_id:
                raise ValidationError(
                    'Verified records require a verification time and verifying user.'
                )

            if not self.scholarship_id and not self.opportunity_id:
                raise ValidationError(
                    'Verified records must be linked to a scholarship or opportunity.'
                )

            if self.source_status != 'AVAILABLE':
                raise ValidationError({
                    'source_status': 'Only available source records can be verified.'
                })

            if self.normalized_deadline and self.normalized_deadline < timezone.localdate():
                raise ValidationError({
                    'normalized_deadline': 'Expired source records cannot be verified.'
                })

            if not self.source.is_active:
                raise ValidationError({
                    'source': 'Only active approved sources can be verified.'
                })

            if self.verified_by and not self.verified_by.is_admin:
                raise ValidationError({
                    'verified_by': 'Only an administrator can verify source records.'
                })

            if self.opportunity_id:
                opportunity = self.opportunity
                if (
                    self.normalized_deadline != opportunity.application_deadline
                    or self.eligibility_scope != opportunity.eligibility_scope
                    or self.eligible_nationalities != opportunity.eligible_nationalities
                    or self.excluded_nationalities != opportunity.excluded_nationalities
                    or (
                        opportunity.application_url
                        and self.official_application_url != opportunity.application_url
                    )
                ):
                    raise ValidationError({
                        'opportunity': (
                            'Verified source facts must match the published opportunity. '
                            'Update the source record and reverify after changing listing facts.'
                        )
                    })

            if self.scholarship_id:
                scholarship = self.scholarship
                if (
                    self.normalized_deadline != scholarship.application_deadline
                    or (
                        scholarship.application_url
                        and self.official_application_url != scholarship.application_url
                    )
                    or (
                        not scholarship.application_url
                        and scholarship.website_url
                        and self.official_source_url != scholarship.website_url
                    )
                ):
                    raise ValidationError({
                        'scholarship': (
                            'Verified source facts must match the scholarship deadline '
                            'and official link.'
                        )
                    })

        if (
            self.opportunity_id
            and self.opportunity.is_published
            and (
                self.verification_status != 'VERIFIED'
                or self.source_status != 'AVAILABLE'
            )
        ):
            raise ValidationError({
                'opportunity': (
                    'An unverified or unavailable source record cannot be linked '
                    'to a published opportunity.'
                )
            })

        if (
            self.scholarship_id
            and self.scholarship.is_published
            and (
                self.verification_status != 'VERIFIED'
                or self.source_status != 'AVAILABLE'
                or not self.verified_at
                or not self.verified_by_id
                or not self.source.is_active
                or not self.verified_by.is_admin
            )
        ):
            raise ValidationError({
                'scholarship': (
                    'An unverified or unavailable source record cannot be '
                    'linked to a published scholarship.'
                )
            })

        if self.verified_status_is_unverified and (
            self.verified_at or self.verified_by_id
        ):
            raise ValidationError(
                'Unverified records cannot contain verifier metadata.'
            )

        overlapping_codes = set(
            self.eligible_nationalities or []
        ).intersection(
            self.excluded_nationalities or []
        )

        if overlapping_codes:
            raise ValidationError({
                'excluded_nationalities': (
                    'A nationality cannot be both eligible and excluded.'
                )
            })

        if (
            self.eligibility_scope == 'ETHIOPIA_ONLY'
            and set(self.eligible_nationalities or []) != {'ET'}
        ):
            raise ValidationError({
                'eligible_nationalities': (
                    'Ethiopia-only eligibility must contain only ET.'
                )
            })

    @property
    def verified_status_is_unverified(self):
        return self.verification_status != 'VERIFIED'

    def save(self, *args, **kwargs):
        self.official_source_url = normalize_url(
            self.official_source_url
        )
        self.official_application_url = normalize_url(
            self.official_application_url
        )

        with transaction.atomic():
            if (
                self.pk
                and self.source_status != 'AVAILABLE'
                and self.verification_status == 'VERIFIED'
            ):
                previous_status = OpportunitySourceRecord.objects.filter(
                    pk=self.pk,
                ).values_list(
                    'verification_status',
                    flat=True,
                ).first()
                if previous_status == 'VERIFIED':
                    self.verification_status = 'SOURCE_UNAVAILABLE'
                    self.verified_at = None
                    self.verified_by = None

            scholarship_ids = set()
            if self.scholarship_id:
                scholarship_ids.add(self.scholarship_id)
            if self.pk:
                previous = OpportunitySourceRecord.objects.filter(
                    pk=self.pk,
                ).values_list('scholarship_id', flat=True).first()
                if previous:
                    scholarship_ids.add(previous)

            is_verified_record = (
                self.verification_status == 'VERIFIED'
                and self.source_status == 'AVAILABLE'
                and self.verified_at is not None
                and self.verified_by_id is not None
                and self.source.is_active
                and self.verified_by.is_admin
                and (
                    self.normalized_deadline is None
                    or self.normalized_deadline >= timezone.localdate()
                )
            )
            if not is_verified_record and scholarship_ids:
                from apps.scholarships.models import Scholarship

                Scholarship.objects.filter(
                    pk__in=scholarship_ids,
                    is_published=True,
                ).update(
                    is_published=False,
                    updated_at=timezone.now(),
                )
                linked_scholarship = self._state.fields_cache.get(
                    'scholarship'
                )
                if linked_scholarship:
                    linked_scholarship.is_published = False

            opportunity_ids = set()
            if self.opportunity_id:
                opportunity_ids.add(self.opportunity_id)
            if self.pk:
                previous = OpportunitySourceRecord.objects.filter(
                    pk=self.pk,
                ).values_list('opportunity_id', flat=True).first()
                if previous:
                    opportunity_ids.add(previous)

            if not is_verified_record and opportunity_ids:
                Opportunity.objects.filter(
                    pk__in=opportunity_ids,
                    is_published=True,
                ).update(
                    is_published=False,
                    updated_at=timezone.now(),
                )
                linked_opportunity = self._state.fields_cache.get('opportunity')
                if linked_opportunity:
                    linked_opportunity.is_published = False

            self.full_clean()
            return super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.source_title} ({self.source.name})'
