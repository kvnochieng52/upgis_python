"""
Core views for UPG System
Includes ESR import functionality and system utilities
"""

import pandas as pd
import json
from datetime import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.utils import timezone
from .models import ESRImport, ESRImportRecord, BusinessMentorCycle
from households.models import Household
from business_groups.models import BusinessGroup
from savings_groups.models import BusinessSavingsGroup
from django.contrib.auth import get_user_model

User = get_user_model()

@login_required
def esr_import_list(request):
    """List all ESR imports - System Admin only"""
    # Check permissions - only system admin (superuser) or ICT Admin can access ESR imports
    user_role = getattr(request.user, 'role', None)
    if not (request.user.is_superuser or user_role == 'ict_admin'):
        messages.error(request, 'You do not have permission to access ESR import functionality. System administrator access required.')
        return redirect('dashboard:dashboard')
    imports = ESRImport.objects.all().order_by('-started_at')

    # Pagination
    paginator = Paginator(imports, 10)
    page_number = request.GET.get('page')
    imports = paginator.get_page(page_number)

    context = {
        'imports': imports,
        'page_title': 'ESR Import History',
    }
    return render(request, 'core/esr_import_list.html', context)

@login_required
def esr_import_create(request):
    """Create new ESR import - System Admin only"""
    # Check permissions - only system admin (superuser) or ICT Admin can access ESR imports
    user_role = getattr(request.user, 'role', None)
    if not (request.user.is_superuser or user_role == 'ict_admin'):
        messages.error(request, 'You do not have permission to access ESR import functionality. System administrator access required.')
        return redirect('dashboard:dashboard')
    if request.method == 'POST':
        if 'file' not in request.FILES:
            messages.error(request, 'Please select a file to import.')
            return redirect('core:esr_import_create')

        uploaded_file = request.FILES['file']
        import_type = request.POST.get('import_type')

        # Validate file type
        if not uploaded_file.name.endswith(('.csv', '.xlsx', '.xls')):
            messages.error(request, 'Please upload a CSV or Excel file.')
            return redirect('core:esr_import_create')

        # Create ESR import record
        esr_import = ESRImport.objects.create(
            file_name=uploaded_file.name,
            file_path=uploaded_file,
            import_type=import_type,
            imported_by=request.user,
            status='pending'
        )

        # Process the file
        try:
            process_esr_file(esr_import)
            messages.success(request, f'ESR file "{uploaded_file.name}" uploaded and processed successfully!')
        except Exception as e:
            esr_import.status = 'failed'
            esr_import.error_log = str(e)
            esr_import.save()
            messages.error(request, f'Error processing file: {str(e)}')

        return redirect('core:esr_import_detail', pk=esr_import.pk)

    context = {
        'page_title': 'Import ESR Data',
        'import_types': ESRImport.IMPORT_TYPE_CHOICES,
    }
    return render(request, 'core/esr_import_create.html', context)

@login_required
def esr_import_detail(request, pk):
    """ESR import detail view - System Admin only"""
    # Check permissions - only system admin (superuser) or ICT Admin can access ESR imports
    user_role = getattr(request.user, 'role', None)
    if not (request.user.is_superuser or user_role == 'ict_admin'):
        messages.error(request, 'You do not have permission to access ESR import functionality. System administrator access required.')
        return redirect('dashboard:dashboard')
    esr_import = get_object_or_404(ESRImport, pk=pk)
    records = esr_import.records.all()

    # Pagination for records
    paginator = Paginator(records, 50)
    page_number = request.GET.get('page')
    records = paginator.get_page(page_number)

    context = {
        'esr_import': esr_import,
        'records': records,
        'page_title': f'ESR Import - {esr_import.file_name}',
    }
    return render(request, 'core/esr_import_detail.html', context)

