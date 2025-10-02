"""
Survey and Data Collection Models
"""

from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Survey(models.Model):
    """
    Survey definition and management
    """
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    version = models.CharField(max_length=20, default='1.0')
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} (v{self.version})"

    class Meta:
        db_table = 'upg_surveys'


class SurveyResponse(models.Model):
    """
    Survey responses from field data collection
    """
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE, related_name='responses')
    respondent = models.ForeignKey('households.Household', on_delete=models.CASCADE)
    surveyor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    response_data = models.JSONField()
    completed = models.BooleanField(default=False)
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.survey.name} - {self.respondent.name}"

    class Meta:
        db_table = 'upg_survey_responses'