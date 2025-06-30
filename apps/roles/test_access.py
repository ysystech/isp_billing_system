from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import Permission
from apps.users.models import CustomUser
from apps.tenants.models import Tenant
from apps.roles.models import Role


class RoleAccessTest(TestCase):
    """Test role access permissions for different user types."""
    
    def setUp(self):
        # Create a tenant
        self.tenant = Tenant.objects.create(name='Test Company')
        
        # Create different types of users
        
        # Tenant owner
        self.tenant_owner = CustomUser.objects.create_user(
            username='owner@test.com',
            email='owner@test.com',
            password='testpass123',
            tenant=self.tenant,
            is_tenant_owner=True
        )
        
        # Regular user with role permissions
        self.admin_user = CustomUser.objects.create_user(
            username='admin@test.com',
            email='admin@test.com',
            password='testpass123',
            tenant=self.tenant
        )
        
        # Grant role view permission
        view_role_perm = Permission.objects.get(codename='view_role')
        self.admin_user.user_permissions.add(view_role_perm)
        
        # Create a role with some permissions
        self.cashier_role = Role.objects.create(
            name='Cashier',
            tenant=self.tenant,
            description='Handles payments'
        )
        
        # Add some permissions to the role
        perms = Permission.objects.filter(
            codename__in=['view_customer_list', 'create_subscription']
        )
        for perm in perms:
            self.cashier_role.add_permission(perm)
    
    def test_tenant_owner_can_view_any_role(self):
        """Test that tenant owners can view any role in their tenant."""
        self.client.login(username='owner@test.com', password='testpass123')
        
        response = self.client.get(
            reverse('roles:role_detail', args=[self.cashier_role.pk])
        )
        
        # Should be able to view the role
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Cashier')
        self.assertNotContains(response, 'You do not have permission')
    
    def test_regular_user_without_permissions_cannot_view_role(self):
        """Test that regular users without the role's permissions cannot view it."""
        self.client.login(username='admin@test.com', password='testpass123')
        
        response = self.client.get(
            reverse('roles:role_detail', args=[self.cashier_role.pk])
        )
        
        # Should be redirected with error message
        self.assertEqual(response.status_code, 302)
        
        # Follow redirect to see the error message
        response = self.client.get(response.url)
        self.assertContains(response, 'You do not have permission to view the role')
    
    def test_user_with_all_role_permissions_can_view_role(self):
        """Test that users with all permissions in a role can view it."""
        # Give the admin user the same permissions as the role
        perms = Permission.objects.filter(
            codename__in=['view_customer_list', 'create_subscription']
        )
        for perm in perms:
            self.admin_user.user_permissions.add(perm)
        
        self.client.login(username='admin@test.com', password='testpass123')
        
        response = self.client.get(
            reverse('roles:role_detail', args=[self.cashier_role.pk])
        )
        
        # Should be able to view the role
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Cashier')
    
    def test_tenant_owner_can_edit_any_role(self):
        """Test that tenant owners can edit any role in their tenant."""
        self.client.login(username='owner@test.com', password='testpass123')
        
        # Grant change permission
        change_perm = Permission.objects.get(codename='change_role')
        self.tenant_owner.user_permissions.add(change_perm)
        
        response = self.client.get(
            reverse('roles:role_edit', args=[self.cashier_role.pk])
        )
        
        # Should be able to access edit page
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Cashier')
