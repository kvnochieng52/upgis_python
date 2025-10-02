from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.report_list, name='report_list'),

    # Download Reports
    path('download/households/', views.download_household_report, name='download_household_report'),
    path('download/ppi/', views.download_ppi_report, name='download_ppi_report'),
    path('download/program-participation/', views.download_program_participation_report, name='download_program_participation_report'),
    path('download/business-groups/', views.download_business_groups_report, name='download_business_groups_report'),
    path('download/savings-groups/', views.download_savings_groups_report, name='download_savings_groups_report'),
    path('download/grants/', views.download_grants_report, name='download_grants_report'),
    path('download/training/', views.download_training_report, name='download_training_report'),
    path('download/mentoring/', views.download_mentoring_report, name='download_mentoring_report'),
    path('download/geographic/', views.download_geographic_report, name='download_geographic_report'),

    # Analytics and Performance
    path('performance-dashboard/', views.performance_dashboard, name='performance_dashboard'),
    path('custom-report-builder/', views.custom_report_builder, name='custom_report_builder'),
    path('download/custom-report/', views.download_custom_report, name='download_custom_report'),
]