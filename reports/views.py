from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.db.models import Count, Q
from django.utils import timezone
from households.models import Household, HouseholdProgram, HouseholdMember, PPI
from business_groups.models import BusinessGroup, BusinessGroupMember
from upg_grants.models import SBGrant, PRGrant
from savings_groups.models import BusinessSavingsGroup, BSGMember
from training.models import Training, HouseholdTrainingEnrollment, MentoringVisit, PhoneNudge
import csv

@login_required
def report_list(request):
    """Reports dashboard view"""
    user = request.user

    # Generate some basic statistics for reports
    reports_data = {
        'total_households': Household.objects.count(),
        'active_programs': HouseholdProgram.objects.filter(participation_status='active').count(),
        'graduated_programs': HouseholdProgram.objects.filter(participation_status='graduated').count(),
        'total_business_groups': BusinessGroup.objects.count(),
    }

    # Mentor logs statistics - visible to M&E, Admin, Field Associates
    mentor_logs_visible = user.is_superuser or user.role in ['me_staff', 'ict_admin', 'field_associate', 'mentor']
    if mentor_logs_visible:
        from datetime import timedelta
        thirty_days_ago = timezone.now().date() - timedelta(days=30)

        reports_data['total_house_visits'] = MentoringVisit.objects.count()
        reports_data['total_phone_calls'] = PhoneNudge.objects.count()
        reports_data['recent_house_visits'] = MentoringVisit.objects.filter(visit_date__gte=thirty_days_ago).count()
        reports_data['recent_phone_calls'] = PhoneNudge.objects.filter(call_date__gte=thirty_days_ago).count()

    context = {
        'reports_data': reports_data,
        'mentor_logs_visible': mentor_logs_visible,
        'page_title': 'Reports & Analytics',
    }

    return render(request, 'reports/report_list.html', context)

@login_required
def download_household_report(request):
    """Download household registration report as CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="household_report_{timezone.now().strftime("%Y%m%d")}.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'Household Name', 'Head of Household', 'Village', 'Parish', 'Subcounty', 'County',
        'Members Count', 'Total Members', 'Program Participants', 'Phone Number', 'Registration Date'
    ])

    for household in Household.objects.select_related('village').prefetch_related('members'):
        program_participants = household.members.filter(is_program_participant=True).count()
        head_of_household = household.members.filter(relationship_to_head='head').first()
        head_name = head_of_household.name if head_of_household else 'Not specified'

        writer.writerow([
            household.name,
            head_name,
            household.village.name if household.village else '',
            '',  # parish not available in current model
            household.village.subcounty if household.village else '',
            household.village.country if household.village else '',  # Country field exists
            getattr(household, 'members_count', household.members.count()),
            household.members.count(),
            program_participants,
            household.phone_number or '',
            household.created_at.strftime('%Y-%m-%d') if household.created_at else ''
        ])

    return response

@login_required
def download_ppi_report(request):
    """Download PPI assessment report as CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="ppi_report_{timezone.now().strftime("%Y%m%d")}.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'Household Name', 'Village', 'Subcounty', 'PPI Name', 'Eligibility Score',
        'Assessment Date', 'Created At'
    ])

    for ppi in PPI.objects.select_related('household', 'household__village', 'household__village__subcounty_obj').order_by('-assessment_date'):
        writer.writerow([
            ppi.household.name,
            ppi.household.village.name if ppi.household.village else '',
            ppi.household.village.subcounty_obj.name if ppi.household.village and ppi.household.village.subcounty_obj else '',
            ppi.name or 'PPI Assessment',
            ppi.eligibility_score,
            ppi.assessment_date.strftime('%Y-%m-%d'),
            ppi.created_at.strftime('%Y-%m-%d %H:%M:%S') if ppi.created_at else ''
        ])

    return response

@login_required
def download_program_participation_report(request):
    """Download program participation report as CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="program_participation_{timezone.now().strftime("%Y%m%d")}.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'Household Name', 'Village', 'Program Name', 'Participation Status',
        'Enrollment Date', 'Graduation Date', 'Progress (%)'
    ])

    for participation in HouseholdProgram.objects.select_related('household', 'household__village', 'program'):
        writer.writerow([
            participation.household.name,
            participation.household.village.name if participation.household.village else '',
            participation.program.name,
            participation.get_participation_status_display(),
            participation.enrollment_date.strftime('%Y-%m-%d') if participation.enrollment_date else '',
            participation.graduation_date.strftime('%Y-%m-%d') if participation.graduation_date else '',
            participation.progress_percentage or 0
        ])

    return response

@login_required
def download_business_groups_report(request):
    """Download business groups report as CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="business_groups_{timezone.now().strftime("%Y%m%d")}.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'Group Name', 'Business Type', 'Business Detail', 'Formation Date',
        'Group Size', 'Members Count', 'Health Status', 'Participation Status', 'Program'
    ])

    for group in BusinessGroup.objects.select_related('program').prefetch_related('members'):
        writer.writerow([
            group.name,
            group.get_business_type_display(),
            group.business_type_detail,
            group.formation_date.strftime('%Y-%m-%d'),
            group.group_size,
            group.members.count(),
            group.get_current_business_health_display(),
            group.get_participation_status_display(),
            group.program.name if group.program else ''
        ])

    return response

