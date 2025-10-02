from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Count
from django.utils import timezone
from django.http import JsonResponse
from datetime import datetime, timedelta
from upg_grants.models import SBGrant, PRGrant, GrantDisbursement, HouseholdGrantApplication
from business_groups.models import BusinessGroup
from programs.models import Program
from households.models import Household

@login_required
def grants_dashboard(request):
    """Grants management dashboard with comprehensive statistics"""
    # Check permissions
    user_role = getattr(request.user, 'role', None)
    if not (request.user.is_superuser or user_role in ['ict_admin', 'county_executive', 'field_associate']):
        messages.error(request, 'You do not have permission to access grants management.')
        return redirect('dashboard:dashboard')

    # SB Grant Statistics
    sb_grants = {
        'total': SBGrant.objects.count(),
        'pending': SBGrant.objects.filter(status='pending').count(),
        'approved': SBGrant.objects.filter(status='approved').count(),
        'funded': SBGrant.objects.filter(status='disbursed').count(),
        'rejected': SBGrant.objects.filter(status='rejected').count(),
        'total_amount_funded': SBGrant.objects.filter(status='disbursed').aggregate(total=Sum('disbursed_amount'))['total'] or 0,
    }

    # PR Grant Statistics
    pr_grants = {
        'total': PRGrant.objects.count(),
        'pending': PRGrant.objects.filter(status='pending').count(),
        'approved': PRGrant.objects.filter(status='approved').count(),
        'funded': PRGrant.objects.filter(status='disbursed').count(),
        'rejected': PRGrant.objects.filter(status='rejected').count(),
        'total_amount_funded': PRGrant.objects.filter(status='disbursed').aggregate(total=Sum('grant_amount'))['total'] or 0,
    }

    # Household Grant Statistics
    household_grants = {
        'total': HouseholdGrantApplication.objects.count(),
        'pending': HouseholdGrantApplication.objects.filter(status__in=['submitted', 'under_review']).count(),
        'approved': HouseholdGrantApplication.objects.filter(status='approved').count(),
        'disbursed': HouseholdGrantApplication.objects.filter(status='disbursed').count(),
        'rejected': HouseholdGrantApplication.objects.filter(status='rejected').count(),
        'total_amount_approved': HouseholdGrantApplication.objects.filter(status='approved').aggregate(total=Sum('approved_amount'))['total'] or 0,
    }

    # Recent activities
    recent_sb_grants = SBGrant.objects.all().order_by('-created_at')[:5]
    recent_pr_grants = PRGrant.objects.all().order_by('-created_at')[:5]
    recent_household_grants = HouseholdGrantApplication.objects.all().order_by('-created_at')[:5]

    # Disbursement statistics - aggregate from all grant types
    sb_disbursed = SBGrant.objects.filter(status='disbursed').aggregate(total=Sum('disbursed_amount'))['total'] or 0
    pr_disbursed = PRGrant.objects.filter(status='disbursed').aggregate(total=Sum('grant_amount'))['total'] or 0
    household_disbursed = HouseholdGrantApplication.objects.filter(status='disbursed').aggregate(total=Sum('disbursed_amount'))['total'] or 0

    total_disbursed = sb_disbursed + pr_disbursed + household_disbursed

    # Pending disbursements (approved but not yet disbursed)
    sb_pending = SBGrant.objects.filter(status='approved').count()
    pr_pending = PRGrant.objects.filter(status='approved').count()
    household_pending = HouseholdGrantApplication.objects.filter(status='approved').count()
    pending_count = sb_pending + pr_pending + household_pending

    # Completed disbursements count
    sb_completed = SBGrant.objects.filter(status='disbursed').count()
    pr_completed = PRGrant.objects.filter(status='disbursed').count()
    household_completed = HouseholdGrantApplication.objects.filter(status='disbursed').count()
    completed_count = sb_completed + pr_completed + household_completed

    disbursements = {
        'total_disbursed': total_disbursed,
        'pending_disbursements': pending_count,
        'completed_disbursements': completed_count,
        'sb_disbursed': sb_disbursed,
        'pr_disbursed': pr_disbursed,
        'household_disbursed': household_disbursed,
    }

    # Get available applicants for grant application
    households = Household.objects.all().order_by('name')
    business_groups = BusinessGroup.objects.all().order_by('name')

    from savings_groups.models import BusinessSavingsGroup
    savings_groups = BusinessSavingsGroup.objects.filter(is_active=True).order_by('name')

    context = {
        'page_title': 'Grants Management Dashboard',
        'sb_grants': sb_grants,
        'pr_grants': pr_grants,
        'household_grants': household_grants,
        'disbursements': disbursements,
        'recent_sb_grants': recent_sb_grants,
        'recent_pr_grants': recent_pr_grants,
        'recent_household_grants': recent_household_grants,
        'total_grants': sb_grants['total'] + pr_grants['total'] + household_grants['total'],
        'total_funding': sb_grants['total_amount_funded'] + pr_grants['total_amount_funded'] + household_grants['total_amount_approved'],
        'households': households,
        'business_groups': business_groups,
        'savings_groups': savings_groups,
    }
    return render(request, 'grants/grants_dashboard.html', context)

