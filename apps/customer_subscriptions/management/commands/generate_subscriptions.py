import random
from datetime import timedelta
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.customer_installations.models import CustomerInstallation
from apps.subscriptions.models import SubscriptionPlan
from apps.users.models import CustomUser
from apps.customer_subscriptions.models import CustomerSubscription


class Command(BaseCommand):
    help = 'Generate sample customer subscriptions'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=20,
            help='Number of subscriptions to generate'
        )

    def handle(self, *args, **options):
        count = options['count']
        
        # Get installations and plans
        installations = list(CustomerInstallation.objects.filter(status='ACTIVE'))
        plans = list(SubscriptionPlan.objects.filter(is_active=True))
        
        if not installations:
            self.stdout.write(self.style.WARNING('No active installations found'))
            return
            
        if not plans:
            self.stdout.write(self.style.WARNING('No active subscription plans found'))
            return
        
        # Get a cashier user
        cashier = CustomUser.objects.filter(user_type='CASHIER').first()
        if not cashier:
            cashier = CustomUser.objects.filter(is_staff=True).first()
        if not cashier:
            self.stdout.write(self.style.WARNING('No cashier or staff user found'))
            return
        
        subscriptions_created = 0
        subscription_types = ['one_month', 'fifteen_days', 'custom']
        
        for _ in range(count):
            # Random installation and plan
            installation = random.choice(installations)
            plan = random.choice(plans)
            subscription_type = random.choice(subscription_types)
            
            # Get latest subscription to determine start date
            latest_sub = CustomerSubscription.get_latest_subscription(installation)
            
            if latest_sub and latest_sub.end_date > timezone.now():
                # Continue from the end of current subscription
                start_date = latest_sub.end_date
            else:
                # Start from a random date in the past 30 days
                days_ago = random.randint(0, 30)
                start_date = timezone.now() - timedelta(days=days_ago)
            
            # Create subscription
            subscription = CustomerSubscription(
                customer_installation=installation,
                subscription_plan=plan,
                subscription_type=subscription_type,
                start_date=start_date,
                created_by=cashier
            )
            
            # Set custom amount if custom type
            if subscription_type == 'custom':
                # Random amount between 100 and plan price
                subscription.amount = Decimal(random.randint(100, int(plan.price)))
            
            # Calculate details and save
            subscription.calculate_subscription_details()
            subscription.save()
            
            subscriptions_created += 1
            self.stdout.write(
                f"Created {subscription.get_subscription_type_display()} subscription for "
                f"{installation.customer.full_name} - ₱{subscription.amount}"
            )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {subscriptions_created} subscriptions'
            )
        )
