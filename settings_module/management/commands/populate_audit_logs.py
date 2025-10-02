"""
Management command to populate sample audit logs for testing
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
import random

from settings_module.models import SystemAuditLog

User = get_user_model()


class Command(BaseCommand):
    help = 'Populate sample audit logs for testing'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Creating sample audit logs...'))

        # Get users or create sample ones
        users = list(User.objects.all())
        if not users:
            self.stdout.write(self.style.WARNING('No users found. Creating sample users...'))
            # Create sample users if none exist
            users = [
                User.objects.create_user(
                    username='admin',
                    email='admin@example.com',
                    role='ict_admin',
                    password='password123'
                ),
                User.objects.create_user(
                    username='mentor1',
                    email='mentor1@example.com',
                    role='mentor',
                    password='password123'
                ),
                User.objects.create_user(
                    username='field_associate1',
                    email='fa1@example.com',
                    role='field_associate',
                    password='password123'
                ),
            ]

        # Sample actions and models
        actions = ['create', 'read', 'update', 'delete', 'login', 'logout', 'export']
        models = ['Household', 'BusinessGroup', 'SavingsGroup', 'User', 'Form', 'Survey', 'Grant']
        ip_addresses = ['127.0.0.1', '192.168.1.100', '10.0.0.50', '172.16.0.25']
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
        ]

        # Create 50 sample audit log entries
        for i in range(50):
            user = random.choice(users)
            action = random.choice(actions)
            model_name = random.choice(models)

            # Create timestamp within last 30 days
            days_ago = random.randint(0, 30)
            timestamp = timezone.now() - timedelta(days=days_ago,
                                                 hours=random.randint(0, 23),
                                                 minutes=random.randint(0, 59))

            # Sample changes data
            changes = {}
            if action == 'update':
                changes = {
                    'old_value': f'old_{i}',
                    'new_value': f'new_{i}',
                    'field': 'status'
                }
            elif action == 'create':
                changes = {'created_fields': ['name', 'status', 'created_at']}

            SystemAuditLog.objects.create(
                user=user,
                action=action,
                model_name=model_name,
                object_id=str(random.randint(1, 100)),
                object_repr=f'{model_name} #{random.randint(1, 100)}',
                ip_address=random.choice(ip_addresses),
                user_agent=random.choice(user_agents),
                request_path=f'/{model_name.lower()}s/',
                request_method=random.choice(['GET', 'POST', 'PUT', 'DELETE']),
                changes=changes,
                success=random.choice([True, True, True, False]),  # 75% success rate
                error_message='Sample error message' if random.random() < 0.25 else '',
                timestamp=timestamp
            )

        # Create some specific recent login/logout entries
        for user in users[:3]:
            # Login entry
            SystemAuditLog.objects.create(
                user=user,
                action='login',
                model_name='User',
                object_repr=str(user),
                ip_address='127.0.0.1',
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                request_path='/accounts/login/',
                request_method='POST',
                success=True,
                timestamp=timezone.now() - timedelta(hours=random.randint(1, 24))
            )

            # Logout entry
            SystemAuditLog.objects.create(
                user=user,
                action='logout',
                model_name='User',
                object_repr=str(user),
                ip_address='127.0.0.1',
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                request_path='/accounts/logout/',
                request_method='POST',
                success=True,
                timestamp=timezone.now() - timedelta(minutes=random.randint(30, 120))
            )

        total_logs = SystemAuditLog.objects.count()
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created sample audit logs. Total logs in database: {total_logs}'
            )
        )