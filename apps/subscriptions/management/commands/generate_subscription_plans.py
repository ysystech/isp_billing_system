from decimal import Decimal
from django.core.management.base import BaseCommand
from apps.subscriptions.models import SubscriptionPlan


class Command(BaseCommand):
    help = 'Generate sample subscription plans for testing'

    def handle(self, *args, **options):
        # Sample plans data
        plans = [
            {
                'name': 'Basic Plan',
                'description': 'Perfect for light internet users. Suitable for browsing, social media, and basic streaming.',
                'speed': 25,
                'price': Decimal('699.00'),
                'is_active': True
            },
            {
                'name': 'Standard Plan',
                'description': 'Ideal for small families. Great for HD streaming, online gaming, and work from home.',
                'speed': 50,
                'price': Decimal('999.00'),
                'is_active': True
            },
            {
                'name': 'Premium Plan',
                'description': 'Best for heavy users and medium families. Perfect for 4K streaming, multiple devices, and heavy downloads.',
                'speed': 100,
                'price': Decimal('1499.00'),
                'is_active': True
            },
            {
                'name': 'Business Starter',
                'description': 'Entry-level business plan with priority support. Includes static IP and business-grade SLA.',
                'speed': 150,
                'price': Decimal('2499.00'),
                'is_active': True
            },
            {
                'name': 'Business Pro',
                'description': 'Professional business plan with dedicated support. Includes multiple static IPs and 99.9% uptime guarantee.',
                'speed': 300,
                'price': Decimal('4999.00'),
                'is_active': True
            },
            {
                'name': 'Enterprise',
                'description': 'Custom enterprise solution with dedicated fiber line. Includes 24/7 support and custom SLA.',
                'speed': 1000,
                'price': Decimal('9999.00'),
                'is_active': True
            },
            {
                'name': 'Student Plan',
                'description': 'Special discounted plan for students. Valid student ID required.',
                'speed': 30,
                'price': Decimal('499.00'),
                'is_active': True
            },
            {
                'name': 'Senior Citizen Plan',
                'description': 'Special plan for senior citizens with simplified support.',
                'speed': 20,
                'price': Decimal('399.00'),
                'is_active': True
            },
            {
                'name': 'Gamer Pro',
                'description': 'Optimized for gaming with low latency and high bandwidth. Includes gaming VPN access.',
                'speed': 200,
                'price': Decimal('1999.00'),
                'is_active': True
            },
            {
                'name': 'Legacy Plan',
                'description': 'Old plan no longer available for new customers.',
                'speed': 10,
                'price': Decimal('299.00'),
                'is_active': False
            }
        ]

        created_count = 0
        for plan_data in plans:
            plan, created = SubscriptionPlan.objects.get_or_create(
                name=plan_data['name'],
                defaults=plan_data
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'Created plan: {plan.name}'))
            else:
                self.stdout.write(self.style.WARNING(f'Plan already exists: {plan.name}'))
        
        self.stdout.write(self.style.SUCCESS(f'\nSuccessfully created {created_count} subscription plans'))
