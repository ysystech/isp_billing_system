from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.tenants.models import Tenant

User = get_user_model()


class Command(BaseCommand):
    help = 'Fix admin user tenant association'

    def handle(self, *args, **options):
        # Get or create a default tenant
        tenant, created = Tenant.objects.get_or_create(
            name="Default ISP",
            defaults={
                'is_active': True
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created new tenant: {tenant.name}'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Using existing tenant: {tenant.name}'))
        
        # Update all admin/superuser accounts without tenants
        admins_without_tenant = User.objects.filter(
            is_superuser=True,
            tenant__isnull=True
        )
        
        updated_count = 0
        for admin in admins_without_tenant:
            admin.tenant = tenant
            admin.is_staff = True  # Ensure they're staff
            admin.is_tenant_owner = True  # Make them tenant owners
            admin.save()
            updated_count += 1
            self.stdout.write(self.style.SUCCESS(f'Updated user: {admin.username or admin.email}'))
        
        if updated_count:
            self.stdout.write(self.style.SUCCESS(f'\nSuccessfully updated {updated_count} admin user(s)'))
        else:
            self.stdout.write(self.style.WARNING('No admin users needed updating'))
        
        # Show current admin status
        self.stdout.write(self.style.SUCCESS('\n=== Current Admin Users ==='))
        for admin in User.objects.filter(is_superuser=True):
            tenant_name = admin.tenant.name if admin.tenant else "NO TENANT"
            owner_status = "Owner" if getattr(admin, 'is_tenant_owner', False) else "Not Owner"
            self.stdout.write(f'{admin.email}: Tenant={tenant_name}, {owner_status}')
