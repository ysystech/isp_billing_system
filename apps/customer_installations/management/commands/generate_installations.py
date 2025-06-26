import random
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.customers.models import Customer
from apps.routers.models import Router
from apps.users.models import CustomUser
from apps.customer_installations.models import CustomerInstallation


class Command(BaseCommand):
    help = 'Generate sample customer installations'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=10,
            help='Number of installations to generate'
        )

    def handle(self, *args, **options):
        count = options['count']
        
        # Get available customers without installations
        customers_without_installation = Customer.objects.filter(
            installation__isnull=True,
            status='ACTIVE'
        )
        
        if not customers_without_installation.exists():
            self.stdout.write(
                self.style.WARNING('No customers without installations found')
            )
            return
        
        # Get available routers and technicians
        routers = list(Router.objects.all())
        technicians = list(CustomUser.objects.filter(user_type='TECHNICIAN', is_active=True))
        
        if not routers:
            self.stdout.write(
                self.style.WARNING('No routers available. Please generate routers first.')
            )
            return
            
        if not technicians:
            self.stdout.write(
                self.style.WARNING('No technicians available. Creating a sample technician...')
            )
            technician = CustomUser.objects.create_user(
                email='technician@example.com',
                username='technician@example.com',
                password='testpass123',
                first_name='John',
                last_name='Technician',
                user_type='TECHNICIAN'
            )
            technicians = [technician]
        
        # Generate installations
        installations_created = 0
        for customer in customers_without_installation[:count]:
            # Random installation date in the past 90 days
            days_ago = random.randint(1, 90)
            installation_date = timezone.now().date() - timedelta(days=days_ago)
            
            installation = CustomerInstallation.objects.create(
                customer=customer,
                router=random.choice(routers) if routers else None,
                installation_date=installation_date,
                installation_technician=random.choice(technicians),
                installation_notes=f"Installation completed successfully for {customer.full_name}",
                status='ACTIVE',
                is_active=True
            )
            
            installations_created += 1
            self.stdout.write(
                f"Created installation for {customer.full_name}"
            )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {installations_created} installations'
            )
        )
