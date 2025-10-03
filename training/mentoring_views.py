"""
Mentoring Report Views for UPG System
Comprehensive mentoring activity tracking and reporting
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db.models import Count, Q, Sum, Avg
from django.utils import timezone
from datetime import datetime, timedelta, date
import csv
import json
from django.core.paginator import Paginator

from .models import (
    MentoringReport, MentoringVisit, PhoneNudge, Training,
    TrainingAttendance, HouseholdTrainingEnrollment
)
from core.models import Mentor, BusinessMentorCycle
from households.models import Household, HouseholdProgram
from django.contrib.auth import get_user_model

User = get_user_model()


@login_required
def mentoring_dashboard(request):
    """Comprehensive mentoring activities dashboard"""
    # Check permissions
    user_role = getattr(request.user, 'role', None)
    if not (request.user.is_superuser or user_role in ['ict_admin', 'me_staff', 'field_associate', 'mentor']):
        messages.error(request, 'You do not have permission to access mentoring reports.')
        return redirect('dashboard:dashboard')

    # Filter data based on user role
    if user_role == 'mentor':
        mentor_filter = Q(mentor=request.user)
        # Filter by assigned villages to only show related households
        if hasattr(request.user, 'profile') and request.user.profile:
            assigned_villages = request.user.profile.assigned_villages.all()
            visits = MentoringVisit.objects.filter(
                mentor=request.user,
                household__village__in=assigned_villages
            )
            phone_nudges = PhoneNudge.objects.filter(
                mentor=request.user,
                household__village__in=assigned_villages
            )
            # MentoringReport doesn't have household field - filter by mentor only
            mentoring_reports = MentoringReport.objects.filter(
                mentor=request.user
            )
            # Training doesn't have village field - filter by assigned mentor only
            trainings = Training.objects.filter(
                assigned_mentor=request.user
            )
        else:
            # No profile or assigned villages - show no data
            visits = MentoringVisit.objects.none()
            phone_nudges = PhoneNudge.objects.none()
            mentoring_reports = MentoringReport.objects.filter(mentor=request.user)
            trainings = Training.objects.none()
    else:
        mentor_filter = Q()
        visits = MentoringVisit.objects.all()
        phone_nudges = PhoneNudge.objects.all()
        mentoring_reports = MentoringReport.objects.all()
        trainings = Training.objects.all()

    # Current month statistics
    current_month = timezone.now().replace(day=1)
    next_month = (current_month.replace(day=28) + timedelta(days=4)).replace(day=1)

    monthly_stats = {
        'visits_this_month': visits.filter(visit_date__gte=current_month, visit_date__lt=next_month).count(),
        'phone_nudges_this_month': phone_nudges.filter(call_date__gte=current_month, call_date__lt=next_month).count(),
        'trainings_this_month': trainings.filter(start_date__gte=current_month, start_date__lt=next_month).count(),
        'active_households': visits.filter(visit_date__gte=current_month).values('household').distinct().count(),
    }

    # Recent activities - order by creation time to show most recently logged items
    recent_visits = visits.order_by('-created_at')[:10]
    recent_phone_nudges = phone_nudges.order_by('-created_at')[:10]
    recent_reports = mentoring_reports.order_by('-submitted_date')[:5]

    # Mentor performance overview
    mentor_stats = []
    if user_role != 'mentor':
        mentors = User.objects.filter(role='mentor')
        for mentor in mentors:
            stats = {
                'mentor': mentor,
                'visits_count': MentoringVisit.objects.filter(mentor=mentor, visit_date__gte=current_month).count(),
                'phone_nudges_count': PhoneNudge.objects.filter(mentor=mentor, call_date__gte=current_month).count(),
                'active_households': MentoringVisit.objects.filter(
                    mentor=mentor, visit_date__gte=current_month
                ).values('household').distinct().count(),
                'avg_call_duration': PhoneNudge.objects.filter(
                    mentor=mentor, call_date__gte=current_month
                ).aggregate(avg_duration=Avg('duration_minutes'))['avg_duration'] or 0,
            }
            mentor_stats.append(stats)

    # Visit type distribution
    visit_type_stats = visits.filter(visit_date__gte=current_month).values('visit_type').annotate(
        count=Count('id')
    ).order_by('-count')

    # Phone nudge type distribution
    nudge_type_stats = phone_nudges.filter(call_date__gte=current_month).values('nudge_type').annotate(
        count=Count('id')
    ).order_by('-count')

    # Available grants for mentors to apply on behalf of households
    available_grants = []
    if user_role == 'mentor':
        from programs.models import Program
        from upg_grants.models import HouseholdGrantApplication

        # Get all active programs as available grant opportunities
        active_programs = Program.objects.filter(status='active')

        # Get grant type choices
        grant_types = HouseholdGrantApplication.GRANT_TYPE_CHOICES

        available_grants = {
            'programs': active_programs,
            'grant_types': grant_types,
        }

    context = {
        'page_title': 'Mentoring Dashboard',
        'monthly_stats': monthly_stats,
        'recent_visits': recent_visits,
        'recent_phone_nudges': recent_phone_nudges,
        'recent_reports': recent_reports,
        'mentor_stats': mentor_stats,
        'visit_type_stats': visit_type_stats,
        'nudge_type_stats': nudge_type_stats,
        'user_role': user_role,
        'current_month': current_month.strftime('%B %Y'),
        'available_grants': available_grants,
    }

    return render(request, 'training/mentoring_dashboard.html', context)


@login_required
def mentoring_reports(request):
    """View and manage mentoring reports"""
    # Check permissions
    user_role = getattr(request.user, 'role', None)
    if not (request.user.is_superuser or user_role in ['ict_admin', 'me_staff', 'field_associate', 'mentor']):
        messages.error(request, 'You do not have permission to access mentoring reports.')
        return redirect('dashboard:dashboard')

    # Filter reports based on user role
    if user_role == 'mentor':
        reports = MentoringReport.objects.filter(mentor=request.user)
    else:
        reports = MentoringReport.objects.all()

    # Apply filters
    mentor_filter = request.GET.get('mentor')
    period_filter = request.GET.get('period')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')

    if mentor_filter:
        reports = reports.filter(mentor_id=mentor_filter)
    if period_filter:
        reports = reports.filter(reporting_period=period_filter)
    if date_from:
        reports = reports.filter(period_start__gte=date_from)
    if date_to:
        reports = reports.filter(period_end__lte=date_to)

    reports = reports.order_by('-submitted_date')

    # Pagination
    paginator = Paginator(reports, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Get mentors for filter dropdown (only if not a mentor)
    mentors = []
    if user_role != 'mentor':
        mentors = User.objects.filter(role='mentor').order_by('first_name', 'last_name')

    context = {
        'page_title': 'Mentoring Reports',
        'page_obj': page_obj,
        'mentors': mentors,
        'user_role': user_role,
        'current_filters': {
            'mentor': mentor_filter,
            'period': period_filter,
            'date_from': date_from,
            'date_to': date_to,
        }
    }

    return render(request, 'training/mentoring_reports.html', context)


@login_required
def create_mentoring_report(request):
    """Create a new mentoring report"""
    # Check permissions
    user_role = getattr(request.user, 'role', None)
    if user_role != 'mentor':
        messages.error(request, 'Only mentors can create mentoring reports.')
        return redirect('training:mentoring_reports')

    if request.method == 'POST':
        try:
            # Extract form data
            reporting_period = request.POST.get('reporting_period')
            period_start = request.POST.get('period_start')
            period_end = request.POST.get('period_end')
            key_activities = request.POST.get('key_activities')
            challenges_faced = request.POST.get('challenges_faced', '')
            successes_achieved = request.POST.get('successes_achieved', '')
            next_period_plans = request.POST.get('next_period_plans', '')

            # Convert dates
            period_start = datetime.strptime(period_start, '%Y-%m-%d').date()
            period_end = datetime.strptime(period_end, '%Y-%m-%d').date()

            # Calculate statistics automatically
            visits_count = MentoringVisit.objects.filter(
                mentor=request.user,
                visit_date__gte=period_start,
                visit_date__lte=period_end
            ).count()

            phone_nudges_count = PhoneNudge.objects.filter(
                mentor=request.user,
                call_date__gte=period_start,
                call_date__lte=period_end
            ).count()

            trainings_count = Training.objects.filter(
                assigned_mentor=request.user,
                start_date__gte=period_start,
                start_date__lte=period_end
            ).count()

            households_visited = MentoringVisit.objects.filter(
                mentor=request.user,
                visit_date__gte=period_start,
                visit_date__lte=period_end
            ).values('household').distinct().count()

            # Create the report
            report = MentoringReport.objects.create(
                mentor=request.user,
                reporting_period=reporting_period,
                period_start=period_start,
                period_end=period_end,
                households_visited=households_visited,
                phone_nudges_made=phone_nudges_count,
                trainings_conducted=trainings_count,
                new_households_enrolled=0,  # This would need additional logic
                key_activities=key_activities,
                challenges_faced=challenges_faced,
                successes_achieved=successes_achieved,
                next_period_plans=next_period_plans,
            )

            messages.success(request, 'Mentoring report created successfully.')
            return redirect('training:mentoring_report_detail', report_id=report.id)

        except Exception as e:
            messages.error(request, f'Error creating report: {str(e)}')

    context = {
        'page_title': 'Create Mentoring Report',
        'reporting_periods': MentoringReport.REPORTING_PERIOD_CHOICES,
    }

    return render(request, 'training/create_mentoring_report.html', context)


@login_required
def mentoring_report_detail(request, report_id):
    """View detailed mentoring report"""
    report = get_object_or_404(MentoringReport, id=report_id)

    # Check permissions
    user_role = getattr(request.user, 'role', None)
    if user_role == 'mentor' and report.mentor != request.user:
        messages.error(request, 'You can only view your own reports.')
        return redirect('training:mentoring_reports')

    # Get related activities for the report period
    visits = MentoringVisit.objects.filter(
        mentor=report.mentor,
        visit_date__gte=report.period_start,
        visit_date__lte=report.period_end
    ).order_by('-visit_date')

    phone_nudges = PhoneNudge.objects.filter(
        mentor=report.mentor,
        call_date__gte=report.period_start,
        call_date__lte=report.period_end
    ).order_by('-call_date')

    trainings = Training.objects.filter(
        assigned_mentor=report.mentor,
        start_date__gte=report.period_start,
        start_date__lte=report.period_end
    ).order_by('-start_date')

    context = {
        'page_title': f'Mentoring Report - {report.period_start} to {report.period_end}',
        'report': report,
        'visits': visits,
        'phone_nudges': phone_nudges,
        'trainings': trainings,
    }

    return render(request, 'training/mentoring_report_detail.html', context)


@login_required
def mentoring_analytics(request):
    """Advanced mentoring analytics and insights"""
    # Check permissions
    user_role = getattr(request.user, 'role', None)
    if not (request.user.is_superuser or user_role in ['ict_admin', 'me_staff', 'field_associate']):
        messages.error(request, 'You do not have permission to access mentoring analytics.')
        return redirect('dashboard:dashboard')

    # Time period filter
    days_back = int(request.GET.get('days', 30))
    start_date = timezone.now().date() - timedelta(days=days_back)

    # Overall statistics
    total_mentors = User.objects.filter(role='mentor').count()
    total_visits = MentoringVisit.objects.filter(visit_date__gte=start_date).count()
    total_phone_nudges = PhoneNudge.objects.filter(call_date__gte=start_date).count()
    total_households_reached = MentoringVisit.objects.filter(
        visit_date__gte=start_date
    ).values('household').distinct().count()

    # Mentor performance ranking
    mentor_performance = []
    mentors = User.objects.filter(role='mentor')
    for mentor in mentors:
        visits_count = MentoringVisit.objects.filter(
            mentor=mentor, visit_date__gte=start_date
        ).count()
        nudges_count = PhoneNudge.objects.filter(
            mentor=mentor, call_date__gte=start_date
        ).count()
        households_count = MentoringVisit.objects.filter(
            mentor=mentor, visit_date__gte=start_date
        ).values('household').distinct().count()

        performance_score = (visits_count * 2) + nudges_count + (households_count * 3)

        mentor_performance.append({
            'mentor': mentor,
            'visits': visits_count,
            'nudges': nudges_count,
            'households': households_count,
            'score': performance_score,
        })

    mentor_performance.sort(key=lambda x: x['score'], reverse=True)

    # Monthly trend data
    monthly_data = []
    for i in range(6):  # Last 6 months
        month_start = (timezone.now().replace(day=1) - timedelta(days=30*i)).replace(day=1)
        month_end = (month_start.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)

        visits = MentoringVisit.objects.filter(
            visit_date__gte=month_start, visit_date__lte=month_end
        ).count()
        nudges = PhoneNudge.objects.filter(
            call_date__gte=month_start, call_date__lte=month_end
        ).count()

        monthly_data.append({
            'month': month_start.strftime('%b %Y'),
            'visits': visits,
            'nudges': nudges,
        })

    monthly_data.reverse()

    # Visit type analysis
    visit_types = MentoringVisit.objects.filter(
        visit_date__gte=start_date
    ).values('visit_type').annotate(count=Count('id')).order_by('-count')

    # Average call duration by nudge type
    nudge_duration_stats = PhoneNudge.objects.filter(
        call_date__gte=start_date
    ).values('nudge_type').annotate(
        avg_duration=Avg('duration_minutes'),
        total_calls=Count('id')
    ).order_by('-avg_duration')

    context = {
        'page_title': 'Mentoring Analytics',
        'total_mentors': total_mentors,
        'total_visits': total_visits,
        'total_phone_nudges': total_phone_nudges,
        'total_households_reached': total_households_reached,
        'mentor_performance': mentor_performance[:10],  # Top 10
        'monthly_data': monthly_data,
        'visit_types': visit_types,
        'nudge_duration_stats': nudge_duration_stats,
        'days_back': days_back,
        'start_date': start_date,
    }

    return render(request, 'training/mentoring_analytics.html', context)


@login_required
def export_mentoring_reports(request):
    """Export mentoring reports to CSV"""
    # Check permissions
    user_role = getattr(request.user, 'role', None)
    if not (request.user.is_superuser or user_role in ['ict_admin', 'me_staff', 'field_associate']):
        return HttpResponse('Permission denied', status=403)

    # Filter reports
    reports = MentoringReport.objects.all().order_by('-submitted_date')

    # Apply filters if provided
    mentor_filter = request.GET.get('mentor')
    period_filter = request.GET.get('period')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')

    if mentor_filter:
        reports = reports.filter(mentor_id=mentor_filter)
    if period_filter:
        reports = reports.filter(reporting_period=period_filter)
    if date_from:
        reports = reports.filter(period_start__gte=date_from)
    if date_to:
        reports = reports.filter(period_end__lte=date_to)

    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="mentoring_reports_{timezone.now().strftime("%Y%m%d")}.csv"'

    writer = csv.writer(response)

    # Write header
    writer.writerow([
        'Mentor Name', 'Reporting Period', 'Period Start', 'Period End',
        'Households Visited', 'Phone Nudges Made', 'Trainings Conducted',
        'New Households Enrolled', 'Key Activities', 'Challenges Faced',
        'Successes Achieved', 'Next Period Plans', 'Submitted Date'
    ])

    # Write data rows
    for report in reports:
        writer.writerow([
            report.mentor.get_full_name(),
            report.get_reporting_period_display(),
            report.period_start.strftime('%Y-%m-%d'),
            report.period_end.strftime('%Y-%m-%d'),
            report.households_visited,
            report.phone_nudges_made,
            report.trainings_conducted,
            report.new_households_enrolled,
            report.key_activities,
            report.challenges_faced,
            report.successes_achieved,
            report.next_period_plans,
            report.submitted_date.strftime('%Y-%m-%d %H:%M:%S'),
        ])

    return response


@login_required
def log_visit(request):
    """Log a new mentoring visit"""
    # Check permissions
    user_role = getattr(request.user, 'role', None)
    if user_role not in ['mentor', 'field_associate']:
        messages.error(request, 'Only mentors and field associates can log visits.')
        return redirect('training:mentoring_dashboard')

    if request.method == 'POST':
        try:
            # Extract form data
            household_id = request.POST.get('household')
            name = request.POST.get('name')
            topic = request.POST.get('topic')
            visit_type = request.POST.get('visit_type')
            visit_date = request.POST.get('visit_date')
            notes = request.POST.get('notes', '')

            # Validate household
            household = get_object_or_404(Household, id=household_id)

            # Convert date
            visit_date = datetime.strptime(visit_date, '%Y-%m-%d').date()

            # Create the visit
            visit = MentoringVisit.objects.create(
                name=name,
                household=household,
                mentor=request.user,
                topic=topic,
                visit_type=visit_type,
                visit_date=visit_date,
                notes=notes,
            )

            messages.success(request, f'Visit "{name}" to {household.name} logged successfully on {visit_date}.')
            return redirect('training:mentoring_dashboard')

        except Exception as e:
            messages.error(request, f'Error logging visit: {str(e)}')
            # Continue to render the form with the error message

    # Get households for the mentor (if they have assigned villages)
    households = Household.objects.all().order_by('name')

    # Filter households if mentor has assigned villages
    if hasattr(request.user, 'profile') and request.user.profile:
        assigned_villages = request.user.profile.assigned_villages.all()
        if assigned_villages:
            households = households.filter(village__in=assigned_villages)

    context = {
        'page_title': 'Log Visit',
        'households': households,
        'visit_types': MentoringVisit.VISIT_TYPE_CHOICES,
    }

    return render(request, 'training/log_visit.html', context)


@login_required
def log_phone_nudge(request):
    """Log a new phone nudge"""
    # Check permissions
    user_role = getattr(request.user, 'role', None)
    if user_role not in ['mentor', 'field_associate']:
        messages.error(request, 'Only mentors and field associates can log phone nudges.')
        return redirect('training:mentoring_dashboard')

    if request.method == 'POST':
        try:
            # Extract form data
            household_id = request.POST.get('household')
            nudge_type = request.POST.get('nudge_type')
            call_date = request.POST.get('call_date')
            call_time = request.POST.get('call_time')
            duration_minutes = request.POST.get('duration_minutes')
            duration_seconds = request.POST.get('duration_seconds', '0')  # For auto-tracked duration
            notes = request.POST.get('notes', '')
            successful_contact = request.POST.get('successful_contact') == 'on'

            # Validate household
            household = get_object_or_404(Household, id=household_id)

            # Convert datetime to timezone-aware
            naive_datetime = datetime.strptime(f'{call_date} {call_time}', '%Y-%m-%d %H:%M')
            call_datetime = timezone.make_aware(naive_datetime, timezone.get_current_timezone())

            # Calculate duration in minutes (use seconds if provided)
            if duration_seconds and int(duration_seconds) > 0:
                calculated_duration = int(duration_seconds) // 60
                if calculated_duration == 0 and int(duration_seconds) > 0:
                    calculated_duration = 1  # Minimum 1 minute for calls with duration
            else:
                calculated_duration = int(duration_minutes) if duration_minutes else 0

            # Create the phone nudge
            phone_nudge = PhoneNudge.objects.create(
                household=household,
                mentor=request.user,
                nudge_type=nudge_type,
                call_date=call_datetime,
                duration_minutes=calculated_duration,
                notes=notes,
                successful_contact=successful_contact,
            )

            messages.success(request, f'Phone nudge to {household.name} logged successfully.')
            return redirect('training:mentoring_dashboard')

        except Exception as e:
            messages.error(request, f'Error logging phone nudge: {str(e)}')

    # Get households for the mentor
    households = Household.objects.all().order_by('name')

    # Filter households if mentor has assigned villages
    if hasattr(request.user, 'profile') and request.user.profile:
        assigned_villages = request.user.profile.assigned_villages.all()
        if assigned_villages:
            households = households.filter(village__in=assigned_villages)

    context = {
        'page_title': 'Log Phone Nudge',
        'households': households,
        'nudge_types': PhoneNudge.NUDGE_TYPE_CHOICES,
    }

    return render(request, 'training/log_phone_nudge.html', context)


@login_required
def visit_list(request):
    """View all visits with filtering options"""
    # Check permissions
    user_role = getattr(request.user, 'role', None)
    if not (request.user.is_superuser or user_role in ['ict_admin', 'me_staff', 'field_associate', 'mentor']):
        messages.error(request, 'You do not have permission to view visits.')
        return redirect('dashboard:dashboard')

    # Filter visits based on user role
    if user_role == 'mentor':
        visits = MentoringVisit.objects.filter(mentor=request.user)
    else:
        visits = MentoringVisit.objects.all()

    # Apply filters
    household_filter = request.GET.get('household')
    mentor_filter = request.GET.get('mentor')
    visit_type_filter = request.GET.get('visit_type')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')

    if household_filter:
        visits = visits.filter(household_id=household_filter)
    if mentor_filter:
        visits = visits.filter(mentor_id=mentor_filter)
    if visit_type_filter:
        visits = visits.filter(visit_type=visit_type_filter)
    if date_from:
        visits = visits.filter(visit_date__gte=date_from)
    if date_to:
        visits = visits.filter(visit_date__lte=date_to)

    visits = visits.order_by('-visit_date').select_related('household', 'mentor')

    # Pagination
    paginator = Paginator(visits, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Get filter options
    households = Household.objects.all().order_by('name')
    mentors = []
    if user_role != 'mentor':
        mentors = User.objects.filter(role='mentor').order_by('first_name', 'last_name')

    context = {
        'page_title': 'Mentoring Visits',
        'page_obj': page_obj,
        'households': households,
        'mentors': mentors,
        'visit_types': MentoringVisit.VISIT_TYPE_CHOICES,
        'user_role': user_role,
        'current_filters': {
            'household': household_filter,
            'mentor': mentor_filter,
            'visit_type': visit_type_filter,
            'date_from': date_from,
            'date_to': date_to,
        }
    }

    return render(request, 'training/visit_list.html', context)


@login_required
def phone_nudge_list(request):
    """View all phone nudges with filtering options"""
    # Check permissions
    user_role = getattr(request.user, 'role', None)
    if not (request.user.is_superuser or user_role in ['ict_admin', 'me_staff', 'field_associate', 'mentor']):
        messages.error(request, 'You do not have permission to view phone nudges.')
        return redirect('dashboard:dashboard')

    # Filter phone nudges based on user role
    if user_role == 'mentor':
        phone_nudges = PhoneNudge.objects.filter(mentor=request.user)
    else:
        phone_nudges = PhoneNudge.objects.all()

    # Apply filters
    household_filter = request.GET.get('household')
    mentor_filter = request.GET.get('mentor')
    nudge_type_filter = request.GET.get('nudge_type')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    contact_status = request.GET.get('contact_status')

    if household_filter:
        phone_nudges = phone_nudges.filter(household_id=household_filter)
    if mentor_filter:
        phone_nudges = phone_nudges.filter(mentor_id=mentor_filter)
    if nudge_type_filter:
        phone_nudges = phone_nudges.filter(nudge_type=nudge_type_filter)
    if date_from:
        phone_nudges = phone_nudges.filter(call_date__gte=date_from)
    if date_to:
        phone_nudges = phone_nudges.filter(call_date__lte=date_to)
    if contact_status == 'successful':
        phone_nudges = phone_nudges.filter(successful_contact=True)
    elif contact_status == 'unsuccessful':
        phone_nudges = phone_nudges.filter(successful_contact=False)

    phone_nudges = phone_nudges.order_by('-call_date').select_related('household', 'mentor')

    # Pagination
    paginator = Paginator(phone_nudges, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Get filter options
    households = Household.objects.all().order_by('name')
    mentors = []
    if user_role != 'mentor':
        mentors = User.objects.filter(role='mentor').order_by('first_name', 'last_name')

    # Calculate statistics
    total_calls = phone_nudges.count()
    successful_calls = phone_nudges.filter(successful_contact=True).count()
    avg_duration = phone_nudges.aggregate(avg_duration=Avg('duration_minutes'))['avg_duration'] or 0

    context = {
        'page_title': 'Phone Nudges',
        'page_obj': page_obj,
        'households': households,
        'mentors': mentors,
        'nudge_types': PhoneNudge.NUDGE_TYPE_CHOICES,
        'user_role': user_role,
        'total_calls': total_calls,
        'successful_calls': successful_calls,
        'avg_duration': avg_duration,
        'current_filters': {
            'household': household_filter,
            'mentor': mentor_filter,
            'nudge_type': nudge_type_filter,
            'date_from': date_from,
            'date_to': date_to,
            'contact_status': contact_status,
        }
    }

    return render(request, 'training/phone_nudge_list.html', context)