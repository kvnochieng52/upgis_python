"""
Reports and Analytics Models
"""

from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Report(models.Model):
    """
    Report definitions and configurations
    """
    REPORT_TYPE_CHOICES = [
        ('dashboard', 'Dashboard'),
        ('tabular', 'Tabular Report'),
        ('chart', 'Chart/Graph'),
        ('custom', 'Custom Report'),
    ]

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    report_type = models.CharField(max_length=20, choices=REPORT_TYPE_CHOICES, default='tabular')
    configuration = models.JSONField(blank=True, default=dict)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'upg_reports'