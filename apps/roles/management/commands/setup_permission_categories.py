"""
Management command to set up initial permission categories.
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.roles.models import PermissionCategory


class Command(BaseCommand):
    help = 'Set up initial permission categories for the ISP billing system'

    def handle(self, *args, **options):
        categories = [
            {
                'name': 'Customer Management',
                'code': 'customers',
                'icon': 'fa-users',
                'order': 10,
                'description': 'Manage customer information, contacts, and profiles'
            },
            {
                'name': 'Billing & Subscriptions',
                'code': 'billing',
                'icon': 'fa-credit-card',
                'order': 20,
                'description': 'Handle customer subscriptions, payments, and receipts'
            },
            {
                'name': 'Infrastructure Management',
                'code': 'infrastructure',
                'icon': 'fa-broadcast-tower',
                'order': 30,
                'description': 'Manage LCP, splitters, NAPs, and network infrastructure'
            },
            {
                'name': 'Technical Operations',
                'code': 'technical',
                'icon': 'fa-tools',
                'order': 40,
                'description': 'Handle installations, router management, and field operations'
            },
            {
                'name': 'Support & Tickets',
                'code': 'support',
                'icon': 'fa-ticket-alt',
                'order': 50,
                'description': 'Customer support tickets and issue tracking'
            },
            {
                'name': 'Reports & Analytics',
                'code': 'reports',
                'icon': 'fa-chart-bar',
                'order': 60,
                'description': 'View and generate business reports and analytics'
            },
            {
                'name': 'System Administration',
                'code': 'admin',
                'icon': 'fa-cog',
                'order': 70,
                'description': 'User management, roles, and system configuration'
            },
            {
                'name': 'Basic Operations',
                'code': 'basic',
                'icon': 'fa-home',
                'order': 5,
                'description': 'Basic system access and navigation'
            }
        ]
        
        created_count = 0
        updated_count = 0
        
        with transaction.atomic():
            for cat_data in categories:
                category, created = PermissionCategory.objects.update_or_create(
                    code=cat_data['code'],
                    defaults={
                        'name': cat_data['name'],
                        'description': cat_data['description'],
                        'icon': cat_data['icon'],
                        'order': cat_data['order']
                    }
                )
                
                if created:
                    created_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'Created category: {category.name}')
                    )
                else:
                    updated_count += 1
                    self.stdout.write(
                        self.style.WARNING(f'Updated category: {category.name}')
                    )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nSummary: Created {created_count} categories, Updated {updated_count} categories'
            )
        )
