from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
import json
from .models import Training, TrainingAttendance
from households.models import Household

@login_required
def training_list(request):
    """Training Sessions list view with role-based filtering"""
    user = request.user

    # Filter trainings based on user role
    if user.is_superuser or user.role in ['ict_admin', 'me_staff', 'field_associate']:
        # Full access to all trainings
        training_sessions = Training.objects.all()
    elif user.role == 'mentor':
        # Mentors only see trainings they're assigned to
        training_sessions = Training.objects.filter(assigned_mentor=user)
    else:
        # Other roles have no access to trainings
        training_sessions = Training.objects.none()

    training_sessions = training_sessions.order_by('-created_at')

    context = {
        'training_sessions': training_sessions,
        'page_title': 'Training Sessions',
        'total_count': training_sessions.count(),
    }

    return render(request, 'training/training_list.html', context)

@login_required
def training_details(request, training_id):
    """Training details page"""
    training = get_object_or_404(Training, id=training_id)

    # Check permissions
    user = request.user
    if not (user.is_superuser or user.role in ['ict_admin', 'me_staff', 'field_associate'] or
            (user.role == 'mentor' and training.assigned_mentor == user)):
        return HttpResponseForbidden()

    # Get related data
    attendances = training.attendances.select_related('household__village', 'marked_by').order_by('household__name')

    # Calculate training statistics
    total_enrolled = attendances.count()
    present_count = attendances.filter(attendance=True).count()
    absent_count = total_enrolled - present_count
    attendance_rate = round((present_count * 100) / total_enrolled) if total_enrolled > 0 else 0
    enrollment_rate = round((total_enrolled * 100) / training.max_households) if training.max_households > 0 else 0

    # Get recent activity (last 10 attendance changes)
    recent_activity = attendances.filter(attendance_marked_at__isnull=False).order_by('-attendance_marked_at')[:10]

    context = {
        'training': training,
        'attendances': attendances,
        'page_title': f'Training Details - {training.name}',
        'total_enrolled': total_enrolled,
        'present_count': present_count,
        'absent_count': absent_count,
        'attendance_rate': attendance_rate,
        'enrollment_rate': enrollment_rate,
        'recent_activity': recent_activity,
    }

    return render(request, 'training/training_details.html', context)

@login_required
@require_http_methods(["POST"])
def start_training(request, training_id):
    """AJAX endpoint to start a training"""
    training = get_object_or_404(Training, id=training_id)

    # Check permissions
    user = request.user
    if not (user.is_superuser or user.role in ['ict_admin', 'me_staff'] or
            (user.role == 'mentor' and training.assigned_mentor == user)):
        return JsonResponse({'success': False, 'message': 'Permission denied'})

    if training.status != 'planned':
        return JsonResponse({'success': False, 'message': 'Training can only be started if it is in planned status'})

    training.status = 'active'
    if not training.start_date:
        training.start_date = timezone.now().date()
    training.save()

    return JsonResponse({'success': True, 'message': 'Training started successfully'})

@login_required
@require_http_methods(["POST"])
def complete_training(request, training_id):
    """AJAX endpoint to complete a training"""
    training = get_object_or_404(Training, id=training_id)

    # Check permissions
    user = request.user
    if not (user.is_superuser or user.role in ['ict_admin', 'me_staff'] or
            (user.role == 'mentor' and training.assigned_mentor == user)):
        return JsonResponse({'success': False, 'message': 'Permission denied'})

    if training.status != 'active':
        return JsonResponse({'success': False, 'message': 'Training can only be completed if it is active'})

    training.status = 'completed'
    if not training.end_date:
        training.end_date = timezone.now().date()
    training.save()

    return JsonResponse({'success': True, 'message': 'Training completed successfully'})

@login_required
@require_http_methods(["DELETE"])
def delete_training(request, training_id):
    """AJAX endpoint to delete a training"""
    training = get_object_or_404(Training, id=training_id)

    # Check permissions - only admin roles can delete
    user = request.user
    if not (user.is_superuser or user.role in ['ict_admin', 'me_staff']):
        return JsonResponse({'success': False, 'message': 'Permission denied'})

    # Check if training has attendances
    if training.attendances.exists():
        return JsonResponse({'success': False, 'message': 'Cannot delete training with existing attendance records'})

    training_name = training.name
    training.delete()

    return JsonResponse({'success': True, 'message': f'Training "{training_name}" deleted successfully'})

