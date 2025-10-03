from django.db import models
from django.contrib.auth import get_user_model
from core.models import BaseModel
from households.models import Household

User = get_user_model()

class Program(BaseModel):
    """Independent Programs that can be created by County Executives"""

    PROGRAM_STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('suspended', 'Suspended'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    PROGRAM_TYPE_CHOICES = [
        ('graduation', 'Ultra-Poor Graduation'),
        ('microfinance', 'Microfinance'),
        ('agricultural', 'Agricultural Support'),
        ('education', 'Education Support'),
        ('health', 'Health Initiative'),
        ('infrastructure', 'Infrastructure Development'),
        ('skills_training', 'Skills Training'),
        ('youth_empowerment', 'Youth Empowerment'),
        ('women_empowerment', 'Women Empowerment'),
        ('other', 'Other'),
    ]

    name = models.CharField(max_length=200, unique=True)
    description = models.TextField()
    program_type = models.CharField(max_length=20, choices=PROGRAM_TYPE_CHOICES, default='other')
    status = models.CharField(max_length=20, choices=PROGRAM_STATUS_CHOICES, default='draft')

    # Program details
    budget = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    target_beneficiaries = models.PositiveIntegerField(default=0)
    duration_months = models.PositiveIntegerField(default=12)

    # Dates
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    application_deadline = models.DateTimeField(null=True, blank=True)

    # Creator and management
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_programs')
    county = models.CharField(max_length=100, blank=True)
    sub_county = models.CharField(max_length=100, blank=True)

    # Eligibility criteria (stored as JSON or text)
    eligibility_criteria = models.TextField(blank=True, help_text="Eligibility requirements for this program")
    application_requirements = models.TextField(blank=True, help_text="Documents and requirements for application")

    # Flags
    is_accepting_applications = models.BooleanField(default=True)
    requires_approval = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"

    @property
    def application_count(self):
        return self.applications.count()

    @property
    def approved_applications(self):
        return self.applications.filter(status='approved').count()

    @property
    def is_upg_program(self):
        """Check if this is an Ultra-Poor Graduation program"""
        return self.program_type == 'graduation'

    @property
    def requires_ppi_scoring(self):
        """Check if this program requires PPI scoring"""
        return self.is_upg_program

    @property
    def supports_business_groups(self):
        """Check if this program supports business group formation"""
        return self.is_upg_program

    @property
    def supports_savings_groups(self):
        """Check if this program supports savings group formation"""
        return self.is_upg_program

    @property
    def has_graduation_milestones(self):
        """Check if this program tracks graduation milestones"""
        return self.is_upg_program

    @property
    def supports_grants(self):
        """Check if this program supports SB/PR grants"""
        return self.is_upg_program

    @property
    def default_duration_months(self):
        """Get default duration based on program type"""
        if self.is_upg_program:
            return 12  # UPG is 12-month model
        return self.duration_months or 6  # Default for other programs


class ProgramApplication(BaseModel):
    """Applications from households/beneficiaries to programs"""

    APPLICATION_STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('waitlisted', 'Waitlisted'),
        ('withdrawn', 'Withdrawn'),
    ]

    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name='applications')
    household = models.ForeignKey(Household, on_delete=models.CASCADE, related_name='program_applications')

    status = models.CharField(max_length=20, choices=APPLICATION_STATUS_CHOICES, default='pending')
    application_date = models.DateTimeField(auto_now_add=True)

    # Application details
    motivation_letter = models.TextField(blank=True, help_text="Why the household wants to join this program")
    additional_notes = models.TextField(blank=True)

    # Review process
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_applications')
    review_date = models.DateTimeField(null=True, blank=True)
    review_notes = models.TextField(blank=True)

    # Approval process
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_applications')
    approval_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-application_date']
        unique_together = ['program', 'household']  # One application per household per program

    def __str__(self):
        return f"{self.household.name} - {self.program.name} ({self.get_status_display()})"


class ProgramBeneficiary(BaseModel):
    """Track households that are active beneficiaries of a program"""

    PARTICIPATION_STATUS_CHOICES = [
        ('active', 'Active'),
        ('suspended', 'Suspended'),
        ('graduated', 'Graduated'),
        ('dropped_out', 'Dropped Out'),
        ('terminated', 'Terminated'),
    ]

    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name='beneficiaries')
    household = models.ForeignKey(Household, on_delete=models.CASCADE, related_name='independent_program_participations')

    participation_status = models.CharField(max_length=20, choices=PARTICIPATION_STATUS_CHOICES, default='active')
    enrollment_date = models.DateField()
    graduation_date = models.DateField(null=True, blank=True)

    # Tracking
    progress_notes = models.TextField(blank=True)
    benefits_received = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    class Meta:
        ordering = ['-enrollment_date']
        unique_together = ['program', 'household']

    def __str__(self):
        return f"{self.household.name} in {self.program.name}"
