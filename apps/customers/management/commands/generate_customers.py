import random
from django.core.management.base import BaseCommand
from apps.customers.models import Customer
from apps.barangays.models import Barangay


class Command(BaseCommand):
    help = 'Generate sample customers for testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=10,
            help='Number of customers to generate'
        )

    def handle(self, *args, **options):
        count = options['count']
        
        # Get active barangays
        barangays = list(Barangay.objects.filter(is_active=True))
        
        if not barangays:
            self.stdout.write(
                self.style.WARNING('No active barangays found. Please add barangays first.')
            )
            return
        
        # Sample customer data
        first_names = ['Juan', 'Maria', 'Pedro', 'Ana', 'Jose', 'Rosa', 'Carlos', 'Elena', 'Miguel', 'Carmen']
        last_names = ['Cruz', 'Santos', 'Reyes', 'Garcia', 'Lopez', 'Martinez', 'Rodriguez', 'Hernandez', 'Gonzalez', 'Perez']
        
        statuses = ['ACTIVE', 'ACTIVE', 'ACTIVE', 'INACTIVE']  # More active customers
        
        created_count = 0
        for i in range(count):
            first_name = random.choice(first_names)
            last_name = random.choice(last_names)
            email = f"{first_name.lower()}.{last_name.lower()}{random.randint(1, 999)}@example.com"
            
            try:
                customer = Customer.objects.create(
                    first_name=first_name,
                    last_name=last_name,
                    email=email,
                    phone_primary=f"09{random.randint(100000000, 999999999)}",
                    barangay=random.choice(barangays),
                    street_address=f"{random.randint(1, 999)} {random.choice(['Main St', 'Rizal St', 'Bonifacio St', 'Mabini St'])}",
                    status=random.choice(statuses)
                )
                created_count += 1
                self.stdout.write(f"Created customer: {customer.full_name}")
                
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f"Failed to create customer: {e}")
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nSuccessfully created {created_count} customers'
            )
        )