@login_required
def manage_attendance(request, training_id):
    """Training attendance management interface with daily attendance support"""
    from datetime import datetime, timedelta

    training = get_object_or_404(Training, id=training_id)

    # Check permissions
    user = request.user
    if not (user.is_superuser or user.role in ['ict_admin', 'me_staff', 'field_associate'] or
            (user.role == 'mentor' and training.assigned_mentor == user)):
        return HttpResponseForbidden()

    # Get selected date from request or use today's date
    selected_date_str = request.GET.get('date')
    if selected_date_str:
        try:
            selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
        except ValueError:
            selected_date = timezone.now().date()
    else:
        selected_date = timezone.now().date()

    # Get training dates - if training_dates is set, use it; otherwise use start_date
    training_dates = []
    if training.training_dates and isinstance(training.training_dates, list):
        training_dates = [datetime.strptime(d, '%Y-%m-%d').date() if isinstance(d, str) else d for d in training.training_dates]
    elif training.start_date:
        # Generate dates from start to end (or just start date if no end date)
        if training.end_date:
            current_date = training.start_date
            while current_date <= training.end_date:
                training_dates.append(current_date)
                current_date += timedelta(days=1)
        else:
            training_dates = [training.start_date]

    # If no dates configured, use current date
    if not training_dates:
        training_dates = [timezone.now().date()]

    # If selected date not in training dates and training has started, add it
    if selected_date not in training_dates and training.status in ['active', 'completed']:
        training_dates.append(selected_date)
        training_dates.sort()

    # Filter attendances for the selected date
    attendances = training.attendances.filter(training_date=selected_date).select_related('household__village', 'marked_by').order_by('household__name')

    # Get unique households enrolled (from all dates)
    enrolled_households = training.attendances.values_list('household', flat=True).distinct()
    total_unique_enrolled = len(set(enrolled_households))

    # Calculate attendance statistics for selected date
    total_enrolled = attendances.count()
    present_count = attendances.filter(attendance=True).count()
    absent_count = total_enrolled - present_count
    attendance_rate = round((present_count * 100) / total_enrolled) if total_enrolled > 0 else 0

    context = {
        'training': training,
        'attendances': attendances,
        'page_title': f'Manage Attendance - {training.name}',
        'total_enrolled': total_enrolled,
        'total_unique_enrolled': total_unique_enrolled,
        'present_count': present_count,
        'absent_count': absent_count,
        'attendance_rate': attendance_rate,
        'selected_date': selected_date,
        'training_dates': sorted(training_dates),
    }

    return render(request, 'training/manage_attendance.html', context)

