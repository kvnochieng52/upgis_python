"""
Management command to create test grant applications
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from upg_grants.models import HouseholdGrantApplication
from households.models import Household
from programs.models import Program
from decimal import Decimal
import random

User = get_user_model()


class Command(BaseCommand):
    help = 'Creates test grant applications with different grant types'

    def handle(self, *args, **kwargs):
        # Get a user to submit applications
        user = User.objects.filter(is_superuser=True).first()
        if not user:
            user = User.objects.first()

        if not user:
            self.stdout.write(self.style.ERROR('No users found in the system'))
            return

        # Get households
        households = list(Household.objects.all()[:6])
        if len(households) < 5:
            self.stdout.write(self.style.WARNING(f'Only {len(households)} households available'))

        # Get a program (optional)
        program = Program.objects.first()

        # Grant application data
        grant_data = [
            {
                'grant_type': 'seed_business',
                'title': 'Vegetable Farming Seed Capital',
                'purpose': 'To establish a vegetable farming business selling fresh produce to the local market. This will provide sustainable income for the household.',
                'business_plan': 'Start with 1-acre plot of tomatoes, kales, and spinach. Target local market and schools. Expected harvest cycle: 3 months.',
                'expected_outcomes': 'Generate monthly income of KES 15,000 after 3 months. Create employment for 2 additional laborers.',
                'budget_breakdown': {
                    'Seeds and seedlings': 3000,
                    'Fertilizers and pesticides': 4000,
                    'Irrigation system': 5000,
                    'Farm tools': 3000,
                },
            },
            {
                'grant_type': 'performance_recognition',
                'title': 'Poultry Expansion Performance Grant',
                'purpose': 'Recognition grant for successful completion of initial poultry business. Funds will be used to expand from 50 to 200 chickens.',
                'business_plan': 'Expand existing successful poultry farm. Purchase 150 additional layer chickens. Build larger coop. Expected ROI within 6 months.',
                'expected_outcomes': 'Triple current egg production. Increase monthly income from KES 8,000 to KES 25,000. Supply eggs to 3 local shops.',
                'budget_breakdown': {
                    'Chickens (150 @ 250)': 37500,
                    'Expanded chicken coop': 15000,
                    'Initial feed stock': 8000,
                    'Feeders and waterers': 4500,
                },
            },
            {
                'grant_type': 'livelihood',
                'title': 'Tailoring Equipment for Income Generation',
                'purpose': 'Purchase tailoring equipment to start home-based tailoring business. Will provide clothing alterations and custom garments to community.',
                'expected_outcomes': 'Establish home-based tailoring business serving 20+ customers monthly. Generate steady income of KES 10,000/month.',
                'budget_breakdown': {
                    'Sewing machine': 18000,
                    'Fabric and materials': 7000,
                    'Table and supplies': 5000,
                },
            },
            {
                'grant_type': 'emergency',
                'title': 'Medical Emergency Support',
                'purpose': 'Emergency medical assistance for household member requiring urgent surgery. Critical health situation requiring immediate financial support.',
                'expected_outcomes': 'Complete medical treatment successfully. Return household member to health and productive capacity within 2 months.',
                'budget_breakdown': {
                    'Hospital bills': 35000,
                    'Medications': 8000,
                    'Transportation': 2000,
                },
            },
            {
                'grant_type': 'education',
                'title': 'Secondary School Fees Support',
                'purpose': 'Educational support for 2 children to complete secondary school. School fees are preventing children from attending despite good academic performance.',
                'expected_outcomes': 'Both children complete Form 3 and 4. Improve chances of further education and better employment opportunities.',
                'budget_breakdown': {
                    'School fees (2 students)': 24000,
                    'School uniforms': 4000,
                    'Books and supplies': 6000,
                    'Boarding costs': 16000,
                },
            },
            {
                'grant_type': 'housing',
                'title': 'House Roof Repair and Improvement',
                'purpose': 'Repair leaking roof and improve housing conditions. Current roof is deteriorating and poses health risk during rainy season.',
                'expected_outcomes': 'Safe, weatherproof housing. Improved health conditions. Reduced medical expenses from rain-related illnesses.',
                'budget_breakdown': {
                    'Iron sheets (30 pieces)': 21000,
                    'Timber and poles': 8000,
                    'Nails and fixtures': 3000,
                    'Labor costs': 8000,
                },
            },
        ]

        created_count = 0
        for idx, data in enumerate(grant_data):
            if idx >= len(households):
                break

            household = households[idx]

            # Calculate requested amount from budget breakdown
            requested_amount = sum(data['budget_breakdown'].values())

            # Create application
            application = HouseholdGrantApplication.objects.create(
                household=household,
                submitted_by=user,
                program=program if random.choice([True, False]) else None,  # Randomly assign program
                grant_type=data['grant_type'],
                title=data['title'],
                purpose=data['purpose'],
                business_plan=data.get('business_plan', ''),
                expected_outcomes=data['expected_outcomes'],
                requested_amount=Decimal(str(requested_amount)),
                budget_breakdown=data['budget_breakdown'],
                status=random.choice(['submitted', 'under_review', 'approved', 'submitted']),
                submission_date=timezone.now(),
            )

            created_count += 1
            self.stdout.write(
                self.style.SUCCESS(
                    f'Created {data["grant_type"]} grant for {household.name}: {data["title"]} (KES {requested_amount:,})'
                )
            )

        self.stdout.write(
            self.style.SUCCESS(f'\nSuccessfully created {created_count} test grant applications')
        )
