from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import Permission
from apps.users.models import CustomUser
from apps.tenants.models import Tenant
from apps.roles.models import Role


class RoleFormTest(TestCase):
    """Test the role form functionality."""
    
    def setUp(self):
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
        
        # Grant role permissions
        permissions = Permission.objects.filter(
            codename__in=['view_role', 'add_role', 'change_role']
        )
        self.user.user_permissions.add(*permissions)
        
        self.client.login(username='admin@test.com', password='testpass123')
    
    def test_role_create_page_renders(self):
        """Test that role create page renders without TypeError."""
        response = self.client.get(reverse('roles:role_create'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Create Role')
        self.assertContains(response, 'form')
    
    def test_role_create_sets_tenant(self):
        """Test that creating a role sets the correct tenant."""
        data = {
            'name': 'Test Role',
            'description': 'A test role for testing',
            'is_active': True,
            'is_system': False
        }
        
        response = self.client.post(reverse('roles:role_create'), data)
        
        # Should redirect to permissions page
        self.assertEqual(response.status_code, 302)
        
        # Check role was created with correct tenant
        role = Role.objects.filter(name='Test Role').first()
        self.assertIsNotNone(role)
        self.assertEqual(role.tenant, self.tenant)
        self.assertEqual(role.description, 'A test role for testing')
    
    def test_role_edit_form_accepts_tenant(self):
        """Test that role edit form accepts tenant parameter."""
        # Create a role
        role = Role.objects.create(
            name='Existing Role',
            tenant=self.tenant,
            description='Test role'
        )
        
        response = self.client.get(reverse('roles:role_edit', args=[role.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Existing Role')
    
    def test_only_same_tenant_roles_visible(self):
        """Test that only roles from same tenant are visible."""
        # Create role in current tenant
        role1 = Role.objects.create(
            name='Tenant1 Role',
            tenant=self.tenant
        )
        
        # Create another tenant and role
        other_tenant = Tenant.objects.create(name='Other Company')
        role2 = Role.objects.create(
            name='Tenant2 Role',
            tenant=other_tenant
        )
        
        # List roles
        response = self.client.get(reverse('roles:role_list'))
        self.assertEqual(response.status_code, 200)
        
        # Should see own tenant's role
        self.assertContains(response, 'Tenant1 Role')
        
        # Should NOT see other tenant's role
        self.assertNotContains(response, 'Tenant2 Role')
