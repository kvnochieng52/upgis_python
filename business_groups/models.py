"""
Business Groups Management Models
"""

from django.db import models
from django.contrib.auth import get_user_model
from households.models import Household
from core.models import Program

User = get_user_model()


class BusinessGroup(models.Model):
    """
    Business Group formed to run business jointly (2-3 entrepreneurs)
    """
    BUSINESS_HEALTH_CHOICES = [
        ('red', 'Red - Poor Performance'),
        ('yellow', 'Yellow - Fair Performance'),
        ('green', 'Green - Good Performance'),
    ]

    PARTICIPATION_STATUS_CHOICES = [
        ('active', 'Active'),
        ('withdrawn', 'Withdrawn'),
        ('suspended', 'Suspended'),
    ]

    BUSINESS_TYPE_CHOICES = [
        ('crop', 'Crop'),
        ('retail', 'Retail'),
        ('service', 'Service'),
        ('livestock', 'Livestock'),
        ('skill', 'Skill'),
    ]

    name = models.CharField(max_length=100)
    program = models.ForeignKey(Program, on_delete=models.CASCADE)
    current_business_health = models.CharField(max_length=10, choices=BUSINESS_HEALTH_CHOICES, default='yellow')
    participation_status = models.CharField(max_length=20, choices=PARTICIPATION_STATUS_CHOICES, default='active')
    group_size = models.IntegerField(default=2)
    business_type = models.CharField(max_length=20, choices=BUSINESS_TYPE_CHOICES)
    business_type_detail = models.CharField(max_length=100, blank=True)  # e.g., cereal, barber shop
    formation_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'upg_business_groups'


class BusinessGroupMember(models.Model):
    """
    Household members of business groups
    """
    ROLE_CHOICES = [
        ('leader', 'Leader'),
        ('treasurer', 'Treasurer'),
        ('secretary', 'Secretary'),
        ('member', 'Member'),
    ]

    business_group = models.ForeignKey(BusinessGroup, on_delete=models.CASCADE, related_name='members')
    household = models.ForeignKey(Household, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member')
    joined_date = models.DateField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.household.name} - {self.business_group.name} ({self.role})"

    class Meta:
        db_table = 'upg_business_group_members'
        unique_together = ['business_group', 'household']


class SBGrant(models.Model):
    """
    SB Grant (Initial Seed Business Grant) awarded to business groups
    """
    FUNDING_STATUS_CHOICES = [
        ('applied', 'Applied'),
        ('approved', 'Approved'),
        ('funded', 'Funded'),
        ('not_funded', 'Not Funded'),
    ]

    business_group = models.ForeignKey(BusinessGroup, on_delete=models.CASCADE, related_name='sb_grants')
    business_type = models.CharField(max_length=20)
    funding_status = models.CharField(max_length=20, choices=FUNDING_STATUS_CHOICES, default='applied')
    funded_date = models.DateField(null=True, blank=True)
    grant_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    leader_name = models.CharField(max_length=100)
    treasurer_name = models.CharField(max_length=100)
    secretary_name = models.CharField(max_length=100)
    business_type_detail = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"SB Grant - {self.business_group.name}"

    class Meta:
        db_table = 'upg_sb_grants'


class PRGrant(models.Model):
    """
    PR Grant (Performance-based second grant) awarded to business groups
    """
    FUNDING_STATUS_CHOICES = [
        ('applied', 'Applied'),
        ('approved', 'Approved'),
        ('funded', 'Funded'),
        ('not_funded', 'Not Funded'),
    ]

    business_group = models.ForeignKey(BusinessGroup, on_delete=models.CASCADE, related_name='pr_grants')
    business_type = models.CharField(max_length=20)
    funding_status = models.CharField(max_length=20, choices=FUNDING_STATUS_CHOICES, default='applied')
    funded_date = models.DateField(null=True, blank=True)
    grant_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    leader_name = models.CharField(max_length=100)
    treasurer_name = models.CharField(max_length=100)
    secretary_name = models.CharField(max_length=100)
    business_type_detail = models.CharField(max_length=100, blank=True)
    why_pr_qualified = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"PR Grant - {self.business_group.name}"

    class Meta:
        db_table = 'upg_pr_grants'


class BusinessProgressSurvey(models.Model):
    """
    Business group progress and performance tracking
    """
    business_group = models.ForeignKey(BusinessGroup, on_delete=models.CASCADE, related_name='progress_surveys')
    survey_date = models.DateField()
    surveyor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    # Financial metrics
    grant_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    grant_used = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    profit = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    business_inputs = models.TextField(blank=True)
    business_inventory = models.TextField(blank=True)
    business_cash = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.business_group.name} - Progress Survey - {self.survey_date}"

    class Meta:
        db_table = 'upg_business_progress_surveys'