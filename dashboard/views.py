"""
Dashboard Views for UPG System
"""

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum, Q
from django.utils import timezone
from datetime import timedelta
from households.models import Household, HouseholdProgram
from business_groups.models import BusinessGroup
from upg_grants.models import SBGrant, PRGrant, HouseholdGrantApplication
from savings_groups.models import BusinessSavingsGroup
from training.models import Training, MentoringVisit, PhoneNudge, MentoringReport, HouseholdTrainingEnrollment
from core.models import BusinessMentorCycle


@login_required
def dashboard_view(request):
    """Role-based dashboard routing"""
    user = request.user
    user_role = getattr(user, 'role', None)

    # Route to specific dashboard based on role
    if user.is_superuser or user_role == 'ict_admin':
        return admin_dashboard_view(request)
    elif user_role == 'mentor':
        return mentor_dashboard_view(request)
    elif user_role in ['county_executive', 'county_assembly']:
        return executive_dashboard_view(request)
    elif user_role in ['me_staff', 'cco_director']:
        return me_dashboard_view(request)
    elif user_role == 'field_associate':
        return field_associate_dashboard_view(request)
    else:
        return general_dashboard_view(request)


@login_required
def admin_dashboard_view(request):
    """System Administrator dashboard view"""
    user = request.user

    # Program Overview Statistics
    program_overview = {
        'total_households_enrolled': Household.objects.count(),
        'active_business_groups': BusinessGroup.objects.filter(participation_status='active').count(),
        'graduation_rate': 0,  # Calculate graduation percentage
        'program_completion_status': '65%'  # Example completion
    }

    # Geographic Coverage - Updated to use subcounty_obj
    geographic_coverage = {
        'villages_by_county': Household.objects.values('village__subcounty_obj').distinct().count(),
        'household_distribution': Household.objects.count(),
        'mentor_coverage_map': 'West Pokot Focus',  # Example
        'saturation_levels': '42%'  # Example
    }

    # Financial Metrics - Calculate total disbursed from all grant types
    sb_disbursed = SBGrant.objects.filter(status='disbursed').aggregate(total=Sum('disbursed_amount'))['total'] or 0
    pr_disbursed = PRGrant.objects.filter(status='disbursed').aggregate(total=Sum('grant_amount'))['total'] or 0
    household_disbursed = HouseholdGrantApplication.objects.filter(status='disbursed').aggregate(total=Sum('disbursed_amount'))['total'] or 0

    financial_metrics = {
        'grants_disbursed': sb_disbursed + pr_disbursed + household_disbursed,
        'business_progress': BusinessGroup.objects.filter(participation_status='active').count(),
        'savings_accumulated': BusinessSavingsGroup.objects.filter(is_active=True).count() * 50000,  # Example
        'income_generation': '125%'  # Example increase
    }

    # Training Progress
    training_progress = {
        'modules_completed': 8,  # Example
        'attendance_rates': '89%',
        'skill_development': 'High',
        'mentoring_sessions': 156  # Example
    }

    # Basic statistics for existing cards - Include all grant types
    stats = {
        'total_households': Household.objects.count(),
        'active_households': HouseholdProgram.objects.filter(participation_status='active').count(),
        'graduated_households': HouseholdProgram.objects.filter(participation_status='graduated').count(),
        'total_business_groups': BusinessGroup.objects.count(),
        'active_business_groups': BusinessGroup.objects.filter(participation_status='active').count(),
        'total_savings_groups': BusinessSavingsGroup.objects.filter(is_active=True).count(),
        'sb_grants_funded': SBGrant.objects.filter(status='disbursed').count(),
        'pr_grants_funded': PRGrant.objects.filter(status='disbursed').count(),
        'household_grants_funded': HouseholdGrantApplication.objects.filter(status='disbursed').count(),
        'total_grants_funded': (
            SBGrant.objects.filter(status='disbursed').count() +
            PRGrant.objects.filter(status='disbursed').count() +
            HouseholdGrantApplication.objects.filter(status='disbursed').count()
        ),
    }

    # Role-specific data
    if user.role == 'mentor':
        # Mentor sees only their assigned villages/households
        if hasattr(user, 'profile') and user.profile:
            try:
                assigned_villages = user.profile.assigned_villages
                # Check if it's a QuerySet or Manager
                if hasattr(assigned_villages, 'all'):
                    stats['assigned_villages'] = assigned_villages.count()
                elif assigned_villages is not None:
                    # It's a list or other iterable
                    stats['assigned_villages'] = len(assigned_villages)
                else:
                    stats['assigned_villages'] = 0
            except (AttributeError, TypeError):
                stats['assigned_villages'] = 0
        else:
            stats['assigned_villages'] = 0

    elif user.role in ['county_executive', 'county_assembly']:
        # County-level users see high-level summaries
        pass

    elif user.role in ['me_staff', 'cco_director']:
        # M&E and directors see all data
        pass

    context = {
        'user': user,
        'stats': stats,
        'program_overview': program_overview,
        'geographic_coverage': geographic_coverage,
        'financial_metrics': financial_metrics,
        'training_progress': training_progress,
    }

    return render(request, 'dashboard/admin_dashboard.html', context)


