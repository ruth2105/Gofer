"""
Admin configuration for StudentProfile model.
"""

from django.contrib import admin
from .models import StudentProfile


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    """Admin for StudentProfile."""
    
    list_display = ('user', 'current_education_level', 'nationality_country', 'residence_country', 'profile_completed', 'reward_points', 'created_at')
    list_filter = ('current_education_level', 'country', 'profile_completed', 'is_active_applicant')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'school_name', 'country')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('User', {'fields': ('user',)}),
        ('Personal Information', {'fields': ('date_of_birth', 'gender', 'nationality_country', 'nationality', 'passport_number')}),
        ('Contact', {'fields': ('address', 'city', 'residence_country', 'country', 'postal_code')}),
        ('Emergency Contact', {'fields': ('emergency_contact_name', 'emergency_contact_phone', 'emergency_contact_relationship')}),
        ('Education', {'fields': ('current_education_level', 'school_name', 'field_of_study', 'graduation_year', 'gpa')}),
        ('Study Preferences', {'fields': ('target_countries', 'target_degree_level', 'preferred_fields', 'budget_range')}),
        ('Test Scores', {'fields': ('english_test_type', 'english_test_score', 'gre_score', 'gmat_score', 'sat_score')}),
        ('Status', {'fields': ('profile_completed', 'is_active_applicant', 'reward_points')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )


from .models import Education, WorkExperience, Skill


class EducationInline(admin.TabularInline):
    """Inline admin for education history."""
    model = Education
    extra = 0
    fields = ('institution_name', 'degree_level', 'field_of_study', 'country', 'start_date', 'end_date', 'is_current', 'gpa')
    readonly_fields = ()


class WorkExperienceInline(admin.TabularInline):
    """Inline admin for work experience."""
    model = WorkExperience
    extra = 0
    fields = ('company_name', 'position_title', 'employment_type', 'start_date', 'end_date', 'is_current')
    readonly_fields = ()


class SkillInline(admin.TabularInline):
    """Inline admin for skills."""
    model = Skill
    extra = 0
    fields = ('name', 'category', 'proficiency', 'years_of_experience')
    readonly_fields = ()


@admin.register(Education)
class EducationAdmin(admin.ModelAdmin):
    """Admin for Education."""
    list_display = ('institution_name', 'degree_level', 'field_of_study', 'student_profile', 'start_date', 'end_date', 'is_current')
    list_filter = ('degree_level', 'is_current', 'country')
    search_fields = ('institution_name', 'field_of_study', 'student_profile__user__email')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Student', {'fields': ('student_profile',)}),
        ('Education Details', {'fields': ('institution_name', 'degree_level', 'field_of_study', 'country')}),
        ('Duration', {'fields': ('start_date', 'end_date', 'is_current')}),
        ('Performance', {'fields': ('gpa', 'gpa_scale', 'achievements')}),
        ('Description', {'fields': ('description',)}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )


@admin.register(WorkExperience)
class WorkExperienceAdmin(admin.ModelAdmin):
    """Admin for WorkExperience."""
    list_display = ('company_name', 'position_title', 'employment_type', 'student_profile', 'start_date', 'end_date', 'is_current')
    list_filter = ('employment_type', 'is_current', 'country')
    search_fields = ('company_name', 'position_title', 'student_profile__user__email')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Student', {'fields': ('student_profile',)}),
        ('Position Details', {'fields': ('company_name', 'position_title', 'employment_type')}),
        ('Location', {'fields': ('location', 'country')}),
        ('Duration', {'fields': ('start_date', 'end_date', 'is_current')}),
        ('Details', {'fields': ('description', 'skills_used')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    """Admin for Skill."""
    list_display = ('name', 'category', 'proficiency', 'years_of_experience', 'student_profile')
    list_filter = ('category', 'proficiency')
    search_fields = ('name', 'student_profile__user__email')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Student', {'fields': ('student_profile',)}),
        ('Skill Details', {'fields': ('name', 'category', 'proficiency', 'years_of_experience')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )


# Update the StudentProfileAdmin to include inlines
StudentProfileAdmin.inlines = [EducationInline, WorkExperienceInline, SkillInline]
