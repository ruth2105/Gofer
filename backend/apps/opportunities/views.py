import re

from django.db.models import Exists, OuterRef, Q, TextField
from django.db.models.functions import Cast
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework import filters, permissions, viewsets
from rest_framework.exceptions import ValidationError

from apps.common.permissions import IsAdminUser

from .models import Opportunity, OpportunitySourceRecord
from .serializers import OpportunitySerializer


class OpportunityViewSet(viewsets.ModelViewSet):
    serializer_class = OpportunitySerializer
    lookup_field = 'slug'
    filter_backends = (
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    )
    filterset_fields = (
        'category',
        'country',
        'level',
        'status',
        'is_featured',
        'employment_type',
        'work_mode',
        'compensation_status',
    )
    search_fields = (
        'title',
        'organization',
        'description',
        'country',
        'location',
        'experience_requirement',
    )
    ordering_fields = (
        'application_deadline',
        'created_at',
        'compensation_amount',
    )
    ordering = ('application_deadline', '-created_at')

    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated(), IsAdminUser()]

    def get_queryset(self):
        queryset = Opportunity.objects.all().prefetch_related(
            'source_records__source',
        )
        user = self.request.user
        if user.is_authenticated and user.is_admin:
            return queryset

        today = timezone.localdate()
        source_is_valid = (
            Q(verification_status='VERIFIED')
            & Q(source_status='AVAILABLE')
            & Q(verified_at__isnull=False)
            & Q(verified_by__role__in=('ADMIN', 'SUPERADMIN'))
            & Q(source__is_active=True)
            & (
                Q(normalized_deadline__isnull=True)
                | Q(normalized_deadline__gte=today)
            )
        )
        source_matches_listing = (
            (
                Q(normalized_deadline=OuterRef('application_deadline'))
                | Q(
                    normalized_deadline__isnull=True,
                    opportunity__application_deadline__isnull=True,
                )
            )
            & Q(eligibility_scope=OuterRef('eligibility_scope'))
            & Q(eligible_nationalities=OuterRef('eligible_nationalities'))
            & Q(excluded_nationalities=OuterRef('excluded_nationalities'))
            & (
                Q(official_application_url=OuterRef('application_url'))
                | Q(official_source_url=OuterRef('application_url'))
                | Q(official_source_url=OuterRef('official_website'))
            )
        )
        valid_source_records = OpportunitySourceRecord.objects.filter(
            opportunity_id=OuterRef('pk'),
        ).filter(source_is_valid & source_matches_listing)
        invalid_source_records = OpportunitySourceRecord.objects.filter(
            opportunity_id=OuterRef('pk'),
        ).filter(~(source_is_valid & source_matches_listing))
        return (
            queryset.filter(
                is_published=True,
                status__in=('OPEN', 'UPCOMING'),
            )
            .filter(
                Q(application_deadline__isnull=True)
                | Q(application_deadline__gte=today)
            )
            .filter(Exists(valid_source_records))
            .filter(~Exists(invalid_source_records))
        )

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)
        education = self.request.query_params.get('education')
        if education:
            queryset = queryset.filter(level=education)

        funding = self.request.query_params.get('funding')
        if funding:
            allowed_funding_values = {
                choice[0] for choice in Opportunity.COMPENSATION_STATUS_CHOICES
            }
            funding = funding.strip().upper()
            if funding not in allowed_funding_values:
                raise ValidationError({
                    'funding': 'Use UNKNOWN, PAID, or UNPAID.'
                })
            queryset = queryset.filter(compensation_status=funding)

        nationality = self.request.query_params.get('nationality')
        if nationality is None:
            return queryset

        nationality = nationality.strip().upper()
        if not re.fullmatch(r'[A-Z]{2}', nationality):
            raise ValidationError({
                'nationality': 'Use a two-letter ISO country code.'
            })

        # A nationality match requires explicitly confirmed eligibility;
        # missing eligibility data is never interpreted as universal access.
        return queryset.alias(
            eligible_codes=Cast('eligible_nationalities', output_field=TextField()),
            excluded_codes=Cast('excluded_nationalities', output_field=TextField()),
        ).filter(
            eligibility_scope__in=(
                'ETHIOPIA_ONLY',
                'ETHIOPIA_AND_OTHERS',
                'OTHER_NATIONALITIES',
            ),
        ).filter(
            eligible_codes__contains=f'"{nationality}"',
        ).exclude(
            excluded_codes__contains=f'"{nationality}"',
        )

    @extend_schema(
        tags=['Opportunities'],
        summary='List published opportunities',
        description=(
            'Lists only published opportunities. Search by title, organization, '
            'description, or country; filter by category, country, level, status, '
            'employment type, work mode, funding, nationality, and featured status. '
            'Education is an alias for level. Closed, expired, and unverified records '
            'are excluded.'
        ),
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        tags=['Opportunities'],
        summary='Get an opportunity',
        description='Retrieve a published opportunity by its slug.',
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