@login_required
def mentor_dashboard_view(request):
    """Mentor-specific dashboard with training assignments"""
    user = request.user

    # Get mentor's assigned trainings
    assigned_trainings = Training.objects.filter(assigned_mentor=user).order_by('-start_date')

    # Get current/active trainings
    current_trainings = assigned_trainings.filter(
        status__in=['planned', 'active'],
        start_date__lte=timezone.now().date(),
        end_date__gte=timezone.now().date()
    )

    # Get households in mentor's assigned villages (more comprehensive)
    if hasattr(user, 'profile') and user.profile:
        try:
            assigned_villages = user.profile.assigned_villages.all()
        except (AttributeError, TypeError):
            # Handle case where assigned_villages might be a list instead of QuerySet
            assigned_villages = getattr(user.profile, 'assigned_villages', [])
            if not hasattr(assigned_villages, 'all'):
                assigned_villages = list(assigned_villages) if assigned_villages else []

        if assigned_villages:
            mentor_households = Household.objects.filter(village__in=assigned_villages).distinct()
        else:
            mentor_households = Household.objects.none()
    else:
        # Fallback to households in mentor's trainings
        mentor_households = Household.objects.filter(
            current_training_enrollment__training__assigned_mentor=user
        ).distinct()

    # Recent mentoring activities (last 30 days)
    thirty_days_ago = timezone.now().date() - timedelta(days=30)
    recent_visits = MentoringVisit.objects.filter(
        mentor=user,
        visit_date__gte=thirty_days_ago
    ).order_by('-visit_date')

    recent_nudges = PhoneNudge.objects.filter(
        mentor=user,
        call_date__gte=thirty_days_ago
    ).order_by('-call_date')

    # Stats for mentor dashboard
    stats = {
        'assigned_trainings': assigned_trainings.count(),
        'active_trainings': current_trainings.count(),
        'total_households': mentor_households.count(),
        'visits_this_month': recent_visits.count(),
        'nudges_this_month': recent_nudges.count(),
        'pending_reports': 0,  # Can be calculated based on reporting schedule
    }

    # Upcoming activities (next 7 days)
    upcoming_trainings = assigned_trainings.filter(
        start_date__gte=timezone.now().date(),
        start_date__lte=timezone.now().date() + timedelta(days=7)
    )

    context = {
        'user': user,
        'stats': stats,
        'assigned_trainings': assigned_trainings[:5],  # Latest 5
        'current_trainings': current_trainings,
        'mentor_households': mentor_households[:10],  # Latest 10
        'recent_visits': recent_visits[:5],
        'recent_nudges': recent_nudges[:5],
        'upcoming_trainings': upcoming_trainings,
        'dashboard_type': 'mentor',
    }

    return render(request, 'dashboard/mentor_dashboard.html', context)


@login_required
def executive_dashboard_view(request):
    """County Executive dashboard with high-level metrics"""
    user = request.user

    # High-level statistics - Include all grant types
    sb_disbursed = SBGrant.objects.filter(status='disbursed').aggregate(total=Sum('disbursed_amount'))['total'] or 0
    pr_disbursed = PRGrant.objects.filter(status='disbursed').aggregate(total=Sum('grant_amount'))['total'] or 0
    household_disbursed = HouseholdGrantApplication.objects.filter(status='disbursed').aggregate(total=Sum('disbursed_amount'))['total'] or 0

    stats = {
        'total_households': Household.objects.count(),
        'active_households': HouseholdProgram.objects.filter(participation_status='active').count(),
        'total_trainings': Training.objects.count(),
        'active_mentors': Training.objects.values('assigned_mentor').distinct().count(),
        'grants_disbursed': sb_disbursed + pr_disbursed + household_disbursed,
        'total_grants_funded': (
            SBGrant.objects.filter(status='disbursed').count() +
            PRGrant.objects.filter(status='disbursed').count() +
            HouseholdGrantApplication.objects.filter(status='disbursed').count()
        ),
    }

    context = {
        'user': user,
        'stats': stats,
        'dashboard_type': 'executive',
    }

    return render(request, 'dashboard/executive_dashboard.html', context)


@login_required
def me_dashboard_view(request):
    """M&E Staff dashboard with monitoring data"""
    user = request.user

    # Monitoring & Evaluation specific metrics
    stats = {
        'total_reports': MentoringReport.objects.count(),
        'pending_reports': MentoringReport.objects.filter(
            submitted_date__gte=timezone.now().date() - timedelta(days=30)
        ).count(),
        'training_completion_rate': 0,  # Calculate based on training completion
        'household_visits': MentoringVisit.objects.filter(
            visit_date__gte=timezone.now().date() - timedelta(days=30)
        ).count(),
    }

    context = {
        'user': user,
        'stats': stats,
        'dashboard_type': 'me',
    }

    return render(request, 'dashboard/me_dashboard.html', context)


@login_required
def field_associate_dashboard_view(request):
    """Field Associate dashboard with mentor oversight"""
    user = request.user

    # Field Associate specific metrics
    stats = {
        'managed_mentors': Training.objects.values('assigned_mentor').distinct().count(),
        'total_trainings': Training.objects.count(),
        'active_trainings': Training.objects.filter(status='active').count(),
        'households_in_training': HouseholdTrainingEnrollment.objects.filter(
            enrollment_status='enrolled'
        ).count(),
    }

    context = {
        'user': user,
        'stats': stats,
        'dashboard_type': 'field_associate',
    }

    return render(request, 'dashboard/field_associate_dashboard.html', context)


@login_required
def general_dashboard_view(request):
    """General dashboard for users without specific roles"""
    user = request.user

    # Basic statistics
    stats = {
        'total_households': Household.objects.count(),
        'total_business_groups': BusinessGroup.objects.count(),
        'total_trainings': Training.objects.count(),
        'system_users': user._meta.model.objects.count(),
    }

    context = {
        'user': user,
        'stats': stats,
        'dashboard_type': 'general',
    }

    return render(request, 'dashboard/general_dashboard.html', context)