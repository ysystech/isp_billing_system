from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import Permission
from apps.users.models import CustomUser
from apps.tenants.models import Tenant
from apps.roles.models import Role, PermissionCategory, PermissionCategoryMapping
from django.core.management import call_command


class RolePermissionsTest(TestCase):
    """Test the role permissions management functionality."""
    
    def setUp(self):
        # Set up permission categories and mappings
        call_command('setup_permission_categories', verbosity=0)
        call_command('map_permissions_to_categories', verbosity=0)
        
        # Create a tenant
        self.tenant = Tenant.objects.create(name='Test Company')
        
        # Create a user with role permissions
        self.user = CustomUser.objects.create_user(
            username='admin@test.com',
            email='admin@test.com',
            password='testpass123',
            tenant=self.tenant,
            is_staff=True
        )
        
        # Grant all permissions for testing
        self.user.is_superuser = True
        self.user.save()
        
        # Create a test role
        self.role = Role.objects.create(
            name='Test Role',
            tenant=self.tenant,
            description='Test role for permissions'
        )
        
        self.client.login(username='admin@test.com', password='testpass123')
    
    def test_role_permissions_page_has_categories(self):
        """Test that role permissions page shows permission categories."""
        response = self.client.get(reverse('roles:role_permissions', args=[self.role.pk]))
        self.assertEqual(response.status_code, 200)
        
        # Check that permission categories are displayed
        self.assertContains(response, 'Customer Management')
        self.assertContains(response, 'Barangay Management')
        self.assertContains(response, 'Router Management')
        self.assertNotContains(response, 'Debug: permission_data has 0 categories')
    
    def test_permission_categories_exist(self):
        """Test that permission categories were created."""
        categories = PermissionCategory.objects.all()
        self.assertGreater(categories.count(), 0)
        
        # Check specific categories exist
        self.assertTrue(
            PermissionCategory.objects.filter(code='customers').exists()
        )
        self.assertTrue(
            PermissionCategory.objects.filter(code='barangays').exists()
        )
    
    def test_permission_mappings_exist(self):
        """Test that permission mappings were created."""
        mappings = PermissionCategoryMapping.objects.all()
        self.assertGreater(mappings.count(), 0)
        
        # Check that customer category has mappings
        customer_category = PermissionCategory.objects.get(code='customers')
        customer_mappings = PermissionCategoryMapping.objects.filter(
            category=customer_category
        )
        self.assertGreater(customer_mappings.count(), 0)
    
    def test_can_assign_permissions_to_role(self):
        """Test that permissions can be assigned to a role."""
        # Get a permission to assign
        permission = Permission.objects.filter(
            codename='view_customer_list'
        ).first()
        
        self.assertIsNotNone(permission)
        
        # Assign permission via POST
        response = self.client.post(
            reverse('roles:role_permissions', args=[self.role.pk]),
            {'permissions': [str(permission.id)]}
        )
        
        # Should redirect after success
        self.assertEqual(response.status_code, 302)
        
        # Check permission was assigned
        self.assertTrue(
            self.role.permissions.filter(id=permission.id).exists()
        )
