"""
Household Management Models
Based on Graduation Model Tracking System
"""

from django.db import models
from django.contrib.auth import get_user_model
from core.models import Village, Program, SubCounty, County

User = get_user_model()


class Household(models.Model):
    """
    Household basic information and demographics
    """
    # Geographic/Administrative Information
    village = models.ForeignKey(Village, on_delete=models.CASCADE)
    subcounty = models.ForeignKey(SubCounty, on_delete=models.SET_NULL, null=True, blank=True, related_name='households')
    constituency = models.CharField(max_length=100, blank=True, help_text="Constituency")
    district = models.CharField(max_length=100, blank=True, help_text="District")
    division = models.CharField(max_length=100, blank=True, help_text="Division")
    location_name = models.CharField(max_length=100, blank=True, help_text="Location")
    sub_location = models.CharField(max_length=100, blank=True, help_text="Sub Location")

    # Household Head Information
    head_first_name = models.CharField(max_length=100, blank=True, help_text="First Name of Household Head")
    head_middle_name = models.CharField(max_length=100, blank=True, help_text="Middle Name of Household Head")
    head_last_name = models.CharField(max_length=100, blank=True, help_text="Last Name of Household Head")
    head_gender = models.CharField(max_length=10, choices=[('male', 'Male'), ('female', 'Female')], blank=True)
    head_date_of_birth = models.DateField(null=True, blank=True, help_text="Date of Birth of Household Head")
    head_id_number = models.CharField(max_length=50, blank=True, help_text="ID Number of Household Head")
    head_phone_number = models.CharField(max_length=15, blank=True, help_text="Phone Number of Household Head")

    # Legacy fields (kept for backward compatibility)
    name = models.CharField(max_length=100, help_text="Household name or identifier")
    national_id = models.CharField(max_length=50)
    phone_number = models.CharField(max_length=15)
    disability = models.BooleanField(default=False)
    gps_latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    gps_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    # Additional eligibility fields
    monthly_income = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Monthly household income in KES")
    assets = models.JSONField(default=dict, blank=True, help_text="Household assets as JSON")
    has_electricity = models.BooleanField(default=False, help_text="Household has electricity access")
    has_clean_water = models.BooleanField(default=False, help_text="Household has clean water access")
    location = models.CharField(max_length=200, blank=True, help_text="Location description (rural, urban, remote)")
    consent_given = models.BooleanField(default=False, help_text="Household consent for program participation")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        if self.head_full_name:
            return f"{self.head_full_name} - {self.village}"
        return f"{self.name} - {self.village}"

    @property
    def head_full_name(self):
        """Get full name of household head"""
        parts = [self.head_first_name, self.head_middle_name, self.head_last_name]
        return ' '.join([p for p in parts if p])

    def run_eligibility_assessment(self):
        """Run comprehensive eligibility assessment using EligibilityScorer"""
        from .eligibility import EligibilityScorer
        scorer = EligibilityScorer(self)
        return scorer.calculate_comprehensive_score()

    def run_qualification_assessment(self):
        """Run full qualification assessment using HouseholdQualificationTool"""
        from .eligibility import HouseholdQualificationTool
        tool = HouseholdQualificationTool(self)
        return tool.run_qualification_assessment()

    def is_eligible_for_upg(self):
        """Quick check if household is eligible for UPG program"""
        from .eligibility import quick_eligibility_check
        return quick_eligibility_check(self)

    @property
    def latest_ppi_score(self):
        """Get the most recent PPI score"""
        latest_ppi = self.ppi_scores.order_by('-assessment_date').first()
        return latest_ppi.eligibility_score if latest_ppi else None

    @property
    def head_member(self):
        """Get the household head"""
        return self.members.filter(relationship_to_head='head').first()

    @property
    def total_members(self):
        """Get total number of household members"""
        return self.members.count()

    @property
    def children_under_5_count(self):
        """Count children under 5 years old"""
        return self.members.filter(age__lt=5).count()

    @property
    def working_members_count(self):
        """Count working-age members (16-64)"""
        return self.members.filter(age__gte=16, age__lte=64).count()

    @property
    def disabled_members_count(self):
        """Count disabled household members"""
        return 1 if self.disability else 0

    @property
    def head_gender(self):
        """Get gender of household head"""
        head = self.head_member
        return head.gender if head else ''

    @property
    def head_age(self):
        """Get age of household head"""
        head = self.head_member
        return head.age if head else 0

    @property
    def head_education_level(self):
        """Get education level of household head"""
        head = self.head_member
        return head.education_level if head else 'none'

    @property
    def is_single_parent(self):
        """Check if this is a single parent household"""
        head = self.head_member
        if not head:
            return False
        spouses = self.members.filter(relationship_to_head='spouse').count()
        children = self.members.filter(relationship_to_head='child').count()
        return children > 0 and spouses == 0

    class Meta:
        db_table = 'upg_households'


class PPI(models.Model):
    """
    Poverty Probability Index for household
    """
    household = models.ForeignKey(Household, on_delete=models.CASCADE, related_name='ppi_scores')
    name = models.CharField(max_length=100, blank=True)  # e.g., Baseline PPI, Endline PPI
    eligibility_score = models.IntegerField()  # 0-100
    assessment_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.household.name} - {self.name} - {self.eligibility_score}"

    class Meta:
        db_table = 'upg_ppi'


