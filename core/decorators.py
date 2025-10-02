"""
Role-based permission decorators for UPG System
"""

from functools import wraps
from django.http import HttpResponseForbidden
from django.contrib.auth.decorators import login_required


def role_required(*allowed_roles):
    """
    Decorator to restrict access to views based on user roles
    Usage: @role_required('ict_admin', 'me_staff')
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            user = request.user

            # Superusers always have access
            if user.is_superuser:
                return view_func(request, *args, **kwargs)

            # Check if user's role is in allowed roles
            if user.role in allowed_roles:
                return view_func(request, *args, **kwargs)

            return HttpResponseForbidden(
                f"Access denied. This page requires one of these roles: {', '.join(allowed_roles)}. "
                f"Your current role is: {user.get_role_display()}"
            )

        return _wrapped_view
    return decorator


def mentor_or_admin_required(view_func):
    """
    Decorator for views that mentors, field associates, and admins can access
    """
    return role_required('mentor', 'field_associate', 'ict_admin', 'me_staff')(view_func)


def admin_only(view_func):
    """
    Decorator for admin-only views
    """
    return role_required('ict_admin')(view_func)


def me_staff_or_admin(view_func):
    """
    Decorator for M&E staff and admin views
    """
    return role_required('me_staff', 'ict_admin')(view_func)


def executive_access(view_func):
    """
    Decorator for county executive and assembly access
    """
    return role_required('county_executive', 'county_assembly', 'ict_admin', 'me_staff')(view_func)


def has_village_access(user, village_id):
    """
    Check if user has access to a specific village
    """
    if user.is_superuser or user.role in ['ict_admin', 'me_staff']:
        return True

    if user.role in ['mentor', 'field_associate']:
        if hasattr(user, 'profile') and user.profile:
            assigned_village_ids = user.profile.assigned_villages.values_list('id', flat=True)
            return int(village_id) in assigned_village_ids

    return False


def filter_by_user_villages(queryset, user, village_field='village'):
    """
    Filter a queryset to only include items from user's assigned villages
    """
    if user.is_superuser or user.role in ['ict_admin', 'me_staff']:
        return queryset

    if user.role in ['mentor', 'field_associate']:
        if hasattr(user, 'profile') and user.profile:
            assigned_villages = user.profile.assigned_villages.all()
            filter_kwargs = {f'{village_field}__in': assigned_villages}
            return queryset.filter(**filter_kwargs)
        else:
            return queryset.none()

    return queryset.none()


def get_user_accessible_villages(user):
    """
    Get all villages accessible to the user based on their role
    """
    from core.models import Village

    if user.is_superuser or user.role in ['ict_admin', 'me_staff']:
        return Village.objects.all()

    if user.role in ['mentor', 'field_associate']:
        if hasattr(user, 'profile') and user.profile:
            return user.profile.assigned_villages.all()
        else:
            return Village.objects.none()

    return Village.objects.none()