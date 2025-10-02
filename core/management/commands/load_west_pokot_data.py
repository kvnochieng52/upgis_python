"""
Management command to load West Pokot County data
"""
from django.core.management.base import BaseCommand
from core.models import County, SubCounty, Village


class Command(BaseCommand):
    help = 'Load West Pokot County, Sub-Counties, and Villages data'

    def handle(self, *args, **options):
        self.stdout.write('Loading West Pokot County data...')

        # Create West Pokot County
        county, created = County.objects.get_or_create(
            name='West Pokot',
            defaults={'country': 'Kenya'}
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f'Created county: {county.name}'))
        else:
            self.stdout.write(f'County already exists: {county.name}')

        # West Pokot Sub-Counties
        subcounties_data = [
            'Kapenguria',
            'Sigor',
            'Kacheliba',
            'Pokot South'
        ]

        subcounties = {}
        for subcounty_name in subcounties_data:
            subcounty, created = SubCounty.objects.get_or_create(
                name=subcounty_name,
                county=county
            )
            subcounties[subcounty_name] = subcounty

            if created:
                self.stdout.write(self.style.SUCCESS(f'  Created subcounty: {subcounty_name}'))
            else:
                self.stdout.write(f'  Subcounty already exists: {subcounty_name}')

        # Villages by Sub-County
        villages_data = {
            'Kapenguria': [
                'Mnagei', 'Siyoi', 'Endugh', 'Kapenguria Town', 'Riwo',
                'Sook', 'Lomut', 'Chesegon', 'Keringet', 'Makutano'
            ],
            'Sigor': [
                'Sekerr', 'Masool', 'Muino', 'Weiwei', 'Kishaunet',
                'Chepkopegh', 'Kabichbich', 'Lokitelaebu', 'Akoret', 'Kasei'
            ],
            'Kacheliba': [
                'Suam', 'Kodich', 'Kasei', 'Alale', 'Kapchok',
                'Kiwawa', 'Mnagei', 'Kacheliba Town', 'Akoret', 'Kakomor'
            ],
            'Pokot South': [
                'Chepareria', 'Batei', 'Lelan', 'Tapach', 'Kokwomoing',
                'Lomut', 'Chesogon', 'Kanyarkwat', 'Wei Wei', 'Kapcherop'
            ]
        }

        village_count = 0
        for subcounty_name, village_names in villages_data.items():
            subcounty = subcounties[subcounty_name]

            for village_name in village_names:
                village, created = Village.objects.get_or_create(
                    name=village_name,
                    subcounty_obj=subcounty,
                    defaults={
                        'country': 'Kenya',
                        'is_program_area': True
                    }
                )

                if created:
                    village_count += 1
                    self.stdout.write(f'    Created village: {village_name}')

        self.stdout.write(self.style.SUCCESS(f'\nSummary:'))
        self.stdout.write(self.style.SUCCESS(f'  County: 1 (West Pokot)'))
        self.stdout.write(self.style.SUCCESS(f'  Sub-Counties: {len(subcounties_data)}'))
        self.stdout.write(self.style.SUCCESS(f'  New Villages: {village_count}'))
        self.stdout.write(self.style.SUCCESS('\nWest Pokot data loaded successfully!'))