def process_esr_file(esr_import):
    """Process uploaded ESR file and import data"""
    esr_import.status = 'processing'
    esr_import.save()

    try:
        # Read the file
        file_path = esr_import.file_path.path
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)

        esr_import.total_records = len(df)
        esr_import.save()

        successful = 0
        failed = 0

        # Process each row
        for index, row in df.iterrows():
            try:
                # Create import record
                import_record = ESRImportRecord.objects.create(
                    esr_import=esr_import,
                    row_number=index + 1,
                    raw_data=row.to_dict(),
                    status='pending'
                )

                # Process based on import type
                if esr_import.import_type == 'household':
                    process_household_record(import_record, row)
                elif esr_import.import_type == 'business_group':
                    process_business_group_record(import_record, row)
                elif esr_import.import_type == 'savings_group':
                    process_savings_group_record(import_record, row)
                else:
                    # Try to auto-detect and process
                    auto_process_record(import_record, row)

                import_record.status = 'processed'
                import_record.processed_at = timezone.now()
                import_record.save()
                successful += 1

            except Exception as e:
                import_record.status = 'failed'
                import_record.error_message = str(e)
                import_record.save()
                failed += 1

        # Update import status
        esr_import.successful_imports = successful
        esr_import.failed_imports = failed
        esr_import.status = 'completed'
        esr_import.completed_at = timezone.now()
        esr_import.import_summary = {
            'total': esr_import.total_records,
            'successful': successful,
            'failed': failed,
            'success_rate': (successful / esr_import.total_records) * 100 if esr_import.total_records > 0 else 0
        }
        esr_import.save()

    except Exception as e:
        esr_import.status = 'failed'
        esr_import.error_log = str(e)
        esr_import.completed_at = timezone.now()
        esr_import.save()
        raise

def process_household_record(import_record, row):
    """Process household data from ESR"""
    # Map ESR fields to UPG Household fields
    mapped_data = {}

    # Common ESR field mappings
    field_mapping = {
        'household_name': 'name',
        'household_head': 'name',
        'name': 'name',
        'national_id': 'national_id',
        'phone': 'phone_number',
        'phone_number': 'phone_number',
        'disability': 'disability',
        'village': 'village_name',
        'village_name': 'village_name',
    }

    for esr_field, upg_field in field_mapping.items():
        if esr_field in row.index and pd.notna(row[esr_field]):
            mapped_data[upg_field] = row[esr_field]

    import_record.mapped_data = mapped_data
    import_record.save()

    # Create household if doesn't exist
    if 'name' in mapped_data:
        household, created = Household.objects.get_or_create(
            name=mapped_data['name'],
            defaults={
                'national_id': mapped_data.get('national_id', ''),
                'phone_number': mapped_data.get('phone_number', ''),
                'disability': mapped_data.get('disability', False),
            }
        )

        import_record.created_object_type = 'Household'
        import_record.created_object_id = str(household.id)
        import_record.save()

def process_business_group_record(import_record, row):
    """Process business group data from ESR"""
    mapped_data = {}

    # Business group field mappings
    field_mapping = {
        'group_name': 'name',
        'business_group_name': 'name',
        'name': 'name',
        'business_type': 'business_type',
        'formation_date': 'formation_date',
        'group_size': 'group_size',
    }

    for esr_field, upg_field in field_mapping.items():
        if esr_field in row.index and pd.notna(row[esr_field]):
            mapped_data[upg_field] = row[esr_field]

    import_record.mapped_data = mapped_data
    import_record.save()

    # Create business group if doesn't exist
    if 'name' in mapped_data:
        business_group, created = BusinessGroup.objects.get_or_create(
            name=mapped_data['name'],
            defaults={
                'business_type': mapped_data.get('business_type', 'crop'),
                'group_size': mapped_data.get('group_size', 2),
            }
        )

        import_record.created_object_type = 'BusinessGroup'
        import_record.created_object_id = str(business_group.id)
        import_record.save()

def process_savings_group_record(import_record, row):
    """Process savings group data from ESR"""
    mapped_data = {}

    # Savings group field mappings
    field_mapping = {
        'group_name': 'name',
        'savings_group_name': 'name',
        'name': 'name',
        'formation_date': 'formation_date',
        'target_members': 'target_members',
        'total_savings': 'total_savings',
    }

    for esr_field, upg_field in field_mapping.items():
        if esr_field in row.index and pd.notna(row[esr_field]):
            mapped_data[upg_field] = row[esr_field]

    import_record.mapped_data = mapped_data
    import_record.save()

    # Create savings group if doesn't exist
    if 'name' in mapped_data:
        savings_group, created = BusinessSavingsGroup.objects.get_or_create(
            name=mapped_data['name'],
            defaults={
                'target_members': mapped_data.get('target_members', 20),
            }
        )

        import_record.created_object_type = 'BusinessSavingsGroup'
        import_record.created_object_id = str(savings_group.id)
        import_record.save()

