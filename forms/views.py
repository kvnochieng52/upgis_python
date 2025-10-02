from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponseForbidden
from django.db import transaction
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
import json

from .models import FormTemplate, FormAssignment, FormSubmission, FormField, FormAssignmentMentor
from core.models import Village
from households.models import Household
from business_groups.models import BusinessGroup

User = get_user_model()

@login_required
def forms_dashboard(request):
    """Main forms dashboard showing different views based on user role"""
    user = request.user
    context = {
        'page_title': 'Dynamic Forms Dashboard',
    }

    if user.role in ['me_staff', 'ict_admin'] or user.is_superuser:
        # M&E staff view - can create and manage forms
        form_templates = FormTemplate.objects.filter(created_by=user)[:5]
        recent_assignments = FormAssignment.objects.filter(assigned_by=user)[:5]
        recent_submissions = FormSubmission.objects.all()[:5]

        context.update({
            'can_create_forms': True,
            'form_templates': form_templates,
            'recent_assignments': recent_assignments,
            'recent_submissions': recent_submissions,
            'total_templates': FormTemplate.objects.filter(created_by=user).count(),
            'active_assignments': FormAssignment.objects.filter(assigned_by=user, status__in=['pending', 'accepted', 'in_progress']).count(),
        })

    elif user.role == 'field_associate':
        # Field associate view - can assign forms to mentors
        assigned_forms = FormAssignment.objects.filter(field_associate=user)
        my_mentor_assignments = FormAssignmentMentor.objects.filter(assigned_by_fa=user)

        context.update({
            'can_assign_to_mentors': True,
            'assigned_forms': assigned_forms,
            'mentor_assignments': my_mentor_assignments,
            'pending_assignments': assigned_forms.filter(status='pending').count(),
        })

    elif user.role == 'mentor':
        # Mentor view - can fill out assigned forms
        my_assignments = FormAssignment.objects.filter(mentor=user)
        my_mentor_assignments = FormAssignmentMentor.objects.filter(mentor=user)
        my_submissions = FormSubmission.objects.filter(submitted_by=user)

        context.update({
            'can_fill_forms': True,
            'my_assignments': my_assignments,
            'my_mentor_assignments': my_mentor_assignments,
            'my_submissions': my_submissions,
            'pending_forms': (my_assignments.filter(status__in=['pending', 'accepted']).count() +
                            my_mentor_assignments.filter(status__in=['pending', 'accepted']).count()),
        })

    return render(request, 'forms/dashboard.html', context)
