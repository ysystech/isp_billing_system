from django.core.management.base import BaseCommand
from django.contrib.auth.models import Permission
from apps.users.models import CustomUser
from apps.roles.models import Role


class Command(BaseCommand):
    help = 'Debug user permissions for customer operations'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Username to check permissions for')

    def handle(self, *args, **options):
        username = options['username']
        
        try:
            user = CustomUser.objects.get(username=username)
        except CustomUser.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'User "{username}" not found'))
            return

        self.stdout.write(self.style.SUCCESS(f'\nUser: {user.username}'))
        self.stdout.write(f'Email: {user.email}')
        self.stdout.write(f'Tenant: {user.tenant.name if user.tenant else "None"}')
        self.stdout.write(f'Is Tenant Owner: {user.is_tenant_owner}')
        self.stdout.write(f'Is Superuser: {user.is_superuser}')
        self.stdout.write(f'Is Staff: {user.is_staff}')

        # Check roles
        self.stdout.write(f'\n{self.style.NOTICE("Roles:")}')
        roles = user.user_roles.all()
        if roles:
            for role in roles:
                self.stdout.write(f'  - {role.name} ({"Active" if role.is_active else "Inactive"})')
        else:
            self.stdout.write('  No roles assigned')

        # Check all customer-related permissions
        self.stdout.write(f'\n{self.style.NOTICE("Customer Permissions:")}')
        
        # Get all permissions for the customer app
        customer_perms = Permission.objects.filter(content_type__app_label='customers').order_by('codename')
        
        self.stdout.write(f'\n{self.style.WARNING("Available Customer Permissions:")}')
        for perm in customer_perms:
            self.stdout.write(f'  - {perm.codename}: {perm.name}')
        
        # Check which permissions the user has
        self.stdout.write(f'\n{self.style.WARNING("User Has These Permissions:")}')
        
        # Direct permissions
        user_perms = user.user_permissions.filter(content_type__app_label='customers')
        if user_perms:
            self.stdout.write('  Direct permissions:')
            for perm in user_perms:
                self.stdout.write(f'    - {perm.codename}: {perm.name}')
        
        # Permissions through groups/roles
        if roles:
            for role in roles:
                role_perms = role.permissions.filter(content_type__app_label='customers')
                if role_perms:
                    self.stdout.write(f'  Via role "{role.name}":')
                    for perm in role_perms:
                        self.stdout.write(f'    - {perm.codename}: {perm.name}')
        
        # Check specific permissions needed for views
        self.stdout.write(f'\n{self.style.WARNING("Permission Check for Views:")}')
        
        view_permissions = [
            ('customers.view_customer_list', 'Customer List'),
            ('customers.view_customer_detail', 'Customer Detail'),
            ('customers.create_customer', 'Create Customer'),
            ('customers.change_customer', 'Update Customer'),
            ('customers.delete_customer', 'Delete Customer'),
        ]
        
        for perm_string, view_name in view_permissions:
            has_perm = user.has_perm(perm_string)
            status = self.style.SUCCESS('✓') if has_perm else self.style.ERROR('✗')
            self.stdout.write(f'  {status} {view_name}: {perm_string}')
