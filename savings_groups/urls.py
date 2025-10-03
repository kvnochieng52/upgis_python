from django.urls import path
from . import views

app_name = 'savings_groups'

urlpatterns = [
    path('', views.savings_list, name='savings_list'),
    path('create/', views.savings_group_create, name='savings_group_create'),
    path('<int:pk>/', views.savings_group_detail, name='savings_group_detail'),
    path('<int:pk>/edit/', views.savings_group_edit, name='savings_group_edit'),

    # Member management
    path('<int:pk>/add-member/', views.add_member, name='add_member'),
    path('<int:pk>/remove-member/<int:member_id>/', views.remove_member, name='remove_member'),

    # Business group management
    path('<int:pk>/add-business-group/', views.add_business_group, name='add_business_group'),
    path('<int:pk>/remove-business-group/<int:bg_id>/', views.remove_business_group, name='remove_business_group'),

    # Savings management
    path('<int:pk>/record-savings/', views.record_savings, name='record_savings'),
    path('<int:pk>/savings-report/', views.savings_report, name='savings_report'),
    path('<int:pk>/export-savings/', views.export_savings_data, name='export_savings_data'),
]