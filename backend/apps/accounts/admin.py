"""
Admin configuration for User model.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from apps.accounts.audit import record_security_event
from .models import SecurityAuditEvent, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Custom admin for User model."""
    
    list_display = ('email', 'first_name', 'last_name', 'role', 'is_active', 'is_verified', 'date_joined')
    list_filter = ('role', 'is_active', 'is_verified', 'is_staff', 'date_joined')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'phone_number')}),
        ('Permissions', {'fields': ('role', 'is_active', 'is_verified', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important Dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'role', 'password1', 'password2'),
        }),
    )
    
    readonly_fields = ('date_joined', 'last_login', 'is_verified')

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = set(self.readonly_fields) | {
            'role',
            'is_staff',
            'is_superuser',
        }
        if not request.user.is_superadmin:
            readonly_fields.update({'groups', 'user_permissions'})
        return tuple(sorted(readonly_fields))

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def save_model(self, request, obj, form, change):
        previous_active = None
        if change:
            previous_active = User.objects.values_list(
                'is_active',
                flat=True,
            ).get(pk=obj.pk)
        super().save_model(request, obj, form, change)
        if change and previous_active != obj.is_active:
            record_security_event(
                'USER_ACTIVATED' if obj.is_active else 'USER_DEACTIVATED',
                actor=request.user,
                target=obj,
                details={
                    'before': {'is_active': previous_active},
                    'after': {'is_active': obj.is_active},
                    'source': 'django_admin',
                },
            )

    def save_related(self, request, form, formsets, change):
        user = form.instance
        previous_groups = set(user.groups.values_list('pk', flat=True))
        previous_permissions = set(user.user_permissions.values_list('pk', flat=True))
        super().save_related(request, form, formsets, change)
        current_groups = set(user.groups.values_list('pk', flat=True))
        current_permissions = set(user.user_permissions.values_list('pk', flat=True))
        if (
            previous_groups != current_groups
            or previous_permissions != current_permissions
        ):
            record_security_event(
                'USER_PERMISSIONS_CHANGED',
                actor=request.user,
                target=user,
                details={
                    'before': {
                        'groups': sorted(previous_groups),
                        'user_permissions': sorted(previous_permissions),
                    },
                    'after': {
                        'groups': sorted(current_groups),
                        'user_permissions': sorted(current_permissions),
                    },
                },
            )


@admin.register(SecurityAuditEvent)
class SecurityAuditEventAdmin(admin.ModelAdmin):
    list_display = ('action', 'actor_role', 'target_role', 'created_at')
    list_filter = ('action', 'actor_role', 'target_role', 'created_at')
    ordering = ('-created_at',)
    readonly_fields = (
        'action',
        'actor',
        'actor_role',
        'target',
        'target_role',
        'details',
        'created_at',
    )

    def has_view_permission(self, request, obj=None):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_superadmin
            and super().has_view_permission(request, obj)
        )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