def auto_process_record(import_record, row):
    """Auto-detect and process mixed ESR data"""
    # Try to determine what type of data this is based on columns
    columns = [col.lower() for col in row.index]

    if any(col in columns for col in ['household_name', 'household_head']):
        process_household_record(import_record, row)
    elif any(col in columns for col in ['business_group_name', 'group_name']):
        if any(col in columns for col in ['savings', 'total_savings']):
            process_savings_group_record(import_record, row)
        else:
            process_business_group_record(import_record, row)
    else:
        # Default to household
        process_household_record(import_record, row)


# API Endpoints for AJAX calls

@login_required
def api_bm_cycles(request):
    """API endpoint to get BM cycles for dropdowns"""
    user = request.user

    # Check permissions
    if not (user.is_superuser or user.role in ['ict_admin', 'me_staff', 'field_associate', 'mentor']):
        return JsonResponse({'error': 'Permission denied'}, status=403)

    cycles = BusinessMentorCycle.objects.all().order_by('bm_cycle_name')

    # Apply role-based filtering if needed
    if user.role == 'mentor':
        # Mentors only see cycles they're involved in
        cycles = cycles.filter(assigned_mentor=user)
    elif user.role == 'field_associate':
        # Field associates see cycles in their assigned villages
        if hasattr(user, 'profile') and user.profile:
            assigned_villages = user.profile.assigned_villages.all()
            cycles = cycles.filter(village__in=assigned_villages)

    data = [
        {
            'id': cycle.id,
            'bm_cycle_name': cycle.bm_cycle_name,
            'village': cycle.village.name if cycle.village else 'N/A'
        }
        for cycle in cycles
    ]

    return JsonResponse(data, safe=False)

@login_required
def api_mentors(request):
    """API endpoint to get mentors for dropdowns"""
    user = request.user

    # Check permissions
    if not (user.is_superuser or user.role in ['ict_admin', 'me_staff', 'field_associate']):
        return JsonResponse({'error': 'Permission denied'}, status=403)

    mentors = User.objects.filter(role='mentor', is_active=True).order_by('first_name', 'last_name')

    # Apply role-based filtering if needed
    if user.role == 'field_associate':
        # Field associates can only assign mentors in their villages
        if hasattr(user, 'profile') and user.profile:
            assigned_villages = user.profile.assigned_villages.all()
            mentors = mentors.filter(profile__assigned_villages__in=assigned_villages).distinct()

    data = [
        {
            'id': mentor.id,
            'full_name': mentor.get_full_name() or mentor.username,
            'username': mentor.username,
            'villages': [v.name for v in mentor.profile.assigned_villages.all()] if hasattr(mentor, 'profile') and mentor.profile else []
        }
        for mentor in mentors
    ]

    return JsonResponse(data, safe=False)


