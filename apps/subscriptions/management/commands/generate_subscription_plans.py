from decimal import Decimal
from django.core.management.base import BaseCommand
from apps.subscriptions.models import SubscriptionPlan


class Command(BaseCommand):
    help = 'Generate sample subscription plans for testing'

    def handle(self, *args, **options):
        # Sample plans data with day_count for prepaid model
        plans = [
            {
                'name': 'Daily Basic',
                'description': 'Perfect for testing or temporary use. 25Mbps for 1 day.',
                'speed': 25,
                'price': Decimal('50.00'),
                'day_count': 1,
                'is_active': True
            },
            {
                'name': '3-Day Promo',
                'description': 'Weekend special. 50Mbps for 3 days.',
                'speed': 50,
                'price': Decimal('150.00'),
                'day_count': 3,
                'is_active': True
            },
            {
                'name': 'Weekly Standard',
                'description': 'One week of reliable internet. 50Mbps for 7 days.',
                'speed': 50,
                'price': Decimal('300.00'),
                'day_count': 7,
                'is_active': True
            },
            {
                'name': 'Quincenal Basic',
                'description': 'Half month basic plan. 25Mbps for 15 days.',
                'speed': 25,
                'price': Decimal('500.00'),
                'day_count': 15,
                'is_active': True
            },
            {
                'name': 'Quincenal Standard',
                'description': 'Half month standard plan. 50Mbps for 15 days.',
                'speed': 50,
                'price': Decimal('700.00'),
                'day_count': 15,
                'is_active': True
            },
            {
                'name': 'Quincenal Premium',
                'description': 'Half month premium plan. 100Mbps for 15 days.',
                'speed': 100,
                'price': Decimal('1000.00'),
                'day_count': 15,
                'is_active': True
            },
            {
                'name': 'Monthly Basic',
                'description': 'Full month basic plan. 25Mbps for 30 days.',
                'speed': 25,
                'price': Decimal('900.00'),
                'day_count': 30,
                'is_active': True
            },
            {
                'name': 'Monthly Standard',
                'description': 'Full month standard plan. 50Mbps for 30 days.',
                'speed': 50,
                'price': Decimal('1300.00'),
                'day_count': 30,
                'is_active': True
            },
            {
                'name': 'Monthly Premium',
                'description': 'Full month premium plan. 100Mbps for 30 days.',
                'speed': 100,
                'price': Decimal('1800.00'),
                'day_count': 30,
                'is_active': True
            },
            {
                'name': 'Monthly Ultra',
                'description': 'Full month ultra-fast plan. 200Mbps for 30 days.',
                'speed': 200,
                'price': Decimal('2500.00'),
                'day_count': 30,
                'is_active': True
            },
            {
                'name': 'Student Weekly',
                'description': 'Special student rate. 30Mbps for 7 days. Valid ID required.',
                'speed': 30,
                'price': Decimal('200.00'),
                'day_count': 7,
                'is_active': True
            },
            {
                'name': 'Business Monthly',
                'description': 'Business plan with priority support. 300Mbps for 30 days.',
                'speed': 300,
                'price': Decimal('5000.00'),
                'day_count': 30,
                'is_active': True
            },
            {
                'name': 'Trial Plan',
                'description': 'One-time trial for new customers. 20Mbps for 3 days.',
                'speed': 20,
                'price': Decimal('99.00'),
                'day_count': 3,
                'is_active': False  # Can be activated for promotions
            }
        ]

        # First, update existing plans or create new ones
        created_count = 0
        updated_count = 0
        
        for plan_data in plans:
            plan, created = SubscriptionPlan.objects.update_or_create(
                name=plan_data['name'],
                defaults=plan_data
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'Created plan: {plan.name}'))
            else:
                updated_count += 1
                self.stdout.write(self.style.WARNING(f'Updated plan: {plan.name}'))
        
        self.stdout.write(self.style.SUCCESS(
            f'\nSuccessfully created {created_count} and updated {updated_count} subscription plans'
        ))
