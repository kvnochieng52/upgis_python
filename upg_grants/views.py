"""
Grant Application and Review Views
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from households.models import Household
from programs.models import Program
from .models import HouseholdGrantApplication, SBGrant, PRGrant
from decimal import Decimal
import json
from itertools import chain
from operator import attrgetter


@login_required
def grant_application_list(request):
    """List all grant applications (Household, SB, PR) with filtering by status and grant type"""
    user = request.user

    # Get Household grants
    if user.role in ['mentor', 'field_associate']:
        household_grants = HouseholdGrantApplication.objects.filter(
            household__village__in=user.profile.assigned_villages.all() if hasattr(user, 'profile') else []
        ).select_related('household', 'household__village', 'program', 'approved_by', 'reviewed_by', 'submitted_by')
    elif user.role in ['program_manager', 'county_director', 'executive', 'ict_admin', 'me_staff'] or user.is_superuser:
        household_grants = HouseholdGrantApplication.objects.all().select_related('household', 'household__village', 'program', 'approved_by', 'reviewed_by', 'submitted_by')
    else:
        household_grants = HouseholdGrantApplication.objects.none()

    # Get SB and PR grants
    if user.role in ['program_manager', 'county_director', 'executive', 'ict_admin', 'me_staff', 'field_associate'] or user.is_superuser:
        sb_grants = SBGrant.objects.all().select_related('business_group', 'program')
        pr_grants = PRGrant.objects.all().select_related('business_group', 'program', 'sb_grant')
    else:
        sb_grants = SBGrant.objects.none()
        pr_grants = PRGrant.objects.none()

    # Apply filters
    status_filter = request.GET.get('status')
    grant_type_filter = request.GET.get('grant_type')

    if status_filter:
        household_grants = household_grants.filter(status=status_filter)
        sb_grants = sb_grants.filter(status=status_filter)
        pr_grants = pr_grants.filter(status=status_filter)

    if grant_type_filter:
        if grant_type_filter == 'sb':
            household_grants = HouseholdGrantApplication.objects.none()
            pr_grants = PRGrant.objects.none()
        elif grant_type_filter == 'pr':
            household_grants = HouseholdGrantApplication.objects.none()
            sb_grants = SBGrant.objects.none()
        else:
            # Household grant type filter
            household_grants = household_grants.filter(grant_type=grant_type_filter)
            sb_grants = SBGrant.objects.none()
            pr_grants = PRGrant.objects.none()

    # Add grant type attribute to each grant for display
    for grant in household_grants:
        grant.display_type = f'Household - {grant.get_grant_type_display()}'
        grant.grant_category = 'household'

    for grant in sb_grants:
        grant.display_type = 'SB Grant'
        grant.grant_category = 'sb'

    for grant in pr_grants:
        grant.display_type = 'PR Grant'
        grant.grant_category = 'pr'

    # Combine all grants and sort by creation date
    all_grants = sorted(
        chain(household_grants, sb_grants, pr_grants),
        key=attrgetter('created_at'),
        reverse=True
    )

    # Determine user permissions
    can_create = user.role in ['mentor', 'field_associate', 'ict_admin', 'me_staff'] or user.is_superuser
    can_review = user.role in ['program_manager', 'county_director', 'executive', 'ict_admin', 'me_staff'] or user.is_superuser
    can_approve = user.role in ['program_manager', 'county_director', 'executive'] or user.is_superuser

    # Create comprehensive grant type choices
    grant_type_choices = [
        ('sb', 'SB Grant'),
        ('pr', 'PR Grant'),
    ] + list(HouseholdGrantApplication.GRANT_TYPE_CHOICES)

    # Get available grants for mentors and field associates
    available_grants = None
    if user.role in ['mentor', 'field_associate']:
        active_programs = Program.objects.filter(status='active')
        available_grants = {
            'programs': active_programs,
            'grant_types': HouseholdGrantApplication.GRANT_TYPE_CHOICES,
        }

    context = {
        'applications': all_grants,
        'page_title': 'All Grant Applications',
        'can_create': can_create,
        'can_review': can_review,
        'can_approve': can_approve,
        'status_filter': status_filter,
        'grant_type_filter': grant_type_filter,
        'status_choices': HouseholdGrantApplication.STATUS_CHOICES,
        'grant_type_choices': grant_type_choices,
        'available_grants': available_grants,
    }
    return render(request, 'upg_grants/application_list.html', context)


@login_required
def grant_application_create(request, household_id=None):
    """Create a new grant application for household, business group, or savings group"""
    user = request.user

    # Check permissions
    if user.role not in ['mentor', 'field_associate', 'ict_admin', 'me_staff']:
        messages.error(request, 'You do not have permission to create grant applications.')
        return redirect('dashboard:dashboard')

    # Handle both URL parameter and GET parameters
    applicant_type = request.GET.get('applicant_type')
    applicant_id = request.GET.get('applicant_id')
    grant_type_param = request.GET.get('grant_type')

    household = None
    business_group = None
    savings_group = None
    applicant_name = ""

    # If called with household_id (old style)
    if household_id:
        household = get_object_or_404(Household, id=household_id)
        applicant_name = household.name
    # New style with GET parameters
    elif applicant_type and applicant_id:
        from business_groups.models import BusinessGroup
        from savings_groups.models import BusinessSavingsGroup

        if applicant_type == 'household':
            household = get_object_or_404(Household, id=applicant_id)
            applicant_name = household.name
        elif applicant_type == 'business_group':
            business_group = get_object_or_404(BusinessGroup, id=applicant_id)
            applicant_name = business_group.name
        elif applicant_type == 'savings_group':
            savings_group = get_object_or_404(BusinessSavingsGroup, id=applicant_id)
            applicant_name = savings_group.name
    # If only grant_type is provided, show household selection page
    elif grant_type_param:
        # Get households for mentor/field associate
        if user.role in ['mentor', 'field_associate'] and hasattr(user, 'profile'):
            households = Household.objects.filter(
                village__in=user.profile.assigned_villages.all()
            ).select_related('village')
        else:
            households = Household.objects.all().select_related('village')

        context = {
            'households': households,
            'grant_type': grant_type_param,
            'page_title': f'Select Household for {dict(HouseholdGrantApplication.GRANT_TYPE_CHOICES).get(grant_type_param, "Grant")} Application',
        }
        return render(request, 'upg_grants/select_household.html', context)
    else:
        messages.error(request, 'No applicant specified.')
        return redirect('grants:grants_dashboard')

    if request.method == 'POST':
        grant_type = request.POST.get('grant_type')
        requested_amount = Decimal(request.POST.get('requested_amount', 0))
        title = request.POST.get('title')
        purpose = request.POST.get('purpose')
        business_plan = request.POST.get('business_plan', '')
        expected_outcomes = request.POST.get('expected_outcomes')
        program_id = request.POST.get('program')

        # Parse budget breakdown from form
        budget_items = request.POST.getlist('budget_item[]')
        budget_amounts = request.POST.getlist('budget_amount[]')
        budget_breakdown = {}
        for item, amount in zip(budget_items, budget_amounts):
            if item and amount:
                budget_breakdown[item] = float(amount)

        # Program is optional
        program = None
        if program_id:
            program = get_object_or_404(Program, id=program_id)

        application = HouseholdGrantApplication.objects.create(
            household=household,
            business_group=business_group,
            savings_group=savings_group,
            submitted_by=user,
            program=program,
            grant_type=grant_type,
            requested_amount=requested_amount,
            title=title,
            purpose=purpose,
            business_plan=business_plan,
            expected_outcomes=expected_outcomes,
            budget_breakdown=budget_breakdown,
            status='submitted',
            submission_date=timezone.now()
        )

        messages.success(request, f'Grant application "{title}" submitted successfully!')
        return redirect('upg_grants:application_detail', application_id=application.id)

    programs = Program.objects.filter(status='active')

    context = {
        'household': household,
        'business_group': business_group,
        'savings_group': savings_group,
        'applicant_name': applicant_name,
        'programs': programs,
        'page_title': f'Apply for Grant - {applicant_name}',
        'preselected_grant_type': grant_type_param,  # Pre-fill grant type from URL
    }
    return render(request, 'upg_grants/application_create.html', context)


@login_required
def grant_application_detail(request, application_id):
    """View details of a grant application"""
    application = get_object_or_404(HouseholdGrantApplication, id=application_id)

    context = {
        'application': application,
        'can_review': application.can_be_reviewed_by(request.user),
        'can_approve': application.can_be_approved_by(request.user),
        'page_title': f'Grant Application - {application.title}',
    }
    return render(request, 'upg_grants/application_detail.html', context)


@login_required
def grant_application_review(request, application_id):
    """Review interface for grant applications"""
    application = get_object_or_404(HouseholdGrantApplication, id=application_id)

    if not application.can_be_reviewed_by(request.user):
        messages.error(request, 'You do not have permission to review this application.')
        return redirect('upg_grants:application_detail', application_id=application_id)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'review':
            application.status = 'under_review'
            application.reviewed_by = request.user
            application.review_date = timezone.now()
            application.review_notes = request.POST.get('review_notes', '')
            application.review_score = int(request.POST.get('review_score', 0)) if request.POST.get('review_score') else None
            application.save()
            messages.success(request, 'Application marked as under review.')

        elif action == 'approve' and application.can_be_approved_by(request.user):
            application.status = 'approved'
            application.approved_by = request.user
            application.approval_date = timezone.now()
            application.approval_notes = request.POST.get('approval_notes', '')
            application.approved_amount = Decimal(request.POST.get('approved_amount', application.requested_amount))
            application.save()
            messages.success(request, 'Application approved successfully!')

        elif action == 'reject' and application.can_be_approved_by(request.user):
            application.status = 'rejected'
            application.approved_by = request.user
            application.approval_date = timezone.now()
            application.approval_notes = request.POST.get('approval_notes', '')
            application.save()
            messages.warning(request, 'Application rejected.')

        return redirect('upg_grants:application_detail', application_id=application_id)

    context = {
        'application': application,
        'can_review': application.can_be_reviewed_by(request.user),
        'can_approve': application.can_be_approved_by(request.user),
        'page_title': f'Review Application - {application.title}',
    }
    return render(request, 'upg_grants/application_review.html', context)


@login_required
def pending_reviews(request):
    """List of applications pending review for managers"""
    user = request.user

    # Allow anyone who can access grants to view pending reviews
    if not (user.is_superuser or user.role in ['program_manager', 'county_director', 'executive', 'ict_admin', 'me_staff', 'field_associate', 'mentor']):
        messages.error(request, 'You do not have permission to view pending grant reviews.')
        return redirect('grants:grants_dashboard')

    pending_applications = HouseholdGrantApplication.objects.filter(
        Q(status='submitted') | Q(status='under_review')
    ).select_related('household', 'program', 'submitted_by', 'reviewed_by').order_by('-submission_date')

    # Determine if user can review applications
    can_review = user.is_superuser or user.role in ['program_manager', 'county_director', 'executive', 'ict_admin', 'me_staff']

    context = {
        'applications': pending_applications,
        'page_title': 'Pending Grant Reviews',
        'can_review': can_review,
    }
    return render(request, 'upg_grants/pending_reviews.html', context)


@login_required
def available_grants_list(request):
    """List all available open grants for application"""
    user = request.user

    # Check permissions - mentors and field associates can apply for grants
    if user.role not in ['mentor', 'field_associate', 'ict_admin', 'me_staff']:
        messages.error(request, 'You do not have permission to view available grants.')
        return redirect('dashboard:dashboard')

    # Get all active programs for grant opportunities
    active_programs = Program.objects.filter(status='active')

    # For household grants, these are always available for application
    grant_types = HouseholdGrantApplication.GRANT_TYPE_CHOICES

    context = {
        'active_programs': active_programs,
        'grant_types': grant_types,
        'page_title': 'Available Grants',
    }
    return render(request, 'upg_grants/available_grants.html', context)
