from django.urls import path
from . import views

app_name = 'programs'

urlpatterns = [
    path('', views.program_list, name='program_list'),
    path('create/', views.program_create, name='program_create'),
    path('<int:pk>/', views.program_detail, name='program_detail'),
    path('<int:pk>/edit/', views.program_edit, name='program_edit'),
    path('<int:pk>/delete/', views.program_delete, name='program_delete'),
    path('<int:pk>/toggle-status/', views.program_toggle_status, name='program_toggle_status'),
    path('<int:pk>/applications/', views.program_applications, name='program_applications'),
    path('<int:pk>/apply/', views.program_apply, name='program_apply'),
    path('applications/', views.my_applications, name='my_applications'),
    path('applications/<int:application_id>/approve/', views.approve_application, name='approve_application'),
    path('applications/<int:application_id>/reject/', views.reject_application, name='reject_application'),
]