from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.http import require_POST
from django.db.models import Q, Count
from django.utils import timezone
from datetime import timedelta
import json

from .models import SystemConfiguration, UserSettings, SystemAuditLog, SystemAlert, UserAlertDismissal, SystemBackup

User = get_user_model()

@login_required
def settings_dashboard(request):
    """System settings dashboard"""
    # Check permissions
    if not (request.user.is_superuser or request.user.role in ['ict_admin', 'me_staff']):
        return HttpResponseForbidden("You do not have permission to access system settings.")

    # Get system statistics
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    inactive_users = total_users - active_users

    # Recent activity (last 7 days)
    week_ago = timezone.now() - timedelta(days=7)
    recent_logins = SystemAuditLog.objects.filter(
        action='login',
        timestamp__gte=week_ago
    ).count()

    # System alerts
    active_alerts = SystemAlert.objects.filter(
        is_active=True,
        show_until__gt=timezone.now()
    ).count()

    # Configuration count
    config_count = SystemConfiguration.objects.count()

    # Last backup
    last_backup = SystemBackup.objects.filter(status='completed').first()

    context = {
        'page_title': 'System Settings',
        'total_users': total_users,
        'active_users': active_users,
        'inactive_users': inactive_users,
        'recent_logins': recent_logins,
        'active_alerts': active_alerts,
        'config_count': config_count,
        'last_backup': last_backup,
        'system_version': '1.0.0',
    }
    return render(request, 'settings_module/settings_dashboard.html', context)

@login_required
def user_management(request):
    """User management page"""
    # Check permissions - only ICT admin and superuser can manage users
    if not (request.user.is_superuser or request.user.role == 'ict_admin'):
        messages.error(request, 'You do not have permission to manage users.')
        return redirect('settings:settings_dashboard')

    users = User.objects.all().order_by('-date_joined')

    # Search functionality
    search_query = request.GET.get('search')
    if search_query:
        users = users.filter(
            username__icontains=search_query
        ) | users.filter(
            email__icontains=search_query
        ) | users.filter(
            first_name__icontains=search_query
        ) | users.filter(
            last_name__icontains=search_query
        )

    # Filter by role
    role_filter = request.GET.get('role')
    if role_filter:
        users = users.filter(role=role_filter)

    # Pagination
    paginator = Paginator(users, 10)
    page_number = request.GET.get('page')
    users = paginator.get_page(page_number)

    context = {
        'page_title': 'User Management',
        'users': users,
        'role_choices': User.ROLE_CHOICES,
        'search_query': search_query,
        'selected_role': role_filter,
    }
    return render(request, 'settings_module/user_management.html', context)

@login_required
def user_create(request):
    """Create new user"""
    if not (request.user.is_superuser or request.user.role == 'ict_admin'):
        messages.error(request, 'You do not have permission to create users.')
        return redirect('settings:user_management')

    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        role = request.POST.get('role')
        password = request.POST.get('password')

        if username and email and password:
            try:
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    password=password,
                    role=role
                )
                messages.success(request, f'User "{username}" created successfully!')
                return redirect('settings:user_management')
            except Exception as e:
                messages.error(request, f'Error creating user: {str(e)}')
        else:
            messages.error(request, 'Username, email, and password are required.')

    context = {
        'page_title': 'Create New User',
        'role_choices': User.ROLE_CHOICES,
    }
    return render(request, 'settings_module/user_create.html', context)

@login_required
def user_edit(request, user_id):
    """Edit user"""
    if not (request.user.is_superuser or request.user.role == 'ict_admin'):
        messages.error(request, 'You do not have permission to edit users.')
        return redirect('settings:user_management')

    user = get_object_or_404(User, id=user_id)

    if request.method == 'POST':
        user.username = request.POST.get('username', user.username)
        user.email = request.POST.get('email', user.email)
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.role = request.POST.get('role', user.role)

        new_password = request.POST.get('password')
        if new_password:
            user.set_password(new_password)

        try:
            user.save()
            messages.success(request, f'User "{user.username}" updated successfully!')
            return redirect('settings:user_management')
        except Exception as e:
            messages.error(request, f'Error updating user: {str(e)}')

    context = {
        'page_title': f'Edit User - {user.username}',
        'user_obj': user,
        'role_choices': User.ROLE_CHOICES,
    }
    return render(request, 'settings_module/user_edit.html', context)

