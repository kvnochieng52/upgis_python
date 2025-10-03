from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.db.models import Sum
from datetime import date
from decimal import Decimal, InvalidOperation
import csv
from .models import BusinessSavingsGroup, BSGMember, SavingsRecord
from core.models import Village
from business_groups.models import BusinessGroup
from households.models import Household

@login_required
def savings_list(request):
    """Savings Groups list view with role-based filtering"""
    user = request.user

    # Filter savings groups based on user role and village assignments
    if user.is_superuser or user.role in ['ict_admin', 'me_staff']:
        # Full access to all savings groups
        savings_groups = BusinessSavingsGroup.objects.filter(is_active=True)
    elif user.role in ['mentor', 'field_associate']:
        # Only groups with members from assigned villages
        if hasattr(user, 'profile') and user.profile:
            assigned_villages = user.profile.assigned_villages.all()
            savings_groups = BusinessSavingsGroup.objects.filter(
                is_active=True,
                bsg_members__household__village__in=assigned_villages
            ).distinct()
        else:
            # No villages assigned, no groups visible
            savings_groups = BusinessSavingsGroup.objects.none()
    else:
        # Other roles have no access to savings groups
        savings_groups = BusinessSavingsGroup.objects.none()

    savings_groups = savings_groups.order_by('-formation_date')

    context = {
        'savings_groups': savings_groups,
        'page_title': 'Savings Groups',
        'total_count': savings_groups.count(),
    }

    return render(request, 'savings_groups/savings_list.html', context)

@login_required
def savings_group_create(request):
    """Create savings group with role-based filtering"""
    user = request.user

    if request.method == 'POST':
        name = request.POST.get('name')
        village_id = request.POST.get('village')
        business_group_id = request.POST.get('business_group')
        target_members = request.POST.get('target_members', 20)

        # Validate village access for mentors
        if user.role in ['mentor', 'field_associate'] and village_id:
            if hasattr(user, 'profile') and user.profile:
                assigned_villages = user.profile.assigned_villages.values_list('id', flat=True)
                if int(village_id) not in assigned_villages:
                    messages.error(request, 'You can only create savings groups in your assigned villages.')
                    village_id = None

        if name:
            formation_date = request.POST.get('formation_date') or date.today()
            meeting_day = request.POST.get('meeting_day', '')
            meeting_location = request.POST.get('meeting_location', '')

            savings_group = BusinessSavingsGroup.objects.create(
                name=name,
                formation_date=formation_date,
                meeting_day=meeting_day,
                meeting_location=meeting_location,
                members_count=0
            )
            messages.success(request, f'Savings group "{savings_group.name}" created successfully!')
            return redirect('savings_groups:savings_group_detail', pk=savings_group.pk)
        else:
            messages.error(request, 'Savings group name is required.')

    # Filter villages and business groups based on user role
    if user.is_superuser or user.role in ['ict_admin', 'me_staff']:
        villages = Village.objects.all()
        business_groups = BusinessGroup.objects.all()
    elif user.role in ['mentor', 'field_associate']:
        if hasattr(user, 'profile') and user.profile:
            assigned_villages = user.profile.assigned_villages.all()
            villages = assigned_villages
            # Business groups with members from assigned villages
            business_groups = BusinessGroup.objects.filter(
                members__household__village__in=assigned_villages
            ).distinct()
        else:
            villages = Village.objects.none()
            business_groups = BusinessGroup.objects.none()
            messages.warning(request, 'You have no assigned villages. Please contact your administrator.')
    else:
        villages = Village.objects.none()
        business_groups = BusinessGroup.objects.none()
        messages.error(request, 'You do not have permission to create savings groups.')

    context = {
        'villages': villages,
        'business_groups': business_groups,
        'page_title': 'Create Savings Group',
    }
    return render(request, 'savings_groups/savings_group_create.html', context)

@login_required
def savings_group_detail(request, pk):
    """Savings group detail view"""
    savings_group = get_object_or_404(BusinessSavingsGroup, pk=pk)

    # Calculate membership percentage
    current_members = savings_group.bsg_members.filter(is_active=True).count()
    target_members = savings_group.target_members or 25  # Default target if not set
    membership_percentage = round((current_members * 100) / target_members) if target_members > 0 else 0

    context = {
        'savings_group': savings_group,
        'page_title': f'Savings Group - {savings_group.name}',
        'current_members': current_members,
        'membership_percentage': membership_percentage,
    }
    return render(request, 'savings_groups/savings_group_detail.html', context)

