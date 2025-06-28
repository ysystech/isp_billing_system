from django.core.management.base import BaseCommand
from django.db import transaction
from faker import Faker

from apps.customers.models import Customer


class Command(BaseCommand):
    help = "Create demo customers for testing"

    def add_arguments(self, parser):
        parser.add_argument(
            "--count",
            type=int,
            default=50,
            help="Number of customers to create"
        )

    def handle(self, *args, **options):
        fake = Faker("en_PH")  # Use Philippine locale
        count = options["count"]
        
        self.stdout.write(f"Creating {count} demo customers...")
        
        created = 0
        with transaction.atomic():
            for i in range(count):
                try:
                    # Generate Philippine-style data
                    first_name = fake.first_name()
                    last_name = fake.last_name()
                    
                    customer = Customer.objects.create(
                        first_name=first_name,
                        last_name=last_name,
                        email=f"{first_name.lower()}.{last_name.lower()}{i}@example.com",
                        phone_primary=f"+639{fake.numerify('#########')}",
                        street_address=fake.street_address(),
                        barangay=fake.random_element(elements=("Carmen", "Nazareth", "Kauswagan", "Lapasan", "Macasandig", "Camaman-an")),
                        status=fake.random_element(elements=[Customer.ACTIVE, Customer.ACTIVE, Customer.ACTIVE, Customer.INACTIVE, Customer.SUSPENDED]),
                        notes=fake.text(max_nb_chars=150) if fake.boolean(chance_of_getting_true=20) else "",
                    )
                    created += 1
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"Failed to create customer: {e}"))
        
        self.stdout.write(self.style.SUCCESS(f"Successfully created {created} demo customers!"))
