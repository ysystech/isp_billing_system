from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.tenants.models import Tenant

User = get_user_model()


class Command(BaseCommand):
    help = 'Make tenant owners staff members'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            help='Specific user email to fix',
        )

    def handle(self, *args, **options):
        email = options.get('email')
        
        if email:
            # Fix specific user
            try:
                user = User.objects.get(email=email)
                if user.is_tenant_owner:
                    user.is_staff = True
                    user.save()
                    self.stdout.write(self.style.SUCCESS(f'✅ Made {email} a staff member'))
                else:
                    # Make them tenant owner and staff
                    user.is_tenant_owner = True
                    user.is_staff = True
                    user.save()
                    self.stdout.write(self.style.SUCCESS(f'✅ Made {email} a tenant owner and staff member'))
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'User with email {email} not found'))
        else:
            # Fix all tenant owners
            updated = User.objects.filter(
                is_tenant_owner=True,
                is_staff=False
            ).update(is_staff=True)
            
            self.stdout.write(self.style.SUCCESS(f'✅ Updated {updated} tenant owners to be staff members'))
            
            # Also update all superusers to be staff
            User.objects.filter(is_superuser=True).update(is_staff=True)
            
        # Show current status
        self.stdout.write(self.style.SUCCESS('\n=== Current Status ==='))
        
        # Show tenant owners
        owners = User.objects.filter(is_tenant_owner=True)
        if owners:
            self.stdout.write('\nTenant Owners:')
            for owner in owners:
                staff_status = "✅ Staff" if owner.is_staff else "❌ Not Staff"
                self.stdout.write(f'  {owner.email}: {staff_status}')
        
        # Show superusers
        admins = User.objects.filter(is_superuser=True)
        if admins:
            self.stdout.write('\nSuperusers:')
            for admin in admins:
                staff_status = "✅ Staff" if admin.is_staff else "❌ Not Staff"
                owner_status = "Owner" if admin.is_tenant_owner else "Not Owner"
                self.stdout.write(f'  {admin.email}: {staff_status}, {owner_status}')
