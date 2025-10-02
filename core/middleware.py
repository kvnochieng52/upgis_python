"""
Middleware for UPG System
"""

from django.utils import timezone
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver
from settings_module.models import SystemAuditLog


def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


class AuditLogMiddleware:
    """
    Middleware to log user actions and system events
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Store request info for later use
        request.audit_data = {
            'ip_address': get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'request_path': request.path,
            'request_method': request.method,
        }

        response = self.get_response(request)

        # Log certain actions based on response status and path
        if hasattr(request, 'user') and request.user.is_authenticated:
            self._log_action_if_needed(request, response)

        return response

    def _log_action_if_needed(self, request, response):
        """Log actions based on request path and method"""
        path = request.path
        method = request.method
        user = request.user

        # Skip certain paths
        skip_paths = ['/static/', '/media/', '/favicon.ico', '/admin/jsi18n/']
        if any(skip_path in path for skip_path in skip_paths):
            return

        # Log specific actions
        if method == 'POST' and response.status_code in [200, 201, 302]:
            action = 'create'
            model_name = ''
            object_repr = ''

            # Determine action and model based on path
            if '/create' in path or '/add' in path:
                action = 'create'
            elif '/edit' in path or '/update' in path:
                action = 'update'
            elif '/delete' in path:
                action = 'delete'
            elif 'login' in path:
                return  # Handled by signal
            elif 'logout' in path:
                return  # Handled by signal
            else:
                action = 'update'  # Generic POST action

            # Extract model name from URL
            url_parts = path.strip('/').split('/')
            if len(url_parts) > 0:
                model_name = url_parts[0].replace('-', '_').title()

            # Create audit log entry
            try:
                SystemAuditLog.objects.create(
                    user=user,
                    action=action,
                    model_name=model_name,
                    object_repr=object_repr,
                    ip_address=request.audit_data['ip_address'],
                    user_agent=request.audit_data['user_agent'],
                    request_path=request.audit_data['request_path'],
                    request_method=request.audit_data['request_method'],
                    success=True
                )
            except Exception:
                # Don't let audit logging break the application
                pass


@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    """Log user login events"""
    try:
        SystemAuditLog.objects.create(
            user=user,
            action='login',
            model_name='User',
            object_repr=str(user),
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            request_path=request.path,
            request_method=request.method,
            success=True
        )
    except Exception:
        pass


@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    """Log user logout events"""
    try:
        SystemAuditLog.objects.create(
            user=user,
            action='logout',
            model_name='User',
            object_repr=str(user) if user else 'Anonymous',
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            request_path=request.path,
            request_method=request.method,
            success=True
        )
    except Exception:
        pass