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
            default=10,
            help='Number of subscriptions to generate per installation'
        )

    def handle(self, *args, **options):
        count = options['count']
        
        # Get all installations
        installations = CustomerInstallation.objects.filter(status='ACTIVE')
        
        if not installations.exists():
            self.stdout.write(
                self.style.WARNING('No active installations found. Please generate installations first.')
            )
            return
        
        # Get available plans and cashiers
        plans = list(SubscriptionPlan.objects.filter(is_active=True))
        cashiers = list(CustomUser.objects.filter(user_type='CASHIER', is_active=True))
        
        if not plans:
            self.stdout.write(
                self.style.WARNING('No active subscription plans found.')
            )
            return
            
        if not cashiers:
            self.stdout.write(
                self.style.WARNING('No cashiers available. Creating a sample cashier...')
            )
            cashier = CustomUser.objects.create_user(
                email='cashier@example.com',
                username='cashier@example.com',
                password='testpass123',
                first_name='Jane',
                last_name='Cashier',
                user_type='CASHIER'
            )
            cashiers = [cashier]
        
        payment_methods = ['CASH', 'GCASH', 'BANK']
        subscriptions_created = 0
        
        for installation in installations:
            # Start date is after installation
            current_date = installation.installation_date
            
            # Generate subscription history
            for i in range(min(count, random.randint(1, count))):
                plan = random.choice(plans)
                
                # Calculate start date (with possible gaps)
                if i > 0:
                    # Add random gap between subscriptions (0-5 days)
                    gap_days = random.randint(0, 5)
                    current_date = current_date + timedelta(days=gap_days)
                
                start_datetime = timezone.make_aware(
                    timezone.datetime.combine(current_date, timezone.datetime.min.time())
                )
                
                # Create subscription
                payment_method = random.choice(payment_methods)
                subscription = CustomerSubscription.objects.create(
                    installation=installation,
                    plan=plan,
                    start_date=start_datetime,
                    amount_paid=plan.price * Decimal(random.uniform(0.9, 1.1)),  # ±10% variation
                    payment_method=payment_method,
                    reference_number=f"REF{random.randint(100000, 999999)}" if payment_method != 'CASH' else '',
                    collected_by=random.choice(cashiers),
                    notes=f"Payment received via {payment_method}"
                )
                
                subscriptions_created += 1
                current_date = subscription.end_date.date()
                
                # Stop if we're past today
                if current_date > timezone.now().date():
                    break
            
            self.stdout.write(
                f"Created subscriptions for {installation.customer.full_name}"
            )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {subscriptions_created} subscriptions'
            )
        )
