from django.urls import path
from . import views
from . import graduation_views

app_name = 'households'

urlpatterns = [
    path('', views.household_list, name='household_list'),
    path('create/', views.household_create, name='household_create'),
    path('<int:pk>/', views.household_detail, name='household_detail'),
    path('<int:pk>/edit/', views.household_edit, name='household_edit'),
    path('<int:pk>/delete/', views.household_delete, name='household_delete'),
    path('<int:household_pk>/members/add/', views.member_create, name='member_create'),
    path('members/<int:pk>/edit/', views.member_edit, name='member_edit'),
    path('members/<int:pk>/delete/', views.member_delete, name='member_delete'),

    # Graduation tracking URLs
    path('graduation/', graduation_views.graduation_dashboard, name='graduation_dashboard'),
    path('<int:household_id>/milestones/', graduation_views.household_milestones, name='household_milestones'),
    path('milestone/<int:milestone_id>/update/', graduation_views.update_milestone, name='update_milestone'),
    path('graduation/reports/', graduation_views.graduation_reports, name='graduation_reports'),
    path('graduation/reports/export/', graduation_views.export_graduation_reports, name='export_graduation_reports'),

    # Eligibility assessment URLs
    path('<int:household_id>/eligibility/', views.run_eligibility_assessment, name='run_eligibility_assessment'),
    path('<int:household_id>/qualification/', views.run_qualification_assessment, name='run_qualification_assessment'),
    path('eligibility/batch-report/', views.batch_eligibility_report, name='batch_eligibility_report'),
    path('eligibility/dashboard/', views.eligibility_dashboard, name='eligibility_dashboard'),
    path('api/<int:household_id>/eligibility/', views.household_eligibility_api, name='household_eligibility_api'),
]