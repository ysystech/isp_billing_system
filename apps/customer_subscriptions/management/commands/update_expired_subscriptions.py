from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.customer_subscriptions.tasks import (
    update_expired_subscriptions,
    update_expired_subscriptions_all_tenants,
    update_expired_subscriptions_for_tenant
)
from apps.tenants.models import Tenant


class Command(BaseCommand):
    help = 'Manually update expired subscriptions'

    def add_arguments(self, parser):
        parser.add_argument(
            '--tenant-id',
            type=int,
            help='Run for specific tenant ID only'
        )
        parser.add_argument(
            '--all-tenants',
            action='store_true',
            help='Run for all active tenants (default)'
        )

    def handle(self, *args, **options):
        tenant_id = options.get('tenant_id')
        
        if tenant_id:
            # Run for specific tenant
            try:
                tenant = Tenant.objects.get(id=tenant_id, is_active=True)
                self.stdout.write(f'Updating expired subscriptions for tenant: {tenant.name}')
                result = update_expired_subscriptions.run_for_tenant(tenant_id)
                self.stdout.write(self.style.SUCCESS(result))
            except Tenant.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Tenant {tenant_id} not found or inactive'))
                return
        else:
            # Run for all tenants
            self.stdout.write('Updating expired subscriptions for all active tenants...')
            results = update_expired_subscriptions.run_for_all_tenants()
            
            for tenant_id, result in results.items():
                tenant = Tenant.objects.get(id=tenant_id)
                if isinstance(result, dict) and 'error' in result:
                    self.stdout.write(
                        self.style.ERROR(f"Tenant {tenant.name}: {result['error']}")
                    )
                else:
                    self.stdout.write(
                        self.style.SUCCESS(f"Tenant {tenant.name}: {result}")
                    )
        
        self.stdout.write(self.style.SUCCESS('Subscription update complete!'))