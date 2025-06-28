from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.customer_subscriptions.models import CustomerSubscription
from apps.customer_installations.models import CustomerInstallation


class Command(BaseCommand):
    help = 'Check subscription statuses'

    def handle(self, *args, **options):
        # Check installations
        print("\n=== INSTALLATIONS ===")
        installations = CustomerInstallation.objects.all()
        for inst in installations:
            print(f"\nInstallation ID: {inst.id}")
            print(f"Customer: {inst.customer.full_name}")
            print(f"Status: {inst.status}")
            print(f"Total subscriptions: {inst.subscriptions.count()}")
            
            # Check subscriptions for this installation
            active_subs = inst.subscriptions.filter(status='ACTIVE')
            print(f"Active subscriptions (by status field): {active_subs.count()}")
            
            # Check if any should be expired
            now = timezone.now()
            for sub in active_subs[:3]:
                print(f"\n  Sub ID {sub.id}:")
                print(f"  - Plan: {sub.subscription_plan.name}")
                print(f"  - End date: {sub.end_date}")
                print(f"  - Current time: {now}")
                print(f"  - Should be expired? {sub.end_date < now}")
                print(f"  - Status: {sub.status}")
                
                # Update status if needed
                sub.update_status()
                if sub.status != 'ACTIVE':
                    print(f"  - Status after update: {sub.status}")
                    sub.save()
