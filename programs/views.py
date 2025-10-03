from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from .models import Program, ProgramApplication, ProgramBeneficiary
from households.models import Household

@login_required
def program_list(request):
    """List all programs"""
    programs = Program.objects.filter(status__in=['active', 'draft']).order_by('-created_at')

    # Search functionality
    search_query = request.GET.get('search')
    if search_query:
        programs = programs.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(county__icontains=search_query)
        )

    # Filter by program type
    program_type = request.GET.get('type')
    if program_type:
        programs = programs.filter(program_type=program_type)

    # Pagination
    paginator = Paginator(programs, 10)
    page_number = request.GET.get('page')
    programs = paginator.get_page(page_number)

    context = {
        'programs': programs,
        'program_types': Program.PROGRAM_TYPE_CHOICES,
        'search_query': search_query,
        'selected_type': program_type,
        'page_title': 'Programs',
    }

    return render(request, 'programs/program_list.html', context)

@login_required
def program_create(request):
    """Create a new program (County Executives, ICT Admins, and Superusers)"""
    user_role = getattr(request.user, 'role', None)
    if not (request.user.is_superuser or user_role in ['county_executive', 'ict_admin']):
        messages.error(request, 'You do not have permission to create programs.')
        return redirect('programs:program_list')

    if request.method == 'POST':
        # Basic form processing - in production, use Django forms
        name = request.POST.get('name')
        description = request.POST.get('description')
        program_type = request.POST.get('program_type')
        budget = request.POST.get('budget') or None
        target_beneficiaries = request.POST.get('target_beneficiaries') or 0

        if name and description:
            program = Program.objects.create(
                name=name,
                description=description,
                program_type=program_type,
                budget=budget,
                target_beneficiaries=target_beneficiaries,
                created_by=request.user,
                county=getattr(request.user, 'county', ''),
                eligibility_criteria=request.POST.get('eligibility_criteria', ''),
                application_requirements=request.POST.get('application_requirements', ''),
            )
            messages.success(request, f'Program "{program.name}" created successfully!')
            return redirect('programs:program_detail', pk=program.pk)
        else:
            messages.error(request, 'Name and description are required.')

    context = {
        'program_types': Program.PROGRAM_TYPE_CHOICES,
        'page_title': 'Create New Program',
    }

    return render(request, 'programs/program_create.html', context)

@login_required
def program_detail(request, pk):
    """Program detail view"""
    program = get_object_or_404(Program, pk=pk)

    # Check if current user has already applied
    user_application = None
    if hasattr(request.user, 'household'):
        try:
            user_application = ProgramApplication.objects.get(
                program=program,
                household=request.user.household
            )
        except ProgramApplication.DoesNotExist:
            pass

    context = {
        'program': program,
        'user_application': user_application,
        'can_apply': program.is_accepting_applications and not user_application,
        'page_title': program.name,
    }

    return render(request, 'programs/program_detail.html', context)

@login_required
def program_applications(request, pk):
    """View applications for a program (Program creators, admins, and superusers)"""
    program = get_object_or_404(Program, pk=pk)

    user_role = getattr(request.user, 'role', None)
    if not (request.user.is_superuser or
            request.user == program.created_by or
            user_role in ['ict_admin', 'me_staff']):
        messages.error(request, 'You do not have permission to view applications.')
        return redirect('programs:program_detail', pk=program.pk)

    applications = program.applications.all().order_by('-application_date')

    # Filter by status
    status_filter = request.GET.get('status')
    if status_filter:
        applications = applications.filter(status=status_filter)

    context = {
        'program': program,
        'applications': applications,
        'status_choices': ProgramApplication.APPLICATION_STATUS_CHOICES,
        'selected_status': status_filter,
        'page_title': f'{program.name} - Applications',
    }

    return render(request, 'programs/program_applications.html', context)

@login_required
def program_apply(request, pk):
    """Apply to a program"""
    program = get_object_or_404(Program, pk=pk)

    if not program.is_accepting_applications:
        messages.error(request, 'This program is not accepting applications.')
        return redirect('programs:program_detail', pk=program.pk)

    # Get or create household for user
    try:
        household = request.user.household
    except:
        messages.error(request, 'You need to be associated with a household to apply.')
        return redirect('programs:program_detail', pk=program.pk)

    # Check if already applied
    if ProgramApplication.objects.filter(program=program, household=household).exists():
        messages.warning(request, 'You have already applied to this program.')
        return redirect('programs:program_detail', pk=program.pk)

    if request.method == 'POST':
        motivation_letter = request.POST.get('motivation_letter', '')
        additional_notes = request.POST.get('additional_notes', '')

        application = ProgramApplication.objects.create(
            program=program,
            household=household,
            motivation_letter=motivation_letter,
            additional_notes=additional_notes,
        )

        messages.success(request, 'Your application has been submitted successfully!')
        return redirect('programs:program_detail', pk=program.pk)

    context = {
        'program': program,
        'page_title': f'Apply to {program.name}',
    }

    return render(request, 'programs/program_apply.html', context)

