from django.core.management.base import BaseCommand
from django.db.models import Sum
from decimal import Decimal
from savings_groups.models import BusinessSavingsGroup, BSGMember, SavingsRecord


class Command(BaseCommand):
    help = 'Recalculate member total_savings from SavingsRecord data'

    def add_arguments(self, parser):
        parser.add_argument('--group-id', type=int, help='Specific savings group ID to fix')

    def handle(self, *args, **options):
        group_id = options.get('group_id')

        if group_id:
            groups = BusinessSavingsGroup.objects.filter(pk=group_id)
        else:
            groups = BusinessSavingsGroup.objects.filter(is_active=True)

        for sg in groups:
            self.stdout.write(f"\nProcessing: {sg.name}")

            # Recalculate each member's total from their savings records
            for member in sg.bsg_members.filter(is_active=True):
                calculated_total = SavingsRecord.objects.filter(member=member).aggregate(
                    total=Sum('amount'))['total'] or Decimal('0')

                old_total = member.total_savings
                member.total_savings = calculated_total
                member.save()

                self.stdout.write(
                    f"  {member.household.name}: {old_total} -> {calculated_total}"
                )

            # Recalculate group total
            group_total = sg.bsg_members.filter(is_active=True).aggregate(
                total=Sum('total_savings'))['total'] or Decimal('0')

            old_group_total = sg.savings_to_date
            sg.savings_to_date = group_total
            sg.save()

            self.stdout.write(
                self.style.SUCCESS(
                    f"\n  Group Total: {old_group_total} -> {group_total}"
                )
            )

        self.stdout.write(self.style.SUCCESS('\nDone!'))
