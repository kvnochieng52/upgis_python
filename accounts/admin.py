"""
Admin configuration for User management
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, UserProfile


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'


class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'role', 'office', 'is_active', 'date_joined')
    list_filter = ('role', 'is_active', 'office', 'country')
    search_fields = ('username', 'email', 'first_name', 'last_name')

    fieldsets = BaseUserAdmin.fieldsets + (
        ('UPG System Info', {
            'fields': ('role', 'phone_number', 'office', 'country')
        }),
    )

    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('UPG System Info', {
            'fields': ('email', 'role', 'phone_number', 'office', 'country')
        }),
    )


admin.site.register(User, UserAdmin)