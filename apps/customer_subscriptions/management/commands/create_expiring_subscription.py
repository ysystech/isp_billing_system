from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from apps.customer_subscriptions.models import CustomerSubscription
from apps.customer_installations.models import CustomerInstallation
from apps.subscriptions.models import SubscriptionPlan
from decimal import Decimal


class Command(BaseCommand):
    help = 'Create a test subscription that expires in 5 minutes'

    def handle(self, *args, **options):
        # Get an active installation
        installation = CustomerInstallation.objects.filter(status='ACTIVE').first()
        if not installation:
            self.stdout.write(self.style.ERROR('No active installations found'))
            return
        
        # Get a subscription plan
        plan = SubscriptionPlan.objects.filter(is_active=True).first()
        if not plan:
            self.stdout.write(self.style.ERROR('No active subscription plans found'))
            return
        
        # Create a subscription that expires in 5 minutes
        now = timezone.now()
        subscription = CustomerSubscription.objects.create(
            customer_installation=installation,
            subscription_plan=plan,
            subscription_type='custom',
            amount=Decimal('100'),
            start_date=now - timedelta(minutes=10),
            end_date=now + timedelta(minutes=5),
            days_added=Decimal('0.01'),  # Very short subscription
            status='ACTIVE',
            created_by=None
        )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Created test subscription for {installation.customer.full_name}\n'
                f'Expires at: {subscription.end_date.strftime("%Y-%m-%d %H:%M:%S")}\n'
                f'Current time: {now.strftime("%Y-%m-%d %H:%M:%S")}\n'
                f'Expires in 5 minutes!'
            )
        )
