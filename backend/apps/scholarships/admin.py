
"""
Admin configuration for Scholarship model.
"""

from django.contrib import admin
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Scholarship


@admin.register(Scholarship)
class ScholarshipAdmin(admin.ModelAdmin):
    """Admin for Scholarship."""

    list_display = (
        'name',
        'provider',
        'country',
        'type',
        'level',
        'amount',
        'status',
        'is_published',
        'is_featured',
        'application_deadline',
    )

    list_filter = (
        'is_published',
        'status',
        'type',
        'level',
        'country',
        'is_featured',
        'is_popular',
    )

    search_fields = ('name', 'provider', 'country', 'description')

    readonly_fields = (
        'view_count',
        'application_count',
        'created_at',
        'updated_at',
    )

    prepopulated_fields = {'slug': ('name',)}

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'description', 'short_description')
        }),
        ('Organization', {
            'fields': ('provider', 'provider_logo', 'country')
        }),
        ('Details', {
            'fields': ('type', 'level', 'amount', 'amount_type')
        }),
        ('Eligibility', {
            'fields': (
                'eligibility',
                'nationality_eligibility',
                'target_countries',
                'excluded_countries',
                'required_gpa',
                'fields',
            )
        }),
        ('Application', {
            'fields': ('application_deadline', 'application_url', 'documents_required')
        }),
        ('Status', {
            'fields': ('status', 'is_published', 'is_featured', 'is_popular')
        }),
        ('Additional', {
            'fields': ('benefits', 'website_url', 'contact_email')
        }),
        ('Statistics', {
            'fields': ('view_count', 'application_count', 'success_rate')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'published_at')
        }),
    )

    actions = [
        'mark_as_featured',
        'mark_as_open',
        'mark_as_closed',
        'mark_as_expired',
        'publish_selected',
        'unpublish_selected',
    ]

    def has_add_permission(self, request):
        return request.user.is_admin and super().has_add_permission(request)

    def has_change_permission(self, request, obj=None):
        return request.user.is_admin and super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        return request.user.is_admin and super().has_delete_permission(request, obj)

    @admin.action(description="Mark selected scholarships as featured")
    def mark_as_featured(self, request, queryset):
        queryset.update(is_featured=True)

    @admin.action(description="Mark selected scholarships as open")
    def mark_as_open(self, request, queryset):
        queryset.update(status='OPEN')

    @admin.action(description="Mark selected scholarships as closed")
    def mark_as_closed(self, request, queryset):
        queryset.update(status='CLOSED', is_published=False)

    @admin.action(description="Mark expired scholarships as expired")
    def mark_as_expired(self, request, queryset):
        updated = queryset.filter(
            application_deadline__lt=timezone.localdate(),
        ).update(status='EXPIRED', is_published=False)
        self.message_user(
            request,
            f'{updated} expired scholarship record(s) marked expired and unpublished.',
            level=messages.SUCCESS,
        )

    @admin.action(description="Publish selected scholarships")
    def publish_selected(self, request, queryset):
        published = 0
        errors = []
        for scholarship in queryset:
            scholarship.is_published = True

            if not scholarship.published_at:
                scholarship.published_at = timezone.now()

            try:
                scholarship.save(
                    update_fields=['is_published', 'published_at', 'updated_at']
                )
            except ValidationError as error:
                errors.append(f'{scholarship.name}: {error}')
            else:
                published += 1

        if published:
            self.message_user(
                request,
                f'{published} scholarship record(s) published.',
                level=messages.SUCCESS,
            )

        if errors:
            self.message_user(
                request,
                'Some scholarships could not be published: '
                + '; '.join(errors),
                level=messages.ERROR,
            )

    @admin.action(description="Unpublish selected scholarships")
    def unpublish_selected(self, request, queryset):
        queryset.update(is_published=False)