@login_required
def savings_group_edit(request, pk):
    """Edit savings group"""
    savings_group = get_object_or_404(BusinessSavingsGroup, pk=pk)

    if request.method == 'POST':
        savings_group.name = request.POST.get('name', savings_group.name)
        formation_date = request.POST.get('formation_date')
        if formation_date:
            savings_group.formation_date = formation_date
        savings_group.meeting_day = request.POST.get('meeting_day', savings_group.meeting_day)
        savings_group.meeting_location = request.POST.get('meeting_location', savings_group.meeting_location)

        # Handle savings_frequency
        savings_frequency = request.POST.get('savings_frequency')
        if savings_frequency:
            savings_group.savings_frequency = savings_frequency

        # Handle target_members
        target_members = request.POST.get('target_members')
        if target_members:
            try:
                savings_group.target_members = int(target_members)
            except ValueError:
                pass  # Keep existing value if invalid input

        savings_group.save()
        messages.success(request, f'Savings group "{savings_group.name}" updated successfully!')
        return redirect('savings_groups:savings_group_detail', pk=savings_group.pk)

    villages = Village.objects.all()
    business_groups = BusinessGroup.objects.all()

    # Calculate membership percentage
    current_members = savings_group.bsg_members.filter(is_active=True).count()
    target_members = savings_group.target_members or 25  # Default target if not set
    membership_percentage = round((current_members * 100) / target_members) if target_members > 0 else 0

    context = {
        'savings_group': savings_group,
        'villages': villages,
        'business_groups': business_groups,
        'page_title': f'Edit - {savings_group.name}',
        'current_members': current_members,
        'membership_percentage': membership_percentage,
    }
    return render(request, 'savings_groups/savings_group_edit.html', context)

@login_required
def add_member(request, pk):
    """Add individual member to savings group"""
    savings_group = get_object_or_404(BusinessSavingsGroup, pk=pk)

    if request.method == 'POST':
        household_id = request.POST.get('household')
        role = request.POST.get('role', 'member')
        joined_date = request.POST.get('joined_date') or date.today()

        if household_id:
            try:
                household = Household.objects.get(id=household_id)

                # Check if already a member
                if BSGMember.objects.filter(bsg=savings_group, household=household, is_active=True).exists():
                    messages.warning(request, f'{household.name} is already a member of this savings group.')
                else:
                    BSGMember.objects.create(
                        bsg=savings_group,
                        household=household,
                        role=role,
                        joined_date=joined_date,
                        is_active=True
                    )
                    messages.success(request, f'{household.name} added to {savings_group.name} successfully!')
            except Household.DoesNotExist:
                messages.error(request, 'Selected household does not exist.')
        else:
            messages.error(request, 'Please select a household.')

        return redirect('savings_groups:savings_group_detail', pk=pk)

    # Get available households (not already members)
    existing_member_households = savings_group.bsg_members.filter(is_active=True).values_list('household_id', flat=True)
    available_households = Household.objects.exclude(id__in=existing_member_households).order_by('name')

    context = {
        'savings_group': savings_group,
        'households': available_households,
        'role_choices': BSGMember.ROLE_CHOICES,
        'page_title': f'Add Member to {savings_group.name}',
    }
    return render(request, 'savings_groups/add_member.html', context)

@login_required
def remove_member(request, pk, member_id):
    """Remove individual member from savings group"""
    savings_group = get_object_or_404(BusinessSavingsGroup, pk=pk)
    member = get_object_or_404(BSGMember, id=member_id, bsg=savings_group)

    if request.method == 'POST':
        member.is_active = False
        member.save()
        messages.success(request, f'{member.household.name} removed from {savings_group.name}.')
        return redirect('savings_groups:savings_group_detail', pk=pk)

    context = {
        'savings_group': savings_group,
        'member': member,
        'page_title': f'Remove Member from {savings_group.name}',
    }
    return render(request, 'savings_groups/remove_member_confirm.html', context)

@login_required
def add_business_group(request, pk):
    """Associate business group with savings group and auto-add all members"""
    savings_group = get_object_or_404(BusinessSavingsGroup, pk=pk)

    if request.method == 'POST':
        business_group_id = request.POST.get('business_group')

        if business_group_id:
            try:
                business_group = BusinessGroup.objects.get(id=business_group_id)

                # Check if already associated
                if business_group in savings_group.business_groups.all():
                    messages.warning(request, f'{business_group.name} is already part of this savings group.')
                else:
                    # Add business group to savings group
                    savings_group.business_groups.add(business_group)

                    # Automatically add all business group members to savings group
                    members_added = 0
                    for bg_member in business_group.members.all():
                        # Check if household is not already a member
                        if not BSGMember.objects.filter(bsg=savings_group, household=bg_member.household, is_active=True).exists():
                            BSGMember.objects.create(
                                bsg=savings_group,
                                household=bg_member.household,
                                role='member',
                                joined_date=date.today(),
                                is_active=True
                            )
                            members_added += 1

                    messages.success(request, f'{business_group.name} added to {savings_group.name} successfully! {members_added} member(s) added.')
            except BusinessGroup.DoesNotExist:
                messages.error(request, 'Selected business group does not exist.')
        else:
            messages.error(request, 'Please select a business group.')

        return redirect('savings_groups:savings_group_detail', pk=pk)

    # Get available business groups (not already associated)
    available_business_groups = BusinessGroup.objects.exclude(
        id__in=savings_group.business_groups.values_list('id', flat=True)
    ).order_by('name')

    context = {
        'savings_group': savings_group,
        'business_groups': available_business_groups,
        'page_title': f'Add Business Group to {savings_group.name}',
    }
    return render(request, 'savings_groups/add_business_group.html', context)