@login_required
def sb_grant_applications(request):
    """View and process SB grant applications"""
    user_role = getattr(request.user, 'role', None)
    if not (request.user.is_superuser or user_role in ['ict_admin', 'county_executive', 'field_associate']):
        messages.error(request, 'You do not have permission to process grants.')
        return redirect('grants:grants_dashboard')

    grants = SBGrant.objects.all().order_by('-created_at')

    # Filter by status
    status_filter = request.GET.get('status')
    if status_filter:
        grants = grants.filter(status=status_filter)

    # Search functionality
    search_query = request.GET.get('search')
    if search_query:
        grants = grants.filter(
            Q(business_group__name__icontains=search_query) |
            Q(business_group__business_type__icontains=search_query)
        )

    # Pagination
    paginator = Paginator(grants, 10)
    page_number = request.GET.get('page')
    grants = paginator.get_page(page_number)

    context = {
        'page_title': 'SB Grant Applications',
        'grants': grants,
        'status_choices': SBGrant.GRANT_STATUS_CHOICES,
        'search_query': search_query,
        'selected_status': status_filter,
    }
    return render(request, 'grants/sb_grants.html', context)

@login_required
def pr_grant_applications(request):
    """View and process PR grant applications"""
    user_role = getattr(request.user, 'role', None)
    if not (request.user.is_superuser or user_role in ['ict_admin', 'county_executive', 'field_associate']):
        messages.error(request, 'You do not have permission to process grants.')
        return redirect('grants:grants_dashboard')

    grants = PRGrant.objects.all().order_by('-created_at')

    # Filter by status
    status_filter = request.GET.get('status')
    if status_filter:
        grants = grants.filter(status=status_filter)

    # Search functionality
    search_query = request.GET.get('search')
    if search_query:
        grants = grants.filter(
            Q(business_group__name__icontains=search_query) |
            Q(business_group__business_type__icontains=search_query)
        )

    # Pagination
    paginator = Paginator(grants, 10)
    page_number = request.GET.get('page')
    grants = paginator.get_page(page_number)

    context = {
        'page_title': 'PR Grant Applications',
        'grants': grants,
        'status_choices': PRGrant.GRANT_STATUS_CHOICES,
        'search_query': search_query,
        'selected_status': status_filter,
    }
    return render(request, 'grants/pr_grants.html', context)

@login_required
def grant_detail(request, grant_type, grant_id):
    """View grant application details"""
    user_role = getattr(request.user, 'role', None)
    if not (request.user.is_superuser or user_role in ['ict_admin', 'county_executive', 'field_associate']):
        messages.error(request, 'You do not have permission to view grant details.')
        return redirect('grants:grants_dashboard')

    if grant_type == 'sb':
        grant = get_object_or_404(SBGrant, id=grant_id)
        template = 'grants/sb_grant_detail.html'
    else:
        grant = get_object_or_404(PRGrant, id=grant_id)
        template = 'grants/pr_grant_detail.html'

    context = {
        'page_title': f'{grant_type.upper()} Grant Application',
        'grant': grant,
        'grant_type': grant_type,
    }
    return render(request, template, context)

@login_required
def process_grant(request, grant_type, grant_id):
    """Process grant application (approve/reject)"""
    user_role = getattr(request.user, 'role', None)
    if not (request.user.is_superuser or user_role in ['ict_admin', 'county_executive', 'field_associate']):
        messages.error(request, 'You do not have permission to process grants.')
        return redirect('grants:grants_dashboard')

    if grant_type == 'sb':
        grant = get_object_or_404(SBGrant, id=grant_id)
    else:
        grant = get_object_or_404(PRGrant, id=grant_id)

    if request.method == 'POST':
        action = request.POST.get('action')
        notes = request.POST.get('notes', '')

        if action == 'approve':
            grant.status = 'funded'
            grant.disbursement_date = timezone.now().date()
            messages.success(request, f'{grant_type.upper()} Grant approved successfully!')
        elif action == 'reject':
            grant.status = 'rejected'
            grant.processed_by = request.user
            grant.notes = notes
            messages.info(request, f'{grant_type.upper()} Grant rejected.')
        elif action == 'review':
            grant.status = 'approved'
            grant.notes = notes
            messages.info(request, f'{grant_type.upper()} Grant moved to review.')

        grant.save()
        return redirect('grants:grant_detail', grant_type=grant_type, grant_id=grant_id)

    return redirect('grants:grant_detail', grant_type=grant_type, grant_id=grant_id)