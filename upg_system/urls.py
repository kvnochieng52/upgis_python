"""
URL configuration for UPG System project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # Authentication
    path('accounts/', include('accounts.urls')),

    # Main Dashboard
    path('', include('dashboard.urls')),

    # Core modules
    path('households/', include('households.urls')),
    path('business-groups/', include('business_groups.urls')),
    path('savings-groups/', include('savings_groups.urls')),
    path('training/', include('training.urls')),
    path('surveys/', include('surveys.urls')),
    path('reports/', include('reports.urls')),
    path('programs/', include('programs.urls')),
    path('grants/', include('grants.urls')),
    path('upg-grants/', include('upg_grants.urls')),
    path('settings/', include('settings_module.urls')),
    path('core/', include('core.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Custom admin site headers
admin.site.site_header = "UPG Management System"
admin.site.site_title = "UPG Admin"
admin.site.index_title = "Ultra-Poor Graduation Management"