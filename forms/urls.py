from django.urls import path
from . import views

app_name = 'forms'

urlpatterns = [
    path('', views.forms_dashboard, name='dashboard'),

    # Form Templates
    path('templates/', views.form_template_list, name='template_list'),
    path('templates/create/', views.form_template_create, name='template_create'),
    path('templates/<int:pk>/builder/', views.form_template_builder, name='template_builder'),

    # Form Assignments
    path('assignments/create/', views.form_assignment_create, name='assignment_create'),
    path('assignments/<int:pk>/', views.assignment_detail, name='assignment_detail'),
    path('assignments/<int:assignment_pk>/assign-mentor/', views.assign_to_mentor, name='assign_to_mentor'),
    path('assignments/<int:assignment_pk>/fill/', views.fill_form, name='fill_form'),

    # Submissions
    path('submissions/<int:pk>/', views.submission_detail, name='submission_detail'),

    # User-specific views
    path('my-assignments/', views.my_assignments, name='my_assignments'),
]