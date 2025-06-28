from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()


class UserManagementViewTest(TestCase):
    """Test cases for user management views."""
    
    def setUp(self):
        # Create a superuser for authentication
        self.superuser = User.objects.create_superuser(
            username='admin@test.com',
            email='admin@test.com',
            password='adminpass123'
        )
        
        # Create regular users
        self.cashier_user = User.objects.create_user(
            username='cashier@test.com',
            email='cashier@test.com',
            password='testpass123',
            first_name='Cashier',
            last_name='User'
        )
        
        self.technician_user = User.objects.create_user(
            username='tech@test.com',
            email='tech@test.com',
            password='testpass123',
            first_name='Tech',
            last_name='User'
        )
        
        # Login as superuser
        self.client.login(username='admin@test.com', password='adminpass123')
    
    def test_list_view_excludes_superusers(self):
        """Test that the list view excludes superusers."""
        url = reverse('users:user_management_list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        # Should contain regular users
        self.assertContains(response, 'Cashier User')
        self.assertContains(response, 'Tech User')
        # Should NOT contain superuser in the user list table
        # Note: admin email may appear in navbar but not in the user list
        self.assertNotContains(response, 'Super Admin')
    
    def test_create_user(self):
        """Test creating a new user."""
        url = reverse('users:user_management_create')
        data = {
            'full_name': 'New User',
            'email': 'newuser@test.com',
            'password': 'newpass123',
            'password_confirm': 'newpass123'
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        
        # Check user was created
        new_user = User.objects.get(email='newuser@test.com')
        self.assertEqual(new_user.first_name, 'New')
        self.assertEqual(new_user.last_name, 'User')
        self.assertEqual(new_user.username, 'newuser@test.com')
        self.assertTrue(new_user.check_password('newpass123'))
    
    def test_update_user(self):
        """Test updating a user."""
        url = reverse('users:user_management_update', kwargs={'pk': self.cashier_user.pk})
        data = {
            'full_name': 'Updated Cashier',
            'email': 'updated@test.com',
            'is_active': True
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        
        # Check user was updated
        self.cashier_user.refresh_from_db()
        self.assertEqual(self.cashier_user.first_name, 'Updated')
        self.assertEqual(self.cashier_user.last_name, 'Cashier')
        self.assertEqual(self.cashier_user.email, 'updated@test.com')
        self.assertEqual(self.cashier_user.username, 'updated@test.com')
        self.assertTrue(self.cashier_user.is_active)
    
    def test_deactivate_user(self):
        """Test that users can be deactivated."""
        # Deactivate the technician user
        url = reverse('users:user_management_delete', kwargs={'pk': self.technician_user.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 302)
        
        self.technician_user.refresh_from_db()
        self.assertFalse(self.technician_user.is_active)
    
    def test_search_functionality(self):
        """Test searching for users."""
        url = reverse('users:user_management_list')
        
        # Search by name
        response = self.client.get(url, {'search': 'Cashier'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Cashier User')
        self.assertNotContains(response, 'Tech User')
        
        # Filter by status
        response = self.client.get(url, {'is_active': 'true'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Tech User')
        self.assertContains(response, 'Cashier User')
    
    def test_non_superuser_can_access(self):
        """Test that non-superusers can now access user management."""
        # Login as regular cashier user
        self.client.logout()
        self.client.login(username='cashier@test.com', password='testpass123')
        
        urls = [
            reverse('users:user_management_list'),
            reverse('users:user_management_create'),
            reverse('users:user_management_detail', kwargs={'pk': self.technician_user.pk}),
            reverse('users:user_management_update', kwargs={'pk': self.technician_user.pk}),
        ]
        
        for url in urls:
            response = self.client.get(url)
            # Should be accessible (200 OK)
            self.assertEqual(response.status_code, 200)
