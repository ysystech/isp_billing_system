"""
Management command to assign roles to users for testing.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.roles.models import Role
from apps.roles.utils import assign_role_to_user

User = get_user_model()


class Command(BaseCommand):
    help = 'Assign roles to existing users for testing purposes'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            help='Email of the user to assign role to',
        )
        parser.add_argument(
            '--role',
            type=str,
            help='Name of the role to assign',
        )
        parser.add_argument(
            '--list-roles',
            action='store_true',
            help='List all available roles',
        )
        parser.add_argument(
            '--list-users',
            action='store_true',
            help='List all users and their roles',
        )

    def handle(self, *args, **options):
        # List roles if requested
        if options['list_roles']:
            self.list_roles()
            return
        
        # List users if requested
        if options['list_users']:
            self.list_users()
            return
        
        # Assign role to specific user
        email = options.get('email')
        role_name = options.get('role')
        
        if email and role_name:
            self.assign_role(email, role_name)
        else:
            # Assign sample roles to test users if they exist
            self.assign_test_roles()
    
    def list_roles(self):
        """List all available roles."""
        self.stdout.write('\nAvailable Roles:')
        self.stdout.write('=' * 50)
        
        for role in Role.objects.filter(is_active=True):
            self.stdout.write(
                f'\n{role.name}'
                f'\n  Description: {role.description}'
                f'\n  Permissions: {role.permissions.count()}'
                f'\n  Users: {role.user_count}'
            )
    
    def list_users(self):
        """List all users and their roles."""
        self.stdout.write('\nUsers and Their Roles:')
        self.stdout.write('=' * 50)
        
        for user in User.objects.all():
            roles = user.groups.filter(role__is_active=True)
            role_names = [group.role.name for group in roles]
            
            self.stdout.write(
                f'\n{user.get_full_name() or user.username} ({user.email})'
                f'\n  Superuser: {"Yes" if user.is_superuser else "No"}'
                f'\n  Staff: {"Yes" if user.is_staff else "No"}'
                f'\n  Active: {"Yes" if user.is_active else "No"}'
                f'\n  Roles: {", ".join(role_names) if role_names else "None"}'
            )
    
    def assign_role(self, email, role_name):
        """Assign a role to a specific user."""
        try:
            user = User.objects.get(email=email)
            
            if assign_role_to_user(user, role_name):
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ Assigned role "{role_name}" to {user.get_full_name() or user.email}'
                    )
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f'✗ Failed to assign role. Role "{role_name}" not found.')
                )
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'✗ User with email "{email}" not found.')
            )
    
    def assign_test_roles(self):
        """Assign roles to test users if they exist."""
        self.stdout.write('\nAssigning roles to test users...')
        
        test_assignments = [
            # Sample assignments - adjust emails as needed
            ('juan.delacruz@ispbilling.com', 'Cashier'),
            ('ana.reyes@ispbilling.com', 'Cashier'),
            ('pedro.garcia@ispbilling.com', 'Technician'),
            ('carlos.martinez@ispbilling.com', 'Technician'),
            ('rosa.domingo@ispbilling.com', 'Customer Service'),
            ('admin@example.com', 'Manager'),
        ]
        
        assigned_count = 0
        
        for email, role_name in test_assignments:
            try:
                user = User.objects.get(email=email)
                if assign_role_to_user(user, role_name):
                    assigned_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'  ✓ {user.get_full_name() or email} → {role_name}'
                        )
                    )
            except User.DoesNotExist:
                pass
        
        # Also ensure superusers have the Super Admin role
        superusers = User.objects.filter(is_superuser=True)
        for superuser in superusers:
            if assign_role_to_user(superuser, 'Super Admin'):
                assigned_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'  ✓ {superuser.get_full_name() or superuser.email} → Super Admin (superuser)'
                    )
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✓ Assigned {assigned_count} roles to users'
            )
        )
