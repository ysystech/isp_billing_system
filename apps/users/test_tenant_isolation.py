from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import Permission
from apps.users.models import CustomUser
from apps.tenants.models import Tenant


class UserManagementTenantIsolationTest(TestCase):
    """Test that user management properly isolates users by tenant."""
    
    def setUp(self):
        # Create two tenants
        self.tenant1 = Tenant.objects.create(name='Tenant One')
        self.tenant2 = Tenant.objects.create(name='Tenant Two')
        
        # Create admin users for each tenant
        self.admin1 = CustomUser.objects.create_user(
            username='admin1@test.com',
            email='admin1@test.com',
            password='testpass123',
            tenant=self.tenant1,
            is_staff=True
        )
        
        self.admin2 = CustomUser.objects.create_user(
            username='admin2@test.com',
            email='admin2@test.com',
            password='testpass123',
            tenant=self.tenant2,
            is_staff=True
        )
        
        # Grant user management permissions
        permissions = Permission.objects.filter(
            codename__in=['view_customuser', 'add_customuser', 'change_customuser', 'delete_customuser']
        )
        self.admin1.user_permissions.add(*permissions)
        self.admin2.user_permissions.add(*permissions)
        
        # Create regular users for each tenant
        self.user1_tenant1 = CustomUser.objects.create_user(
            username='user1_t1@test.com',
            email='user1_t1@test.com',
            password='testpass123',
            tenant=self.tenant1
        )
        
        self.user2_tenant1 = CustomUser.objects.create_user(
            username='user2_t1@test.com',
            email='user2_t1@test.com',
            password='testpass123',
            tenant=self.tenant1
        )
        
        self.user1_tenant2 = CustomUser.objects.create_user(
            username='user1_t2@test.com',
            email='user1_t2@test.com',
            password='testpass123',
            tenant=self.tenant2
        )
    
    def test_user_list_shows_only_same_tenant_users(self):
        """Test that user list only shows users from the same tenant."""
        # Login as tenant1 admin
        self.client.login(username='admin1@test.com', password='testpass123')
        
        response = self.client.get(reverse('users:user_management_list'))
        self.assertEqual(response.status_code, 200)
        
        # Should see tenant1 users
        self.assertContains(response, 'user1_t1@test.com')
        self.assertContains(response, 'user2_t1@test.com')
        
        # Should NOT see tenant2 users
        self.assertNotContains(response, 'user1_t2@test.com')
        
        # Should see self (admin1)
        self.assertContains(response, 'admin1@test.com')
        
        # Should NOT see admin from other tenant
        self.assertNotContains(response, 'admin2@test.com')
    
    def test_cannot_view_user_from_other_tenant(self):
        """Test that users cannot view details of users from other tenants."""
        # Login as tenant1 admin
        self.client.login(username='admin1@test.com', password='testpass123')
        
        # Try to view tenant2 user
        response = self.client.get(
            reverse('users:user_management_detail', args=[self.user1_tenant2.pk])
        )
        
        # Should get 404 as user is from different tenant
        self.assertEqual(response.status_code, 404)
    
    def test_cannot_update_user_from_other_tenant(self):
        """Test that users cannot update users from other tenants."""
        # Login as tenant1 admin
        self.client.login(username='admin1@test.com', password='testpass123')
        
        # Try to access update page for tenant2 user
        response = self.client.get(
            reverse('users:user_management_update', args=[self.user1_tenant2.pk])
        )
        
        # Should get 404 as user is from different tenant
        self.assertEqual(response.status_code, 404)
    
    def test_new_user_created_with_correct_tenant(self):
        """Test that newly created users are assigned to the creator's tenant."""
        # Login as tenant1 admin
        self.client.login(username='admin1@test.com', password='testpass123')
        
        data = {
            'full_name': 'New User',
            'email': 'newuser@test.com',
            'password': 'testpass123',
            'password_confirm': 'testpass123',
            'roles': []  # No roles
        }
        
        response = self.client.post(reverse('users:user_management_create'), data)
        
        # Should redirect after successful creation
        self.assertEqual(response.status_code, 302)
        
        # Check the new user was created with correct tenant
        new_user = CustomUser.objects.filter(email='newuser@test.com').first()
        self.assertIsNotNone(new_user)
        self.assertEqual(new_user.tenant, self.tenant1)
    
    def test_search_only_finds_same_tenant_users(self):
        """Test that search only returns users from the same tenant."""
        # Login as tenant1 admin
        self.client.login(username='admin1@test.com', password='testpass123')
        
        # Search for "user" - should find tenant1 users but not tenant2 users
        response = self.client.get(
            reverse('users:user_management_list'), 
            {'search': 'user', 'is_active': 'true'}
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Should find tenant1 users
        self.assertContains(response, 'user1_t1@test.com')
        self.assertContains(response, 'user2_t1@test.com')
        
        # Should NOT find tenant2 users
        self.assertNotContains(response, 'user1_t2@test.com')
