from django.urls import path
from . import views

app_name = 'upg_grants'

urlpatterns = [
    # Grant application list and management
    path('applications/', views.grant_application_list, name='application_list'),
    path('applications/create/', views.grant_application_create, name='application_create_universal'),
    path('applications/create/<int:household_id>/', views.grant_application_create, name='application_create'),
    path('applications/<int:application_id>/', views.grant_application_detail, name='application_detail'),
    path('applications/<int:application_id>/review/', views.grant_application_review, name='application_review'),

    # Review dashboard
    path('reviews/pending/', views.pending_reviews, name='pending_reviews'),

    # Available grants for application
    path('available/', views.available_grants_list, name='available_grants'),
]