@login_required
@require_http_methods(["POST"])
def create_training(request):
    """Create a new training session"""
    user = request.user

    # Check permissions - mentors can now create/schedule trainings
    if not (user.is_superuser or user.role in ['ict_admin', 'me_staff', 'field_associate', 'mentor']):
        return JsonResponse({'success': False, 'message': 'Permission denied'})

    try:
        # Extract form data
        name = request.POST.get('name', '').strip()
        module_id = request.POST.get('module_id', '').strip()
        bm_cycle_id = request.POST.get('bm_cycle')
        assigned_mentor_id = request.POST.get('assigned_mentor')
        start_date = request.POST.get('start_date')
        max_households = request.POST.get('max_households', 25)
        time_taken = request.POST.get('time_taken')
        status = request.POST.get('status', 'planned')
        description = request.POST.get('description', '').strip()

        # Validation
        errors = {}
        if not name:
            errors['name'] = ['Training name is required']
        if not module_id:
            errors['module_id'] = ['Module ID is required']

        # Validate BM Cycle exists if provided
        bm_cycle = None
        if bm_cycle_id:
            try:
                from core.models import BusinessMentorCycle
                bm_cycle = BusinessMentorCycle.objects.get(id=bm_cycle_id)
            except BusinessMentorCycle.DoesNotExist:
                errors['bm_cycle'] = ['Invalid BM Cycle selected']

        # Validate mentor exists if provided
        assigned_mentor = None
        if assigned_mentor_id:
            try:
                from django.contrib.auth import get_user_model
                User = get_user_model()
                assigned_mentor = User.objects.get(id=assigned_mentor_id, role='mentor')
            except User.DoesNotExist:
                errors['assigned_mentor'] = ['Invalid mentor selected']

        # Validate max households
        try:
            max_households = int(max_households)
            if max_households < 1 or max_households > 50:
                errors['max_households'] = ['Max households must be between 1 and 50']
        except (ValueError, TypeError):
            errors['max_households'] = ['Invalid number for max households']

        # Validate duration if provided
        time_taken_obj = None
        if time_taken:
            try:
                from datetime import timedelta
                # Expected format: "HH:MM:SS"
                parts = time_taken.split(':')
                hours = int(parts[0])
                minutes = int(parts[1]) if len(parts) > 1 else 0
                seconds = int(parts[2]) if len(parts) > 2 else 0
                time_taken_obj = timedelta(hours=hours, minutes=minutes, seconds=seconds)
            except (ValueError, IndexError):
                errors['time_taken'] = ['Invalid duration format']

        # Validate start date if provided
        start_date_obj = None
        if start_date:
            try:
                from datetime import datetime
                start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
            except ValueError:
                errors['start_date'] = ['Invalid date format']

        if errors:
            return JsonResponse({'success': False, 'errors': errors})

        # Create training
        training = Training.objects.create(
            name=name,
            module_id=module_id,
            bm_cycle=bm_cycle,
            assigned_mentor=assigned_mentor,
            time_taken=time_taken_obj,
            description=description,
            status=status,
            start_date=start_date_obj,
            max_households=max_households
        )

        return JsonResponse({
            'success': True,
            'message': f'Training "{training.name}" created successfully',
            'training_id': training.id
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error creating training: {str(e)}'
        })


