"""
Django management command to create sample household data for testing
Usage: python manage.py create_sample_data
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import date, datetime, timedelta
import random

from core.models import Village, Program, Mentor
from households.models import (
    Household, HouseholdMember, HouseholdProgram, UPGMilestone,
    PPI, HouseholdSurvey
)
from training.models import (
    MentoringVisit, PhoneNudge, MentoringReport, Training, TrainingAttendance
)

User = get_user_model()


class Command(BaseCommand):
    help = 'Create sample household data for testing the UPG system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--households',
            type=int,
            default=50,
            help='Number of households to create (default: 50)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before creating new data'
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing data...')
            self.clear_data()

        households_count = options['households']
        self.stdout.write(f'Creating {households_count} sample households...')

        # Create basic data first
        self.create_villages()
        self.create_programs()
        self.create_mentors()

        # Create households and related data
        self.create_households(households_count)
        self.create_household_programs()
        self.create_milestones()
        self.create_mentoring_activities()

        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {households_count} households with sample data!')
        )

    def clear_data(self):
        """Clear existing data"""
        MentoringVisit.objects.all().delete()
        PhoneNudge.objects.all().delete()
        MentoringReport.objects.all().delete()
        UPGMilestone.objects.all().delete()
        HouseholdProgram.objects.all().delete()
        HouseholdMember.objects.all().delete()
        HouseholdSurvey.objects.all().delete()
        PPI.objects.all().delete()
        Household.objects.all().delete()
        self.stdout.write('Existing data cleared.')

    def create_villages(self):
        """Create sample villages"""
        villages_data = [
            {'name': 'Kibera Central', 'subcounty': 'Kibra', 'saturation': 'High', 'qualified_hhs_per_village': 120},
            {'name': 'Mathare North', 'subcounty': 'Mathare', 'saturation': 'Medium', 'qualified_hhs_per_village': 85},
            {'name': 'Korogocho', 'subcounty': 'Kasarani', 'saturation': 'High', 'qualified_hhs_per_village': 95},
            {'name': 'Mukuru Kwa Njenga', 'subcounty': 'Embakasi East', 'saturation': 'Medium', 'qualified_hhs_per_village': 110},
            {'name': 'Kawangware', 'subcounty': 'Dagoretti North', 'saturation': 'Low', 'qualified_hhs_per_village': 70},
            {'name': 'Viwandani', 'subcounty': 'Embakasi East', 'saturation': 'Medium', 'qualified_hhs_per_village': 80},
            {'name': 'Dandora Phase 2', 'subcounty': 'Embakasi North', 'saturation': 'High', 'qualified_hhs_per_village': 100},
            {'name': 'Huruma Estate', 'subcounty': 'Mathare', 'saturation': 'Low', 'qualified_hhs_per_village': 60},
        ]

        for village_data in villages_data:
            village, created = Village.objects.get_or_create(
                name=village_data['name'],
                defaults=village_data
            )
            if created:
                self.stdout.write(f'Created village: {village.name}')

    def create_programs(self):
        """Create sample UPG programs"""
        programs_data = [
            {
                'name': 'UPG Nairobi FY25 Cycle 1',
                'cycle': 'FY25C1',
                'office': 'Nairobi',
                'start_date': date(2024, 10, 1),
                'end_date': date(2025, 9, 30),
                'status': 'active',
                'target_households': 200,
                'target_villages': 5,
            },
            {
                'name': 'UPG Nairobi FY24 Cycle 2',
                'cycle': 'FY24C2',
                'office': 'Nairobi',
                'start_date': date(2024, 4, 1),
                'end_date': date(2025, 3, 31),
                'status': 'active',
                'target_households': 150,
                'target_villages': 4,
            }
        ]

        for program_data in programs_data:
            program, created = Program.objects.get_or_create(
                name=program_data['name'],
                defaults=program_data
            )
            if created:
                self.stdout.write(f'Created program: {program.name}')

    def create_mentors(self):
        """Create sample mentor users and mentor profiles"""
        mentors_data = [
            {'username': 'mentor1', 'first_name': 'Grace', 'last_name': 'Wanjiku', 'email': 'grace.wanjiku@upg.org'},
            {'username': 'mentor2', 'first_name': 'John', 'last_name': 'Kiprotich', 'email': 'john.kiprotich@upg.org'},
            {'username': 'mentor3', 'first_name': 'Mary', 'last_name': 'Achieng', 'email': 'mary.achieng@upg.org'},
            {'username': 'mentor4', 'first_name': 'David', 'last_name': 'Mwangi', 'email': 'david.mwangi@upg.org'},
        ]

        for mentor_data in mentors_data:
            user, created = User.objects.get_or_create(
                username=mentor_data['username'],
                defaults={
                    'first_name': mentor_data['first_name'],
                    'last_name': mentor_data['last_name'],
                    'email': mentor_data['email'],
                    'role': 'mentor',
                    'is_staff': False,
                }
            )
            if created:
                user.set_password('password123')
                user.save()
                self.stdout.write(f'Created mentor user: {user.get_full_name()}')

            # Create Mentor profile
            mentor_profile, created = Mentor.objects.get_or_create(
                user=user,
                defaults={
                    'first_name': mentor_data['first_name'],
                    'last_name': mentor_data['last_name'],
                    'office': 'Nairobi',
                }
            )
            if created:
                self.stdout.write(f'Created mentor profile: {mentor_profile}')

    def create_households(self, count):
        """Create sample households"""
        villages = list(Village.objects.all())

        # Kenyan names for realistic data
        first_names = [
            'Grace', 'Mary', 'Jane', 'Rose', 'Lucy', 'Ann', 'Catherine', 'Margaret', 'Susan', 'Joyce',
            'John', 'Peter', 'James', 'David', 'Joseph', 'Michael', 'Daniel', 'Paul', 'Samuel', 'Francis',
            'Faith', 'Hope', 'Mercy', 'Esther', 'Ruth', 'Naomi', 'Rachel', 'Sarah', 'Rebecca', 'Hannah'
        ]

        last_names = [
            'Wanjiku', 'Mwangi', 'Kamau', 'Njeri', 'Kiprotich', 'Achieng', 'Otieno', 'Wanjira',
            'Kariuki', 'Njoroge', 'Mutua', 'Kimani', 'Ochieng', 'Gitau', 'Waithaka', 'Kihara',
            'Macharia', 'Mbugua', 'Waweru', 'Gathoni', 'Muthoni', 'Nyambura', 'Wangari', 'Njambi'
        ]

        for i in range(count):
            village = random.choice(villages)
            first_name = random.choice(first_names)
            last_name = random.choice(last_names)

            household = Household.objects.create(
                village=village,
                name=f'{first_name} {last_name}',
                national_id=f'{random.randint(20000000, 40000000)}',
                phone_number=f'+254{random.randint(700000000, 799999999)}',
                disability=random.choice([True, False]) if random.random() < 0.15 else False,
                gps_latitude=-1.2921 + random.uniform(-0.1, 0.1),  # Around Nairobi
                gps_longitude=36.8219 + random.uniform(-0.1, 0.1),
            )

            # Create household members
            self.create_household_members(household, first_name, last_name)

            # Create PPI scores
            self.create_ppi_scores(household)

            # Create surveys
            self.create_household_surveys(household)

    def create_household_members(self, household, head_first_name, head_last_name):
        """Create household members"""
        # Create household head
        HouseholdMember.objects.create(
            household=household,
            name=f'{head_first_name} {head_last_name}',
            gender=random.choice(['male', 'female']),
            age=random.randint(25, 55),
            relationship_to_head='head',
            education_level=random.choice(['none', 'primary', 'secondary']),
            is_program_participant=True,
        )

        # Create spouse (sometimes)
        if random.random() < 0.7:
            spouse_names = ['Margaret', 'Grace', 'Peter', 'John', 'Mary', 'James']
            head_member = household.members.first()
            HouseholdMember.objects.create(
                household=household,
                name=f'{random.choice(spouse_names)} {head_last_name}',
                gender='female' if head_member.gender == 'male' else 'male',
                age=random.randint(22, 50),
                relationship_to_head='spouse',
                education_level=random.choice(['none', 'primary', 'secondary']),
                is_program_participant=False,
            )

        # Create children
        num_children = random.randint(1, 5)
        child_names = ['Faith', 'Hope', 'Joy', 'Blessing', 'Gift', 'Emmanuel', 'Joshua', 'Ruth', 'Daniel']

        for i in range(num_children):
            HouseholdMember.objects.create(
                household=household,
                name=f'{random.choice(child_names)} {head_last_name}',
                gender=random.choice(['male', 'female']),
                age=random.randint(1, 18),
                relationship_to_head='child',
                education_level='none' if random.randint(1, 18) < 6 else random.choice(['primary', 'secondary']),
                is_program_participant=False,
            )

    def create_ppi_scores(self, household):
        """Create PPI scores for household"""
        # Baseline PPI
        PPI.objects.create(
            household=household,
            name='Baseline PPI',
            eligibility_score=random.randint(15, 45),  # Poor households
            assessment_date=date.today() - timedelta(days=random.randint(30, 365)),
        )

        # Some households might have midline/endline PPI
        if random.random() < 0.3:
            PPI.objects.create(
                household=household,
                name='Midline PPI',
                eligibility_score=random.randint(20, 55),  # Slight improvement
                assessment_date=date.today() - timedelta(days=random.randint(1, 180)),
            )

    def create_household_surveys(self, household):
        """Create household surveys"""
        HouseholdSurvey.objects.create(
            household=household,
            survey_type='baseline',
            name='Baseline Household Survey',
            survey_date=date.today() - timedelta(days=random.randint(30, 365)),
            income_level=random.choice(['Very Low', 'Low', 'Below Average']),
            assets_owned='Basic furniture, cooking utensils, radio',
            savings_amount=random.randint(0, 5000),
        )

    def create_household_programs(self):
        """Enroll households in UPG programs"""
        programs = list(Program.objects.all())  # All programs are graduation programs in this system
        households = list(Household.objects.all())
        mentors = list(Mentor.objects.all())

        for household in households:
            if random.random() < 0.8:  # 80% enrollment rate
                program = random.choice(programs)
                mentor = random.choice(mentors) if mentors else None

                enrollment_date = program.start_date + timedelta(days=random.randint(0, 60))

                HouseholdProgram.objects.create(
                    household=household,
                    program=program,
                    mentor=mentor,
                    participation_status=random.choice(['enrolled', 'active', 'graduated']),
                    enrollment_date=enrollment_date,
                )

    def create_milestones(self):
        """Create UPG milestones for enrolled households"""
        household_programs = HouseholdProgram.objects.all()

        for hp in household_programs:
            months_since_enrollment = (date.today() - hp.enrollment_date).days // 30

            # Create milestones based on how long they've been enrolled
            for i, (milestone_key, milestone_name) in enumerate(UPGMilestone.MILESTONE_CHOICES):
                if i < months_since_enrollment:
                    # Past milestones - mostly completed
                    status = random.choices(
                        ['completed', 'completed', 'completed', 'delayed', 'skipped'],
                        weights=[70, 15, 10, 4, 1]
                    )[0]

                    target_date = hp.enrollment_date + timedelta(days=30 * (i + 1))
                    completion_date = target_date + timedelta(days=random.randint(-5, 15)) if status == 'completed' else None

                elif i == months_since_enrollment:
                    # Current milestone - in progress
                    status = random.choice(['in_progress', 'not_started'])
                    target_date = hp.enrollment_date + timedelta(days=30 * (i + 1))
                    completion_date = None
                else:
                    # Future milestones - not started
                    status = 'not_started'
                    target_date = hp.enrollment_date + timedelta(days=30 * (i + 1))
                    completion_date = None

                UPGMilestone.objects.create(
                    household_program=hp,
                    milestone=milestone_key,
                    status=status,
                    target_date=target_date,
                    completion_date=completion_date,
                    notes=f'Sample milestone progress for {milestone_name}' if status == 'completed' else '',
                )

    def create_mentoring_activities(self):
        """Create sample mentoring visits and phone nudges"""
        household_programs = HouseholdProgram.objects.filter(mentor__isnull=False)

        for hp in household_programs:
            mentor_user = hp.mentor.user
            household = hp.household

            # Create visits (1-3 per month since enrollment)
            months_enrolled = (date.today() - hp.enrollment_date).days // 30
            num_visits = random.randint(months_enrolled, months_enrolled * 3)

            for i in range(num_visits):
                visit_date = hp.enrollment_date + timedelta(days=random.randint(0, (date.today() - hp.enrollment_date).days))

                MentoringVisit.objects.create(
                    name=f'{random.choice(["Weekly Check-in", "Business Planning", "Problem Solving", "Training Follow-up"])} - {household.name}',
                    household=household,
                    mentor=mentor_user,
                    topic=random.choice([
                        'Business planning and strategy',
                        'Financial management training',
                        'Savings group participation',
                        'Market linkage support',
                        'Problem-solving session',
                        'Skills development',
                        'Health and nutrition education'
                    ]),
                    visit_type=random.choice(['on_site', 'phone', 'virtual']),
                    visit_date=visit_date,
                    notes=f'Regular mentoring visit. Discussed progress and provided guidance on business development.',
                )

            # Create phone nudges (2-5 per month)
            num_nudges = random.randint(months_enrolled * 2, months_enrolled * 5)

            for i in range(num_nudges):
                call_date = timezone.now() - timedelta(days=random.randint(0, (date.today() - hp.enrollment_date).days))

                PhoneNudge.objects.create(
                    household=household,
                    mentor=mentor_user,
                    nudge_type=random.choice(['reminder', 'follow_up', 'support', 'check_in', 'business_advice']),
                    call_date=call_date,
                    duration_minutes=random.randint(5, 30),
                    notes=f'Regular check-in call to provide support and guidance.',
                    successful_contact=random.choice([True, True, True, False]),  # 75% success rate
                )

        # Create some mentoring reports
        mentors = User.objects.filter(role='mentor')
        for mentor in mentors:
            # Create a recent monthly report
            if random.random() < 0.7:  # 70% chance
                period_start = date.today().replace(day=1) - timedelta(days=30)
                period_end = date.today().replace(day=1) - timedelta(days=1)

                # Count actual activities for the period
                visits_count = MentoringVisit.objects.filter(
                    mentor=mentor,
                    visit_date__gte=period_start,
                    visit_date__lte=period_end
                ).count()

                nudges_count = PhoneNudge.objects.filter(
                    mentor=mentor,
                    call_date__gte=period_start,
                    call_date__lte=period_end
                ).count()

                households_visited = MentoringVisit.objects.filter(
                    mentor=mentor,
                    visit_date__gte=period_start,
                    visit_date__lte=period_end
                ).values('household').distinct().count()

                MentoringReport.objects.create(
                    mentor=mentor,
                    reporting_period='monthly',
                    period_start=period_start,
                    period_end=period_end,
                    households_visited=households_visited,
                    phone_nudges_made=nudges_count,
                    trainings_conducted=random.randint(1, 3),
                    new_households_enrolled=random.randint(0, 2),
                    key_activities=f'Conducted {visits_count} household visits focusing on business development and financial literacy. Provided ongoing support through phone check-ins and problem-solving sessions.',
                    challenges_faced='Some households faced challenges with market access due to transportation costs. Weather conditions affected some planned visits.',
                    successes_achieved='Three households successfully launched their businesses. Improved savings habits observed across most households.',
                    next_period_plans='Focus on market linkage activities and group formation for collective bargaining power.',
                )

        self.stdout.write(f'Created mentoring activities for {household_programs.count()} household-mentor pairs')