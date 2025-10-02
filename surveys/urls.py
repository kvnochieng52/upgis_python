from django.urls import path
from . import views

app_name = 'surveys'

urlpatterns = [
    path('', views.survey_list, name='survey_list'),
    path('household/create/', views.household_survey_create, name='household_survey_create'),
    path('business/create/', views.business_survey_create, name='business_survey_create'),
    path('household/<int:pk>/', views.household_survey_detail, name='household_survey_detail'),
    path('business/<int:pk>/', views.business_survey_detail, name='business_survey_detail'),
    path('household/<int:pk>/edit/', views.household_survey_edit, name='household_survey_edit'),
    path('business/<int:pk>/edit/', views.business_survey_edit, name='business_survey_edit'),
]