@login_required
def edit_training(request, training_id):
    """Edit an existing training session"""
    training = get_object_or_404(Training, id=training_id)
    user = request.user

    # Check permissions - mentors can edit trainings they're assigned to
    if not (user.is_superuser or user.role in ['ict_admin', 'me_staff', 'field_associate'] or
            (user.role == 'mentor' and training.assigned_mentor == user)):
        return JsonResponse({'success': False, 'message': 'Permission denied'})

    if request.method == 'GET':
        # Return training data for the edit form
        from core.models import BusinessMentorCycle, Mentor
        from django.contrib.auth import get_user_model
        User = get_user_model()

        # Get available options for form
        bm_cycles = BusinessMentorCycle.objects.all()
        mentors = User.objects.filter(role='mentor')

        # Calculate training statistics
        total_enrolled = training.attendances.count()
        present_count = training.attendances.filter(attendance=True).count()
        completion_rate = round((total_enrolled * 100) / training.max_households) if training.max_households > 0 else 0

        context = {
            'training': training,
            'bm_cycles': bm_cycles,
            'mentors': mentors,
            'page_title': f'Edit Training - {training.name}',
            'present_count': present_count,
            'completion_rate': completion_rate,
        }
        return render(request, 'training/edit_training.html', context)

    elif request.method == 'POST':
        try:
            # Extract form data
            name = request.POST.get('name', '').strip()
            module_id = request.POST.get('module_id', '').strip()
            bm_cycle_id = request.POST.get('bm_cycle')
            assigned_mentor_id = request.POST.get('assigned_mentor')
            start_date = request.POST.get('start_date')
            max_households = request.POST.get('max_households', 25)
            time_taken = request.POST.get('time_taken')
            status = request.POST.get('status', training.status)
            description = request.POST.get('description', '').strip()
            module_number = request.POST.get('module_number')
            duration_hours = request.POST.get('duration_hours')
            location = request.POST.get('location', '').strip()
            participant_count = request.POST.get('participant_count')

            # Validation
            errors = {}
            if not name:
                errors['name'] = ['Training name is required']
            if not module_id:
                errors['module_id'] = ['Module ID is required']

            # Validate BM Cycle exists if provided
            bm_cycle = None
            if bm_cycle_id:
                try:
                    from core.models import BusinessMentorCycle
                    bm_cycle = BusinessMentorCycle.objects.get(id=bm_cycle_id)
                except BusinessMentorCycle.DoesNotExist:
                    errors['bm_cycle'] = ['Invalid BM Cycle selected']

            # Validate mentor exists if provided
            assigned_mentor = None
            if assigned_mentor_id:
                try:
                    from django.contrib.auth import get_user_model
                    User = get_user_model()
                    assigned_mentor = User.objects.get(id=assigned_mentor_id, role='mentor')
                except User.DoesNotExist:
                    errors['assigned_mentor'] = ['Invalid mentor selected']

            # Validate max households
            try:
                max_households = int(max_households)
                if max_households < 1 or max_households > 50:
                    errors['max_households'] = ['Max households must be between 1 and 50']
            except (ValueError, TypeError):
                errors['max_households'] = ['Invalid number for max households']

            # Validate duration if provided
            time_taken_obj = None
            if time_taken:
                try:
                    from datetime import timedelta
                    # Expected format: "HH:MM:SS"
                    parts = time_taken.split(':')
                    hours = int(parts[0])
                    minutes = int(parts[1]) if len(parts) > 1 else 0
                    seconds = int(parts[2]) if len(parts) > 2 else 0
                    time_taken_obj = timedelta(hours=hours, minutes=minutes, seconds=seconds)
                except (ValueError, IndexError):
                    errors['time_taken'] = ['Invalid duration format']

            # Validate start date if provided
            start_date_obj = None
            if start_date:
                try:
                    from datetime import datetime
                    start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
                except ValueError:
                    errors['start_date'] = ['Invalid date format']

            # Validate module number if provided
            module_number_obj = None
            if module_number:
                try:
                    module_number_obj = int(module_number)
                except ValueError:
                    errors['module_number'] = ['Module number must be a valid integer']

            # Validate duration hours if provided
            duration_hours_obj = None
            if duration_hours:
                try:
                    duration_hours_obj = float(duration_hours)
                except ValueError:
                    errors['duration_hours'] = ['Duration hours must be a valid number']

            # Validate participant count if provided
            participant_count_obj = None
            if participant_count:
                try:
                    participant_count_obj = int(participant_count)
                except ValueError:
                    errors['participant_count'] = ['Participant count must be a valid integer']

            if errors:
                return JsonResponse({'success': False, 'errors': errors})

            # Update training
            training.name = name
            training.module_id = module_id
            training.bm_cycle = bm_cycle
            training.assigned_mentor = assigned_mentor
            training.time_taken = time_taken_obj
            training.description = description
            training.status = status
            training.start_date = start_date_obj
            training.max_households = max_households
            training.module_number = module_number_obj
            training.duration_hours = duration_hours_obj
            training.location = location
            training.participant_count = participant_count_obj
            training.save()

            return JsonResponse({
                'success': True,
                'message': f'Training "{training.name}" updated successfully',
                'training_id': training.id
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error updating training: {str(e)}'
            })


@login_required
def get_available_households(request, training_id):
    """Get list of households available to add to training"""
    training = get_object_or_404(Training, id=training_id)

    # Check permissions
    user = request.user
    if not (user.is_superuser or user.role in ['ict_admin', 'me_staff', 'field_associate'] or
            (user.role == 'mentor' and training.assigned_mentor == user)):
        return JsonResponse({'success': False, 'message': 'Permission denied'})

    # Get households that are not already in this training
    enrolled_household_ids = training.attendances.values_list('household_id', flat=True)
    available_households = Household.objects.exclude(id__in=enrolled_household_ids).select_related('village')

    households_data = []
    for household in available_households:
        households_data.append({
            'id': household.id,
            'name': household.name,
            'village': household.village.name,
            'phone': household.phone_number
        })

    return JsonResponse({
        'success': True,
        'households': households_data
    })