@login_required
@require_POST
def user_toggle_status(request, user_id):
    """Toggle user active status"""
    if not (request.user.is_superuser or request.user.role == 'ict_admin'):
        return JsonResponse({'error': 'Permission denied'}, status=403)

    user = get_object_or_404(User, id=user_id)

    # Don't allow deactivating superusers unless request user is also superuser
    if user.is_superuser and not request.user.is_superuser:
        return JsonResponse({'error': 'Cannot modify superuser status'}, status=403)

    # Don't allow users to deactivate themselves
    if user == request.user:
        return JsonResponse({'error': 'Cannot modify your own status'}, status=403)

    user.is_active = not user.is_active
    user.save()

    status = 'activated' if user.is_active else 'deactivated'
    messages.success(request, f'User "{user.username}" has been {status}.')

    return JsonResponse({
        'success': True,
        'status': user.is_active,
        'message': f'User {status} successfully'
    })

@login_required
def user_delete(request, user_id):
    """Delete user"""
    if not (request.user.is_superuser or request.user.role == 'ict_admin'):
        messages.error(request, 'You do not have permission to delete users.')
        return redirect('settings:user_management')

    user = get_object_or_404(User, id=user_id)

    if user == request.user:
        messages.error(request, 'You cannot delete your own account.')
        return redirect('settings:user_management')

    if user.is_superuser and not request.user.is_superuser:
        messages.error(request, 'You cannot delete superuser accounts.')
        return redirect('settings:user_management')

    if request.method == 'POST':
        username = user.username
        user.delete()
        messages.success(request, f'User "{username}" has been deleted.')
        return redirect('settings:user_management')

    context = {
        'page_title': f'Delete User - {user.username}',
        'user_obj': user,
    }
    return render(request, 'settings_module/user_delete.html', context)


# System Configuration Views
@login_required
def system_config(request):
    """System configuration management"""
    if not (request.user.is_superuser or request.user.role == 'ict_admin'):
        return HttpResponseForbidden("You do not have permission to access system configuration.")

    configs = SystemConfiguration.objects.all().order_by('category', 'key')

    # Group configurations by category
    config_groups = {}
    for config in configs:
        if config.category not in config_groups:
            config_groups[config.category] = []
        config_groups[config.category].append(config)

    context = {
        'page_title': 'System Configuration',
        'config_groups': config_groups,
        'total_configs': configs.count(),
    }
    return render(request, 'settings_module/system_config.html', context)


@login_required
def config_edit(request, config_id):
    """Edit system configuration"""
    if not (request.user.is_superuser or request.user.role == 'ict_admin'):
        return HttpResponseForbidden("Permission denied.")

    config = get_object_or_404(SystemConfiguration, id=config_id)

    if not config.is_editable:
        messages.error(request, 'This configuration setting cannot be modified.')
        return redirect('settings:system_config')

    if request.method == 'POST':
        old_value = config.value
        config.value = request.POST.get('value', config.value)
        config.modified_by = request.user

        try:
            config.save()

            # Log the change
            SystemAuditLog.objects.create(
                user=request.user,
                action='update',
                model_name='SystemConfiguration',
                object_id=str(config.id),
                object_repr=str(config),
                changes={'old_value': old_value, 'new_value': config.value},
                success=True
            )

            messages.success(request, f'Configuration "{config.key}" updated successfully!')
            return redirect('settings:system_config')
        except Exception as e:
            messages.error(request, f'Error updating configuration: {str(e)}')

    context = {
        'page_title': f'Edit Configuration - {config.key}',
        'config': config,
    }
    return render(request, 'settings_module/config_edit.html', context)


# User Profile Management
@login_required
def user_settings(request, user_id=None):
    """View/edit user settings"""
    if user_id:
        # Admin viewing/editing another user's settings
        if not (request.user.is_superuser or request.user.role == 'ict_admin'):
            return HttpResponseForbidden("Permission denied.")
        user = get_object_or_404(User, id=user_id)
    else:
        # User viewing/editing their own settings
        user = request.user

    settings_obj, created = UserSettings.objects.get_or_create(user=user)

    if request.method == 'POST':
        # Update profile picture if uploaded
        if 'avatar' in request.FILES:
            user.avatar = request.FILES['avatar']
            try:
                user.save()
                messages.success(request, 'Profile picture updated successfully!')
            except Exception as e:
                messages.error(request, f'Error uploading profile picture: {str(e)}')

        # Update settings
        settings_obj.email_notifications = request.POST.get('email_notifications') == 'on'
        settings_obj.sms_notifications = request.POST.get('sms_notifications') == 'on'
        settings_obj.theme = request.POST.get('theme', settings_obj.theme)
        settings_obj.language = request.POST.get('language', settings_obj.language)
        settings_obj.timezone = request.POST.get('timezone', settings_obj.timezone)

        try:
            settings_obj.save()
            messages.success(request, 'Settings updated successfully!')

            # Log the change
            SystemAuditLog.objects.create(
                user=request.user,
                action='update',
                model_name='UserSettings',
                object_id=str(settings_obj.id),
                object_repr=str(settings_obj),
                success=True
            )

        except Exception as e:
            messages.error(request, f'Error updating settings: {str(e)}')

    context = {
        'page_title': f'User Settings - {user.get_full_name() or user.username}',
        'settings_user': user,
        'settings_obj': settings_obj,
        'is_own_settings': user == request.user,
    }
    return render(request, 'settings_module/user_settings.html', context)


