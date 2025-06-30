from django.core.management.base import BaseCommand
from django.contrib.auth.models import Permission
from apps.roles.models import PermissionCategory, PermissionCategoryMapping
from apps.users.models import CustomUser


class Command(BaseCommand):
    help = 'Debug permission categories and mappings'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user',
            type=str,
            help='Email of user to check permissions for',
        )

    def handle(self, *args, **options):
        # Check categories
        categories = PermissionCategory.objects.all()
        self.stdout.write(f"\nTotal Permission Categories: {categories.count()}")
        for cat in categories:
            self.stdout.write(f"  - {cat.name} ({cat.code})")
        
        # Check mappings
        mappings = PermissionCategoryMapping.objects.all()
        self.stdout.write(f"\nTotal Permission Mappings: {mappings.count()}")
        
        # Check mappings by category
        for cat in categories:
            cat_mappings = PermissionCategoryMapping.objects.filter(category=cat)
            self.stdout.write(f"\n{cat.name}: {cat_mappings.count()} mappings")
            for mapping in cat_mappings[:3]:  # Show first 3
                self.stdout.write(f"  - {mapping.display_name} ({mapping.permission.codename})")
        
        # Check user permissions if specified
        if options['user']:
            try:
                user = CustomUser.objects.get(email=options['user'])
                self.stdout.write(f"\n\nUser: {user.email}")
                self.stdout.write(f"Is Superuser: {user.is_superuser}")
                self.stdout.write(f"Is Tenant Owner: {getattr(user, 'is_tenant_owner', False)}")
                
                user_perms = user.get_all_permissions()
                self.stdout.write(f"\nUser has {len(user_perms)} permissions:")
                for perm in sorted(list(user_perms))[:10]:  # Show first 10
                    self.stdout.write(f"  - {perm}")
                
                # Check how many mapped permissions the user can see
                visible_count = 0
                for mapping in mappings:
                    perm_name = f"{mapping.permission.content_type.app_label}.{mapping.permission.codename}"
                    if user.is_superuser or perm_name in user_perms:
                        visible_count += 1
                
                self.stdout.write(f"\nUser can see {visible_count}/{mappings.count()} mapped permissions")
            except CustomUser.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"User {options['user']} not found"))