@login_required
def download_savings_groups_report(request):
    """Download savings groups report as CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="savings_groups_{timezone.now().strftime("%Y%m%d")}.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'Group Name', 'Formation Date', 'Members Count', 'Savings to Date (KES)',
        'Meeting Day', 'Meeting Location', 'Active Status'
    ])

    for group in BusinessSavingsGroup.objects.prefetch_related('bsg_members'):
        writer.writerow([
            group.name,
            group.formation_date.strftime('%Y-%m-%d'),
            group.bsg_members.count(),
            f"{group.savings_to_date:,.2f}",
            group.meeting_day,
            group.meeting_location,
            'Active' if group.is_active else 'Inactive'
        ])

    return response

@login_required
def download_grants_report(request):
    """Download grant disbursement report as CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="grants_report_{timezone.now().strftime("%Y%m%d")}.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'Grant Type', 'Applicant Name', 'Applicant Type', 'Business Type', 'Grant Amount (KES)',
        'Status', 'Disbursement Status', 'Disbursement Date', 'Application Date'
    ])

    # SB Grants
    for grant in SBGrant.objects.select_related('business_group', 'household', 'savings_group'):
        # Get business type from business_group if available
        business_type = grant.business_group.get_business_type_display() if grant.business_group else 'N/A'

        writer.writerow([
            'SB Grant',
            grant.get_applicant_name(),
            grant.get_applicant_type().replace('_', ' ').title(),
            business_type,
            f"{grant.get_grant_amount():,.2f}",
            grant.get_status_display(),
            grant.get_disbursement_status_display(),
            grant.disbursement_date.strftime('%Y-%m-%d') if grant.disbursement_date else '',
            grant.application_date.strftime('%Y-%m-%d') if grant.application_date else ''
        ])

    # PR Grants
    for grant in PRGrant.objects.select_related('business_group', 'household', 'savings_group'):
        # Get business type from business_group if available
        business_type = grant.business_group.get_business_type_display() if grant.business_group else 'N/A'

        writer.writerow([
            'PR Grant',
            grant.get_applicant_name(),
            grant.get_applicant_type().replace('_', ' ').title(),
            business_type,
            f"{grant.grant_amount:,.2f}",
            grant.get_status_display(),
            'N/A',  # PR Grants don't have disbursement_status field
            grant.disbursement_date.strftime('%Y-%m-%d') if grant.disbursement_date else '',
            grant.application_date.strftime('%Y-%m-%d') if grant.application_date else ''
        ])

    return response