class HouseholdSurvey(models.Model):
    """
    Household living conditions and assets survey
    """
    SURVEY_TYPE_CHOICES = [
        ('baseline', 'Baseline'),
        ('midline', 'Midline'),
        ('endline', 'Endline'),
    ]

    household = models.ForeignKey(Household, on_delete=models.CASCADE, related_name='surveys')
    survey_type = models.CharField(max_length=20, choices=SURVEY_TYPE_CHOICES)
    name = models.CharField(max_length=100)
    survey_date = models.DateField()
    surveyor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    # Survey data fields (simplified for demo)
    income_level = models.CharField(max_length=50, blank=True)
    assets_owned = models.TextField(blank=True)
    savings_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.household.name} - {self.survey_type} - {self.survey_date}"

    class Meta:
        db_table = 'upg_household_surveys'


class HouseholdMember(models.Model):
    """
    Individual household members
    """
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
    ]

    EDUCATION_CHOICES = [
        ('none', 'None'),
        ('primary', 'Primary'),
        ('secondary', 'Secondary'),
        ('tertiary', 'Tertiary'),
    ]

    RELATIONSHIP_CHOICES = [
        ('head', 'Head'),
        ('spouse', 'Spouse'),
        ('child', 'Child'),
        ('parent', 'Parent'),
        ('sibling', 'Sibling'),
        ('other', 'Other'),
    ]

    household = models.ForeignKey(Household, on_delete=models.CASCADE, related_name='members')
    first_name = models.CharField(max_length=100, blank=True)
    middle_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    name = models.CharField(max_length=100, help_text="Full name (for backward compatibility)")
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    date_of_birth = models.DateField(null=True, blank=True, help_text="Date of Birth")
    age = models.IntegerField(help_text="Age in years")
    id_number = models.CharField(max_length=50, blank=True, help_text="National ID or Birth Certificate Number")
    phone_number = models.CharField(max_length=15, blank=True, help_text="Phone Number")
    relationship_to_head = models.CharField(max_length=20, choices=RELATIONSHIP_CHOICES)
    education_level = models.CharField(max_length=20, choices=EDUCATION_CHOICES, default='none')
    is_program_participant = models.BooleanField(default=False, help_text="Only household head can participate")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.household.name})"

    class Meta:
        db_table = 'upg_household_members'


class HouseholdProgram(models.Model):
    """
    Household participation in UPG programs
    """
    PARTICIPATION_STATUS_CHOICES = [
        ('eligible', 'Eligible'),
        ('enrolled', 'Enrolled'),
        ('active', 'Active'),
        ('graduated', 'Graduated'),
        ('dropped_out', 'Dropped Out'),
    ]

    household = models.ForeignKey(Household, on_delete=models.CASCADE, related_name='program_participations')
    program = models.ForeignKey(Program, on_delete=models.CASCADE)
    mentor = models.ForeignKey('core.Mentor', on_delete=models.SET_NULL, null=True, blank=True)
    participation_status = models.CharField(max_length=20, choices=PARTICIPATION_STATUS_CHOICES, default='eligible')
    enrollment_date = models.DateField(null=True, blank=True)
    graduation_date = models.DateField(null=True, blank=True)
    dropout_date = models.DateField(null=True, blank=True)
    dropout_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.household.name} - {self.program.name}"

    class Meta:
        db_table = 'upg_household_programs'
        unique_together = ['household', 'program']


class UPGMilestone(models.Model):
    """
    UPG 12-month graduation milestones tracking
    Only applicable for graduation programs
    """
    MILESTONE_CHOICES = [
        ('month_1', 'Month 1 - PPI Assessment & Business Training Start'),
        ('month_2', 'Month 2 - Business Group Formation'),
        ('month_3', 'Month 3 - Business Plan Development'),
        ('month_4', 'Month 4 - SB Grant Application'),
        ('month_5', 'Month 5 - SB Grant Disbursement'),
        ('month_6', 'Month 6 - Business Operations Start'),
        ('month_7', 'Month 7 - Mid-term Assessment'),
        ('month_8', 'Month 8 - Business Savings Group Formation'),
        ('month_9', 'Month 9 - PR Grant Eligibility Assessment'),
        ('month_10', 'Month 10 - PR Grant Application'),
        ('month_11', 'Month 11 - Final Business Assessment'),
        ('month_12', 'Month 12 - Graduation Assessment'),
    ]

    STATUS_CHOICES = [
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('delayed', 'Delayed'),
        ('skipped', 'Skipped'),
    ]

    household_program = models.ForeignKey(HouseholdProgram, on_delete=models.CASCADE, related_name='milestones')
    milestone = models.CharField(max_length=20, choices=MILESTONE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='not_started')

    # Tracking
    target_date = models.DateField(null=True, blank=True)
    completion_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    completed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['household_program', 'milestone']
        ordering = ['milestone']

    def __str__(self):
        return f"{self.household_program.household.name} - {self.get_milestone_display()}"

    @property
    def is_overdue(self):
        """Check if milestone is overdue"""
        if self.target_date and self.status not in ['completed', 'skipped']:
            from django.utils import timezone
            return timezone.now().date() > self.target_date
        return False