@login_required
def remove_business_group(request, pk, bg_id):
    """Remove business group from savings group"""
    savings_group = get_object_or_404(BusinessSavingsGroup, pk=pk)
    business_group = get_object_or_404(BusinessGroup, id=bg_id)

    if request.method == 'POST':
        savings_group.business_groups.remove(business_group)
        messages.success(request, f'{business_group.name} removed from {savings_group.name}.')
        return redirect('savings_groups:savings_group_detail', pk=pk)

    context = {
        'savings_group': savings_group,
        'business_group': business_group,
        'page_title': f'Remove Business Group from {savings_group.name}',
    }
    return render(request, 'savings_groups/remove_business_group_confirm.html', context)

@login_required
def record_savings(request, pk):
    """Record savings for a savings group meeting"""
    savings_group = get_object_or_404(BusinessSavingsGroup, pk=pk)

    if request.method == 'POST':
        savings_date = request.POST.get('savings_date') or date.today()
        notes = request.POST.get('notes', '')
        records_created = 0

        # Process each member's savings
        for member in savings_group.bsg_members.filter(is_active=True):
            amount_key = f'amount_{member.id}'
            amount = request.POST.get(amount_key, '0')

            try:
                amount = Decimal(str(amount))
                if amount > 0:
                    # Create savings record
                    SavingsRecord.objects.create(
                        bsg=savings_group,
                        member=member,
                        amount=amount,
                        savings_date=savings_date,
                        recorded_by=request.user,
                        notes=notes
                    )

                    # Update member's total savings - refresh from DB first to avoid stale data
                    member.refresh_from_db()
                    current_total = member.total_savings or Decimal('0')
                    member.total_savings = current_total + amount
                    member.save()

                    records_created += 1
            except (ValueError, TypeError, InvalidOperation):
                pass

        # Update group's total savings - refresh first
        savings_group.refresh_from_db()
        total_savings = savings_group.bsg_members.filter(is_active=True).aggregate(
            total=Sum('total_savings'))['total'] or Decimal('0')
        savings_group.savings_to_date = total_savings
        savings_group.save()

        messages.success(request, f'{records_created} savings record(s) created successfully!')
        return redirect('savings_groups:savings_group_detail', pk=pk)

    context = {
        'savings_group': savings_group,
        'members': savings_group.bsg_members.filter(is_active=True).order_by('household__name'),
        'page_title': f'Record Savings - {savings_group.name}',
    }
    return render(request, 'savings_groups/record_savings.html', context)


@login_required
def savings_report(request, pk):
    """Generate savings report for a savings group"""
    savings_group = get_object_or_404(BusinessSavingsGroup, pk=pk)

    # Get filter parameters
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')

    # Get all savings records
    savings_records = SavingsRecord.objects.filter(bsg=savings_group)

    if date_from:
        savings_records = savings_records.filter(savings_date__gte=date_from)
    if date_to:
        savings_records = savings_records.filter(savings_date__lte=date_to)

    # Calculate totals
    total_savings = savings_records.aggregate(total=Sum('amount'))['total'] or 0

    # Member summaries
    member_summaries = []
    for member in savings_group.bsg_members.filter(is_active=True):
        member_records = savings_records.filter(member=member)
        member_total = member_records.aggregate(total=Sum('amount'))['total'] or 0
        member_summaries.append({
            'member': member,
            'total_savings': member_total,
            'record_count': member_records.count(),
            'latest_savings': member_records.order_by('-savings_date').first(),
        })

    context = {
        'savings_group': savings_group,
        'savings_records': savings_records.order_by('-savings_date'),
        'total_savings': total_savings,
        'member_summaries': member_summaries,
        'date_from': date_from,
        'date_to': date_to,
        'page_title': f'Savings Report - {savings_group.name}',
    }
    return render(request, 'savings_groups/savings_report.html', context)


@login_required
def export_savings_data(request, pk):
    """Export savings data to CSV"""
    savings_group = get_object_or_404(BusinessSavingsGroup, pk=pk)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="savings_{savings_group.name}_{date.today()}.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'Date', 'Member Name', 'Amount (KES)', 'Recorded By', 'Notes'
    ])

    # Get savings records
    for record in SavingsRecord.objects.filter(bsg=savings_group).order_by('-savings_date'):
        writer.writerow([
            record.savings_date.strftime('%Y-%m-%d'),
            record.member.household.name,
            f"{record.amount:,.2f}",
            record.recorded_by.get_full_name() if record.recorded_by else 'N/A',
            record.notes
        ])

    # Add summary rows
    writer.writerow([])
    writer.writerow(['SUMMARY'])
    writer.writerow(['Total Savings:', f"KES {savings_group.savings_to_date:,.2f}"])
    writer.writerow(['Total Members:', savings_group.bsg_members.filter(is_active=True).count()])
    writer.writerow(['Savings Frequency:', savings_group.get_savings_frequency_display()])

    return response