@login_required
def my_applications(request):
    """View user's applications"""
    applications = []

    try:
        household = request.user.household
        applications = ProgramApplication.objects.filter(household=household).order_by('-application_date')
    except:
        pass

    context = {
        'applications': applications,
        'page_title': 'My Applications',
    }

    return render(request, 'programs/my_applications.html', context)

@login_required
def program_delete(request, pk):
    """Delete program (Superusers and ICT Admins only)"""
    program = get_object_or_404(Program, pk=pk)

    user_role = getattr(request.user, 'role', None)
    if not (request.user.is_superuser or user_role == 'ict_admin'):
        messages.error(request, 'You do not have permission to delete programs.')
        return redirect('programs:program_detail', pk=program.pk)

    if request.method == 'POST':
        program_name = program.name
        program.delete()
        messages.success(request, f'Program "{program_name}" has been deleted successfully!')
        return redirect('programs:program_list')

    # Count related objects that will be affected
    applications_count = program.applications.count()
    business_groups_count = getattr(program, 'businessgroup_set', None)
    if business_groups_count:
        business_groups_count = business_groups_count.count()
    else:
        business_groups_count = 0

    context = {
        'program': program,
        'applications_count': applications_count,
        'business_groups_count': business_groups_count,
        'page_title': f'Delete Program - {program.name}',
    }
    return render(request, 'programs/program_delete.html', context)

@login_required
def program_edit(request, pk):
    """Edit program (County Executives, ICT Admins, Superusers, and program creators)"""
    program = get_object_or_404(Program, pk=pk)

    user_role = getattr(request.user, 'role', None)
    if not (request.user.is_superuser or
            request.user == program.created_by or
            user_role in ['ict_admin', 'county_executive']):
        messages.error(request, 'You do not have permission to edit this program.')
        return redirect('programs:program_detail', pk=program.pk)

    if request.method == 'POST':
        # Update program fields
        program.name = request.POST.get('name', program.name)
        program.description = request.POST.get('description', program.description)
        program.program_type = request.POST.get('program_type', program.program_type)
        program.budget = request.POST.get('budget') or program.budget
        program.target_beneficiaries = request.POST.get('target_beneficiaries') or program.target_beneficiaries
        program.eligibility_criteria = request.POST.get('eligibility_criteria', program.eligibility_criteria)
        program.application_requirements = request.POST.get('application_requirements', program.application_requirements)

        program.save()
        messages.success(request, f'Program "{program.name}" updated successfully!')
        return redirect('programs:program_detail', pk=program.pk)

    context = {
        'program': program,
        'program_types': Program.PROGRAM_TYPE_CHOICES,
        'page_title': f'Edit {program.name}',
    }

    return render(request, 'programs/program_edit.html', context)

@login_required
def program_toggle_status(request, pk):
    """Toggle program status between active/paused/ended"""
    program = get_object_or_404(Program, pk=pk)

    user_role = getattr(request.user, 'role', None)
    if not (request.user.is_superuser or
            request.user == program.created_by or
            user_role in ['ict_admin', 'county_executive']):
        messages.error(request, 'You do not have permission to change program status.')
        return redirect('programs:program_detail', pk=program.pk)

    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in ['active', 'paused', 'ended', 'draft']:
            old_status = program.get_status_display()
            program.status = new_status
            program.save()
            messages.success(request, f'Program status changed from {old_status} to {program.get_status_display()}')
        else:
            messages.error(request, 'Invalid status provided.')

    return redirect('programs:program_detail', pk=program.pk)


@login_required
def approve_application(request, application_id):
    """Approve a program application"""
    from django.utils import timezone

    user_role = getattr(request.user, 'role', None)
    if not (request.user.is_superuser or user_role in ['county_executive', 'ict_admin', 'me_staff']):
        return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)

    application = get_object_or_404(ProgramApplication, id=application_id)

    if request.method == 'POST':
        try:
            application.status = 'approved'
            application.reviewed_by = request.user
            application.reviewed_at = timezone.now()
            application.save()

            # Create program beneficiary entry
            ProgramBeneficiary.objects.get_or_create(
                program=application.program,
                household=application.household,
                defaults={
                    'enrollment_date': timezone.now().date(),
                    'status': 'active'
                }
            )

            return JsonResponse({
                'success': True,
                'message': f'Application for {application.household.name} has been approved'
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=400)


@login_required
def reject_application(request, application_id):
    """Reject a program application"""
    from django.utils import timezone

    user_role = getattr(request.user, 'role', None)
    if not (request.user.is_superuser or user_role in ['county_executive', 'ict_admin', 'me_staff']):
        return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)

    application = get_object_or_404(ProgramApplication, id=application_id)

    if request.method == 'POST':
        try:
            application.status = 'rejected'
            application.reviewed_by = request.user
            application.reviewed_at = timezone.now()
            application.rejection_reason = request.POST.get('reason', '')
            application.save()

            return JsonResponse({
                'success': True,
                'message': f'Application for {application.household.name} has been rejected'
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=400)
