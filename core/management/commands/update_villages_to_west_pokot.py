"""
Management command to update villages from Nairobi to West Pokot
"""
from django.core.management.base import BaseCommand
from core.models import Village, SubCounty
from households.models import Household


class Command(BaseCommand):
    help = 'Update villages from Nairobi to West Pokot'

    def handle(self, *args, **kwargs):
        # Get West Pokot subcounties
        subcounties = SubCounty.objects.filter(county__name='West Pokot')

        if not subcounties.exists():
            self.stdout.write(self.style.ERROR('No West Pokot subcounties found'))
            return

        # West Pokot villages by subcounty
        west_pokot_villages = {
            'Kapenguria': [
                'Mnagei', 'Siyoi', 'Endugh', 'Riwo', 'Kapenguria Town',
                'Sook', 'Muino', 'Talau', 'Chepareria'
            ],
            'Sigor': [
                'Sekerr', 'Lomut', 'Weiwei', 'Masool', 'Tapach',
                'Kishaunet', 'Chepkorio', 'Sigor Town'
            ],
            'Kacheliba': [
                'Suam', 'Kasei', 'Kacheliba Town', 'Alale', 'Kokok',
                'Kalapata', 'Kiwawa'
            ],
            'Pokot South': [
                'Chepareria', 'Batei', 'Lelan', 'Tapach', 'Chesegon',
                'Kapcherop', 'Kanyarkwat'
            ]
        }

        # Get or create villages and assign to subcounties
        for subcounty_name, village_names in west_pokot_villages.items():
            try:
                subcounty = subcounties.get(name=subcounty_name)

                for village_name in village_names:
                    # Check if village exists
                    existing_villages = Village.objects.filter(name=village_name)

                    if existing_villages.count() > 1:
                        # Handle duplicates - keep the one with subcounty, delete others
                        villages_with_subcounty = existing_villages.filter(subcounty_obj__isnull=False).first()
                        if villages_with_subcounty:
                            village = villages_with_subcounty
                            # Delete duplicates without subcounty
                            existing_villages.exclude(id=village.id).delete()
                        else:
                            # Keep first, delete rest
                            village = existing_villages.first()
                            existing_villages.exclude(id=village.id).delete()

                        village.subcounty_obj = subcounty
                        village.is_program_area = True
                        village.save()
                        self.stdout.write(
                            self.style.WARNING(f'Fixed duplicate: {village_name} in {subcounty_name}')
                        )
                    elif existing_villages.count() == 1:
                        village = existing_villages.first()
                        village.subcounty_obj = subcounty
                        village.is_program_area = True
                        village.save()
                        self.stdout.write(
                            self.style.WARNING(f'Updated village: {village_name} to {subcounty_name}')
                        )
                    else:
                        # Create new village
                        village = Village.objects.create(
                            name=village_name,
                            subcounty_obj=subcounty,
                            country='Kenya',
                            is_program_area=True,
                            qualified_hhs_per_village=0,
                            distance_to_market=5,
                        )
                        self.stdout.write(
                            self.style.SUCCESS(f'Created village: {village_name} in {subcounty_name}')
                        )

            except SubCounty.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'SubCounty not found: {subcounty_name}')
                )

        # Update existing households to use West Pokot villages
        nairobi_villages = [
            'Kibera Central', 'Mathare North', 'Korogocho', 'Mukuru Kwa Njenga',
            'Kawangware', 'Viwandani', 'Dandora Phase 2', 'Huruma Estate'
        ]

        west_pokot_village_objects = Village.objects.filter(
            subcounty_obj__county__name='West Pokot'
        ).order_by('?')  # Random order

        if west_pokot_village_objects.exists():
            for nairobi_village_name in nairobi_villages:
                try:
                    nairobi_village = Village.objects.get(name=nairobi_village_name)
                    households = Household.objects.filter(village=nairobi_village)
                    count = households.count()

                    if count > 0:
                        # Distribute households across West Pokot villages
                        for i, household in enumerate(households):
                            new_village = west_pokot_village_objects[i % west_pokot_village_objects.count()]
                            household.village = new_village
                            household.save()

                        self.stdout.write(
                            self.style.SUCCESS(
                                f'Moved {count} households from {nairobi_village_name} to West Pokot villages'
                            )
                        )
                except Village.DoesNotExist:
                    pass

        self.stdout.write(
            self.style.SUCCESS('\n✓ Successfully updated villages to West Pokot')
        )
