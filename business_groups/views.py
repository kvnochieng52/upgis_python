from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import BusinessGroup, BusinessGroupMember
from households.models import Household
from core.models import Program
from datetime import date

@login_required
def group_list(request):
    """Business Groups list view with role-based filtering"""
    user = request.user

    # Filter business groups based on user role and village assignments
    if user.is_superuser or user.role in ['ict_admin', 'me_staff']:
        # Full access to all business groups
        groups = BusinessGroup.objects.all()
    elif user.role in ['mentor', 'field_associate']:
        # Only groups with members from assigned villages
        if hasattr(user, 'profile') and user.profile:
            assigned_villages = user.profile.assigned_villages.all()
            groups = BusinessGroup.objects.filter(
                members__household__village__in=assigned_villages
            ).distinct()
        else:
            # No villages assigned, no groups visible
            groups = BusinessGroup.objects.none()
    else:
        # Other roles have no access to business groups
        groups = BusinessGroup.objects.none()

    groups = groups.order_by('-created_at')

    context = {
        'groups': groups,
        'page_title': 'Business Groups',
        'total_count': groups.count(),
    }

    return render(request, 'business_groups/group_list.html', context)

@login_required
def group_create(request):
    """Create business group"""
    if request.method == 'POST':
        name = request.POST.get('name')
        program_id = request.POST.get('program')
        business_type = request.POST.get('business_type')
        business_type_detail = request.POST.get('business_type_detail', '')
        group_size = request.POST.get('group_size', 2)
        formation_date = request.POST.get('formation_date') or date.today()

        if name and program_id:
            group = BusinessGroup.objects.create(
                name=name,
                program_id=program_id,
                business_type=business_type or 'crop',
                business_type_detail=business_type_detail,
                group_size=int(group_size),
                formation_date=formation_date
            )
            messages.success(request, f'Business group "{group.name}" created successfully!')
            return redirect('business_groups:group_detail', pk=group.pk)
        else:
            messages.error(request, 'Group name and program are required.')

    programs = Program.objects.filter(status='active')
    context = {
        'programs': programs,
        'business_type_choices': BusinessGroup.BUSINESS_TYPE_CHOICES,
        'page_title': 'Create Business Group',
    }
    return render(request, 'business_groups/group_create.html', context)

@login_required
def group_detail(request, pk):
    """Business group detail view"""
    group = get_object_or_404(BusinessGroup, pk=pk)
    context = {
        'group': group,
        'page_title': f'Business Group - {group.name}',
    }
    return render(request, 'business_groups/group_detail.html', context)

@login_required
def group_edit(request, pk):
    """Edit business group"""
    group = get_object_or_404(BusinessGroup, pk=pk)

    if request.method == 'POST':
        group.name = request.POST.get('name', group.name)
        program_id = request.POST.get('program')
        if program_id:
            group.program_id = program_id
        group.business_type = request.POST.get('business_type', group.business_type)
        group.business_type_detail = request.POST.get('business_type_detail', group.business_type_detail)
        group.group_size = request.POST.get('group_size', group.group_size)
        formation_date = request.POST.get('formation_date')
        if formation_date:
            group.formation_date = formation_date

        group.save()
        messages.success(request, f'Business group "{group.name}" updated successfully!')
        return redirect('business_groups:group_detail', pk=group.pk)

    programs = Program.objects.filter(status='active')
    context = {
        'group': group,
        'programs': programs,
        'business_type_choices': BusinessGroup.BUSINESS_TYPE_CHOICES,
        'page_title': f'Edit - {group.name}',
    }
    return render(request, 'business_groups/group_edit.html', context)

@login_required
def add_member(request, pk):
    """Add household to business group"""
    group = get_object_or_404(BusinessGroup, pk=pk)

    if request.method == 'POST':
        household_id = request.POST.get('household_id')
        role = request.POST.get('role', 'member')
        joined_date = request.POST.get('joined_date') or date.today()

        if household_id:
            try:
                household = Household.objects.get(id=household_id)

                # Check if household is already a member
                if BusinessGroupMember.objects.filter(business_group=group, household=household).exists():
                    messages.error(request, f'{household.name} is already a member of this group.')
                else:
                    BusinessGroupMember.objects.create(
                        business_group=group,
                        household=household,
                        role=role,
                        joined_date=joined_date
                    )
                    messages.success(request, f'{household.name} added to {group.name} successfully!')

            except Household.DoesNotExist:
                messages.error(request, 'Selected household not found.')
        else:
            messages.error(request, 'Please select a household.')

    return redirect('business_groups:group_detail', pk=pk)

@login_required
def remove_member(request, pk, member_id):
    """Remove household from business group"""
    group = get_object_or_404(BusinessGroup, pk=pk)
    member = get_object_or_404(BusinessGroupMember, id=member_id, business_group=group)

    if request.method == 'POST':
        household_name = member.household.name
        member.delete()
        messages.success(request, f'{household_name} removed from {group.name}.')

    return redirect('business_groups:group_detail', pk=pk)

@login_required
def update_member_role(request, pk, member_id):
    """Update member role in business group"""
    group = get_object_or_404(BusinessGroup, pk=pk)
    member = get_object_or_404(BusinessGroupMember, id=member_id, business_group=group)

    if request.method == 'POST':
        new_role = request.POST.get('role')
        if new_role in dict(BusinessGroupMember.ROLE_CHOICES):
            member.role = new_role
            member.save()
            messages.success(request, f'{member.household.name} role updated to {member.get_role_display()}.')
        else:
            messages.error(request, 'Invalid role selected.')

    return redirect('business_groups:group_detail', pk=pk)

@login_required
def get_available_households(request, pk):
    """AJAX endpoint to get households that can be added to the group"""
    group = get_object_or_404(BusinessGroup, pk=pk)

    # Get households that are not already members of this group
    existing_member_ids = group.members.values_list('household_id', flat=True)
    available_households = Household.objects.exclude(id__in=existing_member_ids)

    # Filter by user role and village assignments
    user = request.user
    if user.role in ['mentor', 'field_associate']:
        if hasattr(user, 'profile') and user.profile:
            assigned_villages = user.profile.assigned_villages.all()
            available_households = available_households.filter(village__in=assigned_villages)

    households_data = []
    for household in available_households[:20]:  # Limit to 20 for performance
        households_data.append({
            'id': household.id,
            'name': household.name,
            'village': household.village.name if household.village else 'No Village'
        })

    return JsonResponse({'households': households_data})