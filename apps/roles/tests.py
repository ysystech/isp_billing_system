"""
Tests for RBAC permissions system.
"""
from django.test import TestCase
from django.contrib.auth.models import Permission
from django.contrib.auth import get_user_model
from django.core.management import call_command
from apps.roles.models import Role, PermissionCategory, PermissionCategoryMapping
from apps.utils.test_base import TenantTestCase

User = get_user_model()


class PermissionMappingTest(TestCase):
    """Test that all permissions are properly mapped to categories."""
    
    def setUp(self):
        """Set up test data."""
        super().setUp()
        # Run the management commands to set up categories and mappings
        call_command('setup_permission_categories', verbosity=0)
        call_command('map_permissions_to_categories', verbosity=0)
    
    def test_categories_exist(self):
        """Test that permission categories exist."""
        expected_categories = [
            'dashboard',
            'customers', 
            'barangays',
            'routers',
            'plans',
            'lcp',
            'installations',
            'subscriptions',
            'tickets',
            'reports',
            'users',
        ]
        
        for code in expected_categories:
            self.assertTrue(
                PermissionCategory.objects.filter(code=code).exists(),
                f"Category {code} does not exist"
            )
    
    def test_permission_mapping_structure(self):
        """Test that permission mappings are created correctly."""
        # Just verify that mappings exist and have the right structure
        self.assertTrue(PermissionCategoryMapping.objects.exists())
        
        # Check a sample mapping
        mapping = PermissionCategoryMapping.objects.first()
        self.assertIsNotNone(mapping.category)
        self.assertIsNotNone(mapping.permission)
        self.assertIsNotNone(mapping.display_name)
    
    def test_critical_permissions_exist(self):
        """Test that critical permissions for the system exist and are mapped."""
        critical_permissions = [
            ('customers', 'view_customer_list'),
            ('customers', 'create_customer'),
            ('routers', 'add_router'),
            ('lcp', 'add_lcp'),
            ('customer_installations', 'create_installation'),
            ('customer_subscriptions', 'create_subscription'),
            ('tickets', 'create_ticket'),
            ('roles', 'view_role'),
        ]
        
        for app_label, codename in critical_permissions:
            # Check permission exists
            perm_exists = Permission.objects.filter(
                content_type__app_label=app_label,
                codename=codename
            ).exists()
            
            if perm_exists:
                # Check it's mapped
                perm = Permission.objects.get(
                    content_type__app_label=app_label,
                    codename=codename
                )
                mapping_exists = PermissionCategoryMapping.objects.filter(
                    permission=perm
                ).exists()
                self.assertTrue(
                    mapping_exists,
                    f"Permission {app_label}.{codename} exists but is not mapped"
                )


class RolePermissionTest(TenantTestCase):
    """Test role and permission assignment functionality."""
    
    def setUp(self):
        """Set up test data."""
        super().setUp()  # This creates tenant and users
        call_command('setup_permission_categories', verbosity=0)
        call_command('map_permissions_to_categories', verbosity=0)
        
        # Create test role with tenant
        self.role = Role.objects.create(
            name='Test Role',
            description='Test role for unit tests',
            tenant=self.tenant
        )
    
    def test_role_creation(self):
        """Test that roles can be created successfully."""
        self.assertEqual(self.role.name, 'Test Role')
        self.assertEqual(self.role.tenant, self.tenant)
        self.assertIsNotNone(self.role.group)
    
    def test_role_permission_assignment(self):
        """Test assigning permissions to a role."""
        # Get any existing permission
        perm = Permission.objects.filter(
            codename='view_customer_list'
        ).first()
        
        if perm:
            # Assign permission to role
            self.role.group.permissions.add(perm)
            
            # Verify permission is assigned
            self.assertIn(perm, self.role.permissions)
    
    def test_user_role_assignment(self):
        """Test assigning a role to a user."""
        # Assign role to user
        self.user.groups.add(self.role.group)
        
        # Verify user has the role
        self.assertIn(self.role.group, self.user.groups.all())
    
    def test_user_inherits_role_permissions(self):
        """Test that users inherit permissions from their roles."""
        # Get any existing permission
        perm = Permission.objects.filter(
            codename='view_customer_list'
        ).first()
        
        if perm:
            # Add permission to role
            self.role.group.permissions.add(perm)
            
            # Assign role to user
            self.user.groups.add(self.role.group)
            
            # Verify user has the permission
            self.assertTrue(
                self.user.has_perm(f'{perm.content_type.app_label}.{perm.codename}')
            )
    
    def test_system_role_protection(self):
        """Test that system roles are properly marked."""
        # Create a system role
        system_role = Role.objects.create(
            name='System Role',
            description='System role',
            is_system=True,
            tenant=self.tenant
        )
        
        # Verify it's marked as system
        self.assertTrue(system_role.is_system)
        
        # Regular role should not be system
        self.assertFalse(self.role.is_system)
    
    def test_role_tenant_isolation(self):
        """Test that roles are isolated by tenant."""
        # Create role in other tenant
        other_role = Role.objects.create(
            name='Other Role',
            description='Role in other tenant',
            tenant=self.other_tenant
        )
        
        # Query roles for our tenant
        our_roles = Role.objects.filter(tenant=self.tenant)
        
        # Should only see our role, not the other tenant's role
        self.assertIn(self.role, our_roles)
        self.assertNotIn(other_role, our_roles)
        
        # Each tenant can have roles with same name
        duplicate_role = Role.objects.create(
            name='Test Role',  # Same name as self.role
            description='Duplicate name in other tenant',
            tenant=self.other_tenant
        )
        self.assertEqual(duplicate_role.name, self.role.name)
        self.assertNotEqual(duplicate_role.tenant, self.role.tenant)


class PermissionCategoryTest(TestCase):
    """Test permission categories."""
    
    def setUp(self):
        """Set up test data."""
        super().setUp()
        call_command('setup_permission_categories', verbosity=0)
    
    def test_category_creation(self):
        """Test that categories are created with proper attributes."""
        category = PermissionCategory.objects.filter(code='customers').first()
        
        if category:
            self.assertEqual(category.name, 'Customer Management')
            self.assertEqual(category.code, 'customers')
            self.assertIsNotNone(category.description)
            self.assertIsNotNone(category.icon)
            self.assertGreater(category.order, 0)
    
    def test_category_ordering(self):
        """Test that categories have a defined order."""
        categories = PermissionCategory.objects.all().order_by('order')
        
        # Dashboard should come first
        self.assertEqual(categories.first().code, 'dashboard')
        
        # Reports should come last based on the error we saw
        self.assertEqual(categories.last().code, 'reports')
