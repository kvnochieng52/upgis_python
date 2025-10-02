"""
Management command to create test business groups
"""
from django.core.management.base import BaseCommand
from business_groups.models import BusinessGroup
from core.models import Program
from households.models import Household
from datetime import date


class Command(BaseCommand):
    help = 'Creates test business groups'

    def handle(self, *args, **kwargs):
        program = Program.objects.first()
        if not program:
            self.stdout.write(self.style.ERROR('No programs found'))
            return

        bg_data = [
            ('Kapenguria Women Farmers', 'agriculture'),
            ('Sigor Dairy Cooperative', 'livestock'),
            ('Pokot Poultry Group', 'poultry'),
            ('Mnagei Tailors', 'tailoring'),
            ('Sook Traders', 'retail'),
            ('Riwo Beekeepers', 'apiculture'),
        ]

        for name, btype in bg_data:
            bg, created = BusinessGroup.objects.get_or_create(
                name=name,
                defaults={
                    'business_type': btype,
                    'program': program,
                    'formation_date': date(2024, 1, 15),
                    'participation_status': 'active',
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created: {name} ({btype})'))
            else:
                self.stdout.write(self.style.WARNING(f'Already exists: {name}'))

        self.stdout.write(self.style.SUCCESS(f'\n✓ Business groups ready'))
