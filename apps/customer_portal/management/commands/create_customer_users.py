from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from apps.customers.models import Customer
from apps.tenants.models import Tenant

User = get_user_model()


class Command(BaseCommand):
    help = 'Create user accounts for existing customers'

    def add_arguments(self, parser):
        parser.add_argument(
            '--customer-id',
            type=int,
            help='Create user for specific customer ID',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes',
        )

    def handle(self, *args, **options):
        customer_id = options.get('customer_id')
        dry_run = options.get('dry_run')

        if customer_id:
            customers = Customer.objects.filter(id=customer_id)
        else:
            # Get all customers without user accounts
            customers = Customer.objects.filter(user__isnull=True)

        self.stdout.write(f"Found {customers.count()} customers without user accounts")

        created_count = 0
        for customer in customers:
            # Check if user with this email already exists
            existing_user = User.objects.filter(email=customer.email).first()
            
            if existing_user:
                if existing_user.customer_profile:
                    self.stdout.write(
                        self.style.WARNING(
                            f"User {existing_user.email} already linked to another customer"
                        )
                    )
                else:
                    if not dry_run:
                        customer.user = existing_user
                        customer.save()
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Linked existing user {existing_user.email} to customer {customer.get_full_name()}"
                        )
                    )
                continue

            # Create new user
            username = customer.email.split('@')[0]
            # Ensure unique username
            base_username = username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1

            if dry_run:
                self.stdout.write(
                    f"Would create user: {username} ({customer.email}) for {customer.get_full_name()}"
                )
            else:
                with transaction.atomic():
                    # Create user
                    user = User.objects.create_user(
                        username=username,
                        email=customer.email,
                        first_name=customer.first_name,
                        last_name=customer.last_name,
                        tenant=customer.tenant,
                        is_tenant_owner=False,
                    )
                    
                    # Set a random password - customer will need to reset it
                    user.set_unusable_password()
                    user.save()
                    
                    # Link to customer
                    customer.user = user
                    customer.save()
                    
                    created_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Created user {user.username} ({user.email}) for {customer.get_full_name()}"
                        )
                    )

        if not dry_run:
            self.stdout.write(
                self.style.SUCCESS(f"Successfully created {created_count} user accounts")
            )
