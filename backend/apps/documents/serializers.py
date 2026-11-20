"""
Serializers for Document model.
"""

from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied
from django.core.exceptions import ValidationError
from .models import Document


class DocumentSerializer(serializers.ModelSerializer):
    """Serializer for Document model."""
    
    file_size_mb = serializers.FloatField(read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    owner_email = serializers.EmailField(source='user.email', read_only=True)
    owner_name = serializers.CharField(source='user.get_full_name', read_only=True)
    verified_by_name = serializers.CharField(source='verified_by.get_full_name', read_only=True, allow_null=True)
    
    class Meta:
        model = Document
        fields = (
            'id', 'user', 'owner_email', 'owner_name',
            'document_type', 'title', 'description',
            'file', 'file_size', 'file_size_mb', 'file_extension',
            'application', 'consultation',
            'status', 'verified_by', 'verified_by_name', 'verification_notes', 'verified_at',
            'expiry_date', 'is_expired', 'is_confidential',
            'created_at', 'updated_at'
        )
        read_only_fields = (
            'id', 'user', 'owner_email', 'owner_name',
            'file_size', 'file_size_mb', 'file_extension',
            'status', 'verified_by', 'verified_by_name', 'verification_notes', 'verified_at',
            'created_at', 'updated_at'
        )
    
    def validate_file(self, value):
        """Validate file size and type."""
        # Maximum file size: 10MB
        max_size = 10 * 1024 * 1024
        if value.size > max_size:
            raise serializers.ValidationError(
                f'File size must be less than 10MB. Current size: {round(value.size / (1024 * 1024), 2)}MB'
            )
        
        # Validate file extension
        allowed_extensions = ['pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png']
        extension = value.name.split('.')[-1].lower()
        if extension not in allowed_extensions:
            raise serializers.ValidationError(
                f'File type not supported. Allowed types: {", ".join(allowed_extensions)}'
            )
        
        return value
    
    def validate(self, attrs):
        """Validate document data."""
        user = self.context['request'].user
        
        # Students can only create documents for themselves
        if user.is_student and 'user' in attrs and attrs['user'] != user:
            raise PermissionDenied('You can only upload documents for your own account.')
        
        # Validate application ownership if linking to application
        if 'application' in attrs and attrs['application']:
            if attrs['application'].student.user != user and not user.is_admin:
                raise PermissionDenied('You can only link documents to your own applications.')
        
        # Validate consultation ownership if linking to consultation
        if 'consultation' in attrs and attrs['consultation']:
            if attrs['consultation'].student != user and not user.is_admin:
                raise PermissionDenied('You can only link documents to your own consultations.')
        
        return attrs
    
    def create(self, validated_data):
        """Set user from request."""
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class DocumentUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating document metadata (not the file itself)."""
    
    class Meta:
        model = Document
        fields = ('title', 'description', 'document_type', 'expiry_date', 'is_confidential')


class DocumentVerificationSerializer(serializers.ModelSerializer):
    """Serializer for consultant/admin document verification."""
    
    class Meta:
        model = Document
        fields = ('status', 'verification_notes')
    
    def validate_status(self, value):
        """Ensure only valid status transitions."""
        if value not in ['PENDING', 'APPROVED', 'REJECTED']:
            raise serializers.ValidationError('Invalid status.')
        return value
    
    def update(self, instance, validated_data):
        """Set verified_by and verified_at."""
        from django.utils import timezone
        
        instance.status = validated_data.get('status', instance.status)
        instance.verification_notes = validated_data.get('verification_notes', instance.verification_notes)
        instance.verified_by = self.context['request'].user
        instance.verified_at = timezone.now()
        instance.save()
        
        return instance


class DocumentListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for document lists."""
    
    file_size_mb = serializers.FloatField(read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    owner_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    class Meta:
        model = Document
        fields = (
            'id', 'owner_name', 'document_type', 'title',
            'file_size_mb', 'file_extension', 'status',
            'expiry_date', 'is_expired', 'is_confidential',
            'created_at', 'updated_at'
        )
