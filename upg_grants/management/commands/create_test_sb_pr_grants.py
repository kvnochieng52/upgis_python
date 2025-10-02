"""
Management command to create test SB and PR grant applications
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from upg_grants.models import SBGrant, PRGrant
from business_groups.models import BusinessGroup
from programs.models import Program
from decimal import Decimal

User = get_user_model()


class Command(BaseCommand):
    help = 'Creates test SB and PR grants at different stages'

    def handle(self, *args, **kwargs):
        # Get a user
        user = User.objects.filter(is_superuser=True).first()
        if not user:
            user = User.objects.first()

        if not user:
            self.stdout.write(self.style.ERROR('No users found in the system'))
            return

        # Get business groups
        business_groups = list(BusinessGroup.objects.all()[:6])
        if len(business_groups) < 6:
            self.stdout.write(self.style.WARNING(f'Only {len(business_groups)} business groups available, need at least 6'))
            return

        # Get a program
        program = Program.objects.first()
        if not program:
            self.stdout.write(self.style.ERROR('No programs found in the system'))
            return

        # Create 3 SB Grants at different stages
        sb_grants_data = [
            {
                'business_group': business_groups[0],
                'status': 'pending',
                'business_plan': 'Start a vegetable farming collective to supply local markets with fresh produce. Focus on high-demand crops like kales, tomatoes, and onions.',
                'projected_income': Decimal('25000.00'),
                'startup_costs': Decimal('18000.00'),
                'monthly_expenses': Decimal('8000.00'),
            },
            {
                'business_group': business_groups[1],
                'status': 'under_review',
                'business_plan': 'Establish a dairy farming cooperative. Purchase 5 dairy cows and milking equipment. Supply fresh milk to local community and dairy processors.',
                'projected_income': Decimal('35000.00'),
                'startup_costs': Decimal('22000.00'),
                'monthly_expenses': Decimal('12000.00'),
                'reviewed_by': user,
                'review_date': timezone.now().date(),
                'review_notes': 'Strong business plan. Group has good training attendance. Recommended for approval.',
            },
            {
                'business_group': business_groups[2],
                'status': 'approved',
                'business_plan': 'Launch a poultry farming business with 100 chickens. Focus on egg production for local market. Sustainable income source.',
                'projected_income': Decimal('20000.00'),
                'startup_costs': Decimal('16000.00'),
                'monthly_expenses': Decimal('7000.00'),
                'reviewed_by': user,
                'review_date': timezone.now().date(),
                'review_notes': 'Excellent proposal. Group demonstrates strong commitment.',
                'approved_by': user,
                'approval_date': timezone.now().date(),
            },
        ]

        self.stdout.write(self.style.SUCCESS('\n=== Creating SB Grants ==='))
        for idx, data in enumerate(sb_grants_data):
            bg = data.pop('business_group')

            sb_grant = SBGrant.objects.create(
                program=program,
                business_group=bg,
                submitted_by=user,
                **data
            )

            # Calculate grant amount
            sb_grant.calculate_grant_amount()
            sb_grant.save()

            self.stdout.write(
                self.style.SUCCESS(
                    f'{idx+1}. SB Grant for {bg.name}: {sb_grant.get_status_display()} - KES {sb_grant.get_grant_amount():,.2f}'
                )
            )

        # Create 3 PR Grants at different stages
        # First, create approved SB grants for the PR grants to reference
        pr_sb_grants = []
        for i in range(3, 6):
            sb_grant = SBGrant.objects.create(
                program=program,
                business_group=business_groups[i],
                submitted_by=user,
                business_plan=f'Initial business for {business_groups[i].name}',
                status='disbursed',
                approved_by=user,
                approval_date=timezone.now().date(),
                disbursement_date=timezone.now().date(),
                disbursed_amount=Decimal('15000.00'),
                utilization_report=f'Successfully utilized SB grant. Business is running well.',
            )
            sb_grant.calculate_grant_amount()
            sb_grant.disbursed_amount = sb_grant.get_grant_amount()
            sb_grant.save()
            pr_sb_grants.append(sb_grant)

        pr_grants_data = [
            {
                'sb_grant': pr_sb_grants[0],
                'business_group': business_groups[3],
                'status': 'pending',
                'performance_assessment': 'Group has shown good performance. Regular savings, good attendance.',
                'revenue_generated': Decimal('45000.00'),
                'jobs_created': 3,
                'savings_accumulated': Decimal('12000.00'),
            },
            {
                'sb_grant': pr_sb_grants[1],
                'business_group': business_groups[4],
                'status': 'under_review',
                'performance_assessment': 'Excellent business growth. Expanded operations and created employment.',
                'revenue_generated': Decimal('65000.00'),
                'jobs_created': 5,
                'savings_accumulated': Decimal('18000.00'),
                'assessed_by': user,
                'assessment_date': timezone.now().date(),
                'performance_score': 85,
                'performance_rating': 'excellent',
            },
            {
                'sb_grant': pr_sb_grants[2],
                'business_group': business_groups[5],
                'status': 'approved',
                'performance_assessment': 'Outstanding performance. Business doubled revenue. Strong community impact.',
                'revenue_generated': Decimal('85000.00'),
                'jobs_created': 7,
                'savings_accumulated': Decimal('25000.00'),
                'assessed_by': user,
                'assessment_date': timezone.now().date(),
                'performance_score': 92,
                'performance_rating': 'excellent',
                'approved_by': user,
                'approval_date': timezone.now().date(),
            },
        ]

        self.stdout.write(self.style.SUCCESS('\n=== Creating PR Grants ==='))
        for idx, data in enumerate(pr_grants_data):
            bg = data.pop('business_group')

            pr_grant = PRGrant.objects.create(
                program=program,
                business_group=bg,
                **data
            )

            self.stdout.write(
                self.style.SUCCESS(
                    f'{idx+1}. PR Grant for {bg.name}: {pr_grant.get_status_display()} - KES {pr_grant.grant_amount:,.2f}'
                )
            )

        self.stdout.write(
            self.style.SUCCESS(f'\n✓ Successfully created 3 SB grants and 3 PR grants at different stages')
        )
