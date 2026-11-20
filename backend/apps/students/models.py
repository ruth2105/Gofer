
"""
Student profile model for GOFER EXAM.
"""

import uuid

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class Education(models.Model):
    """
    Education history for students (multiple records allowed).
    """
    DEGREE_LEVEL_CHOICES = [
        ('HIGH_SCHOOL', 'High School'),
        ('ASSOCIATE', 'Associate Degree'),
        ('BACHELOR', 'Bachelor\'s Degree'),
        ('MASTER', 'Master\'s Degree'),
        ('DOCTORATE', 'Doctorate/PhD'),
        ('DIPLOMA', 'Diploma'),
        ('CERTIFICATE', 'Certificate'),
    ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    student_profile = models.ForeignKey(
        'StudentProfile',
        on_delete=models.CASCADE,
        related_name='education_history',
    )

    institution_name = models.CharField(max_length=200)
    degree_level = models.CharField(max_length=20, choices=DEGREE_LEVEL_CHOICES)
    field_of_study = models.CharField(max_length=200)
    country = models.ForeignKey(
        'common.Country',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='educations',
    )
    
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)  # Null if currently enrolled
    is_current = models.BooleanField(default=False)

    gpa = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0.0), MaxValueValidator(10.0)],
    )
    gpa_scale = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        default=4.0,
        help_text="GPA scale (e.g., 4.0, 5.0, 10.0)",
    )

    achievements = models.TextField(blank=True, help_text="Honors, awards, distinctions")
    description = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'student_education'
        verbose_name = 'Education'
        verbose_name_plural = 'Education History'
        ordering = ['-start_date']
        indexes = [
            models.Index(fields=['student_profile']),
            models.Index(fields=['degree_level']),
        ]

    def __str__(self):
        return f"{self.degree_level} in {self.field_of_study} at {self.institution_name}"


class WorkExperience(models.Model):
    """
    Work experience for students (multiple records allowed).
    """
    EMPLOYMENT_TYPE_CHOICES = [
        ('FULL_TIME', 'Full-time'),
        ('PART_TIME', 'Part-time'),
        ('INTERNSHIP', 'Internship'),
        ('CONTRACT', 'Contract'),
        ('FREELANCE', 'Freelance'),
        ('VOLUNTEER', 'Volunteer'),
    ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    student_profile = models.ForeignKey(
        'StudentProfile',
        on_delete=models.CASCADE,
        related_name='work_experience',
    )

    company_name = models.CharField(max_length=200)
    position_title = models.CharField(max_length=200)
    employment_type = models.CharField(max_length=20, choices=EMPLOYMENT_TYPE_CHOICES)
    
    location = models.CharField(max_length=200, blank=True)
    country = models.ForeignKey(
        'common.Country',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='work_experiences',
    )

    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)  # Null if currently working
    is_current = models.BooleanField(default=False)

    description = models.TextField(help_text="Key responsibilities and achievements")
    skills_used = models.JSONField(default=list, blank=True, help_text="List of skills used")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'student_work_experience'
        verbose_name = 'Work Experience'
        verbose_name_plural = 'Work Experience'
        ordering = ['-start_date']
        indexes = [
            models.Index(fields=['student_profile']),
            models.Index(fields=['employment_type']),
        ]

    def __str__(self):
        return f"{self.position_title} at {self.company_name}"


class Skill(models.Model):
    """
    Skills for students with proficiency levels.
    """
    PROFICIENCY_CHOICES = [
        ('BEGINNER', 'Beginner'),
        ('INTERMEDIATE', 'Intermediate'),
        ('ADVANCED', 'Advanced'),
        ('EXPERT', 'Expert'),
    ]

    SKILL_CATEGORY_CHOICES = [
        ('TECHNICAL', 'Technical'),
        ('LANGUAGE', 'Language'),
        ('SOFT_SKILL', 'Soft Skill'),
        ('ACADEMIC', 'Academic'),
        ('OTHER', 'Other'),
    ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    student_profile = models.ForeignKey(
        'StudentProfile',
        on_delete=models.CASCADE,
        related_name='skills',
    )

    name = models.CharField(max_length=100)
    category = models.CharField(max_length=20, choices=SKILL_CATEGORY_CHOICES, default='OTHER')
    proficiency = models.CharField(max_length=20, choices=PROFICIENCY_CHOICES, default='INTERMEDIATE')
    years_of_experience = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(50)],
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'student_skills'
        verbose_name = 'Skill'
        verbose_name_plural = 'Skills'
        ordering = ['category', 'name']
        unique_together = ['student_profile', 'name']  # Prevent duplicate skills
        indexes = [
            models.Index(fields=['student_profile']),
            models.Index(fields=['category']),
        ]

    def __str__(self):
        return f"{self.name} ({self.proficiency})"


