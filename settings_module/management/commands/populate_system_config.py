"""
Management command to populate sample system configuration settings
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from settings_module.models import SystemConfiguration

User = get_user_model()


class Command(BaseCommand):
    help = 'Populate sample system configuration settings'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Creating sample system configurations...'))

        # Get an admin user or create one
        admin_user = User.objects.filter(is_superuser=True).first()
        if not admin_user:
            admin_user = User.objects.filter(role='ict_admin').first()

        if not admin_user:
            admin_user = User.objects.create_user(
                username='config_admin',
                email='admin@example.com',
                role='ict_admin',
                password='password123',
                is_superuser=True
            )

        # Sample configuration settings
        configurations = [
            # General Settings
            {
                'key': 'SYSTEM_NAME',
                'value': 'UPG Management System',
                'setting_type': 'string',
                'description': 'The display name of the system',
                'category': 'general',
                'is_public': True,
                'is_editable': True,
            },
            {
                'key': 'SYSTEM_VERSION',
                'value': '1.0.0',
                'setting_type': 'string',
                'description': 'Current version of the system',
                'category': 'general',
                'is_public': True,
                'is_editable': False,
            },
            {
                'key': 'DEFAULT_LANGUAGE',
                'value': 'en',
                'setting_type': 'string',
                'description': 'Default language for the system',
                'category': 'general',
                'is_public': True,
                'is_editable': True,
            },
            {
                'key': 'DEFAULT_TIMEZONE',
                'value': 'Africa/Nairobi',
                'setting_type': 'string',
                'description': 'Default timezone for the system',
                'category': 'general',
                'is_public': True,
                'is_editable': True,
            },
            {
                'key': 'MAINTENANCE_MODE',
                'value': 'false',
                'setting_type': 'boolean',
                'description': 'Enable maintenance mode to restrict access',
                'category': 'general',
                'is_public': False,
                'is_editable': True,
            },

            # Email Settings
            {
                'key': 'EMAIL_NOTIFICATIONS_ENABLED',
                'value': 'true',
                'setting_type': 'boolean',
                'description': 'Enable email notifications system-wide',
                'category': 'email',
                'is_public': False,
                'is_editable': True,
            },
            {
                'key': 'DEFAULT_FROM_EMAIL',
                'value': 'noreply@upgmanagement.org',
                'setting_type': 'string',
                'description': 'Default sender email address',
                'category': 'email',
                'is_public': False,
                'is_editable': True,
            },
            {
                'key': 'EMAIL_ADMIN_NOTIFICATIONS',
                'value': 'admin@upgmanagement.org',
                'setting_type': 'string',
                'description': 'Email address for admin notifications',
                'category': 'email',
                'is_public': False,
                'is_editable': True,
            },

            # UPG Program Settings
            {
                'key': 'UPG_PROGRAM_DURATION_MONTHS',
                'value': '12',
                'setting_type': 'integer',
                'description': 'Duration of UPG program in months',
                'category': 'program',
                'is_public': True,
                'is_editable': True,
            },
            {
                'key': 'DEFAULT_CURRENCY',
                'value': 'KES',
                'setting_type': 'string',
                'description': 'Default currency for financial transactions',
                'category': 'program',
                'is_public': True,
                'is_editable': True,
            },
            {
                'key': 'MINIMUM_GROUP_SIZE',
                'value': '5',
                'setting_type': 'integer',
                'description': 'Minimum number of members for business groups',
                'category': 'program',
                'is_public': True,
                'is_editable': True,
            },
            {
                'key': 'MAXIMUM_GROUP_SIZE',
                'value': '30',
                'setting_type': 'integer',
                'description': 'Maximum number of members for business groups',
                'category': 'program',
                'is_public': True,
                'is_editable': True,
            },

            # Security Settings
            {
                'key': 'SESSION_TIMEOUT_MINUTES',
                'value': '60',
                'setting_type': 'integer',
                'description': 'User session timeout in minutes',
                'category': 'security',
                'is_public': False,
                'is_editable': True,
            },
            {
                'key': 'PASSWORD_MIN_LENGTH',
                'value': '8',
                'setting_type': 'integer',
                'description': 'Minimum password length requirement',
                'category': 'security',
                'is_public': False,
                'is_editable': True,
            },
            {
                'key': 'ENABLE_TWO_FACTOR_AUTH',
                'value': 'false',
                'setting_type': 'boolean',
                'description': 'Enable two-factor authentication',
                'category': 'security',
                'is_public': False,
                'is_editable': True,
            },

            # Reports Settings
            {
                'key': 'DEFAULT_REPORT_FORMAT',
                'value': 'pdf',
                'setting_type': 'string',
                'description': 'Default format for generated reports',
                'category': 'reports',
                'is_public': True,
                'is_editable': True,
            },
            {
                'key': 'REPORT_RETENTION_DAYS',
                'value': '90',
                'setting_type': 'integer',
                'description': 'Number of days to retain generated reports',
                'category': 'reports',
                'is_public': False,
                'is_editable': True,
            },

            # Advanced Settings
            {
                'key': 'API_RATE_LIMITS',
                'value': '{"per_minute": 60, "per_hour": 1000}',
                'setting_type': 'json',
                'description': 'API rate limiting configuration',
                'category': 'advanced',
                'is_public': False,
                'is_editable': True,
            },
            {
                'key': 'FEATURE_FLAGS',
                'value': '{"experimental_dashboard": false, "beta_reports": true}',
                'setting_type': 'json',
                'description': 'Feature flags for enabling/disabling features',
                'category': 'advanced',
                'is_public': False,
                'is_editable': True,
            },
        ]

        created_count = 0
        for config_data in configurations:
            config, created = SystemConfiguration.objects.get_or_create(
                key=config_data['key'],
                defaults={
                    **config_data,
                    'created_by': admin_user,
                    'modified_by': admin_user,
                }
            )
            if created:
                created_count += 1
                self.stdout.write(f'Created: {config.key}')
            else:
                self.stdout.write(f'Already exists: {config.key}')

        total_configs = SystemConfiguration.objects.count()
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully processed {len(configurations)} configurations. '
                f'Created {created_count} new configurations. '
                f'Total configurations in database: {total_configs}'
            )
        )