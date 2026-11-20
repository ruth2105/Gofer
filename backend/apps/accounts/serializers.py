"""
Serializers for User authentication and profile management.
"""

from django.db import IntegrityError, transaction
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from .models import User, normalize_email_address


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration."""
    
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True, label='Confirm Password')
    
    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'phone_number', 'password', 'password2')
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True},
        }
    
    def validate(self, attrs):
        """Validate password confirmation."""
        privileged_fields = {'role', 'is_staff', 'is_superuser', 'is_verified'}
        if privileged_fields.intersection(self.initial_data):
            raise serializers.ValidationError({
                'role': 'Public registration always creates a student account.',
            })
        attrs['email'] = normalize_email_address(attrs['email'])
        if User.objects.filter(email__iexact=attrs['email']).exists():
            raise serializers.ValidationError(
                {'email': 'A user with this email already exists.'}
            )
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs
    
    def create(self, validated_data):
        """Create new user with STUDENT role by default."""
        validated_data.pop('password2')
        
        try:
            with transaction.atomic():
                user = User.objects.create_user(
                    email=validated_data['email'],
            password=validated_data['password'],
                    first_name=validated_data.get('first_name', ''),
                    last_name=validated_data.get('last_name', ''),
                    phone_number=validated_data.get('phone_number', ''),
                    role='STUDENT'
                )
        except IntegrityError:
            if User.objects.filter(email__iexact=validated_data['email']).exists():
                raise serializers.ValidationError(
                    {'email': 'A user with this email already exists.'}
                )
            raise

        return user


class UserLoginSerializer(serializers.Serializer):
    """Serializer for user login."""
    
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True)
    
    def validate(self, attrs):
        """Validate credentials."""
        email = normalize_email_address(attrs.get('email', ''))
        password = attrs.get('password')
        
        if email and password:
            account = User.objects.filter(email__iexact=email).first()
            if account and not account.is_active:
                raise serializers.ValidationError('Invalid email or password.')

            user = authenticate(
                email=account.email if account else email,
                password=password,
            )
            
            if not user:
                raise serializers.ValidationError('Invalid email or password.')

            if user.is_student and not user.is_verified:
                raise PermissionDenied(
                    'Please verify your email before signing in.'
                )
            
            attrs['user'] = user
            return attrs
        else:
            raise serializers.ValidationError('Must include "email" and "password".')


class UserLogoutSerializer(serializers.Serializer):
    """Request body for blacklisting a refresh token."""

    refresh = serializers.CharField(write_only=True)


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model."""
    
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    
    class Meta:
        model = User
        fields = (
            'id', 'email', 'first_name', 'last_name', 'full_name',
            'phone_number', 'role', 'is_verified', 'date_joined'
        )
        read_only_fields = ('id', 'email', 'role', 'is_verified', 'date_joined')


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user profile."""
    
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'phone_number')

    def to_internal_value(self, data):
        privileged_fields = {'role', 'is_staff', 'is_superuser', 'is_verified'}
        if privileged_fields.intersection(data):
            raise PermissionDenied(
                'Account roles and verification status cannot be changed here.'
            )
        return super().to_internal_value(data)


class EmailVerificationSerializer(serializers.Serializer):
    """Validate a token submitted by the email-verification page."""

    token = serializers.CharField(write_only=True, max_length=128, trim_whitespace=False)


class ResendVerificationSerializer(serializers.Serializer):
    """Validate an address for the verification-email resend endpoint."""

    email = serializers.EmailField()

    def validate_email(self, value):
        return normalize_email_address(value)


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        return normalize_email_address(value)


class PasswordResetTokenSerializer(serializers.Serializer):
    uid = serializers.CharField(max_length=128)
    token = serializers.CharField(max_length=256, trim_whitespace=False)


class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField(max_length=128)
    token = serializers.CharField(max_length=256, trim_whitespace=False)
    new_password = serializers.CharField(write_only=True, max_length=128)
    new_password2 = serializers.CharField(write_only=True, max_length=128)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password2']:
            raise serializers.ValidationError({
                'new_password': "Password fields didn't match.",
            })
        try:
            validate_password(attrs['new_password'], user=self.context.get('user'))
        except DjangoValidationError as error:
            raise serializers.ValidationError({
                'new_password': list(error.messages),
            }) from error
        return attrs


class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, max_length=128)
    new_password2 = serializers.CharField(write_only=True, max_length=128)

    def validate(self, attrs):
        user = self.context['request'].user
        if not user.check_password(attrs['old_password']):
            raise serializers.ValidationError({
                'old_password': 'The current password is incorrect.',
            })
        if attrs['new_password'] != attrs['new_password2']:
            raise serializers.ValidationError({
                'new_password': "Password fields didn't match.",
            })
        try:
            validate_password(attrs['new_password'], user=user)
        except DjangoValidationError as error:
            raise serializers.ValidationError({
                'new_password': list(error.messages),
            }) from error
        return attrs


class ManagedUserSerializer(serializers.ModelSerializer):
    role = serializers.ChoiceField(choices=User.ROLE_CHOICES, required=False)

    class Meta:
        model = User
        fields = (
            'id',
            'email',
            'first_name',
            'last_name',
            'phone_number',
            'role',
            'is_active',
            'is_verified',
            'date_joined',
        )
        read_only_fields = ('id', 'email', 'is_verified', 'date_joined')

    def to_internal_value(self, data):
        privileged_fields = {
            'is_staff',
            'is_superuser',
            'groups',
            'user_permissions',
            'password',
            'email',
            'is_verified',
        }
        attempted_privileged_fields = privileged_fields.intersection(data)
        if attempted_privileged_fields:
            raise PermissionDenied(
                'These account security fields cannot be changed through this endpoint.'
            )
        if 'role' in data and not self.context['request'].user.is_superadmin:
            raise PermissionDenied(
                'Only a superadmin can change account roles.'
            )
        return super().to_internal_value(data)

    def validate(self, attrs):
        user = self.instance
        actor = self.context['request'].user
        if user and actor.pk == user.pk and (
            'role' in attrs
            or attrs.get('is_active') is False
        ):
            raise PermissionDenied(
                'You cannot change your own role or deactivate your own account.'
            )
        return attrs

    def update(self, instance, validated_data):
        role = validated_data.get('role', instance.role)
        for field, value in validated_data.items():
            setattr(instance, field, value)
        if 'role' in validated_data:
            instance.is_staff = role in ('ADMIN', 'SUPERADMIN')
            instance.is_superuser = role == 'SUPERADMIN'
        instance.save()
        return instance


class SecurityAuditEventSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    action = serializers.CharField(read_only=True)
    actor_id = serializers.UUIDField(read_only=True, allow_null=True)
    actor_role = serializers.CharField(read_only=True)
    target_id = serializers.UUIDField(read_only=True, allow_null=True)
    target_role = serializers.CharField(read_only=True)
    details = serializers.JSONField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
