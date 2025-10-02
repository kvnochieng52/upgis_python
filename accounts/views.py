"""
Authentication Views for UPG System
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import CreateView
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from .models import User, PasswordResetToken
from .forms import LoginForm, UserRegistrationForm


def login_view(request):
    """Custom login view"""
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                next_url = request.GET.get('next', '/')
                return redirect(next_url)
            else:
                messages.error(request, 'Invalid username or password')
    else:
        form = LoginForm()

    return render(request, 'accounts/login.html', {'form': form})


@login_required
def logout_view(request):
    """Logout view"""
    logout(request)
    messages.success(request, 'You have been logged out successfully')
    return redirect('accounts:login')


@login_required
def profile_view(request):
    """User profile view"""
    return render(request, 'accounts/profile.html', {'user': request.user})


def forgot_password_view(request):
    """Forgot password form"""
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)

            # Deactivate any existing tokens for this user
            PasswordResetToken.objects.filter(user=user, is_active=True).update(is_active=False)

            # Create new reset token
            reset_token = PasswordResetToken.objects.create(user=user)

            # Build reset URL
            reset_url = request.build_absolute_uri(
                reverse('accounts:reset_password', kwargs={'token': reset_token.token})
            )

            # Send email (you may want to use a template for this)
            subject = 'UPG System - Password Reset Request'
            message = f'''
Hello {user.get_full_name() or user.username},

You have requested to reset your password for the UPG Management System.

Please click the link below to reset your password:
{reset_url}

This link will expire in 24 hours.

If you did not request this password reset, please ignore this email.

Best regards,
UPG Management System
            '''

            try:
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=False,
                )
                return redirect('accounts:password_reset_sent')
            except Exception as e:
                messages.error(request, 'Failed to send password reset email. Please contact system administrator.')

        except User.DoesNotExist:
            # Don't reveal whether email exists for security
            return redirect('accounts:password_reset_sent')

    return render(request, 'accounts/forgot_password.html')


def password_reset_sent_view(request):
    """Password reset email sent confirmation"""
    return render(request, 'accounts/password_reset_sent.html')


def reset_password_view(request, token):
    """Reset password with token"""
    try:
        reset_token = PasswordResetToken.objects.get(token=token)

        if not reset_token.is_valid():
            messages.error(request, 'This password reset link has expired or is invalid.')
            return redirect('accounts:forgot_password')

        if request.method == 'POST':
            password = request.POST.get('password')
            password_confirm = request.POST.get('password_confirm')

            if password != password_confirm:
                messages.error(request, 'Passwords do not match.')
                return render(request, 'accounts/reset_password.html', {'token': token})

            if len(password) < 8:
                messages.error(request, 'Password must be at least 8 characters long.')
                return render(request, 'accounts/reset_password.html', {'token': token})

            # Reset password
            user = reset_token.user
            user.set_password(password)
            user.save()

            # Mark token as used
            reset_token.mark_as_used()

            messages.success(request, 'Your password has been reset successfully.')
            return redirect('accounts:password_reset_complete')

        return render(request, 'accounts/reset_password.html', {'token': token})

    except PasswordResetToken.DoesNotExist:
        messages.error(request, 'Invalid password reset link.')
        return redirect('accounts:forgot_password')


def password_reset_complete_view(request):
    """Password reset complete confirmation"""
    return render(request, 'accounts/password_reset_complete.html')