@login_required
def download_training_report(request):
    """Download training attendance report as CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="training_report_{timezone.now().strftime("%Y%m%d")}.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'Training Name', 'Module ID', 'BM Cycle', 'Status', 'Start Date', 'End Date',
        'Enrolled Households', 'Completed Households', 'Completion Rate (%)'
    ])

    for training in Training.objects.select_related('bm_cycle').prefetch_related('enrolled_households'):
        enrolled_count = training.enrolled_households.count()
        completed_count = training.enrolled_households.filter(enrollment_status='completed').count()
        completion_rate = (completed_count / enrolled_count * 100) if enrolled_count > 0 else 0

        writer.writerow([
            training.name,
            training.module_id,
            training.bm_cycle.bm_cycle_name if training.bm_cycle else 'N/A',
            training.get_status_display(),
            training.start_date.strftime('%Y-%m-%d') if training.start_date else '',
            training.end_date.strftime('%Y-%m-%d') if training.end_date else '',
            enrolled_count,
            completed_count,
            f"{completion_rate:.1f}"
        ])

    return response

@login_required
def download_mentoring_report(request):
    """Download mentoring activities report as CSV - accessible by M&E, Admin, Field Associates"""
    user = request.user

    # Check permissions - M&E, Admin, Field Associates, and Mentors can access
    if not (user.is_superuser or user.role in ['me_staff', 'ict_admin', 'field_associate', 'mentor']):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="error.csv"'
        writer = csv.writer(response)
        writer.writerow(['Error', 'You do not have permission to access this report'])
        return response

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="mentoring_full_log_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'Activity Type', 'Household', 'Village', 'Subcounty', 'Mentor', 'Mentor Email',
        'Date', 'Time', 'Topic/Type', 'Duration (minutes)', 'Successful Contact',
        'Notes', 'Created At', 'Record ID'
    ])

    # Filter based on user role
    visits_query = MentoringVisit.objects.select_related('household', 'household__village', 'household__village__subcounty_obj', 'mentor')
    nudges_query = PhoneNudge.objects.select_related('household', 'household__village', 'household__village__subcounty_obj', 'mentor')

    # Mentors only see their own logs (unless they're superuser/admin)
    if user.role == 'mentor' and not user.is_superuser:
        visits_query = visits_query.filter(mentor=user)
        nudges_query = nudges_query.filter(mentor=user)

    # Apply date filters if provided
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    mentor_id = request.GET.get('mentor_id')

    if date_from:
        visits_query = visits_query.filter(visit_date__gte=date_from)
        nudges_query = nudges_query.filter(call_date__gte=date_from)

    if date_to:
        visits_query = visits_query.filter(visit_date__lte=date_to)
        nudges_query = nudges_query.filter(call_date__lte=date_to)

    if mentor_id and user.role != 'mentor':  # Mentors can't filter by other mentors
        visits_query = visits_query.filter(mentor_id=mentor_id)
        nudges_query = nudges_query.filter(mentor_id=mentor_id)

    # Mentoring Visits
    for visit in visits_query.order_by('-visit_date'):
        writer.writerow([
            'House Visit',
            visit.household.name,
            visit.household.village.name if visit.household.village else '',
            visit.household.village.subcounty_obj.name if visit.household.village and visit.household.village.subcounty_obj else '',
            visit.mentor.get_full_name() if visit.mentor else '',
            visit.mentor.email if visit.mentor else '',
            visit.visit_date.strftime('%Y-%m-%d') if visit.visit_date else '',
            visit.visit_time.strftime('%H:%M') if hasattr(visit, 'visit_time') and visit.visit_time else '',
            visit.topic or '',
            getattr(visit, 'duration_minutes', ''),
            'Yes',
            visit.notes or '',
            visit.created_at.strftime('%Y-%m-%d %H:%M:%S') if hasattr(visit, 'created_at') and visit.created_at else '',
            f"VISIT-{visit.id}"
        ])

    # Phone Nudges
    for nudge in nudges_query.order_by('-call_date'):
        call_date_str = ''
        call_time_str = ''

        # Handle both datetime and date fields
        if hasattr(nudge.call_date, 'date'):
            call_date_str = nudge.call_date.strftime('%Y-%m-%d')
            call_time_str = nudge.call_date.strftime('%H:%M')
        else:
            call_date_str = nudge.call_date.strftime('%Y-%m-%d') if nudge.call_date else ''

        writer.writerow([
            'Phone Call',
            nudge.household.name,
            nudge.household.village.name if nudge.household.village else '',
            nudge.household.village.subcounty_obj.name if nudge.household.village and nudge.household.village.subcounty_obj else '',
            nudge.mentor.get_full_name() if nudge.mentor else '',
            nudge.mentor.email if nudge.mentor else '',
            call_date_str,
            call_time_str,
            nudge.get_nudge_type_display() if hasattr(nudge, 'get_nudge_type_display') else nudge.nudge_type,
            nudge.duration_minutes if nudge.duration_minutes else '',
            'Yes' if nudge.successful_contact else 'No',
            nudge.notes or '',
            nudge.created_at.strftime('%Y-%m-%d %H:%M:%S') if hasattr(nudge, 'created_at') and nudge.created_at else '',
            f"CALL-{nudge.id}"
        ])

    return response

@login_required
def download_geographic_report(request):
    """Download geographic analysis report as CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="geographic_report_{timezone.now().strftime("%Y%m%d")}.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'County', 'Subcounty', 'Parish', 'Village', 'Total Households',
        'Active Programs', 'Business Groups', 'Savings Groups', 'Mentors Assigned'
    ])

    # Get all villages with related data
    from core.models import Village
    for village in Village.objects.all():
        households = Household.objects.filter(village=village)
        active_programs = HouseholdProgram.objects.filter(
            household__village=village,
            participation_status='active'
        ).count()

        business_groups = BusinessGroup.objects.filter(
            members__household__village=village
        ).distinct().count()

        # This would need to be adjusted based on your savings group model structure
        savings_groups = 0  # BusinessSavingsGroup doesn't have village relation in current model

        writer.writerow([
            village.country,
            village.subcounty,
            '',  # parish not available in current model
            village.name,
            households.count(),
            active_programs,
            business_groups,
            savings_groups,
            0  # assigned_mentors not available in current model
        ])

    return response

