from django.core.management.base import BaseCommand
from django.db import transaction
from apps.subscriptions.models import SubscriptionPlan
from apps.customer_installations.models import CustomerInstallation


class Command(BaseCommand):
    help = 'Hard delete all Subscription Plans and Installations'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirm the deletion without prompting',
        )

    def handle(self, *args, **options):
        # Get counts before deletion
        subscription_plans_count = SubscriptionPlan.objects.count()
        installations_count = CustomerInstallation.objects.count()
        
        self.stdout.write(self.style.WARNING(
            f"\nThis will permanently delete:\n"
            f"- {subscription_plans_count} Subscription Plans\n"
            f"- {installations_count} Customer Installations\n"
        ))
        
        if not options['confirm']:
            confirm = input("\nAre you sure you want to delete all these records? Type 'yes' to confirm: ")
            if confirm.lower() != 'yes':
                self.stdout.write(self.style.ERROR("Deletion cancelled."))
                return
        
        try:
            with transaction.atomic():
                # Delete in correct order to respect foreign key constraints
                
                # 1. Delete Customer Installations
                deleted_installations = CustomerInstallation.objects.all().delete()
                self.stdout.write(self.style.SUCCESS(
                    f"✓ Deleted {deleted_installations[0]} Customer Installations"
                ))
                
                # 2. Delete Subscription Plans
                deleted_plans = SubscriptionPlan.objects.all().delete()
                self.stdout.write(self.style.SUCCESS(
                    f"✓ Deleted {deleted_plans[0]} Subscription Plans"
                ))
                
                self.stdout.write(self.style.SUCCESS(
                    "\n✅ All records have been permanently deleted!"
                ))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(
                f"\n❌ Error during deletion: {str(e)}"
            ))
            self.stdout.write(self.style.WARNING(
                "Transaction rolled back - no records were deleted."
            ))
