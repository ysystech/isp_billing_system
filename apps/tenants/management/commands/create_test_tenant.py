from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth import get_user_model
from apps.tenants.models import Tenant

User = get_user_model()


class Command(BaseCommand):
    help = 'Creates a test tenant with an owner for development'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            default='owner@example.com',
            help='Email for the tenant owner'
        )
        parser.add_argument(
            '--password',
            type=str,
            default='testpass123',
            help='Password for the tenant owner'
        )
        parser.add_argument(
            '--company',
            type=str,
            default='Test ISP Company',
            help='Company name for the tenant'
        )

    @transaction.atomic
    def handle(self, *args, **options):
        email = options['email']
        password = options['password']
        company = options['company']
        
        # Check if user exists
        if User.objects.filter(email=email).exists():
            self.stdout.write(self.style.WARNING(f'User with email {email} already exists'))
            return
        
        # Create tenant
        self.stdout.write(f'Creating tenant: {company}')
        tenant = Tenant.objects.create(
            name=company,
            is_active=True
        )
        
        # Create user
        self.stdout.write(f'Creating tenant owner: {email}')
        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name='Test',
            last_name='Owner',
            is_active=True,
            tenant=tenant,
            is_tenant_owner=True
        )
        
        # Update tenant with created_by
        tenant.created_by = user
        tenant.save()
        
        self.stdout.write(self.style.SUCCESS(
            f'Successfully created tenant "{company}" with owner {email}'
        ))
        self.stdout.write(f'Login credentials: {email} / {password}')
