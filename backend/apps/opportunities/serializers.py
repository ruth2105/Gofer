from rest_framework import serializers

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import Q
from django.utils import timezone

from .models import Opportunity, OpportunitySourceRecord


def _model_validation_error_detail(error):
    if hasattr(error, 'message_dict'):
        return error.message_dict
    return error.messages


class OpportunitySerializer(serializers.ModelSerializer):
    eligibility = serializers.ListField(
        child=serializers.CharField(),
        required=False,
    )
    benefits = serializers.ListField(
        child=serializers.CharField(),
        required=False,
    )
    documents_required = serializers.ListField(
        child=serializers.CharField(),
        required=False,
    )
    required_skills = serializers.ListField(
        child=serializers.CharField(),
        required=False,
    )
    eligible_nationalities = serializers.ListField(
        child=serializers.CharField(),
        required=False,
    )
    excluded_nationalities = serializers.ListField(
        child=serializers.CharField(),
        required=False,
    )
    verified_sources = serializers.SerializerMethodField()

    class Meta:
        model = Opportunity
        fields = (
            'id',
            'title',
            'slug',
            'short_description',
            'description',
            'organization',
            'country',
            'location',
            'category',
            'level',
            'eligibility',
            'eligibility_scope',
            'eligible_nationalities',
            'excluded_nationalities',
            'eligibility_notes',
            'benefits',
            'documents_required',
            'required_skills',
            'employment_type',
            'work_mode',
            'compensation_status',
            'compensation_amount',
            'compensation_currency',
            'compensation_period',
            'duration',
            'experience_requirement',
            'minimum_experience_years',
            'application_deadline',
            'application_url',
            'official_website',
            'verified_sources',
            'status',
            'is_published',
            'is_featured',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('id', 'slug', 'created_at', 'updated_at')

    def get_verified_sources(self, opportunity):
        today = timezone.localdate()
        records = OpportunitySourceRecord.objects.filter(
            opportunity=opportunity,
            verification_status='VERIFIED',
            source_status='AVAILABLE',
            verified_at__isnull=False,
            verified_by__role__in=('ADMIN', 'SUPERADMIN'),
            source__is_active=True,
            normalized_deadline=opportunity.application_deadline,
            eligibility_scope=opportunity.eligibility_scope,
            eligible_nationalities=opportunity.eligible_nationalities,
            excluded_nationalities=opportunity.excluded_nationalities,
        ).filter(
            Q(normalized_deadline__isnull=True)
            | Q(normalized_deadline__gte=today)
        ).filter(
            Q(official_application_url=opportunity.application_url)
            | Q(official_source_url=opportunity.application_url)
            | Q(official_source_url=opportunity.official_website)
        ).select_related('source')
        return [
            {
                'url': record.official_source_url,
                'organization': record.source.organization,
                'verified_at': record.verified_at,
                'verified_by': 'Gofer Exam administrator',
            }
            for record in records
        ]

    def create(self, validated_data):
        try:
            return super().create(validated_data)
        except DjangoValidationError as error:
            raise serializers.ValidationError(
                _model_validation_error_detail(error)
            ) from error

    def update(self, instance, validated_data):
        try:
            return super().update(instance, validated_data)
        except DjangoValidationError as error:
            raise serializers.ValidationError(
                _model_validation_error_detail(error)
            ) from error