@login_required
@require_http_methods(["POST"])
def add_household_to_training(request, training_id):
    """Add a household to training attendance"""
    training = get_object_or_404(Training, id=training_id)

    # Check permissions
    user = request.user
    if not (user.is_superuser or user.role in ['ict_admin', 'me_staff', 'field_associate'] or
            (user.role == 'mentor' and training.assigned_mentor == user)):
        return JsonResponse({'success': False, 'message': 'Permission denied'})

    try:
        household_id = request.POST.get('household_id')
        training_date = request.POST.get('training_date')

        if not household_id:
            return JsonResponse({'success': False, 'message': 'Household is required'})

        if not training_date:
            return JsonResponse({'success': False, 'message': 'Training date is required'})

        # Validate household exists
        from households.models import Household
        household = get_object_or_404(Household, id=household_id)

        # Check if household is already in this training
        if training.attendances.filter(household=household).exists():
            return JsonResponse({'success': False, 'message': 'Household already enrolled in this training'})

        # Check training capacity
        if training.max_households and training.attendances.count() >= training.max_households:
            return JsonResponse({'success': False, 'message': 'Training is at maximum capacity'})

        # Parse training date
        from datetime import datetime, timedelta
        training_date_obj = datetime.strptime(training_date, '%Y-%m-%d').date()

        # Create attendance record for the selected date
        attendance = TrainingAttendance.objects.create(
            training=training,
            household=household,
            training_date=training_date_obj,
            attendance=True,  # Default to present for current date
            marked_by=user,
            attendance_marked_at=timezone.now()
        )

        # Automatically mark absent for all previous training dates
        absent_records_created = 0
        if training.start_date and training_date_obj > training.start_date:
            current_date = training.start_date
            while current_date < training_date_obj:
                # Only create if within training period
                if not training.end_date or current_date <= training.end_date:
                    # Check if attendance record already exists for this date
                    if not training.attendances.filter(household=household, training_date=current_date).exists():
                        TrainingAttendance.objects.create(
                            training=training,
                            household=household,
                            training_date=current_date,
                            attendance=False,  # Mark as absent for past dates
                            marked_by=user,
                            attendance_marked_at=timezone.now()
                        )
                        absent_records_created += 1
                current_date += timedelta(days=1)

        message = f'Household "{household.name}" added to training successfully'
        if absent_records_created > 0:
            message += f'. Automatically marked absent for {absent_records_created} previous date(s).'

        return JsonResponse({
            'success': True,
            'message': message,
            'attendance_id': attendance.id,
            'absent_records_created': absent_records_created
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error adding household: {str(e)}'
        })


@login_required
@require_http_methods(["POST"])
def toggle_attendance(request, attendance_id):
    """Toggle attendance status for a household"""
    attendance = get_object_or_404(TrainingAttendance, id=attendance_id)

    # Check permissions
    user = request.user
    if not (user.is_superuser or user.role in ['ict_admin', 'me_staff', 'field_associate'] or
            (user.role == 'mentor' and attendance.training.assigned_mentor == user)):
        return JsonResponse({'success': False, 'message': 'Permission denied'})

    try:
        new_attendance = request.POST.get('attendance') == 'true'
        attendance.attendance = new_attendance
        attendance.marked_by = user
        attendance.attendance_marked_at = timezone.now()
        attendance.save()

        return JsonResponse({
            'success': True,
            'message': f'Attendance updated for {attendance.household.name}',
            'attendance': new_attendance
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error updating attendance: {str(e)}'
        })


@login_required
@require_http_methods(["DELETE"])
def remove_attendance(request, attendance_id):
    """Remove a household from training attendance"""
    attendance = get_object_or_404(TrainingAttendance, id=attendance_id)

    # Check permissions
    user = request.user
    if not (user.is_superuser or user.role in ['ict_admin', 'me_staff', 'field_associate'] or
            (user.role == 'mentor' and attendance.training.assigned_mentor == user)):
        return JsonResponse({'success': False, 'message': 'Permission denied'})

    try:
        household_name = attendance.household.name
        attendance.delete()

        return JsonResponse({
            'success': True,
            'message': f'Household "{household_name}" removed from training'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error removing household: {str(e)}'
        })