@login_required
def performance_dashboard(request):
    """Performance dashboard with key metrics and charts"""
    # Calculate key performance indicators
    total_households = Household.objects.count()
    active_programs = HouseholdProgram.objects.filter(participation_status='active').count()
    graduated_programs = HouseholdProgram.objects.filter(participation_status='graduated').count()
    total_business_groups = BusinessGroup.objects.count()
    total_savings_groups = BusinessSavingsGroup.objects.count()

    # Program participation statistics
    program_stats = []
    from core.models import Program
    for program in Program.objects.all():
        enrolled = HouseholdProgram.objects.filter(program=program).count()
        active = HouseholdProgram.objects.filter(program=program, participation_status='active').count()
        graduated = HouseholdProgram.objects.filter(program=program, participation_status='graduated').count()
        program_stats.append({
            'name': program.name,
            'enrolled': enrolled,
            'active': active,
            'graduated': graduated,
            'completion_rate': (graduated / enrolled * 100) if enrolled > 0 else 0
        })

    # Geographic distribution
    from core.models import Village
    geographic_stats = []
    for village in Village.objects.all()[:10]:  # Top 10 villages
        household_count = Household.objects.filter(village=village).count()
        active_count = HouseholdProgram.objects.filter(
            household__village=village,
            participation_status='active'
        ).count()
        geographic_stats.append({
            'village': village.name,
            'subcounty': village.subcounty,
            'households': household_count,
            'active_programs': active_count
        })

    context = {
        'page_title': 'Program Performance Dashboard',
        'total_households': total_households,
        'active_programs': active_programs,
        'graduated_programs': graduated_programs,
        'total_business_groups': total_business_groups,
        'total_savings_groups': total_savings_groups,
        'program_stats': program_stats,
        'geographic_stats': geographic_stats,
        'graduation_rate': (graduated_programs / total_households * 100) if total_households > 0 else 0,
    }

    return render(request, 'reports/performance_dashboard.html', context)

@login_required
def custom_report_builder(request):
    """Custom report builder interface"""
    from core.models import Village, Program

    # Available filter options
    villages = Village.objects.all()
    programs = Program.objects.all()

    # Available report types
    report_types = [
        ('households', 'Household Report'),
        ('business_groups', 'Business Groups Report'),
        ('savings_groups', 'Savings Groups Report'),
        ('training', 'Training Report'),
        ('ppi', 'PPI Assessment Report'),
        ('geographic', 'Geographic Analysis'),
    ]

    context = {
        'page_title': 'Custom Report Builder',
        'villages': villages,
        'programs': programs,
        'report_types': report_types,
    }

    return render(request, 'reports/custom_report_builder.html', context)

@login_required
def download_custom_report(request):
    """Download custom report based on user selections"""
    report_type = request.GET.get('report_type', 'households')
    village_id = request.GET.get('village')
    program_id = request.GET.get('program')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="custom_report_{timezone.now().strftime("%Y%m%d")}.csv"'

    writer = csv.writer(response)

    if report_type == 'households':
        writer.writerow(['Household Name', 'Village', 'Phone Number', 'Members', 'Registration Date'])

        households = Household.objects.all()
        if village_id:
            households = households.filter(village_id=village_id)
        if date_from:
            households = households.filter(created_at__gte=date_from)
        if date_to:
            households = households.filter(created_at__lte=date_to)

        for household in households.select_related('village'):
            writer.writerow([
                household.name,
                household.village.name if household.village else '',
                household.phone_number or '',
                household.members.count(),
                household.created_at.strftime('%Y-%m-%d') if household.created_at else ''
            ])

    elif report_type == 'business_groups':
        writer.writerow(['Group Name', 'Village', 'Business Type', 'Formation Date', 'Members'])

        groups = BusinessGroup.objects.all()
        if village_id:
            groups = groups.filter(members__household__village_id=village_id).distinct()

        for group in groups:
            village_name = ''
            if group.members.exists():
                first_member = group.members.first()
                if first_member.household.village:
                    village_name = first_member.household.village.name

            writer.writerow([
                group.name,
                village_name,
                group.get_business_type_display(),
                group.formation_date.strftime('%Y-%m-%d'),
                group.members.count()
            ])

    else:
        # Default fallback
        writer.writerow(['Report Type', 'Status'])
        writer.writerow([report_type, 'Not implemented yet'])

    return response