from django.urls import path
from . import views

app_name = 'business_groups'

urlpatterns = [
    path('', views.group_list, name='group_list'),
    path('create/', views.group_create, name='group_create'),
    path('<int:pk>/', views.group_detail, name='group_detail'),
    path('<int:pk>/edit/', views.group_edit, name='group_edit'),
    path('<int:pk>/add-member/', views.add_member, name='add_member'),
    path('<int:pk>/remove-member/<int:member_id>/', views.remove_member, name='remove_member'),
    path('<int:pk>/update-role/<int:member_id>/', views.update_member_role, name='update_member_role'),
    path('<int:pk>/available-households/', views.get_available_households, name='get_available_households'),
]