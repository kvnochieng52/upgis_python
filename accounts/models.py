"""
User and Role Management Models for UPG System
Based on system roles from wireframe
"""

from django.contrib.auth.models import AbstractUser
from django.db import models
import secrets
from django.utils import timezone
from datetime import timedelta


class User(AbstractUser):
    """
    Custom User model with UPG-specific fields and roles
    """
    ROLE_CHOICES = [
        ('county_executive', 'County Executive (CECM & Governor)'),
        ('county_assembly', 'County Assembly Member'),
        ('ict_admin', 'ICT Administrator'),
        ('me_staff', 'M&E Staff'),
        ('field_associate', 'Field Associate/Mentor Supervisor'),
        ('mentor', 'Mentor'),
        ('beneficiary', 'Beneficiary'),
    ]

    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='mentor')
    phone_number = models.CharField(max_length=15, blank=True)
    office = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=50, default='Kenya')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Permission groups based on wireframe role-based access control matrix
    def has_module_permission(self, module_name, permission_type='full'):
        """
        Check if user has permission for specific module
        permission_type: 'full', 'read', 'none'
        """
        # Full access permissions (create, read, update, delete)
        full_permissions = {
            'county_executive': ['dashboard', 'grants', 'reports'],
            'county_assembly': ['dashboard', 'reports'],
            'ict_admin': ['dashboard', 'programs', 'households', 'business_groups', 'savings_groups', 'surveys', 'training', 'grants', 'reports', 'settings'],
            'me_staff': ['dashboard', 'programs', 'households', 'business_groups', 'savings_groups', 'surveys', 'training', 'reports'],
            'field_associate': ['dashboard', 'households', 'business_groups', 'savings_groups', 'surveys', 'training', 'grants'],
            'mentor': ['dashboard', 'households', 'business_groups', 'savings_groups', 'surveys', 'training'],
            'beneficiary': ['dashboard'],
        }

        # Read-only permissions
        read_permissions = {
            'county_executive': ['programs', 'households', 'business_groups', 'savings_groups', 'training'],
            'county_assembly': ['programs', 'households', 'business_groups', 'savings_groups'],
            'ict_admin': [],  # ICT admin has full access to everything
            'me_staff': ['grants'],
            'field_associate': ['programs', 'reports'],
            'mentor': ['programs', 'reports'],
            'beneficiary': ['programs', 'households', 'business_groups', 'savings_groups', 'training'],
        }

        user_full_permissions = full_permissions.get(self.role, [])
        user_read_permissions = read_permissions.get(self.role, [])

        if permission_type == 'full':
            return module_name in user_full_permissions
        elif permission_type == 'read':
            return module_name in user_read_permissions or module_name in user_full_permissions
        else:  # any access
            return module_name in user_full_permissions or module_name in user_read_permissions

    def __str__(self):
        return f"{self.get_full_name()} ({self.get_role_display()})"

    class Meta:
        db_table = 'upg_users'


class UserProfile(models.Model):
    """
    Extended user profile information
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(upload_to='avatars/', blank=True)
    bio = models.TextField(blank=True)
    assigned_villages = models.ManyToManyField('core.Village', blank=True)
    last_activity = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} Profile"

    class Meta:
        db_table = 'upg_user_profiles'


class PasswordResetToken(models.Model):
    """
    Password reset tokens for forgot password functionality
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_reset_tokens')
    token = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    used_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if not self.token:
            self.token = secrets.token_urlsafe(32)
        super().save(*args, **kwargs)

    def is_expired(self):
        """Check if token is expired (24 hours)"""
        expiry_time = self.created_at + timedelta(hours=24)
        return timezone.now() > expiry_time

    def is_valid(self):
        """Check if token is valid and not used"""
        return self.is_active and not self.used_at and not self.is_expired()

    def mark_as_used(self):
        """Mark token as used"""
        self.used_at = timezone.now()
        self.is_active = False
        self.save()

    def __str__(self):
        return f"Password reset token for {self.user.username}"

    class Meta:
        db_table = 'upg_password_reset_tokens'
        ordering = ['-created_at']