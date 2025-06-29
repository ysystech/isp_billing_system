"""
Management command to set up initial permission categories.
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.roles.models import PermissionCategory


class Command(BaseCommand):
    help = 'Set up initial permission categories for the ISP billing system'

    def handle(self, *args, **options):
        # Define categories with better grouping
        categories = [
            {
                'name': 'Dashboard',
                'code': 'dashboard',
                'description': 'Main dashboard and system overview',
                'icon': 'fa-tachometer-alt',
                'order': 10,
            },
            {
                'name': 'Customer Management',
                'code': 'customers',
                'description': 'Manage customer profiles, contacts, and information',
                'icon': 'fa-users',
                'order': 20,
            },
            {
                'name': 'Barangay Management',
                'code': 'barangays',
                'description': 'Manage barangay records and geographic areas',
                'icon': 'fa-map-marker-alt',
                'order': 30,
            },
            {
                'name': 'Router Management',
                'code': 'routers',
                'description': 'Manage router inventory and equipment',
                'icon': 'fa-wifi',
                'order': 40,
            },
            {
                'name': 'Subscription Plans',
                'code': 'plans',
                'description': 'Manage internet plans and pricing',
                'icon': 'fa-list-alt',
                'order': 50,
            },
            {
                'name': 'LCP Infrastructure',
                'code': 'lcp',
                'description': 'Manage LCP, Splitter, and NAP infrastructure',
                'icon': 'fa-broadcast-tower',
                'order': 60,
            },
            {
                'name': 'Network Management',
                'code': 'network',
                'description': 'Network visualization and management',
                'icon': 'fa-network-wired',
                'order': 70,
            },
            {
                'name': 'Installations',
                'code': 'installations',
                'description': 'Manage customer installations and connections',
                'icon': 'fa-tools',
                'order': 80,
            },
            {
                'name': 'Customer Subscriptions',
                'code': 'subscriptions',
                'description': 'Process payments and manage active subscriptions',
                'icon': 'fa-credit-card',
                'order': 90,
            },
            {
                'name': 'Support Tickets',
                'code': 'tickets',
                'description': 'Customer support and ticket management',
                'icon': 'fa-ticket-alt',
                'order': 100,
            },
            {
                'name': 'User Management',
                'code': 'users',
                'description': 'Manage system users and roles',
                'icon': 'fa-users-cog',
                'order': 110,
            },
            {
                'name': 'Reports & Analytics',
                'code': 'reports',
                'description': 'Business reports and analytics',
                'icon': 'fa-chart-bar',
                'order': 120,
            },
            
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