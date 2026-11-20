
"""
Views for GOFER EXAM student profiles.
"""

from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied

from drf_spectacular.utils import extend_schema
from apps.common.permissions import IsStudent

from .serializers import (
    StudentProfileSerializer,
    StudentProfileCompletionSerializer,
)


def get_student_profile(user):
    """Get or create the authenticated student's profile."""

    if user.role != 'STUDENT':
        raise PermissionDenied(
            'Only student accounts can access student profiles.'
        )

    from .models import StudentProfile

    profile, _ = StudentProfile.objects.get_or_create(user=user)

    return profile


class CurrentStudentProfileView(generics.RetrieveUpdateAPIView):
    """Retrieve or partially update the current student's profile."""

    serializer_class = StudentProfileSerializer
    permission_classes = [permissions.IsAuthenticated, IsStudent]

    http_method_names = ['get', 'patch', 'head', 'options']

    def get_object(self):
        return get_student_profile(self.request.user)

    @extend_schema(
        summary='Get current student profile',
        responses={200: StudentProfileSerializer},
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(
        summary='Update current student profile',
        request=StudentProfileSerializer,
        responses={200: StudentProfileSerializer},
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)


class StudentProfileCompletionView(generics.GenericAPIView):
    """Return the current student's profile completion."""

    permission_classes = [permissions.IsAuthenticated, IsStudent]
    serializer_class = StudentProfileCompletionSerializer

    @extend_schema(
        summary='Get student profile completion',
        responses={200: StudentProfileCompletionSerializer},
    )
    def get(self, request, *args, **kwargs):
        profile = get_student_profile(request.user)

        details = profile.get_profile_completion_details()

        serializer = self.get_serializer(data=details)
        serializer.is_valid(raise_exception=True)

        return Response(serializer.data)


from rest_framework import viewsets, status
from .models import Education, WorkExperience, Skill
from .serializers import (
    EducationSerializer,
    WorkExperienceSerializer,
    SkillSerializer,
    StudentProfileDetailSerializer,
)


class EducationViewSet(viewsets.ModelViewSet):
    """
    CRUD operations for student education history.
    Students can only manage their own education records.
    """
    
    serializer_class = EducationSerializer
    permission_classes = [permissions.IsAuthenticated, IsStudent]
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']
    
    def get_queryset(self):
        """Return education records for the current student's profile."""
        profile = get_student_profile(self.request.user)
        return Education.objects.filter(student_profile=profile).select_related('country')
    
    def perform_create(self, serializer):
        """Create education record linked to current student profile."""
        profile = get_student_profile(self.request.user)
        
        # If marking as current, unset other current education at same level
        if serializer.validated_data.get('is_current'):
            Education.objects.filter(
                student_profile=profile,
                degree_level=serializer.validated_data['degree_level'],
                is_current=True
            ).update(is_current=False)
        
        serializer.save(student_profile=profile)


class WorkExperienceViewSet(viewsets.ModelViewSet):
    """
    CRUD operations for student work experience.
    Students can only manage their own work experience records.
    """
    
    serializer_class = WorkExperienceSerializer
    permission_classes = [permissions.IsAuthenticated, IsStudent]
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']
    
    def get_queryset(self):
        """Return work experience records for the current student's profile."""
        profile = get_student_profile(self.request.user)
        return WorkExperience.objects.filter(student_profile=profile).select_related('country')
    
    def perform_create(self, serializer):
        """Create work experience record linked to current student profile."""
        profile = get_student_profile(self.request.user)
        serializer.save(student_profile=profile)


class SkillViewSet(viewsets.ModelViewSet):
    """
    CRUD operations for student skills.
    Students can only manage their own skills.
    """
    
    serializer_class = SkillSerializer
    permission_classes = [permissions.IsAuthenticated, IsStudent]
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']
    
    def get_queryset(self):
        """Return skills for the current student's profile."""
        profile = get_student_profile(self.request.user)
        return Skill.objects.filter(student_profile=profile)
    
    def perform_create(self, serializer):
        """Create skill record linked to current student profile."""
        profile = get_student_profile(self.request.user)
        
        # Check for duplicate skill names (case-insensitive)
        skill_name = serializer.validated_data['name']
        existing = Skill.objects.filter(
            student_profile=profile,
            name__iexact=skill_name
        ).exists()
        
        if existing:
            from rest_framework.exceptions import ValidationError
            raise ValidationError({'name': 'This skill already exists in your profile.'})
        
        serializer.save(student_profile=profile)


class StudentProfileDetailView(generics.RetrieveAPIView):
    """
    Retrieve comprehensive student profile including education, experience, and skills.
    """
    
    serializer_class = StudentProfileDetailSerializer
    permission_classes = [permissions.IsAuthenticated, IsStudent]
    
    def get_object(self):
        return get_student_profile(self.request.user)
    
    @extend_schema(
        summary='Get detailed student profile',
        description='Returns complete student profile with education history, work experience, and skills.',
        responses={200: StudentProfileDetailSerializer},
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
