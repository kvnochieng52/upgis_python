"""
Context processors for UPG System
"""


def user_permissions(request):
    """
    Add user role and permission information to template context
    """
    if request.user.is_authenticated:
        user = request.user

        # Role-based permissions matrix
        permissions = {
            # Module access permissions
            'can_view_programs': user.is_superuser or user.role in ['ict_admin', 'me_staff', 'county_executive', 'county_assembly', 'field_associate'],
            'can_edit_programs': user.is_superuser or user.role in ['ict_admin', 'me_staff'],

            'can_view_households': user.is_superuser or user.role in ['ict_admin', 'me_staff', 'field_associate', 'mentor'],
            'can_edit_households': user.is_superuser or user.role in ['ict_admin', 'me_staff', 'field_associate', 'mentor'],

            'can_view_business_groups': user.is_superuser or user.role in ['ict_admin', 'me_staff', 'field_associate', 'mentor'],
            'can_edit_business_groups': user.is_superuser or user.role in ['ict_admin', 'me_staff', 'field_associate', 'mentor'],

            'can_view_savings_groups': user.is_superuser or user.role in ['ict_admin', 'me_staff', 'field_associate', 'mentor'],
            'can_edit_savings_groups': user.is_superuser or user.role in ['ict_admin', 'me_staff', 'field_associate', 'mentor'],

            'can_view_surveys': user.is_superuser or user.role in ['ict_admin', 'me_staff', 'field_associate', 'mentor'],
            'can_create_surveys': user.is_superuser or user.role in ['ict_admin', 'me_staff'],

            'can_view_training': user.is_superuser or user.role in ['ict_admin', 'me_staff', 'field_associate', 'mentor'],
            'can_create_training': user.is_superuser or user.role in ['ict_admin', 'me_staff', 'field_associate'],
            'can_edit_training': user.is_superuser or user.role in ['ict_admin', 'me_staff', 'field_associate'],
            'can_delete_training': user.is_superuser or user.role in ['ict_admin', 'me_staff'],
            'can_manage_training': user.is_superuser or user.role in ['ict_admin', 'me_staff', 'field_associate'],

            'can_view_grants': user.is_superuser or user.role in ['ict_admin', 'county_executive', 'field_associate'],
            'can_manage_grants': user.is_superuser or user.role in ['ict_admin', 'field_associate'],

            'can_view_reports': user.is_superuser or user.role in ['ict_admin', 'me_staff', 'county_executive', 'county_assembly'],
            'can_export_reports': user.is_superuser or user.role in ['ict_admin', 'me_staff', 'county_executive'],

            'can_view_settings': user.is_superuser or user.role == 'ict_admin',
            'can_manage_users': user.is_superuser or user.role == 'ict_admin',

            # ESR Import permissions
            'can_import_esr': user.is_superuser or user.role == 'ict_admin',

            # Geographic restrictions
            'has_village_restrictions': user.role in ['mentor', 'field_associate'] and not user.is_superuser,
        }

        # Add user role information
        role_info = {
            'user_role': user.role,
            'user_role_display': user.get_role_display(),
            'is_mentor': user.role == 'mentor',
            'is_field_associate': user.role == 'field_associate',
            'is_me_staff': user.role == 'me_staff',
            'is_ict_admin': user.role == 'ict_admin',
            'is_county_executive': user.role == 'county_executive',
            'is_county_assembly': user.role == 'county_assembly',
            'is_beneficiary': user.role == 'beneficiary',
        }

        # Village assignments for mentors and field associates
        village_info = {}
        if hasattr(user, 'profile') and user.profile and user.role in ['mentor', 'field_associate']:
            assigned_villages = user.profile.assigned_villages.all()
            village_info.update({
                'assigned_villages': assigned_villages,
                'assigned_villages_count': assigned_villages.count(),
                'has_village_assignments': assigned_villages.exists(),
            })

        return {
            'perms': permissions,
            'role_info': role_info,
            'village_info': village_info,
        }

    return {}


def system_alerts(request):
    """
    Add active system alerts to template context
    """
    if request.user.is_authenticated:
        from settings_module.models import SystemAlert, UserAlertDismissal
        from django.utils import timezone

        # Get active alerts visible to this user
        active_alerts = SystemAlert.objects.filter(
            is_active=True,
            show_until__gt=timezone.now()
        )

        # Filter alerts by scope
        user_alerts = []
        for alert in active_alerts:
            if alert.is_visible_to_user(request.user):
                # Check if user has dismissed this alert
                dismissed = UserAlertDismissal.objects.filter(
                    user=request.user,
                    alert=alert
                ).exists()

                if not dismissed:
                    user_alerts.append(alert)

        return {
            'system_alerts': user_alerts,
            'alerts_count': len(user_alerts),
        }

    return {}