@login_required
def assign_mentor_to_village(request):
    """Field associates assign mentors to villages"""
    user = request.user
    user_role = getattr(user, 'role', None)

    # Only field associates and admins can assign mentors
    if not (user.is_superuser or user_role in ['field_associate', 'ict_admin', 'me_staff']):
        messages.error(request, 'You do not have permission to assign mentors.')
        return redirect('dashboard:dashboard')

    # Get villages - field associates see only their assigned villages
    from .models import Village
    if user_role == 'field_associate':
        if hasattr(user, 'profile') and user.profile:
            villages = user.profile.assigned_villages.all()
        else:
            villages = Village.objects.none()
    else:
        villages = Village.objects.all().select_related('subcounty_obj')

    # Get mentors
    mentors = User.objects.filter(role='mentor').select_related('profile')

    if request.method == 'POST':
        mentor_id = request.POST.get('mentor_id')
        village_ids = request.POST.getlist('village_ids[]')

        if not mentor_id or not village_ids:
            messages.error(request, 'Please select a mentor and at least one village.')
            return redirect('core:assign_mentor_to_village')

        try:
            mentor = User.objects.get(id=mentor_id, role='mentor')

            # Get or create profile
            from accounts.models import UserProfile
            profile, created = UserProfile.objects.get_or_create(user=mentor)

            # Assign villages
            selected_villages = Village.objects.filter(id__in=village_ids)
            profile.assigned_villages.add(*selected_villages)

            village_names = ', '.join([v.name for v in selected_villages])
            messages.success(
                request,
                f'Successfully assigned {mentor.get_full_name()} to {len(selected_villages)} village(s): {village_names}'
            )
            return redirect('core:assign_mentor_to_village')

        except User.DoesNotExist:
            messages.error(request, 'Selected mentor not found.')
        except Exception as e:
            messages.error(request, f'Error assigning mentor: {str(e)}')

    context = {
        'page_title': 'Assign Mentor to Villages',
        'villages': villages.order_by('subcounty_obj__name', 'name'),
        'mentors': mentors.order_by('first_name', 'last_name'),
    }
    return render(request, 'core/assign_mentor.html', context)


@login_required
def mentor_villages_list(request):
    """View all mentor-village assignments"""
    user = request.user
    user_role = getattr(user, 'role', None)

    if not (user.is_superuser or user_role in ['field_associate', 'ict_admin', 'me_staff']):
        messages.error(request, 'You do not have permission to view mentor assignments.')
        return redirect('dashboard:dashboard')

    # Get all mentors with their assigned villages
    mentors = User.objects.filter(role='mentor').select_related('profile').prefetch_related('profile__assigned_villages__subcounty_obj')

    # Filter for field associates
    if user_role == 'field_associate':
        if hasattr(user, 'profile') and user.profile:
            assigned_villages = user.profile.assigned_villages.all()
            mentors = mentors.filter(profile__assigned_villages__in=assigned_villages).distinct()

    context = {
        'page_title': 'Mentor-Village Assignments',
        'mentors': mentors,
    }
    return render(request, 'core/mentor_villages_list.html', context)


@login_required
def remove_mentor_village(request, mentor_id, village_id):
    """Remove a village from a mentor's assignment"""
    user = request.user
    user_role = getattr(user, 'role', None)

    if not (user.is_superuser or user_role in ['field_associate', 'ict_admin', 'me_staff']):
        messages.error(request, 'You do not have permission to modify mentor assignments.')
        return redirect('dashboard:dashboard')

    try:
        from .models import Village
        mentor = User.objects.get(id=mentor_id, role='mentor')
        village = Village.objects.get(id=village_id)

        # Check if field associate has permission for this village
        if user_role == 'field_associate':
            if hasattr(user, 'profile') and user.profile:
                if village not in user.profile.assigned_villages.all():
                    messages.error(request, 'You do not have permission to modify this village assignment.')
                    return redirect('core:mentor_villages_list')

        if hasattr(mentor, 'profile') and mentor.profile:
            mentor.profile.assigned_villages.remove(village)
            messages.success(
                request,
                f'Removed {village.name} from {mentor.get_full_name()}\'s assignments.'
            )
        else:
            messages.error(request, 'Mentor profile not found.')

    except (User.DoesNotExist, Village.DoesNotExist):
        messages.error(request, 'Mentor or village not found.')
    except Exception as e:
        messages.error(request, f'Error removing assignment: {str(e)}')

    return redirect('core:mentor_villages_list')


@login_required
def bm_cycle_list(request):
    """List all BM Cycles"""
    user = request.user
    user_role = getattr(user, 'role', None)

    if not (user.is_superuser or user_role in ['ict_admin', 'me_staff', 'field_associate']):
        messages.error(request, 'You do not have permission to manage BM Cycles.')
        return redirect('dashboard:dashboard')

    cycles = BusinessMentorCycle.objects.all().select_related('business_mentor').order_by('-created_at')

    context = {
        'page_title': 'Business Mentor Cycles',
        'cycles': cycles,
    }
    return render(request, 'core/bm_cycle_list.html', context)