class StudentProfile(models.Model):
    """
    Extended profile for students.
    One-to-one relationship with User model.
    """

    EDUCATION_LEVEL_CHOICES = [
        ('HIGH_SCHOOL', 'High School'),
        ('UNDERGRADUATE', 'Undergraduate'),
        ('GRADUATE', 'Graduate'),
        ('POSTGRADUATE', 'Postgraduate'),
    ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    user = models.OneToOneField(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='student_profile',
    )

    # Personal Information
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=20, blank=True)
    nationality = models.CharField(max_length=100, blank=True)
    nationality_country = models.ForeignKey(
        'common.Country',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='nationality_profiles',
    )
    passport_number = models.CharField(max_length=50, blank=True)

    # Contact Information
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    residence_country = models.ForeignKey(
        'common.Country',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='residence_profiles',
    )
    postal_code = models.CharField(max_length=20, blank=True)

    # Emergency Contact
    emergency_contact_name = models.CharField(max_length=200, blank=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True)
    emergency_contact_relationship = models.CharField(max_length=100, blank=True)

    # Educational Background
    current_education_level = models.CharField(
        max_length=20,
        choices=EDUCATION_LEVEL_CHOICES,
        default='UNDERGRADUATE',
    )
    school_name = models.CharField(max_length=200, blank=True)
    field_of_study = models.CharField(max_length=200, blank=True)

    graduation_year = models.IntegerField(
        null=True,
        blank=True,
        validators=[
            MinValueValidator(1950),
            MaxValueValidator(2050),
        ],
    )

    gpa = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[
            MinValueValidator(0.0),
            MaxValueValidator(4.0),
        ],
    )

    # Study Abroad Preferences
    target_countries = models.JSONField(default=list, blank=True)
    target_degree_level = models.CharField(max_length=50, blank=True)
    preferred_fields = models.JSONField(default=list, blank=True)
    budget_range = models.CharField(max_length=100, blank=True)

    # Test Scores
    english_test_type = models.CharField(max_length=50, blank=True)
    english_test_score = models.CharField(max_length=20, blank=True)
    gre_score = models.IntegerField(null=True, blank=True)
    gmat_score = models.IntegerField(null=True, blank=True)
    sat_score = models.IntegerField(null=True, blank=True)

    # Profile Completion & Status
    profile_completed = models.BooleanField(default=False)
    is_active_applicant = models.BooleanField(default=True)

    # Reward Points
    reward_points = models.IntegerField(default=0)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'student_profiles'
        verbose_name = 'Student Profile'
        verbose_name_plural = 'Student Profiles'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['country']),
            models.Index(fields=['current_education_level']),
        ]

    def __str__(self):
        return f"Student Profile: {self.user.get_full_name()}"

    @property
    def age(self):
        """Calculate age from date of birth."""

        if self.date_of_birth:
            from datetime import date

            today = date.today()

            return today.year - self.date_of_birth.year - (
                (today.month, today.day)
                < (self.date_of_birth.month, self.date_of_birth.day)
            )

        return None

    def get_profile_completion_details(self):
        """Return profile completion percentage and missing fields."""

        required_fields = [
            'date_of_birth',
            'nationality',
            'current_education_level',
            'school_name',
            'field_of_study',
            'target_countries',
            'target_degree_level',
            'preferred_fields',
        ]

        missing_fields = []

        for field in required_fields:
            value = getattr(self, field)

            if value is None or value == '' or value == []:
                missing_fields.append(field)

        completed = len(required_fields) - len(missing_fields)

        percentage = (completed / len(required_fields)) * 100

        return {
            'percentage': round(percentage, 2),
            'missing_fields': missing_fields,
            'is_completed': percentage >= 80,
        }

    def calculate_profile_completion(self):
        """Calculate and update profile completion status."""

        details = self.get_profile_completion_details()

        self.profile_completed = details['is_completed']

        return details['percentage']
