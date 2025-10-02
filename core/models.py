"""
Core models for UPG System
Based on Graduation Model Tracking System data dictionary
"""

from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class BaseModel(models.Model):
    """
    Abstract base model with common fields
    """
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Mentor(models.Model):
    """
    Business Mentor Contact Information
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='mentor_profile')
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    country = models.CharField(max_length=50, default='Kenya')
    office = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    class Meta:
        db_table = 'upg_mentors'


class BusinessMentorCycle(models.Model):
    """
    Business Mentor Cycle - logs cycle details and activities
    """
    bm_cycle_name = models.CharField(max_length=100, unique=True)
    business_mentor = models.ForeignKey(Mentor, on_delete=models.CASCADE)
    field_associate = models.CharField(max_length=100)
    cycle = models.CharField(max_length=20)  # e.g., FY25C1
    project = models.CharField(max_length=100)
    office = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.bm_cycle_name

    class Meta:
        db_table = 'upg_business_mentor_cycles'


class County(models.Model):
    """
    County information
    """
    name = models.CharField(max_length=100, unique=True)
    country = models.CharField(max_length=50, default='Kenya')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'upg_counties'
        verbose_name_plural = 'Counties'


class SubCounty(models.Model):
    """
    Sub-County information
    """
    name = models.CharField(max_length=100)
    county = models.ForeignKey(County, on_delete=models.CASCADE, related_name='subcounties')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.county.name}"

    class Meta:
        db_table = 'upg_subcounties'
        verbose_name_plural = 'Sub-Counties'
        unique_together = ['name', 'county']


class Village(models.Model):
    """
    Village information including subcounty and coverage
    """
    name = models.CharField(max_length=100)
    subcounty_obj = models.ForeignKey(SubCounty, on_delete=models.CASCADE, related_name='villages', null=True, blank=True)
    saturation = models.CharField(max_length=50, blank=True)  # Coverage level
    qualified_hhs_per_village = models.IntegerField(default=0)
    country = models.CharField(max_length=50, default='Kenya')
    distance_to_market = models.IntegerField(default=0, help_text="Distance to market in kilometers")
    is_program_area = models.BooleanField(default=True, help_text="Whether this village is in a program target area")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.subcounty_obj:
            return f"{self.name} - {self.subcounty_obj.name}"
        return f"{self.name}"

    @property
    def subcounty(self):
        """Backward compatibility property"""
        return self.subcounty_obj.name if self.subcounty_obj else ""

    class Meta:
        db_table = 'upg_villages'


class Program(models.Model):
    """
    UPG Program definition and management
    """
    PROGRAM_STATUS_CHOICES = [
        ('planning', 'Planning'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('suspended', 'Suspended'),
    ]

    name = models.CharField(max_length=100)
    cycle = models.CharField(max_length=20)  # e.g., FY25C1
    country = models.CharField(max_length=50, default='Kenya')
    office = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, choices=PROGRAM_STATUS_CHOICES, default='planning')
    target_households = models.IntegerField(default=0)
    target_villages = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.cycle})"

    class Meta:
        db_table = 'upg_programs'


class AuditLog(models.Model):
    """
    System audit trail for all major actions
    """
    ACTION_CHOICES = [
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('view', 'View'),
        ('login', 'Login'),
        ('logout', 'Logout'),
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    model_name = models.CharField(max_length=100)
    object_id = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.action} - {self.model_name} - {self.timestamp}"

    class Meta:
        db_table = 'upg_audit_logs'
        ordering = ['-timestamp']


class ESRImport(models.Model):
    """
    ESR (External Service Record) Import tracking
    """
    IMPORT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    IMPORT_TYPE_CHOICES = [
        ('household', 'Household Data'),
        ('business_group', 'Business Group Data'),
        ('savings_group', 'Savings Group Data'),
        ('survey', 'Survey Data'),
        ('mixed', 'Mixed Data'),
    ]

    file_name = models.CharField(max_length=255)
    file_path = models.FileField(upload_to='esr_imports/')
    import_type = models.CharField(max_length=20, choices=IMPORT_TYPE_CHOICES)
    imported_by = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=IMPORT_STATUS_CHOICES, default='pending')
    total_records = models.IntegerField(default=0)
    successful_imports = models.IntegerField(default=0)
    failed_imports = models.IntegerField(default=0)
    error_log = models.TextField(blank=True)
    import_summary = models.JSONField(default=dict, blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"ESR Import - {self.file_name} - {self.status}"

    @property
    def success_rate(self):
        if self.total_records == 0:
            return 0
        return (self.successful_imports / self.total_records) * 100

    class Meta:
        db_table = 'upg_esr_imports'
        ordering = ['-started_at']


class ESRImportRecord(models.Model):
    """
    Individual records from ESR imports with mapping details
    """
    RECORD_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processed', 'Processed'),
        ('failed', 'Failed'),
        ('skipped', 'Skipped'),
    ]

    esr_import = models.ForeignKey(ESRImport, on_delete=models.CASCADE, related_name='records')
    row_number = models.IntegerField()
    raw_data = models.JSONField()  # Original data from ESR
    mapped_data = models.JSONField(default=dict)  # Mapped to UPG fields
    status = models.CharField(max_length=20, choices=RECORD_STATUS_CHOICES, default='pending')
    error_message = models.TextField(blank=True)
    created_object_type = models.CharField(max_length=100, blank=True)  # Model name
    created_object_id = models.CharField(max_length=100, blank=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"ESR Record #{self.row_number} - {self.status}"

    class Meta:
        db_table = 'upg_esr_import_records'
        ordering = ['row_number']


class SMSLog(models.Model):
    """
    SMS notification logging for tracking all SMS communications
    """
    phone_number = models.CharField(max_length=20)
    message = models.TextField()
    success = models.BooleanField(default=False)
    provider = models.CharField(max_length=50, help_text="SMS provider used")
    error_message = models.TextField(blank=True)
    sent_at = models.DateTimeField(auto_now_add=True)

    # Optional relationships
    household = models.ForeignKey('households.Household', on_delete=models.SET_NULL, null=True, blank=True)
    training = models.ForeignKey('training.Training', on_delete=models.SET_NULL, null=True, blank=True)
    mentor = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        status = "✓" if self.success else "✗"
        return f"{status} SMS to {self.phone_number} - {self.sent_at.strftime('%Y-%m-%d %H:%M')}"

    class Meta:
        db_table = 'upg_sms_logs'
        ordering = ['-sent_at']