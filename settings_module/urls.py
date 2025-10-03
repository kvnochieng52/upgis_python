from django.urls import path
from . import views

app_name = 'settings'

urlpatterns = [
    path('', views.settings_dashboard, name='settings_dashboard'),

    # User Management
    path('users/', views.user_management, name='user_management'),
    path('users/create/', views.user_create, name='user_create'),
    path('users/<int:user_id>/edit/', views.user_edit, name='user_edit'),
    path('users/<int:user_id>/delete/', views.user_delete, name='user_delete'),
    path('users/<int:user_id>/toggle-status/', views.user_toggle_status, name='user_toggle_status'),

    # System Configuration
    path('config/', views.system_config, name='system_config'),
    path('config/<int:config_id>/edit/', views.config_edit, name='config_edit'),

    # User Settings
    path('user-settings/', views.user_settings, name='user_settings'),
    path('user-settings/<int:user_id>/', views.user_settings, name='user_settings_view'),

    # Audit Logs
    path('audit/', views.audit_logs, name='audit_logs'),

    # System Alerts
    path('alerts/', views.system_alerts, name='system_alerts'),
    path('alerts/create/', views.create_alert, name='create_alert'),
    path('alerts/<int:alert_id>/toggle/', views.toggle_alert, name='toggle_alert'),
    path('alerts/<int:alert_id>/delete/', views.delete_alert, name='delete_alert'),
]