from django.urls import path
from . import views
from . import mentoring_views

app_name = 'training'

urlpatterns = [
    # Training URLs
    path('', views.training_list, name='training_list'),
    path('create/', views.create_training, name='create_training'),
    path('<int:training_id>/details/', views.training_details, name='training_details'),
    path('<int:training_id>/edit/', views.edit_training, name='edit_training'),
    path('<int:training_id>/start/', views.start_training, name='start_training'),
    path('<int:training_id>/complete/', views.complete_training, name='complete_training'),
    path('<int:training_id>/delete/', views.delete_training, name='delete_training'),
    path('<int:training_id>/attendance/', views.manage_attendance, name='manage_attendance'),
    path('<int:training_id>/available-households/', views.get_available_households, name='get_available_households'),
    path('<int:training_id>/add-household/', views.add_household_to_training, name='add_household_to_training'),
    path('attendance/<int:attendance_id>/toggle/', views.toggle_attendance, name='toggle_attendance'),
    path('attendance/<int:attendance_id>/remove/', views.remove_attendance, name='remove_attendance'),

    # Mentoring URLs
    path('mentoring/', mentoring_views.mentoring_dashboard, name='mentoring_dashboard'),
    path('mentoring/reports/', mentoring_views.mentoring_reports, name='mentoring_reports'),
    path('mentoring/reports/create/', mentoring_views.create_mentoring_report, name='create_mentoring_report'),
    path('mentoring/reports/<int:report_id>/', mentoring_views.mentoring_report_detail, name='mentoring_report_detail'),
    path('mentoring/analytics/', mentoring_views.mentoring_analytics, name='mentoring_analytics'),
    path('mentoring/reports/export/', mentoring_views.export_mentoring_reports, name='export_mentoring_reports'),

    # Visit Logging URLs
    path('mentoring/visits/', mentoring_views.visit_list, name='visit_list'),
    path('mentoring/visits/log/', mentoring_views.log_visit, name='log_visit'),
    path('mentoring/phone-nudges/', mentoring_views.phone_nudge_list, name='phone_nudge_list'),
    path('mentoring/phone-nudges/log/', mentoring_views.log_phone_nudge, name='log_phone_nudge'),
]