@login_required
def bm_cycle_create(request):
    """Create a new BM Cycle"""
    user = request.user
    user_role = getattr(user, 'role', None)

    if not (user.is_superuser or user_role in ['ict_admin', 'me_staff', 'field_associate']):
        messages.error(request, 'You do not have permission to create BM Cycles.')
        return redirect('dashboard:dashboard')

    if request.method == 'POST':
        try:
            from .models import Mentor

            bm_cycle_name = request.POST.get('bm_cycle_name')
            business_mentor_id = request.POST.get('business_mentor')
            field_associate = request.POST.get('field_associate')
            cycle = request.POST.get('cycle')
            project = request.POST.get('project')
            office = request.POST.get('office')

            business_mentor = Mentor.objects.get(id=business_mentor_id)

            bm_cycle = BusinessMentorCycle.objects.create(
                bm_cycle_name=bm_cycle_name,
                business_mentor=business_mentor,
                field_associate=field_associate,
                cycle=cycle,
                project=project,
                office=office
            )

            messages.success(request, f'BM Cycle "{bm_cycle_name}" created successfully!')
            return redirect('core:bm_cycle_list')

        except Exception as e:
            messages.error(request, f'Error creating BM Cycle: {str(e)}')

    # Get mentors and field associates for dropdowns
    from .models import Mentor
    mentors = Mentor.objects.all().order_by('first_name', 'last_name')
    field_associates = User.objects.filter(role='field_associate').order_by('first_name', 'last_name')

    context = {
        'page_title': 'Create BM Cycle',
        'mentors': mentors,
        'field_associates': field_associates,
        'cycle': None,
    }
    return render(request, 'core/bm_cycle_form.html', context)


@login_required
def bm_cycle_edit(request, cycle_id):
    """Edit an existing BM Cycle"""
    user = request.user
    user_role = getattr(user, 'role', None)

    if not (user.is_superuser or user_role in ['ict_admin', 'me_staff', 'field_associate']):
        messages.error(request, 'You do not have permission to edit BM Cycles.')
        return redirect('dashboard:dashboard')

    cycle = get_object_or_404(BusinessMentorCycle, id=cycle_id)

    if request.method == 'POST':
        try:
            from .models import Mentor

            cycle.bm_cycle_name = request.POST.get('bm_cycle_name')
            cycle.business_mentor = Mentor.objects.get(id=request.POST.get('business_mentor'))
            cycle.field_associate = request.POST.get('field_associate')
            cycle.cycle = request.POST.get('cycle')
            cycle.project = request.POST.get('project')
            cycle.office = request.POST.get('office')
            cycle.save()

            messages.success(request, f'BM Cycle "{cycle.bm_cycle_name}" updated successfully!')
            return redirect('core:bm_cycle_list')

        except Exception as e:
            messages.error(request, f'Error updating BM Cycle: {str(e)}')

    # Get mentors and field associates for dropdowns
    from .models import Mentor
    mentors = Mentor.objects.all().order_by('first_name', 'last_name')
    field_associates = User.objects.filter(role='field_associate').order_by('first_name', 'last_name')

    context = {
        'page_title': 'Edit BM Cycle',
        'cycle': cycle,
        'mentors': mentors,
        'field_associates': field_associates,
    }
    return render(request, 'core/bm_cycle_form.html', context)


@login_required
def bm_cycle_delete(request, cycle_id):
    """Delete a BM Cycle"""
    user = request.user
    user_role = getattr(user, 'role', None)

    if not (user.is_superuser or user_role in ['ict_admin', 'me_staff']):
        messages.error(request, 'You do not have permission to delete BM Cycles.')
        return redirect('dashboard:dashboard')

    try:
        cycle = get_object_or_404(BusinessMentorCycle, id=cycle_id)
        cycle_name = cycle.bm_cycle_name
        cycle.delete()
        messages.success(request, f'BM Cycle "{cycle_name}" deleted successfully!')
    except Exception as e:
        messages.error(request, f'Error deleting BM Cycle: {str(e)}')

    return redirect('core:bm_cycle_list')