from django.urls import path
from . import views

app_name = 'grants'

urlpatterns = [
    path('', views.grants_dashboard, name='grants_dashboard'),
    path('sb-grants/', views.sb_grant_applications, name='sb_grant_applications'),
    path('pr-grants/', views.pr_grant_applications, name='pr_grant_applications'),
    path('grant/<str:grant_type>/<int:grant_id>/', views.grant_detail, name='grant_detail'),
    path('grant/<str:grant_type>/<int:grant_id>/process/', views.process_grant, name='process_grant'),
]