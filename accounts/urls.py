"""
Accounts URL Configuration
"""

from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),

    # Password reset functionality
    path('forgot-password/', views.forgot_password_view, name='forgot_password'),
    path('reset-password/<str:token>/', views.reset_password_view, name='reset_password'),
    path('password-reset-sent/', views.password_reset_sent_view, name='password_reset_sent'),
    path('password-reset-complete/', views.password_reset_complete_view, name='password_reset_complete'),
]