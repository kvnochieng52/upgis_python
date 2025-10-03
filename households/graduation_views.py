"""
Graduation Tracking Views for UPG System
Comprehensive milestone and graduation management
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db.models import Count, Q, F
from django.utils import timezone
from datetime import datetime, timedelta
import csv
import json
from .models import Household, HouseholdProgram, UPGMilestone
from programs.models import Program


@login_required
def graduation_dashboard(request):
    """Comprehensive graduation tracking dashboard"""
    # Check permissions
    user_role = getattr(request.user, 'role', None)
    if not (request.user.is_superuser or user_role in ['ict_admin', 'me_staff', 'field_associate', 'mentor']):
        messages.error(request, 'You do not have permission to access graduation tracking.')
        return redirect('dashboard:dashboard')

    # Filter for UPG programs only
    upg_programs = Program.objects.filter(program_type='graduation')

    # Get household programs for UPG programs
    household_programs = HouseholdProgram.objects.filter(
        program__program_type='graduation'
    ).select_related('household', 'program')

    # Apply role-based filtering
    if user_role == 'mentor':
        if hasattr(request.user, 'profile') and request.user.profile:
            assigned_villages = request.user.profile.assigned_villages.all()
            household_programs = household_programs.filter(household__village__in=assigned_villages)
    elif user_role == 'field_associate':
        if hasattr(request.user, 'profile') and request.user.profile:
            assigned_villages = request.user.profile.assigned_villages.all()
            household_programs = household_programs.filter(household__village__in=assigned_villages)

    # Graduation statistics
    total_participants = household_programs.count()

    # Calculate progress based on milestones
    milestones_stats = UPGMilestone.objects.filter(
        household_program__in=household_programs
    ).aggregate(
        total_milestones=Count('id'),
        completed_milestones=Count('id', filter=Q(status='completed')),
        overdue_milestones=Count('id', filter=Q(
            status__in=['not_started', 'in_progress'],
            target_date__lt=timezone.now().date()
        )),
        in_progress=Count('id', filter=Q(status='in_progress'))
    )

    # Calculate graduation progress
    households_by_progress = {}
    for hp in household_programs:
        completed_count = hp.milestones.filter(status='completed').count()
        progress_percentage = (completed_count / 12) * 100 if completed_count > 0 else 0

        if progress_percentage == 100:
            category = 'graduated'
        elif progress_percentage >= 75:
            category = 'near_graduation'
        elif progress_percentage >= 50:
            category = 'mid_program'
        elif progress_percentage >= 25:
            category = 'early_stage'
        else:
            category = 'just_started'

        households_by_progress.setdefault(category, 0)
        households_by_progress[category] += 1

    # Recent milestone updates
    recent_milestones = UPGMilestone.objects.filter(
        household_program__in=household_programs,
        updated_at__gte=timezone.now() - timedelta(days=7)
    ).select_related('household_program__household').order_by('-updated_at')[:10]

    # Overdue milestones
    overdue_milestones = UPGMilestone.objects.filter(
        household_program__in=household_programs,
        status__in=['not_started', 'in_progress'],
        target_date__lt=timezone.now().date()
    ).select_related('household_program__household').order_by('target_date')[:10]

    # Monthly progress data for charts
    monthly_data = []
    for i in range(12):
        month_milestones = UPGMilestone.objects.filter(
            household_program__in=household_programs,
            milestone=f'month_{i+1}'
        ).aggregate(
            total=Count('id'),
            completed=Count('id', filter=Q(status='completed')),
            in_progress=Count('id', filter=Q(status='in_progress')),
            overdue=Count('id', filter=Q(
                status__in=['not_started', 'in_progress'],
                target_date__lt=timezone.now().date()
            ))
        )
        monthly_data.append({
            'month': i + 1,
            'total': month_milestones['total'],
            'completed': month_milestones['completed'],
            'in_progress': month_milestones['in_progress'],
            'overdue': month_milestones['overdue'],
            'completion_rate': (month_milestones['completed'] / month_milestones['total'] * 100) if month_milestones['total'] > 0 else 0
        })

    context = {
        'page_title': 'Graduation Tracking Dashboard',
        'total_participants': total_participants,
        'milestones_stats': milestones_stats,
        'households_by_progress': households_by_progress,
        'recent_milestones': recent_milestones,
        'overdue_milestones': overdue_milestones,
        'monthly_data': monthly_data,
        'upg_programs': upg_programs,
    }

    return render(request, 'households/graduation_dashboard.html', context)


@login_required
def household_milestones(request, household_id):
    """View and manage milestones for a specific household"""
    household = get_object_or_404(Household, id=household_id)

    # Check permissions
    user_role = getattr(request.user, 'role', None)
    if not (request.user.is_superuser or user_role in ['ict_admin', 'me_staff', 'field_associate', 'mentor']):
        messages.error(request, 'You do not have permission to view household milestones.')
        return redirect('households:household_detail', pk=household_id)

    # Get UPG program enrollment
    try:
        household_program = HouseholdProgram.objects.get(
            household=household,
            program__program_type='graduation'
        )
    except HouseholdProgram.DoesNotExist:
        messages.error(request, 'This household is not enrolled in a UPG program.')
        return redirect('households:household_detail', pk=household_id)

    # Get or create milestones
    milestones = []
    for milestone_choice in UPGMilestone.MILESTONE_CHOICES:
        milestone_key = milestone_choice[0]
        milestone_display = milestone_choice[1]

        milestone, created = UPGMilestone.objects.get_or_create(
            household_program=household_program,
            milestone=milestone_key,
            defaults={
                'status': 'not_started',
                'target_date': None,
            }
        )
        milestones.append(milestone)

    # Calculate progress
    completed_count = sum(1 for m in milestones if m.status == 'completed')
    progress_percentage = (completed_count / len(milestones)) * 100

    context = {
        'page_title': f'Graduation Milestones - {household.name}',
        'household': household,
        'household_program': household_program,
        'milestones': milestones,
        'completed_count': completed_count,
        'total_milestones': len(milestones),
        'progress_percentage': progress_percentage,
    }

    return render(request, 'households/household_milestones.html', context)


@login_required
def update_milestone(request, milestone_id):
    """Update milestone status and details"""
    milestone = get_object_or_404(UPGMilestone, id=milestone_id)

    # Check permissions
    user_role = getattr(request.user, 'role', None)
    if not (request.user.is_superuser or user_role in ['ict_admin', 'me_staff', 'field_associate', 'mentor']):
        return JsonResponse({'success': False, 'message': 'Permission denied'})

    if request.method == 'POST':
        status = request.POST.get('status')
        notes = request.POST.get('notes', '')
        target_date = request.POST.get('target_date')

        if status in dict(UPGMilestone.STATUS_CHOICES):
            milestone.status = status
            milestone.notes = notes
            milestone.completed_by = request.user if status == 'completed' else None

            if status == 'completed' and not milestone.completion_date:
                milestone.completion_date = timezone.now().date()
            elif status != 'completed':
                milestone.completion_date = None

            if target_date:
                try:
                    milestone.target_date = datetime.strptime(target_date, '%Y-%m-%d').date()
                except ValueError:
                    pass

            milestone.save()

            return JsonResponse({
                'success': True,
                'message': f'Milestone updated successfully',
                'status': milestone.get_status_display(),
                'completion_date': milestone.completion_date.strftime('%Y-%m-%d') if milestone.completion_date else None
            })
        else:
            return JsonResponse({'success': False, 'message': 'Invalid status'})

    return JsonResponse({'success': False, 'message': 'Invalid request method'})


@login_required
def graduation_reports(request):
    """Generate graduation progress reports"""
    # Check permissions
    user_role = getattr(request.user, 'role', None)
    if not (request.user.is_superuser or user_role in ['ict_admin', 'me_staff', 'field_associate']):
        messages.error(request, 'You do not have permission to access graduation reports.')
        return redirect('dashboard:dashboard')

    # Get UPG programs
    upg_programs = Program.objects.filter(program_type='graduation')

    # Detailed analytics
    program_analytics = []
    for program in upg_programs:
        household_programs = HouseholdProgram.objects.filter(program=program)
        total_households = household_programs.count()

        if total_households > 0:
            milestones = UPGMilestone.objects.filter(household_program__in=household_programs)

            analytics = {
                'program': program,
                'total_households': total_households,
                'total_milestones': milestones.count(),
                'completed_milestones': milestones.filter(status='completed').count(),
                'overdue_milestones': milestones.filter(
                    status__in=['not_started', 'in_progress'],
                    target_date__lt=timezone.now().date()
                ).count(),
                'graduation_rate': 0,
                'average_progress': 0,
            }

            # Calculate graduation rate and average progress
            graduated_count = 0
            total_progress = 0

            for hp in household_programs:
                completed = hp.milestones.filter(status='completed').count()
                progress = (completed / 12) * 100
                total_progress += progress

                if completed == 12:
                    graduated_count += 1

            analytics['graduation_rate'] = (graduated_count / total_households) * 100
            analytics['average_progress'] = total_progress / total_households
            analytics['remaining_milestones'] = analytics['total_milestones'] - analytics['completed_milestones'] - analytics['overdue_milestones']

            program_analytics.append(analytics)

    # Calculate overall statistics
    total_participants = sum(analytics['total_households'] for analytics in program_analytics)
    overall_graduation_rate = sum(analytics['graduation_rate'] for analytics in program_analytics) / len(program_analytics) if program_analytics else 0

    context = {
        'page_title': 'Graduation Reports',
        'program_analytics': program_analytics,
        'total_participants': total_participants,
        'overall_graduation_rate': overall_graduation_rate,
    }

    return render(request, 'households/graduation_reports.html', context)


@login_required
def export_graduation_reports(request):
    """Export graduation reports in Excel or CSV format"""
    # Check permissions
    user_role = getattr(request.user, 'role', None)
    if not (request.user.is_superuser or user_role in ['ict_admin', 'me_staff', 'field_associate']):
        return HttpResponse('Permission denied', status=403)

    export_format = request.GET.get('format', 'excel')

    # Get UPG programs
    upg_programs = Program.objects.filter(program_type='graduation')

    # Prepare data
    data = []
    for program in upg_programs:
        household_programs = HouseholdProgram.objects.filter(program=program)
        total_households = household_programs.count()

        if total_households > 0:
            milestones = UPGMilestone.objects.filter(household_program__in=household_programs)

            # Calculate graduation rate
            graduated_count = 0
            for hp in household_programs:
                completed = hp.milestones.filter(status='completed').count()
                if completed == 12:
                    graduated_count += 1

            graduation_rate = (graduated_count / total_households) * 100

            data.append({
                'Program': program.name,
                'Total Households': total_households,
                'Total Milestones': milestones.count(),
                'Completed Milestones': milestones.filter(status='completed').count(),
                'Overdue Milestones': milestones.filter(
                    status__in=['not_started', 'in_progress'],
                    target_date__lt=timezone.now().date()
                ).count(),
                'Graduation Rate (%)': round(graduation_rate, 1),
                'Budget (KES)': program.budget,
                'Start Date': program.start_date.strftime('%Y-%m-%d') if program.start_date else '',
                'Duration (months)': program.duration_months,
            })

    if export_format == 'excel':
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename="graduation_reports_{timezone.now().strftime("%Y%m%d")}.xlsx"'

        # Note: For production, install openpyxl and implement Excel export
        # For now, return CSV format
        export_format = 'csv'

    if export_format == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="graduation_reports_{timezone.now().strftime("%Y%m%d")}.csv"'

        writer = csv.DictWriter(response, fieldnames=[
            'Program', 'Total Households', 'Total Milestones', 'Completed Milestones',
            'Overdue Milestones', 'Graduation Rate (%)', 'Budget (KES)', 'Start Date', 'Duration (months)'
        ])

        writer.writeheader()
        for row in data:
            writer.writerow(row)

        return response

    return HttpResponse('Invalid format', status=400)