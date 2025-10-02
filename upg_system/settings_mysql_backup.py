"""
Django settings for UPG System project.

Generated for Village Enterprise Ultra-Poor Graduation Management System.
For local development and testing.
"""

from pathlib import Path
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
SECRET_KEY = 'django-insecure-upg-system-dev-key-change-in-production-123456789'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0']


# Application definition
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'crispy_forms',
    'crispy_bootstrap5',
]

LOCAL_APPS = [
    'accounts',
    'core',
    'households',
    'business_groups',
    'savings_groups',
    'training',
    'surveys',
    'reports',
    'programs',
    'dashboard',
    'grants',
    'upg_grants',  # UPG-specific grant management
    'forms',  # Dynamic forms system
    'settings_module',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'core.middleware.AuditLogMiddleware',
]

ROOT_URLCONF = 'upg_system.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.user_permissions',
                'core.context_processors.system_alerts',
            ],
        },
    },
]

WSGI_APPLICATION = 'upg_system.wsgi.application'


# Database - MySQL Configuration (Active)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'upg_management_system',
        'USER': 'root',
        'PASSWORD': '',  # XAMPP default (no password)
        'HOST': 'localhost',
        'PORT': '3306',
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            'charset': 'utf8mb4',
        },
        'TEST': {
            'CHARSET': 'utf8mb4',
            'COLLATION': 'utf8mb4_unicode_ci',
        },
    }
}

# SQLite Configuration (Backup - commented out)
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': BASE_DIR / 'db.sqlite3',
#     }
# }


# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Africa/Nairobi'
USE_I18N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom User Model
AUTH_USER_MODEL = 'accounts.User'

# Crispy Forms Configuration
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

# Login URLs
LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/accounts/login/'

# Email Configuration (for development)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# SMS Configuration
# Africa's Talking API (Primary SMS provider for Kenya)
AFRICAS_TALKING_API_KEY = ''  # Set in production
AFRICAS_TALKING_USERNAME = 'sandbox'  # Change to production username
SMS_SENDER_ID = 'UPG_SYS'

# Twilio API (Fallback SMS provider)
TWILIO_ACCOUNT_SID = ''  # Set in production
TWILIO_AUTH_TOKEN = ''   # Set in production
TWILIO_PHONE_NUMBER = '' # Set in production

# SMS Settings
SMS_ENABLED = True
SMS_BACKEND = 'core.sms.SMSService'  # Can be changed for testing

# Session Configuration
SESSION_COOKIE_AGE = 3600  # 1 hour
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# Security Settings for Development
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True

# UPG System Specific Settings
UPG_SYSTEM_VERSION = '1.0.0'
UPG_DEFAULT_COUNTRY = 'Kenya'
UPG_DEFAULT_CURRENCY = 'KES'

# Database compatibility settings
import sys
if 'migrate' in sys.argv or 'makemigrations' in sys.argv:
    # Only apply MySQL/MariaDB settings if using MySQL backend
    if DATABASES['default']['ENGINE'] in ['django.db.backends.mysql', 'django.db.backends.mariadb']:
        if 'OPTIONS' not in DATABASES['default']:
            DATABASES['default']['OPTIONS'] = {}
        DATABASES['default']['OPTIONS']['init_command'] = (
            "SET sql_mode='STRICT_TRANS_TABLES'; "
            "SET SESSION innodb_strict_mode=1; "
        )

# Pagination
ITEMS_PER_PAGE = 25

# File Upload Settings
FILE_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB