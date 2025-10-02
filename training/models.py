"""
Training and Mentoring Models
"""

from django.db import models
from django.contrib.auth import get_user_model
from households.models import Household
from core.models import BusinessMentorCycle

User = get_user_model()


class Training(models.Model):
    """
    Training modules and sessions associated with BM Cycles
    """
    TRAINING_STATUS_CHOICES = [
        ('planned', 'Planned'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    name = models.CharField(max_length=100)
    module_id = models.CharField(max_length=50)
    module_number = models.IntegerField(help_text="Sequential module number (1, 2, 3, etc.)", null=True, blank=True)
    bm_cycle = models.ForeignKey(BusinessMentorCycle, on_delete=models.CASCADE, related_name='trainings', null=True, blank=True)
    assigned_mentor = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'mentor'}, null=True, blank=True)

    # Enhanced training details from meeting notes
    duration_hours = models.DecimalField(max_digits=4, decimal_places=1, help_text="Training length in hours", null=True, blank=True)
    location = models.CharField(max_length=200, help_text="Training location/venue", blank=True)
    participant_count = models.IntegerField(help_text="Actual number of participants", null=True, blank=True)

    time_taken = models.DurationField(help_text="Training duration", null=True, blank=True)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=TRAINING_STATUS_CHOICES, default='planned')
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    training_dates = models.JSONField(default=list, blank=True, help_text="List of specific training session dates")
    max_households = models.IntegerField(default=25, help_text="Maximum households per training")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.bm_cycle.bm_cycle_name}"

    @property
    def enrolled_households_count(self):
        return self.attendances.values('household').distinct().count()

    @property
    def available_slots(self):
        return self.max_households - self.enrolled_households_count

    class Meta:
        db_table = 'upg_trainings'


class TrainingAttendance(models.Model):
    """
    Training attendance tracking
    """
    training = models.ForeignKey(Training, on_delete=models.CASCADE, related_name='attendances')
    household = models.ForeignKey(Household, on_delete=models.CASCADE)
    attendance = models.BooleanField(default=True)
    training_date = models.DateField()

    # Track who marked attendance and when
    marked_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name='marked_attendances',
                                 help_text="Mentor who marked this attendance")
    attendance_marked_at = models.DateTimeField(null=True, blank=True,
                                              help_text="When attendance was last updated")

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.household.name} - {self.training.name}"

    class Meta:
        db_table = 'upg_training_attendances'


class MentoringVisit(models.Model):
    """
    Mentoring visit tracking
    """
    VISIT_TYPE_CHOICES = [
        ('on_site', 'On-site'),
        ('phone', 'Phone Check'),
        ('virtual', 'Virtual'),
    ]

    name = models.CharField(max_length=100)
    household = models.ForeignKey(Household, on_delete=models.CASCADE, related_name='mentoring_visits')
    mentor = models.ForeignKey(User, on_delete=models.CASCADE)
    topic = models.CharField(max_length=200)
    visit_type = models.CharField(max_length=20, choices=VISIT_TYPE_CHOICES, default='on_site')
    visit_date = models.DateField()
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.household.name}"

    class Meta:
        db_table = 'upg_mentoring_visits'


class PhoneNudge(models.Model):
    """
    Phone nudges/calls made by mentors to households
    """
    NUDGE_TYPE_CHOICES = [
        ('reminder', 'Training Reminder'),
        ('follow_up', 'Follow-up Call'),
        ('support', 'Support Call'),
        ('check_in', 'Regular Check-in'),
        ('business_advice', 'Business Advice'),
    ]

    household = models.ForeignKey(Household, on_delete=models.CASCADE, related_name='phone_nudges')
    mentor = models.ForeignKey(User, on_delete=models.CASCADE)
    nudge_type = models.CharField(max_length=20, choices=NUDGE_TYPE_CHOICES)
    call_date = models.DateTimeField()
    duration_minutes = models.IntegerField(help_text="Call duration in minutes")
    notes = models.TextField(blank=True)
    successful_contact = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_nudge_type_display()} - {self.household.name}"

    class Meta:
        db_table = 'upg_phone_nudges'


class MentoringReport(models.Model):
    """
    Weekly/Monthly mentoring reports by mentors
    """
    REPORTING_PERIOD_CHOICES = [
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
    ]

    mentor = models.ForeignKey(User, on_delete=models.CASCADE)
    reporting_period = models.CharField(max_length=20, choices=REPORTING_PERIOD_CHOICES)
    period_start = models.DateField()
    period_end = models.DateField()

    # Summary statistics
    households_visited = models.IntegerField(default=0)
    phone_nudges_made = models.IntegerField(default=0)
    trainings_conducted = models.IntegerField(default=0)
    new_households_enrolled = models.IntegerField(default=0)

    # Narrative report
    key_activities = models.TextField(help_text="Key activities during the period")
    challenges_faced = models.TextField(blank=True)
    successes_achieved = models.TextField(blank=True)
    next_period_plans = models.TextField(blank=True)

    submitted_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.mentor.get_full_name()} - {self.reporting_period} - {self.period_start}"

    class Meta:
        db_table = 'upg_mentoring_reports'
        unique_together = ['mentor', 'reporting_period', 'period_start']


class HouseholdTrainingEnrollment(models.Model):
    """
    Tracks household enrollment in trainings (one household per training rule)
    """
    household = models.OneToOneField(Household, on_delete=models.CASCADE, related_name='current_training_enrollment')
    training = models.ForeignKey(Training, on_delete=models.CASCADE, related_name='enrolled_households')
    enrolled_date = models.DateField()
    enrollment_status = models.CharField(
        max_length=20,
        choices=[
            ('enrolled', 'Enrolled'),
            ('completed', 'Completed'),
            ('dropped_out', 'Dropped Out'),
            ('transferred', 'Transferred'),
        ],
        default='enrolled'
    )
    completion_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.household.name} - {self.training.name}"

    class Meta:
        db_table = 'upg_household_training_enrollments'