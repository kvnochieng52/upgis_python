"""
Dynamic Forms System for UPG Management
Allows M&E staff to create editable forms/surveys and assign them to field associates/mentors
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
import json

User = get_user_model()


class FormTemplate(models.Model):
    """
    Dynamic form template created by M&E staff
    """
    FORM_TYPE_CHOICES = [
        ('household_survey', 'Household Survey'),
        ('business_survey', 'Business Progress Survey'),
        ('ppi_assessment', 'PPI Assessment'),
        ('baseline_survey', 'Baseline Survey'),
        ('midline_survey', 'Midline Survey'),
        ('endline_survey', 'Endline Survey'),
        ('training_evaluation', 'Training Evaluation'),
        ('mentoring_report', 'Mentoring Report'),
        ('custom_form', 'Custom Form'),
    ]

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('archived', 'Archived'),
    ]

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    form_type = models.CharField(max_length=30, choices=FORM_TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')

    # Form structure stored as JSON
    form_fields = models.JSONField(default=list, help_text="JSON structure defining form fields")

    # Assignment and workflow
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_forms')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Form settings
    allow_multiple_submissions = models.BooleanField(default=False)
    require_photo_evidence = models.BooleanField(default=False)
    require_gps_location = models.BooleanField(default=False)
    auto_assign_to_mentors = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} ({self.get_form_type_display()})"

    class Meta:
        db_table = 'upg_form_templates'
        ordering = ['-created_at']


class FormAssignment(models.Model):
    """
    Assignment of forms to field associates or mentors
    """
    ASSIGNMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled'),
    ]

    ASSIGNMENT_TYPE_CHOICES = [
        ('direct_to_mentor', 'Direct to Mentor'),
        ('via_field_associate', 'Via Field Associate'),
    ]

    form_template = models.ForeignKey(FormTemplate, on_delete=models.CASCADE, related_name='assignments')
    assigned_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='form_assignments_made')

    # Assignment can be to field associate who then assigns to mentors, or directly to mentor
    assignment_type = models.CharField(max_length=30, choices=ASSIGNMENT_TYPE_CHOICES)
    field_associate = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True,
                                       related_name='assigned_forms',
                                       limit_choices_to={'role': 'field_associate'})
    mentor = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True,
                              related_name='assigned_forms_mentor',
                              limit_choices_to={'role': 'mentor'})

    # Assignment details
    title = models.CharField(max_length=200)
    instructions = models.TextField(blank=True)
    due_date = models.DateTimeField(null=True, blank=True)
    priority = models.CharField(max_length=20, choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ], default='medium')

    # Status tracking
    status = models.CharField(max_length=20, choices=ASSIGNMENT_STATUS_CHOICES, default='pending')
    assigned_at = models.DateTimeField(auto_now_add=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    # Target criteria (optional filters for which households/groups to survey)
    target_villages = models.JSONField(default=list, blank=True)
    target_households = models.JSONField(default=list, blank=True)
    target_business_groups = models.JSONField(default=list, blank=True)
    min_submissions_required = models.IntegerField(default=1)

    def __str__(self):
        assignee = self.mentor or self.field_associate
        return f"{self.title} -> {assignee.get_full_name() if assignee else 'Unassigned'}"

    def clean(self):
        if self.assignment_type == 'direct_to_mentor' and not self.mentor:
            raise ValidationError("Mentor is required for direct assignments")
        if self.assignment_type == 'via_field_associate' and not self.field_associate:
            raise ValidationError("Field associate is required for field associate assignments")

    class Meta:
        db_table = 'upg_form_assignments'
        ordering = ['-assigned_at']


class FormSubmission(models.Model):
    """
    Individual form submissions by mentors
    """
    SUBMISSION_STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('reviewed', 'Reviewed'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    assignment = models.ForeignKey(FormAssignment, on_delete=models.CASCADE, related_name='submissions')
    form_template = models.ForeignKey(FormTemplate, on_delete=models.CASCADE)

    # Submitter details
    submitted_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='form_submissions')
    submission_date = models.DateTimeField(auto_now_add=True)

    # Form data stored as JSON
    form_data = models.JSONField(default=dict)

    # Optional attachments
    photo_evidence = models.ImageField(upload_to='form_submissions/photos/', null=True, blank=True)
    document_attachment = models.FileField(upload_to='form_submissions/docs/', null=True, blank=True)

    # Location data
    gps_latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    gps_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    location_name = models.CharField(max_length=200, blank=True)

    # Review and approval
    status = models.CharField(max_length=20, choices=SUBMISSION_STATUS_CHOICES, default='draft')
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='reviewed_submissions')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_notes = models.TextField(blank=True)

    # Related entities (optional)
    household = models.ForeignKey('households.Household', on_delete=models.SET_NULL, null=True, blank=True)
    business_group = models.ForeignKey('business_groups.BusinessGroup', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.form_template.name} - {self.submitted_by.get_full_name()} - {self.submission_date.strftime('%Y-%m-%d')}"

    class Meta:
        db_table = 'upg_form_submissions'
        ordering = ['-submission_date']


class FormField(models.Model):
    """
    Individual form field definition for building dynamic forms
    """
    FIELD_TYPE_CHOICES = [
        ('text', 'Text Input'),
        ('textarea', 'Text Area'),
        ('number', 'Number Input'),
        ('email', 'Email Input'),
        ('phone', 'Phone Number'),
        ('date', 'Date Picker'),
        ('datetime', 'Date & Time'),
        ('select', 'Dropdown Select'),
        ('radio', 'Radio Buttons'),
        ('checkbox', 'Checkboxes'),
        ('boolean', 'Yes/No'),
        ('file', 'File Upload'),
        ('image', 'Image Upload'),
        ('rating', 'Rating Scale'),
        ('location', 'GPS Location'),
        ('signature', 'Digital Signature'),
    ]

    form_template = models.ForeignKey(FormTemplate, on_delete=models.CASCADE, related_name='fields')
    field_name = models.CharField(max_length=100)
    field_label = models.CharField(max_length=200)
    field_type = models.CharField(max_length=20, choices=FIELD_TYPE_CHOICES)

    # Field configuration
    required = models.BooleanField(default=False)
    help_text = models.CharField(max_length=500, blank=True)
    placeholder = models.CharField(max_length=200, blank=True)
    default_value = models.CharField(max_length=500, blank=True)

    # For select, radio, checkbox fields
    choices = models.JSONField(default=list, blank=True, help_text="List of choices for select/radio/checkbox fields")

    # Field validation
    min_length = models.IntegerField(null=True, blank=True)
    max_length = models.IntegerField(null=True, blank=True)
    min_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    max_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    validation_regex = models.CharField(max_length=500, blank=True)

    # Display order
    order = models.IntegerField(default=0)

    # Conditional display
    show_if_field = models.CharField(max_length=100, blank=True, help_text="Show this field only if another field has specific value")
    show_if_value = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return f"{self.form_template.name} - {self.field_label}"

    class Meta:
        db_table = 'upg_form_fields'
        ordering = ['order', 'id']


class FormAssignmentMentor(models.Model):
    """
    Many-to-many relationship for field associates assigning forms to multiple mentors
    """
    assignment = models.ForeignKey(FormAssignment, on_delete=models.CASCADE, related_name='mentor_assignments')
    mentor = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'mentor'})
    assigned_by_fa = models.ForeignKey(User, on_delete=models.CASCADE, related_name='fa_mentor_assignments')
    assigned_at = models.DateTimeField(auto_now_add=True)
    instructions = models.TextField(blank=True)
    due_date = models.DateTimeField(null=True, blank=True)

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('overdue', 'Overdue'),
    ]

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    def __str__(self):
        return f"{self.assignment.title} -> {self.mentor.get_full_name()}"

    class Meta:
        db_table = 'upg_form_assignment_mentors'
        unique_together = ['assignment', 'mentor']
