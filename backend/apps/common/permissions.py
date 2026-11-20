"""
Custom permission classes.
"""

from rest_framework import permissions


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Allow read-only access to everyone.
    Only admins can create, update, or delete.
    """
    
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        
        return request.user and request.user.is_authenticated and request.user.is_admin


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Allow owners to edit their own objects.
    Others can only read.
    """
    
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        
        return obj.user == request.user


class IsStudent(permissions.BasePermission):
    """Only allow students."""
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_student


class IsConsultant(permissions.BasePermission):
    """Only allow consultants."""
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_consultant


class IsAdminUser(permissions.BasePermission):
    """Allow ADMIN and SUPERADMIN accounts."""
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_admin


class IsAdmin(permissions.BasePermission):
    """Allow ordinary administrator accounts, excluding superadmins."""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == 'ADMIN'
        )


class IsSuperAdmin(permissions.BasePermission):
    """Allow only explicitly designated superadministrator accounts."""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.is_superadmin
        )


class IsStudentOwner(permissions.BasePermission):
    """Allow a student to access an object linked to their own account."""

    def has_object_permission(self, request, view, obj):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.is_student
            and getattr(obj, 'student_id', None) == request.user.pk
        )


class IsAssignedConsultant(permissions.BasePermission):
    """Allow consultants to access objects assigned to their own account."""

    def has_object_permission(self, request, view, obj):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.is_consultant
            and getattr(obj, 'consultant_id', None) == request.user.pk
        )


class IsNotificationOwner(permissions.BasePermission):
    """Allow an authenticated actor to access only their own notifications."""

    def has_object_permission(self, request, view, obj):
        return (
            request.user
            and request.user.is_authenticated
            and getattr(obj, 'user_id', None) == request.user.pk
        )
