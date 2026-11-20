"""
Views for Document management.
Secure file upload, download, and management for students and authorized users.
"""

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, NotFound
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, OpenApiResponse
from apps.common.permissions import IsStudent, IsConsultant, IsAdminUser

from .models import Document
from .serializers import (
    DocumentSerializer,
    DocumentUpdateSerializer,
    DocumentVerificationSerializer,
    DocumentListSerializer
)


class DocumentViewSet(viewsets.ModelViewSet):
    """
    Document management for authenticated users.
    Students can upload/manage their own documents.
    Consultants can view assigned students' documents.
    Admins can view all documents.
    """
    
    queryset = Document.objects.select_related(
        'user', 'verified_by', 'application', 'consultation'
    ).all()
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return DocumentListSerializer
        elif self.action in ['update', 'partial_update']:
            return DocumentUpdateSerializer
        elif self.action == 'verify':
            return DocumentVerificationSerializer
        return DocumentSerializer
    
    def get_queryset(self):
        """Filter documents based on user role."""
        user = self.request.user
        
        if user.is_admin:
            # Admins can see all documents
            return self.queryset
        elif user.is_consultant:
            # Consultants can see their assigned students' documents
            from apps.consultations.models import Consultation
            assigned_student_ids = Consultation.objects.filter(
                consultant_profile__user=user
            ).values_list('student_id', flat=True)
            return self.queryset.filter(user_id__in=assigned_student_ids)
        else:
            # Students can only see their own documents
            return self.queryset.filter(user=user)
    
    def perform_create(self, serializer):
        """Create document with current user as owner."""
        serializer.save(user=self.request.user)
    
    def perform_update(self, serializer):
        """Ensure user can only update their own documents."""
        if serializer.instance.user != self.request.user and not self.request.user.is_admin:
            raise PermissionDenied('You can only update your own documents.')
        serializer.save()
    
    def perform_destroy(self, instance):
        """Ensure user can only delete their own documents."""
        if instance.user != self.request.user and not self.request.user.is_admin:
            raise PermissionDenied('You can only delete your own documents.')
        instance.delete()
    
    @extend_schema(
        tags=['Documents'],
        summary='Download document file',
        description='Download the document file. Students can download their own documents. '
                    'Consultants can download assigned students\' documents. '
                    'Admins can download all documents.',
        responses={
            200: OpenApiResponse(description='File download'),
            403: OpenApiResponse(description='Not authorized to access this document'),
            404: OpenApiResponse(description='Document not found'),
        }
    )
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """Download document file with authorization check."""
        document = get_object_or_404(
            Document.objects.select_related('user'),
            pk=pk
        )
        
        # Authorization check
        user = request.user
        can_access = False
        
        if user.is_admin:
            can_access = True
        elif user == document.user:
            can_access = True
        elif user.is_consultant:
            # Check if consultant is assigned to this student
            from apps.consultations.models import Consultation
            can_access = Consultation.objects.filter(
                consultant_profile__user=user,
                student=document.user
            ).exists()
        
        if not can_access:
            raise PermissionDenied('You are not authorized to access this document.')
        
        # Check if file exists
        if not document.file:
            raise Http404('Document file not found.')
        
        try:
            # Return file response
            response = FileResponse(
                document.file.open('rb'),
                content_type='application/octet-stream'
            )
            response['Content-Disposition'] = f'attachment; filename="{document.file.name.split("/")[-1]}"'
            return response
        except FileNotFoundError:
            raise Http404('Document file not found on server.')
    
    @extend_schema(
        tags=['Documents'],
        summary='Verify document',
        description='Consultant or admin can verify/approve/reject a document.',
        request=DocumentVerificationSerializer,
        responses={
            200: OpenApiResponse(description='Document verified'),
            403: OpenApiResponse(description='Not authorized'),
        }
    )
    @action(
        detail=True,
        methods=['post'],
        permission_classes=[permissions.IsAuthenticated, IsConsultant | IsAdminUser]
    )
    def verify(self, request, pk=None):
        """Verify document (consultant/admin only)."""
        document = self.get_object()
        serializer = DocumentVerificationSerializer(
            document,
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response({
            'message': 'Document verification updated successfully',
            'document': DocumentSerializer(document).data
        })
    
    @extend_schema(
        tags=['Documents'],
        summary='List documents by type',
        description='Get all documents filtered by type for the current user.',
    )
    @action(detail=False, methods=['get'])
    def by_type(self, request):
        """Get documents grouped by type."""
        documents = self.get_queryset()
        document_type = request.query_params.get('type')
        
        if document_type:
            documents = documents.filter(document_type=document_type)
        
        serializer = self.get_serializer(documents, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        tags=['Documents'],
        summary='List documents by application',
        description='Get all documents linked to a specific application.',
    )
    @action(detail=False, methods=['get'])
    def by_application(self, request):
        """Get documents for a specific application."""
        application_id = request.query_params.get('application_id')
        if not application_id:
            return Response(
                {'error': 'application_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        documents = self.get_queryset().filter(application_id=application_id)
        serializer = self.get_serializer(documents, many=True)
        return Response(serializer.data)

