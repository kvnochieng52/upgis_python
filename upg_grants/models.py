"""
UPG-Specific Grant Management Models
SB (Seed Business) Grants and PR (Performance Recognition) Grants
Only applicable for Ultra-Poor Graduation programs
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from decimal import Decimal
from programs.models import Program
from business_groups.models import BusinessGroup
from savings_groups.models import BusinessSavingsGroup
from core.models import BaseModel

User = get_user_model()


class HouseholdGrantApplication(BaseModel):
    """
    Grant applications submitted by individual households
    Can be reviewed and approved by program managers, county directors, or executives
    """
    GRANT_TYPE_CHOICES = [
        ('seed_business', 'Seed Business Grant'),
        ('performance_recognition', 'Performance Recognition Grant'),
        ('livelihood', 'Livelihood Grant'),
        ('emergency', 'Emergency Grant'),
        ('education', 'Education Support Grant'),
        ('housing', 'Housing Improvement Grant'),
        ('other', 'Other'),
    ]

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('disbursed', 'Disbursed'),
        ('cancelled', 'Cancelled'),
    ]

    # Applicant information - one of these three must be filled
    household = models.ForeignKey('households.Household', on_delete=models.CASCADE, related_name='grant_applications', null=True, blank=True,
                                  help_text="For individual household applications")
    business_group = models.ForeignKey(BusinessGroup, on_delete=models.CASCADE, related_name='grant_applications', null=True, blank=True,
                                       help_text="For business group applications")
    savings_group = models.ForeignKey(BusinessSavingsGroup, on_delete=models.CASCADE, related_name='grant_applications', null=True, blank=True,
                                      help_text="For savings group applications")

    submitted_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='submitted_grant_applications',
                                    help_text="User who submitted the application")
    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name='household_grant_applications', null=True, blank=True,
                                help_text="Optional - for program-specific funding")

    # Grant details
    grant_type = models.CharField(max_length=30, choices=GRANT_TYPE_CHOICES)
    requested_amount = models.DecimalField(max_digits=10, decimal_places=2)
    approved_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    # Application details
    title = models.CharField(max_length=200, help_text="Brief title of grant purpose")
    purpose = models.TextField(help_text="Detailed purpose and justification for the grant")
    business_plan = models.TextField(blank=True, help_text="Business plan if applicable")
    expected_outcomes = models.TextField(help_text="Expected outcomes and impact")
    budget_breakdown = models.JSONField(default=dict, blank=True, help_text="Itemized budget as JSON")

    # Supporting documents (stored as file paths or URLs)
    supporting_documents = models.JSONField(default=list, blank=True, help_text="List of document paths")

    # Status and workflow
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    submission_date = models.DateTimeField(null=True, blank=True)

    # Review process
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='reviewed_household_grants')
    review_date = models.DateTimeField(null=True, blank=True)
    review_notes = models.TextField(blank=True)
    review_score = models.IntegerField(null=True, blank=True, help_text="Review score 0-100")

    # Approval process (requires program_manager, county_director, or executive role)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='approved_household_grants')
    approval_date = models.DateTimeField(null=True, blank=True)
    approval_notes = models.TextField(blank=True)

    # Disbursement
    disbursement_date = models.DateField(null=True, blank=True)
    disbursed_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    disbursed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='disbursed_household_grants')
    disbursement_method = models.CharField(max_length=50, blank=True,
                                          choices=[
                                              ('bank_transfer', 'Bank Transfer'),
                                              ('mobile_money', 'Mobile Money'),
                                              ('cash', 'Cash'),
                                              ('check', 'Check'),
                                          ])
    disbursement_reference = models.CharField(max_length=100, blank=True)

    # Progress tracking
    utilization_report = models.TextField(blank=True, help_text="How the grant was utilized")
    utilization_date = models.DateField(null=True, blank=True)
    final_outcomes = models.TextField(blank=True, help_text="Final outcomes achieved")

    class Meta:
        verbose_name = "Household Grant Application"
        verbose_name_plural = "Household Grant Applications"
        ordering = ['-created_at']
        db_table = 'upg_household_grant_applications'

    def __str__(self):
        applicant_name = self.get_applicant_name()
        return f"{applicant_name} - {self.get_grant_type_display()} - {self.get_status_display()}"

    def get_applicant_name(self):
        """Get the name of the applicant (household, business group, or savings group)"""
        if self.household:
            return self.household.name
        elif self.business_group:
            return self.business_group.name
        elif self.savings_group:
            return self.savings_group.name
        return "Unknown Applicant"

    def get_applicant_type(self):
        """Get the type of applicant"""
        if self.household:
            return "household"
        elif self.business_group:
            return "business_group"
        elif self.savings_group:
            return "savings_group"
        return "unknown"

    def clean(self):
        """Validate that exactly one applicant type is specified"""
        applicants = [self.household, self.business_group, self.savings_group]
        applicants_filled = [a for a in applicants if a is not None]

        if len(applicants_filled) == 0:
            raise ValidationError("Must specify either household, business_group, or savings_group")
        if len(applicants_filled) > 1:
            raise ValidationError("Cannot specify multiple applicant types")

        super().clean()

    def can_be_reviewed_by(self, user):
        """Check if user has permission to review this application"""
        return user.role in ['program_manager', 'county_director', 'executive', 'ict_admin', 'me_staff']

    def can_be_approved_by(self, user):
        """Check if user has permission to approve this application"""
        return user.role in ['program_manager', 'county_director', 'executive']

    @property
    def is_pending_review(self):
        return self.status in ['submitted', 'under_review']

    @property
    def is_approved(self):
        return self.status == 'approved'

    @property
    def remaining_amount(self):
        """Calculate remaining amount to be disbursed"""
        approved = self.approved_amount or self.requested_amount
        return approved - self.disbursed_amount


class UPGGrantManager(models.Manager):
    """Manager to filter grants only for UPG programs"""

    def get_queryset(self):
        return super().get_queryset().filter(
            program__program_type='graduation'
        )


class SBGrant(BaseModel):
    """
    Seed Business (SB) Grants - Initial capital grants for business groups
    Only available for UPG programs
    """
    GRANT_STATUS_CHOICES = [
        ('pending', 'Pending Application'),
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('disbursed', 'Disbursed'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ]

    DISBURSEMENT_STATUS_CHOICES = [
        ('not_disbursed', 'Not Disbursed'),
        ('partially_disbursed', 'Partially Disbursed'),
        ('fully_disbursed', 'Fully Disbursed'),
    ]

    # Core relationships
    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name='sb_grants')
    business_group = models.OneToOneField(BusinessGroup, on_delete=models.CASCADE, related_name='sb_grant', null=True, blank=True,
                                          help_text="For business group applications")
    household = models.ForeignKey('households.Household', on_delete=models.CASCADE, related_name='sb_grants', null=True, blank=True,
                                  help_text="For individual household applications")
    savings_group = models.ForeignKey(BusinessSavingsGroup, on_delete=models.CASCADE, related_name='sb_grants', null=True, blank=True,
                                      help_text="For savings group applications")

    # Application submitter
    submitted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='submitted_sb_grants',
                                    help_text="User who submitted the application")

    # Grant details - Enhanced calculations
    base_grant_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('15000.00'), help_text="Base grant amount")
    calculated_grant_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Auto-calculated based on criteria")
    final_grant_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Final approved amount")

    # Calculation factors
    group_size_factor = models.DecimalField(max_digits=3, decimal_places=2, default=Decimal('1.00'), help_text="Multiplier based on group size")
    business_type_factor = models.DecimalField(max_digits=3, decimal_places=2, default=Decimal('1.00'), help_text="Multiplier based on business type")
    location_factor = models.DecimalField(max_digits=3, decimal_places=2, default=Decimal('1.00'), help_text="Geographic location adjustment")
    performance_factor = models.DecimalField(max_digits=3, decimal_places=2, default=Decimal('1.00'), help_text="Based on group performance")

    application_date = models.DateField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=GRANT_STATUS_CHOICES, default='pending')
    disbursement_status = models.CharField(max_length=20, choices=DISBURSEMENT_STATUS_CHOICES, default='not_disbursed')

    # Application details
    business_plan = models.TextField(help_text="Business plan submitted with application")
    projected_income = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    startup_costs = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Estimated startup costs")
    monthly_expenses = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Projected monthly expenses")

    # Approval process
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_sb_grants')
    review_date = models.DateField(null=True, blank=True)
    review_notes = models.TextField(blank=True)

    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_sb_grants')
    approval_date = models.DateField(null=True, blank=True)

    # Disbursement tracking
    disbursement_date = models.DateField(null=True, blank=True)
    disbursed_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    disbursed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='disbursed_sb_grants')

    # Utilization tracking
    utilization_report = models.TextField(blank=True)
    utilization_date = models.DateField(null=True, blank=True)

    objects = models.Manager()
    upg_objects = UPGGrantManager()

    class Meta:
        verbose_name = "SB Grant (Seed Business)"
        verbose_name_plural = "SB Grants (Seed Business)"
        ordering = ['-created_at']

    def __str__(self):
        applicant_name = self.get_applicant_name()
        return f"SB Grant - {applicant_name} - {self.get_status_display()}"

    def get_applicant_name(self):
        """Get the name of the applicant"""
        if self.business_group:
            return self.business_group.name
        elif self.household:
            return self.household.name
        elif self.savings_group:
            return self.savings_group.name
        return "Unknown Applicant"

    def get_applicant_type(self):
        """Get the type of applicant"""
        if self.business_group:
            return "business_group"
        elif self.household:
            return "household"
        elif self.savings_group:
            return "savings_group"
        return "unknown"

    def calculate_grant_amount(self):
        """Calculate grant amount based on various factors"""
        base_amount = self.base_grant_amount

        # Group size factor (larger groups get more funding)
        group_size = self.business_group.members.count()
        if group_size >= 20:
            self.group_size_factor = Decimal('1.20')  # 20% bonus for large groups
        elif group_size >= 15:
            self.group_size_factor = Decimal('1.10')  # 10% bonus
        elif group_size < 8:
            self.group_size_factor = Decimal('0.90')  # 10% reduction for small groups

        # Business type factor (high-impact businesses get more)
        business_type = getattr(self.business_group, 'business_type', '')
        if business_type in ['agriculture', 'livestock']:
            self.business_type_factor = Decimal('1.15')  # 15% bonus for agriculture
        elif business_type in ['manufacturing', 'processing']:
            self.business_type_factor = Decimal('1.10')  # 10% bonus for manufacturing

        # Location factor (remote areas get more funding)
        location = getattr(self.business_group, 'location', '')
        if 'remote' in location.lower() or 'rural' in location.lower():
            self.location_factor = Decimal('1.05')  # 5% bonus for remote areas

        # Performance factor (based on training completion, group cohesion)
        # This would be calculated based on group's training attendance, savings, etc.
        training_completion_rate = self._get_training_completion_rate()
        if training_completion_rate >= 0.9:
            self.performance_factor = Decimal('1.10')  # 10% bonus for high performers
        elif training_completion_rate < 0.6:
            self.performance_factor = Decimal('0.95')  # 5% reduction for poor performers

        # Calculate final amount
        total_factor = (
            self.group_size_factor *
            self.business_type_factor *
            self.location_factor *
            self.performance_factor
        )

        self.calculated_grant_amount = base_amount * total_factor

        # Apply caps and minimums
        max_grant = Decimal('25000.00')  # Maximum grant
        min_grant = Decimal('10000.00')  # Minimum grant

        if self.calculated_grant_amount > max_grant:
            self.calculated_grant_amount = max_grant
        elif self.calculated_grant_amount < min_grant:
            self.calculated_grant_amount = min_grant

        # Set final amount (can be manually adjusted later)
        if not self.final_grant_amount:
            self.final_grant_amount = self.calculated_grant_amount

        return self.calculated_grant_amount

    def _get_training_completion_rate(self):
        """Calculate training completion rate for the business group"""
        try:
            from training.models import TrainingAttendance
            total_trainings = TrainingAttendance.objects.filter(
                household__business_group_memberships__business_group=self.business_group
            ).count()

            completed_trainings = TrainingAttendance.objects.filter(
                household__business_group_memberships__business_group=self.business_group,
                attendance=True
            ).count()

            if total_trainings > 0:
                return completed_trainings / total_trainings
            return 0.0
        except:
            return 0.8  # Default rate if calculation fails

    def get_grant_amount(self):
        """Get the effective grant amount to use"""
        if self.final_grant_amount:
            return self.final_grant_amount
        elif self.calculated_grant_amount:
            return self.calculated_grant_amount
        else:
            return self.base_grant_amount

    @property
    def remaining_amount(self):
        """Calculate remaining amount to be disbursed"""
        return self.get_grant_amount() - self.disbursed_amount

    @property
    def disbursement_percentage(self):
        """Calculate percentage of grant that has been disbursed"""
        grant_amount = self.get_grant_amount()
        if grant_amount > 0:
            return (self.disbursed_amount / grant_amount) * 100
        return 0

    def can_disburse(self, amount):
        """Check if a specific amount can be disbursed"""
        return (self.disbursed_amount + amount) <= self.get_grant_amount()

    def save(self, *args, **kwargs):
        """Auto-calculate grant amount on save"""
        if not self.calculated_grant_amount:
            self.calculate_grant_amount()
        super().save(*args, **kwargs)

    def clean(self):
        """Validate that this grant is only for UPG programs"""
        # Ensure exactly one applicant type is specified
        applicants = [self.business_group, self.household, self.savings_group]
        applicants_filled = [a for a in applicants if a is not None]

        if len(applicants_filled) == 0:
            raise ValidationError("Must specify either business_group, household, or savings_group")
        if len(applicants_filled) > 1:
            raise ValidationError("Cannot specify multiple applicant types")

        if self.program and not self.program.is_upg_program:
            raise ValidationError("SB Grants are only available for Ultra-Poor Graduation programs")

        # Validate financial calculations
        if self.startup_costs and self.monthly_expenses and self.projected_income:
            if self.startup_costs > self.get_grant_amount() * 2:
                raise ValidationError("Startup costs seem too high relative to grant amount")

            if self.projected_income < self.monthly_expenses:
                raise ValidationError("Projected income should be higher than monthly expenses")

        super().clean()

    @property
    def is_eligible_for_disbursement(self):
        """Check if grant is approved and ready for disbursement"""
        return self.status == 'approved' and self.disbursement_status == 'not_disbursed'

    @property
    def disbursement_percentage(self):
        """Calculate disbursement percentage"""
        if self.grant_amount > 0:
            return (self.disbursed_amount / self.grant_amount) * 100
        return 0


class PRGrant(BaseModel):
    """
    Performance Recognition (PR) Grants - Performance-based grants for business groups
    Only available for UPG programs after SB grant utilization
    """
    GRANT_STATUS_CHOICES = [
        ('not_eligible', 'Not Eligible Yet'),
        ('eligible', 'Eligible'),
        ('pending', 'Pending Application'),
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('disbursed', 'Disbursed'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ]

    PERFORMANCE_CRITERIA_CHOICES = [
        ('excellent', 'Excellent Performance'),
        ('good', 'Good Performance'),
        ('satisfactory', 'Satisfactory Performance'),
        ('poor', 'Poor Performance'),
    ]

    # Core relationships
    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name='pr_grants')
    business_group = models.OneToOneField(BusinessGroup, on_delete=models.CASCADE, related_name='pr_grant', null=True, blank=True,
                                          help_text="For business group applications")
    household = models.ForeignKey('households.Household', on_delete=models.CASCADE, related_name='pr_grants', null=True, blank=True,
                                  help_text="For individual household applications")
    savings_group = models.ForeignKey(BusinessSavingsGroup, on_delete=models.CASCADE, related_name='pr_grants', null=True, blank=True,
                                      help_text="For savings group applications")
    sb_grant = models.OneToOneField(SBGrant, on_delete=models.CASCADE, related_name='pr_grant',
                                   help_text="PR grants are only available after SB grant")

    # Grant details
    grant_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('10000.00'))
    application_date = models.DateField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=GRANT_STATUS_CHOICES, default='not_eligible')

    # Performance assessment
    performance_score = models.IntegerField(null=True, blank=True, help_text="Performance score 0-100")
    performance_rating = models.CharField(max_length=20, choices=PERFORMANCE_CRITERIA_CHOICES, blank=True)
    performance_assessment = models.TextField(blank=True, help_text="Detailed performance assessment")

    # Business metrics (from SB grant period)
    revenue_generated = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    jobs_created = models.PositiveIntegerField(default=0)
    savings_accumulated = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    # Eligibility assessment
    assessed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assessed_pr_grants')
    assessment_date = models.DateField(null=True, blank=True)

    # Approval process
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_pr_grants')
    approval_date = models.DateField(null=True, blank=True)

    # Disbursement
    disbursement_date = models.DateField(null=True, blank=True)
    disbursed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='disbursed_pr_grants')

    objects = models.Manager()
    upg_objects = UPGGrantManager()

    class Meta:
        verbose_name = "PR Grant (Performance Recognition)"
        verbose_name_plural = "PR Grants (Performance Recognition)"
        ordering = ['-created_at']

    def __str__(self):
        applicant_name = self.get_applicant_name()
        return f"PR Grant - {applicant_name} - {self.get_status_display()}"

    def get_applicant_name(self):
        """Get the name of the applicant"""
        if self.business_group:
            return self.business_group.name
        elif self.household:
            return self.household.name
        elif self.savings_group:
            return self.savings_group.name
        return "Unknown Applicant"

    def get_applicant_type(self):
        """Get the type of applicant"""
        if self.business_group:
            return "business_group"
        elif self.household:
            return "household"
        elif self.savings_group:
            return "savings_group"
        return "unknown"

    def clean(self):
        """Validate that this grant is only for UPG programs"""
        # Ensure exactly one applicant type is specified
        applicants = [self.business_group, self.household, self.savings_group]
        applicants_filled = [a for a in applicants if a is not None]

        if len(applicants_filled) == 0:
            raise ValidationError("Must specify either business_group, household, or savings_group")
        if len(applicants_filled) > 1:
            raise ValidationError("Cannot specify multiple applicant types")

        if self.program and not self.program.is_upg_program:
            raise ValidationError("PR Grants are only available for Ultra-Poor Graduation programs")
        super().clean()

    def check_eligibility(self):
        """Check if business group is eligible for PR grant"""
        # Must have completed SB grant successfully
        if not self.sb_grant or self.sb_grant.status != 'disbursed':
            return False, "SB Grant must be successfully disbursed first"

        # Must have good utilization report
        if not self.sb_grant.utilization_report:
            return False, "SB Grant utilization report required"

        # Add more eligibility criteria as needed
        return True, "Eligible for PR Grant"

    @property
    def is_eligible(self):
        """Check if eligible for PR grant"""
        eligible, _ = self.check_eligibility()
        return eligible


class GrantDisbursement(BaseModel):
    """
    Track individual disbursement transactions for grants
    """
    DISBURSEMENT_TYPE_CHOICES = [
        ('sb_grant', 'SB Grant'),
        ('pr_grant', 'PR Grant'),
    ]

    DISBURSEMENT_METHOD_CHOICES = [
        ('bank_transfer', 'Bank Transfer'),
        ('mobile_money', 'Mobile Money'),
        ('cash', 'Cash'),
        ('check', 'Check'),
    ]

    # Grant references (one will be null)
    sb_grant = models.ForeignKey(SBGrant, on_delete=models.CASCADE, null=True, blank=True, related_name='disbursements')
    pr_grant = models.ForeignKey(PRGrant, on_delete=models.CASCADE, null=True, blank=True, related_name='disbursements')

    # Disbursement details
    disbursement_type = models.CharField(max_length=20, choices=DISBURSEMENT_TYPE_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    disbursement_date = models.DateField()
    method = models.CharField(max_length=20, choices=DISBURSEMENT_METHOD_CHOICES, default='bank_transfer')

    # Transaction details
    reference_number = models.CharField(max_length=100, blank=True)
    recipient_name = models.CharField(max_length=100)
    recipient_contact = models.CharField(max_length=50, blank=True)

    # Processing
    processed_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='processed_disbursements')
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-disbursement_date']

    def __str__(self):
        grant_name = self.sb_grant.business_group.name if self.sb_grant else self.pr_grant.business_group.name
        return f"{self.get_disbursement_type_display()} - {grant_name} - {self.amount}"

    def clean(self):
        """Ensure exactly one grant reference is provided"""
        if not (self.sb_grant or self.pr_grant):
            raise ValidationError("Must specify either SB Grant or PR Grant")
        if self.sb_grant and self.pr_grant:
            raise ValidationError("Cannot specify both SB Grant and PR Grant")
        super().clean()