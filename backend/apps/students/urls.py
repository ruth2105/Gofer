"""
URL routes for GOFER EXAM student profiles.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    CurrentStudentProfileView,
    StudentProfileCompletionView,
    StudentProfileDetailView,
    EducationViewSet,
    WorkExperienceViewSet,
    SkillViewSet,
)

app_name = 'students'

router = DefaultRouter()
router.register(r'education', EducationViewSet, basename='education')
router.register(r'experience', WorkExperienceViewSet, basename='experience')
router.register(r'skills', SkillViewSet, basename='skills')

urlpatterns = [
    path(
        'me/',
        CurrentStudentProfileView.as_view(),
        name='current_profile',
    ),
    path(
        'me/detail/',
        StudentProfileDetailView.as_view(),
        name='profile_detail',
    ),
    path(
        'me/completion/',
        StudentProfileCompletionView.as_view(),
        name='profile_completion',
    ),
    path('', include(router.urls)),
]