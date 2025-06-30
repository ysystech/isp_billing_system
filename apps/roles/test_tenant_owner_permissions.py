from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import Permission
from apps.users.models import CustomUser
from apps.tenants.models import Tenant
from apps.roles.models import Role
from django.contrib import messages
from django.core.management import call_command


class TenantOwnerPermissionTest(TestCase):
    """Test that tenant owners can assign any permission to roles."""
    
    def setUp(self):
        # Set up permission categories and mappings
        call_command('setup_permission_categories', verbosity=0)
        call_command('map_permissions_to_categories', verbosity=0)
        
        # Create a tenant
        self.tenant = Tenant.objects.create(name='Test Company')
        
        # Create a tenant owner user (no individual permissions)
        self.tenant_owner = CustomUser.objects.create_user(
            username='owner@test.com',
            email='owner@test.com',
            password='testpass123',
            tenant=self.tenant,
            is_tenant_owner=True,
            is_staff=True
        )
        
        # Give basic role management permission
        role_perm = Permission.objects.get(codename='change_role')
        self.tenant_owner.user_permissions.add(role_perm)
        
        # Create a test role
        self.role = Role.objects.create(
            name='Test Role',
            tenant=self.tenant,
            description='Test role for permissions'
        )
        
        self.client.login(username='owner@test.com', password='testpass123')
    
    def test_tenant_owner_can_see_all_permissions(self):
        """Test that tenant owner can see all permissions even without having them."""
        response = self.client.get(reverse('roles:role_permissions', args=[self.role.pk]))
        self.assertEqual(response.status_code, 200)
        
        # Check that permission categories are displayed
        self.assertContains(response, 'Customer Management')
        self.assertContains(response, 'change_customer_basic')
        
        # Verify debug info shows tenant owner status
        self.assertContains(response, 'Debug: Current user is_tenant_owner: True')
    
    def test_tenant_owner_can_assign_any_permission(self):
        """Test that tenant owner can assign permissions they don't have."""
        # Get a permission the tenant owner doesn't have
        customer_perm = Permission.objects.get(codename='change_customer_basic')
        
        # Verify the tenant owner doesn't have this permission
        self.assertFalse(self.tenant_owner.has_perm('customers.change_customer_basic'))
        
        # Try to assign it to the role
        response = self.client.post(
            reverse('roles:role_permissions', args=[self.role.pk]),
            {'permissions': [str(customer_perm.id)]},
            follow=True
        )
        
        # Should succeed without error
        self.assertEqual(response.status_code, 200)
        
        # Check for success message, not error
        messages_list = list(messages.get_messages(response.wsgi_request))
        self.assertTrue(any('Permissions updated' in str(m) for m in messages_list))
        self.assertFalse(any('You cannot assign' in str(m) for m in messages_list))
        
        # Verify permission was assigned to role
        self.assertTrue(self.role.permissions.filter(id=customer_perm.id).exists())
    
    def test_regular_user_cannot_assign_permission_they_dont_have(self):
        """Test that regular users still cannot assign permissions they don't have."""
        # Create a regular user with role management permission
        regular_user = CustomUser.objects.create_user(
            username='regular@test.com',
            email='regular@test.com',
            password='testpass123',
            tenant=self.tenant,
            is_tenant_owner=False,
            is_staff=True
        )
        role_perm = Permission.objects.get(codename='change_role')
        regular_user.user_permissions.add(role_perm)
        
        self.client.login(username='regular@test.com', password='testpass123')
        
        # Try to assign a permission they don't have
        customer_perm = Permission.objects.get(codename='change_customer_basic')
        response = self.client.post(
            reverse('roles:role_permissions', args=[self.role.pk]),
            {'permissions': [str(customer_perm.id)]},
            follow=True
        )
        
        # Should get error message
        messages_list = list(messages.get_messages(response.wsgi_request))
        self.assertTrue(any('You cannot assign' in str(m) for m in messages_list))
        
        # Permission should not be assigned
        self.assertFalse(self.role.permissions.filter(id=customer_perm.id).exists())
