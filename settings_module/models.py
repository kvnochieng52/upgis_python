"""
Settings Module Models for UPG System
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import json

User = get_user_model()


class SystemConfiguration(models.Model):
    """
    System-wide configuration settings
    """
    SETTING_TYPES = [
        ('string', 'String'),
        ('integer', 'Integer'),
        ('boolean', 'Boolean'),
        ('json', 'JSON'),
        ('file', 'File Path'),
    ]

    key = models.CharField(max_length=100, unique=True, help_text="Configuration key identifier")
    value = models.TextField(help_text="Configuration value")
    setting_type = models.CharField(max_length=20, choices=SETTING_TYPES, default='string')
    description = models.TextField(blank=True, help_text="Description of this setting")
    category = models.CharField(max_length=50, default='general', help_text="Setting category")
    is_public = models.BooleanField(default=False, help_text="Can be viewed by non-admin users")
    is_editable = models.BooleanField(default=True, help_text="Can be modified")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_settings')
    modified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='modified_settings')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.key}: {self.value[:50]}"

    def get_typed_value(self):
        """Return the value converted to the appropriate type"""
        if self.setting_type == 'boolean':
            return self.value.lower() in ('true', '1', 'yes', 'on')
        elif self.setting_type == 'integer':
            try:
                return int(self.value)
            except ValueError:
                return 0
        elif self.setting_type == 'json':
            try:
                return json.loads(self.value)
            except json.JSONDecodeError:
                return {}
        return self.value

    class Meta:
        db_table = 'upg_system_configurations'
        ordering = ['category', 'key']


class UserSettings(models.Model):
    """
    User-specific settings and preferences
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='settings')

    # System preferences
    email_notifications = models.BooleanField(default=True)
    sms_notifications = models.BooleanField(default=False)
    dashboard_layout = models.JSONField(default=dict, blank=True)
    theme = models.CharField(max_length=20, default='light', choices=[('light', 'Light'), ('dark', 'Dark')])
    language = models.CharField(max_length=10, default='en', choices=[('en', 'English'), ('sw', 'Swahili')])
    timezone = models.CharField(max_length=50, default='Africa/Nairobi')

    # Security settings
    two_factor_enabled = models.BooleanField(default=False)
    last_password_change = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} Settings"

    class Meta:
        db_table = 'upg_user_settings'


class SystemAuditLog(models.Model):
    """
    System audit logging for tracking user actions
    """
    ACTION_TYPES = [
        ('create', 'Create'),
        ('read', 'Read'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('export', 'Export'),
        ('import', 'Import'),
        ('system', 'System Action'),
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=20, choices=ACTION_TYPES)
    model_name = models.CharField(max_length=100, blank=True, help_text="Django model name")
    object_id = models.CharField(max_length=100, blank=True, help_text="ID of the object acted upon")
    object_repr = models.CharField(max_length=200, blank=True, help_text="String representation of the object")

    # Request information
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    request_path = models.CharField(max_length=500, blank=True)
    request_method = models.CharField(max_length=10, blank=True)

    # Change details
    changes = models.JSONField(default=dict, blank=True, help_text="Details of what changed")
    additional_data = models.JSONField(default=dict, blank=True, help_text="Additional context data")

    # Status
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True)

    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        user_str = self.user.username if self.user else 'System'
        return f"{user_str} - {self.get_action_display()} - {self.timestamp}"

    class Meta:
        db_table = 'upg_system_audit_logs'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['action', 'timestamp']),
            models.Index(fields=['model_name', 'timestamp']),
        ]


class SystemAlert(models.Model):
    """
    System-wide alerts and notifications
    """
    ALERT_TYPES = [
        ('info', 'Information'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('maintenance', 'Maintenance'),
        ('security', 'Security'),
    ]

    ALERT_SCOPES = [
        ('system', 'System Wide'),
        ('role', 'Role Specific'),
        ('user', 'User Specific'),
    ]

    title = models.CharField(max_length=200)
    message = models.TextField()
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPES, default='info')
    scope = models.CharField(max_length=20, choices=ALERT_SCOPES, default='system')

    # Targeting
    target_roles = models.JSONField(default=list, blank=True, help_text="List of roles if scope is 'role'")
    target_users = models.ManyToManyField(User, blank=True, help_text="Specific users if scope is 'user'")

    # Display settings
    is_active = models.BooleanField(default=True)
    show_until = models.DateTimeField(null=True, blank=True, help_text="Alert expires after this date")
    is_dismissible = models.BooleanField(default=True, help_text="Users can dismiss this alert")

    # Tracking
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_alerts')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} ({self.get_alert_type_display()})"

    def is_expired(self):
        """Check if alert is expired"""
        if self.show_until:
            return timezone.now() > self.show_until
        return False

    def is_visible_to_user(self, user):
        """Check if alert should be shown to a specific user"""
        if not self.is_active or self.is_expired():
            return False

        if self.scope == 'system':
            return True
        elif self.scope == 'role':
            return user.role in self.target_roles
        elif self.scope == 'user':
            return user in self.target_users.all()

        return False

    class Meta:
        db_table = 'upg_system_alerts'
        ordering = ['-created_at']


class UserAlertDismissal(models.Model):
    """
    Track which users have dismissed which alerts
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    alert = models.ForeignKey(SystemAlert, on_delete=models.CASCADE)
    dismissed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'upg_user_alert_dismissals'
        unique_together = ['user', 'alert']


class SystemBackup(models.Model):
    """
    Track system backups
    """
    BACKUP_TYPES = [
        ('full', 'Full Backup'),
        ('incremental', 'Incremental Backup'),
        ('database', 'Database Only'),
        ('media', 'Media Files Only'),
    ]

    BACKUP_STATUS = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    name = models.CharField(max_length=200)
    backup_type = models.CharField(max_length=20, choices=BACKUP_TYPES, default='full')
    status = models.CharField(max_length=20, choices=BACKUP_STATUS, default='pending')

    file_path = models.CharField(max_length=500, blank=True)
    file_size = models.BigIntegerField(null=True, blank=True, help_text="File size in bytes")

    started_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    error_message = models.TextField(blank=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.name} - {self.get_status_display()}"

    @property
    def duration(self):
        """Calculate backup duration"""
        if self.completed_at and self.started_at:
            return self.completed_at - self.started_at
        return None

    class Meta:
        db_table = 'upg_system_backups'
        ordering = ['-started_at']