# Audit Log Views
@login_required
def audit_logs(request):
    """View system audit logs"""
    if not (request.user.is_superuser or request.user.role in ['ict_admin', 'me_staff']):
        return HttpResponseForbidden("You do not have permission to view audit logs.")

    logs = SystemAuditLog.objects.all().select_related('user')

    # Filters
    action_filter = request.GET.get('action')
    if action_filter:
        logs = logs.filter(action=action_filter)

    user_filter = request.GET.get('user')
    if user_filter:
        logs = logs.filter(user__username__icontains=user_filter)

    model_filter = request.GET.get('model')
    if model_filter:
        logs = logs.filter(model_name__icontains=model_filter)

    date_from = request.GET.get('date_from')
    if date_from:
        logs = logs.filter(timestamp__date__gte=date_from)

    date_to = request.GET.get('date_to')
    if date_to:
        logs = logs.filter(timestamp__date__lte=date_to)

    # Pagination
    paginator = Paginator(logs, 50)
    page_number = request.GET.get('page')
    logs = paginator.get_page(page_number)

    context = {
        'page_title': 'System Audit Logs',
        'logs': logs,
        'action_choices': SystemAuditLog.ACTION_TYPES,
        'filters': {
            'action': action_filter,
            'user': user_filter,
            'model': model_filter,
            'date_from': date_from,
            'date_to': date_to,
        },
    }
    return render(request, 'settings_module/audit_logs.html', context)


# System Alerts Management
@login_required
def system_alerts(request):
    """Manage system alerts"""
    if not (request.user.is_superuser or request.user.role == 'ict_admin'):
        return HttpResponseForbidden("Permission denied.")

    alerts = SystemAlert.objects.all().order_by('-created_at')

    context = {
        'page_title': 'System Alerts',
        'alerts': alerts,
    }
    return render(request, 'settings_module/system_alerts.html', context)


@login_required
def create_alert(request):
    """Create system alert"""
    if not (request.user.is_superuser or request.user.role == 'ict_admin'):
        return HttpResponseForbidden("Permission denied.")

    if request.method == 'POST':
        title = request.POST.get('title')
        message = request.POST.get('message')
        alert_type = request.POST.get('alert_type', 'info')
        scope = request.POST.get('scope', 'system')

        if title and message:
            alert = SystemAlert.objects.create(
                title=title,
                message=message,
                alert_type=alert_type,
                scope=scope,
                created_by=request.user
            )

            # Handle role targeting if scope is 'role'
            if scope == 'role':
                target_roles = request.POST.getlist('target_roles')
                alert.target_roles = target_roles
                alert.save()

            messages.success(request, 'System alert created successfully!')
            return redirect('settings:system_alerts')
        else:
            messages.error(request, 'Title and message are required.')

    context = {
        'page_title': 'Create System Alert',
        'alert_types': SystemAlert.ALERT_TYPES,
        'alert_scopes': SystemAlert.ALERT_SCOPES,
        'role_choices': User.ROLE_CHOICES,
    }
    return render(request, 'settings_module/create_alert.html', context)


@login_required
def toggle_alert(request, alert_id):
    """Toggle alert active status"""
    from django.http import JsonResponse

    if not (request.user.is_superuser or request.user.role == 'ict_admin'):
        return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)

    alert = get_object_or_404(SystemAlert, id=alert_id)

    if request.method == 'POST':
        try:
            activate = request.POST.get('activate', 'false') == 'true'
            alert.is_active = activate
            alert.save()

            action = 'activated' if activate else 'deactivated'
            return JsonResponse({
                'success': True,
                'message': f'Alert "{alert.title}" has been {action}'
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=400)


@login_required
def delete_alert(request, alert_id):
    """Delete a system alert"""
    from django.http import JsonResponse

    if not (request.user.is_superuser or request.user.role == 'ict_admin'):
        return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)

    alert = get_object_or_404(SystemAlert, id=alert_id)

    if request.method == 'POST':
        try:
            alert_title = alert.title
            alert.delete()

            return JsonResponse({
                'success': True,
                'message': f'Alert "{alert_title}" has been deleted'
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=400)