"""
Business Savings Groups (BSG) Models
"""

from django.db import models
from django.contrib.auth import get_user_model
from households.models import Household
from business_groups.models import BusinessGroup

User = get_user_model()


class BusinessSavingsGroup(models.Model):
    """
    Community-based savings entity for entrepreneurs
    Can include multiple business groups and individual households
    """
    name = models.CharField(max_length=100)
    business_groups = models.ManyToManyField(BusinessGroup, blank=True, related_name='savings_groups', help_text="Business groups that are part of this savings group")
    members_count = models.IntegerField(default=0)
    target_members = models.IntegerField(default=25, help_text="Target number of members for this savings group")
    savings_to_date = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    formation_date = models.DateField()
    meeting_day = models.CharField(max_length=20, blank=True)
    meeting_location = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    @property
    def total_members(self):
        """Get total count of individual members plus business group members"""
        individual_members = self.bsg_members.filter(is_active=True).count()
        bg_members = sum([bg.member_count for bg in self.business_groups.all()])
        return individual_members + bg_members

    class Meta:
        db_table = 'upg_business_savings_groups'


class BSGMember(models.Model):
    """
    BSG membership tracking
    """
    ROLE_CHOICES = [
        ('chairperson', 'Chairperson'),
        ('secretary', 'Secretary'),
        ('treasurer', 'Treasurer'),
        ('member', 'Member'),
    ]

    bsg = models.ForeignKey(BusinessSavingsGroup, on_delete=models.CASCADE, related_name='bsg_members')
    household = models.ForeignKey(Household, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member')
    joined_date = models.DateField()
    total_savings = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.household.name} - {self.bsg.name}"

    class Meta:
        db_table = 'upg_bsg_members'


class BSGProgressSurvey(models.Model):
    """
    Monthly BSG performance tracking
    """
    bsg = models.ForeignKey(BusinessSavingsGroup, on_delete=models.CASCADE, related_name='progress_surveys')
    survey_date = models.DateField()
    saving_last_month = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    month_recorded = models.DateField()
    attendance_this_meeting = models.IntegerField(default=0)
    surveyor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.bsg.name} - {self.month_recorded}"

    class Meta:
        db_table = 'upg_bsg_progress_surveys'